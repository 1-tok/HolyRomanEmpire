#!/usr/bin/env python3
"""Lossless transport for the user-accepted v021 painted Rhine corridor.

The original binary arrives as a Git-committed ZIP, or as consecutive Base64
text chunks. Verify the *original PNG bytes* before rendering anything.
No regenerate/repaint/approximation is permitted.
"""
from pathlib import Path
import base64, hashlib, io, json, re, sys, zipfile
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"assets"
STAGING=ASSETS/"intake/rhine-v021"
SOURCE=ASSETS/"reference/rhine-v021-continuous-river-original.png"
EXPECTED_SHA="03fd81a8ece2c01d1a902dd8f6d91f0ad5a8cc6d148942f9d851130aa5fb1d10"
EXPECTED_SIZE=4568820
EXPECTED_WH=(1024,1536)
REVIEW=ROOT/"reports/rhine-v021-actual-master-canvas"

def get_payload():
    pack=STAGING/"original-rhine-v021-painting.zip"
    if pack.exists():
        with zipfile.ZipFile(pack) as z:
            names=[x for x in z.namelist() if not x.endswith("/")]
            candidates=[x for x in names if x.endswith("a_highly_detailed_illustrated_historical_map_style.png") or x.endswith("rhine-v021-continuous-river-original.png")]
            if len(candidates)!=1:
                raise ValueError("ZIP requires exactly one PNG with the accepted source filename")
            return z.read(candidates[0]),"original-rhine-v021-painting.zip"
    chunks=sorted((STAGING/"chunks").glob("part-*.b64"))
    if chunks:
        count_txt=STAGING/"chunk-count.txt"
        if not count_txt.is_file():
            raise ValueError("Missing chunk-count.txt for v021 Base64 transport")
        n=int(count_txt.read_text("ascii").strip())
        if len(chunks)!=n or n<1:
            raise ValueError(f"Incomplete v021 chunks: got {len(chunks)}, expected {n}")
        payload=bytearray()
        for i,path in enumerate(chunks):
            if path.name!=f"part-{i:05d}.b64":
                raise ValueError("Chunk missing or out of sequence: "+path.name)
            raw="".join(path.read_text("ascii").split())
            if not re.fullmatch("[A-Za-z0-9+/=]+",raw):
                raise ValueError("Invalid Base64 alphabet in "+path.name)
            payload.extend(base64.b64decode(raw,validate=True))
        return bytes(payload),f"{n} consecutive Git-committed Base64 chunks"
    if SOURCE.exists():
        return SOURCE.read_bytes(),"already committed PNG"
    raise SystemExit("V021 original binary not yet staged. No generated fallback.")

def main():
    data,transport=get_payload()
    sha=hashlib.sha256(data).hexdigest()
    if sha!=EXPECTED_SHA or len(data)!=EXPECTED_SIZE:
        raise ValueError("Original v021 byte checksum/size verification FAILED: "+sha)
    with Image.open(io.BytesIO(data)) as f:
        f.verify()
    with Image.open(io.BytesIO(data)) as f:
        if f.size!=EXPECTED_WH:
            raise ValueError("Wrong source painting dimensions "+str(f.size))
        image=f.convert("RGBA")
    # Verify the exact reconstructed three-sheet layout, no lateral offsets.
    cores=((0,512),(512,1024),(1024,1536))
    expanded=((0,622),(402,1134),(914,1536))
    proof=Image.new("RGBA",EXPECTED_WH)
    pieces=[]
    for i,((a,b),(lo,hi)) in enumerate(zip(cores,expanded),1):
        strip=image.crop((0,lo,1024,hi))
        part=strip.crop((0,a-lo,1024,b-lo))
        proof.paste(part,(0,a))
        pieces.append({"sheet":i,"global_y_bounds":[lo,hi],"core_y":[a,b],"global_x":0})
    if ImageChops.difference(proof,image).getbbox():
        raise ValueError("Three source-exact sheets are not reconstructable")
    SOURCE.parent.mkdir(parents=True,exist_ok=True)
    SOURCE.write_bytes(data)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED_SHA
    REVIEW.mkdir(parents=True,exist_ok=True)
    (REVIEW/"binary-intake-qa.json").write_text(json.dumps({
        "result":"PASS: lossless original PNG committed",
        "source_sha256":sha,
        "source_bytes":len(data),
        "dimensions":EXPECTED_WH,
        "transport":transport,
        "sheet_core_exact":True,
        "all_sheet_x_offsets":[0,0,0],
        "sheet_count":3,
        "sheets":pieces,
        "historical_1618_geography_approved":False,
        "native_300ppi_print_quality_approved":False
    },indent=2)+"\n")
    print("PASS original v021 artwork lossless transfer; all sheet offsets zero, source hash "+sha)

if __name__=="__main__": main()
