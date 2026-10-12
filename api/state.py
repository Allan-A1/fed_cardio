"""
Shared mutable server state — training process, live log buffer, metrics.
All fields are modified in-place by the API endpoints.
"""
from __future__ import annotations
import subprocess
from collections import deque
from typing import Optional, Deque
from datetime import datetime


class TrainingState:
    """Singleton that holds the state of the currently running training job."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.cluster_id: Optional[str] = None
        self.current_round: int = 0
        self.local_epoch: int = 0
        self.local_acc: float = 0.0
        # Circular log buffer — keeps the last 200 lines
        self.log_buffer: Deque[dict] = deque(maxlen=200)
        # Notifications queue
        self._notif_id: int = 0
        self.notifications: list[dict] = []

    # ── Process helpers ───────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    @property
    def pid(self) -> Optional[int]:
        return self.process.pid if self.process else None

    def reset(self):
        self.process = None
        self.cluster_id = None
        self.current_round = 0
        self.local_epoch = 0
        self.local_acc = 0.0

    # ── Log helpers ───────────────────────────────────────────────────────────

    def add_log(self, msg: str, log_type: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_buffer.append({"time": ts, "msg": msg, "type": log_type})

    def get_logs(self) -> list[dict]:
        return list(self.log_buffer)

    # ── Notification helpers ──────────────────────────────────────────────────

    def add_notification(self, title: str, msg: str, notif_type: str = "info"):
        self._notif_id += 1
        self.notifications.append({
            "id": self._notif_id,
            "type": notif_type,
            "title": title,
            "msg": msg,
            "time": "just now",
        })
        # Keep only last 20
        if len(self.notifications) > 20:
            self.notifications.pop(0)


# Global singleton
state = TrainingState()
