"""The lot hop carries the calculated lot on the card. It does not invent a send."""
from __future__ import annotations

import src.judgment.execution_choices as ec
import src.judgment.jev_questions as jq


def test_lot_card_carries_the_calculated_lot(tmp_path, monkeypatch):
    seen = {}

    def ask(state, *, question_id, instructions, criteria):
        seen["instructions"] = instructions
        seen["state"] = state
        return {
            "choice": "place",
            "probability": 0.7,
            "probabilities": {"place": 0.7, "refuse": 0.3},
            "decision_emitted": True,
        }

    monkeypatch.setattr(jq, "prior_outcomes", lambda **k: [])
    monkeypatch.setattr(jq, "land_choice_return", lambda *a, **k: None)
    row = ec.choose(
        "lot",
        symbol="US500.cash",
        reason="open_trade",
        proposed=0.02,
        facts={
            "lots": 0.02,
            "volume_min": 0.01,
            "sleeve": "mx_us500_cash_d1_atr_mean_reversion",
            "balance": 94258.62,
        },
        ask=ask,
        use_cache=False,
        record=True,
        record_to=tmp_path / "execution_choices.jsonl",
    )
    assert row["choice"] == "place"
    assert row["facts"]["lots"] == 0.02
    assert row["facts"]["volume_min"] == 0.01
    assert "lots=0.02" in seen["instructions"]
    assert "volume_min=0.01" in seen["instructions"]
    assert seen["state"]["facts"]["sleeve"] == "mx_us500_cash_d1_atr_mean_reversion"


def test_lot_empty_ask_does_not_place(tmp_path, monkeypatch):
    def ask(state, *, question_id, instructions, criteria):
        return {"choice": None, "decision_emitted": False, "error": "no_unique_highest"}

    monkeypatch.setattr(jq, "prior_outcomes", lambda **k: [])
    monkeypatch.setattr(jq, "land_choice_return", lambda *a, **k: None)
    row = ec.choose(
        "lot",
        symbol="BTCUSD",
        proposed=0.11,
        facts={"lots": 0.11, "volume_min": 0.01},
        ask=ask,
        use_cache=False,
        record=True,
        record_to=tmp_path / "execution_choices.jsonl",
    )
    assert row["choice"] is None
    assert row["decision_emitted"] is False
    assert row["facts"]["lots"] == 0.11
