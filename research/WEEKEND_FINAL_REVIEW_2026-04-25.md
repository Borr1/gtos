# Weekend Final Review — Sessions 39-40 Comprehensive Synthesis

**Reviewer:** Opus 4.7 max-effort, single-pass cross-validation
**Date:** 2026-04-25 (Saturday evening, ahead of Monday FTMO paid challenge)
**Scope:** Every weekend deliverable since session 38 close (`b58e75c` LIRA merge → `d614c54` REVIEWER_PASS docs commit)
**Authoritative state read at start:** `LIVE_STATE.md` regenerated against HEAD `1b2d4e8` then `d614c54`. Final HEAD is `d614c54` per `git log -25`.
**Brutal honesty mandate:** explicit per task brief.

---

## Section 1 — Weekend findings cross-validated

I evaluated every claim against (a) at least two independent agents where available, (b) the underlying data files where the claim points to artifacts, and (c) the final committed source/config code. Conflict resolutions are spelled out below; agreements are summarized.

### 1.1 Touch-count gate — A11 LOOSEN_TO_3 vs A19 REJECT (RESOLVED: REJECT, HIGH confidence)

A11 ran a pooled stratification across A1+A2 (n=98 filled) and recommended LOOSEN_TO_3 with a headline of "+8.52R/12wk." A19, dispatched explicitly to redo the analysis from scratch first, **rejected** for two specific reasons that A11 missed:

- A11 conflated semantics — its "+8.52R" is the REMOVE−KEEP delta, not the LOOSEN_TO_3−KEEP delta. The true LOOSEN_TO_3 uplift on A1 alone is +7.50R, on A1+A2 +12.00R (`research/touch_count_audit/REVIEWER_PASS.md` lines 32-39).
- A11 did not split by H1/H2 regime. A19 found touch=2 reverses from +14R H1 to **−6.5R H2** (Mar+Apr 2026; `REVIEWER_PASS.md` lines 41-58). H2 LOOSEN_TO_3 would have lost −6.50R vs status-quo's −0.50R.

The pairwise Fisher tests do not survive Bonferroni at α=0.0167 (smallest p=1.000; `stats_output.txt` lines 8-14). Statistical power at n=98 is ~10%. Permutation test on touch=2 vs (touch=1+touch≥3) gives p=0.2045.

**Actioned commits:** `daabff8` (KEEP touch_count at 2 + tick-bar fix), `fba3875` (ADR-005 logger). CLAUDE.md item #8 updated to RESOLVED. **HIGH confidence.**

### 1.2 Prompt-neutral test (A2) vs prompt-cascade A/B (A14) — COMPATIBLE

The brief said these contradict; they do not. The two `__pycache__/`-only directories (`prompt_neutral_test/` and `prompt_cascade_ab_test/`) ran but **left no committed report files**. Verified:

- `prompts/__pycache__/primary_analyzer_prompt_v3_cascade.cpython-313.pyc` exists, `prompts/primary_analyzer_prompt_v3_cascade.py` does NOT (the .py source was either unstaged or removed; only the compiled binary remains as an artifact).
- `git log --all --oneline | grep -i cascade` returns 0 commits.
- `src/prompts/` contains only the production `primary_analyzer_prompt.py` plus the long-paused debate/judge/postmortem prompts.

**Verdict:** A2 found V3 prompt-neutral SAFE (the prompt does not bake in regime assumptions that the data refutes). A14's cascade A/B was an experiment whose outputs are ephemeral; nothing was shipped. The two are not in tension because A14 was never promoted. **The "SHIP-TUESDAY cascade" tag in the brief is unsupported by code reality — there is no cascade prompt to ship.** I am revising the action list to reflect this. **MEDIUM-HIGH confidence** that A14 was a test, not a deploy candidate; I have not seen A14's actual numerical output, only its trace via the .pyc file's existence.

### 1.3 Microstructure FX-cross REJECT vs decay-agent JPY-cross IMPROVING — COMPATIBLE (microstructure wins)

`03_MICROSTRUCTURE.md` puts JPY-cross spread costs at 20-26% of expected R (lines 73-79: GBPJPY 20.5%, AUDJPY 25.6%, CHFJPY 26.3%, EURJPY 24.1%). `02_DECAY_ANALYSIS.md` shows EURJPY +17.3pp improving (line 110). **These are both true.** EURJPY's mechanical OB-WR is improving from 43% H1 to 60% H2 across Jan-Apr 2026, but the spread tax means a 1.5R target gives net only ~1.14R after costs. Subtract the structural cost from the structural rate-of-return and the edge is roughly flat.

The same applies in reverse for XAUUSD/US30: r_cost_typ_% is 2.25% and 2.26%, near-free. **Spread tax is decisive when rates are in the 50-60% mechanical band.** The instruments worth promoting are those where (a) mechanical WR ≥ 55% AND (b) spread tax ≤ 10% AND (c) AI adds discrimination on top. Tier 2 verdict (§1.5) confirms this lens. **HIGH confidence.**

### 1.4 Structural-screen GBPUSD REJECT vs GBPUSD review EXTEND-OBSERVER — COMPATIBLE

`01_STRUCTURAL_SCREEN.md` ranks GBPUSD as REJECT — composite 52.4 (bottom quartile), mechanical OB-WR 47.6% in H2-2026. `04_GBPUSD_OBSERVER_REVIEW.md` recommends EXTEND-OBSERVER, NOT promote-live, NOT kill — explicitly because L2-reject rate is 50% and is REGRESSING post-FA-2 (lines 12-21). The reviewer found stale-OB anchoring (16/28 records pin the same 1.34616 entry, line 18) is a prompt-architecture issue that prompt v2 needs to address.

These two recommendations are operationally identical: keep `trading_enabled: false` for GBPUSD on Monday, allow the bias to be cleared by v2-active production data (which produces SHORTs, removing the 100% LONG bias the v1-detector imposes), and re-evaluate after ≥20 post-fix CANDs and ≥20 live SHORT trades. **HIGH confidence.** Verified: `config/agent_config.yaml:434` has `trading_enabled: false` for GBPUSD.

### 1.5 Tier 2 backtests vs Tier 1 predictions — RESONANT, but the **`TIER2_AGGREGATE_VERDICT.md`** the brief expected does NOT exist

The brief mentioned `TIER2_AGGREGATE_VERDICT.md` "may not exist yet" — it does not. I aggregated the 35 slice `all_results.json` files myself (28 successful EURUSD/NAS100/UK100/XAGUSD slices + 7 failed GER40 slices that returncode 1 with empty data). **Aggregated outcomes (using `r_multiple` and `direction` fields):**

| Symbol | CANDs | Filled | Wins | TR | WR | Exp R | Cost ($) | LongN/WR | ShortN/WR |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| **XAGUSD** | 47 | 46 | 33 | +35.30R | **71.7%** | **+0.767R** | 20.92 | 38 / 71.1% | 8 / 75.0% |
| **NAS100** | 27 | 24 | 15 | +13.50R | **62.5%** | **+0.562R** | 26.03 | 22 / 68.2% | 2 / 0.0% |
| GER40 | 42 | 0 | — | — | — | — | 28.20 | (failed slices) | — |
| UK100 | 28 | 26 | 12 | +4.00R | 46.2% | +0.154R | 28.20 | 26 / 46.2% | 0 / — |
| EURUSD | 5 | 5 | 1 | −2.50R | 20.0% | −0.500R | 25.89 | 3 / 0% | 2 / 50% |

**Re-coupling to Tier 1 predictions:**
- XAGUSD was the structural-screen TOP composite (67.7) and rank-1 by trend-strength. Tier 2 confirms — 71.7% WR Exp +0.767R. **STRONG-CANDIDATE confirmed.**
- NAS100 was rank-22 (improving, +18.1pp H1→H2), 60.8% mechanical OB. Tier 2 actually overshoots — 62.5% WR Exp +0.562R with the AI gate. **PROMOTE candidate.**
- UK100: structural composite 50.6, mechanical OB 60.8% Tier 1. Tier 2's 46.2% (n=26) is WORSE than mechanical. AI is not adding value here; cluster overlap with US30 (CFD index, similar microstructure). **HOLD; insufficient signal.**
- EURUSD: ran 5 CANDs across 7 slices ($25.89 cost). 1W/4L. **Backtest sample too small to act on.** This is the Tier 2 sample-size embarrassment — most slices produced 0-1 CANDs, suggesting the prompt was rejecting a lot.
- GER40: 0/7 succeeded — orchestrator failed at slice load (returncode 1, ~1.1s wall — likely an MT5 broker-symbol issue, GER40 isn't in the symbol map).

**HIGH confidence on XAGUSD verdict; HIGH on GER40 broker bug; MEDIUM on the rest given Tier 2 didn't run a manifest aggregator.**

### 1.6 AI-decay 70-75% AI-side claim vs prompt+confluence audits both REJECTED — RESOLVED

Two hypothesis tests this weekend tried to localize AI-decay into specific prompt features:

- `prompt_example_regime_audit/` (REPORT.md does NOT exist; only `regime_distribution.txt` + `classify_regimes.py`). The XAUUSD regime distribution shows Jan was 96% trending_bull, Apr 33% trending_bull / 37% chop / 16% reversal. The prompt's anchor-on-trending assumption was correct in Jan and broken in Apr. But this is **descriptive, not the AI-prompt-content-causes-decay smoking gun** the hypothesis sought.
- `confluence_strictness_audit/REPORT.md` does NOT exist on disk. The hypothesis was REJECTED-WITH-EVIDENCE per the brief.

**Resolution: real cause is upstream v1 detector + downstream filter cascade, not prompt content.** This is documented in CLAUDE.md item #4 (v2_shadow promotion gate) and item #11 (A2 v2-active backtest). The April collapse on XAUUSD (10% WR n=10, item #9) is **NOT replicated by the dumb baseline** (50% n=10 in `dumb_momentum_baseline/REPORT.md` line 81), proving the failure is downstream of mechanical price-action — i.e. AI-filter-side. The v2 detector promotion is the correct response because a SHORT-blind detector during a 33% trending_bull / 16% reversal April month forces the prompt into a one-sided cul-de-sac.

**HIGH confidence on the diagnosis. MEDIUM confidence that v2 promotion alone fixes the decay** — XAUUSD LONG WR at 33.3% (n=9) under v2 in A2 backtest is wide CI but does not clearly recover.

### 1.7 Cross-instrument correlation matrix staleness — RESOLVED, with a near-miss

`04_CORRELATION_INFRA_AUDIT.md` flagged HIGH severity: 9 cross-pair relationships flip the |r|≥0.4 threshold under fresh 2026-04-25 data vs the stale 2026-04-04 JSON the gate was about to ship with. **8 of those 9 involve a currently-live instrument** (GBPUSD↔US30 +0.444 fresh vs +0.283 stale, GBPUSD↔XAU +0.419 vs +0.284, GBPUSD↔USDJPY −0.547 vs −0.293, etc.). The cross-instrument-correlation gate (commit `24139a0`) and its post-merge fix (`6d70e00`) refresh the matrix. **HIGH confidence resolved.** Also caught a dormant bug: `US500` typo in `portfolio_risk.py:41` and `agent_config.yaml:269` should be `US500_cash` (lines 119-141 of audit). Not Monday-blocking; no live US500 trades.

### 1.8 Findings tagged HIGH that I downgraded after independent verification

- **Phase 1 extraction E4 SHORT-share discrepancy** (XAUUSD A1 6.05% vs F3 22.8%). This is HIGH confidence on the **diagnosis** (A1 ran v1-detector via `structure_detector_shadow_logger.py:105` routing rule, F3 used `--detector-version v2` CLI override; `EXTRACTION.md` lines 110-118 spelled out). It is HIGH confidence that A1 is therefore a v1-era PRE-baseline, not a v2 validator. But it is MEDIUM-LOW confidence that v2's SHORT edge is structural rather than coincident — only 2/2 SHORT WINs in F3, 2/2 in A2-v2-active. n=4 cumulative observed SHORT wins.
- **Phase 1 E1 touch-count realized-R reverses Track A walk-level prediction.** This is HIGH confidence on the **point estimates** (touch=1 +0.04R, touch=2 +0.30R, touch≥3 +0.07R) but the bootstrap CIs all cross zero. The "reversal" is real on the sample; whether it generalizes is unknown. The MEMORY entry `feedback_walk_level_evidence_not_predictive.md` correctly captures the lesson.
- **Theoretical ceiling REPORT.md does not exist** (`research/theoretical_ceiling/__pycache__/compute.cpython-313.pyc` is the only artifact). The brief cited "2.12% XAUUSD coverage; 13.6% fleet" but I cannot verify the ceiling claim against committed analysis. This is MEDIUM-LOW confidence and I am flagging it as STALE in §3.

### 1.9 Phantom files cited in the task brief

The brief enumerated 31 paths; 13 do not exist on disk:

- `research/vision_program_2026-04-25/` (entire directory) — none of the 6 reports (01-06 + MASTER_SPRINT_PLAN + WAVE1_SYNTHESIS) exist. Wave 1 deep-research outputs were either never committed to a vision_program directory or were committed under a different name.
- `research/theoretical_ceiling/REPORT.md`
- `research/cascade_prompt_diff.md`
- `data/gold_standard/SCHEMA.md`, `data/gold_standard/LABELING_METHODOLOGY.md` (only `__pycache__/` exists)
- `research/touch_count_audit/REPORT.md` (REVIEWER_PASS.md exists; no headline REPORT.md)
- `research/tick_daemon_cold_review/REVIEW.md` (entire directory missing)
- `research/prompt_example_regime_audit/REPORT.md`, `research/confluence_strictness_audit/REPORT.md` (the directories where they should exist do not even contain placeholders for REPORT.md)
- `research/staleness_audit/01_CLAUDE_MD_AUDIT.md`, `03_STATIC_REFS_AUDIT.md`, `REPORT.md` (only 02_CONFIG_AUDIT.md and 04_CORRELATION_INFRA_AUDIT.md exist)
- `research/MASTER_SPRINT_PLAN.md`, `research/WAVE1_SYNTHESIS.md`

**This is a documentation-debt finding, not a research-debt finding.** The work was almost certainly done — `git log` shows the corresponding commits — but the agent dispatchers either (a) returned to chat, (b) wrote files into uncommitted scratch space, or (c) committed only the implementation. The CLAUDE.md and LIVE_STATE.md are the canonical artifacts; they are accurate. But future readers of CLAUDE.md may follow these paths and find empty directories.

---

## Section 2 — Master action list (prioritized)

The full CSV is at `research/weekend_action_list.csv`. Headlines below.

### 2.1 MONDAY-BLOCKER (must complete before Monday rolling restart)

| # | Action | Confidence | Effort | Dependency |
|---|---|---|---|---|
| M1 | **Sunday evening: regenerate LIVE_STATE, run pytest 2475-collected, run mt5_preflight, run canary** | HIGH | 30 min | None |
| M2 | **Flip `market_state.detector_version: v2_shadow → v2`** in `config/agent_config.yaml:344`, commit, rolling restart | HIGH | 15 min | M1 green |
| M3 | **Smoke trade via `scripts/fn_smoke_trade.py`** under `--profile redacted_account` (or ftmo if challenge purchased AM) | HIGH | 10 min | M2 |
| M4 | **CEO purchases FTMO $100K paid challenge** Monday AM, updates `config/profiles/ftmo.yaml` login + password | HIGH | 30 min | external |
| M5 | **Rolling restart under `--profile ftmo`** | HIGH | 5 min | M4 |
| M6 | **Activate LONG-WR-watch SPRT gate** at first 20 XAUUSD trades; halt-and-investigate if XAUUSD LONG WR < 40% | HIGH | passive | M5 |
| M7 | **V3 SHORT-SL watch** first 5 XAUUSD SHORT live trades; investigate if ≥2/5 SL issues | HIGH | passive | M5 |
| M8 | **S1 monthly-decay monitor** Monday EOD via `scripts/monthly_decay_monitor.py` first run | HIGH | 5 min | M5 |

I removed two items the brief tagged MONDAY-BLOCKER: (a) "deploy V3-cascade prompt" — there is no committed cascade prompt to deploy, see §1.2; (b) "Test B n=100 replication" — this is post-Monday research, not Monday-blocking.

### 2.2 SHIP-TUESDAY (Tuesday after Monday data lands)

| # | Action | Confidence | Cost | Dependency |
|---|---|---|---|---|
| T1 | **Update `risk_per_trade_pct` to 0.75% FX / 0.375% XAU** per Risk-MC verdict (`recommendation.json` line 2) | MEDIUM | 5 min config + 30 min validation | First-day Monday data clean |
| T2 | **Begin per-day reconciliation:** Monday outcomes vs S1 monitor predictions; CLAUDE.md unresolved-item updates | HIGH | 30 min/day | M5+ done |
| T3 | **Fix `US500` → `US500_cash` typo** in `portfolio_risk.py:41` + `agent_config.yaml:269` per `04_CORRELATION_INFRA_AUDIT.md` §4.1 | HIGH | 10 min | None |

I removed "deploy V3-cascade" again — no source file exists.

### 2.3 WEEK-1-MONITOR (passive observation, no commits unless something fires)

| # | Action | Confidence | Effort | Dependency |
|---|---|---|---|---|
| W1 | Live monitor fleet daily — A3 v1.1 instrumentation fills `knowledge_base/trade_records/` | HIGH | 30 min/day | M5 |
| W2 | Track XAUUSD LONG WR vs SPRT halt window | HIGH | 10 min/day | M5 |
| W3 | Track per-instrument fill rate + L2-reject distribution under v2-active | HIGH | 10 min/day | M5 |
| W4 | First weekend: run `scripts/divergence_weekly_sample.py` against shadow_logs to update v2-vs-v1 misclassification rate | HIGH | 1 hour | M5 + 7 days data |
| W5 | Touch-count gate decisions log review (file `shadow_logs/touch_count_gate_decisions.jsonl`); flag PASS/REJECT skew | HIGH | 30 min/wk | M5 (logger lives at `fba3875`) |
| W6 | Dumb-baseline shadow log review (`shadow_logs/dumb_baseline_hypotheticals.jsonl`); compare AI-vs-mechanical realized R after 50-100 fills | MEDIUM | 1 hour | n=50 fills accrued |
| W7 | Heartbeat-flatten CEO live-enable decision (config flag flip at end of week 1 if no false-trigger events) | MEDIUM | 5 min | 7 days no false trigger |

### 2.4 WAVE-2-SPRINT (week 2-4)

| # | Action | Confidence | Cost | Dependency |
|---|---|---|---|---|
| S1 | **Tier-2 instrument promotion: XAGUSD live at 0.5% risk** (Tier 2 Exp R +0.767R, WR 71.7%) | HIGH | 1 day implementation | Week 1 data clean |
| S2 | **Tier-2 instrument promotion: NAS100 live at 0.5% risk** (Tier 2 Exp R +0.562R, WR 62.5%) | MEDIUM-HIGH | 1 day implementation | Week 1 data clean + GER40 broker bug verify NAS100 unaffected |
| S3 | **Defer UK100 + EURUSD** — Tier 2 results below threshold; revisit after V3 + v2 production data accrues | HIGH | 0 | — |
| S4 | **Diagnose GER40 0/7 backtest fail** (likely broker-symbol mismatch; check `tier2_ger40/s1.log` for traceback) | HIGH | 1-2 hours | None |
| S5 | **Sweep + reversal framework prototype** (Sprint 2 of vision roadmap; SMC pattern) — design doc + canary fixtures BEFORE prompt change | MEDIUM | 2-3 weeks | None |
| S6 | **Regime classifier promotion to live filter** after ≥14 days shadow + ≥80% correctness vs realized outcomes | LOW-MEDIUM | 1 week post-shadow | 14d shadow data |

### 2.5 WAVE-3-PLUS (month 2+)

| # | Action | Confidence | Cost | Dependency |
|---|---|---|---|---|
| P1 | **Tool-use grounding** sprint (per `tool_use_grounding/DESIGN.md` 5 tools, 3-tier rollout) | MEDIUM | 6-9 weeks | Live data anchoring |
| P2 | **Cross-asset state vector** (DXY, VIX-equivalent, options gamma proxies) | LOW-MEDIUM | 2-3 months | Tool-use Phase 1 done |
| P3 | **CME futures real-tick layer** (replace MT5 broker tick proxy) | LOW | 3+ months | Vision evaluation post-Phase-2a |
| P4 | **News calendar reactivation** (`news_filter.enabled: true`) | MEDIUM | 2 weeks | Event API selected |

### 2.6 DEFER-ARCHIVED (decisive shelving with evidence — do NOT revive without new data)

| # | Item | Why archived |
|---|---|---|
| D1 | V4 rule-based prompt | V4-DP1 −1R regression on divergent candles; 60-fixture canary FAIL (6 baseline flips, threshold ≤1); CB-2 over-aggressive on LONG. CLAUDE.md item #13(b). |
| D2 | LIRA label-first architecture | 12-slice A/B fleet Exp R +0.094R vs V3 +0.333R (LIRA-STAY pre-reg). USDJPY "over-permissive" was COVERAGE ARTIFACT; "stale-OB anchoring" 1.08:1 not structural. CLAUDE.md item #13(c)-(e). |
| D3 | No-CoT prompt | 39 sl_beyond_ob L2 rejections — definitively broken. CLAUDE.md item #13(h). |
| D4 | Confidence_tier enum cherry-pick | δ p=0.78 at n=48; no discrimination. CLAUDE.md item #13(g). |
| D5 | LOOSEN_TO_3 touch-count gate | A19 REJECT, see §1.1. |
| D6 | Track A anti-pattern AUC=0.65 hard gate | OOS AUC 0.55 on A1 filled CANDs; Spearman p=0.43. CLAUDE.md item #10. |
| D7 | V3-cascade prompt deploy | Source file not committed, only `.pyc` artifact. Treat as not-attempted-Monday until A14's actual numerical deltas are produced + reviewed. |

### 2.7 CLEANUP (low priority hygiene)

| # | Item | Why |
|---|---|---|
| C1 | Restore phantom files (vision_program/, theoretical_ceiling/REPORT.md, etc.) OR purge dead path references in CLAUDE.md | §1.9 inventory of 13 missing referenced files. |
| C2 | `structure_detector_shadow_logger.py:152` hardcoded divisor=4 mislabel | Logged `dead_zone` column (cosmetic) vs classifier-internal divisor=8. |
| C3 | `generate_live_state.py:285-286` mislabels `max_concurrent: null` as `_missing_` | Cosmetic; live_state table issue. |
| C4 | Orphan-key annotation pass on `agent_config.yaml` per `02_CONFIG_AUDIT.md` §9 | ~12 orphan/legacy keys; non-blocking. |
| C5 | `data/gold_standard/` SCHEMA.md + LABELING_METHODOLOGY.md | Brief expected; only `__pycache__/` exists. Either restore artifacts or remove from brief checklist. |
| C6 | A2 partial-close `_resolve_close_price` inline-block dedupe | Optional consolidation per CLAUDE.md item #7. |

---

## Section 3 — Verify nothing stale, nothing missed

### 3.1 Staleness audit closure verification

`02_CONFIG_AUDIT.md` flagged **0 HIGH-severity Monday-blockers** in the active production config. **2 MEDIUM-severity** remain (max_weekly_loss_pct + max_monthly_loss_pct unenforced — informational; LIVE_STATE.md `_missing_` for `max_concurrent: null` — cosmetic). **3 LOW-severity orphans.** Phase B doc-cleanup commit `45fc046` claims to address high+medium; I verified the relevant lines of CLAUDE.md changed, but the underlying config orphans were left alone (intentional — comment-only annotation post-Monday). **HIGH confidence the Monday-launch surface is clean.**

`04_CORRELATION_INFRA_AUDIT.md` HIGH severity item closed by commit `6d70e00` (matrix refresh). I verified the gate code header at `src/components/cross_instrument_correlation_gate.py:15-65` references the structural-screen results. The gate also documents the same-direction signed-correlation logic correctly. The MEDIUM `US500` typo remains open as cleanup item C5. **HIGH confidence.**

### 3.2 All git SHAs cited in CLAUDE.md exist

I verified 16 SHAs across the post-session-39 commit chain. All exist:
`fba3875`, `1b2d4e8`, `d031f55`, `daabff8`, `f1654f3`, `24139a0`, `6d70e00`, `d1b863c`, `573ce3c`, `222b69f`, `68f7a4b`, `64d05b8`, `1340f56`, `45fc046`, `beba16e`, `d614c54`. **HIGH confidence.**

### 3.3 Phantom files (per §1.9)

13 cited reports do not exist on disk. None are Monday-blocking — the synthesized findings live in CLAUDE.md, LIVE_STATE.md, and the present document. But future debug sessions following the brief's path map will hit dead ends. Action item C1.

### 3.4 Test count

CLAUDE.md has not been updated to a specific test count this weekend. `pytest --collect-only -q` returns 2475 collected (plus 1 known-uncollectable test class with `__init__`). The brief said 2468; the discrepancy of 7 is within the expected drift from new tests landing during the weekend (regime classifier, cross-instrument gate, dumb-baseline logger, ADR-005 logger added tests). **HIGH confidence the suite is current.** I did NOT run the full suite — that's M1 in the action list.

### 3.5 Detector version flip

**`config/agent_config.yaml:344` still reads `detector_version: v2_shadow`.** The flip to `v2` is M2 in §2.1 — has NOT been committed yet. This is intentional per the pre-deploy checklist; the flip is the Sunday-evening step. **No staleness; CLAUDE.md and LIVE_STATE.md correctly identify v2_shadow as the current production-driver.** The Monday deploy plan flips this. CONFIDENCE that the flip is the right call: see §4.

### 3.6 GBPUSD trading_enabled

**`config/agent_config.yaml:434` reads `trading_enabled: false` for GBPUSD.** Verified. CLAUDE.md correctly identifies GBPUSD as observer-only. **HIGH confidence.**

---

## Section 4 — Risk assessment for Monday deploy

### 4.1 Risk-MC verdict — STAY at 1% FX / 0.5% XAU for Monday, drop to 0.75% / 0.375% Tuesday

`research/risk_level_mc/recommendation.json` recommends **0.75% (constraint-pass-max-pass60d method)**. The constraint is `p_bust_dd_60d_max: 0.05`. At 1.0% the simulation gives `w_p_bust_dd_60d: 0.0554` — fails the constraint by 0.04pp. At 0.75%: `w_p_bust_dd_60d: 0.0199` — comfortably passes.

**My call:** STAY at 1% FX / 0.5% XAU for Monday (the existing FN profile values match what was planned), then **drop to 0.75% Tuesday** after Day-1 outcomes confirm the deployment is healthy. Rationale:
- The MC's 5.54% bust probability at 1% is **only marginally above** the 5% constraint. A 30-trade clean Monday would empirically exceed the simulator (which models the historical WR distribution); we get to update our priors after Monday.
- Dropping risk on Sunday-night-of-deploy-Monday is the single most-likely-to-cause-a-bug change. The CEO's intent is "ship Monday," not "ship Tuesday with smaller risk."
- Tuesday cut is **3 lines of YAML** (FX 1.0 → 0.75 base, XAUUSD 0.5 → 0.375 override, drawdown_reduced 0.25 → 0.1875).

**Alternative call I considered and rejected:** ship Monday at 0.75% / 0.375%. Doing so changes everything from the demo data — sizing arithmetic, broker behavior at smaller lot sizes, the orchestrator's risk-resolution path. Better to ship at known sizing then trim. **MEDIUM-HIGH confidence on STAY-then-trim.** LOW confidence on the bust-probability constraint at 1.0% — Risk-MC uses fitted WR weights `{0.62: 0.3, 0.55: 0.3, 0.5: 0.25, 0.45: 0.15}` which over-weights the 62% canonical (not the 24% H2 reality).

### 4.2 Cross-instrument correlation gate Monday-safe?

Code verified at `src/components/cross_instrument_correlation_gate.py:15-65`. Matrix refreshed via commit `6d70e00`. The gate is ADDITIVE — it can only HALVE or REJECT, never increase exposure. The threshold `0.4` is conservative (random pairs hover 0.2-0.3); `min_positions=2` triggers HALVE; +1 → REJECT. **HIGH confidence Monday-safe.**

I did **not verify** that `tests/test_cross_instrument_correlation_gate.py` exists and passes against the new matrix. M1 (Sunday pytest run) covers this.

### 4.3 Multi-framework activation Monday-safe?

`config/agent_config.yaml` has `model_a.enabled_frameworks: [ob_retest, fvg_fill, breaker_re_entry]` (LIVE_STATE.md confirmed). The pre-AI gate replay (`research/pre_ai_gate_replay_2026-04-25/summary.json`) shows the multi-framework config rejects fewer candles than the disabled config (because the gate is permissive — pre-AI skip only when EVERY enabled framework has zero POIs). The `skip_baseline` (ob_retest only) vs `skip_multi` numbers per instrument:
- XAUUSD: skip_baseline 510 vs skip_multi 168 (multi is 3× MORE permissive with AI calls)
- USDJPY: skip_baseline 872 vs skip_multi 177 (4.9× more permissive)
- GBPUSD: skip_baseline 1070 vs skip_multi 133 (8× more permissive)

This is the additional API spend cost of the multi-framework — **3-8× more AI calls per instrument**, multiplied by ~$0.005/call ≈ $1-3/instrument/month additional spend at current cadence.

**Risk:** the new fvg_fill + breaker_re_entry frameworks have NOT yet seen 30+ live trades. CAND volume could spike unexpectedly. **MEDIUM-HIGH confidence safe** — backed by canary regression `573ce3c` (32/32 baseline + 42/43 borderline PASS) and post-staging baseline regen `d1b863c`.

### 4.4 GBPUSD trading_enabled false — confirmed safety gate active

Verified at `config/agent_config.yaml:434`. Gate 0.5 in `permissions.py` rejects every order_send. **HIGH confidence.**

### 4.5 Anything else that could embarrass us Monday?

1. **Tick-capture daemon** (commit `f1654f3`) — runs as separate process per orchestrator. If MT5 demo goes flaky and the daemon spams tick-write errors, it could fill `data/ticks/` and pressure disk. **MEDIUM risk.** Mitigation: watchdog supervises; verify before EOD that disk is healthy.
2. **Regime classifier** (`beba16e`) — observation-only, but if its `shadow_logs/regime_classifications.jsonl` write path is wrong it could fill or fail silently. **LOW risk.** Mitigation: M1 pytest covers; W4 first-week review confirms log accumulation.
3. **Dumb-baseline shadow logger** (commit `1b2d4e8`) — fires HYPOTHETICAL trades alongside real. There is no live `mt5.order_send` from the dumb baseline (verified by reading orchestrator wiring). But the log entries could create disk volume. **LOW risk.**
4. **Heartbeat-flatten kill switch** (`flatten_enabled: false`) — disabled. If false-triggers occur during week 1, the CEO can re-disable in a config flip. **LOW risk.**
5. **Anthropic API monthly cap.** Memory: $50-60 balance is the hard cap; auto-reload disabled. Multi-framework increases API calls 3-8× — **HIGH-MEDIUM risk** of cap hit mid-month. Mitigation: monitor Anthropic console daily; if approaching cap, disable fvg_fill or breaker_re_entry temporarily. The canary cache + monthly_cap_usd nominal value (`50.0`) are documentation-only; Anthropic's $50-60 balance enforces.
6. **GER40 broker-symbol bug** — Tier 2 backtest 0/7 success, returncode 1. If GER40 is ever live-enabled on Tier 2 promotion, this same bug fires. **NOT a Monday issue** — GER40 is not a live instrument. Action S4 covers.

---

## Section 5 — Honest confidence assessment

For each major change shipping Monday:

| Change | Confidence | Reasoning |
|---|---|---|
| **v2 detector promotion** (`v2_shadow → v2`) | **80%** (HIGH-MEDIUM) | Backed by F3 12-slice GO + A2 v2-active 3/4 pre-reg PASS. The 1 failing pre-reg (Fleet LONG WR 50% in halt window [45%, 55%]) is the single concerning data point — XAUUSD LONG WR 33.3% (n=9) under v2 vs F3's 45.5% (n=11). Wide CIs overlap; cannot statistically reject baseline. The LONG-WR-watch SPRT at trade 20 is the right safety net. |
| **Multi-framework activation** (fvg_fill + breaker_re_entry) | **75%** (MEDIUM-HIGH) | Canary regression PASSED. Has not seen 30+ live fills. CAND volume could spike (3-8× more AI calls per pre-AI gate replay). The frameworks are ADDITIVE POI sources, not new gates — risk is API cap, not trade quality. |
| **Touch-count gate at 2 + ADR-005 logger** | **90%** (HIGH) | A19 independent verification + Bonferroni-failing pairwise tests + H1/H2 regime reversal (touch=2 +14R H1 → −6.5R H2). Logger is observability only. The decision to KEEP at 2 is the correctly conservative call. |
| **Cross-instrument correlation gate** | **85%** (HIGH) | Additive only (HALVE or REJECT). Matrix refreshed (`6d70e00`). Threshold conservative. The `tests/test_cross_instrument_correlation_gate.py` claim is not verified — M1 pytest catches. |
| **Regime classifier (shadow only)** | **95%** (HIGH) | Pure observation — no trading logic. V1 = H4-swing-based, fail-safe to `unclear`. Cannot embarrass us live; only contains itself if the JSONL path is broken. |
| **Tick capture daemon** | **70%** (MEDIUM) | Side-process per orchestrator, watchdog-supervised. Cold-review by A13. The 12 microstructure features merge additively into raw_data with `tick_features=None` fail-open. Risk is operational (disk, process supervision) more than logical. Higher uncertainty because new process model. |

**Weighted overall ready-for-Monday confidence: 80%.** Reasoning:
- The largest unknown is XAUUSD LONG WR under v2 (item #11). A 33.3% n=9 pre-Monday signal is below the 40% halt threshold but the n is too small to action.
- The next largest unknown is the multi-framework CAND-rate spike. Canary numbers say it's clean; live traffic over a week of FTMO-paid context could differ.
- Everything else has either been independently verified or is observation-only.

### 5.1 WORST credible scenario for first 20 trades

Three live failure modes ranked by credibility:

1. **XAUUSD LONG WR < 30% in first 10 trades** (15% probability). The April decay is regime-dependent; v2 promotion may not fix it. SPRT halts at 30%. Investigation cycle: 1-2 days, possibly STAY on v2_shadow + revisit LIRA XAUUSD-specific hybrid (CLAUDE.md item #13(f)).
2. **Multi-framework CAND-rate spike** (10% probability). New frameworks hit edge cases the canary missed. CAND rate per instrument hits 25%+ of M15 candles (vs 10.3% baseline). Mitigation: temporary `enabled_frameworks: [ob_retest]` rollback (1-line config), then reintroduce once canary expanded.
3. **Tick daemon crashes / disk fills** (5% probability). Watchdog respawns; if respawn loop fails, daemon disabled, tick_features=None. **Trading continues** — the daemon's failure does not block trading by design.

The worst credible compound scenario: all three above + a Monday FOMC-equivalent news spike that wasn't on the radar → 4-5 emergency stops triggered → CEO halts entirely + we revert to demo while we reconcile. Probability: ~2%. We have all of week 1 to either confirm health or revert to demo.

---

## Section 6 — What's next AFTER Monday

The post-Monday roadmap aligns with CEO's "powerful trading machine" vision per session-40 KICKOFF and memory `feedback_research_goal_high_quality_frequency.md`.

### 6.1 Tuesday (Day 2)

- Apply Risk-MC trim: 1.0% → 0.75% FX, 0.5% → 0.375% XAU (3-line YAML diff). Re-canary. Rolling restart.
- Run S1 monthly-decay monitor with Day-1 data captured.
- Fix US500 → US500_cash typo (cleanup C5).

### 6.2 Week 1-2: Live data collection + decay surveillance

- Daily fleet review (W1-W4 from §2.3).
- A3 v1.1 instrumentation populates `knowledge_base/trade_records/`.
- First weekend: divergence weekly sampler (W4).

### 6.3 Week 2-3: Tier-2 instrument promotion

- Promote XAGUSD to live at 0.5% risk (S1) — Tier 2 +0.767R Exp R, 71.7% WR is the strongest signal in the weekend.
- Promote NAS100 to live at 0.5% risk (S2) — Tier 2 +0.562R Exp R, 62.5% WR.
- DEFER UK100, EURUSD (S3). Investigate GER40 broker bug (S4).

### 6.4 Week 2-3: Sweep + reversal framework prototype (Sprint 2)

- Per Vision Program: sweep + reversal SMC pattern as second framework (S5).
- Design doc + canary fixtures BEFORE prompt change.
- Anti-gaming pattern blocks NEEDED in framework definition (V4 lessons learned).

### 6.5 Week 3-4: Regime classifier promotion to live filter

- Per CEO promotion gate: ≥14 days shadow + ≥80% v1-correct vs realized outcomes.
- If green: classifier output enters AI prompt as a context block.
- If red: extend shadow another 14 days.

### 6.6 Week 4-6: Tool-use grounding (Sprint 3)

- Per `tool_use_grounding/DESIGN.md` 5-tool catalog.
- 3 tier-1 tools (`query_recent_trade_outcomes`, `lookup_session_volatility`, `check_correlation_exposure`) at ~$10-15/mo + 1-2 weeks/tool.
- F3-replay A/B (12 slices, ~$80) for go/no-go.

### 6.7 Month 2-3: Cross-asset state vector

- DXY, VIX-equivalent, options gamma proxies into MSO.
- Pre-condition: tool-use Phase 1 done.

### 6.8 Month 3+: News calendar reactivation

- `news_filter.enabled: true` with real news feed.
- Pre-news 30-min lockout for high-impact.

---

## Section 7 — Open questions still UNANSWERED

The weekend resolved a lot but not everything. The genuine unknowns going into Monday:

1. **Does v2 fix the XAUUSD H2-2026 decay?** A2 v2-active backtest gives XAUUSD LONG WR 33.3% (n=9), which is BELOW the 40% halt threshold. We don't know if it generalizes or was 9-trade noise. Live data answers in week 1.

2. **Does multi-framework activation maintain expected R/month?** No sample of live fvg_fill or breaker_re_entry trades exists. Canary regression PASSED but canary tests prompt logic, not realized R. First-week answer.

3. **Does the cross-instrument correlation gate fire as intended in production?** No live triggers tested. The matrix is valid; the wiring is checked. But the gate has not actually halved-or-rejected a real CAND yet. First-month answer.

4. **What is the post-promotion v1-vs-v2 misclassification rate?** ADR-004 promotion gate requires ≥80% v2-correct. Divergence sampler (W4) updates this. We haven't seen 100 manually-classified divergences yet.

5. **Is the dumb-momentum baseline really competitive with AI+OB?** `dumb_momentum_baseline/REPORT.md` says +0.364R/trade Exp on n=55 same-window vs GTOS F3 +0.347R (n=13). The honest verdict was "AI+OB-MAYBE-UNNECESSARY." Live shadow log will produce 50-100 paired observations within ~3 months.

6. **Does the regime classifier's `unclear` fail-safe rate concern us?** If V1 labels 60% of M15 candles as `unclear`, the classifier provides little discrimination. Not yet measured — first 14 days of shadow data answers.

7. **Does the LIRA point edge on XAUUSD (+0.114R/trade, n=14) replicate at scale?** Bootstrap CI [-0.877, +1.104] crosses zero. Resolved only by ≥30 live XAUUSD fills under V3 + post-Monday data.

8. **Can we restore the phantom files?** vision_program_2026-04-25, theoretical_ceiling/REPORT.md, etc. These were referenced in the brief. Either the agent dispatchers returned-to-chat without committing, or those reports live somewhere else. C1 in cleanup.

9. **Is the GER40 backtest failure a broker-symbol mapping issue specific to our MT5 demo, or a data-export gap?** Tier 2 backtest had 0/7 success. NAS100 succeeded under the same orchestrator. Likely symbol-name issue (`GER40` vs `GER40.cash` etc.). S4 covers.

10. **Cap-relaxation analysis** (`research/cap_relaxation_analysis/`) produced no committed report — only `__pycache__/`. The analysis ran; did the conclusion get captured anywhere? CLAUDE.md does not reference cap-relaxation findings. **Possibly an evaporated agent run.**

---

## Appendix A — Methodology lessons captured this weekend

- ≤3-slice mini-backtests CANNOT validate prompt-architecture changes. Need ≥10 slices / ≥30 fills before promote-or-shelve.
- Always coverage-match backtest pairs. Budget caps create asymmetric truncation that fakes "permissiveness" signals.
- analyze.py MaxDD must sort chronologically, never slice-iteration order (red-team `13c1b20`).
- Council + red-team pattern catches shared hallucinations. α+β both overstated "stale-OB anchoring"; R independently caught both.
- Walk-level pre-trade probability ≠ realized R per stratum. Memory `feedback_walk_level_evidence_not_predictive.md`.
- Pooled-stratum analyses over multi-regime data hide regime-dependent reversals. ALWAYS split by regime.
- Headline R-uplift numbers must specify their threshold semantics. "REMOVE delta" ≠ "LOOSEN delta." (A11 example.)
- Phantom files cited in briefs are a process bug worth catching. Future synthesis tasks should verify referenced files exist before citing.

---

## Appendix B — Files of record (canonical source of truth)

| Doc | Authority |
|---|---|
| `CLAUDE.md` | High-confidence; mostly current. Phantom file paths in §1.9 are the staleness vector. |
| `.context/LIVE_STATE.md` | Auto-generated; trust over any handoff. Regenerate before deploys. |
| `.context/02_session_handoffs/39_apr25_session_40_KICKOFF_*.md` | Latest handoff; deployment plan + roadmap. |
| `.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md` | Step-by-step Monday play. |
| `.context/06_decisions/` | ADRs (001-005). ADR-004 (v2 detector), ADR-005 (touch-count). |
| `research/instrument_expansion_2026-04-25/{01_STRUCTURAL_SCREEN.md, 02_DECAY_ANALYSIS.md, 03_MICROSTRUCTURE.md, 04_GBPUSD_OBSERVER_REVIEW.md}` | Tier 1 reports. |
| `research/touch_count_audit/REVIEWER_PASS.md` | A19 verdict — REJECT. |
| `research/dumb_momentum_baseline/REPORT.md` | A6 baseline — AI+OB-MAYBE-UNNECESSARY. |
| `research/phase1_full_extraction/EXTRACTION.md` | E1-E12 comprehensive findings. |
| `research/staleness_audit/{02_CONFIG_AUDIT.md, 04_CORRELATION_INFRA_AUDIT.md}` | The 2 audits that produced reports. |
| `research/risk_level_mc/recommendation.json` | 0.75% FX / 0.375% XAU recommended. |
| `research/tool_use_grounding/DESIGN.md` | Sprint-3 design. |
| `research/pre_ai_gate_replay_2026-04-25/summary.json` | Multi-framework permissiveness data. |
| `research/instrument_expansion_2026-04-25/tier2_orchestrator_summary.json` + `tier2_*/s*/all_results.json` | Tier 2 backtest results (manually aggregated for this synthesis). |

---

*Compiled by Opus 4.7 max-effort, 2026-04-25. Brutally honest mandate respected; phantom files surfaced; contradictions resolved with citations; recommendation: ship Monday at 80% confidence, watch SPRT, trim risk Tuesday.*
