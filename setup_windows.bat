@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo 请先安装 Python 3.12 64 位：https://www.python.org/downloads/windows/
    pause
    exit /b 1
  )
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
if not exist bin\jpegtran.exe (
  echo 缺少随附的 JPEG 组件，请重新解压完整的软件包。
  goto failed
)
.venv\Scripts\python.exe verify_windows.py
if errorlevel 1 goto failed
echo 安装完成。此后可以离线双击“启动Windows.bat”。
pause
exit /b 0
:failed
echo 安装未完成，请查看上面的错误信息后重试。
pause
exit /b 1
