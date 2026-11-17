#!/usr/bin/env python3
"""Strasbourg Ill city-connector batch, HRE 1618.

Separate georeferenced painted PNG sprites: upstream Ill, downstream Ill and
two small canals. Uses actual Strasbourg.png RGBA pixels and mapped Natural
Earth Ill centerline (not the main Rhine). Endpoints are fitted to painted
water at the city's sprite perimeter; buildings never receive river overlay.

Image sprites are always below city sprites; visual and historic status is
provisional until human map-scale signoff.
"""
import csv, hashlib, io, json, math, re, struct, sys, urllib.request, urllib.error, urllib.parse, zipfile
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_rhine_batch001 import px
OUT=ROOT/"assets"/"sprites"/"rivers"/"strasbourg-ill-batch-001"
QA=ROOT/"reports"/"strasbourg-ill-batch-001"
W,H=3600,4800
SOURCE="https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip"
CITY=ROOT/"sprites"/"Strasbourg.png"
PLACE=ROOT/"placements"/"rhine-batch-001.json"
CITY_WIDTH=105
ROI=(875,2380,1160,2730)
SEED=1618

def read_ill():
    """Retrieve observed Ill waterway way geometry from the OSM map API.

    Overpass public instances are often congested, so query the official
    OSM map endpoint over small bounding boxes, then filter named waterways.
    No hand-drawn substitute for missing geographic data is allowed.
    """
    import xml.etree.ElementTree as ET
    # Tiny 0.007° squares evade OSM's 50,000-node cap in central Strasbourg.
    bboxes=[(lon-.0035,lat-.0035,lon+.0035,lat+.0035)
            for lat in (48.535,48.553,48.575,48.597,48.619)
            for lon in (7.731,7.750,7.769)]
    ways=[]
    failures=[]
    other_waterways={}
    for left,bottom,right,top in bboxes:
        url="https://api.openstreetmap.org/api/0.6/map?bbox="+",".join(str(v) for v in (left,bottom,right,top))
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"HolyRomanEmpire1618-MapResearch/1.0"})
            with urllib.request.urlopen(req,timeout=45) as res:
                xml=res.read(45_000_000)
            if len(xml)>=45_000_000:raise RuntimeError("OSM map bbox exceeded size limit")
            tree=ET.fromstring(xml)
            nodes={n.get("id"):(float(n.get("lat")),float(n.get("lon")))
                   for n in tree.findall("node")}
            for way in tree.findall("way"):
                tags={t.get("k"):t.get("v") for t in way.findall("tag")}
                if tags.get("waterway") not in ("river","stream","canal"):
                    continue
                other_waterways[tags.get("name","unnamed")]=other_waterways.get(tags.get("name","unnamed"),0)+1
                if "ill" not in (tags.get("name","")+" "+tags.get("name:fr","")).lower():
                    continue
                line=[nodes[n.get("ref")] for n in way.findall("nd") if n.get("ref") in nodes]
                if len(line)>1:ways.append(line)
        except urllib.error.HTTPError as e:
            failures.append(str(e.code)+": "+e.read(900).decode("utf-8","replace"))
        except Exception as e:
            failures.append(repr(e))
    if not ways:
        raise RuntimeError("Official OSM map API lacks matched Ill ways. Found names: "+str(other_waterways)+"; errors: "+str(failures))
    print("Mapped Ill waterways:",len(ways),"bbox errors:",len(failures),flush=True)
    return ways

def city_and_ports():
    cfg=json.loads(PLACE.read_text())
    entry=next(x for x in cfg["entries"] if x["site"]=="Strasbourg")
    im=Image.open(CITY).convert("RGBA")
    im.thumbnail((CITY_WIDTH,CITY_WIDTH),Image.Resampling.LANCZOS)
    cx=round(entry["x"]);cy=round(entry["y"])
    x=cx-im.width//2;y=cy-im.height//2
    rgb=np.asarray(im,dtype=np.int16)
    a=rgb[:,:,3]
    # Blue-green river paint is materially bluer than nearby roof/stone pixels.
    water=(a>=150)&(rgb[:,:,2]>rgb[:,:,0]+12)&(rgb[:,:,1]>rgb[:,:,0]+6)
    # Scan a 9px edge band; every selected endpoint must be water in the
    # actual committed Strasbourg city PNG, not a guessed attachment.
    h,w=water.shape; candidates=[]
    for yy,xx in zip(*np.where(water)):
        edge=min(xx,yy,w-1-xx,h-1-yy)
        if edge<=9:
            candidates.append({"x":int(x+xx),"y":int(y+yy),"local_x":int(xx),"local_y":int(yy),
                               "edge_distance":int(edge),"blue":int(rgb[yy,xx,2])})
    if len(candidates)<4:
        raise RuntimeError(f"Only {len(candidates)} blue water pixels at actual city boundary")
    def pick(side):
        if side=="north":rank=lambda p:(p["local_y"],abs(p["local_x"]-w*.66))
        elif side=="south":rank=lambda p:(h-1-p["local_y"],abs(p["local_x"]-w*.40))
        elif side=="west":rank=lambda p:(p["local_x"],abs(p["local_y"]-h*.65))
        else:rank=lambda p:(w-1-p["local_x"],abs(p["local_y"]-h*.40))
        return min(candidates,key=rank)
    ports={side:pick(side) for side in ("north","south","west","east")}
    return im,x,y,water,ports

def nearest_on_ill(lines,anchor):
    best=None
    for line in lines:
        for la,lo in line:
            if not (47.75<=la<=49.1 and 7.1<=lo<=8.4):continue
            p=px(la,lo)
            d=(p[0]-anchor[0])**2+(p[1]-anchor[1])**2
            if best is None or d<best[0]:best=(d,p)
    return None if best is None else best[1]

def line_mask(points,width,roi=ROI):
    x0,y0,x1,y1=roi
    mask=Image.new("L",(x1-x0,y1-y0),0)
    draw=ImageDraw.Draw(mask)
    draw.line([(round(x-x0),round(y-y0)) for x,y in points],fill=255,width=width,joint="curve")
    r=width//2
    for x,y in points:
        x=round(x-x0);y=round(y-y0)
        draw.ellipse((x-r,y-r,x+r,y+r),fill=255)
    return mask

def painted(mask,seed):
    core=np.asarray(mask,dtype=np.uint8)>0
    h,w=core.shape
    dist=distance_transform_edt(~core)
    inner=distance_transform_edt(core)
    rng=np.random.default_rng(seed)
    fine=gaussian_filter(rng.standard_normal((h,w)).astype(np.float32),1.3)
    coarse=gaussian_filter(rng.standard_normal((h,w)).astype(np.float32),7)
    coarse=coarse/max(float(coarse.std()),.001)
    n=np.clip(coarse*.55+fine*2.2,-3,3)
    bank=(dist<=8)&(~core)
    rgba=np.zeros((h,w,4),dtype=np.uint8)
    wash=np.clip(n*9,-28,28)
    for c,b in enumerate((147,154,105)):
        rgba[:,:,c]=np.where(bank,np.clip(b+wash,0,255),rgba[:,:,c])
    rgba[:,:,3]=np.where(bank,np.clip((9-dist)*18,0,175),rgba[:,:,3])
    shimmer=np.clip(coarse*10+fine*38,-35,35)
    for c,b in enumerate((65,125,151)):
        rgba[:,:,c]=np.where(core,np.clip(b+shimmer,0,255),rgba[:,:,c])
    rgba[:,:,3]=np.where(core,243,rgba[:,:,3])
    edge=core&(inner<=2)
    rgba[:,:,:3]=np.where(edge[:,:,None],np.clip(rgba[:,:,:3].astype(np.int16)-14,0,255),rgba[:,:,:3])
    return Image.fromarray(rgba,"RGBA")

def build():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    lines=read_ill()
    im,city_x,city_y,water,ports=city_and_ports()
    # The city is north-up at these coordinates. Natural Earth is used for
    # the true Ill corridor; each short endpoint extension meets a WATER
    # pixel of the existing city painting.
    city_c=(city_x+im.width/2,city_y+im.height/2)
    geo=nearest_on_ill(lines,city_c)
    if geo is None or math.dist(geo,city_c)>90:
        raise RuntimeError("Mapped Ill is too distant from Strasbourg city center")
    # Identify geographically plausible outer points to the south/southwest
    # and north/northeast by searching NE10m river vertices.
    pts=[]
    for line in lines:
        for la,lo in line:
            if 48.32<la<48.88 and 7.3<lo<8.0:
                p=px(la,lo)
                if math.dist(p,city_c)<250:pts.append(p)
    if len(pts)<8:raise RuntimeError("Insufficient geographic Ill vertices near Strasbourg")
    # Upstream Ill comes FROM the south; downstream heads NORTH.
    upstream=max((p for p in pts if p[1]>city_c[1]+10),key=lambda p:p[1],default=None)
    downstream=min((p for p in pts if p[1]<city_c[1]-10),key=lambda p:p[1],default=None)
    if upstream is None or downstream is None:raise RuntimeError("Ill north/south bounds not resolved")
    # Port at exact visible blue water of committed city; connector touches
    # city sprite at the port, and is subsequently hidden by city overlay.
    def closest(choices,point):
        return min(choices,key=lambda p:(p["x"]-point[0])**2+(p["y"]-point[1])**2)
    # Restrict to corresponding half of city; use real blue port candidates.
    a=np.asarray(im,dtype=np.int16);alpha=a[:,:,3]
    ww=(alpha>=150)&(a[:,:,2]>a[:,:,0]+12)&(a[:,:,1]>a[:,:,0]+6)
    h,w=ww.shape
    edges=[(city_x+xx,city_y+yy) for yy,xx in zip(*np.where(ww)) if min(xx,yy,w-1-xx,h-1-yy)<=8]
    up_port=min((p for p in edges if p[1]>=city_c[1]),key=lambda p:math.dist(p,upstream),default=None)
    down_port=min((p for p in edges if p[1]<city_c[1]),key=lambda p:math.dist(p,downstream),default=None)
    if not up_port or not down_port:raise RuntimeError("City Ill water ports not found on both sides")
    # Create two separate mainline segments. The bank connectors blend INTO
    # the existing city edge, not on top of its building pixels.
    specs=[
      ("ill-upstream-entry",upstream,up_port,12,upstream,"NE10m Ill upstream"),
      ("ill-downstream-exit",down_port,downstream,12,downstream,"NE10m Ill downstream")
    ]
    # Use TWO ADDITIONAL DISTINCT painted-water ports. The existing city
    # artwork has no reliable independent west/east river outlets, so do not
    # invent those locations. Place short stubs at real observed water edges,
    # and flag their historical course provisional pending map QA.
    def squared(p,q):
        return (p[0]-q[0])**2+(p[1]-q[1])**2
    unused=[p for p in set(edges) if squared(p,up_port)>16 and squared(p,down_port)>16]
    if len(unused)<2:raise RuntimeError("City art exposes fewer than four usable distinct water ports")
    canal1=max(unused,key=lambda p:min(squared(p,up_port),squared(p,down_port)))
    remaining=[p for p in unused if squared(p,canal1)>25]
    if not remaining:raise RuntimeError("Fourth distinct canal port not available in existing art")
    canal2=max(remaining,key=lambda p:min(squared(p,up_port),squared(p,down_port),squared(p,canal1)))
    def out(p,length):
        vx=p[0]-city_c[0];vy=p[1]-city_c[1]
        magnitude=max(1.0,math.hypot(vx,vy))
        return (p[0]+vx/magnitude*length,p[1]+vy/magnitude*length)
    specs += [
      ("ill-canal-branch-a",canal1,out(canal1,24),5,None,"verified city water port; branch course provisional"),
      ("ill-canal-branch-b",canal2,out(canal2,25),5,None,"verified city water port; branch course provisional"),
    ]
    # All components painted in a shared coordinate system; mask city-overlap
    # pixels at presentation, never cover roofs/walls.
    full=Image.new("RGBA",(W,H),(0,0,0,0))
    entries=[]
    for i,(name,p,q,width,reference,source) in enumerate(specs):
        if not (ROI[0]<=p[0]<ROI[2] and ROI[1]<=p[1]<ROI[3] and
                ROI[0]<=q[0]<ROI[2] and ROI[1]<=q[1]<ROI[3]):
            raise RuntimeError("Connector "+name+" extends beyond geographic QA ROI")
        # Short smooth interpolation from the mapped approach to exact city
        # water port, retaining the actual endpoints.
        ctrl=((p[0]+q[0])/2,(p[1]+q[1])/2)
        path=[((1-t)**2*p[0]+2*(1-t)*t*ctrl[0]+t*t*q[0],
               (1-t)**2*p[1]+2*(1-t)*t*ctrl[1]+t*t*q[1])
               for t in np.linspace(0,1,60)]
        mask=line_mask(path,width)
        tile=painted(mask,SEED+i)
        box=tile.getbbox()
        if not box:raise RuntimeError("Empty "+name)
        crop=tile.crop(box)
        # Each independent PNG is tightly cropped but carries a global
        # placement origin; exact reconstructed pixels are checked below.
        ox=ROI[0]+box[0];oy=ROI[1]+box[1]
        file=name+".png";target=OUT/file
        crop.save(target,optimize=True)
        decoded=Image.open(target).convert("RGBA")
        if any(b.getbbox() for b in ImageChops.difference(decoded,crop).split()):
            raise RuntimeError("PNG decode failed "+name)
        full.alpha_composite(decoded,(ox,oy))
        entries.append({"id":name,"file":file,"x":ox,"y":oy,"width":decoded.width,"height":decoded.height,
                        "endpoint_start":[round(p[0],2),round(p[1],2)],
                        "endpoint_end":[round(q[0],2),round(q[1],2)],
                        "city_water_port":list(map(int,up_port if i==0 else down_port if i==1 else canal1 if i==2 else canal2)),
                        "source":source,"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                        "validation":"decoded PNG exact; junction endpoint pinned to city-water mask"})
    # Test PNG reassembly at the committed geographical origins.
    reconstructed=Image.new("RGBA",(W,H),(0,0,0,0))
    for e in entries:
        png=Image.open(OUT/e["file"]).convert("RGBA")
        reconstructed.alpha_composite(png,(e["x"],e["y"]))
    if any(b.getbbox() for b in ImageChops.difference(full,reconstructed).split()):
        raise RuntimeError("Independent connector reconstruction mismatch")
    base=Image.open(ROOT/"base"/"base_3600.jpg").convert("RGBA")
    mapview=Image.alpha_composite(base,reconstructed)
    mapview.alpha_composite(im,(city_x,city_y))
    # Strict evidence: each city connector port is painted blue in actual PNG
    # AND touched by the generated connector water footprint.
    for e in entries:
        port=e["city_water_port"]; ix=port[0]-city_x;iy=port[1]-city_y
        if not (0<=ix<im.width and 0<=iy<im.height and ww[iy,ix]):
            raise RuntimeError("City port not valid blue water pixel: "+e["id"])
        # bank underlay may differ; accept a 5px overlap, not a distant gap
        a=np.asarray(reconstructed.crop((port[0]-5,port[1]-5,port[0]+6,port[1]+6)))[:,:,3]
        if not np.any(a>0):raise RuntimeError("Connector gap at "+e["id"])
    close=(905,2430,1145,2695)
    mapview.crop(close).resize((960,1060),Image.Resampling.LANCZOS).convert("RGB").save(QA/"strasbourg-junction-proof.jpg",quality=94)
    mapview.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"map-progress.jpg",quality=89)
    info={"batch":"Strasbourg separate Ill river connectors",
          "city_asset":"sprites/Strasbourg.png","city_box":[city_x,city_y,im.width,im.height],
          "mapped_mainline":"OpenStreetMap named Ill river ways; Rhine separate",
          "historic_note":"Canal stubs are provisional; not a 1618 mapped reconstruction",
          "layering":["original base","separate connector PNGs","existing Strasbourg sprite","labels"],
          "png_seam_qa":"PASS: exact RGBA reconstruction at manifest coordinates",
          "city_port_qa":"PASS: each connector ends within 5px of BLUE paint on real city sprite",
          "city_water_port_count":len(edges),"connectors":entries,
          "status":"PROVISIONAL pending historical cartography and visual print approval"}
    (OUT/"manifest.json").write_text(json.dumps(info,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+"\n")
    (QA/"qa.json").write_text(json.dumps(info,indent=2)+"\n")
    print("PASS Strasbourg connector batch",len(entries),"sprite PNGs, 4 city ports, geographic Ill",flush=True)
if __name__=="__main__":build()
