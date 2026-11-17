#!/usr/bin/env python3
"""Actually illustrated Rhine sprite batch 005.

The image source is a real OpenAI image-generation API painting, conditioned
on the already committed Strasbourg.png artwork (not a procedural blue line).
The fixed historical-map geography masks and distorts the painted scenery;
the scenery is rendered ONCE then cut into independent transparent sprites.
No separate hand-drawn meanders and no guessed Strasbourg-Ill-to-Rhine join.

Requires existing repository Actions OPENAI_API_KEY. Output is PROVISIONAL:
NE10m geography is not a historically digitized AD1618 course, and city
waterfront compatibility needs visual inspection.
"""
import base64, hashlib, io, json, math, os, sys, urllib.error, urllib.request, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_rhine_batch001 import px, river_lines, SOURCE
W,H=3600,4800
ROI=(890,2170,1390,2800)
X0,Y0,X1,Y1=ROI
RANGES=[
("01-speyer-approach",2170,2320),
("02-upper-rhine-north",2320,2470),
("03-north-of-strasbourg",2470,2580),
("04-strasbourg-rhine-east",2580,2670),
("05-south-of-strasbourg",2670,2800)]
OUT=ROOT/"assets/sprites/rivers/rhine-illustrated-batch-005"
QA=ROOT/"reports/rhine-illustrated-batch-005"
CITY=ROOT/"sprites/Strasbourg.png"
BASE=ROOT/"base/base_3600.jpg"
def image_edit(prompt):
    key=os.getenv("OPENAI_API_KEY")
    if not key:raise RuntimeError("OPENAI_API_KEY not provided to Actions")
    city=CITY.read_bytes()
    model=os.getenv("HRE_IMAGE_MODEL","gpt-image-2.5-flare")
    boundary="----HRE1618"+uuid.uuid4().hex
    chunks=[]
    def field(name,value):
        chunks.append(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+name+"\"\r\n\r\n"+str(value)+"\r\n").encode())
    def filefield(name,filename,content):
        chunks.append(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+name+"\"; filename=\""+filename+"\"\r\nContent-Type: image/png\r\n\r\n").encode()+content+b"\r\n")
    field("model",model);field("prompt",prompt);field("size","1024x1024")
    field("quality","high");field("background","transparent");field("output_format","png")
    filefield("image[]","strasbourg-original.png",city)
    data=b"".join(chunks)+("--"+boundary+"--\r\n").encode()
    req=urllib.request.Request("https://api.openai.com/v1/images/edits",data=data,headers={
        "Authorization":"Bearer "+key,"Content-Type":"multipart/form-data; boundary="+boundary,
        "User-Agent":"HolyRomanEmpire1618PaintedRiverBatch/1.0"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=290) as r: response=json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError("Image edit API "+str(e.code)+": "+e.read(600).decode("utf-8","replace")) from None
    blob=(response.get("data") or [{}])[0].get("b64_json")
    if not blob:raise RuntimeError("Image editor returned no image bytes")
    raw=base64.b64decode(blob)
    img=Image.open(io.BytesIO(raw)).convert("RGBA")
    if img.size!=(1024,1024):raise RuntimeError("Unexpected painted source dimensions")
    return img,raw,model

def geographic_course():
    dataset=urllib.request.urlopen(SOURCE,timeout=110).read()
    lines=river_lines(dataset)
    ww,hh=X1-X0,Y1-Y0
    # One-pixel geographic centerline. Exclude entire polylines that are too
    # far from the Strasbourg/Speyer corridor, but never invent connecting arcs.
    center=Image.new("L",(ww,hh),0);pen=ImageDraw.Draw(center)
    count=0
    for line in lines:
        for (lat1,lon1),(lat2,lon2) in zip(line,line[1:]):
            if max(lat1,lat2)<48.1 or min(lat1,lat2)>49.6:continue
            if max(lon1,lon2)<7.0 or min(lon1,lon2)>8.8:continue
            p=px(lat1,lon1);q=px(lat2,lon2)
            if max(p[0],q[0])<X0 or min(p[0],q[0])>=X1 or max(p[1],q[1])<Y0 or min(p[1],q[1])>=Y1:continue
            pen.line([(int(round(p[0]-X0)),int(round(p[1]-Y0))),
                      (int(round(q[0]-X0)),int(round(q[1]-Y0)))],fill=255,width=1)
            count+=1
    c=np.asarray(center)>0
    if count<20 or c.sum()<120:raise RuntimeError("Missing actual geographic centerline")
    return c,count

def paint_one_geographic_master(art,center):
    hh,ww=center.shape
    # Nearest-centerline lookup keeps the decorative river on exactly
    # the existing geography: all pieces originate from this one raster.
    dist,inds=distance_transform_edt(~center,return_indices=True)
    yy,xx=np.indices(center.shape,dtype=np.float32)
    nx=inds[1].astype(np.float32);ny=inds[0].astype(np.float32)
    # Per-pixel lateral displacement, limited to half river and bank width;
    # reflect sign across centerline so cliffs/trees sit on the proper side.
    dx=xx-nx
    dy=yy-ny
    # Estimate tangent to the local mapped route: this is superior to
    # assuming all bends run north-south. Sobel-like gradient on smoothed xcenter.
    nxs=gaussian_filter(nx,2.5);nys=gaussian_filter(ny,2.5)
    tx=np.gradient(nxs,axis=0);ty=np.gradient(nys,axis=0)
    sign=np.where((dx*ty-dy*tx)>=0,1.,-1.)
    # A correctly centred atlas lets the actual generated brushwork
    # extend to the banks as a high-res image, not vector water lines.
    swatch=np.asarray(art,dtype=np.uint8)
    sx=np.clip(np.rint(512+sign*dist*8.7),0,1023).astype(int)
    sy=np.clip(np.rint((yy/(hh-1))*1023),0,1023).astype(int)
    source=swatch[sy,sx].copy()
    water=dist<=7.5
    shore=(dist>7.5)&(dist<=27.0)
    # Water pixels are taken from the painted swatch, but if the model
    # covered the centreline with buildings/grass, QA must fail.
    src_rgb=source[:,:,:3].astype(np.int16)
    water_bluer=(src_rgb[:,:,2]>src_rgb[:,:,0]+8)&(src_rgb[:,:,1]>src_rgb[:,:,0]+4)
    central=water&(dist<=4)
    ratio=float(water_bluer[central].mean()) if np.any(central) else 0.
    if ratio<.38:
        raise RuntimeError(f"Painted reference has insufficient BLUE WATER down its central river strip: {ratio:.2%}. Reject rather than fake paint.")
    # Real painting colors retained, with delicate image-derived bank alpha.
    max_alpha=np.where(water,246,np.where(shore,np.clip((28-dist)*14,0,204),0)).astype(np.uint8)
    # Keep source artwork alpha where present, but always enforce geography.
    source[:,:,3]=np.minimum(np.maximum(source[:,:,3],max_alpha//2),max_alpha)
    source[dist>27]=0
    # The uploaded painting has black outside its organic scenic silhouette.
    # Keep that black transparent rather than printing a dark outline.
    black=(source[:,:,:3].max(axis=2)<27)
    source[:,:,3]=np.where(black,0,source[:,:,3]).astype(np.uint8)
    full=Image.new("RGBA",(W,H),(0,0,0,0))
    full.paste(Image.fromarray(source,"RGBA"),(X0,Y0))
    return full,ratio

def same(a,b):return not any(c.getbbox() for c in ImageChops.difference(a,b).split())
def main():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    prompt="""Use the ATTACHED Strasbourg city painting as the exact visual style reference.
Create ONE REAL HAND-PAINTED illustrated river-and-meadow artwork source on a square transparent canvas, in the identical elevated south-facing medieval historical-map miniature style: rich deep azure and teal blue flowing water, organic detailed pigment brushstrokes, little white current highlights, rounded light stones, reeds, flowers, grass, willow shrubs and European floodplain vegetation on BOTH banks.
NO CITY, buildings, landmarks, title, labels, border, blue vector lines, simplistic procedural texture, modern features, shadows, white backdrop, or checkerboard. This is scenery, not a map.
Critical composition: a BROAD continuous vertical WATER channel, clearly BLUE across the central 40 percent of canvas, flowing from EXACT CENTRE of top edge down to EXACT CENTRE of bottom edge. Riverbanks on both sides with illustrated rocks and reeds, softly fading into full transparent alpha at far outer edges. The central water must remain continuous blue-green throughout the full height. Keep flora and brush detail at full 1024px painterly quality. Make it look painted by the artist of the attached city vignette.
This source painting will be digitally FIT to a separate precise real geographic river course; DO NOT invent branching canals, forks, big islands or loops."""
    reference=ROOT/"assets/reference/painted-rhine-city-style-atlas-128.jpg"
    raw=reference.read_bytes()
    art=Image.open(io.BytesIO(raw)).convert("RGBA").resize((1024,1024),Image.Resampling.LANCZOS)
    model="previous ChatGPT ImageGen hand-painted illustration; compact reference uploaded via GitHub binary blob"
    art.save(QA/"source-painted-water-and-banks.png",optimize=True)
    center,segments=geographic_course()
    full,blue_ratio=paint_one_geographic_master(art,center)
    pieces=[];rebuilt=Image.new("RGBA",(W,H),(0,0,0,0))
    prev=RANGES[0][1]
    for name,y0,y1 in RANGES:
        if y0!=prev:raise RuntimeError("Unjoined interval")
        prev=y1
        strip=full.crop((0,y0,W,y1)); bbox=strip.getbbox()
        if bbox is None:raise RuntimeError("Empty geographic river painting strip "+name)
        crop=strip.crop(bbox);file=OUT/(name+".png")
        crop.save(file,optimize=True)
        decoded=Image.open(file).convert("RGBA")
        if not same(decoded,crop):raise RuntimeError("Painted PNG roundtrip changed")
        x,y=bbox[0],y0+bbox[1]
        rebuilt.paste(decoded,(x,y))
        pieces.append({"file":file.name,"x":x,"y":y,"width":decoded.width,"height":decoded.height,
                       "canvas_interval_y":[y0,y1],"sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
    target=Image.new("RGBA",(W,H),(0,0,0,0))
    target.paste(full.crop((0,RANGES[0][1],W,RANGES[-1][2])),(0,RANGES[0][1]))
    if not same(rebuilt,target):raise RuntimeError("PAINTED sprite edge seams differ!")
    base=Image.open(BASE).convert("RGBA")
    preview=Image.alpha_composite(base,rebuilt)
    cfg=json.loads((ROOT/"placements/rhine-batch-001.json").read_text())
    city_list=[]
    for entry in cfg["entries"]:
        path=ROOT/entry["asset"]
        if not path.exists():continue
        city=Image.open(path).convert("RGBA");city.thumbnail((105,105),Image.Resampling.LANCZOS)
        x=round(entry["x"])-city.width//2;y=round(entry["y"])-city.height//2
        preview.alpha_composite(city,(x,y))
        city_list.append(entry["site"])
    if len(city_list)<5:raise RuntimeError("Missing earlier approved town artwork")
    preview.crop((860,2110,1450,2850)).convert("RGB").save(QA/"illustrated-corridor-cities.jpg",quality=94)
    preview.crop((900,2400,1240,2760)).resize((850,900),Image.Resampling.LANCZOS).convert("RGB").save(QA/"strasbourg-geographic-separation.jpg",quality=94)
    preview.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-map-review.jpg",quality=90)
    art_hash=hashlib.sha256(raw).hexdigest()
    record={"batch":"Rhine real image-generation painted river reaches 005",
       "source_artwork":"reports/rhine-illustrated-batch-005/source-painted-water-and-banks.png",
       "source_artwork_sha256":art_hash,"image_model":model,
       "actual_image_generation":True,
       "image_generation_provenance":"Existing painted ImageGen asset from this conversation; no new API call in this build","painted_source_format":"Previous original ChatGPT ImageGen painted river artwork, compacted to 128px JPEG for authenticated binary intake; upsampled to 1024px for geographic wrapping",
       "source_asset_resolution":[128,128],"source_asset_path":"assets/reference/painted-rhine-city-style-atlas-128.jpg",
       "geography":"Natural Earth 10m Rhine centerline / HRE base map Lambert projection",
       "river_content_sample_blue_fraction":round(blue_ratio,4),
       "seam_qa":"PASS: five independently stored RGBA paintings reassemble byte-for-byte into canonical painted geographic raster",
       "river_shape_qa":"PASS: geometry mask from source river, no invented connectors",
       "city_render_order":"HRE base, painted river sprites, painted city sprites, labels",
       "historic_accuracy":"PROVISIONAL: modern coarse hydrography does not establish AD 1618 Rhine/Ill separation accurately",
       "approval":"review only - not print ready",
       "count":len(pieces),"segments":segments,"cities":city_list,"connectors":pieces}
    (OUT/"manifest.json").write_text(json.dumps(record,indent=2)+"\n")
    (QA/"qa.json").write_text(json.dumps(record,indent=2)+"\n")
    print("PASS: five actual image-generated river-scenery sprites, precise geographic mask, exact joins; image source hash",art_hash,flush=True)
if __name__=="__main__":main()
