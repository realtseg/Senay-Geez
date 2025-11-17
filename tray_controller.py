import sys
import os
import subprocess
import psutil
import time
from threading import Thread
from PIL import Image, ImageDraw
import pystray
import pystray._win32

class TrayController:
    def __init__(self):
        self.script_path = "text_substituter.py"
        self.process = None
        self.is_running = False
        
        # Create icons if they don't exist
        self.create_icons()
        
        # Create tray icon
        self.icon = pystray.Icon(
            "text_substituter",
            self.create_image("blue"),  # Start with blue (running)
            "Text Substituter - Running",
            menu=pystray.Menu(
                pystray.MenuItem("Toggle", self.toggle_script),
                pystray.MenuItem("Exit", self.exit_app)
            )
        )
    
    def create_icons(self):
        """Create blue and white icons if they don't exist"""
        if not os.path.exists("blue.png"):
            self.create_icon_image("blue.png", (0, 120, 255))
        if not os.path.exists("white.png"):
            self.create_icon_image("white.png", (200, 200, 200))
    
    def create_icon_image(self, filename, color):
        """Create a simple icon image with the given color"""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a circle with the specified color
        draw.ellipse([8, 8, 56, 56], fill=color)
        
        # Draw a 'T' in the center (for Text)
        draw.rectangle([28, 20, 36, 40], fill=(255, 255, 255))
        draw.rectangle([20, 20, 44, 28], fill=(255, 255, 255))
        
        image.save(filename)
    
    def create_image(self, color_type):
        """Create icon image based on color type"""
        if color_type == "blue":
            return Image.open("blue.png")
        else:
            return Image.open("white.png")
    
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
                # Use the same Python interpreter that's running this script
                python_exe = sys.executable
                self.process = subprocess.Popen([python_exe, self.script_path])
                self.is_running = True
                self.icon.icon = self.create_image("blue")
                self.icon.title = "Text Substituter - Running"
                print("Text Substituter started")
            else:
                print(f"Error: {self.script_path} not found!")
        except Exception as e:
            print(f"Error starting script: {e}")
    
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
            
            # Wait a bit for process to terminate
            time.sleep(1)
            
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
            self.icon.icon = self.create_image("white")
            self.icon.title = "Text Substituter - Stopped"
            print("Text Substituter stopped")
            
        except Exception as e:
            print(f"Error stopping script: {e}")
    
    def toggle_script(self, icon, item):
        """Toggle the script on/off"""
        if self.is_running or self.check_script_running():
            self.stop_script()
        else:
            self.start_script()
    
    def monitor_script(self):
        """Monitor the script status and update icon accordingly"""
        while True:
            time.sleep(2)  # Check every 2 seconds
            currently_running = self.check_script_running()
            
            if currently_running != self.is_running:
                self.is_running = currently_running
                if self.is_running:
                    self.icon.icon = self.create_image("blue")
                    self.icon.title = "Text Substituter - Running"
                else:
                    self.icon.icon = self.create_image("white")
                    self.icon.title = "Text Substituter - Stopped"
    
    def exit_app(self, icon, item):
        """Exit the application"""
        self.stop_script()
        icon.stop()
    
    def run(self):
        """Start the tray controller"""
        # Start monitoring thread
        monitor_thread = Thread(target=self.monitor_script, daemon=True)
        monitor_thread.start()
        
        # Check initial state
        if self.check_script_running():
            self.is_running = True
            self.icon.icon = self.create_image("blue")
            self.icon.title = "Text Substituter - Running"
        else:
            self.is_running = False
            self.icon.icon = self.create_image("white")
            self.icon.title = "Text Substituter - Stopped"
        
        # Run the tray icon
        print("Text Substituter Tray Controller started")
        print("Right-click the tray icon to toggle or exit")
        self.icon.run()

def main():
    # Hide console window (Windows only)
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