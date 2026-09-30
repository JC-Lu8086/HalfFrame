# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Explicit format conversions. Original-format export stays in image_io."""
from __future__ import annotations
import errno
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
from PIL import Image
import piexif
import tifffile
from .image_io import ImageData, ImageIOError, _bbox


def _publish(source: Path, destination: Path):
    try:
        os.link(source, destination)
    except FileExistsError as exc:
        raise ImageIOError('文件已存在，不会覆盖 / Output already exists: ' + destination.name) from exc
    except OSError as exc:
        if exc.errno not in (errno.EPERM, errno.EACCES, errno.ENOTSUP, errno.EXDEV, errno.EINVAL, errno.ENOSYS):
            raise
        created = False
        try:
            with destination.open('xb') as output:
                created = True
                with source.open('rb') as original:
                    shutil.copyfileobj(original, output)
        except Exception:
            if created:
                destination.unlink(missing_ok=True)
            raise


def export_converted_crop(data: ImageData, bbox, rotation: int, destination: Path,
                          output_format: str, jpeg_quality: int = 95):
    if rotation not in (0,90,180,270):
        raise ImageIOError('仅支持直角旋转 / Only quarter-turn rotations are supported')
    if output_format not in ('jpeg','tiff16'):
        raise ImageIOError('不支持的输出格式 / Unsupported output format')
    destination = Path(destination)
    expected = {'.jpg','.jpeg'} if output_format == 'jpeg' else {'.tif','.tiff'}
    if destination.suffix.lower() not in expected:
        raise ImageIOError('输出扩展名与格式不符 / Output extension does not match format')
    if destination.exists():
        raise ImageIOError('文件已存在，不会覆盖 / Output already exists: ' + destination.name)
    stat = data.source.stat()
    if (stat.st_size,stat.st_mtime_ns) != data.metadata.get('source_signature'):
        raise ImageIOError('原文件已更改，请重新导入 / Source changed; please import again')
    actual = _bbox(bbox,data.width,data.height)
    l,t,r,b = actual
    pixels = np.ascontiguousarray(np.rot90(data.pixels[t:b,l:r], -rotation//90))
    if pixels.ndim == 3 and pixels.shape[-1] == 1:
        pixels = pixels[...,0]
    height,width = pixels.shape[:2]
    resolution = data.metadata.get('resolution',(72,72))
    if rotation in (90,270):
        resolution = resolution[::-1]
    icc = data.metadata.get('icc_profile')
    notes = []
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.halfframe-',dir=destination.parent) as tmp:
        final = Path(tmp)/destination.name
        if output_format == 'tiff16':
            if pixels.dtype == np.uint8:
                pixels = pixels.astype(np.uint16) * 257
                notes.append('8-bit 数值精确映射到 16-bit；不会增加原始细节。 / 8-bit values are mapped exactly to 16-bit; no new detail is created.')
            else:
                pixels = pixels.astype(np.uint16,copy=False)
            photo = data.metadata.get('photometric',2 if pixels.ndim == 3 and pixels.shape[-1] >= 3 else 1)
            extra = [(274,'H',1,1,False)]
            for code,value in data.metadata.get('descriptive_tags',{}).items():
                extra.append((code,'s',0,value,False))
            if icc:
                extra.append((34675,'B',len(icc),icc,False))
            tifffile.imwrite(final,pixels,photometric=photo,planarconfig='contig',
                             extrasamples=data.metadata.get('extrasamples') or None,
                             compression='deflate',resolution=resolution,
                             resolutionunit=data.metadata.get('resolutionunit',2),
                             metadata=None,software='HalfFrame 0.2.2 by J.C. Lu',extratags=extra,
                             bigtiff=pixels.nbytes >= 4_000_000_000)
            bit_depth,format_name,lossless = 16,'TIFF',True
            notes.append('16-bit TIFF 使用无损压缩，保留裁切范围内全部像素。 / Lossless 16-bit TIFF retains the complete selected area.')
        else:
            if not 1 <= int(jpeg_quality) <= 100:
                raise ImageIOError('JPG 质量必须为 1–100 / JPEG quality must be 1–100')
            if pixels.dtype.itemsize == 2:
                pixels = (pixels.astype(np.uint32)//257).astype(np.uint8)
                notes.append('16-bit 转为 8-bit JPG，精度会降低。 / 16-bit is reduced to 8-bit for JPEG.')
            if data.metadata.get('photometric') == 0:
                pixels = 255-pixels
            image = Image.fromarray(pixels)
            if image.mode in ('RGBA','LA'):
                foreground = image.convert('RGBA')
                background = Image.new('RGBA',foreground.size,(255,255,255,255))
                image = Image.alpha_composite(background,foreground).convert('RGB')
                notes.append('透明区域合成白色背景。 / Transparency is composited onto white.')
            elif image.mode not in ('L','RGB'):
                image = image.convert('RGB')
            exif = {'0th':{274:1,256:width,257:height,305:b'HalfFrame 0.2.2 by J.C. Lu'},
                    'Exif':{40962:width,40963:height},'1st':{},'thumbnail':None}
            for tag,value in data.metadata.get('descriptive_tags',{}).items():
                if tag in (271,272,306,315,33432):
                    exif['0th'][tag] = value.encode('utf-8')
            image.save(final,format='JPEG',quality=int(jpeg_quality),subsampling=0,
                       optimize=True,exif=piexif.dump(exif),icc_profile=icc,dpi=resolution)
            bit_depth,format_name,lossless = 8,'JPEG',False
            notes.append('JPG 为重新有损编码；如需保留原质量请选择原格式。 / JPEG is re-encoded with loss; use Original format to preserve source quality.')
        _publish(final,destination)
    return dict(actual_bbox=actual,width=width,height=height,displayed_size=(width,height),
                pixel_size=(width,height),orientation_storage='pixels',stored_orientation=1,
                bit_depth=bit_depth,format=format_name,lossless=lossless,metadata_notes=notes)
