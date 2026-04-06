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

REM Verificar se o activate.bat existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Arquivo activate.bat nao encontrado!
    echo Execute fix-backend.bat para recriar o ambiente virtual
    echo.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Verificar se ativou corretamente testando o caminho do Python
where python | findstr /i "venv" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Ambiente virtual pode nao ter sido ativado corretamente
    echo Usando Python do venv diretamente...
    echo.
)

echo [OK] Ambiente virtual ativado
echo.

REM Verificar se uvicorn está instalado
venv\Scripts\python.exe -m pip show uvicorn >nul 2>&1
if errorlevel 1 (
    echo [ERRO] uvicorn nao esta instalado!
    echo Execute fix-backend.bat para instalar as dependencias
    echo.
    pause
    exit /b 1
)

echo Iniciando servidor backend na porta 8000...
echo Pressione Ctrl+C para parar o servidor
echo.
echo ========================================
echo  IMPORTANTE - URL DO NGROK
echo ========================================
echo.
echo Para ver a URL publica do ngrok:
echo 1. Abra no navegador: http://localhost:4040
echo 2. Ou aguarde 5 segundos apos o backend iniciar
echo.
echo ========================================
echo.

REM Usar o Python do venv diretamente para garantir
venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

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
