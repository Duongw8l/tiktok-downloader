@echo off
cd /d "%~dp0"
echo === Tao icon ===
venv\Scripts\python.exe create_icon.py
echo.
echo === Build TikSnap.exe ===
venv\Scripts\pyinstaller.exe --noconfirm TikSnap.spec
if errorlevel 1 (
    echo Build that bai!
    pause
    exit /b 1
)
if not exist "dist\downloads" mkdir "dist\downloads"
copy /Y tiksnap.ico dist\tiksnap.ico >nul

echo.
echo === Tao shortcut Desktop ===
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$exe = Join-Path '%CD%' 'dist\TikSnap.exe';" ^
  "$ico = Join-Path '%CD%' 'tiksnap.ico';" ^
  "$desk = [Environment]::GetFolderPath('Desktop');" ^
  "$w = New-Object -ComObject WScript.Shell;" ^
  "$s = $w.CreateShortcut((Join-Path $desk 'TikSnap.lnk'));" ^
  "$s.TargetPath = $exe;" ^
  "$s.WorkingDirectory = (Join-Path '%CD%' 'dist');" ^
  "$s.IconLocation = $ico + ',0';" ^
  "$s.Description = 'TikSnap - Tai TikTok khong watermark';" ^
  "$s.Save();" ^
  "Write-Host 'Shortcut Desktop OK'"

echo.
echo Xong!
echo File: %CD%\dist\TikSnap.exe
echo Shortcut: Desktop\TikSnap.lnk
pause
