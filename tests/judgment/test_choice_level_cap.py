"""A Choice wider than the refusal's maximum is reposted inside that maximum."""

from __future__ import annotations

from src.judgment import nineteen
from src.judgment.jev_client import _rewrite_anchors, _thin_posted_scores, _thin_posted_tokens


DETAIL = '{"detail": "Too many choices. Must have at most 255 choices."}'


def _clear() -> None:
    nineteen._LEARNED_LEVEL_CAP.clear()


def test_the_refusal_names_the_choice_maximum():
    _clear()
    try:
        learned = nineteen.note_score_level_cap(DETAIL)
        assert learned == nineteen._cap_from_detail(DETAIL)
        assert learned is not None
    finally:
        _clear()


def test_a_choice_wider_than_the_refusal_keeps_the_ends():
    _clear()
    try:
        learned = nineteen.note_score_level_cap(DETAIL)
        assert learned is not None
        wide = {f"bars_present_{step}": f"bars_present_{step} ({step})" for step in range(1, learned + 5)}
        wire = {
            "warmup_bars": {
                "type": "choice",
                "instructions": "The score you return is how many closed bars this state needs.",
                "criteria": wide,
            }
        }
        thinned = _thin_posted_scores(wire, {})
        assert thinned is not None
        criteria = thinned["warmup_bars"]["criteria"]
        assert len(criteria) <= learned
        assert len(criteria) >= 2
        keys = list(criteria)
        assert keys[0] == "bars_present_1"
        assert keys[-1] == f"bars_present_{learned + 4}"
    finally:
        _clear()


def test_a_choice_inside_the_maximum_stays():
    _clear()
    try:
        nineteen.note_score_level_cap(DETAIL)
        wire = {
            "warmup_bars": {
                "type": "choice",
                "instructions": "The score you return is how many closed bars this state needs.",
                "criteria": {"bars_present_1": "1", "bars_present_2": "2"},
            }
        }
        assert _thin_posted_scores(wire, {}) is None
    finally:
        _clear()


def test_a_token_refusal_keeps_the_ends_of_a_choice():
    wide = {f"bars_present_{step}": str(step) for step in range(1, 9)}
    wire = {
        "warmup_bars": {
            "type": "choice",
            "instructions": "The score you return is how many closed bars this state needs.",
            "criteria": wide,
        }
    }
    thinned = _thin_posted_tokens(wire, {})
    assert thinned is not None
    criteria = thinned["warmup_bars"]["criteria"]
    assert len(criteria) < len(wide)
    keys = list(criteria)
    assert keys[0] == "bars_present_1"
    assert keys[-1] == "bars_present_8"
    again = _thin_posted_tokens(thinned, {})
    assert again is None or len(again["warmup_bars"]["criteria"]) < len(criteria)


def test_a_choice_of_two_is_not_cut_for_tokens():
    wire = {
        "warmup_bars": {
            "type": "choice",
            "instructions": "The score you return is how many closed bars this state needs.",
            "criteria": {"bars_present_1": "1", "bars_present_2": "2"},
        }
    }
    assert _thin_posted_tokens(wire, {}) is None


def test_a_score_thinned_after_a_token_refusal_returns_the_picked_level():
    criteria = [f"level_{step}" for step in range(8)]
    original = [(label, float((index + 1) * 10)) for index, label in enumerate(criteria)]
    anchors = {"atr_floor": list(original)}
    wire = {
        "atr_floor": {
            "type": "score",
            "instructions": "The score you return is the ATR floor for this state.",
            "criteria": list(criteria),
        }
    }
    thinned = _thin_posted_tokens(wire, anchors)
    assert thinned is not None
    posted = thinned["atr_floor"]["criteria"]
    levels = anchors["atr_floor"]
    assert len(levels) == len(posted)
    picked = 1
    answers = {"atr_floor": {"score": picked, "probabilities": {str(picked): 1.0}}}
    rewritten = _rewrite_anchors(answers, anchors)
    assert rewritten["atr_floor"]["score"] == levels[picked][1]
    assert levels[picked][1] != original[picked][1]
