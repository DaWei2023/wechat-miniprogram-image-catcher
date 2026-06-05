"""首次运行向导."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from wx_mp_catcher.config import AppConfig
from wx_mp_catcher.paths import discover_watch_paths
from wx_mp_catcher.service import CatcherService


class PathPage(QWizardPage):
    def __init__(self, service: CatcherService) -> None:
        super().__init__()
        self.service = service
        self.setTitle("探测微信缓存路径")
        self.setSubTitle("请确保电脑版微信已登录。工具将自动扫描小程序图片缓存目录。")

        layout = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

        btn = QPushButton("重新探测")
        btn.clicked.connect(self._detect)
        layout.addWidget(btn)
        self._detect()

    def _detect(self) -> None:
        paths = discover_watch_paths()
        if paths:
            text = f"已发现 {len(paths)} 个监听目录，例如:\n" + "\n".join(
                str(p) for p in paths[:5]
            )
        else:
            text = "暂未发现缓存目录。您可以稍后在设置中手动添加路径。"
        self.info.setText(text)


class OutputPage(QWizardPage):
    def __init__(self, service: CatcherService) -> None:
        super().__init__()
        self.service = service
        self.setTitle("选择输出目录")
        layout = QVBoxLayout(self)
        self.path_edit = QLineEdit(str(service.config.output_dir))
        browse = QPushButton("浏览…")
        browse.clicked.connect(self._browse)
        layout.addWidget(self.path_edit)
        layout.addWidget(browse)

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self.wizard(), "输出目录")
        if path:
            self.path_edit.setText(path)


class ClassifyPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("分类方式")
        layout = QVBoxLayout(self)
        self.chk_app = QCheckBox("按小程序分文件夹")
        self.chk_app.setChecked(True)
        self.chk_date = QCheckBox("按日期分子文件夹")
        self.chk_date.setChecked(True)
        self.chk_session = QCheckBox("按页面会话分子文件夹")
        layout.addWidget(self.chk_app)
        layout.addWidget(self.chk_date)
        layout.addWidget(self.chk_session)


class KeyPage(QWizardPage):
    def __init__(self, service: CatcherService) -> None:
        super().__init__()
        self.service = service
        self.setTitle("图片解密密钥（可选）")
        self.setSubTitle(
            "V2 加密图片需要密钥。可在微信中查看 2-3 张大图后点击提取，或稍后在设置中配置。"
        )
        layout = QVBoxLayout(self)
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("留空可跳过，稍后在设置中提取")
        extract = QPushButton("现在提取密钥")
        extract.clicked.connect(self._extract)
        layout.addWidget(self.key_edit)
        layout.addWidget(extract)

    def _extract(self) -> None:
        key = self.service.extract_image_key(monitor_seconds=20.0)
        if key:
            self.key_edit.setText(key)
            QMessageBox.information(self, "成功", "密钥已提取并保存。")
        else:
            QMessageBox.warning(self, "提示", "暂未找到密钥，可稍后在设置中重试。")


class FirstRunWizard(QWizard):
    def __init__(self, service: CatcherService, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("首次设置向导")
        self.setMinimumSize(520, 400)

        self.path_page = PathPage(service)
        self.output_page = OutputPage(service)
        self.classify_page = ClassifyPage()
        self.key_page = KeyPage(service)

        self.addPage(self.path_page)
        self.addPage(self.output_page)
        self.addPage(self.classify_page)
        self.addPage(self.key_page)

        self.setOption(QWizard.WizardOption.NoCancelButton, False)
        self.setButtonText(QWizard.WizardButton.BackButton, "上一步")
        self.setButtonText(QWizard.WizardButton.NextButton, "下一步")
        self.setButtonText(QWizard.WizardButton.FinishButton, "完成")
        self.setButtonText(QWizard.WizardButton.CancelButton, "取消")

    def accept(self) -> None:
        cfg = AppConfig(
            output_dir=Path(self.output_page.path_edit.text()),
            watch_paths=self.service.config.watch_paths,
            classify_by_app=self.classify_page.chk_app.isChecked(),
            classify_by_date=self.classify_page.chk_date.isChecked(),
            classify_by_session=self.classify_page.chk_session.isChecked(),
            image_aes_key_hex=self.key_page.key_edit.text().strip() or None,
            wizard_completed=True,
            paused=False,
        )
        self.service.save_config(cfg)
        super().accept()
