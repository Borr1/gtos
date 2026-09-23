# Fresh Session — Tier 2 Re-Verification Prompt (Session 25 continuation)

**Use this verbatim as the opening message to a new Claude Code session.**

---

You are picking up GTOS Session 25 mid-stream. The previous main-thread Claude ran a long-context investigation today (Sat 2026-04-18) and by the end was making mistakes the CEO caught in real time. The CEO's verbatim assessment: *"you're exhausted and you started hallucinating ... we had a very long discussion with you and you're clearly exhausted."*

Your job is to **independently verify everything** — do not trust the previous main thread's conclusions. The raw data (3 agent reports, source code excerpts, trade record) is factually accurate, but the interpretation chain is suspect.

## Stakes

- The CEO starts an FTMO funded account challenge on **Tuesday 2026-04-21**
- Today (Sat) is for Tier 2 decisions and weekend-fix planning
- Tomorrow (Sun) is must-fix engineering work
- Monday is demo verification day
- Any Tier 2 conclusion that drives a deployment decision must be correct, NOT just defensible

## What to read (in this order)

### Mandatory first
1. `CLAUDE.md` — project instructions, current state, validated numbers, prohibited behaviors
2. `.context/02_session_handoffs/25_apr18_retest_tier1_verified_tier2_dispatched_handoff.md` — full session 25 handoff INCLUDING the appended "Tier 2 results + adjudication + load-bearing concern" section that documents the previous main thread's PROVISIONAL conclusions and the specific claims you need to verify
3. `.context/00_core/quick_reference_card.md` — live ops, kill zones, emergency stops

### Tier 2 study artifacts (the 3 agent reports + main thread's joint summary)
4. `research/retest_geometry/tier2_intra_candle_entry_spec.md` — the spec, including the "Decisions" section locked by the CEO and the line that may be factually wrong about production
5. `research/retest_geometry/outputs/intra_candle_entry/intra_a_report.md` — agent A's report (used spec-literal market entry = M15 candle close)
6. `research/retest_geometry/outputs/intra_candle_entry/intra_b_report.md` — agent B's report (used CSV's `retest_entry_price` field for market baseline; produced the cross-tab finding)
7. `research/retest_geometry/outputs/intra_candle_entry/intra_c_adjudication_report.md` — adversarial third agent's adjudication; verdict DEFER; load-bearing claim about production execution model
8. `research/retest_geometry/outputs/intra_candle_entry/convergence_summary.md` — main thread's joint summary (written before CEO challenge surfaced the production-model problem)

### Source code (production execution model — the load-bearing question)
9. `src/prompts/primary_analyzer_prompt.py:130-190` — what AI is told to put in `entry_price`
10. `src/components/orchestrator.py:430-460, 770-900, 1280-1300` — main loop, where pending_intent is checked and where `set_limit_intent` is called
11. `src/components/execution.py:300-600` — `open_trade`, `set_limit_intent`, `check_limit_fill`

### Trade records (real-world verification)
12. List `knowledge_base/trade_records/XAUUSD/` and read `2026-04-16_ny_1316.json` (a `LIMIT_PLACED` record). Then find an actually-FILLED trade record (look for one with non-null `execution` and non-null `exit`) and read it. Compare the `limit_intent` zone vs `execution.entry_price` vs `exit` data to understand the full lifecycle.

### Upstream data pipeline (for question 3 below)
13. Find what generates the `retest_entry_price` field in `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` — likely in `research/retest_geometry/study.py` or similar. Determine what entry-rule the upstream backtest used.

### Background / locked findings
14. `.context/06_decisions/003_retest_geometry_study_corrected_methodology.md` — esp. Lesson 4 and Post-decision verification section
15. `.context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md` — predecessor session

## CEO's operator-grade statement (treat as ground truth, then reconcile with code)

> *"it does notify me of the zone of the limit order, but it only executes it as market order when the candle closes"*

This comes from the person who runs the system live and watches Telegram daily. It is the single most reliable description of production behavior. Your source-code reading must reconcile with this.

## The 7 specific claims to independently verify

For EACH of these, produce evidence (file:line refs, agent-report quotes, trade-record fields) and a yes/no/qualified verdict:

1. **What does the AI's `entry_price` field actually represent in production?** Sample the prompt instruction AND multiple real trade records to confirm the AI follows the instruction. Report any deviation.

2. **Does production market-buy on the CANDIDATE candle close, OR wait for a subsequent candle's wick to touch the AI's entry_price?** Verify the orchestrator main-loop sequencing — line 436 vs line 1287, and specifically whether the CANDIDATE candle ITSELF can trigger its own limit (does `check_limit_fill` get called on the same iteration as `set_limit_intent`?). Confirm with a trade record that shows lifecycle.

3. **What is the CSV `retest_entry_price` field generated from in the upstream A2_v2 backtest pipeline?** intra_b used this — was it consistent with production behavior or not? Trace it to the source script.

4. **If production uses near-edge limit fills, are intra_a's +0.24R and intra_b's +0.18R differentials correctly comparing far-edge vs production, or do they include an artifact?** Quantify if possible.

5. **Is intra_c's cross-tab (156 wins broken / 14 losses rescued / 3.88× R-multiple) numerically reproducible from the per-row simulation data?** Spot-check 3-5 rows manually if scratch data is preserved at `scratch/intra_b/`.

6. **Is intra_c's prerequisite #1 (M5/M1 re-run on 425 wick_later rows) the right next step, OR is the cross-tab finding alone sufficient to lock the DEFER verdict?** Frame the cost/benefit.

7. **Does the production execution model (per CEO + source) actually match the right baseline for Tier 2, OR is there yet another framing you should propose?** This is open-ended — apply judgment.

## What to output

Append a NEW section to `.context/02_session_handoffs/25_apr18_retest_tier1_verified_tier2_dispatched_handoff.md` titled **"Tier 2 fresh-session re-verification (session 25 continuation, fresh-thread)"** containing:

1. **Verified production execution model** — definitive description with source-code line references, reconciled with the CEO's operator statement
2. **Verification verdict per claim (1-7)** — short, evidence-grounded
3. **Re-derived Tier 2 verdict** — given the verified production model, what's the right answer? (deploy / shadow-deploy / DEFER / null)
4. **Recommendation to CEO** — single paragraph, decisive
5. **Sunday recommendation** — do M5/M1 re-run + consecutive-loss sim, OR proceed directly to must-fix work?
6. **Spec/handoff/ADR text corrections** — list any factual errors in the spec text or ADR 003 that need rewriting (do not rewrite them yet — list them for CEO sign-off)

## Hard constraints

- WF-1 discipline: NO `src/components/`, `prompts/`, `config/` changes
- Observation only: no live-system mutation, no commits, no pushes
- DO NOT trust the previous main thread's conclusions — verify independently from source
- DO NOT trust intra_c's claims without independent source-code verification (intra_c was cold but is still an LLM agent; the previous main thread already accepted its claims too quickly)
- DO trust the CEO's operator statement as ground truth, then reconcile with source
- Do NOT spawn additional research agents (intra_d, etc.) — the verification work is YOURS to do directly with file reads
- Honesty over polish: if you can't verify a claim, say so — do not interpolate

## What is locked (do NOT relitigate)

- Tier 1 verified findings (P(WIN | not penetrated, Geom A) = 100% on n=452, Wilson lower 99.16%)
- ADR 003 Lesson 4 (categorical reformulations of continuous variables)
- Wick/close categorical rejected
- Tier 2 spec's 3 CEO-approved decisions (limit-at-midpoint as 1st-class anchor, OB-size as stratification, same-price fills as identical)
- Weekend plan structure (Sat / Sun / Mon / Tue)
- Must-fix list (between-KZ commit, persistence, races, exit data loss)

## What is open (your job to resolve)

- Whether production model in spec line 12 is correct
- Whether intra_a/intra_b reported the right numbers vs. the right baseline
- Whether intra_c's DEFER verdict is correct
- Whether the cross-tab finding is the dominant deployment signal
- Whether weekend bandwidth should go to follow-on Tier 2 work or directly to must-fix engineering

## Why this matters

If the previous main thread's analysis is right, Tier 2 is a CONFIRMED null result with valuable cross-tab insight, and the spec needs corrections. If the previous main thread's analysis is wrong, the original intra_a/intra_b reports may be valid as-is, and the deployment question reverts to the convergence-summary's Option A vs B framing. The CEO needs the right answer before Tuesday's funded challenge.

---

*Prompt authored by main thread Claude (the exhausted one) under CEO instruction. Pass this verbatim to a new Claude Code session.*
