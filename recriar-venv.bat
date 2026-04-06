@echo off
echo ========================================
echo  RECRIAR AMBIENTE VIRTUAL - Prospecta HUB
echo ========================================
echo.

echo ATENCAO: Este script vai DELETAR o ambiente virtual atual
echo e criar um novo do zero.
echo.
pause

cd /d "%~dp0backend"

echo [1/5] Removendo ambiente virtual antigo...
if exist "venv" (
    rmdir /s /q venv
    echo [OK] Ambiente virtual removido
) else (
    echo [INFO] Nenhum ambiente virtual encontrado
)
echo.

echo [2/5] Criando novo ambiente virtual...
python -m venv venv

if errorlevel 1 (
    echo [ERRO] Falha ao criar ambiente virtual
    echo.
    echo Verifique se Python esta instalado:
    python --version
    echo.
    pause
    exit /b 1
)

echo [OK] Ambiente virtual criado
echo.

echo [3/5] Atualizando pip...
venv\Scripts\python.exe -m pip install --upgrade pip
echo.

echo [4/5] Instalando dependencias principais...
echo Instalando uvicorn...
venv\Scripts\python.exe -m pip install uvicorn[standard]

echo Instalando fastapi...
venv\Scripts\python.exe -m pip install fastapi

echo Instalando outras dependencias...
venv\Scripts\python.exe -m pip install python-dotenv httpx pydantic supabase

echo Instalando playwright...
venv\Scripts\python.exe -m pip install playwright
venv\Scripts\python.exe -m playwright install chromium
echo.

echo [5/5] Instalando dependencias do requirements.txt...
if exist "requirements.txt" (
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo [AVISO] requirements.txt nao encontrado
)
echo.

echo ========================================
echo  VERIFICANDO INSTALACAO
echo ========================================
echo.

echo Verificando Python do venv...
venv\Scripts\python.exe --version

echo.
echo Verificando uvicorn...
venv\Scripts\python.exe -m pip show uvicorn

if errorlevel 1 (
    echo.
    echo [ERRO] uvicorn NAO foi instalado!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  AMBIENTE VIRTUAL RECRIADO COM SUCESSO!
echo ========================================
echo.
echo Agora execute: start-backend.bat
echo.
pause
