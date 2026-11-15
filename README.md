# Teddy — Personalized Desktop Voice Assistant

**v2 — fix for 'Teddy does not respond':** now opens a visible window showing status + what Teddy heard, logs everything to `teddy.log`, accepts commands with or without the wake word, and has a typed-command test box + `DEBUG-RUN.bat` so errors are never silent.

A Windows desktop app that starts on boot/login and acts on your voice.

Say **"Teddy"** + a command:

- **Open apps** — "Teddy, open Chrome / Notepad / Calculator / VS Code / Spotify / YouTube / Gmail"
- **Search your PC** — "Teddy, search for resume on PC" (Documents, Downloads, Desktop)
- **Search the web / browser** — "Teddy, search Google for Tokyo weather", "Teddy, search YouTube for lofi music"
- **Time & date** — "Teddy, what time is it"
- **Stop** — "Teddy, sleep"

Teddy speaks back using text-to-speech.

## Quick start (Windows)

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) — tick **"Add Python to PATH"**
2. Double-click **`INSTALL-WINDOWS.bat`** — it installs the libraries, adds Teddy to Windows Startup (runs on boot), and starts Teddy
3. Say: *"Teddy, open Chrome"*

## Optional: single .exe

Double-click **`BUILD-EXE.bat`** on your Windows PC to build `dist\TeddyVoice.exe` with PyInstaller — no Python needed to run it after that.

## Files

| File | What it is |
|---|---|
| `assistant.py` | Main voice assistant (all logic, readable Python) |
| `config.json` | Wake word settings (`teddy`, on/off) |
| `requirements.txt` | Python libraries: SpeechRecognition, pyttsx3, PyAudio |
| `INSTALL-WINDOWS.bat` | One-click install + autostart + first run |
| `START-TEDDY.bat` | Manual start |
| `BUILD-EXE.bat` | Build a single `TeddyVoice.exe` |
| `README-WINDOWS.txt` | Windows setup + troubleshooting |

## Notes

- Voice recognition uses Google's free speech service, so it needs internet.
- It only opens apps already installed on the PC.
- Remove autostart: `Win+R` → `shell:startup` → delete the Teddy shortcut.

Built for Saha (@UltronNisith) — Personalized Desktop App.
