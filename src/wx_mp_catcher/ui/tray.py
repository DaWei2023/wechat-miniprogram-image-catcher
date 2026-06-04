"""系统托盘."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from wx_mp_catcher.service import CatcherService
from wx_mp_catcher.ui.settings_window import SettingsWindow
from wx_mp_catcher.ui.wizard import FirstRunWizard

logger = logging.getLogger(__name__)


class TrayApplication:
    def __init__(self, service: CatcherService) -> None:
        self.service = service
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.settings_window: SettingsWindow | None = None
        self.wizard: FirstRunWizard | None = None

        self.tray = QSystemTrayIcon(self.app)
        self.tray.setToolTip("微信小程序图片抓取")
        self._build_menu()
        self.tray.show()

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_tooltip)
        self._status_timer.start(5000)

    def _build_menu(self) -> None:
        menu = QMenu()
        self.action_pause = QAction("暂停监听", menu)
        self.action_pause.triggered.connect(self._toggle_pause)
        menu.addAction(self.action_pause)

        open_dir = QAction("打开输出目录", menu)
        open_dir.triggered.connect(self._open_output_dir)
        menu.addAction(open_dir)

        settings = QAction("设置", menu)
        settings.triggered.connect(self._show_settings)
        menu.addAction(settings)

        menu.addSeparator()
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_settings()

    def _toggle_pause(self) -> None:
        paused = not self.service.config.paused
        self.service.set_paused(paused)
        self.action_pause.setText("恢复监听" if paused else "暂停监听")
        self._update_tooltip()

    def _open_output_dir(self) -> None:
        out = self.service.config.output_dir
        out.mkdir(parents=True, exist_ok=True)
        path = str(out.resolve())
        if sys.platform == "win32":
            subprocess.Popen(["explorer", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _show_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.service)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _show_wizard(self) -> None:
        self.wizard = FirstRunWizard(self.service)
        if self.wizard.exec():
            self.service.reload_config()

    def _update_tooltip(self) -> None:
        cfg = self.service.config
        status = "已暂停" if cfg.paused else "运行中"
        count = self.service.pipeline.saved_today
        paths = self.service.watcher.watched_count
        self.tray.setToolTip(
            f"微信小程序图片抓取\n{status} | 今日 {count} 张 | 监听 {paths} 目录"
        )

    def _quit(self) -> None:
        self.service.shutdown()
        self.app.quit()

    def run(self) -> int:
        if not self.service.config.wizard_completed:
            self._show_wizard()

        if not self.service.config.paused:
            self.service.start()

        self._update_tooltip()
        return self.app.exec()
