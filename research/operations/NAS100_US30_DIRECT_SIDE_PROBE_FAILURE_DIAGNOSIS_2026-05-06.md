# NAS100/US30 Direct Side-Probe Failure Diagnosis - 2026-05-06

Status: `SOURCE_PROBE_ALIAS_MISMATCH_CONFIRMED`  
Evidence class: `READ_ONLY_MT5_PROBE + CONFIG_CODE_REVIEW + MONITORING_LOG_REVIEW`  
Trading behavior impact: none  
Promotion verdict: `NO_PROMOTION_VERDICT`

## Objective

Determine whether the May 5 NAS100/US30 direct read-only side-probe failure came
from broker symbol mapping, MT5 API contention, terminal state, side process,
timeout, or permissions.

The goal prompt asks this explicitly in
`.context/05_operations/NEXT_IMPROVEMENTS_AND_LTO031_032_GOAL_PROMPT_2026-05-06.md:73`
and again at `:146`.

## Answer

The failure was caused by broker-invalid symbol names in the side probe, not by
terminal outage, permissions, broad MT5 API contention, or production tick
capture failure.

On the redacted_account terminal, the broker symbols are:

| GTOS/canonical label | redacted_account broker symbol | Status |
|---|---|---|
| `NAS100` | `NDX100` | works |
| `US30_cash` | `US30` | works |
| `US30.cash` | not available on this FN terminal | fails |

The direct side-probe symptom matches using `NAS100`, `US30_cash`, or
`US30.cash` as MT5 broker symbols. The profile-resolved symbols `NDX100` and
`US30` work from the same terminal/account.

## Evidence Read

- Monitoring recorded the issue repeatedly as `Terminal: Call failed` while
  tick capture stayed fresh:
  - `research/operations/AI_MARKET_MONITORING_OBSERVATIONS_2026-05-05.md:415`
  - `research/operations/AI_MARKET_MONITORING_OBSERVATIONS_2026-05-05.md:430`
  - `research/operations/AI_MARKET_MONITORING_OBSERVATIONS_2026-05-05.md:445`
  - `research/operations/GTOS_DEEP_ACTIVE_MONITORING_FINAL_2026-05-05.md:22`
  - `research/operations/GTOS_DEEP_ACTIVE_MONITORING_FINAL_2026-05-05.md:58`
  - `research/operations/GTOS_DEEP_ACTIVE_MONITORING_FINAL_2026-05-05.md:65`
  - `research/operations/GTOS_OWNER_DEEP_DIVE_MONITORING_SYNTHESIS_2026-05-06.md:46`
- Config/code confirms production uses profile-resolved broker symbols:
  - `config/profiles/redacted_account.yaml:92` says FN uses `US30`.
  - `config/profiles/redacted_account.yaml:99` sets `US30_cash.market.mt5_symbol: "US30"`.
  - `config/profiles/redacted_account.yaml:116` says FN uses `NDX100`.
  - `config/profiles/redacted_account.yaml:121` sets `NAS100.market.mt5_symbol: "NDX100"`.
  - `config/agent_config.yaml:899` still has base/FTMO `US30.cash`, which is
    expected to be overridden under the redacted_account profile.
  - `src/components/data_ingestion.py:68` and `:74` route broker API calls
    through `market.mt5_symbol`.
  - `scripts/watchdog.ps1:65` maps tick capture `US30_cash -> US30`.
  - `scripts/watchdog.ps1:70` maps tick capture `NAS100 -> NDX100`.
  - `scripts/watchdog.ps1:759` passes the mapped broker symbol to
    `tick_capture --mt5-symbol`.
  - `src/mt5/mt5_real.py:114` shows direct quote reads call
    `symbol_info_tick(symbol)` on the provided symbol string.

## Read-Only MT5 Probe Results

Command:

```powershell
python scripts/inspect_mt5_tick_availability.py --yes-live-readonly --label phase1c_index_probe --symbol NAS100_CANON:NAS100 --symbol NAS100_FN:NDX100 --symbol US30_FN:US30 --symbol US30_CANON:US30_cash --symbol US30_DOT:US30.cash --window may5_ny_probe:2026-05-05T13:10:00Z:2026-05-05T13:15:00Z
```

Result summary:

| Probe symbol | Result |
|---|---|
| `NAS100` | `symbol_select_failed:(-1, 'Terminal: Call failed')` |
| `NDX100` | success, `1458` ticks from `2026-05-05T13:10:00Z` to `13:15:00Z` |
| `US30` | success, `258` ticks from `2026-05-05T13:10:00Z` to `13:15:00Z` |
| `US30_cash` | `symbol_select_failed:(-1, 'Terminal: Call failed')` |
| `US30.cash` | `symbol_select_failed:(-1, 'Terminal: Call failed')` |

The same command reported account `0`, server `redacted_account-Server 2`,
terminal connected `true`, terminal build `5833`, and live-account read-only
mode confirmed by `--yes-live-readonly`.

Additional current quote matrix:

| Symbol | `symbol_info_exists` | `symbol_select` | quote present |
|---|---:|---:|---:|
| `NAS100` | false | false, `Terminal: Call failed` | false |
| `NDX100` | true | true | true |
| `US30` | true | true | true |
| `US30_cash` | false | false, `Terminal: Call failed` | false |
| `US30.cash` | false | false, `Terminal: Call failed` | false |

This directly reproduces the monitoring symptom on the wrong aliases and clears
it on the redacted_account broker aliases.

## Classification

- Broker symbol mapping / symbol selection: `CONFIRMED_CAUSE`.
- MT5 terminal state: `RULED_OUT`; the same terminal was connected and returned
  account, quote, and tick-history data for `NDX100` and `US30`.
- Permissions: `RULED_OUT_FOR_READ_ONLY_DATA`; the read-only probe succeeded on
  the live account for the correct symbols.
- Broad MT5 API contention: `RULED_OUT_FOR_INDEX_DATA`; `copy_ticks_range` and
  `symbol_info_tick` succeeded for the correct symbols in the same process.
- Side process contention: `NOT_SUPPORTED_BY_EVIDENCE`; production tick capture
  and the ad hoc read-only alias probe can both access the correct broker
  symbols.
- Timeout: `RULED_OUT`; failures returned immediately as symbol-selection
  failures, not slow or hung calls.

## Production Impact

No production trading behavior issue is indicated.

The May 5 monitoring file already recorded the production distinction:
tick-capture state stayed fresh while direct side probes failed. Local tick
state confirms NAS100 and US30_cash parquet/state files advanced through the
active NY window:

- `data/ticks/NAS100/.state.json`: `saved_at=2026-05-05T17:15:50.383485+00:00`,
  `last_price=28009.41`.
- `data/ticks/US30_cash/.state.json`:
  `saved_at=2026-05-05T17:13:04.179392+00:00`, `last_price=49189.97`.

## Fix Scope

No live code was changed.

Future ad hoc side probes should resolve broker symbols through the same
profile-aware config path as production, or explicitly use the current
redacted_account broker symbols `NDX100` and `US30` when the probe is intentionally
manual. Using canonical storage labels as broker API symbols will reproduce the
`Terminal: Call failed` false positive.

## Ambiguity Status

The exact May 5 one-liner or helper command that produced the original direct
probe notes was not stored as a standalone artifact. That does not block the
diagnosis because the current read-only matrix reproduces the failure on the
canonical/wrong symbols and clears it on the profile-resolved broker symbols
from the same connected terminal/account.

## Verification

- `python scripts/inspect_mt5_tick_availability.py ...` returned expected alias
  failures and correct-symbol tick rows.
- Inline read-only `MetaTrader5` quote matrix returned current quotes for
  `NDX100` and `US30`, and `Terminal: Call failed` for `NAS100`, `US30_cash`,
  and `US30.cash`.

Final posture: `NO_PROMOTION_VERDICT`
