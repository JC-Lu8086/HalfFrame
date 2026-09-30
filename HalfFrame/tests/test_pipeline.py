# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
from pathlib import Path
import errno
import json
import numpy as np
import pytest
from PIL import Image, ImageOps
import piexif
import tifffile

from halfframe.image_io import load_image, export_crop, _orient, ImageIOError
from halfframe.splitter import detect_split
from halfframe.core import analyze_scan, export_scan


@pytest.mark.parametrize('dtype', [np.uint8, np.uint16])
@pytest.mark.parametrize('channels', [1, 3, 4])
@pytest.mark.parametrize('orientation', range(1, 9))
def test_tiff_exact_pixels_and_profile(tmp_path, dtype, channels, orientation):
    rng = np.random.default_rng(4)
    shape = (97, 133) if channels == 1 else (97, 133, channels)
    raw = rng.integers(0, np.iinfo(dtype).max, size=shape, dtype=dtype)
    source = tmp_path/'原图.tif'
    icc = b'test-icc-profile-payload'
    tifffile.imwrite(source, raw, photometric='rgb' if channels > 1 else 'minisblack',
                     extratags=[(274, 'H', 1, orientation, False), (34675, 'B', len(icc), icc, False)],
                     resolution=(300, 400), metadata=None)
    data = load_image(source)
    expected = _orient(raw, orientation)
    assert np.array_equal(data.pixels, expected)
    for rotation in (0, 90, 180, 270):
        dest = tmp_path/f'{rotation}.tif'
        box = (7, 9, data.width-5, data.height-6)
        result = export_crop(data, box, rotation, dest)
        output = tifffile.imread(dest)
        assert output.dtype == raw.dtype
        assert np.array_equal(output, np.rot90(expected[9:-6, 7:-5], -rotation//90))
        with tifffile.TiffFile(dest) as t:
            assert t.pages[0].tags[34675].value == icc
            assert t.pages[0].tags[274].value == 1
        assert result['actual_bbox'] == box


@pytest.mark.parametrize('orientation', range(1, 9))
@pytest.mark.parametrize('rotation', [0, 90, 180, 270])
def test_jpeg_normalization_rotation_and_metadata(tmp_path, orientation, rotation):
    yy, xx = np.indices((128, 176))
    a = np.stack([xx % 256, yy % 256, (xx + yy) % 256], axis=-1).astype('uint8')
    source = tmp_path/'source.jpg'
    exif = piexif.dump({'0th': {274:orientation}, 'Exif': {}, '1st':{}, 'thumbnail':None})
    Image.fromarray(a).save(source, quality=91, subsampling=0, exif=exif, icc_profile=b'icc-test')
    data = load_image(source)
    box = (11, 13, data.width-3, data.height-5)
    dest = tmp_path/'crop.jpg'
    result = export_crop(data, box, rotation, dest)
    l,t,r,b = result['actual_bbox']
    expected = np.rot90(data.pixels[t:b,l:r], -rotation//90)
    with Image.open(dest) as output:
        assert output.info['icc_profile'] == b'icc-test'
        assert output.getexif()[274] in range(1, 9)
        assert ImageOps.exif_transpose(output).size == (expected.shape[1], expected.shape[0])
        actual = np.array(ImageOps.exif_transpose(output))
        assert np.abs(actual.astype('int16')-expected.astype('int16')).mean() < .7
        assert output.quantization is not None
        # Quantization tables transpose during 90° DCT rotations. A constant
        # quantization table would hide errors, so test coefficient-preserving
        # decoded output above instead of falsely requiring byte-identical JPEG.
    assert l <= box[0] and t <= box[1] and r >= box[2] and b >= box[3]


def test_source_untouched_no_overwrite_and_exfat(tmp_path, monkeypatch):
    source = tmp_path/'source.tif'
    tifffile.imwrite(source, np.arange(120*200,dtype='uint16').reshape(120,200))
    before = source.read_bytes()
    data = load_image(source)
    dest = tmp_path/'crop.tif'
    def unsupported(*args): raise OSError(errno.ENOTSUP, 'no hard links')
    monkeypatch.setattr('halfframe.image_io.os.link', unsupported)
    export_crop(data, (0,0,100,120), 90, dest)
    assert dest.exists() and source.read_bytes() == before
    with pytest.raises(ImageIOError, match='不会覆盖'):
        export_crop(data, (0,0,100,120), 90, dest)


@pytest.mark.parametrize('rotation', range(4))
@pytest.mark.parametrize('bar', [10, 248])
def test_separator_four_scan_orientations(rotation, bar):
    rng = np.random.default_rng(4)
    a = rng.integers(40, 220, (600, 880, 3), dtype='uint8')
    a[:,410:462] = bar
    a = np.rot90(a, rotation)
    split = detect_split(Image.fromarray(a), a.shape[1], a.shape[0])
    assert split['axis'] == ('horizontal' if rotation%2 else 'vertical')
    assert split['start'] >= split['end']
    assert not split.get('export_blocked')
    assert not split['review']


def test_unclear_separator_and_multipage_rejected(tmp_path):
    split = detect_split(Image.new('RGB', (800,600), (120,120,120)),800,600)
    assert split['review'] and split['start'] == split['end'] == 400
    path = tmp_path/'pages.tif'
    with tifffile.TiffWriter(path) as writer:
        writer.write(np.zeros((30,40), dtype='uint8'))
        writer.write(np.zeros((30,40), dtype='uint8'))
    with pytest.raises(ImageIOError, match='多页'):
        load_image(path)


def test_batch_names_manifest_and_source_change(tmp_path):
    raw = np.random.default_rng(2).integers(60,220,(128,200,3), dtype='uint8')
    raw[:,90:110] = 9
    source = tmp_path/'scan.tif';tifffile.imwrite(source,raw)
    scan = analyze_scan(source)
    outputs = tmp_path/'out'
    first = export_scan(scan, outputs)
    second = export_scan(scan, outputs)
    assert len(first) == 2 and len(second) == 2
    assert first[0]['path'] != second[0]['path']
    records = list(outputs.glob('*.json'))
    assert len(records) == 2 and len(json.loads(records[0].read_text())['outputs']) == 2
    source.write_bytes(b'changed')
    with pytest.raises(ImageIOError, match='发生了变化'):
        export_scan(scan, outputs)
