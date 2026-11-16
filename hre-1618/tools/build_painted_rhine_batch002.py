#!/usr/bin/env python3
"""Paint geographic Upper Rhine connectors and city junction proofs, AD 1618 map.

Outputs new painted RGBA sprites rather than flat technical centerline strokes.
The river follows the same Natural Earth centerlines and projection as base;
deterministic raster watercolor is applied to the fixed geometry, never used
to invent or move bends. All pieces are cropped from one canvas, so tiles
reassemble bit-for-bit. City artwork is composited ABOVE the painted river.

Historic river course and painted city-water shoreline integration still
need period-source and visual approval. No old assets overwritten.
"""
import hashlib, json, math, sys, urllib.request
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, maximum_filter
from PIL import Image, ImageDraw, ImageChops, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_rhine_batch001 import px, river_lines, SOURCE
OUT=ROOT/"assets"/"sprites"/"rivers"/"rhine-painted-batch-002"
QA=ROOT/"reports"/"rhine-painted-batch-002"
BASE=ROOT/"base"/"base_3600.jpg"
CFG=ROOT/"placements"/"rhine-batch-001.json"
W,H=3600,4800
# Main corridor Basel--Mainz, deliberately bounded to prevent incidental
# unrelated Danube/Dutch river features becoming part of this batch.
ROI=(850,1740,1510,3190)
TILE=240
RNG=np.random.default_rng(1618)

def paint_river():
    x0,y0,x1,y1=ROI
    w,h=x1-x0,y1-y0
    source=urllib.request.urlopen(SOURCE,timeout=120).read()
    lines=river_lines(source)
    mask=Image.new("L",(w,h),0)
    d=ImageDraw.Draw(mask)
    segments=0
    for line in lines:
        for (a,b),(c,e) in zip(line,line[1:]):
            # Rhine proper from Basel to Mainz, excluding distant features.
            if max(a,c)<47.38 or min(a,c)>50.20: continue
            if max(b,e)<7.25 or min(b,e)>8.90: continue
            p=px(a,b);q=px(c,e)
            p=(round(p[0]-x0),round(p[1]-y0))
            q=(round(q[0]-x0),round(q[1]-y0))
            if max(p[0],q[0])<0 or min(p[0],q[0])>=w or max(p[1],q[1])<0 or min(p[1],q[1])>=h:continue
            d.line((p,q),fill=255,width=13)
            segments+=1
    if segments<40:raise RuntimeError("Rhine feature extraction too small")
    core=np.asarray(mask,dtype=np.uint8)>0
    if not core.any():raise RuntimeError("Empty river mask")
    # Contiguous water body and banks are derived from the same authoritative
    # pixels. Painting has textured COLOR / edge opacity but no freehand route.
    dist_out=distance_transform_edt(~core).astype(np.float32)
    dist_in=distance_transform_edt(core).astype(np.float32)
    fine=gaussian_filter(RNG.standard_normal((h,w)).astype(np.float32),1.4)
    coarse=gaussian_filter(RNG.standard_normal((h,w)).astype(np.float32),18)
    coarse/=max(float(coarse.std()),1e-5)
    medium=gaussian_filter(RNG.standard_normal((h,w)).astype(np.float32),5)
    medium/=max(float(medium.std()),1e-5)
    n=np.clip(0.6*coarse+0.4*medium,-2.4,2.4)
    # A thin meadow/wet-bank buffer on either side of the true route;
    # avoid painting thick fantasy islands or freehand connections.
    bank=(dist_out>=0)&(dist_out<=16+np.clip(2*n,-4,4))
    wet=bank & (dist_out<=4+np.clip(n,-2,2))
    meadow=bank & ~wet
    rgba=np.zeros((h,w,4),dtype=np.uint8)
    # Feather toward the *outside* of the bank to blend to existing terrain.
    alpha_meadow=np.clip((17+2*n-dist_out)*21,0,190).astype(np.uint8)
    # Grassland watercolor washes: deterministic stable noise, not procedural strokes.
    light=n*10+fine*7
    for ch,base in enumerate((140,153,94)):
        rgba[:,:,ch]=np.where(meadow,np.clip(base+light+(8 if ch==0 else 0),0,255),rgba[:,:,ch])
    rgba[:,:,3]=np.where(meadow,alpha_meadow,rgba[:,:,3])
    for ch,base in enumerate((118,124,99)):
        rgba[:,:,ch]=np.where(wet,np.clip(base+light,0,255),rgba[:,:,ch])
    rgba[:,:,3]=np.where(wet,180,rgba[:,:,3])
    # Water occupies only the source corridor: no river drawn on top of city sprites.
    shimmer=(n*11+fine*22+np.sin(np.arange(h,dtype=np.float32)[:,None]*.34)*3)
    for ch,base in enumerate((72,123,145)):
        rgba[:,:,ch]=np.where(core,np.clip(base+shimmer+(8 if ch==2 else 0),0,255),rgba[:,:,ch])
    rgba[:,:,3]=np.where(core,245,rgba[:,:,3])
    # Natural under-bank shade, without shifting the mask or bank center.
    edge=core&(dist_in<=2.2)
    rgba[:,:,:3]=np.where(edge[:,:,None],
                        np.clip(rgba[:,:,:3].astype(np.int16)-10,0,255).astype(np.uint8),
                        rgba[:,:,:3])
    # White broken micro-highlights inside the real water mask.
    current=(core & (dist_in>2) & (fine>0.72))
    rgb=rgba[:,:,:3].astype(np.int16)
    rgb[current]=np.clip(rgb[current]+np.array([21,25,18]),0,255)
    rgba[:,:,:3]=rgb.astype(np.uint8)
    # Replicate pixel for pixel on the full canvas, preserving georeferencing.
    full=Image.new("RGBA",(W,H),(0,0,0,0))
    local=Image.fromarray(rgba,"RGBA")
    full.paste(local,(x0,y0))
    return full,mask,segments

def exact_cuts(full):
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    rebuilt=Image.new("RGBA",(W,H),(0,0,0,0))
    # Every slice is from the SAME painted full image with no rerendering.
    for i,y0 in enumerate(range(0,H,TILE)):
        y1=min(H,y0+TILE)
        strip=full.crop((0,y0,W,y1))
        box=strip.getbbox()
        if box is None:continue
        tile=strip.crop(box)
        file=f"rhine-painted-{i+1:02d}.png"
        p=OUT/file
        tile.save(p,optimize=True)
        decoded=Image.open(p).convert("RGBA")
        if any(b.getbbox() for b in ImageChops.difference(decoded,tile).split()):
            raise AssertionError("PNG decoded colors differ for "+file)
        x,y=box[0],y0+box[1]
        rebuilt.paste(decoded,(x,y))
        manifest.append({"file":file,"x":x,"y":y,"width":decoded.width,"height":decoded.height,
                         "global_y_range":[y0,y1],
                         "sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    if not manifest:raise AssertionError("No painted connector tiles")
    diff=ImageChops.difference(rebuilt,full)
    if any(b.getbbox() for b in diff.split()):
        raise AssertionError("Painted connector seam validation failed")
    return rebuilt,manifest

def composites(full,geo_mask,segments,manifest):
    QA.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(CFG.read_text())
    base=Image.open(BASE).convert("RGBA")
    if base.size!=(W,H):raise RuntimeError("Base size mismatch")
    composed=Image.alpha_composite(base,full)
    placements=[]
    # Produce true side-by-side city-junction crops, NOT only site markers.
    diagnostics=QA/"city-junctions"; diagnostics.mkdir(parents=True,exist_ok=True)
    for entry in cfg["entries"]:
        p=ROOT/entry["asset"]
        if not p.exists():continue
        city=Image.open(p).convert("RGBA")
        city.thumbnail((cfg["working_sprite_width_px"],)*2,Image.Resampling.LANCZOS)
        x=round(entry["x"])-city.width//2
        y=round(entry["y"])-city.height//2
        river_crop=full.getchannel("A").crop((x,y,x+city.width,y+city.height))
        alpha=city.getchannel("A")
        overlap=np.asarray(river_crop)>0
        opaque=np.asarray(alpha)>=224
        occluded=int(np.count_nonzero(overlap&opaque))
        pre=composed.crop((x-65,y-65,x+city.width+65,y+city.height+65)).convert("RGB")
        composed.alpha_composite(city,(x,y))
        post=composed.crop((x-65,y-65,x+city.width+65,y+city.height+65)).convert("RGB")
        compare=Image.new("RGB",(pre.width*2,pre.height),(245,240,226))
        compare.paste(pre,(0,0));compare.paste(post,(pre.width,0))
        dd=ImageDraw.Draw(compare)
        dd.text((7,8),"PAINTED RIVER",fill=(24,26,21),stroke_width=2,stroke_fill=(245,240,226))
        dd.text((pre.width+7,8),"CITY ABOVE RIVER",fill=(24,26,21),stroke_width=2,stroke_fill=(245,240,226))
        compare.resize((760,380),Image.Resampling.LANCZOS).save(diagnostics/(entry["site"]+".jpg"),quality=93)
        placements.append({"site":entry["site"],"asset":entry["asset"],"x":x,"y":y,
                           "river_pixels_under_opaque_city":occluded,
                           "city_layer_above_river":True,
                           "junction_visual_status":"requires review; do not claim a painted shoreline match"})
    if len(placements)<5:raise RuntimeError("Expected five committed Rhine cities")
    composed.crop((800,1750,1600,3180)).convert("RGB").save(QA/"upper-rhine-painted-cities.jpg",quality=93)
    composed.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-map-preview.jpg",quality=90)
    full.save(QA/"painted-rhine-single-continuous-layer.png",optimize=True)
    report={
        "batch":"Rhine painted corridor from Basel to Mainz",
        "source":"Natural Earth 10m Rhine centerline with HRE 1618 base projection",
        "status":"PROVISIONAL painted overlay; historic bends and city shoreline matching require approval",
        "geographic_safeguard":"color and bank texture derived ONLY from fixed centerline pixels",
        "seam_check":"PASS: byte-for-byte same RGBA image after tile reassembly",
        "segment_count":segments,"tiles":len(manifest),"placed_cities":placements,
        "render_order":["original base","painted river connectors","painted city sprites","labels"],
        "qa_limit":"Seam pass applies river-to-river; city-water transition is reviewed visually but not historically certified."
    }
    (QA/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    (OUT/"manifest.json").write_text(json.dumps({**report,"connectors":manifest},indent=2)+"\n")
    print("PAINTED RHINE: connector tiles",len(manifest),"city sprites",len(placements),"segments",segments,"exact seam PASS")

def main():
    full,mask,segments=paint_river()
    recon,parts=exact_cuts(full)
    composites(recon,mask,segments,parts)

if __name__=="__main__":main()
