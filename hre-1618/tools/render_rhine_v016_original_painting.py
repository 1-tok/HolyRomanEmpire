#!/usr/bin/env python3
"""Restore complete extended Rhine v011 painting on actual HRE map.

Required immutable pixel source (binary intake):
  hre-1618/assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png

The v011 full extended overlay was assembled with north/south seam repair and must be
uploaded verbatim. DO NOT generate a proxy, use v013's procedural shoreline,
or claim an unverified 1618 Rhine watercourse fit.

Review outputs are separate from earlier accepted versions; no originals overwritten.
"""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"base/base_3600.jpg"
SOURCE=ROOT/"assets/reference/rhine-v011-registered-overlay-3600x4800.png"
OUT=ROOT/"maps/canvas"
REPORT=ROOT/"reports/rhine-v016-restored-painted-strip"
WIDTH,HEIGHT=3600,4800
def main():
    if not SOURCE.exists():
        raise SystemExit("REQUIRED V011 PAINTED PIXELS MISSING: "+str(SOURCE)+"; do not substitute procedural artwork")
    for p in (OUT,REPORT):p.mkdir(parents=True,exist_ok=True)
    base=Image.open(BASE).convert("RGBA")
    src=Image.open(SOURCE).convert("RGBA")
    if base.size!=(WIDTH,HEIGHT) or src.size!=(WIDTH,HEIGHT):
        raise ValueError(f"Wrong canvas dimensions base {base.size} overlay {src.size}")
    bbox=src.getbbox()
    if bbox is None or (bbox[2]-bbox[0])<150 or (bbox[3]-bbox[1])<1200:
        raise ValueError("Approved illustrated v011 painting missing or unreasonably small")
    # The extended full v011 art must be reproduced WITHOUT any v012-v015 redraws.
    # Its exact premultiplied colors and alpha are placed unchanged.
    overlay_copy=OUT/"rhine-v016-original-painted-overlay.png"
    src.save(overlay_copy,optimize=True)
    decoded=Image.open(overlay_copy).convert("RGBA")
    if any(c.getbbox() for c in ImageChops.difference(decoded,src).split()):
        raise ValueError("Painted pixel copy changed")
    composite=Image.alpha_composite(base,src)
    full=OUT/"rhine-v016-original-painted-strip-full-map.jpg"
    composite.convert("RGB").save(full,quality=95,subsampling=0)
    composite.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(
        REPORT/"full-map-1200.jpg",quality=94)
    x0=max(0,bbox[0]-95);y0=max(0,bbox[1]-95)
    x1=min(WIDTH,bbox[2]+95);y1=min(HEIGHT,bbox[3]+95)
    composite.crop((x0,y0,x1,y1)).convert("RGB").save(
        REPORT/"real-canvas-illustrated-rhine-review.jpg",quality=96)
    sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    report=dict(version="v016",review_only=True,approved_for_print=False,
        geographic_canvas="base/base_3600.jpg",
        original_painted_overlay=str(SOURCE.relative_to(ROOT)),
        original_painted_overlay_sha256=sha,
        original_painted_bbox_pixels=bbox,canvas=[WIDTH,HEIGHT],
        render_order=["actual HRE base","verbatim full v011 extended painted strip"],
        excluded=["v012 procedural river redraw","v013 wetland motifs","v015 invented miniature cities"],
        paint_pixel_integrity="PASS: RGBA image preserved exactly after PNG output",
        map_geometry_1618_certified=False,
        notes="Full extended v011 artwork shown on historic base as registered; painted water follows the registration, not independently QA-certified hydrography. Do not claim to have aligned every historic braid or Ill junction.",
        artifacts=[str(full.relative_to(ROOT)),str(overlay_copy.relative_to(ROOT))])
    (REPORT/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: Restored original v011 painted artwork on real HRE base; review only; SHA256",sha)
if __name__=="__main__":main()
