# Gravador MSR

Aplicativo desktop em Python para gravacao de tela, audio e camera, empacotado com PyInstaller.

## Requisitos

- Windows
- Python com ambiente virtual em `.venv` ou `venv`
- Dependencias do projeto ja instaladas no ambiente virtual
- Pasta `ffmpeg` no diretorio raiz do projeto, contendo o executavel `ffmpeg.exe`
- O FFmpeg deve ser compilado/empacotado junto com o aplicativo, pois e dependencia necessaria para decodificacao e processamento dos videos

## Executar em desenvolvimento

Use o atalho do projeto:

```bat
run_project.bat
```

Ou execute diretamente com o Python do ambiente virtual:

```bat
.venv\Scripts\python.exe main.py
```

## Gerar build

O comando usado para empacotar esta em `params_compile_recorder.txt`.

```bat
.venv\Scripts\python.exe -m PyInstaller --noconsole --onedir --clean --uac-admin --name "Merotec_recorder" --icon="icone.ico" --add-data "icone.ico;." --copy-metadata imageio --copy-metadata moviepy --collect-all customtkinter --collect-all pyautogui --collect-all PIL --collect-all moviepy --collect-all imageio --hidden-import=proglog --hidden-import=imageio_ffmpeg --paths "modules" main.py
```

## Estrutura principal

- `main.py`: interface e fluxo principal do gravador.
- `modules/app_config.py`: caminhos e configuracoes padrao.
- `modules/recorder_engine.py`: motor de gravacao.
- `run_project.bat`: inicializacao local usando ambiente virtual.
- `params_compile_recorder.txt`: comando de build com PyInstaller.

