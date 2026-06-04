"""多目录 watchdog 监听服务."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from wx_mp_catcher.watcher.handlers import FilePipeline

logger = logging.getLogger(__name__)


class _ImageEventHandler(FileSystemEventHandler):
    def __init__(self, pipeline: FilePipeline) -> None:
        super().__init__()
        self.pipeline = pipeline

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.pipeline.enqueue(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.pipeline.enqueue(Path(event.src_path))


class WatchService:
    def __init__(self, pipeline: FilePipeline) -> None:
        self.pipeline = pipeline
        self._observer = Observer()
        self._watched: set[str] = set()
        self._lock = threading.Lock()

    def update_paths(self, paths: list[Path]) -> None:
        with self._lock:
            current = {str(p.resolve()) for p in paths if p.is_dir()}
            to_remove = self._watched - current
            to_add = current - self._watched

            for path_str in to_remove:
                try:
                    self._observer.unschedule_all()
                except Exception:
                    pass
                self._watched.discard(path_str)

            # 重建 observer 更简单可靠
            if to_remove or to_add:
                self._observer.stop()
                self._observer = Observer()
                self._watched.clear()
                handler = _ImageEventHandler(self.pipeline)
                for path_str in current:
                    p = Path(path_str)
                    try:
                        self._observer.schedule(handler, str(p), recursive=True)
                        self._watched.add(path_str)
                        logger.info("监听目录: %s", p)
                    except Exception as exc:
                        logger.warning("无法监听 %s: %s", p, exc)

    def start(self, paths: list[Path]) -> None:
        self.update_paths(paths)
        if self._watched:
            self._observer.start()
            logger.info("文件监听已启动，共 %d 个目录", len(self._watched))

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)
        logger.info("文件监听已停止")

    @property
    def watched_count(self) -> int:
        return len(self._watched)
