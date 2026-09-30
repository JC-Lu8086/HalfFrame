@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\.halfframe-ready (
  call setup_windows.bat
  if errorlevel 1 exit /b 1
)
start "HalfFrame" ".venv\Scripts\pythonw.exe" "app.py"
