import os
import sys
import subprocess
import PyInstaller.__main__

def build_exe():
    print("Building Text Substituter Tray Controller...")
    
    # Build tray controller
    PyInstaller.__main__.run([
        'tray_controller.py',
        '--onefile',
        '--noconsole',  # Hide console window
        '--icon=blue.ico',  # Optional: add an icon file
        '--name=TextSubstituterTray',
        '--add-data=blue.png;.',
        '--add-data=white.png;.',
        '--hidden-import=pystray._win32',
        '--hidden-import=PIL._tkinter_finder',
    ])
    
    print("EXE built successfully!")
    print("Output: dist/TextSubstituterTray.exe")

if __name__ == "__main__":
    build_exe()