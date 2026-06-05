"""授权相关常量."""

from __future__ import annotations

import os

TRIAL_IMAGE_LIMIT = 10

# 部署授权服务后修改此 URL，或通过环境变量 WXMP_LICENSE_URL 覆盖
DEFAULT_LICENSE_SERVER_URL = os.environ.get(
    "WXMP_LICENSE_URL",
    "http://127.0.0.1:8787",
)

PURCHASE_URL = os.environ.get(
    "WXMP_PURCHASE_URL",
    "https://github.com/DaWei2023/wechat-miniprogram-image-catcher",
)

LICENSE_API_PREFIX = "/api/v1"
