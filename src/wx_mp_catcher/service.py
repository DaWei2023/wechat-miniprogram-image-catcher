"""应用核心服务编排."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from wx_mp_catcher.config import AppConfig, ConfigManager
from wx_mp_catcher.decrypt.key_finder import find_image_aes_key_hex_monitor
from wx_mp_catcher.paths import discover_watch_paths
from wx_mp_catcher.pipeline.dedup import DedupStore
from wx_mp_catcher.tracker.miniprogram import MiniProgramTracker
from wx_mp_catcher.watcher.handlers import FilePipeline
from wx_mp_catcher.watcher.service import WatchService

logger = logging.getLogger(__name__)


class CatcherService:
    def __init__(self, config_manager: ConfigManager | None = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.load()
        self.dedup = DedupStore(self.config_manager.dedup_db_path)
        self.tracker = MiniProgramTracker(
            session_idle_minutes=self.config.session_idle_minutes,
            app_aliases=self.config.app_aliases,
        )
        self.pipeline = FilePipeline(
            self.config,
            self.dedup,
            self.tracker,
        )
        self.watcher = WatchService(self.pipeline)
        self._running = False

    def get_watch_paths(self) -> list[Path]:
        auto = discover_watch_paths()
        manual = [p for p in self.config.watch_paths if p.is_dir()]
        combined: list[Path] = []
        seen: set[str] = set()
        for p in auto + manual:
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                combined.append(p)
        return combined

    def start(self) -> None:
        if self._running:
            return
        self.config = self.config_manager.load()
        self.pipeline.reload_config(self.config)
        self.tracker.update_aliases(self.config.app_aliases)
        self.tracker.update_session_idle(self.config.session_idle_minutes)
        self.tracker.start()
        self.pipeline.start()
        paths = self.get_watch_paths()
        self.watcher.start(paths)
        self._running = True
        logger.info("服务已启动")

    def stop(self) -> None:
        if not self._running:
            return
        self.watcher.stop()
        self.pipeline.stop()
        self.tracker.stop()
        self._running = False
        logger.info("服务已停止")

    def set_paused(self, paused: bool) -> None:
        self.config.paused = paused
        self.config_manager.save(self.config)
        self.pipeline.reload_config(self.config)

    def reload_config(self) -> None:
        self.config = self.config_manager.load()
        self.pipeline.reload_config(self.config)
        self.tracker.update_aliases(self.config.app_aliases)
        self.tracker.update_session_idle(self.config.session_idle_minutes)
        if self._running:
            self.watcher.start(self.get_watch_paths())

    def save_config(self, config: AppConfig) -> None:
        self.config = config
        self.config_manager.save(config)
        self.reload_config()

    def extract_image_key(
        self,
        monitor_seconds: float = 30.0,
        cancel_event: threading.Event | None = None,
    ) -> str | None:
        key = find_image_aes_key_hex_monitor(
            duration_seconds=monitor_seconds,
            cancel_event=cancel_event,
        )
        if key:
            self.config.image_aes_key_hex = key
            self.config_manager.save(self.config)
            self.pipeline.reload_config(self.config)
        return key

    def shutdown(self) -> None:
        self.stop()
        self.dedup.close()
