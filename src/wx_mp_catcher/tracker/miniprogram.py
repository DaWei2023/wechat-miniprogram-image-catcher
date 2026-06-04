"""WeChatAppEx 小程序进程跟踪与会话管理."""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

import psutil

logger = logging.getLogger(__name__)

APPID_RE = re.compile(r"--wmpf-appid=(wx[a-zA-Z0-9]+)")
PROCESS_NAMES = ("WeChatAppEx.exe",)


@dataclass
class MiniProgramState:
    app_id: str | None = None
    session_id: str | None = None
    last_active: datetime = field(default_factory=datetime.now)
    display_name: str | None = None


class MiniProgramTracker:
    """轮询 WeChatAppEx 进程，维护当前 AppID 与会话."""

    def __init__(
        self,
        poll_interval: float = 2.0,
        session_idle_minutes: int = 30,
        app_aliases: dict[str, str] | None = None,
    ) -> None:
        self.poll_interval = poll_interval
        self.session_idle_minutes = session_idle_minutes
        self.app_aliases = app_aliases or {}
        self._state = MiniProgramState()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def state(self) -> MiniProgramState:
        with self._lock:
            return MiniProgramState(
                app_id=self._state.app_id,
                session_id=self._state.session_id,
                last_active=self._state.last_active,
                display_name=self._state.display_name,
            )

    def get_display_name(self, app_id: str | None) -> str:
        if not app_id:
            return "unknown"
        return self.app_aliases.get(app_id, app_id)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def update_aliases(self, aliases: dict[str, str]) -> None:
        self.app_aliases = aliases

    def update_session_idle(self, minutes: int) -> None:
        self.session_idle_minutes = minutes

    @staticmethod
    def scan_active_appids() -> list[str]:
        appids: set[str] = set()
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info.get("name") or proc.name()
                if name not in PROCESS_NAMES:
                    continue
                cmdline = proc.info.get("cmdline") or proc.cmdline()
                text = " ".join(cmdline) if cmdline else ""
                for match in APPID_RE.finditer(text):
                    appids.add(match.group(1))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(appids)

    def _loop(self) -> None:
        while not self._stop.is_set():
            appids = self.scan_active_appids()
            primary = appids[0] if appids else None
            now = datetime.now()
            with self._lock:
                prev = self._state.app_id
                idle_seconds = (now - self._state.last_active).total_seconds()
                need_new_session = False

                if primary != prev:
                    need_new_session = True
                elif primary and idle_seconds > self.session_idle_minutes * 60:
                    need_new_session = True

                if primary:
                    self._state.app_id = primary
                    self._state.last_active = now
                    self._state.display_name = self.get_display_name(primary)
                    if need_new_session or not self._state.session_id:
                        self._state.session_id = now.strftime("session_%Y%m%d_%H%M")
                elif not appids:
                    pass  # 保持上一个 app_id 以便分类

            time.sleep(self.poll_interval)
