"""Talon dataclass and markdown+frontmatter parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml


@dataclass
class Talon:
    id: str
    created: datetime
    schedule: str
    prompt_body: str
    last_run: datetime | None = None
    permissions: list[str] = field(default_factory=lambda: [
        "Bash(read_only)", "WebFetch", "WebSearch", "Read", "Glob", "Grep",
    ])
    notify: str = "osascript"
    invocations: str = ""  # raw text under # Invocations
    after: str | None = None


def parse(path: Path) -> Talon:
    """Read a talon .md file and return a Talon."""
    text = path.read_text()

    # Split frontmatter from body
    m = re.match(r"^---\n(.*?\n)---\n(.*)", text, re.DOTALL)
    if not m:
        raise ValueError(f"No YAML frontmatter in {path}")

    meta = yaml.safe_load(m.group(1))
    body = m.group(2)

    # Split prompt body from invocations
    parts = re.split(r"^# Invocations\s*$", body, maxsplit=1, flags=re.MULTILINE)
    prompt_body = parts[0].strip()
    invocations = parts[1] if len(parts) > 1 else ""

    last_run = meta.get("last_run")
    if isinstance(last_run, str) and last_run:
        last_run = datetime.fromisoformat(last_run)
    else:
        last_run = None

    created = meta.get("created", datetime.now())
    if isinstance(created, str):
        created = datetime.fromisoformat(created)

    return Talon(
        id=meta.get("id", path.stem),
        created=created,
        schedule=meta.get("schedule", ""),
        prompt_body=prompt_body,
        last_run=last_run,
        permissions=meta.get("permissions", [
            "Bash(read_only)", "WebFetch", "WebSearch", "Read", "Glob", "Grep",
        ]),
        notify=meta.get("notify", "osascript"),
        invocations=invocations,
        after=meta.get("after"),
    )


def save(talon: Talon, path: Path) -> None:
    """Serialize a Talon back to markdown."""
    meta: dict = {
        "id": talon.id,
        "created": talon.created.isoformat(),
        "notify": talon.notify,
        "permissions": talon.permissions,
    }
    if talon.after:
        meta["after"] = talon.after
    if talon.schedule:
        meta["schedule"] = talon.schedule
    if talon.last_run:
        meta["last_run"] = talon.last_run.isoformat()

    frontmatter = yaml.dump(meta, default_flow_style=False, sort_keys=False)
    parts = [f"---\n{frontmatter}---\n", talon.prompt_body, ""]

    if talon.invocations:
        parts.append("\n# Invocations")
        parts.append(talon.invocations)

    path.write_text("\n".join(parts))


def get_latest_invocation(path: Path) -> str:
    """Return the text under the last ## YYYY-MM-DD heading in a talon file."""
    text = path.read_text()
    # Find all ## headings in the invocations section
    matches = list(re.finditer(r"^## \d{4}-\d{2}-\d{2}[^\n]*\n", text, re.MULTILINE))
    if not matches:
        return ""
    last = matches[-1]
    return text[last.end():].strip()


def append_invocation(path: Path, text: str) -> None:
    """Append a dated invocation entry to the talon file."""
    content = path.read_text()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {now}\n{text}\n"

    if "# Invocations" in content:
        content += entry
    else:
        content += f"\n# Invocations\n{entry}"

    path.write_text(content)
