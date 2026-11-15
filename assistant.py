"""
Teddy Voice Desktop Assistant v3 - for Saha (Windows)
JARVIS-style edition:
- British male butler voice (Windows en-GB voice: George/Daniel if installed),
  calm and slower, formal JARVIS-style manner. NOTE: this is NOT the actual
  movie actor's voice - that voice cannot be cloned. This is the closest
  built-in Windows voice, styled the same way.
- Teddy addresses you as "Sir" after every completed task.
- Say "what can you do for me" and Teddy speaks his full capability list.
- NEW: close apps - but only after confirmation:
    You:   "close Chrome"
    Teddy: "Are you sure, Sir? Shall I close Chrome?"
    You:   "yep" / "yup" / "yes"  -> Teddy closes it: "Chrome is closed, Sir."
    You:   "no" / "cancel"        -> Teddy cancels.
  Same double-confirmation protects shutdown / restart.
- Visible window, live log, teddy.log, typed-command test box (from v2).
Run with: python assistant.py
"""
import os, sys, subprocess, webbrowser, urllib.parse, pathlib, datetime, json, threading, traceback, ctypes

BASE = pathlib.Path(__file__).parent
LOG = BASE / "teddy.log"

def log(msg):
    line = f"{datetime.datetime.now().strftime('%H:%M:%S')}  {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f: f.write(line + "\n")
    except Exception: pass
    if "_gui_log" in globals():
        try: globals()["_gui_log"](line)
        except Exception: pass

# ---------- voice out: British male, JARVIS-style ----------
def _pick_british_male(engine):
    try:
        voices = engine.getProperty('voices')
        # Prefer en-GB male voices, in order
        for want in ("george", "daniel", "arthur", "ryan", "brian"):
            for v in voices:
                if want in v.name.lower(): return v.id
        for v in voices:  # any British English voice
            if "en-gb" in str(getattr(v, 'languages', '')).lower() or "british" in v.name.lower() or "united kingdom" in v.name.lower(): return v.id
        for v in voices:  # any male-sounding English voice
            if any(m in v.name.lower() for m in ("david", "mark", "guy", "christopher")): return v.id
        return voices[0].id if voices else None
    except Exception:
        return None

def speak(text):
    log(f"TEDDY SAYS: {text}")
    def _say():
        try:
            import pyttsx3
            e = pyttsx3.init()
            vid = _pick_british_male(e)
            if vid: e.setProperty('voice', vid)
            e.setProperty('rate', 162)   # slower, calmer, JARVIS-like pace
            e.setProperty('volume', 1.0)
            try: e.setProperty('pitch', 85)  # ignored on some drivers, harmless
            except Exception: pass
            e.say(text); e.runAndWait(); e.stop(); del e
        except Exception as ex:
            log(f"Voice-out failed ({ex}). Text was: {text}")
    threading.Thread(target=_say, daemon=True).start()

# ---------- apps: open targets + Windows process names for closing ----------
APPS = {
    "chrome": ("chrome", "chrome.exe"), "google chrome": ("chrome", "chrome.exe"),
    "firefox": ("firefox", "firefox.exe"), "edge": ("msedge", "msedge.exe"),
    "notepad": ("notepad", "notepad.exe"), "calculator": ("calc", "CalculatorApp.exe"),
    "spotify": ("spotify", "Spotify.exe"), "vs code": ("code", "Code.exe"), "code": ("code", "Code.exe"),
    "file explorer": ("explorer", "explorer.exe"), "explorer": ("explorer", "explorer.exe"),
    "terminal": ("cmd", "cmd.exe"), "command prompt": ("cmd", "cmd.exe"),
    "paint": ("mspaint", "mspaint.exe"), "word": ("winword", "WINWORD.EXE"),
    "excel": ("excel", "EXCEL.EXE"), "powerpoint": ("powerpnt", "POWERPNT.EXE"),
    "youtube": ("https://www.youtube.com", None), "gmail": ("https://mail.google.com", None),
    "google": ("https://www.google.com", None), "whatsapp": ("https://web.whatsapp.com", None),
}
NEVER_CLOSE = {"explorer", "file explorer"}  # closing Explorer kills the desktop/taskbar

def open_app(name):
    name = name.strip().lower(); info = APPS.get(name)
    if info is None:
        try: os.startfile(name); return True
        except Exception: return False
    target = info[0]
    if target.startswith("http"): webbrowser.open(target); return True
    try: subprocess.Popen(target, shell=True); return True
    except Exception: return False

def close_app_now(name):
    """Actually close - only ever called AFTER the user confirms."""
    name = name.strip().lower(); info = APPS.get(name)
    if info is None or info[1] is None: return False
    try:
        r = subprocess.run(["taskkill", "/IM", info[1]], capture_output=True, text=True)
        log(f"taskkill {info[1]} -> {r.stdout.strip()} {r.stderr.strip()}")
        return "success" in (r.stdout + r.stderr).lower() or r.returncode == 0
    except Exception as ex:
        log(f"close failed: {ex}"); return False

def search_pc(query):
    query = query.strip().lower(); found = []
    for d in ["Documents", "Downloads", "Desktop"]:
        root = pathlib.Path.home() / d
        if not root.exists(): continue
        for p in root.rglob("*"):
            if query and query in p.name.lower():
                found.append(str(p))
                if len(found) >= 5: return found
    return found

def volume_key(vk):
    try: ctypes.windll.user32.keybd_event(vk, 0, 0, 0); ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
    except Exception as ex: log(f"volume key failed: {ex}")

CAPABILITIES = [
    "At your service, Sir. Here is what I can do for you.",
    "One, open and close applications. Say: open Chrome, or close Chrome. Before closing anything, I shall always ask for your confirmation first.",
    "Two, search your computer. Say: search for my resume on PC.",
    "Three, search the web. Say: search Google for Tokyo weather, or search YouTube for any video.",
    "Four, open websites directly. Say: open YouTube, open Gmail, or open WhatsApp.",
    "Five, control your system. Volume up, volume down, mute, lock my PC, take a screenshot, and I can tell you the time, the date, and your battery level.",
    "Six, shut down or restart your PC, but only after you confirm it twice, Sir.",
    "Simply tell me what you need, Sir.",
]
def speak_capabilities():
    for line in CAPABILITIES: log(line)
    speak(" ".join(CAPABILITIES))

# ---------- confirmation state ----------
pending = {"action": None, "target": None}  # e.g. {"action":"close","target":"chrome"}
YES_WORDS = {"yep", "yup", "yes", "yeah", "yeh", "sure", "confirm", "confirmed", "do it", "go ahead", "ok", "okay", "please do", "yes please"}
NO_WORDS = {"no", "nope", "cancel", "stop", "don't", "do not", "never mind", "nevermind"}

def ask_confirmation(action, target, question):
    pending["action"] = action; pending["target"] = target
    speak(question)

def handle_confirmation(t):
    action, target = pending["action"], pending["target"]
    pending["action"] = None; pending["target"] = None
    if any(w in t for w in NO_WORDS) and not any(t == w or t.startswith(w + " ") for w in YES_WORDS):
        speak(f"Very well, Sir. I have cancelled it. {target} is untouched."); return True
    if t in YES_WORDS or any(t.startswith(w) for w in YES_WORDS):
        if action == "close":
            if close_app_now(target): speak(f"Done, Sir. {target.capitalize()} is now closed.")
            else: speak(f"My apologies, Sir. {target.capitalize()} does not appear to be running.")
            return True
        if action == "shutdown":
            speak("Shutting down now. Goodbye, Sir."); subprocess.Popen("shutdown /s /t 5", shell=True); return True
        if action == "restart":
            speak("Restarting now. I shall see you shortly, Sir."); subprocess.Popen("shutdown /r /t 5", shell=True); return True
        if action == "lock":
            speak("Locking your PC, Sir."); ctypes.windll.user32.LockWorkStation(); return True
    speak("Forgive me, Sir, I did not catch that. The request has been cancelled for safety.")
    return True

WAKE_VARIANTS = ["teddy", "daddy", "ready", "hey teddy"]

def handle(text):
    log(f"YOU SAID: {text}")
    t = text.lower().strip().strip(".")
    for w in WAKE_VARIANTS:
        if t.startswith(w): t = t[len(w):].strip(" ,"); break
    # If Teddy is waiting for a yes/no, THIS reply is the confirmation.
    if pending["action"]:
        return handle_confirmation(t)
    if not t: speak("Yes, Sir? At your service."); return True
    if t in ("stop", "sleep", "exit", "quit", "go to sleep"): speak("Very well, Sir. Going to sleep."); return False

    # What can you do
    if any(p in t for p in ("what can you do", "what you can do", "what do you do", "your capabilities", "help me", "show help")) or t == "help":
        speak_capabilities(); return True

    # Close app -> ask first, never close immediately
    if t.startswith("close ") or t.startswith("quit ") or t.startswith("exit "):
        name = t.split(" ", 1)[-1].replace("app", "").strip()
        if name in NEVER_CLOSE:
            speak("I would advise against that, Sir. Closing File Explorer would remove your desktop and taskbar. I shall leave it running."); return True
        if name not in APPS:
            speak(f"I do not have {name} in my list, Sir. I can close Chrome, Firefox, Edge, Notepad, Calculator, Spotify, VS Code, Word, Excel, Paint and others I can open."); return True
        ask_confirmation("close", name, f"Are you sure, Sir? Shall I close {name}? Please say yep to confirm, or no to cancel.")
        return True

    # System power -> same confirmation protection
    if "shut down" in t or "shutdown" in t:
        ask_confirmation("shutdown", "PC shutdown", "Are you sure, Sir? Shall I shut down your PC? Say yep to confirm, or no to cancel."); return True
    if "restart" in t or "reboot" in t:
        ask_confirmation("restart", "PC restart", "Are you sure, Sir? Shall I restart your PC? Say yep to confirm, or no to cancel."); return True
    if "lock" in t and "pc" in t or t == "lock":
        ask_confirmation("lock", "PC lock", "Shall I lock your PC, Sir? Say yep to confirm."); return True

    if "volume up" in t or "increase volume" in t: volume_key(0xAF); speak("Volume increased, Sir."); return True
    if "volume down" in t or "decrease volume" in t: volume_key(0xAE); speak("Volume decreased, Sir."); return True
    if "mute" in t: volume_key(0xAD); speak("Muted, Sir."); return True
    if "screenshot" in t:
        try:
            out = BASE / f"screenshot-{datetime.datetime.now().strftime('%H%M%S')}.png"
            subprocess.run(["powershell", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{{PRTSC}}'); Start-Sleep -m 400; Get-Clipboard -Format Image | ForEach-Object {{ $_.Save('{out}') }}"], capture_output=True)
            speak("Screenshot taken and saved in my folder, Sir.")
        except Exception: speak("I could not take that screenshot, Sir.")
        return True
    if "battery" in t:
        try:
            class SPS(ctypes.Structure): _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte), ("BatteryLifePercent", ctypes.c_byte), ("Reserved", ctypes.c_byte), ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
            s = SPS(); ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s))
            speak(f"Your battery is at {s.BatteryLifePercent} percent, Sir.")
        except Exception: speak("I could not read the battery, Sir.")
        return True
    if "time" in t: speak(f"It is {datetime.datetime.now().strftime('%I:%M %p')}, Sir."); return True
    if "date" in t or "today" in t: speak(f"Today is {datetime.date.today().strftime('%A, %d %B %Y')}, Sir."); return True
    if "youtube" in t and "search" in t:
        q = t.split("search")[-1].replace("for", "", 1).strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}")
        speak(f"Searching YouTube for {q}, Sir."); return True
    if t.startswith("search google for") or t.startswith("google "):
        q = t.split("for", 1)[-1].strip() if "for" in t else t.replace("google", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}")
        speak(f"Searching Google for {q}, Sir."); return True
    if t.startswith("search for") or (t.startswith("search ") and " pc" in t):
        q = t.replace("search for", "").replace("search", "").replace("on pc", "").replace("on my pc", "").strip()
        results = search_pc(q)
        if results: speak(f"Found it on your PC, Sir: {pathlib.Path(results[0]).name}"); [log("  " + r) for r in results]
        else: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"); speak(f"Not on your PC, Sir. Searching Google for {q} instead.")
        return True
    if t.startswith("open ") or t.startswith("launch "):
        name = t.split(" ", 1)[-1].strip()
        if open_app(name): speak(f"{name.capitalize()} is open, Sir.")
        else: speak(f"My apologies, Sir. I could not open {name}.")
        return True
    if t.startswith("search "):
        q = t.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}")
        speak(f"Searching for {q}, Sir."); return True
    speak("Forgive me, Sir, I do not know that command yet. Ask me: what can you do for me?")
    return True

stop_flag = threading.Event()
def listen_loop(status):
    try:
        import speech_recognition as sr
    except Exception as ex:
        log(f"ERROR: SpeechRecognition not installed ({ex}). Run INSTALL-WINDOWS.bat again."); status("Not listening - library missing"); return
    try: log(f"Microphones found: {sr.Microphone.list_microphone_names()}")
    except Exception as ex: log(f"Mic list failed: {ex}")
    r = sr.Recognizer(); r.energy_threshold = 300; r.dynamic_energy_threshold = True
    speak("Good day, Sir. All systems are now fully operational. At your service. Say: what can you do for me, or simply, open Chrome.")
    while not stop_flag.is_set():
        try:
            with sr.Microphone() as source:
                status("Listening... speak now, Sir")
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=6, phrase_time_limit=7)
            status("Heard something, thinking...")
            text = r.recognize_google(audio)
            log(f"Heard (raw): {text}")
            low = text.lower()
            # While a confirmation is pending, EVERY reply goes to the confirmation handler.
            if pending["action"] or any(low.strip().startswith(v) for v in ("open", "search", "launch", "google", "close", "what", "volume", "mute", "lock", "shut", "restart", "take", "battery")) or any(w in low for w in WAKE_VARIANTS):
                if not handle(text): stop_flag.set(); status("Stopped"); break
            else:
                log("Ignored (not a command). Say 'open Chrome', 'close Chrome' or 'what can you do for me'.")
        except Exception as ex:
            name = type(ex).__name__
            if name == "WaitTimeoutError": continue
            if name == "UnknownValueError": log("Heard noise but could not understand. Try closer to the mic."); continue
            log(f"Listen error: {name}: {ex}")
            if name == "RequestError": speak("I need internet for voice recognition, Sir."); status("No internet for voice"); return
            continue

def main():
    log("=" * 50); log("Teddy v3 (JARVIS-style) starting...")
    try:
        import tkinter as tk
        root = tk.Tk(); root.title("Teddy Voice Assistant v3 - JARVIS style"); root.geometry("580x430")
        status_var = tk.StringVar(value="Starting...")
        tk.Label(root, text="Teddy - at your service, Sir", font=("Segoe UI", 15, "bold")).pack(pady=6)
        tk.Label(root, textvariable=status_var, font=("Segoe UI", 11), fg="#0a6").pack()
        box = tk.Text(root, height=14, font=("Consolas", 9)); box.pack(fill="both", expand=True, padx=8, pady=6)
        globals()["_gui_log"] = lambda line: root.after(0, lambda: (box.insert("end", line + "\n"), box.see("end")))
        row = tk.Frame(root); row.pack(fill="x", padx=8, pady=4)
        entry = tk.Entry(row); entry.pack(side="left", fill="x", expand=True)
        def typed():
            cmd = entry.get().strip()
            if cmd: entry.delete(0, "end"); threading.Thread(target=handle, args=(cmd,), daemon=True).start()
        tk.Button(row, text="Test typed command", command=typed).pack(side="left", padx=4)
        entry.bind("<return>", lambda e: typed())
        tk.Label(root, text='Try typing:  what can you do for me   |   close notepad   then type:  yep', font=("Segoe UI", 8)).pack()
        threading.Thread(target=listen_loop, args=(lambda s: root.after(0, status_var.set),), daemon=True).start()
        root.protocol("WM_DELETE_WINDOW", lambda: (stop_flag.set(), root.destroy()))
        root.mainloop()
    except Exception:
        log("GUI failed, console fallback:\n" + traceback.format_exc()); listen_loop(print)

if __name__ == "__main__":
    main()
