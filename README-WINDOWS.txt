TEDDY VOICE ASSISTANT - WINDOWS (for Saha)
==========================================

EASIEST WAY - 1 double-click:
1. Unzip this folder somewhere, e.g. Documents\TeddyVoice
2. Double-click INSTALL-WINDOWS.bat
   - It checks Python, installs the voice libraries, adds Teddy to Startup, and starts Teddy.
   - If it says Python not found: install Python from python.org, tick "Add Python to PATH", then run it again.
3. Say: "Teddy, open Chrome"

That's it. Next time you turn on / log in to Windows, Teddy starts by itself.

COMMANDS
- Teddy, open Chrome / Firefox / Edge / Notepad / Calculator / VS Code / Spotify
- Teddy, open YouTube / Gmail / Google
- Teddy, search Google for [anything]
- Teddy, search YouTube for [anything]
- Teddy, search for [filename] on PC   (Documents, Downloads, Desktop)
- Teddy, what time is it / what is the date
- Teddy, sleep   (stops listening)

OPTIONAL .EXE
Want a single file with no Python window? Double-click BUILD-EXE.bat on your Windows PC.
It builds dist\TeddyVoice.exe there. I can't build a Windows .exe from my Linux computer -
Windows .exe files have to be built on Windows, so that script does it on yours in one click.

TROUBLESHOOTING
- Mic not heard: Settings > Privacy > Microphone > allow apps. Plug/check default mic in Sound settings.
- PyAudio error during install: the installer already tries an alternative. If it still fails, send Teddy a screenshot of the error.
- Remove autostart: Win+R > shell:startup > delete TeddyVoiceAssistant shortcut.
