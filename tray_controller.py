import sys
import os
import subprocess
import psutil
import time
from threading import Thread, Event
from infi.systray import SysTrayIcon

class TrayController:
    def __init__(self):
        self.script_path = "text_substituter.py"
        self.process = None
        self.is_running = False
        self.stop_event = Event()
        
        # Menu options
        self.menu_options = (
            ("Help", None, self.open_help),
            ("Settings", None, self.open_settings),
        )
        
        self.systray = None
        
    def check_script_running(self):
        """Check if the text substituter script is running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['cmdline'] and 
                    any('text_substituter.py' in cmd for cmd in proc.info['cmdline']) and
                    'python' in proc.info['name'].lower()):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def start_script(self):
        """Start the text substituter script"""
        try:
            if os.path.exists(self.script_path):
                python_exe = sys.executable
                self.process = subprocess.Popen([python_exe, self.script_path])
                self.is_running = True
                self.update_tray()
                print("Text Substituter started")
                return True
            else:
                print(f"Error: {self.script_path} not found!")
                return False
        except Exception as e:
            print(f"Error starting script: {e}")
            return False
    
    def stop_script(self):
        """Stop the text substituter script"""
        try:
            killed = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['cmdline'] and 
                        any('text_substituter.py' in cmd for cmd in proc.info['cmdline']) and
                        'python' in proc.info['name'].lower()):
                        proc.terminate()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if killed:
                time.sleep(1)
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['cmdline'] and 
                        any('text_substituter.py' in cmd for cmd in proc.info['cmdline']) and
                        'python' in proc.info['name'].lower()):
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            self.is_running = False
            self.update_tray()
            print("Text Substituter stopped")
            return True
            
        except Exception as e:
            print(f"Error stopping script: {e}")
            return False
    
    def update_tray(self):
        """Update the tray icon and hover text"""
        if self.systray:
            icon = "blue.ico" if self.is_running else "white.ico"
            hover_text = "Text Substituter - Running" if self.is_running else "Text Substituter - Stopped"
            self.systray.update(icon=icon, hover_text=hover_text)
    
    def on_quit_callback(self, systray):
        """Called when user wants to quit"""
        self.stop_event.set()
        self.stop_script()
    
    def on_left_click(self, systray):
        """Handle left click - toggle script"""
        print("Left click detected - toggling script")
        if self.is_running:
            self.stop_script()
        else:
            self.start_script()
    
    def open_help(self, systray):
        """Open help.pdf file"""
        try:
            help_file = "help.pdf"
            if os.path.exists(help_file):
                os.startfile(help_file)
            else:
                print("Help file not found: help.pdf")
        except Exception as e:
            print(f"Error opening help: {e}")
    
    def open_settings(self, systray):
        """Open config.csv file"""
        try:
            if os.path.exists("config.csv"):
                os.startfile("config.csv")
            else:
                print("Config file not found: config.csv")
        except Exception as e:
            print(f"Error opening settings: {e}")
    
    def monitor_script(self):
        """Monitor the script status"""
        while not self.stop_event.is_set():
            time.sleep(2)
            currently_running = self.check_script_running()
            if currently_running != self.is_running:
                self.is_running = currently_running
                self.update_tray()
    
    def run(self):
        """Start the tray controller"""
        # Check initial state
        self.is_running = self.check_script_running()
        
        # Create ICO files if they don't exist
        self.create_icons()
        
        # Start systray
        icon = "blue.ico" if self.is_running else "white.ico"
        hover_text = "Text Substituter - Running" if self.is_running else "Text Substituter - Stopped"
        
        self.systray = SysTrayIcon(
            icon,
            hover_text,
            self.menu_options,
            on_quit=self.on_quit_callback,
            default_menu_index=1
        )
        
        # Set left click handler
        self.systray._on_click = self.on_left_click
        
        # Start monitoring
        monitor_thread = Thread(target=self.monitor_script, daemon=True)
        monitor_thread.start()
        
        print("Text Substituter Tray Controller started")
        print("Left-click: Toggle on/off")
        print("Right-click: Menu options")
        
        self.systray.start()
    
    def create_icons(self):
        """Create ICO files from PNG if they don't exist"""
        try:
            from PIL import Image
            if not os.path.exists("blue.ico"):
                img = Image.open("blue.png")
                img.save("blue.ico")
            if not os.path.exists("white.ico"):
                img = Image.open("white.png")
                img.save("white.ico")
        except Exception as e:
            print(f"Error creating ICO files: {e}")

def main():
    # Hide console window
    try:
        import ctypes
        if os.name == 'nt':
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window:
                ctypes.windll.user32.ShowWindow(console_window, 0)
    except:
        pass
    
    controller = TrayController()
    controller.run()

if __name__ == "__main__":
    main()