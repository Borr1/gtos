# GTOS src/ Commits Code Audit — Pre-Restart

**Date:** 2026-04-17
**Auditor:** Independent code-integrity verifier
**Scope:** Commits since 2026-04-13 touching `src/`, `prompts/`, `config/`
**Test baseline:** 1133 passed / 4 pre-existing fails (unchanged)

## Commit verdicts

| Commit | Subject | Verdict |
|---|---|---|
| `78680ec` | prop-firm profile overlay (FTMO / redacted_account) | CLEAN |
| `ab077cd` | liquidity cluster gate (disabled) + R2 logger + schema | CLEAN |
| `1a22d92` | touch-count OB gate + persistence + SL margin + 2R log | CLEAN |
| `acf530f` | sleep race fix + SL sweep margin | CLEAN |
| `d806dc6` | only BE-move at KZ end when in profit | CLEAN |

## Section findings

**A. Commit-level diff review — PASS.** All diffs match messages. Every trading-decision change has tests (touch_count 4 tests in `test_permissions.py:447-470`, liquidity cluster 14 tests, persistence 11 tests in `test_orchestrator.py:564-724`, market_state touches 5 tests).

**B. Liquidity cluster gate DISABLED — PASS.**
- `config/agent_config.yaml:57` → `sl_liquidity_cluster_enabled: false`.
- Neither `ftmo.yaml` nor `redacted_account.yaml` overrides it.
- Code path (`permissions.py:387-388`): `if not enabled: return None`. Shadow-log write is unconditional (line 379-382) as designed.

**C. Touch-count OB gate ACTIVE — PASS.**
- Hard-coded threshold `>= 2` in `permissions.py:163`. No config toggle (gate is load-bearing, not optional — consistent with handoff 19).
- Creates `ExecutionDenial("gate1_safety", "touch_count_too_high", …)` → logged as NO_TRADE, not silently dropped.
- Runs in `_gate1_safety_checks` at line 450, before inverted-TP auto-correct, as documented.

**D. SL margin 0.3→0.5 — PASS.**
- `config/agent_config.yaml:50` → `ob_retest_sl_min_buffer_atr: 0.5`. Comment history (lines 54-56) explicitly documents the 0.3→0.5 raise.
- Grep of repo: no leftover `0.3` near `ATR`/`buffer` in permissions.py. Only doc references in the comment itself.

**E. Pending intent persistence — PASS.**
- Path: `knowledge_base/meta/pending_intent_{symbol}.pkl` (`execution.py:96-98`).
- `schema_version=1` field on dataclass (`execution.py:80`); mismatch → discard + delete (`execution.py:234-242`).
- Staleness: hard 24h cap (`PENDING_INTENT_MAX_AGE_HOURS = 24`, line 33 + check at 259), plus "before today's first KZ" filter (273-282). Note: the audit brief mentioned ">48h"; actual is 24h — **stricter**, which is safer.
- Orphan `.{pid}.tmp` cleanup at init (lines 186-207).

**F. redacted_account 1% profile — PASS.**
- `redacted_account.yaml:27` → `risk_per_trade_pct: 1.0`. `drawdown_reduction.reduced_risk_pct: 0.25`.
- Base config unchanged at 2.0 / 0.5 (lines 19 / 36).
- `apply_profile_overrides` (`src/utils/config.py:81-103`) uses deep_merge; applied in orchestrator BEFORE instrument overrides (verified sequence in commit 78680ec diff). Precedence: base → profile → instrument.
- 13 new profile tests pass.

**G. Test suite — PASS.**
- `pytest tests/ --ignore=tests/test_infrastructure_framework.py --timeout=60` → **1133 passed, 4 failed**.
- 4 failures are all pre-existing (commit 1a22d92 notes): `test_resets_state` (NewDay mock), `test_timeout_trailing_moves_sl_then_closes` (live BE), 2x `test_security_framework` WF-1 Windows quirks.
- No new-since-Apr-13 test is failing. No skipped tests that should pass.

**H. Pre-existing bugs STILL present — PASS (as required).**
1. `pending_intent destroyed before open_trade` in limit-fill — `execution.py:569-594` now conditional (clear only on success), but this was actually resolved previously (commit 5242bfd "fix: limit fill viability checks"). Handoff 17's concern is partially addressed; no regression introduced.
2. `_active_trade_record` NEVER set on limit-fill path — CONFIRMED still present. `orchestrator.py:442` and `:1265` call `_init_trade_tracking()` but NOT `_active_trade_record = ...`. Only the market-open path (line 2222) sets it. Exit data for limit-filled trades will still be lost on `_finalize_exit()` — no partial fix snuck in. Matches handoff 17.

## Config vs CLAUDE.md
- `enabled_frameworks: ["ob_retest"]` — matches.
- `confidence_filter_mode: "shadow"` — matches.
- `primary_model: claude-sonnet-4-6`, `primary_effort: "max"`, `session_memory_enabled: false` — match.
- `min_rr: 1.5`, `max_daily_losses: 2`, `risk_per_trade_pct: 2.0` — match.
- No contradictions found.

## Restart verdict

**SAFE**

No blockers. All five commits are self-consistent, tested, and the liquidity cluster gate ships disabled as documented. Persistence logic uses a stricter 24h staleness window than the audit brief assumed. The two pre-existing bugs remain untouched (as required — require CEO approval to fix). Live processes run base config by default (no `--profile`, no `GTOS_PROFILE` env), so FTMO behavior is unchanged by the profile infrastructure.
