import keyboard
import time
import csv
import os
from collections import deque
from threading import Lock

class TextSubstituter:
    def __init__(self):
        self.substitutions = {}
        self.buffer = deque(maxlen=20)
        self.lock = Lock()
        self.enabled = True
        self.config_file = "config.csv"
        self.last_modified = 0
        self.typing_delay = 0.05
        
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
        # Delete the original characters
        delete_count = len(original)
        for i in range(delete_count):
            keyboard.press_and_release('backspace')
            time.sleep(0.01)
        
        # Type the replacement
        keyboard.write(replacement)
    
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
                return
            
            # Get the actual character
            char = self.get_character_from_event(event)
            if char:
                with self.lock:
                    self.buffer.append(char)
                
                # Wait a bit to allow multi-character sequences to be completed
                time.sleep(self.typing_delay)
                
                # Check for substitution after the delay
                original, replacement = self.check_substitution()
                if original and replacement:
                    # Process the substitution
                    self.process_substitution(original, replacement)
    
    def start_monitoring(self):
        """Start monitoring keyboard input"""
        if not self.substitutions:
            print("No substitutions loaded. Please check your config.csv file.")
            return
        
        print("Text Substituter - Real-time Text Replacement")
        print("=" * 50)
        print("Press Page Up to toggle Ethiopic/Latin modes")
        print("Press ESC to exit")
        print(f"\nLoaded {len(self.substitutions)} substitutions from config.csv")
        print("\nReady to use substitutions...")
        print("Mode: Ethiopic (ENABLED)")
        
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
        mode = "Ethiopic (ENABLED)" if self.enabled else "Latin (DISABLED)"
        print(f"\nMode: {mode}")
    
    def stop(self):
        """Stop the application"""
        print("\nStopping Text Substituter...")
        keyboard.unhook_all()
        exit(0)

def main():
    """Main function"""
    # Hide console window
    try:
        import ctypes
        if os.name == 'nt':
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window:
                ctypes.windll.user32.ShowWindow(console_window, 0)
    except:
        pass
    
    substituter = TextSubstituter()
    
    try:
        substituter.start_monitoring()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have the required permissions and try running as Administrator.")

if __name__ == "__main__":
    main()