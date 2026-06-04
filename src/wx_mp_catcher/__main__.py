"""程序入口."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

from wx_mp_catcher.config import ConfigManager
from wx_mp_catcher.service import CatcherService


def setup_logging(config_manager: ConfigManager) -> None:
    config_manager.ensure_dirs()
    log_file = config_manager.log_dir / "wx-mp-catcher.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def run_cli(service: CatcherService) -> int:
    print("微信小程序图片抓取 — 命令行模式")
    print("按 Ctrl+C 停止")
    service.start()
    paths = service.get_watch_paths()
    print(f"监听 {len(paths)} 个目录:")
    for p in paths[:10]:
        print(f"  {p}")
    if len(paths) > 10:
        print(f"  ... 共 {len(paths)} 个")

    def _handler(sig, frame):  # noqa: ARG001
        print("\n正在停止…")
        service.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)

    try:
        while True:
            time.sleep(5)
            print(
                f"运行中 | 今日保存 {service.pipeline.saved_today} 张 | "
                f"总计 {service.pipeline.saved_count} 张 | "
                f"当前 AppID: {service.tracker.state.app_id or '无'}"
            )
    except KeyboardInterrupt:
        service.shutdown()
    return 0


def run_gui(service: CatcherService) -> int:
    from wx_mp_catcher.ui.tray import TrayApplication

    app = TrayApplication(service)
    return app.run()


def main() -> int:
    parser = argparse.ArgumentParser(description="微信小程序图片抓取工具")
    parser.add_argument("--cli", action="store_true", help="命令行模式（无 GUI）")
    args = parser.parse_args()

    config_manager = ConfigManager()
    setup_logging(config_manager)
    service = CatcherService(config_manager)

    if args.cli:
        return run_cli(service)
    return run_gui(service)


if __name__ == "__main__":
    raise SystemExit(main())
