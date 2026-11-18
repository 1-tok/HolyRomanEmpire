#!/usr/bin/env python3
"""v017 registration gate for Bingen–Mainz–Frankfurt and Worms–Speyer.

Create actual on-canvas map-scale river and city geometry guides from existing
approved source and fixed HRE projected anchors. NO invented painted city art.
Guide is the invariant underlay for later horizon-free native repaint.
"""
from pathlib import Path
import json,sys,hashlib,math
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_rhine_batch001 import px
OUT=ROOT/"reports/rhine-v017-geometry-lock-001"
OUT.mkdir(parents=True,exist_ok=True)
CONFIG=json.loads((ROOT/"placements/rhine-v017-panel-manifest.json").read_text())
BASE=ROOT/"base/base_3600.jpg"
PAINT=ROOT/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png"
RIVER=ROOT/"maps/canvas/rhine-v012-geographic-overlay.png"
MAIN=ROOT/"reports/main-batch-001/main-canonical-transparent.png"
base=Image.open(BASE).convert("RGBA")
paint=Image.open(PAINT).convert("RGBA")
rhine=Image.open(RIVER).convert("RGBA")
main=Image.open(MAIN).convert("RGBA")
assert all(i.size==(3600,4800) for i in (base,paint,rhine,main))
assert hashlib.sha256(PAINT.read_bytes()).hexdigest()=="b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4"
# Fixed coordinates in the global 3600px registration grid; no independent
# scaled image map for each city. Each piece is a crop of same source.
regions=[
  {"id":"bingen-mainz-frankfurt", "bbox":[955,1860,1550,2115],
   "sites":["Bingen","Mainz","Frankfurt","Hanau","Aschaffenburg","Oppenheim","Boppard","Worms"],
   "critical":"The Main meets the Rhine at Mainz; the river and urban position are locked independently."},
  {"id":"worms-speyer", "bbox":[1060,2050,1430,2380],
   "sites":["Oppenheim","Worms","Speyer","Germersheim"],
   "critical":"The Rhine is one shared centerline; only landscape and settlement layers are repainted."}
]
by={x["site"]:x for x in CONFIG["cities"]}
M=Image.alpha_composite(base,paint)
print_info=[]
for region in regions:
    x0,y0,x1,y1=region["bbox"]
    window=(x0,y0,x1,y1)
    source=M.crop(window)
    gw=rhine.crop(window).getchannel("A").point(lambda a:185 if a>100 else 0)
    ge=Image.new("RGBA",source.size,(214,38,201,0));ge.putalpha(gw)
    composite=Image.alpha_composite(source,ge)
    # main overlay as cyan only in geographic guide; distinguish two rivers.
    mw=main.crop(window).getchannel("A").point(lambda a:210 if a>100 else 0)
    layer=Image.new("RGBA",source.size,(13,244,234,0));layer.putalpha(mw)
    composite=Image.alpha_composite(composite,layer)
    draw=ImageDraw.Draw(composite)
    candidates=[]
    for name in region["sites"]:
        if name not in by:raise ValueError("Missing site "+name)
        item=by[name];x,y=px(item["lat"],item["lon"])
        if not (x0<=x<x1 and y0<=y<y1):
            # record external context anchors but do not draw them off the canvas
            candidates.append(dict(name=name,map_px=[round(x,2),round(y,2)],in_frame=False))
            continue
        cx,cy=x-x0,y-y0
        draw.ellipse((cx-5,cy-5,cx+5,cy+5),fill=(255,230,55),outline=(38,31,25),width=2)
        draw.text((cx+8,cy-9),name,fill=(255,230,55),stroke_width=2,stroke_fill=(20,20,22))
        candidates.append(dict(name=name,map_px=[round(x,2),round(y,2)],
                final_print_px=[round(x*3,2),round(y*3,2)],local_panel_px=[round(cx,2),round(cy,2)],in_frame=True))
    draw.text((10,8),"MAGENTA Rhine / CYAN Main - GEOGRAPHY GUIDE, NOT PAINTED ART",
        fill=(255,240,146),stroke_width=2,stroke_fill=(30,30,35))
    source.save(OUT/(region["id"]+"-source-1x.png"))
    composite.convert("RGB").save(OUT/(region["id"]+"-registration-1x.jpg"),quality=95)
    # 3x scaled diagnostic only, not a native painting
    composite.resize((composite.width*3,composite.height*3),Image.Resampling.LANCZOS).convert("RGB").save(
        OUT/(region["id"]+"-registration-3x.jpg"),quality=94)
    print_info.append(dict(id=region["id"],bbox_work_px=region["bbox"],
        print_bbox_px=[v*3 for v in region["bbox"]],site_anchors=candidates,
        source_image=region["id"]+"-source-1x.png",
        registered_guide=region["id"]+"-registration-3x.jpg",
        geometry="same global projected coordinates for both neighboring sections",
        must_repaint="independent horizon-free city, bank, field and terrain art above fixed river layer",
        bridge_and_bank_approval=False))
# These facts are assertable in the canonical map coordinate system.
pairs=[
("Bingen","Mainz"),("Mainz","Frankfurt"),("Mainz","Worms"),
("Worms","Speyer"),("Speyer","Germersheim")
]
relations=[]
for a,b in pairs:
    p=px(by[a]["lat"],by[a]["lon"]);q=px(by[b]["lat"],by[b]["lon"])
    relations.append(dict(a=a,b=b,dx_px=round(q[0]-p[0],1),
        dy_px=round(q[1]-p[1],1),distance_work_px=round(math.dist(p,q),1)))
audit=dict(version="v017",status="GEOREGISTRATION LOCKED; NATIVE REPAINT PENDING",
    print_master=[10800,14400],print_inches=[36,48],dpi=300,
    original_v016_preserved=True,source_water="rhine-v012 geographic and main-canonical guide",
    historical_watercourse_accuracy_1618_unverified=True,
    horizon_in_paintings_allowed=False,
    font_or_label_in_paintings_allowed=False,
    full_visual_join_pass=False,print_approval=False,
    original_new_highres_paintings_completed=False,
    selected_regions=print_info,city_relations=relations,
    corrected_method="Use one true projected map for river/settlement locations; compose independent horizon-free native artwork and test its alpha/join at the exact same fixed coordinates.",
    next_requirement="Native city-bearing transparent paintings based on this exact guide; no stretching of previously generated panoramas")
(OUT/"qa.json").write_text(json.dumps(audit,indent=2)+"\n")
print("PASS: 2 fixed-geometry guide regions; original v016 unchanged; print approval FALSE.")
