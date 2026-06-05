"""授权服务器 HTTP 客户端."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from wx_mp_catcher.license.constants import DEFAULT_LICENSE_SERVER_URL, LICENSE_API_PREFIX

logger = logging.getLogger(__name__)


@dataclass
class ActivateResult:
    ok: bool
    message: str
    license_token: str | None = None


@dataclass
class TrialStatusResult:
    ok: bool
    images_used: int = 0
    trial_exhausted: bool = False
    limit: int = 10
    message: str = ""


class LicenseApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 15.0) -> None:
        self.base_url = (base_url or DEFAULT_LICENSE_SERVER_URL).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{LICENSE_API_PREFIX}{path}"

    def get_trial_status(self, device_id: str) -> TrialStatusResult:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self._url("/trial/status"),
                    json={"device_id": device_id},
                )
            data = resp.json()
            if resp.status_code != 200:
                return TrialStatusResult(ok=False, message=data.get("detail", "服务器错误"))
            return TrialStatusResult(
                ok=True,
                images_used=int(data.get("images_used", 0)),
                trial_exhausted=bool(data.get("trial_exhausted")),
                limit=int(data.get("limit", 10)),
            )
        except httpx.HTTPError as exc:
            logger.warning("试用状态同步失败: %s", exc)
            return TrialStatusResult(ok=False, message="无法连接授权服务器")

    def report_trial_usage(self, device_id: str, images_used: int) -> TrialStatusResult:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self._url("/trial/report"),
                    json={"device_id": device_id, "images_used": images_used},
                )
            data = resp.json()
            if resp.status_code != 200:
                return TrialStatusResult(ok=False, message=data.get("detail", "服务器错误"))
            return TrialStatusResult(
                ok=True,
                images_used=int(data.get("images_used", images_used)),
                trial_exhausted=bool(data.get("trial_exhausted")),
                limit=int(data.get("limit", 10)),
            )
        except httpx.HTTPError as exc:
            logger.warning("试用上报失败: %s", exc)
            return TrialStatusResult(ok=False, message="无法连接授权服务器")

    def activate(self, device_id: str, code: str, app_version: str) -> ActivateResult:
        code = code.strip().upper()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self._url("/activate"),
                    json={
                        "device_id": device_id,
                        "code": code,
                        "app_version": app_version,
                    },
                )
            data: dict[str, Any] = resp.json()
            if resp.status_code == 200:
                return ActivateResult(
                    ok=True,
                    message=data.get("message", "激活成功"),
                    license_token=data.get("license_token"),
                )
            return ActivateResult(ok=False, message=data.get("detail", "激活失败"))
        except httpx.HTTPError as exc:
            logger.warning("激活请求失败: %s", exc)
            return ActivateResult(ok=False, message="无法连接授权服务器，请检查网络")

    def validate(self, device_id: str, license_token: str) -> ActivateResult:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self._url("/validate"),
                    json={"device_id": device_id, "license_token": license_token},
                )
            data = resp.json()
            if resp.status_code == 200 and data.get("valid"):
                return ActivateResult(ok=True, message="授权有效")
            return ActivateResult(ok=False, message=data.get("detail", "授权无效"))
        except httpx.HTTPError as exc:
            logger.warning("授权校验失败: %s", exc)
            return ActivateResult(ok=False, message="无法连接授权服务器")
