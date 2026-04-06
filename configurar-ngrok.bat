@echo off
echo ========================================
echo  CONFIGURAR NGROK - Prospecta HUB
echo ========================================
echo.

REM Verificar se ngrok.exe existe
if not exist "%~dp0ngrok.exe" (
    echo [ERRO] ngrok.exe nao encontrado!
    echo.
    echo Por favor, baixe o ngrok:
    echo 1. Acesse: https://ngrok.com/download
    echo 2. Baixe a versao para Windows
    echo 3. Extraia o ngrok.exe na pasta do projeto
    echo.
    pause
    exit /b 1
)

echo [OK] ngrok.exe encontrado
echo.

echo Para usar o ngrok, voce precisa de um authtoken GRATUITO.
echo.
echo Como obter seu authtoken:
echo 1. Acesse: https://ngrok.com/
echo 2. Crie uma conta (gratis)
echo 3. Va para: https://dashboard.ngrok.com/get-started/your-authtoken
echo 4. Copie seu authtoken
echo.
echo ========================================
echo.

set /p AUTHTOKEN="Cole seu authtoken aqui e pressione Enter: "

if "%AUTHTOKEN%"=="" (
    echo.
    echo [ERRO] Authtoken nao pode ser vazio!
    pause
    exit /b 1
)

echo.
echo Configurando ngrok...
"%~dp0ngrok.exe" config add-authtoken %AUTHTOKEN%

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao configurar ngrok
    pause
    exit /b 1
)

echo.
echo ========================================
echo  NGROK CONFIGURADO COM SUCESSO!
echo ========================================
echo.
echo Agora execute: start-backend.bat
echo.
echo Para ver a URL do ngrok:
echo - Abra no navegador: http://localhost:4040
echo.
pause
