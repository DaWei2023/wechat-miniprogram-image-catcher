"""测试路径探测."""

from pathlib import Path

from wx_mp_catcher.paths import extract_appid_from_path


def test_extract_appid_from_path():
    p = Path("/home/user/xwechat_files/account/applet/wxabcdef1234567890/cache/img.dat")
    assert extract_appid_from_path(p) == "wxabcdef1234567890"


def test_extract_appid_none():
    p = Path("/some/random/path/file.dat")
    assert extract_appid_from_path(p) is None
