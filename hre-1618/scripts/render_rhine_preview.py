#!/usr/bin/env python3
"""Render a geographic Rhine-placement QA preview from the committed GeoJSON.

This is a north-up *placement diagnostic*, not the final 1618 atlas painting.
Source geometry is Natural Earth 1:50m, not a historically verified riverbank.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/placements/rhine-reference-geometry.geojson"
ART = ROOT / "assets/sprites/rhine"
OUTPUT = ROOT / "reports/rhine-placement/river-placement-preview.png"
W, H = 1550, 2250

def project(lon, lat):
    return (round(160 + (lon - 4.35) / (9.05 - 4.35) * 1200),
            round(120 + (52.15 - lat) / (52.15 - 47.28) * 2000))

def main():
    fc = json.loads(DATA.read_text(encoding="utf-8"))
    river = next(f for f in fc["features"] if f["geometry"]["type"] == "LineString")
    pts = [project(*p) for p in river["geometry"]["coordinates"]]
    im = Image.new("RGBA", (W, H), (237, 232, 206, 255))
    d = ImageDraw.Draw(im)
    d.line(pts, fill=(208, 207, 173), width=42, joint="curve")
    d.line(pts, fill=(53, 112, 138), width=28, joint="curve")
    d.line(pts, fill=(120, 169, 193), width=11, joint="curve")
    for f in fc["features"]:
        if f["geometry"]["type"] != "Point":
            continue
        x, y = project(*f["geometry"]["coordinates"])
        p = f["properties"]
        name = p["name"]
        sprite = p.get("artwork")
        if sprite:
            file = ART / sprite
            if file.exists():
                icon = Image.open(file).convert("RGBA")
                icon.thumbnail((225, 225), Image.Resampling.LANCZOS)
                im.alpha_composite(icon, (max(0, x-icon.width//2), max(0, y-icon.height//2)))
        d.ellipse((x-6, y-6, x+6, y+6), fill=(158, 60, 45))
        d.text((x+12, y-12), name, fill=(47, 47, 42))
    d.text((48, 30), "Rhine 1618 - placement QA only / centerline is modern generalized reference", fill=(44, 51, 49))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(OUTPUT)
    print(OUTPUT)

if __name__ == "__main__":
    main()
