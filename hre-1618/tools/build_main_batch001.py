#!/usr/bin/env python3
"""Generate geographically anchored Main river-section PNG sprites in Actions.

All tiles are pixel-exact crops of one water raster in the HRE 1618 Lambert
Conformal Conic geographic frame. Cities are added above the river, never under.
NE10m geometry is a technical starting point, not historical 1618 certification.
"""
import csv, hashlib, io, json, os, struct, urllib.request, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"assets"/"sprites"/"rivers"/"main"
QA=ROOT/"reports"/"main-batch-001"
SOURCE="https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_rivers_lake_centerlines.zip"
W,H=3600,4800
TILE=240
# Reuse projection math without rerunning base construction.
import sys
sys.path.insert(0,str(ROOT/"tools"))
# Exact 3600 x 4800 base map forward projection reused from existing builder.
from build_rhine_batch001 import px

def selected_lines(data):
    z=zipfile.ZipFile(io.BytesIO(data))
    shp=z.read(next(k for k in z.namelist() if k.endswith(".shp")))
    dbf=z.read(next(k for k in z.namelist() if k.endswith(".dbf")))
    num=struct.unpack("<I",dbf[4:8])[0]
    header,step=struct.unpack("<HH",dbf[8:12])
    fields=[];o=32
    while dbf[o]!=13:
        fields.append((dbf[o:o+11].split(b"\0")[0].decode(),dbf[o+16]));o+=32
    names=[]
    for k in range(num):
        row=dbf[header+k*step:header+(k+1)*step]; offset=1; name=""
        for key,length in fields:
            if key.lower()=="name": name=row[offset:offset+length].decode("latin-1").strip("\0 ").lower()
            offset+=length
        names.append(name)
    items=[];counts={}
    pos=100;i=0
    while pos+8<=len(shp):
        n=struct.unpack(">i",shp[pos+4:pos+8])[0]*2
        rec=shp[pos+8:pos+8+n];pos+=8+n
        label=names[i] if i<len(names) else "";i+=1
        if label.strip() != "main": continue
        if struct.unpack("<i",rec[:4])[0] != 3:continue
        groups,points=struct.unpack("<ii",rec[36:44])
        starts=list(struct.unpack("<%di"%groups,rec[44:44+4*groups]))+[points]
        raw=struct.unpack("<%dd"%(2*points),rec[44+4*groups:44+4*groups+16*points])
        counts[label]=counts.get(label,0)+1
        for j in range(groups):
            coords=[(raw[k*2+1],raw[k*2]) for k in range(starts[j],starts[j+1])]
            # The cartographic corridor is Schweinfurt to Mainz, including the Main bends.
            if len(coords)>1 and any(49.55<la<50.45 and 7.9<lo<10.85 for la,lo in coords):
                items.append(coords)
    if not items:raise RuntimeError("No named Main geometry in Natural Earth 10m source")
    return items,counts

def build():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    data=urllib.request.urlopen(SOURCE,timeout=100).read()
    lines,labels=selected_lines(data)
    water=Image.new("RGBA",(W,H),(0,0,0,0));draw=ImageDraw.Draw(water)
    segments=0
    for line in lines:
        for (a,b),(c,d) in zip(line,line[1:]):
            if max(a,c)<49.55 or min(a,c)>50.45 or max(b,d)<7.9 or min(b,d)>10.85:continue
            p=px(a,b);q=px(c,d)
            for width,color in ((15,(63,111,143,220)),(9,(81,143,168,200)),(2,(154,189,187,100))):
                draw.line([p,q],fill=color,width=width)
            segments+=1
    if segments<15:raise RuntimeError("Too few Main river segments found; aborting")
    water.save(QA/"main-canonical-transparent.png")
    recon=Image.new("RGBA",(W,H),(0,0,0,0))
    tiles=[]
    for y0 in range(0,H,TILE):
        for x0 in range(0,W,TILE):
            x1=min(x0+TILE,W);y1=min(y0+TILE,H)
            crop=water.crop((x0,y0,x1,y1));bbox=crop.getbbox()
            if bbox is None:continue
            tight=crop.crop(bbox)
            if tight.width<1 or tight.height<1:continue
            x,y=x0+bbox[0],y0+bbox[1]
            name="main-{:02d}-{:02d}.png".format(y0//TILE,x0//TILE)
            tight.save(OUT/name,optimize=True)
            img=Image.open(OUT/name).convert("RGBA")
            if any(b.getbbox() for b in ImageChops.difference(img,tight).split()):
                raise RuntimeError("Decoded PNG mismatch "+name)
            recon.paste(img,(x,y))
            tiles.append({"file":name,"x":x,"y":y,"width":img.width,"height":img.height,
                          "sha256":hashlib.sha256((OUT/name).read_bytes()).hexdigest()})
    if not tiles:raise RuntimeError("No Main connector sprites")
    delta=ImageChops.difference(water,recon)
    if any(b.getbbox() for b in delta.split()):
        raise RuntimeError("Connector tile seam mismatch")
    base=Image.open(ROOT/"base"/"base_3600.jpg").convert("RGBA")
    if base.size!=(W,H):raise RuntimeError("Unexpected base dimensions")
    comp=Image.alpha_composite(base,recon)
    sites=[]
    with (ROOT/"river-sites.csv").open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["river"]!="Main" or not row["on_sheet"].startswith("yes"):continue
            site=row["site"]
            x=round(float(row["px_x"])/3);y=round(float(row["px_y"])/3)
            name=site.replace("ö","oe").replace("ü","ue").replace("ä","ae")
            variants=[ROOT/"sprites"/(site+".png"),ROOT/"sprites"/(name+".png")]
            asset=next((v for v in variants if v.exists()),None)
            status="anchor-only"
            if asset:
                sprite=Image.open(asset).convert("RGBA");sprite.thumbnail((105,105),Image.Resampling.LANCZOS)
                comp.alpha_composite(sprite,(x-sprite.width//2,y-sprite.height//2))
                status="placed-provisional"
            sites.append({"site":site,"x":x,"y":y,"asset":str(asset.relative_to(ROOT)) if asset else None,"status":status})
    comp.convert("RGB").save(QA/"main-on-existing-base.jpg",quality=90)
    # QA corridor includes Schweinfurt through Frankfurt to Mainz, with a geographic margin.
    box=(1040,1740,1950,2350)
    comp.crop(box).convert("RGB").save(QA/"main-corridor-progress.jpg",quality=90)
    manifest={"status":"PROVISIONAL geographic sprite batch; historical 1618 flow not verified",
              "source_canvas":"base/base_3600.jpg","source":"Natural Earth 10m named Main centreline",
              "projection":"same Lambert Conformal Conic as base",
              "render_order":["existing base","Main river connectors","city sprites","labels"],
              "seam_qa":"PASS: exact RGBA reconstruction",
              "segment_count":segments,"geometry_feature_labels":labels,
              "tile_count":len(tiles),"connectors":tiles,"sites":sites,
              "historical_qa":"pending","city_water_alignment_qa":"pending"}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    (QA/"qa.json").write_text(json.dumps({"seam_qa":"PASS","tiles":len(tiles),"sites":sites,
                                         "historical_qa":"pending"},indent=2,ensure_ascii=False)+"\n")
    print("Main batch committed build: tiles",len(tiles),"river segments",segments,
          "sites",len(sites),"seam QA passed")
if __name__=="__main__":build()
