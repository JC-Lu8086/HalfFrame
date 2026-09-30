# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Analysis works on previews. Exports always reload original pixel data."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time

from PIL import Image

from .image_io import load_image, export_crop, ImageIOError
from .splitter import detect_split, split_boxes


def preview_crop(scan: dict, index: int) -> Image.Image:
    frame = scan["frames"][index]
    preview = scan["preview"]
    sx, sy = preview.width / scan["width"], preview.height / scan["height"]
    l, t, r, b = frame["bbox"]
    box = (round(l*sx), round(t*sy), round(r*sx), round(b*sy))
    result = preview.crop(box)
    return result.rotate(-int(frame.get("rotation", 0)), expand=True)


def analyze_scan(path: str | Path) -> dict:
    data = load_image(path)
    split = detect_split(data.preview, data.width, data.height)
    scan = dict(source=str(data.source), name=data.source.name, format=data.format,
                width=data.width, height=data.height, bit_depth=data.bit_depth,
                preview=data.preview, split=split, frames=[],
                source_signature=list(data.metadata["source_signature"]))
    for bbox in split_boxes(split, data.width, data.height):
        scan["frames"].append(dict(bbox=bbox, rotation=0, manual_rotation=False,
                                  review=False))
    return scan


def export_scan(scan: dict, output_dir: str | Path | None, output_format: str = "original", jpeg_quality: int = 95) -> list[dict]:
    if scan["split"].get("export_blocked") and not scan["split"].get("manual"):
        raise ImageIOError("分隔位置尚未确认。为避免裁掉画面，请先调整分隔线或选择分片方向，再导出。")
    source = Path(scan["source"])
    output = Path(output_dir).expanduser().resolve() if output_dir is not None else source.parent
    output.mkdir(parents=True, exist_ok=True)
    signature = source.stat()
    if list((signature.st_size, signature.st_mtime_ns)) != scan.get("source_signature"):
        raise ImageIOError("原文件在分析后发生了变化，请重新导入再导出。")
    data = load_image(source)
    if output_format not in ("original", "jpeg", "tiff16"):
        raise ImageIOError("不支持的输出格式 / Unsupported output format")
    suffix = {"jpeg": ".jpg", "tiff16": ".tif"}.get(output_format, source.suffix.lower())
    index = 0
    # A reservation prevents two app instances from choosing the same pair.
    while True:
        stem = source.stem + (f"__{index + 1}" if index else "")
        paths = [output / f"{stem}_{i}{suffix}" for i in (1, 2)]
        manifest = output / f"{stem}_处理记录.json"
        lock = output / f".{stem}.halfframe-lock"
        index += 1
        if any(p.exists() for p in paths + [manifest]):
            continue
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
            break
        except FileExistsError:
            continue
    results, created = [], []
    try:
        for frame, destination in zip(scan["frames"], paths):
            if output_format == "original":
                result = export_crop(data, frame["bbox"], frame["rotation"], destination)
            else:
                from .export_formats import export_converted_crop
                result = export_converted_crop(data, frame["bbox"], frame["rotation"], destination,
                                               output_format, jpeg_quality)
            created.append(destination)
            result.update(path=str(destination), source=str(source),
                          requested_bbox=frame["bbox"], rotation=frame["rotation"],
                          manual_rotation=bool(frame.get("manual_rotation")),
                          needs_review=bool(frame.get("review") or scan["split"].get("review")))
            results.append(result)
        record = dict(application="HalfFrame 0.2.2", author="J.C. Lu", exported_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                      source=str(source), output_format=output_format, split=scan["split"], outputs=results)
        with manifest.open("x", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
        return results
    except Exception:
        # Treat the two frames as one transaction; do not leave half a pair.
        for file in created:
            file.unlink(missing_ok=True)
        raise
    finally:
        lock.unlink(missing_ok=True)
