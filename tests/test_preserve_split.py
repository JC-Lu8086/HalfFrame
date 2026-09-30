# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Adversarial scans with independently known photographed regions.

These fixtures use generated colours only.  No private photographs are copied
into the test suite.  Masks represent the original frame contents; checking
their containment catches cuts that a union-of-crops check alone would miss.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from halfframe.splitter import detect_split, split_boxes


def synthetic_scan(case: str, height: int = 500, width: int = 800):
    """Return an image and two ground-truth masks, without using the detector."""
    yy, xx = np.indices((height, width))
    row = np.arange(height)
    middle = width * .5
    if case == "thin":
        lower = np.full(height, int(middle) - 1)
        upper = np.full(height, int(middle) + 1)
    elif case == "wide":
        lower = np.full(height, int(middle) - 41)
        upper = np.full(height, int(middle) + 40)
    elif case == "variable_width":
        lower = np.rint(middle - 21 - 16 * np.sin(row / 33)).astype(int)
        upper = np.rint(middle + 24 + 18 * np.cos(row / 49)).astype(int)
    elif case == "inclined":
        center = middle - 52 + 104 * row / max(1, height - 1)
        lower = np.rint(center - 12).astype(int)
        upper = np.rint(center + 15).astype(int)
    elif case == "zigzag":
        center = middle + 42 * (2 * np.abs((row / 95) % 2 - 1) - 1)
        lower = np.rint(center - 10 - 4 * np.sin(row / 17)).astype(int)
        upper = np.rint(center + 13 + 6 * np.cos(row / 19)).astype(int)
    elif case == "picture_tips":
        lower = np.full(height, int(middle) - 28)
        upper = np.full(height, int(middle) + 28)
        # Short protrusions defeat percentiles that discard unusual rows.
        lower[71:77] = int(middle) + 19
        upper[313:319] = int(middle) - 17
    else:
        raise ValueError(case)
    first = xx < lower[:, None]
    second = xx >= upper[:, None]
    rng = np.random.default_rng(193)
    image = rng.integers(55, 220, (height, width, 3), dtype=np.uint8)
    image[~(first | second)] = 5

    # Irregular outer black edges plus edge-adjacent coloured details expose
    # opportunistic border trimming.  Their exact shape is unrelated to the
    # center separator, just as it is in a scanner crop.
    top_edge = 2 + (9 * (np.sin(np.arange(width) / 47) + 1)).astype(int)
    bottom_edge = 3 + (7 * (np.cos(np.arange(width) / 31) + 1)).astype(int)
    outer = (yy < top_edge[None, :]) | (yy >= height - bottom_edge[None, :])
    outer |= (xx < (3 + row % 8)[:, None]) | (xx >= width - (3 + row % 11)[:, None])
    image[outer] = 3
    for x, y in ((1, 1), (width - 2, 1), (1, height - 2), (width - 2, height - 2)):
        image[y, x] = (255, 60, 170)
    return image, (first, second)


def assert_all_source_pixels_retained(boxes, width, height):
    coverage = np.zeros((height, width), dtype=bool)
    assert len(boxes) == 2
    for left, top, right, bottom in boxes:
        assert 0 <= left < right <= width
        assert 0 <= top < bottom <= height
        coverage[top:bottom, left:right] = True
    assert coverage.all(), "The two default crops must cover every source pixel."


def assert_whole_frames_retained(boxes, masks, axis):
    coordinate = 1 if axis == "vertical" else 0
    ordered_masks = sorted(masks, key=lambda m: np.nonzero(m)[coordinate].mean())
    for (left, top, right, bottom), mask in zip(boxes, ordered_masks):
        yy, xx = np.nonzero(mask)
        assert left <= xx.min() and right > xx.max(), "A photographed horizontal tip was clipped."
        assert top <= yy.min() and bottom > yy.max(), "A photographed vertical tip was clipped."


@pytest.mark.parametrize("quarter_turns", range(4))
@pytest.mark.parametrize("case", ["thin", "wide", "variable_width", "inclined", "zigzag", "picture_tips"])
def test_irregular_scan_preserves_every_pixel_and_each_frame(case, quarter_turns):
    raw, masks = synthetic_scan(case)
    raw = np.rot90(raw, quarter_turns)
    masks = tuple(np.rot90(mask, quarter_turns) for mask in masks)
    height, width = raw.shape[:2]
    split = detect_split(Image.fromarray(raw), width, height)
    boxes = split_boxes(split, width, height)
    assert_all_source_pixels_retained(boxes, width, height)
    assert_whole_frames_retained(boxes, masks, split["axis"])
    if split.get("export_blocked"):
        assert split["review"]
        assert boxes == [[0, 0, width, height], [0, 0, width, height]]
    else:
        assert split["axis"] == ("horizontal" if quarter_turns % 2 else "vertical")
        assert split["start"] >= split["end"], "Automatic cuts must overlap or abut."
    # A clear, straight, broad separator must remain genuinely automatic.
    if case == "wide":
        assert not split.get("export_blocked", False)
        if split["axis"] == "vertical":
            assert max(box[2] - box[0] for box in boxes) < width
        else:
            assert max(box[3] - box[1] for box in boxes) < height


@pytest.mark.parametrize("quarter_turns", range(4))
def test_scaled_preview_does_not_round_cuts_inward(quarter_turns):
    raw, masks = synthetic_scan("inclined", height=503, width=809)
    # A reduced preview and odd original dimensions exercise coordinate
    # conversion without deriving expectations from detector internals.
    raw = np.repeat(np.repeat(raw, 3, axis=0), 3, axis=1)
    masks = tuple(np.repeat(np.repeat(m, 3, axis=0), 3, axis=1) for m in masks)
    raw = np.rot90(raw, quarter_turns)
    masks = tuple(np.rot90(mask, quarter_turns) for mask in masks)
    height, width = raw.shape[:2]
    preview = Image.fromarray(raw)
    preview.thumbnail((599, 599), Image.Resampling.LANCZOS)
    split = detect_split(preview, width, height)
    boxes = split_boxes(split, width, height)
    assert_all_source_pixels_retained(boxes, width, height)
    assert_whole_frames_retained(boxes, masks, split["axis"])


@pytest.mark.parametrize("shape", [(500, 800), (800, 500), (621, 621)])
@pytest.mark.parametrize("quarter_turns", range(4))
@pytest.mark.parametrize("separator_level", [5, 249])
def test_separator_axis_is_not_guessed_from_scan_aspect_ratio(shape, quarter_turns, separator_level):
    height, width = shape
    raw = np.random.default_rng(29).integers(45, 222, (height, width, 3), dtype=np.uint8)
    left, right = width // 2 - 13, width // 2 + 14
    raw[:, left:right] = separator_level
    xx = np.indices(shape)[1]
    masks = (xx < left, xx >= right)
    raw = np.rot90(raw, quarter_turns)
    masks = tuple(np.rot90(m, quarter_turns) for m in masks)
    height, width = raw.shape[:2]
    split = detect_split(Image.fromarray(raw), width, height)
    assert not split.get("export_blocked", False)
    assert split["axis"] == ("horizontal" if quarter_turns % 2 else "vertical")
    boxes = split_boxes(split, width, height)
    assert_all_source_pixels_retained(boxes, width, height)
    assert_whole_frames_retained(boxes, masks, split["axis"])


@pytest.mark.parametrize("shape", [(500, 800), (800, 500), (621, 621)])
@pytest.mark.parametrize("case", ["uniform_gray", "dark_scene", "competing_dividers"])
def test_uncertain_scene_keeps_full_scans_and_requires_review(shape, case):
    height, width = shape
    if case == "uniform_gray":
        raw = np.full((height, width, 3), 120, dtype=np.uint8)
    elif case == "dark_scene":
        raw = np.random.default_rng(6).integers(0, 20, (height, width, 3), dtype=np.uint8)
    else:
        raw = np.random.default_rng(9).integers(55, 220, (height, width, 3), dtype=np.uint8)
        raw[:, int(width * .37):int(width * .40)] = 5
        raw[:, int(width * .60):int(width * .63)] = 5
    split = detect_split(Image.fromarray(raw), width, height)
    boxes = split_boxes(split, width, height)
    assert split["review"]
    assert split.get("export_blocked"), "Ambiguous scans must not silently export a guessed midpoint."
    assert boxes == [[0, 0, width, height], [0, 0, width, height]]
    assert_all_source_pixels_retained(boxes, width, height)
