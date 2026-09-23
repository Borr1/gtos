# A2-verify — Lane FC (Sol exit overlays)

Fable verification agent, FA-continuation Phase A2. Verified 2026-08-03.

**February authority**: every February figure below is ATTRIBUTION-ONLY under
`owner_mandate_20260801` — read solely to recompute FC's frozen-rule attribution
number; nothing was fitted, ranked, or selected on February. No March 2026 data
and no live-forward (2026-07-29+) outcome was read; every consumed timestamp was
asserted to be 2026-01 or 2026-02.

Sol's receipts are the CLAIMS; the raw tick/M1/ledger data are the EVIDENCE. All
recomputation was done by a fresh implementation of the frozen
`OVERLAY_PROTOCOL.json` semantics (`fc_verify_scan.py` + `fc_verify_replay.py`
here) that imports none of FC's code.

## Verdict table

| # | Claim | Claimed | Recomputed from raw | Verdict |
|---|---|---|---|---|
| FC1.train | best overlay V17 TRAIN | +0.197 ("R/trade" in tasking) | **+0.19712161821747798** total net R, 30-trade TRAIN book | **VERIFIED** (unit caveat below) |
| FC1.holdout | V17 HOLDOUT | −1.920 | **−1.919983256352641** total net R, 27-trade HOLDOUT book | **VERIFIED** |
| FC1.february | V17 February | −0.381 | **−0.38061377136255437** total net R, 58-trade attribution book | **VERIFIED** |
| FC1.q | TRAIN improvement q | 0.486 | **0.4861111111111111** (p 0.119140625 = 122/1024 exact day-block sign-flip over 10 nonzero daily deltas; BH across the 40-cell family) | **VERIFIED** |
| FC1.persistence | 0/40 persist | 0/40 | **0/40** (see below) | **VERIFIED** |
| FC2.registration | FC registered a **sign-convention defect** against **family artifact V17** | — | **no such registration exists anywhere in FC's branch** | **REFUTED as stated** |
| FC2.flip | what actually flipped | — | overlay **cell** V17's book **sign-flips out of sample**: +0.19712 TRAIN → −1.91998 HOLDOUT | **VERIFIED** |
| FC3.family | 40 distinct overlay cells evaluated | 40 | **40** (1 identity + 39 selectable), all evaluated at 30/27/58 rows; BH denominator 40 confirmed numerically | **VERIFIED** |

Tolerance: every recomputed FC1/FC2.flip number equals FC's stored double
exactly (my aggregates match to <1e-12; per-trade vs FC's 10-dp rounded records
max |Δ| 5.0e-11 over 115/115 trades).

**Unit caveat (loud)**: the tasking text says "+0.197 **R/trade**". All three
numbers are executed-book **TOTALS** (30-, 27-, 58-trade books). Per-trade they
are +0.00657 / −0.07111 / −0.00657 R. FC's own receipts state them correctly as
book totals; the "/trade" is the tasking text's mislabel.

## How the recompute was anchored to raw evidence

1. **Trade geometry**: `TRADES_JAN_TABLE.json` (57) and `TRADES_FEB_TABLE.json`
   (58) anchor to the raw engine ledgers
   `CJ_RECLOCKED_S0R0_V7_TRADE_LEDGER.jsonl` and
   `CP_FEBRUARY_TRUE_UTC_S0R0_V1_TRADE_LEDGER.jsonl` — 57/57 and 58/58 composite
   keys, **zero** mismatches on entry_price / stop_loss / cost_r / net_r /
   gross_r / entry_time_utc (`FC_RAW_LEDGER_ANCHOR.json`). The raw lane
   LANE_TRADE_TABLE.jsonl files match identically (57/57, 58/58, 0 mismatches).
2. **Paths**: 8 raw tick jsonl files (Jan+Feb × EURUSD/USDJPY/XAGUSD/XAUUSD)
   streamed byte-complete with sha256 verified against the CJ lane manifests;
   `ts_utc`/`time` textual agreement enforced on every consumed row; 9 raw M1
   CSVs sha256-verified. Paths start strictly after the recorded fill and end at
   decision+120 min, per the frozen protocol.
3. **Split**: 13 TRAIN / 8 HOLDOUT dates read from the upstream
   `CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json` `base_pool` (the frozen source FC used).
4. **Implementation validation**: my V00 identity replay reproduces the raw
   ledger `net_r` on **40/40 January and 51/51 February ordered-tick rows within
   1e-6 R** (max 4.95e-9 / 7.90e-9). M1 rows: Jan 6/15 comparable differ
   (aggregate −0.07556 R), Feb 3/7 differ (aggregate +0.78167 R) — matching FC's
   B3158 to the digit, confirming the M1 fallback is the conservative
   lower-of-two-orderings diagnostic FC scoped it as. Delayed fills 13/24, max
   delays 6062.403 s / 5657.809 s — match.

## FC1 — persistence detail (recomputed)

- Frozen ranking reproduces: top-3 = **V17_GB_T050_G010, V18_GB_T050_G020,
  V19_GB_T050_G030** (descending TRAIN book, then TRAIN improvement, then id).
- Gate components on my numbers: V17 fails TRAIN (q 0.4861 > 0.10), fails
  HOLDOUT (−1.920 < 0), fails February (−0.381 < 0). V18 (−0.150 / −2.754 /
  −0.893) and V19 (−0.995 / −3.392 / −1.289) fail everything.
- Family-wide: exactly **1** cell TRAIN-positive (V17), **5** HOLDOUT-positive
  (V03, V04, V34, V38, V39 — disjoint from V17), **22** February-positive,
  **0** positive on all three, **0** positive on the combined 57-trade January
  book (best combined −1.484 R). Identity book: −4.2945 / −1.3995 / −3.1797.
- Minimum TRAIN improvement q across the 39 selectable cells: **0.2083** — no
  cell clears the 0.10 bar even before holdout/level gates.
- Not recomputed: the side-flip/shuffle null suite (not in the commissioned
  claims; null cleanliness cannot rescue the failed gates).

## FC2 — the "V17 sign flip", precisely

**What is true (VERIFIED from raw data)**: overlay cell `V17_GB_T050_G010`
(tighter giveback, trigger 0.5R, gap 0.1R) **flips the sign of its executed book
across the frozen split**: +0.19712 R TRAIN → −1.91998 R HOLDOUT; its paired
improvement flips too (+4.49167 → −0.52044); February stays negative (−0.38061)
though improvement is +2.79911. FC registered exactly this at
`IMPLEMENTATION_STATE.md` **B3154** and in the result doc; FA cites it as "FC's
0/40 with the V17 sign flip" (`SESSION_FA_CONTINUATION.md:200`,
`SESSION_FA_BROAD_FORENSIC_RESULT.md:72`).

**What is false (REFUTED)**: "FC registered a **sign-convention defect** against
**family artifact V17**". Exhaustive search of every commit diff on
`phase19/sol-exit` (f8c05d0ac..210307687), all five output artifacts, FC's
tests, and blocks B3150–B3160 finds **no sign-convention defect**. The only
"sign flip" in FC's code is the exact one-sided day-block **sign-flip
permutation test**; the only side inversion is the deliberate SIDE_FLIP **null
control**. FC's two registered analyzer defects (both runs invalidated and
preserved by physical hash in `LOOK_MANIFEST.json`) are (R1) pre-fill quote
eligibility on delayed fills and (R2) indexing lane ticks by raw broker-wall
`time_msc` — neither is a sign convention. And `CANDIDATE_FAMILY_V17.json`
(the phase15 candidate-family ledger, declared by CH on 2026-07-31) contains no
sign-convention content — all 16 "sign" hits are `source_bound_signal_r` /
"significance" strings — and FC's 13 changed paths touch no family artifact.
"V17" in FA's phrase is FC's own overlay **cell id**, not the family ledger.

## FC3 — the 40-overlay family (for A4's retro-declaration)

- **Exactly 40 distinct overlay cells**: V00 identity + 39 selectable
  (4 break-even, 12 partial-harvest, 12 tighter-giveback, 3 time-box,
  8 partial-then-break-even). Declared pre-outcome (`declared_family_size: 40`,
  first frozen commit `4ef888ab7`). All 40 carry evaluated results at 30/27/58
  executed rows plus residual/full-pool surfaces; my independent replay
  evaluated the same 40 from the protocol alone.
- **BH denominator 40 confirmed numerically**: the published q = 0.4861111
  reproduces from my own p-vector only with m = 40 (identity at p = 1.0).
- **Look accounting** (all unbilled `FORENSIC_DIAGNOSTIC`): 196 events =
  40 (R0 schema abort) + 52 (R1, invalidated: pre-fill) + 52 (R2, invalidated:
  broker-epoch indexing) + **52 valid final** = 40 cell looks + 12 null looks
  (frozen top-3 × {side-flip, shuffle 1901/1902/1903}). Distinct look
  hypotheses 72 = 40 cells + 8 distinct nulled variants × 4 null types.
- For A4: the SCREENING family is the **40 cells**; the null looks are controls,
  not members; the invalidated runs changed no cell, threshold, split, cost
  rule, ranking rule, or seed.

## New findings

1. **Unit mislabel** in the tasking text ("R/trade") — see the loud caveat above.
2. **Join-hazard extension**: the executed books have **zero composite-key
   overlap** with the scoreable pools (0/57 Jan keys in
   `CJ_RECLOCKED_S0R0_POOL_V1`, 0/58 Feb keys in
   `CP_FEBRUARY_S0R0_POOL_V1`). The id namespace is **partially shared**, which
   makes bare-id joins actively dangerous rather than merely empty: the 57 Jan
   trades carry 55 unique candidate_ids (2 recur inside the trade table
   itself); 18 of the 55 appear in the Jan pool **only at other decision
   times** (218 rows — e.g. trade decision 07:00 vs pool rows
   04:30/04:45/05:00/05:15, same id/symbol/side); Feb: 58 trades / 44 unique
   ids, 27 present at other decision times (537 rows), 0 exact matches. A bare
   candidate_id join trades→pool would **mis-join hundreds of
   wrong-decision-time rows and silently drop the trades whose ids never
   appear** (37/55 Jan, 17/44 Feb). The correct raw anchor for executed trades
   is the engine TRADE_LEDGER, where everything anchors 100 % with zero
   mismatches.
3. **Ranking fragility corroborated from the raw manifest**: the two
   invalidated runs had selected **different top-3s** (R1: V23/V25/V29; R2:
   V23/V26/V27 — visible in the preserved null look-ids). The published
   V17/V18/V19 ranking exists only after the pre-fill and true-UTC repairs; the
   would-be winner under either defective analyzer was **V23** (a 1.0R-trigger
   cell). This confirms and quantifies FC's own "plausible but false rankings"
   account; the frozen protocol never changed across the three runs.
4. V17's February **improvement** is positive (+2.799 R) while its February
   **book** is negative (−0.381 R) — improvement-without-positivity, the same
   shape that failed the January HOLDOUT gate. Nothing found contradicts FC's
   0/40 verdict.

## Boundaries

March 2026 read: **no**. Live-forward read: **no**. February fitted: **no**
(attribution-only, stated above). Lane arms / replays / test suite run: **no**.
Source files edited: **no**. Writes confined to this `a2_verify/` directory and
the session scratchpad.

## Artifacts

- `fc_verify_scan.py` — stage 1: streaming raw extraction, sha256 verification,
  lane/ledger anchoring (peak memory far under 1.5 GB; the 3.2M-row sidecar was
  never loaded — the executed books do not consume it).
- `fc_verify_replay.py` — stage 2: independent 40-cell replay + statistics.
- `FC_RECOMPUTE_DETAIL.json` — full 40-cell book, per-trade V00/V17 rows,
  positivity lists, gate arithmetic.
- `FC_RAW_LEDGER_ANCHOR.json` — trade-table→raw-engine-ledger anchor receipts.
