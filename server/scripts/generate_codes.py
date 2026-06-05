#!/usr/bin/env python3
"""批量生成激活码."""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_URL = os.environ.get("WXMP_LICENSE_URL", "http://127.0.0.1:8787")
DEFAULT_TOKEN = os.environ.get("WXMP_ADMIN_TOKEN", "change-me-in-production")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 WxMpCatcher 激活码")
    parser.add_argument("-n", "--count", type=int, default=1, help="生成数量")
    parser.add_argument("--prefix", default="WXMP", help="激活码前缀")
    parser.add_argument("--url", default=DEFAULT_URL, help="授权服务器地址")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="管理员令牌")
    args = parser.parse_args()

    resp = httpx.post(
        f"{args.url.rstrip('/')}/admin/generate-codes",
        params={"admin_token": args.token},
        json={"count": args.count, "prefix": args.prefix},
        timeout=30,
    )
    if resp.status_code != 200:
        print(resp.text, file=sys.stderr)
        return 1
    data = resp.json()
    for code in data.get("codes", []):
        print(code)
    print(f"共生成 {data.get('count', 0)} 个激活码", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
