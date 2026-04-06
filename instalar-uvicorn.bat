@echo off
echo ========================================
echo  INSTALAR UVICORN - Prospecta HUB
echo ========================================
echo.

cd /d "%~dp0backend"

echo Verificando ambiente virtual...
if not exist "venv" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat ou fix-backend.bat primeiro
    pause
    exit /b 1
)

echo [OK] Ambiente virtual encontrado
echo.

echo Instalando uvicorn...
venv\Scripts\python.exe -m pip install uvicorn[standard]

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar uvicorn
    pause
    exit /b 1
)

echo.
echo Verificando instalacao...
venv\Scripts\python.exe -m pip show uvicorn

if errorlevel 1 (
    echo.
    echo [ERRO] uvicorn NAO foi instalado corretamente
    pause
    exit /b 1
)

echo.
echo ========================================
echo  UVICORN INSTALADO COM SUCESSO!
echo ========================================
echo.
echo Agora execute: start-backend.bat
echo.
pause
