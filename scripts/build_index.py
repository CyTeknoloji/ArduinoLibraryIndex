"""Builds a slim Arduino Library Manager index for the mobile app.

Input:  https://downloads.arduino.cc/libraries/library_index.json.gz (one entry per release)
Output: out/libraries.json.gz (one entry per library, newest releases first)
"""

import gzip
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

SOURCE_URL = "https://downloads.arduino.cc/libraries/library_index.json.gz"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")
FORMAT_VERSION = 1
MAX_VERSIONS = 8
MAX_INCLUDES = 8
MAX_SENTENCE = 160
MAX_AUTHOR = 60


def version_key(v: str):
    main, _, pre = v.partition("-")
    main = main.split("+", 1)[0]
    nums = []
    for part in main.split("."):
        m = re.match(r"\d+", part)
        nums.append(int(m.group(0)) if m else 0)
    while len(nums) < 4:
        nums.append(0)
    return (tuple(nums[:4]), 0 if pre else 1, pre)


def clean(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "\u2026"
    return text


def short_author(author: str) -> str:
    author = re.sub(r"<[^>]*>", "", author or "")
    return clean(author, MAX_AUTHOR)


def main():
    print("Downloading", SOURCE_URL)
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "ArduinoLibraryIndex-builder"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = gzip.decompress(resp.read())
    source = json.loads(raw)
    releases = source.get("libraries", [])
    print("Releases:", len(releases))

    grouped = {}
    for rel in releases:
        name = (rel.get("name") or "").strip()
        version = (rel.get("version") or "").strip()
        if not name or not version or "," in name:
            continue
        grouped.setdefault(name, []).append(rel)

    libs = []
    for name, rels in grouped.items():
        rels.sort(key=lambda r: version_key(r.get("version", "")), reverse=True)
        latest = rels[0]
        archs = sorted({(a or "").strip().lower() for a in latest.get("architectures") or [] if (a or "").strip()})
        includes = [i.strip() for i in latest.get("providesIncludes") or [] if (i or "").strip()][:MAX_INCLUDES]
        deps = sorted({(d.get("name") or "").strip() for d in latest.get("dependencies") or [] if (d.get("name") or "").strip()})
        entry = {
            "n": name,
            "v": [r["version"] for r in rels[:MAX_VERSIONS]],
            "a": short_author(latest.get("author", "")),
            "s": clean(latest.get("sentence", ""), MAX_SENTENCE),
            "c": (latest.get("category") or "").strip(),
            "ar": archs or ["*"],
        }
        if includes:
            entry["i"] = includes
        if deps:
            entry["d"] = deps
        repo = (latest.get("repository") or "").strip()
        if repo.startswith("https://"):
            entry["r"] = repo
        libs.append(entry)

    libs.sort(key=lambda e: e["n"].lower())
    body = json.dumps(libs, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    doc = {
        "format": FORMAT_VERSION,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hash": digest,
        "count": len(libs),
        "libs": libs,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    data = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with open(os.path.join(OUT_DIR, "libraries.json.gz"), "wb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=9, mtime=0) as gz:
            gz.write(data)
    meta = {"format": FORMAT_VERSION, "generated": doc["generated"], "hash": digest, "count": len(libs)}
    with open(os.path.join(OUT_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)

    size = os.path.getsize(os.path.join(OUT_DIR, "libraries.json.gz"))
    print(f"Libraries: {len(libs)}  raw: {len(data)} bytes  gz: {size} bytes  hash: {digest}")
    if len(libs) < 1000:
        print("Refusing to publish: library count looks wrong", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
