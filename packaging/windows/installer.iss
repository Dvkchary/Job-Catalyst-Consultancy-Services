; ==============================================================================
; JobCatalyst AI - Professional Enterprise Inno Setup Compiler Configuration
; ==============================================================================
; This script generates the standard enterprise-grade JobCatalystAI-Setup.exe
; installer supporting silent deployment, repair installations, and automatic updates.

#define AppName "JobCatalyst AI"
#define AppVersion "1.0.0-RC1"
#define AppPublisher "JobCatalyst Corporation"
#define AppURL "https://jobcatalyst.ai"
#define AppExeName "JobCatalystLauncher.exe"

[Setup]
; Unique App ID for upgrade and uninstall routines
AppId={{5E43C9A6-C6E8-41E2-A2F7-3C9A6FF7BA21}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/support
AppUpdatesURL={#AppURL}/updates
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
InfoBeforeFile=..\..\docs\INSTALLATION_GUIDE_RC1.md
OutputDir=..\..\dist-release\windows
OutputBaseFilename=JobCatalystAI-Setup
SetupIconFile=..\..\assets\favicon.ico
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Enterprise silent install parameters configuration
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
DisableReadyPage=no
DisableFinishedPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Launch JobCatalyst AI services on system startup"; GroupDescription: "System Services:"; Flags: unchecked

[Files]
; Primary application launch scripts and executables
Source: "..\..\dist-release\windows\JobCatalystLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\dist\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\nginx\*"; DestDir: "{app}\nginx"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\docker-compose.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\docker-compose.prod.yml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

; Offline bundled service dependencies (Embedded PostgreSQL, Redis, Python 64-bit binaries)
Source: "..\..\dependencies\windows\redis\*"; DestDir: "{app}\services\redis"; Flags: ignoreversion recursesubdirs createallsubdirs Check: IsOfflineInstaller
Source: "..\..\dependencies\windows\postgresql\*"; DestDir: "{app}\services\postgresql"; Flags: ignoreversion recursesubdirs createallsubdirs Check: IsOfflineInstaller
Source: "..\..\dependencies\windows\python\*"; DestDir: "{app}\services\python"; Flags: ignoreversion recursesubdirs createallsubdirs Check: IsOfflineInstaller

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Run]
; Run initialization scripts and start local docker containers or services
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Tear down background containers and services prior to files deletion
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -Command ""& '{app}\scripts\uninstall-cleanup.ps1'"""; Flags: runhidden

[Code]
var
  IsOfflineMode: Boolean;

function InitializeSetup(): Boolean;
begin
  // Set offline mode based on command-line parameter or file presence
  IsOfflineMode := CmdLineParamExists('/OFFLINE') or FileExists(ExpandConstant('{src}\dependencies.cab'));
  Result := True;
end;

function IsOfflineInstaller(): Boolean;
begin
  Result := IsOfflineMode;
end;

function CmdLineParamExists(const ParamName: string): Boolean;
var
  I: Integer;
begin
  Result := False;
  for I := 1 to ParamCount do
  begin
    if CompareText(ParamStr(I), ParamName) = 0 then
    begin
      Result := True;
      Break;
    end;
  end;
end;
