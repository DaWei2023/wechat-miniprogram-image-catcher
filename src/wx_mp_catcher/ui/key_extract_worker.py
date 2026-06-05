"""后台提取微信图片密钥，避免阻塞 UI."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QProgressDialog, QVBoxLayout, QWidget

from wx_mp_catcher.service import CatcherService


@dataclass
class KeyExtractResult:
    key: str | None = None
    started: bool = False
    canceled: bool = False


class KeyExtractWorker(QThread):
    finished = Signal(object)

    def __init__(self, service: CatcherService, duration_seconds: float = 30.0) -> None:
        super().__init__()
        self.service = service
        self.duration_seconds = duration_seconds
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        key = self.service.extract_image_key(
            monitor_seconds=self.duration_seconds,
            cancel_event=self._cancel,
        )
        self.finished.emit(key)


def extract_key_with_dialog(
    parent: QWidget,
    service: CatcherService,
    duration_seconds: float = 30.0,
) -> KeyExtractResult:
    """在后台线程提取密钥，显示进度对话框。"""
    reply = QMessageBox.question(
        parent,
        "提取密钥",
        "请先在微信中打开并查看 2-3 张图片（点击看大图）。\n\n"
        f"点击「是」后开始扫描微信进程内存（约 {int(duration_seconds)} 秒），期间界面不会卡死。",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return KeyExtractResult()

    progress = QProgressDialog(parent)
    progress.setWindowTitle("提取图片密钥")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setCancelButtonText("取消")
    progress.setRange(0, 0)
    hint = QLabel(
        "正在扫描微信进程内存，请稍候…\n"
        "若长时间无结果，请确认微信已登录，并在微信里点开 2–3 张大图后重试。"
    )
    hint.setWordWrap(True)
    layout = QVBoxLayout()
    layout.addWidget(hint)
    box = QWidget()
    box.setLayout(layout)
    progress.setLabel(box)

    worker = KeyExtractWorker(service, duration_seconds)
    outcome = KeyExtractResult(started=True)
    canceled = False

    def on_finished(key: object) -> None:
        if canceled:
            outcome.canceled = True
        else:
            outcome.key = key if isinstance(key, str) else None
        progress.close()

    def on_canceled() -> None:
        nonlocal canceled
        canceled = True
        worker.cancel()
        progress.setLabelText("正在取消…")

    worker.finished.connect(on_finished)
    progress.canceled.connect(on_canceled)
    worker.start()
    progress.exec()
    worker.wait(5000)
    return outcome
