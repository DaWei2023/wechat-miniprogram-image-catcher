"""授权管理 — 试用限制与激活."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum

from wx_mp_catcher import __version__
from wx_mp_catcher.license.api import LicenseApiClient
from wx_mp_catcher.license.constants import DEFAULT_LICENSE_SERVER_URL, TRIAL_IMAGE_LIMIT
from wx_mp_catcher.license.device import get_device_id
from wx_mp_catcher.license.store import LicenseState, LicenseStore

logger = logging.getLogger(__name__)


class LicenseStatus(str, Enum):
    LICENSED = "licensed"
    TRIAL = "trial"
    TRIAL_EXPIRED = "trial_expired"


class LicenseManager:
    def __init__(
        self,
        store: LicenseStore | None = None,
        api: LicenseApiClient | None = None,
        server_url: str | None = None,
    ) -> None:
        self.store = store or LicenseStore()
        self.server_url = server_url or DEFAULT_LICENSE_SERVER_URL
        self.api = api or LicenseApiClient(self.server_url)
        self._state = self._load_and_bind_device()

    def _load_and_bind_device(self) -> LicenseState:
        state = self.store.load()
        device_id = get_device_id()
        if not state.device_id:
            state.device_id = device_id
        elif state.device_id != device_id:
            logger.warning("设备 ID 变化，保留试用/授权状态并更新设备 ID")
            state.device_id = device_id
        if not state.server_url:
            state.server_url = self.server_url
        self.store.save(state)
        return state

    @property
    def state(self) -> LicenseState:
        return self._state

    def refresh_from_server(self) -> None:
        if self.is_licensed():
            if self._state.license_token:
                result = self.api.validate(self._state.device_id, self._state.license_token)
                if result.ok:
                    self._state = self.store.touch_validated(self._state)
                    return
            return

        remote = self.api.get_trial_status(self._state.device_id)
        if remote.ok:
            self._state.trial_images_used = max(
                self._state.trial_images_used,
                remote.images_used,
            )
            self._state.trial_exhausted = (
                self._state.trial_exhausted or remote.trial_exhausted
            )
            self.store.save(self._state)

    def get_status(self) -> LicenseStatus:
        if self.is_licensed():
            return LicenseStatus.LICENSED
        if self._state.trial_exhausted or self._state.trial_images_used >= TRIAL_IMAGE_LIMIT:
            return LicenseStatus.TRIAL_EXPIRED
        return LicenseStatus.TRIAL

    def is_licensed(self) -> bool:
        return bool(self._state.license_token)

    def remaining_trial_images(self) -> int:
        if self.is_licensed():
            return -1
        return max(0, TRIAL_IMAGE_LIMIT - self._state.trial_images_used)

    def can_save_image(self) -> bool:
        if self.is_licensed():
            return True
        if self._state.trial_exhausted:
            return False
        return self._state.trial_images_used < TRIAL_IMAGE_LIMIT

    def record_image_saved(self) -> None:
        """记录一次成功保存。"""
        if self.is_licensed():
            return
        if self._state.trial_exhausted:
            return

        self._state.trial_images_used += 1
        if self._state.trial_images_used >= TRIAL_IMAGE_LIMIT:
            self._state.trial_exhausted = True
        self.store.save(self._state)

        remote = self.api.report_trial_usage(
            self._state.device_id,
            self._state.trial_images_used,
        )
        if remote.ok:
            self._state.trial_images_used = max(
                self._state.trial_images_used,
                remote.images_used,
            )
            self._state.trial_exhausted = (
                self._state.trial_exhausted or remote.trial_exhausted
            )
            self.store.save(self._state)

    def activate(self, code: str) -> tuple[bool, str]:
        result = self.api.activate(
            self._state.device_id,
            code,
            __version__,
        )
        if not result.ok or not result.license_token:
            return False, result.message

        self._state.license_token = result.license_token
        self._state.activation_code = code.strip().upper()
        self._state.activated_at = datetime.now().isoformat(timespec="seconds")
        self._state.trial_exhausted = False
        self.store.save(self._state)
        return True, result.message

    def status_text(self) -> str:
        status = self.get_status()
        if status == LicenseStatus.LICENSED:
            return "已激活（正式版）"
        if status == LicenseStatus.TRIAL_EXPIRED:
            return f"试用已结束（已用 {self._state.trial_images_used}/{TRIAL_IMAGE_LIMIT} 张）"
        remaining = self.remaining_trial_images()
        return f"试用中（还可抓取 {remaining} 张）"
