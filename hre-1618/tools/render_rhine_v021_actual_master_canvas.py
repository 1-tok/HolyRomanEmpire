#!/usr/bin/env python3
"""v021 review-only, full-canvas illustrated corridor assembly.

Requires the ORIGINAL accepted 1024x1536 PNG. No substitute city icons,
no procedural replacement river, no per-sheet x offsets or inferred detail.
Place conservatively as a north-up UNIFORM-SCALE overlay on actual HRE map.
The exterior scenic border is feathered for development preview only.
Print quality and period-geographic fit are explicitly NOT certified.
"""
from pathlib import Path
from PIL import Image, ImageChops
import hashlib,json,math
R=Path(__file__).resolve().parents[1]
SC=R/"assets/reference/rhine-v021-continuous-river-original.png"
BASE=R/"base/base_3600.jpg"
V016=R/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png"
QA=R/"reports/rhine-v021-actual-master-canvas"
OUT=R/"maps/canvas"
QA.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
SPEC=json.loads((R/"placements/rhine-v021-approved-sheets-on-master.json").read_text())
if not SC.is_file():
    raise SystemExit("Original accepted v021 art PNG is missing; do not generate any substitute.")
original_sha=hashlib.sha256(SC.read_bytes()).hexdigest()
if original_sha!=SPEC["source_sha256"]:
    raise ValueError("v021 accepted artwork source checksum mismatch")
art=Image.open(SC).convert("RGBA")
base=Image.open(BASE).convert("RGBA")
v016=Image.open(V016).convert("RGBA")
assert art.size==(1024,1536) and base.size==v016.size==(3600,4800)
# Proof of strictly exact original-sheet reconstruction.
rebuilt=Image.new("RGBA",art.size)
for s in SPEC["sheets"]:
    x0,y0,x1,y1=s["master_crop"]
    lo,hi=s["core_y"]
    piece=art.crop((x0,y0,x1,y1))
    assert piece.width==1024
    core=piece.crop((0,lo-y0,1024,hi-y0))
    rebuilt.paste(core,(0,lo))
assert ImageChops.difference(rebuilt,art).getbbox() is None,"Print sheets do not reconstruct source exactly"
# Use a single uniform scale to avoid the unacceptable non-linear v018 warp.
scale=float(SPEC["working_canvas_placement"]["uniform_scale"])
tx,ty=SPEC["working_canvas_placement"]["top_left_map_px"]
w,h=round(1024*scale),round(1536*scale)
resized=art.resize((w,h),Image.Resampling.LANCZOS)
feather=int(SPEC["working_canvas_placement"]["feather_edge_work_px"])
# Edge fade is visual-only. Never describe the blend as an exact river join.
a=resized.getchannel("A")
edge=Image.new("L",(w,h)); p=edge.load()
for j in range(h):
    for i in range(w):
        dist=min(i,j,w-1-i,h-1-j)
        p[i,j]=round(max(0,min(1,dist/feather))*255) if feather else 255
resized.putalpha(ImageChops.multiply(a,edge))
overlay=Image.new("RGBA",base.size)
overlay.alpha_composite(resized,(tx,ty))
overlay.save(OUT/"rhine-v021-unwarped-master-review-overlay.png",optimize=True)
full=Image.alpha_composite(Image.alpha_composite(base,v016),overlay)
f=OUT/"rhine-v021-print-master-review-3600x4800.jpg"
full.convert("RGB").save(f,quality=94,subsampling=0)
assert Image.open(f).size==(3600,4800)
# QA includes original unblended crop, no unreviewed city markers in print image.
full.crop((max(0,tx-140),max(0,ty-140),min(3600,tx+w+140),min(4800,ty+h+140))).convert("RGB").save(
    QA/"rhine-v021-actual-map-scale-placement.jpg",quality=96)
q={
"status":"ACTUAL HRE CANVAS REVIEW; NOT HISTORIC OR PRINT APPROVED",
"source_sha256":original_sha,
"source_size":[1024,1536],
"working_canvas_size":[3600,4800],
"final_print_canvas_size":[10800,14400],
"sheet_source_pixel_difference_count":0,
"all_sheet_x_offsets": [0,0,0],
"source_has_new_print_detail":False,
"source_upsampled_for_300ppi_master":True,
"geographic_city_anchor_validation":False,
"historic_rhine_main_course_verified":False,
"river_join_to_old_v016_verified":False,
"new_city_sprite_substitution":False,
"placement":{"x":tx,"y":ty,"scale":scale,"width":w,"height":h},
"print_quality":{"final_inches":[36,48],"target_ppi":300,"native_detail_300ppi":False},
"rendered_full_map":str(f.relative_to(R)),
"overlay":str((OUT/"rhine-v021-unwarped-master-review-overlay.png").relative_to(R)),
"approved_for_print":False
}
(QA/"qa.json").write_text(json.dumps(q,indent=2)+"\n")
print("PASS actual full map review, exact source pixels across sheet joins, print/geography hold")
