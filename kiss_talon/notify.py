"""Notification backends."""

from __future__ import annotations

import subprocess
import urllib.request
import json


def notify(method: str, title: str, message: str, config: dict) -> None:
    """Send a notification via the specified method."""
    if method == "osascript":
        _notify_osascript(title, message)
    elif method == "dialog":
        _notify_dialog(title, message)
    elif method == "ntfy":
        _notify_ntfy(title, message, config)
    else:
        print(f"Unknown notify method: {method}")


def _notify_osascript(title: str, message: str) -> None:
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    subprocess.run([
        "osascript", "-e",
        f'display notification "{safe_msg}" with title "{safe_title}"',
    ], check=False)


def _notify_dialog(title: str, message: str) -> None:
    safe_title = title.replace('"', '\\"')
    safe_msg = message.replace('"', '\\"')
    subprocess.Popen([
        "osascript", "-e",
        f'display dialog "{safe_msg}" with title "{safe_title}" buttons {{"OK"}} default button "OK"',
    ])


def _notify_ntfy(title: str, message: str, config: dict) -> None:
    url = config.get("ntfy_url", "").rstrip("/")
    topic = config.get("ntfy_topic", "kiss_talon")
    if not url:
        print("ntfy URL not configured, skipping notification")
        return

    req = urllib.request.Request(
        f"{url}/{topic}",
        data=message.encode(),
        headers={"Title": title},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"ntfy notification failed: {e}")
