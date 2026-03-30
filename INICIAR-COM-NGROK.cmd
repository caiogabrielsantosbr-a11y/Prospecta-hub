@echo off
setlocal enabledelayedexpansion

title Plataforma Prospect - Iniciar com ngrok

echo ========================================
echo  Plataforma Prospect - Iniciar com ngrok
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if ngrok exists locally
if exist "%SCRIPT_DIR%ngrok.exe" (
    echo [OK] ngrok encontrado localmente
    set "NGROK=%SCRIPT_DIR%ngrok.exe"
    goto :start_services
)

REM Check if ngrok is in PATH
where ngrok >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] ngrok encontrado no sistema
    set "NGROK=ngrok"
    goto :start_services
)

REM Download ngrok
echo [!] ngrok nao encontrado. Baixando...
echo.

REM Download ngrok zip
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip' -OutFile '%SCRIPT_DIR%ngrok.zip' -UseBasicParsing}"

if %ERRORLEVEL% NEQ 0 (
    echo [X] Falha ao baixar ngrok
    echo.
    echo Por favor, baixe manualmente de:
    echo https://ngrok.com/download
    echo.
    pause
    exit /b 1
)

echo Extraindo ngrok...
powershell -Command "& {Expand-Archive -Path '%SCRIPT_DIR%ngrok.zip' -DestinationPath '%SCRIPT_DIR%' -Force}"

if %ERRORLEVEL% NEQ 0 (
    echo [X] Falha ao extrair ngrok
    pause
    exit /b 1
)

REM Clean up zip file
del "%SCRIPT_DIR%ngrok.zip" >nul 2>nul

echo [OK] ngrok baixado e extraido com sucesso!
echo.
set "NGROK=%SCRIPT_DIR%ngrok.exe"

:start_services

REM Authenticate ngrok if not already authenticated
echo Verificando autenticacao do ngrok...
"%NGROK%" config check >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Configurando authtoken do ngrok...
    "%NGROK%" config add-authtoken 3BehjMz5YOrJDuwXyphGBhZXE48_3CzNy8U9SeDg96o9gEzoD
    if %ERRORLEVEL% EQU 0 (
        echo [OK] ngrok autenticado com sucesso!
    ) else (
        echo [!] Aviso: Falha ao autenticar ngrok automaticamente
        echo Tentando continuar mesmo assim...
    )
) else (
    echo [OK] ngrok ja esta autenticado
)
echo.

REM Check if backend venv exists
if not exist "%SCRIPT_DIR%backend\venv\Scripts\python.exe" (
    echo [X] Virtual environment nao encontrado em backend\venv
    echo.
    echo Execute primeiro:
    echo   cd backend
    echo   python -m venv venv
    echo   .\venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "%SCRIPT_DIR%frontend\node_modules" (
    echo [X] node_modules nao encontrado em frontend\
    echo.
    echo Execute primeiro:
    echo   cd frontend
    echo   npm install
    echo.
    pause
    exit /b 1
)

REM Start backend
echo [1/3] Iniciando backend...
start "Backend - Plataforma Prospect" cmd /k "cd /d "%SCRIPT_DIR%backend" && .\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend
echo Aguardando backend iniciar...
timeout /t 5 /nobreak >nul

REM Start ngrok tunnel
echo.
echo [2/3] Iniciando ngrok Tunnel...
echo.
echo ========================================
echo  IMPORTANTE: Copie a URL que aparecer!
echo  Exemplo: https://abc123.ngrok-free.app
echo ========================================
echo.

start "ngrok Tunnel - Plataforma Prospect" cmd /k "cd /d "%SCRIPT_DIR%" && "%NGROK%" http 8000"

REM Wait for tunnel
echo Aguardando tunnel iniciar...
timeout /t 5 /nobreak >nul

REM Start frontend
echo.
echo [3/3] Iniciando frontend...
start "Frontend - Plataforma Prospect" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm run dev"

echo.
echo ========================================
echo  Tudo iniciado!
echo ========================================
echo.
echo Proximos passos:
echo 1. Copie a URL do ngrok da janela que abriu
echo    Exemplo: https://abc123.ngrok-free.app
echo.
echo 2. Acesse: http://localhost:5173/admin/config
echo.
echo 3. Cole a URL do ngrok e clique em "Salvar e Testar"
echo.
echo DICA: Voce tambem pode ver a URL em: http://127.0.0.1:4040
echo.
echo Aguardando 8 segundos antes de abrir o navegador...
timeout /t 8 /nobreak >nul

REM Open ngrok dashboard and admin config
start http://127.0.0.1:4040
timeout /t 2 /nobreak >nul
start http://localhost:5173/admin/config

echo.
echo Para parar tudo, feche as 3 janelas que abriram.
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
