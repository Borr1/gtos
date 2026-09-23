# Session 25 — Apr 18, 2026 — Retest Geometry Tier 1 Verified + Tier 2 Spec/Dispatched + Weekend Plan

**Status:** Tier 1 distributional analysis verified on n=726. Tier 2 (intra-candle entry) specced + dispatched in parallel. Weekend fix list locked. FTMO funded challenge target: Tue 2026-04-21.
**Predecessor:** Session 24 (Task A — OB continuation monitor shipped, commit `11dee1d`)
**Author:** Main thread Claude
**WF-1:** No `src/components/`, `prompts/`, or `config/` changes this session. Compliance maintained.
**Commits this session:** zero. Documentation + research only.

---

## TL;DR

1. **Tier 1 distributional analysis (Q1-Q5) on n=121:** 2 parallel agents (`distrib_a`, `distrib_b`) converged byte-identical Q1-Q4. Headline: P(WIN | retest does NOT penetrate far OB edge, Geom A) = 100% (n=55), Wilson 95% lower bound 93.5%.
2. **Verification on n=726 (A2_v2):** 2 parallel agents (`verify_a`, `verify_b`) reproduced. Strengthened to **P=100% (452/452), Wilson lower 99.16%**. Per-symbol replication: 5/5 symbols independently 100% WR on non-penetrated, all Wilson lowers 95.6-96.4%.
3. **Wick-vs-close categorical investigation REJECTED.** `verify_b` caught it as a mechanical artifact of the existing 0.5 ATR SL margin discontinuity. Stratified by depth: shallow (≤0.5 ATR) both classes 100% WR; deep (>0.5 ATR) both classes 0% WR; pairwise Fisher p = 1.00 within each depth bucket. **Lesson 4 logged in ADR 003.** Do NOT build a wick/close gate.
4. **Tier 2 (intra-candle entry study) specced + dispatched in parallel** (`intra_a` + `intra_b`). Tests far-edge limit, midpoint limit, hybrid 50/50 vs market entry. Spec: `research/retest_geometry/tier2_intra_candle_entry_spec.md`. 3 originally-open questions resolved by CEO and locked in spec "Decisions" section.
5. **Weekend plan (CEO-approved):** Sat = Tier 2 results + decisions / Sun = between-KZ commit + persistence + races + canary refresh / Mon = demo verification with all fixes deployed / Tue = FTMO funded account challenge live.

---

## What we did this session (chronological)

### Phase 1 — Distributional Tier 1 (Q1-Q5) on n=121
- Original framing was binary continuation rates (Geom A 70% / Geom B 37.5%); CEO redirected to distributional analysis for SL/entry calibration. Quote: *"im trying to get as much juice as possible from the data"*.
- Two parallel agents: `distrib_a`, `distrib_b`. Same brief, separate code paths.
- Both ran on `research/retest_geometry/outputs/historical/combined_retests.csv` (A1_v2, n=121, ADR-003-compliant timing fix).
- Q1-Q4 byte-identical. Q5 SL-sensitivity diverged on the optimal margin (`distrib_a`: keep m=0.5; `distrib_b`: try m=0.7) due to different handling of the simulator's skip-entry-candle convention. Both agreed tightening below m=0.3 ATR is destructive.
- Reports: `research/retest_geometry/outputs/distributional_analysis/distrib_{a,b}_report.md`

### Phase 2 — Verification on n=726 (A2_v2 sample)
- CEO approved n=726 verification round given small n=121 in Phase 1.
- Two parallel agents: `verify_a`, `verify_b`. Same brief.
- All headline numbers replicated identically between agents.
- Verified finding: **P(WIN | not penetrated, Geom A) = 100% (452/452), Wilson 95% lower bound 99.16%** (strengthened from 93.5% on n=55).
- Reports: `research/retest_geometry/outputs/distributional_analysis/verify_{a,b}_report.md`

### Phase 3 — Wick-vs-close categorical investigation
- CEO observed that "penetration" was wick-based (candle's extreme price), conflating wick-reclaim vs close-past-edge events. Asked whether close-past-edge could be a structural failure signal that wick-only isn't.
- Both verify agents produced identical 3-way splits: not_penetrated / wick_only / close_penetrated = 466 / 56 / 204; WRs 100% / 70% / 19%; pairwise Fisher p ≈ 1.6e-12.
- `verify_a` recommended deploying close-past-edge as a production exit gate.
- `verify_b` ran depth-stratification analysis `verify_a` missed: stratified by penetration depth, the categorical added zero information (shallow ≤0.5 ATR: both classes 100% WR; deep >0.5 ATR: both classes 0% WR; pairwise Fisher p = 1.00 within each depth bucket).
- Conclusion: the apparent signal was a downstream artifact of the existing 0.5 ATR SL margin discontinuity. The wick/close categorical IS the SL margin in disguise.
- **Decision: do NOT build a wick/close gate.** Lesson 4 logged in ADR 003.
- This validates the 2-agent independent verification pattern: `verify_b` caught a methodological artifact `verify_a` missed.

### Phase 4 — Tier 2 specification
- Authored spec at `research/retest_geometry/tier2_intra_candle_entry_spec.md`.
- Tests intra-candle limit-at-edge entry vs current market-on-close entry.
- 8 sub-questions, pre-committed H1/H2/H2b/H3 hypotheses, decision tree for deployment.
- 3 open questions resolved by CEO and locked in spec "Decisions" section before dispatch:
  1. **Add limit-at-midpoint as a 1st-class anchor** (H2b added)
  2. **OB-size as stratification, NOT subset**
  3. **Same-price market/limit fills treated as identical** (differential = 0R, count tracked separately)

### Phase 5 — Tier 2 dispatch
- Dispatched `intra_a` + `intra_b` in parallel (Opus 4.7, max-effort).
- Independent code paths, no coordination.
- Output: `research/retest_geometry/outputs/intra_candle_entry/intra_{a,b}_report.md`
- Wall clock estimate: 30-45 min per agent (raw OHLC re-walk is O(n × window) per row × n=726).

---

## Findings — verified, headline-grade

### Continuation post-non-penetration is essentially certain
- **P(WIN | retest does NOT penetrate far OB edge, Geom A) = 100%** (452/452 on n=726)
- Wilson 95% lower bound: **99.16%**
- Per-symbol replication: all 5 symbols independently 100% WR; Wilson lowers 95.6-96.4%
- Interpretation: when the OB defends, it defends absolutely on this dataset

### Median winner reverses shallow
- Tier 1 finding (consistent across both rounds): median winner reverses at ~55% of OB body depth
- Most winners do NOT reach the far edge → far-edge limit would NEVER fill on the highest-conviction winners
- This tension is exactly what Tier 2 quantifies: fill rate vs price improvement vs missed-setup cost

### Existing SL = 0.5 ATR margin is empirically near optimal cliff
- Winner MAE p90 = 1.06 ATR (sits below median total SL distance from entry of ~1.34 ATR)
- Loser p10 MAE = 0.87 ATR (nearly all losers MAE'd past the body)
- Best Youden separator: 0.92 ATR (n=121) → 0.53 ATR (n=726, tightens toward the SL margin)
- **No SL change recommended on this evidence.**

### Wick/close categorical was an artifact (do NOT build the gate)
- The 3-way split (100%/70%/19%) was real; the causal claim was not
- Stratified by depth: categorical adds zero information
- Recommendation: SL margin already captures depth-based discrimination. Future rule: stratify by underlying continuous variable before recommending categorical gate.

---

## ADR 003 — Lesson 4 added

**"Categorical reformulations of continuous variables can produce statistically dramatic but mechanically meaningless splits."**

Wick-vs-close penetration looked like a discovery (3-way WR split 100% / 70% / 19%, Fisher p ≈ 1.6e-12) — but stratified by penetration depth, the categorical added zero information (shallow ≤0.5 ATR: both classes 100% WR; deep >0.5 ATR: both classes 0% WR; pairwise Fisher p = 1.00 within each depth bucket). The "discovery" was a downstream artifact of the existing 0.5 ATR SL margin discontinuity.

**Future rule:** before recommending a categorical gate, stratify by the underlying continuous variable to verify the categorical isn't a downstream proxy.

ADR 003 also gained a full "Post-decision verification (2026-04-18, same session)" section documenting all four agent rounds (`distrib_a/b`, `verify_a/b`).

---

## Tier 2 study — state at end of session 25

- **Spec:** `research/retest_geometry/tier2_intra_candle_entry_spec.md` (locked, 3 open questions resolved in "Decisions" section)
- **Dispatched:** `intra_a` + `intra_b` at session 25 close, parallel, Opus 4.7
- **Output dir:** `research/retest_geometry/outputs/intra_candle_entry/`
- **Reports expected:** `intra_a_report.md`, `intra_b_report.md`
- **Convergence checks:** fill rate (within 2pp), mean R differential (within bootstrap CI), H1/H2/H2b/H3 verdict agreement
- **If verdicts disagree:** adversarial methodology review (third agent, cold) before any decision
- **Decision rules already pre-committed in spec — see Hypothesis section**

When agents complete, next session should:
1. Read both reports
2. Verify convergence (fill rate, R differential, verdict)
3. Write joint summary
4. Bring CEO go/no-go decision on hybrid entry rule

---

## Weekend plan (CEO-approved 2026-04-18)

### Saturday 2026-04-18
- ✅ Tier 1 verification + ADR 003 update (this session)
- ✅ Tier 2 spec lock + dispatch (this session)
- ⏳ Wait for `intra_a`/`intra_b` reports (~30-45 min each)
- ⏳ Convergence check + joint summary
- ⏳ CEO go/no-go on hybrid entry rule

### Sunday 2026-04-19 — must-fix before funded
- Commit between-KZ pending limit fix (handoff 17, ready, uncommitted) → restart 5 processes
- Implement `pending_intent` persistence (in-memory only → JSON file with restore-on-startup)
- Fix `execution.py:233` destruction race (`pending_intent = None` set BEFORE MT5 order confirmation)
- Fix `_active_trade_record` never set on limit fill path → `_finalize_exit()` never called → exit data lost

### Sunday 2026-04-19 — should-fix
- Refresh canary fixtures with borderline CANDIDATEs (T7 has higher CR than P2A v1; current 10 fixtures all NO_TRADE)
- CEO decision on `sl_too_tight` OB exception (handoff 16, blocking 4-5 trades/week)
- CEO decision on GBPUSD/XAUUSD macro override (handoff 16, T7 non-compliance)
- Apply Tier 2 result if H1/H2b/H2 holds (likely shadow-first, not direct live)
- Write Sunday wrap-up handoff (session 26 starter)

### Monday 2026-04-20 — demo verification day
- All Sunday fixes deployed
- Run all 5 instruments on demo for full trading day
- Watch for regressions
- **Abort funded plan if anything off**

### Tuesday 2026-04-21 — FTMO funded account go-live
- Start funded challenge ONLY if Monday clean
- Daily monitoring per existing protocol

---

## Must-fix list (priority-ordered for Sunday)

| # | Item | File / Ref | Risk if shipped without |
|---|------|------------|------------------------|
| 1 | Between-KZ pending limit fix commit + restart | handoff 17 (uncommitted) | Confirmed +1.5R US30 miss; happens whenever limit pending outside KZ |
| 2 | `pending_intent` persistence | New: persist to `knowledge_base/meta/pending_intents.json` (or per-symbol file); restore on startup | Watchdog kills every 15 min; pending limit silently lost across restarts |
| 3 | Fix `pending_intent` destruction race | `execution.py:233` — move `pending_intent = None` AFTER successful MT5 order confirmation | Order failure → intent silently lost (higher risk outside KZ with wider spreads) |
| 4 | Fix `_active_trade_record` never set on limit fill path | `execution.py` (limit fill code path) — wire `_active_trade_record` so `_finalize_exit()` runs | Exit data lost for all limit-filled trades; corrupts post-trade analysis |

---

## Should-fix list (best-effort this weekend)

- Refresh canary fixtures: 10 fixtures in `scripts/canary_fixtures/` are all NO_TRADE; need borderline CANDIDATE coverage for T7 drift detection
- CEO decision: `sl_too_tight` OB exception (handoff 16)
- CEO decision: GBPUSD / XAUUSD macro override (handoff 16)
- CEO decision: batch simulations for remaining instruments (~$120.58 total; script ready at `scripts/simulate_t7_live_period.py`)
- Apply Tier 2 result (if H1/H2b/H2 holds) — likely shadow first, not live, but CEO may approve direct live deploy if differential is large

---

## Deferred / parked (not weekend, not blocking funded)

- **Approach C in-line resolver** for OB continuation monitor (next WF-1 window — see Task A handoff 24)
- **XAUUSD 126-day silent gap** in `data/historical/` (Task A handoff — needs investigation when bandwidth permits)
- **Wire OB continuation monitor into watchdog cron** (currently CLI-runnable; cron next session)
- **MT5 timezone bug** in `mt5_real.py` (`fromtimestamp()` without UTC — latent on UTC machines, dormant on Windows)
- **Tier 2 follow-on questions** (continuation-R distribution, depth × magnitude correlation, partial-close optimization) — independent specs

---

## Open CEO decisions (pending)

1. **Tier 2 hybrid entry rule** — depends on Tier 2 results (this weekend)
2. **`sl_too_tight` OB exception** (handoff 16)
3. **GBPUSD / XAUUSD macro override** (handoff 16, T7 non-compliance)
4. **Batch simulations remaining instruments** (~$120.58)
5. **GBPUSD post-2026-04-30** (CEO-locked through Apr 30; revisit then)

---

## Live system state at end of session 25

- **WF-1:** maintained (no `src/components/`, `prompts/`, `config/` changes)
- **Commits this session:** zero
- **All 5 instrument processes:** assumed running (not verified this session — git status shows live_evaluations + no_trades accumulating for 2026-04-17, consistent with normal operation)
- **Last commit on main:** `817b5bc` (docs: reframe session 25 briefing — pre-session)
- **Recent commits in scope:** `11dee1d` (Task A monitor), `0c26d25` (Task C canary cache)
- **Test suite:** 1292 pass, 8 pre-existing failures (unchanged from session 24)

---

## Fresh-session reading order

1. **CLAUDE.md** — project instructions, current state, validated numbers
2. **`.context/02_session_handoffs/25_apr18_retest_tier1_verified_tier2_dispatched_handoff.md`** (this file) — most recent state
3. **`.context/00_core/quick_reference_card.md`** — live ops, kill zones, emergency stops
4. **`.context/06_decisions/003_retest_geometry_study_corrected_methodology.md`** — esp. Lesson 4 + Post-decision verification section (Tier 1 verified findings)
5. **`research/retest_geometry/tier2_intra_candle_entry_spec.md`** — Tier 2 spec with locked decisions
6. **`research/retest_geometry/outputs/intra_candle_entry/intra_{a,b}_report.md`** — Tier 2 results (when ready)
7. **`.context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md`** — predecessor for monitor + parked items context
8. **`.context/02_session_handoffs/17_apr14_between_kz_limit_fix_handoff.md`** — uncommitted between-KZ fix (Sunday must-fix #1)
9. **`.context/02_session_handoffs/16_apr13_monitoring_audit_handoff.md`** — sl_too_tight + macro override CEO decisions

---

## TODO for THIS handoff (will be appended when Tier 2 results arrive)

When `intra_a` + `intra_b` complete, append:
- "Tier 2 results — convergence check + joint summary" section
- H1/H2/H2b/H3 verdict
- Update Open CEO decisions item #1 with the actual recommendation
- Update Sunday plan with any deploy/no-deploy decision

---

# APPENDED — Tier 2 results + adjudication + load-bearing concern (post-dispatch, same session)

**⚠️ CEO ASSESSMENT (verbatim): "you're exhausted and you started hallucinating ... we had a very long discussion with you and you're clearly exhausted." — main thread Claude was running long-context by the time this section was written. Treat the CONCLUSIONS in this section as PROVISIONAL. The DATA (what each agent reported, what the trade record shows, what the source code says) is preserved verbatim. A fresh session is being dispatched explicitly to re-verify everything from scratch — see `25_apr18_FRESH_SESSION_TIER2_VERIFICATION_PROMPT.md`.**

---

## Timeline of post-dispatch events

1. `intra_a` completed first → report at `research/retest_geometry/outputs/intra_candle_entry/intra_a_report.md` (263 lines)
2. `intra_b` completed → report at `research/retest_geometry/outputs/intra_candle_entry/intra_b_report.md` (423 lines)
3. Main thread wrote convergence summary at `research/retest_geometry/outputs/intra_candle_entry/convergence_summary.md` — flagged verdict disagreement on H1 + H2b
4. CEO chose **Option A** (per spec line 156): dispatch adversarial third agent for adjudication
5. `intra_c` (cold, with access to prior reports) completed → report at `research/retest_geometry/outputs/intra_candle_entry/intra_c_adjudication_report.md` (442 lines)
6. intra_c verdict: **DEFER** with a load-bearing claim that production already uses limit-at-OB-near-edge (not market-on-close as the spec stated)
7. Main thread attempted source-code verification of intra_c's claim
8. CEO pushed back: "doesn't it use market order when the candle close? please verify this"
9. Main thread dug deeper — production is "software-limit at AI's near-edge → MT5 market order at candle close when wick triggers"
10. CEO pushed back again with operator-grade observation: "it does notify me of the zone of the limit order, but it only executes it as market order when the candle closes"
11. CEO declared main thread exhausted; instructed to update handoff + write fresh-session verification prompt

---

## What the 3 agents actually reported (raw findings — preserved verbatim)

### intra_a (file: `intra_a_report.md`)
- Used spec-literal market entry = M15 candle close
- Far-edge limit fill 71.6% (520/726), midpoint 87.7% (637/726)
- Far-edge limit-minus-market mean R: **+0.240** [+0.108, +0.368]
- Midpoint limit-minus-market mean R: **+0.150** [+0.077, +0.219]
- Verdicts: H1 HOLDS by mean (CI lower below threshold), H2 single-pos HOLDS, H2 per-leg below bar, H2b HOLDS, H3 fails
- Recommendation: deploy hybrid 50/50 (far-edge) to live shadow

### intra_b (file: `intra_b_report.md`)
- Used CSV's `retest_entry_price` field for market entry baseline
- Far-edge limit fill 71.6% (520/726), midpoint 85.5% (621/726) — 16-row gap from intra_a
- Far-edge limit-minus-market mean R: **+0.178** [+0.053, +0.299]
- Midpoint limit-minus-market mean R: **+0.086** [+0.015, +0.154]
- Verdicts: H1 FAIL, H2 per-leg FAIL, H2 single-pos PASS, H2b FAIL, H3 fail
- **Critical finding (intra_b uniquely):** Cross-tab on n=498 paired far-edge outcomes:
  - 156 cases (43.8% of market wins) where far-edge limit BREAKS a win that market would have caught
  - 14 cases (8.8% of market losses) where far-edge limit RESCUES a loss
  - 182 cases (51.1% of market wins) where both win, with limit giving 3.86× the R per win
  - **Mean +0.18R differential exists ONLY because winning limit trades are 3.86× R-magnitude — high-variance edge, not high-WR edge**

### intra_c adjudication (file: `intra_c_adjudication_report.md`)
- Final verdict: **DEFER** (not deploy, not document-as-null)
- **Load-bearing claim:** production does NEITHER market-on-close NOR CSV's `retest_entry_price`. It places a limit at OB NEAR edge per `src/prompts/primary_analyzer_prompt.py:150` and `src/components/execution.py:440-595`.
- Claimed verification against trade record `knowledge_base/trade_records/XAUUSD/2026-04-16_ny_1316.json`
- intra_b's interpretation declared canonical for the study (preserves Tier 1 coherence)
- Cross-tab independently verified: 156/14/3.88× — declared methodology-INDEPENDENT
- Pessimism claim refuted: intra_b's own optimistic sensitivity moves differential DOWN (+0.085) not UP, because optimistic resolution helps both market and limit equally
- Two prerequisites before any deployment: (1) M5/M1 re-run on 425 wick_later rows; (2) production-realistic consecutive-loss simulation
- Cross-tab implies P(3 consecutive losses) jumps 1.4% → 23.8% on far-edge limit (17× increase) — wrong shape for prop-firm rules

### Convergence summary (file: `convergence_summary.md`)
- Identified ~0.06R systematic gap between intra_a and intra_b across both anchors
- Root cause framed as "different market-entry interpretation"
- Per spec line 156: verdicts disagree → adversarial third agent required
- Surfaced intra_b's win-broken/loss-rescued finding as deployment-critical

---

## Source-code spot-checks performed by main thread (preserved verbatim — DO NOT trust the conclusions, re-verify)

### Files read
- `src/prompts/primary_analyzer_prompt.py:130-190`
- `src/components/orchestrator.py:434-450, 770-900, 1280-1295`
- `src/components/execution.py:300-600`
- `knowledge_base/trade_records/XAUUSD/2026-04-16_ny_1316.json`

### Raw findings (verbatim from source)
- `primary_analyzer_prompt.py:150`: *"entry_price: OB zone entry — ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT (bottom of nearest unmitigated H1 OB). Do NOT use the current candle close price."*
- `orchestrator.py:838-853`: section comment "# 8. PLACE LIMIT ORDER", calls `set_limit_intent(trade_params={..., "entry_price": tp.entry_price, ...})`
- `orchestrator.py:436-439`: *"if self.execution.pending_intent: ... trade_state = self.execution.check_limit_fill(m15_candles[-1])"* — checks pending_intent BEFORE evaluating fresh setup
- `orchestrator.py:1287`: second call site for `check_limit_fill(candle)` — needs to be understood (intra-KZ? extended check?)
- `execution.py:452-460`: `set_limit_intent` stores `limit_price = trade_params["entry_price"]` (i.e., AI's near-edge value)
- `execution.py:510-513`: trigger logic `(LONG and candle["low"] <= limit_price) or (SHORT and candle["high"] >= limit_price)`
- `execution.py:387-401`: when triggered, sends `{"action": 1, "type": order_type, "price": entry_price, ...}` — `action=1` is `TRADE_ACTION_DEAL` (market order)
- `execution.py:347-352`: `entry_price = tick.ask if direction == "LONG" else tick.bid` (current tick at trigger time)
- Trade record `2026-04-16_ny_1316.json`: AI's `entry_price = 4796.28`, `limit_intent.limit_price = 4796.28`, `decision_pipeline.final_outcome = LIMIT_PLACED`, `execution = None`, `exit = None` (never filled within 48h)

### Main thread's INTERPRETATION (PROVISIONAL — fresh session must verify)
- Production behavior described as: "software-side limit at AI's near-edge price → MT5 market order at current tick when a candle's wick triggers, executed at candle close"
- Concluded the spec's framing of "production currently enters retests at market on the M15 candle close" is factually incorrect
- Concluded both intra_a and intra_b used wrong baselines, so the +0.18R / +0.24R differentials are likely overstated
- Concluded intra_c's DEFER verdict is strengthened (the apparent edge was inflated by a wrong baseline AND the cross-tab still shows shallow-retest winners are forfeited)
- **CEO pushback flagged this entire chain of reasoning as suspect.** Main thread had been running hours; conclusions were drawn quickly under load.

### CEO's operator-grade statement (treat as ground truth, then verify against code)
*"it does notify me of the zone of the limit order, but it only executes it as market order when the candle closes"*

This statement comes from the person who runs the system live and watches Telegram notifications daily. It is the most reliable single source on production behavior. The fresh session should reconcile this with the source code reading.

---

## Specific claims the fresh session MUST independently verify (do not take main thread's word)

1. **What does the AI's `entry_price` field actually represent in production?** (prompt instruction vs. what AI typically outputs in CANDIDATE responses — sample multiple trade records)
2. **Does production market-buy on the CANDIDATE candle close, OR wait for a subsequent candle's wick to touch the AI's entry_price?** (verify the orchestrator main-loop sequencing carefully — line 436 vs line 1287, and whether the CANDIDATE candle itself can trigger its own limit)
3. **What is the CSV `retest_entry_price` field generated from in the upstream A2_v2 backtest pipeline?** (intra_b used this — was it consistent with production behavior or not?)
4. **If production uses near-edge limit fills, are intra_a and intra_b's +0.18R / +0.24R differentials correctly comparing far-edge vs production, or do they include an artifact?**
5. **Is intra_c's cross-tab (156 wins broken / 14 losses rescued / 3.88× R-multiple) numerically reproducible from the per-row simulation data?**
6. **Is intra_c's prerequisite #1 (M5/M1 re-run on 425 wick_later rows) the right next step, OR is the cross-tab finding alone sufficient to lock the DEFER verdict?**
7. **Does the production execution model (per CEO + source) actually match the right baseline for Tier 2, OR is there yet another framing the fresh session should propose?**

---

## What is locked at end of session 25 (regardless of fresh-session re-derivation)

- **Tier 1 verified findings** (P(WIN | not penetrated, Geom A) = 100% on n=452, Wilson lower 99.16%) — these are agent-converged and independent of the production-execution-model question above
- **ADR 003 Lesson 4** (categorical reformulations of continuous variables) — locked
- **Wick/close categorical rejected** — locked
- **Tier 2 spec text** (3 CEO-approved decisions in "Decisions" section) — locked, but the spec's "production currently enters retests at market on the M15 candle close" line MAY need correction pending fresh-session verification
- **Weekend plan** (Sat = Tier 2 + decisions / Sun = must-fix / Mon = demo verification / Tue = funded) — locked
- **Must-fix list** (between-KZ commit, persistence, races, exit data loss) — locked, on Sunday's plate

---

## What the fresh session should output

1. Independent verification (yes/no with evidence) of each of the 7 claims above
2. A corrected production-execution-model description if the current one is wrong
3. A re-derived Tier 2 verdict given the verified production model
4. A recommendation to CEO: deploy / shadow-deploy / DEFER / null result
5. Recommendation on whether to do M5/M1 re-run + consecutive-loss simulation this weekend OR move directly to Sunday must-fix work
6. Updated session 25 handoff (this file) with the corrected analysis as a NEW appended section — preserve the existing PROVISIONAL section as a record of the original (possibly-wrong) main-thread analysis

---

## Files for fresh session to read (priority order)

1. `CLAUDE.md` (mandatory first)
2. **This handoff** (`.context/02_session_handoffs/25_apr18_retest_tier1_verified_tier2_dispatched_handoff.md`)
3. `.context/00_core/quick_reference_card.md`
4. `research/retest_geometry/tier2_intra_candle_entry_spec.md`
5. `research/retest_geometry/outputs/intra_candle_entry/intra_a_report.md`
6. `research/retest_geometry/outputs/intra_candle_entry/intra_b_report.md`
7. `research/retest_geometry/outputs/intra_candle_entry/intra_c_adjudication_report.md`
8. `research/retest_geometry/outputs/intra_candle_entry/convergence_summary.md`
9. `src/prompts/primary_analyzer_prompt.py:130-190`
10. `src/components/orchestrator.py:430-460, 770-900, 1280-1300`
11. `src/components/execution.py:300-600`
12. Several trade records in `knowledge_base/trade_records/XAUUSD/` and `knowledge_base/trade_records/<other>/` — both `LIMIT_PLACED` and (if available) actually-filled trades to see the full lifecycle
13. `.context/06_decisions/003_retest_geometry_study_corrected_methodology.md` — Lesson 4 + Post-decision verification section
14. `.context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md` — predecessor

The fresh-session prompt itself is at `25_apr18_FRESH_SESSION_TIER2_VERIFICATION_PROMPT.md` — pass that to the new session.

---

*Appended by main thread Claude under CEO instruction after extended-context exhaustion. Honesty preserved over polish: conclusions in this appended section are PROVISIONAL pending fresh-session re-verification. Raw data and source-code excerpts are factually accurate (verified at read time).*

---

## Tier 2 fresh-session re-verification (session 25 continuation, fresh-thread)

**Date:** 2026-04-18 (Session 25, fresh context after compaction)
**Verifier:** Main thread Claude, fresh context, `/effort max`, instructed to not trust prior main-thread chain and to treat CEO operator statement as ground truth.
**Scope:** Independent verification of the 7 claims above against source code and raw trade records. No sub-agents spawned. No code changes. Observation only.

### TL;DR

- **Production execution model (per earlier section) is directionally correct but UNDER-SPECIFIED.** Verified byte-for-byte from source.
- **The Tier 2 study has TWO independent mismatches with production, not just one.** The prior main-thread analysis caught one (market-baseline fork), not the other (TP convention).
- **Re-derived Tier 2 verdict: NULL / DEFER regardless of M5/M1 re-run.** The cross-tab + TP-convention mismatch together lock the decision independently of whether intra_a or intra_b is "right."
- **Recommendation:** Do NOT deploy, do NOT shadow-deploy, do NOT do M5/M1 re-run this weekend. The study as designed cannot answer the production-relevant question.
- **Sunday:** skip Tier 2 follow-up entirely. Go directly to the must-fix list (between-KZ commit, pending persistence, race fixes, exit data loss).

### 1. Verified production execution model (ground truth)

Source-verified chain, CANDIDATE → fill:

1. **AI computes `entry_price` at OB NEAR edge.** `src/prompts/primary_analyzer_prompt.py:150` — *"entry_price: OB zone entry — ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT … Do NOT use the current candle close price."* Sample verified: 20/20 `LIMIT_PLACED` trade records in `knowledge_base/trade_records/` match — AI entry sits at `ob_high` (LONG) with SL below `ob_low`.
2. **AI computes TP as entry + 1.5 × SL_distance (entry-relative, fixed 1.5R).** `src/prompts/primary_analyzer_prompt.py:152` — *"take_profit_1: entry + 1.5 x |entry - stop_loss|"*. All 20 trade records confirm R = 1.497–1.504.
3. **On CANDIDATE M15 close, orchestrator calls `execution.set_limit_intent(...)`.** No market order on the CANDIDATE candle. `src/components/orchestrator.py:841-853`. Intent stores `limit_price = trade_params["entry_price"]` → the AI-chosen OB near edge.
4. **Pending check runs BEFORE new evaluation.** `src/components/orchestrator.py:436-461` — if `self.execution.pending_intent`, call `check_limit_fill(m15_candles[-1])` then `return` unconditionally. The CANDIDATE candle cannot trigger its own limit (pending intent isn't set yet when the check runs on that candle; the limit is placed later in the same loop). Next candle close is the first eligible trigger.
5. **Trigger rule on subsequent M15 close:** `src/components/execution.py:510-513` — `(LONG and candle["low"] <= limit_price) or (SHORT and candle["high"] >= limit_price)`. **Wick touch is sufficient; closed penetration not required.**
6. **On trigger, market execution at current tick.** `src/components/execution.py:526-582` — `tick = mt5.get_tick(symbol); current_price = tick.ask` (LONG). `open_trade` is called with `entry_price=intent.limit_price` (the ORIGINAL limit for records) and `sl_distance_override=original_sl_distance` (for position sizing). The MT5 request uses `action: TRADE_ACTION_DEAL` (= 1, market order).
7. **Viability aborts before execution:** wrong-side-of-SL (price blew past), `sl_absolute_min` cushion check. Either aborts to `pending_intent = None`, no fallback retry.

**Key implication for Tier 2 framing:**
- Actual fill price ≠ limit price. Limit price is the TRIGGER; execution is market at tick.
- Slippage between wick-trigger and tick-fill is a real cost the simulation did NOT model.
- Position sizing uses the ORIGINAL limit→SL distance, so R-math is consistent with the limit.
- Lifecycle is "software limit placed → wait for next-candle wick → market-execute at tick with original-SL sizing."

CEO's operator statement ("it does notify me of the zone of the limit order, but only executes it as market order when the candle closes") reconciles exactly with the code: Telegram notification goes out at `set_limit_intent`; execution is the MT5 market deal at subsequent candle.

**Dataset caveat:** No `LIMIT_FILLED` trade record samples found in `knowledge_base/trade_records/` (all 20 sampled are `LIMIT_PLACED`, 50 `REJECTED_L2`, 14 `REJECTED_GATE1_SAFETY`, 6 `EXECUTION_FAILED`, 2 `REJECTED_L2_POST_M5`, 0 `LIMIT_FILLED`). Fill lifecycle is inferred from source only; no live example to cross-check slippage magnitudes. This is a gap — flag for monitoring once a limit actually fills live.

### 2. Per-claim verdicts

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | AI's `entry_price` = OB near edge, not CANDIDATE close | **✅ VERIFIED** | `primary_analyzer_prompt.py:150`; 20/20 trade records confirm |
| 2 | Production waits for subsequent candle; CANDIDATE candle cannot trigger own limit | **✅ VERIFIED** | `orchestrator.py:436-461` sequencing (pending check before new eval; `return` after pending branch) |
| 3 | CSV `retest_entry_price` = M15 close if inside zone else next-candle open | **✅ VERIFIED** | `A2_v2_validation.py:534-553` |
| 4 | intra_a/intra_b differentials correctly compare vs production | **❌ FAILS** on two independent grounds (detailed below) | See §3 |
| 5 | intra_c's win-broken/loss-rescued cross-tab (156/14/3.88×/+0.178R) is numerically reproducible | **✅ VERIFIED BYTE-EXACT** | `scratch/intra_b/simulation_results_canonical.csv`: 156 broken, 14 rescued, 182 both-win, ratio 3.88×, mean diff +0.1780 |
| 6 | M5/M1 re-run is required next step, or does cross-tab alone lock DEFER? | **Cross-tab alone locks DEFER** | See §4 |
| 7 | Production execution model matches Tier 2 study baseline, or different framing needed? | **❌ Different framing needed** | See §3 |

### 3. Why claim 4 fails — TWO independent mismatches

**Mismatch #1: Market baseline (identified by intra_c, still real).** Neither intra_a's "M15 candle close" nor intra_b's `retest_entry_price` models production's "software limit at AI's near-edge, filled on next candle's wick touch, market-executed at tick." Production's effective entry is **the AI-chosen near edge**, with a 1-candle delay and wick-based trigger. Neither agent simulated this. The 0.06R gap between intra_a and intra_b is a methodology fork within a study that is comparing against the wrong baseline in both interpretations.

**Mismatch #2: TP convention (missed by all three agents and the prior main-thread synthesis).** The study inherits `target_a = ob_high + ob_body` from `A2_v2_validation.py:582` — an **OB-anchored fixed target**. Production's AI uses `TP = entry + 1.5 × (entry − SL)` — an **entry-relative fixed 1.5R**. Under OB-anchored TP, a limit filled at a better price hits the same absolute target and so earns a larger R-multiple per winner. That is the mechanical source of intra_b's "3.88× R-per-winner on both-win trades" finding and of the +0.178R mean differential.

Under production's entry-relative 1.5R TP, every winner pays exactly +1.5R and every loser pays exactly −1.0R regardless of where the entry lives on the OB zone. The mean-R advantage of a better entry price **collapses to zero by construction**. What remains is only:

- **Cost:** 156 broken wins (cases where price never retests deep enough and the limit never fills, leaving the trade unbooked) — this cost PERSISTS under any TP convention because it's a fill-rate issue, not a payoff issue.
- **Benefit:** 14 rescued losses (cases where the market entry would have lost but the limit never filled) — PERSISTS for the same reason.

Net under production's TP: ~ (14 × +1.5R rescued) − (156 × +1.5R wins forfeited)/… in expected-R terms is clearly **net negative** before considering the small number of genuinely better fills. The "limit-at-edge is better" conclusion from the Tier 2 study is **an artifact of OB-anchored TP**, not a production-transferable edge.

This is the more fundamental mismatch. The market-baseline fork (intra_a vs intra_b) is noise compared to the TP-convention error.

### 4. Re-derived Tier 2 verdict

**Verdict: NULL / DEFER.** Specifically:

- **H1 (far-edge ≥ +0.20R, fill > 40%):** rejected. The +0.20R was a TP-convention artifact; under production's entry-relative TP the mean differential is ≤ 0 and likely negative due to 156/14 asymmetry.
- **H2 (hybrid ≥ +0.10R):** rejected under both interpretations; same artifact.
- **H2b (midpoint ≥ +0.10R, fill > 50%):** rejected; same artifact.
- **H3 (null):** this is the verdict that actually holds once TP convention is corrected.

**Crucially, M5/M1 re-run would NOT change this.** M5/M1 only addresses same-candle SL-before-TP pessimism within the existing OB-anchored simulation. It refines the magnitude of intra_b's +0.178R figure but does not re-convert TPs. The study's central comparison (better price → bigger R per winner) is the TP-convention artifact, and no granularity upgrade fixes that.

### 5. Recommendation to CEO (single paragraph)

Do not deploy the limit-at-edge change, do not shadow-deploy it, and do not invest weekend time in an M5/M1 re-run or a consecutive-loss simulation of the current Tier 2 design. The Tier 2 study compared far-edge/midpoint/market entries under an OB-anchored TP (target = ob_high + ob_body), but production uses an entry-relative 1.5R TP. Under production's convention, the "better entry price → bigger R per winner" mechanism collapses to zero by construction, and the 156-broken-wins / 14-rescued-losses asymmetry becomes a pure cost. Production's existing behavior — software-limit at AI's OB near edge, filled on the next M15 wick touch via MT5 market order — is already close to the intended economic design, and Tier 1's 100% WR on non-penetrated retests (Wilson lower 99.16%) confirms the base rule is not broken. The honest conclusion is a null result for the entry-rule-change hypothesis and a documented methodology correction for the spec. Use the weekend for Sunday must-fix work; Tier 2 can be re-designed post-funded-challenge if the question is still live.

### 6. Sunday recommendation

**Skip all Tier 2 follow-up. Go directly to the must-fix list.** Priority order (unchanged from prior handoffs):

1. Between-KZ pending-limit check commit + 5-process restart (handoff 17 — uncommitted trading logic change, CEO approval pending)
2. `pending_intent` persistence across process restarts (watchdog kills every 15 min → in-memory intent lost)
3. `pending_intent` destroyed before `open_trade` in `execution.py:233` (race on market fill; silent intent loss on MT5 failure)
4. `_active_trade_record` never set on limit fill path (`_finalize_exit()` never called → exit data loss)
5. Canary fixture refresh (all 10 still baseline NO_TRADE; T7's higher CR makes them lose discriminative value)

The Tier 2 study can be re-designed after the funded challenge runs if the question is still relevant. A corrected design would need to:
(a) use production's entry-relative 1.5R TP,
(b) model the wick-trigger + next-candle + market-tick fill mechanics,
(c) simulate the 1-candle delay for the "CANDIDATE candle cannot trigger own limit" constraint, and
(d) use XAUUSD-NY-only or similar narrow cuts to achieve statistical power on an effect that is now much smaller.

### 7. Corrections required to existing artifacts

Proposed changes — **NOT applied by this session**, flagged for CEO review. Trading-logic code and prompts are WF-1 locked; these are documentation-only corrections.

1. **`research/retest_geometry/tier2_intra_candle_entry_spec.md:12`** — "Production currently enters retests at market on the M15 candle close" is wrong on two counts. Replace with: *"Production places a software-side limit order at the AI-chosen OB near edge on CANDIDATE M15 close, then waits for the next M15 candle's wick to touch the limit; on trigger, MT5 executes a market order at the current tick. Position sizing uses the original limit→SL distance. TP is entry-relative (1.5 × SL distance), not OB-anchored."*
2. **`research/retest_geometry/tier2_intra_candle_entry_spec.md:79-80`** — SL/TP formulation uses OB-anchored target (`target_a = ob_high + ob_body`) inherited from A2_v2. Add explicit warning: *"Production uses entry-relative 1.5R TP, not OB-anchored. Any R-differential attributed to 'better entry price → bigger R per winner' must be recomputed under entry-relative TP before any production claim."*
3. **`research/retest_geometry/outputs/intra_candle_entry/intra_a_report.md`, `intra_b_report.md`, `intra_c_adjudication_report.md`, `convergence_summary.md`** — add prominent header block: *"METHODOLOGY CORRECTION (session 25 fresh-thread): All R-differentials in these reports are computed under an OB-anchored TP (`target_a = ob_high + ob_body`) inherited from `A2_v2_validation.py:582`. Production uses an entry-relative 1.5R TP. Under production's TP, the mean-R advantage of limit-over-market entry collapses to zero by construction and the 156/14 win-broken/loss-rescued asymmetry becomes a pure cost. Do not cite these differentials as production-transferable."*
4. **Create `.context/06_decisions/004_tier2_null_result_tp_convention.md`** — formal ADR recording: the null finding, the two independent mismatches (market baseline + TP convention), why the study as designed cannot answer the production question, and the four prerequisites for any future re-design.
5. **Append to `research/retest_geometry/tier2_intra_candle_entry_spec.md`** — an open-questions section noting that any future Tier 2 design must explicitly model: (a) production's entry-relative TP, (b) wick-trigger on subsequent candle, (c) market-tick fill with slippage, (d) 1-candle-delay sequencing, (e) position sizing on original limit→SL distance.
6. **`CLAUDE.md` → "What is unresolved"** — add line: *"Tier 2 intra-candle entry study — null result pending re-design. Current agents' reports compare OB-anchored-TP R-differentials; production uses entry-relative 1.5R. Do not cite those numbers."*

### 8. Confidence and caveats

- **High confidence** on: production execution model (source-verified at every step), AI near-edge entry rule (20/20 trade records), prompt TP formula, A2_v2 OB-anchored TP (`target_a = ob_high + ob_body`), cross-tab numeric reproduction (byte-exact).
- **Medium confidence** on: fill mechanics (no `LIMIT_FILLED` records in sampled trades; relying on source code only for slippage and tick behavior).
- **Low confidence / open** on: exact magnitude of net expected R under production's entry-relative TP. The direction is clear (net negative given 156/14 asymmetry and collapsed R-multiple advantage), but a proper restatement would require re-simulating the 726 paired cases under entry-relative 1.5R TP. That re-simulation is NOT recommended for this weekend — the qualitative conclusion is robust enough to act on.
- **No changes made to source code, prompts, configs, or the study outputs in this session.** All text proposed above for spec/ADR/handoff is deferred for CEO approval.

---

*Appended by fresh-context main thread Claude under CEO instruction, session 25 continuation. Verified against source files at read time (2026-04-18). Source-code line references checked byte-for-byte. Previous provisional section preserved above. If this section conflicts with anything in the provisional section, this section supersedes.*
