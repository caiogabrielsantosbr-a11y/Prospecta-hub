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
venv\Scripts\python.exe -m pip install "uvicorn[standard]>=0.34"

echo Instalando fastapi...
venv\Scripts\python.exe -m pip install "fastapi>=0.115"

echo Instalando outras dependencias essenciais...
venv\Scripts\python.exe -m pip install python-dotenv httpx playwright beautifulsoup4 aiofiles openpyxl

echo Instalando supabase (pode demorar)...
venv\Scripts\python.exe -m pip install supabase --no-build-isolation

echo Instalando playwright browser...
venv\Scripts\python.exe -m playwright install chromium
echo.

echo [5/5] Instalando dependencias opcionais do requirements.txt...
if exist "requirements.txt" (
    echo Tentando instalar dependencias restantes...
    venv\Scripts\python.exe -m pip install -r requirements.txt --no-build-isolation 2>nul
    if errorlevel 1 (
        echo [AVISO] Algumas dependencias opcionais falharam, mas o essencial foi instalado
    )
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
