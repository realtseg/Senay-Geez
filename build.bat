@echo off
title Building Text Substituter Portable EXE
echo ===============================================
echo Text Substituter Portable Builder
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Installing required packages...
echo.

REM Install all required packages
pip install keyboard psutil Pillow pyinstaller pywin32

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install required packages!
    echo Try running as Administrator: Right-click -> Run as Administrator
    pause
    exit /b 1
)

echo.
echo All required packages installed successfully!
echo.

REM Create dist directory if it doesn't exist
if not exist "dist" mkdir dist

REM Build the main text substituter
echo ===============================================
echo Building Text Substituter Main...
echo ===============================================
pyinstaller --onefile --noconsole --name "TextSubstituter" ^
--hidden-import=keyboard._winkeyboard ^
--hidden-import=win32timezone ^
--add-data "config.csv;." ^
text_substituter.py

if errorlevel 1 (
    echo ERROR: Failed to build Text Substituter!
    echo Trying alternative build method...
    
    REM Try simpler build command
    pyinstaller --onefile --noconsole --name "TextSubstituter" text_substituter.py
    
    if errorlevel 1 (
        echo.
        echo ERROR: Build failed completely!
        echo Please check your Python installation.
        pause
        exit /b 1
    )
)

REM Build the toggle overlay
echo.
echo ===============================================
echo Building Toggle Overlay...
echo ===============================================
pyinstaller --onefile --noconsole --name "TextSubToggle" ^
--hidden-import=win32timezone ^
--hidden-import=PIL._tkinter_finder ^
--add-data "blue.png;." ^
--add-data "white.png;." ^
--add-data "config.csv;." ^
toggle_display.py

if errorlevel 1 (
    echo ERROR: Failed to build Toggle Overlay!
    echo Trying alternative build method...
    
    REM Try simpler build command
    pyinstaller --onefile --noconsole --name "TextSubToggle" toggle_display.py
    
    if errorlevel 1 (
        echo ERROR: Toggle overlay build failed!
    )
)

REM Create a combined launcher
echo.
echo ===============================================
echo Creating Portable Package...
echo ===============================================

REM Create a launcher batch file for easy use
echo @echo off > "dist\Start Text Substituter.bat"
echo echo Starting Text Substituter... >> "dist\Start Text Substituter.bat"
echo echo Press PAGE UP to toggle substitution >> "dist\Start Text Substituter.bat"
echo echo Overlay will show status for 2 seconds >> "dist\Start Text Substituter.bat"
echo echo. >> "dist\Start Text Substituter.bat"
echo echo Close this window to exit >> "dist\Start Text Substituter.bat"
echo echo. >> "dist\Start Text Substituter.bat"
echo TextSubToggle.exe >> "dist\Start Text Substituter.bat"
echo pause >> "dist\Start Text Substituter.bat"

REM Copy config file to dist
if exist "config.csv" copy "config.csv" "dist\"
if exist "blue.png" copy "blue.png" "dist\"
if exist "white.png" copy "white.png" "dist\"

REM Create README file
echo Text Substituter - Portable Version > "dist\README.txt"
echo =============================================== >> "dist\README.txt"
echo. >> "dist\README.txt"
echo USAGE INSTRUCTIONS: >> "dist\README.txt"
echo 1. Run "Start Text Substituter.bat" to start the program >> "dist\README.txt"
echo 2. Press PAGE UP key to toggle text substitution ON/OFF >> "dist\README.txt"
echo 3. A small overlay will appear near your taskbar showing status >> "dist\README.txt"
echo 4. Blue icon = RUNNING, White icon = STOPPED >> "dist\README.txt"
echo. >> "dist\README.txt"
echo FEATURES: >> "dist\README.txt"
echo - Type Amharic characters using Latin keyboard >> "dist\README.txt"
echo - Works in any application >> "dist\README.txt"
echo - No installation required >> "dist\README.txt"
echo - Portable - can run from USB drive >> "dist\README.txt"
echo. >> "dist\README.txt"
echo CUSTOMIZATION: >> "dist\README.txt"
echo Edit config.csv to add your own text substitutions >> "dist\README.txt"
echo Format: latin_text,ethiopic_text >> "dist\README.txt"
echo Example: h,ሀ >> "dist\README.txt"
echo. >> "dist\README.txt"
echo TROUBLESHOOTING: >> "dist\README.txt"
echo - Run as Administrator if it doesn't work in some programs >> "dist\README.txt"
echo - Make sure PAGE UP key is not used by other applications >> "dist\README.txt"
echo. >> "dist\README.txt"

echo.
echo ===============================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ===============================================
echo.
echo Created files in 'dist' folder:
echo.
if exist "dist\TextSubstituter.exe" echo   TextSubstituter.exe     - Main program
if exist "dist\TextSubToggle.exe" echo   TextSubToggle.exe       - Toggle controller with overlay
if exist "dist\Start Text Substituter.bat" echo   "Start Text Substituter.bat" - Easy launcher
if exist "dist\config.csv" echo   config.csv              - Your substitutions
if exist "dist\README.txt" echo   README.txt              - Instructions
echo.
echo TO USE ON OTHER COMPUTERS:
echo 1. Copy the entire 'dist' folder to the other computer
echo 2. Run "Start Text Substituter.bat"
echo 3. No installation required!
echo.
echo Press any key to open the dist folder...
pause >nul

REM Open the dist folder
if exist "dist" start dist

echo.
echo Done! Your portable Text Substituter is ready.
pause