@echo off
title Simple Text Substituter Builder
echo Installing dependencies...
pip install pyinstaller
pip install keyboard
pip install psutil
pip install Pillow
pip install pywin32

echo.
echo Building executable...
pyinstaller --onefile --noconsole --name "Senay-Geez" toggle_display.py

echo.
if exist "dist\Senay-Geez.exe" (
    echo SUCCESS: Built dist\EthiopicTextSub.exe
    echo Copy this file along with config.csv, blue.png, and white.png to other computers.
) else (
    echo ERROR: Build failed!
)

pause