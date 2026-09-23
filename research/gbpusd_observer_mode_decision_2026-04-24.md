# GBPUSD Observer-Mode Formalization — Decision Document

**Date:** 2026-04-24
**Author:** Claude Code (Opus 4.7)
**Status:** IMPLEMENTED — awaiting CEO review before merge
**Branch:** `worktree-agent-ad0a9ebd`

---

## Current state (pre-fix)

- GBPUSD runs the full pipeline (Components 1-8) as one of five live
  orchestrators, just like XAUUSD, US30, USDJPY, GBPJPY.
- Under the redacted_account profile it uses `risk_per_trade_pct: 1.0%` (same as
  the other three non-XAUUSD fleet instruments; XAUUSD is overridden to
  0.5%).
- "Observer" exists only as a label in comments and handoffs —
  `src/components/sprt_monitor.py:38`, CLAUDE.md "What is working", memory
  note `project_gbpusd_observer_cost.md`. The code path from CANDIDATE to
  `mt5.order_send` is identical to the live instruments.
- Thursday 2026-04-23 audit
  (`research/thursday_2026-04-23_analysis/GBPUSD_analysis.md`) observed the
  gap: **the only thing preventing GBPUSD from placing a trade today is the
  pre-AI h1_poi_availability gate, which is a cost governor, not a safety
  barrier.** If MSO ever contains an unmitigated H1 OB and the AI grades a
  setup A+ inside it, the trade fills. The Thursday audit also flagged a
  63.6% L2 `sl_beyond_ob` reject rate for GBPUSD in the measurement window —
  the underlying AI precision issue is FA-2 prompt-driven and already fixed,
  but the non-code "observer" label meant nobody noticed that it mattered for
  live-fill risk.

## Post-fix state

- Config schema: `instruments.<SYMBOL>.trading_enabled: bool` in
  `config/agent_config.yaml`. Default **true** if missing (non-breaking for
  any instrument config that lacks the key).
- New gate: `permissions._reject_if_trading_disabled` runs as **Gate 0.5**
  between Gate 0 (`deployment.phase`) and Gate 3 (circuit breakers).
- `instruments.GBPUSD.trading_enabled: false` — formalizes the observer-only
  state. XAUUSD / US30_cash / USDJPY / GBPJPY are all explicitly
  `trading_enabled: true`.
- Gate fires at INFO level: `"GBPUSD trade blocked by observer-mode flag
  (trading_enabled=false)"`. Rejection carries `gate="gate0_5_trading_enabled"`,
  `reason="trading_disabled_for_instrument:GBPUSD"`. This lets dashboards
  distinguish the observer block from a real L2/L3 gate reject.
- Pipeline still runs: L2 evaluation, shadow logging, CAND-rate monitor,
  proximity logs, cost governor all continue to accumulate data. Only the
  `mt5.order_send` path is severed.
- Smoke verified 2026-04-24 against real `config/agent_config.yaml` +
  `config/profiles/redacted_account.yaml`: loader produces
  `config["trading_enabled"] = False` for GBPUSD, `True` for the other four.
  Gate returns `ExecutionDenial(gate="gate0_5_trading_enabled", ...)` on an
  otherwise-passing A+ CANDIDATE.

## Remaining blockers for promoting GBPUSD to live

1. **FA-2 FX precision leak** — 63.6% L2-reject on `sl_beyond_ob` (Thursday
   GBPUSD audit). The FA-2 prompt fix (`fa35cc0`) added sl_buffer_applied
   non-zero enforcement; the follow-on T2.prompt.v2 should land before any
   flip.
2. **Post-v2 empirical validation** — ≥20 CANDIDATEs under the updated
   prompt, <20% L2-reject rate, ≥30% CAND rate sustained over a rolling
   window.
3. **CEO end-of-April review** — per memory note
   `project_gbpusd_observer_cost.md`. The $10/mo observer cost is accepted
   through April; reassess then.

## Decision

Implement **Option A (safety-first flag)** this cycle. Keep
`trading_enabled: false` on GBPUSD until all three blockers above clear.

### Why this option

- **Minimally invasive.** One permissions function, one config schema key,
  six tests. Existing gate ordering preserved; Gate 0 fail-closed semantics
  untouched; no changes to orchestrator, execution, market state, or any
  shadow logger.
- **Reversible.** Promoting GBPUSD to live is a one-line config flip
  (`trading_enabled: false` → `true`). Gate stays in place for future
  observer needs (e.g. when a new instrument is added in shadow).
- **Testable.** Six new tests cover allow, block, default-true, ordering
  (Gate 0.5 before 1/3), Gate 0 still wins, and the config-loader
  flattening contract. Full suite stays green (1838 pass, 1 pre-existing
  flaky time-based test unrelated to this change).

## Trade-offs considered

- **Disable the GBPUSD orchestrator process entirely** → stops the ~$10/mo
  API cost outright.
  - Rejected: CEO explicitly wants observation data continuing per memory
    note `project_gbpusd_observer_cost.md`. Killing the process kills the
    proximity/displacement/candidate-feature shadow streams that feed the
    GBPUSD validation case.
- **Gate earlier — e.g. skip the Component 3 AI call if `trading_enabled:
  false`.**
  - Rejected: that collapses "observer" into "cost governor", which is what
    the pre-AI `h1_poi_availability_enabled` gate already does. The point
    of this change is to add a dedicated safety barrier AT the execution
    boundary, not another throttle earlier in the pipeline. The two should
    coexist — cost governor saves money, `trading_enabled` saves a bad
    fill.
- **Gate at the `execution.place_order` call site instead of in
  `permissions.py`.**
  - Rejected: permissions.py is the single funnel for every order path.
    Putting the gate further down the call chain makes it easier to bypass
    (e.g. a future code path that builds an order without going through
    permissions). Gate where the other safety gates already live.
- **Put the flag in `redacted_account.yaml` instead of `agent_config.yaml`.**
  - Rejected: observer mode is a **global** decision about this instrument,
    not a redacted_account-specific one. If the CEO ever tests under FTMO or any
    other profile, GBPUSD should stay blocked until promoted. The profile
    overlay can still override if a profile-specific observer policy is
    ever needed (deep-merge semantics are preserved).

## Follow-up

- When CEO approves promotion: flip `instruments.GBPUSD.trading_enabled` to
  `true` in `config/agent_config.yaml` (+ CEO-review diff). The safety gate
  stays in place for future observer needs.
- The `sprt_monitor.py:38` comment referencing "observer-only" can stay —
  it's now descriptive of the config-enforced state, not a half-truth.
- When the next observer-mode instrument is added (e.g. a NAS100 shadow
  rollout), explicitly set `trading_enabled: false` in its instruments
  block. Relying on the `true` default is fine for live-from-day-one
  instruments but risky for shadow-first rollouts.

## Evidence trail

- **Audit that surfaced the issue:**
  `research/thursday_2026-04-23_analysis/GBPUSD_analysis.md`
- **Commit(s):**
  - Commit A (code + config + tests): `feat(safety): per-instrument
    trading_enabled gate (Gate 0.5)`
  - Commit B (this doc): `docs(gbpusd): observer-mode decision document`
- **Test results:** `pytest tests/test_permissions.py -v` →
  60/60 pass (6 new). Full suite: 1838 pass / 1 pre-existing flaky skip /
  2 skipped / 0 new failures.
- **Smoke run (2026-04-24):** GBPUSD under redacted_account profile with an A+
  bullish CANDIDATE returns `ExecutionDenial(gate="gate0_5_trading_enabled",
  reason="trading_disabled_for_instrument:GBPUSD")` at the permissions
  layer. XAUUSD same CANDIDATE returns `None` (passes). Log line:
  `INFO src.components.permissions: GBPUSD trade blocked by observer-mode
  flag (trading_enabled=false)`.
