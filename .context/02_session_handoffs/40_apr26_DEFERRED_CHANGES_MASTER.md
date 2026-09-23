# DEFERRED CHANGES & IMPROVEMENTS — Master Pursuit List

**Created:** 2026-04-26 (session 40 close)
**Author:** Claude Code (Opus 4.7, max effort, end of weekend sprint)
**Purpose:** Comprehensive list of every improvement, fix, or research candidate surfaced by the weekend's data-mining + review agents that was NOT implemented. Fresh session uses this as primary input — dispatch verification/review agents per item, decide what to pursue, ship the validated subset.

**CEO directive driving this list (verbatim):**
> "i want to make sure that we're doing every possible improvement possible, even if it includes risk, but genuinely makes the system better"

So: do not pre-defer items because of risk. Verify each one. If it's valid AND it genuinely improves the system AND we accept the risk, ship it.

---

## Section 1 — How to use this document

**Fresh session workflow:**

1. Regenerate `.context/LIVE_STATE.md` and read it.
2. Read this document end-to-end.
3. For each item in Section 3, dispatch a verification/review agent (Opus 4.7, max effort) per the **Verification brief** field. Each agent reads the cited artifacts + current code, returns: (a) is the finding still valid? (b) is the proposed change correct? (c) what risk does it carry? (d) what's the expected R impact?
4. After all verification agents return, present a triage to CEO:
   - **SHIP** — verified valid, low risk OR risk worth taking
   - **RESEARCH** — needs more data / longer experiment
   - **REJECT** — verification disagreed with original finding
5. Ship the SHIP-bucket items in dependency order. Update CLAUDE.md unresolved-list as items close.

**Anti-patterns to avoid (from this weekend):**
- Don't recreate findings already present — read the artifact files first.
- Don't ship prompt changes without a 60-fixture canary regression run.
- Don't claim significance at n<20 OR Wilson CI crossing the breakeven threshold.
- Don't trust walk-level evidence as predictive of realized R per stratum (memory: `feedback_walk_level_evidence_not_predictive.md`).
- Don't extrapolate backtest finding to live without checking the BT-vs-live divergence (rejected mining surfaced 94% non-fill in BT vs 46% in live for `sl_beyond_ob`).

---

## Section 2 — Honest expectancy + confidence assessment for Monday

These are **my numbers**, derived from current evidence. Fresh session should pressure-test them.

### Edge confidence (does an edge exist?)
- **HIGH** — XAUUSD 62% WR n=129 Oct'25-Mar'26 survives Bonferroni (p=3.42e-08). USDJPY 75.8% n=33 (p=1.96e-04). OB-zone advantage +17pp (p=0.003). Five Bonferroni-surviving findings.
- The cross-instrument validation across metals + JPY classes (per-class agent finding) is consistent: AI uplift +5.8pp metals, +7.4pp JPY.

### Edge magnitude confidence (how big is it?)
- **MEDIUM-LOW** — H2-2026 decay is real. XAUUSD Mar 33%, Apr 10% (n=10) vs H1-2026 (Jan+Feb) 64.5% n=31. Chi-square p=0.006. Cause unknown.
- v2 detector promotion expected to recover SHORT signal (was 0% under v1) — F3 backtest showed +0.407R fleet Exp on v2_shadow.
- Per-class adapter findings: indices class -2.5pp uplift (AI is hurting), tight-FX class -30.8pp (AI is severely hurting). Active fleet has 2 indices instruments (US30, NAS100, plus GER40/UK100 deferred).

### Monday FTMO challenge expectancy ranges

| Scenario | P(Phase 1 pass in 30 days) | P(Phase 1 pass in 90 days) | P(blow up via DD limits) | Expected R/month |
|---|---|---|---|---|
| **Optimistic** (v2 holds, no decay continuation, indices class-bias addressed) | 75-85% | 90-95% | 3-7% | +25R / +2.5% account |
| **Base case** (v2 partial recovery, decay continues but mild, indices class-bias persists) | 60-70% | 80-88% | 8-15% | +10-15R / +1-1.5% |
| **Pessimistic** (XAUUSD Apr-style decay continues, v2 doesn't recover SHORTs, indices keep losing) | 35-50% | 60-75% | 15-25% | +0 to +5R / 0-0.5% |

**My read:** somewhere between base and optimistic. ~70% P(Phase 1 pass in 30 days), ~10% P(blow up).

### What changes the math

- **v2 promotion (Sunday-pending):** if SHORT signal recovers as F3 backtest predicts → optimistic case more likely.
- **Adapter A (XAU-anchor gate by correlation):** if validated and shipped → indices class-bias problem partially addressed → +2-5pp uplift recovery on US30/NAS100. Could shift base→optimistic.
- **Cross-instrument correlation gate (already shipped):** caught USD-weakness 4-way LONG cluster gap. Hard to quantify but likely averted at least one DD event.
- **LONG-WR-watch SPRT halt at <40% n=20:** safety net. Caps blow-up tail risk. If XAUUSD continues Apr 10% performance, it halts XAUUSD LONG within ~20 trades = ~3-5 days.
- **7-instrument fleet:** dilutes single-instrument decay. XAUUSD 0.5% sized down; metals + JPY + indices + tight-FX (observer) diversification.

### What I'm NOT confident about
- Magnitude of v2 SHORT recovery in production. F3 backtest had n=2 XAUUSD SHORTs WIN both — wide CI, but directionally promising.
- Whether April XAUUSD WR=10% is regime-driven (will end when regime changes) or AI-side (will persist until prompt fix). The dumb-momentum baseline showed Apr XAUUSD mechanical 50% WR — pointing to AI-side, but the per-class agent's class-bias finding offers an alternative explanation: residual bullish bias on indices may have diluted XAUUSD mean-reversion signals.
- True impact of fvg_fill + breaker_re_entry frameworks. 4mo backtest showed 0 fvg_fill fills, 2 breaker fills out of 217. Tiny sample, could be backtest-window artifact or could be cosmetic frameworks.
- Whether the ~$57/mo API spend stays under $50-60 cap once 7 instruments are live (cap-saturation risk).

---

## Section 3 — Deferred items (full list with verification briefs)

**Format:** Each item lists: **Source agent / artifact** | **Effort** | **Risk** | **Direct impact if shipped** | **Why deferred this weekend** | **Verification brief for fresh-session agent**.

---

### Group A — Sunday-shippable (low risk, additive, no approval needed)

#### A.1 — `sl_beyond_ob` live shadow logger
- **Source:** `research/rejected_candidates_value_mining/` (live forward-resolution analysis)
- **Effort:** 1-2h code (new shadow logger module + permissions.py hook)
- **Risk:** $0, additive observability only
- **Direct impact if shipped:** Captures every `sl_beyond_ob` L2 rejection's hypothetical outcome live. Feeds the post-30d decision on whether to relax. Currently we have n=35 with WR 45.7% (Wilson [30.5, 61.8]); ExpR +0.65R, +43R/mo if relaxed — but n is too thin to ship the relax. A shadow logger gets us to n=80+ in ~30 days for a confident decision.
- **Why deferred:** Called it "this week" instead of "Sunday" — pure ordering call.
- **Verification brief:** Confirm live `sl_beyond_ob` rejection rate ≥ ~30/mo across active 5 instruments to justify shadow logger ROI. Validate that BT-vs-live disagreement (BT 94% non-fill vs live 46% non-fill) isn't a methodology bug — if it IS a bug, the entire +43R/mo finding might be wrong. Read `research/rejected_candidates_value_mining/10_live_l2_corrected.py` + `13_live_notrade.py`. Output: PASS/FAIL on shipping the shadow logger Monday.

#### A.2 — Direction-emission audit logger (Adapter E)
- **Source:** `research/per_framework_class_analysis/mining_results.json` (per-class agent)
- **Effort:** 1-2h code (logger module + primary_analyzer hook, captures: `instrument`, `proposed_direction`, `xau_d1_direction`, `correlation_to_xau`, `time`)
- **Risk:** $0, additive observability only
- **Direct impact if shipped:** Captures every CANDIDATE emission with direction-vs-XAU-D1 alignment. After 30d we have empirical data on whether the XAU-anchored cross-instrument block is causing direction asymmetry (UK100 100% LONG, GER40 95% LONG, XAGUSD 17% SHORT in backtest — does this hold live?). Validates Adapter A signal before shipping prompt change.
- **Why deferred:** Same — labeled "ship Sunday" but didn't actually ship.
- **Verification brief:** Confirm direction-emission asymmetry holds in shadow log if/when it accumulates. Validate that the per-class agent's metric (LONG share % per instrument) is faithful to current production prompt — not stale. Read `research/per_framework_class_analysis/mine.py` + `mining_results.json`. Cross-reference with `src/prompts/primary_analyzer_prompt.py:1235-1270`. Output: confirmed direction asymmetry rate per instrument (or refuted), with sample sizes.

#### A.3 — Adapter B: Tight-FX SL buffer 0.25→0.50×ATR
- **Source:** Per-class agent
- **Effort:** 5 min config edit (`src/components/permissions.py` or `verification.py` SL buffer constant — currently 0.25×H1-ATR for `entry_in_ob` check)
- **Risk:** Low — only affects tight-FX class (EURUSD/GBPUSD)
- **Direct impact if shipped:** EURUSD currently has 97% L2-rejection rate (168/173); the per-class agent identified the 0.25×H1-ATR SL buffer as too tight for tight-FX volatility. Doubling to 0.50×ATR (matching the OB-retest exception buffer in `gate1.ob_retest_sl_min_buffer_atr`) would make EURUSD viable for reactivation. GBPUSD is observer-mode (trading_enabled=false) so no immediate live effect, but prevents repeating the issue.
- **Why deferred:** EURUSD/GBPUSD are deferred from active fleet → "no Monday urgency" framing. But it's a 5-min change with ~zero risk.
- **Verification brief:** Confirm that the L2 `sl_beyond_ob` check in `src/components/verification.py` is using a hardcoded 0.25×H1-ATR buffer for tight-FX vs the configurable `gate1.ob_retest_sl_min_buffer_atr` (0.5×H1-ATR for OB-retest exception). Run a counterfactual: with the buffer doubled, how many of the 168 EURUSD L2 rejections in the per-class agent's data would have passed? If >30% pass and the resulting WR/Exp R is positive — SHIP. If still <50% pass rate or negative R — REJECT (the buffer isn't the bottleneck).

#### A.4 — CLAUDE.md size prune (36,940 → <30k)
- **Source:** Doc cleanup agent
- **Effort:** ~1h editing (cut chronological deltas from session 33-39 closed-block, old fix-it-once items, redundant validated-numbers caveats)
- **Risk:** None — pure documentation
- **Direct impact if shipped:** Every parallel agent dispatch inherits CLAUDE.md. At ~37k chars × N parallel agents, the bloat tax is real (memory: `feedback_claudemd_size_discipline.md`). Cutting to <30k saves ~7k chars × N tokens per dispatch.
- **Why deferred:** Cleanup agent flagged "needs CEO approval" — but the user instructions in memory explicitly say "Prune proactively past ~35k; cut chronological deltas + full handoff index first." So no approval actually needed.
- **Verification brief:** Identify the 7k+ chars to cut. Candidates: (a) sessions 33-39 closed-block (~3k chars; replace with one-liner pointing at handoff series), (b) full validated-numbers caveats (some can be moved to `.context/01_knowledge_base/`), (c) duplicated runtime instructions already in `LIVE_STATE.md` boilerplate. Verify cut sections aren't load-bearing for any active workflow. Output: a diff that gets CLAUDE.md to <30k chars without losing essential context.

---

### Group B — Sunday cold-review-required (could ship Monday if green)

#### B.1 — Adapter A: Gate XAU-anchor block by |corr| ≥ 0.4 (HIGHEST LEVERAGE)
- **Source:** Per-class agent — primary smoking gun finding
- **Effort:** 30-60 min prompt edit + canary regression
- **Risk:** MEDIUM — touches `src/prompts/primary_analyzer_prompt.py:1252-1270` (DECISION GUIDANCE block). Affects AI behavior for ALL instruments.
- **Direct impact if shipped:** The per-class agent identified this block as the primary mechanism causing class-bias. Current behavior: every non-XAU instrument inherits XAUUSD's D1 directional bias regardless of own structure. Combined with v1's 100%-bullish MSO labels, this produced UK100 100% LONG / GER40 95% LONG / XAGUSD only 17% SHORT direction emission. **Fix:** gate the cross-instrument decision-guidance ONLY when the candidate instrument's correlation to XAUUSD is |corr| ≥ 0.4 (per the cross-instrument correlation matrix already loaded). For tight-FX (DXY-dominant pairs), this still applies (high |corr|). For indices (low |corr| with XAU), the block is silenced. Expected: indices class-bias ~50% reduction → +2-5pp uplift recovery. Could shift Monday base→optimistic case.
- **Why deferred:** Cold-review-before-ship is the right call for any prompt change touching all instruments. Was queued for Sunday cold-review.
- **Verification brief:** This is the highest-leverage Monday-shippable item. Council-pattern is justified here (3-stage: parallel implementers → ranked → chairman synthesis). Stage 1: 3 agents draft the prompt edit independently — each gets the file `src/prompts/primary_analyzer_prompt.py:1230-1273` + the cross-instrument correlation matrix from `src/components/cross_instrument_correlation_gate.py` + per-class agent findings. Stage 2: 2 ranking agents anonymize + score for: correctness, edge-case safety, prompt clarity, regression risk. Stage 3: chairman picks one + drafts canary regression test (60-fixture run + slice of XAU-anchor-conflict cases). If canary is green AND no baseline-fixture flips — **SHIP MONDAY**. If any flips OR canary fails — defer to post-Monday with detailed failure analysis.

---

### Group C — Post-Monday research candidates (longer experiments)

#### C.1 — Adapter C: Drop fvg_fill framework
- **Source:** Per-class agent (Tier 2 backtest 0/217 fvg_fill fills)
- **Effort:** 1 line config (`config/agent_config.yaml` `model_a.enabled_frameworks` remove `fvg_fill`)
- **Risk:** Low (additive removal of a framework that's not firing)
- **Direct impact if dropped:** Removes FVG_FILL section from prompt → smaller prompt, lower cost. ~5-10% prompt-token reduction. No fill-rate impact (already 0).
- **Why post-Monday:** fvg_fill was just shipped Sunday. 4-month BT pre-merge had 0 fills but the BT was on PRE-Sunday-merge code; live behavior on merged code is unknown. Need 30d live observation before killing.
- **Verification brief:** Wait 30 days. After 30d live, count fvg_fill fills + L2 outcomes. If still 0 fills OR ExpR < +0.10R — DROP. If ≥5 fills with positive ExpR — KEEP. Read live shadow logs from 2026-04-27 onward; specifically `knowledge_base/live_evaluations/{INSTRUMENT}/*.jsonl` filtered to `framework="fvg_fill"`.

#### C.2 — Adapter D: Per-class confidence floors
- **Source:** Per-class agent
- **Effort:** Larger prompt rewrite (per-class adaptive thresholds)
- **Risk:** HIGH — fundamental change to confidence scoring
- **Direct impact if shipped:** Tighter filtering on weak-uplift classes (indices, tight-FX), looser on strong-uplift classes (metals, JPY). Could recover the indices class-bias more thoroughly than Adapter A alone.
- **Why post-Monday:** Needs n≥20 per class to validate floors empirically. Current data: tight-FX n thin, indices n=24 NAS100 + similar small samples. Cannot calibrate floors without more data.
- **Verification brief:** After 30-60d live, regress confidence-score-percentile-band → realized-R per instrument class. Identify the per-class confidence threshold at which ExpR becomes negative. If thresholds are stable across 30d — design Adapter D. Otherwise iterate.

#### C.3 — Adapter F: Class-aware LONG-WR-watch SPRT halt thresholds
- **Source:** Per-class agent
- **Effort:** Config + monitor refactor
- **Risk:** Medium
- **Direct impact if shipped:** Per-class halt thresholds (e.g., metals halt at <55% LONG WR n=20, indices at <40% LONG WR n=20) instead of single global threshold. Tighter risk control on weak classes.
- **Why post-Monday:** Each class needs n=20 to calibrate. Monday is day 1.
- **Verification brief:** After 60d live with n≥20 per class on LONG and SHORT, compute per-class halt thresholds. Cross-check with bootstrap CI to avoid over-fitting.

#### C.4 — G0_MULTI gate over-skipping investigation (+6R missed Q1)
- **Source:** Pre-AI gate optimization agent (`research/pre_ai_gate_optimization/analysis.json`)
- **Effort:** Medium investigation (read 9,069 row replay, identify which 9 of 37 A2 CANDs in skip-strata)
- **Risk:** MEDIUM — could un-skip too many losers if the surprise finding is wrong
- **Direct impact if shipped:** Recover ~+6R/quarter (~$2-3K equity at 1% risk) by relaxing the multi-framework pre-AI gate. The pre-AI agent's surprise finding: the gate is OVER-skipping, not under-skipping. 9 of 37 A2 CANDs sit in skip-strata = 7W/2L = +6R missed.
- **Why post-Monday:** Needs 14d v2-live data to validate that BT-finding holds in v2-prod. v2 was promoted Sunday (pending commit per checklist) and the over-skipping may be v1-detector-specific.
- **Verification brief:** After 14d v2-live data, re-run the over-skip analysis on production data. If +6R/14d figure replicates within 50% — SHIP a relaxed pre-AI gate. If not — investigate divergence (likely v1 vs v2 detector difference).

#### C.5 — G2.4 cross-instrument correlation pre-skip
- **Source:** Pre-AI gate optimization agent
- **Effort:** Medium prompt + gate edit
- **Risk:** Medium
- **Direct impact if shipped:** API cost reduction by pre-AI-skipping setups where the candidate's L1-bias direction conflicts with high-correlation peer's recent direction.
- **Why post-Monday:** Needs L1-bias→AI-direction calibration before shipping. The pre-AI gate currently doesn't have a reliable bias→direction predictor.
- **Verification brief:** Verify that pre-AI L1-bias prediction matches AI-emitted direction at >80% accuracy on a 30d shadow window. If yes — design G2.4. If no — kill the proposal.

#### C.6 — `sl_beyond_ob` live relax (JPY/GBP +43R/mo)
- **Source:** Rejected setups mining agent
- **Effort:** Prompt edit
- **Risk:** Medium-high (n=35, Wilson CI [30.5, 61.8] crosses 50%)
- **Direct impact if shipped:** Direct R recovery on JPY/GBP pairs. +43R/mo headline figure but CI is wide.
- **Why post-Monday:** n=35 too thin. Need n≥80 + Wilson lower-bound ≥50% before action. The shadow logger from item A.1 gets us there in ~30 days.
- **Verification brief:** Wait for shadow logger to hit n≥80. Then recompute Wilson CI + ExpR. If lower-bound ≥50% AND ExpR ≥ +0.20R after costs — SHIP relax. Otherwise hold.

#### C.7 — BLOCKED_LIMIT cap saturation +40R/mo recovery
- **Source:** Rejected setups mining agent (separate from gate-relaxation)
- **Effort:** Risk-policy decision (raise `risk.max_concurrent` from current 4 → 6 or 8)
- **Risk:** HIGH — directly increases concurrent position exposure during peak hours
- **Direct impact if shipped:** GER40 +67R, XAGUSD +73R, NAS100 +32R/4mo backtest — these were CANDs that hit the concurrent-position cap and got blocked. Total +159R/4mo backtest = +40R/mo.
- **Why post-Monday:** Cap-relaxation is a separate risk-policy track (already flagged as in-flight research). Crosses the FTMO 5%/4% daily-loss boundary too easily if uncapped.
- **Verification brief:** Run a Monte Carlo with `max_concurrent` = 6 (not 8) on 4mo backtest data using actual realized R per CAND. Compute new MaxDD distribution. If 99% MaxDD < 4% — SHIP cap=6. If between 4-5% — leave at 4 with alert. If ≥5% — REJECT (FTMO-fail risk).

#### C.8 — Cascade prompt re-draft against current 3-framework V3
- **Source:** Doc cleanup agent (cascade prompt LOST during weekend, recovered template at `research/prompt_cascade_ab_test/RECOVERED_v3_cascade_template.py.txt` is STALE vs current production V3)
- **Effort:** Medium prompt work (recovered template needs to absorb fvg_fill + breaker_re_entry framework sections from current V3)
- **Risk:** Medium (full prompt change), but CEO never explicitly approved the cascade UX — it was an A14 A/B test that got lost
- **Direct impact if shipped:** The cascade UX was supposed to make the prompt more explicit about cause-effect chains (impulse → BOS → OB → retest → continuation) — hypothesized to reduce rambling and improve adherence. A14 results lost so we don't have measured impact.
- **Why post-Monday:** Lost Saturday. Re-implementation requires re-running A14 60-fixture A/B against current V3 + fvg_fill + breaker. Not Monday-shippable.
- **Verification brief:** Read `research/cascade_prompt_status_2026-04-25.md` for the recovery context. Re-draft the cascade template against current 3-framework V3. Run A14 A/B (60 fixtures, ~$25). If cascade beats V3 by ≥5pp WR or ≥0.15R ExpR — SHIP. Otherwise abandon.

---

### Group D — Vision program (large effort, high ceiling)

#### D.1 — Tick daemon → AI evaluation wiring
- **Source:** Vision program (CLAUDE.md item: tick capture daemon shipped, features collecting, NOT YET wired)
- **Effort:** Large (modify `primary_analyzer.py` to inject `tick_features` from `data/ticks/{SYMBOL}/*.parquet` into the AI prompt; design prompt section for microstructure features)
- **Risk:** Medium — adds new prompt section, adds parquet read latency to each evaluation
- **Direct impact if shipped:** AI sees per-M15-bar microstructure features (Lee-Ready CVD, footprint imbalance, micro-reversal count, tick velocity, aggressor balance, CVD divergence flag, etc.) — could improve setup-quality discrimination. Vision-aligned (tick-based microstructure was Layer 1 of the powerful-machine vision).
- **Why post-Monday:** Daemon was just shipped Friday. Need to validate tick capture is reliable across all 7 instruments for ≥7 days before wiring into decision path.
- **Verification brief:** After 7 days live, audit `data/ticks/{SYMBOL}/*.parquet` for completeness (no gaps in M15 buckets) across all 7 instruments. Verify `tick_features` extraction works on 100% of bars. Then design + canary the AI integration. SHIP only if canary passes 60-fixture regression.

#### D.2 — Regime classifier → live filter
- **Source:** Regime classifier shipped shadow-only (`src/components/regime_classifier.py`, commit `beba16e`)
- **Effort:** Config + prompt integration (regime-aware halt or sizing rules)
- **Risk:** Medium-high
- **Direct impact if shipped:** Regime-aware halts (e.g., halt mean-reversion edges in clear trending regimes) or regime-aware sizing (e.g., 0.25% in `chop`, 1.0% in `trending_bull`). Could reduce DD from regime-mismatched trades.
- **Why post-Monday:** Needs ≥14d shadow data + comparison to realized outcomes. Promotion to live filter requires V2 classifier + outcome regression.
- **Verification brief:** After 14d, compute realized R per regime classification. If regime-stratified ExpR diverges by ≥0.20R — design live filter. Otherwise V1 classifier may not be the right approach.

#### D.3 — AI tools grounding (research/tool_use_grounding/DESIGN.md)
- **Source:** Vision program scaffolding shipped (`src/components/ai_tools/`, DESIGN.md exists, NOT yet wired into `PrimaryAnalyzer`)
- **Effort:** Large refactor (rewire PrimaryAnalyzer to use Anthropic tool-use API instead of free-text response)
- **Risk:** HIGH — foundational change to AI flow
- **Direct impact if shipped:** Reduce hallucination on numeric facts (price levels, ATR values, OB coordinates) by forcing AI to call typed tools instead of generating free-text. Could materially improve setup-quality if hallucination is a meaningful fraction of false positives.
- **Why post-Monday:** Foundational change. Needs full canary + live-shadow validation period.
- **Verification brief:** Read `research/tool_use_grounding/DESIGN.md` end-to-end. Identify the top-3 highest-impact tool-grounded checks. Implement those as a SHADOW path in parallel with current AI flow. After 30d shadow, compare hallucination rate (price-level disagreements between AI text and tool-call) and outcome-stratified WR. SHIP only if shadow shows ≥5pp WR uplift.

---

### Group E — Earlier-session unresolved items (carry-over)

#### E.1 — Heartbeat kill switch live enablement
- **Source:** CLAUDE.md unresolved item #2
- **Effort:** Config flag flip (`config.heartbeat.flatten_enabled: false → true`)
- **Risk:** HIGH — flatten-on-stale-heartbeat could trigger on benign delays
- **Direct impact if shipped:** Activates the 3-miss/3-trigger cascade. Mitigates risk of dead orchestrator leaving positions open.
- **Why deferred:** Shipped DISABLED. CEO call after live observation window.
- **Verification brief:** After 30d live with `flatten_enabled: false`, count false-positive cascade-near-miss events in `shadow_logs/heartbeat_flatten_events.jsonl`. If <1/week false positives — recommend enable. If higher — diagnose and refine cascade thresholds before enable.

#### E.2 — `skip_first_ny_candle` window-boundary bug fix
- **Source:** CLAUDE.md unresolved item #6 (session 38 R2)
- **Effort:** 5-min code fix (window check `ny_start <= t < ny_start + 15` vs orchestrator `_next_m15_close` returning `close_time + 5s`)
- **Risk:** Low (window expansion or contraction by ~5s)
- **Direct impact if shipped:** Closes the ~13:00:05-13:00:14 wake-up that the policy intends to skip but currently doesn't.
- **Why deferred:** R2 alone shipped zero behavior change. Need 30d shadow counter data at 13:15-13:29 wake-up to decide fix-bound vs retire-policy.
- **Verification brief:** Read shadow counter from `shadow_logs/...` for 30d post-2026-04-27. If counter shows ≥10 wake-ups in the bug window — fix or retire. If <10 — retire policy (it's not actually firing).

#### E.3 — Touch-count threshold 2 → 3 revisit
- **Source:** CLAUDE.md unresolved item #8 (A19 REJECTED LOOSEN_TO_3 due to H2 regime reversal)
- **Effort:** 1 line config (`gate1.touch_count_reject_threshold: 2 → 3`)
- **Risk:** HIGH — A19 H2-2026 backtest showed LOOSEN_TO_3 = -6.00R vs status-quo -0.50R
- **Direct impact if shipped:** Currently REJECTS target H1 OB at touch_count ≥ 2. Loosening to ≥3 would PASS more setups but A19 evidence says they're predominantly losers in H2 regime.
- **Why deferred (rejected this weekend):** A19 explicitly REJECTED the loosen. ADR-005 shadow logger now collecting PASS+REJECT decisions in production. Re-evaluate after ≥30 production rejection events / ≥6 weeks live data.
- **Verification brief:** After 6 weeks production data in `shadow_logs/touch_count_gate_decisions.jsonl`, recompute touch=2 and touch=3 ExpR by stratum. If touch=3 stratum ExpR ≥ touch=2 in production regime — reconsider. Otherwise leave at 2.

---

### Group F — Documentation / state fixes

#### F.1 — Many stale worktrees (~50+ locked agent worktrees)
- **Source:** `git worktree list` output
- **Effort:** Manual cleanup (`git worktree remove --force` for completed agent worktrees)
- **Risk:** Low (worktrees are isolated)
- **Direct impact:** Disk space + cleaner repo. Locked worktrees from completed agents accumulate.
- **Why deferred:** Cosmetic, no operational impact.
- **Verification brief:** Identify worktrees whose branch tip exists in main (cherry-picked already). Force-remove those. Keep only worktrees with unique work.

#### F.2 — Old research branches (`lira-*`, `v4-*`, `phase1-*`)
- **Source:** Branch list audit
- **Effort:** `git branch -D` for shelved research
- **Risk:** Low (work is captured in research/ directory + committed)
- **Direct impact:** Cleaner branch list, easier navigation.
- **Why deferred:** Cosmetic.
- **Verification brief:** Confirm each branch's research artifacts are committed to main under `research/{name}/`. If yes — delete branch. Otherwise import artifacts first.

---

## Section 4 — Pursuit priority recommendation

If fresh session can only ship 3 things Monday, ship these in order:

1. **A.1 + A.2 shadow loggers** — $0 risk, opens decision-data pipeline for #B.1 and #C.6 in 30d
2. **A.3 tight-FX SL buffer config** — 5-min change, removes EURUSD reactivation blocker
3. **B.1 Adapter A (XAU-anchor gate)** — IF Sunday cold-review passes. Highest single Monday R impact.

If fresh session has more bandwidth: ship A.4 (CLAUDE.md prune), then sequence Group C items by elapsed-time milestones (14d v2-live, 30d shadow, 6w production).

If fresh session is risk-averse and CEO prefers stability: ship A.1, A.2, A.3, A.4 only. B.1 deferred 1-2 weeks.

---

## Section 5 — Reference index (every artifact cited)

### Research artifacts (committed in `2cac8f5`)
- `research/per_framework_class_analysis/mining_results.json` — per-class agent raw output
- `research/per_framework_class_analysis/mine.py` — per-class agent code
- `research/rejected_candidates_value_mining/` — full rejected-mining artifacts (13 scripts + JSONLs + CSVs)
- `research/pre_ai_gate_optimization/analysis.json` + `analyze.py` + `rich_per_candle.csv` (9,069 rows)
- `research/instrument_expansion_2026-04-25/TIER2_AGGREGATE_VERDICT.md` — Tier 2 backtest verdicts (XAGUSD PROMOTE-LIVE, NAS100 3-DAY-OBSERVE, GER40/UK100/EURUSD DEFER)
- `research/dumb_momentum_baseline/REPORT.md` — Test A baseline
- `research/touch_count_audit/REVIEWER_PASS.md` — A19 REJECT verdict for LOOSEN_TO_3
- `research/lira_ab_deep_forensic/` — V4+LIRA shelving forensics
- `research/cascade_prompt_status_2026-04-25.md` — cascade-lost recovery report
- `research/WEEKEND_FINAL_REVIEW_2026-04-25.md` — cross-validator weekend summary
- `research/tool_use_grounding/DESIGN.md` — tool-grounding scaffolding design

### Source files referenced (current code, post-`2cac8f5`)
- `src/prompts/primary_analyzer_prompt.py:1230-1273` — XAU-anchored cross-instrument block (Adapter A target)
- `src/components/permissions.py` — touch-count gate, SL gates, cross-instrument correlation gate (line 299)
- `src/components/cross_instrument_correlation_gate.py` — correlation matrix + sizing logic
- `src/components/verification.py` — L2 checks: `entry_in_ob`, `entry_in_fvg`, `entry_in_breaker`, `sl_beyond_ob`
- `src/components/pre_ai_gates.py` — `h1_poi_availability` multi-framework gate
- `src/components/regime_classifier.py` — V1 H4-swing classifier (shadow-only)
- `src/components/ai_tools/` — tool-grounding scaffolding (not wired)
- `src/components/touch_count_gate_logger.py` — ADR-005 logger
- `config/agent_config.yaml` — `model_a.enabled_frameworks`, `gate1.*`, `risk.*`
- `config/profiles/redacted_account.yaml` — XAUUSD 0.5%, XAGUSD 0.5%, NAS100 0.25% overrides

### Live shadow logs (operational data)
- `shadow_logs/touch_count_gate_decisions.jsonl` — ADR-005 PASS+REJECT
- `shadow_logs/structure_detector_divergences.jsonl` — v2_shadow vs v1 (65,201 lines)
- `shadow_logs/heartbeat_flatten_events.jsonl` — heartbeat cascade events
- `shadow_logs/dumb_baseline_hypotheticals.jsonl` (gitignored) — dumb-baseline live shadow
- `knowledge_base/live_evaluations/{INSTRUMENT}/*.jsonl` — per-evaluation live records
- `knowledge_base/no_trades/*.yaml` — NO_TRADE rationales
- `knowledge_base/trade_records/{INSTRUMENT}/*.json` — fill records

### Branches (operational state, post-audit)
- All feature/fix branches squash-merged to main; 0 commits ahead unmerged anywhere
- `feat/tick-capture-daemon` shows 1 commit ahead — that's the pre-squash original (already in main as `f1654f3`)
- ~50 worktree-agent-* branches: locked, completed-agent state, candidates for cleanup
- `staging-sunday-deploy-imported` and `staging/sunday-deploy`: import branches from staging merge, no unique work
- `research/lira-*`, `research/v4-*`, `research/phase1-*`: shelved, artifacts committed

### CLAUDE.md unresolved items still open after this weekend
- Item #2 — Heartbeat kill switch (E.1)
- Item #4 — v2 promotion (Sunday-pending; will close on Sunday config commit)
- Item #6 — skip_first_ny_candle (E.2)
- Item #8 — Touch-count threshold revisit (E.3, post-6w production)

### Memory files (`C:\Users\MSI\.claude\projects\C--Users-MSI-Documents-ai-trading-agent\memory\`)
- `feedback_walk_level_evidence_not_predictive.md` — don't ship gate changes on walk evidence alone
- `feedback_decay_is_ceo_number_one_concern.md` — backtest-shadow > live-shadow when feasible
- `feedback_research_goal_high_quality_frequency.md` — optimize R/month, don't trade freq for tiny WR gains
- `feedback_canary_timeout_scales_with_fixture_count.md` — every fixture-count change requires re-benchmark
- `feedback_long_running_subprocess_pattern.md` — long sims dispatch from main thread, not from inside agents
- `feedback_billing_tracks_distinction.md` — Claude Code subscription vs Anthropic API are separate cost lines
- `project_anthropic_billing_auto_reload_disabled.md` — $50-60 balance IS the cap (no prepaid card)
- `project_distributional_findings.md` — fat-tail ξ=0.35, GARCH 0.9906 — calibration numbers

---

## Section 6 — Fresh session opening commands

```bash
# 1. Read current state
python scripts/generate_live_state.py
cat .context/LIVE_STATE.md

# 2. Read this document
cat .context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md

# 3. Read CLAUDE.md (will point here)
cat CLAUDE.md

# 4. Verify prompt file location for Adapter A
grep -n "XAUUSD D1" src/prompts/primary_analyzer_prompt.py

# 5. Quick sanity on git state
git log --oneline -5
git status
```

Then dispatch verification agents per Section 3 verification briefs. CEO will triage their findings.

---

*End of master deferred-changes document. Fresh session inherits from here.*
