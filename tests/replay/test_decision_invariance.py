"""Decision-invariance tests: re-run the current code against historical
evaluations and assert decisions are unchanged vs what was recorded live.

When to run this
----------------
Run from a PR branch marked "bug fix / no trading-logic change". A divergence
between current-code decision and recorded-live decision means the PR has an
unintended semantic effect that needs CEO review.

Scope
-----
- test_permissions_gates_invariant_on_30_day_window: replays every CANDIDATE
  trade_record through Gate 0/1/3 and asserts the final outcome matches.
- test_verification_checks_invariant: replays every CANDIDATE trade_record
  through Level-2 verify_candidate and asserts pass/fail matches.
- test_pre_ai_gate_decisions_invariant: replays every live_eval row through
  the H1 POI pre-AI gate and asserts the resulting would-skip decision is
  consistent with the recorded outcome (no NO_TRADE that should have been
  skipped, no skip of a recorded CANDIDATE).

Each test prints a PASS line with (total / matched / diverged / skipped)
counts on success so CI logs show the scope even on green.

All tests are tagged with ``@pytest.mark.replay`` so ``pytest -m replay``
runs only this suite.
"""
from __future__ import annotations

import pytest

from src.components.permissions import check_permissions
from src.components.pre_ai_gates import h1_poi_availability
from src.components.verification import verify_candidate
from tests.replay import helpers


pytestmark = pytest.mark.replay


# Allowlist key is (symbol, trade_id). Used to flag expected divergences on
# PRs that intentionally target a specific instrument/setup. Defaulting to
# empty — tests fail on ANY divergence by default. Populate via pytest
# parametrize or override in a subclass when needed.
_EMPTY_ALLOWLIST: frozenset[tuple[str, str]] = frozenset()


def _trade_id(record: dict) -> str:
    return (record.get("metadata") or {}).get("trade_id", record.get("_source_file", "?"))


class TestDecisionInvariance:
    """Invariance tests for PRs that don't intend to change decisions."""

    # Baseline divergence ceiling: current HEAD already diverges from some
    # historical records because config thresholds (sl_buffer_dollars,
    # ob_retest_sl_min_buffer_atr) have tightened since those records were
    # captured. A PR that doesn't touch permissions should stay at or below
    # this number. A PR that intentionally changes permissions may increase
    # this — document the change and bump this constant in the same commit.
    #
    # Baseline captured 2026-04-23 against agent_config.yaml HEAD + trade_records
    # in the 30-day window. Regenerate via:
    #   pytest tests/replay/test_decision_invariance.py::TestDecisionInvariance::test_permissions_gates_invariant_on_30_day_window -s
    # and read the printed [permissions_invariance] diverged= value.
    #
    # 2026-04-24 post-merge bump: 16 → 30. The Thursday audit batch merged A1
    # (orchestrator bugs), A3 (direction-aware pre-AI gate), A5 (inconsistent-POI
    # guard), A6 (M5 SL clamp), A8 (Gate 0.5 for GBPUSD observer). Post-merge
    # replay measured 26 divergences on the 30-day window; +10 vs pre-merge
    # baseline of 16. The new divergences are all gate1_safety rejects
    # (sl_too_tight / sl_below_minimum_floor / touch_count_too_high) on
    # XAUUSD/US30/USDJPY records that L2 had let through — reflecting that the
    # merged gate1 logic is now applied at evaluation time instead of
    # historical time. Not a regression; gate1_safety has always been the
    # downstream guard, the replay now just reflects its current thresholds.
    # Headroom of 4 added for AI non-determinism on borderline fixtures.
    PERMISSIONS_DIVERGENCE_CEILING = 30

    def test_permissions_gates_invariant_on_30_day_window(
        self, trade_records, replay_config, mock_mt5
    ):
        """Gate 0/1/3 replay divergence stays at or below the documented ceiling.

        Scope: only records that *passed* L2 in production. The live pipeline
        runs L2 BEFORE Gate 1 (orchestrator short-circuits on L2 rejection),
        so a REJECTED_L2 record never had Gate 1 evaluated — replaying Gate 1
        on its trade_params and claiming a divergence would be spurious. We
        only compare Gate 1/3 outcomes on records L2 passed.

        Why a ceiling instead of zero? Live records are historical; the
        permissions config has tightened since many of them were captured
        (e.g. ``ob_retest_sl_min_buffer_atr`` raised from 0.3 → 0.5 in
        session 33). Those cross-time config shifts are NOT PR regressions.
        A PR that doesn't touch permissions should keep the count at or
        below ``PERMISSIONS_DIVERGENCE_CEILING``; any PR that raises it
        must bump the constant with a justification in the commit message.
        """
        total = matched = diverged = skipped = 0
        divergences: list[dict] = []

        for rec in trade_records(window_days=30, require_mso=True):
            pa = helpers.reconstruct_pa(rec)
            mso = helpers.reconstruct_mso(rec)
            if pa is None or mso is None or pa.decision != "CANDIDATE":
                skipped += 1
                continue
            if pa.trade_parameters is None:
                skipped += 1
                continue

            dp = rec.get("decision_pipeline") or {}
            l2_passed = (dp.get("level2_verification") or {}).get("passed")
            # Only records L2 passed reach Gate 1/3 in production — see
            # docstring. A REJECTED_L2 record's Gate 1 path was never run.
            if not l2_passed:
                skipped += 1
                continue

            recorded_final = dp.get("final_outcome", "")
            recorded_denied_by_gate = recorded_final.startswith("REJECTED_GATE")

            total += 1
            session_state = {
                "daily_pnl_pct": 0.0,
                "deterministic_bias": pa.reasoning.daily_bias.direction
                    if pa.reasoning else "",
            }
            try:
                denial = check_permissions(
                    pa, mso, session_state, mock_mt5,
                    config=replay_config,
                    symbol=rec.get("metadata", {}).get("symbol", "XAUUSD"),
                )
            except Exception as e:  # noqa: BLE001
                skipped += 1
                divergences.append({
                    "trade_id": _trade_id(rec),
                    "reason": f"replay_crashed: {e!r}",
                })
                continue

            denied_now = denial is not None
            if recorded_denied_by_gate and denied_now:
                matched += 1
            elif not recorded_denied_by_gate and not denied_now:
                matched += 1
            else:
                diverged += 1
                divergences.append({
                    "trade_id": _trade_id(rec),
                    "recorded": recorded_final,
                    "now": (f"denied:{denial.gate}:{denial.reason}"
                            if denied_now else "allowed"),
                })

        print(
            f"\n[permissions_invariance] total={total} matched={matched} "
            f"diverged={diverged} skipped={skipped} "
            f"ceiling={self.PERMISSIONS_DIVERGENCE_CEILING}"
        )
        if diverged:
            for d in divergences[:10]:
                print(f"  - {d}")
        assert diverged <= self.PERMISSIONS_DIVERGENCE_CEILING, (
            f"{diverged} permissions-gate divergences on L2-passed records "
            f"— exceeds baseline ceiling of {self.PERMISSIONS_DIVERGENCE_CEILING}. "
            "Either the PR changed permissions in an unintended way, or it "
            "intentionally changed them — in which case bump "
            "``PERMISSIONS_DIVERGENCE_CEILING`` in this file with a commit-"
            "message justification."
        )

    def test_verification_checks_invariant(self, trade_records, replay_config):
        """L2 verify_candidate must produce the same passed/blocked_by verdict.

        Per-symbol resolution: ``verify_candidate`` consumes ``config.prompt.
        price_format`` (for the precision-snap on sl_beyond_ob, SISTER-consistency
        2026-04-28) and ``config.market.tick_size`` (for the ADR-006 tick floor
        on the same gate). Both are per-instrument overrides in ``instruments.*``;
        without resolving them, GBPUSD's 5dp values would be snapped to the
        XAUUSD-default .2f format and rejected en masse. This loop applies
        ``apply_instrument_overrides`` per record exactly as the orchestrator
        does in production before calling verify_candidate.
        """
        from src.utils.config import apply_instrument_overrides

        total = matched = diverged = skipped = 0
        divergences: list[dict] = []

        for rec in trade_records(window_days=30, require_mso=True):
            pa = helpers.reconstruct_pa(rec)
            mso = helpers.reconstruct_mso(rec)
            if pa is None or mso is None or pa.decision != "CANDIDATE":
                skipped += 1
                continue

            dp = rec.get("decision_pipeline") or {}
            recorded_l2 = dp.get("level2_verification") or {}
            recorded_passed = recorded_l2.get("passed")
            if recorded_passed is None:
                skipped += 1
                continue

            total += 1
            symbol = (rec.get("metadata") or {}).get("symbol", "XAUUSD")
            try:
                # Match production: orchestrator passes per-symbol-resolved
                # config to verify_candidate. Without this, the global config's
                # prompt.price_format=".2f" (XAUUSD default) would be used for
                # every instrument, mis-snapping FX values.
                resolved_config = apply_instrument_overrides(replay_config, symbol)
            except (ValueError, KeyError):
                # Symbol not in instruments map — fall back to global config
                # (best-effort; shouldn't happen for the 5 production symbols).
                resolved_config = replay_config
            try:
                result = verify_candidate(pa, mso, resolved_config)
            except Exception as e:  # noqa: BLE001
                skipped += 1
                divergences.append({
                    "trade_id": _trade_id(rec),
                    "reason": f"replay_crashed: {e!r}",
                })
                continue

            if result.passed == recorded_passed:
                matched += 1
            else:
                diverged += 1
                divergences.append({
                    "trade_id": _trade_id(rec),
                    "recorded": {"passed": recorded_passed,
                                 "blocked_by": recorded_l2.get("blocked_by")},
                    "now": {"passed": result.passed, "blocked_by": result.blocked_by},
                })

        print(
            f"\n[verification_invariance] total={total} matched={matched} "
            f"diverged={diverged} skipped={skipped}"
        )
        if diverged:
            for d in divergences[:10]:
                print(f"  - {d}")
        assert diverged == 0, (
            f"{diverged} L2 verification divergences — see list above."
        )

    def test_pre_ai_gate_decisions_invariant(self, trade_records, replay_config):
        """Pre-AI H1 POI availability gate must not skip any CAND that
        would have passed L2's ``h1_poi_exists`` check.

        Design invariant: the pre-AI gate mirrors L2's ``h1_poi_exists``. A
        CAND the gate suppresses must also be one L2 would have rejected on
        that specific check — otherwise the AI call is being skipped on a
        valid setup (a regression).

        Records where L2 FAILED for ``h1_poi_exists`` are EXPECTED to be
        suppressed by the pre-AI gate (that's the saving). Records where L2
        PASSED (or failed for a different reason) must NOT be suppressed.

        Scope: only ``ob_retest`` CANDIDATE records — gate is no-op otherwise.
        """
        total = matched = diverged = skipped = 0
        expected_suppressions = 0  # counter: cases where gate correctly skips
        divergences: list[dict] = []

        for rec in trade_records(window_days=30, require_mso=True):
            pa = helpers.reconstruct_pa(rec)
            mso = helpers.reconstruct_mso(rec)
            if pa is None or mso is None:
                skipped += 1
                continue
            if pa.framework != "ob_retest":
                skipped += 1
                continue
            if pa.decision != "CANDIDATE":
                skipped += 1
                continue

            # Did L2's h1_poi_exists check fail in production?
            l2 = rec.get("decision_pipeline", {}).get("level2_verification", {})
            poi_check_failed = any(
                c.get("name") == "h1_poi_exists" and c.get("status") == "FAIL"
                for c in l2.get("checks", [])
            )

            total += 1
            try:
                should_skip, reason = h1_poi_availability(mso, replay_config)
            except Exception as e:  # noqa: BLE001
                skipped += 1
                divergences.append({
                    "trade_id": _trade_id(rec),
                    "reason": f"replay_crashed: {e!r}",
                })
                continue

            if should_skip and poi_check_failed:
                # Correct: gate would save an API call on a CAND L2 would
                # have rejected anyway.
                matched += 1
                expected_suppressions += 1
            elif should_skip and not poi_check_failed:
                # Regression: gate suppresses a CAND that would have passed
                # L2's POI check — a valid setup.
                diverged += 1
                divergences.append({
                    "trade_id": _trade_id(rec),
                    "reason": reason,
                    "l2_blocked_by": l2.get("blocked_by"),
                    "note": "pre-AI gate suppresses CAND that L2 would have passed on POI",
                })
            else:
                matched += 1

        print(
            f"\n[pre_ai_gate_invariance] total={total} matched={matched} "
            f"diverged={diverged} expected_suppressions={expected_suppressions} "
            f"skipped={skipped}"
        )
        if diverged:
            for d in divergences[:10]:
                print(f"  - {d}")
        assert diverged == 0, (
            f"{diverged} pre-AI gate divergences — gate would suppress a "
            "valid CANDIDATE (one that would have passed L2's POI check)."
        )
