# T2 — five full-January arms through the repaired engine (Phase D item 2)

Session FA continuation. All arms: S0R0, full January, lane digest `b44b4330…`, strictly
serial, every config 2-day-smoked before its full arm, receipts + per-arm analysis JSONs
beside this file (`T2_ARM_{I..V}_ANALYSIS.json`). Baseline r0 = `CJ_RECLOCKED_S0R0_V7`
(−5.5062, 57 trades); seed band 0.751 R (B2); contest-site diffs reported separately from
shared-trade economics per B2 rule 3. Arm compositions exactly as declared
(`CELL_DECLARATION_V1` + amendments `424500467`, `008aec561`).

**EVIDENCE CLASS: DEVELOPMENT-FITTED lane evidence, billed:false.** January only — the
same window every repair was derived on. Nothing here is admission-grade; March (frozen,
prereg, owner-triggered) is the only decoding window.

## The table

| arm | composition | trades | book net R | Δ vs r0 |
|---|---|---:|---:|---:|
| r0 | CJ recipe (frozen costs) | 57 | −5.5062 | — |
| (i) | + R-COST-TRUTH | 138 | **−31.4640** | −25.958 |
| (ii) | + R-BELIEF + R-SCHEMA | 6 | **+0.5782** | +6.084 |
| (iii) | + `cost_ceiling_0p05` (comm. swap, − ruler) | 1 | **+0.1495** | +5.656 |
| (iv) | CJ pair + 8 inert controls | 57 | **−5.5062** | **+0.0000** |
| (v) | (iii) + breaker transform (the edge in) | 1 | **+0.1495** | +5.656 |

Wall 6.4–12.2 ks per arm, RSS peak 4.1–4.8 GB, zero errors, all censuses complete.

## What each arm established

**(i) Cost truth alone makes the book 5.7× WORSE — the frozen cost inflation was
accidental risk control.** The frozen layer charged 8.5× the truthed spread
(157,637 R vs 18,584 R over 153,486 packets). Truthing it admits 93 new trades (74 %
`current_fvg_fill` — T1's worst fill-axis family) summing −19.1 R, and loses 12
frozen-only trades that summed **+7.0 R**. The 45 shared trades' booked economics are
essentially unchanged (mean +0.002, 4 moved) — cost repairs move the ADMISSION GATE,
not the booked fill economics. Attribution is single-variable by construction: r0's
recipe already carries gated-commission + swap, and the ruler is measured-inert on
January, so (i)−r0 ≈ spread truth.

**(ii) Belief honesty re-narrows the funnel to near-silence — and the result is
positive but noise-level.** 57 → 6 trades (all fvg); the book +0.58 sits inside the
0.751 seed band. The one trade shared with r0 is the sole-survivor class (EV −0.22
repriced honest, realized +0.71). BELIEF_RECAL's 0/108 no-honest-sub-book verdict
STANDS: the honest system stops the bleeding by mostly refusing to trade, not by
finding edge.

**(iii) The declared ceiling composes to one trade in the month (+0.15).** It removed
5 of (ii)'s 6 trades including the +1.86 winner — at n=6→1 this is sample starvation,
not a mechanism reversal of T1's pool-level F−A (which is loss-avoidance over
thousands of rows). T1/T2 "sign disagreement" on the ceiling is recorded and
adjudicated as scale mismatch, with the T3 arm below closing the composition
confounder.

**(iv) The attribution baseline is EXACT.** All 8 control wrappers live (breaker
control deep-copy-proved 12,668 candidates): 57/57 trades, per-trade Δ 0.0, book Δ
+0.0000 vs r0. Every delta in this table is repair semantics, not machinery.

**(v) THE EDGE IN: the billed candidate is INEXPRESSIBLE in the gated engine.** The
transform ran on all 12,668 breaker candidates (zero errors; 483/483 smoke-verified
geometry) — and the book is byte-identical to (iii): the transform bought ZERO trades.
Mechanism, measured at the pool: transformed median `cost_r` **0.701 vs 0.191**
untransformed (3.7× — the 0.25D stop shrinks the R unit), and **12,668/12,668 REFUSED
at the pre-trade cost packet** (arm (iii): 12,514/12,668 refused, 154 passed). The
engine's cost gate is denominated in R units and structurally presumes ~unit-R stops:
a small-stop/high-RR candidate can NEVER pass it, at any declared ceiling, regardless
of realizable economics. CQ's +11.9 walker figure and the engine disagree not about
the cell's economics but about whether a 20R-target trade may pay 0.7R of cost — the
walker shows it can afford to; the gate refuses on principle. **Trade-TP provenance
(the declaration's first question): NOT_EVALUABLE at n=0 transformed trades.**

## Consequences in force

1. **No repair combination yields a tradeable positive January book.** Best case is
   near-silence (+0.15…+0.58, noise-level). The negative-vs-invalid asymmetry closes
   honestly: the invalid measurement is repaired, and the repaired truth is "stand
   down".
2. **The cost-gate denomination is a real architectural finding.** A future repair
   (price/notional-denominated gating, or RR-scaled ceilings) is licensed by arm (v)'s
   measurement, NOT built here. Without it, no high-RR candidate — V27 or any
   successor — can be expressed through this engine.
3. **The frozen book's −5.51 was itself an artifact of two canceling errors**: an
   8.5× cost overcharge suppressing admissions (i) over a pool whose honest EV is
   negative (ii). Removing either alone moves the book violently in opposite
   directions. Any live-transfer claim from the frozen January book inherits both.
4. **T3**: one arm — (ii) + commission gated→accounting, no ceiling — isolates the
   swap confounder inside the (ii)→(iii) delta (triggered mechanically by the >5 %
   admission-set change). The belief bundle's internal attribution is settled by
   BELIEF_RECAL mechanistically; leave-one-out over it is not run (recorded).
5. March prereg carries: the five compositions verbatim, the 0.751 seed band, paired
   daily net-R primary endpoint, and NOT_EVALUABLE terminals for cells the engine
   cannot express (per finding 2).
