#!/usr/bin/env python3
"""Safe, idempotent ZIP sprite intake for the HRE 1618 repository.

Scans every ZIP under hre-1618/ (including previously uploaded archives).
Only validated image PNGs become sprites. Other files stay in their archive.
Output: sprites/*.png, sprites/manifest.csv, reports/intake/*.json.
No external service or Python dependency beyond Pillow.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageFile, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "sprites"
REPORT = ROOT / "reports" / "intake"
MANIFEST = DEST / "manifest.csv"
FIELDS = ("site", "file", "width", "height", "sha256", "ingested_utc")
MAX_ZIP = 100 * 1024 * 1024
MAX_ENTRIES = 500
MAX_TOTAL_UNPACKED = 250 * 1024 * 1024
MAX_PNG = 45 * 1024 * 1024
MIN_SIDE = 1024
MAX_SIDE = 12000
Image.MAX_IMAGE_PIXELS = 144_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False

def sha(data):
    return hashlib.sha256(data).hexdigest()

def clean_name(member):
    # A ZIP member is not trusted as a destination path.
    raw = member.replace("\\", "/")
    parts = raw.split("/")
    if raw.startswith("/") or any(p in (".", "..") for p in parts):
        return None
    basename = parts[-1]
    if basename.startswith(".") or not basename.lower().endswith(".png"):
        return None
    stem = Path(basename).stem
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-_")
    return (stem[:90] + ".png") if stem else None

def validate_png(data):
    if len(data) > MAX_PNG:
        return None, "PNG too large"
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None, "not a PNG"
    try:
        with Image.open(io.BytesIO(data)) as im:
            if im.format != "PNG":
                return None, "not a PNG image"
            w, h = im.size
            if w != h or not (MIN_SIDE <= w <= MAX_SIDE):
                return None, f"expected square {MIN_SIDE}-{MAX_SIDE}px; got {w}x{h}"
            if im.mode not in ("RGBA", "LA", "P") or (
                im.mode == "P" and "transparency" not in im.info
            ):
                return None, "no alpha/transparency channel"
            alpha = im.convert("RGBA").getchannel("A")
            extrema = alpha.getextrema()
            if extrema[0] == 255:
                return None, "alpha channel entirely opaque"
            im.load()  # Verify compressed raster data can actually be read.
            return (w, h), None
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        return None, "invalid PNG: " + str(exc)[:180]

def existing_manifest():
    if not MANIFEST.exists():
        return {}
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        return {r["site"]: r for r in csv.DictReader(f)}

def archives():
    # Ignore build caches and generated sprite/output directories.
    return sorted(p for p in ROOT.rglob("*.zip")
                  if not any(part in ("sprites", "reports", ".git", "__pycache__")
                             for part in p.relative_to(ROOT).parts))

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    registered = existing_manifest()
    existing_by_hash = {}
    for p in sorted(DEST.glob("*.png")):
        existing_by_hash[sha(p.read_bytes())] = p.name
    summary = {"archives": 0, "accepted": 0, "duplicates": 0,
               "conflicts": 0, "rejected": 0, "archives_failed": 0}
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for archive in archives():
        summary["archives"] += 1
        archive_bytes = archive.read_bytes() if archive.stat().st_size <= MAX_ZIP else b""
        h = sha(archive_bytes)[:12] if archive_bytes else "oversized"
        report_path = REPORT / (re.sub(r"[^A-Za-z0-9_-]", "-", archive.stem)[:70] +
                                "-" + h + ".json")
        record = {"archive": archive.relative_to(ROOT).as_posix(),
                  "archive_sha256": sha(archive_bytes) if archive_bytes else None,
                  "accepted": [], "duplicate": [], "conflict": [], "rejected": []}
        try:
            if not archive_bytes:
                raise ValueError("archive exceeds 100 MB")
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
                infos = z.infolist()
                if len(infos) > MAX_ENTRIES:
                    raise ValueError("too many ZIP entries")
                if sum(x.file_size for x in infos) > MAX_TOTAL_UNPACKED:
                    raise ValueError("unpacked ZIP exceeds 250 MB")
                for member in infos:
                    if member.is_dir():
                        continue
                    raw = member.filename.replace("\\", "/")
                    if "__MACOSX/" in raw or Path(raw).name.startswith("._"):
                        continue
                    if not raw.lower().endswith(".png"):
                        continue  # metadata/scripts: retained in original archive
                    name = clean_name(raw)
                    if not name:
                        record["rejected"].append({"member": raw, "reason": "unsafe filename"})
                        continue
                    if (member.external_attr >> 16) & 0o170000 == 0o120000:
                        record["rejected"].append({"member": raw, "reason": "symbolic link"})
                        continue
                    if member.file_size > MAX_PNG:
                        record["rejected"].append({"member": raw, "reason": "PNG too large"})
                        continue
                    try:
                        data = z.read(member)
                    except (RuntimeError, zipfile.BadZipFile, OSError, EOFError) as exc:
                        record["rejected"].append({"member": raw, "reason": "read error: " + str(exc)[:100]})
                        continue
                    dims, error = validate_png(data)
                    if error:
                        record["rejected"].append({"member": raw, "reason": error})
                        continue
                    digest = sha(data)
                    if digest in existing_by_hash:
                        record["duplicate"].append({"member": raw, "existing": existing_by_hash[digest]})
                        continue
                    target = DEST / name
                    if target.exists():
                        record["conflict"].append({"member": raw, "target": name, "reason": "different PNG already uses this filename"})
                        continue
                    target.write_bytes(data)  # byte-for-byte copy, no recompression
                    site = Path(name).stem
                    registered[site] = {
                        "site": site, "file": f"sprites/{name}",
                        "width": str(dims[0]), "height": str(dims[1]),
                        "sha256": digest, "ingested_utc": now
                    }
                    existing_by_hash[digest] = name
                    record["accepted"].append({"member": raw, "file": f"sprites/{name}", "sha256": digest})
        except (ValueError, zipfile.BadZipFile, OSError) as exc:
            record["archive_error"] = str(exc)[:300]
            summary["archives_failed"] += 1
        for key, count in (("accepted", "accepted"), ("duplicate", "duplicates"),
                           ("conflict", "conflicts"), ("rejected", "rejected")):
            summary[count] += len(record[key])
        report_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{archive.relative_to(ROOT)}: accepted={len(record['accepted'])} "
              f"duplicates={len(record['duplicate'])} conflicts={len(record['conflict'])} "
              f"rejected={len(record['rejected'])} error={record.get('archive_error', '-')}")
    if registered:
        with MANIFEST.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(registered[k] for k in sorted(registered))
    print("SUMMARY", json.dumps(summary, sort_keys=True))
    # File-level failures are quarantined *by report*, never silently accepted.
    # The job remains green to permit clean members in partially malformed archives.
    # A corrupt ZIP itself is reported but does not block other archives.

if __name__ == "__main__":
    main()
