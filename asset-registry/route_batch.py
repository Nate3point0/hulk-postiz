#!/usr/bin/env python3
"""Route a Mixboard image batch into Pinterest / Social / Video / Merch lanes + niche/funnel tags.

Run ON THE MAC (Hulk or MacBook) where the drive is mounted. Never moves/copies originals:
it builds symlink "lanes" + a master registry (CSV + JSON) with absolute paths that
Postiz, ComfyUI/video pipeline, and BrainVault can all read.

  python3 route_batch.py --src "/Volumes/MUSIC/MIXBOARD/SECOND BATCH" --batch batch2 \
      --inventory ".../Mixboard Batch 2 Asset Library/asset-inventory.csv" \
      --duplicates ".../Mixboard Batch 2 Asset Library/duplicate-report.csv"

Niche matching uses the path RELATIVE to --src plus the inventory's descriptive columns,
never the volume path (so "/Volumes/MUSIC/MIXBOARD" can't tag everything as music).
"""
import argparse, csv, json, os, re, sys
from pathlib import Path

IMG = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}
LANES = ("pinterest", "social", "video", "merch")
# inventory columns that carry paths/hashes/sizes, not meaning; excluded from niche text
NON_TEXT = re.compile(r"path|link|sha|hash|width|height|px|file_type|asset_id", re.I)
try:
    from PIL import Image
except ImportError:
    Image = None
    print("! Pillow missing -> `pip3 install pillow` for aspect-ratio routing (falling back to keywords)", file=sys.stderr)

def probe(p):
    """(width, height, has_transparency)."""
    if not Image: return (0, 0, False)
    try:
        with Image.open(p) as im:
            alpha = False
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                lo, _ = im.convert("RGBA").getchannel("A").getextrema()
                alpha = lo < 255
            return (*im.size, alpha)
    except Exception: return (0, 0, False)

def word(kw):
    return re.compile(rf"\b{re.escape(kw)}s?\b")

def lanes_for(w, h, text, transparent):
    """Aspect ratio first, keywords as backup. Transparent cut-outs only go to merch."""
    if transparent: return ["merch"]
    out = set()
    if w and h:
        r = w / h
        if r <= 0.70: out |= {"pinterest", "video"}          # 2:3 pins, 9:16 reels/tiktok/shorts
        elif r <= 0.85: out |= {"social", "pinterest"}       # 4:5 / 3:4 feed + pins
        elif r <= 1.2: out.add("social")                     # 1:1
        else: out |= {"video", "social"}                     # 16:9 youtube/b-roll, cropped feed
    t = text.lower()
    for kw, lane in (("pin", "pinterest"), ("print", "pinterest"), ("reel", "video"), ("video", "video"),
                     ("ad", "social"), ("social", "social"), ("landing", "social")):
        if word(kw).search(t): out.add(lane)
    return sorted(out or {"social"})

def niche_for(text, cfg):
    t = text.lower()
    for name, n in cfg["niches"].items():
        if any(word(k).search(t) for k in n["keywords"]): return name
    return cfg["default_niche"]

def rel_key(path, src):
    """Path relative to the batch root, so inventory rows match files on any mount point."""
    s, p = str(src).rstrip("/") + "/", str(path)
    return p[len(s):] if p.startswith(s) else None

def load_inventory(path, src):
    """rel-path -> descriptive text. Keyed by relative path (not bare filename: names repeat across folders)."""
    m = {}
    if path and Path(path).exists():
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                orig = row.get("original_path") or next((v for v in row.values() if v and Path(v).suffix.lower() in IMG), "")
                key = rel_key(orig, src) or (f'{row["collection"]}/{row["filename"]}' if row.get("collection") and row.get("filename") else orig)
                if key: m[key] = " ".join(v for k, v in row.items() if v and not NON_TEXT.search(k))
    return m

def load_dupes(path, src):
    """rel-paths to skip: every copy after the first in each sha256 group (nothing deleted).
    Handles both one-row-per-group (`original_paths` joined with ' | ') and one-row-per-file reports."""
    skip, seen = set(), set()
    if path and Path(path).exists():
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("original_paths"):
                    paths = [x.strip() for x in row["original_paths"].split(" | ") if x.strip()]
                    skip |= {rel_key(x, src) or x for x in paths[1:]}
                    continue
                g = next((v for k, v in row.items() if re.search(r"group|hash|sha", k, re.I)), None)
                fn = next((v for v in row.values() if v and Path(v).suffix.lower() in IMG), None)
                if g and fn:
                    if g in seen: skip.add(rel_key(fn, src) or fn)
                    else: seen.add(g)
    return skip

def load_pod_titles(src):
    """POD drops carry results.json [{design, title}]; map design prefix -> title (+ 'merch')."""
    p = Path(src) / "results.json"
    try: return {d["design"]: d.get("title", "") + " merch" for d in json.load(open(p)) if d.get("design")}
    except Exception: return {}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--src", required=True)
    a.add_argument("--batch", default="batch2")
    a.add_argument("--inventory"); a.add_argument("--duplicates")
    a.add_argument("--out", default=os.path.expanduser("~/HULK/asset-registry"))
    a.add_argument("--niches", default=str(Path(__file__).with_name("niches.json")))
    o = a.parse_args()
    src = Path(o.src)
    cfg = json.load(open(o.niches))
    inv, skip, pod = load_inventory(o.inventory, src), load_dupes(o.duplicates, src), load_pod_titles(src)
    out = Path(o.out) / o.batch
    rows, skipped = [], 0
    for p in sorted(src.rglob("*")):
        if p.suffix.lower() not in IMG or p.name.startswith("."): continue
        rel = str(p.relative_to(src))
        if rel in skip: skipped += 1; continue
        w, h, alpha = probe(p)
        transparent = alpha or "_transparent" in p.stem.lower()
        text = f"{rel} {inv.get(rel, '')} {pod.get(p.stem.split('_')[0], '')}"
        lanes = lanes_for(w, h, text, transparent)
        niche = "merch-pod" if transparent and "merch-pod" in cfg["niches"] else niche_for(text, cfg)
        rid = f"{o.batch}-{len(rows)+1:04d}"
        for lane in lanes:  # symlink lanes: /out/<lane>/<niche>/<id>__name
            d = out / lane / niche; d.mkdir(parents=True, exist_ok=True)
            link = d / f"{rid}__{p.name}"
            if not link.is_symlink(): link.symlink_to(p.resolve())
        rows.append({"id": rid, "batch": o.batch, "abs_path": str(p.resolve()), "filename": p.name,
                     "width": w, "height": h, "transparent": int(transparent), "lanes": "|".join(lanes), "niche": niche,
                     "funnel": cfg["niches"][niche]["funnel"], "funnel_url": cfg["niches"][niche]["funnel_url"],
                     "codex_category": inv.get(rel, "")[:200], "postiz_media_id": "", "postiz_url": "",
                     "status": "staged"})
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "registry.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"]); wr.writeheader(); wr.writerows(rows)
    json.dump(rows, open(out / "registry.json", "w"), indent=1)
    # master index across all batches (batch1 + batch2 + ...) for Postiz / BrainVault / ComfyUI
    master = Path(o.out) / "MASTER_INDEX.json"
    idx = json.load(open(master)) if master.exists() else {}
    idx[o.batch] = {"src": o.src, "registry": str(out / "registry.csv"), "count": len(rows),
                    "lanes": {l: sum(l in r["lanes"].split("|") for r in rows) for l in LANES},
                    "niches": {n: sum(r["niche"] == n for r in rows) for n in cfg["niches"]}}
    json.dump(idx[o.batch], sys.stdout, indent=1); print()
    json.dump(idx, open(master, "w"), indent=1)
    print(f"skipped dupes: {skipped} (of {len(skip)} listed)  -> {out}")

if __name__ == "__main__": main()
