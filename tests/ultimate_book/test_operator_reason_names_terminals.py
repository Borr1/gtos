"""Operator cycle reason must name generation terminals, not lie as a quiet bar.

Admission keeps ``decision_status == "no_candidates_this_bar"`` (tests pin that
enum). The launcher prints ``summary["reason"]``. When gcc terminals are
``stale_decision_bar`` / ``profile_unsupported`` / etc., that reason must name
the mix — a stale book must not look like a quiet market.
"""

from __future__ import annotations

from src.components.ultimate_book.book_engine import rewrite_no_candidates_operator_reason


def _terminals(stale: int, unsupported: int) -> list[dict]:
    rows = [{"terminal_status": "stale_decision_bar"} for _ in range(stale)]
    rows.extend({"terminal_status": "profile_unsupported"} for _ in range(unsupported))
    return rows


def test_evaluated_zero_with_16_stale_and_7_unsupported_is_not_bare_no_candidates():
    """The live lie: reason=no_candidates_this_bar while gcc is stale/unsupported."""
    reason = rewrite_no_candidates_operator_reason(
        "no_candidates_this_bar",
        generation={"generator_evaluated_symbol_slot_count": 0},
        generation_terminals=_terminals(16, 7),
    )
    assert reason != "no_candidates_this_bar"
    assert reason == "terminals:stale_decision_bar=16,profile_unsupported=7"


def test_missing_evaluated_count_treats_as_zero():
    reason = rewrite_no_candidates_operator_reason(
        "no_candidates_this_bar",
        generation={},
        generation_terminals=_terminals(16, 7),
    )
    assert reason == "terminals:stale_decision_bar=16,profile_unsupported=7"


def test_some_slots_evaluated_keeps_admission_prefix():
    reason = rewrite_no_candidates_operator_reason(
        "no_candidates_this_bar",
        generation={"generator_evaluated_symbol_slot_count": 3},
        generation_terminals=(
            [{"terminal_status": "no_candidate"}] * 3
            + [{"terminal_status": "stale_decision_bar"}] * 16
        ),
    )
    assert reason == "no_candidates_this_bar+terminals:stale_decision_bar=16,no_candidate=3"


def test_no_terminals_leaves_admission_status():
    assert rewrite_no_candidates_operator_reason(
        "no_candidates_this_bar",
        generation={"generator_evaluated_symbol_slot_count": 0},
        generation_terminals=[],
    ) == "no_candidates_this_bar"


def test_other_decision_status_is_untouched():
    assert rewrite_no_candidates_operator_reason(
        "shadow_book_disabled",
        generation={"generator_evaluated_symbol_slot_count": 0},
        generation_terminals=_terminals(16, 7),
    ) == "shadow_book_disabled"


def test_engine_evaluate_reason_is_not_bare_when_all_slots_unsupported():
    """Cycle path: owner/launcher reason comes from evaluate()['reason']."""
    import tempfile

    from tests.ultimate_book.test_book_engine import _FakeMT5, _cfg, _fixture_now
    from src.components.ultimate_book.book_engine import UltimateBookLiveEngine

    class _Resolver:
        def __call__(self, symbol):
            return symbol

        def supports(self, symbol):
            return False

    now = _fixture_now()
    res = UltimateBookLiveEngine(
        _cfg(True), _FakeMT5(), tempfile.mkdtemp(), broker_symbol=_Resolver()
    ).evaluate(tags=("crypto",), now_utc=now)
    assert res["ok"] is True
    assert res["n_intents"] == 0
    assert res["decision"].decision_status == "no_candidates_this_bar"
    assert res["reason"] != "no_candidates_this_bar"
    assert str(res["reason"]).startswith("terminals:")
    assert "profile_unsupported=" in str(res["reason"])
