; Inno Setup 安装脚本 — 生成 WxMpCatcher-Setup.exe（简体中文界面）

#define MyAppName "微信小程序图片抓取工具"
#define MyAppNameEn "WxMpCatcher"
#define MyAppVersion "0.1.2"
#define MyAppPublisher "WxMpCatcher"
#define MyAppExeName "wx-mp-catcher.exe"
#define MyAppURL "https://github.com/DaWei2023/wechat-miniprogram-image-catcher"

[Setup]
AppId={{A8F3C2E1-9B4D-4A2F-8E7C-1D5F6A9B0C3E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppNameEn}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=WxMpCatcher-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile=..\assets\LICENSE_zh.txt
InfoBeforeFile=..\assets\INSTALL_README.txt
ShowLanguageDialog=no

[Languages]
Name: "chinesesimplified"; MessagesFile: "..\assets\innosetup\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加选项："; Flags: unchecked
Name: "startup"; Description: "开机自动启动（登录后运行）"; GroupDescription: "附加选项："; Flags: unchecked

[Files]
Source: "..\dist\wx-mp-catcher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppNameEn}"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "立即启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\wx-mp-catcher\logs"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

[CustomMessages]
chinesesimplified.LicenseLabel=安装前请阅读下列重要信息。
chinesesimplified.LicenseAccepted=我同意(&A)
chinesesimplified.LicenseNotAccepted=我不同意(&D)
