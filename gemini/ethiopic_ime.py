import tkinter as tk
from tkinter import filedialog, messagebox
from pynput import keyboard
from pynput.keyboard import Key, Controller
import csv
import os
import sys
import threading
import time

# Default configuration including user examples (h, T, etc)
DEFAULT_CONFIG = """h,ሀ
hu,ሁ
hi,ሂ
ha,ሃ
hy,ሄ
he,ህ
ho,ሆ
hW,ኋ
l,ለ
lu,ሉ
li,ሊ
la,ላ
ly,ሌ
le,ል
lo,ሎ
lW,ሏ
s,ሰ
su,ሱ
si,ሲ
sa,ሳ
sy,ሴ
se,ስ
so,ሶ
sW,ሷ
r,ረ
ru,ሩ
ri,ሪ
ra,ራ
ry,ሬ
re,ር
ro,ሮ
rW,ሯ
b,በ
bu,ቡ
bi,ቢ
ba,ባ
by,ቤ
be,ብ
bo,ቦ
bW,ቧ
t,ተ
tu,ቱ
ti,ቲ
ta,ታ
ty,ቴ
te,ት
to,ቶ
tW,ቷ
n,ነ
nu,ኑ
ni,ኒ
na,ና
ny,ኔ
ne,ን
no,ኖ
nW,ኗ
a,አ
u,ኡ
i,ኢ
aa,ኣ
ee,ኤ
e,እ
o,ኦ
k,ከ
ku,ኩ
ki,ኪ
ka,ካ
ky,ኬ
ke,ክ
ko,ኮ
kW,ኳ
w,ወ
wu,ዉ
wi,ዊ
wa,ዋ
wy,ዌ
we,ው
wo,ዎ
z,ዘ
zu,ዙ
zi,ዚ
za,ዛ
zy,ዜ
ze,ዝ
zo,ዞ
zW,ዟ
d,ደ
du,ዱ
di,ዲ
da,ዳ
dy,ዴ
de,ድ
do,ዶ
dW,ዷ
T,ጠ
Tu,ጡ
Ti,ጢ
Ta,ጣ
Ty,ጤ
Te,ጥ
To,ጦ
TW,ጧ
T[,ፀ
T[u,ፁ
T[i,ፂ
T[a,ፃ
T[y,ፄ
T[e,ፅ
T[o,ፆ
"""

class EthiopicIME:
    def __init__(self, root):
        self.root = root
        self.root.title("Ethiopic IME")
        self.root.geometry("300x150")
        self.root.attributes('-topmost', True)
        
        # IME State
        self.is_active = tk.BooleanVar(value=True)
        self.mapping = {}
        self.output_chars = set()
        self.buffer = ""
        self.keyboard_controller = Controller()
        self.listener = None
        
        # Synchronization flags
        self.ignore_backspaces = 0 

        # Setup UI
        self.setup_ui()
        
        # Setup Data
        self.config_file = "config.csv"
        self.ensure_config_exists()
        self.load_mapping()
        
        # Start Keyboard Listener
        self.start_listener()

    def setup_ui(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.toggle_chk = tk.Checkbutton(
            frame, 
            text="Enable IME", 
            variable=self.is_active, 
            command=self.on_toggle,
            font=("Segoe UI", 12, "bold")
        )
        self.toggle_chk.pack(pady=5)

        self.info_label = tk.Label(frame, text="Status: Running", fg="green")
        self.info_label.pack(pady=5)

        btn_load = tk.Button(frame, text="Load Custom CSV", command=self.load_custom_csv)
        btn_load.pack(pady=5, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def ensure_config_exists(self):
        if not os.path.exists(self.config_file):
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    f.write(DEFAULT_CONFIG)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create default config: {e}")

    def load_mapping(self):
        try:
            new_mapping = {}
            with open(self.config_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        key = row[0].strip()
                        val = row[1].strip()
                        # Sort mapping by key length descending to ensure longest match wins if needed
                        new_mapping[key] = val
            
            self.mapping = new_mapping
            self.output_chars = set(self.mapping.values())
            self.info_label.config(text=f"Loaded {len(self.mapping)} keys")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")

    def load_custom_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if filename:
            self.config_file = filename
            self.load_mapping()

    def on_toggle(self):
        if self.is_active.get():
            self.info_label.config(text="Status: Active", fg="green")
            self.buffer = ""
        else:
            self.info_label.config(text="Status: Paused", fg="gray")
            self.buffer = ""

    def start_listener(self):
        # Using on_press for immediate feedback
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

    def on_close(self):
        if self.listener:
            self.listener.stop()
        self.root.destroy()
        sys.exit()

    def on_key_press(self, key):
        if not self.is_active.get():
            return

        # 1. Handle Backspaces (Ignore our own, clear buffer on user press)
        if key == Key.backspace:
            if self.ignore_backspaces > 0:
                self.ignore_backspaces -= 1
                return
            else:
                self.buffer = ""
                return

        # 2. Handle Space/Enter -> Reset buffer
        if key == Key.space or key == Key.enter:
            self.buffer = ""
            return

        # 3. Extract Character
        char = None
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char
        except AttributeError:
            return

        if not char:
            return

        # 4. Ignore Ethiopic Output (prevent loops)
        if char in self.output_chars:
            return

        self.process_char(char)

    def process_char(self, char):
        candidate = self.buffer + char
        
        # --- CASE 1: Match Found (e.g., "h"->ሀ or "hu"->ሁ) ---
        if candidate in self.mapping:
            if self.buffer:
                # We are extending a sequence (e.g. 'h' was already 'ሀ', now adding 'u')
                # We need to remove the previous Ethiopic char AND the new latin char.
                # Backspace count = 2
                self.apply_replacement(candidate, 2)
            else:
                # We are starting a new sequence (e.g. 'h')
                # We just need to remove the new latin char.
                # Backspace count = 1
                self.apply_replacement(candidate, 1)
            return

        # --- CASE 2: Partial Match (Prefix) ---
        # e.g., user typed "h" (buffer="h"), now types "W" (candidate="hW").
        # If "hW" isn't in map but "hWa" is, we wait.
        # NOTE: In your specific CSV, "hW" IS in the map, so it hits Case 1.
        # But if you had a 3-letter code like "abc", this handles "ab".
        is_prefix = any(k.startswith(candidate) for k in self.mapping.keys())
        if is_prefix:
            self.buffer = candidate
            return
        
        # --- CASE 3: Sequence Broken ---
        # e.g. Buffer="h" (screen ሀ). User types "h". Candidate "hh".
        # "hh" is not in map. Sequence breaks.
        # The user effectively "committed" the previous character.
        # We treat the NEW char ("h") as the start of a brand new sequence.
        
        new_buffer = char
        if new_buffer in self.mapping:
            # The new char itself is a match (e.g. second 'h' -> 'ሀ')
            # We only remove the new char (1 backspace). We leave the old 'ሀ' alone.
            self.apply_replacement(new_buffer, 1)
        elif any(k.startswith(new_buffer) for k in self.mapping.keys()):
            # The new char is a prefix of something else
            self.buffer = new_buffer
        else:
            # Total reset
            self.buffer = ""

    def apply_replacement(self, match_key, backspaces_needed):
        eth_char = self.mapping[match_key]
        
        # Tell listener to ignore the upcoming backspaces
        self.ignore_backspaces += backspaces_needed
        
        # 1. Delete raw input
        for _ in range(backspaces_needed):
            self.keyboard_controller.tap(Key.backspace)
            # No sleep needed usually, but tiny buffer helps some apps
            
        # 2. Type Ethiopic character
        self.keyboard_controller.type(eth_char)
        
        # 3. Update buffer to the current matched key
        self.buffer = match_key

if __name__ == "__main__":
    root = tk.Tk()
    app = EthiopicIME(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass