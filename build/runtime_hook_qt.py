"""PyInstaller 运行时：确保 Qt 插件路径正确."""

import os
import sys


def _setup_qt_plugins() -> None:
    if not getattr(sys, "frozen", False):
        return
    base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    plugins = os.path.join(base, "PySide6", "plugins")
    if os.path.isdir(plugins):
        os.environ.setdefault("QT_PLUGIN_PATH", plugins)
        platforms = os.path.join(plugins, "platforms")
        if os.path.isdir(platforms):
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", platforms)


_setup_qt_plugins()
