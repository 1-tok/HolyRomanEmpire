#!/usr/bin/env python3
"""Lossless reconstruction of approved Rhine v011 PNG from Git-committed Base64 text chunks.

Port of the successful text-chunk -> verified PNG -> Actions commit approach used in
earlier map projects. No substituted/generated image is ever accepted.
"""
import base64, hashlib, json, re, sys
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"placements/rhine-v016-original-painted-intake.json"
IN=ROOT/"assets/intake/rhine-v011/chunks"
OUT=ROOT/"assets/reference/rhine-v011-full-painted-strip-overlay-3600x4800.png"
DEFAULT_HASH="b24dd693d513704b87fb26e7bb02eeaf771e8ef10a0a1790481940b7611e1af4"

def decode_chunks(chunks,expected_sha,output):
    data=bytearray()
    for f in chunks:
        raw=f.read_text("ascii")
        # Strict only Base64 and whitespace permitted. No other scripts/payloads.
        if not re.fullmatch(r"[A-Za-z0-9+/=\s]*",raw):
            raise ValueError("Unexpected non-Base64 bytes: "+f.name)
        data.extend(base64.b64decode("".join(raw.split()),validate=True))
    checksum=hashlib.sha256(data).hexdigest()
    if checksum!=expected_sha:
        raise ValueError(f"Source SHA-256 mismatch: got {checksum} expected {expected_sha}")
    if not bytes(data).startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Not an actual PNG file")
    from io import BytesIO
    with Image.open(BytesIO(data)) as image:
        image.verify()
    with Image.open(BytesIO(data)) as image:
        if image.size!=(3600,4800) or image.mode!="RGBA":
            raise ValueError(f"Invalid exact image size/mode: {image.size}/{image.mode}")
        if image.getbbox()!=(802,1901,1273,3274):
            raise ValueError("Wrong source: not the full extended v011 painting")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(data)
    assert hashlib.sha256(output.read_bytes()).hexdigest()==checksum
    return {"size":len(data),"sha256":checksum,"source_chunks":len(chunks),"output":str(output)}

def main():
    q=json.loads(MANIFEST.read_text())
    expected=q["sha256"]
    if expected!=DEFAULT_HASH:
        raise ValueError("Source manifest hash changed without approval")
    parts=sorted(IN.glob("part-*.b64"))
    if not parts:
        raise SystemExit("No painted-image Base64 chunks committed yet; refusing to generate substitute art.")
    # Required complete series: part-00000.b64 to part-N.b64 and exactly
    # the count declared by the intake manifest.
    total=q.get("chunk_count")
    if not isinstance(total,int) or total<1:
        raise SystemExit("Intake manifest requires chunk_count once binary parts are staged.")
    if len(parts)!=total:
        raise SystemExit(f"Missing v011 payload parts: expected {total}, found {len(parts)}")
    for i,f in enumerate(parts):
        if f.name!=f"part-{i:05d}.b64":
            raise SystemExit("Out-of-order/missing chunk sequence at part "+str(i))
    result=decode_chunks(parts,expected,OUT)
    qa=ROOT/"reports/rhine-v016-restored-painted-strip/binary-intake-qa.json"
    qa.parent.mkdir(parents=True,exist_ok=True)
    qa.write_text(json.dumps({**result,"status":"LOSSLESS VERIFIED ORIGINAL PAINTING","not_regenerated":True},indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
