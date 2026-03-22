# kiss_talon

Bare-bones cron for your agents. A unit of work is a **talon**.

kiss_talon includes a Claude Code skill, so in a chat you can just say:

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

kiss_talon also includes a Python CLI to list, create, and inspect talons. Its use by humans is optional. You can just install the skill and talk to Claude, or edit the markdown files directly.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
kiss_talon init      # creates ~/.kiss_talon/, adds crontab entry, installs skill
```

## CLI

```
kiss_talon init                # set up dirs, crontab, skill symlink
kiss_talon tick                # run any due talons (called by cron every 10 min)
kiss_talon list                # show all talons and their status
kiss_talon show <id>           # print a talon's recent invocations
kiss_talon create --id NAME --schedule "every 12h" --prompt "..."
```

## Schedule formats

- `every Xh` — every X hours
- `every Xm` — every X minutes
- `daily` — once per day
- `nightly` — once per day, between 1am–5am

## Configuration

Copy `config.example.toml` to `~/.kiss_talon/config.toml`. Supports ntfy.sh for push notifications and extra Claude CLI flags.

## Requirements

- Python 3.10+
- [Claude CLI](https://claude.ai/download) on PATH
- macOS (for osascript notifications; ntfy works anywhere)
