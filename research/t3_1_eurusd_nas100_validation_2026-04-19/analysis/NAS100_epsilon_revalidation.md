# NAS100 — T7 Epsilon Revalidation (A2/A3, session 35)

**Symbol:** NAS100  
**Legacy `_FILL_EPSILON`:** 0.05 (hardcoded pre-session-35)  
**Honest `_FILL_EPSILON`:** 2.0 (per-instrument from `EPSILON_BY_SYMBOL`)  
**Records replayed:** 1600 total — 37 CANDIDATE, 84 REJECTED_L2, 82 BLOCKED_LIMIT.

Degenerate records (entry=SL or entry=TP or SL=TP) are counted separately; their phantom `WIN r=0` outcome under the original sim is excluded from WR / sumR / expR.

---

### CANDIDATE (n=37) — accepted trades

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 37 | 37 | 0 |
| n_degenerate | 0 | 0 | 0 |
| n_real | 37 | 37 | 0 |
| W | 22 | 22 | 0 |
| L | 11 | 11 | 0 |
| UNFILLED | 4 | 4 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 33 | 33 | 0 |
| WR% | 66.7 | 66.7 | 0.0 |
| sumR | 22.03 | 22.03 | 0.0 |
| expR | 0.595 | 0.595 | 0.0 |

### CANDIDATE — outcome transitions (old → new)

| old | new | count |
|---|---|---:|
| WIN | WIN | 22 |
| LOSS | LOSS | 11 |
| UNFILLED | UNFILLED | 4 |

### REJECTED_L2 (n=84) — counterfactual if all L2 rejects had traded

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 84 | 84 | 0 |
| n_degenerate | 0 | 0 | 0 |
| n_real | 84 | 84 | 0 |
| W | 37 | 37 | 0 |
| L | 47 | 47 | 0 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 84 | 84 | 0 |
| WR% | 44.0 | 44.0 | 0.0 |
| sumR | 8.5 | 8.5 | 0.0 |
| expR | 0.101 | 0.101 | 0.0 |

### REJECTED_L2 bucket breakdown (symbol=NAS100, new eps=2.0)

| l2_reason | N | old.sumR | old.expR | new.sumR | new.expR | ΔsumR |
|---|---:|---:|---:|---:|---:|---:|
| sl_beyond_ob | 46 | 19.0 | 0.413 | 19.0 | 0.413 | 0.0 |
| h1_poi_exists | 32 | -4.5 | -0.141 | -4.5 | -0.141 | 0.0 |
| entry_in_ob | 5 | -5.0 | -1.0 | -5.0 | -1.0 | 0.0 |
| m15_choch_exists | 1 | -1.0 | -1.0 | -1.0 | -1.0 | 0.0 |

### BLOCKED_LIMIT (n=82) — counterfactual if all KZ/day blocks had traded

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 82 | 82 | 0 |
| n_degenerate | 0 | 0 | 0 |
| n_real | 82 | 82 | 0 |
| W | 43 | 43 | 0 |
| L | 24 | 24 | 0 |
| UNFILLED | 15 | 15 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 67 | 67 | 0 |
| WR% | 64.2 | 64.2 | 0.0 |
| sumR | 40.62 | 40.62 | 0.0 |
| expR | 0.495 | 0.495 | 0.0 |

### BLOCKED_LIMIT bucket breakdown (symbol=NAS100, new eps=2.0)

| block_reason | N | old.sumR | old.expR | new.sumR | new.expR | ΔsumR |
|---|---:|---:|---:|---:|---:|---:|
| max_kz_trades | 60 | 31.62 | 0.527 | 31.62 | 0.527 | 0.0 |
| max_daily_trades_sim | 22 | 9.0 | 0.409 | 9.0 | 0.409 | 0.0 |

---

## Focus #1 — `sl_beyond_ob` L2 bucket (n=46)

The +13.5R standalone / +20.50R joint NAS100 claim from session 33.

### sl_beyond_ob

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 46 | 46 | 0 |
| n_degenerate | 0 | 0 | 0 |
| n_real | 46 | 46 | 0 |
| W | 26 | 26 | 0 |
| L | 20 | 20 | 0 |
| UNFILLED | 0 | 0 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 46 | 46 | 0 |
| WR% | 56.5 | 56.5 | 0.0 |
| sumR | 19.0 | 19.0 | 0.0 |
| expR | 0.413 | 0.413 | 0.0 |

### sl_beyond_ob — outcome transitions (old → new)

| old | new | count |
|---|---|---:|
| WIN | WIN | 26 |
| LOSS | LOSS | 20 |

---

## Focus #2 — `max_kz_trades` BLOCKED_LIMIT bucket (n=60)

The +16.02R claim from NAS100 T3.1. Includes dupes (same setup re-fires in same KZ); not deduped here.

### max_kz_trades

| Metric | Legacy eps=0.05 | Honest eps | Δ |
|---|---:|---:|---:|
| n_total | 60 | 60 | 0 |
| n_degenerate | 0 | 0 | 0 |
| n_real | 60 | 60 | 0 |
| W | 33 | 33 | 0 |
| L | 18 | 18 | 0 |
| UNFILLED | 9 | 9 | 0 |
| OPEN | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| resolved | 51 | 51 | 0 |
| WR% | 64.7 | 64.7 | 0.0 |
| sumR | 31.62 | 31.62 | 0.0 |
| expR | 0.527 | 0.527 | 0.0 |

### max_kz_trades — outcome transitions (old → new)

| old | new | count |
|---|---|---:|
| WIN | WIN | 33 |
| LOSS | LOSS | 18 |
| UNFILLED | UNFILLED | 9 |

---

## Interpretation

* **Old eps (0.05)** is the NAS100 T3.1 / EURUSD T3.1 regime — same numbers reported in the session 33/34 synthesis docs.
* **New eps** replays identical record set with honest per-instrument fill geometry.
* **ΔsumR** on NAS100 should be modest (0.05 ≈ a tenth of a point is ~tight enough on an index); if ΔsumR on CANDIDATE set ≤ ±1R, the T3.1 CANDIDATE WR stands.
* **ΔsumR** on EURUSD should be large: 0.05 = 500 pips on EURUSD — every limit was at-market under legacy, so most 'WIN at legacy' records flip to UNFILLED under honest 2-pip eps.
* **The `sl_beyond_ob` focus block is the T2.9 gate-fix decision evidence** — we re-check whether the NAS100 +13.5R claim survives honest eps.
