# hulk-postiz

> Triple-interface Postiz social scheduling plugin for AI agents (MCP · REST · CLI)

**Price: $9.99** | [Buy on Gumroad](https://gumroad.com/l/hulk-postiz) | [View on MCPmarket](https://mcpmarket.com)

---

## What It Does

You have content. You have platforms. `hulk-postiz` is the bridge between your AI workflow and your Postiz social scheduling pipeline.

**Three interfaces — one plugin:**

| Interface | Best For |
|---|---|
| MCP (SSE) | AI agent tool calls inside Claude, Cursor, VS Code |
| REST API | Batch operations, automation scripts |
| CLI | Auth checks, dynamic metadata, async recovery |

---

## Quick Install

```bash
git clone https://github.com/Nate3point0/hulk-postiz
cd hulk-postiz
```

**Add to Claude Code:**
Copy `SKILL.md` to `~/.claude/skills/hulk-postiz/SKILL.md`

**Requirements:** Postiz instance (self-hosted or cloud), API key from Postiz Settings

---

## MCP Tools

```
get-integrations    → list connected social channels
upload-file         → stage media before posting
create-post         → schedule or publish immediately  
list-posts          → review your queue
```

---

## The Core Flow

```
1. upload-file (stage your media)
2. get-integrations (get channel IDs)
3. create-post (schedule with channel IDs + media ID)
4. list-posts (verify)
```

**Never skip step 1.** Posting without staged media is the #1 cause of failures.

---

## Platform Coverage

- **Facebook, Instagram, Threads, YouTube** — standard post creation
- **Reddit** — dynamic subreddit + flair fetching
- **TikTok/Instagram** — async post reconnection (no immediate publication ID)
- **Discord** — webhook-based posting
- **Pinterest, Tumblr** — standard scheduling

---

## Error Handling

| Error | Fix |
|---|---|
| 401 Unauthorized | Check POSTIZ_API_KEY in your Postiz Settings |
| 429 Rate Limit | Bundle posts — max 90-100/hour |
| SSE Dropout | Re-invoke skill — SSE reconnects automatically |
| Media Rejected | Check format: MP4/MOV ≤4GB, JPG/PNG ≤10MB |
| Missing Post ID (TikTok/IG) | Run `posts:connect` after 2-5 min delay |

---

## v2.0 Features

- RSS auto-posting — turn any feed into a scheduled queue
- Evergreen queues — recycle your best content automatically
- AI copilot — caption generation inside the pipeline
- n8n + Make.com nodes

---

## Stack Integration

Works with: `hulk-music-factory` · `ComfyUI FLUX` · `ffmpeg` · `Metricool` · `Systeme.io`

---

**License:** Personal use. Not for redistribution.  
**Support:** Open an issue on this repo.  
**Built by:** [Nate3point0](https://github.com/Nate3point0) / HULKCLAW Digital

## Video pipeline (`media-out/pipeline.sh`)

`render.js` (Playwright → silent MP4) → ffmpeg mix (VO + ducked music, -14 LUFS) → optional DaVinci Resolve polish (M4, Studio) → Postiz upload.

```
./media-out/pipeline.sh                    # render + mix (headless, Hulk or M4)
./media-out/pipeline.sh --skip-render      # mix only
./media-out/pipeline.sh --skip-render --resolve   # + build Resolve timeline with SFX markers
POSTIZ_API_KEY=... ./media-out/pipeline.sh --upload-only   # upload <NAME>_FINAL.mp4 as-is
```
