#!/usr/bin/env python3
"""Generate *candidate* HRE 1618 Rhine sprites via OpenAI Images API.

Requires OPENAI_API_KEY in environment. Never changes approved sprites.
Usage:
  python tools/generate_rhine_candidates.py --count 2 --model gpt-image-2.5-flare
  python tools/generate_rhine_candidates.py --count 1 --site Koblenz
"""
import argparse, base64, csv, datetime, hashlib, json, os, re, sys
import urllib.error, urllib.request
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageFile

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts" / "rhine.md"
SITES = ROOT / "river-sites.csv"
ACCEPTED = ROOT / "sprites"
CANDIDATES = ROOT / "sprites" / "candidates"
REPORTS = ROOT / "reports" / "generation"
MODELS = {"gpt-image-2.5-flare", "gpt-image-2.5-sunburst"}
IMAGE_URL = "https://api.openai.com/v1/images/generations"
Image.MAX_IMAGE_PIXELS = 100_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False

STYLE = """
Art direction, locked for HRE 1618: a fine hand-painted miniature landscape
sprite matching the previously approved Crusader Map architectural painting
style (warm natural stone, terracotta roofs, leafy local European forests and
fields, delicately varied ink outlines, visible hand-painted pigment texture).
View from SOUTH, looking NORTH, elevated about 35-45 degrees above the horizon:
see roofs and street plan as well as visible south-facing facades.
Not a top-down plan and not a low-side view; no skyline or horizon.
Accurate local European architecture as it stood in AD 1618; Renaissance
features allowed if already built, no later Baroque alterations, no modern
features. No generic duplicate twin-spired cathedrals. Each city's named
landmark must have its historically specific silhouette.
An isolated, single compact city vignette, with a restrained fringe of
riverside fields/trees. Transparent background: NO checkerboard, white matte,
paper halo, shadow, border, title, lettering, flag text, or labels.
The geographic river is already painted on the repository base map:
avoid painting a long river corridor or changing its course. Where water is
required by the subject, show only a small bank edge, quay, canal or bridge
that can be masked onto the pre-existing Rhine watercourse. Do not invent a
new meander to connect sprites. Strong silhouette legible at 225px across,
while preserving architectural detail at 1024px.
"""

def parse_prompt_file():
    data = PROMPTS.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^##\s+\d+\.\s+(.+?)\s*$", data))
    result = {}
    for i, m in enumerate(matches):
        section = data[m.end():matches[i+1].start() if i+1<len(matches) else len(data)]
        q = re.search(r"(?m)^>\s*(.+(?:\n(?!\n|#|File:).+)*)", section)
        if not q:
            continue
        # All Rhine instructions in the existing manifest are single-line quoted prompts.
        result[m.group(1).strip()] = q.group(1).strip().replace("\n", " ")
    return result

def api_generate(prompt, model, key):
    request = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "quality": "high",
        "background": "transparent",
        "output_format": "png",
        "n": 1
    }
    body = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(IMAGE_URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            output = json.load(response)
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"Images API returned {exc.code}: {payload}") from None
    items = output.get("data") or []
    if not items or not items[0].get("b64_json"):
        raise RuntimeError("Images API returned no base64 PNG payload")
    return base64.b64decode(items[0]["b64_json"], validate=True)

def validate(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not PNG data")
    with Image.open(BytesIO(data)) as im:
        if im.format != "PNG" or im.width < 1024 or im.height < 1024 or im.width != im.height:
            raise ValueError(f"expected square PNG >=1024px, got {im.size}")
        rgba = im.convert("RGBA")
        alpha = rgba.getchannel("A")
        if alpha.getextrema()[0] >= 255:
            raise ValueError("background is opaque")
        # Require genuine open space for overlapping / placement.
        transparent = sum(v for i,v in enumerate(alpha.histogram()) if i<32)
        if transparent / (im.width*im.height) < .07:
            raise ValueError("insufficient transparent area for a standalone sprite")
        # Require some painted content (not only transparent pixels).
        if alpha.getextrema()[1] < 180:
            raise ValueError("image appears empty or too translucent")
        im.load()
    return True

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--count",type=int,default=1)
    arg.add_argument("--site",default=None)
    arg.add_argument("--model",choices=sorted(MODELS),default="gpt-image-2.5-flare")
    args=arg.parse_args()
    if not 1<=args.count<=3:
        raise SystemExit("--count must be 1, 2 or 3 (cost-control limit)")
    key=os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY missing; nothing generated or charged")
    prompts=parse_prompt_file()
    positions={}
    with SITES.open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if row["river"]=="Rhine" and row["on_sheet"].startswith("yes"):
                positions[row["site"]]=row
    if args.site and args.site not in positions:
        raise SystemExit(f"Unknown Rhine site: {args.site}")
    queue=[args.site] if args.site else sorted(
        positions, key=lambda k:int(positions[k]["order"]))
    CANDIDATES.mkdir(parents=True,exist_ok=True)
    REPORTS.mkdir(parents=True,exist_ok=True)
    generated=[]
    for place in queue:
        if len(generated)>=args.count:break
        if place not in prompts:
            print(f"SKIP missing source prompt: {place}");continue
        if (ACCEPTED/f"{place}.png").exists() or any(CANDIDATES.glob(f"{place}--*.png")):
            print(f"SKIP already accepted/candidate: {place}");continue
        position=positions[place]
        prompt=(STYLE+"\n\nSite: "+place+"; latitude "+
                position["lat"]+", longitude "+position["lon"]+
                ".\nExact repository-specific historic site brief:\n"+
                prompts[place]+"\n\nIMPORTANT: The south-facing art viewpoint "
                "does not alter the north-up geographical course. "
                "Keep the town at its true riverbank and leave waterways "
                "under separate base-map control.")
        print("Generating candidate:",place,flush=True)
        data=api_generate(prompt,args.model,key)
        validate(data)
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ident=hashlib.sha256(data).hexdigest()
        name=f"{place}--{stamp}--{ident[:10]}.png"
        (CANDIDATES/name).write_bytes(data)
        record={"site":place,"status":"candidate-needs-visual-approval",
            "png":f"sprites/candidates/{name}","sha256":ident,
            "model":args.model,"created_utc":stamp,
            "prompt_source":"prompts/rhine.md","lat":position["lat"],
            "lon":position["lon"],
            "qa":{"dimensions":True,"transparency":True,
                "historical_accuracy":"not-reviewed",
                "river_banks":"not-reviewed","map_scale":"not-reviewed"}}
        (REPORTS/f"{name[:-4]}.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
        generated.append(record)
    print(json.dumps({"generated_count":len(generated),
        "candidate_files":[item["png"] for item in generated]},indent=2))

if __name__=="__main__":
    main()
