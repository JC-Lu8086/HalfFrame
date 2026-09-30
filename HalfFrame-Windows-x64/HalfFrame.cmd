@echo off
setlocal
cd /d "%~dp0"
start "" "%~dp0runtime\pythonw.exe" "%~dp0app\app.py" %*
