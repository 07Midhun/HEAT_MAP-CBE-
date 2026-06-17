@echo off
cd /d "%~dp0frontend"
call npm install
call npm run build
cd /d "%~dp0"
echo Frontend built to frontend\dist
