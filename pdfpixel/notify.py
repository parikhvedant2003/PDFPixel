"""Best-effort desktop notifications, per OS. Never raises."""
from __future__ import annotations

import platform
import shutil
import subprocess


def notify(summary: str, body: str = "") -> None:
    system = platform.system()
    try:
        if system == "Linux":
            if shutil.which("notify-send"):
                subprocess.run(["notify-send", summary, body], check=False)
        elif system == "Darwin":
            safe = body.replace('"', "'")
            title = summary.replace('"', "'")
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{safe}" with title "{title}"'],
                check=False,
            )
        elif system == "Windows":
            try:
                from winotify import Notification
                Notification(app_id="PDFPixel", title=summary, msg=body).show()
            except Exception:
                pass
    except Exception:
        pass  # notifications are non-essential
