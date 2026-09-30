# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Pixel-preserving TIFF and DCT-preserving JPEG crop/quarter-turn export.

All public geometry is in the visually upright (EXIF-normalized) source space.
JPEG boundaries are expanded to include complete MCU blocks. Partial blocks
at the original edges are kept; no requested picture content is discarded.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import errno
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
from PIL import Image
import piexif
import tifffile


class ImageIOError(ValueError):
    """An actionable input/export error suitable for the application UI."""


@dataclass
class ImageData:
    pixels: np.ndarray
    preview: Image.Image
    width: int
    height: int
    format: str
    bit_depth: int
    metadata: dict[str, Any]
    source: Path


def _orient(array: np.ndarray, orientation: int) -> np.ndarray:
    if orientation == 2:
        return np.fliplr(array)
    if orientation == 3:
        return np.rot90(array, 2)
    if orientation == 4:
        return np.flipud(array)
    if orientation == 5:
        return array.swapaxes(0, 1)
    if orientation == 6:
        return np.rot90(array, -1)
    if orientation == 7:
        return np.flip(array.swapaxes(0, 1), axis=(0, 1))
    if orientation == 8:
        return np.rot90(array, 1)
    return array


def _orientation(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = 1
    return number if 1 <= number <= 8 else 1


def _preview(array: np.ndarray, *, miniswhite: bool = False) -> Image.Image:
    # Downsample before converting 16-bit arrays; the full-resolution pixels
    # are retained separately and never converted during TIFF export.
    step = max(1, math.ceil(max(array.shape[:2]) / 2000))
    small = array[::step, ::step]
    if array.dtype.itemsize == 2:
        small = (small.astype(np.uint32) // 257).astype(np.uint8)
    else:
        small = small.astype(np.uint8, copy=False)
    if miniswhite:
        small = 255 - small
    if small.ndim == 3 and small.shape[2] == 1:
        small = small[:, :, 0]
    result = Image.fromarray(np.ascontiguousarray(small)).convert("RGB")
    result.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
    return result


def _tag(page: Any, code: int, default: Any = None) -> Any:
    tag = page.tags.get(code)
    return tag.value if tag is not None else default


def _number(value: Any) -> float:
    if isinstance(value, tuple) and len(value) == 2:
        return value[0] / value[1] if value[1] else 1.0
    return float(value)


def _jpeg_header_segments(blob: bytes):
    """Yield (marker, start, end, payload), leaving entropy data untouched."""
    if not blob.startswith(b"\xff\xd8"):
        raise ImageIOError("文件不是有效的 JPEG 图片。")
    offset = 2
    while offset < len(blob):
        start = offset
        if blob[offset] != 255:
            raise ImageIOError("JPEG 文件头损坏。")
        while offset < len(blob) and blob[offset] == 255:
            offset += 1
        if offset >= len(blob):
            raise ImageIOError("JPEG 文件不完整。")
        marker = blob[offset]
        offset += 1
        if marker in (0xD9, 0xDA):
            return
        if marker in (0x01, *range(0xD0, 0xD9)):
            yield marker, start, offset, b""
            continue
        if offset + 2 > len(blob):
            raise ImageIOError("JPEG 文件不完整。")
        length = int.from_bytes(blob[offset:offset + 2], "big")
        end = offset + length
        if length < 2 or end > len(blob):
            raise ImageIOError("JPEG 文件段损坏。")
        yield marker, start, end, blob[offset + 2:end]
        offset = end


def _jpeg_mcu(blob: bytes) -> tuple[int, int]:
    for marker, _, _, payload in _jpeg_header_segments(blob):
        if marker in (0xC0, 0xC1, 0xC2):
            if len(payload) < 6 or payload[0] != 8:
                raise ImageIOError("目前仅支持 8 位 JPEG；高位深请使用 TIFF。")
            count = payload[5]
            if len(payload) < 6 + 3 * count or count < 1:
                raise ImageIOError("JPEG 采样信息损坏。")
            sampling = [payload[7 + 3 * i] for i in range(count)]
            return max(v >> 4 for v in sampling) * 8, max(v & 15 for v in sampling) * 8
    raise ImageIOError("不支持此 JPEG 编码方式；请使用标准 JPEG 或 TIFF。")


def load_image(path: str | Path) -> ImageData:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise ImageIOError(f"找不到图片：{source.name}")
    stat = source.stat()
    signature = (stat.st_size, stat.st_mtime_ns)
    try:
        with source.open("rb") as handle:
            magic = handle.read(4)
        if magic[:2] in (b"II", b"MM"):
            with tifffile.TiffFile(source) as tif:
                if len(tif.pages) != 1:
                    raise ImageIOError("不支持多页 TIFF。请先将每一页另存为单独的 TIFF，以免遗漏照片。")
                page = tif.pages[0]
                photo = int(page.photometric)
                if photo not in (0, 1, 2):
                    raise ImageIOError("此 TIFF 的色彩模式暂不支持。请使用灰度、RGB 或 RGBA TIFF。")
                pixels = page.asarray()
                if int(page.planarconfig or 1) == 2 and pixels.ndim == 3:
                    pixels = np.moveaxis(pixels, 0, -1)
                if pixels.ndim not in (2, 3) or (pixels.ndim == 3 and pixels.shape[-1] not in (1, 2, 3, 4)):
                    raise ImageIOError("此 TIFF 不是受支持的二维照片。")
                if pixels.dtype.kind != "u" or pixels.dtype.itemsize not in (1, 2):
                    raise ImageIOError("目前支持 8 位或 16 位无符号整数 TIFF。")
                orient = _orientation(_tag(page, 274, 1))
                raw_h, raw_w = pixels.shape[:2]
                resolution = (_number(_tag(page, 282, 1)), _number(_tag(page, 283, 1)))
                if orient in (5, 6, 7, 8):
                    resolution = resolution[::-1]
                # Keep well-defined descriptive tags, never stale offsets,
                # thumbnails, strip tables, crop geometry or MakerNote offsets.
                descriptive = {}
                for code in (269, 270, 271, 272, 285, 306, 315, 316, 33432):
                    value = _tag(page, code)
                    if isinstance(value, str) and value:
                        if code == 270 and value.lstrip().startswith(("{", "[", "<?xml", "<OME", "ImageJ=")):
                            # Structured descriptions encode old dimensions/axes.
                            # Copying them would misdescribe the cropped output.
                            continue
                        descriptive[code] = value
                meta = {
                    "orientation": orient, "raw_size": (raw_w, raw_h),
                    "photometric": photo, "extrasamples": tuple(int(x) for x in page.extrasamples),
                    "resolution": resolution, "resolutionunit": int(_tag(page, 296, 1)),
                    "icc_profile": _tag(page, 34675), "descriptive_tags": descriptive,
                    "source_signature": signature,
                }
                pixels = _orient(pixels, orient)
                preview = _preview(pixels, miniswhite=photo == 0)
                return ImageData(pixels, preview, pixels.shape[1], pixels.shape[0], "TIFF", pixels.dtype.itemsize * 8, meta, source)
        if magic[:2] == b"\xff\xd8":
            blob = source.read_bytes()
            mcu = _jpeg_mcu(blob)
            with Image.open(source) as opened:
                orient = _orientation(opened.getexif().get(274, 1))
                raw_size = opened.size
                pixels = np.array(opened.convert("RGB"))
                meta = {
                    "orientation": orient, "raw_size": raw_size, "mcu": mcu,
                    "icc_profile": opened.info.get("icc_profile"),
                    "source_signature": signature,
                }
            pixels = _orient(pixels, orient)
            return ImageData(pixels, _preview(pixels), pixels.shape[1], pixels.shape[0], "JPEG", 8, meta, source)
        raise ImageIOError("仅支持 JPG、JPEG、TIF 或 TIFF 图片。")
    except ImageIOError:
        raise
    except Exception as exc:
        raise ImageIOError(f"无法读取 {source.name}：{exc}") from exc


def _bbox(bbox: Any, width: int, height: int) -> tuple[int, int, int, int]:
    if len(bbox) != 4 or not all(math.isfinite(float(x)) for x in bbox):
        raise ImageIOError("裁切范围必须包含四个有效坐标。")
    left, top = max(0, math.floor(bbox[0])), max(0, math.floor(bbox[1]))
    right, bottom = min(width, math.ceil(bbox[2])), min(height, math.ceil(bbox[3]))
    if left >= right or top >= bottom:
        raise ImageIOError("裁切范围为空或位于图片之外。")
    return left, top, right, bottom


def _map_box(box: tuple[int, int, int, int], orientation: int, width: int, height: int, inverse: bool = False):
    def point(x: int, y: int):
        if inverse:
            return {
                1: (x, y), 2: (width - x, y), 3: (width - x, height - y),
                4: (x, height - y), 5: (y, x), 6: (y, height - x),
                7: (width - y, height - x), 8: (width - y, x),
            }[orientation]
        return {
            1: (x, y), 2: (width - x, y), 3: (width - x, height - y),
            4: (x, height - y), 5: (y, x), 6: (height - y, x),
            7: (height - y, width - x), 8: (y, width - x),
        }[orientation]
    points = [point(x, y) for x in (box[0], box[2]) for y in (box[1], box[3])]
    return min(x for x, y in points), min(y for x, y in points), max(x for x, y in points), max(y for x, y in points)


def jpegtran_path() -> str:
    candidates = []
    binary = "jpegtran.exe" if os.name == "nt" else "jpegtran"
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        candidates.append(str(Path(bundle) / "bin" / binary))
    candidates.extend([str(Path(__file__).resolve().parent.parent / "bin" / binary),
                       shutil.which(binary)])
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise ImageIOError("缺少 JPEG 无损裁切组件 jpegtran；请安装完整版本，或安装 libjpeg-turbo 后重试。")


def _jpeg_transform(orientation: int, rotation: int) -> list[str]:
    return {1: [], 2: ["-flip", "horizontal"], 3: ["-rotate", "180"], 4: ["-flip", "vertical"], 5: ["-transpose"], 6: ["-rotate", "90"], 7: ["-transverse"], 8: ["-rotate", "270"]}[_composed_orientation(orientation, rotation)]


def _composed_orientation(orientation: int, rotation: int) -> int:
    """EXIF orientation for source normalization followed by a quarter turn."""
    marker = np.arange(12).reshape(3, 4)
    expected = np.rot90(_orient(marker, orientation), -(rotation // 90))
    for value in range(1, 9):
        candidate = _orient(marker, value)
        if candidate.shape == expected.shape and np.array_equal(candidate, expected):
            return value
    raise AssertionError("D4 transform composition failed")


def _clean_jpeg_exif(path: Path, width: int, height: int, orientation: int = 1) -> list[str]:
    """Update EXIF using encoded pixel dimensions and the display orientation."""
    blob = path.read_bytes()
    exif_segments = [(start, end, payload) for marker, start, end, payload in _jpeg_header_segments(blob) if marker == 0xE1 and payload.startswith(b"Exif\x00\x00")]
    xmp_segments = [(start, end, payload) for marker, start, end, payload in _jpeg_header_segments(blob)
                    if marker == 0xE1 and payload.startswith((b"http://ns.adobe.com/xap/1.0/", b"http://ns.adobe.com/xmp/extension/"))]
    notes = []
    if xmp_segments:
        notes.append("已移除可能包含旧方向、裁切信息或缩略图的 XMP；ICC 与标准 EXIF 保留。")
    if exif_segments:
        try:
            exif = piexif.load(exif_segments[0][2])
        except Exception:
            exif = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
            notes.append("原 EXIF 数据损坏，已移除并重建方向和尺寸标签。")
    else:
        exif = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
    exif["0th"][piexif.ImageIFD.Orientation] = orientation
    exif["0th"][piexif.ImageIFD.ImageWidth] = width
    exif["0th"][piexif.ImageIFD.ImageLength] = height
    exif["Exif"][piexif.ExifIFD.PixelXDimension] = width
    exif["Exif"][piexif.ExifIFD.PixelYDimension] = height
    exif["1st"] = {}
    exif["thumbnail"] = None
    # MakerNotes may contain offsets into the original EXIF block. Retaining
    # them after rebuilding EXIF can create corrupt references.
    if piexif.ExifIFD.MakerNote in exif["Exif"]:
        del exif["Exif"][piexif.ExifIFD.MakerNote]
        notes.append("已移除可能失效的厂商 MakerNote；保留标准 EXIF 和 ICC 色彩配置。")
    try:
        # Some EXIF readers expect a trailing next-IFD pointer even for the
        # final EXIF sub-IFD, which piexif omits. Harmless padding keeps those
        # readers from reporting a truncated EXIF block when it has no values
        # stored after its directory entries.
        payload = piexif.dump(exif) + b"\x00\x00\x00\x00"
    except Exception as exc:
        raise ImageIOError(f"无法安全更新 JPEG 的 EXIF 信息：{exc}") from exc
    if len(payload) + 2 > 65535:
        raise ImageIOError("JPEG 的 EXIF 信息过大，无法安全写入。")
    insertion = b"\xff\xe1" + (len(payload) + 2).to_bytes(2, "big") + payload
    # Replace only EXIF APP1 records. In particular, retain ICC APP2 bytes and
    # all compressed image data exactly as produced by jpegtran.
    chunks = [blob[:2], insertion]
    previous = 2
    for start, end, _ in sorted(exif_segments + xmp_segments):
        chunks.append(blob[previous:start])
        previous = end
    chunks.append(blob[previous:])
    path.write_bytes(b"".join(chunks))
    return notes


def _run_jpegtran(args: list[str], source: Path, destination: Path):
    process = subprocess.run([jpegtran_path(), "-copy", "all", "-perfect", *args, "-outfile", str(destination), str(source)], capture_output=True, timeout=180,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if process.returncode:
        reason = process.stderr.decode("utf-8", errors="replace").strip()
        raise ImageIOError(f"JPEG 无损处理失败：{reason}")


def export_crop(data: ImageData, bbox: tuple[int, int, int, int], rotation: int, destination: str | Path) -> dict[str, Any]:
    """Export without overwriting, returning actual upright-source bounds.

    ``rotation`` is clockwise. JPEG ``actual_bbox`` can be slightly larger
    than requested, to preserve every requested pixel without recompression.
    TIFF pixel values are preserved exactly (including 16-bit channels).
    """
    if rotation not in (0, 90, 180, 270):
        raise ImageIOError("旋转角度仅支持 0、90、180 或 270 度。")
    destination = Path(destination).expanduser().absolute()
    if destination.exists():
        raise ImageIOError(f"输出文件已存在，不会覆盖：{destination.name}")
    if destination.suffix.lower() not in ({".jpg", ".jpeg"} if data.format == "JPEG" else {".tif", ".tiff"}):
        raise ImageIOError("输出扩展名必须与原图格式相同。")
    try:
        stat = data.source.stat()
        if (stat.st_size, stat.st_mtime_ns) != data.metadata.get("source_signature"):
            raise ImageIOError("原图在读取后发生了变化，请重新添加图片再导出。")
    except OSError as exc:
        raise ImageIOError(f"无法访问原图：{exc}") from exc
    requested = _bbox(bbox, data.width, data.height)
    actual = requested
    destination.parent.mkdir(parents=True, exist_ok=True)
    notes = []
    orientation_storage = "pixels"
    stored_orientation = 1
    try:
        with tempfile.TemporaryDirectory(prefix=".halfframe-", dir=destination.parent) as temporary:
            temp = Path(temporary)
            final = temp / ("result.jpg" if data.format == "JPEG" else "result.tif")
            if data.format == "TIFF":
                left, top, right, bottom = actual
                pixels = np.ascontiguousarray(np.rot90(data.pixels[top:bottom, left:right], -(rotation // 90)))
                height, width = pixels.shape[:2]
                pixel_size = (width, height)
                resolution = data.metadata["resolution"]
                if rotation in (90, 270):
                    resolution = resolution[::-1]
                extra = [(274, "H", 1, 1, False)]
                for code, value in data.metadata["descriptive_tags"].items():
                    extra.append((code, "s", 0, value, False))
                icc = data.metadata.get("icc_profile")
                if icc:
                    extra.append((34675, "B", len(icc), icc, False))
                tifffile.imwrite(final, pixels, photometric=data.metadata["photometric"], planarconfig="contig", extrasamples=data.metadata["extrasamples"] or None, compression="deflate", resolution=resolution, resolutionunit=data.metadata["resolutionunit"], metadata=None, software="HalfFrame 0.2.2 by J.C. Lu", extratags=extra, bigtiff=pixels.nbytes >= 4_000_000_000)
                notes.append("TIFF 使用无损压缩；保留像素位深、ICC、分辨率和常见描述标签；不保留旧 XMP、缩略图和厂商私有标签。")
            elif data.format == "JPEG":
                raw_w, raw_h = data.metadata["raw_size"]
                orient = data.metadata["orientation"]
                raw = _map_box(requested, orient, raw_w, raw_h, inverse=True)
                mx, my = data.metadata["mcu"]
                raw = ((raw[0] // mx) * mx, (raw[1] // my) * my,
                       min(raw_w, math.ceil(raw[2] / mx) * mx),
                       min(raw_h, math.ceil(raw[3] / my) * my))
                actual = _map_box(raw, orient, raw_w, raw_h)
                left, top, right, bottom = raw
                cropped = temp / "cropped.jpg"
                _run_jpegtran(["-crop", f"{right-left}x{bottom-top}+{left}+{top}"], data.source, cropped)
                transform = _jpeg_transform(orient, rotation)
                if transform and (right - left) % mx == 0 and (bottom - top) % my == 0:
                    _run_jpegtran(transform, cropped, final)
                else:
                    cropped.rename(final)
                    if transform:
                        # Do not move partially filled edge blocks, even for
                        # a transpose that libjpeg considers perfect. EXIF
                        # also preserves the original chroma sampling axes.
                        stored_orientation = _composed_orientation(orient, rotation)
                        orientation_storage = "exif"
                        notes.append("为完整保留 JPEG 边缘的非整块像素，旋转记录在 EXIF 方向中；支持 EXIF 的看图软件会正确回正。")
                width, height = actual[2] - actual[0], actual[3] - actual[1]
                if rotation in (90, 270):
                    width, height = height, width
                with Image.open(final) as encoded:
                    pixel_size = encoded.size
                expected_size = pixel_size[::-1] if stored_orientation in (5, 6, 7, 8) else pixel_size
                if expected_size != (width, height):
                    raise ImageIOError("JPEG 无损裁切后的尺寸不符合预期，已停止导出以避免丢失画面。")
                notes.extend(_clean_jpeg_exif(final, *pixel_size, orientation=stored_orientation))
                if actual != requested:
                    notes.append(f"JPEG 为保留全部所选画面且避免重新有损压缩，边界已向外扩展到 {mx} × {my} 像素压缩块；可能多保留少量边框。")
                notes.append("JPEG 压缩系数和 ICC 保持不变；EXIF 方向与尺寸已更新，旧缩略图已移除。")
            else:
                raise ImageIOError(f"不支持的图片格式：{data.format}")
            # Hard-link installation is atomic and fails if another export
            # already created the destination. Both files are on one volume.
            try:
                os.link(final, destination)
            except FileExistsError as exc:
                raise ImageIOError(f"输出文件已存在，不会覆盖：{destination.name}") from exc
            except OSError as exc:
                if exc.errno not in (errno.EPERM, errno.EACCES, errno.ENOTSUP, errno.EXDEV, errno.EINVAL, errno.ENOSYS):
                    raise
                # FAT/exFAT removable disks do not support hard links. Exclusive
                # creation still guarantees no overwrite; remove partial writes.
                created = False
                try:
                    with destination.open("xb") as target:
                        created = True
                        with final.open("rb") as original:
                            shutil.copyfileobj(original, target)
                except Exception:
                    if created:
                        destination.unlink(missing_ok=True)
                    raise
    except ImageIOError:
        raise
    except Exception as exc:
        raise ImageIOError(f"无法导出 {destination.name}：{exc}") from exc
    return {"actual_bbox": actual, "width": width, "height": height,
            "displayed_size": (width, height), "pixel_size": pixel_size,
            "orientation_storage": orientation_storage, "stored_orientation": stored_orientation,
            "bit_depth": data.bit_depth, "format": data.format, "lossless": True, "metadata_notes": notes}
