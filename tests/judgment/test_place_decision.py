"""Place Choice resolves by unique highest probability.

An empty map or a tie is not PLACE, and it is not a flatten. A reported
label without a unique probability is not the decision. No order send.
"""

from __future__ import annotations

import pytest

from src.judgment.place_choice import PLACE_ORDER, evaluate_place_choice


class _Intent:
    symbol = "GBPUSD"
    sleeve = "dsp_descending_lows_accepted"
    side = "buy"
    details = {"namespace": "operator"}


def _mass(winner: str | None, *, tie: bool = False, empty: bool = False) -> dict[str, float]:
    if empty:
        return {}
    names = list(PLACE_ORDER)
    if tie:
        return {name: 0.5 if name in {names[0], names[1]} else 0.0 for name in names}
    rest = (1.0 - 0.56) / (len(names) - 1)
    return {name: (0.56 if name == winner else rest) for name in names}


@pytest.fixture(autouse=True)
def _no_live_account(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "src.judgment.equity_frame.attach_account",
        lambda state: state,
    )


def _evaluate(monkeypatch: pytest.MonkeyPatch, probabilities: dict, label: str) -> dict:
    seen = {"n": 0}

    def _fake(state, questions, merge_sleeve=False):
        del state, merge_sleeve
        seen["n"] += 1
        assert "place" in questions
        return {
            "answers": {
                "place": {
                    "probabilities": probabilities,
                    "choice": label,
                }
            },
            "model": "jev-1.13.0",
            "calls_used": 0,
        }

    monkeypatch.setattr("src.judgment.jev_client.evaluate", _fake)
    row = evaluate_place_choice(
        _Intent(),
        namespace="operator",
        login=0,
        observe=False,
    )
    assert seen["n"] == 1
    assert row["broker_effect"] is False
    assert row["hop"] == "place"
    return row


def test_unique_highest_is_the_place_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    row = _evaluate(monkeypatch, _mass("STAND"), "PLACE")
    assert row["action"] == "STAND"
    assert row["choice"] == "STAND"
    assert row["unique_highest"] is True
    assert row["probability"] == pytest.approx(0.56)
    assert row["action"] != "PLACE"
    assert row["action"] != "FLATTEN_CANDIDATE"


def test_unique_place_is_place(monkeypatch: pytest.MonkeyPatch) -> None:
    row = _evaluate(monkeypatch, _mass("PLACE"), "STAND")
    assert row["action"] == "PLACE"
    assert row["unique_highest"] is True


def test_empty_answer_does_not_restore_place(monkeypatch: pytest.MonkeyPatch) -> None:
    row = _evaluate(monkeypatch, _mass(None, empty=True), "PLACE")
    assert row["action"] is None
    assert row["choice"] is None
    assert row["unique_highest"] is False
    assert row["probability"] is None
    assert row["action"] != "FLATTEN_CANDIDATE"
    assert row["action"] != "REMINT"


def test_tie_does_not_restore_first_name(monkeypatch: pytest.MonkeyPatch) -> None:
    row = _evaluate(monkeypatch, _mass(None, tie=True), "PLACE")
    assert row["action"] is None
    assert row["unique_highest"] is False
    assert row["action"] != PLACE_ORDER[0]
    assert row["action"] != "FLATTEN_CANDIDATE"


def test_bare_label_is_not_a_place_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {"n": 0}

    def _fake(state, questions, merge_sleeve=False):
        del state, questions, merge_sleeve
        seen["n"] += 1
        return {
            "answers": {"place": {"choice": "PLACE"}},
            "model": "jev-1.13.0",
        }

    monkeypatch.setattr("src.judgment.jev_client.evaluate", _fake)
    row = evaluate_place_choice(_Intent(), namespace="operator", login=0)
    assert seen["n"] == 1
    assert row["action"] is None
    assert row["unique_highest"] is False
    assert row["broker_effect"] is False
