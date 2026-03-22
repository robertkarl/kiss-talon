---
name: kiss_talon
description: Manage kiss_talon periodic agent tasks (talons)
triggers:
  - talon
  - kiss_talon
  - add a hook
  - check hook
  - periodic task
  - scheduled agent
---

# kiss_talon Skill

You can manage kiss_talon talons — periodic tasks run by Claude via cron.

## Talon file format

Talons live in `~/.kiss_talon/talons/` as markdown files with YAML frontmatter:

```markdown
---
id: example-task
created: 2026-03-22T10:00:00
schedule: every 12h
notify: osascript
permissions:
  - Bash(read_only)
  - WebFetch
  - WebSearch
  - Read
---

Check example.com for downtime and report any issues.

# Invocations
```

### Reactive talons (`after` field)

A talon can use `after` instead of `schedule` to fire after another talon completes. The trigger talon's latest output is injected as context.

```markdown
---
id: mac-mini-summarizer
after: mac-mini-checker
notify: dialog
permissions:
  - Read
---

Based on the latest mac-mini-checker findings, draft a tweet
if there is anything newsworthy. Otherwise do nothing.
```

A talon has either `schedule` or `after`, never both. Chains work: if B watches A and C watches B, C fires after B in the same tick. Chain depth is capped at 10.

## Commands

- `kiss_talon init` — Set up ~/.kiss_talon/ and crontab
- `kiss_talon create --id NAME --schedule "every 12h" --prompt "Do the thing"` — Create a scheduled talon
- `kiss_talon create --id NAME --after OTHER_ID --prompt "React to other talon"` — Create a reactive talon
- `kiss_talon list` — Show all talons
- `kiss_talon show ID` — Show talon details and recent invocations
- `kiss_talon tick` — Run any due talons and their reactive dependents (called by cron every 10 min)

## Schedule formats

- `every Xh` — every X hours
- `every Xm` — every X minutes
- `daily` — once per day
- `nightly` — once per day, between 1am-5am

## When creating a talon

1. Pick a descriptive ID (kebab-case)
2. Choose a schedule OR an `after` target
3. Write a clear prompt describing the task
4. Choose permissions (default is read-only + web access)
5. Use `kiss_talon create` or write the .md file directly to `~/.kiss_talon/talons/`
