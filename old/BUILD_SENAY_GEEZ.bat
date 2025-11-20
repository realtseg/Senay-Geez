@echo off
title Building SENAY GEEZ
color 0A

echo Installing dependencies...
pip install pyinstaller keyboard psutil pillow pywin32

echo Cleaning old builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul

echo Building Senay Geez...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "Senay Geez" ^
  --add-data "blue.png;." ^
  --add-data "white.png;." ^
  --add-data "config.csv;." ^
  senay_geez.py

echo.
echo =====================================
echo   BUILD COMPLETE!
echo   dist\Senay Geez.exe is ready
echo =====================================
pause
