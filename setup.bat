@echo off
echo ============================================================
echo  ShayariBot Setup Script (Dual Environment Architecture)
echo ============================================================
echo.

echo [1/4] Building Main Application Environment (.venv)...
if not exist .venv (
    echo Creating .venv with default Python...
    py -m venv .venv
)
call .\.venv\Scripts\activate.bat
pip install -r requirements.txt
python backend\ingest.py
deactivate

echo.
echo [2/4] Building Isolated TTS Microservice (.venv_tts)...
if not exist .venv_tts (
    echo Creating .venv_tts with Python 3.10...
    py -3.10 -m venv .venv_tts
)
call .\.venv_tts\Scripts\activate.bat
echo Installing Voice AI (This may take a while)...
pip install -r requirements_tts.txt
deactivate

echo.
echo ============================================================
echo  Setup complete! Run the app with:
echo  .\.venv\Scripts\streamlit run app\main.py
echo ============================================================
pause
