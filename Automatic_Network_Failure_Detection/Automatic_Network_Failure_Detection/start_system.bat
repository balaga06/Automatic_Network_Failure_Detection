@echo off

:: Kill old instances (IMPORTANT)
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1

cd /d C:\Users\laksh\OneDrive\Desktop\Automatic_Network_Failure_Detection

:: Start monitoring
start "" pythonw monitoring.py

:: Small delay (VERY IMPORTANT)
timeout /t 2 > nul

:: Start dashboard
start "" pythonw dashboard/app.py