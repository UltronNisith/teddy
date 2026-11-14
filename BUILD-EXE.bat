@echo off
title Build TeddyVoice.exe (optional, one-time)
echo This builds a single TeddyVoice.exe so you don't need Python to run it.
echo It takes 2-4 minutes on your PC.
echo.
python -m pip install pyinstaller SpeechRecognition pyttsx3 pyaudio
python -m PyInstaller --noconfirm --onefile --noconsole --name TeddyVoice assistant.py
echo.
if exist dist\TeddyVoice.exe (
  echo SUCCESS: dist\TeddyVoice.exe created.
  echo You can move TeddyVoice.exe anywhere and double-click it.
  echo For autostart: Win+R, shell:startup, put a shortcut to TeddyVoice.exe there.
) else (
  echo Build did not finish. Keep using INSTALL-WINDOWS.bat version instead - it works the same.
)
pause
