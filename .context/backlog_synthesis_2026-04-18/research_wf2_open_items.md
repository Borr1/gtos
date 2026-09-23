# Research / WF-2 / ADR Open Items Backlog — 2026-04-18

**Agent role:** Research & backlog sweep (one of three parallel agents — handoffs and quantlabs run separately)
**Session:** 26 (pre-challenge, redacted_account Stellar 2-Step starts Tuesday 2026-04-21)
**Operator:** Claude Code — read-only sweep, no code/config/commit mutations
**Dedup note:** Items overlapping with parallel handoff agent carry `ALSO-IN-HANDOFFS: yes (handoff #)`
**Purpose:** Feed CEO Tier-2/3 prioritization against the 3-day window before live capital

---

## 1. Sweep coverage summary

| Source bucket | Files read | Items surfaced |
|---|---|---|
| WF-2 canon (`.context/04_agents/WF2_SHADOW_GATES_V2.md`) | 1 | 6 |
| ADR parked alternatives (`.context/06_decisions/001–004`) | 4 | 5 |
| Research verdicts (q24, q27, q52, q62, q65, variant_c) | 6 | 9 (incl. shadow enrichments) |
| 113-question plan (`.context/03_analysis/research_execution_plan_113q.md`) | 1 | ~95 unexecuted Qs (10 promoted as R-items, rest cataloged) |
| L4 academic pipeline (`research/academic_pipeline/L4_all_actionable_items_v1.md`) | 1 | ~135 items (12 promoted as R-items, rest cataloged) |
| KAP pipeline (`research/kap_outputs/untested_claims_priority.md`, `ACTIONABLE_TRADING_EDGES_*`, others) | 5 | 6 |
| Podcast intel (`kb_podcast_intelligence_111_episodes.md`) | 1 | 8 unimplemented H# |
| Edge-mechanism / decay docs (`kb_edge_mechanisms_and_risks.md`) | 1 | 3 (Test B, C, D) |
| SWOT (`SWOT_FINAL.md`) | 1 | 8 Opportunities + 3 Weaknesses promoted |
| Operator playbook automation gaps (`operator_decision_playbook.md`) | 1 | 6 |
| Config shadow/disabled flags (`config/agent_config.yaml`) | 1 | 5 |
| Code TODO/FIXME/XXX/HACK markers (grep src/) | all src | 0 |
| Session-26 post-challenge deferred items | 1 | 5 |

**Total surfaced R-items (structured):** 78
**Counts by evidence strength:** HIGH=23, MEDIUM=32, LOW=23

---

## 2. WF-2 Shadow Gates Canon — current status

Source: `.context/04_agents/WF2_SHADOW_GATES_V2.md` (pre-WF-1 cut, April 2026)

| Code | Candidate | Canonical gate | Current status (verified 2026-04-18) | Backlog ID |
|---|---|---|---|---|
| C01 | Trailing stop (TS10) | Live WR ≥55% + trailing adds ≥0.2R | Not built. Shadow logger partially implemented via `partial_close_shadow_logger.py` (Variant C, different beast). | R001 |
| C02 | Friday no-trade filter | Mon–Thu WR ≥5pp > Fri AND n(Fri)≥30 | Not built. No Friday filter, no partition logger. | R002 |
| C03 | Strip confidence scorer | Post-T7 decision still bound. | Partially resolved — T7 C-gate replaced P2A scored output. Confidence still emitted (Q-scores r=-0.06). Code still logs `confidence`. Clean-strip not done. | R003 |
| C04 | ATR multiplier tuning (1.5→1.2, test 1.0) | Bootstrap ≥0.15R lift, p<0.05 | Partially addressed by sl_too_tight + 0.5 ATR sweep floor (ADR 004 REVERT). Full multiplier sweep never tested. | R004 |
| C05 | News filter (NFP/CPI/FOMC) | Post-news WR ≥5pp < baseline | `news_filter.enabled: false`. Infra exists but untuned; explicit "funded-only" toggle per config. | R005 |
| C06 | Session memory revival (structure-only) | None until T2b disproof reversed | T2b proved 55% CR suppression p=0.007 — CURRENTLY KILLED. Revisit as "structural-only" (no labels/numbers per D15 in L4). | R006 |

**Plus:** L4 Cluster D recommends ensemble diverse-prompt voting (D17/D18/D20) as a NEW WF-2 candidate not in the canon. → R007

---

## 3. Research Qs (2026-04-18 verdict synthesis)

| Q | Title | Verdict | Revisit trigger | Backlog ID |
|---|---|---|---|---|
| Q-2.4 / B7 | FVG gap fill rates | DEFER (shadow-log gap/ATR only) | Post-challenge: R2 log ≥30 CANDIDATE evals with FVG; independence test vs OB | R008 |
| Q-2.7 / B2 | Premium/discount zone | DEFER (shadow-log pd_zone) | Post-challenge review of R2 pd_zone feature | R009 |
| Q-5.2 / B6 | Per-symbol MAE SL calibration | KILL H1 — unified 0.5 ATR stands | Shadow monitor optional; revisit on OB-detection change | R010 |
| Q-6.2 / B8 | Partial close optimization (variant C etc.) | DEFER — no scheme clears Bonferroni | n≥30 live BE-triggered trades OR n≥30 Variant-C triggers | R011 |
| Q-6.5 / B4 | Speed-to-MFE as predictor (fast ×10 slower 1R) | NULL — no signal | — | R012 (close) |
| Variant C | 33% @ 1.0R partial close | DEFER — historical p=0.363 | Live n≥30 Variant-C triggers | R013 |

From the 113-question plan (research_execution_plan_113q.md), 19/113 were answered pre-plan. These have NOT been executed and remain open (selected promotions):

| Q# | Area | Priority call | ID |
|---|---|---|---|
| 1.1 | Does a lookback window ≤30 trades predict WR breakdown? (Hotelling T²) | HIGH | R014 |
| 2.1 | Does OB continuation rate vary by session × day-of-week? | MEDIUM | R015 |
| 2.5 | Does mitigated-vs-fresh OB exhibit continuation differential? | MEDIUM | R016 |
| 3.1 | Sub-population "multi-touch" OB (≥2 touches) continuation rate (already partially handled — touch-count gate ships live) | CLOSE-OUT | — |
| 4.1 | Does FTMO daily cap shadow-log correlate with realized vol clusters? | LOW | R017 |
| 5.6 | What is break-even required trade frequency at min_rr=1.5? | LOW | R018 |
| 7.3 | Does two-stage entry (M15 trigger + M1 confirm) beat single M15 entry? | MEDIUM | R019 |
| 8.4 | Does order flow signature at entry (last 3 M1 candles) predict continuation? | MEDIUM | R020 |

---

## 4. Podcast Hypotheses (H1–H34) — unimplemented

Source: `.context/01_knowledge_base/kb_podcast_intelligence_111_episodes.md`

| H | Claim | Status | ID |
|---|---|---|---|
| H1 | Chop-zone entries halve WR | NOT TESTED | R021 |
| H2 | Asia-range midpoint as bias anchor | NOT TESTED | R022 |
| H6 | R:R sweet spot 1.8–2.2 (beats 1.5 and 3.0) | NOT TESTED (config at min_rr=1.5) | R023 |
| H7 | 66% stop reduction after reaching 1:1 (not full BE) | NOT TESTED (BE shadow runs full BE; 66% variant is different) | R024 |
| H10 | Alpha decay speed differs by session | NOT TESTED | R025 |
| H11 | RSI divergence at OB retest boosts WR | NOT TESTED | R026 |
| H12 | Multi-TF confluence (H4 + H1 + M15) | Partially covered by T7 C-gate; full stack not tested | R027 |
| H22 | Kill-zone saturation hurts tail kill-zone | NOT TESTED | R028 |

**Already implemented:** H29 (8% DD → 0.5% risk) LIVE; H2 BE shadow logger; H25 session volatility monitor; H16 US30 sweep divergence.

---

## 5. ADR Parked Alternatives

| ADR | Parked option | Revisit trigger | ID |
|---|---|---|---|
| 001 (Task A OB monitor) | Approach B (side-file swing resolver for live feed) | If live feed can't supply OBs directly | R029 |
| 001 (Task A OB monitor) | Approach C (in-line resolver in orchestrator) | Next WF-1 window — treat as follow-on | R030 |
| 002 (Retest geometry) | Approach D (pre-2024 regime-data extension) | On reject of 2024+ regime homogeneity assumption | R031 |
| 003 (Retest geometry corrected) | — (no parked approaches) | — | — |
| 004 (SL gate reconciliation) | Option C (additive bypass for structural SLs) | Post ≥100 shadow rows in liquidity cluster gate | R032 |
| 004 (SL gate reconciliation) | Option D (narrow Gate B to buffer>0.5 ATR) | If Option C mitigation fails or CEO rejects bypass semantics | R033 |

**ALSO-IN-HANDOFFS:** ADR 004 state is reflected in handoff 26 (REVERTED state). The Option C revisit is explicitly on the post-challenge list.

---

## 6. Config shadow/disabled flags (open decisions)

Source: `config/agent_config.yaml` cross-referenced with CLAUDE.md

| Key | State | Decision pending | ID |
|---|---|---|---|
| `confidence_filter_mode` | "shadow" | Strip vs keep — tied to R003 | (see R003) |
| `sl_liquidity_cluster_enabled` | false | Enable after ≥100 shadow rows show precision/recall gate | R034 |
| `news_filter.enabled` | false | Enable for redacted_account only? Requires calendar source decision | (see R005) |
| `session_memory_enabled` | false | Keep killed vs revive as structural-only | (see R006) |
| `debate_round2_enabled` | true (but unused) | Component 3B PAUSED in orchestrator; either wire or remove flag | R035 |

---

## 7. SWOT-derived opportunities (unaddressed)

Source: `.context/03_analysis/SWOT_FINAL.md`

| Code | Title | Evidence strength | ID |
|---|---|---|---|
| O1 | Adaptive exit / partial close | HIGH (r=-0.06 confidence-win, MFE skew) | R036 |
| O2 | Debate Agent (3B) promotion | MEDIUM (code exists, never evaluated) | R037 |
| O3 | Multi-timeframe confluence scorer | MEDIUM | R038 |
| O4 | Regime-aware framework switch | MEDIUM | R039 |
| O5 | Secondary instruments (EURUSD, NAS100) | HIGH | R040 |
| O6 | Passive alert system (Telegram missed A+) | LOW-MEDIUM | R041 |
| O7 | Strip confidence scorer (meta) | HIGH | (see R003) |
| O8 | Shadow-log OB touch count before live gate | RESOLVED (touch-count gate shipped session 25) | — |

SWOT weaknesses also promoted:

| Code | Title | ID |
|---|---|---|
| W1 | No within-CANDIDATE discrimination mechanism (post-C-gate) | R042 |
| W6 | No adaptive position management (trail / partial) | (R036 / R001) |
| W9 | No graceful API degradation policy | R043 |

---

## 8. KAP claims & academic pipeline items (promotions)

| Source | Claim | Test already done? | ID |
|---|---|---|---|
| KAP untested #1–4 (video_01) | EURUSD H1 100-OB backtest at 1:2 RR (43% WR, 10% DD, 28% untriggered) | NO (EURUSD not in instrument set) | R044 |
| KAP untested #5 | OB WR by weekday (Mon/Fri vs Tue–Thu) | NO | R045 (overlap with Q2.1 / R015) |
| KAP untested #6 | OB age vs WR (fresh > stale) | NO | R046 |
| KAP Edge #1 | Liquidity sweep detection as entry trigger (separate from OB retest) | NO — partially covered by sweep_divergence_monitor.py logging only | R047 |
| KAP Edge #2 | Central-bank calendar position sizing modulation | NO | R048 |
| KAP Edge #4 | Fed linguistic sentiment scoring | NO | R049 |
| L4 A3 | GPD fit to MAE tail (confirm ξ>0) | PARTIALLY via distributional_findings memo | R050 |
| L4 A14 | GARCH-EVT conditional SL vs ATR | NO | R051 |
| L4 A19 | BE trailing stop evaluation (Wilcoxon on BE shadow log) | WAITING FOR n≥30 | R052 (close-out via BE shadow log when ripe) |
| L4 A20 | Empirical Kelly f* from R-multiples | NO | R053 |
| L4 A22 | Risk-constrained Kelly for FTMO | NO | R054 |
| L4 B1 | P(2R \| 1R reached) conditional MFE | PARTIAL via Variant C replay; full distribution not built | R055 |
| L4 B28 | MFE scales with realized volatility (corr > 0.30) | NO | R056 |
| L4 B37 | Single vol-regime classifier modulates all exits | NO | R057 |
| L4 C1 | Post-publication decay benchmark two-proportion z-test | NO | R058 |
| L4 C2 | Quadratic decay model (WR acceleration) | NO (underpowered until more data) | R059 |
| L4 C11 | Google Trends SVI for SMC/ICT vs quarterly WR | NO | R060 |
| L4 D1 | CUSUM on CANDIDATE rate (p0=0.103) | NO | R061 |
| L4 D2 | ADWIN change detection | NO | R062 |
| L4 D6 | Borderline canary fixtures (stale baseline) | NO (canaries all NO_TRADE baseline, flagged in CLAUDE.md) | R063 |
| L4 D7 | DDM on win rate | NO | R064 |
| L4 D17 | 3-prompt diverse ensemble majority vote | NO | R065 |
| L4 D20 | Position reduction on ensemble disagreement | NO | R066 |

---

## 9. Edge-mechanism decay-monitoring open Tests

Source: `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md`

| Test | Description | Status | ID |
|---|---|---|---|
| Test A | Dumb momentum baseline vs OB | DONE (+17pp, p=0.003) | — |
| Test B | Prompt-neutral rerun (same MSOs, stripped prompt) | NOT RUN | R067 |
| Test C | H1 autocorrelation monitoring | NOT AUTOMATED | R068 |
| Test D | OB zone vs generic S/R (post-Test A discrimination) | NOT RUN | R069 |

---

## 10. Operator playbook automation gaps

Source: `.context/05_operations/operator_decision_playbook.md` — scenarios currently requiring manual response but amenable to automation.

| Scenario | Current response | Automation target | ID |
|---|---|---|---|
| S13 | SL/TP broker-reported mismatch | Manual check | Auto-detect + Telegram alert | R070 |
| S23/24 | Zero-trade day/week | Manual recognize | Auto-flag CR below rolling floor | R071 |
| S26 | Flash crash (>2×ATR single candle) | Manual pause | Auto-freeze entry pipeline | R072 |
| S28 | VIX spike threshold | Manual risk reduce | Auto-reduce risk pct | R073 |
| S31 | Correlation exposure gate | Manual check | Already coded; audit log missing | R074 |
| S41 | API model change (silent) | Not handled | Add model-id pinning + drift alert | R075 |

---

## 11. Session-26 post-challenge deferred list (carry-forward)

Source: `.context/02_session_handoffs/26_apr18_pre_challenge_tier1_shipped_handoff.md`

| Item | Deferred by | ID |
|---|---|---|
| F1 EURUSD + NAS100 inclusion (vs O5) | Session 26 | R076 (ties to R040) |
| Variant C partial close promotion | n<30 trigger evidence | (see R013) |
| Liquidity cluster gate enable | ≥100 shadow rows | (see R034) |
| ADR 004 Option C revisit | liquidity-gate maturity | (see R032) |
| Canary fixture refresh to borderline | Canary baseline staleness | R077 (overlaps R063) |

---

## 12. Code TODO / FIXME / XXX / HACK audit

Grep across `src/` returned **zero matches** (clean hygiene — session-21 conftest guard cleared marked items). One structural gap remains NOT marked but surfaced in handoff 17:

| Finding | Source | ID |
|---|---|---|
| `pending_intent` destroyed before `open_trade` in `execution.py:233` | Handoff 17 | R078 (ALSO-IN-HANDOFFS: yes (17)) |
| `_active_trade_record` never set on limit-fill path → `_finalize_exit()` never called | Handoff 17 | (same as R078) |
| Pending-intent not persisted across process restart (watchdog kills every 15 min) | Handoff 17 | R079 (ALSO-IN-HANDOFFS: yes (17, 19)) |

---

## 13. Full candidate table (all R-IDs)

Columns: **ID | Title | Source | Category | Description | Why still open | Evidence | Impact | Cost | Implementation surface | Pre-req/blocker | ALSO-IN-HANDOFFS**

### 13.1 WF-2 canon

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R001 | Trailing stop (TS10) | WF2_SHADOW_GATES_V2 | exit-mgmt | Replace fixed TP with trailing after +1R | Gate requires live WR ≥55% + ≥0.2R lift from trailing shadow log. Shadow logger not yet emitting trailing simulation. | HIGH (backtest +38.9R to +52.4R / 100 trades) | HIGH | MEDIUM (shadow logger add + promotion logic) | `partial_close_shadow_logger.py` sibling + `execution.py` post-promote | Shadow data + ≥30 trades reaching +1R | — |
| R002 | Friday filter | WF2_SHADOW_GATES_V2 | filter | Skip Fri trades if Mon–Thu ≥5pp stronger | Partition logger never shipped | MEDIUM (weekday effect in KAP claim #5, not GTOS-validated) | MEDIUM | LOW (cron-time gate + log) | `permissions.py` + new partition logger | n(Fri)≥30 | — |
| R003 | Strip confidence scorer | WF2_SHADOW_GATES_V2 + SWOT O7 | prompt | Remove `confidence` field from T7 output + log | Prompt change post-WF-1; currently r=-0.06 with wins | HIGH (T5→T8 showed zero predictive power) | LOW (cleanup, no edge gain) | LOW | `prompts/t7_c_gate*.md` + `primary_analyzer.py` parse | CEO prompt-freeze waiver | — |
| R004 | ATR multiplier sweep | WF2_SHADOW_GATES_V2 | risk-geom | Test SL at {1.0, 1.2, 1.5}×ATR | Post-ADR 004, 0.5 ATR floor is new; multiplier sweep never re-run | MEDIUM | MEDIUM | MEDIUM (backtest + canary) | `permissions.py` config + retest study | ≥30 live post-ADR-004 trades | — |
| R005 | News filter (NFP/CPI/FOMC) | WF2_SHADOW_GATES_V2 | filter | Disable entries 30 min pre/post tier-1 release | `news_filter.enabled: false`; calendar source not wired | MEDIUM (L4 B20 Lucca & Moench 2015) | MEDIUM | MEDIUM (calendar API + config) | `filters/news_filter.py` (exists, untuned) | Calendar source decision | — |
| R006 | Session memory structural-only | WF2_SHADOW_GATES_V2 | prompt | Revive memory but strip labels/numbers (per L4 D15) | T2b killed full memory; stripped variant never tested | MEDIUM (L4 D15 expects ≥3pp WR lift) | MEDIUM | MEDIUM (prompt + KB reader) | `session_memory.py` + prompt | CEO approval; costs ~$45 to test | — |
| R007 | Ensemble 3-prompt diverse vote | L4 D17 | prompt | Run 3 prompts per MSO, majority vote | Not in canon but strongest candidate in D cluster | HIGH (L4 D17/D20/D21 form coherent stack) | HIGH (WR ≥3pp + calibrated confidence from agreement rate) | HIGH (3× API cost + prompt authoring) | `primary_analyzer.py` parallel calls + new agg | CEO prompt-freeze + budget | — |

### 13.2 Research-Q verdicts

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R008 | FVG gap/ATR shadow enrichment | q24 verdict | feat-log | Add gap/ATR magnitude features to R2 candidate logger | Verdict DEFER — shadow-log only pre-challenge | HIGH pre-reg (p≈0 size effect) | LOW (shadow only) | LOW (~30–50 LOC) | `src/components/candidate_features_logger.py` | — (pre-challenge safe) | — |
| R009 | Premium/discount pd_zone logger | q27 verdict | feat-log | Shadow-log pd_zone labels + impulse range | Verdict DEFER | MEDIUM | LOW | LOW | R2 logger | — | — |
| R010 | Per-symbol SL shadow monitor | q52 verdict | monitor | Monthly shadow monitor mirroring `ob_continuation_monitor.py` | KILL H1 — no live change, optional monitor | HIGH (clean null, n=799) | LOW | LOW (~150 LOC standalone) | `scripts/mae_per_symbol_monitor.py` | Optional | — |
| R011 | Partial-close scheme re-eval | q62 verdict | exit-mgmt | Re-test 33%/50%/67% schemes on live data | Historical no scheme clears Bonferroni | LOW historical, unknown live | MEDIUM | LOW (replay + decision gate) | `partial_close_shadow_logger.py` | n≥30 BE-triggered live trades | — |
| R012 | Speed-to-MFE (close-out) | q65 report | close | Close as NULL — no signal | Already NULL | — | — | — | — | — | — |
| R013 | Variant C promotion gate | variant_c decision | exit-mgmt | Promote 33% @ 1.0R after live replication | Historical p=0.363; n<30 | MEDIUM | MEDIUM | LOW (flip flag) | `partial_close_shadow_logger.py` | n≥30 live Variant-C triggers | — |

### 13.3 113-question plan promotions

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R014 | Rolling-30 WR breakdown predictor (Q1.1) | 113q plan | monitor | Hotelling T² on rolling-30 feature vector | Early warning not built | MEDIUM | MEDIUM | MEDIUM | `scripts/monitoring/` new | 30+ trades/instrument | — |
| R015 | OB continuation by session × DoW (Q2.1, KAP #5) | 113q plan + KAP | decay | Matrix of continuation by 3×5 bucket | Never computed | MEDIUM | LOW–MEDIUM | LOW (query OB monitor CSV) | `scripts/ob_continuation_monitor.py` extension | — | — |
| R016 | Mitigated vs fresh OB (Q2.5, KAP #6) | 113q + KAP | decay | 2-sample test on fresh vs mitigated continuation | Never computed | MEDIUM (literature-backed) | MEDIUM | LOW | `market_state.py` already flags mitigation | — | — |
| R017 | FTMO daily cap vs realized vol (Q4.1) | 113q plan | risk | Correlate daily cap loss clustering with realized vol | Never computed | LOW | LOW | LOW | New notebook | — | — |
| R018 | Break-even frequency at min_rr=1.5 (Q5.6) | 113q plan | risk-math | Solve E[R] = 0 for trade count | Never computed | LOW | LOW | TRIVIAL | Notebook | — | — |
| R019 | Two-stage entry (M15 trigger + M1 confirm) (Q7.3) | 113q plan | entry | Backtest two-stage | Never computed | MEDIUM | HIGH | HIGH (new component) | new M1 confirm module | CEO prompt/logic change | — |
| R020 | Order-flow signature at entry (Q8.4) | 113q plan | entry | Last 3 M1 candles as continuation feature | Never computed | MEDIUM | MEDIUM | MEDIUM | R2 logger enrichment | — | — |

### 13.4 Podcast hypotheses

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R021 | Chop-zone entry suppression (H1) | kb_podcast | filter | Detect ranging H1 + suppress | Never tested | LOW–MEDIUM | MEDIUM | MEDIUM | `market_state.py` regime classifier | — | — |
| R022 | Asia-range midpoint bias (H2) | kb_podcast | bias | Use midpoint of Asia range as daily bias | Never tested | LOW | LOW–MEDIUM | MEDIUM | new Asia-range module | — | — |
| R023 | R:R sweet spot 1.8–2.2 (H6) | kb_podcast | risk-geom | Sweep min_rr {1.5, 1.8, 2.0, 2.2, 2.5, 3.0} | Never tested; config fixed at 1.5 | MEDIUM | MEDIUM | LOW (backtest sweep) | `config/agent_config.yaml` + batch | CEO config approval | — |
| R024 | 66% stop reduction at 1:1 (H7) | kb_podcast | exit-mgmt | Reduce SL by 66% (not full BE) at +1R | Distinct from BE shadow | LOW–MEDIUM | MEDIUM | MEDIUM | shadow logger variant | — | — |
| R025 | Alpha decay by session (H10) | kb_podcast | decay | Per-session OB continuation trend | Not in current monitor | LOW | MEDIUM | LOW (monitor extension) | `ob_continuation_monitor.py` | — | — |
| R026 | RSI divergence at OB retest (H11) | kb_podcast | feature | Log RSI divergence at retest | Never tested | LOW | LOW–MEDIUM | LOW | R2 logger feature | — | — |
| R027 | Multi-TF confluence (H12) | kb_podcast | bias | Full H4+H1+M15 stack vote | T7 covers only H1/M15 direction; H4 absent | MEDIUM | MEDIUM | MEDIUM | prompt + MSO | CEO prompt change | — |
| R028 | Kill-zone saturation (H22) | kb_podcast | filter | After N trades in KZ, suppress | Already have max_daily_losses=2; not per-KZ cap | LOW | LOW | LOW | `permissions.py` | — | — |

### 13.5 ADR parked alternatives

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R029 | Task A Approach B (side-file swing resolver) | ADR 001 | monitor | Live-feed OB resolver | Revisit only if live feed lacks OBs | LOW (preserved for completeness) | LOW | MEDIUM | `ob_continuation_monitor.py` live mode | Live-feed requirement change | — |
| R030 | Task A Approach C (in-line resolver) | ADR 001 | monitor | Resolver inside orchestrator | Next WF-1 window | MEDIUM | MEDIUM | HIGH | `orchestrator.py` | Next WF window | — |
| R031 | Retest geometry Approach D (pre-2024 data) | ADR 002 | research | Extend data to pre-2024 regime | Assumes regime homogeneity 2024+ | LOW | LOW | MEDIUM | `research/retest_geometry/study.py` | Regime test rejection | — |
| R032 | ADR 004 Option C bypass | ADR 004 | SL-gate | Additive bypass for structural SLs | Post liquidity-gate ≥100 rows | HIGH | HIGH (~4–5 trades/week) | MEDIUM (~30 LOC + tests) | `permissions.py` | Liquidity gate maturity | ALSO-IN-HANDOFFS: yes (26) |
| R033 | ADR 004 Option D narrow | ADR 004 | SL-gate | Narrow Gate B to buffer>0.5 ATR | Fallback if Option C rejected | LOW | LOW (limited unblock) | LOW | `permissions.py` | Option C rejection | — |

### 13.6 Config shadow/disabled flags

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R034 | Enable liquidity cluster gate | agent_config.yaml | SL-gate | Flip `sl_liquidity_cluster_enabled: true` | Awaiting ≥100 shadow rows precision/recall review | MEDIUM | MEDIUM | TRIVIAL flip + recovery plan | `permissions.py` | Shadow maturity | ALSO-IN-HANDOFFS: yes (26) |
| R035 | Wire or remove debate Round 2 flag | CLAUDE.md + config | code-hygiene | `debate_round2_enabled: true` but 3B paused | Dead flag or unrealized feature | LOW | LOW | LOW | orchestrator | — | — |

### 13.7 SWOT opportunities

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R036 | Adaptive exit / partial close (O1) | SWOT | exit-mgmt | Package R001+R013+R024 under one roadmap | Items dispersed | HIGH (multiple studies converge) | HIGH | MEDIUM | multi-file | prior items' prereqs | — |
| R037 | Debate Agent 3B promotion (O2) | SWOT | pipeline | Evaluate 3B behind A/B vs 3A-only | Code exists, never evaluated | MEDIUM | MEDIUM | MEDIUM (A/B harness) | `debate.py` + orchestrator | ≥30 per arm | — |
| R038 | Multi-TF confluence scorer (O3) | SWOT | bias | (see R027) | duplicate; track via R027 | — | — | — | — | — | — |
| R039 | Regime-aware framework switch (O4) | SWOT | framework | Activate different frameworks per regime | `enabled_frameworks` is flat list | MEDIUM (L4 B37 regime classifier) | HIGH | HIGH (multi-framework path) | new regime classifier + orchestrator | — | — |
| R040 | Secondary instruments EURUSD/NAS100 (O5) | SWOT + session-26 | scope | Add instruments to live | Never extended past 5 | HIGH (KAP #1 EURUSD evidence) | HIGH | MEDIUM (new symbol configs) | `config/` + scripts | Post-challenge | ALSO-IN-HANDOFFS: yes (26) |
| R041 | Passive alert for missed A+ (O6) | SWOT | ops | Telegram alert for NO_TRADE that post-hoc was +1.5R | Not implemented | LOW | LOW | MEDIUM | new alert script + Telegram | — | — |
| R042 | Within-CANDIDATE discrimination (W1) | SWOT | prompt | Post-C-gate, no ranking among CANDIDATEs | All CANDIDATEs equal weight | HIGH | MEDIUM | HIGH (prompt redesign or ensemble R007) | prompt + logger | — | — |
| R043 | Graceful API degradation (W9) | SWOT | ops | Defined behaviour on refusals/rate-limits/model-change | Apr 13 event self-resolved; no policy | MEDIUM | MEDIUM | MEDIUM | `primary_analyzer.py` + new refusal policy | — | — |

### 13.8 KAP + L4 promotions

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R044 | EURUSD 100-OB baseline replication | KAP #1–4 | research | Replicate 43% WR / 10% DD claim on EURUSD | Precondition to onboarding | MEDIUM | MEDIUM | LOW (backtest) | `research/` new notebook | MT5 EURUSD history | — |
| R045 | OB by weekday | KAP #5 (dup Q2.1/R015) | decay | — | — | — | — | — | — | — | — |
| R046 | OB age vs continuation | KAP #6 | decay | Log zone age → logistic regression on outcome | Never tested | MEDIUM | LOW–MEDIUM | LOW | R2 logger | — | — |
| R047 | Liquidity sweep as entry trigger | KAP Edge #1 | entry | New framework: sweep-then-displace | Separate from OB retest | MEDIUM (Osler 2005 literature) | MEDIUM | HIGH (new framework) | `primary_analyzer.py` + prompt | — | — |
| R048 | Central-bank calendar sizing | KAP Edge #2 | risk-mod | Upweight after CB buying announcements | Never wired | LOW | LOW–MEDIUM | MEDIUM | new calendar feed | — | — |
| R049 | Fed linguistic sentiment | KAP Edge #4 | research | Hawkish/dovish score vs gold moves | Never wired | LOW–MEDIUM | MEDIUM | HIGH (text pipeline) | new sentiment module | — | — |
| R050 | GPD shape on MAE tail (L4 A3) | L4 | research | Fit GPD, confirm ξ>0.3 | Memo suggests 0.35 but formal fit on current trades missing | MEDIUM | LOW–MEDIUM | LOW | notebook | n≥30 MAE | — |
| R051 | GARCH-EVT conditional SL (L4 A14) | L4 | risk-geom | Compute conditional VaR per trade as alt SL | Heavy dependency; never prototyped | HIGH (Cotter 2007) | MEDIUM–HIGH | HIGH | new module | R050 done | — |
| R052 | BE trailing stop decision (L4 A19) | L4 | exit-mgmt | Wilcoxon on BE shadow log at n≥30 | Waiting on log accumulation | HIGH | MEDIUM | TRIVIAL (decision gate) | `be_shadow_logger.py` → decision notebook | n≥30 BE-triggered | — |
| R053 | Empirical Kelly f* from R-multiples (L4 A20) | L4 | risk-sizing | Bootstrap f* CI + MC at {1%,1.5%,2%,half-Kelly} | Never run | HIGH | HIGH (sizing) | LOW | notebook | 300 R-multiples (GTOS has ~42 live) | — |
| R054 | Risk-constrained Kelly for FTMO (L4 A22) | L4 | risk-sizing | Convex optimization under DD constraint | Never run | HIGH | HIGH | MEDIUM | notebook | R053 + cvxpy | — |
| R055 | Conditional MFE distribution P(nR\|mR) (L4 B1, B36) | L4 | exit-mgmt | Foundation for all partial-close decisions | Partially via Variant C | HIGH | HIGH | LOW | notebook | 300 trades (42 live now) | — |
| R056 | MFE × realized vol correlation (L4 B28) | L4 | exit-mgmt | Compute corr(session RV, MFE) ≥ 0.30 | Never computed | MEDIUM | MEDIUM | LOW | notebook | — | — |
| R057 | Single vol-regime classifier (L4 B37) | L4 | framework | Classify H/M/L vol, apply per-regime exits | Never built | MEDIUM | HIGH | MEDIUM | new module + exits | — | — |
| R058 | Post-publication decay two-prop z-test (L4 C1) | L4 | decay | First-half vs second-half of 300-trade window | Never run | MEDIUM | LOW | LOW | notebook | batch corpus | — |
| R059 | Quadratic decay model (L4 C2) | L4 | decay | Regress quarterly WR with linear + quadratic | Underpowered (4 quarters) | LOW (low power) | LOW | TRIVIAL | notebook | More data | — |
| R060 | Google Trends SVI crowding signal (L4 C11) | L4 | decay | Correlate SMC/ICT search volume with quarterly WR | Never wired | LOW | LOW | LOW | new ingest | — | — |
| R061 | CUSUM on CANDIDATE rate (L4 D1) | L4 | monitor | Two-sided CUSUM at p0=0.103, h=4.0 | Never wired — key gap | HIGH | HIGH | LOW (standalone script) | `scripts/monitoring/` | shadow logs ≥30 | — |
| R062 | ADWIN change detection (L4 D2) | L4 | monitor | river.drift.ADWIN on CR, confidence, token count | Never wired | MEDIUM | MEDIUM | LOW | `scripts/monitoring/` | — | — |
| R063 | Borderline canary fixtures (L4 D6) | L4 + session-26 | monitor | Replace all-NO_TRADE baseline with 50/50 MSOs | Canaries documented as stale in CLAUDE.md | HIGH | MEDIUM | MEDIUM (~$10 + authoring) | `scripts/canary_fixtures/` | CEO sign-off | ALSO-IN-HANDOFFS: yes (26) |
| R064 | DDM on win rate (L4 D7) | L4 | monitor | Warning mu+2σ, drift mu+3σ | Never wired; overlaps with SPRT/CUSUM | MEDIUM | MEDIUM | LOW | `scripts/monitoring/` | — | — |
| R065 | 3-prompt ensemble (duplicate R007) | — | — | — | — | — | — | — | — | — | — |
| R066 | Position reduction on split decisions (L4 D20) | L4 | risk-sizing | Halve size when ensemble splits | Depends on R007/R065 | HIGH | MEDIUM | LOW | `permissions.py` + ensemble | R007 | — |

### 13.9 Edge-mechanism Tests B/C/D

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R067 | Test B prompt-neutral rerun | kb_edge | research | Same MSOs, stripped prompt — measure WR delta | Never run | HIGH (would isolate prompt contribution vs mechanical) | HIGH | MEDIUM (~$15–$30 API) | `scripts/simulate_*` | CEO budget | — |
| R068 | Test C autocorrelation monitoring | kb_edge | monitor | Periodic ACF on H1 returns during KZ | MEDIUM priority per KB | MEDIUM | MEDIUM | LOW | new cron script | — | — |
| R069 | Test D OB zone vs generic S/R | kb_edge | research | Post-Test A discrimination against S/R reversal | MEDIUM priority per KB | MEDIUM | MEDIUM | MEDIUM (comparative study) | `research/` new | — | — |

### 13.10 Playbook automation gaps

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R070 | SL/TP mismatch auto-alert (S13) | playbook | ops | Compare broker-reported SL/TP vs logged | Manual today | MEDIUM | MEDIUM | LOW | watchdog extension | — | — |
| R071 | Zero-trade auto-flag (S23/S24) | playbook | ops | Flag if CR below rolling floor | Manual recognition | MEDIUM | LOW–MEDIUM | LOW | Telegram alert | — | — |
| R072 | Flash-crash auto-freeze (S26) | playbook | ops | Auto-freeze entries on >2×ATR candle | Manual pause | MEDIUM | HIGH (capital protect) | MEDIUM | `orchestrator.py` + `market_state.py` | — | — |
| R073 | VIX auto-reduce (S28) | playbook | ops | Reduce risk_pct when VIX > threshold | Manual risk-reduce | LOW–MEDIUM | MEDIUM | MEDIUM | new VIX feed + `drawdown_manager.py`-style manager | VIX data source | — |
| R074 | Correlation gate audit log (S31) | playbook | ops | Log every correlation-block decision | Coded but audit missing | LOW | LOW | TRIVIAL | `permissions.py` | — | — |
| R075 | Model-id pinning + drift alert (S41) | playbook | ops | Pin model-id hash; alert on silent change | Not handled; high risk for silent regime | MEDIUM | HIGH | LOW | `primary_analyzer.py` | — | — |

### 13.11 Post-challenge carry-forward (session 26)

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R076 | EURUSD + NAS100 onboarding (F1) | session-26 | scope | Full onboard after challenge | Deferred pre-challenge | HIGH | HIGH | MEDIUM | configs + canaries | Challenge complete | ALSO-IN-HANDOFFS: yes (26) |
| R077 | Canary fixture refresh to borderline | session-26 + L4 D6 | monitor | Same as R063 — track as carry-forward | Canary staleness | HIGH | MEDIUM | MEDIUM | `scripts/canary_fixtures/` | — | ALSO-IN-HANDOFFS: yes (26) |

### 13.12 Code-level structural gaps (not TODO-marked)

| ID | Title | Source | Cat | Description | Why open | Evidence | Impact | Cost | Surface | Prereq | Handoff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R078 | Fix pending_intent / _active_trade_record on limit-fill path | Handoff 17 | bug | Intent destroyed before open_trade; exit record never set | Two pre-existing bugs flagged in session-17 sub-agent review | HIGH (can silently lose a limit-filled trade's exit data) | HIGH (correctness) | MEDIUM (4–6 tests + exec refactor) | `src/components/execution.py:233` + `orchestrator.py` | CEO approval + restart | ALSO-IN-HANDOFFS: yes (17) |
| R079 | Persist pending_intent across restart | Handoff 17 + 19 | bug | In-memory only; watchdog kill every 15m loses intent | Not fixed | HIGH (limit orders outside KZ vulnerable) | HIGH | MEDIUM (add to `knowledge_base/`) | intent serializer | — | ALSO-IN-HANDOFFS: yes (17, 19) |

---

## 14. Cataloged but not promoted to R-items

These items are recorded as existing in source documents but deliberately not promoted to individual R-entries because of redundancy, low evidence, or pre-challenge irrelevance:

- **113q plan** — the remaining ~95 questions (Waves 1–5 not promoted here) live in `research_execution_plan_113q.md`. Triage them post-challenge.
- **L4 Cluster A (A4–A29)** — 25+ additional SL-refinement items behind R050–R057.
- **L4 Cluster B (B2–B38 minus promoted)** — 30+ additional exit-optimization items.
- **L4 Cluster C (C3–C32 minus promoted)** — 28+ additional decay/crowding items.
- **L4 Cluster D (D3–D22 minus promoted)** — 18+ additional model-risk items.
- **KAP untested claims #8–#181** — the remaining 173 untested testable claims in `untested_claims_priority.md`.
- **KAP ACTIONABLE_TRADING_EDGES #3, #5–#8** — tokenized-gold volume, GLD flows, misc seasonal items, all non-DIRECT for current instrument set.

These clusters contain thousands of LOW-value items; they should be mined selectively when a specific research brief demands them, not treated as a backlog CEO must walk through.

---

## 15. Dedup note for parallel agents

Explicit overlap flags (carry `ALSO-IN-HANDOFFS: yes (#)` in the full table):

- R032 (ADR 004 Option C) → handoff 26
- R034 (liquidity cluster gate enable) → handoff 26
- R040 (EURUSD/NAS100) → handoff 26
- R063 / R077 (canary refresh) → handoff 26
- R076 (EURUSD + NAS100) → handoff 26
- R078 (execution.py:233 bug) → handoff 17
- R079 (pending_intent persistence) → handoff 17 + 19

All other R-items are research-/ADR-/SWOT-sourced and unlikely to collide with the handoffs-pass agent, though the handoffs pass may repeat R001–R006 (WF-2 canon items appear across multiple handoffs).

---

## 16. Recommended CEO triage bands (for the 3-day window)

**This backlog is READ-ONLY advisory — no prioritization is committed to git.** Ordering below is a quick reference for the CEO's Tier-1/2/3 decision.

**Tier-1 candidates (pre-challenge safe, ships as shadow/observation):**
R008 (FVG gap logger), R009 (pd_zone logger), R010 (MAE monitor), R061 (CUSUM on CR), R063/R077 (canary refresh IF time permits).

**Tier-2 candidates (post-challenge Week 1–2, code change required):**
R032 (ADR 004 Option C), R034 (liquidity gate enable), R078/R079 (execution bugs), R040/R076 (secondary instruments), R001 (TS10 promotion gate), R013 (Variant C promotion), R052 (BE decision at n=30).

**Tier-3 (post-challenge Month 1+, research-heavy):**
R007 / R065 (ensemble), R019 (two-stage entry), R039 (regime-aware framework), R047 (liquidity sweep framework), R051 (GARCH-EVT SL), R053/R054 (Kelly), R055 (conditional MFE distribution), R067 (Test B prompt-neutral rerun).

**Kill / close-out:**
R012 (speed-to-MFE, NULL), R059 (quadratic decay, underpowered), several LOW-evidence KAP ACTIONABLE edges.

---

*End of sweep. File is advisory. No config, code, or prompt mutation performed by this sweep.*
