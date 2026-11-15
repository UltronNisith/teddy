# Teddy — Personalized Desktop Voice Assistant

**v3 — JARVIS-style edition:** British male butler voice (the closest built-in Windows en-GB voice — the actual movie actor's voice can't be cloned), Teddy addresses you as **"Sir"** after every task, say **"what can you do for me"** for the full spoken capability list, and **close any app with confirmation** — Teddy asks *"Are you sure, Sir?"* and only closes when you say **yep / yup / yes**. Same protection for shutdown/restart. Also new: volume, mute, screenshot, battery, lock PC.

**v3.1 — voice fix:** v3's voice was the old Windows SAPI engine (robotic, and female on PCs with no male SAPI voice installed). v3.1 speaks with a **neural British male voice (en-GB Ryan)** first, then Windows' natural OneCore voice via `speak.ps1`, and only then SAPI — and it logs exactly which voice it used in the window / `teddy.log`. For the best offline voice, also add the free British pack on your PC: **Settings → Time & language → Speech → Add voices → English (United Kingdom)**.

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
