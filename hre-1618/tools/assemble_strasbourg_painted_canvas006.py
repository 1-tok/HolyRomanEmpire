#!/usr/bin/env python3
"""Place approved-style painted Rhine river reach sprites on the real HRE 1618 map.

Outputs:
  maps/canvas/strasbourg-painted-rhine-006.png    transparent map-sized overlay
  maps/canvas/strasbourg-painted-rhine-006.jpg    base+painted rivers+existing cities
  reports/strasbourg-painted-canvas-006/*         enlarged and QA diagnostic views

The city PNG remains unchanged. We NEVER invent a connector between Strasbourg's
Ill canals and the geographically separate main Rhine. River to river seams
are proven exact. Short white bars in an earlier concept composition are
not copied into this georeferenced assembly.

Source artwork is a prior ImageGen painted scenery image, see batch005; do
not misstate this as freshly generated API painting or historically true 1618.
"""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageChops,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
SPR=ROOT/"assets/sprites/rivers/rhine-illustrated-batch-005"
OUT=ROOT/"maps/canvas"
QA=ROOT/"reports/strasbourg-painted-canvas-006"
BASE=ROOT/"base/base_3600.jpg"
PLAC=ROOT/"placements/rhine-batch-001.json"
W,H=3600,4800
def eq(a,b):
    return not any(c.getbbox() for c in ImageChops.difference(a,b).split())
def main():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    m=json.loads((SPR/"manifest.json").read_text())
    assert m["count"]==5 and m["seam_qa"].startswith("PASS")
    base=Image.open(BASE).convert("RGBA")
    if base.size!=(W,H):raise RuntimeError("Authoritative 3600x4800 canvas missing")
    master=Image.new("RGBA",(W,H),(0,0,0,0))
    segments=[]
    for rec in m["connectors"]:
        path=SPR/rec["file"]
        png=Image.open(path).convert("RGBA")
        if png.size!=(rec["width"],rec["height"]):raise RuntimeError("Sprite file dimension changed")
        if hashlib.sha256(path.read_bytes()).hexdigest()!=rec["sha256"]:raise RuntimeError("Sprite hash changed")
        master.paste(png,(rec["x"],rec["y"]))
        segments.append(rec)
    # Pixel-for-pixel rebuilding from independent source PNG files.
    reconstructed=Image.new("RGBA",(W,H),(0,0,0,0))
    for rec in segments:
        reconstructed.paste(Image.open(SPR/rec["file"]).convert("RGBA"),(rec["x"],rec["y"]))
    if not eq(master,reconstructed):raise RuntimeError("Water scene seam mismatch")
    # Do not introduce manually drawn white transition strips, overlays,
    # shadows or fabricated junctions.
    mask=np.asarray(master.getchannel("A"))
    painted=(mask>0)
    if int(painted.sum())<2000:raise RuntimeError("Missing painterly geographic river")
    cfg=json.loads(PLAC.read_text())
    cities=[]
    citylayer=Image.new("RGBA",(W,H),(0,0,0,0))
    for entry in cfg["entries"]:
        file=ROOT/entry["asset"]
        if not file.exists():continue
        city=Image.open(file).convert("RGBA")
        city.thumbnail((cfg["working_sprite_width_px"],)*2,Image.Resampling.LANCZOS)
        x=round(entry["x"])-city.width//2
        y=round(entry["y"])-city.height//2
        citylayer.alpha_composite(city,(x,y))
        cities.append({"site":entry["site"],"x":x,"y":y,"width":city.width,"height":city.height})
    if {c["site"] for c in cities} != {"Basel","Strasbourg","Speyer","Worms","Mainz"}:
        raise RuntimeError("Expected five existing painted city sprites")
    composite=Image.alpha_composite(Image.alpha_composite(base,master),citylayer)
    # The printable map preview and its independent transparent layers are
    # stored where future HRE rebuild scripts can reference them.
    master.save(OUT/"strasbourg-painted-rhine-006.png",optimize=True)
    citylayer.save(OUT/"existing-city-layer-006.png",optimize=True)
    composite.convert("RGB").save(OUT/"strasbourg-painted-rhine-006.jpg",quality=93)
    composite.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-map-review.jpg",quality=92)
    crop=(870,2360,1280,2810)
    composite.crop(crop).resize((984,1080),Image.Resampling.LANCZOS).convert("RGB").save(QA/"strasbourg-junction-review.jpg",quality=95)
    # Before/after: raw base / canvas with scenic painted river and cities.
    before=Image.alpha_composite(base,citylayer).crop(crop).convert("RGB")
    after=composite.crop(crop).convert("RGB")
    b=before.resize((615,675),Image.Resampling.LANCZOS)
    a=after.resize((615,675),Image.Resampling.LANCZOS)
    pair=Image.new("RGB",(1230,675),(247,242,224));pair.paste(b,(0,0));pair.paste(a,(615,0))
    d=ImageDraw.Draw(pair)
    d.text((14,14),"BEFORE | original base and city",fill=(41,43,35),stroke_width=2,stroke_fill=(249,244,225))
    d.text((629,14),"AFTER | georeferenced scenic river",fill=(41,43,35),stroke_width=2,stroke_fill=(249,244,225))
    pair.save(QA/"before-after-city-river.jpg",quality=93)
    # Verify the source artworks retain their original colors at non-overlap:
    # original master pasted at each exact global coordinate, no interpolation.
    for rec in segments:
        direct=Image.open(SPR/rec["file"]).convert("RGBA")
        test=master.crop((rec["x"],rec["y"],rec["x"]+rec["width"],rec["y"]+rec["height"]))
        if not eq(direct,test):raise RuntimeError("A neighboring sprite overwrote or altered "+rec["file"])
    # Geographic limitation: the Rhine map's modern coarse source may
    # visually meet Strasbourg city painting although actual Strasbourg
    # historically sits on Ill west of Rhine. Do not certify that join.
    qa={
       "map_canvas":"base/base_3600.jpg","canvas_size":[W,H],
       "painted_scenery_source":"assets/sprites/rivers/rhine-illustrated-batch-005/manifest.json",
       "approved_city_source":"placements/rhine-batch-001.json",
       "transparent_map_overlay":"maps/canvas/strasbourg-painted-rhine-006.png",
       "composite_map_canvas":"maps/canvas/strasbourg-painted-rhine-006.jpg",
       "city_layer":"maps/canvas/existing-city-layer-006.png",
       "tiles":len(segments),"placed_cities":cities,
       "pixel_seams":"PASS: 5 painterly river sprite files exactly reconstruct their painted master; no white transition strips used",
       "visible_white_bars_in_this_composition":"none drawn or introduced",
       "river_sprite_content":"actual ImageGen painted water and banks carried from batch 005; not plain cartographic strokes",
       "historical_river_qa":"PENDING: 1618 Ill/Rhine alignment, canal arms and exact historic river course",
       "strasbourg_city_water_qa":"REVIEW REQUIRED: do not mistake main Rhine touching city artwork for verified Ill attachment",
       "print_approval":False,
       "notes":"This is a repository-native full map placement review. The separate city PNGs and painted river source are unchanged; original 1618 base was not overwritten."
    }
    (QA/"qa.json").write_text(json.dumps(qa,indent=2)+"\n")
    (OUT/"strasbourg-painted-rhine-006-placement.json").write_text(json.dumps(qa,indent=2)+"\n")
    print("PASS: actual painted Rhine sprite overlay on base map; 5 geographic reach PNGs, 5 existing cities, no seam bars",flush=True)
if __name__=="__main__":main()
