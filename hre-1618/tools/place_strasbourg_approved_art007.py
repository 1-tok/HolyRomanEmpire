#!/usr/bin/env python3
"""HRE 1618 Strasbourg approved-art geographic canvas preview 007.

The original 1122x1402 RGB painting is preserved in assets/reference.
Remove the parchment background only for a transparent map-placement
version, scale once, then cut north, central-city, south individual
overlays FROM THE SAME IMAGE so joined brush pixels have exact seams.
Use 3600x4800 geographic base as-is; no newly invented river geometry.

CAUTION: This is a real art placement proof, not a 1618 hydrography
certification. Strasbourg's city water is the Ill, separate from main Rhine.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter
import numpy as np
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/reference/strasbourg-approved-painterly-river-full.png"
BASE=ROOT/"base/base_3600.jpg"
PLAC=ROOT/"placements/rhine-batch-001.json"
OUT=ROOT/"assets/sprites/rivers/strasbourg-approved-placement-007"
CANVAS=ROOT/"maps/canvas"
QA=ROOT/"reports/strasbourg-approved-placement-007"
W,H=3600,4800
# City center is the established geographic manifest anchor.
PAINT_W=250
CUTS=[("01-ill-upper-painted",0,90),("02-strasbourg-city-river",90,234),
      ("03-ill-lower-painted",234,312)]
def difference_equal(a,b):
    return not any(ch.getbbox() for ch in ImageChops.difference(a,b).split())
def make_transparent(original):
    rgb=np.array(original.convert("RGB"))
    r=rgb[:,:,0].astype(np.int16)
    g=rgb[:,:,1].astype(np.int16)
    b=rgb[:,:,2].astype(np.int16)
    # Characteristic parchment is warm orange; retain painted blue water,
    # plants, warm brick roofs, stone outlines, and riverside structures.
    foreground=((r<202)|(g<156)|(b<96)|(r-g<18)|(g-b<21)|(b>g-3))
    a=Image.fromarray((foreground*255).astype("uint8"),"L")
    a=a.filter(ImageFilter.GaussianBlur(1.8))
    converted=original.convert("RGBA")
    converted.putalpha(a)
    return converted
def main():
    for p in (OUT,CANVAS,QA):p.mkdir(parents=True,exist_ok=True)
    source=Image.open(SOURCE).convert("RGB")
    assert source.size==(1122,1402),source.size
    cfg=json.loads(PLAC.read_text())
    target=next(x for x in cfg["entries"] if x["site"]=="Strasbourg")
    local=make_transparent(source)
    local.save(QA/"strasbourg-approved-full-transparency.png",optimize=True)
    # This 250px-wide full master is the unique map-scale painting;
    # all cropped tiles preserve exact same global paint pixels.
    scaled=local.resize((250,312),Image.Resampling.LANCZOS)
    # Painted city center in approved source is approximately (480,750).
    # Anchor the city's approved artwork to the manifest city coordinate.
    x0=round(target["x"]-480*250/1122)
    y0=round(target["y"]-750*312/1402)
    assert 800<x0<1100 and 2280<y0<2620
    # Fit only the OUTER reaches of the newly approved painting to the
    # georeferenced older river position. Preserve city brushwork and its
    # approved architecture without geometric displacement.
    # The previously committed blue-line/painted layer is used as a geometric
    # guide ONLY, never as visible final artwork.
    guide_path=ROOT/"maps/canvas/strasbourg-painted-rhine-006.png"
    guide=np.asarray(Image.open(guide_path).getchannel("A"))
    pic=np.asarray(scaled)
    blue=(pic[:,:,3]>140)&(pic[:,:,2]>pic[:,:,0]+8)&(pic[:,:,1]>pic[:,:,0]+5)
    def paint_centre(row):
        indices=np.flatnonzero(blue[row])
        if len(indices)<3:raise RuntimeError("No blue-water pixels in painting endpoint row")
        return float(np.median(indices))
    def geo_centre(map_y):
        lo=max(0,round(target["x"])-160);hi=min(W,round(target["x"])+210)
        index=np.flatnonzero(guide[map_y,lo:hi]>200)
        if len(index)<3:raise RuntimeError("No geographic Rhine pixels at target endpoint")
        return lo+float(np.median(index))
    delta_top=np.clip(geo_centre(y0+10)-(x0+paint_centre(10)),-75,75)
    delta_bottom=np.clip(geo_centre(y0+300)-(x0+paint_centre(300)),-75,75)
    # Wide transparent working strip accommodates translated tree and banks.
    adjusted=np.zeros((312,400,4),dtype=np.uint8)
    for row in range(312):
        if row<90: shift=delta_top*((90-row)/90)**1.3
        elif row>234: shift=delta_bottom*((row-234)/(311-234))**1.3
        else: shift=0
        xx=75+int(round(shift))
        adjusted[row,xx:xx+250]=pic[row]
    # Gently blend painted exit edges onto the existing geographic river;
    # this prevents hard rectangular terminations in the map preview.
    feather=22
    for row in range(312):
        blend=min(1.0,(row+1)/feather,(312-row)/feather)
        adjusted[row,:,3]=np.rint(adjusted[row,:,3].astype(float)*blend).astype(np.uint8)
    scaled=Image.fromarray(adjusted,"RGBA")
    x0-=75
    layer=Image.new("RGBA",(W,H),(0,0,0,0))
    pieces=[];previous_end=0
    for name,ya,yb in CUTS:
        if ya!=previous_end:raise AssertionError("Uncovered join row")
        previous_end=yb
        strip=scaled.crop((0,ya,400,yb))
        bounds=strip.getbbox()
        if bounds is None:raise RuntimeError("Empty painted piece: "+name)
        piece=strip.crop(bounds)
        file=OUT/(name+".png")
        piece.save(file,optimize=True)
        reloaded=Image.open(file).convert("RGBA")
        assert difference_equal(piece,reloaded)
        gx=x0+bounds[0];gy=y0+ya+bounds[1]
        layer.paste(reloaded,(gx,gy))
        pieces.append({"file":file.name,"x":gx,"y":gy,
                       "width":reloaded.width,"height":reloaded.height,
                       "source_y":[ya,yb],
                       "sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
                       "kind":"approved hand-painted transparent scenery"})
    expected=Image.new("RGBA",(W,H),(0,0,0,0))
    expected.paste(scaled,(x0,y0))
    if not difference_equal(layer,expected):raise RuntimeError("Failed pixel-exact painterly seam reconstruction")
    # Confirm real painted blue water intersects both cut rows, not a
    # misleading pass through fully transparent background.
    rgba=np.asarray(scaled,dtype=np.int16)
    blue=(rgba[:,:,3]>160)&(rgba[:,:,2]>rgba[:,:,0]+8)&(rgba[:,:,1]>rgba[:,:,0]+4)
    seam_coverage={}
    for y in (89,90,233,234):
        count=int(blue[y].sum())
        if count<3:raise RuntimeError(f"No blue painted water across seam row {y}")
        seam_coverage[str(y)]=count
    base=Image.open(BASE).convert("RGBA")
    assert base.size==(W,H)
    result=Image.alpha_composite(base,layer)
    # Existing city vignettes remain; Strasbourg is replaced only in this
    # PREVIEW by the approved new painted city-and-Ill image.
    cities=[]
    for item in cfg["entries"]:
        if item["site"]=="Strasbourg":continue
        p=ROOT/item["asset"]
        if not p.exists():continue
        city=Image.open(p).convert("RGBA")
        city.thumbnail((cfg["working_sprite_width_px"],)*2,Image.Resampling.LANCZOS)
        xx=round(item["x"])-city.width//2
        yy=round(item["y"])-city.height//2
        result.alpha_composite(city,(xx,yy))
        cities.append(item["site"])
    if len(cities)<4:raise RuntimeError("Other city sprites not in repo")
    result.convert("RGB").save(CANVAS/"strasbourg-approved-painted-preview-007.jpg",quality=93)
    layer.save(CANVAS/"strasbourg-approved-painted-overlay-007.png",optimize=True)
    # Detailed map view with real territorial boundaries and no misleading
    # paper graphic or new map background.
    crop=(865,2330,1230,2775)
    result.crop(crop).resize((876,1068),Image.Resampling.LANCZOS).convert("RGB").save(
        QA/"strasbourg-map-section-preview.jpg",quality=95)
    result.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(
        QA/"full-map-preview.jpg",quality=92)
    # Artwork directly from approved painting is never re-generated.
    # Local seam proof is derived from actual pixel cut lines.
    diagnostic=scaled.convert("RGBA")
    dbg=ImageDraw.Draw(diagnostic)
    for _,a,b in CUTS[:-1]:
        dbg.line((0,b-1,399,b-1),fill=(232,60,55,255),width=1)
    diagnostic.resize((750,936),Image.Resampling.NEAREST).save(QA/"sprite-cut-boundaries.png")
    checks={
       "approved_art":"assets/reference/strasbourg-approved-painterly-river-full.png",
       "source_dimensions":[1122,1402],"render_size":[250,312],
       "canvas_dimensions":[W,H],"city_anchor":[target["x"],target["y"]],
       "painting_origin_on_map":[x0,y0],
       "geo_endpoint_shift_px":{"north":round(float(delta_top),2),"south":round(float(delta_bottom),2)},
       "river_edge_blend_px":22,
       "city_render_order":"base, three transparent approved painting segments, other city sprites, labels",
       "pixel_seams":"PASS: three individual transparent PNGs exactly reconstruct one common painting",
       "water_across_seams":"PASS: painted blue water exists on both sides of all two cuts",
       "blue_counts_by_seam_row":seam_coverage,
       "original_painting_unmodified":True,
       "replaces_older_strasbourg_art_in_preview_only":True,
       "map_geography":"Base unchanged; approved city anchored to Strasbourg; scenic outer river reaches elastically shifted toward existing mapped river course, historic Ill/Rhine still provisional",
       "historic_caution":"Strasbourg is on Ill, not the main Rhine. The image's river is an artistic concept, NOT validated 1618 Ill/Rhine channels.",
       "print_approval":False,
       "pieces":pieces,
       "map_preview":"maps/canvas/strasbourg-approved-painted-preview-007.jpg",
       "status":"MAP-SCALE ART PLACEMENT FOR USER VISUAL REVIEW"
    }
    (OUT/"manifest.json").write_text(json.dumps(checks,indent=2)+"\n")
    (QA/"qa.json").write_text(json.dumps(checks,indent=2)+"\n")
    print("PASS approved Strasbourg art, 3 independent painted PNG sections, 2 exact seams, original 3600x4800 map.")
if __name__=="__main__":main()
