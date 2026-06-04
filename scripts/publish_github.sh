#!/usr/bin/env bash
# 推送 GitHub 并触发 Actions 构建，完成后下载安装包到 dist/
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== 微信小程序图片抓取 — GitHub 发布 ==="

if ! command -v gh >/dev/null 2>&1; then
  echo "请先安装 GitHub CLI: https://cli.github.com/"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "尚未登录 GitHub，请按提示完成登录:"
  gh auth login --hostname github.com --git-protocol https --web
fi

REPO="${1:-}"
if [[ -z "$REPO" ]]; then
  REPO="$(gh api user -q .login 2>/dev/null)/wechat-miniprogram-image-catcher"
  echo "将使用仓库: $REPO"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  gh repo create "${REPO#*/}" --public --source=. --remote=origin --push --description "Windows 电脑版微信小程序图片自动抓取工具"
else
  git push -u origin main
fi

echo ""
echo "等待 GitHub Actions 构建完成..."
gh run watch --exit-status

RUN_ID="$(gh run list --workflow=build-windows.yml --limit 1 --json databaseId -q '.[0].databaseId')"
echo "下载安装包 artifact..."
mkdir -p dist
gh run download "$RUN_ID" -n WxMpCatcher-Setup -D dist/

echo ""
echo "=== 完成 ==="
echo "安装包已下载到: $ROOT/dist/"
ls -lh dist/*.exe 2>/dev/null || ls -lh dist/
