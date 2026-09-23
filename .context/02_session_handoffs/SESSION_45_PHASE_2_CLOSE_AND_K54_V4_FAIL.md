# Session 45 Handoff — Phase 2 + Forensic Program Close + Q1.5 K54 v4 FAIL + side_aware Ship

**Date:** 2026-04-29 (session close)
**Status:** Q1 CLOSES per Q1.5 FALLBACK 3. Phase 3 pivots to substrate-immune Renaissance candidates.
**Authors:** ML Program Orchestrator (handoff to next session)

---

## TL;DR

Multi-phase research session. **Inputs:** Q1.4 K54 v3 FAIL (1/6 gates). **Outputs:** 22 agent dispatches across forensic + Phase 2 + K54 v4 modeler programs, comprehensive root-cause analysis of every fail, methodology gate locked program-wide, 5 K-family lift claims demolished, **side_aware_everywhere ALPHA shipped (config-only flip)**, K54 v4 PRIMARY FAILED (all 3 architectures), Q1 closes with K54 v4 reframed as K55-shadow refinement only.

**Net inventory change:**
- Pre-session: 5 confirmed-or-candidate alphas (J46-J49, S79, AI baseline, mech OB, K54 v3 top-3% candidate, NAS specialist candidate).
- Post-session: 4 confirmed + 1 modifier (side_aware) + 1 K55-shadow refinement (K54 v3/v4 top-3% — concentration filter on mech OB, NOT independent).
- **Net: BURIED 2 candidates (NAS specialist + K54 family as primary), DOWNGRADED 1 (K54 v3 top-3% from primary to refinement), ADDED 1 modifier (side_aware).**

**Honest verdict on the session value:** the methodology rigor invalidated more than it validated. Real value is in the locked methodology gate (catches future false positives) + the 5 surviving alphas being properly calibrated. Phase 3 priority pivots HARD: stop K-family iteration, start substrate-immune Renaissance discovery (calendar features, free-feed integration).

---

## What got DONE this session (concrete deliverables)

### Production change (1 line)
- `config/agent_config.yaml:85` — `side_aware_sizing.enabled: false → true` (LONG=0.5x SHORT=1.0x universal, NA-5 standardized profile).
- YAML validated. **Orchestrator restart pending** (CEO said "let it apply naturally").
- SPRT auto-disable at LONG WR < 0.50 over 20-trade window is the live safety net.

### Research dispatches (22 agents)
- **12 forensic agents** (`research/ml_program/forensics/2026-04-29/`): A/A2/B/C/D/E/F/G/H/I/J/K1.
- **8 Phase 2 agents** (`research/ml_program/phase_2/`): K1-FU1/FU2/FU3, H-PM01/03/04, NA-3, NA-11.
- **1 K54 v4 modeler** (`research/ml_program/models/k54_v4/`).
- **1 Combined-MC follow-up** (J46×S79×side_aware ship-stack validation).

### Documentation produced
- 30+ memory files in `~/.claude/projects/.../memory/` (auto-loaded in future sessions).
- 2 master syntheses (`forensics/2026-04-29/MASTER_SYNTHESIS.md` + `phase_2/MASTER_SYNTHESIS_PHASE_2.md`).
- Q1.5 hypothesis pre-registered in `PRE_REGISTERED_HYPOTHESES.md`.
- 4 integration tickets in `research/operations/`.
- This session handoff.

---

## What was VALIDATED (DSR + apples-to-apples)

| # | Alpha | Evidence | Status |
|---|---|---|---|
| 1 | **J46-J49 portfolio policy** (J49 TP1=3.0R + J46 partial=0% + J47 immediate-on-TP1 BE; J48 negligible) | DSR-p=1.23e-7 (5.16σ post-deflation); H-PM04 PASS at base=2.0% (P(pass FN) 99.7%/91.7%, P(bust HARD) 0.26-0.54%) | LIVE since commit `2dcee4f` (already shipped pre-session) |
| 2 | **S79 risk policy uniform_fn 2.0%** | DSR-p<2.22e-16 (machine zero); per Agent F is mechanical Kelly-scaling at 0.083× full-Kelly | LIVE since commit `9549928` (already shipped pre-session) |
| 3 | **side_aware_everywhere LONG=0.5x SHORT=1.0x** | H-PM03 Pareto-clean winner (full P(pass) 0.83→0.94, P(bust HARD) 0.150→0.022); Combined-MC PASS on safety axes (P(bust HARD) 0.04-0.06%, p99 MTM-DD 4.77-4.92%) | **FLIPPED LIVE 2026-04-29; orchestrator restart pending** |
| 4 | **AI baseline ~63% WR (pooled)** | NA-3: DSR-validated vs Wilson-95-LB breakeven (DSR-p=2e-4) ONLY; **NOT** vs mechanical OB (DSR-p=0.88, CI includes zero) | Operating; canonical citation = "clears breakeven" |
| 5 | **Mechanical OB cross-period 2022-2023** | z=10.5 separately validated (Agent C); the program's signal-detection foundation | Tracked |

---

## What was DEMOLISHED (5 lift claims invalidated)

| # | Claim | Demolition source |
|---|---|---|
| 1 | Q1.3 Arch A "+0.0492 over K54 v1" | K1: was inflated by +0.0166 baseline-mismatch (modeler used `symbol`-augmented v1 0.5133 instead of canonical 0.5286); apples-to-apples = +0.0339 (FAILS +0.04 threshold) |
| 2 | Q1.3 Arch B "4-of-4 groups positive" | K1-FU2: collapses to 1/4 under canonical baseline; **GBPUSD_USDJPY +0.0024 → -0.0703 sign-flip** (4.4× the baseline-mismatch rate) |
| 3 | NAS_US30 specialist "+0.103 over global" | Agent C apples-to-apples paired Δ=-0.007 (pool-aggregation artifact); K1-FU1 fold-aligned T7 retrain confirmed at per-path Δ=+0.0169 (fails all gates) |
| 4 | Vol-conditional sizing portfolio-wide | H-PM01: Sharpe -2.58%, DSR-p=1.0; only NAS100 sub-PASS |
| 5 | K54 v4 PRIMARY (Hybrid 5 + master + Hybrid 4) | K54 v4 modeler: all 3 architectures FAIL 3/7 testable gates; Phase 2-A backfill INFEASIBLE (broker data limit pre-2024 GBPJPY+US30); top-3% K55-shadow refinement is the only ship target |

---

## CEO decisions this session (audit trail)

1. 2026-04-29: CEO authorized "unlimited time/effort/data" forensic deep-dive ("no ambiguity left").
2. 2026-04-29: CEO approved Phase 2 dispatch sequence ("lets proceed as proposed and recommended").
3. 2026-04-29: CEO approved Phase 2 master synthesis 5 decisions ("let's go as proposed and recommended, i approve").
4. 2026-04-29: CEO chose Path A for ship execution ("lets go path A and do now").
5. 2026-04-29: CEO confirmed "let restart apply naturally; will inform monitoring session."

---

## Open ambiguities (status as of session close)

| # | Ambiguity | Status |
|---|---|---|
| NA-1 | +0.0166 baseline-mismatch program-wide pattern | RESOLVED (K1-FU2; non-uniform 0.6×-4.4×) |
| NA-2 | T7 NAS specialist [-0.007, +0.111] gap | RESOLVED (K1-FU1; BURIED at +0.0169) |
| NA-3 | AI baseline DSR-validated lift claim | RESOLVED (split verdict; vs breakeven only) |
| NA-4 | USDJPY n=33 outlier | OPEN — needs live n≥50 |
| NA-5 | side_aware profile inconsistency | RESOLVED (LONG=0.5x SHORT=1.0x standardized) |
| NA-6 | aggregated AUC vs per-path | RESOLVED (per Agent A2; per-path is overfit) |
| NA-7 | Christoffersen UC test | DEFERRED to K54 v4 holdout (now MOOT — K54 v4 FAIL) |
| NA-8 | UK100 +43.3% recovery | OPEN — flag if UK100 deploys |
| NA-9 | spot-FX coverage gap | OPEN — Databento DEFER, futures broker investigation pending |
| NA-10 | per-instrument λ | DEFERRED to Phase 6 |
| NA-11 | alpha pairwise correlation | RESOLVED (empirical ρ̄=+0.008, K54 v3 top-3% is concentration filter) |
| NA-12 | T_paths 15→25 lift assumption | TESTED via K54 v4 (K54 v3 master at T=15 still survived; K1-FU3 projection over-optimistic) |

**New ambiguities surfaced this session:**
- NA-13: K54 v4 Hybrid 5 marginal +0.0013 over master alone (didn't replicate at retrain).
- NA-14: K54 v3/v4 top-3% concentration filter on mech OB (not separable alpha — needs unified per-M15-candle cohort to measure LIVE Mech-AI rho).
- NA-15: Realistic-density velocity question (Combined-MC 14d median vs S79-density 3d).
- NA-16: Lagged-vol multiplier for FX/metals (Phase 6 candidate).
- NA-17: Q1.6 BLOCKED on alternative-broker data for pre-2024 GBPJPY+US30 OHLCV.

---

## Pending integration / operational work (main-thread queue)

1. **Orchestrator restart** — picks up side_aware flip on next natural restart (CEO directive: "let it apply naturally").
2. **L-6 + L-7 main-thread integration** — existing ticket at `research/operations/l6_l7_integration_ticket_2026-04-29.md`. ~12 + 50-60 LOC across `src/components/primary_analyzer.py` + `slippage_shadow_logger.py` + `execution.py`. 23/23 unit tests pass; reference impls ready.
3. **K55-shadow K54 v3 top-3% scaffold engineering** — existing ticket at `research/operations/k55_shadow_k54_v3_top3pct_integration_ticket_2026-04-29.md`. Updated with NA-11 + K1-FU3 footnotes. Target model: K54 v3 master (existing artifacts; Hybrid 5 marginal +0.030R top-3% improvement not worth re-running). ~3-5 days engineering.
4. **Free-feed integration sprint** — existing ticket at `research/operations/free_feed_integration_sprint_2026-04-29.md`. 10 eng days, $0/yr cost, +$400/yr expected lift, 19 substrate-immune items unblocked. CFTC + FRED + WGC + LBMA + CBOE-GEX scrapers.
5. **Alternative-broker investigation** — pre-2024 GBPJPY+US30 OHLCV unavailable on FN. Investigate NinjaTrader/IBKR/AMP via Rithmic/CQG ($50-100/mo, 30-50% < Databento). Q1.6 unblock prerequisite.

---

## Phase 3 priority pivot (recommended)

**STOP:**
- Further K54 architecture iteration (K54 family is exhausted at n=528 cohort; Q1.6 blocked on broker data).
- Forensic deep-dives on closed claims (NAS specialist, vol-conditional, Q1.3 Arch A all settled).
- Vol-conditional sizing variants beyond NAS100-only (portfolio FAIL settled).

**START (in priority order):**
1. **Free-feed integration sprint** (Agent D's 10 eng-day plan). Best ROI in the program — $0/yr cost, unlocks 19 substrate-immune items.
2. **Agent J top-3 Renaissance candidates** — calendar features (LBMA fix, pre-FOMC, FX-fix W-shape). Highest a priori independence per NA-11 (mechanism decoupled from OB-zone).
3. **Alternative-broker investigation** for pre-2024 GBPJPY+US30 OHLCV. Unblocks Q1.6 K54 family in 6-10 weeks.
4. **L-6 + L-7 main-thread integration**. Unlocks cost analytics + close-side slippage telemetry.
5. **K55-shadow K54 v3 top-3% scaffold engineering**. Complementary signal layer (concentration filter on mech OB).
6. **NAS100-only vol-managed sizing** (Phase 5). Default OFF + 30d shadow A/B once K55-shadow ships.

**Phase 3 hard deadline:** 8 weeks from session 45 close → either add 2-3 more alphas OR re-evaluate program trajectory honestly.

---

## Methodology discipline locked program-wide

Forward gate for every Q1.6+ lift claim:
- DSR-corrected p (Bailey & Lopez de Prado 2014) at ONC effective_N (per Agent B).
- CSCV PBO (Bailey & Lopez de Prado 2017) with n_combinations ≥ 14.
- B=1000 null shuffles (Phipson & Smyth 2010).
- Per-path mean AUC primary aggregator (NOT pooled per-row, per K1-FU1 lesson).
- Apples-to-apples paired comparison (identical CPCV folds + canonical baseline).
- Canonical K54 v1 baseline = 0.5286 (NOT modeler-modified `symbol`-augmented v1 0.5133).
- Cross-period robustness gate (where applicable).
- Pre-dispatch substrate compatibility check (per Agent D's `pre_dispatch_screen.py`).
- Pre-dispatch cohort feasibility verification against `audit/data_backfill_2022_2023.md` (LESSON FROM K54 v4 FAIL).

---

## Honest expectancy (for live FN $100k Phase 1 system)

Per CEO's session-close question. Calibrated against:
- DSR-validated J46-J49 +0.742R/trade
- DSR-validated S79 base=2.0%
- side_aware_everywhere flipped LIVE 2026-04-29 (orchestrator restart pending)
- AI baseline ~63% WR pooled (DSR-validated vs breakeven only)
- Combined-MC realistic-density results

**Trade frequency:** ~17 trades/month historical baseline = ~4/week = ~0.6/day. Realistic range 10-25/month.

**Per-trade R (post-J46-J49):** +0.742R DSR-validated mean (high variance per-trade).

**Effective sizing (post-side_aware on next restart):**
- 91% LONG at 2.0% × 0.5 = 1.0% per trade
- 9% SHORT at 2.0% × 1.0 = 2.0% per trade
- Average: ~1.09% per trade

**Per-trade $ at $100k account:** ~$1,090 risk × 0.742R = ~$809 expected $/trade.

**Per-month $:** ~17 × $809 = ~$13,750 expected $/month at baseline frequency.

**Phase 1 timing ($8,000 = 8% target):**
- Expected ~10 trades to hit target on E[R] math.
- Median days-to-pass per Combined-MC realistic-density: **14 days**.
- Mean days-to-pass: ~3-4 weeks (right-tailed distribution).
- 90th percentile: 6-8 weeks.
- P(pass within 30 days) per Combined-MC realistic: **81%**.
- P(pass within 60 days): ~95% extrapolated.

**Phase 2 timing ($5,000 = 5% target):**
- Lower target → faster on average.
- Expected ~6-7 trades to hit target.
- Median: ~9 days. Mean: ~2-3 weeks. 90th percentile: ~4-6 weeks.
- P(pass | passed Phase 1): ~85% (similar dynamics, lower target).

**Payout timing:**
- Phase 1 + Phase 2 + first payout cycle = **2-5 months realistic**.
- FN typical payout cycle: ~14 days post-Phase 2.

**Cost:**
- API: ~$30/mo (canary $12 + AI primary ~$15-20 with cache).
- Funding fee: already paid.
- Total ongoing: ~$30-50/mo.

**P(payout) — HONEST RANGE: 70-90%.**
- Optimistic (S79-density assumption): 95%+.
- Realistic (Combined-MC realistic density): ~70-80%.
- Pessimistic (regime drift, SPRT auto-disable, bug cascades): ~60%.

**Major caveats (honest):**
1. side_aware just flipped today; live A/B 30d shadow data not yet collected. SPRT could auto-disable.
2. The "17 trades/month" baseline is from older periods; recent live frequency was 1 trade in 2 days due to bug cascade fix recovery.
3. The H1→H2 LONG decay (per F2/F15) was substantial. H3-2026 unknown.
4. FA-2 fix (2026-04-20) recovered some calibration (A4 GREEN n=11 mean R +0.818) but n is small.
5. Daily HARD breach (5%) and total HARD breach (10%) caps are the binding tail-risk. Combined-MC P(bust HARD) 0.04-0.06% means low but nonzero.

**Single-number estimate: 75% confidence of getting first payout in 2-5 months.** That's the honest middle of the range.

---

## Files committed this session (commit reference)

See git log for the comprehensive commit. Key paths:
- `config/agent_config.yaml` (side_aware flip)
- `research/ml_program/forensics/2026-04-29/*` (12 + 2 forensic agent outputs)
- `research/ml_program/phase_2/*` (8 + 2 Phase 2 agent outputs + master synthesis)
- `research/ml_program/models/k54_v4/*` (K54 v4 modeler outputs)
- `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` (Q1.5 entry + result)
- `research/ml_program/MASTER_BACKLOG.md` (status flips)
- `research/ml_program/dispatch_log.md` (Phase 2 + K54 v4 entries)
- `research/ml_program/literature/HYPOTHESIS_BACKLOG.md` (§8 update)
- `research/ml_program/audit/dsr_diagnostics.json` (Q1.5 K54 v4 rows appended)
- `research/operations/k55_shadow_k54_v3_top3pct_integration_ticket_2026-04-29.md`
- `research/operations/free_feed_integration_sprint_2026-04-29.md`
- `research/operations/j46_j49_main_merge_and_side_aware_flip_ticket_2026-04-29.md`
- `scripts/research/c1_coval_shumway_audit.py`
- `scripts/research/dsr_audit.py`
- `scripts/research/na8_babu_decomposition.py`
- `scripts/research/q1_dlinear_baseline.py`
- `CLAUDE.md` (alpha inventory updated; Q1 close)
- `.context/LIVE_STATE.md` (regenerated)
- `.context/02_session_handoffs/SESSION_45_PHASE_2_CLOSE_AND_K54_V4_FAIL.md` (this doc)

---

## What the next session should read first (priority order)

1. `CLAUDE.md` (always read first) — alpha inventory updated to reflect post-session state.
2. `.context/LIVE_STATE.md` — regenerated; auto-derived from git + config + src.
3. **This handoff** — synthesizes everything from the 22-agent session.
4. `research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md` — full Phase 2 verdict.
5. `research/ml_program/forensics/2026-04-29/MASTER_SYNTHESIS.md` — full forensic verdict.
6. Memories auto-load (≥30 new memories from this session).

If diving into a specific topic:
- K54 v4 FAIL: `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` + memory `project_k54_v4_modeler_FAIL_q1_close_FALLBACK_3_2026-04-29`.
- Phase 3 priorities: `research/operations/free_feed_integration_sprint_2026-04-29.md` + Agent J's 25-candidate backlog at `research/ml_program/forensics/2026-04-29/agent_j_candidate_backlog_ranked.csv`.
- Operational: `research/operations/*_ticket_2026-04-29.md` (3 tickets).

---

*End of session 45 handoff. CEO closed session 2026-04-29 post K54 v4 FAIL verdict. Next session: read CLAUDE.md + LIVE_STATE.md + this handoff, then triage Phase 3 dispatch sequence.*
