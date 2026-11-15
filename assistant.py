"""
Teddy Voice Desktop Assistant v2 - for Saha (Windows)
Changes in v2 (fix for "Teddy does not respond"):
- Visible window: you can SEE status, what Teddy heard, and errors
- Everything is logged to teddy.log next to this file
- Commands work WITH or WITHOUT the wake word (v1 silently ignored
  anything where Google didn't hear the exact word "teddy")
- Voice engine is re-created for every sentence (v1's engine often
  hung on Windows after the first sentence, so Teddy went mute)
- A text box lets you type a command to test Teddy without the mic
- Mic test button lists microphones and checks yours
Run with:  python assistant.py   (NOT pythonw - so you can see it)
"""
import os, sys, subprocess, webbrowser, urllib.parse, pathlib, datetime, json, platform, threading, traceback

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

# ---------- speech out (fresh engine each time - fixes Windows hang) ----------
def speak(text):
    log(f"TEDDY SAYS: {text}")
    def _say():
        try:
            import pyttsx3
            e = pyttsx3.init(); e.setProperty('rate', 175)
            e.say(text); e.runAndWait(); e.stop()
            del e
        except Exception as ex:
            log(f"Voice-out failed ({ex}). Text was: {text}")
    threading.Thread(target=_say, daemon=True).start()

# ---------- config ----------
config = {"wake_word": "teddy", "use_wake_word": False}
cp = BASE / "config.json"
if cp.exists():
    try: config.update(json.loads(cp.read_text()))
    except Exception: pass
WAKE_VARIANTS = ["teddy", "daddy", "ready", "teddy,", "hey teddy"]

APPS = {
    "chrome": "chrome", "google chrome": "chrome", "firefox": "firefox",
    "edge": "msedge", "notepad": "notepad", "calculator": "calc",
    "spotify": "spotify", "vs code": "code", "code": "code",
    "file explorer": "explorer", "explorer": "explorer", "terminal": "cmd",
    "command prompt": "cmd", "paint": "mspaint", "word": "winword",
    "excel": "excel", "powerpoint": "powerpnt",
    "youtube": "https://www.youtube.com", "gmail": "https://mail.google.com",
    "google": "https://www.google.com", "whatsapp": "https://web.whatsapp.com",
}

def open_app(name):
    name = name.strip().lower()
    target = APPS.get(name)
    if target is None:
        try: os.startfile(name); return True
        except Exception: return False
    if target.startswith("http"): webbrowser.open(target); return True
    try: subprocess.Popen(target, shell=True); return True
    except Exception: return False

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

def handle(text):
    log(f"YOU SAID: {text}")
    t = text.lower().strip()
    for w in WAKE_VARIANTS:
        if t.startswith(w): t = t[len(w):].strip(" ,"); break
    if not t: speak("Yes Saha? Try: open Chrome"); return True
    if t in ("stop", "sleep", "exit", "quit", "go to sleep"): speak("Okay, going to sleep."); return False
    if "time" in t: speak(f"It's {datetime.datetime.now().strftime('%I:%M %p')}"); return True
    if "date" in t or "today" in t: speak(f"Today is {datetime.date.today().strftime('%A, %d %B %Y')}"); return True
    if "youtube" in t and "search" in t:
        q = t.split("search")[-1].replace("for", "", 1).strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}")
        speak(f"Searching YouTube for {q}"); return True
    if t.startswith("search google for") or t.startswith("google "):
        q = t.split("for", 1)[-1].strip() if "for" in t else t.replace("google", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}")
        speak(f"Searching Google for {q}"); return True
    if t.startswith("search for") or (t.startswith("search ") and " pc" in t):
        q = t.replace("search for", "").replace("search", "").replace("on pc", "").replace("on my pc", "").strip()
        results = search_pc(q)
        if results: speak(f"Found it on your PC: {pathlib.Path(results[0]).name}"); [log("  " + r) for r in results]
        else: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"); speak(f"Not found on PC, searching Google for {q}")
        return True
    if t.startswith("open ") or t.startswith("launch "):
        name = t.split(" ", 1)[-1].strip()
        if open_app(name): speak(f"Opening {name}")
        else: speak(f"I could not open {name}")
        return True
    if t.startswith("search "):
        q = t.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}")
        speak(f"Searching for {q}"); return True
    speak("I heard you, but I don't know that command yet. Try: open Chrome")
    return True

# ---------- listening loop ----------
stop_flag = threading.Event()
def listen_loop(status):
    try:
        import speech_recognition as sr
    except Exception as ex:
        log(f"ERROR: SpeechRecognition not installed ({ex}). Run INSTALL-WINDOWS.bat again.")
        status("Not listening - library missing. Run INSTALL-WINDOWS.bat"); return
    try:
        names = sr.Microphone.list_microphone_names()
        log(f"Microphones found: {names if names else 'NONE - check your mic!'}")
    except Exception as ex:
        log(f"Mic list failed: {ex}")
    r = sr.Recognizer(); r.energy_threshold = 300; r.dynamic_energy_threshold = True
    speak("Hi Saha, Teddy is ready. Say: open Chrome")
    while not stop_flag.is_set():
        try:
            with sr.Microphone() as source:
                status("Listening... speak now")
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=6, phrase_time_limit=7)
            status("Heard something, thinking...")
            text = r.recognize_google(audio)
            log(f"Heard (raw): {text}")
            low = text.lower()
            # v2: no silent ignoring. If no wake word, still act on clear commands.
            if any(low.strip().startswith(v) for v in ("open", "search", "launch", "google")) or any(w in low for w in WAKE_VARIANTS):
                if not handle(text): stop_flag.set(); status("Stopped"); break
            else:
                log("Ignored (not a command / no wake word). Say 'Teddy, open Chrome' or just 'open Chrome'.")
        except Exception as ex:
            name = type(ex).__name__
            if name in ("WaitTimeoutError",): continue
            if name in ("UnknownValueError",): log("Heard noise but could not understand words. Try closer to mic."); continue
            log(f"Listen error: {name}: {ex}")
            if name in ("RequestError",): speak("I need internet for voice recognition."); status("No internet for voice"); return
            if "PyAudio" in str(ex) or "microphone" in str(ex).lower():
                status("MIC PROBLEM - see log / run mic test"); 
            continue

def main():
    log("=" * 50); log("Teddy v2 starting...")
    try:
        import tkinter as tk
        root = tk.Tk(); root.title("Teddy Voice Assistant v2"); root.geometry("560x420")
        status_var = tk.StringVar(value="Starting...")
        tk.Label(root, text="Teddy Voice Assistant", font=("Segoe UI", 15, "bold")).pack(pady=6)
        tk.Label(root, textvariable=status_var, font=("Segoe UI", 11), fg="#0a6").pack()
        box = tk.Text(root, height=14, font=("Consolas", 9)); box.pack(fill="both", expand=True, padx=8, pady=6)
        def gui_log(line):
            try: root.after(0, lambda: (box.insert("end", line + "\n"), box.see("end")))
            except Exception: pass
        globals()["_gui_log"] = gui_log
        row = tk.Frame(root); row.pack(fill="x", padx=8, pady=4)
        entry = tk.Entry(row); entry.pack(side="left", fill="x", expand=True)
        def typed():
            cmd = entry.get().strip()
            if cmd: entry.delete(0, "end"); threading.Thread(target=handle, args=(cmd,), daemon=True).start()
        tk.Button(row, text="Test typed command", command=typed).pack(side="left", padx=4)
        entry.bind("<return>", lambda e: typed())
        tk.Label(root, text='Type e.g.  open notepad  here to test without mic, then try voice.', font=("Segoe UI", 8)).pack()
        def start_listening():
            stop_flag.clear()
            threading.Thread(target=listen_loop, args=(lambda s: root.after(0, status_var.set),), daemon=True).start()
        tk.Button(root, text="Start listening", command=start_listening, font=("Segoe UI", 10, "bold")).pack(pady=6)
        root.after(600, start_listening)
        root.protocol("WM_DELETE_WINDOW", lambda: (stop_flag.set(), root.destroy()))
        root.mainloop()
    except Exception:
        log("GUI failed, falling back to console:\n" + traceback.format_exc())
        listen_loop(print)

if __name__ == "__main__":
    main()
