"""
Teddy Voice Desktop Assistant - for Saha
Listens for voice, speaks back, opens apps, searches PC and web.

Wake word: "Teddy" (optional - can be turned off in config)
Examples:
  "Teddy, open Chrome"
  "Teddy, open Notepad / Calculator / VS Code / Spotify"
  "Teddy, search for my resume on PC"
  "Teddy, search Google for Tokyo weather"
  "Teddy, open YouTube and search lofi music"
  "Teddy, what time is it"
  "Teddy, stop / sleep"
"""
import os, sys, subprocess, webbrowser, urllib.parse, pathlib, datetime, json, platform

try:
    import speech_recognition as sr
except ImportError:
    print("Install first: pip install -r requirements.txt"); sys.exit(1)

try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    def speak(text):
        print(f"Teddy: {text}")
        try:
            engine.say(text); engine.runAndWait()
        except Exception:
            pass
except Exception:
    def speak(text): print(f"Teddy: {text}")

CONFIG_PATH = pathlib.Path(__file__).with_name("config.json")
config = {"wake_word": "teddy", "use_wake_word": True}
if CONFIG_PATH.exists():
    try: config.update(json.loads(CONFIG_PATH.read_text()))
    except: pass

# Common apps per OS
APPS = {
    "chrome": {"windows": "chrome", "darwin": "Google Chrome", "linux": "google-chrome"},
    "firefox": {"windows": "firefox", "darwin": "Firefox", "linux": "firefox"},
    "edge": {"windows": "msedge", "darwin": "Microsoft Edge", "linux": "microsoft-edge"},
    "notepad": {"windows": "notepad", "darwin": "TextEdit", "linux": "gedit"},
    "calculator": {"windows": "calc", "darwin": "Calculator", "linux": "gnome-calculator"},
    "spotify": {"windows": "spotify", "darwin": "Spotify", "linux": "spotify"},
    "vs code": {"windows": "code", "darwin": "Visual Studio Code", "linux": "code"},
    "code": {"windows": "code", "darwin": "Visual Studio Code", "linux": "code"},
    "file explorer": {"windows": "explorer", "darwin": "Finder", "linux": "xdg-open ."},
    "explorer": {"windows": "explorer", "darwin": "Finder", "linux": "xdg-open ."},
    "terminal": {"windows": "cmd", "darwin": "Terminal", "linux": "gnome-terminal"},
    "youtube": {"url": "https://www.youtube.com"},
    "gmail": {"url": "https://mail.google.com"},
    "google": {"url": "https://www.google.com"},
}

def open_app(name):
    name = name.strip().lower()
    info = APPS.get(name)
    if not info:
        # try as direct command / url
        if name.startswith("http"): webbrowser.open(name); return True
        try:
            if platform.system() == "Windows": os.startfile(name)
            elif platform.system() == "Darwin": subprocess.Popen(["open", "-a", name])
            else: subprocess.Popen([name])
            return True
        except Exception: return False
    if "url" in info: webbrowser.open(info["url"]); return True
    sysname = platform.system().lower()  # windows/darwin/linux
    cmd = info.get(sysname)
    if not cmd: return False
    try:
        if platform.system() == "Windows": subprocess.Popen(cmd, shell=True)
        elif platform.system() == "Darwin": subprocess.Popen(["open", "-a", cmd])
        else: subprocess.Popen(cmd.split())
        return True
    except Exception: return False

def search_pc(query):
    query = query.strip().lower()
    roots = [pathlib.Path.home() / d for d in ["Documents","Downloads","Desktop"]]
    found = []
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if query in p.name.lower():
                found.append(str(p))
                if len(found) >= 5: break
        if len(found) >= 5: break
    return found

def handle(text):
    t = text.lower().strip()
    print(f"You: {text}")
    # strip wake word
    if config.get("wake_word") in t: t = t.split(config["wake_word"],1)[-1].strip(" ,")

    if t in ("stop","sleep","exit","quit","go to sleep"): speak("Okay, going to sleep."); return False
    if "time" in t: speak(f"It's {datetime.datetime.now().strftime('%I:%M %p')}"); return True
    if "date" in t or "today" in t: speak(f"Today is {datetime.date.today().strftime('%A, %d %B %Y')}"); return True

    if t.startswith("open youtube and search") or t.startswith("search youtube for"):
        q = t.split("search",1)[-1].replace("for","",1).strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}")
        speak(f"Searching YouTube for {q}"); return True
    if t.startswith("search google for") or t.startswith("google "):
        q = t.split("for",1)[-1].strip() if "for" in t else t.replace("google","").strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}")
        speak(f"Searching Google for {q}"); return True
    if "search" in t and ("pc" in t or "computer" in t or "file" in t or " on " in t):
        q = t.replace("search","").replace("for","").replace("on pc","").replace("on my pc","").replace("file","").strip()
        results = search_pc(q)
        if results: speak(f"Found {len(results)} results. First is {pathlib.Path(results[0]).name}"); print("\n".join(results))
        else: speak(f"I didn't find {q} in Documents, Downloads or Desktop")
        return True
    if t.startswith("search for"):
        q = t.replace("search for","").strip()
        # default: try PC first, if nothing, Google
        results = search_pc(q)
        if results: speak(f"Found it on your PC: {pathlib.Path(results[0]).name}"); print("\n".join(results))
        else: webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"); speak(f"Not on PC, searching Google for {q}")
        return True
    if t.startswith("open ") or t.startswith("launch "):
        name = t.split(" ",1)[-1].strip()
        speak(f"Opening {name}") if open_app(name) else speak(f"I couldn't open {name}. Check the name in config.")
        return True
    if t.startswith("search "):
        q = t.replace("search","").strip()
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}")
        speak(f"Searching for {q}"); return True

    speak("I heard you, but I don't know that command yet. Try open Chrome, search Google for, or search for a file.")
    return True

def main():
    r = sr.Recognizer()
    mic = sr.Microphone()
    speak("Hi Saha, Teddy voice assistant is ready. Say Teddy, open Chrome.")
    with mic as source: r.adjust_for_ambient_noise(source, duration=1)
    while True:
        try:
            with mic as source:
                print("Listening...")
                audio = r.listen(source, timeout=8, phrase_time_limit=8)
            text = r.recognize_google(audio)
            if config.get("use_wake_word") and config["wake_word"] not in text.lower():
                print(f"(ignored, no wake word) {text}"); continue
            if not handle(text): break
        except sr.WaitTimeoutError: continue
        except sr.UnknownValueError: continue
        except sr.RequestError: speak("Internet is needed for voice recognition."); break
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()
