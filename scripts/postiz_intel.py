#!/usr/bin/env python3
"""Pull every analytics signal Postiz exposes and write a tuning report.

Run on Hulk (or anywhere that can reach the Postiz backend):

    POSTIZ_URL=http://localhost:3000 POSTIZ_API_KEY=xxx python3 scripts/postiz_intel.py --days 30

Outputs (in ./intel/<date>/):
  raw.json      - every API response, untouched (baseline — never delete)
  posts.csv     - one row per post: channel, weekday, hour, format, hook, has_cta, metrics
  report.md     - winners, losers, best slots per channel, what to record next

Stdlib only. Endpoints that 404 on your Postiz version are skipped, not fatal.
"""
import argparse, csv, datetime as dt, json, os, re, statistics, sys, urllib.error, urllib.request
from collections import defaultdict

BASE = os.environ.get("POSTIZ_URL", "http://localhost:3000").rstrip("/")
KEY = os.environ.get("POSTIZ_API_KEY", "")
LIVE = {"facebook", "instagram", "instagram-standalone", "threads", "youtube", "pinterest", "tumblr", "discord"}
CTA = re.compile(r"(👉|link in bio|https?://|systeme\.io|gumroad|grab|download|get it|shop|free )", re.I)
ENGAGE_KEYS = ("like", "comment", "share", "save", "repost", "reply", "reaction", "click", "engage")
REACH_KEYS = ("impression", "view", "reach", "play")


def get(path):
    for prefix in ("/public/v1", "/api/public/v1"):
        req = urllib.request.Request(BASE + prefix + path, headers={"Authorization": KEY})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read() or "null")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                sys.exit("401 — check POSTIZ_API_KEY (Settings → Public API)")
            if e.code in (404, 405):
                continue
            print(f"  ! {path}: HTTP {e.code}", file=sys.stderr)
            return None
        except urllib.error.URLError as e:
            sys.exit(f"Cannot reach {BASE}: {e.reason}")
    return None


def sum_metric(blob, keys):
    """Postiz analytics come back as [{label, data:[{total,date}]}] — sum matching labels."""
    total = 0.0
    for series in blob if isinstance(blob, list) else []:
        label = str(series.get("label", "")).lower()
        if any(k in label for k in keys):
            for pt in series.get("data", []):
                try:
                    total += float(pt.get("total", 0))
                except (TypeError, ValueError):
                    pass
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    if not KEY:
        sys.exit("Set POSTIZ_API_KEY")

    now = dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=a.days)
    out = os.path.join("intel", now.strftime("%Y-%m-%d"))
    os.makedirs(out, exist_ok=True)
    raw = {}

    integrations = get("/integrations") or []
    raw["integrations"] = integrations
    chan = {i["id"]: i for i in integrations if isinstance(i, dict)}
    print(f"{len(chan)} channels")

    raw["channel_analytics"] = {}
    for cid, i in chan.items():
        raw["channel_analytics"][cid] = get(f"/analytics/{cid}?date={a.days}")

    posts = get(f"/posts?startDate={start.isoformat()}&endDate={now.isoformat()}") or []
    posts = posts.get("posts", posts) if isinstance(posts, dict) else posts
    raw["posts"] = posts
    raw["post_analytics"] = {}

    rows = []
    for p in posts:
        pid = p.get("id")
        integ = p.get("integration") or {}
        cid = integ.get("id") or p.get("integrationId")
        provider = (integ.get("providerIdentifier") or chan.get(cid, {}).get("identifier") or "?").lower()
        pa = get(f"/posts/{pid}/analytics?date={a.days}") if pid else None
        raw["post_analytics"][pid] = pa
        when = dt.datetime.fromisoformat(str(p.get("publishDate", now.isoformat())).replace("Z", "+00:00"))
        text = re.sub(r"<[^>]+>", " ", p.get("content") or "").strip()
        eng, reach = sum_metric(pa, ENGAGE_KEYS), sum_metric(pa, REACH_KEYS)
        rows.append({
            "id": pid, "channel": provider, "name": integ.get("name", ""),
            "state": p.get("state") or p.get("status"), "weekday": when.strftime("%a"), "hour_utc": when.hour,
            "has_media": bool(p.get("image")), "has_cta": bool(CTA.search(text)),
            "hook": text.split("\n")[0][:90], "chars": len(text),
            "reach": reach, "engagement": eng, "eng_rate": round(eng / reach, 4) if reach else 0,
        })

    json.dump(raw, open(os.path.join(out, "raw.json"), "w"), indent=2, default=str)
    if rows:
        with open(os.path.join(out, "posts.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)

    # ---- report ----
    L = [f"# Postiz Intel — last {a.days} days ({now:%Y-%m-%d})", "",
         f"Posts: {len(rows)} · Channels: {len(chan)}", ""]
    L += ["## Channel health", "| Channel | Name | Status |", "|---|---|---|"]
    for i in chan.values():
        bad = i.get("disabled") or i.get("refreshNeeded") or i.get("inBetweenSteps")
        L.append(f"| {i.get('identifier')} | {i.get('name')} | {'🔴 FIX' if bad else '🟢'} |")

    by = defaultdict(list)
    for r in rows:
        by[r["channel"]].append(r)
    L += ["", "## Per channel", "| Channel | Posts | Avg reach | Avg eng | Eng rate | CTA posts eng vs non-CTA | Best slot (UTC) |", "|---|---|---|---|---|---|---|"]
    for c, rs in sorted(by.items()):
        m = lambda k, s=rs: round(statistics.mean(x[k] for x in s), 1) if s else 0
        cta = [x["engagement"] for x in rs if x["has_cta"]]; non = [x["engagement"] for x in rs if not x["has_cta"]]
        slots = defaultdict(list)
        for x in rs:
            slots[(x["weekday"], x["hour_utc"])].append(x["engagement"])
        best = max(slots.items(), key=lambda kv: statistics.mean(kv[1]))[0] if slots else ("-", "-")
        L.append(f"| {c} | {len(rs)} | {m('reach')} | {m('engagement')} | {m('eng_rate')} | "
                 f"{round(statistics.mean(cta),1) if cta else '-'} vs {round(statistics.mean(non),1) if non else '-'} | {best[0]} {best[1]}:00 |")

    ranked = sorted(rows, key=lambda r: (r["engagement"], r["reach"]), reverse=True)
    L += ["", "## Top 5 — make more of these (re-record the hook, new angle)"]
    L += [f"- **{r['channel']}** {r['engagement']:.0f} eng / {r['reach']:.0f} reach — “{r['hook']}”" for r in ranked[:5]]
    L += ["", "## Bottom 5 — do NOT delete (baseline data); retire the angle"]
    L += [f"- **{r['channel']}** {r['engagement']:.0f} eng — “{r['hook']}”" for r in ranked[-5:]]
    failed = [r for r in rows if str(r["state"]).upper() in ("ERROR", "FAILED")]
    if failed:
        L += ["", f"## ⚠ {len(failed)} failed posts — check channel tokens"]
        L += [f"- {r['channel']}: {r['hook']}" for r in failed[:10]]
    no_data = sum(1 for r in rows if not r["reach"] and not r["engagement"])
    if no_data:
        L += ["", f"> {no_data} posts returned no metrics. For IG/TikTok run `postiz posts:missing <id>` → `posts:connect` to relink."]

    open(os.path.join(out, "report.md"), "w").write("\n".join(L) + "\n")
    print(f"Wrote {out}/report.md, posts.csv, raw.json")


if __name__ == "__main__":
    main()
