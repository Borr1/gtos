"""SHADOW unlock remasure — 45 non-XAU sufficient rows use symbol_state.

Never place. Never APPLY. US30 stays house hard-off.
"""

from src.judgment.compose import compose_shadow
from tests.judgment.cages import assert_live_cages
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.non_xau_remeasure import (
    GRID_SPEC,
    NON_XAU_REMEASURE_N,
    NON_XAU_REMEASURE_SYMBOLS,
    SCHEMA,
    US30_HARD_OFF_SLEEVE,
    assemble_grid_row,
    gold_default_leaks,
    iter_grid_as_ofs,
    remasure_non_xau_sufficient,
)
from src.judgment.symbol_class import field_map
from src.judgment.symbol_state import SCHEMA as SYMBOL_SCHEMA
from tests.judgment.test_symbol_state import EMPTY_SPINE


def test_field_map_pins_n_non_xau_sufficient_45():
    mapped = field_map()
    assert mapped["n_non_xau_sufficient"] == 45 == NON_XAU_REMEASURE_N
    assert mapped["non_xau_remeasure_symbols"] == list(NON_XAU_REMEASURE_SYMBOLS)
    assert mapped["non_xau_uses_symbol_state"] is True
    assert mapped["us30_hard_off"] is True
    assert mapped["never_place"] is True


def test_gold_default_leaks_catches_gold_state_on_eurusd():
    spec = GRID_SPEC["EURUSD"]
    gold = assemble_gold_state_v0(
        as_of_utc=iter_grid_as_ofs()[0],
        side="long",
        sleeve=spec["sleeve"],
        symbol="EURUSD",
        origin_organism="f5_challenge",
        books=spec["books"],
        spines=EMPTY_SPINE,
        geometry=spec["geo"],
        cost={"spread_r_of_stop": 0.05},
        sleeve_features={"tag": spec["sleeve"]},
    )
    leaks = gold_default_leaks(gold, compose_shadow(gold, ticket="gold-default-eur"))
    assert "schema_gold_state_v0" in leaks
    assert "missing_class_specific" in leaks
    assert "news_unfiltered_gold" in leaks
    assert gold.get("gold_state") is None  # it *is* the gold object
    assert gold["identity"]["symbol"] == "EURUSD"


def test_gold_default_leaks_clean_on_symbol_state_eurusd():
    state = assemble_grid_row("EURUSD", iter_grid_as_ofs()[0])
    composed = compose_shadow(state, ticket="symbol-eur")
    assert gold_default_leaks(state, composed) == []
    assert state["schema"] == SYMBOL_SCHEMA
    assert state["gold_state"] is None
    assert composed["named_apply_symbol"] is False
    assert composed["live_size_tilt"] == 1.0
    assert_live_cages(composed, ticket="symbol-eur")


def test_n_non_xau_sufficient_45_shadow_pipe_rejects_gold_defaults():
    receipt = remasure_non_xau_sufficient()
    assert receipt["schema"] == SCHEMA
    assert receipt["n"] == 45
    assert receipt["n_non_xau_sufficient"] == 45
    assert receipt["n_gold_default_leaks"] == 0
    assert receipt["leak_codes"] == {}
    assert receipt["named_apply_symbol"] == 0
    assert receipt["apply_this_row"] == 0
    assert receipt["live_size_tilt_locked"] is True
    assert receipt["live_cost_tilt_locked"] is True
    assert receipt["never_place"] is True
    assert receipt["never_apply"] is True
    assert receipt["admit_choice_emitted"] == 0
    assert receipt["us30_hard_off"] == 9
    assert receipt["us30_off"] == 9
    assert receipt["unlock"] == "non-XAU sufficient rows use symbol_state.v0, not gold-defaults"
    assert receipt["jev_calls"] == "off"
    assert receipt["not_landed_challenge_tape"] is True
    for symbol in NON_XAU_REMEASURE_SYMBOLS:
        bag = receipt["by_symbol"][symbol]
        assert bag["n"] == 9
        assert bag["n_sufficient"] == 9
        assert bag["n_leaks"] == 0
        if symbol == "US30":
            assert bag["n_hard_off"] == 9
        else:
            assert bag["n_hard_off"] == 0
    for row in receipt["rows"]:
        assert row["schema"] == SYMBOL_SCHEMA
        assert row["gold_state_nested"] is False
        assert row["named_apply_symbol"] is False
        assert row["apply_this_row"] is False
        assert row["live_size_tilt"] == 1.0
        assert row["live_cost_tilt"] == 1.0
        assert row["never_place"] is True
        assert row["leaks"] == []
        if row["symbol"] == "US30":
            assert row["family_class"] == "house_hard_off"
            assert row["house_block"] is True
            assert row["asset_class"] == "index"
        else:
            assert row["asset_class"] == "fx"
            assert row["family_class"] != "house_hard_off"


def test_us30_sleeve_stays_hard_off_on_grid():
    assert GRID_SPEC["US30"]["sleeve"] == US30_HARD_OFF_SLEEVE
    state = assemble_grid_row("US30", iter_grid_as_ofs()[0])
    assert state["identity"]["family_class"] == "house_hard_off"
    assert state["surface"]["us30_off"] is True
    assert state["class_specific"]["index"]["house_us30_off"] is True
    composed = compose_shadow(state, ticket="us30-off")
    assert composed["house_block"] is True
    assert composed["named_apply_symbol"] is False
    assert composed["live_size_tilt"] == 1.0
