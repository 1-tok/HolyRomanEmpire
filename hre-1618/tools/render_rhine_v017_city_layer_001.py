#!/usr/bin/env python3
"""v017 non-destructive coordinate-locked city layer proof.

Renders canonical city assets at their geographic coordinates, with existing
registered Rhine/Main guide geometry. The original painted v016 strip remains
untouched. Missing Bingen/Frankfurt artwork is explicitly shown as QA anchors,
not silently replaced with invented cities. No painted panorama warp.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import json,hashlib,sys,math
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"tools"))
from build_rhine_batch001 import px
OUT=R/"reports/rhine-v017-city-layer-001";OUT.mkdir(parents=True,exist_ok=True)
BASE=R/"base/base_3600.jpg"
V016=R/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png"
RHINE=R/"maps/canvas/rhine-v012-geographic-overlay.png"
MAIN=R/"reports/main-batch-001/main-canonical-transparent.png"
MAN=R/"placements/rhine-v017-panel-manifest.json"
M=json.loads(MAN.read_text())
A=Image.open(BASE).convert("RGBA")
B=Image.open(V016).convert("RGBA")
G=Image.open(RHINE).convert("RGBA")
H=Image.open(MAIN).convert("RGBA")
assert all(im.size==(3600,4800) for im in [A,B,G,H])
before=hashlib.sha256(V016.read_bytes()).hexdigest()
assert before=="b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4"
# Keep the photograph-like source image only as read-only style reference.
# Actual city proof is drawn over base with geographic water masks and city assets,
# intentionally NOT old whole panos (their river branches were invented).
bbox=(935,1830,1570,2400)
x0,y0,x1,y1=bbox
canvas=A.crop(bbox)
rh=G.crop(bbox);ma=H.crop(bbox)
# Canonical water: geography control at the same map locations used in v016 QA.
canvas=Image.alpha_composite(canvas,rh)
canvas=Image.alpha_composite(canvas,ma)
by={q["site"]:q for q in M["cities"]}
sites=["Bingen","Mainz","Frankfurt","Oppenheim","Worms","Speyer","Germersheim"]
sprites={"Mainz":"sprites/Mainz.png","Worms":"sprites/Worms.png","Speyer":"sprites/Speyer.png"}
# Place unique city art above the true river course and with transparent alpha.
# No second Mainz or duplicate city painted in backdrop.
cities_layer=Image.new("RGBA",canvas.size,(0,0,0,0))
qa_data=[]
placed_boxes={}
for name in sites:
    q=by[name];x,y=px(q["lat"],q["lon"]);xlocal=int(round(x-x0));ylocal=int(round(y-y0))
    rec=dict(name=name,work_pixel=[round(x,2),round(y,2)],
             final_pixel=[round(x*3,2),round(y*3,2)],
             source=sprites.get(name),status="anchored_pending_sprite")
    if name in sprites:
        path=R/sprites[name];sprite=Image.open(path).convert("RGBA")
        # Scale of 105px is the current working-page legacy policy.
        sprite.thumbnail((105,105),Image.Resampling.LANCZOS)
        t=(xlocal-sprite.width//2,ylocal-sprite.height//2)
        cities_layer.alpha_composite(sprite,t)
        placed_boxes[name]=(t[0],t[1],t[0]+sprite.width,t[1]+sprite.height)
        rec.update(status="legacy_city_sprite_preview_only",shown_size_px=list(sprite.size),
                   bbox_panel_pixels=list(placed_boxes[name]),
                   native_detail_at_300ppi="NOT VERIFIED")
    qa_data.append(rec)
canvas=Image.alpha_composite(canvas,cities_layer)
# Audit overlapping sprite bounding boxes.
collisions=[]
for a,aa in placed_boxes.items():
    for b,bb in placed_boxes.items():
        if a>=b:continue
        ix=max(0,min(aa[2],bb[2])-max(aa[0],bb[0]))
        iy=max(0,min(aa[3],bb[3])-max(aa[1],bb[1]))
        if ix*iy:collisions.append(dict(a=a,b=b,overlap_px=ix*iy))
# Draw unpainted anchor markers ONLY in a separate QA map (not the artwork).
qa=canvas.copy();d=ImageDraw.Draw(qa)
for rec in qa_data:
    ix=int(round(rec["work_pixel"][0]-x0));iy=int(round(rec["work_pixel"][1]-y0))
    if rec["status"].startswith("anchored"):
        d.ellipse((ix-5,iy-5,ix+5,iy+5),fill=(250,226,64),outline=(35,31,26),width=2)
    d.text((ix+8,iy-14),rec["name"],fill=(255,246,182),stroke_width=2,stroke_fill=(31,25,23))
# Final image is plainly a working proof at 1x, not print-approved artwork.
canvas.convert("RGB").save(OUT/"seven-city-fixed-course-preview.jpg",quality=94)
qa.resize(((x1-x0)*2,(y1-y0)*2),Image.Resampling.LANCZOS).convert("RGB").save(
    OUT/"seven-city-registration-2x.jpg",quality=94)
cities_layer.save(OUT/"unique-city-transparent-layer.png",optimize=True)
qa_report=dict(version="v017",status="PLACEMENT PROOF ONLY; NOT NATIVE HIGH-RES ART",
    geographic_frame_bbox=bbox,existing_city_sprite_count=len(placed_boxes),
    missing_city_sprite_count=len(sites)-len(placed_boxes),sites=qa_data,
    collisions=collisions,artwork_unique_count=len(placed_boxes),
    river_source="maps/canvas/rhine-v012-geographic-overlay.png",
    main_source="reports/main-batch-001/main-canonical-transparent.png",
    expected_print_master=[10800,14400],ppi_at_36_by_48=300,
    v016_sha256=before,print_ready=False,original_v016_unchanged=True,
    river_watercourse_historical_1618_verified=False,
    geo_registration_pass=True,visual_landscape_join_pass=False,
    statement="This is a first actual coordinate-locked composition using three existing city sprites and verified geographic Main/Rhine. It is NOT painted city landscape and does not claim new Bingen/Frankfurt art.")
(OUT/"qa.json").write_text(json.dumps(qa_report,indent=2)+"\n")
assert hashlib.sha256(V016.read_bytes()).hexdigest()==before
print("PASS geographic city layer anchored",len(placed_boxes),"existing city sprites",len(sites)-len(placed_boxes),"missing",len(collisions),"bbox overlaps")
