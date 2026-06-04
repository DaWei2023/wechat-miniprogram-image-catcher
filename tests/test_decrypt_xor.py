"""XOR 解密单元测试."""

from pathlib import Path

from wx_mp_catcher.decrypt.dat import decrypt_bytes, xor_decrypt


def test_xor_decrypt_jpeg():
    # 模拟 XOR 加密的 JPEG (key=0x42)
    jpeg_header = b"\xff\xd8\xff\xe0"
    plain = jpeg_header + b"\x00" * 100
    key = 0x42
    encrypted = xor_decrypt(plain, key)
    result = decrypt_bytes(encrypted)
    assert result is not None
    assert result.ext == "jpg"
    assert result.data[:4] == jpeg_header


def test_plain_png_passthrough():
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    result = decrypt_bytes(png)
    assert result is not None
    assert result.ext == "png"


def test_v1_magic_header_detection():
    from wx_mp_catcher.decrypt.dat import V1_MAGIC

    assert V1_MAGIC == b"\x07\x08V1\x08\x07"
