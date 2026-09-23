"""19 and 11 are the only planted decision numbers in the spine.

Boolean plumbing in the spine is True and False.
Integer plumbing 0 and 1 does not appear. Empty stays None, or a computed sum.
An empty score does not come back as a leftover constant.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import src.judgment as judgment
import src.judgment.nineteen as nineteen
import src.judgment.place_gate as place_gate
from src.judgment.book_engine_choices import QUESTIONS, last_bar_question_text

SPINE = ROOT / "src" / "judgment" / "nineteen.py"
_ALLOWED = {19, 11}
_OLD = (1.5, 2, 32)
_BANNED_BODY = ("jev", "system one", "systemone")

# Boolean plumbing listed for the AST walk. Not decision integers.
PLUMBING_BOOLS = (True, False)
# Integer 0 and 1 are absent from the spine.
PLUMBING_INTS = ()


def _literals(path: Path) -> list[int | float]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[int | float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            found.append(node.value)
    return found


def _parents(tree: ast.AST, nodes: list[ast.AST]) -> list[ast.AST]:
    wanted = set(id(node) for node in nodes)
    found: dict[int, ast.AST] = {}

    def walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if id(child) in wanted:
                found[id(child)] = node
            walk(child)

    walk(tree)
    return [found[id(node)] for node in nodes]


def _bools(path: Path) -> list[bool]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[bool] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            found.append(node.value)
    return found


def _independent_fold(value: int, remainder: int | None = None) -> int:
    current = abs(int(value))
    stop = None if remainder is None else abs(int(remainder))
    seen: list[int] = []
    while True:
        if current == 19 or (stop is not None and current == stop):
            return current
        if current in seen:
            return current
        seen.append(current)
        nxt = sum(int(ch) for ch in str(current) if ch.isdigit())
        if nxt == current:
            return current
        current = nxt


def test_spine_plants_only_19_and_11() -> None:
    found = _literals(SPINE)
    assert found, "the spine should plant 19 and 11"
    extra = [value for value in found if value not in _ALLOWED]
    assert extra == [], extra
    assert set(found) == _ALLOWED
    assert PLUMBING_INTS == ()
    assert set(_bools(SPINE)) == set(PLUMBING_BOOLS)
    text = SPINE.read_text(encoding="utf-8")
    assert "import random" not in text
    init_tree = ast.parse((ROOT / "src" / "judgment" / "__init__.py").read_text(encoding="utf-8"))
    clobber = [
        node
        for node in ast.walk(init_tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "nineteen" for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and node.value.value is None
    ]
    assert clobber
    assert all(isinstance(node, ast.ExceptHandler) for node in _parents(init_tree, clobber))


def test_import_stays_a_module() -> None:
    assert nineteen.DENOMINATOR == 19
    assert nineteen.OTHER == 11
    assert judgment.nineteen is nineteen
    assert callable(nineteen.write_import_stamp)
    assert nineteen.write_import_stamp() is None
    assert callable(place_gate.place_apply_enabled)


def test_residue_and_fold_are_computed() -> None:
    assert nineteen.residue(nineteen.DENOMINATOR) == _independent_fold(0) or nineteen.residue(nineteen.DENOMINATOR) == 0
    assert nineteen.residue(nineteen.DENOMINATOR) == 0
    assert nineteen.residue(nineteen.OTHER) == nineteen.OTHER
    assert nineteen.divides(nineteen.DENOMINATOR) is True
    assert nineteen.divides(nineteen.OTHER) is False
    assert nineteen.shares_denominator(nineteen.DENOMINATOR * 5) is True
    assert nineteen.digit_fold(nineteen.DENOMINATOR) == nineteen.DENOMINATOR
    assert nineteen.fold(nineteen.DENOMINATOR) == nineteen.DENOMINATOR
    assert nineteen.digit_fold(nineteen.OTHER) == _independent_fold(nineteen.OTHER)
    for sample in (0, 5, 11, 19, 29, 38, 99, 114, 334, 6346, 8534):
        assert nineteen.residue(sample) == sample % 19
        assert nineteen.fold(sample) == _independent_fold(sample)
    assert nineteen.fold(29, remainder=11) == 11
    assert nineteen.digit_sum(6346) == 6 + 3 + 4 + 6
    seen: list[int] = []
    real = nineteen.digit_sum

    def wrapped(value: int) -> int | None:
        seen.append(value)
        return real(value)

    nineteen.digit_sum = wrapped
    try:
        assert nineteen.fold(6346) == 19
    finally:
        nineteen.digit_sum = real
    assert seen
    assert nineteen.letter_total("Basmalah") == len("Basmalah")
    assert nineteen.letter_total("a" * nineteen.DENOMINATOR, "a") == nineteen.DENOMINATOR


def test_checksum_and_seed_do_not_invent_a_factor() -> None:
    counts = {"Q": 19, "N": 11, "S": 19, "Y.S.": 11, "extra": 3}
    row = nineteen.checksum(counts)
    assert isinstance(row, dict)
    assert row["sum"] == 19 + 11 + 19 + 11 + 3
    assert "factor" not in row
    assert row["residue"] == row["sum"] % 19
    assert row["shares"] is (row["sum"] % 19 == 0)
    assert row["fold"] == nineteen.fold(row["sum"])
    mix = nineteen.seed_mix()
    assert mix["product"] == nineteen.DENOMINATOR * nineteen.OTHER
    assert mix["sum"] == nineteen.DENOMINATOR + nineteen.OTHER
    assert nineteen.product_denominator(nineteen.OTHER) == mix["product"]
    assert nineteen.product(nineteen.OTHER, nineteen.DENOMINATOR) == mix["product"]
    assert nineteen.product("other", nineteen.DENOMINATOR) == mix["product"]
    assert nineteen.seed_mix("ab") == nineteen.residue(nineteen.letter_total("ab") + nineteen.OTHER)
    assert nineteen.letter_count("Basmalah") == len("Basmalah")
    asked = nineteen.quantity(
        {"symbol": "XAUUSD"},
        question_id="clock_skew_seconds",
        instructions="seconds",
        ask=lambda *a, **k: {"ok": False, "error": "empty", "answers": {}},
    )
    assert asked is None
    assert nineteen.length(("XAUUSD", "XAGUSD", "XPTUSD")) == 3
    assert nineteen.total(()) == 0


def test_empty_score_does_not_restore_a_constant() -> None:
    import src.judgment.jev_client as client

    original = client.evaluate

    def _empty(*_args, **_kwargs):
        return {"ok": False, "error": "empty", "answers": {}, "skipped": "empty"}

    client.evaluate = _empty
    try:
        assert nineteen.score({"symbol": "XAUUSD"}, question_id="clock_skew_seconds", instructions="seconds") is None
        for role in nineteen.ROLES:
            got = nineteen.quantity(role, {"symbol": "XAGUSD"})
            assert got is None
            for old in _OLD:
                assert got != old
            assert got != nineteen.DENOMINATOR
    finally:
        client.evaluate = original


def test_tie_does_not_restore_a_score() -> None:
    def tied(state, questions, merge_sleeve=False):
        del questions, merge_sleeve
        role = state["role"]
        return {
            "ok": True,
            "answers": {
                role: {"score": 1.5, "probabilities": {"none": 0.5, "trace": 0.5}},
                "jev_call_timeout": {"score": 32},
            },
        }

    assert nineteen.quantity("atr_multiple", {"symbol": "XAUUSD"}, ask=tied) is None
    assert nineteen.quantity("size", {"symbol": "XPTUSD"}, ask=lambda *a, **k: {"ok": False, "answers": {"size": {"score": 2}}}) is None
    assert nineteen.product_denominator(None, {"symbol": "XAUUSD"}, ask=lambda *a, **k: {"ok": True, "answers": {}}) is None


def test_body_does_not_name_the_judge() -> None:
    def ask(state, questions, merge_sleeve=False):
        assert merge_sleeve is False
        role = state["role"]
        blob = json.dumps({"questions": questions, "state": {k: state[k] for k in state if k != "prior_outcomes"}}).lower()
        for word in _BANNED_BODY:
            assert word not in blob
        assert state["order_kind"] == "limit"
        assert "silver" in questions[role]["instructions"]
        return {"ok": True, "answers": {role: {"score": 7.25, "probabilities": {"modest": 0.7, "small": 0.2}}}}

    assert nineteen.quantity("size", {"symbol": "XPTUSD"}, ask=ask) == 7.25


def test_last_bar_question_carries_the_close() -> None:
    spec = QUESTIONS["last_bar"]
    assert spec["id"] == "be_last_bar"
    assert tuple(spec["criteria"]) == (
        "closed_bar_reaches",
        "use_previous_close",
        "closed_bar_does_not_reach",
    )
    text = last_bar_question_text(
        {
            "symbol": "XAGUSD",
            "sleeve": "metals_core",
            "open": 31.0,
            "high": 31.8,
            "low": 31.0,
            "close": 31.2,
            "range_to_low": 0.2,
            "range_to_high": 0.6,
            "bid": 31.1,
            "ask": 31.3,
            "decision_bar_iso": "2026-09-22T13:00:00+00:00",
            "seconds_from_clock": 19,
        }
    )
    for piece in (
        "Symbol XAGUSD",
        "Sleeve metals_core",
        "Open 31",
        "High 31.8",
        "Low 31",
        "Close 31.2",
        "Bid 31.1",
        "Ask 31.3",
        "Seconds from the clock 19",
        "closed_bar_reaches",
        "use_previous_close",
        "closed_bar_does_not_reach",
        "does not restore a skip",
    ):
        assert piece in text, piece
    assert "unit_long" not in text


def test_engine_asks_last_bar_before_the_clock_gate() -> None:
    engine = (ROOT / "src" / "components" / "ultimate_book" / "book_engine.py").read_text(encoding="utf-8")
    ask = engine.find('"last_bar"')
    gate = engine.find("> 30.0")
    assert 0 < ask < gate
    assert "else:" in engine[ask:gate]
    assert "_closed_bar_card" in engine
    assert "closed_bar_does_not_reach" in engine


def _run() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for fn in tests:
        fn()
        print("PASS", fn.__name__)


if __name__ == "__main__":
    _run()
