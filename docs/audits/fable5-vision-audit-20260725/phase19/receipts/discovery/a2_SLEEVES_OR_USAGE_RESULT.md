# a2 — owner report receipt (phase-19 broad-forensic wave)

**Deliverable:** `docs/audits/fable5-vision-audit-20260725/phase19/SLEEVES_OR_USAGE_OWNER_REPORT.md`
(513 lines, owner-facing). **Machine receipt:** `a2_SLEEVES_OR_USAGE_RESULT.json` (this directory).

`a2_RESULT.json` / `LATENCY_OWNER_REPORT.md` in this directory belong to the **earlier** a2 lane
(the latency question) and were deliberately **not** overwritten.

## What this lane did

No new measurement. It is a synthesis lane: it answers Borhen's two questions —
*"is it the sleeves or the way we're using the sleeves?"* and *"where do we go from here?"* — from
the committed receipts of the foundation lanes (f1, f2), the decomposition lanes (d1b, d2, d3, d4,
d5, d6, d7, d8x) and the persistence / sealed / adversarial lanes (p1, p2, p3).

## Verdict

**Axis: SIGNAL.** The setups carry a real but tiny directional edge (0.0119 bps of price per trade)
against a 3.0159 bps broker toll — a 253× shortfall — and, unlike a working sleeve's, it **does not
accumulate with holding time** (0.97× from 2 h to 320 h against 37.58×). The usage is measured at
~84 % of its own reachable ceiling and **adds** value rather than destroying it; perfect usage on
every axis simultaneously is 98.8 % reproduced by a coin flip.

## Numbers re-read from the JSON artifacts while writing (not taken on trust from lane returns)

| number | artifact | verified |
|---|---|---|
| clean roster −0.013268637647644799 / 0.28118403421917193 / −0.29445267186681673, n 298,537 | `f1_BASELINE_V1.json → roster.roster_pooled.filled_clean` | exact |
| sealed pooled +0.027176768863484385, toll 0.3426242156468404, net −0.31544744678335607, n 97,802, p 0.001, 3/3 | `P2_SEALED_V1.json → H1_signal_is_zero` | exact |
| sealed breakeven gross 0.3818891275259781 / net 0.5265832649027788 | same | exact |
| accumulation curve live 3.4067→128.0388 bps, broad 0.2008→0.1938, growth 37.5844 / 0.9654 | `d3/D3_CURVE.json` | exact |
| median stops 215.375 (live) / 9.683 (broad) bps | same | exact |
| walker bias bound −0.064365 (h240, T1.5) and −0.06956 (h240, T2.0); s/d median 0.0988 | `D8X_GEOM_V1.json → touch_rates`, `s_over_d` | exact |
| live-sleeve control +0.15555286655580824, CI [0.09191, 0.22088], n 4,352; armed 138 at +1.24084 | `D8X_CROSS_V1.json → ALL`, `armed_only` | exact |
| tick truth per opportunity −0.025007449890037614 (202601) / −0.03692998365775097 (202604) | `p3_RESULT.json → TICK.POOLED_*` | exact |
| cost lever required_C −0.013268637647644799, reduction 104.71884461167606 %, feasible false | `d7/D7_STAGE1.json → cohorts.CLEAN.levers.L4_cost` | exact |
| clean-roster breakeven_net 0.5057540948128497, gap_net_pp −12.5965, toll_bps 3.002018388899679 | `d7/D7_STAGE1.json → cohorts.CLEAN` | exact |
| loser lever required_b 0.4262892771483894 (−52.69 %) | same → `L3_loser_size` | exact |
| forming bar sealed: close −0.2804148473822154 (n 2,132) vs partial −0.30550933234190464 (n 2,249), CANDIDATE FAILS | `P2_SEALED_SEP_H5.json → b_implementable` | exact |
| forming bar paired effect still replicates: +0.1806271744762689, p 0.000 | same → `a_paired` | exact |
| f2 paired signal R1 +0.00315437408148702, halfwidth 0.010264096935302029, 5/8 months | `f2/F2_POOLED_V1.json → PAIRED_SIGNAL_POOLED` | exact |
| toll deciles D1 toll 0.021742613426094824 at 37.35 bps → D10, ratio non-monotone peaking 0.244 | `d1b_SIGNAL_QUALITY_V1.json → toll_deciles` | exact |
| never-opened archive: 24 instruments, 439,895 bars, 2014-01-02→2026-06-15, 0 wave-19 references | `d8x_RESULT.json → never_opened_data` | exact |

Derived in this lane (arithmetic, shown so it can be checked):

- `0.3426242156468404 / 0.027176768863484385 = 12.606` — toll ÷ gross on the sealed months.
- `3.0159 / 0.0119 = 253.4` — price-unit shortfall (matches p2's own published factor).
- `324 + 282 + 954 + 56 + 1414 + 66 + 127 + 11 = 3,234` — total configurations priced across the
  eight sweeping lanes, **zero** positive books.
- `0.30825 / 0.02548 = 12.10` — p1's oracle cell-selection ceiling against the at-market toll.

## Structure of the report

1. The answer in ten lines (both questions, with numbers).
2. What was examined / what was not + a vocabulary table (every term defined on first use).
3. Three corrections to numbers the owner already has: the pool was the wrong object; `min_rr` is
   1.5 not 2.0 and the "11-point hole" was blamed on the setups when it is the broker; three
   headlines built and killed this week, each with its mechanism.
4. Seven finds, led by what was **found** (the edge is real and replicates on unseen months), not by
   what was ruled out.
5. The exhaustiveness table (3,234 configurations) and the measured detection floor, so "nothing
   found" reads as a result rather than an absence.
6. Levers priced jointly (double-count factor 21.9×), the family end to end, and every escape route
   closed with its own number.
7. What is thin, stated plainly and not buried — five items, including that the sealed gross sits
   inside the walker's own measured bias and that the held-out set is now spent.
8. Seven ordered recommendations with worth and cost, starting at "change nothing live" and ending
   at the one experiment nobody has run.

## Constraints observed

No live-forward P&L read (live-sleeve figures are research walks on `AQ_ESTATE_TRADES_V2`). No
sealed replay arm launched, no VPS contact, no broker script, no git commit, `main` untouched. The
three sealed windows were not re-opened by this lane; their economics are quoted from p2's committed
receipt.
