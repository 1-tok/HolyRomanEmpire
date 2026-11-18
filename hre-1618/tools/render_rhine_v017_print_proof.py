#!/usr/bin/env python3
"""HRE v017 five-panel, 2x 7200x9600 print-development REFERENCE proof.

Authoritative sheet spec is 36x48in at 300 PPI, or 10800x14400px.
This builder produces a deliberately unapproved 2x INTERPOLATED reference at
200 PPI for that final 36x48 sheet. It does not invent raster detail, claim
a high-resolution painted master, or change earlier approved v016 artwork.

GIS city anchors are projected from WGS84 using existing HRE map math.
The Main river reference is the existing geographic transparent PNG; the
diagnostic guide is DRAWN ONLY on QA panel B, never on the printed art.

Panel exports use transparent overlaps in source composition and preserve the
source's exact location. They are NOT falsely claimed native-redrawn paintings.
"""
from pathlib import Path
import sys, json, hashlib
from PIL import Image,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from build_rhine_batch001 import px
WORK=(3600,4800)
PROOF=(7200,9600)
FINAL=(10800,14400)
R=2
PANELS=ROOT/"placements/rhine-v017-panel-manifest.json"
SOURCE=ROOT/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png"
BASE=ROOT/"base/base_3600.jpg"
MAIN=ROOT/"reports/main-batch-001/main-canonical-transparent.png"
OUT=ROOT/"reports/rhine-v017-print-proof"
CANVAS=ROOT/"maps/canvas"
OUT.mkdir(parents=True,exist_ok=True)
CANVAS.mkdir(parents=True,exist_ok=True)

def main():
    config=json.loads(PANELS.read_text())
    if config["proof_canvas_px"]!=list(PROOF) or config["final_print_canvas_px"]!=list(FINAL):
        raise RuntimeError("HRE sheet print resolution specification changed")
    base=Image.open(BASE).convert("RGBA")
    paint=Image.open(SOURCE).convert("RGBA")
    assert base.size==paint.size==WORK
    expected="b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4"
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==expected
    # Same raw source and placement as v016, without procedural v012-v015 layers.
    original=Image.alpha_composite(base,paint)
    city_anchors=[]
    for c in config["cities"]:
        x,y=px(c["lat"],c["lon"])
        label=dict(c,x_work_px=round(x,2),y_work_px=round(y,2),
                   x_proof_px=round(2*x,2),y_proof_px=round(2*y,2),
                   x_final_px=round(3*x,2),y_final_px=round(3*y,2))
        owner=next(p for p in config["panels"] if p["id"]==c["panel"])
        x0,y0,x1,y1=owner["bbox_work_px"]
        if not(x0<=x<=x1 and y0<=y<=y1):
            raise ValueError(f"City anchor outside assigned panel: {c['site']} {x:.1f},{y:.1f} in {owner['id']}")
        city_anchors.append(label)
    # A genuinely uncompressed detail source cannot be inferred by upsampling.
    # Generate 2x reference as stated; preserve full resolution, not thumbnail.
    resized=original.resize(PROOF,Image.Resampling.LANCZOS)
    full=CANVAS/"rhine-v017-reference-7200x9600.jpg"
    resized.convert("RGB").save(full,quality=92,subsampling=0)
    assert Image.open(full).size==PROOF
    # Thumbnail map for quick placement check.
    original.resize((1200,1600),Image.Resampling.LANCZOS).convert("RGB").save(
        OUT/"full-map-reference-1200.jpg",quality=92)
    panel_records=[]
    main_geo=Image.open(MAIN).convert("RGBA")
    assert main_geo.size==WORK
    for p in config["panels"]:
        x0,y0,x1,y1=p["bbox_work_px"]
        # Each panel is clipped to its exact same global map, then 2x resampled.
        cropped=original.crop((x0,y0,x1,y1))
        artifact=f"panel-{p['id'].lower()}-reference-2x.jpg"
        cropped.resize(((x1-x0)*2,(y1-y0)*2),Image.Resampling.LANCZOS).convert("RGB").save(
            OUT/artifact,quality=94)
        # Separate QA-only copy with real city anchors, panel edges and Main fork trace.
        qa=cropped.copy()
        d=ImageDraw.Draw(qa)
        for c in city_anchors:
            x,y=c["x_work_px"],c["y_work_px"]
            if x0<=x<x1 and y0<=y<y1:
                xx=round(x-x0);yy=round(y-y0)
                d.ellipse((xx-4,yy-4,xx+4,yy+4),fill=(255,235,74,255),
                    outline=(49,40,32,255),width=2)
                d.text((xx+8,yy-9),c["site"],fill=(255,238,104,255),
                    stroke_width=2,stroke_fill=(40,33,25,255))
        if p["id"]=="B":
            # Show geographic Main (not conceptual hand-drawn blue water) on QA.
            line=main_geo.crop((x0,y0,x1,y1))
            mask=line.getchannel("A").point(lambda a:235 if a>90 else 0)
            geometry=Image.new("RGBA",line.size,(235,44,183,0))
            geometry.putalpha(mask)
            qa=Image.alpha_composite(qa,geometry)
            d=ImageDraw.Draw(qa)
            d.text((12,12),"MAGENTA: projected Main centerline — QA ONLY",
                fill=(255,242,133),stroke_width=2,stroke_fill=(28,28,24))
        qa.resize(((x1-x0)*2,(y1-y0)*2),Image.Resampling.LANCZOS).convert("RGB").save(
            OUT/f"panel-{p['id'].lower()}-city-registration-qa.jpg",quality=93)
        panel_records.append(dict(id=p["id"],source_bbox_work_px=p["bbox_work_px"],
            proof_bbox=[2*x0,2*y0,2*x1,2*y1],
            print_bbox=[3*x0,3*y0,3*x1,3*y1],
            panel_filename=artifact,
            city_qa_filename=f"panel-{p['id'].lower()}-city-registration-qa.jpg",
            overlap_preserved_via_single_master=True,
            native_redraw_complete=False))
    # Rebuild low-res source exact from the chosen global crop (overlapping panel
    # edges are *not* independently painted so no river jumps are introduced).
    report=dict(version="v017",build="2x-interpolated reference from v016",
        full_map_proof=str(full.relative_to(ROOT)),
        source_painting_sha256=expected,
        original_canvas_size=list(WORK),reference_proof_size=list(PROOF),
        reference_proof_ppi_at_36x48=200,
        final_master_size=list(FINAL),final_master_ppi=300,
        final_sheet_inch=[36,48],
        source_pixels_interpolated=True,
        genuinely_new_high_resolution_painted_pixels=False,
        print_ready=False,merge_to_main_allowed=False,
        original_v016_untouched=True,
        panels=panel_records,cities=city_anchors,
        main_fork_geometry="Existing named Main geographic PNG shown in Panel B QA only; do not infer that it is rendered in new highres painted style",
        strasbourg="User permits visual water connection; Ill remains separately named geographic river",
        geographic_quality="Requires 1618 river-bank/channel historical certification",
        acceptance_gate=[
            "Produce new detailed native painted artwork at 3x scale for each accepted panel",
            "Do not interpolate the 3600px painted v011 source and call it 300PPI detail",
            "Confluence at Mainz must follow main-canonical-transparent.png geometry",
            "Correct Breisach–Basel geographic river mismatch before final print",
            "Per-panel source pixel count, alpha edges, city landmarks, density and seams must pass QA"
        ])
    (OUT/"qa.json").write_text(json.dumps(report,indent=2)+"\n")
    print(f"v017 reference built: 7200x9600 on existing v016, {len(city_anchors)} geographic anchors, {len(panel_records)} overlapping proof panels; print approval FALSE",flush=True)
if __name__=="__main__":
    main()
