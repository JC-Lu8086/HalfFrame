# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Regression coverage for preserving every requested JPEG edge and corner."""
import numpy as np
import piexif
import pytest
from PIL import Image, ImageOps

from halfframe.image_io import export_crop, load_image, _composed_orientation, _orient


def _write_scan(path, size, orientation, subsampling):
    width, height = size
    yy, xx = np.indices((height, width))
    # A gentle gradient plus distinct corner patches makes a missing or
    # incorrectly mirrored edge immediately observable after EXIF normalization.
    pixels = np.stack((40 + xx * 100 // max(width, 1),
                       45 + yy * 105 // max(height, 1),
                       60 + (xx + yy) * 80 // max(width + height, 1)), -1).astype('uint8')
    edge = min(12, width // 3, height // 3)
    if edge:
        pixels[:edge, :edge] = (240, 30, 30)
        pixels[:edge, -edge:] = (20, 225, 50)
        pixels[-edge:, :edge] = (30, 50, 235)
        pixels[-edge:, -edge:] = (240, 220, 30)
    exif = piexif.dump({'0th': {274: orientation}, 'Exif': {}, '1st': {}, 'thumbnail': None})
    Image.fromarray(pixels).save(path, quality=92, subsampling=subsampling,
                                exif=exif, icc_profile=b'corner-preservation-icc')


@pytest.mark.parametrize('subsampling', (0, 1, 2))
@pytest.mark.parametrize('orientation', range(1, 9))
@pytest.mark.parametrize('rotation', (0, 90, 180, 270))
def test_odd_image_edges_and_orientation_preserved(tmp_path, subsampling, orientation, rotation):
    source = tmp_path / 'odd.jpg'
    _write_scan(source, (179, 137), orientation, subsampling)
    original_bytes = source.read_bytes()
    data = load_image(source)
    with Image.open(source) as opened:
        quantization = opened.quantization
    box = (0, 0, data.width, data.height)
    destination = tmp_path / 'result.jpg'
    result = export_crop(data, box, rotation, destination)
    expected = np.rot90(data.pixels, -(rotation // 90))
    assert result['actual_bbox'] == box
    assert result['displayed_size'] == (expected.shape[1], expected.shape[0])
    assert result['lossless']
    with Image.open(destination) as output:
        displayed = np.asarray(ImageOps.exif_transpose(output))
        assert displayed.shape == expected.shape
        assert result['pixel_size'] == output.size
        assert result['stored_orientation'] == output.getexif()[274]
        assert output.info['icc_profile'] == b'corner-preservation-icc'
        assert output.getexif()[256] == output.width
        assert output.getexif()[257] == output.height
        # A physical transpose also transposes the quantization matrix. No
        # newly generated quality table is permitted in either storage mode.
        transform = _composed_orientation(orientation, rotation)
        transposed = result['orientation_storage'] == 'pixels' and transform >= 5
        expected_q = {key: np.asarray(value).reshape(8, 8).T.ravel().tolist()
                      if transposed else value for key, value in quantization.items()}
        assert output.quantization == expected_q
    # EXIF fallback leaves compressed samples unchanged. Physical transforms
    # can differ slightly at decode time through IDCT/chroma rounding.
    for ys, xs in ((slice(0, 3), slice(0, 3)), (slice(0, 3), slice(-3, None)),
                   (slice(-3, None), slice(0, 3)), (slice(-3, None), slice(-3, None))):
        difference = np.abs(displayed[ys, xs].astype('int16') - expected[ys, xs].astype('int16'))
        assert difference.max() <= 3
    assert np.abs(displayed.astype('int16') - expected.astype('int16')).mean() < 1.0
    if result['orientation_storage'] == 'exif':
        assert np.array_equal(displayed, expected)
    assert source.read_bytes() == original_bytes


@pytest.mark.parametrize('subsampling', (0, 1, 2))
@pytest.mark.parametrize('orientation', range(1, 9))
@pytest.mark.parametrize('rotation', (0, 90, 180, 270))
def test_arbitrary_crop_expands_outward_in_upright_space(tmp_path, subsampling, orientation, rotation):
    source = tmp_path / 'scan.jpg'
    _write_scan(source, (179, 137), orientation, subsampling)
    data = load_image(source)
    with Image.open(source) as luminance:
        luminance.draft('L', luminance.size)
        source_luminance = _orient(np.asarray(luminance), orientation)
    for index, box in enumerate(((11, 13, data.width - 5, data.height - 7),
                                  (data.width - 1, data.height - 1, data.width, data.height),
                                  (0, 0, 1, 1), (3, 5, 7, 9))):
        destination = tmp_path / f'crop-{index}.jpg'
        result = export_crop(data, box, rotation, destination)
        left, top, right, bottom = result['actual_bbox']
        assert 0 <= left <= box[0] < box[2] <= right <= data.width
        assert 0 <= top <= box[1] < box[3] <= bottom <= data.height
        expected = np.rot90(data.pixels[top:bottom, left:right], -(rotation // 90))
        with Image.open(destination) as output:
            displayed = np.asarray(ImageOps.exif_transpose(output))
        assert displayed.shape == expected.shape
        # Decode JPEG luminance directly to isolate retained detail from
        # decoder chroma interpolation at newly exposed crop boundaries.
        # For crops narrower than an MCU, libjpeg may switch its chroma
        # interpolator; comparing decoded RGB would then give false failures.
        with Image.open(destination) as luminance:
            luminance.draft('L', luminance.size)
            actual_luminance = _orient(np.asarray(luminance), result['stored_orientation'])
        expected_luminance = np.rot90(source_luminance[top:bottom, left:right], -(rotation // 90))
        assert np.abs(actual_luminance.astype('int16') - expected_luminance.astype('int16')).max() <= 1


@pytest.mark.parametrize('size', ((1, 1), (1, 7), (7, 1), (5, 9), (8, 16), (16, 8)))
@pytest.mark.parametrize('orientation', range(1, 9))
def test_images_smaller_than_one_mcu_keep_all_pixels(tmp_path, size, orientation):
    source = tmp_path / 'tiny.jpg'
    _write_scan(source, size, orientation, 2)
    data = load_image(source)
    for rotation in (0, 90, 180, 270):
        destination = tmp_path / f'tiny-{rotation}.jpg'
        result = export_crop(data, (0, 0, data.width, data.height), rotation, destination)
        with Image.open(destination) as output:
            displayed = np.asarray(ImageOps.exif_transpose(output))
        expected = np.rot90(data.pixels, -(rotation // 90))
        assert displayed.shape == expected.shape
        assert result['actual_bbox'] == (0, 0, data.width, data.height)
        assert np.abs(displayed.astype('int16') - expected.astype('int16')).mean() < 1.5


def test_jpeg_export_never_calls_pillow_encoder(tmp_path, monkeypatch):
    source = tmp_path / 'scan.jpg'
    _write_scan(source, (179, 137), 7, 2)
    data = load_image(source)
    def forbidden(*args, **kwargs):
        raise AssertionError('JPEG export must not decode and re-encode pixels')
    monkeypatch.setattr(Image.Image, 'save', forbidden)
    result = export_crop(data, (3, 7, data.width, data.height), 90, tmp_path / 'result.jpg')
    assert result['lossless']
