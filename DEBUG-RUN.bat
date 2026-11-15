@echo off
title Teddy DEBUG - errors stay visible here
cd /d "%~dp0"
echo Running Teddy in DEBUG mode. Keep this window open.
echo If anything fails, the error will show HERE - screenshot it and send to Teddy.
echo.
python assistant.py
echo.
echo Teddy stopped. Read the messages above.
pause
