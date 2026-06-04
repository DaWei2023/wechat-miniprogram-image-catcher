# 发布说明 — 获取 Windows 安装包

## 您需要的文件

```
dist/WxMpCatcher-Setup-0.1.0.exe
```

这是标准 Windows 安装程序：**双击 → 下一步 → 完成**，无需安装 Python。

---

## 在一台 Windows 电脑上构建（约 3–5 分钟）

### 前置条件

- Windows 10/11 64 位
- [Python 3.11+](https://www.python.org/downloads/)（安装时勾选 **Add python.exe to PATH**）

### 步骤

1. 将整个 `wechat-miniprogram-image-catcher` 文件夹复制到 Windows
2. **双击** `build\build.bat`
3. 等待完成，脚本会自动：
   - 安装 Python 依赖
   - PyInstaller 打包应用
   - 尝试用 Inno Setup 生成安装包（若未安装会通过 winget 自动安装）
4. 打开 `dist\WxMpCatcher-Setup-0.1.0.exe` 安装

### PowerShell 方式

```powershell
cd wechat-miniprogram-image-catcher
Set-ExecutionPolicy -Scope Process Bypass
.\build\build_installer.ps1
```

---

## 没有 Inno Setup 时

构建脚本仍会生成便携版：

```
dist\wx-mp-catcher\wx-mp-catcher.exe
```

运行备用安装脚本（创建桌面快捷方式）：

```powershell
.\build\install_portable.ps1
```

---

## GitHub Actions 自动构建

若代码托管在 GitHub，推送后 Actions 会自动构建，在 **Actions → Artifacts** 下载 `WxMpCatcher-Setup`。

---

## 安装后

1. 开始菜单 → **微信小程序图片抓取工具**
2. 完成首次向导
3. 微信中查看 2–3 张大图 → 设置 → **提取图片密钥**
4. 打开小程序页面即可自动保存图片
