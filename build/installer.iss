; Inno Setup 安装脚本 — 生成 WxMpCatcher-Setup.exe
; 编译: iscc build\installer.iss

#define MyAppName "微信小程序图片抓取工具"
#define MyAppNameEn "WxMpCatcher"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "WxMpCatcher"
#define MyAppExeName "wx-mp-catcher.exe"
#define MyAppURL "https://github.com/local/wx-mp-catcher"

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
LicenseFile=..\assets\LICENSE.txt
InfoBeforeFile=..\assets\INSTALL_README.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "startup"; Description: "开机自动启动（登录后运行）"; GroupDescription: "其他:"; Flags: unchecked

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
