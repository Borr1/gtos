# NEWS_CALENDAR_REPAIR

Repair = sync HIGH rows **from** the live spine. Never invent. Never overwrite June.

| Artifact | Role |
|---|---|
| `data/news_calendar.json` | June 2026-05-31 **week of record**. Do not overwrite. |
| `data/news/f5_high_calendar_host_20260916.json` | Live HIGH spine (13 events, sha256 starts `5258c3ba`) |
| `data/news/news_calendar_f5_synced_from_spine.json` | Synced snapshot (this repair) |
| `news_calendar.json.frozen-20260821` | History (6239 events, different schema) — not a drop-in merge |

Tickets copy from a VPS stub only on **exact** `scheduled_utc` + name match.

```
python3 scripts/jev_news_calendar_sync_from_spine.py
```

Empty spine ≠ no HIGH. Event questions abstain.

Repair map (LIVE / STUB / MISSING, no invented endpoints):
`NEWS_PROTOCOL_REPAIR_MAP.md` + `NEWS_PROTOCOL_REPAIR_BACKLOG.md`.
`calendar_honest` is already APPLIED as writer-not-READ — do not invert
`spine_empty`.
