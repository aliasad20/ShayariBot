#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "============================================================"
echo " ShayariBot Linux Setup Script (Docker)"
echo "============================================================"
echo ""

echo "[1/4] Building Main Application Environment (.venv)..."
if [ ! -d ".venv" ]; then
    echo "Creating .venv with Python 3.13..."
    python3.13 -m venv .venv
fi
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
python backend/ingest.py
deactivate

echo ""
echo "[2/4] Building Isolated TTS Microservice (.venv_tts)..."
if [ ! -d ".venv_tts" ]; then
    echo "Creating .venv_tts with Python 3.10..."
    python3.10 -m venv .venv_tts
fi
source .venv_tts/bin/activate
echo "Installing Voice AI (This may take a while)..."
pip install --no-cache-dir -r requirements_tts.txt
deactivate

echo ""
echo "============================================================"
echo " Setup complete! The application is ready to run."
echo "============================================================"
