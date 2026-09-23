# Challenge multi-symbol bars — Fable joint pull

**Pulled at (UTC):** 2026-09-17T11:07:48Z
**Mode:** READ-ONLY (`copy_rates_range` only — no place / modify / trade)
**Source machine:** `7cfa9657-805b-4e9c-9fbb-886c500f997b` (redacted_host)
**Terminal:** `C:\MT5\FTMO\terminal64.exe`
**Account:** login `0` / server `FTMO-Server` / company `FTMO Global Markets Ltd`
**Offset:** FTMO-Server `+3h` vs VPS UTC; exported `time_utc = labeled − 3h`

## Symbols

From `deals_since_20260909.jsonl` closed symbols, excluding XAUUSD (already in parent `challenge_shadow_bars/`).
Also required by owner: EURUSD, GBPUSD, BTCUSD.

| Symbol | TF | Count | First time_utc | Last time_utc | Files |
|--------|----|------:|----------------|---------------|-------|
| EURUSD | M15 | 1677 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `EURUSD_M15.csv` + `.json` |
| EURUSD | H4 | 75 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `EURUSD_H4.csv` + `.json` |
| GBPUSD | M15 | 1674 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `GBPUSD_M15.csv` + `.json` |
| GBPUSD | H4 | 75 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `GBPUSD_H4.csv` + `.json` |
| BTCUSD | M15 | 2177 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `BTCUSD_M15.csv` + `.json` |
| BTCUSD | H4 | 98 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `BTCUSD_H4.csv` + `.json` |
| EURGBP | M15 | 1677 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `EURGBP_M15.csv` + `.json` |
| EURGBP | H4 | 75 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `EURGBP_H4.csv` + `.json` |
| US30.cash | M15 | 1593 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `US30_cash_M15.csv` + `.json` |
| US30.cash | H4 | 74 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `US30_cash_H4.csv` + `.json` |
| UK100.cash | M15 | 1493 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `UK100_cash_M15.csv` + `.json` |
| UK100.cash | H4 | 75 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `UK100_cash_H4.csv` + `.json` |
| ETHUSD | M15 | 2177 | 2026-08-25T00:00:00Z | 2026-09-17T11:00:00Z | `ETHUSD_M15.csv` + `.json` |
| ETHUSD | H4 | 98 | 2026-09-01T01:00:00Z | 2026-09-17T09:00:00Z | `ETHUSD_H4.csv` + `.json` |

CSV columns: `time_utc,open,high,low,close,tick_volume,spread,real_volume,time_server_labeled`

Note: `US30.cash` / `UK100.cash` file stems use underscore (`US30_cash`, `UK100_cash`).

Box mirror: `/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi/`
