@echo off
echo ========================================
echo  INSTALAR TUDO - Prospecta HUB
echo ========================================
echo.
echo Este script instala TODAS as dependencias
echo.
pause

cd /d "%~dp0backend"

echo [1/3] Verificando ambiente virtual...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)
echo [OK] Ambiente virtual pronto
echo.

echo [2/3] Atualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip
echo.

echo [3/3] Instalando TODAS as dependencias...
echo.

echo Instalando dependencias uma por uma...
venv\Scripts\python.exe -m pip install "fastapi>=0.115"
venv\Scripts\python.exe -m pip install "uvicorn[standard]>=0.34"
venv\Scripts\python.exe -m pip install "python-socketio>=5.12"
venv\Scripts\python.exe -m pip install "httpx>=0.28"
venv\Scripts\python.exe -m pip install "sqlalchemy[asyncio]>=2.0"
venv\Scripts\python.exe -m pip install "aiosqlite>=0.21"
venv\Scripts\python.exe -m pip install "asyncpg>=0.29"
venv\Scripts\python.exe -m pip install "python-dotenv>=1.0"
venv\Scripts\python.exe -m pip install "openpyxl>=3.1"
venv\Scripts\python.exe -m pip install "aiofiles>=24.1"
venv\Scripts\python.exe -m pip install "playwright>=1.49"
venv\Scripts\python.exe -m pip install "beautifulsoup4>=4.12"
venv\Scripts\python.exe -m pip install "supabase>=2.0"

echo.
echo Instalando navegador Chromium...
venv\Scripts\python.exe -m playwright install chromium

echo.
echo ========================================
echo  VERIFICANDO INSTALACAO
echo ========================================
echo.

venv\Scripts\python.exe -c "import fastapi; print('[OK] fastapi')"
venv\Scripts\python.exe -c "import uvicorn; print('[OK] uvicorn')"
venv\Scripts\python.exe -c "import socketio; print('[OK] socketio')"
venv\Scripts\python.exe -c "import httpx; print('[OK] httpx')"
venv\Scripts\python.exe -c "import sqlalchemy; print('[OK] sqlalchemy')"
venv\Scripts\python.exe -c "import aiosqlite; print('[OK] aiosqlite')"
venv\Scripts\python.exe -c "import asyncpg; print('[OK] asyncpg')"
venv\Scripts\python.exe -c "import dotenv; print('[OK] python-dotenv')"
venv\Scripts\python.exe -c "import openpyxl; print('[OK] openpyxl')"
venv\Scripts\python.exe -c "import aiofiles; print('[OK] aiofiles')"
venv\Scripts\python.exe -c "import playwright; print('[OK] playwright')"
venv\Scripts\python.exe -c "import bs4; print('[OK] beautifulsoup4')"
venv\Scripts\python.exe -c "import supabase; print('[OK] supabase')"

echo.
echo ========================================
echo  INSTALACAO COMPLETA!
echo ========================================
echo.
echo Todas as dependencias foram instaladas.
echo.
echo Agora execute: start-backend.bat
echo.
pause
