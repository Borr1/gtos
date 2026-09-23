# Expanded OOS XAGUSD/SI V2 MTF Replay Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Batch ID:** `sierra_si_xagusd_v2_mtf_pilot_20260504`  

This registry is written before running V2 MTF path-scaling on the converted `SIM26-COMEX` to `XAGUSD` proxy root. The M15 prequential pilot found 6 `XAGUSD|london|bullish|D1` actions with 4 resolved TP outcomes, but the source has known sparsity and remains proxy-transfer evidence only.

## Registered Replay

| Field | Value |
| --- | --- |
| Source root | `data/sierra_ohlcv_roots/sierra_si_to_xagusd_pilot_20260504` |
| Evidence class | `FUTURES_PROXY_TRANSFER` |
| Source warning | sparse `SIM26-COMEX` first-wave source |
| Candidate focus | `CAND-001`, `CAND-002`, `CAND-003` |
| Opened slice | `2026-04-15T00:00:00Z` to `2026-04-17T17:00:00Z` |
| AI/API calls | `0` |

Command:

```powershell
python scripts\run_raw_ohlc_path_scaling_v2_levels.py --data-dir data\sierra_ohlcv_roots\sierra_si_to_xagusd_pilot_20260504 --start 2026-04-15T00:00:00Z --end 2026-04-17T17:00:00Z --include-blocked-controls --max-events 500 --output-root data\external\validation\expanded_oos_full_unblocking\sierra_si_xagusd_v2_mtf_pilot_20260504 --report-path research\program_control\EXPANDED_OOS_XAGUSD_SI_V2_MTF_PILOT_2026-05-04.md --write --quiet
```

Boundary: V2 MTF replay can resolve lower-timeframe path ordering on the SI proxy source root. It is not broker execution truth and cannot promote live logic.
