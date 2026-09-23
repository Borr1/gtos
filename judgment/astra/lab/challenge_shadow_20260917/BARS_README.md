# Challenge-true XAU bars — Fable Wave E re-prove pull

**Pulled at (UTC):** 2026-09-17T10:40:56Z  
**Mode:** READ-ONLY (MetaTrader5 `copy_rates_range` only — no place / modify / trade)  
**Source machine:** `7cfa9657-805b-4e9c-9fbb-886c500f997b` (redacted_host)  
**Terminal:** `C:\MT5\FTMO\terminal64.exe`  
**Python:** `C:\Users\MSI\Documents\ai-trading-agent\.venv-gtos\Scripts\python.exe` + `MetaTrader5`  
**Account:** login `0` / server `FTMO-Server` / company `FTMO Global Markets Ltd`  
**Symbol:** `XAUUSD`

## Time basis (important)

FTMO-Server bar/`tick.time` values encode **broker server wall clock as Unix** (measured **UTC+3** vs VPS UTC clock at pull).

Exported column **`time_utc`** = `fromtimestamp(rate.time) − 3h` (true UTC).  
CSV also keeps `time_server_labeled` for audit.

Cross-check ticket **293332188** SHORT:
- True open UTC: `2026-09-17T07:30:55Z` (owner/context)
- MT5 `position.time` labeled: `2026-09-17T10:30:55Z` (= +3h)
- Entry price: `4331.45`
- Matching M15 bar `time_utc=2026-09-17T07:30:00Z`: O=4329.26 H=4334.89 L=4329.26 C=4331.28

## Bar files

| TF | File(s) | Count | First `time_utc` | Last `time_utc` | Bars before entry bar open |
|----|---------|------:|------------------|-----------------|--------------------------------:|
| M15 | `XAUUSD_M15.csv` + `.json` | 1597 | 2026-08-25T00:00:00Z | 2026-09-17T10:30:00Z | 1584 |
| H4 | `XAUUSD_H4.csv` + `.json` | 75 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | 74 |
| D1 | `XAUUSD_D1.csv` + `.json` | 56 | 2026-07-01T21:00:00Z | 2026-09-16T21:00:00Z | 56 |

CSV columns: `time_utc,open,high,low,close,tick_volume,spread,real_volume,time_server_labeled`

### SUCCESS gate (M15)

- Entry `2026-09-17T07:30:55Z` is **inside** series (bar open `07:30:00Z`).
- Bars strictly before entry bar open: **1584 ≥ 20**.
- **SUCCESS = true**

Note: D1 opens at `21:00Z` (= midnight server UTC+3). H4 session alignment yields first bar `01:00Z` on 2026-09-01 rather than `00:00Z`.

## Slate (newer than prior parent 10:26 pull)

| Artifact | Value |
|----------|-------|
| `latest_slate.json` | `slate_id=bddc8ff9fad4a254` built `2026-09-17T10:41:05.126377+00:00` |
| Pointed body | `slate_20260917T104105Z_bddc8ff9fad4a254.json` |
| Also kept | `slate_20260917T103607Z_f2197039bb6ee7d7.json` (prior during pull) |

Parent folder `/workspace/gtos/fable_joint_pull_20260917/` updated to the same `latest_slate.json` + pointed body.

## Events (optional)

| File | Notes |
|------|-------|
| `events_since_20260915.jsonl` | **Preferred.** 7729 lines, ~3.4 MB, `ts_utc` from `2026-09-15T00:00:15Z` → `2026-09-17T10:41:32Z`. Source: last 8 MB of VPS `shadow_logs\f5_minimal\operator\events.jsonl` filtered by `ts_utc >= 2026-09-15`. |
| `events_tail_5MB.jsonl` | Raw last 5 MB of same file (~10.6k lines). Many lines are news reevals whose `event_version` stays on 2026-09-14; use `ts_utc` or the since-0915 extract. |

VPS full events path: `host-local\redacted_host\repo\shadow_logs\f5_minimal\operator\events.jsonl` (~17.3 MB at pull).

## Meta

See `pull_meta.json` for machine-readable counts / entry-bar OHLC / account ids.

## Box paths for parent

```
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_M15.csv
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_M15.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_H4.csv
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_H4.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_D1.csv
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/XAUUSD_D1.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/pull_meta.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/BARS_README.md
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/latest_slate.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/slate_20260917T104105Z_bddc8ff9fad4a254.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/slate_20260917T103607Z_f2197039bb6ee7d7.json
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/events_since_20260915.jsonl
/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/events_tail_5MB.jsonl
```

Parent slate mirrors:
```
/workspace/gtos/fable_joint_pull_20260917/latest_slate.json
/workspace/gtos/fable_joint_pull_20260917/slate_20260917T104105Z_bddc8ff9fad4a254.json
```
