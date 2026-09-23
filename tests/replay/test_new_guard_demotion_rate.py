"""New-guard demotion rate tests.

When a PR adds a new post-AI validator (e.g. another
``guard_candidate_*`` in ``primary_analyzer``), run this test against the
proposed guard. It applies the guard to every historical CANDIDATE and:

1. Fails if the guard demotes any CANDIDATE that *actually filled* in
   production. Demoting a pending-only CAND that never filled is fine
   (protective); demoting a winner is destructive.
2. Fails if the guard's demotion rate on all historical CANDs exceeds
   ``DEMOTION_RATE_WARN_THRESHOLD`` (default 10%). Higher rates indicate
   the guard is overfit or has a bug.

How to add a new guard
----------------------
Subclass or parameterize via the ``guard_func`` fixture::

    from my.branch import my_new_guard

    class TestMyNewGuard(TestNewGuardDemotionRate):
        @pytest.fixture
        def guard_func(self):
            return my_new_guard

Default ``guard_func`` is ``primary_analyzer.guard_candidate_degenerate_params``
— the most recent production guard — so the smoke test runs on a known
benign input. Both tests should PASS on current HEAD since that guard
has already been validated against live data.

Cost: ~1 sec. Zero API. Last 30 days of trade_records (~90 CANDs).
"""
from __future__ import annotations

import pytest

from src.components.primary_analyzer import guard_candidate_degenerate_params
from tests.replay import helpers


pytestmark = pytest.mark.replay


# ---------------------------------------------------------------------------
# Configuration thresholds (subclass / parametrize to override per guard)
# ---------------------------------------------------------------------------


DEMOTION_RATE_WARN_THRESHOLD = 0.10  # 10% — tune up/down per guard


# ---------------------------------------------------------------------------
# Default guard (smoke test — known benign on historical data)
# ---------------------------------------------------------------------------


@pytest.fixture
def guard_func():
    """Default: the degenerate-params guard shipped in FA-2.

    Override in a subclass or via parametrize to test a proposed guard::

        @pytest.fixture
        def guard_func(self):
            return my_new_guard
    """
    return guard_candidate_degenerate_params


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNewGuardDemotionRate:
    """When adding a post-AI validator, run these checks before shipping."""

    def test_guard_does_not_demote_any_historical_fill(
        self, historical_fills, guard_func
    ):
        """Any guard that demotes a filled CANDIDATE is a regression.

        "Filled" here means the trade_record has execution metadata
        indicating an actual broker fill (see ``helpers.is_historical_fill``).
        Pending LIMIT_PLACED records that never filled are excluded — those
        are safe to demote.
        """
        if not historical_fills:
            pytest.skip(
                "No historical fills in the 30-day window — common for low-frequency "
                "accounts. Run this test again once fills are recorded, or widen the "
                "window via the fixture factory."
            )

        demoted: list[dict] = []
        for rec in historical_fills:
            pa = helpers.reconstruct_pa(rec)
            if pa is None or pa.decision != "CANDIDATE":
                continue
            before_decision = pa.decision
            try:
                result = guard_func(pa)
            except Exception as e:  # noqa: BLE001
                demoted.append({
                    "trade_id": (rec.get("metadata") or {}).get("trade_id"),
                    "error": f"guard_crashed: {e!r}",
                })
                continue
            if result.decision != before_decision:
                demoted.append({
                    "trade_id": (rec.get("metadata") or {}).get("trade_id"),
                    "new_decision": result.decision,
                    "no_trade_reason": getattr(result, "no_trade_reason", None),
                    "r_multiple": helpers.r_multiple_of(rec),
                    "exit_type": helpers.outcome_of(rec),
                })

        print(
            f"\n[demotion_rate/fills] fills_checked={len(historical_fills)} "
            f"demoted={len(demoted)}"
        )
        for d in demoted[:5]:
            print(f"  - {d}")
        assert not demoted, (
            f"{len(demoted)} historical fills would have been demoted by "
            f"the proposed guard. See the list above — each entry is a "
            "trade that reached production AND would now be suppressed. "
            "Review the guard logic before shipping."
        )

    def test_guard_demotion_rate_below_threshold(
        self, trade_records, guard_func
    ):
        """Global demotion rate across all CANDIDATEs stays below threshold."""
        total_cands = 0
        demoted_count = 0
        demoted_examples: list[dict] = []

        for rec in trade_records(window_days=30):
            pa = helpers.reconstruct_pa(rec)
            if pa is None or pa.decision != "CANDIDATE":
                continue
            total_cands += 1
            try:
                result = guard_func(pa)
            except Exception:  # noqa: BLE001
                demoted_count += 1
                continue
            if result.decision != "CANDIDATE":
                demoted_count += 1
                if len(demoted_examples) < 5:
                    demoted_examples.append({
                        "trade_id": (rec.get("metadata") or {}).get("trade_id"),
                        "reason": getattr(result, "no_trade_reason", None),
                    })

        if total_cands == 0:
            pytest.skip(
                "No historical CANDIDATEs in the 30-day window to evaluate "
                "demotion rate against. Widen the window in the fixture factory."
            )

        rate = demoted_count / total_cands
        print(
            f"\n[demotion_rate/global] total_cands={total_cands} "
            f"demoted={demoted_count} rate={rate:.1%}"
        )
        for d in demoted_examples:
            print(f"  - {d}")
        assert rate <= DEMOTION_RATE_WARN_THRESHOLD, (
            f"Demotion rate {rate:.1%} exceeds threshold "
            f"{DEMOTION_RATE_WARN_THRESHOLD:.0%}. Either the guard is too "
            "aggressive or this is a real regression worth investigating."
        )
