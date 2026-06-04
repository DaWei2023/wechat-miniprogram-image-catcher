#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REPO_NAME="${REPO_NAME:-wechat-miniprogram-image-catcher}"
VISIBILITY="${VISIBILITY:-public}"

if ! command -v gh >/dev/null 2>&1; then
  echo "请先安装 GitHub CLI: https://cli.github.com/"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "请先登录 GitHub:"
  gh auth login
fi

echo "==> 提交本地变更"
git add -A
if git diff --cached --quiet; then
  echo "无新变更"
else
  git commit -m "$(cat <<'EOF'
chore: sync project for GitHub Actions Windows installer build

EOF
)"
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "==> 推送到 origin"
  git push -u origin main
else
  echo "==> 创建 GitHub 仓库并推送: $REPO_NAME ($VISIBILITY)"
  gh repo create "$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push
fi

echo "==> 触发 Windows 安装包构建"
gh workflow run "Build Windows Installer" || true

echo ""
echo "完成！请打开仓库 Actions 页面等待构建结束，然后下载 Artifacts → WxMpCatcher-Setup"
gh repo view --web 2>/dev/null || gh repo view "$(gh repo view --json nameWithOwner -q .nameWithOwner)"
