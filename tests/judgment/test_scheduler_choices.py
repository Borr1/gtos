"""Scheduler and allocator Choices: two sides, unique highest, no restored boolean."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.judgment.scheduler_choices import (
    QUESTIONS,
    choose,
    clear_cache,
    eligible_by_choice,
    expression_gate,
    select_expressed,
    set_ask,
    set_force,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    AllocatorOption,
    SchedulerV4Config,
)

REPO = Path(__file__).resolve().parents[2]
ALLOCATOR = REPO / "src" / "research" / "moonshot_scheduler_v4_best_trade_allocator.py"
PERMISSIONS = REPO / "src" / "components" / "permissions.py"
CHOICES = REPO / "src" / "judgment" / "scheduler_choices.py"
SELECTOR = REPO / "src" / "components" / "selector_v4.py"


def _ask(winner: str, probs: dict[str, float]):
    def ask(state, *, question_id, instructions, criteria):
        assert question_id
        assert instructions
        assert set(criteria) == set(probs)
        assert state["ns"] == "operator"
        assert "jev_absent" not in instructions
        return {
            "choice": winner,
            "probability": probs[winner],
            "probabilities": dict(probs),
            "decision_emitted": True,
            "model": "jev-1.13.0",
            "probability_source": "test",
        }

    return ask


def _plan(answers: dict[str, str]):
    def ask(state, *, question_id, instructions, criteria):
        question = state["question"]
        assert set(criteria) == set(QUESTIONS[question]["criteria"])
        assert len(criteria) == 2
        winner = answers.get(question)
        if winner is None:
            return {
                "choice": None,
                "probability": None,
                "probabilities": {},
                "decision_emitted": False,
                "error": "no_unique_highest",
                "model": "jev-1.13.0",
            }
        other = next(name for name in criteria if name != winner)
        probs = {winner: 0.71, other: 0.29}
        return {
            "choice": winner,
            "probability": probs[winner],
            "probabilities": probs,
            "decision_emitted": True,
            "model": "jev-1.13.0",
        }

    return ask


def _option(**overrides) -> AllocatorOption:
    payload = dict(
        option_id="opt-1",
        source_type="new_candidate",
        action_class="new_position",
        candidate_id="cand-1",
        exposure_id=None,
        pending_id=None,
        symbol="EURUSD",
        side="LONG",
        requested_risk_pct=0.5,
        approved_risk_pct=0.5,
        risk_delta_pct=0.5,
        score=1.2,
        score_components={},
        decision_status="candidate",
        reason="test",
    )
    payload.update(overrides)
    return AllocatorOption(**payload)


def _zero() -> AllocatorOption:
    return _option(
        option_id="zero",
        source_type="zero_trade",
        action_class="zero_trade",
        candidate_id=None,
        symbol=None,
        side=None,
        requested_risk_pct=0.0,
        approved_risk_pct=0.0,
        risk_delta_pct=0.0,
        score=0.2,
        decision_status="zero_trade",
        reason="zero_trade",
    )


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    clear_cache()
    set_ask(None)
    set_force(None)
    monkeypatch.setenv("GTOS_SCHEDULER_CHOICES_RECORD", str(tmp_path / "scheduler_choices.jsonl"))
    yield
    clear_cache()
    set_ask(None)
    set_force(None)


def test_each_question_has_two_sides_and_no_absent_label():
    assert len(QUESTIONS) >= 20
    ids = [spec["id"] for spec in QUESTIONS.values()]
    assert len(ids) == len(set(ids))
    assert all(len(spec["criteria"]) == 2 for spec in QUESTIONS.values())
    text = CHOICES.read_text(encoding="utf-8")
    assert "jev_absent" not in text
    assert "294215389" not in text
    assert "restored_boolean" in text


def test_unique_highest_is_the_decision():
    probs = {"express_zero": 0.22, "express_a_candidate": 0.78}
    row = choose(
        "eligible_pool",
        symbol="EURUSD",
        proposed="cand-1",
        ask=_ask("express_a_candidate", probs),
        use_cache=False,
    )
    assert row["decision_emitted"] is True
    assert row["choice"] == "express_a_candidate"
    assert row["agent_order_send"] is False
    assert row["persist"] == "0.00"
    assert row["restored_boolean"] is False


def test_tie_is_not_a_decision():
    def ask(state, *, question_id, instructions, criteria):
        return {
            "choice": None,
            "probabilities": {"this_candidate": 0.5, "another_candidate": 0.5},
            "decision_emitted": False,
            "error": "no_unique_highest",
        }

    row = choose("selected_identity", ask=ask, use_cache=False)
    assert row["decision_emitted"] is False
    assert row["choice"] is None


def test_expression_gate_follows_the_choice_not_the_boolean():
    gate = expression_gate(
        selected_action="zero_trade",
        selected_candidate_id="other",
        candidate_id="cand-1",
        runtime_effect_now=False,
        symbol="EURUSD",
        ask=_plan(
            {
                "selected_zero": "express_this_trade",
                "selected_identity": "this_candidate",
                "runtime_effect": "runtime_effect",
            }
        ),
    )
    assert gate["expressed"] is True
    assert gate["restored_boolean"] is False


def test_expression_gate_empty_does_not_restore_zero_trade_boolean():
    gate = expression_gate(
        selected_action="zero_trade",
        selected_candidate_id="cand-1",
        candidate_id="cand-1",
        runtime_effect_now=True,
        symbol="EURUSD",
        ask=_plan({}),
    )
    assert gate["expressed"] is False
    assert gate["reason"] == "scheduler_choice_no_decision"
    assert gate["question"] == "selected_zero"


def test_select_expressed_unique_primary():
    primary = _option()
    selected = select_expressed(
        eligible_non_zero=[primary],
        zero=_zero(),
        snapshot=None,
        config=SchedulerV4Config(),
        ask=_plan(
            {
                "executable_transfer": "transfer_allowed",
                "hazard_versus_zero": "above_zero",
                "hard_dominance": "legacy_order",
                "eligible_pool": "express_a_candidate",
                "window_cardinality": "one_trade",
                "leading_trade": "express_leading",
                "burst_guard": "express_primary",
            }
        ),
    )
    assert [option.option_id for option in selected] == ["opt-1"]


def test_burst_tie_does_not_restore_the_primary_boolean():
    primary = _option()
    selected = select_expressed(
        eligible_non_zero=[primary],
        zero=_zero(),
        snapshot=None,
        config=SchedulerV4Config(),
        ask=_plan(
            {
                "executable_transfer": "transfer_allowed",
                "hazard_versus_zero": "above_zero",
                "hard_dominance": "legacy_order",
                "eligible_pool": "express_a_candidate",
                "window_cardinality": "one_trade",
                "leading_trade": "express_leading",
            }
        ),
    )
    assert len(selected) == 1
    assert selected[0].action_class == "zero_trade"
    assert selected[0].reason == "scheduler_choice_no_decision"


def test_choice_can_withhold_the_score_leader():
    leader = _option(option_id="leader", score=9.0)
    other = _option(option_id="other", candidate_id="cand-2", score=0.4)
    answers = {
        "executable_transfer": "transfer_allowed",
        "hazard_versus_zero": "above_zero",
        "hard_dominance": "legacy_order",
        "eligible_pool": "express_a_candidate",
        "window_cardinality": "one_trade",
        "burst_guard": "express_primary",
    }
    calls = {"n": 0}

    def ask(state, *, question_id, instructions, criteria):
        question = state["question"]
        if question == "leading_trade":
            calls["n"] += 1
            winner = "not_the_leading_trade" if calls["n"] == 1 else "express_leading"
        else:
            winner = answers[question]
        other_name = next(name for name in criteria if name != winner)
        return {
            "choice": winner,
            "probability": 0.8,
            "probabilities": {winner: 0.8, other_name: 0.2},
            "decision_emitted": True,
            "model": "jev-1.13.0",
        }

    selected = select_expressed(
        eligible_non_zero=[leader, other],
        zero=_zero(),
        snapshot=None,
        config=SchedulerV4Config(),
        ask=ask,
    )
    assert selected[0].option_id == "other"


def test_forced_challenge_allocator_uses_the_choice():
    from src.research.moonshot_scheduler_v4_best_trade_allocator import (
        _risk_adjusted_selected_options,
    )

    set_force(True)
    set_ask(
        _plan(
            {
                "executable_transfer": "transfer_allowed",
                "hazard_versus_zero": "above_zero",
                "hard_dominance": "legacy_order",
                "eligible_pool": "express_a_candidate",
                "window_cardinality": "one_trade",
                "leading_trade": "express_leading",
                "burst_guard": "express_primary",
            }
        )
    )
    selected = _risk_adjusted_selected_options(
        eligible_non_zero=[_option()],
        zero=_zero(),
        snapshot=None,
        config=SchedulerV4Config(),
    )
    assert [option.option_id for option in selected] == ["opt-1"]


def test_eligibility_empty_does_not_keep_a_high_score():
    kept = eligible_by_choice([_option()], SchedulerV4Config(), ask=_plan({}))
    assert kept == []


def test_sources_hook_the_choice_and_do_not_edit_the_selector():
    allocator = ALLOCATOR.read_text(encoding="utf-8")
    permissions = PERMISSIONS.read_text(encoding="utf-8")
    assert "select_expressed" in allocator
    assert "eligible_by_choice" in allocator
    assert "return [zero] if burst_blocked else [primary]" in allocator
    assert "expression_gate" in permissions
    assert "scheduler_v4_selected_zero_trade" in permissions
    assert "jev_absent" not in allocator
    assert "jev_absent" not in permissions
    selector = SELECTOR.read_text(encoding="utf-8")
    assert "scheduler_choices" not in selector
