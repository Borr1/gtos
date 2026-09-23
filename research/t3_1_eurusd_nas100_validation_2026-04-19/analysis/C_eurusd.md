# EURUSD T7 Simulation — L2 Verification + BLOCKED_LIMIT Counterfactual

**Scope:** the 253 REJECTED_L2 records (AI said CANDIDATE but L2 verification.py rejected) + 38 BLOCKED_LIMIT records (L1+L2 passed but KZ/daily cap blocked). Goal: do the NAS100 leaks (sl_beyond_ob strict-`<`, max_kz_trades cap) replicate here, and would relaxing them add R?

**Data:** 2280 records → 253 REJECTED_L2 + 38 BLOCKED_LIMIT.

---

## TL;DR (5 bullets)

1. **The NAS100 sl_beyond_ob leak technically replicates on EURUSD in direction (42 LONG bit-exact rejects there → 81 LONG bit-exact rejects here, 100% LONG skew), but 89% of EURUSD's sl_beyond_ob rejects (72 of 81) are AI 2-decimal-place output degenerate records where entry=SL=TP are all the same rounded price.** Only 9 real (non-degenerate) sl_beyond_ob rejects exist, and they are 9 re-firings of ONE Feb 10 event (same entry 1.18, same SL 1.1797, same OB collision on zone_low=1.18).
2. **CSV replay of the 9 real sl_beyond_ob rejects at sim-faithful `_FILL_EPSILON = 0.05` gives 9 WIN / +55.02R (huge apparent edge). At a sane 1-pip epsilon (0.0001), the same 9 trades flip to 9 LOSS / -9.00R. The "leak" is 100% fill-epsilon artefact.** This is the dominant methodological finding of the angle and — per my reading — the dominant finding of the entire EURUSD validation.
3. **h1_poi_exists rejects (155 total, 89 real after dedup) show the same pattern:** eps=0.05 → 78W / 11L / +149.45R; eps=0.0001 → 42W / 47L / +15.68R. All 89 LONG. De-duplicated to 20 distinct setups. The edge that appears under sim-faithful fill-epsilon evaporates under 1-pip.
4. **BLOCKED_LIMIT: 38 records → 9 distinct setups → 6 overlap already-accepted CANDs → 3 novel setups.** Of those 3, 1 is degenerate (SHORT E=SL=TP), 2 are real. Replaying the 2 real novel blocked-limit setups gives +0.67R combined (1 WIN +1.67R, 1 LOSS -1.00R). **The max_kz_trades cap relaxation is worth ~0-2R on EURUSD, not the +16R it was worth on NAS100. The cap is not the bottleneck here.**
5. **Joint counterfactual (relax both gates): +55R sl_beyond_ob + ~+1R BLOCKED_LIMIT = +56R at sim-faithful epsilon → +5-6R at 1-pip epsilon on the 11-trade joint set.** Even on the most charitable reading, this is not a deployable edge after dedup, degenerate-stripping, and epsilon correction.

---

## 1 — REJECTED_L2 full taxonomy

### 1a. Category breakdown (253 total)

| l2_reason category | total | degenerate | real | LONG | SHORT |
|---|---|---|---|---|---|
| h1_poi_exists | 155 | 66 | 89 | 155 | 0 |
| sl_beyond_ob | 81 | 72 | 9 | 81 | 0 |
| entry_in_ob | 13 | 10 | 3 | 13 | 0 |
| m15_choch_exists | 4 | 4 | 0 | 0 | 4 |

**Red flag: 152 of 253 REJECTED_L2 (60.1%) are degenerate** — AI emitted entry=SL=TP. Same pattern as the CAND set: 2-dp AI rounding on a 4-dp instrument produces zero-risk geometries that the gate correctly rejects but that carry no trading information.

**Second red flag: 99.6% of non-degenerate L2 rejects are LONG** — 252 of 253 total, 4 SHORT (all degenerate m15_choch_exists). The pipeline is producing LONG-only candidate trades after the AI gate on EURUSD.

### 1b. Real sl_beyond_ob: one event, 9 re-firings

The 9 "real" sl_beyond_ob rejects ALL fire on 2026-02-10 between 07:00 and 11:45 UTC:

| t | dir | entry | SL | TP | reason |
|---|---|---|---|---|---|
| 2026-02-10 07:00 | LONG | 1.18 | 1.1797 | 1.1845 | sl_beyond_ob: SL 1.18 is NOT below OB low 1.18 |
| 2026-02-10 07:30 | LONG | 1.18 | 1.1797 | 1.1805 | same |
| 2026-02-10 08:00 | LONG | 1.18 | 1.1797 | 1.1805 | same |
| 2026-02-10 08:15 | LONG | 1.18 | 1.1797 | 1.1845 | same |
| 2026-02-10 08:30 | LONG | 1.18 | 1.1797 | 1.1805 | same |
| 2026-02-10 09:00 | LONG | 1.18 | 1.1797 | 1.1805 | same |
| 2026-02-10 09:15 | LONG | 1.18 | 1.1797 | 1.1845 | same |
| 2026-02-10 09:45 | LONG | 1.18 | 1.1797 | 1.1805 | same |
| 2026-02-10 11:45 | LONG | 1.18 | 1.1797 | 1.1805 | same |

**This is ONE trading event** — the AI locked on to a level and re-evaluated it for ~5 hours. The `l2_reason` string displays "SL 1.18 is NOT below OB low 1.18" because `verification.py` prints with `{sl:.2f}` (confirmed at lines 525, 530, 539, 544 in `src/components/verification.py`), which hides the 4th-dp precision. The actual comparison is `1.1797 < 1.18` (true) but the OB-zone low is computed from the M15 candles and happens to round-down-to-1.18000 (bit-exact collision — the identical pattern NAS100 Angle C identified).

Independent event count for this "leak": **1**. Not 9. Not 81.

### 1c. Real h1_poi_exists — 89 records / 20 distinct setups

Distinct non-degenerate setups (first 15 shown):

| date | dir | entry | SL | TP |
|---|---|---|---|---|
| 2026-01-27 | LONG | 1.19 | 1.1885 | 1.1923 |
| 2026-01-28 | LONG | 1.19 | 1.187 | 1.1945 |
| 2026-01-28 | LONG | 1.19 | 1.1897 | 1.1905 |
| 2026-01-29 | LONG | 1.19 | 1.187 | 1.1945 |
| 2026-01-29 | LONG | 1.19 | 1.1897 | 1.1905 |
| 2026-01-29 | LONG | 1.19 | 1.1897 | 1.1945 |
| 2026-01-30 | LONG | 1.19 | 1.187 | 1.1945 |
| 2026-01-30 | LONG | 1.19 | 1.1897 | 1.1905 |
| 2026-02-02 | LONG | 1.18 | 1.177 | 1.1845 |
| 2026-02-02 | LONG | 1.1818 | 1.1785 | 1.1868 |
| 2026-02-02 | LONG | 1.19 | 1.187 | 1.1945 |
| 2026-02-03 | LONG | 1.1757 | 1.1727 | 1.1802 |
| 2026-02-03 | LONG | 1.18 | 1.1797 | 1.1805 |
| 2026-02-04 | LONG | 1.18 | 1.1797 | 1.1805 |
| 2026-02-05 | LONG | 1.18 | 1.1797 | 1.1805 |
| (5 more) | | | | |

20 distinct setups across 89 records → 4.5× re-firing factor. Contrast with NAS100 h1_poi_exists dedup (also ~4× from memory).

---

## 2 — CSV replay counterfactual at two fill-epsilon values

Replay tool: `_scratch/eurusd_replay.py`, mirrors `scripts/simulate_t7_live_period.py::compute_outcome()` bit-exact. Every rejected setup replayed on `data/historical_2026/EURUSD_M15.csv` as if L2 had passed.

### 2a. sl_beyond_ob real (n=9, dedup to 1 independent event)

| fill_epsilon | WIN | LOSS | UNF | OPEN | totalR |
|---|---|---|---|---|---|
| 0.05 (sim-faithful) | 9 | 0 | 0 | 0 | **+55.02** |
| 0.0001 (1 pip) | 0 | 9 | 0 | 0 | **-9.00** |

**Delta: 64R difference** — the entire apparent edge is in the fill-epsilon. At sim-faithful epsilon, the limits fill at-market on the signal candle and the subsequent bars carry price up to TP. At 1-pip epsilon, price must come back down to the 1.18 limit before the limit is triggered (and did not within 9 trades' observation windows, so they turned into straight losses when the 1.1797 SL eventually printed).

After dedup to 1 independent event and applying the 1-pip epsilon, the "leak" contribution is **-1R at best** (one trade, direction wrong, SL hit).

### 2b. h1_poi_exists real (n=89, dedup to 20)

| fill_epsilon | WIN | LOSS | totalR | WR |
|---|---|---|---|---|
| 0.05 | 78 | 11 | +149.45 | 87.6% |
| 0.0001 | 42 | 47 | +15.68 | 47.2% |

**Delta: 134R** from fill-epsilon alone. WR drops from 87.6% to 47.2% — below breakeven.

On the dedup-to-20 set, 1-pip epsilon would project to roughly +3.5R total (20 setups × 0.175R/setup average). This is the cleanest counterfactual estimate: the h1_poi_exists gate, if relaxed to allow "AI-cited POI doesn't match a bit-exact unmitigated OB," adds at most ~3R/quarter after correcting for epsilon + dedup. Not deployable.

### 2c. entry_in_ob real (n=3)

All 3 are degenerate-adjacent: entry 1.16 "outside OB zone 1.17-1.17", entry 1.18 "outside OB zone 1.19-1.19", etc. Distinct setups. At sim eps=0.05 all 3 WIN (symmetric issue), at 1-pip eps all 3 UNFILLED (the entry never touches — classic "far limit" problem).

### 2d. m15_choch_exists real (n=0)

All 4 are degenerate SHORTs. Nothing to replay.

---

## 3 — BLOCKED_LIMIT analysis

### 3a. Full 38 → 9 distinct → 3 novel dedup

| t | dir | E | SL | TP | degen | also CAND? |
|---|---|---|---|---|---|---|
| 2026-01-07 10:00 | SHORT | 1.17 | 1.17 | 1.17 | YES | yes |
| 2026-01-23 11:15 | LONG | 1.16 | 1.157 | 1.1645 | no | yes |
| 2026-01-23 11:30 | LONG | 1.16 | 1.1597 | 1.1605 | no | **novel** |
| 2026-02-04 07:15 | LONG | 1.18 | 1.18 | 1.18 | YES | yes (degen CAND) |
| 2026-02-10 07:45 | LONG | 1.18 | 1.177 | 1.1845 | no | yes (dedup dup of 07:15 CAND) |
| 2026-02-23 08:30 | LONG | 1.18 | 1.17 | 1.19 | no | yes (dedup dup) |
| 2026-02-23 09:45 | LONG | 1.18 | 1.17 | 1.185 | no | **novel** |
| 2026-03-02 08:15 | SHORT | 1.18 | 1.18 | 1.17 | no | **novel** |
| 2026-03-06 14:15 | SHORT | 1.16 | 1.16 | 1.16 | YES | yes (degen CAND) |

- 38 BLOCKED_LIMIT → 9 distinct → **3 novel setups** (not already in CAND set).
- Of 3 novel: 1 degenerate (Mar 2 SHORT E=SL=1.18), 2 real LONG/SHORT.

### 3b. Replay of 3 novel BLOCKED_LIMIT setups

| t | dir | geometry | outcome eps=0.05 | outcome eps=0.0001 |
|---|---|---|---|---|
| 2026-01-23 11:30 | LONG | E=1.16 SL=1.1597 TP=1.1605 | WIN +1.67R | WIN +1.67R |
| 2026-02-23 09:45 | LONG | E=1.18 SL=1.17 TP=1.185 | LOSS -1.00R | LOSS -1.00R |
| 2026-03-02 08:15 | SHORT | E=1.18 SL=1.18 TP=1.17 | UNKNOWN (degen) | UNKNOWN (degen) |

Novel BLOCKED total: **+0.67R** at both epsilons. The 0.03-pip SL on Jan 23 11:30 is too tight to fill-epsilon-dependent, and it naturally exits within 1 M15 bar.

### 3c. max_kz_trades cap relaxation value

NAS100 saw +16.02R from relaxing the cap (counterfactual on 45 distinct blocked trades). EURUSD sees +0.67R on 2 viable relaxed trades. The cap is simply **not the bottleneck on EURUSD** — signal flow is too thin for the 1-per-KZ cap to bite.

---

## 4 — Joint counterfactual (both leaks relaxed)

If we fix BOTH the sl_beyond_ob strict-`<` → `<=` gate AND relax max_kz_trades, the EURUSD sim would additionally accept:

- 9 real sl_beyond_ob (1 independent event) at eps=0.0001: -1R
- 2 real novel BLOCKED_LIMIT: +0.67R
- Joint: **-0.33R** (one independent joint addition to the 5-real CAND set)

At sim-faithful epsilon 0.05: +55R + 0.67R = +55.67R "joint" — but that number is the epsilon artefact inflating a single Feb 10 event.

**Joint honest estimate (1-pip eps + dedup): -0.33R. Unsupportable leak value on EURUSD.**

Compare to NAS100 chairman table:
- NAS100 Leak #1 (sl_beyond_ob): +13.5R standalone
- NAS100 Leak #2 (max_kz relax): +16.02R standalone
- NAS100 Joint: +36.5R

EURUSD "Joint" at sim-faithful eps: +55.67R (but 100% epsilon artefact from 1 Feb 10 event).
EURUSD "Joint" at 1-pip eps: -0.33R.

**The leaks do not replicate as trading opportunities on EURUSD.** What *does* replicate is the underlying L2 gate behavior (LONG-skewed bit-exact collisions + AI hallucination of POIs at round numbers), but the opportunity cost is invisible because the market didn't move enough during the sim.

---

## 5 — The degenerate-record problem (critical)

Not confined to CANDs — it dominates the L2 bucket:

- 60.1% of REJECTED_L2 are degenerate (152/253)
- 59.7% of all AI trade_parameter outputs are degenerate (179/300)
- 44.4% of CANDs are degenerate (4/9)

Root cause: the AI rounds to 2 decimal places on an instrument quoted to 5. When H1 bias is bearish and the OB zone is a single 5-minute candle, the rounded `zone_low` often collapses to the same 2-dp price as `entry` and `SL`, producing E=SL=TP and a trivial "WIN r=0" from the compute_outcome loop.

**This must be fixed in the prompt (force ≥4-dp precision on FX) before any counterfactual analysis on EURUSD is meaningful.** See E/F synthesis.

---

## 6 — Methodology validation

- Replay tool `_scratch/eurusd_replay.py` mirrors `compute_outcome()` line-by-line (SL-before-TP, same fill-epsilon default, tracks fill_candle, handles LONG/SHORT symmetric).
- Added explicit `degenerate_zero_risk` guard that `compute_outcome()` lacks — returns UNKNOWN rather than phantom-WIN. Spot-checked 5 of the 9 CANDs: 5/5 outcomes match sim bit-exact; 4 flagged degenerate (the right answer per trading logic).
- Two epsilons run side-by-side: 0.05 (sim default) and 0.0001 (sane FX 1-pip). Everyone can see the delta.

---

## 7 — What chairman should take

1. **Do NOT claim NAS100 sl_beyond_ob leak replicates on EURUSD with +55R.** That number is a fill-epsilon artefact. The honest estimate is ~-1R after epsilon + dedup.
2. **Do NOT claim max_kz_trades cap relaxation is worth the complexity on EURUSD.** +0.67R on 2 trades is noise.
3. **The degenerate-record problem is a blocker for any EURUSD counterfactual analysis.** Fix the AI prompt (4-dp precision on FX) BEFORE running another EURUSD simulation.
4. **The `_FILL_EPSILON = 0.05` constant at `scripts/simulate_t7_live_period.py:462` is mis-calibrated for FX.** On XAUUSD/NAS100 it's "0.05 points" ≈ 5 cents; on EURUSD it's 0.05 price units = 500 pips = at-market-everything. This is a sim-engine bug, not a model issue.
5. **The cross-instrument leak pattern (LONG-skewed bit-exact-OB-low collisions) is real, but the R-value flagged on NAS100 is instrument-specific and does not transfer.** T2.9 (gate fix) remains defensible on NAS100 grounds, but cannot be claimed as "cross-instrument verified" on this evidence.
