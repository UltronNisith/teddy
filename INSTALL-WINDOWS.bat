@echo off
title Teddy Voice Assistant - Install for Windows
echo ==========================================
echo  Teddy Voice Assistant - Windows Install
echo ==========================================
echo.
echo Step 1/3: Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found. Please install Python 3.10+ from https://www.python.org/downloads/
  echo IMPORTANT: tick "Add Python to PATH" during install, then run this file again.
  pause
  exit /b 1
)
python --version
echo.
echo Step 2/3: Installing voice libraries (needs internet, 1-2 minutes)...
python -m pip install --upgrade pip
python -m pip install SpeechRecognition pyttsx3
python -m pip install pyaudio
if errorlevel 1 (
  echo PyAudio failed, trying alternative wheel...
  python -m pip install pipwin
  pipwin install pyaudio
)
echo.
echo Step 3/3: Adding Teddy to Windows Startup (starts on boot/login)...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set HERE=%~dp0
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP%\TeddyVoiceAssistant.lnk'); $s.TargetPath='python.exe'; $s.Arguments='\"%HERE%assistant.py\"'; $s.WorkingDirectory='%HERE%'; $s.Save()"
echo.
echo DONE! Teddy will start automatically next time you log in.
echo Starting Teddy now for a first test...
start "Teddy Voice Assistant" python "%HERE%assistant.py"
echo.
echo Say: Teddy, open Chrome
echo To stop: say Teddy, sleep - or close the Teddy window.
echo To remove autostart: Win+R, type shell:startup, delete TeddyVoiceAssistant.
pause
