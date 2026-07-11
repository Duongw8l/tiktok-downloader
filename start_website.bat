@echo off
cd /d "%~dp0"
title TikSnap Website
echo ========================================
echo   TikSnap Website (iPhone / trinh duyet)
echo ========================================
echo.
echo 1) Dang mo server local...
echo 2) Tunnel public se hien link https://....trycloudflare.com
echo 3) Giữ cua so nay MO de website chay
echo 4) Desktop app TikSnap.exe van dung doc lap
echo.
echo Nhan Ctrl+C de tat website.
echo.

set TIKSNAP_DESKTOP=
set PORT=5000

start "TikSnap-Server" cmd /c "cd /d "%~dp0" && venv\Scripts\python.exe -c "from waitress import serve; from app import app; serve(app, host='0.0.0.0', port=5000, threads=4)""

timeout /t 3 /nobreak >nul

if not exist "tools\cloudflared.exe" (
  echo Dang tai cloudflared...
  mkdir tools 2>nul
  powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'tools\cloudflared.exe' -UseBasicParsing"
)

echo.
echo Dang tao link public...
tools\cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
