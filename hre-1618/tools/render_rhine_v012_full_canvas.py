#!/usr/bin/env python3
"""Rhine v012: repository-native geographic Rhine full-canvas *review*.
Reuses actual existing HRE map and approved source assets, not unattached chat PNGs.
Renders one coherent fixed-course river, then cuts it into exact independent sprites.
Important: current Natural Earth 10m is NOT proven 1618 river geometry.
"""
from pathlib import Path
import sys, json, hashlib, math, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
R=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(R/"tools"))
from build_rhine_batch001 import river_lines, px, SOURCE
W,H=3600,4800; ROI=(650,1350,1660,3220)
OUT=R/"maps/canvas"; QA=R/"reports/rhine-v012-full-canvas"
SPR=R/"assets/sprites/rivers/rhine-v012"
for p in (OUT,QA,SPR): p.mkdir(parents=True,exist_ok=True)
base=Image.open(R/"base/base_3600.jpg").convert("RGBA")
assert base.size==(W,H)
x0,y0,x1,y1=ROI; w=x1-x0; h=y1-y0
payload=urllib.request.urlopen(SOURCE,timeout=90).read()
paths=river_lines(payload)
water=Image.new("L",(w,h),0); d=ImageDraw.Draw(water); nseg=0
for line in paths:
    for (a,b),(c,e) in zip(line,line[1:]):
        if min(a,c)>51.08 or max(a,c)<47.35:continue
        if min(b,e)>9.00 or max(b,e)<6.75:continue
        p=px(a,b); q=px(c,e)
        if max(p[0],q[0])<x0 or min(p[0],q[0])>=x1 or max(p[1],q[1])<y0 or min(p[1],q[1])>=y1:continue
        d.line((p[0]-x0,p[1]-y0,q[0]-x0,q[1]-y0),fill=255,width=12)
        nseg+=1
assert nseg>40, f"River extraction too small {nseg}"
core=np.asarray(water)>0
# Wetland scenery follows the *existing river geometry*, not invented painted bends.
banks=np.array(water.filter(ImageFilter.MaxFilter(41)),dtype=np.uint8)>0
edge=np.array(water.filter(ImageFilter.MaxFilter(85)),dtype=np.uint8)>0
YY,XX=np.indices((h,w),dtype=np.int32)
rng=np.random.default_rng(1618)
noise=rng.integers(-12,13,(h,w),dtype=np.int16)
t=(np.sin((XX+2*YY)*.31)+np.sin((YY-XX)*.15))*4
im=np.zeros((h,w,4),dtype=np.uint8)
for ch,col in enumerate((137,154,103)):
    im[:,:,ch]=np.where(edge,np.clip(col+noise+t,0,255),0)
im[:,:,3]=np.where(edge,80,0)
for ch,col in enumerate((115,137,88)):
    im[:,:,ch]=np.where(banks,np.clip(col+noise+t,0,255),im[:,:,ch])
im[:,:,3]=np.where(banks,145,im[:,:,3])
for ch,col in enumerate((70,126,151)):
    im[:,:,ch]=np.where(core,np.clip(col+noise+t,0,255),im[:,:,ch])
im[:,:,3]=np.where(core,248,im[:,:,3])
# Fine canopy and reeds: deterministic texture only within geographic riparian buffers.
scenery=Image.fromarray(im,"RGBA")
painter=ImageDraw.Draw(scenery,"RGBA")
for i in range(9500):
    xx=int(rng.integers(3,w-3));yy=int(rng.integers(3,h-3))
    if not banks[yy,xx] or core[yy,xx]:continue
    radius=int(rng.choice([1,2,2,3,4]))
    painter.ellipse((xx-radius,yy-radius,xx+radius,yy+radius),
                    fill=(48+int(rng.integers(0,40)),82+int(rng.integers(0,38)),50+int(rng.integers(0,24)),int(rng.integers(75,175))))
master=Image.new("RGBA",(W,H),(0,0,0,0))
master.paste(scenery,(x0,y0))
# Exact non-overlapping 140px Y intervals, no separately painted kinks/ghosting.
rebuilt=Image.new("RGBA",(W,H),(0,0,0,0))
pieces=[]
for i,ya in enumerate(range(y0,y1,140),1):
    yb=min(y1,ya+140); strip=master.crop((0,ya,W,yb)); bb=strip.getbbox()
    if bb is None:continue
    piece=strip.crop(bb); fn=f"rhine-v012-{i:02d}.png"
    piece.save(SPR/fn,optimize=True)
    at=(bb[0],ya+bb[1]);rebuilt.paste(Image.open(SPR/fn).convert("RGBA"),at)
    pieces.append(dict(file=fn,x=at[0],y=at[1],width=piece.width,height=piece.height,source_y=[ya,yb],sha256=hashlib.sha256((SPR/fn).read_bytes()).hexdigest()))
assert not any(ch.getbbox() for ch in ImageChops.difference(master,rebuilt).split()), "FAIL: non-pixel-exact reach join"
# Current real geographic base; city art above landscape, no duplicate opaque paintings.
composite=Image.alpha_composite(base,rebuilt)
existing=json.loads((R/"placements/rhine-batch-001.json").read_text())
placed=[]
for c in existing["entries"]:
    f=R/c["asset"]
    if not f.exists():continue
    sprite=Image.open(f).convert("RGBA")
    sprite.thumbnail((105,105),Image.Resampling.LANCZOS)
    xx=round(c["x"])-sprite.width//2;yy=round(c["y"])-sprite.height//2
    composite.alpha_composite(sprite,(xx,yy))
    placed.append(dict(site=c["site"],asset=c["asset"],x=xx,y=yy))
# Geographic markers identify cities lacking approved unique sprite art; they are NOT town paintings.
towns=[
("Cologne",50.94222,6.95778),("Bonn",50.73528,7.10222),("Andernach",50.439,7.401),
("Koblenz",50.3568,7.59366),("Boppard",50.231,7.589),("Bingen",49.966,7.899),
("Oppenheim",49.851,8.354),("Germersheim",49.222,8.366),
("Gambsheim",48.692,7.885),("La Wantzenau",48.657,7.825),
("Rhinau",48.318,7.707),("Marckolsheim",48.165,7.547),
("Breisach",48.033,7.582),("Neuenburg",47.814,7.561)]
draw=ImageDraw.Draw(composite)
for name,lat,lon in towns:
    xx,yy=px(lat,lon);xx=int(round(xx));yy=int(round(yy))
    if xx<0 or yy<0 or xx>=W or yy>=H:continue
    draw.ellipse((xx-5,yy-5,xx+5,yy+5),fill=(237,222,173,255),outline=(73,50,26,255),width=2)
    draw.text((xx+9,yy-8),name,fill=(46,37,28,255),stroke_width=2,stroke_fill=(244,235,204,255))
# Save full-res result in repo plus context zoom and QA.
composite.convert("RGB").save(OUT/"rhine-v012-geographic-full-map-review.jpg",quality=91)
composite.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-map-1200.jpg",quality=92)
crop=(700,1500,1530,3150)
composite.crop(crop).convert("RGB").save(QA/"rhine-cologne-basel-corridor.jpg",quality=93)
master.save(OUT/"rhine-v012-geographic-overlay.png",optimize=True)
qa={"status":"GEOGRAPHIC CANVAS REVIEW ONLY", "canvas_size":[W,H],
    "base":"base/base_3600.jpg","geometry":"Natural Earth 10m river polyline, same geometry/projection as HRE base",
    "historic_1618_course_certified":False,"river_segments":nseg,"scenery_segments":len(pieces),
    "exact_sprite_seams":"PASS - one canonical georeferenced painting sliced and reassembled pixel-exactly",
    "existing_city_sprites":placed,"additional_city_markers":[x[0] for x in towns],
    "style_note":"Procedural painterly wetland scenery derived from fixed Rhine course; newer standalone chat-generated paintings are not embedded because their binaries are not committed to this branch.",
    "strasbourg":"City on Ill; main Rhine follows geometry separately; do not infer a fabricated connecting channel",
    "limitations":["Natural Earth 10m is modern generalized hydrography","minor-city sprite imagery still to be produced","1618 floodplain banks, islands and historical city walls not certified"],
    "print_approval":False,"pieces":pieces}
(SPR/"manifest.json").write_text(json.dumps(qa,indent=2)+"\n")
(QA/"qa.json").write_text(json.dumps(qa,indent=2)+"\n")
print("Generated real 3600x4800 map composite; segments",nseg,"pieces",len(pieces),flush=True)
