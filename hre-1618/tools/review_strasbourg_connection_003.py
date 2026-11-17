#!/usr/bin/env python3
"""Review Strasbourg city/Ill connector joins on the AUTHORITATIVE HRE 1618 canvas.

This is a placement QA report, NOT approval of the new ChatGPT-painted images,
which are not present in the repo until intake. Uses only actual committed PNGs.
"""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"assets/sprites/rivers/strasbourg-ill-batch-002"
OUT=ROOT/"reports/strasbourg-ill-connection-review-003"
OUT.mkdir(parents=True,exist_ok=True)
old=json.loads((DATA/"manifest.json").read_text())
base=Image.open(ROOT/"base/base_3600.jpg").convert("RGBA")
city=Image.open(ROOT/"sprites/Strasbourg.png").convert("RGBA")
cx,cy,cw,ch=old["city_box"]
city.thumbnail((cw,ch),Image.Resampling.LANCZOS)
assert city.size==(cw,ch)
river=Image.new("RGBA",base.size,(0,0,0,0))
port_diagnostics=[]
for n,rec in enumerate(old["connectors"],1):
    png=Image.open(DATA/rec["file"]).convert("RGBA")
    x,y=rec["x"],rec["y"]
    river.alpha_composite(png,(x,y))
    port=rec["city_water_port"]
    # Find distance to the opposite free endpoint; this is NOT connected
    # unless the next mapped river sprite covers the same water pixels.
    p=np.asarray(png.getchannel("A"))
    sample=p[max(0,port[1]-y-3):min(p.shape[0],port[1]-y+4),
             max(0,port[0]-x-3):min(p.shape[1],port[0]-x+4)]
    port_diagnostics.append({
       "name":rec["id"],"file":rec["file"],"map_xy":[x,y],
       "water_port_xy":port,"city_port_alpha_confirmed":bool(np.any(sample>=200)),
       "outer_endpoint_xy":rec["endpoint_start"] if "upstream" in rec["id"] else rec["endpoint_end"],
       "status":"outward endpoint UNCONNECTED: no next sprite registered in this review",
       "course_qa":"modern OSM candidate" if "upstream" in rec["id"] or "downstream" in rec["id"] else "historic canal course not verified"
    })
assembled=Image.alpha_composite(base,river)
assembled.alpha_composite(city,(cx,cy))
# Preserve the 3600x4800 canvas; overlay annotations only into a separate QA image.
qa=assembled.copy().convert("RGB")
d=ImageDraw.Draw(qa)
styles=[(224,114,36),(216,77,51),(82,120,212),(157,71,169)]
for index,rec in enumerate(port_diagnostics):
    x,y=rec["outer_endpoint_xy"]; x,y=int(round(x)),int(round(y))
    color=styles[index]
    r=7
    d.ellipse((x-r,y-r,x+r,y+r),fill=(255,246,211),outline=color,width=3)
    px,py=rec["water_port_xy"]
    d.ellipse((px-3,py-3,px+3,py+3),outline=(44,137,76),width=2)
    d.line([(px,py),(x,y)],fill=color,width=1)
    rec["unconnected_endpoint_marked"]=True
# Mark the missing watercourse to the closest relevant already generated
# connector? DO NOT draw a false connection: leave open endpoints visible.
box=(890,2390,1210,2740)
scale=3
qa.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.LANCZOS).save(OUT/"strasbourg-annotated-endpoints.jpg",quality=94)
assembled.crop(box).convert("RGB").resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.LANCZOS).save(OUT/"strasbourg-assembled-map.jpg",quality=94)
assembled.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(OUT/"full-map-review.jpg",quality=90)
report={
  "origin_canvas":"base/base_3600.jpg",
  "city_asset":"sprites/Strasbourg.png",
  "connector_manifest":"assets/sprites/rivers/strasbourg-ill-batch-002/manifest.json",
  "layer_order":["base","separate river connectors","existing Strasbourg city","labels"],
  "connectors_registered":len(port_diagnostics),
  "png_position_qa":"PASS: committed connector global map coordinates used",
  "actual_city_port_qa":"PASS: committed four true port pixel checks" if all(p["city_port_alpha_confirmed"] for p in port_diagnostics) else "FAIL: at least one port suspect",
  "end_to_end_watercourse_qa":"NOT PASSED: four free ends have no adjoining painted corridor sprite registered",
  "new_chat_generated_artwork":"Not committed; this review does not claim those illustrations were placed",
  "strasbourg_ill_vs_rhine":"Separate waterways; do not join city canals to main Rhine arbitrarily",
  "river_branches_1618":"Canal stub courses remain historically provisional",
  "accept_for_print":False,
  "connector_details":port_diagnostics
}
(OUT/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
print("Strasbourg placement review:",len(port_diagnostics),"existing connectors; free ends intentionally visible")
if not all(x["city_port_alpha_confirmed"] for x in port_diagnostics):
    raise RuntimeError("One or more committed connector city-port checks failed")
