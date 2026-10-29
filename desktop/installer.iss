[Setup]
AppId=FemaleVocalIndic
AppName=FemaleVocal
AppVersion=0.3.0
AppPublisher=FreeVoice contributors
DefaultDirName={localappdata}\Programs\FemaleVocal
DefaultGroupName=FemaleVocal
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=release
OutputBaseFilename=FemaleVocal-Indic-Setup-Windows-x64
Compression=lzma2/fast
SolidCompression=yes
DiskSpanning=yes
DiskSliceSize=1900000000
SlicesPerDisk=1
LicenseFile=LICENSE
UninstallDisplayIcon={app}\FemaleVocalIndic.exe
WizardStyle=modern

[Files]
Source: "dist\FemaleVocalIndic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\FemaleVocal"; Filename: "{app}\FemaleVocalIndic.exe"
Name: "{autodesktop}\FemaleVocal"; Filename: "{app}\FemaleVocalIndic.exe"

[Run]
Filename: "{app}\FemaleVocalIndic.exe"; Description: "Open FemaleVocal"; Flags: nowait postinstall skipifsilent unchecked
