# Fresh Session 34 — Post-NAS100 Worklist

**Issued:** 2026-04-19 (Sun) by session 33 main thread.
**Target window:** Sun evening → Mon 2026-04-20 → redacted_account kickoff Tue 2026-04-21 am UTC.
**Your role:** Claude Code, fresh context. Session 33 ran the NAS100 deep-dive; this prompt hands you the 5 decided follow-up actions. All CEO decisions are locked — do NOT re-open them without explicit CEO request.

---

## MISSION (one sentence)

**Ship the new concurrent-cap + daily-loss-stop risk architecture (T2.8) before redacted_account kickoff Tuesday 2026-04-21, and complete 4 supporting research items (sl_beyond_ob audit, D1-bias-lag shadow logger, EURUSD analysis, live rolling restart for model migration) — without re-opening any locked CEO decisions.**

---

## MANDATORY READING

1. `CLAUDE.md` — project rules.
2. `python scripts/generate_live_state.py` → read `.context/LIVE_STATE.md`.
3. `.context/02_session_handoffs/33_apr19_session_close_handoff.md` — session-33 delta + locked decisions.
4. `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/NAS100_T3_1_synthesis.md` — chairman synthesis, source of the 5 actions.
5. `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/E_review_critique.md` — cold review; the "Opus 4.5 ran this" claim is a HALLUCINATION, already invalidated; don't resurrect it.

Then `git log --oneline -20` to see what's actually landed.

---

## SETTLED DECISIONS — DO NOT RE-OPEN

- **Sim ran Sonnet-4.6 bit-exact** ($22.97 cost math proves it). Don't re-run on Sonnet.
- **Agent A's "3 simulator-artefact wins" claim is DEBUNKED.** Headline 66.7% WR stands. 33 resolved = 22W/11L.
- **redacted_account Stellar 2-Step $100K @ 1% risk, kickoff Tue Apr 21.** Settled.
- **H29 DD reduction STAYS** on top of the new risk architecture. redacted_account: 1.0% → 0.25% at DD ≥8%.
- **Sonnet-4.6 + effort=max** everywhere. No Opus for live gates.
- **Session memory disabled live.** Don't re-enable.

### Risk architecture decisions (CEO-locked session 33)

| # | Decision |
|---:|---|
| 1 | Concurrent cap formulaic: `max_concurrent = floor(max_daily_loss_pct / risk_per_trade_pct)`. redacted_account → 4. FTMO → 2. |
| 2 | Same-instrument concurrency **allowed**. |
| 3 | "Concurrent" counts **filled positions only**. Pending limits don't count. |
| 4 | Daily loss measured **MTM** (realized + unrealized). |
| 5 | On trigger: cancel pending limits + stop AI + let open positions close naturally. |
| 6 | Stop AI calls (not just block trade placement). Save cost. |
| 7 | Daily reset **00:00 UTC**. |
| 8 | Correlation caps remain, layered on top. |
| 9 | H29 DD reduction stays on top. |
| 10 | Daily loss stop at **4%** (replaces current 2.0%). |

---

## ACTION WORKLIST (ordered; parallelizable where noted)

### Action 1 — T2.8 risk architecture (SPRINT, PRE-KICKOFF TARGET)

**Goal:** Ship the concurrent-cap + daily-loss-stop architecture before Tuesday Apr 21 kickoff. If it slips, ship first-week-live.

**Files to change:**
- `src/components/permissions.py:146-150` — DELETE the `kz_trade_limit` gate block.
- `src/components/permissions.py:131-143` — keep `daily_loss_limit` but read from new config key; DELETE `max_daily_losses` count cap.
- `src/components/permissions.py` — ADD a new gate that reads current open-position count (via MT5 `positions_get()` across all symbols, filtered by our magic numbers) and rejects when count ≥ `max_concurrent`.
- `src/components/permissions.py` — ADD a new gate that reads the "dormant_until_utc_day" marker from `pipeline_state/dormant_state.json` and rejects all trades if dormant.
- `config/agent_config.yaml:20` — change `max_daily_loss_pct: 2.0` → **4.0**. DELETE `max_daily_losses: 2` line.
- `config/agent_config.yaml` risk section — ADD `max_concurrent: null` (computed, not set directly). Add documentation comment.
- `config/profiles/redacted_account.yaml` — explicitly pin `max_daily_loss_pct: 4.0` and `max_concurrent: 4` (derived from 4/1 for safety-pin).
- (No FTMO profile currently exists separately beyond the base — FTMO inherits base 4% cap and 2% risk → 2 concurrent. Confirm by running `python run_agent.py --profile ftmo --mode ...` and verifying).
- `src/components/orchestrator.py` — ADD daily-loss trigger handler:
  - Check MTM daily P&L vs −4% at top of each M15 cycle.
  - On trigger: cancel all pending limit orders via `execution.cancel_pending()`, write `pipeline_state/dormant_state.json` with `{"dormant_until_utc_day": "YYYY-MM-DD"}`, skip AI analysis, Telegram alert.
  - On 00:00 UTC new day: clear dormant marker.
- NEW: `src/components/concurrent_tracker.py` or inline function — cross-instrument open-position counter. Must use MT5 magic-number filter so we only count GTOS positions (not manual trades).
- Tests: `tests/test_permissions.py` — ADD cases for concurrent cap and dormant state; `tests/test_concurrent_cap.py` if extracted; `tests/test_daily_loss_stop.py` for the dormant-on-trigger path.

**Verification:**
- Run full pytest suite. Expect ≥1635 passed + 2 skipped baseline; any new failures block ship.
- Manual smoke on demo: set `max_daily_loss_pct` temporarily to 0.01% in a scratch config, trigger a trade, confirm dormant-state file is written and subsequent AI calls are skipped.
- Confirm correlation-group gate still engages on correlated symbols (don't break `portfolio_risk.py`).
- Confirm H29 DD-reduction still fires at DD ≥8%.

**Risk / caveats:**
- **Gate relaxation** — removing `max_kz_trades=1` increases trade frequency. Budget impact: ~+5-10% API spend. Acceptable.
- **MT5 position-count query latency** — cache with 5-10s TTL to avoid per-evaluation round-trip.
- **Backfill scenario** — if the bot restarts mid-day with 3 open positions and the dormant marker is missing, must correctly read MT5 state on startup. Test this.
- **Daily-loss MTM measurement during open positions** — requires poll of unrealized P&L; budget for one extra MT5 call per M15 cycle.

**Approval:** CEO pre-approved the design (session 33). Implementation itself does NOT need re-approval unless you find a structural issue. If you do, stop and ask.

**Timebox:** 4-8h implementation + 2-4h testing. Aim to commit by Mon evening.

---

### Action 2 — sl_beyond_ob cross-instrument audit (RESEARCH, PARALLEL)

**Goal:** Before shipping the `verification.py:522/536` `<`→`<=` fix, audit whether the 42 bit-exact LONG pattern on NAS100 also exists on XAUUSD historical.

**Data sources:**
- XAUUSD 367-trade batch KB at `knowledge_base/trades/` (see `scripts/run_batch_sim.py` for the reading pattern).
- XAUUSD Test A rerun data (see `.context/03_analysis/` for file refs).
- Optionally: XAUUSD T7 simulation at `research/t7_live_simulation/XAUUSD_t7_simulation.json` (existing).

**Questions to answer:**
1. What % of XAUUSD L2 rejects have `l2_reason == "sl_beyond_ob"` with SL bit-exact to OB bound?
2. Direction skew (LONG vs SHORT) on XAUUSD — does the NAS100 44/46 LONG asymmetry replicate?
3. Counterfactual WR on XAUUSD if the gate were `<=` instead of `<`.
4. Is `sl_buffer_applied: 0.0` universal across XAUUSD records too?
5. If the pattern replicates cross-instrument, it's a global prompt/gate bug. If NAS100-only, it may be instrument-specific and warrant a prompt-level fix instead.

**Deliverable:** `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md` — numerical answers + recommended fix path (gate vs prompt).

**Approval:** No approval needed — research, $0.

**Parallelize:** Yes. Can run alongside Action 1.

---

### Action 3 — D1-bias-lag shadow logger (ADDITIVE, PARALLEL)

**Goal:** Detect when D1 bias contradicts H4+H1 for ≥N candles during a regime inflection (the W14 pattern: 54/54 bearish while +4.20% rally).

**Design:**
- New file: `src/components/d1_bias_lag_logger.py`.
- Called from `orchestrator.py` after MSO build, before AI call.
- Inputs: current MSO (h1_direction, h4 bias if available, d1 bias).
- Log condition: `d1_bias != h1_direction AND d1_bias != h4_bias` (both agree against D1).
- Log to `shadow_logs/d1_bias_lag.jsonl` with: timestamp, symbol, d1_bias, h4_bias, h1_direction, kill_zone, rolling_N_consecutive.
- Alert (Telegram) when consecutive count crosses threshold (e.g., N=20 candles = ~5h of M15).
- Config: `d1_bias_lag_logger.enabled: true`, `alert_threshold_consecutive: 20`.
- Tests: `tests/test_d1_bias_lag_logger.py`.

**Approval:** No approval (additive, log-only per CLAUDE.md "Allowed without approval").

**Parallelize:** Yes.

---

### Action 4 — EURUSD analysis (RESEARCH, PARALLEL)

**Goal:** Apply the same 4-agent + review + chairman pipeline used for NAS100 to EURUSD.

**Inputs:**
- `research/t7_live_simulation/EURUSD_t7_simulation.json` (4.3 MB, complete).
- `data/historical_2026/EURUSD_M15.csv`, `EURUSD_D1.csv` for CSV replay.

**Pipeline:** Same A/B/C/D/E agent briefs as used for NAS100 (see session 33 git log for agent prompts — re-use them with s/NAS100/EURUSD/g).

**Deliverable:** `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_T3_1_synthesis.md` + 5 agent files (A/B/C/D/E).

**Cost:** ~$4 in Opus-4.7 agent runs (4 analysis + 1 review). Get CEO cost-approval before firing.

**Expected outcome:** Cross-check if the 2 NAS100 leaks (sl_beyond_ob bit-exact + max_kz_trades) replicate on a currency instrument.

**Approval:** CEO cost-approval ($4).

**Parallelize:** Yes — independent of Actions 1-3.

---

### Action 5 — Rolling restart for model migration (OPERATIONAL, BLOCKING)

**Goal:** Make the `b298e2a` M5 refinement + devils_advocate model migration take effect in live processes.

**Procedure:**
1. Verify each of the 5 instrument processes is running: `python scripts/watchdog_e2e_verify.py`.
2. Pick ONE instrument; stop its process gracefully (e.g., XAUUSD first).
3. Restart: `python run_agent.py --mode live --symbol XAUUSD`.
4. Watch `logs/xauusd.log` for pipeline heartbeat recovery (first M15 cycle completes without errors).
5. Confirm Telegram "startup" alert received.
6. Repeat for US30, USDJPY, GBPJPY, GBPUSD sequentially. **Do NOT restart all at once** — if the migration has any hidden bug, a rolling restart lets you catch it on instrument 1 before impacting all 5.
7. Confirm via Anthropic usage dashboard that subsequent M5 refinement + DA calls are showing `claude-sonnet-4-6` instead of `claude-sonnet-4-20250514`.

**Validation caveat:** The T5 M5-refinement measured +0.81R lift was on the OLD model. Schedule a re-validation on the next KB slice if ANY degradation appears — this is NOT blocking the restart, just a known unknown.

**Approval:** Operational — no CEO approval needed, but CEO should be Telegram-notified before each restart.

**Blocking?** Yes — must complete before Tue Apr 21 kickoff so the challenge runs on the correct model.

**Timebox:** 30 min total across all 5 instruments.

---

## DISPATCH PLAN

**Serial (blocking):** Action 5 before kickoff.
**Parallel worktrees (agent dispatch):**
- Worktree A: Action 1 (risk architecture implementation — largest, most risky).
- Worktree B: Action 2 (sl_beyond_ob audit — research, $0).
- Worktree C: Action 3 (D1-bias-lag logger — additive).
- Worktree D: Action 4 (EURUSD analysis — $4, CEO-approve first).

All 4 worktrees can run simultaneously. Use `isolation: "worktree"` on Agent tool. Main thread stays in orchestration + review.

---

## CLOSING ACTIONS

After all 5 actions land:
1. Regenerate `LIVE_STATE.md` (`python scripts/generate_live_state.py`).
2. Update CLAUDE.md "What is working" / "What is unresolved" as needed.
3. Update `.context/backlog_synthesis_2026-04-18/00_MASTER_BACKLOG.md` — mark T2.8 + T3.1 CLOSED.
4. Write session 34 close handoff.
5. **CEO: consider pushing to `origin/main` before Apr 21 kickoff.** 22+ commits ahead after this session.

---

_Prompt author: Claude Code, session 33 main thread, 2026-04-19 evening._
