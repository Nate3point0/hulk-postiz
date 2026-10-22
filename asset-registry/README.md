# Asset Registry — Mixboard batches → Pinterest / Social / Video → Postiz + local pipeline

Originals never move. Each batch gets symlink lanes + a registry with absolute paths.

```
~/HULK/asset-registry/
  MASTER_INDEX.json            # every batch: src, count, lane totals (Postiz/BrainVault/ComfyUI read this)
  batch2/registry.csv|json     # id, abs_path, WxH, lanes, niche, funnel, postiz_media_id, status
  batch2/pinterest/<niche>/    # 2:3 + 4:5 portrait → pins
  batch2/social/<niche>/       # 1:1, 4:5, 16:9 → IG/FB/X/LinkedIn feed
  batch2/video/<niche>/        # 9:16 + ≥1920px → Reels/TikTok/Shorts/Ken-Burns b-roll
```

## Run (on the Mac, drive mounted)
```bash
pip3 install pillow
L="$HOME/Documents/Codex/2026-09-25/volumes-music-mixboard-second-batch/outputs/Mixboard Batch 2 Asset Library"
python3 route_batch.py --src "/Volumes/MUSIC/MIXBOARD/SECOND BATCH" --batch batch2 \
  --inventory "$L/asset-inventory.csv" --duplicates "$L/duplicate-report.csv"
# Batch 1 into the same index:
python3 route_batch.py --src "/Volumes/MUSIC/MIXBOARD/<FIRST BATCH>" --batch batch1
```

## Stage into Postiz (media upload only — posts stay human-reviewed)
```bash
export POSTIZ_URL=http://100.106.11.18:<postiz-port> POSTIZ_API_KEY=...
python3 postiz_stage.py --registry ~/HULK/asset-registry/batch2/registry.csv --lane pinterest --niche music-production --limit 25
```
Writes `postiz_media_id` / `postiz_url` back into registry.csv → use those in `/public/v1/posts`.

Niches + funnel mapping: edit `niches.json`.
Duplicates: only the first file of each group from `duplicate-report.csv` is routed; nothing deleted.
