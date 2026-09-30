# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Launch HalfFrame; --self-test DIR checks a packaged installation offline."""
import sys

def self_test(directory):
    import json
    from pathlib import Path
    import numpy as np
    from PIL import Image
    import tifffile
    from halfframe.image_io import load_image, export_crop, jpegtran_path
    from halfframe.export_formats import export_converted_crop
    output = Path(directory); output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    pixels = rng.integers(0, 255, (80, 128, 3), dtype='uint8')
    tifffile.imwrite(output/'input.tif', pixels)
    Image.fromarray(pixels).save(output/'input.jpg', quality=95)
    for ext in ('tif', 'jpg'):
        data = load_image(output/f'input.{ext}')
        result = export_crop(data, (0,0,64,80), 90, output/f'output.{ext}')
        assert (result['width'],result['height']) == (80,64)
        if ext == 'tif':
            assert np.array_equal(tifffile.imread(output/'output.tif'), np.rot90(pixels[:,:64], -1))
    data = load_image(output/'input.tif')
    export_converted_crop(data, (0,0,64,80), 90, output/'converted16.tif', 'tiff16')
    expected = np.rot90(pixels[:,:64], -1).astype(np.uint16) * 257
    assert np.array_equal(tifffile.imread(output/'converted16.tif'), expected)
    export_converted_crop(data, (0,0,64,80), 90, output/'converted.jpg', 'jpeg')
    with Image.open(output/'converted.jpg') as converted:
        assert converted.size == (80,64)
    print(json.dumps({'ok':True,'jpegtran':jpegtran_path(),'automatic_orientation':False}))
    return 0

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        raise SystemExit(self_test(sys.argv[2]))
    from halfframe.gui import main
    raise SystemExit(main())
