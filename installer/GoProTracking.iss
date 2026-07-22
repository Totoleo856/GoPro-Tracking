; Script Inno Setup pour GoPro Cinema Tracker.
; Prérequis : avoir buildé l'app au préalable avec PyInstaller (dossier dist\GoProTracking\
; à la racine du projet, cf. commande dans le README) avant de compiler cet installeur.
;
; Penser à mettre à jour MyAppVersion ci-dessous en même temps que version.py à chaque
; nouvelle version.

#define MyAppName "GoPro Cinema Tracker"
#define MyAppVersion "1.11.0"
#define MyAppPublisher "LTT"
#define MyAppExeName "GoProTracking.exe"

; Identifiant fixe (ne jamais changer) : permet à Inno Setup de reconnaître les mises à
; jour d'une même app plutôt que d'installer une deuxième copie à côté.
#define MyAppId "{{6F2B2C6E-6C1E-4E9C-9C7F-2B7B6C7B0A11}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
SetupIconFile=..\assets\icon.ico
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Pas besoin de droits admin : installation dans le profil de l'utilisateur courant si
; celui-ci n'est pas administrateur (pratique pour une diffusion interne en studio).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline dialog
OutputDir=Output
OutputBaseFilename=GoProCinemaTracker-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis supplémentaires :"

[Files]
Source: "..\dist\GoProTracking\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent
