# Expanded OOS Full-Unblocking Progress Checkpoint - 2026-05-04

**Goal prompt:** `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_GOAL_PROMPT_2026-05-04.md`  
**Status:** `STARTED_NOT_TERMINAL`  
**Scope:** research/tooling only  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**AI/API calls:** 0  
**Databento spend:** $0  
**Live trading surface changed:** no

## What Was Unblocked

The first missing adapter blocker was removed. A research-only Sierra `.scid` to GTOS OHLCV root converter now exists at `scripts/convert_sierra_scid_to_ohlcv.py`, with tests in `tests/test_convert_sierra_scid_to_ohlcv.py`.

The converter writes M1/M5/M15/H1/D1 CSV roots plus a manifest carrying source hash, evidence class, transform, row/gap counts, invalid-record counts, and `NO_PROMOTION_VERDICT`. It supports futures-proxy mappings and inverse price transform for `6J -> USDJPY`.

The existing SCID inspection tests were also hardened to use a repo-local temp fixture so this environment's Windows temp ACL issue does not block adapter verification.

## First-Wave Breadth

After the initial NQ pilot, the bounded first-wave conversion produced 95 CSV files plus a manifest for 19 mappings across NQ/MNQ, YM/MYM, XAUUSD, GC/MGC, SI/SIL, 6J, 6B, EURUSD/6E, ES/MES, CL, ZN, VXM, and VXMM.

Source-quality status is versioned at:

- `research/program_control/EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_2026-05-04.json`

Sparse warnings remain for `SIM26-COMEX`, `SILM26-COMEX`, and `VXMM26-CFE`. Futures and cross-instrument mappings remain transfer evidence only.

## Opened Replay Ledger

| Batch | Type | Slice | Rows | Actions / Takes | Resolved | Result |
|---|---|---|---:|---:|---:|---|
| `sierra_nq_to_nas100_pilot_20260504` | M15 prequential | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | 76 | 0 actions | 0 | Path works, no frozen cohort match. |
| `sierra_xauusd_scid_to_xauusd_pilot_20260504` | M15 prequential | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | 76 | 30 actions | 0 | Unresolved M15 outcomes: same-bar/no-entry. |
| `sierra_xauusd_scid_v2_mtf_pilot_20260504` | V2 MTF | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | 76 | 30 takes | 5 reference resolved | Diagnostic-positive small-n source-transfer result; best structural was `STRUCT_BOS_LEVEL_V2` at net +0.77465R after 0.05R cost versus J46 at -0.078468R. |
| `sierra_ym_to_us30_cash_pilot_20260504` | M15 prequential | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | 50 | 6 actions | 0 | No resolved outcomes. |
| `sierra_ym_us30_cash_v2_mtf_pilot_20260504` | V2 MTF | 2026-04-15 13:00 to 2026-04-17 17:00 UTC | 50 | 6 takes | 0 | All no-entry. |
| `sierra_6j_to_usdjpy_pilot_20260504` | M15 prequential | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | 96 | 0 actions | 0 | Path works, no actions. |
| `sierra_6b_to_gbpusd_pilot_20260504` | M15 prequential | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | 90 | 0 actions | 0 | Path works, no actions. |
| `sierra_si_to_xagusd_pilot_20260504` | M15 prequential | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | 72 | 6 actions | 4 | M15 mean +1.5R, but proxy/sparse and not path-portable. |
| `sierra_si_xagusd_v2_mtf_pilot_20260504` | V2 MTF | 2026-04-15 00:00 to 2026-04-17 17:00 UTC | 72 | 6 takes | 0 | All no-entry on lower timeframe. |

## Candidate Survival Snapshot

| Candidate / Family | Evidence After Checkpoint | Status |
|---|---|---|
| Current J46-J49/live baseline | XAUUSD same-market V2 MTF n=5 was weak; XAGUSD/SI V2 had no fills. | Still not promotion-usable. |
| V2 structural selectors | XAUUSD same-market source-transfer produced a small-n positive diagnostic, best `STRUCT_BOS_LEVEL_V2`. | Interesting only as discovery/source-transfer evidence. |
| NAS100 futures-proxy replay | NQ adapter path works but frozen `NAS100|ny|bullish|D1` did not match this slice. | No survival evidence. |
| US30/YM futures proxy | M15 actions appeared but V2 lower-timeframe replay had no entries. | No resolved evidence. |
| XAGUSD/SI proxy | M15 positive did not survive lower-timeframe fill reconstruction. | Treat as path ambiguity, not alpha. |
| USDJPY/6J and GBPUSD/6B | Replay path works but no actions in opened slice. | Source-ready, no outcome evidence. |

## Requirement Audit

| Requirement | Status | Evidence |
|---|---|---|
| Do not stop at missing adapters/converters. | Met for SCID OHLCV. | Built and tested the converter instead of stopping at portability gap. |
| Targeted Databento allowed, AI/API not approved. | Met. | No Databento call was required; AI/API calls stayed at 0. |
| No live logic/prompts/risk/execution/safety changes. | Met. | Changes are research scripts, tests, artifacts, and generated research data roots only. |
| Go broad after first pilot. | Met at source-quality layer. | Converted 19 first-wave mappings after the first NQ path. |
| Preserve `NO_PROMOTION_VERDICT`. | Met. | All registries, manifests, reports, and checkpoint artifacts retain the verdict. |
| Full completion standard. | Not met. | Depth parity extraction, broader date loops, true temporal OOS, proxy equivalence, and promotion-grade sample floors remain open. |

## Remaining Blockers

- Sierra `.depth` parity extractor is not built.
- Futures proxy mappings remain source-transfer evidence, not broker-truth validation.
- Sparse first-wave sources remain for silver and VXMM.
- No true temporal OOS or forward-shadow promotion evidence was produced here.
- No DSR/PBO/effective-N promotion statistics are valid because sample floors and evidence classes do not qualify.

## Verification

```powershell
python -m pytest tests\test_convert_sierra_scid_to_ohlcv.py -q -p no:cacheprovider
# 4 passed in 0.21s

python -m pytest tests\test_inspect_sierra_scid.py tests\test_convert_sierra_scid_to_ohlcv.py -q -p no:cacheprovider
# 6 passed in 0.27s
```

## Bottom Line

The expanded OOS full-unblocking goal is materially started: Sierra intraday bars are now portable into GTOS replay roots, the first pilot path works, the first-wave source layer was broadened, and several registered replay slices were opened. The result is a research checkpoint, not a terminal goal completion and not a promotion dossier.
