#!/usr/bin/env python3
"""Build verifiable HRE 1618 Rhine progress composites on ORIGINAL base_3600.jpg.

Renders only actual committed sprites; uncommitted downstream sites are marked
as hollow anchor rings, not depicted as finished artwork.
"""
import csv, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports"/"rhine-batch-001"
BASE=ROOT/"base"/"base_3600.jpg"
W,H=3600,4800

def font(size):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        if Path(name).exists(): return ImageFont.truetype(name,size)
    return ImageFont.load_default()

def main():
    # Generate the same continuous water and city overlay as the existing QA.
    subprocess.run([sys.executable,str(ROOT/"tools"/"build_rhine_batch001.py")],check=True)
    placements=json.loads((OUT/"placements.json").read_text())
    placed={c["site"] for c in placements["city_placements"]}
    canvas=Image.open(OUT/"on-existing-base-3600.jpg").convert("RGB")
    d=ImageDraw.Draw(canvas)
    sites=[]
    with (ROOT/"river-sites.csv").open(newline="",encoding="utf-8") as f:
        sites=[r for r in csv.DictReader(f) if r["river"]=="Rhine" and r["on_sheet"].startswith("yes")]
    # The site file's px coordinates are for the full 10800x14400 master.
    # Convert by exactly 3, preserving the authoritative existing map projection.
    rows=[]
    for r in sites:
        x=round(float(r["px_x"])/3);y=round(float(r["px_y"])/3)
        active=r["site"] in placed
        rows.append({"site":r["site"],"x":x,"y":y,"status":"placed-provisional" if active else "anchor-only"})
        if active:
            # Small neutral center ring, no claim that the building faces the right bank
            d.ellipse((x-9,y-9,x+9,y+9),outline=(18,79,27),width=3)
        else:
            d.ellipse((x-13,y-13,x+13,y+13),outline=(56,52,46),width=4)
            d.ellipse((x-7,y-7,x+7,y+7),fill=(249,239,218))
    # Crop from the ACTUAL base and actual composite, preserving upstream drawing.
    region=(800,1770,1660,3190)
    inset=canvas.crop(region)
    d=ImageDraw.Draw(inset)
    ft=font(19);small=font(15)
    names={"Basel","Strasbourg","Speyer","Worms","Mainz","Koblenz","Bonn","Cologne","Düsseldorf","Duisburg","Wesel"}
    label_x=[135,430,135,430,135,430,135,430,135,430,135]
    relevant=[r for r in rows if r["site"] in names and region[0]<=r["x"]<region[2] and region[1]<=r["y"]<region[3]]
    for n,r in enumerate(relevant):
        x=r["x"]-region[0]; y=r["y"]-region[1]
        lx=max(4,min(inset.width-270,label_x[n%len(label_x)]))
        ly=max(6,min(inset.height-28,y-25))
        label=r["site"]+("  ✓" if r["status"]=="placed-provisional" else "  ○")
        bb=d.textbbox((0,0),label,font=ft)
        d.rectangle((lx-3,ly-2,lx+bb[2]+6,ly+bb[3]+6),fill=(251,247,231),outline=(89,76,57),width=1)
        d.text((lx,ly),label,font=ft,fill=(30,50,35))
        d.line((x,y,lx+min(bb[2],70),ly+12),fill=(65,61,52),width=1)
    inset.save(OUT/"rhine-upper-detail.png")
    overview=canvas.resize((1200,1600),Image.Resampling.LANCZOS)
    overview.save(OUT/"rhine-progress-overview.jpg",quality=91)
    (OUT/"rhine-progress-status.json").write_text(json.dumps({
        "source_canvas":str(BASE.relative_to(ROOT)),"geometry":"existing NE10m base river",
        "source_sprite_directory":"sprites/","placed_count":len(placed),
        "placed":sorted(placed),"anchors":rows,
        "outputs":["rhine-progress-overview.jpg","rhine-upper-detail.png",
                   "continuous-rhine-water-overlay.png","on-existing-base-3600.jpg"],
        "qa":"provisional: image generation is not historical verification"
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Rhine progress maps:",len(placed),"actual sprites,",len(rows)-len(placed),"unfilled anchor sites")

if __name__=="__main__":main()
