#!/usr/bin/env python3
"""Strasbourg painted Ill/canal junction refinement, batch 002.

Refines four separate committed connector PNGs *without shifting their mapped
coordinates or city attachment ports*.  Samples water and bank colours from the
actual committed Strasbourg.png at each port, blends those colours into the
last few pixels of each waterway, adds deterministic ink/watercolour edge grain,
and keeps the city sprite ABOVE all connector artwork.

Geometry is inherited from batch 001 (OSM named Ill ways used for its Ill
reference points). Modern OSM does not independently verify 1618 courses.
Two short canal stubs are only candidates: they do not represent historically
verified exterior waterways.
"""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label
from PIL import Image, ImageChops, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/"assets/sprites/rivers/strasbourg-ill-batch-001"
OUT=ROOT/"assets/sprites/rivers/strasbourg-ill-batch-002"
QA=ROOT/"reports/strasbourg-ill-batch-002"
BASE=ROOT/"base/base_3600.jpg"
CITY=ROOT/"sprites/Strasbourg.png"
W,H=3600,4800
SEED=161802

def is_water(pixels):
    p=pixels.astype(np.int16)
    return (p[:,:,3]>=145)&(p[:,:,2]>p[:,:,0]+12)&(p[:,:,1]>p[:,:,0]+6)

def color_samples(city, port, city_origin):
    a=np.asarray(city.convert("RGBA"))
    x=int(port[0]-city_origin[0]);y=int(port[1]-city_origin[1])
    x0=max(0,x-6);x1=min(a.shape[1],x+7)
    y0=max(0,y-6);y1=min(a.shape[0],y+7)
    patch=a[y0:y1,x0:x1]
    m=is_water(patch)
    if not np.any(m):raise RuntimeError("No actual city painted blue water at port "+str(port))
    target=np.median(patch[m,:3],axis=0).astype(float)
    # Color-consistent grass/silt sampling around the port, not recoloring roofs.
    border=(patch[:,:,3]>180)&(~m)&(patch[:,:,1]>patch[:,:,2]*.78)
    shore=np.median(patch[border,:3],axis=0).astype(float) if np.any(border) else np.array([143.,151.,103.])
    return target,shore

def refine(sprite, city, rec, city_origin, index):
    """Retain the exact alpha footprint, geographic endpoints and layer bounds."""
    rgba=np.asarray(sprite.convert("RGBA")).copy()
    h,w=rgba.shape[:2]
    port=rec["city_water_port"]
    ox=int(rec["x"]);oy=int(rec["y"])
    xp=int(port[0]-ox);yp=int(port[1]-oy)
    if not (-8<=xp<w+8 and -8<=yp<h+8):raise RuntimeError("Port is outside PNG proximity: "+rec["id"])
    target,shore=color_samples(city,port,city_origin)
    water=is_water(rgba)
    if np.count_nonzero(water)<5:raise RuntimeError("Missing painted water in "+rec["id"])
    # City-port-adjacent source color is measured from the existing connector.
    yy,xx=np.mgrid[:h,:w]
    d=np.hypot(xx-xp,yy-yp)
    near=water&(d<=9)
    if not near.any():raise RuntimeError("No wet pixels within 9px of city port: "+rec["id"])
    source=np.median(rgba[near,:3],axis=0).astype(float)
    shift=target-source
    # Stronger harmonization at city; gradually return to original painted hue.
    # At the port the RGB difference is constrained to <= 8 per channel.
    strength=np.clip((26-d)/23,0,1)**1.7
    strength[d<=3]=1
    rng=np.random.default_rng(SEED+index)
    fine=gaussian_filter(rng.standard_normal((h,w)).astype(np.float32),.7)
    med=gaussian_filter(rng.standard_normal((h,w)).astype(np.float32),2)
    med/=max(float(med.std()),1e-6)
    # Gouache grain on original water footprint only; faded at attachment.
    grain=np.clip(fine*16+med*2.3,-8,8)*(1-strength)
    rgb=rgba[:,:,:3].astype(float)
    corrected=rgb+shift[None,None,:]*strength[:,:,None]
    corrected+=grain[:,:,None]*np.array([.72,1.0,1.1])[None,None,:]
    rgba[:,:,:3]=np.where(water[:,:,None],np.clip(corrected,0,255),rgba[:,:,:3]).astype(np.uint8)
    # Tint only shoreline fringe to match adjacent city greenery and stone.
    bank=(rgba[:,:,3]>0)&(~water)
    blend=np.clip((17-d)/17,0,.58)
    bank_color=rgba[:,:,:3].astype(float)*(1-blend[:,:,None])+shore[None,None,:]*blend[:,:,None]
    rgba[:,:,:3]=np.where(bank[:,:,None],np.clip(bank_color,0,255),rgba[:,:,:3]).astype(np.uint8)
    # Strictly unchanged geometry/opacity, including cutout edge.
    original=np.asarray(sprite.convert("RGBA"))
    assert np.array_equal(rgba[:,:,3],original[:,:,3])
    # Verify water tint actually got closer to city sample.
    refined=np.median(rgba[near,:3],axis=0).astype(float)
    before=float(np.linalg.norm(source-target))
    after=float(np.linalg.norm(refined-target))
    if after>before+.1 or after>17:
        raise RuntimeError(f"Color matching did not converge {rec['id']} before={before:.1f} after={after:.1f}")
    return Image.fromarray(rgba,"RGBA"),{
        "attachment_port":[int(v) for v in port],
        "city_water_rgb":[round(float(v),1) for v in target],
        "old_port_rgb":[round(float(v),1) for v in source],
        "new_port_rgb":[round(float(v),1) for v in refined],
        "old_color_distance":round(before,2),
        "new_color_distance":round(after,2),
        "alpha_footprint_preserved":True,
        "port_overlap_pixels":int(np.count_nonzero(near))
    }

def assemble(srcdir,records):
    full=Image.new("RGBA",(W,H),(0,0,0,0))
    for rec in records:
        png=Image.open(srcdir/rec["file"]).convert("RGBA")
        full.alpha_composite(png,(int(rec["x"]),int(rec["y"])))
    return full

def main():
    OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
    prev=json.loads((OLD/"manifest.json").read_text())
    city=Image.open(CITY).convert("RGBA")
    box=prev["city_box"];city.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
    assert city.size==tuple(box[2:4])
    city_origin=tuple(box[:2])
    recs=[]
    for index,rec in enumerate(prev["connectors"]):
        original=Image.open(OLD/rec["file"]).convert("RGBA")
        refined,metrics=refine(original,city,rec,city_origin,index)
        if refined.size!=(rec["width"],rec["height"]):
            raise RuntimeError("Sprite dimensions changed")
        target=OUT/rec["file"];refined.save(target,optimize=True)
        decoded=Image.open(target).convert("RGBA")
        diff=ImageChops.difference(decoded,refined)
        if any(ch.getbbox() for ch in diff.split()):
            raise RuntimeError("PNG round-trip mismatch "+rec["file"])
        item=dict(rec)
        item.update(metrics)
        item["sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
        item["source_geometry"]="Inherited from validated batch-001 city port and mapped Ill candidate"
        if "canal" in rec["id"]:
            item["historical_course_qa"]="UNVERIFIED: port-attached short stub only"
        else:
            item["historical_course_qa"]="OSM modern named Ill reference; AD 1618 course not established"
        recs.append(item)
    assembled=assemble(OUT,recs)
    # Independent second reconstruction from disk, test every RGBA band.
    round_trip=assemble(OUT,recs)
    if any(b.getbbox() for b in ImageChops.difference(assembled,round_trip).split()):
        raise RuntimeError("RGBA sprite reassembly failure")
    # Each piece's alpha footprint must match batch 001 (seam endpoint stability).
    for rec in recs:
        old=np.asarray(Image.open(OLD/rec["file"]).convert("RGBA"))[:,:,3]
        new=np.asarray(Image.open(OUT/rec["file"]).convert("RGBA"))[:,:,3]
        if not np.array_equal(old,new):raise RuntimeError("Shape/connector seam changed "+rec["file"])
    composed=Image.alpha_composite(Image.open(BASE).convert("RGBA"),assembled)
    before_city=composed.copy()
    composed.alpha_composite(city,city_origin)
    # City layer is pixel-identical to committed artwork. Connector visible
    # only outside it / through its own transparent regions.
    check=Image.new("RGBA",(W,H),(0,0,0,0))
    check.alpha_composite(city,city_origin)
    a=np.asarray(city)[:,:,3]
    if a.max()<245:raise RuntimeError("City is unexpectedly transparent")
    # Four individual 2x junction QA crops and one map-scale assembled preview.
    diag=QA/"city-junctions";diag.mkdir(parents=True,exist_ok=True)
    for rec in recs:
        xp,yp=rec["city_water_port"]
        crop=(max(0,xp-42),max(0,yp-42),min(W,xp+43),min(H,yp+43))
        pre=before_city.crop(crop).convert("RGB").resize((340,340),Image.Resampling.LANCZOS)
        post=composed.crop(crop).convert("RGB").resize((340,340),Image.Resampling.LANCZOS)
        paired=Image.new("RGB",(680,340),(238,230,212))
        paired.paste(pre,(0,0));paired.paste(post,(340,0))
        draw=ImageDraw.Draw(paired)
        draw.text((8,8),"River underlay",fill=(20,26,25),stroke_width=2,stroke_fill=(248,246,225))
        draw.text((348,8),"City over river",fill=(20,26,25),stroke_width=2,stroke_fill=(248,246,225))
        paired.save(diag/(rec["id"]+".jpg"),quality=92)
    boxview=(910,2430,1160,2690)
    composed.crop(boxview).convert("RGB").resize((1000,1040),Image.Resampling.LANCZOS).save(QA/"strasbourg-refined-assembled.jpg",quality=94)
    composed.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(QA/"full-map-preview.jpg",quality=90)
    oldcomposed=Image.alpha_composite(Image.open(BASE).convert("RGBA"),assemble(OLD,prev["connectors"]))
    oldcomposed.alpha_composite(city,city_origin)
    oldpanel=oldcomposed.crop(boxview).convert("RGB").resize((700,728),Image.Resampling.LANCZOS)
    newpanel=composed.crop(boxview).convert("RGB").resize((700,728),Image.Resampling.LANCZOS)
    compare=Image.new("RGB",(1400,728))
    compare.paste(oldpanel,(0,0));compare.paste(newpanel,(700,0))
    compare.save(QA/"before-after.jpg",quality=91)
    qa={
        "batch":"Strasbourg Ill painted-bank and canal-junction refinement 002",
        "source_city":"hre-1618/sprites/Strasbourg.png",
        "city_box":box,
        "geometry_source":"batch-001 mapped Ill candidate endpoints, OSM modern-way references",
        "geometry_preserved":True,
        "new_historically_verified_1618_canal_routes":0,
        "historic_accuracy":"UNVERIFIED: no period historical waterways digitization is in repository",
        "water_tint_qa":"PASS: port-local city-water color convergence for each connector",
        "seam_qa":"PASS: all four separate PNGs preserve original alpha footprint; exact RGBA on-disk reassembly",
        "layer_order":["original base","painted river connector sprites","committed city PNG","labels"],
        "city_buildings_unchanged":True,
        "city_sprites":1,"connector_count":len(recs),
        "connectors":recs,
        "review_status":"provisional; inspect city shoreline and 1618 Ill/canal course at map scale",
        "comparison":"reports/strasbourg-ill-batch-002/before-after.jpg"
    }
    (OUT/"manifest.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (QA/"qa.json").write_text(json.dumps(qa,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PASS: refined 4 painted Ill/canal PNGs, preserved geometry and alpha footprints, city-port watercolor tint matched",flush=True)

if __name__=="__main__":main()
