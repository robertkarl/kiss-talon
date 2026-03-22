"""CLI entry point for kiss_talon."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import talon as talon_mod
from .runner import tick, TALONS_DIR, LOGS_DIR, CONFIG_PATH


DEFAULT_CONFIG = """\
[notify]
default = "osascript"

[notify.ntfy]
url = "https://ntfy.example.com"
topic = "kiss_talon"

[claude]
# additional flags passed to claude CLI on every run
extra_flags = ""
"""

CRON_COMMENT = "# kiss_talon tick"
CRON_LINE = "*/10 * * * * kiss_talon tick"


def cmd_init(args: argparse.Namespace) -> None:
    """Create ~/.kiss_talon dirs, config, and crontab entry."""
    TALONS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(DEFAULT_CONFIG)
        print(f"Created {CONFIG_PATH}")
    else:
        print(f"Config already exists: {CONFIG_PATH}")

    # Add crontab entry
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""
    except FileNotFoundError:
        existing = ""

    if "kiss_talon tick" not in existing:
        new_crontab = existing.rstrip() + f"\n{CRON_COMMENT}\n{CRON_LINE}\n"
        subprocess.run(
            ["crontab", "-"],
            input=new_crontab,
            text=True,
            check=True,
        )
        print("Added crontab entry (every 10 minutes)")
    else:
        print("Crontab entry already exists")

    # Install skill symlink
    skill_src = Path(__file__).parent.parent / "skill" / "kiss_talon.md"
    skill_dst = Path.home() / ".claude" / "skills" / "kiss_talon.md"
    if skill_src.exists() and not skill_dst.exists():
        skill_dst.parent.mkdir(parents=True, exist_ok=True)
        skill_dst.symlink_to(skill_src)
        print(f"Installed skill: {skill_dst}")

    print("kiss_talon initialized.")


def cmd_tick(args: argparse.Namespace) -> None:
    tick()


def cmd_list(args: argparse.Namespace) -> None:
    """List all talons with status."""
    if not TALONS_DIR.exists():
        print("No talons directory. Run 'kiss_talon init' first.")
        return

    talon_files = sorted(TALONS_DIR.glob("*.md"))
    if not talon_files:
        print("No talons found.")
        return

    for path in talon_files:
        try:
            t = talon_mod.parse(path)
            last = t.last_run.strftime("%Y-%m-%d %H:%M") if t.last_run else "never"
            if t.after:
                trigger = f"after={t.after:12s}"
            else:
                trigger = f"schedule={t.schedule:12s}"
            print(f"  {t.id:20s}  {trigger}  last_run={last}")
        except Exception as e:
            print(f"  {path.name:20s}  ERROR: {e}")


def cmd_show(args: argparse.Namespace) -> None:
    """Show a talon's details and recent invocations."""
    path = TALONS_DIR / f"{args.id}.md"
    if not path.exists():
        print(f"Talon not found: {args.id}")
        sys.exit(1)

    t = talon_mod.parse(path)
    print(f"ID:       {t.id}")
    if t.after:
        print(f"After:    {t.after}")
    if t.schedule:
        print(f"Schedule: {t.schedule}")
    print(f"Notify:   {t.notify}")
    print(f"Last run: {t.last_run or 'never'}")
    print(f"Permissions: {', '.join(t.permissions)}")
    print()
    print("--- Prompt ---")
    print(t.prompt_body)
    if t.invocations.strip():
        print("\n--- Invocations ---")
        # Show last 50 lines
        lines = t.invocations.strip().splitlines()
        if len(lines) > 50:
            print(f"  ... ({len(lines) - 50} earlier lines omitted)")
            lines = lines[-50:]
        print("\n".join(lines))


def cmd_create(args: argparse.Namespace) -> None:
    """Create a new talon."""
    talon_id = args.id
    schedule = args.schedule
    after = args.after
    prompt = args.prompt

    if not talon_id or not prompt:
        print("Usage: kiss_talon create --id NAME --schedule 'every 12h' --prompt 'Do the thing'")
        print("   or: kiss_talon create --id NAME --after OTHER_ID --prompt 'React to other talon'")
        sys.exit(1)

    if not schedule and not after:
        print("Error: must specify either --schedule or --after")
        sys.exit(1)

    path = TALONS_DIR / f"{talon_id}.md"
    if path.exists():
        print(f"Talon already exists: {path}")
        sys.exit(1)

    TALONS_DIR.mkdir(parents=True, exist_ok=True)

    t = talon_mod.Talon(
        id=talon_id,
        created=datetime.now(),
        schedule=schedule or "",
        prompt_body=prompt,
        after=after,
    )
    talon_mod.save(t, path)
    print(f"Created talon: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="kiss_talon", description="Lightweight agent orchestrator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize kiss_talon")
    sub.add_parser("tick", help="Run scheduled talons")
    sub.add_parser("list", help="List all talons")

    show_p = sub.add_parser("show", help="Show talon details")
    show_p.add_argument("id", help="Talon ID")

    create_p = sub.add_parser("create", help="Create a new talon")
    create_p.add_argument("--id", required=True, help="Talon ID")
    trigger_group = create_p.add_mutually_exclusive_group(required=True)
    trigger_group.add_argument("--schedule", help="Schedule (e.g. 'every 12h')")
    trigger_group.add_argument("--after", help="Run after another talon completes")
    create_p.add_argument("--prompt", required=True, help="Task prompt")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "tick": cmd_tick,
        "list": cmd_list,
        "show": cmd_show,
        "create": cmd_create,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
