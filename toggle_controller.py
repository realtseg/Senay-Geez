import sys
import os
import keyboard
import time
import psutil
from threading import Thread, Lock
from PIL import Image, ImageDraw
import pystray

class ToggleController:
    def __init__(self):
        self.script_path = "text_substituter.py"
        self.process = None
        self.is_running = False
        self.tray_icon = None
        self.lock = Lock()
        
        # Create icons
        self.create_icons()
        
        # Register hotkey
        keyboard.add_hotkey('page up', self.toggle_script)
        
        print("Text Substituter Toggle Controller")
        print("=" * 40)
        print("Press PAGE UP to toggle text substitution on/off")
        print("Tray icon will show status (blue=running, white=stopped)")
        print("=" * 40)
        
        # Check initial state
        self.is_running = self.check_script_running()
        self.update_tray_icon()
    
    def create_icons(self):
        """Create blue and white icons"""
        # Blue icon (running)
        blue_image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        blue_draw = ImageDraw.Draw(blue_image)
        blue_draw.ellipse([2, 2, 14, 14], fill=(0, 120, 255))
        self.blue_icon = blue_image
        
        # White icon (stopped)
        white_image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        white_draw = ImageDraw.Draw(white_image)
        white_draw.ellipse([2, 2, 14, 14], fill=(200, 200, 200))
        self.white_icon = white_image
    
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
                print("✓ Text Substituter STARTED")
                return True
            else:
                print("✗ Error: text_substituter.py not found!")
                return False
        except Exception as e:
            print(f"✗ Error starting script: {e}")
            return False
    
    def stop_script(self):
        """Stop the text substituter script"""
        try:
            # Kill all python processes running the text substituter
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['cmdline'] and 
                        any('text_substituter.py' in cmd for cmd in proc.info['cmdline']) and
                        'python' in proc.info['name'].lower()):
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            time.sleep(0.5)
            
            # Force kill if still running
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['cmdline'] and 
                        any('text_substituter.py' in cmd for cmd in proc.info['cmdline']) and
                        'python' in proc.info['name'].lower()):
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            self.is_running = False
            print("✓ Text Substituter STOPPED")
            return True
            
        except Exception as e:
            print(f"✗ Error stopping script: {e}")
            return False
    
    def toggle_script(self):
        """Toggle the script on/off with Page Up key"""
        with self.lock:
            if self.is_running:
                self.stop_script()
            else:
                self.start_script()
            
            # Update tray icon to reflect new state
            self.update_tray_icon()
    
    def update_tray_icon(self):
        """Update or create tray icon based on current state"""
        if self.tray_icon:
            # Update existing icon
            if self.is_running:
                self.tray_icon.icon = self.blue_icon
                self.tray_icon.title = "Text Sub - RUNNING (Page Up to toggle)"
            else:
                self.tray_icon.icon = self.white_icon
                self.tray_icon.title = "Text Sub - STOPPED (Page Up to toggle)"
        else:
            # Create new tray icon
            icon = self.blue_icon if self.is_running else self.white_icon
            title = "Text Sub - RUNNING (Page Up to toggle)" if self.is_running else "Text Sub - STOPPED (Page Up to toggle)"
            
            self.tray_icon = pystray.Icon(
                "text_substituter",
                icon,
                title,
                menu=pystray.Menu(
                    pystray.MenuItem("Help", self.open_help),
                    pystray.MenuItem("Settings", self.open_settings),
                    pystray.MenuItem("Exit", self.exit_app)
                )
            )
            
            # Start the tray icon in a separate thread
            tray_thread = Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
    
    def open_help(self, icon, item):
        """Open help.pdf file"""
        try:
            help_file = "help.pdf"
            if os.path.exists(help_file):
                os.startfile(help_file)
            else:
                print("Help file not found: help.pdf")
        except Exception as e:
            print(f"Error opening help: {e}")
    
    def open_settings(self, icon, item):
        """Open config.csv file"""
        try:
            if os.path.exists("config.csv"):
                os.startfile("config.csv")
            else:
                print("Config file not found: config.csv")
        except Exception as e:
            print(f"Error opening settings: {e}")
    
    def exit_app(self, icon, item):
        """Exit the application"""
        print("Exiting Toggle Controller...")
        self.stop_script()
        if self.tray_icon:
            self.tray_icon.stop()
        os._exit(0)
    
    def monitor_script(self):
        """Monitor the script status in background"""
        while True:
            time.sleep(3)
            currently_running = self.check_script_running()
            if currently_running != self.is_running:
                self.is_running = currently_running
                self.update_tray_icon()
    
    def run(self):
        """Start the toggle controller"""
        # Start monitoring thread
        monitor_thread = Thread(target=self.monitor_script, daemon=True)
        monitor_thread.start()
        
        # Initial tray icon
        self.update_tray_icon()
        
        print("Toggle controller is running...")
        print("Current status: " + ("RUNNING" if self.is_running else "STOPPED"))
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.exit_app(None, None)

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
    
    # Import subprocess here to avoid issues
    import subprocess
    globals()['subprocess'] = subprocess
    
    controller = ToggleController()
    controller.run()

if __name__ == "__main__":
    main()