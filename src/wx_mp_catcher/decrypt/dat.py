"""微信 .dat 图片解密 (XOR / V1 / V2)."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

V1_MAGIC = b"\x07\x08V1\x08\x07"
V2_MAGIC = b"\x07\x08V2\x08\x07"
V1_AES_KEY = b"cfcd208495d565ef"

IMAGE_MAGICS: dict[bytes, str] = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"BM": "bmp",
    b"RIFF": "webp",
}


class DatFormat(str, Enum):
    XOR = "xor"
    V1 = "v1"
    V2 = "v2"
    PLAIN = "plain"
    UNKNOWN = "unknown"


@dataclass
class DecryptResult:
    data: bytes
    ext: str
    fmt: DatFormat


def detect_image_ext(data: bytes) -> str | None:
    for magic, ext in IMAGE_MAGICS.items():
        if data[: len(magic)] == magic:
            if ext == "webp" and len(data) >= 12 and data[8:12] != b"WEBP":
                continue
            return ext
    return None


def detect_xor_key(header: bytes) -> int | None:
    """通过 magic bytes 推断单字节 XOR key."""
    for magic in IMAGE_MAGICS:
        if len(header) < len(magic):
            continue
        key = header[0] ^ magic[0]
        ok = True
        for i in range(1, len(magic)):
            if (header[i] ^ key) != magic[i]:
                ok = False
                break
        if ok:
            return key
    return None


def xor_decrypt(data: bytes, key: int) -> bytes:
    return bytes(b ^ key for b in data)


def aligned_aes_block_size(n: int) -> int:
    return ((n + 15) // 16) * 16


def parse_v2_header(data: bytes) -> tuple[int, int, int] | None:
    if len(data) < 15 or data[:6] != V2_MAGIC:
        return None
    aes_size = struct.unpack("<I", data[6:10])[0]
    xor_size = struct.unpack("<I", data[10:14])[0]
    offset = 15
    return aes_size, xor_size, offset


def v2_decrypt(
    data: bytes,
    aes_key: bytes,
    xor_key: int = 0x88,
) -> bytes | None:
    parsed = parse_v2_header(data)
    if parsed is None:
        return None
    aes_size, xor_size, offset = parsed
    aligned = aligned_aes_block_size(aes_size)
    if len(data) < offset + aligned + xor_size:
        return None

    parts: list[bytes] = []
    if aes_size > 0:
        aes_data = data[offset : offset + aligned]
        try:
            cipher = AES.new(aes_key[:16], AES.MODE_ECB)
            dec = unpad(cipher.decrypt(aes_data), 16)
            parts.append(dec[:aes_size])
        except (ValueError, KeyError):
            return None
        offset += aligned

    raw_size = xor_size
    if raw_size > 0:
        raw_end = len(data) - xor_size if xor_size else len(data)
        raw_data = data[offset:raw_end]
        if raw_data:
            parts.append(raw_data)
        xor_data = data[raw_end:]
        if xor_data:
            parts.append(xor_decrypt(xor_data, xor_key))

    result = b"".join(parts)
    return result if detect_image_ext(result) else None


def v1_decrypt(data: bytes, xor_key: int = 0x88) -> bytes | None:
    return v2_decrypt(data, V1_AES_KEY, xor_key)


def decrypt_bytes(
    data: bytes,
    aes_key: bytes | None = None,
    xor_key: int = 0x88,
) -> DecryptResult | None:
    if detect_image_ext(data):
        ext = detect_image_ext(data)
        assert ext
        return DecryptResult(data=data, ext=ext, fmt=DatFormat.PLAIN)

    head = data[:6]
    if head == V2_MAGIC:
        if not aes_key:
            return None
        dec = v2_decrypt(data, aes_key, xor_key)
        if dec:
            ext = detect_image_ext(dec) or "jpg"
            return DecryptResult(data=dec, ext=ext, fmt=DatFormat.V2)
        return None

    if head == V1_MAGIC:
        dec = v1_decrypt(data, xor_key)
        if dec:
            ext = detect_image_ext(dec) or "jpg"
            return DecryptResult(data=dec, ext=ext, fmt=DatFormat.V1)
        return None

    key = detect_xor_key(data[:16])
    if key is not None:
        dec = xor_decrypt(data, key)
        ext = detect_image_ext(dec)
        if ext:
            return DecryptResult(data=dec, ext=ext, fmt=DatFormat.XOR)

    return None


def decrypt_file(
    path: Path,
    aes_key: bytes | None = None,
    xor_key: int = 0x88,
) -> DecryptResult | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 4:
        return None
    return decrypt_bytes(data, aes_key=aes_key, xor_key=xor_key)


def aes_key_from_hex(hex_str: str | None) -> bytes | None:
    if not hex_str:
        return None
    cleaned = hex_str.strip().replace(" ", "")
    if len(cleaned) != 32:
        return None
    try:
        return bytes.fromhex(cleaned)
    except ValueError:
        return None
