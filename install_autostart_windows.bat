@echo off
REM Run this once on Windows - adds Teddy to Startup (runs on boot/login)
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT=%~dp0assistant.py
echo Creating shortcut in Startup folder...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP%\TeddyVoiceAssistant.lnk'); $s.TargetPath='pythonw.exe'; $s.Arguments='\"%SCRIPT%\"'; $s.WorkingDirectory='%~dp0'; $s.Save()"
echo Done. Teddy will start next time you log in to Windows.
echo To remove: delete TeddyVoiceAssistant from your Startup folder (Win+R, shell:startup)
pause
