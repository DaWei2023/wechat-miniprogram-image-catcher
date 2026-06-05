"""激活对话框."""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from wx_mp_catcher.license.constants import PURCHASE_URL
from wx_mp_catcher.license.manager import LicenseManager


class ActivateWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, manager: LicenseManager, code: str) -> None:
        super().__init__()
        self.manager = manager
        self.code = code

    def run(self) -> None:
        ok, message = self.manager.activate(self.code)
        self.finished.emit(ok, message)


class ActivationDialog(QDialog):
    def __init__(self, manager: LicenseManager, parent=None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("激活软件")
        self.setMinimumWidth(460)
        self._worker: ActivateWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "试用额度已用完，或您希望直接激活正式版。\n"
                "每个激活码只能绑定一台设备，激活成功后该码将失效。"
            )
        )

        form = QFormLayout()
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("例如：WXMP-XXXX-XXXX-XXXX")
        form.addRow("激活码：", self.code_edit)
        layout.addLayout(form)

        self.status_label = QLabel(self.manager.status_text())
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buy_row = QHBoxLayout()
        buy_btn = QPushButton("购买激活码")
        buy_btn.clicked.connect(lambda: webbrowser.open(PURCHASE_URL))
        buy_row.addWidget(buy_btn)
        buy_row.addStretch()
        layout.addLayout(buy_row)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self._on_activate)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def _on_activate(self) -> None:
        code = self.code_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入激活码。")
            return

        self.buttons.setEnabled(False)
        self.status_label.setText("正在联网激活，请稍候…")
        self._worker = ActivateWorker(self.manager, code)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, ok: bool, message: str) -> None:
        self.buttons.setEnabled(True)
        if ok:
            QMessageBox.information(self, "激活成功", message)
            self.accept()
        else:
            self.status_label.setText(message)
            QMessageBox.warning(self, "激活失败", message)
