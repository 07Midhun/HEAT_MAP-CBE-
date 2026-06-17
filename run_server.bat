@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
if not exist "output\cbe_burning_heatmap.html" (
  echo Generating heat map HTML...
  python generate_heatmap.py --no-open -o output/cbe_burning_heatmap.html
)
echo Starting local web server at http://127.0.0.1:5000
python app.py
