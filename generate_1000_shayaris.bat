@echo off
echo ============================================================
echo   ShayariBot — Dataset Generator Pipeline
echo ============================================================
echo.
echo Connecting to Gemini to fetch 1000 authentic shayaris...
echo This will take approximately 5-10 minutes. 
echo Do not close this window.
echo.

call c:\Users\aasad\Desktop\RAG_Project\.venv\Scripts\activate.bat
python C:\Users\aasad\.gemini\antigravity-ide\brain\7b32d18e-1219-40c9-9fef-60cfe7aaa1aa\scratch\generator.py

echo.
echo ============================================================
echo   Dataset generation complete!
echo   Rebuilding ChromaDB index...
echo ============================================================
python c:\Users\aasad\Desktop\RAG_Project\backend\ingest.py

echo.
echo Done! You can now restart Streamlit.
pause
