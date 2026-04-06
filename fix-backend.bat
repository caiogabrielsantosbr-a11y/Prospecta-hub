@echo off
echo ========================================
echo  CORRIGIR BACKEND - Prospecta HUB
echo ========================================
echo.

echo Este script vai reinstalar todas as dependencias do backend
echo.
pause

cd /d "%~dp0backend"

echo [1/6] Verificando ambiente virtual...
if not exist "venv" (
    echo Ambiente virtual nao encontrado. Criando...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
)
echo [OK] Ambiente virtual existe
echo.

echo [2/6] Atualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip
echo.

echo [3/6] Instalando uvicorn (OBRIGATORIO)...
venv\Scripts\python.exe -m pip install uvicorn[standard]
echo.

echo [4/6] Instalando dependencias principais...
venv\Scripts\python.exe -m pip install fastapi python-dotenv httpx pydantic supabase
echo.

echo [5/6] Instalando Playwright...
venv\Scripts\python.exe -m pip install playwright
venv\Scripts\python.exe -m playwright install chromium
echo.

echo [6/6] Instalando dependencias restantes do requirements.txt...
venv\Scripts\python.exe -m pip install -r requirements.txt
echo.

echo ========================================
echo  VERIFICANDO INSTALACAO
echo ========================================
echo.

echo Verificando se uvicorn foi instalado...
venv\Scripts\python.exe -m pip show uvicorn
if errorlevel 1 (
    echo [ERRO] uvicorn NAO foi instalado!
    echo Tente instalar manualmente:
    echo   cd backend
    echo   venv\Scripts\python.exe -m pip install uvicorn
    pause
    exit /b 1
)

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Agora execute: start-backend.bat
echo.
pause
