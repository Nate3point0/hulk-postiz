---
name: hulk-postiz
description: >
  Operate and control the Postiz social scheduling pipeline via MCP, REST API, and Agents CLI.
  Covers media staging, post creation, update workarounds, dynamic platform metadata (Reddit
  flairs, YouTube playlists), and async asset reconnection for TikTok/Instagram. Integrates
  with the HULKCLAW content stack (Metricool, Systeme.io, ComfyUI, hulk-music-factory).

  Activate when the user says: "post this to all platforms", "schedule this drop", "push to
  Postiz", "upload to Postiz", "hulk-postiz", "list scheduled posts", "delete a post", "update
  a post", "sync missing TikTok post", "get my integrations", "Postiz 401", "SSE dropout",
  "Postiz rate limit", or any variant of scheduling or managing social posts via Postiz. Also
  fire when routing audio/video from hulk-music-factory or ComfyUI to social platforms, or
  when asked about the Metricool + Postiz dual-post pattern.
---

# hulk-postiz

Operates the Postiz social scheduling pipeline across three interfaces. Default flow for any
content drop: **upload media → get integrations → create post → verify queue**.

---

## Live Channel Status (as of 2026-08-08)

| Channel | Status | Notes |
|---------|--------|-------|
| Facebook (Motocity) | 🟢 LIVE | |
| Instagram | 🟢 LIVE | |
| Threads | 🟢 LIVE | |
| YouTube (MOTOCITY) | 🟢 LIVE | |
| Pinterest (motocty) | 🟢 LIVE | |
| Tumblr (natefunkadelic) | 🟢 LIVE | |
| Discord | 🟢 LIVE | |
| X/Twitter | 🔴 BLOCKED | API pay-per-post; credits depleted (402). Fix: buy credits in X Developer Console → Billing → Credits. No code changes needed. |
| Reddit | ⏸ PARKED | Needs Reddit API approval |
| TikTok | ⏸ PARKED | Needs domain verification + demo video review |
| GMB | ⏸ PARKED | No business profile on Google account |
| Medium | ⏸ PARKED | No longer issues API tokens |

**Default target set for all multi-platform posts:** FB + IG + Threads + YouTube + Pinterest + Tumblr + Discord (7 channels).
Credentials live at `hulk:~/postiz/docker-compose.yml`.

---

## Invoke

```
/hulk-postiz [status|schedule|upload|list|delete|update|connect|sync-missing]
```

---

## Architecture

```
Content Stack (hulk-music-factory / ComfyUI FLUX / ffmpeg)
        │
        ▼
  hulk-postiz skill
   ┌────┴────────────────────────────────┐
   │  MCP (SSE)  │  REST API  │  CLI     │
   │  tool calls │  /public/  │  postiz  │
   └────┬────────────────────────────────┘
        │
        ▼
  Postiz Backend (NestJS + Temporal)
        │
        ▼
  Social Platforms (IG, TikTok, X, YouTube, Reddit…)
```

**Key rule:** Media must be staged (`upload`) before any post creation call. Raw file paths
and unverified external URLs are rejected by all three interfaces.

---

## Interface 1 — MCP (SSE)

### Connection

| Setting | Value |
|---------|-------|
| Endpoint | `https://api.postiz.com/mcp` or `https://api.postiz.com/mcp/:apiKey` |
| Transport | HTTP + Server-Sent Events (SSE) |
| Auth | `Authorization: Bearer <API_KEY>` header |
| Proxy req | Must support `Transfer-Encoding: chunked` — prevents SSE dropout |

### Tool Schemas

#### `get-integrations`
```json
{ "inputs": {} }
// Returns: array of { id, provider, accessState }
```

#### `upload-file`
```json
{ "inputs": { "filePath": "string (local path or verified URL)" } }
// Returns: { fileId: string, publicUrl: string }
```

#### `create-post`
```json
{
  "inputs": {
    "content":       "string (required)",
    "integrations":  ["UUID", "…"],
    "status":        "'draft' | 'scheduled' | 'now'  (optional, default: scheduled)",
    "scheduledDate": "ISO 8601 string (optional)",
    "images":        ["verified postiz URL"]  // from upload-file output only
  }
}
// Returns: { status: string, postId: string }
```

#### `list-posts`
```json
{ "inputs": { "startDate": "ISO 8601", "endDate": "ISO 8601" } }
// Returns: array of post records
```

---

## Interface 2 — REST API

**Base URL:** `https://api.postiz.com` (cloud) or `http://localhost:3000` (self-hosted)
**Auth header:** `Authorization: Bearer <API_KEY>`

### Rate Limits

| Instance | Limit |
|----------|-------|
| Self-hosted | 90 POST /posts per hour |
| Cloud | 100 POST /posts per hour |

**Optimization:** Bundle multiple posts in one request payload array.

### Endpoints

#### Upload media (always first)
```
POST /public/v1/upload
Content-Type: multipart/form-data
Body: file=<binary>

Response: { id: string, url: string }
```

#### Create / schedule post
```
POST /public/v1/posts
Content-Type: application/json

{
  "type": "schedule",
  "date": "2026-08-06T14:00:00.000Z",
  "shortLink": false,
  "tags": [],
  "posts": [
    {
      "integration": { "id": "your-integration-uuid" },
      "value": [
        {
          "content": "Hello from the Postiz API! 🚀",
          "image": [
            { "id": "img-123", "path": "https://uploads.postiz.com/cover.jpg" }
          ]
        }
      ],
      "settings": {
        "__type": "instagram",
        "post_type": "post"
      }
    }
  ]
}

Response: { id: string, status: string }
```

**Critical fields:**
- `type` (required): `"schedule"` or `"now"`
- `shortLink` (required): `true` or `false`
- `tags` (required): array (can be empty `[]`)
- `integration` is a **nested object** `{ "id": "UUID" }` — NOT flat `integrationId`
- Content + media live inside `value: [{ content, image }]` — NOT top-level
- Images inside `value[]` use `{ id, path }` objects
- Platform settings use `settings: { "__type": "platform", ... }`

#### List posts
```
GET /public/v1/posts?startDate=ISO&endDate=ISO&customer=optional

// NOTE: No server-side filtering by integrationId — filter client-side
```

#### Delete post
```
DELETE /public/v1/posts/:id
// Cancels pending Temporal workflows
```

### Update Workaround (no PUT/PATCH endpoint)

The REST API has no update endpoint. Follow this 5-step sequence:

```
1. GET    /public/v1/posts?startDate=…&endDate=…   → find target record
2. DELETE /public/v1/posts/:id                      → cancel workflow
3. Strip server fields: id, createdAt, updatedAt, status
4. Modify payload locally
5. POST   /public/v1/posts                          → resubmit as new
```

---

## Interface 3 — Agents CLI

**Install:** `npm install -g postiz` (alias for `@postiz/cli`)
**Output:** All commands return structured JSON (machine-parseable).

### Pre-flight Auth Check (run first in any automated loop)
```bash
postiz auth:status
# exit code 1 = auth failed → halt execution loop, run postiz auth:login
```

### Commands

| Command | Args | Output |
|---------|------|--------|
| `postiz integrations:settings <id>` | UUID | Platform schema (char limits, validation rules) |
| `postiz integrations:trigger <id> <tool>` | `-d '{}' ` JSON params | Dynamic data (subreddits, flairs, playlists) |
| `postiz upload <file>` | local path | `{ id, url }` |
| `postiz posts:create` | `-c "text" -s "ISO" -i "UUID" -m "url"` | `{ id }` |
| `postiz posts:missing <id>` | post ID | Unlinked external post candidates |
| `postiz posts:connect <id> --release-id <ext>` | IDs | Binds DB record to platform ID |

### Dynamic Metadata (Reddit, YouTube)
```bash
# Fetch before scheduling — required for Reddit and YouTube
postiz integrations:trigger <UUID> list_subreddits
postiz integrations:trigger <UUID> list_flairs -d '{"subreddit":"beats"}'
postiz integrations:trigger <UUID> list_playlists
# Use returned values in posts:create payload
```

### Async Asset Reconnection (TikTok / Instagram)

Short-form video platforms return no immediate publication ID. Restore analytics polling with:
```bash
postiz posts:missing <local_post_id>
# → returns external_id candidates

postiz posts:connect <local_post_id> --release-id <external_id>
# → restores analytics polling
```

---

## Platform Settings Reference

| Platform | `__type` | Required Settings |
|---|---|---|
| X/Twitter | `x` | `who_can_reply_post`: `"everyone"` \| `"following"` \| `"mentions"` |
| Instagram | `instagram` | `post_type`: `"post"` \| `"story"` \| `"reel"` |
| LinkedIn | `linkedin` | `companyId` (optional), `carousel` (optional) |
| YouTube | `youtube` | `title`, `type`, `tags`, `playlistId` (optional) |
| Reddit | `reddit` | `subreddit`, `title`, `flair` (optional) |
| TikTok | `tiktok` | `privacy`, `duet`, `stitch` |
| Pinterest | `pinterest` | `board`, `section` (optional) |
| Facebook | `facebook` | `pageId` (via `integrations:trigger`) |
| Medium | `medium` | `title`, `subtitle`, `tags` |

---

## HULKCLAW Integration Patterns

### Content Stack → Postiz Pipeline
```
hulk-music-factory  →  audio/mp3
ComfyUI TI2V        →  animated mp4
hulk-audio-qc       →  QC gate
         │
         ▼
postiz upload <file>          →  { id, url }
         │
         ▼
postiz posts:create           →  scheduled across all platform UUIDs
```

### Metricool + Postiz Dual-Post
- **Metricool MCP** (`mcp__metricool__createScheduledPost`): analytics-tracked posts on
  connected accounts (20-post/month budget — use selectively).
- **Postiz REST/CLI**: multi-platform batching, draft management, platforms outside Metricool.
- Offset by **5–10 min** between tools to avoid duplicate-detection flags.

### Systeme.io Affiliate Link Injection
Before `create-post` / `posts:create`, append the Systeme.io affiliate link (60% LTV) to
the `content` string. Pattern: `\n\n👉 [link]` appended after main copy.

---

## Agent Decision Tree

```
Task: "Post this audio drop to all platforms"

1. hulk-audio-qc                → QC pass?
2. postiz upload <mp3/mp4>      → get verified URL
3. get-integrations             → list active channel UUIDs
   ⚠ Filter to LIVE channels only (see Live Channel Status table above):
     FB / IG / Threads / YouTube / Pinterest / Tumblr / Discord
     Skip X (blocked), Reddit/TikTok/GMB/Medium (parked)
4. For YouTube:
     integrations:trigger       → fetch playlist IDs
5. create-post / posts:create   → schedule across 7 LIVE UUIDs
6. list-posts (next 7d)         → confirm in queue
```

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Bad/missing API key | Check `Authorization: Bearer` header |
| `Media rejected` | Raw path or unverified URL | Run `upload` first, use returned URL |
| `429 Rate limit` | >90–100 posts/hr | Bundle posts in single payload; back off 60s |
| `SSE dropout` | Proxy lacks chunked encoding | Enable `Transfer-Encoding: chunked` |
| `exit code 1` (CLI) | Auth expired | Run `postiz auth:login` before loop |
| Missing TikTok/IG ID | Async platform | `posts:missing` → `posts:connect` |
| Double-post on retry | Hash collision edge case | Check idempotency: platformId+content+timestamp |
| `500` on DELETE | Known bug: missing post ID may return 500 instead of 404 | Same as 404 — safe to ignore if post already deleted |
| `413 Payload Too Large` | Base64-inlined images >50MB | Always use `upload` endpoint first; never inline large media |

---

## Advanced Features

### RSS Auto-Post (Team+ plans)
Feed any RSS URL → Postiz auto-converts to social posts. Use for:
- Blog posts → X/LinkedIn threads
- YouTube uploads → community posts
- Podcast releases → multi-platform announcements

### Evergreen / Repeat Posts
Any post can auto-repeat on cadence. Killer for:
- Sample pack drops (weekly rotation)
- Affiliate link posts (evergreen revenue)
- Content reminder loops

### AI Copilot (Built-in)
Postiz has native AI copilot for text, image, and video generation. Can reduce HULKCLAW →
Postiz handoff complexity for simple text-only posts.

### n8n / Make.com / Zapier Nodes
Native integration nodes available. Use for:
- Replacing custom REST calls with no-code flows
- Triggering Postiz from Systeme.io form submissions
- Auto-posting when new products hit eBay store

---

## Markdown Metadata
- **Last updated**: 2026-08-05
- **Maintainer**: Nate's AI System
- **Intended audience**: Agent / AI Training
- **Format version**: SCD v2.0
- **Research source**: Official Postiz API docs (api.postiz.com/docs), Postiz CLI repo, community knowledge
