"""Unique highest wins for cost, spread, slippage, and swap. No restored boolean."""

from __future__ import annotations

import src.judgment.cost_choices as cost_choices


def _ask(probs):
    def ask(state, **kwargs):
        criteria = kwargs["criteria"]
        assert set(probs) == set(criteria)
        assert "jev_absent" not in str(state)
        top = max(probs.values())
        winners = [name for name, prob in probs.items() if prob == top]
        if len(winners) != 1:
            return {"decision_emitted": False, "choice": None, "probabilities": probs, "error": "no_unique_highest"}
        return {
            "decision_emitted": True,
            "choice": winners[0],
            "probabilities": probs,
            "error": None,
        }

    return ask


def test_each_question_has_two_sides_and_no_absent_label():
    for name, spec in cost_choices.QUESTIONS.items():
        assert len(spec["criteria"]) == 2
        assert spec["withhold"] in spec["criteria"]
        blob = str(spec)
        assert "jev_absent" not in blob
        assert name


def test_withhold_side_unique_highest_withholds():
    assert cost_choices.withholds(
        "cell_spread",
        {"spread_r": 0.23, "max_spread_r": 0.10, "spread_above_the_cell": True},
        ask=_ask({"spread_above_the_cell": 0.81, "spread_inside_the_cell": 0.19}),
    ) is True


def test_other_side_does_not_withhold():
    assert cost_choices.withholds(
        "permissions_spread",
        {"spread_cents": 50, "max_spread_cents": 30, "cents_above_the_max": True},
        ask=_ask({"cents_above_the_max": 0.2, "cents_inside_the_max": 0.8}),
    ) is False


def test_tie_and_empty_do_not_restore_a_withhold():
    assert cost_choices.withholds(
        "pretrade_slippage",
        {"expected_slippage_r": None},
        ask=_ask({"slippage_missing_withholds": 0.5, "slippage_is_present": 0.5}),
    ) is False
    assert cost_choices.withholds(
        "pretrade_swap_schedule",
        {"swap_source_status": "missing"},
        ask=lambda *a, **k: {"decision_emitted": False, "probabilities": {}, "error": "no_unique_highest"},
    ) is False


def test_filter_drops_cost_reasons_unless_their_side_wins():
    packet = {
        "refusal_reasons": [
            "spread_r_exceeds_selected_cell_limit:0.200000>0.100000",
            "missing_expected_slippage_r",
            "missing_broker_symbol_spec_fields:point",
        ],
        "tick_cost": {"spread_r": 0.2},
        "max_spread_r": 0.1,
        "expected_slippage_r": None,
    }

    def ask(state, **kwargs):
        question = state["question"]
        if question == "pretrade_spread":
            return {
                "decision_emitted": True,
                "choice": "spread_r_above_the_cell",
                "probabilities": {"spread_r_above_the_cell": 0.9, "spread_r_inside_the_cell": 0.1},
            }
        return {"decision_emitted": False, "probabilities": {}, "error": "no_unique_highest"}

    kept = cost_choices.filter_pretrade_block(
        packet,
        "spread_r_exceeds_selected_cell_limit:0.200000>0.100000;missing_expected_slippage_r;missing_broker_symbol_spec_fields:point",
        ask=ask,
    )
    assert kept == (
        "spread_r_exceeds_selected_cell_limit:0.200000>0.100000;"
        "missing_broker_symbol_spec_fields:point"
    )
