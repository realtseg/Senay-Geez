import sys
import os
import keyboard
import time
import csv
import psutil
import subprocess
from collections import deque
from threading import Lock, Thread, Timer
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import win32gui
import win32con
import win32api

class TextSubstituter:
    def __init__(self):
        self.substitutions = {}
        self.buffer = deque(maxlen=20)
        self.lock = Lock()
        self.enabled = True
        self.config_file = "config.csv"
        self.last_modified = 0
        self.typing_delay = 0.05
        self.suppress_keys = False
        self.pending_chars = []
        
        # Special key mappings
        self.special_keys = {
            'open bracket': '[',
            'close bracket': ']',
            'comma': ',',
            'period': '.',
            'slash': '/',
            'backslash': '\\',
            'semicolon': ';',
            'quote': "'",
            'grave': '`',
            'minus': '-',
            'equal': '='
        }
        
        # Load configuration from CSV
        self.load_config()
        
    def load_config(self):
        """Load substitutions from config.csv file only"""
        self.substitutions = {}
        
        if not os.path.exists(self.config_file):
            print(f"Error: {self.config_file} not found!")
            print("Please create config.csv with your substitutions in the format:")
            print("key,value")
            print("Example:")
            print("h,ሀ")
            print("hu,ሁ")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 2:
                        key = row[0].strip()
                        value = row[1].strip()
                        self.substitutions[key] = value
                
                print(f"Loaded {len(self.substitutions)} substitutions from {self.config_file}")
                self.last_modified = os.path.getmtime(self.config_file)
                
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def check_config_updates(self):
        """Check if config file has been modified and reload if necessary"""
        if os.path.exists(self.config_file):
            current_modified = os.path.getmtime(self.config_file)
            if current_modified > self.last_modified:
                print("Config file updated. Reloading substitutions...")
                self.load_config()
    
    def get_character_from_event(self, event):
        """Get the actual character from keyboard event, handling all special keys"""
        try:
            # Handle special keys
            if event.name in self.special_keys:
                return self.special_keys[event.name]
            
            # Handle regular characters
            elif hasattr(event, 'name') and event.name and len(event.name) == 1 and event.name.isprintable():
                return event.name
            
            # Handle shift-modified characters
            elif hasattr(event, 'scan_code'):
                if keyboard.is_pressed('shift'):
                    # Shifted characters
                    shift_map = {
                        '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                        '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                        '`': '~', '-': '_', '=': '+', '[': '{', ']': '}',
                        '\\': '|', 'semicolon': ':', 'quote': '"', 'comma': '<', 'period': '>', 'slash': '?'
                    }
                    if event.name in shift_map:
                        return shift_map[event.name]
                
                # Handle bracket keys specifically
                if event.name == 'open bracket':
                    return '['
                elif event.name == 'close bracket':
                    return ']'
                    
        except Exception as e:
            print(f"Error getting character: {e}")
        
        return None
    
    def check_substitution(self):
        """Check if buffer ends with any substitution key"""
        with self.lock:
            if not self.buffer:
                return None, None
                
            buffer_str = ''.join(self.buffer)
            
            # Sort by length (longest first) to prioritize longer matches
            sorted_subs = sorted(self.substitutions.items(), key=lambda x: len(x[0]), reverse=True)
            
            for key, value in sorted_subs:
                if buffer_str.endswith(key):
                    return key, value
            return None, None
    
    def process_substitution(self, original, replacement):
        """Process the substitution by deleting original and typing replacement"""
        # Delete the original characters that were typed
        delete_count = len(self.pending_chars)
        for i in range(delete_count):
            keyboard.press_and_release('backspace')
            time.sleep(0.01)
        
        # Clear pending characters
        self.pending_chars.clear()
        
        # Type the replacement
        keyboard.write(replacement)
    
    def should_suppress_character(self, char):
        """Check if this character should be suppressed (Latin characters that could form Ethiopic)"""
        if not self.enabled:
            return False
            
        # Only suppress characters that could be part of Ethiopic substitutions
        latin_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return char in latin_chars
    
    def on_key_press(self, event):
        """Handle key press events"""
        if not self.enabled:
            return
        
        # Check for config updates periodically
        if len(self.buffer) % 10 == 0:
            self.check_config_updates()
        
        # Handle regular characters
        if event.event_type == keyboard.KEY_DOWN:
            # Skip modifier and special keys that shouldn't go in buffer
            skip_keys = ['shift', 'ctrl', 'alt', 'caps lock', 'tab', 'enter', 'backspace', 'space', 
                        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
                        'print screen', 'scroll lock', 'pause', 'insert', 'home', 'page up',
                        'delete', 'end', 'page down', 'up', 'down', 'left', 'right', 'esc']
            
            if event.name in skip_keys:
                return
            
            # Handle backspace
            if event.name == 'backspace':
                with self.lock:
                    if self.buffer:
                        self.buffer.pop()
                    if self.pending_chars:
                        self.pending_chars.pop()
                return
            
            # Get the actual character
            char = self.get_character_from_event(event)
            if char:
                # Check if we should suppress this character
                if self.should_suppress_character(char):
                    # Suppress the key to prevent it from being typed
                    keyboard._suppress_key(event.scan_code)
                    
                    with self.lock:
                        self.buffer.append(char)
                        self.pending_chars.append(char)
                    
                    # Wait a bit to allow multi-character sequences to be completed
                    time.sleep(self.typing_delay)
                    
                    # Check for substitution after the delay
                    original, replacement = self.check_substitution()
                    if original and replacement:
                        # Process the substitution - this will type the Ethiopic character
                        self.process_substitution(original, replacement)
                    # If no substitution found, characters remain in memory but not displayed
                else:
                    # For non-Latin characters, allow normal typing but still track in buffer
                    with self.lock:
                        self.buffer.append(char)
    
    def start_monitoring(self):
        """Start monitoring keyboard input"""
        if not self.substitutions:
            print("No substitutions loaded. Please check your config.csv file.")
            return
        
        print("Senay Geez - Real-time Text Replacement")
        print("=" * 50)
        print("Press Page Up to toggle Ethiopic/Latin modes")
        print("Press ESC to exit")
        print(f"\nLoaded {len(self.substitutions)} substitutions from config.csv")
        print("\nReady to use substitutions...")
        print("Mode: Ethiopic (ENABLED) - Latin characters suppressed")
        
        # Register hotkeys
        keyboard.add_hotkey('page up', self.toggle_enabled)
        keyboard.add_hotkey('esc', self.stop)
        
        # Start monitoring all keys
        keyboard.hook(self.on_key_press)
        
        # Keep the program running
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.stop()
    
    def toggle_enabled(self):
        """Toggle substitution on/off (Ethiopic/Latin mode)"""
        self.enabled = not self.enabled
        
        # If disabling, flush any pending characters
        if not self.enabled and self.pending_chars:
            with self.lock:
                # Type all pending characters
                for char in self.pending_chars:
                    keyboard.write(char)
                self.pending_chars.clear()
        
        mode = "Ethiopic (ENABLED - Latin suppressed)" if self.enabled else "Latin (DISABLED - normal typing)"
        print(f"\nMode: {mode}")
    
    def stop(self):
        """Stop the application"""
        # Flush any pending characters before exiting
        if self.pending_chars:
            with self.lock:
                for char in self.pending_chars:
                    keyboard.write(char)
                self.pending_chars.clear()
        
        print("\nStopping Senay Geez...")
        keyboard.unhook_all()
        exit(0)

class TaskbarOverlay:
    def __init__(self):
        self.script_name = "senay_geez"
        self.process = None
        self.is_running = False
        self.lock = Lock()
        self.current_overlay = None
        self.substituter = None
        self.current_pid = os.getpid()
        
        # Create images if they don't exist
        self.create_images()
        
        # Register hotkey
        keyboard.add_hotkey('page up', self.toggle_script)
        
        print("Senay Geez Toggle with Overlay")
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
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Skip our own process
                if proc.info['pid'] == current_pid:
                    continue
                    
                if (proc.info['cmdline'] and 
                    any('senay_geez' in cmd for cmd in proc.info['cmdline']) and
                    'python' in proc.info['name'].lower()):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    def start_script(self):
        """Start the text substituter functionality"""
        try:
            # Start the text substitution functionality directly
            self.substituter = TextSubstituter()
            # Run in a separate thread to avoid blocking
            self.script_thread = Thread(target=self.substituter.start_monitoring, daemon=True)
            self.script_thread.start()
            
            self.is_running = True
            print("✓ Senay Geez STARTED")
            print("  - Latin characters are suppressed from display")
            print("  - Ethiopic characters appear when patterns match")
            return True
        except Exception as e:
            print(f"✗ Error starting script: {e}")
            return False
    
    def stop_script(self):
        """Stop the text substituter functionality"""
        try:
            # Stop the substituter if it's running
            if self.substituter:
                self.substituter.stop()
            
            self.is_running = False
            print("✓ Senay Geez STOPPED")
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
            overlay.configure(bg='#2b2b2b')
            overlay.attributes("-transparentcolor", "#2b2b2b")
            
            # Choose image based on state
            if self.is_running:
                image = self.blue_image
                status_text = "ሰናይ ግዕዝ"
                text_color = "#00ff00"
            else:
                image = self.white_image
                status_text = "Senay Geez"
                text_color = "#ff4444"
            
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
                x = screen_width - 200
                y = taskbar_rect[1] - 100
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
    
    def run(self):
        """Start the controller"""
        print("Senay Geez controller is running...")
        print("Press PAGE UP to toggle, overlay will show near taskbar")
        
        # Auto-start the substitution functionality
        if not self.is_running:
            self.start_script()
        
        # Start tkinter main loop
        root = tk.Tk()
        root.withdraw()
        
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

def ensure_config_exists():
    """Ensure config.csv exists with sample data"""
    if not os.path.exists("config.csv"):
        sample_config = """h,ሀ
hu,ሁ
hi,ሂ
ha,ሃ
he,ሄ
h,ህ
ho,ሆ
l,ለ
lu,ሉ
li,ሊ
la,ላ
le,ሌ
l,ል
lo,ሎ
H,ሐ
Hu,ሑ
Hi,ሒ
Ha,ሓ
He,ሔ
H,ሕ
Ho,ሖ
m,መ
mu,ሙ
mi,ሚ
ma,ማ
me,ሜ
m,ም
mo,ሞ
"""
        with open("config.csv", "w", encoding="utf-8") as f:
            f.write(sample_config)
        print("Created sample config.csv file")

def close_existing_instances():
    """Close any existing instances of Senay Geez (excluding current process)"""
    current_pid = os.getpid()
    instances_found = False
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip our own process
            if proc.info['pid'] == current_pid:
                continue
                
            if (proc.info['cmdline'] and 
                any('senay_geez' in cmd for cmd in proc.info['cmdline']) and
                'python' in proc.info['name'].lower()):
                print(f"Closing existing Senay Geez instance (PID: {proc.info['pid']})")
                proc.terminate()
                instances_found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if instances_found:
        time.sleep(1)  # Give time for processes to close

def main():
    # Don't hide console window initially - show status messages
    # try:
    #     import ctypes
    #     if os.name == 'nt':
    #         console_window = ctypes.windll.kernel32.GetConsoleWindow()
    #         if console_window:
    #             ctypes.windll.user32.ShowWindow(console_window, 0)
    # except:
    #     pass
    
    print("Starting Senay Geez...")
    
    # Close any existing instances (excluding ourselves)
    close_existing_instances()
    
    # Ensure config file exists
    ensure_config_exists()
    
    # Start the application
    controller = TaskbarOverlay()
    controller.run()

if __name__ == "__main__":
    main()