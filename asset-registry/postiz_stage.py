#!/usr/bin/env python3
"""Upload a lane (e.g. pinterest/music-production) to Postiz and write media IDs back to registry.csv.
  POSTIZ_URL=http://100.106.11.18:5000 POSTIZ_API_KEY=... python3 postiz_stage.py \
      --registry ~/HULK/asset-registry/batch2/registry.csv --lane pinterest --niche music-production --limit 25
Only uploads (media staging). Post creation stays a human-reviewed step (publication firewall)."""
import argparse, csv, json, os, subprocess
a = argparse.ArgumentParser()
a.add_argument("--registry", required=True); a.add_argument("--lane", required=True)
a.add_argument("--niche"); a.add_argument("--limit", type=int, default=25)
o = a.parse_args()
base, key = os.environ["POSTIZ_URL"].rstrip("/"), os.environ["POSTIZ_API_KEY"]
rows = list(csv.DictReader(open(o.registry)))
n = 0
for r in rows:
    if n >= o.limit: break
    if o.lane not in r["lanes"].split("|") or r["postiz_media_id"]: continue
    if o.niche and r["niche"] != o.niche: continue
    res = subprocess.run(["curl", "-sS", "-X", "POST", f"{base}/public/v1/upload", "-H", f"Authorization: {key}",
                          "-F", f"file=@{r['abs_path']}"], capture_output=True, text=True)
    try:
        j = json.loads(res.stdout); r["postiz_media_id"], r["postiz_url"] = j.get("id", ""), j.get("path") or j.get("url", "")
        r["status"] = "in_postiz"; n += 1; print("OK", r["id"], r["postiz_url"])
    except Exception:
        print("FAIL", r["id"], res.stdout[:200] or res.stderr[:200])
with open(o.registry, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(f"uploaded {n}")
