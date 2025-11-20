@echo off
echo =========================================
echo      Building Senay Geez IME
echo =========================================

echo Installing dependencies...
pip install pyinstaller pynput pystray Pillow

echo.
echo Building EXE...
echo Note: Ensure 'app.ico' is in this folder for the icon to be applied.

pyinstaller --noconsole --onefile --icon=app.ico --name="Senay Geez" ethiopic_ime.py

echo.
echo =========================================
echo Build Complete!
echo.
echo You can find 'Senay Geez.exe' in the 'dist' folder.
echo.
echo IMPORTANT:
echo Copy 'Senay Geez.exe' from 'dist' to your deployment folder.
echo Ensure the following files are next to the .exe:
echo   - config.csv
echo   - splash.jpg
echo   - blue.png
echo   - white.png
echo   - app.ico (optional, for tray icon)
echo =========================================
pause