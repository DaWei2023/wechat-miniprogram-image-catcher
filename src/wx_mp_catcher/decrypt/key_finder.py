"""Windows 微信进程内存图片 AES 密钥提取."""

from __future__ import annotations

import logging
import platform
import re
import threading
from typing import Iterator

import psutil

logger = logging.getLogger(__name__)

WECHAT_PROCESS_NAMES = ("WeChat.exe", "Weixin.exe")
WECHAT_PROCESS_NAMES_FALLBACK = ("WeChatAppEx.exe",)
# 16 字节可打印/二进制 AES key 候选：前后为非 hex 边界
AES_KEY_PATTERN = re.compile(rb"(?<![0-9a-fA-F])([0-9a-fA-F]{32})(?![0-9a-fA-F])")


def _iter_wechat_processes() -> Iterator[psutil.Process]:
    seen: set[int] = set()
    for names in (WECHAT_PROCESS_NAMES, WECHAT_PROCESS_NAMES_FALLBACK):
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pid = proc.info.get("pid") or proc.pid
                if pid in seen:
                    continue
                name = proc.info.get("name") or proc.name()
                if name in names:
                    seen.add(pid)
                    yield proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue


def _read_process_memory(proc: psutil.Process, max_regions: int = 60) -> bytes:
    """读取进程可读内存区域（仅 Windows 完整支持）."""
    if platform.system() != "Windows":
        return b""

    chunks: list[bytes] = []
    count = 0
    try:
        for mmap in proc.memory_maps(grouped=False):
            count += 1
            if count > max_regions:
                break
            path = getattr(mmap, "path", "") or ""
            if path and any(x in path.lower() for x in (".dll", ".exe", "wechat")):
                continue
    except (psutil.AccessDenied, AttributeError):
        pass

    # Windows: use memory_info + read via ctypes if available
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400

        handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, proc.pid
        )
        if not handle:
            return b""

        class MEMORY_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD),
                ("RegionSize", ctypes.c_size_t),
                ("State", wintypes.DWORD),
                ("Protect", wintypes.DWORD),
                ("Type", wintypes.DWORD),
            ]

        mbi = MEMORY_BASIC_INFORMATION()
        address = 0
        max_addr = 0x7FFFFFFFFFFF
        regions_read = 0

        while address < max_addr and regions_read < max_regions:
            result = kernel32.VirtualQueryEx(
                handle,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                ctypes.sizeof(mbi),
            )
            if not result:
                break
            base = mbi.BaseAddress or 0
            size = mbi.RegionSize or 0
            # MEM_COMMIT=0x1000, readable pages
            if mbi.State == 0x1000 and 0 < size < 16 * 1024 * 1024:
                buf = ctypes.create_string_buffer(size)
                bytes_read = ctypes.c_size_t(0)
                ok = kernel32.ReadProcessMemory(
                    handle,
                    ctypes.c_void_p(base),
                    buf,
                    size,
                    ctypes.byref(bytes_read),
                )
                if ok and bytes_read.value:
                    chunks.append(buf.raw[: bytes_read.value])
                    regions_read += 1
            address = base + size

        kernel32.CloseHandle(handle)
    except Exception as exc:
        logger.debug("内存读取失败 pid=%s: %s", proc.pid, exc)

    return b"".join(chunks)


def _score_key_candidate(key_bytes: bytes, memory: bytes) -> int:
    """对候选 key 打分：在内存中出现次数 + 字节熵."""
    if len(key_bytes) != 16:
        return 0
    score = memory.count(key_bytes) * 10
    unique = len(set(key_bytes))
    score += unique
    return score


def find_image_aes_key_hex(timeout_scan: int = 1) -> str | None:
    """
    扫描微信进程内存，寻找 16 字节 AES key。
    返回 32 位 hex 字符串，失败返回 None。
    """
    if platform.system() != "Windows":
        logger.warning("图片密钥提取仅支持 Windows")
        return None

    candidates: dict[bytes, int] = {}

    for proc in _iter_wechat_processes():
        memory = _read_process_memory(proc)
        if not memory:
            continue

        for match in AES_KEY_PATTERN.finditer(memory):
            hex_str = match.group(1)
            try:
                key_bytes = bytes.fromhex(hex_str.decode("ascii"))
            except ValueError:
                continue
            score = _score_key_candidate(key_bytes, memory)
            if score > 0:
                candidates[key_bytes] = candidates.get(key_bytes, 0) + score

        # 也搜索原始 16 字节块（非 hex 编码）
        for i in range(0, len(memory) - 16, 4096):
            block = memory[i : i + 16]
            if len(set(block)) < 6:
                continue
            score = _score_key_candidate(block, memory)
            if score >= 15:
                candidates[block] = candidates.get(block, 0) + score

    if not candidates:
        return None

    best = max(candidates, key=candidates.get)
    return best.hex()


def find_image_aes_key_hex_monitor(
    duration_seconds: float = 30.0,
    interval: float = 2.0,
    cancel_event: threading.Event | None = None,
) -> str | None:
    """持续监控模式：在用户查看图片期间轮询扫描."""
    import time

    deadline = time.time() + duration_seconds
    found: str | None = None
    while time.time() < deadline:
        if cancel_event and cancel_event.is_set():
            return None
        key = find_image_aes_key_hex()
        if key:
            found = key
            break
        if cancel_event and cancel_event.wait(timeout=interval):
            return None
        else:
            time.sleep(interval)
    return found
