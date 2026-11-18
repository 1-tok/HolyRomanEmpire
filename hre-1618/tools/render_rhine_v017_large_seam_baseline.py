#!/usr/bin/env python3
"""v017 large-painted-section seam contract — no city-sprite substitution.

Cuts north, center, and south from the SAME approved, georegistered v011
painted corridor, with overlapping edges. Reassembles their unique nonoverlap
cores pixel-for-pixel and provides seam references for future separately
painted northern and southern extensions. These slices themselves are
existing original artwork, NOT newly generated northern/southern paintings.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png'
OUT=ROOT/'reports/rhine-v017-large-seam-baseline'
OUT.mkdir(parents=True,exist_ok=True)
im=Image.open(SOURCE).convert('RGBA')
assert im.size==(3600,4800)
h=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert h=='b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4'
# Exact painting bbox 802,1901,1273,3274. Preserve generous x margins.
X=(750,1350)
# Core intervals form a non-overlapping partition of original painterly strip.
cores=[('north',(1901,2340)),('center',(2340,2710)),('south',(2710,3274))]
OVERLAP=70
panels=[]
rebuilt=Image.new('RGBA',im.size)
for n,(cy0,cy1) in cores:
    sy0=max(0,cy0-OVERLAP)
    sy1=min(im.height,cy1+OVERLAP)
    bounds=(X[0],sy0,X[1],sy1)
    panel=im.crop(bounds)
    filename=f'rhine-v017-{n}-original-painting-with-overlap.png'
    panel.save(OUT/filename,optimize=True)
    # Rebuild from unchanged central core only. No two overlays double-composited.
    core=panel.crop((0,cy0-sy0,X[1]-X[0],cy1-sy0))
    rebuilt.paste(core,(X[0],cy0))
    panels.append({'section':n,'source_bbox_px':list(bounds),
        'unblended_core_y_px':[cy0,cy1],
        'overlap_top_px':cy0-sy0,'overlap_bottom_px':sy1-cy1,
        'image':filename,
        'source':'Original registered v011 painted pixels (unchanged)',
        'new_painting':False})
# This is strict pixel-exact QA of established paint, not new independent art.
original=Image.new('RGBA',im.size)
original.paste(im.crop((X[0],1901,X[1],3274)),(X[0],1901))
diff=ImageChops.difference(original,rebuilt)
assert all(channel.getbbox() is None for channel in diff.split())
# Preserve full-area background outside the strip entirely.
base=Image.open(ROOT/'base/base_3600.jpg').convert('RGBA')
composite=Image.alpha_composite(base,rebuilt)
crop=(680,1815,1480,3365)
review=composite.crop(crop).convert('RGB')
d=ImageDraw.Draw(review)
for y in (2340,2710):
    v=y-crop[1]
    d.line((0,v,review.width,v),fill=(233,82,47),width=2)
review.save(OUT/'original-three-section-map-scale-join-QA.jpg',quality=94)
# Painted-water continuity in the original art is not the same as conformance
# to period Rhine centerline geometry. Report separately.
qa={'status':'PASS: source-piece joins exactly reproduce original v011 raster',
 'geographic_1618_watercourse_approved':False,
 'new_north_or_south_extension_complete':False,
 'new_paintings_binaries_in_repo':False,
 'source_sha256':h,
 'core_partition_y_px':[1901,2340,2710,3274],
 'stitched_pixels_identical':True,
 'raster_difference_pixels':0,
 'visual_master':'large continuous original painting; never miniature isolated cities',
 'sections':panels,
 'north_extension_join_contract':{'join_at_map_y':1901,'required_bank_tangent':'Must match original painting and geographic reference; exact approved pixels at boundary'},
 'south_extension_join_contract':{'join_at_map_y':3274,'required_bank_tangent':'Must match original painting and geographic reference; exact approved pixels at boundary'},
 'print_ready':False,
 'note':'Exact existing raster joins pass. New independently painted extensions must separately pass bank and visual QA; do not assume their joins pass.'}
(OUT/'qa.json').write_text(json.dumps(qa,indent=2)+'\n')
print('PASS exact source reconstruction; new art extensions pending')
