# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Find license documents in a source checkout or a relocated frozen bundle."""
from pathlib import Path
import sys


def resource_root():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def license_pages(root):
    return [(title, root / path) for title, path in (
        ("第三方声明 / Third-party notices", "THIRD_PARTY_NOTICES.md"),
        ("HalfFrame · MIT", "LICENSE"),
        ("Qt / PySide / Shiboken · LGPLv3", "licenses/Qt/LGPL-3.0-only.txt"),
        ("GNU GPLv3 (referenced by LGPLv3)", "licenses/Qt/GPL-3.0-only.txt"),
        ("替换与重建 / Replacing and rebuilding libraries", "RELINKING.md"),
        ("源码交付 / Included library sources", "third_party_sources/README.md"),
        ("发布说明 / Distribution notes", "RELEASE-LICENSING.md"),
        ("Windows · Microsoft runtime scope", "WINDOWS-RUNTIME-TERMS.md"),
        ("Microsoft runtime · English", "licenses/Microsoft/VC-Runtime-en.txt"),
        ("微软运行库 · 中文", "licenses/Microsoft/VC-Runtime-zh.txt"),
    )]
