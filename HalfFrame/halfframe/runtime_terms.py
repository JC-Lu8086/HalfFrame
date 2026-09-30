# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""One-time, local Windows runtime terms acknowledgement; no network calls."""
import hashlib
import sys
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QLabel, QMessageBox,
    QTextBrowser, QVBoxLayout,
)
from .license_view import resource_root


class RuntimeTermsDialog(QDialog):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Windows 运行库条款 / Runtime terms")
        self.resize(780, 600)
        layout = QVBoxLayout(self)
        scope = QLabel("以下条款仅适用于微软运行库。HalfFrame 自编代码仍为 MIT，Qt 等组件仍遵循 LGPL。\n"
                       "These terms apply only to Microsoft runtime components, not HalfFrame MIT or Qt LGPL code.")
        scope.setWordWrap(True)
        layout.addWidget(scope)
        self.language = QComboBox()
        self.language.addItem("简体中文", "zh")
        self.language.addItem("English", "en")
        layout.addWidget(self.language)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser, 1)
        self.agree = QCheckBox("我已阅读并同意微软运行库条款 / I have read and agree to the Microsoft runtime terms")
        layout.addWidget(self.agree)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("同意并继续 / Agree and continue")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("退出 / Exit")
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.agree.toggled.connect(self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        def show_terms():
            language = self.language.currentData()
            terms = (root / "licenses/Microsoft" / f"VC-Runtime-{language}.txt").read_text(encoding="utf-8")
            self.browser.setPlainText(terms)
        self.language.currentIndexChanged.connect(show_terms)
        show_terms()


def confirm_runtime_terms(*, platform=None, root=None, settings=None, dialog_factory=RuntimeTermsDialog):
    if (sys.platform if platform is None else platform) != "win32":
        return True
    root = resource_root() if root is None else root
    settings = QSettings("HalfFrame", "HalfFrame") if settings is None else settings
    try:
        documents = [root / "WINDOWS-RUNTIME-TERMS.md",
                     root / "licenses/Microsoft/VC-Runtime-en.txt",
                     root / "licenses/Microsoft/VC-Runtime-zh.txt"]
        digest = hashlib.sha256(b"\0".join(p.read_bytes() for p in documents)).hexdigest()
        if settings.value("licenses/microsoft-runtime-accepted") == digest:
            return True
        dialog = dialog_factory(root)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False
        settings.setValue("licenses/microsoft-runtime-accepted", digest)
        settings.sync()
        return True
    except OSError as error:
        QMessageBox.critical(None, "Runtime terms unavailable", str(error))
        return False
