"""Core runner: parse talons, check schedule, spawn Claude."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import talon as talon_mod
from .scheduler import is_due
from .notify import notify


TALONS_DIR = Path.home() / ".kiss_talon" / "talons"
LOGS_DIR = Path.home() / ".kiss_talon" / "logs"
CONFIG_PATH = Path.home() / ".kiss_talon" / "config.toml"


def _load_config() -> dict:
    config_path = CONFIG_PATH
    if not config_path.exists():
        return {}
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib  # type: ignore
        return tomllib.loads(config_path.read_text())
    except Exception:
        return {}


def _build_claude_cmd(
    talon: talon_mod.Talon,
    path: Path,
    config: dict,
    trigger_context: str | None = None,
) -> list[str]:
    allowed = ",".join(talon.permissions)
    prompt = (
        f"You are a kiss_talon agent. Read the talon file at {path}. "
        f"Do the task described in the prompt body. "
        f"Append your findings under '# Invocations' with today's date as a ## heading. "
        f"If something urgent is found, output a line starting with 'NOTIFY:' followed by the message."
    )
    if trigger_context is not None:
        prompt += (
            f"\n\nThis talon was triggered by '{talon.after}'. "
            f"Latest output:\n\n{trigger_context}"
        )
    cmd = [
        "claude",
        "--print",
        "--allowedTools", allowed,
        "--prompt", prompt,
    ]
    extra = config.get("claude", {}).get("extra_flags", "")
    if extra:
        cmd.extend(extra.split())
    return cmd


def run_talon(
    talon: talon_mod.Talon,
    path: Path,
    config: dict,
    trigger_context: str | None = None,
) -> None:
    """Run a single talon: spawn Claude, handle output, update state."""
    print(f"Running talon: {talon.id}")
    cmd = _build_claude_cmd(talon, path, config, trigger_context)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout
    except subprocess.TimeoutExpired:
        output = "ERROR: Claude timed out after 5 minutes"
    except FileNotFoundError:
        print("Error: 'claude' CLI not found in PATH")
        return

    # Log output
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"{talon.id}_{timestamp}.log"
    log_file.write_text(output)

    # Append invocation to the talon file
    talon_mod.append_invocation(path, output)

    # Check for NOTIFY: lines
    notify_config = config.get("notify", {})
    for line in output.splitlines():
        if line.startswith("NOTIFY:"):
            msg = line[len("NOTIFY:"):].strip()
            notify(talon.notify, f"kiss_talon: {talon.id}", msg, {
                "ntfy_url": notify_config.get("ntfy", {}).get("url", ""),
                "ntfy_topic": notify_config.get("ntfy", {}).get("topic", "kiss_talon"),
            })

    # Update last_run
    talon.last_run = datetime.now()
    talon_mod.save(talon, path)
    print(f"  Finished: {talon.id}")


MAX_CHAIN_DEPTH = 10


def tick() -> None:
    """Walk all talons, run any that are due, then fire reactive talons."""
    if not TALONS_DIR.exists():
        print("No talons directory found. Run 'kiss_talon init' first.")
        return

    config = _load_config()
    talon_files = sorted(TALONS_DIR.glob("*.md"))

    if not talon_files:
        print("No talons found.")
        return

    # Parse all talons upfront
    talons: dict[str, tuple[talon_mod.Talon, Path]] = {}
    for path in talon_files:
        try:
            t = talon_mod.parse(path)
            talons[t.id] = (t, path)
        except Exception as e:
            print(f"  Skipping {path.name}: {e}")

    # Pass 1: run schedule-due talons
    ran_ids: list[str] = []
    for tid, (t, path) in talons.items():
        if t.schedule and is_due(t.schedule, t.last_run):
            run_talon(t, path, config)
            ran_ids.append(tid)

    # Pass 2: fire reactive talons in chain
    fired: set[str] = set(ran_ids)
    pending = list(ran_ids)
    depth = 0
    while pending and depth < MAX_CHAIN_DEPTH:
        next_pending: list[str] = []
        for trigger_id in pending:
            for tid, (t, path) in talons.items():
                if t.after == trigger_id and tid not in fired:
                    # Get the trigger talon's latest output
                    trigger_path = talons[trigger_id][1]
                    context = talon_mod.get_latest_invocation(trigger_path)
                    run_talon(t, path, config, trigger_context=context)
                    fired.add(tid)
                    next_pending.append(tid)
        pending = next_pending
        depth += 1

    if depth >= MAX_CHAIN_DEPTH and pending:
        print(f"Warning: chain depth limit ({MAX_CHAIN_DEPTH}) reached, stopping.")

    # Warn about circular or missing after targets
    for tid, (t, path) in talons.items():
        if t.after and t.after not in talons:
            print(f"  Warning: {tid} has after={t.after}, but no talon with that ID exists.")

    if not fired:
        print("No talons due.")
