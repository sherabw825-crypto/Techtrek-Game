@echo off
cd /d "%~dp0"
"venv\Scripts\python.exe" "src\gui.py"
if errorlevel 1 pause
