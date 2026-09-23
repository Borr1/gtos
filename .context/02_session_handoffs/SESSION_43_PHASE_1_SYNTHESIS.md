# Session 43 — Phase 1 Final Synthesis & Phase 2 Plan Reset

**Date:** 2026-04-27 (chairman synthesis, after CEO pause)
**Author:** Wave 7 chairman (Opus 4.7, max effort, $0 API)
**Inputs:** Wave 1 (C15/C16/J45/J46-J49/H37+H38), Wave 2 (I41-I44/Q71-Q73), Wave 3 (N62/O65/R74/R75 infra), Wave 4 (E24+E26/S77/S78/S79), Wave 5 (D20+D23), Wave 6 (HALLUC-1/2/4), Windows OS RCA, plus session-42 strategic synthesis (A1/A6/F2/F8/F11/F15)
**Status of underlying research:** all branches committed; **none merged** to main (research artifacts only)
**Production HEAD:** `6eaeaa2` (API efficiency safety branch + Bug #25 fix); 7 orchestrators self-terminated end-of-day or cycle to fresh code Tuesday 08:01 KL

---

## Section 1 — Executive Summary

**The 5 highest-impact Phase 1 findings**

1. **Decay is regime-conditioned LONG-side selectivity collapse.** F15 lifted A6 regime attribution to **+48.3pp Bonferroni p=0.0016** after the F14 broker-history backfill. The v1 detector's 100%-bullish emission funneled the system into the *trending_bull/LONG/XAUUSD-London* cell that collapsed in H2-2026 (76.5% → 16.7%). Not feature drift, not hallucination, not confidence drift — operational responses already correct (v2 detector flip + LONG-WR-watch SPRT).
2. **NAS100's 93% "hallucination" is a deterministic precision bug, not AI capability failure.** HALLUC-1 walked the 13/13 demotion chain step-by-step: NAS100 prompt renders OBs at `.1f`, prompt instructs "every price field has exactly 1 decimal", prompt instructs "entry_price = ob_high" — but `guard_candidate_inconsistent_pois` reads underlying floats. ROUND-HALF-UP makes the guard *mathematically unsatisfiable* whenever the OB high's 2nd decimal is `>=5` (~50% of OBs). The AI did exactly what the prompt asked. Pattern B (9/13) added a separate prompt-vs-guard contradiction on stop_loss anchored to swing-low.
3. **J46-J49 portfolio policy delivers +0.742R/trade vs production baseline (n=321, p=3.3e-20 HIGH).** `0% partial close + immediate-on-TP1 BE + 12-bar time-stop + 3.0R TP1` over 750-config sweep. Per-instrument winners differ → per-instrument deployment. Already wired to a shadow-logger branch for live A/B during Phase 2.
4. **S79 risk-policy: cap=4, 2.0% base risk, sharpe-weighted profile delivers +25.8pp P(pass Phase 1)** over current `cap=2 floor(4/2), 1.0% FN, uniform` configuration (Monte Carlo over 129-fill XAUUSD population). Largest single-knob impact in Phase 1.
5. **S77 + S78 quantify two structural drags.** S77: FN broker costs the system 21.04% of ideal-broker R (n=318, p<10^-27); FTMO equivalent is 15.42%. At Phase 2 scale (~$50/$100/2%), the broker swap could be worth ~$1.2-1.3k/month. S78: dropping NAS100 + XAGUSD raises portfolio Sharpe-per-trade from 0.326 to ~0.45 in top-3-by-sharpe config.

**The 3 highest-priority decisions for CEO**

1. **Approve HALLUC-1 precision fix** (`prompts/primary_analyzer_prompt.py` self-check item 3 + entry_price directive + stop_loss directive; corresponding guard relaxation in `primary_analyzer.py:836`). Blocking NAS100 from CANDIDATE emission for a deterministic system bug, not an AI failure. **Do this Tuesday or Wednesday.**
2. **Approve S79 risk policy ship** (raise `risk_per_trade_pct` 1.0 → 2.0, cap stays at 4, switch to sharpe_weighted profile via per-instrument override). +25.8pp P(pass) is the highest-leverage single change in the Phase 1 program. **DD ceiling 4.44% in-sample is uncomfortable; council-worthy if CEO is risk-averse Phase 1.**
3. **Approve Windows OS RCA fix + operator actions** (canary file-lock ~30 LOC + free 50GB + raise pagefile). $450-540/mo stall savings; lifts the canary fanout cause of two confirmed 5-minute API stalls today.

**The 1-line Phase 2 priority order**

`[K54 regime-aware ML classifier] → [F27-F30 feedback loop] → [HALLUC-3/5 prompt A/B] → [B10/P68-P70 regime-selectivity prompts] → [A4 trending_bull cohort replay] → [C17/C18/C19 fix validation] → [D21/D22 multi-framework production] → [E25 microstructure-in-prompt]`

---

## Section 2 — Decay Diagnosis: Definitive Answers

### The synthesis (cross-referencing Wave 1+2+5 + session-42 carry-forwards)

| Question | Answer | Anchor |
|---|---|---|
| Is decay system-side or market-side? | **System.** AI -0.131R H2 vs mechanical OB +0.036R H2; gap eroded +6.9 → -4.8pp (delta -11.7pp). Mechanical OB still works H2; AI now drags. | A1 dumb-baseline (memory `project_a1_dumb_baseline_verdict_2026-04-26`) |
| LONG vs SHORT contribution? | **LONG-side dominant.** XAUUSD LONG 48.4% → 18.8%; SHORT 91.7% n=12. side bonf p=0.056. | A6 (memory `project_a6_decay_attribution_long_side_concentrated`) |
| Regime contribution? | **Regime is the load-bearing axis.** After F14 broker-history backfill, A6 regime bonf flipped 0.834 → **0.0016** (+48.3pp). H1 78% bullish-cohort 53.1% WR → H2 bullish 4.8% WR. | F15 (memory `project_f15_synthesis_regime_is_load_bearing`) |
| Pinpoint cell? | **XAUUSD London/trending_bull/LONG.** -59.8pp H1→H2 (76.5%→16.7%). Apr-only WR=0% n=4 on London + NY trending_bull. | F2 (memory `project_f2_long_decay_pinpointed_trending_bull_2026-04-27`) |
| Is OB-zone advantage extinct? | **No, decay-dominant but ~78% real decay + ~22% methodology drift.** +16.8 → +12.1 → +4.6pp (pre-2026 → H1 → H2). K54 should weight OB lower but keep. Phase 2 prompts target the *selectivity layer above OB recognition*. | F11 (memory `project_f11_ob_zone_decay_velocity_pinned`) |
| Is hallucination a decay mechanism? | **No.** Intra-April hallucination rate IMPROVED -5.10pp while realized R worsened. Decision-making calibration drifted, not perception. | F8 (memory `project_f8_hallucination_not_decay_mechanism`) |
| Are confidence/walk-level signals predictive? | **No.** B12 confidence rubber-stamps (98% emit confidence=80). B14 walk-level + Track A reverse under realized-R. | session-39, `feedback_walk_level_evidence_not_predictive.md` |
| Multi-framework shape? | **OB+FVG diversification real (uplift +36.8pp coverage). Breaker rare/low value (9.7% candles, BK-only 0.00%).** D20 marginals. | `research/d20_d23_multi_framework/results.json` |

### One-paragraph mechanism statement

The H2 decay mechanism is **regime-conditioned LONG-side selectivity collapse in the v1-detector-induced trending_bull cohort**, mitigated by the **v2 detector promotion (active 2026-04-27, +LONG-WR-watch SPRT halt)** and the **J46-J49 portfolio policy + per-instrument trail rules** Phase 1 produced, monitored by the **S1 monthly-decay shadow monitor + OB-continuation rolling-50 + the new K54 regime-aware classifier** (Phase 2). The OB edge is degraded (+4.6pp in H2 vs +16.8pp pre-2026) but not extinct; Phase 2 prompts attack the *post-OB selectivity layer* — i.e., when the AI gets a valid OB retest in trending_bull, why does it now pick worse trades than mechanical baseline?

---

## Section 3 — AI Failure Modes: Reframed

### What HALLUC-1 changes about the entire AI hallucination narrative

Before Wave 6: "NAS100 is hallucinating 93% of CANDIDATEs; OB confusion or context overload."

After HALLUC-1: **The AI is doing exactly what the system prompt instructed.** The pipeline contains a deterministic precision-mismatch defect:

- `config/agent_config.yaml:685` sets NAS100 `prompt.price_format='.1f'`
- `src/prompts/primary_analyzer_prompt.py:805-808` self-check: "every price field has exactly 1 decimal places"
- `src/prompts/primary_analyzer_prompt.py:658`: `entry_price = ob_high for LONG`
- `src/components/primary_analyzer.py:815-845` `guard_candidate_inconsistent_pois` reads **underlying** floats, requires `entry_price <= ob.high`
- For OBs whose `.high` 2nd decimal `>=5`, ROUND-HALF-UP to `.1f` produces a value `> underlying`. **No AI emission can satisfy all three constraints simultaneously.** Mathematically inevitable.

This is the **same compound-bug class** as `project_eurusd_sl_root_cause` — strict-binary L2 + AI-side `sl_buffer_applied=0.0` + tight-FX precision rounding — now mirrored to indices via the `.1f` price format choice. F12 + F13 already localized US30_cash hallucination to this class (15.5% MSO-grounded after tolerance from 5→100 ticks).

### What HALLUC-2 found

`live_evaluations` does NOT log per-call token usage. `_last_usage` is in-memory in PrimaryAnalyzer and overwritten per candle. `evaluation_logger.py:55` schema has no `usage` block. **Production HALLUC-2 is uncomputable** until ~10-LOC instrumentation patch lands. On the proxy backtest dataset (n=1420 Opus 4.5 records), pooled direction: input_tokens LOWER for hallucinated, output_tokens HIGHER for hallucinated (Mann-Whitney p<0.001 each); but Simpson-confounded by instrument identity. **max_tokens ceiling is NOT the cause** — only 1.2% of records hit the 2000 ceiling, and Fisher exact at-ceiling vs below is p=1.0.

### What HALLUC-4 confirmed

Cross-instrument-context block already gates on `|corr|>=0.4` correctly. No XAU-bias bleed observed in scanned XAU rationale audit (`xau_rationale_hits=0` on the inspected GBPJPY samples; `cited_xau_in_rationale: false`). The B.1 deferral (item #9 in CLAUDE.md) remains valid: revisit only after 30d production data shows residual XAU citation by non-correlated instruments.

### Bug #25 is shipped

Equity=0 transient daily-loss-stop fix landed in `de1bb1f` (merge). Dormant marker cleared 14:35 UTC.

### One-paragraph reframe

**The AI's capability is intact; the failures we observed live were defects in our guard layer.** US30_cash 23.4% and NAS100 93% were both compound-bug classes (precision mismatch + prompt-vs-guard contradiction), not capability failure. Live token-usage observability is the missing piece (HALLUC-2 ~10 LOC fix). Cross-instrument context gating works (HALLUC-4). Hallucination is not a decay mechanism (F8). The remaining open question — *Phase 2 budgeted* — is **why decision-quality drifts even when grounding is intact**, which is regime-conditional selectivity prompt research, not perception research.

---

## Section 4 — Position Management & Sizing: Action Items

### What Phase 1 produced

| Item | Result | n | p | Confidence | Branch |
|---|---|---|---|---|---|
| **J46-J49 portfolio policy** (0% partial + immediate-on-TP1 BE + 12-bar time-stop + 3.0R TP1) | +0.742R/trade vs baseline; mean R +0.342 → +1.084; WR 32.1% → 70.7%; mean DD per trade similar (-0.466 → -0.474 R) | 321 | 3.3e-20 | HIGH | `feat/research-j46-j49-position-mgmt-sweep-v2` (`be33522`) |
| **J45 GBPUSD `atr-0.5` trail** | +1.321R/trade vs static; mean R +1.157 → +2.478 | 35 | 0.003 | HIGH | `feat/research-j45-trailing-stop-sweep-v3` (`87cd1a2`) |
| **J45 portfolio fixed-N10-M50 trail** | +0.164R; not significant | 321 | 0.39 | MEDIUM | same |
| **H37 regime stability** | Persistence rate 79.4%; mid-trade flip does NOT predict outcome (Yates p=0.564) | 335 | 0.564 | HIGH (null) | `feat/research-h37-h38-regime-stability-sizing-v2` (`c4c373d`) |
| **H38 brief sizing rule** {chop=0.25%, trending=0.5%, reversal=1.0%} | LOST $5,673 (5.0%) in H2 vs static 0.5%. Decay was side×regime, not chop-vs-trending. **Recommend side-aware** sizing (LONG=0.25%, SHORT=0.5-1.0%) | 335 | n/a | MEDIUM | same |
| **S79 risk-policy MC** | cap=4, 2.0% base, sharpe_weighted profile → +25.8pp P(pass Phase 1) | 129 (XAU MC) | n/a | MEDIUM (in-sample MC) | `research/s79_risk_policy_counterfactual` |
| **S78 fleet** | Drop NAS100 + XAGUSD: top-3-by-Sharpe (GBPUSD/USDJPY/US30_cash) → annualized Sharpe ~3.7 → ~5.4 (at lower frequency) | 262 | n/a | MEDIUM | `research/s78_fleet_counterfactual` |
| **S77 broker** | FN -21.04% R-loss vs ideal (n=318, p<10^-27); FTMO -15.42%; cheaper to swap to FTMO at Phase 2 | 318 | <10^-27 | HIGH | `research/s77_broker_counterfactual` |
| **C15 ADR-006 counterfactual** | ZERO flips on tolerance gate sweep; gate cannot loosen by design. Cure is on prompt side (sl_buffer_min_ticks). | 133 | n/a | HIGH | `feat/research-c15-adr006-counterfactual-replay-v2` (`328a562`) |
| **C16 tight-FX Pareto** | atr_mult=0.25 better point-estimate for GBPUSD/USDJPY but **n_unique_days=2-3, EURUSD NO_DATA** | 28-34 | n/a | LOW | `feat/research-c16-tight-fx-pareto-sweep-v3` (`d9480b7`) |

### Recommended SHIPPING ORDER (rationale)

**Tier 1 — ship this week (Tuesday-Friday)**

1. **HALLUC-1 precision fix** — bug fix; unblocks NAS100 + indices; mitigates ~15-20% live FN R-loss attributable to precision-class guard demotions. *Allowed without CEO approval per WF-1 "bug fix preventing function".*
2. **Bug #25** — already merged.
3. **API efficiency safety branch** — already merged.
4. **Windows OS RCA file-lock canary fix** — already designed; CEO approval gate; ~30 LOC. ~$450-540/mo savings.
5. **HALLUC-2 token-usage logger (~10 LOC)** — additive logger; unblocks all future HALLUC-style audits.
6. **Q71 slippage logger (~30 LOC)** — additive logger; unblocks Phase 2 broker A/B and ongoing slippage monitoring. Q71 NULL today is a data gap, not a finding.

**Tier 2 — ship next 2-3 weeks (after live observation accumulates)**

7. **J46-J49 shadow logger** (already in flight on `feat/j46-j49-shadow-logger`) — observational A/B vs live for 30d before flip.
8. **J45 GBPUSD `atr-0.5`** — HIGH conf, n=35, p=0.003. Ship as default-OFF config flag; flip ON after 10-15 live GBPUSD fills cross-validate.
9. **D20+D23 framework prioritization** — keep `ob_retest` + `fvg_fill` as primary dispatch; **retire `breaker_re_entry`** (9.7% candle coverage, 0.00% BK-only). Conservative: leave it shadow-only and audit. **Council-worthy** before ship.

**Tier 3 — ship after Phase 2 evidence**

10. **S79 risk policy raise (1.0% → 2.0% sharpe_weighted)** — highest impact but largest behavioural change. Should bundle with v2 detector + LONG-WR-watch SPRT being live for ~30d, and side-aware sizing. Council-worthy.
11. **H38 side-aware sizing** (LONG=0.25%, SHORT=0.5-1.0%) — pairs with #10; bundle.
12. **S78 fleet reduction** (drop NAS100 + XAGUSD) — only after S77 broker decision confirms FN stays through Phase 1. Otherwise re-eval.
13. **S77 broker swap (FN → FTMO)** — at Phase 2 scale only; CEO call. The 21% R-loss is real but the FN paid challenge is in flight.

**Tier 4 — REJECT or do not pursue**

- **C16 tight-FX atr_mult=0.25 changes** — LOW conf, sample too small. Wait for ≥30 fills per cell.
- **I41-I44 correlation gate threshold 0.3** — LOW conf, fails Bonferroni vs 32-cell sweep. Keep current 0.4.
- **C15 gate loosening** — ZERO flips; not actionable.

---

## Section 5 — Operational + Infrastructure

### Already merged in session 43 (HEAD `6eaeaa2`)

- `de1bb1f` Bug #25 equity=0 transient daily-loss-stop fix
- `080f703` Cache TTL 5m → 1h
- `1c233fd` `api_timeout_seconds` 60 → 90s
- `65b3a4e` `timeout_retry_enabled` flag (default false)
- `1fd98a7` `heartbeat.flatten_enabled: true`
- `a413af7` `start_all.bat` staggered 0-6s

### Built but not enabled (research branches)

- **N62 debate shadow wire** — built, default OFF (research door per CLAUDE.md item #10)
- **O65 LanceDB index** — built (sentence-transformers; no Anthropic call)
- **R74 prompt-revision scaffolding** — built, awaiting Phase 2 prompt research
- **R75 weekly review script** — built, ready to schedule

### Operational fixes pending

- **Windows OS RCA file-lock canary** — `src/components/orchestrator.py:_run_canary_check (2419-2516)`. Wrap subprocess spawn in process-shared file lock (`msvcrt.locking` on `knowledge_base/meta/.canary_subprocess.lock`). Re-check cache after acquiring lock. ~30 LOC. **CEO approval gate.**
- **Disk cleanup** — free 50+ GB on C: drive; raise pagefile minimum to 1.5x physical RAM. **Operator action.**
- **Reduce 24/7 orchestrator count** — park XAGUSD/NAS100 on KZ-only launcher (frees ~10-15GB virtual; reduces canary fanout from 6 to 4). **Bundles with S78 decision.**
- **HALLUC-1 precision fix** — `src/prompts/primary_analyzer_prompt.py` (3 directives) + `src/components/primary_analyzer.py:836` (guard tolerance). Council-worthy because it touches prompt + permissions in same patch.
- **HALLUC-2 token-usage logger (~10 LOC)** — extend `src/components/evaluation_logger.py:55` schema with `usage` block read from `primary_analyzer._last_usage`. *Additive observability — no CEO approval needed per WF-1.*
- **Q71 slippage logger (~30 LOC)** — patch `src/components/execution.py` to write `{requested_price, fill_price, slippage}` to `shadow_logs/slippage.jsonl` on every successful `order_send`. *Additive — no approval needed.*

### Microstructure (E24+E26)

`per_cell_correlations[*].verdict = NO_SIGNAL` across all 12 cells. cumulative_delta, footprint_imbalance, micro_reversal_count all Spearman ρ ≈ 0; Bonferroni p=1.0 throughout. **Caveat:** all M15 fallback (real M1 backfill not available). **Recommendation:** do NOT prune microstructure features yet; re-evaluate after a real M1/tick backfill window of ≥30d. Prompt-side consumption (E25) remains Phase 2 candidate but de-prioritized.

---

## Section 6 — Phase 2 Plan Reset

This is the load-bearing section. Phase 1 sharpened the original kickoff order substantially.

### Phase 2 candidate task table

| Rank | Task | Description | Est cost (batch+cache) | Est impact | Phase 1 dependency | Confidence |
|:-:|---|---|---:|---|---|---|
| **1** | **K54 regime-aware ML classifier** | Train per-regime ensemble classifier on extended F14 broker-history dataset (8086 H1 windows + 411 trades). Use regime as first-class feature. Do NOT prune from K50/K51 component-importance noise. | ~$60-150 | If +0.10R/trade across cohort: ~+$1.5k/mo at FN scale | A1+A6+F11+F15+R74 scaffolding | HIGH (well-scoped) |
| **2** | **F27-F30 feedback loop** | Continuous prompt-revision pipeline. R74/R75 already built. Run weekly review → propose targeted prompt diffs → run on canary 60-fixture before merge. | ~$30-60/run × 4-12 runs | Compounding (each run ships a small +Δ) | R74/R75 scaffolding | MEDIUM (process risk) |
| **3** | **HALLUC-3 effort=high vs max** | A/B same prompt across 200-300 evaluations. Test if effort=high (~50% cost) preserves CR/WR. | ~$10-25 | If preserves: ~$6/mo savings × 12 = $72/yr (small but easy) | HALLUC-2 token logger | LOW (cost-saving probe) |
| **4** | **HALLUC-5 A/B without cross_context block** | Test if removing cross_instrument_context block changes CR/WR/quality on non-correlated instruments. | ~$10-25 | Cleaner answer to ADR-006 follow-up B.1 | HALLUC-2 token logger; HALLUC-4 baseline | MEDIUM |
| **5** | **B10/P68-P70 regime-selectivity prompts** | Phase 2 prompt research targets *post-OB selectivity in trending_bull cohort* — when AI sees a valid OB retest, why pick worse-than-mechanical entries? Council-stage if a draft survives canary. | ~$40-80 (council-scoped) | Direct attack on F2/F15 cell | F2+F15+R74; HALLUC-3 ranking | MEDIUM (research) |
| **6** | **A4 AI-on-historical-CANDs replay (trending_bull-scoped)** | Replay the 75 H2-XAUUSD-CAND set under candidate prompts (V3 baseline + best B10/P68 variants). Constrain to trending_bull cohort to control scope. | ~$30-60 (replay-only) | Validates Phase 2 prompt diffs against known-bad cell | B10/P68 prompt drafts | HIGH (controlled replay) |
| **7** | **C17 parallel-evaluation dispatch validation** | Validate ADR-006 parallel-evaluation dispatch end-to-end on 60-fixture canary + 30-day live shadow. | ~$5-10 (canary cost in cache) | Confirms session-41 ADR-006 ship | already shipped | HIGH |
| **8** | **C18 ADR-006 follow-up B.1 corr-gate live** | Ship cross_instrument_context block gate by `|corr|>=0.4` if HALLUC-5 + 30d production data justify it. | ~$0 (config + canary) | Cleaner GBPUSD/USDJPY rationales | HALLUC-5; A.2 audit log | MEDIUM |
| **9** | **C19 v2 detector full backtest** | Run v2-active over the full 411-trade pop (post-F14 broker history) with side-aware sizing + LONG-WR-watch SPRT. Validate operational responses. | ~$0 (replay) | Production confidence | F14+F15 | HIGH |
| **10** | **D21 multi-framework production A/B** | After D23 verdicts, A/B `ob_retest`-only vs `ob_retest+fvg_fill` on 60d canary + 30d live. Retire `breaker_re_entry` if D23 cells confirm low value. | ~$5-15 | Validates Phase 1 D20+D23 | D20+D23 | MEDIUM |
| **11** | **D22 framework-selection shadow** | Shadow-log AI's framework selection vs alternatives (per ADR-006 parallel dispatch) on 30d live. Measure dispatch impact. | ~$0 (shadow logger) | Direct measure of dispatch lift | ADR-006 dispatch | MEDIUM |
| **12** | **B8/B9/B11/B13 AI-behaviour API tasks** | Behavioural batch — confidence calibration, walk-level reverse-engineering, prompt-self-consistency, knowledge-cutoff probes. Likely lower-leverage post-F8 ruling out hallucination. | ~$60-120 | Diagnostic | F8+F11 | LOW |
| **13** | **E25 synthetic tick features in prompt** | Wire E24+E26 microstructure features into prompt context. Re-evaluate AFTER real M1 backfill (≥30d). | ~$30-60 | Likely small (E24+E26 NO_SIGNAL) | M1 backfill window | LOW |

### Phase 2 NEW candidates implied by Phase 1 findings (not in original kickoff)

| Rank | New task | Cost | Impact | Phase 1 anchor |
|:-:|---|---:|---|---|
| **A** | **D.3 production wiring** (after F3-replay confirms gains) | ~$0 | Localized US30/NAS100 fixes | F3+F12+F13 |
| **B** | **K54 production training run** (separate from #1 above; K54 #1 is research, this is the production deployment) | ~$0 (training is local; inference via Anthropic) | Live ML-aided gating | K54 #1 |
| **C** | **B.1 corr-gate ship as default-OFF flag** | ~$0 | Cleaner non-correlated rationales | C18 |
| **D** | **L.1 J45 GBPUSD trailing default-OFF flag** | ~$0 (config) | +1.32R/trade at GBPUSD scale (HIGH conf) | J45 |

### Phase 2 budget request from CEO

| Tier | Tasks | Min $ | Max $ |
|---|---|--:|--:|
| **Critical-path (rank 1-7)** | K54 + F27-F30 + HALLUC-3+5 + B10/P68 + A4 + C17 | $185 | $410 |
| **High-value extension (rank 8-11)** | C18 + C19 + D21 + D22 | $5 | $15 |
| **Diagnostic-only (rank 12-13)** | B8/B9/B11/B13 + E25 | $90 | $180 |
| **TOTAL** | | **~$280** | **~$605** |

**Recommended budget:** **$300-400 prepaid Anthropic top-up (assume $200 currently low),** which covers ranks 1-7 + opportunistic rank 8-11 with cache hits. CEO can authorize ranks 12-13 separately if cost trajectory permits.

**Justification:** Phase 1 cost ~$30-50 + subscription work; Phase 2 produces the K54 regime-aware classifier (single-largest expected impact change) and the regime-selectivity prompt research targeting the F2/F15 pinpointed cell. Without Phase 2, Phase 1's findings (regime is the axis; prompts must target selectivity not perception) cannot be acted on.

---

## Section 7 — Decisions Pending CEO

Numbered, ordered by urgency.

1. **Approve HALLUC-1 precision fix?** Tuesday-Wednesday ship. Bug fix; mitigates NAS100 demotion class. Council-worthy scope (touches prompts + guard).
2. **Approve J45 GBPUSD `atr-0.5` trailing stop ship (config flag, default OFF)?** HIGH conf, n=35, p=0.003. Flag flip after 10-15 live GBPUSD fills cross-validate.
3. **Approve S79 risk policy raise (1.0% → 2.0% sharpe_weighted)?** +25.8pp P(pass Phase 1). Largest single-knob impact. **Council-worthy**; bundle with H38 side-aware sizing.
4. **Approve S78 fleet reduction (drop NAS100 + XAGUSD orchestrators)?** Top-3-by-Sharpe portfolio. Pair with HALLUC-1 fix decision (if HALLUC-1 ships, NAS100 may stay).
5. **Approve Windows OS RCA file-lock canary fix (~30 LOC)?** $450-540/mo stall savings.
6. **Approve disk cleanup + pagefile raise (operator action)?** Companion to #5.
7. **Approve Phase 2 budget?** Recommend $300-400 top-up. Bundle with #8.
8. **Anthropic balance topup decision ($150-200 minimum, $300-400 recommended)?** Current $50 won't last a week per session-42 telemetry.
9. **Any of the breaker_re_entry retirement track?** D20: 9.7% candle coverage, 0.00% BK-only; D23: framework-class realized R below ob_retest in FX cell. Conservative path = leave shadow-only; aggressive = retire from `model_a.enabled_frameworks` config.
10. **Approve HALLUC-2 token-usage logger (~10 LOC, additive observability)?** Per WF-1, additive observability is allowed without approval. Listing for visibility — recommend ship without further sign-off.
11. **Approve Q71 slippage logger (~30 LOC, additive)?** Same as #10.
12. **Approve J46-J49 portfolio policy ship after 30d shadow A/B?** +0.742R/trade portfolio (HIGH conf, p=3.3e-20). Shadow logger already in flight on `feat/j46-j49-shadow-logger`. Decision-after-data; not for this session.
13. **Approve H38 side-aware sizing (LONG=0.25%, SHORT=0.5-1.0%)?** Bundles with #3.

---

## Section 8 — What is NOT Solved

### Phase 1 didn't answer

- **Live token usage** (HALLUC-2 NULL until logger ships).
- **Live slippage** (Q71 NULL until logger ships).
- **Real M1/tick microstructure signal** (E24+E26 ran on M15 fallback; cannot rule out signal at finer granularity).
- **N62 debate framework empirical lift** (built, not wired; CLAUDE.md item #10).
- **Cascade-prompt rebuild** (LOST-IRRECOVERABLE, post-Monday research candidate per CLAUDE.md item #8).

### Tasks deferred to Phase 2 or 3

- All 13 ranked Phase 2 tasks above.
- Vision Layer 2/3 program (not in this session).
- Council-grade prompt rewrite for V4+ (V4 SHELVED per CLAUDE.md item #8; rebuild after K54 + B10 baseline).
- LanceDB session memory re-introduction (T2b proved 55% CR suppression; durable disable per CLAUDE.md config).
- Component 3B Bull/Bear/Judge debate framework decision (DELETE/WIRE/LEAVE; CLAUDE.md item #10).

### Open research questions

1. **Why does AI decision-quality drift in trending_bull/LONG cohort even when grounding is intact?** This is the regime-selectivity question that Phase 2 prompt research (B10/P68-P70) attacks. F8 ruled out hallucination as the mechanism; we don't yet know what *is* the mechanism.
2. **Does v2-detector promotion fix the cohort funneling effect on its own, or does the AI need a separate selectivity-layer prompt?** Live data ≥30 SHORT trades + SPRT result will partially answer; A4 replay sharpens.
3. **Is the OB-zone +4.6pp H2 figure stable, or still in transit?** F11 said decay-dominant ~78% real + ~22% methodology. Re-run after H2 → H3 transition confirms.
4. **What's the FN broker R-loss decomposition on the live LONG-side?** S77 was on extended history; LIVE FN baseline still being collected.
5. **Will K54 regime-aware classifier survive OOS in Phase 2 like Track A failed in Phase 1?** Phase 1's anti-pattern classifier dropped AUC 0.65 → 0.55 OOS (CLAUDE.md item #7). K54 must avoid Track A's failure mode.

### Known data gaps

- `trade_records/` `execution: null` for all 148 April records (memory `project_trade_records_enrichment_gap`).
- `fill_price` never persisted alongside requested price (Q71 root cause).
- Per-call token usage never persisted (HALLUC-2 root cause).
- Microstructure data is M15 fallback; no real M1/tick window of meaningful length.
- `live_evaluations` schema does not include `usage`, `cache_read`, or `cache_creation` blocks.

---

*End of Phase 1 synthesis. Standing by for CEO triage on Section 7 decisions.*
