# Session 36 — FRESH SESSION: redacted_account Readiness Verification + FA-4 Execution + Q4.6 Investigation

**Handoff from:** Session 35 FA (2026-04-20 ~07:00 UTC)
**Kickoff window:** redacted_account Stellar 2-Step $100K demo — CEO is treating **Monday 2026-04-20 (today)** as the go-live date using redacted_account settings, **with Tuesday 2026-04-21** the formal Chairman-synthesis kickoff date. Treat today as kickoff for all practical purposes.
**Your role:** Take this session from analytical work → production-ready. Every item in this handoff matters; there is no "nice-to-have" below.
**CEO instruction verbatim:** *"i want a fresh session that does the rest and makes a full verification on what happened and what got implemented and what not and what this recent data we redid with gold and eurusd tell us that you might've missed ... having it as the final checklist of verifying everything ... especially cross checking with the chairman synthesis to make sure we're good and implementing the FA-4"*.

**CRITICAL NEW FINDING (post-handoff v1, from EURUSD Jan-Feb slice completing at 08:55 UTC):**
FA-2 Change 2 (FX precision + validator) is **fully working on XAUUSD but largely NOT working on EURUSD at n=193**. EURUSD Jan-Feb (n=175) shows 63% of raw CANDs are degenerate — FA-2 prompt did not constrain Sonnet-4-6 to 5dp distinct prices on FX. Live validator catches 59% of EURUSD CANDs that sim lets through. See §`Known gaps #4` and `fa3_t7_rerun_report.md §2 + §6 D1` for full detail. **This does NOT change Tuesday plan** (EURUSD stays NO-GO per Chairman, XAUUSD 0.5% stays shipped). It DOES change the narrative in §1.5 (CLAUDE.md item #7 cannot be marked fully closed) and adds a post-kickoff follow-up: prompt v2 for FX before EURUSD can ever be enabled.

---

## MANDATORY FIRST ACTIONS (do these before anything else)

1. Read `CLAUDE.md`.
2. Regenerate + read `.context/LIVE_STATE.md`:
   ```
   python scripts/generate_live_state.py
   ```
3. Read this handoff (you are here).
4. Read `research/b_deep_audit_2026-04-19/phase4_chairman_synthesis.md` — the decision document this session implements.
5. Read `research/b_deep_audit_2026-04-19/fa3_t7_rerun_report.md` — session 35's post-FA-2 sim findings + outstanding decision points.
6. Skim the latest commit diff (`git show fa35cc0`) — FA-2.1/FA-2.2/FA-2.3 implementation.
7. EURUSD Jan-Feb sim (`research/t7_live_simulation/post_fa2/eurusd_jan_feb/`) completed at ~08:55 UTC session 35. FA-3 report has been updated with Section 2 covering all 4 slices and the EURUSD FA-2 compliance failure finding. No further sim work pending.

---

## What was shipped in session 35 (session-level delta)

Five commits relevant to this handoff:

| Commit | Scope |
|--------|-------|
| `4af838f` | **Change 1** (autonomous, session 35 start): per-instrument `_FILL_EPSILON` in `simulate_t7_live_period.py:462` + `EPSILON_BY_SYMBOL` at `:80` |
| `5bdf6f0` | Research: NAS100+EURUSD T7 epsilon revalidation (session 35) |
| `0f66f4c` | Research: session 35 deep diagnostic Phase 1-4 deliverables |
| `5923375` | Docs: touch-count production semantics + honest MC redacted_account |
| **`fa35cc0`** | **Changes 2+3+4 (FA-2):** D3-1 FX precision prompt + validator, D3-2 non-zero `sl_buffer_applied`, C3 XAUUSD 0.5% risk in redacted_account profile |

All five Chairman-recommended changes (1,2,3,4,5) are now in code. Change 5 (D1-bias-lag shadow logger) shipped earlier as commit `0f2dee0`.

Additional session-35 artifacts:
- `research/t7_live_simulation/post_fa2/` — 4 slices × Jan-Apr 2026 post-FA-2 T7 sims (3 of 4 complete at handoff time; EURUSD Jan-Feb may still be running)
- `research/b_deep_audit_2026-04-19/fa3_t7_rerun_report.md` — FA-3 combined report + decision points
- Memory note `feedback_parallelize_aggressively_tier4.md` — split future sims into 8-16 parallel 1-2 week chunks, not 2-4 two-month chunks

---

## Your agenda (in this order)

### Phase 1 — Verification (no changes; prove the session-35 work is correct)

For each item below, produce a tick/cross. If anything fails, STOP and flag to the CEO before proceeding.

#### 1.1 — Code / config bit-exact verification vs Chairman synthesis

Open `phase4_chairman_synthesis.md` §"CEO Q3 — Top 3-5 restoration/edge-upgrade changes" and cross-check each:

- **Change 1** — `scripts/simulate_t7_live_period.py:462` should reference `EPSILON_BY_SYMBOL` (not hardcoded `0.05`). Table at `:80` should include XAUUSD=0.20, NAS100=2.0, USDJPY/GBPJPY=0.02, EURUSD/GBPUSD=0.0002. Verify via `grep -n "EPSILON_BY_SYMBOL\|_FILL_EPSILON" scripts/simulate_t7_live_period.py`.
- **Change 2** — `src/prompts/primary_analyzer_prompt.py` should contain a PRECISION block (after line 157) stating "entry_price, stop_loss, take_profit_1, take_profit_2, take_profit_3, and sl_buffer_applied MUST use the SAME decimal precision as the prices shown in the Market State Object above." + examples. The `_PRICE_FMT` per-instrument rendering is already in place via `set_price_format()` at `primary_analyzer.py:194` (this was pre-session-35 infrastructure; the prompt change leverages it). **Verify the PRECISION block text is there and the schema block at line 236 still shows `"sl_buffer_applied": <float, MSO precision, > 0>` (not literal `0.0`).**
- **Change 3** — Same file: line 152 (stop_loss instruction mentions "non-zero buffer (see sl_buffer_applied below)"), line 155 narrative (`max(0.25 x H1 ATR(14) from MSO, 3 x the smallest price tick shown)`), line 236 schema (`<float, MSO precision, > 0>`). Validator lives at `src/components/primary_analyzer.py:310` via `guard_candidate_degenerate_params` at line ~633. **Verify:** `grep -n "guard_candidate_degenerate_params" src/components/primary_analyzer.py` returns both the definition and the call site.
- **Change 4** — `config/profiles/redacted_account.yaml` should have an `instruments.XAUUSD.risk.risk_per_trade_pct: 0.5` block at lines 46-49 with the C3 rationale comment above it. Verify profile overlay actually applies: start a dummy load of the profile via `python -c "from src.config.loader import apply_profile_overrides, apply_instrument_overrides; ..."` — or, simpler, run `run_agent.py --dry-run --profile redacted_account --symbol XAUUSD` and confirm the effective risk is 0.5%. If you don't have a fast way to verify the merge order, grep the orchestrator: `grep -n "apply_profile_overrides\|apply_instrument_overrides" src/components/orchestrator.py`. **Merge order matters** — the instrument block must be applied AFTER the profile's global risk block.
- **Change 5** — `grep -n "d1_bias_lag" src/ shadow_logs/` should show the logger wired. Commit `0f2dee0` is the reference.

#### 1.2 — Canary regression

Run `python scripts/canary_test.py` from a fresh shell with `.env` loaded. Expected per T1.3.1:
- Baseline tier: ≥11/12 decisions match (≤1 flip permitted)
- Borderline tier: ≥3/4 decisions match (≥75% match)
- Zero keyword drift violations (or ≤2 per fixture, per the tiered spec)

Session 35 confirmed 12/12 + 4/4 post-FA-2. If this run shows regression, something changed — find it before Tuesday.

#### 1.3 — Validator smoke test (critical — session 35 did NOT do this)

The FA-3 report flagged this gap. Do one of:

- **Option A (preferred, ~15 min):** Write a single pytest at `tests/safety/test_guard_candidate_degenerate_params.py` that constructs a `PrimaryAnalysisOutput` with `decision="CANDIDATE"` and `trade_parameters.entry_price == trade_parameters.stop_loss`, calls `guard_candidate_degenerate_params(result)`, asserts result.decision == "NO_TRADE" and result.no_trade_reason == "degenerate_trade_parameters". Second case: entry_price == take_profit_1. Third case: non-degenerate (assert NO demote). This is a 3-case test, 30 lines.
- **Option B (quick-and-dirty, ~5 min):** Python REPL: import the function, construct a fake `PrimaryAnalysisOutput`, call it, assert the decision flip. Log the output. No test artifact.

Option A is the right default — adds coverage, takes 15 min, proof-in-code.

#### 1.4 — FA-3 data sanity check

The previous session wrote `research/b_deep_audit_2026-04-19/fa3_t7_rerun_report.md` with findings on 3 completed slices (XAUUSD Jan-Feb, XAUUSD Mar-Apr, EURUSD Mar-Apr). If EURUSD Jan-Feb has now completed, extend the report with Section 7 (addendum). Aggregate trade-outcome table in §4 will need updating.

Spot-check one number:
- XAUUSD combined Jan-Apr: 32 trades, 8W/24L = 25% WR, −12R total, −0.375R/trade. If your re-derivation disagrees by more than 1 trade or 0.5R, investigate.

#### 1.5 — CLAUDE.md / LIVE_STATE.md hygiene

CLAUDE.md `What is unresolved` still lists items #5 and #7 as open. FA-2 shipped; canary passed. These should flip to closed. Update CLAUDE.md in the same commit that closes the last verification item of Phase 1.

Items to flip:
- #5 T2.prompt (non-zero `sl_buffer_applied`) → **CLOSED for XAUUSD (100% compliance n=184). PARTIALLY CLOSED for FX — EURUSD at n=193 shows 35% compliance. Validator at `primary_analyzer.py:310` is the safety net; prompt v2 needed before EURUSD can be enabled live. XAUUSD/US30/JPY-crosses are GO.**
- #7 FX AI precision issue → **PARTIALLY CLOSED via `fa35cc0`. XAUUSD fully fixed. EURUSD Jan-Feb (n=175) shows 63% degeneracy → FA-2 Change 2 under-constrains Sonnet-4-6 on 5dp FX output. Live validator catches 59% of EURUSD CANDs → EURUSD disabled anyway per Chairman. Reopen as "T2.prompt.v2" post-kickoff: stricter FX precision scaffolding + re-run FA-3 Slice A.**
- #4 / T2.9 sl_beyond_ob — leave as REJECTED (not shipping, per synthesis)

Do NOT close #6 (rolling restart) until you actually do it in Phase 2.

---

### Phase 2 — FA-4 Pre-Tuesday Checklist (from Chairman synthesis §Pre-Tuesday checklist, p.547)

Six items. Execute in this order; #1 and #5 are the ones where a mistake costs real money.

#### 2.1 — Rolling restart all live under `--profile redacted_account` (CRITICAL)

This picks up three waves of changes that are NOT active in the currently-running processes:
- `b298e2a` — M5 refinement + devils_advocate migrated to sonnet-4-6 effort=max
- `dc4cec2` — T2.8 concurrent-cap + daily-loss-stop + dormant state
- `fa35cc0` — FA-2 prompt + validator + XAUUSD 0.5%

Procedure (verify exact process manager with CEO — likely direct PIDs + tmux/pm2):
1. Identify current live PIDs: `ps -ef | grep run_agent` (or Windows equivalent; this is Windows so `tasklist | findstr python` or check the Claw Empire process manager).
2. Kill the 5 symbol processes cleanly (SIGTERM, wait, SIGKILL fallback). XAUUSD, US30, USDJPY, GBPJPY, GBPUSD.
3. Restart each with `--profile redacted_account` overlay:
   ```
   python run_agent.py --mode live --symbol XAUUSD --profile redacted_account
   python run_agent.py --mode live --symbol US30 --profile redacted_account
   python run_agent.py --mode live --symbol USDJPY --profile redacted_account
   python run_agent.py --mode live --symbol GBPJPY --profile redacted_account
   # GBPUSD stays observer — confirm with CEO whether GBPUSD also gets redacted_account profile
   ```
4. Confirm post-restart: each process's startup log should show `profile: redacted_account` and (for XAUUSD) `risk_per_trade_pct: 0.5` (per-instrument override).
5. Verify FA-2 validator is on the hot path: tail each instrument's `logs/{symbol}.log` for the first candle post-restart; should see normal MSO → PA flow. Force a degenerate output is impractical pre-KZ, but the pytest in 1.3 already proves the function works.

**DO NOT skip this step.** Everything else in this session is meaningless if the processes run stale config.

#### 2.2 — Equity peak state reset (CRITICAL, 5 min)

`knowledge_base/equity_peak_state.json` is the H29 drawdown manager's baseline. If it carries the FTMO demo peak into redacted_account, H29's 8% DD trigger fires on the wrong number (could cut XAUUSD risk to 0.25% day-1 artificially, OR fail to cut when DD actually hits 8%).

Procedure:
1. Read the current file. Note the stored equity peak.
2. Get redacted_account demo starting balance from the CEO (should be $100,000).
3. Replace the stored peak with the redacted_account starting balance. Keep the schema identical (don't invent new fields).
4. Verify `src/components/drawdown_manager.py` reads the file correctly on next candle.

If you're not sure what the schema looks like, read the manager's load logic first. Better to ask CEO for the current file contents + the reset value than to guess at format.

#### 2.3 — `mt5_preflight.py` on redacted_account demo (10 min)

`python scripts/mt5_preflight.py` is the 8-check sanity pass. First time we're hitting the redacted_account demo account.

Run it. If any check fails, STOP. Most likely failures:
- Wrong credentials — CEO needs to provide redacted_account demo login
- Symbol names differ (redacted_account may use `XAUUSD.m` or `XAUUSD+` or similar suffix) — if so, the full system needs symbol-mapping support, which is NOT in code. Flag immediately to CEO.
- Spread wildly different from FTMO — Chairman contingency: if redacted_account XAUUSD spread ≥2× FTMO, hold XAUUSD at NO-GO

#### 2.4 — Watchdog E2E verifier (5 min)

`python scripts/watchdog_e2e_verify.py`. Weekend + dead-zone lenient; should report HEALTHY on all 5 instruments post-restart.

#### 2.5 — Telegram alerts: FIX stale FTMO hardcodes + smoke test (30-45 min)

**This is not just a smoke test.** Session 35 found `src/notifications.py` carries stale FTMO assumptions that will make every live redacted_account Telegram notification wrong by 2-4× on dollar figures. Must fix before the first live fill.

**Bug specifics:**
- `src/notifications.py:32-34` hardcodes:
  ```python
  _ACCOUNT_BALANCE = 100_000
  _RISK_PCT = 0.02  # 2%
  _RISK_DOLLARS = _ACCOUNT_BALANCE * _RISK_PCT  # $2,000 per 1R
  ```
- These are module-level static constants. No config read. Every `_fmt_dollars()` call uses this.
- Under redacted_account: non-XAUUSD (1%) → correct is $1,000/R (this module says $2,000). XAUUSD (0.5%) → correct is $500/R (this module says $2,000).
- Affected: `notify_limit_placed` (Risk line), `notify_trade_closed` (P&L dollar line + daily total), `notify_daily_summary` (P&L + per-trade breakdown).

**Proposed fix (recommend this shape; get CEO sign-off on diff before commit):**
1. Read `_RISK_PCT` from the active profile at module import — but the profile isn't known at module import time in this codebase. So plumb risk_pct through call signatures instead: each `notify_*` takes an optional `risk_pct: float` argument; if None, fall back to a config-derived default.
2. Or: add a `configure_notifications(risk_pct_default, risk_pct_by_instrument, account_balance)` one-shot called from orchestrator startup after profile overlay is applied. This is less invasive than signature changes on every call site.
3. Per-instrument override: XAUUSD under redacted_account is 0.5%. The `_fmt_dollars` function needs the symbol to pick the right risk_pct. It already has symbol plumbing in most paths.

Prefer **Option 2** (configure-once at startup). Minimal call-site changes, and the config flows from the single `apply_profile_overrides` + `apply_instrument_overrides` path already wired in the orchestrator.

**Tests to add:** `tests/test_notifications.py` — stub `_send`, call `notify_trade_closed("XAUUSD", "tp_hit", actual_r=1.5)` under a configured state matching redacted_account + XAUUSD 0.5%, assert the message string contains "+$750" (1.5R × $500/R), not "+$3000".

**After fix ships — smoke test:**
1. Ask CEO to confirm `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` are the redacted_account-context values (they may be separate from FTMO-era values).
2. Temporary test script: `python -c "from src.notifications import notify_alert; notify_alert('redacted_account kickoff smoke test — ignore')"` — confirm message arrives on the intended chat.
3. Trigger a test via `notify_trade_closed` with dummy values under the new config to confirm dollar math matches expectations.

**CEO approval:** This is a bug-fix (wrong user-facing $ figures, not trading logic). Falls under "Allowed without approval → Bug fixes that prevent function". BUT: show the CEO the diff before commit anyway — it touches the config plumbing.

#### 2.6 — redacted_account terms web-audit (CEO pre-approved web search, 30-60 min)

Scope:
- Phase 1 profit target: 10% (per CEO; Chairman synthesis said 8% — verify which is current)
- Phase 2 profit target: 5%
- Max daily loss: 5% (broker) vs 4% (our GTOS internal cap) — confirm 4% is still the right internal number
- Max total loss: 10%
- Weekend positions: allowed or not?
- News trading: allowed / restricted / blackout windows?
- Minimum/maximum trading days?
- Consistency rule (e.g., "no single day > X% of total profit")?
- EA / bot policy: explicit permission for automated trading
- Payout terms, profit split, refundable fee

Write findings to `.context/05_operations/redacted_account_terms_audit_2026-04-20.md`. If ANY term materially changes a GTOS gate (e.g., a consistency rule means we should cap single-day profit), flag to CEO before Tuesday.

---

### Phase 3 — Q4.6 Investigation (HIGH-PRIORITY BUG, 4h budget)

Chairman flagged Q4.6 as HIGH-PRIORITY BUG because every Phase 1-3 claim rests on T7 sim numbers. Specifically: Phase 2 γ review surfaced a **12× CAND-rate discrepancy** — T7 sim reports 10 XAUUSD CANDIDATEs across 2100 records (0.48%), while δ's session-KB sample reports 48 CANDs (~2-5%) on the same period.

This is NOT a Tuesday blocker per Chairman — live is protected, FX is disabled, XAUUSD sized-down. But it IS a "how confident are we in the decisions we made" question, since those decisions used T7 sim numbers.

Scope (per Chairman Q4.6):
- Walk 10 XAUUSD session-KB records that are CANDIDATE in KB; trace each to T7 sim → CAND / L2-reject / BLOCKED / NO_TRADE / missing.
- Identify the drop stage. Likely causes in order:
  1. T7 sim drops at L2 stage that session KB keeps
  2. T7 sim pre-screen stricter than live pre-screen
  3. Session KB includes back-fills / replay CANDs that sim dedups out
- Write findings to `research/b_deep_audit_2026-04-19/Q4_6_sim_vs_kb_cand_rate.md`

**Stop condition:** if you spend >4h on this without converging, STOP and hand back to CEO with a status report. This is an investigation, not a fix.

---

## Success criteria (the "done" bar)

- Phase 1 done: every verification item has a ✓ or a CEO-acknowledged ✗.
- Phase 2 done:
  - `logs/{symbol}.log` for each of the 4-5 live instruments shows first post-restart candle processed under redacted_account profile
  - `knowledge_base/equity_peak_state.json` reflects redacted_account starting balance
  - `mt5_preflight.py` passes on redacted_account demo
  - Watchdog HEALTHY
  - Telegram test passed
  - redacted_account terms audit committed
- Phase 3 done or stop-condition hit: Q4.6 either resolved or status-reported
- CLAUDE.md updated: #5, #7 closed; #6 closed after restart; other items audited for currency
- Final commit on main summarizing the session with `Co-Authored-By: Claude Opus 4.7` footer

---

## Known gaps / risks you are INHERITING (be careful about these)

1. **Live FX safety under new prompt is NOT empirically verified.** Canary fixtures are XAUUSD-only. β review showed 0% JPY-cross degenerate PRE-FA-2, but post-FA-2 we have no canary or sim data confirming USDJPY/GBPJPY still emit non-degenerate output. Low risk that new PRECISION block confuses AI on 3dp JPY-cross inputs, but UNVERIFIED. First live JPY-cross CANDIDATE is the first empirical check. Watch the log.

2. **Sim-validator parity gap.** `simulate_t7_live_period.py` parses raw JSON and does NOT invoke `PrimaryAnalyzer.evaluate()`. Sim sees degenerate trades the live validator would have demoted. Impact in session-35 FA-3 report: EURUSD Mar-Apr Cand[1] was a fake `LOSS −1R` in sim that would have been NO_TRADE live. **Patch needed:** 15-min change in sim to call the validator path. Defer to post-Tuesday unless you hit unexpected sim results.

3. **Q4.6 12× CAND-rate discrepancy** (Phase 3 of this handoff).

4. **EURUSD FA-2 compliance failure (NEW — post-FA-3 Slice A):** At n=193 combined (175 Jan-Feb + 18 Mar-Apr), EURUSD raw CANDs are 59% degenerate, 65% sub-FX-precision, 35% non-zero buffer. FA-2 prompt did NOT constrain Sonnet-4-6 on 5dp FX output. Live validator catches the degenerate cases — EURUSD is safe to disable (which it is). Before EURUSD can EVER be enabled, stronger FX-specific prompt scaffolding + FA-3 Slice A re-run needed. Filed as post-kickoff "T2.prompt.v2". Not Tuesday-actionable. See `fa3_t7_rerun_report.md §2 + §6 D1`.

5. **Heartbeat kill switch DISABLED** — CLAUDE.md unresolved #2/#9. Per CEO intent, enable after observation window. Do NOT enable in this session unless CEO says to.

6. **FA-3 report addendum COMPLETE** — EURUSD Jan-Feb landed as Slice A. Section 2 now covers all 4 slices with consistent max-dp methodology. Section 3 added sim-vs-live per-trade breakdown for EURUSD Jan-Feb (2 of 5 sim losses are degenerate → live would see 3 losses, not 5). Section 4 (XAUUSD outcome comparison) unchanged. Section 6 D1 tightened: EURUSD prompt v2 required before enable.

---

## Things to NOT do

- **Do NOT reopen prompt tuning for XAUUSD / US30 / JPY-crosses.** Canary passes, 100% XAUUSD compliance. CEO has said "ship as-is" and the validator is the backstop for the EURUSD residual (which is 59% degeneracy — meaningful but EURUSD is disabled).
- **Do NOT attempt an FX prompt v2 in this session.** EURUSD prompt v2 is identified as a post-kickoff follow-up. Don't touch the prompt pre-Tuesday; filed for a separate strategic session.
- **Do NOT enable FX instruments.** EURUSD/GBPUSD explicitly NO-GO per Chairman. USDJPY/GBPJPY GO at 1% (already enabled pre-session).
- **Do NOT adjust XAUUSD risk.** 0.5% is shipped and CEO-confirmed this session. If FA-4 surfaces a reason to go lower, flag to CEO; don't edit.
- **Do NOT enable heartbeat flatten kill switch.** Stays DISABLED per CLAUDE.md #2/#9.
- **Do NOT ship T2.9 `sl_beyond_ob` strict-`<` → `<=`.** Chairman rejected. Net −1R on XAUUSD bit-exact audit.
- **Do NOT make the demo-environment / terms-audit findings fit the plan.** If redacted_account terms materially conflict with GTOS behaviour, say so and stop. Tuesday slip is better than fail.

---

## Agent usage guidance (project-specific)

- CLAUDE.md at ~30k chars; every Agent() dispatch inherits it. Keep parallel dispatches bounded — memory note `feedback_claudemd_size_discipline.md`.
- For the redacted_account terms web-audit: spawn a `general-purpose` Agent with WebFetch/WebSearch, give it the specific URLs/domains to target (funded-next.com, their terms page, any T&C PDFs). Don't delegate open-ended "research redacted_account"; give it the bullet list above.
- For Q4.6 investigation: spawn an `Explore` Agent pointed at `research/b_deep_audit_2026-04-19/phase2/gamma_review.md` + `research/t7_live_simulation/XAUUSD_t7_simulation.json` + session KB under `knowledge_base/`. Brief it with the specific 10-record trace methodology above.
- Main thread stays on orchestration; delegate Phase 2 executions (restart, preflight, watchdog) as explicit tool calls by you, not sub-agents — they need your full context on the infrastructure state.
- Council pattern (Stage 1+2+3) is NOT needed for this session — all items are execution / verification, not strategic decisions. Use single agents.

---

## Communication pattern the CEO prefers

- Brutally honest. Don't soften confidence numbers; don't hedge to be polite. If something is at 60%, say 60%.
- Before starting each Phase, one-sentence plan + dispatch. After each Phase, one-paragraph status.
- Show diffs BEFORE commit for any prompt / config / live-code change. CEO reviews.
- Flag any discovery that changes the Tuesday kickoff plan IMMEDIATELY — don't batch.
- Memory notes to save if anything new comes up: prefer `feedback_*` for durable rules; `project_*` for redacted_account-specific facts.

---

## Reference map

| Doc | Purpose |
|-----|---------|
| `research/b_deep_audit_2026-04-19/phase4_chairman_synthesis.md` | Session 35 decision document — the "why" behind everything |
| `research/b_deep_audit_2026-04-19/fa3_t7_rerun_report.md` | Post-FA-2 sim results + decision points |
| `config/profiles/redacted_account.yaml` | Active profile for kickoff |
| `src/prompts/primary_analyzer_prompt.py` | Prompt including FA-2 PRECISION block |
| `src/components/primary_analyzer.py` | Validator at line 310 + function at ~633 |
| `scripts/simulate_t7_live_period.py` | Sim tool; sim-validator gap lives here |
| `scripts/canary_test.py` | Canary regression runner |
| `scripts/mt5_preflight.py` | redacted_account demo sanity pass |
| `scripts/watchdog_e2e_verify.py` | Watchdog integration check |
| `knowledge_base/equity_peak_state.json` | H29 DD baseline — MUST be reset to redacted_account starting balance |
| `CLAUDE.md` | Source of truth — unresolved #5/#6/#7 need updating this session |

---

## CEO's closing directive (session 35 verbatim)

> *"basically testing the system is starting from today monday in the demo, but with the redacted_account settings, basically pretending it's the actual funded account and we need to be fully ready and confident for it"*

Today IS live-equivalent. The trading processes need to be treating their next candle as the first redacted_account live trade. Phase 2 item 2.1 is therefore the single most time-sensitive thing in this handoff. If you do nothing else in Phase 2, do the rolling restart + equity peak reset before a kill zone opens.

**Current time at handoff write:** ~07:00 UTC, 2026-04-20 (Monday). London KZ opens 07:00 UTC for XAUUSD/USDJPY/GBPJPY, 08:00 UTC for US30, 07:00 UTC for GBPUSD. **You may already be inside London KZ at session start.** If so: do the restart anyway — at worst you miss one signal; at best you avoid running the next signal on stale config. The CEO has said the velocity-over-caution preference applies (memory `feedback_wf1_velocity_preference.md`).

Good luck.
