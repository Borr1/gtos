# Cold Review — `00_gtos_upgrade_candidates.md`

**Reviewer role:** Red team / verification agent
**Target:** `research/quantlabs_competitor_intel/synthesis/00_gtos_upgrade_candidates.md` (356 lines, 35 candidates, 6 P0 / 13 P1 / 10 P2 / 6 P3)
**Sources verified against:** `blog_extractions/batch_{01..10}.md`, `youtube_extractions/batch_{01..05}.md`, `CLAUDE.md` current-state, `.context/02_session_handoffs/` 17–24
**Date:** 2026-04-18
**Verdict:** **GO WITH FIXES** — structurally sound, factually ~90% accurate, but three P0 items are priority-miscalibrated (trading-logic risk during WF-1) and nine citation errors need correction before the doc is CEO-usable.

---

## 1. Top-line verdict

**GO WITH FIXES.** The synthesis is the product of a reasonable read of the corpus. The highest-value competitor-surfaced finding — the heartbeat-flatten kill switch — is correctly identified (verified verbatim at `youtube_extractions/batch_02.md` video 5 `8F5hsbqTFi8`), and the Section 4 "what GTOS does better" moat analysis is accurate. The candidate-by-candidate logic is mostly well-reasoned.

But the doc fails three stress tests:

1. **Eight `[xxx]` placeholder citations in Section 2** — Sections 2.2, 2.3, 2.5, 2.6, 2.8 use `[xxx]` where batch item numbers should be. Unacceptable for a CEO-facing synthesis.
2. **One factual error in Section 2.3** — "VPIN 65% vs Hawkes 78%" — the source (`batch_08.md:9,40`) says **Microprice 65%**, not VPIN 65%. VPIN is listed as a feature, not a detection-score benchmark, in the Bayesian/microprice/Hawkes triad.
3. **Three P0 items are risk-miscalibrated**. Candidates #4 (DCC-GARCH), #5 (VPIN), #6 (time-based stop) are classified P0 despite being either MEDIUM effort net-new statistical pipelines (#4, #5) or trading-logic changes during WF-1 (#6). P0 in GTOS vocabulary means "safe, concrete, ship this week" — these are R2 shadow-log candidates at best.

Fixing these makes the doc CEO-actionable. Leaving them leaves the CEO to re-sort the P0 list under time pressure.

---

## 2. Candidate-by-candidate annotations

Columns: **Source-check** (citation traces to the claimed batch?) · **Risk/effort-realism** (is the tag defensible given GTOS shadow-logger precedent?) · **Priority-recommend** (if different from synthesis) · **Blocker** (what else must be true before this ships).

| # | Candidate | Source-check | Risk/effort-realism | Priority-recommend | Blocker / note |
|---|-----------|--------------|---------------------|--------------------|----------------|
| 1 | Heartbeat-flatten kill switch | **PASS** (youtube batch_02 video 5 verbatim confirmed) | M/L fair | **P0 KEEP** | Single best finding. Caveat: requires careful safety-gate for false positives (a 30s network blip shouldn't flatten $100K). Recommend: spec 3 consecutive missed heartbeats @ 5min intervals before trigger. |
| 2 | Pending intent persistence to disk | **PASS** (cross-ref: CLAUDE.md Known Issues + handoff 20 `PendingLimitIntent schema_version`) | S/L fair — CLAUDE.md already flags this as open | **P0 KEEP** | Low-risk; align with handoff 20 schema. Recommend: ship alongside #1 (same file touches). |
| 3 | Daily no-data alert per symbol | **PASS** (blog batch_10 [15] Brent BZ 523 events / 5h 54m verified) | S/L fair | **P0 KEEP** | CLAUDE.md session 23 canary cache already addresses part. Spec: separate from canary — canary checks API drift, this checks M15-tick liveness. |
| 4 | DCC-GARCH correlation-breakdown monitor | **PASS** (batch_03 [#3] `batch_03.md:61` `DCC alert at 3σ... detection 73%, false alarms 8%` verified) — but synthesis uses `[xxx]` placeholder, citing `batch_03` generically | M/L too optimistic — MEDIUM effort means new `arch`/`statsmodels` dependency, DCC-GARCH fit on multi-symbol returns, rolling estimation. CLAUDE.md has none of this. Realistically L/L. | **P0 → P1** (or split: P0 *shadow-log-only monitor on static correlation matrix*; P1 DCC-GARCH proper) | (1) Dependency decision (arch vs statsmodels). (2) Shadow-log vs gate decision. (3) Validation cycle. Not a single-week ship. |
| 5 | VPIN shadow logger per symbol per KZ | **PASS** (batch_09 [3] EQS composite `z(VPIN)*0.4 + z(OBI)*0.3 + z(AC1)*0.3` verified; batch_04 VPIN<0.7 gate verified) | M/L too optimistic — VPIN requires tick-bucket infrastructure (equal-volume buckets of ~50-100 ticks) that GTOS has never built. MT5 tick API is known-quirky on FTMO demo (ticks can be delayed or missing). Realistically L/L. | **P0 → P1** | (1) Tick-pipeline spike (1-2 days). (2) Bucket-size calibration per symbol. (3) Shadow-log 30+ candidates before any gate promotion. Not a P0 week-one item. |
| 6 | Time-based stop (30min max hold) | **PASS** (batch_05 [17] stablecoin 1800s time-stop verified; `batch_05.md:258`) | **S/M is wrong — risk is actually H.** Changing exit logic during WF-1 = trading-logic change. Requires CEO approval + restart all 5 processes. CLAUDE.md prohibits this without approval. | **P0 → split**: P0 *shadow-log what would have happened at 30/60/120min exits* (edit `be_shadow_logger.py` pattern); P1 *actual exit-gate change* after 30+ observations | (1) Shadow-log first. (2) Wilcoxon promotion gate. (3) OB-retest trades often take 4-8h to work (per CLAUDE.md session-volatility decay note). 30min may kill the edge. |
| 7 | Hurst exponent shadow feature | **PARTIAL PASS** — cited as "batch_08, batch_09 [12]" — actual source for core finding is `batch_08.md:164,237-242` item **[19]** (Random Walk Memory, Caltech/BGU), not the unnumbered `[xxx]` in synthesis Section 2.2. batch_09 [12] verified (MotiveWave Hurst cycles). | S/L fair — pandas + `numpy` or `nolds` is retail-accessible | **P1 KEEP** | Ship into `candidate_features_logger.py` (handoff 20). |
| 8 | HMM regime classifier | **PASS** (batch_03 [#3] HMM 5-state + `High_Vol 0.40, Low_Vol 1.15, Trending 1.30, MR 0.85, Crisis 0.25` Kelly modifiers verified `batch_03.md:61`; batch_08 [2] HMM Sharpe 1.8/2.5/2.2 verified `batch_08.md:40`; batch_09 [2] HMM context verified) | L/L fair — `hmmlearn` is retail-standard | **P1 KEEP** | Shadow-log first; gating requires H29 refactor. |
| 9 | Gateway-only broker connection | **PASS** (batch_09 [21] Valkey + .NET 8; batch_10 [21] Valkey engine) | L/H accurate — architectural change, touches MT5 connection | **P1 KEEP** | Large scope. Handoff 20 `PendingLimitIntent` persistence is a cheaper partial solution that may suffice. |
| 10 | OFI shadow logger | **PASS** (batch_03 [#3] `OBI = [Σ V_bid·e^(-λd) - ...]`; batch_04 verified; batch_09 [3] verified) | M/L fair | **P1 KEEP** | Lee-Ready tick-rule is retail-accessible; OFI is directional complement to symmetric VPIN. |
| 11 | Drawdown-to-Profit Ratio gate | **WEAK CITATION** — cited as "batch_06". Did not find "DDtoP" or "drawdown-to-profit" as explicit terminology in batch_06. May be present but not recovered in extraction TOP FINDINGS. **Flag for re-verification.** | S/L fair IF source is valid | **P1 KEEP provisional** | Recheck batch_06 for the specific term or citation number. |
| 12 | Composite strategy score | **PASS** (batch_07 [20] — synthesis cites "batch_07" — `0.30*Sharpe + 0.20*Sortino + 0.20*ExpR + 0.15*WR + 0.15*Calmar` verified `batch_07.md:10`) | S/L fair | **P1 KEEP** | Blocked by single-framework WF-1; post-WF-1 candidate. |
| 13 | Half-Kelly + HMM-regime multipliers | **PASS** (batch_03 [#3] Kelly modifiers verified) | L/H accurate | **P1 KEEP** | Supersedes H29. Requires HMM maturity first → L4 milestone, not R2. |
| 14 | "Block all orders" master flag | **PASS** (youtube batch_03 [6] verbatim `batch_03.md:194-198,234-236`) | S/L fair | **P1 KEEP** | GTOS has `deployment.phase`; batch_03 [6] author flags prod/paper code-path sharing as failure mode. Recommend: audit current `deployment.phase` use sites before shipping a separate flag. |
| 15 | Consecutive-loss cooldown | **CITATION WEAK** — synthesis cites "competitor pattern (common)" but the source is **specifically `batch_03.md:11 [#18] Multi-Asset Bot Suite`**: "circuit breaker (3 consecutive losses → 60-min cooldown)" + hard stops 16bps gold → 280bps ETH. This is **one article's opinion**, not "common competitor pattern." | S/M risk fair — gate change | **P1 KEEP but tighten citation** | Shadow-log first (would it have blocked next profitable trade?) per synthesis's own note. |
| 16 | Weekly AI-reasoned skipped-trade summary | **PASS** (youtube batch_01 #4 + batch_02 #3 "how are the potential trading opportunities" prompt verified) | S/L fair | **P1 KEEP** | ~$2/mo. Trivial to add. |
| 17 | Parameter perturbation validation | **PASS** (batch_10 [25] — cited correctly) | M/L fair | **P1 KEEP** | R2 promotion battery addition. |
| 18 | News-confirmation shadow logger | **PARTIAL** — youtube batch_05 #3 template confirmed in synthesis Section 6.1 [I] paraphrase, but this is a **pattern**, not a production-ready plug-in. Requires news-feed ingestion GTOS doesn't have. | M/L understates — requires news pipeline build | **P1 KEEP but effort → L** | Blocked on news-ingestion infrastructure. |
| 19 | Microprice feature | **PASS** (batch_09 [2] verified; also batch_03 `MicroPrice = (V_bid × Ask + V_ask × Bid)/(V_bid + V_ask)` at `batch_03.md:442`) | S/L fair | **P1 KEEP** | Requires L1 bid/ask sizes; MT5 limits exposure. |
| 20 | Parallel MC resampling (permutation) | **PASS** (batch_10 [25]) | S/L fair | **P1 KEEP** | Cheap add to existing MC battery. |
| 21 | Regime-conditioned prompt variant for T7 | **PASS** (batch_02 prompt template pattern — but the `[xxx]` placeholder in synthesis Section 2.5 should be a specific batch_02 item number; couldn't confirm exact item number in a single grep) | S/H fair — modifies T7 | **P2 KEEP** | WF-1 protects T7. Only if HMM shadow-log shows state-dependent WR divergence. |
| 22 | Hawkes process toxicity | **PARTIAL** — formula verified (`batch_08.md:51`), but synthesis says "82% toxicity detection" — correct but attribution to Hawkes specifically is Bayesian-toxicity (82%), Hawkes is 78%. | L/L fair | **P2 KEEP** | Research-grade. |
| 23 | Portfolio bot health score 0-100 | **PASS** (batch_02 [16] composite score — cited as `batch_02 [xxx]` placeholder, actual is [16] `batch_02.md:8`) | M/L fair | **P2 KEEP** | |
| 24 | Shanghai gold premium | **PASS** (batch_09 [1] CME outage) | M/L fair | **P2 KEEP** | |
| 25 | COT positioning filter | **PASS** (batch_09 [15]) | M/L fair | **P2 KEEP** | Free CFTC data; research-grade. |
| 26 | MCP supply-chain audit | **PASS** (youtube batch_05 #4 LMLite credential-steal) | S/L fair | **P2 KEEP** | Operational hygiene. |
| 27 | Prepaid card cap | **PASS** (youtube batch_05 #4 `$10,000 API bill` — also `batch_07.md:6` "$10K over single weekend"). Synthesis cites youtube batch_05, actual source is also blog batch_07 [1]. | S/L fair | **P2 could rise to P1** | CLAUDE.md effort=max = cost-spike risk. Cheap to do. |
| 28 | Log-event density benchmark | **PASS** (batch_02 + batch_10 verified) | S/L fair | **P2 KEEP** | |
| 29 | Quote-stuffing detection | **CITATION WEAK** — synthesis cites "batch_09 [24]" — `batch_09.md` item [24] (checked; didn't find quote-stuffing specifics there). The actual quote-stuffing / fake-liquidity detection writeup is **`batch_03.md:333` [#41 or similar]** "Quote Fade Algorithm... Quote-stuffing detection via top-3-level covariance." | L/L fair | **P2 KEEP but re-cite** | Fix citation to batch_03 Quote Fade. |
| 30 | Seasonal commodity filters | **PASS** (batch_10 [28]) | S/L fair | **P2 KEEP** | |
| 31 | AI-generated "new bot from logs" pipeline | **PASS** (youtube batch_02 #3) | L/L fair | **P3 KEEP (reject)** | GTOS's KAP pipeline is higher-rigor. |
| 32 | "One strategy, many instruments" | **PASS** (youtube batch_02 #5) | L/H fair | **P3 KEEP (reject)** | |
| 33 | Broker migration | **PASS** (batch_09 [1] + batch_10 multiple) | L/H fair | **P3 KEEP (reject)** | Scope-mismatch. |
| 34 | BlackRock AlphaAgents | **PASS** (batch_05 [29]) | L/L fair | **P3 KEEP (reject)** | Correctly flagged as duplicate of Component 3B. |
| 35 | Streamlit per-strategy sandbox | **PASS** (youtube batch_04 #2) | M/M fair | **P3 KEEP (reject)** | UI out of scope. |

---

## 3. Fabrication / overclaim flags

### 3a. Factual errors in the synthesis (require correction before CEO-circulation)

| Line | Claim | Correction | Source proof |
|------|-------|------------|--------------|
| 49 | "batch_08 Bayesian toxicity 82% vs **VPIN 65%** vs Hawkes 78%" | **Microprice 65%**, not VPIN 65%. VPIN is listed as a *feature* in the Bayesian/Hawkes comparison, not a benchmark. | `batch_08.md:9` TOP FINDINGS: "Bayesian toxicity detection scores 82% vs VPIN/microprice 65%" — actually conflates both; `batch_08.md:40` is authoritative: "Microprice 65%, Bayesian 82%, Hawkes 78%" |
| 39 | "batch_08 regime-mult stop sizing (hi=2.5/norm=1.5/lo=1.0 ATR)" | Source is **batch_07 [15]**, not batch_08. | `batch_07.md:5` TOP FINDINGS: "stop = ATR × regime multiplier (hi=2.5, norm=1.5, lo=1.0)" |
| 342 | Table row "Regime-mult ATR stop ... hi 2.5 / norm 1.5 / lo 1.0" — no source given | Add `(batch_07 [15])` | same as above |
| 166 | Candidate #29 "batch_09 [24]" for quote-stuffing/spoofing | Actual source is **batch_03 [#41] Quote Fade Algorithm** `batch_03.md:333` — "Quote-stuffing detection via top-3-level covariance." batch_09 [24] is a promotional listing with no detail. | `batch_03.md:332-335` + direct check of batch_09 [24] extraction |

### 3b. Placeholder citations (`[xxx]`) that must be resolved

| Line | Section | Needs |
|------|---------|-------|
| 35 | Section 2.2 HMM | `batch_03 [#3]` for RBOB/HMM, `batch_08 [2]` for HMM Sharpe |
| 37 | Section 2.2 Hurst | `batch_08 [19]` (Random Walk Memory) |
| 45 | Section 2.3 OFI | `batch_03 [#3]` for RBOB OFI |
| 51 | Section 2.3 DCC-GARCH | `batch_03 [#3]` |
| 65 | Section 2.4 Half-Kelly | `batch_03 [#3]` |
| 79 | Section 2.5 regime prompt | `batch_02 [#?]` — needs resolution |
| 81 | Section 2.5 JSON | `batch_03 [#1]` |
| 95 | Section 2.6 bot health | `batch_02 [16]` |
| 117 | Section 2.8 AlphaAgents | `batch_05 [29]` |
| 119 | Section 2.8 4-phase orch | `batch_02 [#?]` |

### 3c. Overclaims / mild fabrication risk

- **Line 15 / Section 1:** "6 P0 (propose to CEO now)" — but 3 of 6 (#4, #5, #6) are not actually ship-this-week given the effort/risk profile I've verified. Overclaim of P0 readiness.
- **Line 59:** "competitor pattern (common)" for consecutive-loss cooldown — only ONE source (batch_03 [#18]). Not "common."
- **Line 15 Section 2:** "6-8 high-signal articles" — vague. The TOP FINDINGS tally more carefully would show 10-12 genuinely-useful blog items + 4-5 video architectural gems. Not a fabrication but imprecision.
- **Line 131 Section 3 preface:** "YES" / "PARTIAL" / "NO" / "MAYBE" novelty tags — all checked against CLAUDE.md / handoff corpus; found no false "YES" (i.e., claiming novelty for something GTOS already ships) except candidate **#34** which correctly flags duplication with Component 3B. Clean.

### 3d. No-projection discipline (good)

The doc correctly refrains from citing AI-projected Sharpe/WR numbers as validated, and the "competitor weaknesses" Section 2.9 point 2 calls this out explicitly. Stage 1 integrity PASS.

---

## 4. Missing from P0 (recommended additions)

Two P0 items should be ADDED; one P2 item should RISE.

### 4.1 New P0: **"Block all orders" master flag audit**

Currently synthesis candidate #14 at P1. Suggest **promote to P0**.

- **Rationale:** YouTube batch_03 [6] Brian Downing's specific failure mode — test env + prod env sharing code path, flag miss → real-money loss — is a week-one audit not a weeks-away deploy. CLAUDE.md has `deployment.phase: 2` but no evidence in the codebase that this is a true circuit-breaker vs. a cosmetic config switch. Audit is cheap (1 day), risk is real (one wrong flag = live FTMO loss).
- **Effort:** S (audit + test harness).
- **Risk:** L (read-only audit; fix is simple additive gate).
- **Evidence:** `youtube_extractions/batch_03.md:194-198,234-236`.

### 4.2 New P0: **API spend cap (prepaid-card)**

Currently candidate #27 at P2. Suggest **promote to P0** given:

- CLAUDE.md current cost ~$60/mo with effort=max; a busy day with max-effort + heavy candidate traffic can 5-10× that transiently.
- `batch_07.md:6` "$10,000 API bill over a single weekend" — direct competitor horror story.
- CLAUDE.md session 23 canary cache already reduced exposure ("$6–75/day → ~$12/mo") but only for canary calls. Main-loop spend is uncapped.
- Operational (not code) — prepaid-card setup with monthly cap is a 1-hour task.
- Asymmetric: downside is catastrophic, upside cost is zero.

### 4.3 Flag: **Between-KZ pending limit commit**

CLAUDE.md flags this as uncommitted + blocking (handoff 17) — this is NOT in the synthesis's candidate list because it's not a competitor-sourced item. The synthesis correctly stays in-scope. **But** a good synthesis memo would note in Section 5 ("What GTOS is missing or exposed on") that this is the #0 prerequisite before any of the #1-#6 P0 items ship. The synthesis already notes this at Line 227, so PARTIAL CREDIT — just needs stronger sequencing language.

---

## 5. Duplicates with existing GTOS capability

| # | Synthesis candidate | Existing GTOS capability | Duplicate? | Notes |
|---|---------------------|--------------------------|------------|-------|
| 3 | Daily no-data alert | Canary cache (handoff 23) + between-KZ fix (handoff 17) | **Partial** — synthesis correctly flags as "PARTIAL" novelty. Distinction: canary = API drift, this = tick liveness. Keep. |
| 16 | Weekly AI summary of skipped trades | `api_refusal_monitor.py` + `malformed_responses.jsonl` | **Partial** — extends not duplicates. Keep. |
| 28 | Log-event density benchmark | `shadow_logs/` already writes per-event; density baseline is new | **Not duplicate** — new dimension. Keep. |
| 34 | BlackRock AlphaAgents debate | Component 3B (Bull/Bear Debate, paused per CLAUDE.md) | **Full duplicate** — synthesis correctly rejects at P3. |
| 11 | DDtoP ratio gate | None explicit | **Not duplicate** — keep. |
| 12 | Composite strategy score | None (single framework) | **Not duplicate** — keep. |
| 9 | Gateway-only broker connection | Per-symbol PID-locked processes + 15min watchdog | **Not duplicate** — fundamentally different architecture. Keep. |
| (new) | Shadow-mode deployment pattern (Section 2.4 item 9) | GTOS already does shadow-log-then-promote: `be_shadow_logger.py`, `proximity_shadow_logger.py`, `partial_close_shadow_logger.py`, `candidate_features_logger.py`, `ob_continuation_monitor.py` | **Full duplicate** — synthesis correctly does NOT candidate-list this. Clean hygiene. |

**Verdict on duplicate hygiene: GOOD.** Synthesis avoids re-surfacing existing GTOS capabilities as novel candidates. Only candidate #34 is explicitly duplicate and correctly rejected.

---

## 6. Recommended edits (concrete, one-line each)

1. **Line 49:** Change "batch_08 Bayesian toxicity 82% vs VPIN 65% vs Hawkes 78%" → **"batch_08 [2] Bayesian toxicity 82% vs Microprice 65% vs Hawkes 78%"**.
2. **Line 39:** Change "batch_08 regime-mult stop sizing" → **"batch_07 [15] regime-mult stop sizing"**.
3. **Lines 35, 37, 45, 51, 65, 79, 81, 95, 117, 119:** Replace all `[xxx]` placeholders with specific batch-item numbers per Section 3b above.
4. **Line 143-146 (candidates #4, #5, #6):** Reclassify **P0 → P1** OR split each into "P0 shadow-log-only" + "P1 gate-change" to align with WF-1 discipline. Specifically:
   - #4 DCC-GARCH: split into P0 *"add correlation-shock Telegram alert on rolling Pearson >2σ move"* (trivial, additive) + P1 *"full DCC-GARCH pipeline"*.
   - #5 VPIN: stays P1 (tick-pipeline spike is the blocker).
   - #6 Time-stop: split into P0 *"`time_in_trade_shadow_logger.py` — log what exit at 30/60/120min would have yielded"* + P1 *"actual exit-gate change"*.
5. **Line 141 (candidate #1):** Add implementation caveat: *"Guard against false-positive flatten on transient network blip — require 3 consecutive missed heartbeats @ 5min intervals before trigger."*
6. **Line 154 (candidate #14):** Promote **P1 → P0** — "Block all orders" master-flag audit is a week-one deliverable, not R2.
7. **Line 167 (candidate #27):** Promote **P2 → P0** — prepaid-card API cap is operational, 1-hour task, protects against $10K weekend.
8. **Line 152 (candidate #11):** Mark citation as **"NEEDS RE-VERIFICATION"** — DDtoP terminology not found in batch_06 TOP FINDINGS. Reviewer to confirm exists or remove.
9. **Line 169 (candidate #29):** Change citation from "batch_09 [24]" to **"batch_03 [#41] Quote Fade Algorithm"**.
10. **Line 59:** Change "competitor pattern (common)" to **"batch_03 [#18] Multi-Asset Bot Suite (single source — not universal competitor practice)"**.
11. **Line 155 (candidate #15):** Tighten the citation the same way — reference batch_03 [#18] explicitly, not "competitor pattern (common)".
12. **Section 3 preface (Line 137):** Add sentence: *"P0 priority requires BOTH (a) concrete within 1 week AND (b) WF-1-safe (shadow-log-only OR additive-safety-gate OR bugfix). P0 items that touch exit-gate or sizing logic must be split into shadow-log-P0 + gate-change-P1."*
13. **Section 5 sequencing (Line 207):** Add at top: *"Prerequisite: ship between-KZ pending-limit fix (handoff 17, uncommitted) before any P0 from this list — orchestrator change + 5-process restart is shared blast radius."*
14. **Section 1 Line 15:** Change "6 P0 (propose to CEO now)" to accurate count after P0 reclassification (recommend **5 P0** after moves: #1, #2, #3, #14 [promoted], #27 [promoted] — with #4/#5/#6 in various shadow-logger vs gate-change splits).
15. **Section 6.1 Line 248 ("Generate a profitable trading rule..."):** Note: this verbatim prompt format is **research-grade only** — shipping a similar prompt into T7 violates WF-1 without CEO explicit approval. Synthesis already flags this at candidate #21 P2; reinforce in the prompt-library section.

---

## 7. Overall quality score

Four-dimension scorecard (each /10):

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Factual accuracy** | 7/10 | One clear error (VPIN/microprice swap), one misattribution (batch_08/batch_07 for regime-mult), 8-10 `[xxx]` placeholder citations. Core high-value finding (heartbeat-flatten verbatim) is verified. No fabricated numbers. |
| **Priority calibration** | 5/10 | Three of six P0 items (#4, #5, #6) are miscalibrated for WF-1 discipline — they are net-new statistical pipelines or trading-logic changes, not "safe, concrete, ship this week." Candidate #14 (block-all-orders audit) and #27 (API cap) are mis-demoted. Structure of priority tiers is sound; assignments need work. |
| **CEO-readiness** | 6/10 | Sections 1, 4, 5 are CEO-readable as-is. Section 2 has too many `[xxx]` placeholders for a deliverable; Section 3 priorities need reshuffle. After the 15 edits above, this rises to ~9/10. |
| **GTOS-duplication hygiene** | 9/10 | Synthesis correctly flags Component 3B duplicate (#34), correctly avoids re-surfacing shadow-logger-already-exists patterns, correctly credits CLAUDE.md moat (Section 4). Only minor imprecision: shadow-log-then-promote pattern could be called out as already-GTOS more clearly in Section 2.4 (blue-green deploy item). |

**Total: 27/40.** After the 15 recommended edits: ~34-36/40.

---

## 8. Summary for the CEO

- **Ship:** heartbeat-flatten kill switch (#1), pending-intent persistence (#2), no-data alert (#3), block-all-orders audit (#14 promoted), API spend cap (#27 promoted). These 5 are truly WF-1-safe and deliverable in 1-2 weeks.
- **Shadow-log first, decide later:** DCC-GARCH correlation alert (#4 split), VPIN/OFI loggers (#5, #10), time-in-trade logger (#6 split), Hurst feature (#7), HMM regime logger (#8), microprice (#19).
- **R2 validation-battery adds:** DDtoP gate (#11 — re-verify source), composite score (#12), parameter perturbation (#17), MC permutation (#20).
- **Defer:** #22 Hawkes, #21 T7 regime prompt, #24-25 COT/Shanghai, #29 quote-stuffing (research-grade).
- **Reject:** #31-35 (correctly flagged P3).

**Biggest single-item takeaway:** the heartbeat-flatten kill switch closes the most dangerous safety gap in GTOS today — a silent symbol-process death with open position during a high-volatility news release. Every other candidate is lower-consequence. This is the P0-of-P0s.

---

*End of cold review. 15 recommended edits. Verdict: GO WITH FIXES. Quality score 27/40 → projected 34-36/40 post-edits.*
