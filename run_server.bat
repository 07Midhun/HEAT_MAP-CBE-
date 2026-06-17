@echo off
cd /d "%~dp0"
if not exist "frontend\dist\index.html" (
  echo Building React frontend...
  call build_frontend.bat
)
call venv\Scripts\activate.bat
echo Starting local web server at http://127.0.0.1:5000
python app.py
