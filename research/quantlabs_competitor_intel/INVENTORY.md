# QuantLabsNet Competitor Intel — Phase 1 Inventory

**Generated:** 2026-04-18
**Purpose:** Extract every valuable idea from Bryan Downing's QuantLabsNet site + YouTube channel that could upgrade GTOS.
**Scope filters (from CEO):** Skip matlab, crypto/bitcoin/ethereum, pure-options content, careers/salaries/interviews. Focus on MT5-accessible instruments (forex majors, NAS100, US30, XAUUSD). Cast wide, filter later in synthesis.

## Blog (quantlabsnet.com)

**Total unique articles in sitemap:** 1,474 (dated 2025-03-20 → 2026-04-18)

Tagging via URL-slug keyword matching (see `scripts/quantlabs_build_blog_manifest.py`):

| Tag | Count | Handling |
|-----|-------|----------|
| PRIORITY | 132 | MT5/IBKR/forex/gold/NAS/claude/prop-firm slugs — all extract |
| KEEP | 1,059 | Generic AI/trading/strategy — top 168 most-recent extract |
| JOBS | 63 | Careers/salaries/interviews — excluded |
| OPTIONS | 26 | Pure options-only — excluded |
| SKIP | 194 | matlab / crypto / bitcoin / ethereum / polymarket / stablecoin — excluded |

**Phase 2b extraction scope:** 300 articles (132 PRIORITY + top 168 KEEP by lastmod DESC)
**Split:** 10 round-robin batches of 30 URLs each → `blog_batches/batch_NN.txt`
**Output:** `blog_extractions/batch_NN.md`

## YouTube (channel @quantlabs, 14.1K subs)

### Playlist "Quant Trading Live Report" (CEO-flagged primary source)
- Listed size: 135
- Public / yt-dlp-accessible: **34**
- Private / Deleted: 101 (creator keeps past livestreams private)
- Manifest: `urls_youtube.txt`, raw: `playlist_raw.txt`

### Channel upload feed (all-time)
- Total uploads: 4,277 (oldest: ~2010 Matlab tutorials; newest: 2026-04-18)
- Rough title-keyword counts: 557 AI/Claude/LLM-related, 607 forex/MT5/gold/NAS-related (overlap likely)
- Raw: `channel_raw.txt`
- **Reserved for Tier 2:** pending CEO decision after Tier 1 synthesis lands

**Phase 2a/3 scope:** 34 public playlist videos
**Output:** `transcripts/<video_id>.txt` (raw, dedup'd) → `youtube_extractions/batch_NN.md`

## Files produced

| Path | Purpose |
|------|---------|
| `urls_blog.txt` | 1,474 tagged blog URLs |
| `urls_youtube.txt` | 34 public playlist video URLs (Tier 1) |
| `playlist_raw.txt`, `channel_raw.txt` | yt-dlp raw outputs (preserved for Tier 2 re-processing) |
| `blog_batches/batch_01..10.txt` | 30-URL batch files for parallel extraction |
| `INVENTORY.md` | this file |
| `scripts/quantlabs_build_blog_manifest.py` | sitemap parser + tagger |
| `scripts/quantlabs_split_batches.py` | batch splitter |
| `scripts/quantlabs_fetch_transcripts.sh` | yt-dlp batch transcript fetcher |

## Gotchas / caveats

1. yt-dlp `--flat-playlist` doesn't expose upload dates for channels — dates show `NA`. Workaround if needed: per-video `yt-dlp -j` (costly for 4277 vids, deferred).
2. 101 playlist videos are private/deleted — permanently out of scope.
3. `WebFetch` truncated the blog sitemap (~300 of 1474). Recovered via `curl` + XML parse.
4. Sitemap only exposes `/post/*` slugs. If the site has non-post content (category landing pages, courses), not in scope here.
5. URL-slug tagging can mis-classify (e.g., a "futures-options" article might be about MT5-style futures indices that interest us). Extraction agents will correct-tag when they read the body.

## Next phases

| Phase | What | Parallelism | ETA |
|-------|------|-------------|-----|
| 2a | yt-dlp batch fetch 34 transcripts | 1 serial (background) | 30-45 min |
| 2b | Extract 300 blog articles | 10 parallel agents | ~20 min |
| 3 | Analyze 34 transcripts for findings | 3-4 parallel agents | ~10 min |
| 4 | Cluster + diff vs GTOS → ranked candidates | 2 agents | ~10 min |
