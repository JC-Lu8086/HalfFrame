# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""An unresolved scan must not prevent exporting ready scans in the same batch."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import time
import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication, QMessageBox
from halfframe.core import analyze_scan
from halfframe.gui import MainWindow


def test_batch_exports_ready_scans_and_keeps_unresolved(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    raw = np.random.default_rng(10).integers(50,220,(160,240,3),dtype='uint8')
    raw[:,108:132] = 5
    good = tmp_path/'paired.tif'; bad = tmp_path/'single.tif'
    tifffile.imwrite(good,raw)
    tifffile.imwrite(bad,np.full_like(raw,100))
    window = MainWindow()
    window.scans = {str(p):analyze_scan(p) for p in (good,bad)}
    window.output_dir = tmp_path/'export'
    assert not window.scans[str(good)]['split']['export_blocked']
    assert window.scans[str(bad)]['split']['export_blocked']
    def unexpected_dialog(*args, **kwargs):
        raise AssertionError('A mixed batch should export ready scans without a blocking dialog')
    monkeypatch.setattr(QMessageBox,'information',unexpected_dialog)
    window.start_export(True)
    deadline = time.monotonic()+10
    while window.busy_kind and time.monotonic()<deadline:
        app.processEvents()
        time.sleep(.005)
    assert not window.busy_kind
    assert window.exported_count == 2
    assert window.export_skipped == [str(bad)]
    assert str(bad) in window.scans
    assert '1' in window.status.text()
    assert len(list(window.output_dir.glob('*.tif'))) == 2
    assert not list(window.output_dir.glob('single*'))
    window.close()
