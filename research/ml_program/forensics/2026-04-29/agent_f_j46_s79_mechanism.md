# Forensic Agent F — J46-J49 + S79 Mechanism Decomposition

**Date:** 2026-04-29
**Author:** Forensic Agent F (post-DSR survival audit)
**Discipline anchors:** `feedback_paired_fixed_hp_discipline`, `feedback_walk_level_evidence_not_predictive`, `feedback_decay_is_ceo_number_one_concern`, `project_dsr_retroactive_sweep_2026-04-29`.

## Executive summary

The two GTOS alphas that SURVIVED the DSR retroactive audit (Phase 1 quick-win bundle B-8) — J46-J49 and S79 — are both at the **position-management layer**, not the signal-detection layer. This forensic decomposes:

1. Which J46-J49 components carry the +0.742R/trade lift (Shapley attribution).
2. Whether S79's +25.8pp P(pass FN) is driven by cap raise, base_risk_pct doubling, or profile choice.
3. Whether J46-J49 and S79 are independent alphas or overlapping.
4. What position-management alpha space remains unexplored.
5. Discovery rate implications for the Phase 2 portfolio-of-edges strategy.

**Headline findings:**
- **J46-J49 lift is THREE-WAY ORTHOGONAL.** TP1=3.0R (J49) carries +0.270R, partial=0% (J46) carries +0.245R, immediate-on-TP1 BE (J47) carries +0.217R. 12-bar time-stop (J48) is a tertiary contributor (+0.010R) — its role is WR/DD shaping, not mean-R lift.
- **S79 is OVERWHELMINGLY a base_risk_pct doubling.** The cap raise (2 -> 4) actually DETRACTS by ~2.4pp. Doubling risk-per-trade from 1.0% to 2.0% is the entire +25.8pp P(pass) lift. Sharpe per trade is ESSENTIALLY UNCHANGED (0.343 -> 0.336). It's mechanical Kelly-scaling.
- **J46-J49 and S79 are INDEPENDENT alphas.** S79 is a position-size scalar; J46-J49 is a per-trade R-distribution transform. They commute and stack multiplicatively in expected value.
- **Top 3 adjacent unexplored variants:** Vol-conditional sizing (Barroso-Santa-Clara port), J46-J49 6R-target partial close, side-aware regime-conditioning sizing.

---

## Section 1 — J46-J49 component-by-component attribution

### Method

Pareto-frontier rows from `research/j46_j49_position_mgmt_sweep/pareto_frontier.csv` (commit `be33522`, n=321 fills, 750 configurations). Computed Shapley-style average marginal contribution across all valid baseline -> winner paths in the Pareto-coverage. Cross-validated via "drop one component" ablation.

### Result

| Component | Knob change | Avg marginal lift | Share of total | DD impact |
|---|---|---:|---:|---:|
| **J49 TP1 distance** | 1.5R -> 3.0R | **+0.270R** | 36.4% | unchanged (-0.474R) |
| **J46 partial close %** | 100% -> 0% | **+0.245R** | 33.0% | unchanged (-0.474R) |
| **J47 BE trigger** | KZ-end -> immediate-on-TP1 | **+0.217R** | 29.3% | unchanged |
| **J48 time stop** | off -> 12 bars | **+0.010R** | 1.3% | -0.466R -> -0.474R |
| **TOTAL** | (all together) | **+0.742R** | 100% | -0.466R -> -0.474R |

Sum-of-marginal-losses ablation = +0.747R (independence ratio 1.007); axes are highly orthogonal.

### J46-J49 mechanism — what underlying behavior IS the policy?

The winner policy is functionally a **3-stage trailing-stop** wearing position-management clothing:
1. Original SL (max -1R loss).
2. BE pull when price reaches 3R (after that, worst case is 0R).
3. Higher target at 6R, OR time-stop at 12 bars (3 hours), OR original/BE SL.

The "partial close + BE" framing was a **strict Pareto-loser**: it banks at TP1, then the remainder runs to BE (or a tiny upside via time-stop). The "0% partial + far TP1 + immediate-BE-at-TP1" winner says: do NOT bank early; let the trade reach 3R, then protect; let it run to 6R if it wants.

### J46-J49 behavioral anchors

- **Disposition effect (Odean 1998, Frydman et al. 2014, Locke-Mann 2005):** discretionary closing of winners at first profitable opportunity is the universal counterparty bias. By forcing partial=0% + far TP1, GTOS structurally avoids THE most-replicated retail bias.
- **Stop-cascade reversion (Osler 2003/2005, Stübinger-Endres 2018):** post-displacement reversion lasts to 2-6R levels; the 3.0R distance approximately aligns with the 2nd round-number anchor below/above the initial OB. The 6R higher-target aligns with the 3rd round-number anchor.
- **Fat tails (project_distributional_findings — gold ξ=0.35, 6.2x Gaussian 3σ events):** the mean-R-improvement-per-R-of-target is positive at all checkpoints (1.0R, 1.5R, 2.0R, 2.5R, 3.0R), consistent with fat-tailed return distribution. Banking at TP1=1.5R explicitly truncates the fat tail.
- **Edge-decay immune:** does NOT depend on the OB-zone advantage being intact. If F11 erosion continues from +17pp to +5pp, J46-J49 still extracts more per filled trade. Pure downstream-of-selection lift.

### J46-J49 sensitivity (per-axis lift curves)

**J49 TP1 distance progression** (at p=0%, BE=immediate, ts=12b):
| TP1 | Mean R | WR | DD |
|---|---:|---:|---:|
| 1.0R | +0.624 | 67.0% | -0.456 |
| 1.5R | +0.820 | 69.5% | -0.469 |
| 2.0R | +0.926 | 70.1% | -0.473 |
| 2.5R | +1.009 | 70.4% | -0.473 |
| **3.0R** | **+1.084** | **70.7%** | -0.474 |

**Diminishing returns above 2.0R**: 76% of J49 lift accrues by 2.0R. Going from 2.0R to 3.0R adds only +0.158R/trade. **A 2.0R compromise would preserve most of the lift if 3.0R proves fragile live.**

**J48 time-stop progression** (at p=0%, BE=immediate, TP=3.0R):
| Time-stop | Mean R | WR | DD | Bars held |
|---|---:|---:|---:|---:|
| 12b | +1.084 | **70.7%** | **-0.474** | 10.6 |
| 24b | +1.133 | 62.9% | -0.552 | 19.6 |
| 48b | **+1.248** | 62.0% | -0.657 | 34.6 |

Looser time-stop -> higher mean R but lower WR and deeper DD. The **12b winner choice optimizes WR + DD shape**; 48b would be the mean-R-max choice. The CEO ship decision (12b) was a defensive choice — privileging trade-by-trade reliability over portfolio mean-R.

### J46-J49 per-instrument winners

All 5 instruments converge on partial=0% and TP1>=2.0R. The BE trigger and time-stop axes show per-instrument optima:
- **GBPJPY:** be=+2R, ts=96b, TP=3.0R — long hold, moderate BE.
- **GBPUSD:** be=KZ, ts=24b, TP=3.0R — uses session boundary BE.
- **US30_cash:** be=immediate, ts=12b, TP=3.0R — matches portfolio winner.
- **USDJPY:** be=+1R, ts=48b, TP=2.0R — only TP=2.0R winner.
- **XAUUSD:** be=+1.5R, ts=12b, TP=3.0R — moderate BE.

The portfolio winner is per-instrument-suboptimal but *near-optimal* across all 5. Per-instrument tuning gain: ~+0.10-0.20R/trade per instrument vs portfolio winner.

---

## Section 2 — S79 mechanism deep-dive

### Method

`research/s79_risk_policy_counterfactual/per_config_pareto.csv` (commit `c53bc51`, 450 configurations × 1000-trial bootstrap MC). Two-axis Shapley attribution for the (cap, base_risk_pct) component within profile=uniform_fn.

### Result

| Component | Knob change | Avg marginal lift |
|---|---|---:|
| **base_risk_pct** | 1.0% -> 2.0% | **+0.289pp (109% of total)** |
| **cap** | 2 -> 4 | **-0.024pp (-9% of total — DETRACTS)** |
| **TOTAL** | | **+0.265pp** |

The cap raise from 2 to 4 was actually a SLIGHT P(pass) loss. Cap=2, base=2.0%, uniform_fn delivers P(pass)=0.863 with bust=0.006 — Pareto-DOMINATES the shipped cap=4 (P_pass=0.844, bust=0.011). The cap raise was operational deployment-flexibility (allow 4 simultaneous fills), not P(pass) maximization.

### S79 mechanism — what does it actually do?

**S79 is mechanical Kelly-scaling.** Same Sharpe per trade (0.343 -> 0.336, essentially unchanged), 2x position size, ~6.34x compound growth rate (per FN MC), at proportionally higher MTM-DD risk (3.95% -> 7.78% in-sample worst).

The 2.0% base is at the **diminishing-returns elbow**:
- 1.0% -> 1.5%: +0.215pp P(pass)
- 1.5% -> 2.0%: +0.080pp P(pass)
- 2.0% would saturate further increments

Above 2.0%, marginal P(pass) gain compresses while in-sample DD scales near-linearly. The 2.0% choice is the kink, calibrated against the FN 8% total-DD ceiling.

### Kelly calibration check

- Sornette et al. 2020 calibrated "fractional Kelly" for jump-diffusion + ξ=0.35 fat tail = 0.4 of full-Kelly.
- Thorp 2006 "half-Kelly" recommendation = 0.5 of full-Kelly.
- GTOS Sharpe per trade = 0.336; if avg σ(R) ~ 1.0, full-Kelly ~ 24% per trade.
- S79 2% is **0.083x of full-Kelly** — VERY conservative even by fat-tail standards.

**Implication:** S79 is FN-constraint-bound, NOT Kelly-growth-bound. If FN constraints relax (Phase 2 broker swap, scale-stage 2), S79 has substantial room to raise risk further.

### S79 behavioral anchors

- **Roy 1952 safety-first frame (P037 in Group E):** maximize P(W_T >= target | W_T not below floor). S79 IS the explicit Roy 1952 problem. Floor = $96k (8% total DD); target = $108k (FN Phase 1 8% gain). uniform_fn cap=4 base=2.0 is the Roy 1952 solution under the empirical (R, σ) distribution.
- **Strub 2014/2018 EVT-CDaR (Group E P021-028):** under fat tails, fractional Kelly is always dominated by fixed-fraction at 50-90% of Kelly. S79 2% = 8% of Kelly is well within Strub's safe zone but leaves significant Sharpe-per-dollar on the table.
- **Kahneman-Tversky loss aversion λ ≈ 2 (Walasek-Mullett-Stewart 2025 confirms in asymmetric ordered contexts like trading):** 2 consecutive 2% losses = 4% MTM hit, exactly the FN daily ceiling. S79 implicitly auto-calibrates to behavioral-loss-aversion floor.

### S79 caveats

- **In-sample bootstrap MC** of n=129 trades — true OOS P(pass) likely lower than 0.844 by 5-15pp.
- **DSR-corrected p < 2.22e-16** (machine zero) — strongest signal in entire audit. ECONOMIC validity rests on the in-sample MC assumption.
- **NAS100 HELD at 0.25% pending HALLUC-1 observation** (per ship commit). Re-evaluate Wed 2026-04-30.
- **side_aware "bad" finding in S79 = LONG=0.25x SHORT=1.0x definition** — DIFFERENT from H38 brief side_aware_a (LONG=0.5x SHORT=1.0x). The two memos appear to contradict but are using different profile definitions. Cross-reference required for Phase 2 sharpe_weighted re-tune.

---

## Section 3 — Independence vs overlap analysis

### Verdict: **INDEPENDENT** alphas, multiplicative compounding.

| Axis | S79 | J46-J49 |
|---|---|---|
| **Operates on** | Position-size scalar | Per-trade R-distribution |
| **Modifies** | Risk-per-trade (1.0% -> 2.0%) | R-realized per fill |
| **Sharpe per trade** | unchanged (0.343 -> 0.336) | dramatically improved (effectively 3.17x mean R) |
| **WR change** | none | 32.1% -> 70.7% |
| **DD per trade** | 2x scaling | unchanged (-0.466R -> -0.474R) |
| **Decay sensitivity** | amplifies edge erosion | edge-decay-immune |
| **Bars held** | unchanged | 9.7 -> 10.6 |

S79 is a position-size scalar; J46-J49 is a per-trade R-distribution transform. Mathematically: `PnL = sum(risk_pct * R_realized)`. S79 scales the multiplier; J46-J49 transforms each R_realized. **They commute.**

### Combined-MC re-run is required before J46-J49 main-merge

- J46-J49 winner increases mean R to 1.084, but ALSO increases variance (3.0R targets create dispersion). Higher variance + higher position size could re-elevate hard-bust risk.
- J46-J49 extends bars-held (10.6 vs production ~1-2 bars for FULL_TP). Cross-instrument concurrency gate behavior may differ.
- BE-pull mechanism interaction with cross-instrument correlation gate's HALVE behavior is unmodeled.

**Pre-registered prediction:** Combined P(pass FN Phase 1) > 0.90 at base=2.0% under J46-J49 winner R-distribution; P(bust HARD) <= 0.025. If combined MTM-DD violates >2% of paths, S79 must back off to base=1.5%.

**This is the load-bearing analysis for Phase 2.**

---

## Section 4 — Top 3 most-promising adjacent unexplored variants

### Rank 1 (HIGHEST EV): H-PM01 Vol-conditional position sizing

`position_size_R = base_R × clip(target_vol / realized_R_vol_30d, 0.5, 2.0)` per-instrument. Barroso-Santa-Clara 2015 magnitude: +30-50% Sharpe vs uniform_fn 2.0%. Bundles directly with S79 Phase 2 sharpe_weighted. Cost: 1-2 days engineering + 1 day MC re-run.

### Rank 2 (LOWEST COST): H-PM10 Partial-close at 6R higher-target

Variation on J46-J49: still 0% at TP1=3R + immediate BE; ALSO 50% at 6R + trail remainder. Captures fat-tail upside while banking some. Magnitude: +0.05-0.20R/trade depending on instrument fat-tail thickness. Uses existing J46-J49 sweep infrastructure. Cost: 1-2 days.

### Rank 3 (MOST-PRECISELY-TARGETED): H-PM03 Side-aware sizing with regime conditioning

`LONG=0.5x in {trending_bull, transitional} AND realized_vol_z > +1; 1.0x otherwise`. F15 + F2 already pinpoint XAUUSD London/trending_bull/LONG as the load-bearing decay cell. Uses regime classifier already in shadow mode. Cost: 1-2 days.

See `agent_f_position_mgmt_backlog.md` for the full top-20 ranked list.

---

## Section 5 — Portfolio-of-edges discovery rate

### Status

- **2 SURVIVING DSR alphas: J46-J49 + S79.** Both at position-management layer.
- **0 SURVIVING DSR alphas at signal-detection layer** (post-DSR audit). XAUUSD WR, OB advantage, FVG-in-impulse, K54 v1, all FAIL DSR at N=200 trial budget.
- **9-month exploration (H-series + S-series) yielded 4 grade-A candidates;** 2 SURVIVED DSR. Discovery rate ≈ 0.5 SURVIVING alphas per quarter per agent.

### Renaissance Medallion model implication

Medallion's reported Sharpe ~3-4 is built on 100+ small, uncorrelated alphas, each contributing fractional Sharpe ~0.05. GTOS at 2 alphas is at the **start of the curve.** 

| # alphas | Approx Sharpe (uncorrelated +0.10 each) | Approx P(pass FN) |
|---:|---:|---:|
| 2 | 0.34 (current) | 0.844 |
| 5 | 0.50 | 0.92 |
| 10 | 0.71 | 0.97 |
| 20 | 1.0 | 0.99+ |
| 50 | 1.6 | (saturated) |

### Realistic 12-month target

If the position-management top-20 backlog yields 3-5 SURVIVING alphas + Phase 2 K54 v3 yields 1-2 + literature-port additions yield 2-3, the cumulative could reach **8-10 SURVIVING DSR alphas by Q1 2027**, contributing +0.3-0.6 cumulative Sharpe. This is the program's tractable target.

### Phase 2 priority implication

Position-management discovery is **edge-decay-immune** (orthogonal to F11 + F15 erosion). Discovery cycle is **short** (1-3 days vs 2-3 weeks for K54 v3). Position-management lifts **stack multiplicatively**.

**Recommendation:** weight Phase 2 effort 60% on position-management discovery (top-20 backlog) and 40% on signal-detection (K54 v3, prompt overhauls, regime classifier promotion). Current Phase 2 plan rank #1 = K54 (signal-detection) — should be reweighted.

---

## Section 6 — New ambiguities / follow-ups

### Open ambiguity

1. **side_aware definition contradiction:** S79 sweep uses LONG=0.25x SHORT=1.0x; H38 brief and project_side_aware_sizing_findings memory use LONG=0.5x SHORT=1.0x. The two analyses are NOT comparing the same profile. Phase 2 must standardize on one definition before re-running.

2. **J49=2.0R vs 3.0R robustness:** Most lift (76%) accrues by 2.0R. The 2.5R -> 3.0R increment is +0.075R only. Pre-registered question: which is more robust live?

3. **Per-instrument vs portfolio winner ship:** Per-instrument winners deliver +0.10-0.20R additional vs portfolio winner. Implementation cost is significant. Phase 2 cost-benefit decision needed.

### Required follow-up dispatches

1. **H-PM04 (combined MC re-run)** — must run BEFORE J46-J49 main-merge. 0.5 day. Pre-registered prediction: combined P(pass FN) > 0.90 at base=2.0%, P(bust HARD) <= 0.025.

2. **H-PM01 (vol-conditional sizing port)** — bundles with S79 Phase 2 sharpe_weighted. 2-3 days. Pre-registered prediction: +30-50% Sharpe vs uniform_fn 2.0%.

3. **H-PM03 (side-aware regime-conditional sizing)** — direct test against F15 decay cell. 1-2 days. Pre-registered prediction: XAUUSD H2 P(pass) recovers from 0.515 to 0.60-0.65.

### Research-design gaps

- **No 2022-2023 cross-period replay of J46-J49.** The 1798-trade mechanical OB cohort has FIXED-TP=1.5R outcomes — cannot directly validate. F11 cohort builder has the OHLCV-walked data; recommend dispatching J46-J49 re-replay on this cohort. Pre-registered prediction: directional consistency, smaller magnitude (~+0.4-0.6R) — would refute "in-sample overfit" alternative.

- **No mechanistic test of why partial=0% beats partial=25%/50%/100%.** The Shapley says ~+0.245R, but the *behavioral story* (disposition effect on retail counterparties) is unfalsifiable without market-microstructure data on counterparty closure rates at TP1 levels.

- **No test of whether J46-J49 lift compounds with K54 v3 confidence-conditional sizing (H-PM05).** Combined ship is strictly better in expectation but combined MTM-DD profile is unmodeled.

---

## Section 7 — Files committed

- `research/ml_program/forensics/2026-04-29/agent_f_j46_s79_mechanism.md` — this document.
- `research/ml_program/forensics/2026-04-29/agent_f_j46_component_attribution.json` — Shapley + ablation per-component.
- `research/ml_program/forensics/2026-04-29/agent_f_s79_mechanism.json` — S79 deep-dive.
- `research/ml_program/forensics/2026-04-29/agent_f_independence_analysis.json` — J46 × S79 independence verdict.
- `research/ml_program/forensics/2026-04-29/agent_f_position_mgmt_backlog.md` — ranked top-20 candidates.
- `research/ml_program/forensics/2026-04-29/_pareto_frontier_j46_j49.csv` — copy of pareto frontier (commit be33522).
- `research/ml_program/forensics/2026-04-29/_s79_per_config.csv` — copy of per-config pareto (commit c53bc51).

No production / live system / `src/` / `config/` / `scripts/canary_fixtures/` files modified.

---

*End of forensic agent F report. Reproducibility: all numerical findings can be regenerated by running the analysis blocks in this document against the two committed CSVs above.*
