"""分类路径单元测试."""

from pathlib import Path

from wx_mp_catcher.config import AppConfig, ClassifyMode
from wx_mp_catcher.pipeline.classifier import ImageClassifier
from wx_mp_catcher.tracker.miniprogram import MiniProgramState


def test_classify_by_app_only(tmp_path):
    cfg = AppConfig(
        output_dir=tmp_path,
        classify_by_app=True,
        classify_by_date=False,
        classify_by_session=False,
    )
    clf = ImageClassifier(cfg)
    state = MiniProgramState(app_id="wx1234567890abcdef", display_name="wx1234567890abcdef")
    out = clf.build_output_dir(state)
    assert out == tmp_path / "wx1234567890abcdef"


def test_classify_by_app_and_date(tmp_path):
    cfg = AppConfig(
        output_dir=tmp_path,
        classify_by_app=True,
        classify_by_date=True,
        classify_by_session=False,
    )
    clf = ImageClassifier(cfg)
    state = MiniProgramState(app_id="wxtest", session_id="session_20260101_1200")
    out = clf.build_output_dir(state)
    parts = out.parts
    assert "wxtest" in parts
    assert any(len(p) == 10 and p[4] == "-" for p in parts)  # YYYY-MM-DD


def test_classify_with_alias(tmp_path):
    cfg = AppConfig(
        output_dir=tmp_path,
        classify_by_app=True,
        classify_by_date=False,
        app_aliases={"wxabc": "测试小程序"},
    )
    clf = ImageClassifier(cfg)
    state = MiniProgramState(app_id="wxabc")
    out = clf.build_output_dir(state)
    assert out == tmp_path / "测试小程序"


def test_classify_mode_flag():
    cfg = AppConfig(classify_by_app=True, classify_by_date=True, classify_by_session=True)
    mode = cfg.classify_mode
    assert mode & ClassifyMode.BY_APP
    assert mode & ClassifyMode.BY_DATE
    assert mode & ClassifyMode.BY_SESSION
