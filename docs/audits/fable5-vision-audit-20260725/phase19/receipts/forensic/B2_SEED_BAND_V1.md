# B2 — the seed-replicate band: three full-January S0R0 arms (r0/r1/r2)

Session FA continuation, Phase B item 2 (the last open Phase B leg). Three replicates of
the identical arm config — CJ recipe (6 cuts + `commission_broker_true_gated,
swap_horizon_true`), full January window, lane source-plan digest
`b44b433039bf7f5372fc067f62477cdb5c8b0d2caf4202755a922a7c198be954` — differing ONLY in
the neutral RNG seed:

- **r0** = `CJ_RECLOCKED_S0R0_V7` (wave-16 worktree; sealed seed `0c6b8723…` — the
  published CJ baseline of record)
- **r1** = `FA2_SEED_S0R0_R1_JAN` (seed `cdeae5d8…`, via `neutral_seed_replicate_r1`,
  applied exactly once; wall 8,850 s, RSS peak 4.19 GB)
- **r2** = `FA2_SEED_S0R0_R2_JAN` (seed `709126af…`, via `neutral_seed_replicate_r2`,
  applied exactly once; wall 8,810 s, RSS peak 4.36 GB)

Machine artifact: `B2_SEED_BAND_V1.json` beside this file. Join key
`canonical_replay_candidate_instance_key`; None-aware for the 2-row unscoreable class
(`ordered_tick_required_for_adverse_before_profit_sequence`), which is **identical across
all three arms**.

**EVIDENCE CLASS: DEVELOPMENT-FITTED lane evidence, billed:false.** January only.

## Result

| arm | trades | book net R | Δ vs r0 |
|---|---:|---:|---:|
| r0 | 57 | −5.5062 | — |
| r1 | 57 | −5.7590 | −0.2527 |
| r2 | 58 | −6.2570 | −0.7508 |

**Month-scale seed band: 0.751 R (max−min of three replicates).** Daily paired-delta sd:
r0↔r1 0.058, r0↔r2 0.138, r1↔r2 0.128 — against a daily book sd of 1.754 (19 trading
days with trades). Seed noise is 3–8 % of daily book noise.

## Mechanism — pure selection degeneracy, and it can change the admitted COUNT

**Zero `moved` trades in any pair**: every trade shared between two arms is bit-identical
(net_r to 1e-9). All divergence is same-timestamp contest resolution at **four sites**:

| site | r0 | r1 | r2 |
|---|---|---|---|
| 2026-01-02 XAUUSD | fvg inst A +0.7131 | fvg inst A +0.7131 | **fvg inst B +0.8132** |
| 2026-01-16 XAUUSD | breaker +0.6144 | **fvg +0.3616** | **fvg +0.3616** |
| 2026-01-22 US30_cash (×2) | fvg insts +0.4698/−1.1244 | same as r0 | **insts +0.4244/−1.1327** |
| 2026-01-28 GBPJPY | *(no trade)* | *(no trade)* | **sorb −0.5444 admitted** |

The 01-28 site is the finding: seed noise resolved a contest such that an **extra trade
was admitted** (57→58, +2 orders, −1 missed row). Selection degeneracy is not only
"which twin wins" — it moves the book's trade count. Family mix shifts accordingly
(breaker 9/8/8, fvg 21/22/22, sorb 20/20/21, sde 7/7/7).

## Consequences in force

1. **The January verdict is seed-robust.** All three replicates are negative at −5.5 to
   −6.3; the band (0.75 R) is an order of magnitude smaller than the book magnitude.
2. **The March MDE floor.** Any month-scale arm-vs-arm delta ≤ ~0.75 R sits inside the
   selection-degeneracy band and is **NOT_EVALUABLE** as an economics verdict — this
   number feeds `MARCH_PREREG_V1` §MDE directly, alongside the day-ledger variance term.
   n=3 replicates: treat 0.75 R as the order of magnitude, not a calibrated quantile.
3. **T2 arm deltas inherit this band.** T2 arms share the sealed seed, so seed noise does
   not enter arm-vs-arm deltas directly — but any repair that changes EV at a contest
   site re-resolves the contest, producing count/composition changes of exactly this
   magnitude class that are *mechanism*, not noise. T2 receipts must report contest-site
   diffs (only-in-A/only-in-B) separately from shared-trade economics, as done here.
