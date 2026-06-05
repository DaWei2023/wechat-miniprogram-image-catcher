"""设备指纹 — 同一台 Windows 机器重装后保持不变."""

from __future__ import annotations

import hashlib
import logging
import platform
import subprocess
from functools import lru_cache

if platform.system() == "Windows":
    import winreg
else:
    winreg = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _read_machine_guid() -> str:
    if platform.system() != "Windows" or winreg is None:
        return platform.node()
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
    except OSError as exc:
        logger.debug("读取 MachineGuid 失败: %s", exc)
        return ""


def _read_system_drive_serial() -> str:
    if platform.system() != "Windows":
        return ""
    try:
        result = subprocess.run(
            ["cmd", "/c", "vol", "C:"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        for part in result.stdout.split():
            if "-" in part and len(part) >= 9:
                return part.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug("读取卷序列号失败: %s", exc)
    return ""


def _read_baseboard_serial() -> str:
    if platform.system() != "Windows":
        return ""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_BaseBoard).SerialNumber",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug("读取主板序列号失败: %s", exc)
    return ""


@lru_cache(maxsize=1)
def get_device_id() -> str:
    """生成稳定的设备 ID（64 位 hex）."""
    parts = [
        _read_machine_guid(),
        _read_system_drive_serial(),
        _read_baseboard_serial(),
        platform.node(),
    ]
    raw = "|".join(p for p in parts if p)
    if not raw:
        raw = platform.node() or "unknown-device"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
