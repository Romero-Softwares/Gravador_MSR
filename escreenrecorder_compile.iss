[Setup]
AppName=Gravador MSR
AppVersion=2.0
DefaultDirName={autopf}\GravadorPro
DefaultGroupName=Gravador Pro
OutputDir=.\Output
OutputBaseFilename=Setup_Merotec_recorder
Compression=lzma
SolidCompression=yes
; Necessário para criar pasta no C: e editar Variáveis de Ambiente
PrivilegesRequired=admin
SetupIconFile=C:\Users\Merotec\Desktop\Screenrecorder\icone.ico
UninstallDisplayIcon={app}\icone.ico

[Files]
; O executável do seu programa Python
Source: "C:\Users\Merotec\Desktop\Screenrecorder\dist\Merotec_recorder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Users\Merotec\Desktop\Screenrecorder\icone.ico"; DestDir: "{app}"; Flags: ignoreversion
; A sua pasta do FFmpeg que vai junto no pacote
; O DestDir "C:\ffmpeg" garante que ela vá para a raiz do disco C
Source: "C:\Users\Merotec\Desktop\Screenrecorder\ffmpeg\*"; DestDir: "C:\ffmpeg"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar
Name: "{group}\Gravador MSR"; Filename: "{app}\Merotec_recorder.exe"; IconFilename: "{app}\icone.ico"
; Atalho na Área de Trabalho
Name: "{autodesktop}\Gravador MSR"; Filename: "{app}\Merotec_recorder.exe"; IconFilename: "{app}\icone.ico"

[Registry]
; Versão simplificada em linha única para evitar erro de parâmetro Root
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};C:\ffmpeg"; Check: NeedsAddPath('C:\ffmpeg')

[Code]
// Função para evitar caminhos duplicados no PATH
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(Uppercase(Param), Uppercase(OrigPath)) = 0;
end;