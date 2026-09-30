#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [[ -d "dist/HalfFrame.app" ]]; then
  open "dist/HalfFrame.app"
  exit
fi
if [[ ! -x .venv/bin/python ]]; then
  PYTHON="$(command -v python3.12 || command -v python3 || true)"
  if [[ -z "$PYTHON" ]]; then
    print '请先安装 Python 3.12：https://www.python.org/downloads/'
    read '?按回车关闭…'; exit 1
  fi
  "$PYTHON" -c 'import sys; assert sys.version_info >= (3,11), "请安装 Python 3.12 或更新版本"'
  "$PYTHON" -m venv .venv
fi
if [[ ! -f .venv/.halfframe-ready ]]; then
  .venv/bin/python -m pip install -r requirements.txt
  touch .venv/.halfframe-ready
fi
exec .venv/bin/python app.py
