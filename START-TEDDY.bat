@echo off
cd /d "%~dp0"
REM v2: run VISIBLE (python, not pythonw) so you can see Teddy's window and status
start "Teddy Voice Assistant" python assistant.py
exit
