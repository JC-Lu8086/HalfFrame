# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Folder imports skip complete recorded exports, never explicit file picks."""
import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication
import tifffile

from halfframe.core import analyze_scan, export_scan
from halfframe.gui import MainWindow, recorded_outputs


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    widget = MainWindow()
    widget.same_folder.setChecked(True)
    yield widget
    widget.close()


def make_record(folder, stem="scan", outputs=None, application="HalfFrame 0.2.0"):
    if outputs is None:
        outputs = []
        for index in (1, 2):
            path = folder / f"{stem}_{index}.tif"
            path.write_bytes(b"an existing exported photo")
            outputs.append({"path": str(path)})
    record = folder / f"{stem}_处理记录.json"
    record.write_text(json.dumps({"application": application, "outputs": outputs}), encoding="utf-8")
    return record


def test_real_exports_skipped_across_sessions_but_explicit_files_allowed(tmp_path, window):
    originals, exported = [], []
    for index in (1, 2):
        folder = tmp_path / f"含空格的目录 {index}"
        folder.mkdir()
        source = folder / "原片.tif"
        raw = np.random.default_rng(index).integers(40, 210, (64, 96, 3), dtype="uint8")
        raw[:, 42:54] = 8
        tifffile.imwrite(source, raw, photometric="rgb")
        scan = analyze_scan(source)
        scan["split"].update(manual=True, export_blocked=False)
        scan["frames"][0]["bbox"] = [0, 0, 54, 64]
        scan["frames"][1]["bbox"] = [42, 0, 96, 64]
        originals.append(str(source))
        exported.extend(result["path"] for result in export_scan(scan, None))
    assert set(window.paths_from_inputs([tmp_path])) == set(originals)
    assert set(window.paths_from_inputs(exported)) == set(exported)
    assert set(window.paths_from_inputs([tmp_path, *exported])) == set(originals + exported)


@pytest.mark.parametrize("invalid", [
    "malformed_json", "wrong_application", "not_a_list", "bad_entry",
    "missing_file", "outside_folder", "wrong_name", "relative_path", "too_large",
])
def test_invalid_records_cannot_hide_photos(tmp_path, window, invalid):
    folder = tmp_path / "photos"
    folder.mkdir()
    one, two = folder / "scan_1.tif", folder / "scan_2.tif"
    one.write_bytes(b"photo one")
    two.write_bytes(b"photo two")
    record = make_record(folder)
    content = json.loads(record.read_text())
    if invalid == "malformed_json":
        record.write_text("{broken", encoding="utf-8")
    elif invalid == "too_large":
        record.write_text(" " * 1_048_577, encoding="utf-8")
    else:
        if invalid == "wrong_application":
            content["application"] = "OtherApp"
        elif invalid == "not_a_list":
            content["outputs"] = {"path": str(one)}
        elif invalid == "bad_entry":
            content["outputs"][1] = None
        elif invalid == "missing_file":
            two.unlink()
        elif invalid == "outside_folder":
            outside = tmp_path / "scan_2.tif"
            outside.write_bytes(b"unrelated external photo")
            content["outputs"][1]["path"] = str(outside)
        elif invalid == "wrong_name":
            renamed = folder / "unrelated.tif"
            renamed.write_bytes(b"unrelated photo")
            content["outputs"][1]["path"] = str(renamed)
        elif invalid == "relative_path":
            content["outputs"][1]["path"] = "scan_2.tif"
        record.write_text(json.dumps(content), encoding="utf-8")
    assert recorded_outputs(folder) == set()
    assert set(window.paths_from_inputs([folder])) == {str(p) for p in folder.glob("*.tif")}


def test_symlink_output_cannot_exclude_another_photo(tmp_path, window):
    folder = tmp_path / "photos"
    folder.mkdir()
    target = tmp_path / "scan_2.tif"
    target.write_bytes(b"external original")
    record = make_record(folder)
    link = folder / "scan_2.tif"
    link.unlink()
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks unavailable on this platform")
    assert recorded_outputs(folder) == set()
    assert str(target) in window.paths_from_inputs([folder])
