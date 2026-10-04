; OvozYoz oʻrnatuvchisi — Inno Setup 6.3+ (admin ruxsatisiz, joriy foydalanuvchi uchun)
#define AppName "OvozYoz"
#ifndef AppVersion
  #define AppVersion "0.5"
#endif
#define Model "vosk-model-small-uz-0.22"

[Setup]
AppId={{8E5B1C2A-6F3D-4E7A-9B21-0A4C7D3E5F61}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Xudaykulov Uchqun Yunusovich
AppCopyright=© 2026 Xudaykulov Uchqun Yunusovich
VersionInfoVersion={#AppVersion}
; admin kerak emas: %LOCALAPPDATA%\Programs\OvozYoz ga oʻrnatiladi
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes
DisableDirPage=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\Output
OutputBaseFilename=OvozYoz-Setup-{#AppVersion}
SetupIconFile=..\assets\ovozyoz.ico
UninstallDisplayIcon={app}\OvozYoz.exe
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; ishlab turgan dasturni aniqlab, yopishni soʻraydi
AppMutex=Local\OvozYoz
CloseApplications=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Ish stolida yorliq yaratish"; GroupDescription: "Qoʻshimcha:"
Name: "autostart"; Description: "Windows bilan birga ishga tushirish"; GroupDescription: "Qoʻshimcha:"

[Files]
Source: "..\dist\OvozYoz\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\models\{#Model}\*"; DestDir: "{app}\{#Model}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\OvozYoz.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\OvozYoz.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\OvozYoz.exe"""; Tasks: autostart

[Run]
Filename: "{app}\OvozYoz.exe"; Description: "OvozYoz ni hozir ishga tushirish"; Flags: nowait postinstall skipifsilent
; avtomatik (jim) yangilanishdan keyin dasturni qayta ochish
Filename: "{app}\OvozYoz.exe"; Flags: nowait; Check: WizardSilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
// Oʻchirishda avtoyuklash yozuvini ham olib tashlash (dastur sozlamalaridan yoqilgan boʻlsa ham)
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', '{#AppName}');
end;
