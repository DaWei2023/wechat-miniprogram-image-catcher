"""授权状态持久化 — 存放在 ProgramData，卸载软件后不删除."""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


def license_data_dir() -> Path:
    if platform.system() == "Windows":
        base = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        return Path(base) / "WxMpCatcher"
    return Path.home() / ".local" / "share" / "WxMpCatcher"


class LicenseState(BaseModel):
    device_id: str = ""
    trial_images_used: int = 0
    trial_exhausted: bool = False
    license_token: str | None = None
    activation_code: str | None = None
    activated_at: str | None = None
    last_validated_at: str | None = None
    server_url: str = ""


class LicenseStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (license_data_dir() / "license_state.json")

    def ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> LicenseState:
        self.ensure_dir()
        if not self.path.exists():
            return LicenseState()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return LicenseState.model_validate(raw)

    def save(self, state: LicenseState) -> None:
        self.ensure_dir()
        self.path.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def touch_validated(self, state: LicenseState) -> LicenseState:
        state.last_validated_at = datetime.now().isoformat(timespec="seconds")
        self.save(state)
        return state
