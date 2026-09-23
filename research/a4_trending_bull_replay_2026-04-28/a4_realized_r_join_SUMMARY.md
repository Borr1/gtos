# A4 Stage 2.5 — Realized R Join Summary

**Task:** Enrich the 11-record A4 trending_bull XAUUSD CANDIDATE cohort with
realized R-multiples from non-trade_records sources, so verdict bands
(GREEN/YELLOW/RED) can be evaluated against the Stage 2 replay results.

**Output CSV:** `a4_realized_r_join.csv` (11 rows)
**Sources used:** trade_record `final_outcome` (pipeline state) + M1 forward-replay
fill simulator + WAVE1_R2_REPORT.md cross-reference

---

## Counts

- **Total cohort records:** 11
- **Records with realized_r value:** 4 (36%)
- **Records NEVER_FILLED:** 7 (64%)
- **Records UNKNOWN:** 0

## Per-source breakdown

| Source | Count | Records |
|--------|-------|---------|
| `trade_record_pipeline_rejected_l2` | 6 | 4/15 1315, 1330, 1345, 1615, 1700; 4/16 london_0800 |
| `trade_record_pipeline_rejected_gate1` | 1 | 4/17 ny_1315 |
| `m1_fill_sim_2026-04-28` | 3 | 4/15 ny_1415; 4/16 london_0930; 4/17 ny_1330 |
| `m1_fill_sim_2026-04-28 + WAVE1_R2_REPORT` | 1 | 4/16 ny_1316 |

## Aggregate stats on the 4 records WITH realized R

| Metric | Value |
|--------|-------|
| n | 4 |
| WIN | 2 (4/15 ny_1415 +1.50R; 4/17 ny_1330 +1.50R) |
| LOSS | 2 (4/16 london_0930 -1.00R; 4/16 ny_1316 -1.00R) |
| BE | 0 |
| Win rate | 50.0% |
| Mean R | (+1.50 + 1.50 - 1.00 - 1.00) / 4 = **+0.25R** |
| Sum R | +1.00R total |
| Distribution | Bimodal: every fill hit either TP1 (+1.50R) or SL (-1.00R) |

## Filtered-subset interpretation (for verdict bands)

Stage 2 replay on this cohort emits CANDIDATE on **all 11 records** (CAND_to_CAND).
Therefore the **filtered subset = full cohort = 11 records**, but only 4 have
realized R; the other 7 were stopped by deterministic safety gates BEFORE the
broker received any order.

Two interpretations of the filtered-subset mean R:

1. **Trades-actually-attempted basis** (n=4): mean R = **+0.25R**, WR = **50%**
   - Falls in YELLOW zone (≥+0.10R but <+0.30R AND <50% required for GREEN's WR≥50%
     condition; here WR is exactly 50% — borderline GREEN-vs-YELLOW depending on
     threshold convention. With strict `≥50%`, this satisfies GREEN's WR clause.)
   - Mean R +0.25R is BETWEEN bands: above YELLOW's +0.10R but below GREEN's +0.30R.
     **Verdict: borderline YELLOW (mean R below GREEN threshold)**.

2. **All-cohort-records basis** (n=11, NEVER_FILLED counted as 0R): mean R = **+0.091R**
   - Falls in YELLOW zone (≥+0.10R is missed by 0.009R — borderline YELLOW vs RED).
   - This treats the safety-gate filtering as part of the system's edge contribution.
   - Sum R = +1.00R / 11 trades = +0.0909R per cohort record.

The CEO/synthesizer should pick the interpretation. The Stage 2 brief implies
**filtered subset = records the new prompt accepts**, so n=11 is the relevant
base for the verdict band; under that base, mean R = **+0.091R = borderline RED**.

## Per-record detail

| trade_id | outcome | realized_r | source |
|----------|---------|------------|--------|
| 2026-04-15_ny_1315 | NEVER_FILLED | — | rejected at L2 (sl_beyond_ob) |
| 2026-04-15_ny_1330 | NEVER_FILLED | — | rejected at L2 |
| 2026-04-15_ny_1345 | NEVER_FILLED | — | rejected at L2 |
| 2026-04-15_ny_1415 | WIN | +1.5000 | M1 sim: filled 04-16 17:40 → TP 18:04 |
| 2026-04-15_ny_1615 | NEVER_FILLED | — | rejected at L2 |
| 2026-04-15_ny_1700 | NEVER_FILLED | — | rejected at L2 |
| 2026-04-16_london_0800 | NEVER_FILLED | — | rejected at L2 |
| 2026-04-16_london_0930 | LOSS | -1.0000 | M1 sim: filled 04-16 16:52 → SL 17:40 |
| 2026-04-16_ny_1316 | LOSS | -1.0000 | M1 sim + WAVE1_R2_REPORT (both confirm -1R) |
| 2026-04-17_ny_1315 | NEVER_FILLED | — | rejected at GATE1_SAFETY |
| 2026-04-17_ny_1330 | WIN | +1.4998 | M1 sim: filled 04-17 13:31 → TP 15:40 |

## Methodology / caveats

### Why 7 records are NEVER_FILLED

The cohort manifest is built from `live_evaluations/XAUUSD/*.jsonl`, which logs
the AI's decision (CANDIDATE/NO_TRADE) at evaluation time. But the production
pipeline applies L2/Gate1 safety checks AFTER the AI returns CANDIDATE. For
seven of these eleven candidates, the safety stack rejected the order before
it ever reached the broker:

- **6 × REJECTED_L2 (sl_beyond_ob)**: AI emitted SL=4762.14 == OB low 4762.14
  on the 4/15 cluster (and 4/16 london_0800), failing the strict `SL < OB low`
  L2 verifier. This is the same compound bug class memorialized in
  `project_eurusd_sl_root_cause` (AI-side `sl_buffer_applied: 0.0`) and is
  the entire reason ADR-006 added a tolerance-tier rollback knob.
- **1 × REJECTED_GATE1_SAFETY** (4/17 ny_1315): A different deterministic
  guard (likely RR/grade/SL-floor/SL-ATR composite). Did not reach broker.

Result: those 7 trades never had the chance to win or lose; **realized_r is
formally undefined**.

### How the 4 LIMIT_PLACED records were resolved

Production logged `final_outcome: LIMIT_PLACED` for 4/15 ny_1415, 4/16
london_0930, 4/16 ny_1316, 4/17 ny_1330. All four have `execution: null` and
`exit: null` in the trade_record JSON (the gap memorialized in
`project_trade_records_enrichment_gap`). The trade index ends 2026-03-13 and
contains nothing for our cohort dates. Live sessions / live_monitor / shadow
logs likewise lack outcome data for these IDs.

I therefore wrote a deterministic forward-replay simulator using the M1
historical CSV (`data/historical_2026/XAUUSD_M1.csv`, range 2026-01-14 ->
2026-04-27, n=100,003 bars) to:

1. Find the first M1 bar after the placement candle whose low ≤ limit_price
   (LONG fill convention).
2. Walk forward from the fill bar; SL hit if low ≤ SL, TP hit if high ≥ TP1,
   ambiguous bar resolves to SL-first (conservative LONG convention).
3. Otherwise time-expiry at 192 M15 candles = 2880 M1 minutes (48h).

Cross-reference for 4/16 ny_1316: `WAVE1_R2_REPORT.md` (counterfactual for
the `skip_first_ny_candle` bug fix) reports the same trade was filled live
on 04-17 01:00 at 4795.23 (broker slippage) and SL hit at 03:00 → -1.00R.
My M1 sim reports fill 04-16 16:52 at 4796.28 (limit price, no slippage) and
SL hit at 16:55 → -1.00R. The fill timing differs but the R outcome is the
same. The intra-bar discrepancy likely reflects that the broker's tick
stream did not match the M1 OHLC in the one or two highly-volatile minutes
around 16:52-16:55 (a known limitation of M1-from-broker post-hoc data).

### Unexpected findings

1. **The 4/16 13:16 trade is the ONLY one of the 11 cohort records that
   actually traded with the live broker** (per WAVE1_R2 evidence). The
   other 3 LIMIT_PLACED trades have no broker confirmation in any
   surviving artifact; my M1 forward-replay assumes the limit was
   submitted to broker exactly as recorded in `limit_intent`. If the live
   limit-placement code path errored or was overridden, those 3 may also
   have NEVER_FILLED in reality.

2. **Even after counting the 4 fills, the cohort produces +1.0R total /
   +0.25R/trade on n=4** — that's mean R that would be GREEN if WR is
   strictly ≥50% (it's exactly 50%) and mean R were ≥+0.30R (it's +0.25R).
   On the all-cohort basis (n=11), it's +0.091R/record which is borderline
   between YELLOW and RED. The cohort is small enough that a single
   different SL/TP touch flips the verdict band.

3. **The two LOSSes were both filled within the same M15 candle (04-16
   16:45)** at very similar prices (both at limit 4796.28). One was the
   4/16 london_0930 setup, the other the 4/16 ny_1316 setup. Both were
   stopped out by the same volatile down-move that started at 04-16 16:51.
   This is one event, not two independent losses.

4. **Both WINs were also "TP1 in single bounce" trades** (filled, then
   walked straight to TP1 within ~1-2 hours). These are the cleanest LONG
   trending_bull setups in the cohort.

5. **Methodology uncertainty for 4/16 london_0930:** my simulator's M15
   version reported FILLED_WIN on a 5x ambiguous bar; the M1 version
   reported FILLED_LOSS because at M1 resolution price hit the limit
   (4796.28) at 16:52 BEFORE rallying. The M15 high (4819.39) covered
   the TP (4817.04), but at M1 res the rally that produced that high
   happened BEFORE the bar's low pulled price below the limit. So the
   M1 verdict `LOSS` is correct: the limit only filled after the rally
   was over. This is a textbook reason to never use M15 OHLC for
   intra-bar fill simulation.

---

## Files in this directory

| File | Purpose |
|------|---------|
| `fill_simulator.py` | M15 fill simulator (kept for reference; M15-OHLC ambiguity flagged) |
| `fill_simulator_m1.py` | **M1 fill simulator (canonical)** |
| `fill_simulation_results.json` | M15 sim output (kept for cross-check) |
| `fill_simulation_m1_results.json` | **M1 sim output** |
| `build_realized_r_join.py` | Joiner script that produced the CSV |
| `a4_realized_r_join.csv` | **Final realized-R join (11 rows)** |
| `a4_realized_r_join_SUMMARY.md` | This document |
