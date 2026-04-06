@echo off
echo ========================================
echo  DIAGNOSTICO - Prospecta HUB
echo ========================================
echo.

echo Verificando instalacoes...
echo.

REM Verificar Python
echo [1/5] Verificando Python...
python --version 2>nul
if errorlevel 1 (
    echo [X] Python NAO encontrado
    echo     Instale Python 3.11+ de https://www.python.org/downloads/
    echo     IMPORTANTE: Marque "Add Python to PATH" durante instalacao
) else (
    echo [OK] Python instalado
)
echo.

REM Verificar Node.js
echo [2/5] Verificando Node.js...
node --version 2>nul
if errorlevel 1 (
    echo [X] Node.js NAO encontrado
    echo     Instale Node.js 18+ de https://nodejs.org/
) else (
    echo [OK] Node.js instalado
)
echo.

REM Verificar ambiente virtual Python
echo [3/5] Verificando ambiente virtual Python...
if exist "backend\venv\" (
    echo [OK] Ambiente virtual existe
) else (
    echo [X] Ambiente virtual NAO encontrado
    echo     Execute install.bat para criar
)
echo.

REM Verificar node_modules
echo [4/5] Verificando node_modules...
if exist "frontend\node_modules\" (
    echo [OK] Dependencias Node.js instaladas
) else (
    echo [X] Dependencias Node.js NAO instaladas
    echo     Execute install.bat para instalar
)
echo.

REM Verificar arquivos .env
echo [5/5] Verificando arquivos .env...
if exist "backend\.env" (
    echo [OK] backend\.env existe
) else (
    echo [!] backend\.env NAO encontrado
    echo     O backend pode nao funcionar sem credenciais
)

if exist "frontend\.env" (
    echo [OK] frontend\.env existe
) else (
    echo [!] frontend\.env NAO encontrado
    echo     O frontend pode nao funcionar sem configuracao
)
echo.

echo ========================================
echo  DIAGNOSTICO COMPLETO
echo ========================================
echo.
echo Se todos os itens estao [OK], execute start.bat
echo Se algum item esta [X], execute install.bat primeiro
echo.
pause
