# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""HalfFrame's local desktop interface.

The full-resolution crop/export lives in core.py; the UI only displays reduced
previews. Workers send results through Qt signals and never touch widgets.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QThread, Signal, QSignalBlocker, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSlider, QSpinBox, QSplitter,
    QTextBrowser, QToolButton, QVBoxLayout, QWidget,
)

from .core import analyze_scan, export_scan, preview_crop
from . import __version__


SUPPORTED = {".jpg", ".jpeg", ".tif", ".tiff"}
COLORS = ("#9cdda7", "#8cc9f4")


def recorded_outputs(folder: Path) -> set[Path]:
    """Find this folder's own exports without trusting paths in a record.

    Only complete, local pairs matching a HalfFrame record's filename count.
    A bad record must never hide arbitrary photos or files outside this folder.
    """
    folder = folder.resolve()
    ignored: set[Path] = set()
    suffix = "_处理记录.json"
    for record in folder.glob("*" + suffix):
        try:
            if record.is_symlink() or not record.is_file() or record.stat().st_size > 1_048_576:
                continue
            content = json.loads(record.read_text(encoding="utf-8"))
            if not isinstance(content, dict):
                continue
            application = content.get("application")
            if not isinstance(application, str) or not (application == "HalfFrame" or application.startswith("HalfFrame ")):
                continue
            outputs = content.get("outputs")
            if not isinstance(outputs, list) or len(outputs) != 2:
                continue
            stem = record.name[:-len(suffix)]
            pair: set[Path] = set()
            for index, output in enumerate(outputs, 1):
                value = output.get("path") if isinstance(output, dict) else None
                if not isinstance(value, str) or not value:
                    break
                candidate = Path(value)
                if (not candidate.is_absolute() or candidate.is_symlink()
                        or candidate.stem != f"{stem}_{index}"
                        or candidate.suffix.lower() not in SUPPORTED):
                    break
                resolved = candidate.resolve()
                if resolved.parent != folder or not resolved.is_file():
                    break
                pair.add(resolved)
            if len(pair) == 2:
                ignored.update(pair)
        except (OSError, ValueError, UnicodeError, RuntimeError):
            # Interrupted writes, malformed JSON, invalid paths and symlink
            # loops leave every source photo eligible for import.
            continue
    return ignored


LANGUAGE = "zh"
TEXT = {
    "作者：J.C. Lu": "By J.C. Lu",
    "开源许可与第三方声明": "Licenses and credits",
    "选择照片文件": "Choose image files",
    "选择文件夹后，批量读取其中及子文件夹内的 JPG / TIFF。\n也可以拖入文件夹或照片文件。": "Choose a folder to import JPG / TIFF images from it and its subfolders.\nYou can also drop folders or image files here.",
    "照片队列 · {count}": "PHOTO QUEUE · {count}",
    "移除选中": "Remove selected",
    "全部处理均在本机完成\n原片保留，导出为独立文件": "Entirely on your device\nOriginals stay untouched",
    "一张扫描，两张照片。": "One scan. Two photographs.",
    "自动分片 · 手动旋转 · 保留完整画面": "Automatic split · Manual rotation · Full frame",
    "导出这张": "Export selected",
    "导出全部": "Export all",
    "把半格扫描交给这里": "Your half-frame scans belong here",
    "原始扫描 / 裁切范围": "ORIGINAL SCAN / CROP BOUNDS",
    "选择扫描文件夹，批量导入照片\n自动找到两张底片之间的分隔": "Choose a scan folder to import photos\nFind the split between the two frames",
    "分隔线微调": "ADJUST THE SPLIT",
    "左右分片  │": "Side by side  │",
    "上下分片  ─": "Top and bottom  ─",
    "自动定位中间的分隔区域": "Automatically locate the separator",
    "照片 1 结束于": "Photo 1 ends at",
    "照片 2 开始于": "Photo 2 starts at",
    "恢复自动结果": "Reset split and rotation",
    "照片 01": "PHOTO 01",
    "照片 02": "PHOTO 02",
    "等待导入": "Waiting for photos",
    "每张照片都可独立旋转": "Rotate each photo independently",
    "↶  左转": "↶  Left",
    "右转  ↷": "Right  ↷",
    "逆时针旋转 90°": "Rotate 90° counterclockwise",
    "顺时针旋转 90°": "Rotate 90° clockwise",
    "旋转角度，相对于导入后的原片方向": "Rotation relative to the imported scan",
    "▸  微调裁切边界": "▸  Fine-tune crop bounds",
    "▾  微调裁切边界": "▾  Fine-tune crop bounds",
    "左": "Left", "上": "Top", "右": "Right", "下": "Bottom",
    "等待分析": "Waiting to analyze",
    "分隔范围已手动调整": "Split adjusted manually",
    "请先定位分界 · 当前保留完整扫描": "Set the split first · Full scan retained",
    "分隔位置待复核 · 可拖动下方滑块": "Check the split · Adjust with the sliders",
    "已定位分界 · 重叠保边，保留完整画面": "Split found · Overlap preserves the full frame",
    "保留外框与分隔处重叠，避免自动裁掉画面。方向由你手动调整。": "Borders and overlap are retained to protect the frame. Rotate each photo manually.",
    "原格式 JPG 向外对齐裁切边界；必要时用方向标签保全边缘。": "Original JPG expands crop bounds; an orientation tag may preserve edge pixels.",
    "导出格式": "Output format",
    "原格式": "Original format",
    "JPG（有损）": "JPG (lossy)",
    "16-bit TIFF": "16-bit TIFF",
    "JPG 质量": "JPG quality",
    "保留原始格式与位深。TIFF 无损；JPG 无损裁切会向外保留边界。": "Keep source format and bit depth. TIFF is lossless; JPG crops expand to preserve edges.",
    "JPG 会重新有损压缩；16-bit 原片转为 8-bit，ICC 保留。": "JPG is re-encoded with loss. 16-bit sources become 8-bit; ICC is retained.",
    "无损保存为 16-bit TIFF；8-bit 升为 16-bit 不会增加原片细节。": "Lossless 16-bit TIFF. Converting 8-bit to 16-bit does not create new image detail.",
    "保存到各原片文件夹": "Save beside each source",
    "选择导出文件夹": "Choose output folder",
    "尚未选择": "No folder selected",
    "每张扫描的原片文件夹": "Each scan’s source folder",
    "打开文件夹 ↗": "Open folder ↗",
    "准备就绪 · 支持批量导入 JPG、TIFF": "Ready · Batch import JPG and TIFF scans",
    "扫描照片 (*.jpg *.jpeg *.tif *.tiff *.JPG *.JPEG *.TIF *.TIFF)": "Scan photos (*.jpg *.jpeg *.tif *.tiff *.JPG *.JPEG *.TIF *.TIFF)",
    "选择扫描文件夹": "Choose scan folder",
    "无法读取文件夹": "Cannot read folder",
    "没有新的 JPG / TIFF 文件可导入。已在队列中的文件会自动跳过。": "No new JPG / TIFF files found. Files already in the queue are skipped.",
    "正在定位分隔区域…": "Locating the separator…",
    "需要复核": "Check split",
    "请先定位分界": "Set split first",
    "已就绪": "Ready",
    "已导出 · {state}": "Exported · {state}",
    "{name}\n{state}  ·  2 张照片": "{name}\n{state}  ·  2 photos",
    "读取失败": "Read failed",
    "读取失败 · {error}": "Read failed · {error}",
    "分析完成 · {count} 张扫描 / {photos} 张照片": "Analysis complete · {count} scans / {photos} photos",
    " · {count} 张读取失败（选择查看原因）": " · {count} failed (select for details)",
    "正在分析 · {current} / {total} · {name}": "Analyzing · {current} / {total} · {name}",
    "正在导出 · {current} / {total} · {name}": "Exporting · {current} / {total} · {name}",
    "请先调整分隔位置": "Set the split first",
    "{count} 张扫描尚未定位分界。请选中它们并调整滑块后再导出。": "The split is unresolved in {count} scans. Select them and adjust the sliders before exporting.",
    "导出完成 · {count} 张照片 · {folder}": "Export complete · {count} photos · {folder}",
    " · {count} 个文件失败": " · {count} files failed",
    " · 已跳过 {count} 张待定位扫描（仍保留在队列）": " · Skipped {count} unresolved scans (kept in queue)",
    "待定位扫描：\n{names}": "Unresolved scans:\n{names}",
    " · {count} 张 JPG 已向外保边，详情见处理记录": " · {count} JPG crops expanded to preserve edges; see export records",
    "部分文件未能导出": "Some files could not be exported",
    "已导出 {count} 张照片。{errors} 个扫描文件导出失败。": "Exported {count} photos. {errors} scans could not be exported.",
    "正在完成当前文件，然后关闭窗口…": "Finishing the current file, then closing…",
}


def tr(text: str, **values) -> str:
    return (TEXT.get(text, text) if LANGUAGE == "en" else text).format(**values)


def translate_existing(text: str) -> str:
    if LANGUAGE == "en":
        return TEXT.get(text, text)
    reverse = {value: key for key, value in TEXT.items()}
    return reverse.get(text, text)

STYLE = """
QMainWindow, QWidget#workspace { background: #f5f4ef; color: #252b28; }
QWidget { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', 'Helvetica Neue', sans-serif;
          font-size: 13px; color: #252b28; }
QWidget#sidebar { background: #ecece5; border-right: 1px solid #ddded5; }
QLabel#brand { font-size: 31px; font-weight: 700; letter-spacing: 1px; }
QLabel#wordmark { color: #788074; font-size: 11px; letter-spacing: 3px; }
QLabel#title { font-size: 26px; font-weight: 650; }
QLabel#muted { color: #777f74; font-size: 12px; }
QLabel#section { color: #687260; font-size: 11px; font-weight: 650; letter-spacing: 1px; }
QLabel#small { font-size: 11px; color: #788074; }
QLabel#fileTitle { font-size: 16px; font-weight: 650; }
QPushButton, QToolButton { background: #fffef9; border: 1px solid #d6dacf;
  border-radius: 7px; padding: 8px 13px; font-weight: 500; }
QPushButton:hover, QToolButton:hover { background: #e4eadc; border-color: #b3bfaa; }
QPushButton:pressed, QToolButton:pressed { background: #d6dfcc; }
QPushButton:disabled, QToolButton:disabled { color: #abb0a5; background: #eceee8; border-color: #e0e3d9; }
QPushButton#primary { background: #364e38; color: #ffffff; border-color: #364e38; }
QPushButton#primary:hover { background: #47634a; }
QPushButton#primary:disabled { background: #9da899; border-color: #9da899; color: #e5e9e2; }
QListWidget { border: none; background: transparent; outline: none; }
QListWidget::item { border: 1px solid transparent; border-radius: 8px; padding: 10px 8px;
 margin: 3px 0px; color: #515b4c; }
QListWidget::item:selected { background: #fafbf5; color: #26382a; border-color: #c9d2c1; }
QListWidget::item:hover:!selected { background: #e2e6db; }
QFrame#panel, QWidget#card { background: #fffef9; border: 1px solid #dedfd6; border-radius: 10px; }
QLabel#badge { border: 0; background: #e8efdf; color: #4b6241; border-radius: 5px; padding: 4px 7px; font-size: 11px; }
QComboBox, QSpinBox { background: #fffef9; border: 1px solid #d6dacf; border-radius: 5px; padding: 5px 7px; }
QComboBox:disabled, QSpinBox:disabled { color: #9da899; }
QComboBox QAbstractItemView { background: #fffef9; selection-background-color: #dce8d6; }
QSlider::groove:horizontal { height: 4px; background: #e0e5d8; border-radius: 2px; }
QSlider::handle:horizontal { background: #5d7955; border: 2px solid #fffef9; width: 14px; margin: -6px 0; border-radius: 8px; }
QProgressBar { border: none; background: #e1e6da; border-radius: 3px; height: 5px; }
QProgressBar::chunk { background: #698762; border-radius: 3px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #c7cebe; border-radius: 4px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: transparent; width: 8px; }
QToolTip { background: #fffef9; color: #252b28; border: 1px solid #ccd3c4; padding: 6px; }
"""


def label(text: str, object_name: str | None = None) -> QLabel:
    result = QLabel(tr(text))
    if object_name:
        result.setObjectName(object_name)
    return result


def pil_pixmap(img: Image.Image) -> QPixmap:
    rgb = img.convert("RGB")
    data = rgb.tobytes()
    qimg = QImage(data, rgb.width, rgb.height, rgb.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class ImageCanvas(QWidget):
    def __init__(self, empty_text: str = "", parent=None):
        super().__init__(parent)
        self.pixmap: QPixmap | None = None
        self.scan: dict | None = None
        self.empty_text = empty_text
        self.setMinimumSize(160, 170)

    def set_image(self, image: Image.Image | None, scan: dict | None = None):
        self.pixmap = pil_pixmap(image) if image is not None else None
        self.scan = scan
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#202622"))
        painter.drawRoundedRect(self.rect(), 7, 7)
        if self.pixmap is None:
            painter.setPen(QColor("#8e9a8e"))
            painter.drawText(self.rect().adjusted(24, 24, -24, -24),
                             Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                             tr(self.empty_text))
            return
        inner = self.rect().adjusted(14, 14, -14, -14)
        scale = min(inner.width() / self.pixmap.width(), inner.height() / self.pixmap.height())
        width, height = int(self.pixmap.width() * scale), int(self.pixmap.height() * scale)
        x, y = (self.width() - width) // 2, (self.height() - height) // 2
        painter.drawPixmap(x, y, width, height, self.pixmap)
        if self.scan:
            sx, sy = width / self.scan["width"], height / self.scan["height"]
            for i, frame in enumerate(self.scan["frames"]):
                left, top, right, bottom = frame["bbox"]
                color = QColor(COLORS[i % len(COLORS)])
                painter.setPen(QPen(color, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                rx, ry = x + left * sx, y + top * sy
                rw, rh = (right - left) * sx, (bottom - top) * sy
                painter.drawRect(int(rx), int(ry), int(rw), int(rh))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(int(rx + 4), int(ry + 4), 23, 21, 3, 3)
                painter.setPen(QColor("#243629"))
                painter.drawText(int(rx + 4), int(ry + 4), 23, 21, Qt.AlignmentFlag.AlignCenter, str(i + 1))


class AnalysisWorker(QThread):
    ready = Signal(str, object)
    failed = Signal(str, str)
    progress = Signal(int, int, str)

    def __init__(self, paths: list[str], parent=None):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        for i, path in enumerate(self.paths):
            if self.isInterruptionRequested():
                break
            self.progress.emit(i, len(self.paths), Path(path).name)
            try:
                scan = analyze_scan(path)
                self.ready.emit(path, scan)
            except Exception as error:
                self.failed.emit(path, str(error))
            self.progress.emit(i + 1, len(self.paths), Path(path).name)


class ExportWorker(QThread):
    ready = Signal(str, object)
    failed = Signal(str, str)
    progress = Signal(int, int, str)

    def __init__(self, scans: list[dict], output_dir: Path | None,
                 output_format="original", jpeg_quality=95, parent=None):
        super().__init__(parent)
        self.scans = scans
        self.output_dir = output_dir
        self.output_format = output_format
        self.jpeg_quality = jpeg_quality

    def run(self):
        for i, scan in enumerate(self.scans):
            if self.isInterruptionRequested():
                break
            self.progress.emit(i, len(self.scans), scan["name"])
            try:
                results = export_scan(scan, self.output_dir,
                                      output_format=self.output_format,
                                      jpeg_quality=self.jpeg_quality)
                self.ready.emit(scan["source"], results)
            except Exception as error:
                self.failed.emit(scan["source"], str(error))
            self.progress.emit(i + 1, len(self.scans), scan["name"])


class PhotoCard(QWidget):
    rotate = Signal(int, int)
    bounds_changed = Signal(int, object)

    def __init__(self, index: int):
        super().__init__()
        self.index = index
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 13, 13, 12)
        layout.setSpacing(10)
        header = QHBoxLayout()
        header.addWidget(label(f"照片 0{index + 1}", "section"))
        header.addStretch()
        self.badge = label("等待导入", "badge")
        header.addWidget(self.badge)
        layout.addLayout(header)
        self.canvas = ImageCanvas("每张照片都可独立旋转")
        self.canvas.setMinimumHeight(210)
        layout.addWidget(self.canvas, 1)
        tools = QHBoxLayout()
        self.dimensions = label("—", "small")
        tools.addWidget(self.dimensions)
        tools.addStretch()
        self.rotate_left = QPushButton("↶  左转")
        self.rotate_right = QPushButton("右转  ↷")
        self.rotate_left.setToolTip("逆时针旋转 90°")
        self.rotate_right.setToolTip("顺时针旋转 90°")
        self.rotate_left.clicked.connect(lambda: self.rotate.emit(self.index, -90))
        self.rotate_right.clicked.connect(lambda: self.rotate.emit(self.index, 90))
        tools.addWidget(self.rotate_left)
        tools.addWidget(self.rotate_right)
        layout.addLayout(tools)
        self.bounds_toggle = QToolButton()
        self.bounds_toggle.setText("▸  微调裁切边界")
        self.bounds_toggle.setCheckable(True)
        self.bounds_toggle.setStyleSheet("border: none; padding: 0; text-align: left; color: #6f7968; font-size: 11px;")
        layout.addWidget(self.bounds_toggle)
        self.bounds_area = QWidget()
        self.bounds_area.setVisible(False)
        bounds_layout = QGridLayout(self.bounds_area)
        bounds_layout.setContentsMargins(0, 4, 0, 0)
        self.bounds = []
        for i, name in enumerate(("左", "上", "右", "下")):
            spin = QSpinBox()
            spin.setMaximum(100000)
            spin.setSuffix(" px")
            spin.setMinimumWidth(84)
            spin.valueChanged.connect(self.emit_bounds)
            bounds_layout.addWidget(label(name, "small"), i // 2, (i % 2) * 2)
            bounds_layout.addWidget(spin, i // 2, (i % 2) * 2 + 1)
            self.bounds.append(spin)
        layout.addWidget(self.bounds_area)
        self.bounds_toggle.toggled.connect(self.toggle_bounds)
        self.set_active(False)

    def toggle_bounds(self, shown):
        self.bounds_area.setVisible(shown)
        self.bounds_toggle.setText(tr(("▾" if shown else "▸") + "  微调裁切边界"))

    def set_active(self, active):
        self.rotate_left.setEnabled(active)
        self.rotate_right.setEnabled(active)
        self.bounds_toggle.setEnabled(active)
        self.bounds_area.setEnabled(active)

    def emit_bounds(self):
        self.bounds_changed.emit(self.index, [s.value() for s in self.bounds])

    def update_scan(self, scan: dict):
        frame = scan["frames"][self.index]
        self.canvas.set_image(preview_crop(scan, self.index))
        left, top, right, bottom = frame["bbox"]
        width, height = right - left, bottom - top
        if frame.get("rotation", 0) % 180:
            width, height = height, width
        self.dimensions.setText(f"{width:,} × {height:,} px")
        self.badge.setText(f"{frame.get('rotation', 0) % 360}°")
        self.badge.setStyleSheet("background: #e6edf4; color: #47617b; border-radius: 5px; padding: 4px 7px; font-size: 11px;")
        self.badge.setToolTip(tr("旋转角度，相对于导入后的原片方向"))
        for i, spin in enumerate(self.bounds):
            with QSignalBlocker(spin):
                spin.setMaximum(scan["width"] if i % 2 == 0 else scan["height"])
                spin.setValue(frame["bbox"][i])
        self.set_active(True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"半格 · HalfFrame {__version__}")
        self.resize(1370, 980)
        self.setMinimumSize(1050, 760)
        self.setAcceptDrops(True)
        self.scans: dict[str, dict] = {}
        self.items: dict[str, QListWidgetItem] = {}
        self.errors: dict[str, str] = {}
        self.output_dir: Path | None = None
        self.worker: QThread | None = None
        self.busy_kind = ""
        self.exported_count = 0
        self.export_adjusted_count = 0
        self.export_notes: list[str] = []
        self.export_errors: list[str] = []
        self.current_path: str | None = None
        self._updating = False
        self._close_when_idle = False
        self._status_parts = [("准备就绪 · 支持批量导入 JPG、TIFF", {})]
        self._export_destination: Path | None = None
        self.build_ui()
        self.setStyleSheet(STYLE)
        self.refresh_buttons()

    def build_ui(self):
        root = QWidget()
        root.setObjectName("workspace")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 28, 20, 20)
        side.setSpacing(13)
        side.addWidget(label("半格", "brand"))
        side.addWidget(label("HALFFRAME", "wordmark"))
        side.addWidget(label("作者：J.C. Lu", "muted"))
        side.addWidget(label(f"v{__version__}", "small"))
        self.language = QComboBox()
        self.language.addItem("简体中文", "zh")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(0 if LANGUAGE == "zh" else 1)
        self.language.currentIndexChanged.connect(self.change_language)
        side.addWidget(self.language)
        side.addSpacing(20)
        self.folder_button = QPushButton("选择扫描文件夹")
        self.folder_button.setObjectName("primary")
        self.folder_button.clicked.connect(self.pick_folder)
        side.addWidget(self.folder_button)
        self.add_button = QPushButton("选择照片文件")
        self.add_button.clicked.connect(self.pick_files)
        side.addWidget(self.add_button)
        self.import_hint = label("选择文件夹后，批量读取其中及子文件夹内的 JPG / TIFF。\n也可以拖入文件夹或照片文件。", "muted")
        self.import_hint.setWordWrap(True)
        side.addWidget(self.import_hint)
        side.addSpacing(15)
        self.queue_label = label("照片队列 · 0", "section")
        side.addWidget(self.queue_label)
        self.file_list = QListWidget()
        self.file_list.setSpacing(2)
        self.file_list.currentItemChanged.connect(self.select_item)
        side.addWidget(self.file_list, 1)
        self.remove_button = QPushButton("移除选中")
        self.remove_button.clicked.connect(self.remove_selected)
        side.addWidget(self.remove_button)
        side.addSpacing(6)
        local = label("全部处理均在本机完成\n原片保留，导出为独立文件", "small")
        local.setWordWrap(True)
        side.addWidget(local)
        qt_credit = label("Qt / PySide / Shiboken · LGPLv3\n© The Qt Company Ltd. and contributors", "small")
        qt_credit.setWordWrap(True)
        side.addWidget(qt_credit)
        self.licenses_button = QPushButton("开源许可与第三方声明")
        self.licenses_button.clicked.connect(self.show_licenses)
        side.addWidget(self.licenses_button)
        outer.addWidget(sidebar)

        main = QVBoxLayout()
        main.setContentsMargins(28, 26, 28, 18)
        main.setSpacing(10)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(7)
        heading.addWidget(label("一张扫描，两张照片。", "title"))
        heading.addWidget(label("自动分片 · 手动旋转 · 保留完整画面", "muted"))
        header.addLayout(heading)
        header.addStretch()
        self.export_current = QPushButton("导出这张")
        self.export_current.clicked.connect(lambda: self.start_export(False))
        header.addWidget(self.export_current)
        self.export_all = QPushButton("导出全部")
        self.export_all.setObjectName("primary")
        self.export_all.clicked.connect(lambda: self.start_export(True))
        header.addWidget(self.export_all)
        main.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setObjectName("workspace")
        content = QVBoxLayout(scroll_content)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(13)
        file_header = QHBoxLayout()
        self.file_title = label("把半格扫描交给这里", "fileTitle")
        self.file_info = label("", "small")
        file_header.addWidget(self.file_title)
        file_header.addStretch()
        file_header.addWidget(self.file_info)
        content.addLayout(file_header)

        source_panel = QFrame()
        source_panel.setObjectName("panel")
        source_layout = QHBoxLayout(source_panel)
        source_layout.setContentsMargins(13, 13, 16, 13)
        source_layout.setSpacing(20)
        original_layout = QVBoxLayout()
        original_layout.setSpacing(9)
        original_layout.addWidget(label("原始扫描 / 裁切范围", "section"))
        self.original = ImageCanvas("选择扫描文件夹，批量导入照片\n自动找到两张底片之间的分隔")
        self.original.setMinimumHeight(200)
        original_layout.addWidget(self.original, 1)
        source_layout.addLayout(original_layout, 5)

        settings = QVBoxLayout()
        settings.setSpacing(7)
        settings.addWidget(label("分隔线微调", "section"))
        self.axis = QComboBox()
        self.axis.addItem("左右分片  │", "vertical")
        self.axis.addItem("上下分片  ─", "horizontal")
        self.axis.currentIndexChanged.connect(self.axis_changed)
        settings.addWidget(self.axis)
        self.split_badge = label("自动定位中间的分隔区域", "small")
        self.split_badge.setWordWrap(True)
        settings.addWidget(self.split_badge)
        self.gap_sliders: list[QSlider] = []
        self.gap_spins: list[QSpinBox] = []
        for index, name in enumerate(("照片 1 结束于", "照片 2 开始于")):
            row = QHBoxLayout()
            row.addWidget(label(name, "small"))
            spin = QSpinBox()
            spin.setSuffix(" px")
            spin.setMaximum(100000)
            spin.setMinimumWidth(96)
            spin.valueChanged.connect(lambda value, i=index: self.gap_changed(i, value))
            row.addWidget(spin)
            settings.addLayout(row)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMaximum(100000)
            slider.valueChanged.connect(lambda value, i=index: self.gap_changed(i, value))
            settings.addWidget(slider)
            self.gap_spins.append(spin)
            self.gap_sliders.append(slider)
        settings.addStretch()
        self.reset_button = QPushButton("恢复自动结果")
        self.reset_button.clicked.connect(self.reset_current)
        settings.addWidget(self.reset_button)
        source_layout.addLayout(settings, 3)
        content.addWidget(source_panel)

        previews = QHBoxLayout()
        previews.setSpacing(14)
        self.cards = [PhotoCard(0), PhotoCard(1)]
        for card in self.cards:
            card.rotate.connect(self.rotate_frame)
            card.bounds_changed.connect(self.bounds_changed)
            previews.addWidget(card, 1)
        content.addLayout(previews, 1)
        self.review_note = label("保留外框与分隔处重叠，避免自动裁掉画面。方向由你手动调整。", "small")
        self.review_note.setWordWrap(True)
        content.addWidget(self.review_note)
        scroll.setWidget(scroll_content)
        main.addWidget(scroll, 1)

        format_row = QHBoxLayout()
        format_row.addWidget(label("导出格式", "small"))
        self.output_format = QComboBox()
        self.output_format.addItem("原格式", "original")
        self.output_format.addItem("JPG（有损）", "jpeg")
        self.output_format.addItem("16-bit TIFF", "tiff16")
        self.output_format.currentIndexChanged.connect(self.output_format_changed)
        format_row.addWidget(self.output_format)
        self.quality_label = label("JPG 质量", "small")
        format_row.addWidget(self.quality_label)
        self.jpeg_quality = QSpinBox()
        self.jpeg_quality.setRange(1, 100)
        self.jpeg_quality.setValue(95)
        self.jpeg_quality.setFixedWidth(76)
        format_row.addWidget(self.jpeg_quality)
        format_row.addStretch()
        self.same_folder = QCheckBox("保存到各原片文件夹")
        self.same_folder.toggled.connect(self.output_location_changed)
        format_row.addWidget(self.same_folder)
        main.addLayout(format_row)
        self.format_note = label("保留原始格式与位深。TIFF 无损；JPG 无损裁切会向外保留边界。", "small")
        self.format_note.setWordWrap(True)
        main.addWidget(self.format_note)

        bottom = QHBoxLayout()
        self.output_button = QPushButton("选择导出文件夹")
        self.output_button.clicked.connect(self.choose_output)
        bottom.addWidget(self.output_button)
        self.output_label = label("尚未选择", "small")
        self.output_label.setMinimumWidth(60)
        bottom.addWidget(self.output_label, 1)
        self.open_button = QPushButton("打开文件夹 ↗")
        self.open_button.clicked.connect(self.open_output)
        self.open_button.setEnabled(False)
        bottom.addWidget(self.open_button)
        main.addLayout(bottom)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        main.addWidget(self.progress)
        self.status = label("准备就绪 · 支持批量导入 JPG、TIFF", "small")
        self.status.setWordWrap(True)
        main.addWidget(self.status)
        outer.addLayout(main, 1)
        self.output_format_changed()
        self.change_language()

    def show_licenses(self):
        from .license_view import license_pages, resource_root
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("开源许可与第三方声明"))
        dialog.resize(800, 620)
        layout = QVBoxLayout(dialog)
        selector = QComboBox()
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        pages = license_pages(resource_root())
        for title, path in pages:
            selector.addItem(title, path)
        def display(index):
            path = pages[index][1]
            text = path.read_text(encoding="utf-8", errors="replace")
            browser.document().setBaseUrl(QUrl.fromLocalFile(str(path.parent) + "/"))
            if path.suffix.lower() == ".md":
                browser.setMarkdown(text)
            else:
                browser.setPlainText(text)
        selector.currentIndexChanged.connect(display)
        layout.addWidget(selector)
        layout.addWidget(browser, 1)
        display(0)
        # Keep a reference for a non-modal, offline-readable notice window.
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.license_dialog = dialog
        dialog.show()

    def set_status(self, key, **values):
        self._status_parts = [(key, values)]
        self.status.setText(tr(key, **values))

    def append_status(self, key, **values):
        self._status_parts.append((key, values))
        self.status.setText("".join(tr(k, **v) for k, v in self._status_parts))

    def change_language(self):
        global LANGUAGE
        LANGUAGE = self.language.currentData() or "zh"
        # Translate existing static text in place; keep file names, crop edits,
        # queue selection, progress, and a running worker intact.
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QLabel, QPushButton, QToolButton, QCheckBox)):
                widget.setText(translate_existing(widget.text()))
            if widget.toolTip():
                widget.setToolTip(translate_existing(widget.toolTip()))
            if isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    widget.setItemText(index, translate_existing(widget.itemText(index)))
        self.queue_label.setText(tr("照片队列 · {count}", count=len(self.items)))
        for path, item in self.items.items():
            if path in self.scans:
                self.update_item(path)
            elif path in self.errors:
                item.setText(Path(path).name + "\n" + tr("读取失败"))
            else:
                item.setText(Path(path).name + "\n" + tr("等待分析"))
        self._status_parts = [
            (key, {name: translate_existing(value) if isinstance(value, str) else value
                   for name, value in values.items()})
            for key, values in self._status_parts
        ]
        self.status.setText("".join(tr(key, **values) for key, values in self._status_parts))
        self.original.update()
        for card in self.cards:
            card.canvas.update()
        if self.current_scan():
            self.show_scan(self.current_path)
        self.output_format_changed()
        self.update_output_location()

    def output_format_changed(self):
        chosen = self.output_format.currentData()
        jpeg = chosen == "jpeg"
        self.quality_label.setVisible(jpeg)
        self.jpeg_quality.setVisible(jpeg)
        notes = {
            "original": "保留原始格式与位深。TIFF 无损；JPG 无损裁切会向外保留边界。",
            "jpeg": "JPG 会重新有损压缩；16-bit 原片转为 8-bit，ICC 保留。",
            "tiff16": "无损保存为 16-bit TIFF；8-bit 升为 16-bit 不会增加原片细节。",
        }
        self.format_note.setText(tr(notes.get(chosen, notes["original"])))

    def output_location_changed(self):
        self.update_output_location()
        self.refresh_buttons()

    def effective_output_folder(self):
        if self.same_folder.isChecked():
            source = self.current_path or next(iter(self.scans), None)
            return Path(source).parent if source else None
        return self.output_dir

    def update_output_location(self):
        if self.same_folder.isChecked():
            self.output_label.setText(tr("每张扫描的原片文件夹"))
            folder = self.effective_output_folder()
            self.output_label.setToolTip(str(folder) if folder else "")
        else:
            self.output_label.setText(str(self.output_dir) if self.output_dir else tr("尚未选择"))
            self.output_label.setToolTip(str(self.output_dir) if self.output_dir else "")
        self.open_button.setEnabled(self.effective_output_folder() is not None)

    def paths_from_inputs(self, paths):
        result = []
        recorded_by_folder: dict[Path, set[Path]] = {}
        output_resolved = self.output_dir.resolve() if self.output_dir and not self.same_folder.isChecked() else None
        for value in paths:
            path = Path(value).expanduser()
            is_folder = path.is_dir()
            candidates = sorted(path.rglob("*")) if is_folder else [path]
            for candidate in candidates:
                if not candidate.is_file() or candidate.suffix.lower() not in SUPPORTED:
                    continue
                resolved = candidate.resolve()
                if (is_folder and output_resolved and output_resolved != path.resolve()
                        and output_resolved in resolved.parents):
                    continue
                if is_folder:
                    parent = candidate.parent.resolve()
                    if parent not in recorded_by_folder:
                        recorded_by_folder[parent] = recorded_outputs(parent)
                    if resolved in recorded_by_folder[parent]:
                        continue
                text = str(resolved)
                if text not in self.items and text not in result:
                    result.append(text)
        return result

    def pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr("选择照片文件"), "", tr("扫描照片 (*.jpg *.jpeg *.tif *.tiff *.JPG *.JPEG *.TIF *.TIFF)"))
        self.add_paths(paths)

    def pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, tr("选择扫描文件夹"))
        if path:
            self.add_paths([path])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.busy_kind:
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not self.busy_kind:
            self.add_paths([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
            event.acceptProposedAction()

    def add_paths(self, values):
        if self.busy_kind or not values:
            return
        try:
            paths = self.paths_from_inputs(values)
        except OSError as error:
            QMessageBox.warning(self, tr("无法读取文件夹"), str(error))
            return
        if not paths:
            self.set_status("没有新的 JPG / TIFF 文件可导入。已在队列中的文件会自动跳过。")
            return
        for path in paths:
            item = QListWidgetItem(Path(path).name + "\n" + tr("等待分析"))
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.items[path] = item
            self.file_list.addItem(item)
        self.queue_label.setText(tr("照片队列 · {count}", count=len(self.items)))
        self.busy_kind = "分析"
        worker = AnalysisWorker(paths, self)
        self.worker = worker
        worker.ready.connect(self.analysis_ready)
        worker.failed.connect(self.analysis_failed)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.analysis_finished)
        self.refresh_buttons()
        self.set_status("正在定位分隔区域…")
        self.progress.setRange(0, 0)
        worker.start()

    def analysis_ready(self, path, scan):
        scan["_automatic"] = {"frames": copy.deepcopy(scan["frames"]), "split": copy.deepcopy(scan["split"])}
        self.scans[path] = scan
        self.update_item(path)
        if self.current_path is None or self.current_path == path:
            self.file_list.setCurrentItem(self.items[path])
            self.show_scan(path)
        self.refresh_buttons()

    def update_item(self, path):
        if path not in self.items:
            return
        scan = self.scans.get(path)
        if not scan:
            return
        review = scan["split"].get("review", False)
        state = tr("需要复核" if review else "已就绪")
        if scan["split"].get("export_blocked"):
            state = tr("请先定位分界")
        if scan.get("_exported"):
            state = tr("已导出 · {state}", state=state)
        self.items[path].setText(tr("{name}\n{state}  ·  2 张照片", name=scan["name"], state=state))

    def analysis_failed(self, path, error):
        self.errors[path] = error
        self.items[path].setText(Path(path).name + "\n" + tr("读取失败"))
        self.items[path].setToolTip(path + "\n\n" + error)

    def analysis_finished(self):
        self.busy_kind = ""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self.refresh_buttons()
        self.set_status("分析完成 · {count} 张扫描 / {photos} 张照片", count=len(self.scans), photos=2 * len(self.scans))
        if self.errors:
            self.append_status(" · {count} 张读取失败（选择查看原因）", count=len(self.errors))
        if self._close_when_idle:
            self.close()

    def update_progress(self, current, total, name):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(current)
        key = "正在导出 · {current} / {total} · {name}" if self.busy_kind == "导出" else "正在分析 · {current} / {total} · {name}"
        self.set_status(key, current=current, total=total, name=name)

    def select_item(self, item, previous=None):
        if item is None:
            self.current_path = None
            self.refresh_buttons()
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        self.current_path = path
        if path in self.scans:
            self.show_scan(path)
        else:
            self.clear_preview()
            self.file_title.setText(Path(path).name)
            if path in self.errors:
                self.set_status("读取失败 · {error}", error=self.errors[path])
        self.refresh_buttons()

    def show_scan(self, path):
        self.current_path = path
        scan = self.scans[path]
        self._updating = True
        self.file_title.setText(scan["name"])
        self.file_title.setToolTip(path)
        self.file_info.setText(f"{scan['format']} · {scan['width']:,} × {scan['height']:,} · {scan.get('bit_depth', 8)} bit")
        self.original.set_image(scan["preview"], scan)
        self.axis.setCurrentIndex(0 if scan["split"]["axis"] == "vertical" else 1)
        dimension = scan["width"] if scan["split"]["axis"] == "vertical" else scan["height"]
        for index, key in enumerate(("start", "end")):
            for widget in (self.gap_sliders[index], self.gap_spins[index]):
                with QSignalBlocker(widget):
                    widget.setRange(1, dimension - 1)
                    widget.setValue(int(scan["split"][key]))
        if scan["split"].get("manual"):
            self.split_badge.setText(tr("分隔范围已手动调整"))
        elif scan["split"].get("export_blocked"):
            self.split_badge.setText(tr("请先定位分界 · 当前保留完整扫描"))
        elif scan["split"].get("review", False):
            self.split_badge.setText(tr("分隔位置待复核 · 可拖动下方滑块"))
        else:
            self.split_badge.setText(tr("已定位分界 · 重叠保边，保留完整画面"))
        self.split_badge.setToolTip(scan["split"].get("reason", ""))
        for card in self.cards:
            card.update_scan(scan)
        self._updating = False
        self.review_note.setText(tr("保留外框与分隔处重叠，避免自动裁掉画面。方向由你手动调整。"))
        if scan["format"] == "JPEG":
            self.review_note.setText(self.review_note.text() + " " + tr("原格式 JPG 向外对齐裁切边界；必要时用方向标签保全边缘。"))
        self.refresh_buttons()

    def clear_preview(self):
        self.original.set_image(None)
        self.file_info.setText("")
        for card in self.cards:
            card.canvas.set_image(None)
            card.dimensions.setText("—")
            card.badge.setText(tr("等待分析"))
            card.set_active(False)

    def current_scan(self):
        return self.scans.get(self.current_path)

    def mark_edited(self, scan):
        scan.pop("_exported", None)
        self.update_item(scan["source"])

    def rotate_frame(self, index, angle):
        scan = self.current_scan()
        if not scan:
            return
        frame = scan["frames"][index]
        frame["rotation"] = (frame.get("rotation", 0) + angle) % 360
        frame["manual_rotation"] = True
        frame["review"] = False
        self.mark_edited(scan)
        self.cards[index].update_scan(scan)

    def axis_changed(self):
        scan = self.current_scan()
        if self._updating or not scan:
            return
        axis = self.axis.currentData()
        dimension = scan["width"] if axis == "vertical" else scan["height"]
        split = scan["split"]
        split.update(axis=axis, start=dimension // 2, end=dimension // 2, manual=True, review=False, export_blocked=False)
        w, h = scan["width"], scan["height"]
        if axis == "vertical":
            scan["frames"][0]["bbox"] = [0, 0, split["start"], h]
            scan["frames"][1]["bbox"] = [split["end"], 0, w, h]
        else:
            scan["frames"][0]["bbox"] = [0, 0, w, split["start"]]
            scan["frames"][1]["bbox"] = [0, split["end"], w, h]
        for frame in scan["frames"]:
            frame.update(rotation=0, review=False, manual_rotation=False)
        self.mark_edited(scan)
        self.show_scan(self.current_path)

    def gap_changed(self, index, value):
        scan = self.current_scan()
        if self._updating or not scan:
            return
        split = scan["split"]
        dimension = scan["width"] if split["axis"] == "vertical" else scan["height"]
        value = max(1, min(value, dimension - 1))
        if index == 0:
            split["start"] = value
            split["end"] = min(split["end"], value)
        else:
            split["end"] = value
            split["start"] = max(split["start"], value)
        split.update(manual=True, review=False, export_blocked=False)
        first, second = scan["frames"]
        if split["axis"] == "vertical":
            first["bbox"][2] = split["start"]
            first["bbox"][0] = min(first["bbox"][0], split["start"] - 1)
            second["bbox"][0] = split["end"]
            second["bbox"][2] = max(second["bbox"][2], split["end"] + 1)
        else:
            first["bbox"][3] = split["start"]
            first["bbox"][1] = min(first["bbox"][1], split["start"] - 1)
            second["bbox"][1] = split["end"]
            second["bbox"][3] = max(second["bbox"][3], split["end"] + 1)
        self.mark_edited(scan)
        self.show_scan(self.current_path)

    def bounds_changed(self, index, bbox):
        scan = self.current_scan()
        if self._updating or not scan:
            return
        left, top, right, bottom = bbox
        left = min(max(0, left), scan["width"] - 1)
        top = min(max(0, top), scan["height"] - 1)
        right = max(left + 1, min(right, scan["width"]))
        bottom = max(top + 1, min(bottom, scan["height"]))
        # Retain overlap at the separator; do not create an unexported gap.
        other = scan["frames"][1 - index]["bbox"]
        if scan["split"]["axis"] == "vertical":
            if index == 0:
                right = max(right, other[0])
                left = min(left, right - 1)
            else:
                left = min(left, other[2])
                right = max(right, left + 1)
        else:
            if index == 0:
                bottom = max(bottom, other[1])
                top = min(top, bottom - 1)
            else:
                top = min(top, other[3])
                bottom = max(bottom, top + 1)
        scan["frames"][index]["bbox"] = [left, top, right, bottom]
        scan["split"].update(manual=True, review=False, export_blocked=False)
        if scan["split"]["axis"] == "vertical":
            scan["split"]["start" if index == 0 else "end"] = right if index == 0 else left
        else:
            scan["split"]["start" if index == 0 else "end"] = bottom if index == 0 else top
        self.mark_edited(scan)
        self.show_scan(self.current_path)

    def reset_current(self):
        scan = self.current_scan()
        if scan:
            scan["frames"] = copy.deepcopy(scan["_automatic"]["frames"])
            scan["split"] = copy.deepcopy(scan["_automatic"]["split"])
            self.mark_edited(scan)
            self.show_scan(self.current_path)

    def remove_selected(self):
        if self.busy_kind or not self.current_path:
            return
        path = self.current_path
        item = self.items.pop(path)
        self.scans.pop(path, None)
        self.errors.pop(path, None)
        self.file_list.takeItem(self.file_list.row(item))
        self.queue_label.setText(tr("照片队列 · {count}", count=len(self.items)))
        if not self.items:
            self.current_path = None
            self.clear_preview()
            self.file_title.setText(tr("把半格扫描交给这里"))
        self.refresh_buttons()

    def choose_output(self):
        initial = str(self.output_dir) if self.output_dir else str(Path(self.current_path).parent if self.current_path else Path.home() / "Pictures")
        selected = QFileDialog.getExistingDirectory(self, tr("选择导出文件夹"), initial)
        if selected:
            self.output_dir = Path(selected)
            self.update_output_location()
        return bool(selected)

    def open_output(self):
        folder = self.effective_output_folder()
        if folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def start_export(self, all_scans):
        if self.busy_kind:
            return
        scans = list(self.scans.values()) if all_scans else [self.current_scan()]
        scans = [scan for scan in scans if scan]
        if not scans:
            return
        blocked = [scan for scan in scans if scan["split"].get("export_blocked")
                   and not scan["split"].get("manual")]
        ready = [scan for scan in scans if not scan["split"].get("export_blocked")
                 or scan["split"].get("manual")]
        if blocked and (not all_scans or not ready):
            QMessageBox.information(self, tr("请先调整分隔位置"),
                                    tr("{count} 张扫描尚未定位分界。请选中它们并调整滑块后再导出。", count=len(blocked)))
            return
        self.export_skipped = [scan["source"] for scan in blocked]
        scans = ready
        if not self.same_folder.isChecked() and not self.output_dir and not self.choose_output():
            return
        snapshots = []
        for scan in scans:
            snapshot = dict(scan)
            snapshot["frames"] = copy.deepcopy(scan["frames"])
            snapshot["split"] = copy.deepcopy(scan["split"])
            snapshots.append(snapshot)
        self.exported_count = 0
        self.export_adjusted_count = 0
        self.export_notes = []
        self.export_errors = []
        self.busy_kind = "导出"
        self._export_destination = None if self.same_folder.isChecked() else self.output_dir
        worker = ExportWorker(snapshots, self._export_destination,
                              output_format=self.output_format.currentData(),
                              jpeg_quality=self.jpeg_quality.value(), parent=self)
        self.worker = worker
        worker.ready.connect(self.export_ready)
        worker.failed.connect(self.export_failed)
        worker.progress.connect(self.update_progress)
        worker.finished.connect(self.export_finished)
        self.refresh_buttons()
        worker.start()

    def export_ready(self, path, results):
        self.exported_count += len(results)
        for result in results:
            if tuple(result.get("actual_bbox", ())) != tuple(result.get("requested_bbox", ())):
                self.export_adjusted_count += 1
            for note in result.get("metadata_notes", []):
                if note not in self.export_notes:
                    self.export_notes.append(note)
        if path in self.scans:
            self.scans[path]["_exported"] = True
            self.update_item(path)

    def export_failed(self, path, error):
        self.export_errors.append(f"{Path(path).name}: {error}")

    def export_finished(self):
        self.busy_kind = ""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self.refresh_buttons()
        folder = str(self._export_destination) if self._export_destination else tr("每张扫描的原片文件夹")
        self.set_status("导出完成 · {count} 张照片 · {folder}", count=self.exported_count, folder=folder)
        if self.export_errors:
            self.append_status(" · {count} 个文件失败", count=len(self.export_errors))
        if self.export_skipped:
            self.append_status(" · 已跳过 {count} 张待定位扫描（仍保留在队列）", count=len(self.export_skipped))
            self.export_notes.append(tr("待定位扫描：\n{names}", names="\n".join(self.export_skipped)))
        if self.export_adjusted_count:
            self.append_status(" · {count} 张 JPG 已向外保边，详情见处理记录", count=self.export_adjusted_count)
        self.status.setToolTip("\n".join(self.export_notes))
        if self.export_errors and not self._close_when_idle:
            box = QMessageBox(self)
            box.setWindowTitle(tr("部分文件未能导出"))
            box.setIcon(QMessageBox.Icon.Warning)
            box.setText(tr("已导出 {count} 张照片。{errors} 个扫描文件导出失败。", count=self.exported_count, errors=len(self.export_errors)))
            box.setDetailedText("\n\n".join(self.export_errors))
            box.exec()
        if self._close_when_idle:
            self.close()

    def refresh_buttons(self):
        busy = bool(self.busy_kind)
        current = self.current_scan() is not None
        self.add_button.setEnabled(not busy)
        self.folder_button.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and self.current_path is not None)
        blocked = current and bool(self.current_scan()["split"].get("export_blocked"))
        self.export_current.setEnabled(not busy and current and not blocked)
        self.export_current.setToolTip(tr("请先调整分隔位置") if blocked else "")
        self.export_all.setEnabled(not busy and bool(self.scans))
        self.output_button.setEnabled(not busy and not self.same_folder.isChecked())
        self.same_folder.setEnabled(not busy)
        self.output_format.setEnabled(not busy)
        self.jpeg_quality.setEnabled(not busy)
        self.axis.setEnabled(current and self.busy_kind != "导出")
        self.reset_button.setEnabled(current and self.busy_kind != "导出")
        for widget in self.gap_sliders + self.gap_spins:
            widget.setEnabled(current and self.busy_kind != "导出")
        for card in self.cards:
            card.set_active(current and self.busy_kind != "导出")
        self.update_output_location()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            # Interrupt between source files, avoiding a half-written export.
            self._close_when_idle = True
            self.worker.requestInterruption()
            self.set_status("正在完成当前文件，然后关闭窗口…")
            event.ignore()
            return
        event.accept()


def main(argv=None):
    args = sys.argv if argv is None else argv
    app = QApplication.instance() or QApplication(args)
    app.setApplicationName("HalfFrame")
    app.setApplicationDisplayName("半格 · HalfFrame")
    app.setOrganizationName("HalfFrame")
    from .runtime_terms import confirm_runtime_terms
    if not confirm_runtime_terms():
        return 0
    window = MainWindow()
    window.show()
    paths = [arg for arg in args[1:] if not arg.startswith("-")]
    if paths:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: window.add_paths(paths))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
