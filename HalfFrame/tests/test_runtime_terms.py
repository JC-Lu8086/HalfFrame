# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Test local acknowledgement with synthetic text, not a real agreement."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox
from halfframe.runtime_terms import confirm_runtime_terms, RuntimeTermsDialog


def fixture_files(root):
    (root / "licenses/Microsoft").mkdir(parents=True)
    for name in ["WINDOWS-RUNTIME-TERMS.md", "licenses/Microsoft/VC-Runtime-en.txt", "licenses/Microsoft/VC-Runtime-zh.txt"]:
        (root / name).write_text("Synthetic test fixture. This is not an agreement.")
    return QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat)


def test_non_windows_needs_no_terms(tmp_path):
    assert confirm_runtime_terms(platform="darwin", root=tmp_path)


def test_reject_does_not_record_acceptance(tmp_path):
    settings = fixture_files(tmp_path)
    class Reject:
        def __init__(self, root): pass
        def exec(self): return QDialog.DialogCode.Rejected
    assert not confirm_runtime_terms(platform="win32", root=tmp_path, settings=settings, dialog_factory=Reject)
    assert not settings.contains("licenses/microsoft-runtime-accepted")


def test_accept_is_local_and_terms_change_requires_new_acknowledgement(tmp_path):
    settings = fixture_files(tmp_path); calls = []
    class Accept:
        def __init__(self, root): calls.append(root)
        def exec(self): return QDialog.DialogCode.Accepted
    for _ in range(2):
        assert confirm_runtime_terms(platform="win32", root=tmp_path, settings=settings, dialog_factory=Accept)
    assert len(calls) == 1
    (tmp_path / "WINDOWS-RUNTIME-TERMS.md").write_text("Updated synthetic test fixture, not an agreement.")
    assert confirm_runtime_terms(platform="win32", root=tmp_path, settings=settings, dialog_factory=Accept)
    assert len(calls) == 2


def test_checkbox_starts_unchecked_and_both_languages_load(tmp_path):
    app = QApplication.instance() or QApplication([])
    fixture_files(tmp_path)
    dialog = RuntimeTermsDialog(tmp_path)
    button = dialog.buttons.button(QDialogButtonBox.StandardButton.Ok)
    assert not dialog.agree.isChecked() and not button.isEnabled()
    dialog.language.setCurrentIndex(1)
    assert "Synthetic test fixture" in dialog.browser.toPlainText()
    dialog.agree.setChecked(True)
    assert button.isEnabled()
    dialog.reject()
