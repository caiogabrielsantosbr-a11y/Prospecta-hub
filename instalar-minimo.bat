@echo off
echo ========================================
echo  INSTALACAO MINIMA - Prospecta HUB
echo ========================================
echo.
echo Este script instala APENAS as dependencias essenciais
echo sem precisar de compiladores C++
echo.
pause

cd /d "%~dp0backend"

echo [1/4] Verificando ambiente virtual...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
)
echo [OK] Ambiente virtual pronto
echo.

echo [2/4] Atualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip
echo.

echo [3/4] Instalando dependencias essenciais...
echo.
echo - uvicorn (servidor web)
venv\Scripts\python.exe -m pip install "uvicorn[standard]"

echo - fastapi (framework web)
venv\Scripts\python.exe -m pip install fastapi

echo - python-dotenv (variaveis de ambiente)
venv\Scripts\python.exe -m pip install python-dotenv

echo - httpx (cliente HTTP)
venv\Scripts\python.exe -m pip install httpx

echo - python-socketio (WebSocket)
venv\Scripts\python.exe -m pip install python-socketio

echo - playwright (automacao navegador)
venv\Scripts\python.exe -m pip install playwright

echo - beautifulsoup4 (parser HTML)
venv\Scripts\python.exe -m pip install beautifulsoup4

echo - supabase (banco de dados)
venv\Scripts\python.exe -m pip install supabase

echo - openpyxl (Excel)
venv\Scripts\python.exe -m pip install openpyxl

echo - aiofiles (arquivos async)
venv\Scripts\python.exe -m pip install aiofiles
echo.

echo [4/4] Instalando navegador Chromium...
venv\Scripts\python.exe -m playwright install chromium
echo.

echo ========================================
echo  VERIFICANDO INSTALACAO
echo ========================================
echo.

echo Verificando uvicorn...
venv\Scripts\python.exe -c "import uvicorn; print('uvicorn OK')"

echo Verificando fastapi...
venv\Scripts\python.exe -c "import fastapi; print('fastapi OK')"

echo Verificando playwright...
venv\Scripts\python.exe -c "import playwright; print('playwright OK')"

echo Verificando supabase...
venv\Scripts\python.exe -c "import supabase; print('supabase OK')"

echo.
echo ========================================
echo  INSTALACAO MINIMA CONCLUIDA!
echo ========================================
echo.
echo Todas as dependencias essenciais foram instaladas.
echo.
echo Agora execute: start-backend.bat
echo.
pause
