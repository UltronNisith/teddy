@echo off
title Close Teddy
echo Closing Teddy...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*assistant.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('Closed Teddy, PID ' + $_.ProcessId) }"
echo Done. If Teddy was running, it is now fully closed.
pause
