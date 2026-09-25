#!/usr/bin/env python3
"""Route a Mixboard image batch into Pinterest / Social / Video lanes + niche/funnel tags.

Run ON THE MAC (Hulk or MacBook) where the drive is mounted. Never moves/copies originals:
it builds symlink "lanes" + a master registry (CSV + JSON) with absolute paths that
Postiz, ComfyUI/video pipeline, and BrainVault can all read.

  python3 route_batch.py --src "/Volumes/MUSIC/MIXBOARD/SECOND BATCH" --batch batch2 \
      --inventory ".../Mixboard Batch 2 Asset Library/asset-inventory.csv" \
      --duplicates ".../Mixboard Batch 2 Asset Library/duplicate-report.csv"
"""
import argparse, csv, json, os, re, sys
from pathlib import Path

IMG = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tif", ".tiff"}
try:
    from PIL import Image
except ImportError:
    Image = None
    print("! Pillow missing -> `pip3 install pillow` for aspect-ratio routing (falling back to keywords)", file=sys.stderr)

def dims(p):
    if not Image: return (0, 0)
    try:
        with Image.open(p) as im: return im.size
    except Exception: return (0, 0)

def lanes_for(w, h, text):
    """Aspect-ratio first, keywords as backup. An image can land in several lanes."""
    out = set()
    if w and h:
        r = w / h
        if r <= 0.70: out |= {"pinterest", "video"}          # 2:3 pins, 9:16 reels/tiktok/shorts
        elif r <= 0.85: out |= {"social", "pinterest"}       # 4:5 IG/FB feed
        elif r <= 1.2: out.add("social")                     # 1:1
        else: out |= {"video", "social"}                     # 16:9 youtube/b-roll, cropped feed
        if max(w, h) >= 1920: out.add("video")               # enough res for Ken-Burns pans
    t = text.lower()
    for kw, lane in (("pin", "pinterest"), ("print", "pinterest"), ("reel", "video"), ("video", "video"),
                     ("background", "video"), ("ad", "social"), ("social", "social"), ("landing", "social")):
        if re.search(rf"\b{kw}", t): out.add(lane)
    return sorted(out or {"social"})

def niche_for(text, cfg):
    t = text.lower()
    for name, n in cfg["niches"].items():
        if any(re.search(rf"\b{re.escape(k)}", t) for k in n["keywords"]): return name
    return cfg["default_niche"]

def load_inventory(path):
    """Map filename -> row text (category/intended use) from the Codex inventory, whatever its columns."""
    m = {}
    if path and Path(path).exists():
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                key = next((v for k, v in row.items() if v and Path(v).suffix.lower() in IMG), None)
                if key: m[Path(key).name] = " ".join(v for v in row.values() if v)
    return m

def load_dupes(path):
    """Keep first file of each dup group; skip the rest from lanes (not deleted)."""
    skip, seen = set(), {}
    if path and Path(path).exists():
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                g = next((v for k, v in row.items() if "group" in k.lower() or "hash" in k.lower()), None)
                fn = next((v for v in row.values() if v and Path(v).suffix.lower() in IMG), None)
                if g and fn:
                    if g in seen: skip.add(Path(fn).name)
                    else: seen[g] = fn
    return skip

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--src", required=True)
    a.add_argument("--batch", default="batch2")
    a.add_argument("--inventory"); a.add_argument("--duplicates")
    a.add_argument("--out", default=os.path.expanduser("~/HULK/asset-registry"))
    a.add_argument("--niches", default=str(Path(__file__).with_name("niches.json")))
    o = a.parse_args()
    cfg = json.load(open(o.niches))
    inv, skip = load_inventory(o.inventory), load_dupes(o.duplicates)
    out = Path(o.out) / o.batch
    rows = []
    for p in sorted(Path(o.src).rglob("*")):
        if p.suffix.lower() not in IMG or p.name.startswith("."): continue
        if p.name in skip: continue
        w, h = dims(p)
        text = f"{p.relative_to(o.src)} {inv.get(p.name, '')}"
        lanes, niche = lanes_for(w, h, text), niche_for(text, cfg)
        rid = f"{o.batch}-{len(rows)+1:04d}"
        for lane in lanes:  # symlink lanes: /out/<lane>/<niche>/<id>__name
            d = out / lane / niche; d.mkdir(parents=True, exist_ok=True)
            link = d / f"{rid}__{p.name}"
            if not link.exists(): link.symlink_to(p.resolve())
        rows.append({"id": rid, "batch": o.batch, "abs_path": str(p.resolve()), "filename": p.name,
                     "width": w, "height": h, "lanes": "|".join(lanes), "niche": niche,
                     "funnel": cfg["niches"][niche]["funnel"], "funnel_url": cfg["niches"][niche]["funnel_url"],
                     "codex_category": inv.get(p.name, "")[:200], "postiz_media_id": "", "postiz_url": "",
                     "status": "staged"})
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "registry.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["id"]); wr.writeheader(); wr.writerows(rows)
    json.dump(rows, open(out / "registry.json", "w"), indent=1)
    # master index across all batches (batch1 + batch2 + ...) for Postiz / BrainVault / ComfyUI
    master = Path(o.out) / "MASTER_INDEX.json"
    idx = json.load(open(master)) if master.exists() else {}
    idx[o.batch] = {"src": o.src, "registry": str(out / "registry.csv"), "count": len(rows),
                    "lanes": {l: sum(l in r["lanes"] for r in rows) for l in ("pinterest", "social", "video")}}
    json.dump(idx, open(master, "w"), indent=1)
    print(json.dumps(idx[o.batch], indent=1)); print(f"skipped dupes: {len(skip)}  -> {out}")

if __name__ == "__main__": main()
