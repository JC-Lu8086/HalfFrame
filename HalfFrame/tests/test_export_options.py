# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
import tifffile
from halfframe.core import analyze_scan,export_scan

@pytest.mark.parametrize('source_bits',[8,16])
@pytest.mark.parametrize('output_format',['original','jpeg','tiff16'])
def test_output_options_and_source_folder(tmp_path,source_bits,output_format):
    raw = np.random.default_rng(51).integers(0,200,(91,137,3),dtype='uint8')
    raw[:,60:77]=5
    if source_bits==16: raw=raw.astype('uint16')*257
    path=tmp_path/'原始照片.tif'
    tifffile.imwrite(path,raw,photometric='rgb')
    scan=analyze_scan(path)
    scan['split'].update(manual=True,export_blocked=False)
    scan['frames'][0].update(bbox=[0,0,77,91],rotation=90)
    scan['frames'][1].update(bbox=[60,0,137,91],rotation=0)
    before=path.read_bytes()
    results=export_scan(scan,None,output_format,jpeg_quality=95)
    assert path.read_bytes()==before
    for frame,result in zip(scan['frames'],results):
        output=Path(result['path'])
        assert output.parent==tmp_path
        l,t,r,b=frame['bbox'];expected=np.rot90(raw[t:b,l:r],-frame['rotation']//90)
        if output_format=='jpeg':
            with Image.open(output) as image:
                assert image.size==(expected.shape[1],expected.shape[0])
                assert result['bit_depth']==8 and not result['lossless']
        else:
            if output_format=='tiff16' and source_bits==8:expected=expected.astype('uint16')*257
            actual=tifffile.imread(output)
            assert np.array_equal(actual,expected)
            assert actual.dtype == expected.dtype
    second=export_scan(scan,None,output_format)
    assert second[0]['path']!=results[0]['path']


def test_no_automatic_rotation(tmp_path):
    raw=np.random.default_rng(8).integers(50,230,(120,160,3),dtype='uint8');raw[:,73:88]=8
    path=tmp_path/'scan.tif';tifffile.imwrite(path,raw)
    scan=analyze_scan(path)
    assert [f['rotation'] for f in scan['frames']]==[0,0]
    assert all('orientation' not in f for f in scan['frames'])
