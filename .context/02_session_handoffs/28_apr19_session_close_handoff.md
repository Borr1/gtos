# Session 28 Close Handoff — 2026-04-19

**Session focus:** Close remaining T0 items (T0.2 Gate 0 deployment phase enforcement, T0.3 stale-line sweep + ADR 004 closure, T0.6 watchdog e2e verifier, T0.4 R078 verification); T1.2 closed-operational (Anthropic billing auto-reload disabled = hard cap).

---

## First actions for the fresh session

1. Read `CLAUDE.md`.
2. Run `python scripts/generate_live_state.py` → read `.context/LIVE_STATE.md` (authoritative current state).
3. Read this file for session 28 delta + outstanding T1 / doc-sweep directives.
4. Wait for CEO direction before touching files.

**Trust rule (unchanged):** if any handoff/backlog/ADR disagrees with `LIVE_STATE.md` or `git log`, the code/git is correct and the doc is stale — update the doc in the same commit.

---

## What session 28 shipped (3 commits, all local, NOT pushed — repo now 28 commits ahead of `origin/main`)

| SHA | Scope |
|-----|-------|
| `3005a83` | docs(t0.3): stale-line sweep + ADR 004 CLOSED-OPTION-C closure |
| `fa94b96` | tools(watchdog): end-to-end integration verifier (T0.6) — `scripts/watchdog_e2e_verify.py` 1031 lines, 4 integration checks, weekend + dead-zone leniency, 46 tests + 1 Windows-skip |
| `4944794` | feat(permissions): enforce deployment.phase gate (Gate 0, T0.2/Q014) — config `phase: 2→3`, new `_reject_if_deployment_phase_blocked`, autouse conftest shim, 6 new tests + ordering test vs Gate 3 |

Do not push without CEO approval.

---

## T0 status after session 28 — ALL CLOSED

| Item | Status | Closure evidence |
|------|--------|------------------|
| T0.1 "Revert Impl-A" | CLOSED (session 26 revert + session 27 config = ADR 004 Option C de-facto) | ADR 004 header now `CLOSED-OPTION-C-DE-FACTO` + §9 closure note |
| T0.2 `deployment.phase` enforcement (Q014) | CLOSED | Config `phase: 3` (live_micro), Gate 0 in `permissions.py::_reject_if_deployment_phase_blocked` (line 50), wired as FIRST gate in `check_permissions`, 6 tests + 1 ordering test |
| T0.3 Stale-line sweep | CLOSED | CLAUDE.md date + stale claims updated; ADR 004 header closed; master backlog update deferred to fresh-session doc sweep (see below) |
| T0.4 R078 verification | CLOSED | `src/components/execution.py:584-593` — `self.pending_intent = None` fires ONLY after successful `open_trade()`. No destruction-before-order. Remove from "open" lists on next doc sweep. |
| T0.6 Watchdog e2e verifier | CLOSED | `scripts/watchdog_e2e_verify.py` — read-only offline-capable audit tool. 4 integration checks (OB continuation, API refusal, canary cache, redacted_account profile) with ABSENT/STALE/MALFORMED distinction. Weekend leniency Fri 17:15 UTC → Sun 21:00 UTC (aligned to `watchdog.ps1:7-12`). Dead-zone leniency 01:15-07:45 local. Exit codes 0=PASS/WARN, 1=FAIL, 2=script-error. 46 tests pass + 1 Windows-skip. |

**Gate 0 gap to note:** `phase=2` (log-only) currently behaves identically to `phase=1` (block) because the orchestrator has no divert path. Documented in Gate 0 docstring as T1 follow-up. Production runs at `phase=3` (live_micro) — correct behavior preserved.

---

## T1 status

| Item | Status | Notes |
|------|--------|-------|
| T1.1 Heartbeat-flatten kill switch | **OPEN — approved 2026-04-19, dispatch deferred to fresh session** | MEDIUM size, HIGH risk (touches live position management). Full spec in §T1.1 below. |
| T1.2 Prepaid card cap | **CLOSED-OPERATIONAL** | Anthropic billing auto-reload DISABLED by CEO. Balance $50-60 IS the hard cap (stronger than any software enforcement — system fails closed when balance exhausts). No prepaid-card code work needed. Memory: `project_anthropic_billing_auto_reload_disabled.md`. |
| T1.3 Borderline canary fixtures | **OPEN — approved 2026-04-19, dispatch deferred to fresh session** | LOW risk, ~2h + ~$10 API. Full spec in §T1.3 below. |

---

## §T1.1 Heartbeat-flatten kill switch — dispatch spec

**Motivation:** Apr 16 silent sleep-TOCTOU crash left an XAUUSD position open without monitoring; trailing stop never moved → -1R. Watchdog.ps1 restarts the main process but does NOT close orphan positions. Closes the gap.

**Module:** `src/safety/heartbeat_monitor.py` (+ empty `src/safety/__init__.py`)

**Mechanics:**
- Main orchestrator writes `pipeline_state/heartbeat.json` with UTC timestamp every 30s (config-driven)
- Monitor runs as a separate watchdog-launched process, checks heartbeat every 30s
- 3 consecutive misses (heartbeat ≥ 90s stale) → TRIGGER candidate
- 3 consecutive trigger candidates (full 90s grace, ~180s total) → flatten sequence
- Market-hours gate: only flatten inside any instrument's active kill zone (per CLAUDE.md schedule)
- Telegram pre-flatten alert with 30s countdown + CANCEL reply listener
- MT5 `close_position` per open position, magic comment `heartbeat_flatten`, retry 3x with 5s backoff on failure
- Events logged to `shadow_logs/heartbeat_flatten_events.jsonl`
- Telegram throttle: no re-alert within 60 min

**Config additions (default DISABLED):**
- `heartbeat.flatten_enabled: false`
- `heartbeat.write_interval_seconds: 30`
- `heartbeat.miss_threshold: 3`
- `heartbeat.telegram_countdown_seconds: 30`

When `flatten_enabled: false`: monitor runs in log-only mode (records triggers, no action).

**Tests (10-15 in `tests/test_heartbeat_monitor.py`):** fresh heartbeat, 1/2 misses no-trigger, 3 misses trigger, 3× trigger → flatten (when enabled), counter reset on success, outside KZ → log-only, feature-off → log-only, MT5 failure retry 3×, Telegram CANCEL aborts, throttle blocks second alarm, missing/malformed heartbeat file treated as miss. Follow session 21 canon (`tmp_path` + module-ref monkeypatch).

**Watchdog integration:** Add heartbeat_monitor.py launch to `scripts/watchdog.ps1` as independent child (persists across main process restarts).

**Constraint:** Ship DISABLED. CEO enables after live validation.

**Dispatch pattern:** Single Opus 4.7 impl agent (max effort) + single Opus 4.7 cold-review agent. Do NOT use council — scope is well-defined.

---

## §T1.3 Borderline canary fixtures — dispatch spec

**Motivation:** Current 10 fixtures in `scripts/canary_fixtures/` all return NO_TRADE. Blind to drift in either direction — if the system becomes MORE aggressive (borderline setups start approving) or MORE conservative (easy wins stop approving), current canaries can't detect it.

**Goal:** Add 3-4 borderline MSO fixtures targeting the CANDIDATE threshold.

**Selection criteria:**
- Mix borderline-CANDIDATE (barely passed) and borderline-NO_TRADE (barely failed)
- Multi-symbol preference (not all XAUUSD), multi-session (London/NY/Tokyo)
- Source preference: real MSOs from `shadow_logs/candidate_features_log.jsonl`, `pipeline_state/` archives, or `research/t7_live_simulation/` outputs
- Last resort: synthesized (clearly labeled with rationale)

**Naming:** `borderline_{symbol}_{YYYYMMDDTHHMM}_{disposition}.json` (e.g., `borderline_xauusd_20260118T0815_candidate.json`)

**Schema:** Match existing fixture JSON structure exactly. Include expected output field.

**Re-baseline:** Run canary runner across all fixtures (existing + new), capture new baseline hashes, confirm stability across 3 consecutive runs OR via canary cache idempotency check (session 23 `0c26d25`).

**Budget:** ~$10 API (hard cap $15). Sonnet-4-6 at effort=max to match production.

**Deliverables:** new JSON fixtures + updated baseline + `scripts/canary_fixtures/README_borderline.md` (short — what each targets and why borderline) + brief impl report.

**Constraint:** Additive only. Do NOT remove existing fixtures or modify canary runner.

**Dispatch pattern:** Single Opus 4.7 impl agent (max effort) + single Opus 4.7 cold-review agent.

---

## Doc sweep directive — fresh session

Master backlog (`.context/backlog_synthesis_2026-04-18/00_MASTER_BACKLOG.md`) is frozen at session 27 and does NOT reflect session-28 commits. Also CLAUDE.md "What is unresolved" still lists items that are now closed.

**Fresh-session workflow:**
1. Read this handoff + regenerate LIVE_STATE.md
2. Update master backlog: mark T0.1, T0.2, T0.3, T0.4, T0.6, T1.2 as CLOSED with commit SHAs + date
3. Update CLAUDE.md "What is unresolved" section: strike R078, Q014 (both closed); keep GBPUSD macro, MT5 TZ bug, batch simulations, canary freshness (pending T1.3)
4. After T1.1 + T1.3 ship in the fresh session: add those closures to the same doc sweep (consolidated commit)
5. Commit as `docs(backlog): session-28 closures + T1.1/T1.3 results`

---

## Known open items (last swept 2026-04-19 — re-verify via LIVE_STATE.md before acting)

1. **GBPUSD XAUUSD macro override** — partial fix `bf57d90` (strip XAUUSD D1 context). Verify gap closed in fresh session.
2. **Batch simulations for remaining 4 instruments** — ~$120.58 total, script ready, CEO decision pending.
3. **Canary fixtures stale** — addressed by T1.3 when dispatched.
4. **MT5 timezone bug** — `fromtimestamp()` without UTC in `mt5_real.py`, latent on UTC machines.
5. **Quantlabs P0 folds still valid** (beyond T1.1):
   - Per-symbol no-data alert (S, $0/mo)
   - Correlation-shock Telegram alert (S, $0/mo)
   - Time-in-trade shadow logger (S, $0/mo)
   - Weekly AI-reasoned skipped-trades summary (S, ~$2/mo)

---

## redacted_account kickoff

Tuesday 2026-04-21 — Stellar 2-Step $100K @ 1% risk. Profile `config/profiles/redacted_account.yaml` + watchdog `--profile redacted_account` hook both present and validated by session-28 verifier (`fa94b96`). No code changes required pre-kickoff.

---

## Memory updates this session

- Saved: `project_anthropic_billing_auto_reload_disabled.md` — billing auto-reload disabled, $50-60 balance IS the hard cap (T1.2 closed-operational). MEMORY.md pointer added.

---

## How to start the fresh session

1. Close this Claude Code session (or type `/clear` if available in your CLI).
2. Open a fresh Claude Code session in `C:\Users\MSI\Documents\ai-trading-agent`.
3. The fresh session will auto-read `CLAUDE.md` and execute its MANDATORY FIRST ACTION protocol (regenerate `LIVE_STATE.md`, read this handoff).
4. First message to the fresh session:
   > "Run the doc sweep per session-28 handoff, then dispatch T1.3 and T1.1 as parallel Opus 4.7 max-effort agents (specs in the handoff). Both approved. Report back when both complete + reviewed."

Signed: session 28 close.
