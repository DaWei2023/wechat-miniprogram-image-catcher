# 微信小程序图片抓取工具 (wx-mp-catcher)

Windows 电脑版微信 4.0+ 小程序页面图片自动抓取、解密与分类保存工具。

## 功能

- 监听微信 4.x 小程序缓存目录（`xwechat_files`、`XWeb` 等）
- 跟踪当前打开的 `WeChatAppEx` 小程序进程（AppID）
- 自动解密 `.dat` 加密图片（XOR / V1 / V2）
- 按小程序、日期、页面会话三种模式组合分类
- SHA256 去重，系统托盘后台运行

## 合规说明

本工具仅供**个人备份与学习**使用，请勿用于爬取他人数据或商业用途。

## 系统要求

- Windows 10/11
- 电脑版微信 4.0 及以上
- Python 3.11+（开发/源码运行）或直接使用打包 exe

## 快速开始

### 方式一：Windows 安装包（推荐）

在 **Windows 电脑**上获取安装包 `WxMpCatcher-Setup-0.1.0.exe`：

**选项 A — 本地构建（需 Windows + Python 3.11+）**

双击或在 cmd 中运行：

```bat
build\build.bat
```

或 PowerShell：

```powershell
.\build\build_installer.ps1
```

构建完成后，安装包位于：

```
dist\WxMpCatcher-Setup-0.1.0.exe
```

**双击该 exe 即可安装**，无需 Python，安装完成后从开始菜单启动。

**选项 B — GitHub Actions 自动构建（推荐，无需本地 Windows 构建）**

```bash
# 安装 GitHub CLI 后一键发布并下载安装包
chmod +x scripts/publish_github.sh
./scripts/publish_github.sh
```

或手动推送后，在 GitHub **Actions → Artifacts** 下载 `WxMpCatcher-Setup`。

详细步骤见 [docs/GITHUB_PUBLISH.md](docs/GITHUB_PUBLISH.md)

### 方式二：源码运行（开发调试）

```bash
cd wechat-miniprogram-image-catcher
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# 命令行模式（无 GUI）
python -m wx_mp_catcher --cli

# 图形界面（系统托盘）
python -m wx_mp_catcher
```

### 方式三：打包 exe（仅便携目录，非安装包）

```bash
pip install -e ".[dev]"
pyinstaller build/wx_mp_catcher.spec
# 产物: dist/wx-mp-catcher/wx-mp-catcher.exe
```

制作完整安装包请使用 `build\build_installer.ps1`。

## 首次使用：密钥初始化（V2 加密）

微信 4.x 部分图片为 V2 加密（AES-128-ECB + XOR），需一次性提取密钥：

1. 保持微信已登录并运行
2. 在微信中打开任意带图片的聊天/小程序，**点击查看 2–3 张大图**
3. 打开本工具 → 设置 → 点击「提取图片密钥」
4. 密钥保存成功后，后续可自动解密 V2 格式 `.dat` 文件

若安全软件拦截内存扫描，请在设置中**手动粘贴** 32 位十六进制 AES 密钥。

## 分类模式

在设置中可组合开启：

| 模式 | 输出路径示例 |
|------|-------------|
| 按小程序 | `输出目录/小程序名/img_20260604_153012_001.jpg` |
| + 按日期 | `输出目录/小程序名/2026-06-04/img_...jpg` |
| + 按会话 | `输出目录/小程序名/session_20260604_1530/img_...jpg` |

## 监听路径（自动探测）

工具会自动扫描：

- `%USERPROFILE%\Documents\xwechat_files\<账号>\applet\`
- `%USERPROFILE%\Documents\xwechat_files\<账号>\cache\`
- `%USERPROFILE%\Documents\xwechat_files\<账号>\tempImageUtils\`
- `%LOCALAPPDATA%\Tencent\WeChat\XWeb\*\Cache\`

可在设置中手动添加或覆盖路径。

## 配置文件

- 配置：`%APPDATA%\wx-mp-catcher\config.json`
- 去重数据库：`%APPDATA%\wx-mp-catcher\dedup.db`
- 日志：`%APPDATA%\wx-mp-catcher\logs\`

## 常见问题

**Q: 打开小程序后没有图片？**  
A: 确认监听已启动；滚动页面加载图片；V2 加密需先完成密钥初始化。

**Q: 杀软报毒？**  
A: 密钥提取需读取微信进程内存，可能误报。添加白名单或使用手动粘贴密钥。

**Q: 微信更新后失效？**  
A: 在设置中重新探测路径，或手动指定新的缓存目录。

## 开发

```bash
pytest tests/
```

详见 [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)

## License

MIT
