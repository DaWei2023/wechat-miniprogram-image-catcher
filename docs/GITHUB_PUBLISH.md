# GitHub 发布与下载安装包

## 一键发布（推荐）

在项目根目录执行：

```bash
chmod +x scripts/publish_github.sh
./scripts/publish_github.sh
```

脚本会：
1. 引导 `gh auth login`（若未登录）
2. 创建 GitHub 公开仓库并推送代码
3. 等待 Actions 构建完成
4. 自动下载 `WxMpCatcher-Setup-0.1.0.exe` 到 `dist/`

指定仓库名（默认 `你的用户名/wechat-miniprogram-image-catcher`）：

```bash
./scripts/publish_github.sh yourname/wechat-miniprogram-image-catcher
```

## 手动步骤

### 1. 登录 GitHub CLI

```bash
gh auth login
```

### 2. 创建仓库并推送

```bash
cd wechat-miniprogram-image-catcher
gh repo create wechat-miniprogram-image-catcher --public --source=. --remote=origin --push
```

若仓库已存在：

```bash
git remote add origin https://github.com/你的用户名/wechat-miniprogram-image-catcher.git
git push -u origin main
```

### 3. 查看构建进度

```bash
gh run list --workflow=build-windows.yml
gh run watch
```

或在浏览器打开：**仓库 → Actions → Build Windows Installer**

### 4. 下载安装包

**网页**：Actions 运行记录 → Artifacts → **WxMpCatcher-Setup**

**命令行**：

```bash
gh run download <run-id> -n WxMpCatcher-Setup -D dist/
```

## 重新触发构建

```bash
gh workflow run build-windows.yml
gh run watch
```
