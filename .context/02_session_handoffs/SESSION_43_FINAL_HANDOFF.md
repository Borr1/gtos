# Session 43 Final Handoff — Session 44 Starter

**Closed:** 2026-04-27 ~22:30 UTC (Mon end-of-day)
**Successor session:** Session 44 — execute J46-J49 ship + side-aware flag
**HEAD on main:** `9af92e8` (after this commit will be `<this commit SHA>`)

---

## MANDATORY FIRST ACTION (do BEFORE anything else)

1. Read `CLAUDE.md` (already updated by session 43 close)
2. Regenerate + read `.context/LIVE_STATE.md`:
   ```
   python scripts/generate_live_state.py
   ```
3. Read `.context/02_session_handoffs/SESSION_43_PHASE_1_SYNTHESIS.md` (8 sections, ~7.9k words — Phase 1 closeout)
4. Read `research/phase_1_verification_audit_2026-04-27/AUDIT_REPORT.md` (verification verdict + readiness)
5. Read `.context/00_core/quick_reference_card.md`
6. Confirm production state: `bash monitor.sh` should show 7 alive (post-08:01 KL auto-restart) OR all dead if pre-restart

---

## Context (HEAD `9af92e8` at session 43 close)

**Phase 1 COMPLETE — 47/47 tasks, 0 lost, all CEO-approved fixes shipped to main.**

Tomorrow's 08:01 KL auto-restart picks up:
- HALLUC-1 precision fix + 4 sister-bug fixes (m5_refinement.py + verification.py FVG/breaker)
- S79 risk policy raise (FN base 1.0%→2.0%, XAU/XAG 1.0%, US30 2.0%, NAS100 HELD 0.25%)
- Windows OS RCA file-lock canary (eliminates 6-orchestrator KZ stampede)
- Cache TTL 5m→1h
- heartbeat-flatten enabled
- equity guard (bug #25)
- timeout-retry off
- staggered orchestrator startup
- Q71 + HALLUC-2 observability loggers
- Bug #24 fn_smoke false-close fix

**Validation-hardening agent** (worktree `agent-af31d4d740e9ad84f`, branch `feat/research-validation-hardening-j4649-sideaware`, commit `124de56`) confirmed both pending policies via M1+bootstrap+walk-forward+slippage stress tests:

- **J46-J49 portfolio policy: SHIP-NOW** (4/4 stress tests passed; M1 preserves +0.742R; H2-OOS amplifies to +1.16R; slippage-adjusted CI lower +0.862R; P(delta≤0)=0.0000)
- **Side-aware sizing: SHIP-WITH-FLAG** (4/5 gates; bootstrap PnL CI95 lower -$3.6k requires flag-default-OFF + 30d shadow validation)
- **K55 ML gate: NOT NOW** (YELLOW — model can't discriminate, GBPJPY actively harmed; revisit after 200 AI-emitted SHORT trades accumulate)

**Expected post-J46-J49 monthly P&L: $22-28k (mid-range conservative on $100k FN account = 22-28% monthly).** Updated FN payout timeline: Phase 1 in ~10-12 days, Phase 2 in ~6-8 days, first payout 30-46 days from go-live.

---

## Your immediate work — IN ORDER

### 1. Ship J46-J49 to production (P0)

Wire winning policy from validation-hardening:
- **J46:** partial close ratio at TP1 = **0%** (let position run to higher target)
- **J47:** BE trigger = **immediate-on-TP1 BE pull**
- **J48:** time stop = close at market after **12 M15 bars (3h)**
- **J49:** TP1 distance = **3.0R**

Implementation steps:
- Read existing position-mgmt code in `src/components/execution.py` (close logic, BE pull, partial close)
- Read the original sweep module at branch `feat/research-j46-j49-position-mgmt-sweep-v2`:`src/research_infra/j46_j49_position_mgmt.py` (commit `be33522`) for reference
- Add `position_mgmt.j46_j49_v2.enabled: true` to `config/agent_config.yaml` (default ON)
- Wire the policy into `_finalize_exit` / `_pull_to_be` / `_partial_close` paths (depending on architecture)
- Add 2-3 canary fixtures exercising: same-bar SL+TP collision, 12-bar timeout exit, 3.0R TP1 hit-and-BE
- Add tests in `tests/test_j46_j49_policy.py`
- Branch: `feat/ship-j46-j49-policy`
- pytest must pass full suite (target ≥3811)
- Merge to main with --no-ff

**Note on the J46-J49 SHADOW LOGGER (already merged from session 43):**
After this ship, swap the framing in `src/components/j46_j49_shadow_logger.py` so it logs "actual = new policy, hypothetical = OLD policy". That gives the regression-detection signal in case the new policy underperforms in live data.

### 2. Side-aware sizing flag infrastructure (P1)

Wire side-aware sizing per validation-hardening + side-aware-replay outputs:
- LONG positions: multiply `risk_per_trade_pct` by 0.5
- SHORT positions: multiply `risk_per_trade_pct` by 1.0 (no change)
- Add `risk.side_aware_sizing.enabled: false` to `config/agent_config.yaml` (DEFAULT OFF)
- Add LONG-WR-watch SPRT auto-revert: if LONG live WR < 50% over 20 trades, force-disable flag (per CLAUDE.md item #5)
- Tests in `tests/test_side_aware_sizing.py`
- Branch: `feat/ship-side-aware-sizing-flag`
- Merge to main with --no-ff

CEO will manually flip the flag ON after observing 30d of shadow data confirms regime continues.

### 3. Verify auto-restart picks up new code

Tomorrow's 08:01 KL auto-restart fires `start_all.bat`. Verify by:
- Confirming HEAD is post-merge of both branches
- Pytest sanity: `pytest tests/test_j46_j49_policy.py tests/test_side_aware_sizing.py -v`
- Canary: `python scripts/canary_test.py --quick` (if available)
- Confirm `config/agent_config.yaml` has `position_mgmt.j46_j49_v2.enabled: true` AND `risk.side_aware_sizing.enabled: false`

### 4. Anthropic balance topup (CEO action — track but don't block on it)

CEO needs to top-up to $200-300 prepaid. At post-fix steady state ~$10-15/day, $50 buys 3-5 days. Plus Phase 2 tasks (when authorized) need $200-700 more. **Don't dispatch any API-cost agents until CEO confirms top-up.**

---

## Critical DO-NOTs

- **DO NOT enable side-aware default ON** — only the flag infrastructure ships; CEO controls the flip
- **DO NOT modify production trading logic outside J46-J49 + side-aware scope** — no other behavior changes
- **DO NOT touch the live orchestrators directly** — they self-restart at 08:01 KL with new code
- **DO NOT dispatch Phase 2 API-cost agents** until CEO authorizes Anthropic balance topup
- **DO NOT delete any branches** (per CLAUDE.md retention)
- **DO NOT modify K55-retrospective verdict** — it's YELLOW / not-now, revisit when more SHORT data accumulates
- **DO NOT push to remote** without explicit CEO approval

---

## Phase 2 task ordering (FOR LATER — after J46-J49 ships + ~1 week live data)

These are **NOT needed before going live**. They inform Week 2+ decisions and require API budget.

| Rank | Task | Cost | Why valuable | Computable? |
|---|---|---|---|---|
| 1 | A4 AI-on-historical-CANDs replay (trending_bull cohort) | $40-90 | Confirms HALLUC-1+S79+sister fixes RECOVERED the H2 decay (definitive evidence) | API-required (re-run current prompt on historical setups) |
| 2 | F27 backward outcome injection prototype | $25-50 | Tests if AI improves from past trade outcomes. HUGE if works (+0.1-0.3R/trade potential) | API-required (modifies AI prompt to include past outcomes) |
| 3 | C19 v2 detector full 2-year BT | $40-80 | Quantifies SHORT signal recovery — sharpens side-aware ship confidence | API-required (full backtest with v2 detector emitting SHORT signals) |
| 4 | D21 per-framework forced-evaluation | $100-150 | Settles breaker_re_entry retire OR fvg_fill keep decisions at scale | API-required (force AI to single framework, observe per-class realized R) |
| 5 | F28 feedback granularity sweep (only if F27 positive) | $100-200 | Optimal feedback schema | API-required |

**ALL Phase 2 tasks require API budget.** All compute-only Phase 2 candidates were closed in session 43 (K55-retrospective, validation-hardening, sister-bug fixes, observability loggers, K54 baseline).

**Recommended Phase 2 minimal set: A4 + F27 = $65-140 total.** Validates current state + tests one big new edge. Skip everything else unless A4/F27 surface a need.

---

## Timeline reference

- **Today (Mon 2026-04-27):** session 43 closed; HEAD `9af92e8`
- **Tomorrow (Tue 2026-04-28) 08:01 KL:** auto-restart with new code IF you ship J46-J49 + side-aware tonight
- **Tue+Wed+Thu+Fri:** J46-J49 live, accumulating shadow data
- **Day 30 (~2026-05-27):** evaluate side-aware shadow + decide flag flip
- **Phase 2 dispatch:** when CEO authorizes API budget topup

---

## Reference branches (do NOT delete; sources for ship work)

- `feat/research-validation-hardening-j4649-sideaware` (commit `124de56`) — validation reports + ship plans
- `feat/research-j46-j49-position-mgmt-sweep-v2` (commit `be33522`) — original J46-J49 sweep + module
- `feat/research-side-aware-sizing-replay` (commit `4da4266`) — original side-aware sweep + integration sketch
- `feat/j46-j49-shadow-logger-v2` (commit `6fc2690`) — already MERGED to main; shadow logger wired into `_finalize_exit`
- `feat/research-k55-retrospective-ml-vs-ai` (commit `dd6a855`) — K55 retro YELLOW verdict + per-cohort table
- `feat/research-k54-ml-classifier-baseline` (commit `af5d97e`) — K54 model + scripts
- `feat/research-m1-backfill-microstructure-rerun` (commit `f9931ee`) — M1 OHLCV data (3.5 months × 7 instruments)
- `feat/research-windows-os-stall-rca` (commit `0066f28`) — RCA forensic report

---

## Engineering principles (reminder)

- Engineer systemic, not patch
- Walk-level evidence ≠ realized R
- Decay is CEO #1 concern
- Live system safety > research velocity (don't disturb production for any reason)
- All dispatched agents: Opus 4.7 max effort
- Keep CLAUDE.md ≤30k chars

---

## What's already on main (verified at session 43 close)

| Layer | Commits | Status |
|---|---|---|
| Day-1 ops | `de1bb1f` + `6eaeaa2` | bug #25 + API efficiency safety branch |
| HALLUC-1 class | `2da9be3` + `f1dba2a` | NAS100 unblock + 4 sister bugs fixed |
| S79 risk | `9549928` | uniform_fn 2.0% (NAS100 HELD 0.25%) |
| Windows OS RCA | `32b062b` | file-lock canary |
| Observability | `8666298` + `5d6c944` + `303768f` | Q71 + HALLUC-2 + bug #24 |
| Test alignment | `82d2368` | stale fixtures aligned |
| Docs | `3990732` + `9af92e8` | synthesis + monitor.sh + memory + CLAUDE.md |
| **This handoff** | _next commit_ | LIVE_STATE regen + handoff doc + research artifacts |

---

*Session 43 close. 2026-04-27 ~22:30 UTC. Next: ship J46-J49 + side-aware flag, go live Tuesday morning.*
