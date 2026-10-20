# HULKCLAW Social Operating Plan v1 — "One Drop, Seven Channels"

Locked plan. Runs on the Postiz pipeline documented in `SKILL.md`. Tuned every Sunday from
`scripts/postiz_intel.py` output — numbers win arguments, not vibes.

---

## 0. Rules (what we do NOT do)

- **Never mass-delete old posts.** Every post is baseline analytics. Deleting "non-CTA" posts
  or "last week's data" wipes the only data that tells us what works. Low performers get
  their *angle* retired, not their record.
- **No apology posts, no "sorry I've been gone."** Just post.
- **One product anchor per 14-day sprint.** Every post points to it (directly or as proof).
- **80/20 content split:** 80% value/proof/story, 20% hard CTA. All-CTA feeds get throttled
  by the algorithm and ignored by humans.
- **Affiliate / Systeme.io link goes in the last line** (`\n\n👉 link`), never the hook.

## 1. Channels & roles (7 live)

| Channel | Role | Format | Cadence |
|---|---|---|---|
| Instagram | Discovery + DM sales | Reel 15–45s, carousel | 1 Reel/day + 2 carousels/wk |
| YouTube | Search + Shorts discovery | Short daily, 1 long-form/wk | 1/day + 1/wk |
| Facebook (Motocity) | Warm audience, groups | Same Reel + text post | 1/day |
| Threads | Voice, hot takes, build-in-public | Text 1–3 lines | 2/day |
| Pinterest | Evergreen traffic → funnel | Vertical pin → Systeme.io | 3/day (evergreen queue) |
| Tumblr | SEO backlink / archive | Repost + link | 1/day (auto) |
| Discord | Community + buyers | Drop announcements, behind-scenes | 3/wk |

Parked until fixed: X (buy credits), Reddit (API approval), TikTok (domain verify). TikTok
is the single highest-upside fix — do the demo video for review this week.

## 2. Content pillars (rotate daily)

| Day | Pillar | Purpose |
|---|---|---|
| Mon | **Build-in-public** — "I built X with AI in Y minutes" | Authority |
| Tue | **Tutorial** — one tool, one result, 30s | Saves/shares |
| Wed | **Proof** — screen of sale, result, testimonial, before/after | Trust |
| Thu | **Music / creative drop** (hulk-music-factory, ComfyUI) | Reach |
| Fri | **Offer day** — the anchor product, hard CTA | Revenue |
| Sat | **Story** — the underdog grind (3 D's) | Connection |
| Sun | **Recap + intel** — "what worked this week" | Retention; run intel script |

## 3. The daily machine (60 min total, on your side)

```
07:00  Record  — 1 batch session covers 2–3 days (see §4)
       ↓ drop raw clips in Hulk capture folder
Hulk   ffmpeg cut → captions → 9:16 + 1:1 + pin variants
       ↓
Local  Ollama rebuilds copy in your voice → HUMAN REVIEW (you, 5 min)
       ↓
Postiz upload → posts:create to 7 LIVE UUIDs, staggered (below)
       ↓
Sunday postiz_intel.py → report.md → adjust §2/§5
```

**Posting windows (start points — intel script replaces these after 2 weeks):**
IG/FB 11:30 & 19:00 local · YouTube Short 17:00 · Threads 08:00 & 21:00 ·
Pinterest spread 3×/day · Discord 18:00. Stagger channels 5–10 min apart.

## 4. What to RECORD live (shot list)

Batch these on Mon + Thu. Phone vertical, face in frame first 1 second, talk to one person.

### Every session — 6 clips
1. **3 hooks, 3 seconds each** for the same video (A/B the hook; post the rest as Threads text).
   - "I made $__ from a tool I built in 20 minutes. Here's the tool."
   - "Stop paying for ___. I built my own with AI."
   - "This is my entire business running on a Mac Mini."
2. **Screen-record + voiceover (45s):** Hulk running a job end-to-end (prompt → output → posted).
3. **Talking head (30s):** one lesson from this week, no script, one take.
4. **Offer walk-through (60s):** the anchor product — problem, click-through, result, price.
5. **Behind-the-scenes b-roll (10–20s × 3):** hands, desk, Cricut/merch, Mac Mini lights.
   Silent — music gets laid over for Reels/Shorts.
6. **Music clip (15s):** a loop from hulk-music-factory playing over the visual — doubles as
   sample-pack promo.

### Weekly — 1 long-form (8–12 min, YouTube)
Full build: "Building a $27 product with AI, start to sale." Cut into 5+ Shorts.

### Live stream (1×/week, 30–45 min, YouTube + FB simultaneous)
Build something live, answer comments, pitch the anchor at minute 20 and at the end.
Recording = next week's Shorts source.

## 5. Scorecard (from `report.md`)

| Metric | Kill | Keep | Double down |
|---|---|---|---|
| Eng rate (eng/reach) | <1% | 1–4% | >4% |
| Link clicks / post (Systeme.io) | 0 over 5 posts | 1–5 | >5 |
| Saves (IG/Pinterest) | — | — | Any post with saves > likes/10 → remake as carousel |

Sunday ritual (15 min): run the script, take **Top 5** → re-record their hooks with new angle,
drop the **Bottom 5** angle from rotation, move posting times to the reported best slots.

## 6. 48-hour launch sequence

1. Run `scripts/postiz_intel.py --days 90` → establish baseline (don't delete anything first).
2. Pick the anchor product (the one with the most clicks/sales in the baseline).
3. Batch-record §4 session #1.
4. Schedule 7 days × 7 channels in Postiz; set Pinterest + Tumblr to evergreen repeat.
5. Submit TikTok domain verification + demo video.
