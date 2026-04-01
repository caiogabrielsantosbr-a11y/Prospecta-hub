@echo off
start "ngrok" /min "%~dp0ngrok.exe" http 8000
cd /d "%~dp0backend"
call venv\Scripts\activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
