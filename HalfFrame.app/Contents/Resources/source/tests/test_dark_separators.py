# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""A colour-uniform gap must stay distinct from dark photographic backgrounds."""
import numpy as np
import pytest
from PIL import Image
from halfframe.splitter import detect_split, split_boxes


@pytest.mark.parametrize('turns',range(4))
def test_brown_gap_in_dark_scene_is_usable_and_preserves_frames(turns):
    rng=np.random.default_rng(319)
    h,w=500,800
    pixels=np.clip(rng.normal((14,24,25),7,(h,w,3)),0,255).astype('uint8')
    left,right=390,432
    pixels[:,left:right]=np.clip(rng.normal((13,10,3),1.2,(h,right-left,3)),0,255).astype('uint8')
    # Isolated visible details on each photo, separate from the film base.
    pixels[90:150,90:150]=(185,160,130)
    pixels[300:380,610:665]=(145,180,210)
    xx=np.indices((h,w))[1]
    masks=[np.rot90(xx<left,turns),np.rot90(xx>=right,turns)]
    pixels=np.rot90(pixels,turns);height,width=pixels.shape[:2]
    split=detect_split(Image.fromarray(pixels),width,height)
    assert not split['export_blocked']
    boxes=split_boxes(split,width,height)
    coord=1 if split['axis']=='vertical' else 0
    masks.sort(key=lambda m:np.nonzero(m)[coord].mean())
    coverage=np.zeros((height,width),dtype=bool)
    for (l,t,r,b),mask in zip(boxes,masks):
        coverage[t:b,l:r]=True
        ys,xs=np.nonzero(mask)
        assert l<=xs.min() and r>xs.max() and t<=ys.min() and b>ys.max()
    assert coverage.all()
    assert split['start']-split['end']<80


@pytest.mark.parametrize('turns',range(4))
def test_offcentre_shadow_is_not_a_two_frame_separator(turns):
    rng=np.random.default_rng(22)
    pixels=rng.integers(60,220,(500,800,3),dtype='uint8')
    pixels[:,265:300]=(8,9,4)
    pixels=np.rot90(pixels,turns)
    height,width=pixels.shape[:2]
    split=detect_split(Image.fromarray(pixels),width,height)
    assert split['export_blocked']
