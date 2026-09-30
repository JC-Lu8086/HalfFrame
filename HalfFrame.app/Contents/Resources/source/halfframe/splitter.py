# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Locate separators conservatively, retaining all source pixels by default.

The two rectangles overlap across the separator and never trim outer borders.
An uncertain detector returns two full scans and prevents automatic export.
"""
from __future__ import annotations

import numpy as np
import math
from PIL import Image
from .separators import all_candidates


def _runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))



def detect_split(preview: Image.Image, width: int, height: int) -> dict:
    image = preview.convert("RGB").copy()
    image.thumbnail((1400, 1400))
    a = np.asarray(image, dtype=np.float32) / 255
    gray = a @ np.array([.299, .587, .114], dtype=np.float32)
    def blocked(reason):
        axis = "vertical" if width >= height else "horizontal"
        mid = (width if axis == "vertical" else height) // 2
        return dict(axis=axis, start=mid, end=mid, confidence=0., review=True,
                    export_blocked=True, preserve_all=True, reason=reason)
    if min(image.size) < 8:
        return blocked("图片尺寸太小，无法判断分界；请使用完整扫描。")
    candidates = all_candidates(a)
    candidates.sort(key=lambda c: c["score"], reverse=True)
    if not candidates:
        return blocked("未找到可靠分界，保留完整扫描；请定位分隔位置后再导出。")
    best = candidates[0]
    scale = width / image.width if best["axis"] == "vertical" else height / image.height
    ambiguous = len(candidates) > 1 and candidates[1]["score"] > best["score"] - .10
    # A low contrast score calls for review, not a failure to locate a strip.
    # Dark photographs often have low outside variance despite a clear gap.
    if ambiguous:
        return blocked("分界有歧义，保留完整扫描；请确认分隔位置后再导出。")
    matrix = gray if best["axis"] == "vertical" else gray.T
    colors = a if best["axis"] == "vertical" else a.swapaxes(0, 1)
    first, last = best["start"], best["end"]
    global_reference = np.median(colors[:, first:last].reshape(-1, 3), axis=0)
    # Follow the actual band on individual preview rows. Do not discard unusual
    # rows with percentile statistics: small frame tips may appear only once.
    column = (first + last) // 2
    starts, ends = [], []
    unusual_rows = False
    pad = max(4, int(matrix.shape[1] * .006))
    for row_index, row in enumerate(matrix):
        # Colour similarity separates a brown film gap from genuinely dark
        # photographic content more reliably than a broad brightness cutoff.
        # Scanner shading, dust and grain can change the gap's colour along
        # its length. Estimate each row from the darkest/lightest core pixels
        # instead of rejecting the whole scan on one global RGB mismatch.
        core = colors[row_index, first:last]
        luminance = row[first:last]
        order = np.argsort(luminance)
        count = max(1, math.ceil(len(order) * .25))
        selected = order[:count] if best["kind"] == "dark" else order[-count:]
        reference = np.median(core[selected], axis=0)
        gap_level = float(np.median(luminance[selected]))
        plausible = gap_level < .32 if best["kind"] == "dark" else gap_level > .70
        plausible = plausible and np.max(np.abs(reference-global_reference)) < .10
        mask = np.max(np.abs(colors[row_index] - reference), axis=1) < .025
        # A photo may intrude into the initial uniform-core column. Find the
        # nearest run within the detected band, retaining both sides' envelope.
        runs = [(a, b) for a, b in _runs(mask)
                if b > first and a < last] if plausible else []
        if not runs:
            border_row = row_index < matrix.shape[0]*.08 or row_index > matrix.shape[0]*.92
            border_match = np.max(np.abs(colors[row_index]-global_reference), axis=1) < .035
            uniform_border = bool(border_match[first:last].all() and any(
                a <= first and b >= last and b-a > matrix.shape[1]*.25
                for a, b in _runs(border_match)))
            if border_row and uniform_border and plausible:
                # Solid scanner border at the top/bottom contains no evidence
                # about the separator. Keep it in the output rectangles.
                starts.append(first); ends.append(last)
                continue
            # A short protruding corner may push the whole gap outside the
            # profile core, including near the image's top or bottom. Search
            # nearby for the observed film colour rather than inventing an
            # edge from other rows or treating every outer row as black border.
            mask = np.max(np.abs(colors[row_index] - global_reference), axis=1) < .025
            runs = [(a, b) for a, b in _runs(mask)
                    if max(2, (last-first)*.25) <= b-a <= matrix.shape[1]*.25
                    and abs((a+b)/2-column) < matrix.shape[1]*.20]
            if not runs:
                return blocked("分隔边界不连续或倾斜较大，已保留完整扫描；请手动定位。")
            unusual_rows = True
        a, b = min(runs, key=lambda p: abs((p[0]+p[1])/2-column))
        starts.append(a); ends.append(b)
    # Left-photo content ends at the LEFT edge of the gap; right-photo content
    # starts at its RIGHT edge. Envelope those edges, then include the midpoint
    # in both crops so every source pixel (including the gap) remains present.
    # Using the opposite edges duplicated the entire gap and adjacent scenes.
    dimension = width if best["axis"] == "vertical" else height
    midpoint = (first+last)/2
    best["start"] = min(dimension, math.ceil((max(midpoint, max(starts)) + pad) * scale))
    best["end"] = max(0, math.floor((min(midpoint, min(ends)) - pad) * scale))
    best["detected_band"] = [math.floor(first*scale), math.ceil(last*scale)]
    best["review"] = best["confidence"] < .72 or unusual_rows or best.get("uncertain_width", False)
    best["export_blocked"] = False
    best["preserve_all"] = True
    best["reason"] = "已保留分界两侧和全部外边缘；两张照片在边界处重叠，避免丢失画面。"
    best.pop("score", None)
    return best


def split_boxes(split: dict, width: int, height: int) -> list[list[int]]:
    if split.get("export_blocked") and not split.get("manual"):
        return [[0, 0, width, height], [0, 0, width, height]]
    if split["axis"] == "vertical":
        return [[0, 0, split["start"], height], [split["end"], 0, width, height]]
    return [[0, 0, width, split["start"]], [0, split["end"], width, height]]
