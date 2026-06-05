"""应用配置读写."""

from __future__ import annotations

import json
import os
import platform
from enum import Flag, auto
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ClassifyMode(Flag):
    BY_APP = auto()
    BY_DATE = auto()
    BY_SESSION = auto()


def default_config_dir() -> Path:
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    else:
        base = str(Path.home() / ".config")
    return Path(base) / "wx-mp-catcher"


def default_output_dir() -> Path:
    return Path.home() / "Documents" / "WxMpImages"


class AppConfig(BaseModel):
    output_dir: Path = Field(default_factory=default_output_dir)
    watch_paths: list[Path] = Field(default_factory=list)
    classify_by_app: bool = True
    classify_by_date: bool = True
    classify_by_session: bool = False
    min_file_bytes: int = 1024
    session_idle_minutes: int = 30
    only_after_start: bool = True
    image_aes_key_hex: str | None = None
    license_server_url: str = ""
    app_aliases: dict[str, str] = Field(default_factory=dict)
    wizard_completed: bool = False
    paused: bool = False

    @property
    def classify_mode(self) -> ClassifyMode:
        mode = ClassifyMode(0)
        if self.classify_by_app:
            mode |= ClassifyMode.BY_APP
        if self.classify_by_date:
            mode |= ClassifyMode.BY_DATE
        if self.classify_by_session:
            mode |= ClassifyMode.BY_SESSION
        if mode == ClassifyMode(0):
            mode = ClassifyMode.BY_APP
        return mode

    def set_classify_mode(self, mode: ClassifyMode) -> None:
        self.classify_by_app = bool(mode & ClassifyMode.BY_APP)
        self.classify_by_date = bool(mode & ClassifyMode.BY_DATE)
        self.classify_by_session = bool(mode & ClassifyMode.BY_SESSION)


class ConfigManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or default_config_dir()
        self.config_path = self.config_dir / "config.json"
        self.log_dir = self.config_dir / "logs"
        self.dedup_db_path = self.config_dir / "dedup.db"

    def ensure_dirs(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        self.ensure_dirs()
        if not self.config_path.exists():
            cfg = AppConfig()
            self.save(cfg)
            return cfg
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        return AppConfig.model_validate(self._coerce_paths(raw))

    def save(self, config: AppConfig) -> None:
        self.ensure_dirs()
        data = config.model_dump(mode="json")
        data["output_dir"] = str(config.output_dir)
        data["watch_paths"] = [str(p) for p in config.watch_paths]
        self.config_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if platform.system() != "Windows":
            os.chmod(self.config_path, 0o600)

    @staticmethod
    def _coerce_paths(raw: dict[str, Any]) -> dict[str, Any]:
        if "output_dir" in raw:
            raw["output_dir"] = Path(raw["output_dir"])
        if "watch_paths" in raw:
            raw["watch_paths"] = [Path(p) for p in raw["watch_paths"]]
        return raw
