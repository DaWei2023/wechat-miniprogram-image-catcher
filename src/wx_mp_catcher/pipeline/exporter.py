"""图片导出写入."""

from __future__ import annotations

import logging
from pathlib import Path

from wx_mp_catcher.pipeline.classifier import ImageClassifier
from wx_mp_catcher.pipeline.dedup import DedupStore
from wx_mp_catcher.tracker.miniprogram import MiniProgramState

logger = logging.getLogger(__name__)


class ImageExporter:
    def __init__(
        self,
        classifier: ImageClassifier,
        dedup: DedupStore,
    ) -> None:
        self.classifier = classifier
        self.dedup = dedup
        self._seq = 0

    def export(
        self,
        data: bytes,
        ext: str,
        source_path: Path,
        state: MiniProgramState,
        app_id_from_path: str | None = None,
    ) -> Path | None:
        sha256 = self.dedup.hash_bytes(data)
        if self.dedup.is_duplicate_content(sha256):
            logger.debug("跳过重复图片: %s", source_path)
            return None

        out_dir = self.classifier.build_output_dir(state, app_id_from_path)
        out_dir.mkdir(parents=True, exist_ok=True)

        self._seq += 1
        filename = self.classifier.build_filename(ext, self._seq)
        out_path = out_dir / filename

        # 避免覆盖
        while out_path.exists():
            self._seq += 1
            filename = self.classifier.build_filename(ext, self._seq)
            out_path = out_dir / filename

        out_path.write_bytes(data)
        try:
            mtime = source_path.stat().st_mtime
        except OSError:
            mtime = 0.0
        self.dedup.record(source_path, mtime, sha256, out_path)
        logger.info("已保存: %s -> %s", source_path.name, out_path)
        return out_path
