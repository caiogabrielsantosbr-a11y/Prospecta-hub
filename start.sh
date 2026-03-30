#!/bin/bash
echo "========================================"
echo "  Plataforma Prospect - Iniciando..."
echo "========================================"
echo ""

# Verifica se o venv existe
if [ ! -d "backend/venv" ]; then
    echo "[SETUP] Primeira execucao detectada. Instalando dependencias..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python -m playwright install chromium
    cd ../frontend
    npm install
    cd ..
    npm install
    echo ""
fi

echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Pressione Ctrl+C para parar os servidores."
echo "========================================"
echo ""

npm run dev
