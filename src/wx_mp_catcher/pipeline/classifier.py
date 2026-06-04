"""图片分类路径生成."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from wx_mp_catcher.config import AppConfig, ClassifyMode
from wx_mp_catcher.tracker.miniprogram import MiniProgramState


class ImageClassifier:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def build_output_dir(
        self,
        state: MiniProgramState,
        app_id_from_path: str | None = None,
    ) -> Path:
        mode = self.config.classify_mode
        app_id = state.app_id or app_id_from_path or "unknown"
        display = self.config.app_aliases.get(app_id, state.display_name or app_id)

        parts: list[str] = [str(self.config.output_dir)]

        if mode & ClassifyMode.BY_APP or not (mode & (ClassifyMode.BY_DATE | ClassifyMode.BY_SESSION)):
            parts.append(self._safe_name(display))

        if mode & ClassifyMode.BY_DATE:
            parts.append(datetime.now().strftime("%Y-%m-%d"))

        if mode & ClassifyMode.BY_SESSION and state.session_id:
            parts.append(state.session_id)

        return Path(*parts)

    @staticmethod
    def _safe_name(name: str) -> str:
        invalid = '<>:"/\\|?*'
        result = "".join(c if c not in invalid else "_" for c in name)
        return result.strip() or "unknown"

    def build_filename(self, ext: str, seq: int) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"img_{ts}_{seq:03d}.{ext}"
