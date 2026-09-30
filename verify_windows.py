# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Validate bundled JPEG utility and locate Python's VC runtime on Windows."""
from pathlib import Path
import shutil
import subprocess
import sys
root = Path(__file__).resolve().parent
for name in ('vcruntime140.dll', 'vcruntime140_1.dll'):
    runtime = Path(sys.base_prefix)/name
    if runtime.exists():
        shutil.copy2(runtime, root/'bin'/name)
subprocess.run([str(root/'bin'/'jpegtran.exe'), '-version'], check=True)
(root/'.venv'/'.halfframe-ready').write_text('ready\n')
print('HalfFrame 已就绪。')
