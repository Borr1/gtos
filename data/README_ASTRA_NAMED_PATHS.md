# Astra-named calendar path repair (2026-09-07)

Pointed by JUDGMENT_NEWS_AUDIT_V2 seven-source census + NEWS_PROTOCOL_V2 / WATCH_V2 / WRITER_V2.

## Wired paths (host-local)
| Path | Role |
|---|---|
| `repo/data/news_brief.json` | Astra MISSING → ready brief from spine times |
| `repo/pipeline_state/ultimate_book/operator/judgment/news_brief.json` | Astra MISSING → same |
| `repo/data/news_calendar.json` | Astra MISSING → ready_stub schedule (not live MQL5 harvest claim) |
| `repo/data/official_high_spine.json` | refresh Sep HIGH (no invented clocks) |
| `.../judgment/state/f5_high_calendar.json` | writer-readable HIGH |
| `repo/judgment/state/f5_high_calendar.json` | mirror |
| `C:\Users\trader\intel-layer\calendar\{news_brief,official_high_spine}.json` | refresh stale intel-layer |

## Not invented
- NEWS_PROTOCOL immutable packet queue / capability receipts
- event_state.py pre-send registry
- Fake applied=True / HTTP200 success
- Alternate FOMC "17 Sep UTC" — real source is **2026-09-16T18:00:00Z** (= 17 Sep ICT)

See Mac: `astra-pack/audit/judgment/NEWS_PROTOCOL_V2.md`, `JUDGMENT_NEWS_AUDIT_V2.md`.
