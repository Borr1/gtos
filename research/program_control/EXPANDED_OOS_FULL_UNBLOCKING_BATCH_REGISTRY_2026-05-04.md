# Expanded OOS Full-Unblocking Batch Registry - 2026-05-04

**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Frozen candidate registry:** `research/program_control/EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_2026-05-03.md`  

This registry is written before opening the first converted-source replay slice. It converts the 2026-05-03 blocker "Sierra converter missing" into an implementation task and preserves slice accounting before any deterministic replay output is read.

## Tooling Registered

| Tool | Status | Verification |
| --- | --- | --- |
| `scripts/convert_sierra_scid_to_ohlcv.py` | `IMPLEMENTED_TESTED_MVP` | `python -m pytest tests\test_convert_sierra_scid_to_ohlcv.py -q -p no:cacheprovider` -> `4 passed` |

## Frozen Candidate Set

No new candidate rules are introduced here. The active set remains:

1. `CAND-001-J46-J49-LIVE-BASELINE`
2. `CAND-002-V2-OB-BOUNDARY`
3. `CAND-003-V2-FVG-PATH`
4. `CAND-004-V3-FVG-ONLY-RESCUE`
5. `CAND-005-NAS100-DEPTH-THINNESS`
6. `CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR`

## Registered Pilot Batch

| Field | Value |
| --- | --- |
| Batch ID | `sierra_nq_to_nas100_pilot_20260504` |
| Family | NAS100/NDX100 with NQ |
| Source | `C:\SierraChart\Data\NQM26-CME.scid` |
| Output file symbol | `NAS100` |
| Evidence class | `FUTURES_PROXY_TRANSFER` |
| Price transform | `identity` |
| Conversion timeframes | `M1`, `M5`, `M15`, `H1`, `D1` |
| Conversion slice | Full local file for lookback; not an outcome-opened slice by itself |
| Replay opened slice | `2026-04-15T13:00:00Z` to `2026-04-17T17:00:00Z` |
| Reserved holdout | `2026-04-20T00:00:00Z` to `2026-05-01T21:00:00Z` |

Planned commands:

```powershell
python scripts\convert_sierra_scid_to_ohlcv.py --batch-id sierra_nq_to_nas100_pilot_20260504 --mapping NQM26-CME=NAS100:FUTURES_PROXY_TRANSFER --timeframe M1 --timeframe M5 --timeframe M15 --timeframe H1 --timeframe D1 --quiet
python scripts\run_raw_ohlc_prequential_replay.py --data-dir data\sierra_ohlcv_roots\sierra_nq_to_nas100_pilot_20260504 --start 2026-04-15T13:00:00Z --end 2026-04-17T17:00:00Z --include-blocked-controls --max-events 500 --write --quiet
```

Boundary: this can prove a converted-source deterministic replay path and generate `FUTURES_PROXY_TRANSFER` diagnostics only. It is not MT5 broker execution truth and cannot promote live logic.

## First-Wave Family Status

| Family | Status | Next action |
| --- | --- | --- |
| NAS100/NDX100 with NQ/MNQ | `PILOT_REGISTERED` | Convert `NQM26-CME` and run bounded replay. |
| US30/US30_cash with YM/MYM | `PENDING_AFTER_PILOT` | Convert `YMM26-CBOT` or `MYMM26-CBOT`; run label-status/replay if compatible. |
| XAUUSD with XAUUSD.scid and GC/MGC | `PENDING_AFTER_PILOT` | Separate same-market `XAUUSD.scid` from futures-proxy GC/MGC batches. |
| XAGUSD with SI/SIL | `PENDING_AFTER_PILOT_SPARSE_SCID_WARNING` | Convert and preserve sparse SCID warning. |
| USDJPY with 6J | `PENDING_MAPPING_CAUTION` | Use inverse price transform only after proxy contract mapping is registered. |
| GBPUSD with 6B | `PENDING_AFTER_PILOT` | Convert `6BM26-CME` as futures proxy. |
| EURUSD with EURUSD/6E | `PENDING_AFTER_PILOT` | Separate same-market `EURUSD.scid` from futures-proxy 6E. |
| S&P with ES/MES | `PENDING_AFTER_PILOT` | Convert ES/MES as control/expansion family. |
| CL macro/liquidity proxy/control | `PENDING_AFTER_PILOT` | Convert `CLM26-NYMEX` for source-quality/control status. |
| ZN macro/rates proxy/control | `PENDING_AFTER_PILOT` | Convert `ZNM26-CBOT` for source-quality/control status. |
| VIX/VXM controls | `PENDING_SPARSE_OR_NO_DEPTH` | Inventory/convert VXM and preserve VXMM sparse warning. |

## Slice Policy

| Slice type | Policy |
| --- | --- |
| Converted source rows | Not outcome-opened until a replay or label join reads them for candidate scoring. |
| Pilot replay slice | Burned for future pure OOS once the replay command is run. |
| Reserved holdouts | Must not be used for tuning or post-hoc variant design. |

All outputs remain `NO_PROMOTION_VERDICT`.
