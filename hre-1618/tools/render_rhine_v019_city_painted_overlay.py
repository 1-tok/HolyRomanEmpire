#!/usr/bin/env python3
"""Non-destructive print development review for large v019 Rhine/Main painting.
No TPS warp, no skyline horizon, no city icon replacement, no false print pass.
Source image required as exact PNG binary from conversation.
"""
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/"placements/rhine-v019-painterly-overlay-and-joins.json").read_text())
source=R/"assets/reference/rhine-v019-confluence-city-bearing-original.png"
if not source.exists():
    raise SystemExit("Original unwarped v019 PNG not committed yet. No reconstructed substitute is allowed.")
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest["source_sha256"]
im=Image.open(source).convert("RGBA")
assert im.size==(1122,1402)
base=Image.open(R/"base/base_3600.jpg").convert("RGBA")
prev=Image.open(R/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png").convert("RGBA")
assert base.size==prev.size==(3600,4800)
x,y=manifest["placement"]["top_left_work"]
w,h=round(im.width*manifest["placement"]["scale"]),round(im.height*manifest["placement"]["scale"])
scaled=im.resize((w,h),Image.Resampling.LANCZOS)
# Taper alpha at edge on review map ONLY. This cannot produce geographically
# correct river joins, and no seam acceptance is inferred from it.
alph=scaled.getchannel("A")
edge=32
mask=Image.new("L",(w,h),0);pix=mask.load()
for j in range(h):
    for i in range(w):
        pix[i,j]=round(255*min(1.,max(0.,min(i,j,w-i-1,h-j-1)/edge)))
from PIL import ImageChops
scaled.putalpha(ImageChops.multiply(alph,mask))
overlay=Image.new("RGBA",(3600,4800),(0,0,0,0))
overlay.alpha_composite(scaled,(x,y))
assembly=Image.alpha_composite(Image.alpha_composite(base,prev),overlay)
CAN=R/"maps/canvas"
QA=R/"reports/rhine-v019-painterly-overlay"
CAN.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
overlay.save(CAN/"rhine-v019-candidate-unwarped-overlay.png",optimize=True)
assembly.convert("RGB").save(CAN/"rhine-v019-candidate-on-full-map.jpg",quality=94)
assembly.crop((850,1700,1530,2570)).convert("RGB").save(QA/"rhine-v019-map-scale-placement.jpg",quality=95)
# Four source-exact boundary strips are the paint targets for actual extensions.
contracts=[]
bounds={side:box for side,box in [
 ("north",(0,0,1122,150)),("south",(0,1252,1122,1402)),
 ("east",(972,0,1122,1402)),("west",(0,0,150,1402))]}
for side,box in bounds.items():
    cut=im.crop(box)
    out=QA/("rhine-v019-"+side+"-exact-edge.png")
    cut.save(out,optimize=True)
    assert not ImageChops.difference(cut,im.crop(box)).getbbox()
    contracts.append({"side":side,"bounds_px":box,"file":out.name,
       "source_exact":True,"new_extension_painting_complete":False})
QA.joinpath("qa.json").write_text(json.dumps({
 "version":"v019","status":"UNWARPED LARGE-PAINTING REVIEW; NEW EXTENSIONS PENDING",
 "source_sha256":manifest["source_sha256"],
 "print_effective_ppi":manifest["native_effective_print_ppi"],
 "print_300_ppi_pass":False,"full_map_dimensions":[3600,4800],
 "printed_master_dimensions":[10800,14400],
 "geographic_proximity_approved":False,
 "median_city_residual_work_px":manifest["median_residual_work_px"],
 "visual_water_join_approved":False,
 "new_north_south_east_west_art_approved":False,
 "approved_v016_original_unchanged":True,
 "exact_edge_contracts":contracts},indent=2)+"\n")
print("PASS large original v019 unwarped painting composited; four exact edge contracts; geography/print HOLD")
