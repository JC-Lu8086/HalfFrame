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
.venv\Scripts\python.exe -m pip install -r requirements-release.txt
if errorlevel 1 goto failed
if not exist bin\jpegtran.exe (
  echo 源码包不附 Windows 二进制。请将官方 libjpeg-turbo 的 jpegtran.exe 和 jpeg62.dll 放入 bin 目录，详见 bin\README.md。
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
