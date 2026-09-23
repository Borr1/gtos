# Phase 1 Research Synthesis — high-quality frequency

**Session:** 39 (2026-04-24)
**Scope:** Three parallel CPU-only research tracks, all Opus 4.7 max effort, worktree-isolated. $0 API spend.
**Fleet state during run:** `detector_version: v2_shadow` LIVE since 2026-04-24 ~11:49 UTC, untouched. HEAD `dea858d`.

---

## 0. Headline

**Phase 1 produced five new pieces of statistical information and zero deployable hard gates.** Both clauses matter. The findings below reframe how the OB edge should be understood — they are not a failure to find a new edge.

### What's new (ranked by potential R/mo impact)

| # | Finding | Evidence | Action |
|---|---|---|---|
| 1 | **The LONG-OB edge concentrates sharply in fresh zones.** Touch=0 primary rate 31.7% (n=60), touch=1 7.2% (n=680), touch=2 3.1% (n=548), touch≥3 2.1% (n=284). Bonferroni-corrected χ² p ≈ 5e-16. Fresh OBs carry 5.5× the overall-population baseline probability of being a 2R-before-1R winner. | Track A §5 — 6,604 M15 candle walk, Jan-Apr 2026, detector v1, held-out Mar-Apr test | **Ship ADR-005 shadow logger** (research-only, 30-day AI-behaviour audit). Hard gate explicitly rejected — net −1.0 R/mo at 2R:1R geometry because frequency loss dominates WR gain. |
| 2 | **FVG density outranks OB distance for the 2R/12H1 horizon.** TEST permutation importance: `h1_fvg_unfilled_count` (0.020) + `m15_fvg_unfilled_count` (0.017) dominate the primary label; OB distance doesn't make top-6. (OB distance DOES dominate the 1.5R/4H1 "quick" label — time-horizon changes what matters.) | Track A §3, permutation importance on TEST set | Open question the ADR-005 shadow logger can answer alongside touch_count: does the AI currently weigh FVG unfilled-count adequately? |
| 3 | **Independent empirical recalibration of v2_shadow magnitude.** 765 of 1,101 TEST primary-positive candles (69.5%) are proxy-rejected by the current C-gate; 100% of those are SHORTs in v1-bullish MSOs. F3 backtest predicted 22.8% raw SHORT CAND emergence on XAUUSD — the latent *population* pre-filter is 5-7× larger than the fill-level measurement F3 produced. | Track A §4 — walk-derived proxy-gate analysis | v2_shadow promotion path is unchanged; Phase 1 independently sizes the underlying opportunity larger than F3 alone showed. |
| 4 | **Anti-pattern classifier has real signal (TEST AUC 0.652) but no shippable operating point pre-v2_shadow.** At 60% precision it flags 109 losses + 41 wins per 150 flags (+27R). Blocked by (a) 70%+ precision collapses n<20 flagged — below CLAUDE.md significance threshold; (b) 96% of flagged cluster is SHORT-in-v1-bullish — calibration inverts under v2. | Track A §6 | Re-run ≥30 days post-v2_shadow production data. Signal is harvestable; timing is blocked behind v2 cutover. |
| 5 | **`h1_ob_max_touch` is top-4 anti-pattern feature.** "When many existing H1 OBs across the MSO are already well-touched, losses come faster." Losing regimes appear to be efficient-zone-clearing regimes, not just "market went the wrong way." | Track A §3 anti-pattern permutation importances | Composite feature (OB supply × avg touch × velocity) is a Phase 2 research lens; no immediate action. |

### What we actually DIDN'T find (genuine nulls)

- **No sub-session bucket edge at current data volume.** 0 EMPHASIS + 0 SKIP at n≥20 threshold across 5 instruments × 3 KZ (Track C). Trimming the worst XAUUSD 60-min bucket yields +0.10 R/mo point estimate, bootstrap CI [−0.25, +0.44] — indistinguishable from zero. This is a real null at 266-trade sample size, not "didn't look hard enough."
- **No sniper-stratum edge on available data.** Non-tautological reduction (A+ AND touch_count=1): n=13, ΔWR −7.6pp vs complement, Bonferroni p=1.00 (Track D). Tells us `setup_grade=A+` alone is not predictive above the 62% XAUUSD baseline.

### Reframed picture (the answer to "is the OB edge decaying?")

The OB edge isn't decaying uniformly — it's **concentrating**:

| Sub-population | Forward 2R/12H1 rate | Current sampling share |
|---|---:|---|
| Fresh (touch=0), proper structural confluence | ~30% | under-represented (fresh OBs aren't yet retest-mature) |
| Touch=1, well-structured | ~7% | majority of current CANDs |
| Touch≥2 / v1-bullish-mislabeled-SHORT | ~2-3% | meaningful share — this is where the leak lives |

CLAUDE.md's quarterly WR decay 73.2% → 59.4% may not be the underlying edge dying. It may be the AI increasingly sampling from the bottom sub-population as OBs age and v1 mislabeling accumulates. **v2_shadow (already in flight)** addresses the SHORT-blind slice. **ADR-005 follow-up** (30-day shadow → soft prompt nudge if AI isn't already discriminating) addresses the touch-count drift slice. Both handles exist; neither requires abandoning the core edge thesis.

We are NOT quoting a combined R/mo estimate until the 30-day AI-behaviour data exists — that guardrail is strict per the research-not-fabrication discipline.

### Highest-priority Phase-1-originated next step

**ADR-005 shadow logger (N2 in §4)** — the only deployable Phase-1 output. Research-only, additive, zero trading risk. Answers "is the AI already discriminating on touch_count + FVG density?" in ~30 days. If answer is NO, a follow-up ADR will propose a soft prompt nudge with a measured R/mo target.

---

## 1. Per-track results

### Track A — XAUUSD reverse-engineering (MIXED)

**Worktree branch:** `research/phase1-track-a-xauusd-reverse` (`0f8b4a3`)
**Source:** `research/phase1_xauusd_reverse_engineering/SYNTHESIS.md` (worktree)

- **Dataset:** 8 parallel slice workers walked 6,604 XAUUSD M15 candles Jan 2 – Apr 13 2026 → 13,208 feature rows (LONG+SHORT). Labeled under the 4 CEO-locked lenses (primary 2R/1R/12H1, quick 1.5R/1R/4H1, premium 3R/1R/24H1, anti-pattern 1R-adv/1R-fav/8H1). IRON train/test split Jan-Feb vs Mar-Apr 13. Detector v1 (stable baseline, NOT perturbing v2_shadow).
- **Classifier TEST AUC** (GradientBoosting, lightgbm unavailable): Primary 0.659, Quick 0.673, Premium 0.630, Anti-pattern 0.652. All Bonferroni-surviving. **Moderate ranker signal, not hard-filter strength** (precision @ best-F1 = 26-43%, well below ~70% gate threshold).
- **Missed-win clusters (3 top):**
  1. `SHORT + D1 unk/transitional + v1 bullish MSO` (test n=876, primary rate 30.8%).
  2. `SHORT + D1 transitional` (test n=2,562, primary rate 26.0%).
  3. `SHORT + sl_fallback + high atr_regime` (test n=71, primary rate 33.8%).
  - **100% of 765/1,101 TEST primary-positive candles proxy-rejected by current C-gate are SHORTs in v1-bullish MSOs.** Same population as ADR-004 / v2_shadow target.
- **Touch-count decay (new, strongest finding):** LONG + sl_source=ob stratified by `h1_opp_ob_touch`: touch=0 31.7% (n=60), touch=1 7.2% (n=680), touch=2 3.1% (n=548), touch≥3 2.1% (n=284). Bonferroni-corrected χ² p ≈ 5e-16.
- **Anti-pattern classifier:** AUC 0.65 is real signal, but no usable operating point (≥70% precision → n<20 flagged; ≤60% precision → Bonferroni-insignificant). Additionally pre-v2 calibration will shift post-v2. **No gate proposal.**
- **Hit/miss mapping vs production CANDIDATE log:** uninformative — `candidate_features_log.jsonl` XAUUSD rows START 2026-04-17 (post-test-window). Zero overlap with Mar-Apr 13 test window. Honest data-availability artifact, not a 100% miss rate.
- **Draft ADR:** `.context/06_decisions/ADR-005_touch_count_shadow.md` — research-only shadow logger + 30-day AI-behaviour audit. Hard gate explicitly rejected with expected-R/mo math.

### Track C — Sub-session edge map (NULL)

**Worktree branch:** `research/phase1-track-c-sub-session-map` (`ed0bc16`)
**Source:** `research/phase1_xauusd_reverse_engineering/SUB_SESSION_MAP.md` (worktree)

- **Dataset:** 266 trades unified from q65_sim (225) + F3 backtest (32) + T7 live-sim (9), date range 2024-04 → 2026-04-08. **Zero live production trade records usable** — 173 live records exist but none have populated `execution`/`exit` fields (FTMO free-trial EA-excluded, retcode "AutoTrading disabled by client"). One Apr-16 XAUUSD fill was "closed by broker" 6 min later with no exit metadata captured.
- **Recommendations at n≥20 threshold: 0 EMPHASIS + 0 SKIP.** Structural data-volume problem, not analytical.
- **The only 5 buckets at n≥20 are all XAUUSD 60-min:**
  - Best total R: XAUUSD NY 14:00-15:00 (n=22, WR 63.6%, E[R] +0.421, +9.27R total) — OBSERVE (E[R]_lo95 = −0.03, crosses zero).
  - Worst E[R]: XAUUSD NY 13:00-14:00 (n=29, WR 48.3%, E[R] −0.088, −2.55R total) — OBSERVE (WR_hi95 65.5% well above 35.7% breakeven).
- **Hypothetical trim lift:** trimming XAUUSD NY 13:00-14:00 alone yields point estimate +0.10 R/month, bootstrap CI [−0.25, +0.44] — **indistinguishable from zero at 95%**. 18% XAUUSD frequency cost, 3pp WR uplift. Per high-quality-frequency framing: **do not trim. Observe.**
- **Pre/post v2_shadow diagnostic not possible** — simulator data ends 2026-04-08 vs flip 2026-04-24. 94% of dataset is LONG (v1 bullish bias).

### Track D — Sniper subset (REJECT + INSUFFICIENT SAMPLE)

**Worktree branch:** `research/phase1-track-d-sniper-subset` (`4350e3f`)
**Source:** `research/phase1_xauusd_reverse_engineering/SNIPER_SUBSET.md` (worktree)

- **Dataset:** 199-row master frame (129 batch + 32 F3 + 38 live — 161 with realized outcome).
- **Exact sniper cell (A+ AND tc=1 AND m5=true AND realized_RR≥2.0): n = 0.** Fatal for two independent reasons:
  1. `m5_refined` is NOT persisted to any historical trade record (only to `pipeline_state/m5_refinement.json`, overwritten per candle).
  2. `realized_RR ≥ 2.0` axis is **tautological** — every batch trade with r_multiple ≥ 2.0 is by construction a WIN (LOSS range [−1.0, −0.09], WIN range [+0.05, +3.99]). Filtering on realized RR is an outcome filter, not a setup filter; zero predictive value ex ante.
- **Non-tautological reduction `A+ AND tc=1`:** n=13, WR 53.8% Wilson 95% [29.1, 76.8], expectancy +0.347R bootstrap [−0.42, +0.93]. Complement: WR 61.5% [53.5, 68.9]. **ΔWR −7.6pp, Fisher p_raw=0.768, Bonferroni p=1.00.** **No edge.** Sniper subset (stripped of tautological axes) performs slightly WORSE than the complement.
- **Required sample for 80% power, 5pp uplift:** ~1,400-1,500 per arm. Current n=13 is ~110× below threshold. At current ~17 trades/month fleet, ~14 years to accumulate.
- **Meta-finding (infrastructure):** `touch_count` and `m5_refined` must be persisted on every filled trade record going forward. This is a **non-trading-logic** addition (no CEO approval required per CLAUDE.md §WF-1 "Allowed without approval: infrastructure"). After ≥6 months of instrumented data, Phase 2 can validly answer this question.
- **Canonical "367 trades" disambiguation:** current live KB is 129 enriched rows (reseeded 2026-04-04). The 367 aggregate is a historical count from session-file `trade_executed=true` markers; surviving per-trade resource is 129. Track D used 129+32+38 honestly vs fabricating the missing 238.

---

## 2. Cross-track convergences

Three independent tracks converged on one underlying truth:

1. **The dataset is not instrumented + volumed for the questions Phase 1 asked.**
   - Track C: bucket n too low (only 5 cells at n≥20, all XAUUSD 60-min).
   - Track D: schema missing `touch_count` + `m5_refined` on trade records.
   - Track A: production CANDIDATE log started too late (2026-04-17) to map hits/misses for Mar-Apr test window.

2. **The v1 bullish bias dominates all SHORT-direction findings.**
   - Track A's top missed-win clusters are all v1-bullish-MSO SHORTs (already targeted by v2_shadow).
   - Track C's dataset is 94% LONG.
   - Track D's analysis is LONG-heavy and not generalizable post-v2_shadow.

3. **FTMO free-trial EA-exclusion (retcode "AutoTrading disabled by client") is a systemic blocker to live-outcome research.**
   - 32 post-Apr-7 live LIMIT_PLACED records, zero have execution/exit data.
   - The single Apr-16 fill that DID execute was closed by broker 6 min later with no exit metadata.
   - This means: until FTMO moves off free-trial (paid FTMO challenge or FN EA add-on), every "live trade outcome" research project is blocked.

4. **v2_shadow is still the single highest-leverage change in flight** — +7.0 R/month estimated per F3 backtest. Phase 1 did not identify any higher-leverage alternative. The 14-day observation window + divergence classification gate remains the correct next gate.

---

## 3. Hypothesis reconciliation vs Phase 1 kickoff brief

| Kickoff hypothesis | Phase 1 finding |
|---|---|
| Track A: "GTOS captures some but not all MFE-positive setups; missed wins form clusters." | **True** — clusters found. But they are dominated by SHORT-in-v1-bullish-MSO, which is already the v2_shadow target. No non-ADR-004 cluster large enough to motivate a new gate. |
| Track C: "15-min buckets have materially different WR; worst 20% trim could raise WR 3-5pp at low cost." | **Unsupported** — dataset too thin. 0 buckets qualify at n≥20 threshold. Even descriptive "trim worst" scenario yields lift indistinguishable from zero at 95%. |
| Track D: "Sniper subset (A+ AND tc=1 AND m5=true AND RR≥2.0) has higher WR than CANDIDATE population." | **Untestable** (m5 field not persisted; RR≥2.0 axis is tautological) + **rejected** on non-tautological reduction (ΔWR −7.6pp, p=1.00 Bonferroni). |

Every kickoff hypothesis either landed on an honest null, a data-structure blocker, or a re-discovery of the v2_shadow path. **This is a valid outcome per CLAUDE.md §Reliability Rule #2 ("file not found is always acceptable"); it is not a research failure.**

---

## 4. Proposed next-step actions (ranked by expected R/month and reversibility)

| # | Proposal | Type | Approval? | Est R/mo impact | Reversibility | Next step |
|---|---|---|---|---|---|---|
| **N1** | Continue v2_shadow 14-day observation (already in flight) | Ongoing | No (in progress) | **+7.0 R/mo** (per F3 backtest) | Fully reversible via flag flip | Let the remote `v2_cutover` check run 2026-06-02 14:00 UTC; CEO reviews weekly divergence-sampling markdown |
| **N2** | Ship ADR-005 — touch-count shadow logger + 30-day AI-behaviour audit | Infra + shadow log | **CEO review of ADR draft** | 0 (observation-only); unblocks follow-up prompt-nudge ADR | Fully additive, reversible | Review `research/phase1-track-a-xauusd-reverse` worktree → approve/reject ADR-005; if approved, Wave 2 implements `candidate_features_log` one-line extension + test |
| **N3** | Persist `target_ob_touch_count` + `m5_refined` on filled trade records | Infra | No (non-trading-logic) | 0 (enables Phase 2 validity); blocks sniper Q for ≥6 months otherwise | Additive schema; safe | Extend `save_trade_record` path in `orchestrator.py`; add to `candidate_features_log.jsonl`; 1 test |
| **N4** | Unblock FTMO live-outcome research by moving off free trial | CEO-level business decision | **CEO decision** | Unblocks future Phase 2 — no direct R/mo estimate | Reversible | CEO weighs paid FTMO challenge / FN EA add-on / keep demo / wait-for-v2-live-data |
| **N5** | Explicit Phase 2 scope: re-run Track C after ≥300 live-filled trades; re-run Track D after ≥6 months of instrumented live data; re-run Track A anti-pattern after ≥30 days of post-v2_shadow production | Plan-of-record | No (planning only) | Deferred | N/a | Documented below |

**Rank rationale (per memory `feedback_research_goal_high_quality_frequency.md`):**
- N1 dwarfs everything else and is already shipping. Everything else is gardening.
- N2 is the only Phase-1-originated shippable deliverable; zero production risk; unblocks a follow-up decision in ~30 days.
- N3 is the cheapest change with the largest forward-research leverage.
- N4 is the biggest hidden cost — every live-outcome research project is blocked until this resolves.
- N5 is how we avoid repeating Phase 1's dead ends prematurely.

---

## 5. Phase 2 scope (deferred until preconditions met)

Do NOT run these until the named precondition holds. They will produce the same null results if run earlier.

| Phase 2 item | Precondition | Expected timing |
|---|---|---|
| Track D re-run (sniper subset) | ≥6 months of trade records with `touch_count` + `m5_refined` persisted AND post-v2_shadow-promotion volume | 2026-Q4 earliest |
| Track C re-run (sub-session edge map) | ≥300 live-filled trades with executed outcomes (requires N4 unblock) | 2026-Q3-Q4 |
| Track A anti-pattern re-run | ≥30 days of post-v2_shadow production data + `candidate_features_log.jsonl` covering the window | 2026-05 post-promotion |
| Track B (instrument expansion, $60-120 API, explicitly OUT OF SESSION 39 scope per kickoff) | CEO greenlight + budget cap room | 2026-05+ |

---

## 6. What did NOT make it into this synthesis (boundary conditions)

- **No production changes were made** in this session. `src/`, `config/`, `prompts/` all untouched. Only additions are research artifacts in worktree branches + `.context/06_decisions/ADR-005_touch_count_shadow.md` (draft) in Track A's worktree + this PHASE1_SYNTHESIS.md at repo root.
- **No new validated numbers** added to CLAUDE.md §Validated Numbers. Touch-count decay is real but awaits live-AI-behaviour confirmation before any canonical claim.
- **No Track B instrument-expansion work done.** Scope was held at Phase 2 per kickoff.
- **No v2_shadow perturbation.** Detector stays frozen at v2_shadow until promotion check 2026-06-02.

---

## 7. Artifact locations

### In worktrees (not merged, not pushed)

| Track | Worktree path | Branch | HEAD |
|---|---|---|---|
| A | `.claude/worktrees/agent-a7c39cbfec5fec7b2/` | `research/phase1-track-a-xauusd-reverse` | `0f8b4a3` |
| C | `.claude/worktrees/agent-ab5f9ce34b1c3de7c/` | `research/phase1-track-c-sub-session-map` | `ed0bc16` |
| D | `.claude/worktrees/agent-ae90bbdf7b7e56912/` | `research/phase1-track-d-sniper-subset` | `4350e3f` |

Key files inside worktrees:
- A: `research/phase1_xauusd_reverse_engineering/{RECON.md, SYNTHESIS.md, slice_worker.py, synthesis.py, slice_[1-8]/features.parquet, synthesis_output/*.json}` + `.context/06_decisions/ADR-005_touch_count_shadow.md`
- C: `research/phase1_xauusd_reverse_engineering/{SUB_SESSION_MAP.md, unified_trades.csv, bucket_stats_[15|30|60]min.csv, lift_analysis.md, _build_dataset.py, _analyze_buckets.py, _lift_analysis.py, _render_report.py}`
- D: `research/phase1_xauusd_reverse_engineering/{SNIPER_SUBSET.md, build_master_df.py, analyze_sniper.py, master_df.jsonl, strata_summary.csv, sniper_comparisons.csv}`

### In main (this session)

- `PHASE1_SYNTHESIS.md` (this file) — uncommitted, awaiting CEO review before commit.

---

## 8. Caveats carried forward from the track reports

1. **All XAUUSD research is circa-Jan-Apr 2026 regime-dependent.** CLAUDE.md §Validated Numbers notes quarterly WR decay 73% → 59%. Findings here may not generalize to later 2026 regime.
2. **Fat-tail discipline applied** — bootstrap CIs (≥1000-5000 iter) + Wilson for proportions, no naive t-tests on R-multiples. But thin-leaf point estimates (e.g., Track A leaf 13 n=45) inherit tail risk.
3. **v1 detector LONG-only bias** dominates all SHORT findings. Any SHORT-specific lens pre-v2_shadow will shift post-promotion.
4. **Simulator ≠ live.** All WR/expectancy in Track C + D are simulator-derived. No tick-level slippage, no real spread, no partial-fill realism.
5. **Multiple-testing posture is Bonferroni across tracks + within-track strata.** BH-FDR would keep a few weakly-significant signals alive but none of them are ones we'd act on at current sample sizes.

---

*End of Phase 1 synthesis. Awaiting CEO decision on N1-N5 ranking + ADR-005 merge-or-reject + worktree-branch merge-or-leave.*
