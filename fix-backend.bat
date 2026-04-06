@echo off
echo ========================================
echo  CORRIGIR BACKEND - Prospecta HUB
echo ========================================
echo.

echo Este script vai reinstalar todas as dependencias do backend
echo.
pause

cd backend

echo [1/5] Ativando ambiente virtual...
call venv\Scripts\activate

if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual
    echo Recriando ambiente virtual...
    rmdir /s /q venv
    python -m venv venv
    call venv\Scripts\activate
)

echo [OK] Ambiente virtual ativado
echo.

echo [2/5] Atualizando pip...
python -m pip install --upgrade pip
echo.

echo [3/5] Instalando dependencias principais...
pip install fastapi uvicorn python-dotenv httpx pydantic supabase
echo.

echo [4/5] Instalando Playwright...
pip install playwright
python -m playwright install chromium
echo.

echo [5/5] Instalando dependencias restantes...
pip install -r requirements.txt
echo.

echo ========================================
echo  INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Agora execute: start-backend.bat
echo.
pause
