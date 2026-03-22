# kiss-talon

Keep-it-simple-stupid cron hooks for Claude. A unit of work is a **talon**.

> Add a nightly talon that checks macrumors.com and 9to5mac.com for news about the next Mac Mini generation. Give it web fetch and web search permissions.

A markdown file is the database for one talon. It holds the schedule, permissions, context, and invocations.

```markdown
---
id: mac-mini-news
created: '2026-03-22T10:00:00'
schedule: nightly
notify: osascript
permissions:
- WebFetch
- WebSearch
---

Check macrumors.com and 9to5mac.com for news about the next
Mac Mini generation. Summarize anything new.

# Invocations

## 2025-03-23 02:10
No new articles found on either site.

## 2025-03-24 02:10
NOTIFY: 9to5Mac reports Apple suppliers ramping M5 Mac Mini production.
New article: https://9to5mac.com/2026/03/23/m5-mac-mini-production/
```

kiss-talon also includes a Python CLI to list, create, and inspect talons. Its use by humans is optional. You can just install the skill and talk to Claude, or edit the markdown files directly.

kiss-talon can optionally pop a notification dialog on macos.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
kisstalon init      # creates ~/.kisstalon/, adds crontab entry, installs skill
```

## CLI

```
kisstalon init                # set up dirs, crontab, skill symlink
kisstalon tick                # run any due talons (called by cron every 10 min)
kisstalon list                # show all talons and their status
kisstalon show <id>           # print a talon's recent invocations
kisstalon create --id NAME --schedule "every 12h" --prompt "..."
```

## Schedule formats

- `every Xh` — every X hours
- `every Xm` — every X minutes
- `daily` — once per day
- `nightly` — once per day, between 1am–5am

## Configuration

Copy `config.example.toml` to `~/.kisstalon/config.toml`. Supports ntfy.sh for push notifications and extra Claude CLI flags.

## Requirements

- Python 3.10+
- [Claude CLI](https://claude.ai/download) on PATH
- macOS (for osascript notifications; ntfy works anywhere)
