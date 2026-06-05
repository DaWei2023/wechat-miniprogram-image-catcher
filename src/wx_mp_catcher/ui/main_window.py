"""实时抓取主界面."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wx_mp_catcher.service import CatcherService
from wx_mp_catcher.ui.utils import open_file_or_folder, open_output_directory


class MainWindow(QMainWindow):
    """显示监听状态与最近抓取图片。"""

    image_saved = Signal(str)
    settings_requested = Signal()
    activate_requested = Signal()
    trial_blocked = Signal()

    def __init__(self, service: CatcherService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self._tray_hint = None
        self.setWindowTitle("微信小程序图片抓取")
        self.setMinimumSize(720, 520)
        self._build_ui()
        self.image_saved.connect(self._on_image_saved)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_status)
        self._timer.start(1500)
        self.refresh_status()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        status_group = QGroupBox("运行状态")
        grid = QGridLayout(status_group)
        self.lbl_status = QLabel("—")
        self.lbl_app = QLabel("—")
        self.lbl_session = QLabel("—")
        self.lbl_today = QLabel("0")
        self.lbl_total = QLabel("0")
        self.lbl_watch = QLabel("0")
        self.lbl_output = QLabel("—")
        self.lbl_key = QLabel("—")
        self.lbl_license = QLabel("—")

        rows = [
            ("监听状态", self.lbl_status),
            ("授权状态", self.lbl_license),
            ("当前小程序", self.lbl_app),
            ("页面会话", self.lbl_session),
            ("今日抓取", self.lbl_today),
            ("累计抓取", self.lbl_total),
            ("监听目录数", self.lbl_watch),
            ("输出目录", self.lbl_output),
            ("解密密钥", self.lbl_key),
        ]
        for i, (title, widget) in enumerate(rows):
            grid.addWidget(QLabel(title + "："), i, 0)
            widget.setWordWrap(True)
            widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(widget, i, 1)
        layout.addWidget(status_group)

        list_group = QGroupBox("最近抓取（实时更新）")
        list_layout = QVBoxLayout(list_group)
        self.capture_list = QListWidget()
        self.capture_list.itemDoubleClicked.connect(self._open_selected_image)
        list_layout.addWidget(self.capture_list)
        layout.addWidget(list_group, stretch=1)

        btn_row = QHBoxLayout()
        self.btn_pause = QPushButton("暂停监听")
        self.btn_pause.clicked.connect(self._toggle_pause)
        btn_open_dir = QPushButton("打开输出目录")
        btn_open_dir.clicked.connect(self._open_output_dir)
        btn_settings = QPushButton("设置")
        btn_settings.clicked.connect(self.settings_requested.emit)
        btn_activate = QPushButton("激活软件")
        btn_activate.clicked.connect(self.activate_requested.emit)
        btn_tray = QPushButton("最小化到托盘")
        btn_tray.clicked.connect(self.hide)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(btn_open_dir)
        btn_row.addWidget(btn_settings)
        btn_row.addWidget(btn_activate)
        btn_row.addWidget(btn_tray)
        layout.addLayout(btn_row)

        hint = QLabel("提示：关闭窗口不会退出程序，程序仍在系统托盘运行。双击托盘图标可重新打开本界面。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)

    def refresh_status(self) -> None:
        cfg = self.service.config
        state = self.service.tracker.state
        paused = cfg.paused
        self.lbl_status.setText("已暂停" if paused else "运行中")
        self.lbl_status.setStyleSheet("color: orange;" if paused else "color: green;")
        self.btn_pause.setText("恢复监听" if paused else "暂停监听")
        self.lbl_app.setText(state.display_name or state.app_id or "未检测到（请打开小程序页面）")
        self.lbl_session.setText(state.session_id or "—")
        self.lbl_today.setText(str(self.service.pipeline.saved_today))
        self.lbl_total.setText(str(self.service.pipeline.saved_count))
        self.lbl_watch.setText(str(self.service.watcher.watched_count))
        self.lbl_output.setText(str(cfg.output_dir))
        if cfg.image_aes_key_hex:
            self.lbl_key.setText("已配置")
            self.lbl_key.setStyleSheet("color: green;")
        else:
            self.lbl_key.setText("未配置（V2 图片无法解密）")
            self.lbl_key.setStyleSheet("color: orange;")
        self.lbl_license.setText(self.service.license.status_text())
        if self.service.license.is_licensed():
            self.lbl_license.setStyleSheet("color: green;")
        elif self.service.license.get_status().value == "trial_expired":
            self.lbl_license.setStyleSheet("color: red;")
        else:
            self.lbl_license.setStyleSheet("color: #0066cc;")

    def add_capture(self, saved_path: str) -> None:
        path = Path(saved_path)
        ts = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{ts}] {path.name}\n{path.parent.name}")
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                72,
                72,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            item.setIcon(QIcon(scaled))
        self.capture_list.insertItem(0, item)
        while self.capture_list.count() > 200:
            self.capture_list.takeItem(self.capture_list.count() - 1)
        self.refresh_status()

    def _on_image_saved(self, saved_path: str) -> None:
        self.add_capture(saved_path)

    def _toggle_pause(self) -> None:
        paused = not self.service.config.paused
        self.service.set_paused(paused)
        self.refresh_status()

    def _open_output_dir(self) -> None:
        open_output_directory(self.service.config.output_dir)

    def _open_selected_image(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            open_file_or_folder(Path(path))

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        if self._tray_hint:
            self._tray_hint("程序已最小化到系统托盘，双击托盘图标可重新打开。")

    def set_tray_hint(self, callback) -> None:
        self._tray_hint = callback
