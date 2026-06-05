"""设置窗口."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from wx_mp_catcher.config import AppConfig
from wx_mp_catcher.paths import discover_watch_paths
from wx_mp_catcher.service import CatcherService

logger = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    def __init__(self, service: CatcherService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("设置 - 微信小程序图片抓取")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_from_config()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 输出目录
        out_group = QGroupBox("输出")
        out_layout = QHBoxLayout(out_group)
        self.output_edit = QLineEdit()
        browse_out = QPushButton("浏览…")
        browse_out.clicked.connect(self._browse_output)
        out_layout.addWidget(self.output_edit)
        out_layout.addWidget(browse_out)
        layout.addWidget(out_group)

        # 分类
        cls_group = QGroupBox("分类模式")
        cls_layout = QVBoxLayout(cls_group)
        self.chk_app = QCheckBox("按小程序分文件夹")
        self.chk_date = QCheckBox("按日期分子文件夹")
        self.chk_session = QCheckBox("按页面会话分子文件夹")
        cls_layout.addWidget(self.chk_app)
        cls_layout.addWidget(self.chk_date)
        cls_layout.addWidget(self.chk_session)
        layout.addWidget(cls_group)

        # 过滤
        filter_group = QGroupBox("过滤")
        filter_form = QFormLayout(filter_group)
        self.min_bytes = QSpinBox()
        self.min_bytes.setRange(0, 10_000_000)
        self.min_bytes.setSuffix(" bytes")
        self.min_bytes.setValue(1024)
        filter_form.addRow("最小文件大小:", self.min_bytes)
        self.chk_only_new = QCheckBox("仅保存启动后新产生的文件")
        filter_form.addRow(self.chk_only_new)
        self.session_idle = QSpinBox()
        self.session_idle.setRange(1, 240)
        self.session_idle.setSuffix(" 分钟")
        filter_form.addRow("会话空闲超时:", self.session_idle)
        layout.addWidget(filter_group)

        # 密钥
        key_group = QGroupBox("图片解密密钥 (V2)")
        key_layout = QVBoxLayout(key_group)
        self.key_status = QLabel()
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("32 位十六进制 AES 密钥，可手动粘贴")
        extract_btn = QPushButton("提取图片密钥（请在微信中查看 2-3 张大图）")
        extract_btn.clicked.connect(self._extract_key)
        key_layout.addWidget(self.key_status)
        key_layout.addWidget(self.key_edit)
        key_layout.addWidget(extract_btn)
        layout.addWidget(key_group)

        # 监听路径
        path_group = QGroupBox("监听路径")
        path_layout = QVBoxLayout(path_group)
        self.paths_label = QLabel()
        self.paths_label.setWordWrap(True)
        self.paths_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        detect_btn = QPushButton("重新探测路径")
        detect_btn.clicked.connect(self._refresh_paths_label)
        add_btn = QPushButton("添加自定义路径…")
        add_btn.clicked.connect(self._add_watch_path)
        path_layout.addWidget(self.paths_label)
        path_layout.addWidget(detect_btn)
        path_layout.addWidget(add_btn)
        layout.addWidget(path_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_from_config(self) -> None:
        cfg = self.service.config
        self.output_edit.setText(str(cfg.output_dir))
        self.chk_app.setChecked(cfg.classify_by_app)
        self.chk_date.setChecked(cfg.classify_by_date)
        self.chk_session.setChecked(cfg.classify_by_session)
        self.min_bytes.setValue(cfg.min_file_bytes)
        self.chk_only_new.setChecked(cfg.only_after_start)
        self.session_idle.setValue(cfg.session_idle_minutes)
        self.key_edit.setText(cfg.image_aes_key_hex or "")
        self._update_key_status()
        self._refresh_paths_label()

    def _update_key_status(self) -> None:
        if self.service.config.image_aes_key_hex:
            self.key_status.setText("密钥状态: 已配置")
            self.key_status.setStyleSheet("color: green;")
        else:
            self.key_status.setText("密钥状态: 未配置（V2 加密图片无法解密）")
            self.key_status.setStyleSheet("color: orange;")

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.output_edit.setText(path)

    def _refresh_paths_label(self) -> None:
        auto = discover_watch_paths(self.service.config.watch_paths)
        lines = [str(p) for p in auto[:20]]
        if len(auto) > 20:
            lines.append(f"... 共 {len(auto)} 个目录")
        self.paths_label.setText("\n".join(lines) if lines else "未探测到路径，请确认微信已登录")

    def _add_watch_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "添加监听目录")
        if path:
            paths = list(self.service.config.watch_paths)
            p = Path(path)
            if p not in paths:
                paths.append(p)
            self.service.config.watch_paths = paths
            self._refresh_paths_label()

    def _extract_key(self) -> None:
        from wx_mp_catcher.ui.key_extract_worker import extract_key_with_dialog

        result = extract_key_with_dialog(self, self.service, duration_seconds=30.0)
        if result.key:
            self.key_edit.setText(result.key)
            self._update_key_status()
            QMessageBox.information(self, "成功", f"密钥已保存: {result.key[:8]}...")
        elif result.started and not result.canceled:
            QMessageBox.warning(
                self,
                "未找到密钥",
                "未能从微信进程提取密钥。请确认微信正在运行，并在微信里查看 2–3 张大图后重试，或手动粘贴密钥。",
            )

    def _save(self) -> None:
        cfg = AppConfig(
            output_dir=Path(self.output_edit.text()),
            watch_paths=self.service.config.watch_paths,
            classify_by_app=self.chk_app.isChecked(),
            classify_by_date=self.chk_date.isChecked(),
            classify_by_session=self.chk_session.isChecked(),
            min_file_bytes=self.min_bytes.value(),
            session_idle_minutes=self.session_idle.value(),
            only_after_start=self.chk_only_new.isChecked(),
            image_aes_key_hex=self.key_edit.text().strip() or None,
            app_aliases=self.service.config.app_aliases,
            wizard_completed=True,
            paused=self.service.config.paused,
        )
        self.service.save_config(cfg)
        self._update_key_status()
        QMessageBox.information(self, "已保存", "设置已保存并生效。")
        self.accept()
