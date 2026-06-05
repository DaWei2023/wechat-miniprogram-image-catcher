"""文件事件处理流水线."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable

from wx_mp_catcher.config import AppConfig
from wx_mp_catcher.decrypt.dat import aes_key_from_hex, decrypt_file
from wx_mp_catcher.license.manager import LicenseManager, LicenseStatus
from wx_mp_catcher.paths import extract_appid_from_path
from wx_mp_catcher.pipeline.classifier import ImageClassifier
from wx_mp_catcher.pipeline.dedup import DedupStore
from wx_mp_catcher.pipeline.exporter import ImageExporter
from wx_mp_catcher.tracker.miniprogram import MiniProgramTracker

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".dat", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ""}


class FilePipeline:
    """解密、去重、分类保存."""

    def __init__(
        self,
        config: AppConfig,
        dedup: DedupStore,
        tracker: MiniProgramTracker,
        license_manager: LicenseManager | None = None,
        on_saved: Callable[[Path], None] | None = None,
        on_trial_blocked: Callable[[], None] | None = None,
    ) -> None:
        self.config = config
        self.dedup = dedup
        self.tracker = tracker
        self.license = license_manager
        self.on_saved = on_saved
        self.on_trial_blocked = on_trial_blocked
        self.classifier = ImageClassifier(config)
        self.exporter = ImageExporter(self.classifier, dedup)
        self._start_time = time.time()
        self._queue: deque[Path] = deque()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._process_loop, daemon=True)
        self._stop = threading.Event()
        self.saved_count = 0
        self.saved_today = 0
        self._today = datetime.now().date()

    def start(self) -> None:
        self._worker.start()

    def stop(self) -> None:
        self._stop.set()

    def enqueue(self, path: Path) -> None:
        with self._lock:
            self._queue.append(path)

    def reload_config(
        self,
        config: AppConfig,
        license_manager: LicenseManager | None = None,
    ) -> None:
        self.config = config
        if license_manager is not None:
            self.license = license_manager
        self.classifier = ImageClassifier(config)
        self.exporter = ImageExporter(self.classifier, self.dedup)

    def _process_loop(self) -> None:
        while not self._stop.is_set():
            path: Path | None = None
            with self._lock:
                if self._queue:
                    path = self._queue.popleft()
            if path is None:
                time.sleep(0.1)
                continue
            try:
                self._handle_file(path)
            except Exception:
                logger.exception("处理文件失败: %s", path)

    def _handle_file(self, path: Path) -> None:
        if self.config.paused:
            return
        if self.license and not self.license.can_save_image():
            logger.info("试用额度已用尽，跳过保存")
            if self.on_trial_blocked:
                self.on_trial_blocked()
            return
        if not path.is_file():
            return

        suffix = path.suffix.lower()
        if suffix not in IMAGE_SUFFIXES and suffix:
            return

        try:
            stat = path.stat()
        except OSError:
            return

        if stat.st_size < self.config.min_file_bytes:
            return

        if self.config.only_after_start and stat.st_mtime < self._start_time:
            return

        if self.dedup.was_processed(path, stat.st_mtime):
            return

        aes_key = aes_key_from_hex(self.config.image_aes_key_hex)
        result = decrypt_file(path, aes_key=aes_key)
        if result is None:
            logger.debug("无法解密或识别: %s", path)
            return

        state = self.tracker.state
        app_from_path = extract_appid_from_path(path)
        saved = self.exporter.export(
            result.data,
            result.ext,
            path,
            state,
            app_from_path,
        )
        if saved:
            if self.license:
                self.license.record_image_saved()
            self.saved_count += 1
            today = datetime.now().date()
            if today != self._today:
                self._today = today
                self.saved_today = 0
            self.saved_today += 1
            if self.on_saved:
                self.on_saved(saved)
