; sokonalysis Windows Installer Script
; Inno Setup Script for sokonalysis v3.5.0
; Place this file in your project root alongside build.bat

#define MyAppName "sokonalysis"
#define MyAppVersion "3.5.0"
#define MyAppPublisher "Kapasa Makasa University (KMU)"
#define MyAppCopyright "2024-2026 Kapasa Makasa University (KMU)"
#define MyAppURL "https://github.com/sokonalysis/sokonalysis"
#define MyAppExeName "sokonalysis.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{B8F5A3D2-7E9C-4F12-9A6B-3D8E5F1C2A7B}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright={#MyAppCopyright}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=The Cipher Toolkit Built For All Skill Levels
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

; Installation paths - installs for current user only (no admin required)
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} v{#MyAppVersion}

; Compression
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120,120
WizardResizable=yes

; Icons - Use small ICO file (must be 16x16 to 256x256)
SetupIconFile=assets\logo.ico

; Privileges - NO ADMIN REQUIRED
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible

; Require Windows 7 or later
MinVersion=6.1sp1

; Output directory
OutputDir=dist
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-windows-installer

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; Main executable (REQUIRED)
Source: "dist\{#MyAppName}-{#MyAppVersion}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Assets
Source: "dist\{#MyAppName}-{#MyAppVersion}\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation (skip if missing - no error)
Source: "dist\{#MyAppName}-{#MyAppVersion}\README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\{#MyAppName}-{#MyAppVersion}\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\{#MyAppName}-{#MyAppVersion}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\{#MyAppName}-{#MyAppVersion}\version.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; John the Ripper files (skip if missing - no error)
Source: "dist\{#MyAppName}-{#MyAppVersion}\JtR\*"; DestDir: "{app}\JtR"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Comment: "Launch {#MyAppName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Comment: "Uninstall {#MyAppName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Launch {#MyAppName}"

[Registry]
; Register as installed application (HKCU - no admin required)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "DisplayName"; ValueData: "{#MyAppName}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#MyAppVersion}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\{#MyAppExeName}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "QuietUninstallString"; ValueData: "{uninstallexe} /SILENT"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#MyAppURL}"
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: dword; ValueName: "NoModify"; ValueData: 1
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: dword; ValueName: "NoRepair"; ValueData: 1

[Run]
; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent shellexec; WorkingDir: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    Log('sokonalysis v{#MyAppVersion} installation completed successfully.');
  end;
end;

function InitializeSetup: Boolean;
begin
  Result := True;
end;

// Custom welcome page message
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption := 
    'This will install {#MyAppName} v{#MyAppVersion} on your computer.' + #13#10#13#10 +
    '{#MyAppName} is a cryptographic toolkit featuring:' + #13#10 +
    '• Symmetric & Asymmetric Cipher Tools' + #13#10 +
    '• Hash Cracking & Analysis' + #13#10 +
    '• CTF Challenge Tools' + #13#10 +
    '• Wi-Fi Security Analysis' + #13#10 +
    '• Steganography Tools' + #13#10 +
    '• Password Cracking (John the Ripper)' + #13#10 +
    '• And much more...' + #13#10#13#10 +
    'Created by Soko James & Rosaria Phiri' + #13#10 +
    '{#MyAppCopyright}' + #13#10#13#10 +
    'It is recommended that you close all other applications before continuing.';
  
  WizardForm.PageNameLabel.Font.Style := [fsBold];
  WizardForm.PageDescriptionLabel.Font.Color := clGray;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
end;