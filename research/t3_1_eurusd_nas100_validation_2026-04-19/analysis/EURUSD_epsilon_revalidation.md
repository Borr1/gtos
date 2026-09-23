# EURUSD — T7 Epsilon Revalidation (A2/A3, session 35)

**Symbol:** EURUSD  
**Legacy `_FILL_EPSILON`:** 0.05 (hardcoded pre-session-35)  
**Honest `_FILL_EPSILON`:** 0.0002 (per-instrument from `EPSILON_BY_SYMBOL`)  
**Records replayed:** 2280 total — 9 CANDIDATE, 253 REJECTED_L2, 38 BLOCKED_LIMIT.

Degenerate records (entry=SL or entry=TP or SL=TP) are counted separately; their phantom `WIN r=0` outcome under the original sim is excluded from WR / sumR / expR.

---

### CANDIDATE (n=9) — accepted trades

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 9 | 9 | 0 |
| n_degenerate | 4 | 4 | 0 |
| n_real | 5 | 5 | 0 |
| W | 4 | 0 | -4 |
| L | 1 | 5 | 4 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 5 | 5 | 0 |
| WR% | 80.0 | 0.0 | -80.0 |
| sumR | 5.17 | -5.0 | -10.17 |
| expR | 1.034 | -1.0 | -2.034 |

### CANDIDATE — outcome transitions (old → new)

| old | new | count |
|---|---|---:|
| WIN | LOSS | 4 ← FLIPPED |
| LOSS | LOSS | 1 |

### REJECTED_L2 (n=253) — counterfactual if all L2 rejects had traded

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 253 | 253 | 0 |
| n_degenerate | 152 | 152 | 0 |
| n_real | 101 | 101 | 0 |
| W | 88 | 43 | -45 |
| L | 13 | 58 | 45 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 101 | 101 | 0 |
| WR% | 87.1 | 42.6 | -44.5 |
| sumR | 203.97 | 6.18 | -197.79 |
| expR | 2.02 | 0.061 | -1.959 |

### REJECTED_L2 bucket breakdown (symbol=EURUSD, new eps=0.0002)

| l2_reason | N | old.sumR | old.expR | new.sumR | new.expR | ΔsumR |
|---|---:|---:|---:|---:|---:|---:|
| h1_poi_exists | 155 | 149.45 | 1.679 | 15.68 | 0.176 | -133.77 |
| sl_beyond_ob | 81 | 55.02 | 6.113 | -9.0 | -1.0 | -64.02 |
| entry_in_ob | 13 | -0.5 | -0.167 | -0.5 | -0.167 | 0.0 |
| m15_choch_exists | 4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### BLOCKED_LIMIT (n=38) — counterfactual if all KZ/day blocks had traded

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 38 | 38 | 0 |
| n_degenerate | 23 | 23 | 0 |
| n_real | 15 | 15 | 0 |
| W | 10 | 1 | -9 |
| L | 5 | 14 | 9 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 15 | 15 | 0 |
| WR% | 66.7 | 6.7 | -60.0 |
| sumR | 10.17 | -12.33 | -22.5 |
| expR | 0.678 | -0.822 | -1.5 |

### BLOCKED_LIMIT bucket breakdown (symbol=EURUSD, new eps=0.0002)

| block_reason | N | old.sumR | old.expR | new.sumR | new.expR | ΔsumR |
|---|---:|---:|---:|---:|---:|---:|
| max_kz_trades | 32 | 1.17 | 0.13 | -6.33 | -0.703 | -7.5 |
| max_daily_trades_sim | 6 | 9.0 | 1.5 | -6.0 | -1.0 | -15.0 |

---

## Focus #1 — `sl_beyond_ob` L2 bucket (n=81)

The +13.5R standalone / +20.50R joint NAS100 claim from session 33.

### sl_beyond_ob

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 81 | 81 | 0 |
| n_degenerate | 72 | 72 | 0 |
| n_real | 9 | 9 | 0 |
| W | 9 | 0 | -9 |
| L | 0 | 9 | 9 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 9 | 9 | 0 |
| WR% | 100.0 | 0.0 | -100.0 |
| sumR | 55.02 | -9.0 | -64.02 |
| expR | 6.113 | -1.0 | -7.113 |

### sl_beyond_ob — outcome transitions (old → new)

| old | new | count |
|---|---|---:|
| WIN | LOSS | 9 ← FLIPPED |

---

## Focus #2 — `max_kz_trades` BLOCKED_LIMIT bucket (n=32)

The +16.02R claim from NAS100 T3.1. Includes dupes (same setup re-fires in same KZ); not deduped here.

### max_kz_trades

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 32 | 32 | 0 |
| n_degenerate | 23 | 23 | 0 |
| n_real | 9 | 9 | 0 |
| W | 4 | 1 | -3 |
| L | 5 | 8 | 3 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 9 | 9 | 0 |
| WR% | 44.4 | 11.1 | -33.3 |
| sumR | 1.17 | -6.33 | -7.5 |
| expR | 0.13 | -0.703 | -0.833 |

### max_kz_trades — outcome transitions (old → new)

| old | new | count |
|---|---|---:|
| LOSS | LOSS | 5 |
| WIN | LOSS | 3 ← FLIPPED |
| WIN | WIN | 1 |

---

## Interpretation

* **Old eps (0.05)** is the NAS100 T3.1 / EURUSD T3.1 regime — same numbers reported in the session 33/34 synthesis docs.
* **New eps** replays identical record set with honest per-instrument fill geometry.
* **ΔsumR** on NAS100 should be modest (0.05 ≈ a tenth of a point is ~tight enough on an index); if ΔsumR on CANDIDATE set ≤ ±1R, the T3.1 CANDIDATE WR stands.
* **ΔsumR** on EURUSD should be large: 0.05 = 500 pips on EURUSD — every limit was at-market under legacy, so most 'WIN at legacy' records flip to UNFILLED under honest 2-pip eps.
* **The `sl_beyond_ob` focus block is the T2.9 gate-fix decision evidence** — we re-check whether the NAS100 +13.5R claim survives honest eps.
