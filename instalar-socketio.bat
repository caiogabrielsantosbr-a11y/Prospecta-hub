@echo off
echo ========================================
echo  INSTALAR SOCKETIO - Prospecta HUB
echo ========================================
echo.

cd /d "%~dp0backend"

echo Instalando python-socketio...
venv\Scripts\python.exe -m pip install python-socketio

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar python-socketio
    pause
    exit /b 1
)

echo.
echo Verificando instalacao...
venv\Scripts\python.exe -c "import socketio; print('socketio OK')"

if errorlevel 1 (
    echo.
    echo [ERRO] socketio NAO foi instalado corretamente
    pause
    exit /b 1
)

echo.
echo ========================================
echo  SOCKETIO INSTALADO COM SUCESSO!
echo ========================================
echo.
echo Agora execute: start-backend.bat
echo.
pause
