; ==============================================================================
; 🌸 SANYYY WINDOWS INSTALLER CREATOR (Inno Setup 6 Script)
; ==============================================================================
; Compiles dist\Sanyyy\* into a 1-click Windows Installer Wizard (SanyyySetup.exe)
; Creates Desktop & Start Menu Shortcuts and sets up auto-start.
; ==============================================================================

#define MyAppName "Sanyyy AI Assistant"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Coursewaalah Private Limited"
#define MyAppExeName "Sanyyy.exe"

[Setup]
AppId={{D9B38A2F-814C-4E7B-A630-1A87E4C4B98D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Sanyyy
DefaultGroupName={#MyAppName}
OutputDir=..\output
OutputBaseFilename=SanyyySetup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Automatically launch Sanyyy when Windows starts"; GroupDescription: "Startup Options:"

[Files]
; Include all files from PyInstaller dist output
Source: "..\dist\Sanyyy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprogram}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
