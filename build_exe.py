import os
import PyInstaller.__main__

def build_exe():
    print("Building Text Substituter Tray Controller...")
    
    # Build tray controller
    PyInstaller.__main__.run([
        'tray_controller.py',
        '--onefile',
        '--noconsole',
        '--name=TextSubstituterTray',
        '--add-data=blue.png;.',
        '--add-data=white.png;.',
        '--hidden-import=pystray._win32',
        '--hidden-import=PIL._tkinter_finder',
    ])
    
    print("Tray Controller EXE built successfully!")
    print("Output: dist/TextSubstituterTray.exe")
    
    print("\nBuilding Text Substituter Main...")
    
    # Build main text substituter
    PyInstaller.__main__.run([
        'text_substituter.py',
        '--onefile',
        '--noconsole',
        '--name=TextSubstituter',
        '--hidden-import=keyboard._winkeyboard',
    ])
    
    print("Main Text Substituter EXE built successfully!")
    print("Output: dist/TextSubstituter.exe")

if __name__ == "__main__":
    build_exe()