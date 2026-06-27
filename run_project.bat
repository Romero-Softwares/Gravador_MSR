@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    python main.py
    exit /b %errorlevel%
)

if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    python main.py
    exit /b %errorlevel%
)

echo ERRO: ambiente virtual do projeto nao encontrado.
echo Crie ou restaure uma pasta .venv ou venv dentro do projeto.
exit /b 1
