# Expanded OOS Data Source Map

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Control Status

- No expanded-OOS outcome slice was opened by this source-map build.
- Candidate rules must remain frozen by the companion registry before replay.
- Cross-instrument and futures-proxy evidence must not be called live validation.

## Source Summary

| Source | Status | Count | Coverage / note |
| --- | --- | --- | --- |
| MT5 OHLCV manifests | present | 9 | 44 symbol/timeframe aggregates |
| MT5 tick probes | present | 3 | Recent tick windows only; older tick retention remains limited |
| MT5 live symbol specs | present | 22 | Read-only terminal snapshot when available |
| Sierra .scid | present | 33 | 26 first-wave relevant files |
| Sierra .depth | present | 465 | 59.701 GB; missing first-wave depth=[] |
| Databento cached orderflow | present | 128 | local_cached_only; broad new Databento pulls forbidden without explicit approval |

## MT5 OHLCV Aggregate Sample

| Symbol | TF | Datasets | Rows | First | Last | Gap count sum | Max gap seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EURUSD | H1 | 1 | 24 | 2026-04-15 00:00:00 | 2026-04-15 23:00:00 | 0 | 0.000000 |
| EURUSD | M15 | 1 | 96 | 2026-04-15 00:00:00 | 2026-04-15 23:45:00 | 0 | 0.000000 |
| GBPJPY | D1 | 3 | 1148 | 2022-01-03 00:00:00 | 2026-05-01 00:00:00 | 234 | 259200.000000 |
| GBPJPY | H1 | 3 | 27339 | 2022-01-03 00:00:00 | 2026-05-01 23:00:00 | 242 | 255600.000000 |
| GBPJPY | H4 | 1 | 138 | 2026-04-01 00:00:00 | 2026-05-01 20:00:00 | 4 | 187200.000000 |
| GBPJPY | M1 | 4 | 1736586 | 2022-01-03 00:00:00 | 2026-05-01 23:59:00 | 1501 | 252720.000000 |
| GBPJPY | M15 | 4 | 102706 | 2022-04-14 11:15:00 | 2026-05-01 23:45:00 | 243 | 252900.000000 |
| GBPJPY | M5 | 4 | 427710 | 2022-01-03 00:00:00 | 2026-05-01 23:55:00 | 403 | 252900.000000 |
| GBPUSD | D1 | 3 | 1148 | 2022-01-03 00:00:00 | 2026-05-01 00:00:00 | 234 | 259200.000000 |
| GBPUSD | H1 | 3 | 27342 | 2022-01-03 00:00:00 | 2026-05-01 23:00:00 | 241 | 262800.000000 |
| GBPUSD | H4 | 1 | 138 | 2026-04-01 00:00:00 | 2026-05-01 20:00:00 | 4 | 187200.000000 |
| GBPUSD | M1 | 4 | 1735165 | 2022-01-03 00:00:00 | 2026-05-01 23:59:00 | 3017 | 259320.000000 |
| GBPUSD | M15 | 4 | 102716 | 2022-04-14 19:00:00 | 2026-05-01 23:45:00 | 229 | 260100.000000 |
| GBPUSD | M5 | 4 | 427855 | 2022-01-03 00:00:00 | 2026-05-01 23:55:00 | 443 | 259500.000000 |
| NAS100 | D1 | 3 | 934 | 2022-10-20 00:00:00 | 2026-05-01 00:00:00 | 193 | 345600.000000 |
| NAS100 | H1 | 3 | 20855 | 2022-10-20 11:00:00 | 2026-05-01 23:00:00 | 935 | 270000.000000 |
| NAS100 | H4 | 1 | 137 | 2026-04-01 00:00:00 | 2026-05-01 20:00:00 | 4 | 201600.000000 |
| NAS100 | M1 | 4 | 1184881 | 2022-10-20 11:00:00 | 2026-05-01 23:59:00 | 3789 | 270000.000000 |
| NAS100 | M15 | 4 | 75420 | 2022-10-20 11:00:00 | 2026-05-01 23:45:00 | 3580 | 270000.000000 |
| NAS100 | M5 | 4 | 319449 | 2022-10-20 11:00:00 | 2026-05-01 23:55:00 | 3965 | 270000.000000 |

Full MT5 aggregate rows are in the JSON artifact.

## Sierra First-Wave Depth

| Symbol | Files | MB | First date | Last date | Status |
| --- | --- | --- | --- | --- | --- |
| 6BM26-CME | 31 | 748.705000 | 2026-04-03 | 2026-05-03 | present |
| 6EM26-CME | 31 | 1242.881000 | 2026-04-03 | 2026-05-03 | present |
| 6JM26-CME | 31 | 925.057000 | 2026-04-03 | 2026-05-03 | present |
| CLM26-NYMEX | 31 | 4029.823000 | 2026-04-03 | 2026-05-03 | present |
| ESM26-CME | 31 | 5800.825000 | 2026-04-03 | 2026-05-03 | present |
| GCM26-COMEX | 31 | 2249.025000 | 2026-04-03 | 2026-05-03 | present |
| MESM26-CME | 31 | 5384.625000 | 2026-04-03 | 2026-05-03 | present |
| MGCM26-COMEX | 31 | 3639.616000 | 2026-04-03 | 2026-05-03 | present |
| MNQM26-CME | 31 | 17151.837000 | 2026-04-03 | 2026-05-03 | present |
| MYMM26-CBOT | 31 | 2451.692000 | 2026-04-03 | 2026-05-03 | present |
| NQM26-CME | 31 | 10491.103000 | 2026-04-03 | 2026-05-03 | present |
| SILM26-COMEX | 31 | 1009.488000 | 2026-04-03 | 2026-05-03 | present |
| SIM26-COMEX | 31 | 846.096000 | 2026-04-03 | 2026-05-03 | present |
| YMM26-CBOT | 31 | 1765.478000 | 2026-04-03 | 2026-05-03 | present |
| ZNM26-CBOT | 31 | 3397.576000 | 2026-04-03 | 2026-05-03 | present |

## Sierra First-Wave Intraday

| Symbol | Records | MB | First | Last | Warnings |
| --- | --- | --- | --- | --- | --- |
| 6AM26-CME | 1765381 | 67.344000 | 2025-10-30T14:05:26.228000+00:00 | 2026-05-01T20:59:59.310000+00:00 |  |
| 6BM26-CME | 1369667 | 52.249000 | 2025-10-29T14:16:38.206000+00:00 | 2026-05-01T20:59:57.769000+00:00 |  |
| 6CM26-CME | 1044421 | 39.842000 | 2025-10-29T14:08:33.543000+00:00 | 2026-05-01T20:59:55.017000+00:00 |  |
| 6EM26-CME | 3494582 | 133.308000 | 2025-10-29T19:16:06.452000+00:00 | 2026-05-01T20:59:55.016000+00:00 |  |
| 6JM26-CME | 2570524 | 98.058000 | 2025-10-29T08:30:34.030000+00:00 | 2026-05-01T20:59:59.048000+00:00 |  |
| 6SM26-CME | 717146 | 27.357000 | 2025-10-29T19:35:15.029000+00:00 | 2026-05-01T20:59:56.056000+00:00 |  |
| CLM26-NYMEX | 5197396 | 198.265000 | 2025-10-29T10:55:14.096000+00:00 | 2026-05-01T20:59:59.375000+00:00 |  |
| ESM26-CME | 39692015 | 1514.130000 | 2025-10-29T17:29:01.444000+00:00 | 2026-05-01T20:59:59.092000+00:00 |  |
| EURUSD | 25225959 | 962.294000 | 2025-10-28T14:27:04.217000+00:00 | 2026-05-01T20:58:59.320000+00:00 |  |
| GCM26-COMEX | 3185285 | 121.509000 | 2025-10-29T05:09:05.892000+00:00 | 2026-05-01T20:59:59.600000+00:00 |  |
| M2KM26-CME | 3668834 | 139.955000 | 2025-10-29T07:07:49.240000+00:00 | 2026-05-01T20:59:59.769000+00:00 |  |
| MCLM26-NYMEX | 3143590 | 119.918000 | 2025-10-29T13:38:36.580000+00:00 | 2026-05-01T20:59:58.371000+00:00 |  |
| MESM26-CME | 29659284 | 1131.412000 | 2025-10-28T14:29:35.469000+00:00 | 2026-05-01T20:59:59.678001+00:00 |  |
| MGCM26-COMEX | 9297679 | 354.678000 | 2025-10-29T06:30:54.023000+00:00 | 2026-05-01T20:59:59.896000+00:00 |  |
| MNQM26-CME | 57252455 | 2184.008000 | 2025-10-28T14:54:37.713000+00:00 | 2026-05-01T20:59:59.999000+00:00 |  |
| MYMM26-CBOT | 5307278 | 202.457000 | 2025-10-29T08:36:01.658000+00:00 | 2026-05-01T20:59:57.920000+00:00 |  |
| NQM26-CME | 16876939 | 643.804000 | 2025-10-29T22:43:23.898000+00:00 | 2026-05-01T20:59:59.073000+00:00 |  |
| RTYM26-CME | 5657395 | 215.813000 | 2025-10-30T13:35:57.186000+00:00 | 2026-05-01T20:59:58.711000+00:00 |  |
| SILM26-COMEX | 5208 | 0.199000 | 2026-03-31T00:16:51.350000+00:00 | 2026-05-01T20:56:20.127000+00:00 | known_sparse_scid_first_wave_warning,low_record_count |
| SIM26-COMEX | 12028 | 0.459000 | 2025-11-03T15:24:05.245000+00:00 | 2026-05-01T20:49:05.750000+00:00 | known_sparse_scid_first_wave_warning |
| VXM26-CFE | 533115 | 20.337000 | 2025-10-29T14:38:24.877000+00:00 | 2026-05-01T20:59:58.202001+00:00 |  |
| VXMM26-CFE | 4278 | 0.163000 | 2025-12-23T13:05:15.748000+00:00 | 2026-05-01T20:58:14.078000+00:00 | known_sparse_scid_first_wave_warning,low_record_count |
| XAUUSD | 9463561 | 361.006000 | 2025-10-28T14:19:09.044000+00:00 | 2026-05-01T20:44:58.881000+00:00 |  |
| YMM26-CBOT | 917231 | 34.990000 | 2025-10-30T14:03:53.366000+00:00 | 2026-05-01T20:59:57.305000+00:00 |  |
| ZBM26-CBOT | 7059787 | 269.310000 | 2025-10-29T19:32:33.520000+00:00 | 2026-05-01T20:59:59.146003+00:00 |  |
| ZNM26-CBOT | 24060922 | 917.851000 | 2025-10-29T13:54:09.212000+00:00 | 2026-05-01T20:59:57.783000+00:00 |  |

## Evidence Class Plan

| Evidence class | Eligible sources | Current status |
| --- | --- | --- |
| TRUE_TEMPORAL_OOS | MT5 same-symbol/source untouched date blocks | requires P2 replay portability plus frozen date-slice registration before outcomes |
| SAME_MARKET_SOURCE_TRANSFER | Sierra .scid for XAUUSD/EURUSD and comparable market files | available as robustness evidence only; not broker execution truth |
| FUTURES_PROXY_TRANSFER | Sierra .scid/.depth first-wave futures, cached/targeted Databento futures artifacts | available for mechanism/orderflow research; not MT5 broker outcome truth |
| CROSS_INSTRUMENT_TRANSFER | MT5 expansion basket, Sierra first-wave controls | screen after candidate registry; never call live validation |
| REGIME_TRANSFER | MT5/exported OHLCV, existing external validation event logs | requires fixed regime definitions before outcome readout |
| FORWARD_SHADOW | future GTOS logs, future Sierra active-session depth | deferred until new rows arrive |

## Cost And Licensing Policy

- `mt5`: local read-only exports; no AI/API cost; broker history retention limits apply
- `sierra`: local files from paid Package 12 setup; no incremental API cost in parsing; disk/storage monitored
- `databento`: cached artifacts only in this control pass; targeted paid windows require explicit predeclared question and approval
- `web_sources`: use cached source-evidence protocol before new fetches

## Opened / Reserved Slices

- Opened outcome slices at P0/P1: `0`.
- Reserved holdouts: `[{'slice_id': 'RESERVED_POST_FIRST_BATCH_HOLDOUT_V1', 'status': 'reserved_not_opened', 'note': 'Exact date/source slices to be assigned after P2 portability audit; no expanded OOS outcomes opened by this P0/P1 artifact.'}]`.

## Blockers And Warnings

- Missing first-wave Sierra depth symbols: `[]`.
- Missing first-wave Sierra .scid symbols: `[]`.
- MT5 OHLCV is broker-source data; Sierra/Databento futures are proxy/source-transfer data.
- Contract specs and spreads come from the live MT5 read-only snapshot only when MT5 initializes; otherwise they are `not_computable` in the JSON.
