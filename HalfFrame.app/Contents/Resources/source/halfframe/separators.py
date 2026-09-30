# SPDX-License-Identifier: MIT
# Copyright (C) 2026 J.C. Lu
"""Locate colour-uniform film separators at several noise thresholds."""
from __future__ import annotations
import numpy as np


def _runs(mask):
    d = np.diff(np.r_[False, mask, False].astype(np.int8))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def _candidates(colors, axis="vertical"):
    colors=np.asarray(colors,dtype=np.float32)
    if colors.max()>1.5: colors=colors/255.
    m=colors if axis=="vertical" else colors.swapaxes(0,1)
    h,w,_=m.shape
    trim=max(1,int(h*.02)); m=m[trim:-trim]
    # max channel prevents chromatic dark scenery collapsing to one grey value.
    spread=m.std(axis=0).max(axis=1)
    # Mean +/- std is only used for darkness; robust quantiles are substantially
    # slower. Dark scenery must still pass the much tighter spread tests.
    mean=m.mean(axis=0)
    dark=(mean.max(axis=1)<.27)
    light=(mean.min(axis=1)>.75)
    found=[]
    for kind, level in (("dark",dark),("light",light)):
      for threshold in (.008,.012,.018,.025,.035,.05):
        mask=level & (spread<threshold)
        # Fill isolated grain-sized holes; never join separated scene bands.
        for _ in range(2): mask[1:-1] |= mask[:-2] & mask[2:]
        for start,end in _runs(mask):
          length=end-start; center=(start+end)/(2*w)
          if length<max(4,w*.003):continue
          # Geometry is evidence: a two-frame separator is near the centre.
          # Off-centre black scenery in a single portrait is not a separator.
          if not .40<center<.60:continue
          if length>w*.23:continue
          pad=max(5,int(w*.02)); inside=float(np.median(spread[start:end]))
          if kind == 'light' and inside > .025:
            continue  # Clouds and pale scenery are not uniform scanner gaps.
          ls=spread[max(0,start-pad):start]; rs=spread[end:min(w,end+pad)]
          left=float(np.median(ls)) if ls.size else inside
          right=float(np.median(rs)) if rs.size else inside
          # Multithreshold candidates nest. Reward actual steps around a tight
          # core, rather than broad dark scene extensions at loose thresholds.
          edge=np.clip((max(left,right)-inside)/max(.008,inside),0,3)/3
          both=np.clip((min(left,right)-inside)/max(.008,inside),0,2)/2
          uniform=np.clip(1-inside/.035,0,1)
          width_bonus=np.clip(length/(w*.025),0,1)
          score=float(.33+.22*uniform+.20*edge+.10*both+.20*width_bonus-2.1*abs(center-.5))
          if w>h:score+=.09
          confidence=float(np.clip(score-.09 if w>h else score,0,.99))
          if confidence < .40:
            continue
          if w < h and h/w >= 1.25 and confidence < .80:
            continue  # A horizon across a full photograph is weak evidence.
          found.append(dict(axis=axis,start=int(start),end=int(end),kind=kind,
                            confidence=confidence,score=score,threshold=threshold,
                            rgb_spread=inside,uncertain_width=bool(length>w*.12)))
    # NMS joins nested cores from the threshold sweep, avoiding artificial
    # ambiguity between several thresholds describing the very same film gap.
    selected=[]
    for c in sorted(found,key=lambda c:c['score'],reverse=True):
      if any(c['kind']==p['kind'] and min(c['end'],p['end'])-max(c['start'],p['start'])>0
             and (min(c['end'],p['end'])-max(c['start'],p['start']))/min(c['end']-c['start'],p['end']-p['start'])>.5 for p in selected):
        continue
      selected.append(c)
    if not selected and (w >= h or h/w < 1.25):
      # Some black photos are literally indistinguishable from the film base.
      # A low-variance plateau THROUGH THE CENTRE supports only a tentative
      # central core; report the uncertainty instead of growing into scenery.
      for kind,level in (("dark",dark),("light",light)):
        mask=level & (spread<.018)
        mask[1:-1]|=mask[:-2]&mask[2:]
        for start,end in _runs(mask):
          if (w*.16<end-start<w*.60 and
              (start<w*.49 and end>w*.51 or w*.40<start<w*.60 or w*.40<end<w*.60)):
            # A blank half-frame may join the gap. Use the nearest low-texture
            # core to the centre and flag it for review; never split a uniform
            # whole image or an off-centre shadow in a normal photograph.
            core_width=max(4,int(w*.04))
            lo=max(start,min(int(w*.48),end-core_width));hi=lo+core_width
            selected.append(dict(axis=axis,start=lo,end=hi,kind=kind,
                                 confidence=.43,score=.43+(.09 if w>h else 0),
                                 threshold=.018,rgb_spread=float(np.median(spread[lo:hi])),
                                 uncertain_width=True,plateau=[int(start),int(end)]))
    return sorted(selected,key=lambda c:c['score'],reverse=True)


def all_candidates(colors):
    return sorted(_candidates(colors,"vertical")+_candidates(colors,"horizontal"),key=lambda c:c['score'],reverse=True)
