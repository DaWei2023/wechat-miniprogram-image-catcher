# GitHub 发布与下载安装包

## 一键推送并触发构建

在项目根目录执行：

```bash
./scripts/publish_github.sh
```

首次使用需先登录 GitHub：

```bash
gh auth login
```

按提示在浏览器完成授权即可。

## 手动步骤

```bash
# 1. 登录
gh auth login

# 2. 创建仓库并推送（若尚未创建）
gh repo create wechat-miniprogram-image-catcher --public --source=. --remote=origin --push

# 3. 或推送到已有仓库
git push -u origin main

# 4. 手动触发构建
gh workflow run "Build Windows Installer"
```

## 下载安装包

1. 打开 GitHub 仓库 → **Actions**
2. 点击最新的 **Build Windows Installer** 运行记录
3. 页面底部 **Artifacts** → 下载 **WxMpCatcher-Setup**
4. 解压 zip，得到 `WxMpCatcher-Setup-0.1.0.exe`
5. 双击安装

## 命令行下载（需已登录 gh）

```bash
# 查看最新成功运行的 artifact
gh run list --workflow="Build Windows Installer" --limit 1
gh run download <run-id> -n WxMpCatcher-Setup -D ./release
```
