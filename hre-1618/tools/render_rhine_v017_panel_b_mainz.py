#!/usr/bin/env python3
"""v017 Panel B Mainz/Main geographical painting registration.

Builds exact 1x and 3x reference views from repository assets only. The
high-res reference is INTERPOLATED for layout, never claimed to be newly painted
print-ready detail. The confluence is a real Main geometry overlay, NOT invented
river strokes. No procedural replacement of original v016 painting is accepted.

Future native panel artists may trace the QA guide and render independently
at >= print_bbox dimensions. QA guide markers must not enter the painting.
"""
import json, hashlib, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_rhine_batch001 import px
MAN=ROOT/"placements/rhine-v017-panel-manifest.json"
RPT=ROOT/"reports/rhine-v017-panel-b"
RPT.mkdir(parents=True,exist_ok=True)
cfg=json.loads(MAN.read_text())
b=next(p for p in cfg["panels"] if p["id"]=="B")
x0,y0,x1,y1=b["bbox_work_px"]
assert (x0,y0,x1,y1)==(1010,1740,1850,2180)
W,H=(x1-x0),(y1-y0)
base=Image.open(ROOT/"base/base_3600.jpg").convert("RGBA")
original=Image.open(ROOT/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png").convert("RGBA")
main_geo=Image.open(ROOT/"reports/main-batch-001/main-canonical-transparent.png").convert("RGBA")
assert base.size==original.size==main_geo.size==(3600,4800)
expected_hash="b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4"
assert hashlib.sha256((ROOT/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png").read_bytes()).hexdigest()==expected_hash
# Subdivide for precise comparison of original art and corresponding geographic fork.
frame=base.crop((x0,y0,x1,y1))
original_cut=original.crop((x0,y0,x1,y1))
main_cut=main_geo.crop((x0,y0,x1,y1))
# Genuine source pixel integrity: adding it over the actual base preserves
# both layers and no fake geography has been inserted into artwork.
scene=Image.alpha_composite(frame,original_cut)
# Render Main as separate translucent geographic context for compositional study.
geolayer=Image.new("RGBA",scene.size,(233,37,161,0))
ma=main_cut.getchannel("A").point(lambda v:200 if v>100 else 0)
geolayer.putalpha(ma)
georeview=Image.alpha_composite(scene,geolayer)
d=ImageDraw.Draw(georeview)
sites=[]
for rec in cfg["cities"]:
    xx,yy=px(rec["lat"],rec["lon"])
    if not(x0<=xx<x1 and y0<=yy<y1):continue
    c=dict(site=rec["site"],panel=rec["panel"],map_work_px=[round(xx,2),round(yy,2)],
        panel_work_px=[round(xx-x0,2),round(yy-y0,2)],
        panel_final_native_px=[round(3*(xx-x0),2),round(3*(yy-y0),2)])
    sites.append(c)
    sx=round(xx-x0);sy=round(yy-y0)
    d.ellipse((sx-4,sy-4,sx+4,sy+4),fill=(248,227,54),outline=(29,25,23),width=2)
    d.text((sx+9,sy-11),rec["site"],fill=(250,230,100),stroke_width=2,stroke_fill=(42,27,34))
d.text((10,12),"PANEL B / MAIN FORK — MAGENTA GEOGRAPHIC GUIDE",fill=(255,244,170),
       stroke_width=2,stroke_fill=(35,32,38))
# Use 3x scale only for registration guide; native artist must repaint
# at this output size, not use the enlarged pixels as final print master.
scene.resize((W*3,H*3),Image.Resampling.LANCZOS).convert("RGB").save(
    RPT/"panel-b-v016-painting-reference-3x.jpg",quality=94)
georeview.resize((W*3,H*3),Image.Resampling.LANCZOS).convert("RGB").save(
    RPT/"panel-b-main-fork-geographic-qa-3x.jpg",quality=94)
scene.convert("RGB").save(RPT/"panel-b-working-map-source.jpg",quality=93)
# Separate four subregions that isolate city-area visual production:
# Mainz/Rhine confluence plus Main east arm.
subregions=[
 ("mainz-confluence",[1110,1800,1420,2090]),
 ("frankfurt-approach",[1320,1800,1580,2030]),
 ("hanau-main",[1430,1820,1740,2030]),
 ("aschaffenburg-east",[1550,1840,1850,2150])]
for name,rect in subregions:
    ax,ay,bx,by=rect
    if ax<x0 or ay<y0 or bx>x1 or by>y1:
        raise RuntimeError("Subregion exceeds Panel B")
    cut=scene.crop((ax-x0,ay-y0,bx-x0,by-y0))
    cut.resize((cut.width*3,cut.height*3),Image.Resampling.LANCZOS).convert("RGB").save(
        RPT/(name+"-reference-3x.jpg"),quality=94)
qa=dict(version="v017-B",status="GEOGRAPHIC SOURCE REGISTERED; NATIVE ARTWORK NOT YET DELIVERED",
    panel_bbox_work_px=[x0,y0,x1,y1],panel_size_final_print_native_px=[W*3,H*3],
    final_sheet_native_px=cfg["final_print_canvas_px"],
    source_sha256=expected_hash,
    source_art="assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png",
    main_geography="reports/main-batch-001/main-canonical-transparent.png",
    geo_layer_mode="QA only magenta; never baked into original artwork",
    city_anchors=sites,
    main_confluence_constraints=[
      "Main flows westward into Rhine at Mainz; it is a river tributary, not an independent northern Rhine channel",
      "Mainz city occupies actual Mainz bank location, distinct from Frankfurt/Hanau on upstream east river",
      "Only a single painted Mainz city; preserve v016 stylistic brushwork",
      "No unrelated Rhine city/cathedral replicas inside this narrow panel",
      "Render separate transparent finished native art for background terrain, riverbank scenery, cities and decorative text",
      "Water channel and junction QA against existing Main and Rhine projected geometry"
    ],native_original_art_pixels=False,source_interpolated=True,
    historical_city_fabric_verified=False,print_ready=False,
    deliverables=[
      "reports/rhine-v017-panel-b/panel-b-main-fork-geographic-qa-3x.jpg",
      "reports/rhine-v017-panel-b/panel-b-v016-painting-reference-3x.jpg"
    ])
(RPT/"qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print("PASS Panel B geo context",W,H,"3x",W*3,H*3,"settlements",len(sites))
if __name__=="__main__":main()
