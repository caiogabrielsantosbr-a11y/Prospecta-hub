@echo off
chcp 65001 >nul
echo ========================================
echo   PROSPECTA HUB - Instalação Automática
echo ========================================
echo.

REM Verificar Python
echo [1/5] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale Python 3.11+ de: https://www.python.org/downloads/
    echo ⚠️  IMPORTANTE: Marque "Add Python to PATH" durante a instalação
    pause
    exit /b 1
)
echo ✓ Python encontrado
echo.

REM Verificar Node.js
echo [2/5] Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js não encontrado!
    echo.
    echo Por favor, instale Node.js 18+ de: https://nodejs.org/
    pause
    exit /b 1
)
echo ✓ Node.js encontrado
echo.

REM Instalar Backend
echo [3/5] Instalando Backend (Python)...
cd backend

REM Criar ambiente virtual
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente virtual e instalar dependências
echo Instalando dependências Python...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

REM Instalar Playwright
echo Instalando navegador Playwright...
playwright install chromium

REM Verificar .env
if not exist ".env" (
    echo.
    echo ⚠️  ATENÇÃO: Arquivo .env não encontrado!
    echo.
    echo Crie o arquivo backend\.env com:
    echo SUPABASE_URL=sua_url
    echo SUPABASE_KEY=sua_key
    echo SUPABASE_SERVICE_KEY=sua_service_key
    echo JWT_SECRET=sua_chave_secreta
    echo.
)

cd ..
echo ✓ Backend instalado
echo.

REM Instalar Frontend
echo [4/5] Instalando Frontend (React)...
cd frontend

echo Instalando dependências Node.js...
call npm install

REM Verificar .env
if not exist ".env" (
    echo.
    echo ⚠️  ATENÇÃO: Arquivo .env não encontrado!
    echo.
    echo Crie o arquivo frontend\.env com:
    echo VITE_SUPABASE_URL=sua_url
    echo VITE_SUPABASE_ANON_KEY=sua_key
    echo VITE_API_URL=http://localhost:8000
    echo.
)

cd ..
echo ✓ Frontend instalado
echo.

REM Finalizar
echo [5/5] Instalação concluída!
echo.
echo ========================================
echo   ✓ Instalação Completa!
echo ========================================
echo.
echo Próximos passos:
echo.
echo 1. Configure os arquivos .env:
echo    - backend\.env
echo    - frontend\.env
echo.
echo 2. Crie as tabelas no Supabase
echo    (veja INSTALACAO_RAPIDA.md)
echo.
echo 3. Execute o projeto:
echo    start.bat
echo.
echo ========================================
pause
