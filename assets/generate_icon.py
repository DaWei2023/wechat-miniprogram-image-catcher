"""生成应用图标 assets/icon.ico"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _make_png(size: int, rgb: tuple[int, int, int]) -> bytes:
    r, g, b = rgb
    raw = b""
    for y in range(size):
        row = b"\x00"
        for x in range(size):
            # 简单渐变 + 中心圆形
            cx, cy = size // 2, size // 2
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < size * 0.35:
                row += bytes([min(255, r + 40), min(255, g + 40), min(255, b + 40)])
            else:
                row += bytes([r, g, b])
        raw += row
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )


def _write_ico(path: Path, sizes: list[int], rgb: tuple[int, int, int]) -> None:
    images = [(s, _make_png(s, rgb)) for s in sizes]
    offset = 6 + 16 * len(images)
    parts = [struct.pack("<HHH", 0, 1, len(images))]
    data_parts: list[bytes] = []
    for size, png in images:
        w = h = size if size < 256 else 0
        parts.append(
            struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(png), offset)
        )
        data_parts.append(png)
        offset += len(png)
    path.write_bytes(b"".join(parts) + b"".join(data_parts))


def main() -> None:
    out = Path(__file__).resolve().parent / "icon.ico"
    _write_ico(out, [16, 32, 48, 64, 128, 256], (7, 193, 96))  # 微信绿
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
