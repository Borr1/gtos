"""Execution Choices: the unique highest probability is the decision."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.judgment.execution_choices import QUESTIONS, choose, clear_cache

REPO = Path(__file__).resolve().parents[2]
EXECUTION = REPO / "src" / "components" / "execution.py"


def _ask(winner: str, probs: dict[str, float]):
    def ask(state, *, question_id, instructions, criteria):
        assert question_id
        assert instructions
        assert set(criteria) == set(probs)
        assert state["ns"] == "operator"
        return {
            "choice": winner,
            "probability": probs[winner],
            "probabilities": dict(probs),
            "decision_emitted": True,
            "model": "jev-1.13.0",
            "probability_source": "test",
        }

    return ask


def _tie_ask(probs: dict[str, float]):
    def ask(state, *, question_id, instructions, criteria):
        return {
            "choice": None,
            "probability": None,
            "probabilities": dict(probs),
            "decision_emitted": False,
            "error": "no_unique_highest",
            "model": "jev-1.13.0",
        }

    return ask


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    clear_cache()
    monkeypatch.setenv("GTOS_EXECUTION_CHOICES_RECORD", str(tmp_path / "execution_choices.jsonl"))
    yield
    clear_cache()


def test_nine_questions_are_separate():
    assert set(QUESTIONS) == {
        "fill",
        "modify",
        "partial",
        "trail",
        "time_stop",
        "reject",
        "retry",
        "spread",
        "lot",
    }
    ids = [spec["id"] for spec in QUESTIONS.values()]
    assert len(ids) == len(set(ids)) == 9
    assert all(len(spec["criteria"]) == 2 for spec in QUESTIONS.values())
    assert "jev_absent" not in EXECUTION.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "question,winner,probs",
    [
        ("fill", "fill", {"fill": 0.7, "leave_pending": 0.3}),
        ("fill", "leave_pending", {"fill": 0.3, "leave_pending": 0.7}),
        ("modify", "modify", {"modify": 0.8, "leave_stop": 0.2}),
        ("modify", "leave_stop", {"modify": 0.2, "leave_stop": 0.8}),
        ("partial", "partial", {"partial": 0.6, "hold_full": 0.4}),
        ("partial", "hold_full", {"partial": 0.4, "hold_full": 0.6}),
        ("trail", "trail", {"trail": 0.9, "leave_stop": 0.1}),
        ("time_stop", "fire_time_stop", {"fire_time_stop": 0.55, "let_it_run": 0.45}),
        ("time_stop", "let_it_run", {"fire_time_stop": 0.45, "let_it_run": 0.55}),
        ("reject", "continue", {"block": 0.2, "continue": 0.8}),
        ("reject", "block", {"block": 0.8, "continue": 0.2}),
        ("retry", "retry", {"retry": 0.66, "stop": 0.34}),
        ("retry", "stop", {"retry": 0.34, "stop": 0.66}),
        ("spread", "spread_ok", {"spread_ok": 0.81, "spread_too_wide": 0.19}),
        ("spread", "spread_too_wide", {"spread_ok": 0.19, "spread_too_wide": 0.81}),
        ("lot", "place", {"place": 0.7, "refuse": 0.3}),
        ("lot", "refuse", {"place": 0.3, "refuse": 0.7}),
    ],
)
def test_unique_highest_is_the_decision(question, winner, probs):
    row = choose(
        question,
        ticket=294215389,
        symbol="XAUUSD",
        reason="test",
        ask=_ask(winner, probs),
        use_cache=False,
    )
    assert row["decision_emitted"] is True
    assert row["choice"] == winner
    assert row["probability"] == probs[winner]
    assert row["agent_order_send"] is False
    assert row["model"] == "jev-1.13.0"
    assert row["persist"] == "0.00"


def test_tie_is_not_a_decision():
    row = choose(
        "spread",
        symbol="XAUUSD",
        ask=_tie_ask({"spread_ok": 0.5, "spread_too_wide": 0.5}),
        use_cache=False,
    )
    assert row["decision_emitted"] is False
    assert row["choice"] is None


def test_missing_answer_does_not_decide():
    def ask(state, *, question_id, instructions, criteria):
        raise RuntimeError("down")

    row = choose("time_stop", ticket=1, ask=ask, use_cache=False)
    assert row["decision_emitted"] is False
    assert row["choice"] is None
    assert row["error"] == "RuntimeError"


def test_unknown_question_does_not_decide():
    row = choose("flatten_the_book", ask=_ask("fill", {"fill": 1.0}), use_cache=False)
    assert row["error"] == "unknown_question"
    assert row["decision_emitted"] is False


def test_source_has_each_hook_and_no_ticket_pin():
    source = EXECUTION.read_text(encoding="utf-8")
    assert "294215389" not in source
    assert "gold_ticket_do_not_close" not in source
    assert "gold_pin" not in source
    tree = ast.parse(source)
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "_exec_choice":
            continue
        if node.args and isinstance(node.args[0], ast.Constant):
            calls.append(node.args[0].value)
    assert set(calls) == set(QUESTIONS)
    assert calls.count("reject") == 3
    assert calls.count("retry") == 3
    assert calls.count("partial") == 2
