# Lane G receipts

Independent verification of the wave-21 funnel findings (2026-08-12). Every script here reads
only sealed/cached inputs and writes only to `/private/tmp`; nothing touches a live path.

| script | what it establishes |
|---|---|
| `laneg_walk.py` | the three-arm walk: ORIG (control, reproduces Phase 0 exactly), **MIRROR** (direction flipped, geometry preserved — the assumption-free control), INV (Phase 0's inverted contract). Writes `/private/tmp/laneG-walk/lg_{month}.pkl.gz`. |
| `extract.py` | compact `pool_table.npz` from the five-month puzzle cache. |
| `bench_from_p0.py` | reproduces `p0_full.driftless_p` verbatim, then applies the quote-frame correction. → `bench_p0_vs_corrected.json` |
| `frame_check2.py` | the per-row identity proving the fill sits on the executable ENTRY side and the barriers on the EXIT side (exact on 98.3–98.7 % of barrier rows). |
| `mirror.py` | RR=2.0 verification at scale, control vs Phase 0's walk, raw paired mirror test. → `mirror_result.json` |
| `mirror2.py` | mirror test adjusted for the LONG/SHORT geometry asymmetry (difference in differences). → `mirror_adjusted.json` |
| `mirror3.py` | the assumption-free geometry-matched endorsed-vs-opposed test + economics. → `mirror_geometry_matched.json` |
| `martingale.py` | `E[gross] = −E[spread_r]` for a driftless tape, both arms, full and cost-eligible. → `martingale.json` |
| `pool_null.py` | the pool scan under two defensible nulls (cell-label permutation within month; month-label permutation within cell). → `pool_null.json` |
| `pool_edge.py` | the pool question restated on the cost-free edge `net + cost_r`, with a BH-corrected cell search. → `pool_edge.json` |
| `reconcile.py` | Lane C vs Lane E: cost-free expectancy by resolution type + the corridor control. → `reconcile.json` |
| `residual_probe.py` | tests the gap-censoring mechanism, the paired direction control, and family stationarity. |
| `power.py`, `final_checks.py` | selected-book CIs, ANOVA, minimum detectable edge, trades-needed. → `power.json` |

Run order: `laneg_walk.py` → `extract.py` → everything else. Reports:
`../LANE_G_INDEPENDENT_VERIFICATION_V1.md` and `../LANE_G_RECONCILIATION_V1.md`.
