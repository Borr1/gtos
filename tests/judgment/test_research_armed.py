"""Chair Module_ATR research overlay + SHADOW/APPLY enable path.

Research tags are STATE/alive overlay only. They never splice
``config/live_armed_set.json``. Jev never ``order_send``.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.alive_menu import rebuild_choice_criteria
from src.judgment.cycle import run_fluid_gate_cycle
from src.judgment.flags import APPLY_ENV, SHADOW_ENV, apply_enabled, shadow_enabled
from src.judgment.inventory import collect_live_inventory, inventory_fingerprint
from src.judgment.p0_hist_prove import hist_prove_allows_label_apply
from tests.judgment.cages import assert_live_cages
from src.judgment.research_armed import (
    MODULE_ATR_WINNER_TAGS,
    attach_research_overlay,
    live_armed_set_contains,
    load_research_armed_tags,
    research_armed_tag_names,
)

REPO = Path(__file__).resolve().parents[2]
LIVE_ARMED_SET = REPO / "config" / "live_armed_set.json"
RESEARCH_JSON = REPO / "judgment" / "astra" / "research_armed_tags.json"
RECIPE = REPO / "judgment" / "CHAIR_LAND_RECIPE_VPS_F5_LIVE.md"


def _inventory(**kwargs):
    return collect_live_inventory(
        sleeves=kwargs.get("sleeves", ("spring", "vss")),
        workers=kwargs.get("workers", ("challenge:0",)),
        handlers=kwargs.get("handlers", ("shadow_log", "label_draft")),
        include_w7_armed=False,
        include_launcher_workers=False,
        include_research_armed=kwargs.get("include_research_armed", True),
    )


def test_module_atr_winner_tags_are_the_named_pair() -> None:
    assert MODULE_ATR_WINNER_TAGS == (
        "dsp_three_fresh_lower_lows",
        "dsp_spring_close_on_20low_through_the_box",
    )
    doc = load_research_armed_tags()
    assert doc["missing_authority"] is False
    assert doc["module"] == "Module_ATR"
    assert doc["status"] == "research_overlay_only"
    assert doc["live_armed_set_mutated"] is False
    assert doc["place"] == "writer_only"
    assert doc["never_order_send"] is True
    assert doc["hard_off_keep_research"] is False
    assert tuple(doc["tags"]) == MODULE_ATR_WINNER_TAGS
    assert research_armed_tag_names() == MODULE_ATR_WINNER_TAGS
    assert "US30_cash" not in doc["surface"]


def test_research_json_is_not_a_fabricated_scoreboard() -> None:
    raw = json.loads(RESEARCH_JSON.read_text(encoding="utf-8"))
    banned = (
        "scoreboard",
        "win_rate",
        "expectancy",
        "p_pass",
        "net_r",
        "monthly_r",
        "fabricated",
    )
    blob = json.dumps(raw).lower()
    for key in banned:
        assert key not in raw
        assert key not in blob
    assert raw["status"] == "research_overlay_only"
    assert raw["live_armed_set_mutated"] is False
    notes = raw.get("tag_notes") or {}
    for tag in MODULE_ATR_WINNER_TAGS:
        assert notes[tag]["not_armed"] is True
        assert notes[tag]["status"] == "forward_only"


def test_missing_authority_returns_empty_tags(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    doc = load_research_armed_tags(path=missing)
    assert doc["tags"] == []
    assert doc["missing_authority"] is True
    assert doc["live_armed_set_mutated"] is False
    assert doc["place"] == "writer_only"


def test_research_tags_are_not_in_live_armed_set() -> None:
    armed = json.loads(LIVE_ARMED_SET.read_text(encoding="utf-8"))
    named: set[str] = set()
    for block in (armed.get("accounts") or {}).values():
        named.update(block.get("armed_sleeves") or [])
    for tag in MODULE_ATR_WINNER_TAGS:
        assert tag not in named
        assert live_armed_set_contains(tag) is False


def test_inventory_puts_tags_on_research_overlay_not_fire_sleeves() -> None:
    inv = _inventory()
    assert inv.research_armed_tags == MODULE_ATR_WINNER_TAGS
    for tag in MODULE_ATR_WINNER_TAGS:
        assert tag not in inv.sleeves
    assert "research_armed_tags" in inv.notes
    # Fingerprint stays fire-only — research overlay must not move it.
    assert inv.fingerprint == inventory_fingerprint(
        inv.sleeves, inv.workers, inv.handlers, inv.blocked_sleeves
    )


def test_injected_research_names_are_stripped_from_fire_sleeves() -> None:
    inv = _inventory(sleeves=("spring",) + MODULE_ATR_WINNER_TAGS)
    assert "spring" in inv.sleeves
    for tag in MODULE_ATR_WINNER_TAGS:
        assert tag not in inv.sleeves
        assert tag in inv.research_armed_tags


def test_alive_menu_offers_research_sleeve_not_live_sleeve() -> None:
    menu = rebuild_choice_criteria(_inventory())
    for tag in MODULE_ATR_WINNER_TAGS:
        assert f"research_sleeve:{tag}" in menu.option_ids
        assert f"sleeve:{tag}" not in menu.option_ids
        assert f"research_armed_overlay:{tag}" in menu.notes
    crit = next(c for c in menu.criteria if c.id.endswith(MODULE_ATR_WINNER_TAGS[0]))
    assert "live_armed_set splice" in crit.not_for
    assert "order_send" in crit.not_for


def test_attach_research_overlay_copies_state_without_armed_set_mutation() -> None:
    gold = {"identity": {"keep_signature": True, "ticket": "291816474"}}
    out = attach_research_overlay(gold)
    assert out["identity"]["keep_signature"] is True
    assert out["identity"]["ticket"] == "291816474"
    assert out["identity"]["research_armed_tags"] == list(MODULE_ATR_WINNER_TAGS)
    assert out["research_armed_tags"] == list(MODULE_ATR_WINNER_TAGS)
    overlay = out["identity"]["research_overlay"]
    assert overlay["live_armed_set_mutated"] is False
    assert overlay["place"] == "writer_only"
    assert overlay["never_order_send"] is True
    assert overlay["hard_off_keep_research"] is False
    assert gold["identity"].get("research_armed_tags") is None


def test_hist_prove_allows_label_apply_only_when_keep_wins_preserved() -> None:
    committed = hist_prove_allows_label_apply()
    assert committed["allowed"] is True
    assert committed["wins_preserved"] is True
    assert committed["hard_off_keep_research"] is False
    assert_live_cages(committed)

    missing = hist_prove_allows_label_apply(path=Path("/tmp/no-such-fire1201.json"))
    assert missing["allowed"] is False
    assert missing["reason"] == "hist_prove_receipt_missing"

    lost = hist_prove_allows_label_apply(
        receipt={"wins_preserved": False, "hard_off_keep_research": False}
    )
    assert lost["allowed"] is False
    assert lost["reason"] == "hist_prove_keep_wins_not_preserved"

    hard = hist_prove_allows_label_apply(
        receipt={
            "wins_preserved": True,
            "research_candidate": {"hard_off_keep_research": True},
        }
    )
    assert hard["allowed"] is False
    assert hard["reason"] == "hist_prove_hard_off_keep_research"


def test_shadow_required_apply_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SHADOW_ENV, raising=False)
    monkeypatch.delenv("GTOS_JEV_EVERYWHERE_SHADOW", raising=False)
    monkeypatch.delenv(APPLY_ENV, raising=False)
    assert shadow_enabled() is False
    assert apply_enabled() is False
    monkeypatch.setenv(SHADOW_ENV, "1")
    assert shadow_enabled() is True
    assert apply_enabled() is False


def test_cycle_stamps_research_overlay_and_never_places(tmp_path: Path) -> None:
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        gold_state={"identity": {"ticket": "research-overlay"}},
        log_dir=tmp_path,
        force=True,
        apply_flag=False,
    )
    assert result.apply.apply is False
    assert result.apply_path is None
    assert "chair_research_armed_overlay_module_atr" in result.notes
    assert result.inventory.research_armed_tags == MODULE_ATR_WINNER_TAGS
    assert result.warroom_shadow is not None
    pack = result.warroom_shadow.as_dict()
    assert pack["apply"] is False
    assert pack["never_place"] is True
    assert pack["research_armed_tags"] == list(MODULE_ATR_WINNER_TAGS)
    assert pack["research_overlay"]["live_armed_set_mutated"] is False
    doc = json.loads(result.log_path.read_text(encoding="utf-8"))
    assert doc["inventory"]["research_armed_tags"] == list(MODULE_ATR_WINNER_TAGS)
    assert doc["inventory"]["live_armed_set_mutated"] is False
    assert doc["inventory"]["place"] == "writer_only"
    assert_live_cages(doc)
    assert doc["broker_effect"] is False


def test_cycle_label_apply_refused_when_hist_prove_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.judgment.cycle.hist_prove_allows_label_apply",
        lambda **_k: {
            "allowed": False,
            "reason": "hist_prove_keep_wins_not_preserved",
            "wins_preserved": False,
        },
    )
    prove = tmp_path / "prove"
    prove.mkdir()
    (prove / "UB-AUTH-010.json").write_text(
        json.dumps(
            {
                "site_id": "UB-AUTH-010",
                "wire_class": "A1",
                "proven": True,
                "owner_word": "chair",
            }
        ),
        encoding="utf-8",
    )
    result = run_fluid_gate_cycle(
        inventory=_inventory(),
        answers={
            "next_gate": {
                "choice": "LABEL",
                "confidence": 0.7,
                "probabilities": {"LABEL": 0.7},
            }
        },
        stake="label_assist",
        log_dir=tmp_path / "logs",
        prove_dir=prove,
        prove_site_id="UB-AUTH-010",
        force=True,
        apply_flag=True,
    )
    assert result.apply.apply is False
    assert result.apply.reason == "hist_prove_keep_wins_not_preserved"
    assert result.apply_path is None


def test_research_armed_module_has_no_order_send() -> None:
    src = (REPO / "src" / "judgment" / "research_armed.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            assert name not in {"order_send", "open_trade"}
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lower()
            assert "mt5" not in mod
            assert "book_owner" not in mod


def test_chair_land_recipe_names_enable_env_and_prove() -> None:
    text = RECIPE.read_text(encoding="utf-8")
    assert "GTOS_JEV_FLUID_GATES_SHADOW" in text
    assert "GTOS_JEV_FLUID_GATES_APPLY" in text
    assert "GTOS_DIG_MULTI_STAGE_GUARD_APPLY" in text
    assert "run_p0_shadow_hooks_historical_prove.py" in text
    assert "wins_preserved" in text
    assert "dsp_three_fresh_lower_lows" in text
    assert "live_armed_set.json" in text
    assert "order_send" in text
    assert "NEWS_PROTOCOL" in text
    assert "0" in text
