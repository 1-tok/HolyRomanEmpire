#!/usr/bin/env python3
"""Strasbourg Ill extension proof: four independent connected painted sprites.

This is a geographic/visual candidate, NOT historical approval. City ports are
read unchanged from 002. The main through-course continues south and north;
the two short southern/eastern canals reconnect to the continuous painted
river network instead of terminating as unconnected blue stubs. Endpoint
courses outside the city are design candidates because a period digitization
of the exact Ill arms has not been committed.
"""
import json, hashlib, math
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, label
from PIL import Image,ImageDraw,ImageChops

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"assets/sprites/rivers/strasbourg-ill-batch-002"
OUT=ROOT/"assets/sprites/rivers/strasbourg-ill-extensions-003"
QA=ROOT/"reports/strasbourg-ill-extensions-003"
BASE=ROOT/"base/base_3600.jpg"
CITY=ROOT/"sprites/Strasbourg.png"
W,H=3600,4800
ROI=(900,2360,1190,2790)
OX,OY,EX,EY=ROI
CW,CH=EX-OX,EY-OY

def smooth_path(points, samples_per_segment=24):
    out=[]
    for n in range(len(points)-1):
        p0=np.array(points[max(0,n-1)],float)
        p1=np.array(points[n],float)
        p2=np.array(points[n+1],float)
        p3=np.array(points[min(len(points)-1,n+2)],float)
        for k in range(samples_per_segment):
            t=k/samples_per_segment
            # Catmull Rom spline, and clamp tangent overshoots back inside ROI.
            p=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+
                  (-p0+3*p1-3*p2+p3)*t*t*t)
            out.append((float(p[0]),float(p[1])))
    out.append(tuple(points[-1]))
    return out

def drawpath(mask,pts,width):
    d=ImageDraw.Draw(mask)
    p=[(int(round(x-OX)),int(round(y-OY))) for x,y in smooth_path(pts)]
    d.line(p,fill=255,width=width,joint="curve")
    r=max(2,width//2)
    for x,y in p[::10]+[p[-1]]:
        d.ellipse((x-r,y-r,x+r,y+r),fill=255)

def pigment(mask,seed):
    core=np.asarray(mask)>0
    dist=distance_transform_edt(~core)
    h,w=core.shape
    yy,xx=np.indices((h,w),dtype=np.float32)
    gx=xx+OX;gy=yy+OY
    bank=(dist<=7)&~core
    a=np.zeros((h,w,4),dtype=np.uint8)
    grain=np.sin(gx*.29+gy*.18)*4+np.sin(gy*.59-gx*.23)*3
    # Water tint is identical across sprites at same global pixel positions;
    # that prevents a fresh discontinuity at branch crossings.
    for c,b in enumerate((72,123,148)):
        a[:,:,c]=np.where(core,np.clip(b+grain,0,255),a[:,:,c])
    a[:,:,3]=np.where(core,245,a[:,:,3])
    for c,b in enumerate((141,149,102)):
        a[:,:,c]=np.where(bank,np.clip(b+grain*1.3,0,255),a[:,:,c])
    a[:,:,3]=np.where(bank,np.clip((8-dist)*23,0,174),a[:,:,3])
    return Image.fromarray(a,"RGBA"), core

def main():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    origin=json.loads((SRC/"manifest.json").read_text())
    ports={rec["id"]:tuple(map(int,rec["city_water_port"])) for rec in origin["connectors"]}
    required={"ill-upstream-entry","ill-downstream-exit","ill-canal-branch-a","ill-canal-branch-b"}
    assert set(ports)==required
    # Direction convention: river flows from south of Strasbourg to north.
    # No guessed crossing of the main Rhine east of the city.
    up=ports["ill-upstream-entry"]
    down=ports["ill-downstream-exit"]
    ca=ports["ill-canal-branch-a"]
    cb=ports["ill-canal-branch-b"]
    paths=[
      ("ill-south-main-extension",
       [(up[0],up[1]),(1017,2630),(1000,2660),(985,2697),(968,2738),(955,2772)],12,
       "Ill south continuation; outside-city meanders provisional"),
      ("ill-north-main-extension",
       [(down[0],down[1]),(1090,2532),(1099,2505),(1080,2470),(1067,2430),(1082,2375)],12,
       "Ill north continuation; outside-city meanders provisional"),
      ("ill-south-canal-return",
       [(ca[0],ca[1]),(1076,2631),(1063,2651),(1032,2659),(1000,2660)],5,
       "Canal arm candidate joining southern Ill; historical course unverified"),
      ("ill-east-canal-return",
       [(cb[0],cb[1]),(1113,2585),(1123,2554),(1115,2525),(1099,2505)],5,
       "Canal arm candidate joining northern Ill; historical course unverified")
    ]
    # The two smaller canal banks must not obscure the main river water.
    # Compositing order: main courses then minor branches.
    allwater=np.zeros((CH,CW),bool)
    composite=Image.new("RGBA",(W,H),(0,0,0,0))
    entries=[]
    for i,(name,pts,width,provenance) in enumerate(paths):
        if any(not(OX+15<=x<EX-10 and OY+10<=y<EY-10) for x,y in pts):
            raise RuntimeError("Out of bounding ROI: "+name)
        mask=Image.new("L",(CW,CH),0);drawpath(mask,pts,width)
        img,water=pigment(mask,1618+i)
        # Raster aliases remain precisely tied to fixed master canvas grid.
        bbox=img.getbbox()
        if bbox is None:raise RuntimeError("Empty "+name)
        cropped=img.crop(bbox)
        file=name+".png";dest=OUT/file;cropped.save(dest,optimize=True)
        test=Image.open(dest).convert("RGBA")
        if any(c.getbbox() for c in ImageChops.difference(test,cropped).split()):
            raise RuntimeError("PNG decode mismatch: "+file)
        gx,gy=OX+bbox[0],OY+bbox[1]
        composite.alpha_composite(test,(gx,gy))
        allwater|=water
        entries.append({"id":name,"file":file,"x":gx,"y":gy,"width":test.width,"height":test.height,
                        "begin":[int(v) for v in pts[0]],"end":[int(v) for v in pts[-1]],
                        "source":provenance,"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                        "geographic_status":"candidate; must compare with historical map before print"})
    # Exact on-disk raster rebuild: no edge stretching or resampling.
    rebuilt=Image.new("RGBA",(W,H),(0,0,0,0))
    for item in entries:
        rebuilt.alpha_composite(Image.open(OUT/item["file"]).convert("RGBA"),(item["x"],item["y"]))
    if any(b.getbbox() for b in ImageChops.difference(rebuilt,composite).split()):
        raise RuntimeError("PNG reassembly mismatch")
    # The 4 paths must be a SINGLE connected water mask.
    struct=np.ones((3,3),dtype=int)
    connected,ncomp=label(allwater,structure=struct)
    if ncomp!=1:raise RuntimeError("Unjoined river water components: "+str(ncomp))
    city=Image.open(CITY).convert("RGBA")
    cx,cy,w,h=origin["city_box"]
    city.thumbnail((w,h),Image.Resampling.LANCZOS)
    cityrgb=np.asarray(city,dtype=np.int16)
    painted_city_water=(cityrgb[:,:,3]>=150)&(cityrgb[:,:,2]>cityrgb[:,:,0]+12)&(cityrgb[:,:,1]>cityrgb[:,:,0]+6)
    for name,port in ports.items():
        x,y=port
        if not painted_city_water[y-cy,x-cx]:raise RuntimeError("Unchanged city water port missing "+name)
        px,py=x-OX,y-OY
        if not allwater[py,px]:raise RuntimeError("New river misses city port "+name)
    base=Image.open(BASE).convert("RGBA")
    comp=Image.alpha_composite(base,rebuilt)
    comp.alpha_composite(city,(cx,cy))
    region=(910,2370,1190,2790)
    comp.crop(region).resize((840,1260),Image.Resampling.LANCZOS).convert("RGB").save(QA/"strasbourg-extended-preview.jpg",quality=94)
    comp.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-map-preview.jpg",quality=90)
    # Diagnostic: mark 4 verified city ports, 2 confluences and remaining outward ends.
    detail=comp.crop(region).convert("RGB")
    d=ImageDraw.Draw(detail)
    for n,(name,(x,y)) in enumerate(ports.items(),1):
        x-=region[0];y-=region[1]
        d.ellipse((x-5,y-5,x+5,y+5),outline=(25,160,74),width=3)
        d.text((x+7,y-13),str(n),fill=(24,60,28),stroke_fill=(255,246,217),stroke_width=2)
    for x,y in ((1000,2660),(1099,2505)):
        x-=region[0];y-=region[1]
        d.ellipse((x-5,y-5,x+5,y+5),outline=(207,108,25),width=3)
    for x,y in ((955,2772),(1082,2375)):
        x-=region[0];y-=region[1]
        d.ellipse((x-7,y-7,x+7,y+7),outline=(182,41,41),width=3)
    detail.resize((840,1260),Image.Resampling.LANCZOS).save(QA/"strasbourg-extended-annotated.jpg",quality=94)
    # Compare original, to avoid mistaking a successful port test for real visual quality.
    old=Image.new("RGBA",(W,H),(0,0,0,0))
    for rec in origin["connectors"]:
        old.alpha_composite(Image.open(SRC/rec["file"]).convert("RGBA"),(rec["x"],rec["y"]))
    previous=Image.alpha_composite(base,old);previous.alpha_composite(city,(cx,cy))
    before=previous.crop(region).resize((560,840),Image.Resampling.LANCZOS).convert("RGB")
    after=comp.crop(region).resize((560,840),Image.Resampling.LANCZOS).convert("RGB")
    compare=Image.new("RGB",(1120,840));compare.paste(before,(0,0));compare.paste(after,(560,0))
    ImageDraw.Draw(compare).text((10,12),"BEFORE - SHORT STUBS",fill=(20,30,24),stroke_width=2,stroke_fill=(249,246,227))
    ImageDraw.Draw(compare).text((570,12),"AFTER - CONTINUOUS CANDIDATE",fill=(20,30,24),stroke_width=2,stroke_fill=(249,246,227))
    compare.save(QA/"before-after.jpg",quality=94)
    audit={"batch":"strasbourg-ill-extensions-003",
           "status":"MAP-SCALE PROVISIONAL - course requires historical review",
           "not_a_new_rhine_connection":True,
           "city_ports_preserved":ports,
           "source":"Existing city painted water and earlier OSM-derived Ill anchors",
           "exterior_courses":"Conceptual paths between fixed ports and exterior points; NOT historically verified AD 1618",
           "canal_routes":"Two canal return candidates join a single continuous river mask, but exact historic routing unverified",
           "water_connectivity":"PASS: exactly one 8-connected painted water component",
           "city_port_overlap":"PASS: 4 of 4 committed city water ports touch new water",
           "rgba_reassembly":"PASS: exact RGBA after reading independent PNGs",
           "original_city_unmodified":True,
           "composite_layer_order":["HRE base","independent river PNGs","Strasbourg city","labels"],
           "unresolved":"Two north/south outward endpoints await corridor extension; ensure no false joins with Rhine",
           "approval":"Review only, not final or print-ready",
           "connectors":entries}
    (OUT/"manifest.json").write_text(json.dumps(audit,indent=2)+"\n")
    (QA/"qa.json").write_text(json.dumps(audit,indent=2)+"\n")
    print("PASS: 4 independent painted extension PNGs, single connected water mask, 4 preserved city ports",flush=True)
if __name__=="__main__":main()
