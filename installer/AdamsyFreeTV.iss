#ifndef AppName
  #define AppName "Adamsy Free TV"
#endif
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef AppPublisher
  #define AppPublisher "AdabTech"
#endif
#ifndef StagingDir
  #error "StagingDir define is required."
#endif
#ifndef OutputDir
  #error "OutputDir define is required."
#endif

[Setup]
AppId={{7D546B94-065D-4A84-AE55-C9261F7B2BF2}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=Adamsy-Free-TV-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\dist\VirtualTV.exe
SetupIconFile={#StagingDir}\adamsy-free-tv.ico
WizardImageFile={#StagingDir}\adamsy-free-tv-wizard.png
WizardSmallImageFile={#StagingDir}\adamsy-free-tv-wizard-small.png
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "{#StagingDir}\VirtualTV.exe"; DestDir: "{app}\dist"; Flags: ignoreversion
Source: "{#StagingDir}\tv_channels.json"; DestDir: "{app}\dist"; Flags: onlyifdoesntexist
Source: "{#StagingDir}\start_tv_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#StagingDir}\stop_tv_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#StagingDir}\stop_tv_app.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "{#StagingDir}\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\start_tv_app.bat"; WorkingDir: "{app}"; IconFilename: "{app}\dist\VirtualTV.exe"; Comment: "Launch {#AppName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\start_tv_app.bat"; WorkingDir: "{app}"; IconFilename: "{app}\dist\VirtualTV.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\start_tv_app.bat"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
function IsVlcInstalled: Boolean;
begin
  Result :=
    FileExists(ExpandConstant('{pf}\VideoLAN\VLC\vlc.exe')) or
    FileExists(ExpandConstant('{pf32}\VideoLAN\VLC\vlc.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and not IsVlcInstalled then
  begin
    MsgBox(
      'VLC media player was not detected. Install VLC before launching Adamsy Free TV.',
      mbInformation,
      MB_OK
    );
  end;
end;
