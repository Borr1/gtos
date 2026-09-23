"""s19 usage-observe + s20 Dig E hard-off. Never mutate skip. Never block place."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.judgment.a1_log import a1_enabled
from src.judgment.book_owner_observe_splice import (
    S16_ON_CHALLENGE_PLACE,
    observe_before_continue,
    observe_every_on,
    usage_observe_on,
)
from src.judgment.challenge import CHALLENGE_LOGIN
from src.judgment.s16_flags import (
    APPLY_ENV,
    CHALLENGE_PLACE_PATH_DUAL_FLAG,
    SHADOW_ENV,
    dig_guard_on_challenge_place,
    s16_apply_enabled,
)
from src.judgment.s16_guard import GuardResult, maybe_write_shadow_row

REPO = Path(__file__).resolve().parents[2]
OWNER = REPO / "src" / "components" / "ultimate_book" / "book_owner.py"
SPLICE = REPO / "src" / "judgment" / "book_owner_observe_splice.py"
RECEIPT = REPO / "judgment" / "astra" / "lab" / "s19_s20_land" / "RECEIPT.json"


def test_usage_observe_on_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "GTOS_JEV_A1_LOG",
        "GTOS_JEV_ALIVE_SHADOW",
        "GTOS_JEV_A1_OBSERVE_EVERY",
        "A1_OBSERVE_EVERY",
    ):
        monkeypatch.delenv(name, raising=False)
    assert usage_observe_on() is False
    assert observe_every_on() is False
    assert a1_enabled() is False


def test_usage_observe_on_a1_log(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GTOS_JEV_ALIVE_SHADOW", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_OBSERVE_EVERY", raising=False)
    monkeypatch.delenv("A1_OBSERVE_EVERY", raising=False)
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")
    assert usage_observe_on() is True
    assert observe_every_on() is False
    assert a1_enabled() is True


def test_usage_observe_on_every_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GTOS_JEV_A1_LOG", raising=False)
    monkeypatch.delenv("GTOS_JEV_ALIVE_SHADOW", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_OBSERVE_EVERY", raising=False)
    monkeypatch.setenv("A1_OBSERVE_EVERY", "1")
    assert observe_every_on() is True
    assert usage_observe_on() is True
    assert a1_enabled() is True


def test_observe_before_continue_never_mutates_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")
    monkeypatch.setenv("GTOS_JEV_A1_OBSERVE_EVERY", "1")
    intent = SimpleNamespace(
        symbol="XAUUSD",
        sleeve="crypto",
        stop_dist=5.0,
        side="short",
        entry=2300.0,
        stop=2305.0,
        target=2290.0,
        candidate_id="s19-no-mutate",
    )
    tick = SimpleNamespace(bid=2300.0, ask=2300.2)
    cost = "spread_r_above_max"
    row = {
        "symbol": "XAUUSD",
        "sleeve": "crypto",
        "reason": "already_placed_this_bar",
    }
    snapshot = dict(row)
    assert observe_before_continue(intent, tick, cost_skip=cost) is None
    assert cost == "spread_r_above_max"
    assert observe_before_continue(intent, tick, skipped_row=row) is None
    assert row == snapshot


def test_observe_before_continue_never_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GTOS_JEV_A1_LOG", "1")
    monkeypatch.setenv("A1_OBSERVE_EVERY", "1")
    observe_before_continue(object(), object(), cost_skip="x")
    observe_before_continue(object(), None, skipped_row={"reason": "no_tick_transient"})


def test_skip_decision_stays_caller_owned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GTOS_JEV_A1_LOG", raising=False)
    monkeypatch.delenv("GTOS_JEV_A1_OBSERVE_EVERY", raising=False)
    monkeypatch.delenv("A1_OBSERVE_EVERY", raising=False)
    cost_skip = "spread_r_above_max"
    observe_before_continue(SimpleNamespace(symbol="XAUUSD"), None, cost_skip=cost_skip)
    assert cost_skip == "spread_r_above_max"


def test_challenge_writer_identity() -> None:
    assert CHALLENGE_LOGIN == "0"
    assert S16_ON_CHALLENGE_PLACE is False
    assert CHALLENGE_PLACE_PATH_DUAL_FLAG is False
    assert dig_guard_on_challenge_place() is False


def test_splice_and_owner_never_carry_dig_dual_flag() -> None:
    splice = SPLICE.read_text(encoding="utf-8")
    owner = OWNER.read_text(encoding="utf-8")
    assert "DIG_MULTI_STAGE_GUARD" not in splice
    assert "DIG_MULTI_STAGE_GUARD" not in owner
    assert "s16_guard" not in splice
    assert "from src.judgment.s16" not in owner
    tree = ast.parse(splice, filename=str(SPLICE))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = {alias.name for alias in node.names}
            assert "s16_guard" not in names
            assert "s16_flags" not in names
            assert not mod.endswith("s16_guard")
            assert not mod.endswith("s16_flags")


def test_splice_never_invents_news_protocol() -> None:
    splice = SPLICE.read_text(encoding="utf-8")
    assert "Never invents NEWS_PROTOCOL" in splice
    tree = ast.parse(splice, filename=str(SPLICE))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == "NEWS_PROTOCOL":
            raise AssertionError("splice must not invent NEWS_PROTOCOL")


def test_owner_wires_cost_skip_and_skipped_row() -> None:
    owner = OWNER.read_text(encoding="utf-8")
    assert "observe_before_continue" in owner
    assert "cost_skip=cost_skip" in owner
    assert "skipped_row=skipped_row" in owner or "skipped_row=summary[\"skipped\"][-1]" in owner
    assert owner.count("_observe_skip_continue") >= 16
    assert "maybe_observe_ub_plc_017" in owner
    assert "maybe_observe_fluid_at_place" in owner
    cost_i = owner.index("cost_skip = self._spread_cost_screen")
    assert owner.index("maybe_observe_ub_plc_017") > cost_i
    assert owner.index("cost_skip=cost_skip") > cost_i


def test_observe_only_harness_must_not_block_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(APPLY_ENV, "1")
    monkeypatch.setenv(SHADOW_ENV, "1")
    assert s16_apply_enabled() is True
    assert dig_guard_on_challenge_place() is False
    row = GuardResult(tool="order_send", fixture_id="dig-e-kill", stage="tool_pre")
    path = maybe_write_shadow_row(row, log_dir=tmp_path, force=False)
    assert path is None
    assert list(tmp_path.rglob("*.json")) == []


def test_receipt_pack1b_not_beaten() -> None:
    import json

    doc = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert doc["pack1b_beaten"] is False
    assert doc["login"] == "0"
    assert doc["news_protocol_invented"] is False
    assert doc["s20"]["observe_only_blocks_place"] is False
    assert doc["s20"]["dual_flag_on_challenge_place"] is False
