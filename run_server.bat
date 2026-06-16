@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting local web server at http://127.0.0.1:5000
echo Note: Gunicorn does not work on Windows. Use this script locally.
echo Render deployment still uses: gunicorn app:app --bind 0.0.0.0:$PORT
python app.py
