# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Success regressions for real scanner noise, separate from pixel safety.

The two photographed rectangles are known before the separator is painted.
All fixtures are synthetic; no user's photographs are shipped with the tests.
"""
from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from halfframe.splitter import detect_split, split_boxes


def _scan(case: str):
    height, width = 500, 800
    rng = np.random.default_rng(3)
    photo_min, photo_max = (64, 110) if case == "low_contrast" else (55, 220)
    pixels = rng.integers(photo_min, photo_max, (height, width, 3), dtype=np.uint8)
    left, right = 382, 420
    pixels[:, left:right] = 5
    if case == "noise_row":
        # One scanner row is brighter by 13/255 across the same intact gap.
        pixels[250, left:right] = 18
    elif case == "brightness_gradient":
        # Scanner shading alters brightness, never either frame's geometry.
        pixels[:, left:right] = np.rint(np.linspace(0, 40, height)).astype(np.uint8)[:, None, None]
    elif case == "dark_photo_edge":
        # A dark detail belongs to the first photograph, despite matching film.
        pixels[250, 300:left] = 5
    elif case != "low_contrast":
        raise ValueError(case)
    xx = np.indices((height, width))[1]
    return pixels, (xx < left, xx >= right)


def _assert_retained(boxes, masks, shape, axis):
    height, width = shape
    coverage = np.zeros(shape, dtype=bool)
    coordinate = 1 if axis == "vertical" else 0
    ordered_masks = sorted(masks, key=lambda mask: np.nonzero(mask)[coordinate].mean())
    for (left, top, right, bottom), mask in zip(boxes, ordered_masks):
        assert 0 <= left < right <= width
        assert 0 <= top < bottom <= height
        coverage[top:bottom, left:right] = True
        yy, xx = np.nonzero(mask)
        assert left <= xx.min() and right > xx.max(), "A photographed region was cut inward."
        assert top <= yy.min() and bottom > yy.max(), "A photographed region was cut inward."
    assert coverage.all(), "The two outputs must retain every original source pixel."


@pytest.mark.parametrize("quarter_turns", range(4))
@pytest.mark.parametrize("case", ["noise_row", "brightness_gradient", "dark_photo_edge", "low_contrast"])
def test_single_clear_gap_survives_scanner_noise_and_dark_content(case, quarter_turns):
    raw, masks = _scan(case)
    raw = np.rot90(raw, quarter_turns)
    masks = tuple(np.rot90(mask, quarter_turns) for mask in masks)
    height, width = raw.shape[:2]
    result = detect_split(Image.fromarray(raw), width, height)
    assert not result.get("export_blocked", False), "An intact, unique gap must produce a usable split."
    expected_axis = "horizontal" if quarter_turns % 2 else "vertical"
    assert result["axis"] == expected_axis
    boxes = split_boxes(result, width, height)
    _assert_retained(boxes, masks, (height, width), expected_axis)
    dimension = width if expected_axis == "vertical" else height
    assert all((box[2] - box[0] if expected_axis == "vertical" else box[3] - box[1]) < dimension
               for box in boxes), "Success must actually split the scan, not duplicate the full image."
    if case == "dark_photo_edge":
        overlap = result["start"] - result["end"]
        assert 0 <= overlap <= dimension * .08, "A single dark detail must not cause excessive overlap."


@pytest.mark.parametrize("quarter_turns", range(4))
def test_two_equally_plausible_gaps_still_require_manual_confirmation(quarter_turns):
    height, width = 500, 800
    raw = np.random.default_rng(9).integers(55, 220, (height, width, 3), dtype=np.uint8)
    raw[:, 296:320] = 5
    raw[:, 480:504] = 5
    raw = np.rot90(raw, quarter_turns)
    height, width = raw.shape[:2]
    result = detect_split(Image.fromarray(raw), width, height)
    assert result.get("export_blocked", False), "Two equally credible separators must not be silently guessed."
    assert result["review"]
    boxes = split_boxes(result, width, height)
    assert boxes == [[0, 0, width, height], [0, 0, width, height]]


@pytest.mark.parametrize("quarter_turns", range(4))
@pytest.mark.parametrize("first_row", [5, 250])
def test_brief_frame_tip_outside_global_gap_is_never_guessed_away(first_row, quarter_turns):
    height, width = 500, 800
    raw = np.random.default_rng(8).integers(110, 230, (height, width, 3), dtype=np.uint8)
    left = np.full(height, 382)
    right = np.full(height, 420)
    # Two rows extend beyond the entire globally detected separator. A brief
    # protrusion at the top is still photographed content, not scanner border.
    left[first_row:first_row + 2] = 490
    right[first_row:first_row + 2] = 528
    xx = np.indices((height, width))[1]
    first_frame = xx < left[:, None]
    second_frame = xx >= right[:, None]
    raw[~(first_frame | second_frame)] = 5
    raw[first_row:first_row + 2, 382:420] = 150
    raw = np.rot90(raw, quarter_turns)
    masks = tuple(np.rot90(mask, quarter_turns) for mask in (first_frame, second_frame))
    height, width = raw.shape[:2]
    result = detect_split(Image.fromarray(raw), width, height)
    boxes = split_boxes(result, width, height)
    if result.get("export_blocked", False):
        assert result["review"]
        assert boxes == [[0, 0, width, height], [0, 0, width, height]]
    else:
        assert result["axis"] == ("horizontal" if quarter_turns % 2 else "vertical")
        _assert_retained(boxes, masks, (height, width), result["axis"])


@pytest.mark.parametrize("shape", [(1, 800), (2, 800), (800, 1), (800, 2), (1, 1), (2, 2)])
def test_tiny_scan_requests_review_without_an_exception(shape):
    height, width = shape
    result = detect_split(Image.new("RGB", (width, height), "gray"), width, height)
    assert result.get("export_blocked", False)
    assert result["review"]
    assert split_boxes(result, width, height) == [[0, 0, width, height], [0, 0, width, height]]
