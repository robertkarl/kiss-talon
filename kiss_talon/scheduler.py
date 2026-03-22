"""Schedule parsing and due-checking."""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta


def _parse_time_of_day(s: str) -> time | None:
    """Parse 'HH:MM' or 'H:MM' into a time object."""
    m = re.match(r"(\d{1,2}):(\d{2})$", s)
    if m:
        return time(int(m.group(1)), int(m.group(2)))
    return None


def is_due(schedule: str, last_run: datetime | None) -> bool:
    """Check whether a talon with the given schedule and last_run is due now."""
    now = datetime.now()
    s = schedule.strip().lower()

    # "daily" or "daily HH:MM"
    if s.startswith("daily"):
        parts = s.split(None, 1)
        target_time = time(0, 0)
        if len(parts) == 2:
            parsed = _parse_time_of_day(parts[1])
            if parsed:
                target_time = parsed
        today_target = datetime.combine(now.date(), target_time)
        if now < today_target:
            return False
        return last_run is None or last_run < today_target

    # "nightly" = daily 2:00, only between 1am-5am
    if s == "nightly":
        if not (1 <= now.hour <= 5):
            return False
        today_target = datetime.combine(now.date(), time(2, 0))
        if now < today_target:
            return False
        return last_run is None or last_run < today_target

    # "every Xh" or "every Xm"
    m = re.match(r"every\s+(\d+)\s*([hm])", s)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        interval = timedelta(hours=val) if unit == "h" else timedelta(minutes=val)
        if last_run is None:
            return True
        return (now - last_run) >= interval

    return False  # unknown schedule format
