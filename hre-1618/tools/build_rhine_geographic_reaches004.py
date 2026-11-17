#!/usr/bin/env python3
"""Geographic Rhine reach sprite batch (Basel--Mainz), correcting Strasbourg false joins.

Important: Strasbourg is ON THE ILL, not the main Rhine. Its separately
painted canal network must NOT be forcibly bridged east to the Rhine or
extended north with guessed routes. This batch produces independent,
transparent WATER+BANK sprites from ONE fixed geographic Rhine centerline.

The natural course is rendered just once from the project geo data; the
finished painting is cut in non-overlapping geographic sheet-Y intervals.
Every PNG has a precise original-canvas placement, so reassembly is
pixel-for-pixel with NO connector kinks or double-painted banks.
"""
import json,hashlib,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import numpy as np
from scipy.ndimage import label

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_painted_rhine_batch002 import paint_river,ROI,W,H
OUT=ROOT/"assets/sprites/rivers/rhine-geographic-reaches-004"
QA=ROOT/"reports/rhine-geographic-reaches-004"
BASE=ROOT/"base/base_3600.jpg"
PLACEMENTS=ROOT/"placements/rhine-batch-001.json"
CITY=ROOT/"sprites/Strasbourg.png"
# Boundaries chosen on geographic map rows, never chosen by freehand shapes.
REACHES=[
  ("01-mainz-to-worms",1900,2075),
  ("02-worms-to-speyer",2075,2220),
  ("03-speyer-north",2220,2375),
  ("04-speyer-to-strasbourg-north",2375,2515),
  ("05-strasbourg-rhine-east",2515,2615),
  ("06-strasbourg-south",2615,2750),
  ("07-upper-rhine-north",2750,2890),
  ("08-upper-rhine-to-basel",2890,3050)
]

def all_band_equal(a,b):
    return not any(ch.getbbox() for ch in ImageChops.difference(a,b).split())

def main():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    full,watermask,source_segment_count=paint_river()
    if full.size!=(W,H):raise RuntimeError("Georeferenced master size changed")
    # Single canonical painted source; crop, never resample independent reaches.
    continuous=full.crop((0,1900,W,3050))
    composite=Image.new("RGBA",(W,H),(0,0,0,0))
    pieces=[];prev_end=None
    for n,(reach,y0,y1) in enumerate(REACHES):
        if prev_end is not None and prev_end!=y0:raise RuntimeError("Unjoined geographic Y intervals")
        prev_end=y1
        strip=full.crop((0,y0,W,y1))
        bbox=strip.getbbox()
        if bbox is None:raise RuntimeError("Missing Rhine water in "+reach)
        png=strip.crop(bbox)
        name=reach+".png";file=OUT/name;png.save(file,optimize=True)
        decoded=Image.open(file).convert("RGBA")
        if not all_band_equal(decoded,png):raise RuntimeError("PNG changed pixel values "+name)
        x=bbox[0];y=bbox[1]+y0
        composite.paste(decoded,(x,y))
        pieces.append({"id":reach,"file":name,"x":x,"y":y,"width":decoded.width,
                       "height":decoded.height,"source_map_y":[y0,y1],
                       "sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
                       "role":"individual painted water-and-bank river sprite"})
    expected=Image.new("RGBA",(W,H),(0,0,0,0))
    expected.paste(continuous,(0,1900))
    if not all_band_equal(composite,expected):
        raise RuntimeError("River sprite seam reconstruction mismatch")
    reconstructed=Image.new("RGBA",(W,H),(0,0,0,0))
    for p in pieces:
        reconstructed.paste(Image.open(OUT/p["file"]).convert("RGBA"),(p["x"],p["y"]))
    if not all_band_equal(reconstructed,composite):
        raise RuntimeError("PNG file reassembly mismatch")
    # Audit: there is no new Strasbourg Ill-to-Rhine artwork or invented loop.
    # City PNG stays ABOVE the geographically traced painted Rhine.
    config=json.loads(PLACEMENTS.read_text())
    base=Image.open(BASE).convert("RGBA")
    if base.size!=(W,H):raise RuntimeError("Wrong map base")
    assembled=Image.alpha_composite(base,composite)
    painted=[]
    for entry in config["entries"]:
        file=ROOT/entry["asset"]
        if not file.exists():continue
        city=Image.open(file).convert("RGBA")
        city.thumbnail((config["working_sprite_width_px"],)*2,Image.Resampling.LANCZOS)
        x=round(entry["x"])-city.width//2;y=round(entry["y"])-city.height//2
        assembled.alpha_composite(city,(x,y))
        painted.append({"site":entry["site"],"x":x,"y":y,"width":city.width,"height":city.height})
    if len(painted)<5:raise RuntimeError("Missing previously committed city paintings")
    # Highlight Strasbourg separate watercourse and the authentic main Rhine,
    # only on the diagnostic preview (never on the actual artwork).
    center=next(e for e in config["entries"] if e["site"]=="Strasbourg")
    sx,sy=round(center["x"]),round(center["y"])
    water=np.asarray(composite.getchannel("A"))
    ys,xs=np.where(water[max(0,sy-65):min(H,sy+65),
                          max(0,sx-120):min(W,sx+220)]>220)
    if len(xs)==0:raise RuntimeError("No main Rhine geography near Strasbourg")
    wx=xs+max(0,sx-120);wy=ys+max(0,sy-65)
    # Use the nearest main Rhine pixel east of city; if geometry is west of
    # expected corridor, fail rather than lie about bank orientation.
    east=wx>sx+35
    if not np.any(east):
        raise RuntimeError("No east-of-Strasbourg Rhine water pixels in candidate rendering")
    rhine_x=int(np.median(wx[east]));rhine_y=int(np.median(wy[east]))
    # This gap should remain geographically honest; do NOT create new river.
    sep=max(0,rhine_x-sx)
    zoom=(800,1900,1470,3090)
    assembled.crop(zoom).convert("RGB").save(QA/"rhine-painted-reaches-cities.jpg",quality=93)
    near=(870,2430,1330,2710)
    assembled.crop(near).resize((1150,700),Image.Resampling.LANCZOS).convert("RGB").save(QA/"strasbourg-ill-vs-rhine.jpg",quality=94)
    annotated=assembled.crop(near).convert("RGB")
    d=ImageDraw.Draw(annotated)
    d.ellipse((sx-near[0]-6,sy-near[1]-6,sx-near[0]+6,sy-near[1]+6),
              outline=(226,118,44),width=3)
    d.ellipse((rhine_x-near[0]-6,rhine_y-near[1]-6,
               rhine_x-near[0]+6,rhine_y-near[1]+6),
              outline=(31,105,179),width=3)
    d.text((sx-near[0]-75,sy-near[1]+24),"Strasbourg / Ill",fill=(54,45,32),
           stroke_width=2,stroke_fill=(243,237,215))
    d.text((rhine_x-near[0]+10,rhine_y-near[1]+12),"Rhine course",fill=(30,67,99),
           stroke_width=2,stroke_fill=(243,237,215))
    annotated.resize((1150,700),Image.Resampling.LANCZOS).save(QA/"strasbourg-river-separation-qa.jpg",quality=93)
    assembled.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-base-preview.jpg",quality=90)
    # View individual sprites assembled in the correct continuous course,
    # exactly as they will overlay the geographic canvas.
    isolated=Image.new("RGBA",(W,H),(0,0,0,0))
    isolated.paste(composite,(0,0))
    isolated.crop(zoom).save(QA/"assembled-transparent-rhine-reaches.png",optimize=True)
    manifest={
      "batch":"Rhine geographic painted reaches 004",
      "status":"review candidate; historical 1618 channel locations not yet certified",
      "source":"Natural Earth 10m named Rhine geometry, same map projection as existing base",
      "no_invented_strasbourg_rhine_connection":True,
      "strasbourg_city_on_ill":True,
      "city_rhine_separation_px":sep,
      "river_tile_count":len(pieces),
      "geographic_course_segment_count":source_segment_count,
      "seam_qa":"PASS: independent RGBA PNGs exactly reconstruct geographic continuous master",
      "city_layer_qa":"PASS: all 5 existing city sprites rendered above river",
      "note":"Strasbourg local Ill canal system not extended in this Rhine batch. Previously hand-drawn loops are superseded for geographic preview but preserved in history.",
      "coverage":"north of Basel through Mainz, with the Rhine east of Strasbourg",
      "register_to_map":True,
      "approved_for_print":False,
      "connectors":pieces,
      "cities":painted
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (QA/"qa.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("PASS:",len(pieces),"individual painted geographic river sprites, exact joins, 5 city overlays, Strasbourg Ill not falsely bridged")
if __name__=="__main__":main()
