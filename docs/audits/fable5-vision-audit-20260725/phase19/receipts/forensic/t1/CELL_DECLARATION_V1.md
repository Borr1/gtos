# Cell declaration for T2 arms (iii)/(v) — R-GEOMETRY and R-CAPS (declared BEFORE arm (iii) runs)

Session FA continuation, Phase D. Required by `REPAIR_SET_SPEC.md` §5/§6 ("Cells selected
by this rule are DECLARED in the freeze (§10) **before T2 arm (iii) runs**"). This receipt
is that declaration; Phase E's `MARCH_PREREG_V1` carries it forward verbatim. Evidence:
`T1_SCREENS_V1.md`/`.json` + the F−A derivation below (`t1_rcaps_frontier.py`).

**EVIDENCE CLASS: DEVELOPMENT-FITTED lane evidence, billed:false.** All numbers January;
February untouched by this derivation; no March bytes.

## R-GEOMETRY: ZERO cells declared

The §5 rule, executed on truthed costs (T1 Screen B): every exit-shape cell in the
declared prior is NEGATIVE pool-wide (base −0.199; stops ×1.5/×2/×3 −0.179/−0.166/−0.149;
targets 1.5R/3R/5R −0.205/−0.236/−0.295), deltas ±0.05 R — an order of magnitude below
the fill-axis gap (+0.258 pool, +0.75/+0.63 on the two retrace families), and the
fill-axis ceiling is uncapturable by either simple entry policy (T1 fill-axis section).
No cell graduates to a measured arm; FB's two grid survivors route through the CANDIDATE
door (arm (v)) at the ratified rule, never as pool-wide contract repair.

**Router design decision (recorded per §5):** the dead router (`momentum_exhaustion` on
8,448/8,448, L3c) is NOT revived by family-fit exit contracts — the family-fit search came
back empty on this pool. The router mechanism RETIRES as a pool-wide repair surface;
family-specific contracts remain available to candidates only.

## R-CAPS: ONE cell declared — `cost_ceiling_0p05` (tightening)

§6's formal derivation on P\* (the January pool at spread-model truth + broker commission
+ swap + flat 0.02 slippage), grid closed at `COST_CEILING_CELLS = (0.05, 0.10, 0.25,
0.50, 1.00)`, current rule = `spread_r ≤ 0.10 AND total_cost_r ≤ 0.15`, train = Jan
days 1–21, holdout = days 22–31 (contiguous split, declared here). F = Σ net of winners
freed/lost, A = Σ net of losers admitted/avoided; frontier = argmax F+A on train.

Dial-exact (total-only ceiling, as `cost_ceiling_*` implements):

| cell | train F | train A | train F+A | holdout F+A |
|---|---:|---:|---:|---:|
| **0.05** | **−1,768.7** | **+3,025.0** | **+1,256.2** | **+1,092.1** |
| 0.10 | −748.5 | +1,394.5 | +646.0 | +556.2 |
| 0.25 | +1,715.1 | −4,329.6 | −2,614.5 | −1,414.2 |
| 0.50 | +2,891.5 | −7,642.3 | −4,750.8 | −2,393.1 |
| 1.00 | +3,268.1 | −9,256.3 | −5,988.2 | −2,928.4 |

(The ratio-companion variant — spread cap held at 2/3·c — is within 6 % of every figure
and picks the same frontier; table in `t1_rcaps_frontier.py` output.)

**Reading:** every LOOSENING cell is net-negative on both splits — the spec's null ("the
frontier lands NEAR the current caps") is beaten in the TIGHTENING direction. At 0.05 the
avoided losers (+3,025 train) dwarf the lost winners (−1,769); holdout sign-consistent.
This is **loss-avoidance, not edge** (T1 Screen A: no cap value makes the admitted set
positive; precision enrichment tops out at 39.8 %). Constraints discharged: outcomes are
gross + external cost only (C2-B); reachable-winner quote at the consistent rule (Jan
78.1 %); no geometry cell landed, so caps are derived at current geometry (§6 joint rule);
T2 acceptance scored on price-normalized outcomes.

## Consequent arm compositions (final)

- **Arm (iii)** = arm (ii) + `cost_ceiling_0p05`, with the CJ recipe's
  `commission_broker_true_gated` swapped to `commission_broker_true` (accounting-only) per
  the INCOMPATIBLE row — exactly one wrapper owns the gate. Declared in the arm manifest
  and named in the receipt. No R-GEOMETRY content.

  **Amended 2026-08-04, BEFORE arm (iii) ran, on the runner's own fail-closed check:** the
  first smoke of this composition raised `RepairUnavailable('cost_ruler_harmonize' ×
  'cost_ceiling_*')` — both re-run `pretrade_cost_refusal_reasons` on the same packet
  builder, a second INCOMPATIBLE row this declaration failed to carry (the registry had it;
  the declaration did not). Arm (iii) therefore also **drops `cost_ruler_harmonize`**.
  Economically inert on January by measurement (the ruler is a February flat-override
  detector; January identity is clean — calls > 0, applied 0/8,448 in the belief smoke),
  but the composition difference vs arm (ii) is now three-fold and declared: {− ruler,
  commission gated→accounting, + ceiling 0.05}. March carries the same composition.
- **Arm (v)** = arm (iii) + the admitted candidate: **CQ's inverted breaker** (the one
  standing lane admission after A1's corrected null; `ENABLE_CONFIG_KEY =
  "phase18_current_breaker_re_entry_repair_enabled"`, absent-false,
  `src/components/current_breaker_re_entry_repair.py:26`). The transform has **no lane
  hook yet** — a small repair entry (runtime rebind + inert control + 2-day smoke, the
  Phase C pattern) is authored before arm (v) runs and recorded in its receipt. OB-retest
  is NOT graduated (no declared step at the ratified rule exists); it does not ride.

  **Amended 2026-08-04, BEFORE arm (v) ran (hook `e7b7aa4d6` + seam fix `c25e2510d`,
  smoke ARMV-SMOKE-PASS 483/483 transformed pool rows).** Two facts the smoke
  established, recorded ex ante:
  1. **The first seam was wrong and its own smoke caught it**: lane arms replay
     prepared-pack candidates; `V4DecisionCycleCore.generate_candidates` censused ZERO
     calls. The hook now wraps the one funnel both branches share
     (`evaluate_symbol_candidates_with_batched_proof_hashes`).
  2. **Arm (v) measures the candidate under the ENGINE's exit contract, not CQ's
     walker cell.** The missed pool prices every arm at the policy 2R target by
     construction (its `take_profit_1` is the policy computation on the row's stop
     distance — under the transform, 2R × 0.25D = 0.5D). CQ's +11.9 net R/trade was
     measured at the 5D declared target on the path walker; **that figure is NOT the
     ex-ante expectation here.** Whether an EXECUTED transformed trade runs the
     candidate-declared 5D take-profit or the policy target is an open engine-contract
     question — the arm-(v) receipt must answer it from the first transformed trade's
     ORDER/TRADE rows before any economic reading. Sign at book scale: declared unknown.
     A candidate-declared-target passthrough, if the answer is "policy wins", is a
     possible FUTURE repair licensed by measurement — not built in this arm.
- Expected directions, stated ex ante: arm (iii) trade count ≤ arm (ii)'s (a tighter cost
  gate composing with belief stand-down); the delta vs (ii) is loss-avoidance if the pool
  derivation transfers through the funnel; sign unknown at book scale.
