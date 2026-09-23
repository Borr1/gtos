# EURGBP × vss_fxcross_london — MULTIYEAR HOLD-span Dig replay — 2026-09-20

**Status:** **FAIL** (HOLD-span / no-pre-2022-train) · **place=false** · **ready_for_key_fx=false** · APPLY unset  
**ts_ict:** 2026-09-20 14:28 ICT  
**Affinity:** Challenge KEEP **291816474** +1.87 vs loser **291087142** −1.20 · mixed twin; Dig multiyear is expectancy test

## Tape (REAL — prior BLOCKED thin superseded)

| Role | Path | Span | n bars |
|------|------|------|-------:|
| **VPS MT5 (this run)** | `/workspace/gtos/research/warroom_20260920/multiyear/EURGBP_M15_from_mt5.csv` | 2022-09-13 → 2026-09-18 (~4.01y) | 100000 |
| Prior thin (superseded) | box historical_2026 / fable ~weeks–months | 2026-only | ≤7761 |

## TRAIN / HOLD honesty

| Question | Answer |
|----------|--------|
| TRAIN ≤2021 possible? | **NO** — tape starts 2022-09-13 → **HOLD-span / no-pre-2022-train** |
| HOLD ≥2022 bars | **100000** |
| TRAIN bars ≤2021 | **0** |
| Span gate ≥~2y | **PASS** (4.01y) |

## Dig PRIMARY-style fill model (gate)

- Adapted from `multiyear/run_multiyear_positive_v0.py`: geometry OHLC touch · structure stop = opp ORB · **TP=1R** · **time_stop=32** · entry=signal close · stop-before-tp
- Signal: Dig-style `vss_fxcross_london_proxy` (London ORB impulse + continuation break; both sides)
- **Do not** port XAU spring/expanding/three_fresh geometry
- Cost never kill-gate · no NEWS invent · place=false

## Owner gate (≥2022 HOLD window — v0 1R)

| Gate | Result |
|------|--------|
| HOLD sumR > 0 | **-15.2672** → **FAIL** |
| WR (reported) | **49.83%** (floor 40% → OK) |
| n / avgR / maxDD | 905 / -0.0169 / 51.7307 |
| side mix | {'SHORT': 458, 'LONG': 447} |
| place | **false** |
| ready_for_key_fx | **false** |

### Year table (PRIMARY Dig · v0 1R)

| year | n | WR | avgR | sumR |
|-----:|--:|---:|-----:|-----:|
| 2022 | 72 | 48.61% | -0.0314 | -2.2578 |
| 2023 | 240 | 45.83% | -0.0958 | -23.0009 |
| 2024 | 216 | 49.54% | -0.0288 | -6.2247 |
| 2025 | 218 | 55.05% | 0.0901 | 19.6436 |
| 2026 | 159 | 49.69% | -0.0216 | -3.4274 |

Exit reasons (1R): `{'orig_tp': 429, 'orig_stop': 448, 'time_stop': 28}`

### Disclosure — Dig blotter 3R (same signal; not gate)

| metric | value |
|--------|------:|
| sumR | 11.891 |
| WR | 31.05% |
| n | 905 |

3R year sumR: [(2022, np.float64(-6.0893)), (2023, np.float64(-23.7951)), (2024, np.float64(23.0343)), (2025, np.float64(17.6208)), (2026, np.float64(1.1203))]

## Affinity note (Challenge twin)

- Twin autopsy: 291087142 FS **−1.20** vs 291816474 **+1.87** → mixed; REVIEW path (`CHALLENGE_KEEP_TWIN_FS_AUTOPSY_20260920`)
- Dig HOLD-span **FAIL** (sumR=-15.2672, n=905, WR 49.83%) outweighs single KEEP ticket for multiyear Dig edge claim
- Do **not** hard-off EURGBP×vss from Dig alone without Chair affinity law review; place remains false

## Milestone

- **PASS/FAIL (owner sumR gate on Dig v0 1R):** **FAIL**
- **Monday-ready:** **NO**
- **WakeParent:** NO
- **APPLY:** unset
- Next unlock for full TRAIN/HOLD: EURGBP M15 spanning ≤2021 (broker terminal maxbars=100000 capped this pull at ~2022-09)

## Artifacts

- `EURGBP_VSS_MULTIYEAR_20260920.{md,json}`
- `blotter_HOLD_EURGBP_vss_fxcross_london_proxy_v0_1R.jsonl` / `blotter_HOLD_EURGBP_vss_fxcross_london_proxy_dig3R.jsonl`
- Tape: `multiyear/EURGBP_M15_from_mt5.csv`

