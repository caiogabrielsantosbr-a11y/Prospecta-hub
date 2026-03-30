@echo off
echo ========================================
echo   Plataforma Prospect - Iniciando...
echo ========================================
echo.

REM Verifica se o venv existe, se nao, roda setup
if not exist "backend\venv\" (
    echo [SETUP] Primeira execucao detectada. Instalando dependencias...
    call npm run setup
    echo.
)

REM Verifica se node_modules existe na raiz
if not exist "node_modules\" (
    echo [SETUP] Instalando concurrently...
    call npm install
    echo.
)

echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Pressione Ctrl+C para parar os servidores.
echo ========================================
echo.

npm run dev
