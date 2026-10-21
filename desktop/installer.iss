[Setup]
AppId=FreeVoiceReadyVoice
AppName=FreeVoice
AppVersion=0.2.0
AppPublisher=FreeVoice contributors
DefaultDirName={localappdata}\Programs\FreeVoice
DefaultGroupName=FreeVoice
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=release
OutputBaseFilename=FreeVoice-Setup-Windows-x64
Compression=lzma2/fast
SolidCompression=yes
DiskSpanning=yes
DiskSliceSize=1900000000
SlicesPerDisk=1
LicenseFile=LICENSE
UninstallDisplayIcon={app}\FreeVoice.exe
WizardStyle=modern

[Files]
Source: "dist\FreeVoice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FreeVoice"; Filename: "{app}\FreeVoice.exe"
Name: "{autodesktop}\FreeVoice"; Filename: "{app}\FreeVoice.exe"

[Run]
Filename: "{app}\FreeVoice.exe"; Description: "Open FreeVoice"; Flags: nowait postinstall skipifsilent unchecked
