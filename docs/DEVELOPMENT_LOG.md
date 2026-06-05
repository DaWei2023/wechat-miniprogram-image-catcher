### 2026-06-05 — 修复密钥提取卡死 UI

- 密钥扫描改为 **QThread 后台线程**，主界面显示进度对话框，支持取消
- 缩小内存扫描范围，优先扫描 `WeChat.exe` / `Weixin.exe`，加快单次扫描速度

## 2026-06-04 — v0.1.1 主界面与中文安装包

### 变更
- 新增 **实时抓取主界面**（`ui/main_window.py`）：显示监听状态、当前小程序、抓取计数、最近图片列表
- 向导/安装完成后 **自动显示主界面**，不再仅隐藏到托盘
- 关闭主窗口 → 最小化到托盘（不退出）；双击托盘可重新打开
- Inno Setup **简体中文界面**：内置 `assets/innosetup/ChineseSimplified.isl`
- 安装许可与说明改为中文（`LICENSE_zh.txt`）
- 版本号升至 **0.1.1**


### 项目信息
- 独立项目路径: `~/wechat-miniprogram-image-catcher`
- 目标平台: Windows 电脑版微信 4.0+

### 完成模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 配置 | `src/wx_mp_catcher/config.py` | JSON 持久化，分类模式、密钥、路径 |
| 路径探测 | `src/wx_mp_catcher/paths.py` | xwechat_files / XWeb 自动扫描 |
| 解密 | `src/wx_mp_catcher/decrypt/dat.py` | XOR / V1 / V2 智能解密 |
| 密钥提取 | `src/wx_mp_catcher/decrypt/key_finder.py` | Windows 进程内存扫描 |
| 进程跟踪 | `src/wx_mp_catcher/tracker/miniprogram.py` | WeChatAppEx AppID + 会话 |
| 去重 | `src/wx_mp_catcher/pipeline/dedup.py` | SQLite SHA256 |
| 分类 | `src/wx_mp_catcher/pipeline/classifier.py` | 小程序/日期/会话 |
| 导出 | `src/wx_mp_catcher/pipeline/exporter.py` | 写入输出目录 |
| 监听 | `src/wx_mp_catcher/watcher/` | watchdog 多目录递归 |
| 服务 | `src/wx_mp_catcher/service.py` | 编排启动/停止 |
| GUI | `src/wx_mp_catcher/ui/` | 托盘、设置、首次向导 |
| 入口 | `src/wx_mp_catcher/__main__.py` | `--cli` / GUI 双模式 |
| 打包 | `build/wx_mp_catcher.spec` | PyInstaller 单 exe |

### 技术决策
- Python 3.11 + PySide6 + watchdog + pycryptodome
- V2 密钥需一次性从微信进程内存提取，支持手动粘贴 fallback
- 默认「仅保存启动后新文件」，避免历史缓存洪水

### 测试
- `tests/test_decrypt_xor.py` — XOR/明文解密
- `tests/test_classifier.py` — 分类路径
- `tests/test_paths.py` — AppID 路径解析

### 打包
- `build/wx_mp_catcher.spec` — PyInstaller 目录模式（含 PySide6 插件过滤）
- `build/installer.iss` — Inno Setup 安装程序脚本
- `build/build_installer.ps1` — 一键构建 `WxMpCatcher-Setup-0.1.0.exe`
- `build/build.bat` — 双击构建入口
- `build/install_portable.ps1` — 无 Inno Setup 时的备用安装
- `assets/icon.ico` — 应用与安装包图标
- `.github/workflows/build-windows.yml` — CI 自动构建

### 安装包产物
- **正式安装包**: `dist/WxMpCatcher-Setup-0.1.0.exe`（Inno Setup，需 Windows 构建）
- **便携版目录**: `dist/wx-mp-catcher/`（PyInstaller 输出）

### 测试结果 (Linux 开发机)
- `pytest tests/ -v` — 9 passed
- PyInstaller spec 验证通过（Linux 侧构建 dist/wx-mp-catcher/）

### 待 Windows 实机验证
- Inno Setup 安装包完整流程
- 内存密钥提取成功率
- 杀软兼容性
