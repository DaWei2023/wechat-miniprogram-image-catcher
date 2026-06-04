"""微信 4.x 缓存路径自动探测."""

from __future__ import annotations

import os
import platform
from pathlib import Path


WATCH_SUBDIRS = ("applet", "cache", "tempImageUtils", "msgattach", "temp")


def discover_xwechat_roots() -> list[Path]:
    """发现 xwechat_files 根目录下的账号目录."""
    roots: list[Path] = []
    candidates = [
        Path.home() / "Documents" / "xwechat_files",
        Path.home() / "Documents" / "WeChat Files",
    ]
    if platform.system() == "Windows":
        userprofile = os.environ.get("USERPROFILE", str(Path.home()))
        candidates = [
            Path(userprofile) / "Documents" / "xwechat_files",
            Path(userprofile) / "Documents" / "WeChat Files",
        ] + candidates

    seen: set[Path] = set()
    for base in candidates:
        if not base.is_dir():
            continue
        for child in base.iterdir():
            if not child.is_dir():
                continue
            if child.name.lower() in ("all users", "applet", "wmpf"):
                continue
            resolved = child.resolve()
            if resolved not in seen:
                seen.add(resolved)
                roots.append(child)
    return roots


def discover_xweb_cache_dirs() -> list[Path]:
    """发现 XWeb 内核缓存目录."""
    dirs: list[Path] = []
    if platform.system() == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            xweb_base = Path(local) / "Tencent" / "WeChat" / "XWeb"
            if xweb_base.is_dir():
                for sub in xweb_base.rglob("Cache"):
                    if sub.is_dir():
                        dirs.append(sub)
    return dirs


def discover_watch_paths(extra: list[Path] | None = None) -> list[Path]:
    """汇总所有应监听的目录."""
    paths: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        if not p.is_dir():
            return
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            paths.append(p)

    for account in discover_xwechat_roots():
        for sub in WATCH_SUBDIRS:
            candidate = account / sub
            if candidate.is_dir():
                add(candidate)
        applet_dir = account / "applet"
        if applet_dir.is_dir():
            add(applet_dir)

    for xweb in discover_xweb_cache_dirs():
        add(xweb)

    if extra:
        for p in extra:
            add(p)

    return paths


def extract_appid_from_path(path: Path) -> str | None:
    """从文件路径中尝试提取小程序 AppID (wx...)."""
    parts = path.parts
    for part in parts:
        lower = part.lower()
        if lower.startswith("wx") and len(part) >= 10:
            # 典型 AppID: wx + 16 hex chars
            suffix = part[2:]
            if suffix.isalnum():
                return part
    return None
