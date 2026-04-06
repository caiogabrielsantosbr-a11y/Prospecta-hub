@echo off
echo ========================================
echo  Iniciando Backend - Prospecta HUB
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.11+ e adicione ao PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verificar se o ambiente virtual existe
if not exist "%~dp0backend\venv" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute install.bat primeiro para instalar as dependencias
    echo.
    pause
    exit /b 1
)

echo [OK] Ambiente virtual encontrado
echo.

REM Verificar se o arquivo .env existe
if not exist "%~dp0backend\.env" (
    echo [AVISO] Arquivo .env nao encontrado em backend/
    echo O backend pode nao funcionar corretamente sem as credenciais
    echo.
)

REM Iniciar ngrok em segundo plano
echo Iniciando ngrok...
start "ngrok" /min "%~dp0ngrok.exe" http 8000
echo [OK] ngrok iniciado
echo.

REM Ativar ambiente virtual e iniciar backend
echo Ativando ambiente virtual...
cd /d "%~dp0backend"
call venv\Scripts\activate

if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual
    echo.
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado
echo.
echo Iniciando servidor backend na porta 8000...
echo Pressione Ctrl+C para parar o servidor
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

REM Se o uvicorn falhar, mostrar erro
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar o servidor backend
    echo.
    echo Possiveis causas:
    echo - Porta 8000 ja esta em uso
    echo - Dependencias nao instaladas corretamente
    echo - Erro no codigo do backend
    echo.
    pause
    exit /b 1
)
