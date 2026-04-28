#!/bin/bash
# HireWise Quick Start Script
set -e

echo "🧠 HireWise AI — Quick Start"
echo "==============================="

# Check Python
python3 --version || { echo "❌ Python 3 required"; exit 1; }
node --version || { echo "❌ Node.js required"; exit 1; }

# Backend setup
echo ""
echo "[1/4] Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --quiet

# .env setup
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  ⚠️  Created .env — add your ANTHROPIC_API_KEY if you have one (optional)"
fi

# Train ML model
echo ""
echo "[2/4] Training ML model..."
python ml/train.py

echo ""
echo "[3/4] Starting backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend setup
echo ""
echo "[4/4] Setting up and starting frontend on port 3000..."
cd ../frontend
npm install --silent
npm start &
FRONTEND_PID=$!

echo ""
echo "==============================="
echo "✅ HireWise is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo "==============================="

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
