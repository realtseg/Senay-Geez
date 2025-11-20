import tkinter as tk
from tkinter import messagebox
from pynput import keyboard
from pynput.keyboard import Key, Controller
import csv
import os
import sys
import threading
import time
import webbrowser
import pystray
from PIL import Image, ImageTk, ImageDraw

class SenayGeezIME:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Start hidden, we only show splash then tray
        self.root.title("Senay Geez")

        # 1. Determine Base Path (Where the script or exe is located)
        self.base_path = self.get_base_path()
        
        # 2. Define File Paths
        self.config_path = os.path.join(self.base_path, "config.csv")
        self.icon_path = os.path.join(self.base_path, "app.ico")
        self.splash_path = os.path.join(self.base_path, "splash.jpg")
        self.blue_img_path = os.path.join(self.base_path, "blue.png")
        self.white_img_path = os.path.join(self.base_path, "white.png")

        # 3. Set Window Icon (if available)
        if os.path.exists(self.icon_path):
            try:
                self.root.iconbitmap(self.icon_path)
            except Exception:
                pass

        # 4. Initialize State
        self.is_active = True
        self.mapping = {}
        self.output_chars = set()
        self.buffer = ""
        self.keyboard_controller = Controller()
        self.listener = None
        self.ignore_backspaces = 0
        self.tray_icon = None

        # 5. Show Splash Screen
        self.show_splash()

        # 6. Load Data & Start Services
        self.load_config()
        self.setup_tray()
        self.start_listener()

    def get_base_path(self):
        """Returns the directory where the executable or script is located."""
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            return os.path.dirname(sys.executable)
        else:
            # Running as python script
            return os.path.dirname(os.path.abspath(__file__))

    def show_splash(self):
        """Displays splash.jpg for 5 seconds then closes."""
        if not os.path.exists(self.splash_path):
            # If no splash image, just return, app runs in background
            return

        splash = tk.Toplevel(self.root)
        splash.overrideredirect(True) # Remove window border
        splash.attributes('-topmost', True)

        try:
            # Load and display image
            pil_img = Image.open(self.splash_path)
            # Resize if necessary or ensure it fits, but user said 640x360 provided
            # We keep a reference to prevent GC
            self.splash_img = ImageTk.PhotoImage(pil_img)
            
            width, height = pil_img.size
            
            # Center on screen
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w // 2) - (width // 2)
            y = (screen_h // 2) - (height // 2)
            splash.geometry(f"{width}x{height}+{x}+{y}")

            lbl = tk.Label(splash, image=self.splash_img, bg="black")
            lbl.pack(fill=tk.BOTH, expand=True)

            # Close after 5 seconds
            self.root.after(5000, splash.destroy)
        except Exception as e:
            print(f"Splash error: {e}")
            splash.destroy()

    def load_config(self):
        """Loads mapping strictly from config.csv in the app folder."""
        if not os.path.exists(self.config_path):
            messagebox.showerror("Config Missing", f"Could not find config.csv in:\n{self.base_path}\n\nPlease add the file and restart.")
            return

        try:
            new_mapping = {}
            with open(self.config_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        key = row[0].strip()
                        val = row[1].strip()
                        new_mapping[key] = val
            
            self.mapping = new_mapping
            self.output_chars = set(self.mapping.values())
        except Exception as e:
            messagebox.showerror("Config Error", f"Error reading config.csv:\n{e}")

    # --- TRAY ICON LOGIC ---
    def setup_tray(self):
        threading.Thread(target=self._run_tray, daemon=True).start()

    def _run_tray(self):
        # Load Icon
        icon_img = None
        if os.path.exists(self.icon_path):
            try:
                icon_img = Image.open(self.icon_path)
            except Exception:
                pass
        
        # Fallback Icon Generator
        if icon_img is None:
            width = 64
            height = 64
            icon_img = Image.new('RGB', (width, height), "black")
            dc = ImageDraw.Draw(icon_img)
            dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill="white")

        menu = pystray.Menu(
            pystray.MenuItem("Help", self.open_help),
            pystray.MenuItem("Settings", self.open_settings),
            pystray.MenuItem("Exit", self.quit_app)
        )

        self.tray_icon = pystray.Icon("Senay Geez", icon_img, "Senay Geez IME", menu)
        self.tray_icon.run()

    def open_help(self, icon, item):
        webbrowser.open("https://trufat.net/senaygeez/")

    def open_settings(self, icon, item):
        if os.path.exists(self.config_path):
            try:
                os.startfile(self.config_path)
            except Exception as e:
                print(f"Error opening settings: {e}")
        else:
            # If it doesn't exist, try to create an empty one or warn
            messagebox.showwarning("Settings", "config.csv not found.")

    def quit_app(self, icon, item):
        self.tray_icon.stop()
        self.root.quit()
        os._exit(0)

    # --- VISUAL NOTIFICATION ---
    def show_notification(self, is_on):
        self.root.after(0, lambda: self._create_overlay(is_on))

    def _create_overlay(self, is_on):
        image_file = self.blue_img_path if is_on else self.white_img_path
        
        top = tk.Toplevel(self.root)
        top.overrideredirect(True)
        top.attributes('-topmost', True)
        
        # Position Bottom Right
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = 100
        win_h = 100
        x_pos = screen_w - win_w - 20
        y_pos = screen_h - win_h - 60 
        top.geometry(f"{win_w}x{win_h}+{x_pos}+{y_pos}")

        try:
            # Use PIL for loading png to support transparency/formats better
            pil_img = Image.open(image_file)
            # Resize to fit notification box if needed
            pil_img = pil_img.resize((win_w, win_h), Image.Resampling.LANCZOS)
            self.current_notify_img = ImageTk.PhotoImage(pil_img)
            
            lbl = tk.Label(top, image=self.current_notify_img, bg="black")
            lbl.pack(fill=tk.BOTH, expand=True)
        except Exception:
            # Fallback
            color = "blue" if is_on else "white"
            text_color = "white" if is_on else "black"
            text = "ON" if is_on else "OFF"
            lbl = tk.Label(top, text=text, bg=color, fg=text_color, font=("Arial", 20, "bold"))
            lbl.pack(fill=tk.BOTH, expand=True)

        top.after(2000, top.destroy)

    # --- KEYBOARD LISTENER ---
    def start_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_key_press(self, key):
        # Toggle Logic
        if key == Key.page_up:
            self.is_active = not self.is_active
            self.buffer = ""
            self.show_notification(self.is_active)
            return

        if not self.is_active:
            return

        if key == Key.backspace:
            if self.ignore_backspaces > 0:
                self.ignore_backspaces -= 1
                return
            else:
                self.buffer = ""
                return

        if key == Key.space or key == Key.enter:
            self.buffer = ""
            return

        char = None
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char
        except AttributeError:
            return

        if not char:
            return

        if char in self.output_chars:
            return

        self.process_char(char)

    def process_char(self, char):
        candidate = self.buffer + char
        
        # Case 1: Exact Match
        if candidate in self.mapping:
            backspaces = 2 if self.buffer else 1
            self.apply_replacement(candidate, backspaces)
            return

        # Case 2: Prefix Match
        is_prefix = any(k.startswith(candidate) for k in self.mapping.keys())
        if is_prefix:
            self.buffer = candidate
            return
        
        # Case 3: Broken Sequence
        new_buffer = char
        if new_buffer in self.mapping:
            self.apply_replacement(new_buffer, 1)
        elif any(k.startswith(new_buffer) for k in self.mapping.keys()):
            self.buffer = new_buffer
        else:
            self.buffer = ""

    def apply_replacement(self, match_key, backspaces_needed):
        eth_char = self.mapping[match_key]
        self.ignore_backspaces += backspaces_needed
        
        for _ in range(backspaces_needed):
            self.keyboard_controller.tap(Key.backspace)
            
        self.keyboard_controller.type(eth_char)
        self.buffer = match_key

if __name__ == "__main__":
    # Ensure high DPI awareness for Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    root = tk.Tk()
    app = SenayGeezIME(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass