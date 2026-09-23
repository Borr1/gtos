# GBPJPY × sub_mid_dn_re — MULTIYEAR HOLD-span replay — 2026-09-20

**Status:** **FAIL** (HOLD-span / no-pre-2022-train) · **place=false** · **ready_for_key_fx=false** · APPLY unset  
**ts_ict:** 2026-09-20 14:24 ICT  
**Affinity:** Challenge KEEP 293540988 sumR=+2.96 · plan rank 5

## Tape (REAL — prior BLOCKED used wrong tape)

| Role | Path | Span | n bars |
|------|------|------|-------:|
| **VPS historical (this run)** | `/workspace/gtos/research/warroom_20260920/multiyear/GBPJPY_M15_from_vps_historical.csv` | 2022-03-28 → 2026-04-17 | 100967 |
| Prior hydrate (superseded) | `/workspace/instrument-edge/hydrate_2045/GBPJPY_M15.csv` | ~2026-08→09 | 2500 |

## TRAIN / HOLD honesty

| Question | Answer |
|----------|--------|
| TRAIN ≤2021 possible? | **NO** — tape starts 2022-03-28 → **HOLD-span / no-pre-2022-train** |
| HOLD ≥2022 bars | **100967** (entire tape) |
| TRAIN bars ≤2021 | **0** |

## Dig PRIMARY-style fill model (gate)

- Adapted from `multiyear/run_multiyear_positive_v0.py`: geometry OHLC touch · structure stop beyond stretch · **TP=1R** · **time_stop=32** · entry=signal close · stop-before-tp
- Signal: FX `sub_mid_dn_re` proxy (SMA20, stretch>1.0×ATR14, London/NY) — **SHORT primary** after upside stretch
- **Do not** port XAU spring/expanding/three_fresh geometry
- Cost never kill-gate · no NEWS invent · place=false

## Owner gate (≥2022 HOLD window — v0 1R)

| Gate | Result |
|------|--------|
| HOLD sumR > 0 | **-922.0** → **FAIL** |
| WR (reported) | **38.22%** (floor 40% → BELOW) |
| n / avgR / maxDD | 3912 / -0.2357 / 926.0 |
| place | **false** |
| ready_for_key_fx | **false** |

### Year table (PRIMARY SHORT · v0 1R)

| year | n | WR | avgR | sumR |
|-----:|--:|---:|-----:|-----:|
| 2022 | 674 | 41.99% | -0.1602 | -108.0 |
| 2023 | 981 | 36.39% | -0.2722 | -267.0 |
| 2024 | 1002 | 37.92% | -0.2415 | -242.0 |
| 2025 | 954 | 37.63% | -0.2474 | -236.0 |
| 2026 | 301 | 38.54% | -0.2292 | -69.0 |

Exit reasons (1R): `{'orig_stop': 2417, 'orig_tp': 1495}`

### Disclosure — Dig blotter 3R (same signal; not gate)

| metric | value |
|--------|------:|
| sumR | -103.6877 |
| WR | 24.63% |
| n | 3662 |

3R year sumR: [(2022, 83.1211), (2023, -70.7174), (2024, -80.5129), (2025, -47.7641), (2026, 12.1856)]

## Cross-ref (ATR lens scoreboard — different R-universe)

- GBPJPY×sub_mid_dn_re_proxy ATR hold_year_sumR≈**472.87** n=3706 WR≈13% on same secondary span
- Do **not** merge with Dig v0 1R gate

## Milestone

- **PASS/FAIL (owner sumR gate on Dig v0 1R):** **FAIL**
- **Monday-ready:** **NO**
- **WakeParent:** NO
- **APPLY:** unset
- Next unlock for full TRAIN/HOLD: GBPJPY M15 spanning ≤2021 (absent today)

## Artifacts

- `GBPJPY_SUB_MID_MULTIYEAR_20260920.{md,json}`
- `multiyear/blotter_HOLD_GBPJPY_sub_mid_dn_re_proxy_v0_1R.jsonl`
- Tape: `multiyear/GBPJPY_M15_from_vps_historical.csv`


## Affinity stamp — Continue 1425 ICT

**as_of:** 2026-09-20 ~14:25 ICT

Per owner instrument×sleeve law: Dig PRIMARY-style geometry on this pairing is **NARROW/KILL_DIG_GEOMETRY** (research), not promote.

- Dig HOLD-span FAIL (sumR=−922, n=3912, WR 38%) outweighs Challenge KEEP +2.96 (**n=1**).
- Do **not** claim multiyear Dig edge for GBPJPY×sub_mid.
- Challenge KEEP ticket may remain sleeve-family **KEEP_RESEARCH** only.
- Stamp: `codila_absorb/war_room/AFFINITY_GBPJPY_SUB_MID_DIG_FAIL_20260920.md`
