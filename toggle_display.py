import sys
import os
import keyboard
import time
import psutil
import subprocess
from threading import Thread, Lock, Timer
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import win32gui
import win32con
import win32api

class TaskbarOverlay:
    def __init__(self):
        self.script_path = "text_substituter.py"
        self.process = None
        self.is_running = False
        self.lock = Lock()
        self.current_overlay = None
        
        # Create images if they don't exist
        self.create_images()
        
        # Register hotkey
        keyboard.add_hotkey('page up', self.toggle_script)
        
        print("Text Substituter Toggle with Overlay")
        print("=" * 45)
        print("Press PAGE UP to toggle text substitution")
        print("Overlay will show near taskbar for 2 seconds")
        print("=" * 45)
        
        # Check initial state
        self.is_running = self.check_script_running()
        print(f"Current status: {'RUNNING' if self.is_running else 'STOPPED'}")
    
    def create_images(self):
        """Create blue and white images if they don't exist"""
        # Create blue image
        if not os.path.exists("blue.png"):
            blue_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            blue_draw = ImageDraw.Draw(blue_image)
            blue_draw.ellipse([8, 8, 56, 56], fill=(0, 120, 255, 255))
            blue_image.save("blue.png")
        
        # Create white image  
        if not os.path.exists("white.png"):
            white_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            white_draw = ImageDraw.Draw(white_image)
            white_draw.ellipse([8, 8, 56, 56], fill=(200, 200, 200, 255))
            white_image.save("white.png")
        
        # Load images
        self.blue_image = Image.open("blue.png")
        self.white_image = Image.open("white.png")
    
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
                # Start without showing console window
                self.process = subprocess.Popen([python_exe, self.script_path], 
                                              creationflags=subprocess.CREATE_NO_WINDOW)
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
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['cmdline'] and 
                        any('text_substituter.py' in cmd for cmd in proc.info['cmdline']) and
                        'python' in proc.info['name'].lower()):
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            time.sleep(0.5)
            
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
    
    def get_taskbar_position(self):
        """Get taskbar position and size"""
        try:
            taskbar = win32gui.FindWindow("Shell_TrayWnd", None)
            if taskbar:
                rect = win32gui.GetWindowRect(taskbar)
                screen_width = win32api.GetSystemMetrics(0)
                
                # Simple detection - if taskbar is wide, it's bottom/top
                if rect[2] - rect[0] > screen_width / 2:
                    if rect[1] == 0:  # At top of screen
                        return "top", rect
                    else:  # At bottom
                        return "bottom", rect
                else:  # Side taskbar
                    if rect[0] == 0:  # Left side
                        return "left", rect
                    else:  # Right side
                        return "right", rect
        except:
            pass
        
        # Default to bottom taskbar
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        return "bottom", (0, screen_height-40, screen_width, screen_height)
    
    def show_overlay(self):
        """Show overlay image near taskbar clock"""
        try:
            # Close any existing overlay
            if self.current_overlay:
                try:
                    self.current_overlay.destroy()
                except:
                    pass
            
            # Get taskbar position
            position, taskbar_rect = self.get_taskbar_position()
            
            # Create overlay window
            overlay = tk.Toplevel()
            overlay.overrideredirect(True)
            overlay.attributes('-topmost', True)
            overlay.attributes('-alpha', 0.95)
            overlay.configure(bg='#2b2b2b')  # Dark background
            overlay.attributes("-transparentcolor", "#2b2b2b")  # Make this color transparent
            
            # Choose image based on state
            if self.is_running:
                image = self.blue_image
                status_text = "" 
                text_color = "#00ff00"  # Green text for running
            else:
                image = self.white_image
                status_text = "" 
                text_color = "#ff4444"  # Red text for stopped
            
            # Resize image
            image = image.resize((72, 72), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Create frame with background
            frame = tk.Frame(overlay, bg='#2b2b2b', relief='raised', bd=1)
            frame.pack(padx=0, pady=0)
            
            # Create label with image
            label = tk.Label(frame, image=photo, bg='#2b2b2b')
            label.image = photo
            label.pack(side='left', padx=5, pady=5)
            
            # Add status text
            text_label = tk.Label(frame, text=status_text, 
                                bg='#2b2b2b', fg=text_color,
                                font=('Arial', 10, 'bold'))
            text_label.pack(side='left', padx=5, pady=5)
            
            # Position near taskbar clock
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            
            if position == "bottom":
                x = screen_width - 200  # Right side offset
                y = taskbar_rect[1] - 100  # Above taskbar
            elif position == "top":
                x = screen_width - 200
                y = taskbar_rect[3] + 5
            elif position == "right":
                x = taskbar_rect[0] - 120
                y = screen_height - 150
            else:  # left
                x = taskbar_rect[2] + 5
                y = screen_height - 150
            
            overlay.geometry(f"+{x}+{y}")
            
            # Store reference
            self.current_overlay = overlay
            
            # Start fade out after 2 seconds
            self.start_fade_out(overlay)
            
        except Exception as e:
            print(f"Error showing overlay: {e}")
    
    def start_fade_out(self, window):
        """Start fade out animation"""
        def fade():
            try:
                current_alpha = window.attributes('-alpha')
                if current_alpha > 0.1:
                    new_alpha = current_alpha - 0.05
                    window.attributes('-alpha', new_alpha)
                    window.after(30, fade)
                else:
                    window.destroy()
                    if self.current_overlay == window:
                        self.current_overlay = None
            except:
                pass
        
        # Wait 2 seconds then start fade
        window.after(2000, fade)
    
    def toggle_script(self):
        """Toggle the script on/off and show overlay"""
        with self.lock:
            if self.is_running:
                self.stop_script()
            else:
                self.start_script()
            
            # Show overlay with new status
            self.show_overlay()
    
    def monitor_script(self):
        """Monitor the script status in background"""
        while True:
            time.sleep(3)
            currently_running = self.check_script_running()
            if currently_running != self.is_running:
                self.is_running = currently_running
                status = "RUNNING" if self.is_running else "STOPPED"
                print(f"Status changed: {status}")
    
    def run(self):
        """Start the controller"""
        # Start monitoring thread
        monitor_thread = Thread(target=self.monitor_script, daemon=True)
        monitor_thread.start()
        
        print("Toggle controller is running...")
        print("Press PAGE UP to toggle, overlay will show near taskbar")
        
        # Start tkinter main loop
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        try:
            root.mainloop()
        except KeyboardInterrupt:
            print("\nExiting...")
            self.stop_script()
            if self.current_overlay:
                try:
                    self.current_overlay.destroy()
                except:
                    pass

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
    
    controller = TaskbarOverlay()
    controller.run()

if __name__ == "__main__":
    main()