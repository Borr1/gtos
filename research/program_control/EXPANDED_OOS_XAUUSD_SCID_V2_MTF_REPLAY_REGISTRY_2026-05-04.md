# Expanded OOS XAUUSD SCID V2 MTF Replay Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch ID:** `sierra_xauusd_scid_v2_mtf_pilot_20260504`  

This registry is written before running V2 MTF path-scaling on the converted Sierra `XAUUSD.scid` root. The M15 prequential pilot found 30 frozen `XAUUSD|ny|bullish|D1` matches, but M15-only scoring left all outcomes unresolved (`SAME_BAR` or `NO_ENTRY`). The next registered action is to use the existing lower-timeframe path adapter against the already converted M1/M5/M15 root.

## Registered Replay

| Field | Value |
| --- | --- |
| Source root | `data/sierra_ohlcv_roots/sierra_xauusd_scid_to_xauusd_pilot_20260504` |
| Evidence class | `SAME_MARKET_SOURCE_TRANSFER` |
| Candidate focus | `CAND-001`, `CAND-002`, `CAND-003` |
| Opened slice | `2026-04-15T13:00:00Z` to `2026-04-17T17:00:00Z` |
| AI/API calls | `0` |

Command:

```powershell
python scripts\run_raw_ohlc_path_scaling_v2_levels.py --data-dir data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504 --start 2026-04-15T13:00:00Z --end 2026-04-17T17:00:00Z --include-blocked-controls --max-events 500 --output-root data\external\validation\expanded_oos_full_unblocking\sierra_xauusd_scid_v2_mtf_pilot_20260504 --report-path research\program_control\EXPANDED_OOS_XAUUSD_SCID_V2_MTF_PILOT_2026-05-04.md --write --quiet
```

Boundary: V2 MTF replay can resolve lower-timeframe path ordering on same-market Sierra source-transfer data. It is not MT5 broker execution truth and cannot promote live logic.
