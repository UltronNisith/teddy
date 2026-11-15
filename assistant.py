"""
Teddy Voice Desktop Assistant v3.2 - for Saha (Windows)
VOICE FIX in v3.1: v3 used pyttsx3 = old Windows SAPI "Desktop" voices.
Those are robotic by design, and if the PC has no British male SAPI voice
installed it falls back to the female default (Zira). v3.1 changes engine:
  1st choice: edge-tts NEURAL voice en-GB-RyanNeural (natural British male,
              free, needs internet - which voice recognition needs anyway)
  2nd choice: Windows natural voice via speak.ps1 (WinRT, George/Ryan)
  3rd choice: pyttsx3 SAPI, with the chosen voice LOGGED so it is visible
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

# ---------- voice out v3.1: neural British male first ----------
import queue, asyncio
_say_q = queue.Queue()
VOICE_NAME = "en-GB-RyanNeural"  # natural British male (neural, online)

def _play_mp3(path):
    """Play an mp3 on Windows via MCI (winmm), no extra apps needed."""
    try:
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW("close teddymp3", None, 0, 0)
        r = winmm.mciSendStringW(f'open "{path}" type mpegvideo alias teddymp3', None, 0, 0)
        if r != 0: raise RuntimeError(f"mci open failed {r}")
        winmm.mciSendStringW("play teddymp3 wait", None, 0, 0)
        winmm.mciSendStringW("close teddymp3", None, 0, 0)
        return True
    except Exception as ex:
        log(f"mp3 play via MCI failed: {ex}")
    try:  # fallback: Windows Media Player COM via PowerShell
        ps = f"$p=New-Object -ComObject WMPlayer.OCX; $p.URL='{path}'; $p.controls.play(); Start-Sleep 1; while($p.playState -eq 3){{Start-Sleep -m 300}}"
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=60)
        return True
    except Exception as ex:
        log(f"mp3 play via WMP failed: {ex}"); return False

def _say_edge_tts(text):
    import edge_tts
    out = str(BASE / "_teddy_say.mp3")
    async def _gen(): 
        await edge_tts.Communicate(text, VOICE_NAME, rate="-8%", pitch="-6Hz").save(out)
    asyncio.run(_gen())
    return _play_mp3(out)

def _say_winrt(text):
    ps1 = BASE / "speak.ps1"
    if not ps1.exists(): return False
    env = dict(os.environ); env["TEDDY_SAY"] = text
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
                       env=env, capture_output=True, text=True, timeout=60)
    if r.stdout.strip(): log(r.stdout.strip())
    return r.returncode == 0

def _say_sapi(text):
    import pyttsx3
    e = pyttsx3.init()
    voices = e.getProperty('voices')
    log("SAPI voices available: " + ", ".join(v.name for v in voices))
    chosen = None
    for want in ("george", "daniel", "arthur", "ryan", "david", "mark"):
        for v in voices:
            if want in v.name.lower(): chosen = v; break
        if chosen: break
    if chosen: e.setProperty('voice', chosen.id); log(f"Using SAPI voice: {chosen.name}")
    else: log("WARNING: no male SAPI voice found on this PC - using system default. Install the en-GB voice pack (see README) or use the neural voice.")
    e.setProperty('rate', 162); e.say(text); e.runAndWait(); e.stop(); del e
    return True

def _speaker_worker():
    while True:
        text = _say_q.get()
        if text is None: break
        done = False
        for name, fn in (("neural edge-tts en-GB-RyanNeural", _say_edge_tts),
                         ("Windows natural voice (WinRT)", _say_winrt),
                         ("SAPI fallback", _say_sapi)):
            try:
                if fn(text): log(f"(spoken via {name})"); done = True; break
            except Exception as ex:
                log(f"Voice engine '{name}' failed: {ex}")
        if not done: log(f"All voice engines failed. Text was: {text}")
        _say_q.task_done()

threading.Thread(target=_speaker_worker, daemon=True).start()

def speak(text):
    log(f"TEDDY SAYS: {text}")
    _say_q.put(text)

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

# ---------- close Teddy itself ----------
_root = None
def shutdown_app():
    """Fully close Teddy: stop listening, close the window, end the process."""
    log("Closing Teddy now, Sir.")
    try: stop_flag.set()
    except Exception: pass
    def _kill():
        try:
            if _root is not None: _root.destroy()
        except Exception: pass
        os._exit(0)
    # give the goodbye message ~2.5s to be spoken before the process ends
    threading.Timer(2.5, _kill).start()

SELF_CLOSE_PHRASES = ("close teddy", "close yourself", "exit teddy", "quit teddy",
    "stop teddy", "shut down teddy", "shutdown teddy", "bye teddy", "goodbye teddy",
    "goodbye", "bye", "sleep", "go to sleep", "stop", "exit", "quit")

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
    if t in SELF_CLOSE_PHRASES or t.startswith("close your"):
        speak("Goodbye, Sir. Closing now."); shutdown_app(); return False

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
            if pending["action"] or any(low.strip().startswith(v) for v in ("open", "search", "launch", "google", "close", "what", "volume", "mute", "lock", "shut", "restart", "take", "battery", "bye", "goodbye", "sleep", "stop", "exit", "quit")) or any(w in low for w in WAKE_VARIANTS):
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
    log("=" * 50); log("Teddy v3.2 (JARVIS-style, neural voice, self-close fixed) starting...")
    try:
        import tkinter as tk
        root = tk.Tk(); globals()["_root"] = root; root.title("Teddy Voice Assistant v3.2 - JARVIS style"); root.geometry("580x430")
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
        tk.Button(root, text="Close Teddy", command=lambda: (speak("Goodbye, Sir. Closing now."), shutdown_app()), fg="white", bg="#b00", font=("Segoe UI", 10, "bold")).pack(pady=4)
        tk.Label(root, text='Try typing:  what can you do for me   |   close notepad   then type:  yep', font=("Segoe UI", 8)).pack()
        threading.Thread(target=listen_loop, args=(lambda s: root.after(0, status_var.set),), daemon=True).start()
        root.protocol("WM_DELETE_WINDOW", lambda: (stop_flag.set(), root.destroy()))
        root.mainloop()
    except Exception:
        log("GUI failed, console fallback:\n" + traceback.format_exc()); listen_loop(print)

if __name__ == "__main__":
    main()
