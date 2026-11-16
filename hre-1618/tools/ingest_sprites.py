#!/usr/bin/env python3
"""Ingest ChatGPT sprite PNGs for the HRE 1618 map.

Save each finished sprite into sprites/inbox/, named after its site as in
sprite-brief.md (Vienna.png, Regensburg.png, ...). Then run:

    python3 tools/ingest_sprites.py                # check and move inbox files
    python3 tools/ingest_sprites.py --commit       # also commit to git
    python3 tools/ingest_sprites.py --commit --push

Checks: PNG file, square canvas, at least 512 px, transparent (alpha or tRNS).
A file that fails any check stays in the inbox with the reason printed.
Standard library only.
"""
import argparse, csv, hashlib, os, shutil, struct, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "sprites")
INBOX = os.path.join(SPRITES, "inbox")
MANIFEST = os.path.join(SPRITES, "manifest.csv")
MIN_SIZE = 512
FIELDS = ["site", "file", "width", "height", "sha256", "ingested_utc"]


def check_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None, ["not a PNG file"]
    w, h, _depth, ctype = struct.unpack(">IIBB", data[16:26])
    has_trns, pos = False, 8
    while pos + 8 <= len(data):
        length, = struct.unpack(">I", data[pos:pos + 4])
        if data[pos + 4:pos + 8] == b"tRNS":
            has_trns = True
        pos += 12 + length
    problems = []
    if w != h:
        problems.append(f"not square ({w}x{h})")
    if min(w, h) < MIN_SIZE:
        problems.append(f"smaller than {MIN_SIZE}px ({w}x{h})")
    if not (ctype in (4, 6) or has_trns):
        problems.append("no transparency (export as a transparent PNG)")
    return (w, h, data), problems


def read_manifest():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_manifest(rows):
    rows.sort(key=lambda r: r["site"])
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replace", action="store_true", help="overwrite an existing sprite")
    ap.add_argument("--commit", action="store_true", help="git add and commit the new sprites")
    ap.add_argument("--push", action="store_true", help="push after committing")
    args = ap.parse_args()

    os.makedirs(INBOX, exist_ok=True)
    files = sorted(f for f in os.listdir(INBOX) if f.lower().endswith(".png"))
    if not files:
        print("Inbox is empty.")
        return

    rows = {r["site"]: r for r in read_manifest()}
    done, rejected = [], []
    for name in files:
        src = os.path.join(INBOX, name)
        site = os.path.splitext(name)[0]
        dest = os.path.join(SPRITES, site + ".png")
        try:
            info, problems = check_png(src)
        except Exception as e:
            info, problems = None, [str(e)]
        if not problems and os.path.exists(dest) and not args.replace:
            problems = ["sprite already exists (use --replace)"]
        if problems:
            rejected.append((name, problems))
            continue
        w, h, data = info
        digest = hashlib.sha256(data).hexdigest()
        shutil.move(src, dest)
        rows[site] = {"site": site, "file": f"sprites/{site}.png", "width": w,
                      "height": h, "sha256": digest,
                      "ingested_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
        done.append(site)

    if done:
        write_manifest(list(rows.values()))
        print("Ingested: " + ", ".join(done))
    for name, problems in rejected:
        print(f"Rejected {name}: " + "; ".join(problems))

    if done and args.commit:
        paths = [f"sprites/{s}.png" for s in done] + ["sprites/manifest.csv"]
        subprocess.run(["git", "-C", ROOT, "add", "--"] + paths, check=True)
        msg = f"Add HRE 1618 sprites: {', '.join(done)}"
        subprocess.run(["git", "-C", ROOT, "commit", "-q", "-m", msg], check=True)
        print("Committed.")
        if args.push:
            subprocess.run(["git", "-C", ROOT, "push"], check=True)
            print("Pushed.")


if __name__ == "__main__":
    main()
