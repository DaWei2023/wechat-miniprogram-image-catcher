"""系统托盘与 GUI 入口."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from wx_mp_catcher.service import CatcherService
from wx_mp_catcher.ui.main_window import MainWindow
from wx_mp_catcher.ui.settings_window import SettingsWindow
from wx_mp_catcher.ui.utils import open_output_directory
from wx_mp_catcher.ui.wizard import FirstRunWizard

logger = logging.getLogger(__name__)


class TrayApplication:
    def __init__(self, service: CatcherService) -> None:
        self.service = service
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("微信小程序图片抓取")
        self.app.setQuitOnLastWindowClosed(False)

        self.main_window = MainWindow(service)
        self.main_window.settings_requested.connect(self._show_settings)
        self.main_window.activate_requested.connect(self._show_activation)
        self.main_window.set_tray_hint(self._show_tray_message)

        self.settings_window: SettingsWindow | None = None
        self.wizard: FirstRunWizard | None = None

        self.service.pipeline.on_saved = self._on_image_saved_threadsafe
        self.service.pipeline.on_trial_blocked = self._on_trial_blocked
        self.main_window.trial_blocked.connect(self._handle_trial_blocked)

        self.tray = QSystemTrayIcon(self.app)
        self.tray.setToolTip("微信小程序图片抓取")
        self._build_menu()
        self.tray.show()

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_tooltip)
        self._status_timer.start(5000)

    def _on_image_saved_threadsafe(self, path: Path) -> None:
        self.main_window.image_saved.emit(str(path))

    def _build_menu(self) -> None:
        menu = QMenu()
        show_main = QAction("显示主界面", menu)
        show_main.triggered.connect(self._show_main)
        menu.addAction(show_main)

        self.action_pause = QAction("暂停监听", menu)
        self.action_pause.triggered.connect(self._toggle_pause)
        menu.addAction(self.action_pause)

        open_dir = QAction("打开输出目录", menu)
        open_dir.triggered.connect(lambda: open_output_directory(self.service.config.output_dir))
        menu.addAction(open_dir)

        settings = QAction("设置", menu)
        settings.triggered.connect(self._show_settings)
        menu.addAction(settings)

        activate = QAction("激活软件", menu)
        activate.triggered.connect(self._show_activation)
        menu.addAction(activate)

        menu.addSeparator()
        quit_action = QAction("退出", menu)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self._show_main()

    def _show_main(self) -> None:
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        self.main_window.refresh_status()

    def _show_tray_message(self, text: str) -> None:
        self.tray.showMessage(
            "微信小程序图片抓取",
            text,
            QSystemTrayIcon.MessageIcon.Information,
            3000,
        )

    def _toggle_pause(self) -> None:
        paused = not self.service.config.paused
        self.service.set_paused(paused)
        self.action_pause.setText("恢复监听" if paused else "暂停监听")
        self.main_window.refresh_status()
        self._update_tooltip()

    def _show_activation(self) -> None:
        from wx_mp_catcher.ui.activation_dialog import ActivationDialog

        dialog = ActivationDialog(self.service.license, self.main_window)
        if dialog.exec():
            self.main_window.refresh_status()
            self._update_tooltip()

    def _on_trial_blocked(self) -> None:
        self.main_window.trial_blocked.emit()

    def _handle_trial_blocked(self) -> None:
        self.main_window.refresh_status()
        self._show_main()
        self._show_activation()

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
        self._show_main()
        return self.app.exec()
