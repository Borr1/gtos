# M1b — Per-Branch Decision Invariance Replay

**Reviewer:** Opus 4.7 max effort, read-only replay
**Date:** 2026-04-24
**Data window:** 2026-03-24 to 2026-04-22 (30 days ending day-before Thursday)
**Source:** `knowledge_base/live_evaluations/*/*.jsonl` (+ `shadow_logs/candidate_features_log.jsonl` for MSO context)
**Row count:** 1,231 eval rows across 5 instruments (132 CANDIDATE, 1,099 NO_TRADE)
**Symbols:** GBPJPY 285, GBPUSD 154, US30_cash 238, USDJPY 335, XAUUSD 219

| Branch | Label | Verdict | Flips | Notes |
|---|---|---|---|---|
| A1 `worktree-agent-a08c4676` | orchestrator bug bundle | **INVARIANT** | 0 | 40/40 tests; all 8 post-CAND `_log_candle` sites carry `produced_candidate=True` |
| A2 `worktree-agent-aa7f6346` | execution + verification | **INVARIANT** | 0 | 30/30 tests; choch invariance proven synthetically; displacement invariance holds by config coupling |
| A3 `worktree-agent-a97f76b5` | pre-AI gate formalization | **INVARIANT** | 0 | 19/19 tests; bit-exact vs live (CRLF-normalized); 8/8 synthetic gate cases; 139 gate emissions in live logs |
| A6 `worktree-agent-aa6fc1ba` | M5 SL clamp | **INVARIANT_WITH_CAVEAT** | 0 decisions; SL values may drift | 40/40 tests; clamp produces L2-compatible SL under production config (buffer > 0); edge-case flagged at buffer == 0 |
| A8 `worktree-agent-ad0a9ebd` | GBPUSD Gate 0.5 | **EXPECTED_BEHAVIOR** | 29 GBPUSD CAND → NO_TRADE (as designed) | 60/60 tests; non-GBPUSD CANDs unchanged (103/103) |

---

## A1 — orchestrator bug bundle

**Branch:** `worktree-agent-a08c4676` (5 commits: `7106340`, `26a36a8`, `2a5a250`, `c028754`, `00bc3bb`)

### Methodology
Pure observability + lifecycle fixes; decision invariance trivially holds if branch tests pass.
1. Ran `pytest tests/test_bugfixes_0.py` in the branch worktree.
2. Scanned every `_log_candle` call site in the post-CANDIDATE block (lines 865-1090
   of `src/components/orchestrator.py`); confirmed each passes `produced_candidate=True`.

### Results
- **Tests:** 40/40 passed (rc=0).
- **Post-CANDIDATE `_log_candle` sites checked:** 8 (lines 879, 900, 936, 964, 988, 1016, 1040, 1086).
- **Sites with `produced_candidate=True`:** 8/8.

### Observability invariance
Confirmed. No trading-logic file touched (permissions.py, verification.py, execution.py unchanged vs main).

### Notes
- The 3 PRE-AI `_log_candle` calls at lines 623, 634, 642, 650, 688 (NO_TRADE /
  SKIP_NEWS_EVENT / BLOCKED_CALENDAR / deterministic_no_bias / pre_ai_gate) do NOT
  carry the flag because they logically cannot produce a CANDIDATE (AI hasn't run yet).
- Reproducibility artifact: `research/reviews_2026-04-24/m1b_replays/replay_a1.py`.

**Verdict: INVARIANT — 0 decision flips on historical data.**

---

## A2 — execution + verification

**Branch:** `worktree-agent-aa7f6346` (2 commits: `1b6ac3b` close-price fallback, `d749035` displacement reversed iteration)

### Methodology
1. Ran `pytest tests/test_verification.py` in branch worktree.
2. Synthetic invariance proof for `_check_m15_choch` — 8 scenarios covering
   empty/single/multi-event sequences, crossed directions, non-qualifying events.
3. Synthetic invariance proof for `_check_displacement_ratio` — 7 scenarios,
   including the theoretical canary where `displacement_present` but ratio-below-min.
4. Live-data scan of 1,231 eval rows in window.

### Results
- **Tests:** 30/30 passed (rc=0).
- **_check_m15_choch invariance:** 8/8 scenarios invariant; 0 verdict flips under iteration reversal.
- **_check_displacement_ratio invariance:** 6/7 scenarios invariant; 1 theoretical canary flip.

### Displacement canary analysis (the 1 "flip")
The canary scenario has `displacement_present=True` on two CHoCH events with ratios
(1.2, 2.0) and `min_ratio=1.5`. Forward iteration picks the first CHoCH (ratio=1.2 → FAIL);
reversed iteration picks the last CHoCH (ratio=2.0 → PASS). Verdict flips.

**This scenario is IMPOSSIBLE in production:**
- `src/components/market_state.py:318-320` hard-codes `disp_present = disp_ratio >= 1.5`.
- `config/agent_config.yaml:83` sets `displacement_min_ratio: 1.5`.
- Therefore every `displacement_present` event automatically satisfies the ratio check.
- Iteration order cannot flip verdict under this config coupling.

Live eval rows carry AI-reported displacement summaries, not L2's MSO structure_events
(eval fields come from `reasoning.m15_confirmation`, per `src/components/evaluation_logger.py:75-76`).
So the ~35 CAND rows with AI-reported ratio<1.5 are informational only; they do NOT
indicate L2-side invariance violations.

### Close-price fallback (commit `1b6ac3b`)
Non-AI-changing; adds a tick-price fallback when MT5 returns `result.price=0.0` on
close. Mirrors the existing fill-side fallback at `execution.py:417-425`. Verified
by inspection; no historical fixture replays this path.

**Verdict: INVARIANT — 0 decision flips; displacement invariance holds by config coupling.**

---

## A3 — pre-AI gate formalization

**Branch:** `worktree-agent-a97f76b5` (2 commits: `a84abde` direction-aware upgrade, `3da685b` watchdog drift check)

### Methodology
1. Byte-diff branch's `pre_ai_gates.py` vs main working tree (normalize CRLF/LF).
2. Ran `pytest tests/test_pre_ai_gates.py`.
3. Synthetic replay of gate function against 8 fabricated MSOs covering
   bullish/bearish/no-bias × unmit/mitigated OB × unretested/retested breakers.
4. Scanned eval rows for `pre_ai_gate:` reason strings + log files for emissions.

### Results
- **Byte-diff:** branch 3031 bytes (CRLF), main 2955 bytes (LF), normalized: IDENTICAL.
- **Tests:** 19/19 passed (rc=0).
- **Synthetic gate replay:** 8/8 cases match expected skip/reason.
- **Eval rows with `pre_ai_gate:` reason:** 0 (the gate fires pre-AI, and pre-A1-fix
  `log_candidate_features` was not called on the pre-AI-gate path — historical eval
  rows simply don't capture these events; they live only in `logs/*.log`).
- **Log emissions in branch window:** 139 total gate fires —
    - `no_unmitigated_h1_pois`: 48 (pre-direction-aware deploy, before Apr 22)
    - `no_unmitigated_bullish_h1_pois`: 91 (post Apr 22 direction-aware)
    - `no_unmitigated_bearish_h1_pois`: 0 (bearish bias never emitted in production; see V4 §1.4)

### Gate reason strings
All 139 emissions match the allowed set:
`{no_unmitigated_h1_pois, no_unmitigated_bullish_h1_pois, no_unmitigated_bearish_h1_pois}`.

Zero unexpected reasons.

**Verdict: INVARIANT — bit-exact with live code (text); 0 decision flips possible.**

Note: the "bit-exact with live code" claim from V4 §1.1 is confirmed once line endings
are normalized (branch has CRLF, main has LF). The semantic content is identical.

---

## A6 — M5 SL clamp

**Branch:** `worktree-agent-aa6fc1ba` (1 commit: `c3002fa`)

### Methodology
1. Ran `pytest tests/test_m5_refinement.py` in branch worktree.
2. Synthetic battery for `clamp_m5_sl_to_ob_boundary` — 8 scenarios covering:
    - LONG m5 already-below-OB (no-op pass-through)
    - LONG m5 inside OB with room to tighten (clamp applied)
    - LONG clamp not tighter than pre_m5_sl (feasible=False)
    - LONG OB boundary above entry (degenerate, feasible=False)
    - SHORT mirror of LONG
    - SHORT inside OB with room
    - LONG with buffer=0 (canary — clamp lands on boundary, L2 would FAIL)
    - matched_ob=None (legacy no-op)
3. Cross-check: for each feasible-clamp scenario, run the resulting SL through
   `verification._check_sl_beyond_ob`'s strict-`<` semantics.
4. Verified `verification.py:sl_beyond_ob` still uses strict-`<` (T2.9 rejected).
5. Scanned `candidate_features_log.jsonl` for CAND rows "at risk" of the clamp firing
   (unmitigated H1 OB present + nearest distance < 0.5 ATR).

### Results
- **Tests:** 40/40 passed (rc=0).
- **Clamp battery:** 8/8 scenarios match expected clamp/feasible verdicts.
- **L2 semantics unchanged:** strict-`<` present, no `<=` drift.
- **L2 failures after clamp:** 1 scenario — the buffer=0 edge case (clamped_sl == ob.low,
  strict `<` FAILs). Production config never reaches buffer=0 (multiplier=0.5 × positive M15_ATR).
- **Historical CAND classification in window:** 54 CAND rows in feature log.
    - By symbol: USDJPY 15, GBPUSD 15, XAUUSD 3, US30_cash 2, GBPJPY 19.
    - CAND with zero unmitigated H1 OBs (clamp cannot fire): 23.
    - CAND "at risk" for clamp (unmit OB + nearest < 0.5 ATR): 31.

### Decision invariance
Confirmed. Clamp only adjusts SL value; it does not reject CANDIDATEs (when
infeasible, it falls back to pre-M5 SL, which was the original primary analyzer
output → unchanged from current behavior).

### SL drift tracking
Historical eval rows and `candidate_features_log.jsonl` do NOT persist M5 refinement
output per-trade (`pipeline_state/m5_refinement.json` is overwritten each cycle), so
we cannot compute the exact % unchanged/clamped/infeasible on historical CANDs. What
we CAN say: 31 of 54 CANDs in the window had the geometric prerequisites for the
clamp to potentially fire (unmitigated OB + close proximity). Whether M5 actually
proposed an inside-OB SL in any of them is unknowable without per-CAND M5 refinement
archives.

### Blocker check
Zero clamp results in the production-config case would fail Gate 1 buffer check —
the clamp's buffer is computed from `gate1.ob_retest_sl_min_buffer_atr` (the SAME
multiplier Gate 1 uses), so Gate 1's buffer is satisfied by construction when feasible=True.

### Buffer=0 edge case (documented, non-blocker)
If `gate1.ob_retest_sl_min_buffer_atr` is ever set to 0 OR if `M15_ATR == 0`, the
clamp produces `clamped_sl == ob.low` (LONG), which fails L2's strict-`<`
`_check_sl_beyond_ob` → REJECTED_L2_POST_M5. This was flagged in the V6 review
(§Edge case 1). Production config pins multiplier=0.5 and M15_ATR is positive on
any non-flat M15 window, so the case is unreachable today.

**Recommendation (non-blocking):** add a one-line guard in `clamp_m5_sl_to_ob_boundary`
that sets `target = ob.low - max(buffer, 0.00001)` (or equivalent) if we ever want
to allow `buffer=0` to propagate.

**Verdict: INVARIANT (decisions) + SL DRIFT ACCEPTABLE (the explicit purpose of the clamp).**

---

## A8 — GBPUSD trading_enabled Gate 0.5

**Branch:** `worktree-agent-ad0a9ebd` (2 commits: `32fbe58` gate, `4369214` decision doc)

### Methodology
1. Ran `pytest tests/test_permissions.py` in branch worktree.
2. Extracted `trading_enabled` flags from branch's `config/agent_config.yaml`.
3. Synthetic per-symbol gate verification — invoke `_reject_if_trading_disabled`
   for each instrument + an unknown-symbol default case.
4. Historical replay: for each of 1,231 eval rows in window, apply the per-symbol
   flag + gate and count CAND rows that would flip to NO_TRADE.

### Results
- **Tests:** 60/60 passed (rc=0).
- **Per-instrument flags extracted:**
    - XAUUSD, EURUSD, NAS100, XAGUSD, USDJPY, US30_cash, GBPJPY, NZDUSD → `trading_enabled: true`
    - GBPUSD → `trading_enabled: false`
- **Synthetic gate verification:** 10/10 cases match (9 explicit + 1 default-case).
- **Historical CAND replay (window):**
    - Total rows: 1,231 (132 CANDIDATE)
    - GBPUSD CANDs: 29 → ALL 29 blocked by new Gate 0.5 (100%)
    - Non-GBPUSD CANDs: 103 → 0 blocked by new gate (pass-through unchanged)
    - Per-symbol CAND counts: GBPJPY 34, GBPUSD 29, US30_cash 20, USDJPY 37, XAUUSD 12.

### Decision flips (EXPECTED)
29 GBPUSD CAND rows flip from CANDIDATE → NO_TRADE under Gate 0.5. This is the
designed behavior — GBPUSD observer mode was previously a documentation label,
not a code gate.

### CRITICAL finding — pre-A8 gap confirmed
Scanning `logs/gbpusd.log` for the same window:
- **8 `LIMIT PLACED` events** for GBPUSD pre-A8.
- Actual `mt5.order_send` did NOT fire (zero fills observed, zero `order_send` log
  entries). The path from `set_limit_intent` → `check_limit_fill` → `safe_place_order`
  requires the limit price to be hit AND a subsequent kill-zone or between-KZ check
  to fire. In this window the limits were cancelled by `new_day` before filling.
- However, the gate path EXISTS for a fill to occur without Gate 0.5. A8 closes the
  gap before a real fill happens on "observer-mode" GBPUSD.

### Non-GBPUSD safety
0/103 non-GBPUSD CANDs are blocked by Gate 0.5. All pass-through as expected.

**Verdict: EXPECTED_BEHAVIOR — 29 GBPUSD CAND flips (by design); zero unintended
blocks on other 4 instruments.**

---

## Overall summary

All 5 branches verify their invariance claims:

- **A1, A2, A3, A6** — zero historical decision flips. Ship-safe.
- **A6** has a documented edge case at `buffer == 0` that cannot occur under
  current production config; worth a 1-line future guard but not a blocker.
- **A8** flips 29 GBPUSD CANDs to NO_TRADE (explicit design goal); closes a real
  gap where `set_limit_intent` could have reached `mt5.order_send` on GBPUSD
  without a structural block.

No blocker findings. No surprises in the test suites (total passed: 40 + 30 + 19 + 40 + 60 = **189 tests**).

---

## Reproducibility artifacts

All replay scripts live in `research/reviews_2026-04-24/m1b_replays/`:

- `replay_a1.py` — A1 orchestrator bug bundle
- `replay_a2_displacement.py` — A2 verification displacement iteration
- `replay_a3_pre_ai_gate.py` — A3 pre-AI gate formalization
- `replay_a6_m5_clamp.py` — A6 M5 SL clamp
- `replay_a8_gbpusd_gate.py` — A8 GBPUSD Gate 0.5

Run any script from the main repo root; no arguments required. Outputs are written
to `m1b_replays/outputs/replay_<branch>_result.json`.

Runtime per script: 10-30s each. Total replay time: < 2 minutes. Zero API cost.
