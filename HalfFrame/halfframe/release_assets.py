# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Check that a release actually delivers the documented LGPL source archives."""
import hashlib
import json
from pathlib import Path
from .license_view import license_pages


def verify_release_assets(root):
    root = Path(root)
    for _, path in license_pages(root):
        if not path.is_file():
            raise ValueError(f"Missing release document: {path.name}")
    sources = root / "third_party_sources"
    entries = json.loads((sources / "manifest.json").read_text())["archives"]
    expected = {
        "qtbase-everywhere-src-6.11.2.tar.xz",
        "qtsvg-everywhere-src-6.11.2.tar.xz",
        "pyside-setup-everywhere-src-6.11.2.tar.xz",
    }
    if len(entries) != len(expected) or {r["file"] for r in entries} != expected:
        raise ValueError("Incomplete matching Qt/PySide/Shiboken sources")
    for row in entries:
        digest = hashlib.sha256()
        with (sources / row["file"]).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != row["sha256"]:
            raise ValueError(f"Source checksum mismatch: {row['file']}")
    return len(entries)
