@echo off
echo Building Text Substituter Tray Controller...
pyinstaller --onefile --noconsole --name TextSubstituterTray --add-data "blue.png;." --add-data "white.png;." --hidden-import pystray._win32 --hidden-import PIL._tkinter_finder tray_controller.py
echo.
echo Build complete! Check dist folder for TextSubstituterTray.exe
pause