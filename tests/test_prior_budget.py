"""Prior history must fit the POST the API already accepted."""

import sys
import types

_challenge = types.ModuleType("src.judgment.challenge")
_challenge.CHALLENGE_LOGIN = 0
_challenge.CHALLENGE_MAGIC = 0
_challenge.CHALLENGE_NS = "operator"
sys.modules.setdefault("src.judgment.challenge", _challenge)

from src.judgment.jev_questions import BODY_BUDGET, _body_len, _folded_history


def _score_row(index: int) -> dict:
    return {
        "spot": "size_cash",
        "value": 0.5,
        "at_utc": f"2026-01-01T00:00:{index:05d}Z",
        "ticket": 294356559,
        "symbol": "GBPUSD",
        "sleeve": "dsp_wide_down",
        "realized_closed_profit": -189.62,
    }


def test_short_score_history_stays_whole():
    rows = [_score_row(1)]
    history = _folded_history(rows, {"equity": 1.0}, {})
    assert history == [
        {
            "spot": "size_cash",
            "value": 0.5,
            "at_utc": "2026-01-01T00:00:00001Z",
            "ticket": 294356559,
            "symbol": "GBPUSD",
            "sleeve": "dsp_wide_down",
            "realized_closed_profit": -189.62,
        }
    ]


def test_score_history_stays_inside_body_budget():
    rows = [_score_row(i) for i in range(800)]
    state = {"login": 0, "equity": 93524.82, "balance": 93524.82}
    questions = {
        "size_cash": {
            "type": "score",
            "instructions": "What cash does the next unit risk?",
            "criteria": ["none", "trace", "small", "modest", "notable", "heavy"],
        }
    }
    history = _folded_history(rows, state, questions)
    size = _body_len({**state, "prior_outcomes": history}, questions)
    assert size <= BODY_BUDGET
    assert history != rows
