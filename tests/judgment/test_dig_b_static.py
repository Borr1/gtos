"""Dig B STATIC APPLY consume — Challenge 0.

Behavioural: KEEP integers stay off, MENU_FILTER refuses relax/alias,
2-stop refuse-remint, GLOBAL shadow KILL, fluid inventory PLACE KILL,
book-owner P1 KEEP envelope. No broker, no redacted_account, no NEWS_PROTOCOL.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.judgment.chair_enforce import (
    SCOPED_EXCEPTION_FORBIDDEN,
    consume_hard_off_keep_off,
    hard_off_reason,
    refuse_scoped_exception,
    stamp_chair_enforce,
)
from src.judgment.chair_static_close import (
    KILL_ALREADY_CLOSED,
    KEEP_REASONS,
    classify_book_owner_reason,
    close_queue,
    consume_keep_envelope,
    consume_kill_already_closed,
    is_keep_envelope,
    is_kill_already_closed,
)
from src.judgment.challenge import CHALLENGE_LOGIN, CHALLENGE_NS
from src.judgment.dig_b_static import (
    APPLY_CANDIDATE_KEEP,
    HARD_OFF_KEEP_OFF_REASONS,
    KILL_ENFORCE_REASONS,
    LOGIN,
    MAGIC,
    MENU_FILTER_KEEP_REASONS,
    NS,
    RECEIPT,
    SCOPED_XAU_CONFLICT_APPLY_UNTOUCHED,
    TWO_STOP_KEEP_REASON,
    VERDICT_APPLY_CONSUME,
    VERDICT_KILL_ENFORCE,
    DigBApplyError,
    HardOffScopedExceptionError,
    consume_verdict,
    refuse_apply_killed,
    static_in_prove_closed,
)
from src.judgment.fluid_gates import (
    EXPECTED_FLUID,
    apply_fluid_inventory_48,
    assert_inventory_shape,
    consume_fluid_inventory_48,
    fluid_inventory_48_place_authorized,
)
from src.judgment.jev_sleeve_select_shadow import (
    APPLY_ENABLED,
    RESTING_SHADOW,
    apply_jev_sleeve_select_shadow,
    apply_jev_sleeve_select_shadow_global,
    global_shadow_enabled,
    scoped_xau_conflict_apply_untouched,
)
from src.judgment.sleeve_select import (
    REFUSED_ALIAS_PACKAGE_B,
    SOFT_RELAX_HOUSE_LAW,
    consume_menu_filter_reasons,
    menu_filter,
)
from src.judgment.two_stop_day_circuit import refuse_remint
from src.judgment.veto import InventedNewsProtocolVeto, refuse_invented_news_protocol

REPO = Path(__file__).resolve().parents[2]
RECEIPT_MD = REPO / "judgment" / "DIG_B_STATIC_APPLY_CONSUME.md"
RECEIPT_JSON = REPO / "judgment" / "astra" / "lab" / "wires" / "DIG_B_STATIC_APPLY_CONSUME.json"
JUDGMENT_SRC = REPO / "src" / "judgment"


def _parse_md_table(heading: str) -> dict[str, str]:
    text = RECEIPT_MD.read_text(encoding="utf-8")
    start = text.index(heading)
    rest = text[start:]
    rows: dict[str, str] = {}
    for line in rest.splitlines():
        if line.startswith("## ") and not line.startswith(heading):
            break
        if not line.startswith("| ") or line.startswith("| reason") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and cells[1] in {VERDICT_APPLY_CONSUME, VERDICT_KILL_ENFORCE}:
            rows[cells[0]] = cells[1]
    return rows


def test_static_board_is_nine_apply_two_kill() -> None:
    closed = static_in_prove_closed()
    assert closed["login"] == LOGIN == CHALLENGE_LOGIN == "0"
    assert closed["ns"] == NS == CHALLENGE_NS == "operator"
    assert closed["magic"] == MAGIC == 0
    assert closed["apply_candidate"] == 9
    assert closed["kill"] == 2
    assert closed["resting_shadow"] == 0
    assert len(APPLY_CANDIDATE_KEEP) == 9
    assert len(KILL_ENFORCE_REASONS) == 2
    assert closed["place"] is False
    assert closed["never_broker_send"] is True
    assert closed["news_protocol_invented"] is False
    assert closed["redacted_account_untouched"] is True
    for name in APPLY_CANDIDATE_KEEP:
        assert consume_verdict(name) == VERDICT_APPLY_CONSUME
        assert closed["apply_consume"][name] == VERDICT_APPLY_CONSUME
    for name in KILL_ENFORCE_REASONS:
        assert consume_verdict(name) == VERDICT_KILL_ENFORCE
        assert closed["kill_enforce"][name] == VERDICT_KILL_ENFORCE


def test_receipt_markdown_and_json_match_integers() -> None:
    static_rows = _parse_md_table("## STATIC_IN_PROVE_CHAIR_LIST")
    assert static_rows == {
        **{name: VERDICT_APPLY_CONSUME for name in APPLY_CANDIDATE_KEEP},
        **{name: VERDICT_KILL_ENFORCE for name in KILL_ENFORCE_REASONS},
    }
    p1_rows = _parse_md_table("## CHAIR_STATIC_CLOSE_QUEUE")
    assert p1_rows == {
        **{name: VERDICT_APPLY_CONSUME for name in KEEP_REASONS},
        **{name: VERDICT_KILL_ENFORCE for name in KILL_ALREADY_CLOSED},
    }
    payload = json.loads(RECEIPT_JSON.read_text(encoding="utf-8"))
    assert payload["receipt"] == RECEIPT
    assert payload["login"] == "0"
    assert payload["apply_candidate"] == 9
    assert payload["kill"] == 2
    assert payload["resting_shadow"] == 0
    assert payload["scoped_exception_forbidden"] is True
    assert payload["static_in_prove"] == static_rows
    assert payload["p1_keep_envelope"] == {name: VERDICT_APPLY_CONSUME for name in KEEP_REASONS}
    assert payload["p1_kill_already_closed"] == {
        name: VERDICT_KILL_ENFORCE for name in KILL_ALREADY_CLOSED
    }


def test_hard_off_keep_off_no_scoped_exception() -> None:
    assert SCOPED_EXCEPTION_FORBIDDEN is True
    mapping = {
        ("dsp_bleed_acc", "XAUUSD"): "chair_bleed_hard_off",
        ("orb_crypto_london", "ETHUSD"): "chair_orb_crypto_hard_off",
        ("xa_huge_20_extreme", "EURUSD"): "chair_xa_huge_hard_off",
        ("mx_us30_break", "XAUUSD"): "chair_mx_us30_hard_off",
        ("idxrev", "UK100.cash"): "chair_g_index_hard_off",
        ("dsp_walked_hi", "US30.cash"): "chair_g_index_hard_off",
    }
    for (sleeve, symbol), reason in mapping.items():
        assert hard_off_reason(sleeve=sleeve, symbol=symbol) == reason
        stamp = stamp_chair_enforce(sleeve=sleeve, symbol=symbol)
        assert stamp.hard_off is True
        assert stamp.hard_off_reason == reason
        assert stamp.verdict == VERDICT_APPLY_CONSUME
        assert stamp.scoped_exception_forbidden is True
        assert "scoped_exception_forbidden" in stamp.notes
        assert stamp.size_ceiling <= 1.0
    consumed = consume_hard_off_keep_off()
    assert tuple(consumed) == HARD_OFF_KEEP_OFF_REASONS
    with pytest.raises(HardOffScopedExceptionError):
        refuse_scoped_exception({"exception": "SCOPED_EXCEPTION", "sleeve": "bleed"})
    with pytest.raises(HardOffScopedExceptionError):
        stamp_chair_enforce(
            sleeve="dsp_bleed_acc",
            symbol="XAUUSD",
            chair_doc={"decisions": {}, "note": "SCOPED_EXCEPTION for bleed"},
        )
    keep = stamp_chair_enforce(sleeve="dsp_spring_close", symbol="XAUUSD")
    assert keep.hard_off is False
    assert keep.keep_family is True
    assert keep.verdict is None


def test_menu_filter_keep_refuses_relax_and_package_b() -> None:
    relax = menu_filter(sleeve="dsp_spring_close", symbol="XAUUSD", relax_house_law=True)
    assert relax.allow is False
    assert relax.reason == SOFT_RELAX_HOUSE_LAW
    assert relax.verdict == VERDICT_APPLY_CONSUME
    alias = menu_filter(sleeve="package_b", alias_to="sub_mid_dn_revert")
    assert alias.allow is False
    assert alias.reason == REFUSED_ALIAS_PACKAGE_B
    starve = menu_filter(sleeve="sub_mid_dn_revert", symbol="EURUSD")
    assert starve.allow is False
    assert starve.reason == REFUSED_ALIAS_PACKAGE_B
    hard = menu_filter(sleeve="orb_crypto_london", symbol="ETHUSD")
    assert hard.allow is False
    assert hard.reason == "chair_orb_crypto_hard_off"
    assert hard.verdict == VERDICT_APPLY_CONSUME
    keep = menu_filter(sleeve="vss_fxcross_london_up_low", symbol="EURGBP")
    assert keep.allow is True
    assert keep.reason is None
    menu = consume_menu_filter_reasons()
    assert tuple(menu) == MENU_FILTER_KEEP_REASONS


def test_two_stop_refuse_remint_keep() -> None:
    doc = {
        "closed": [
            {
                "ticket": 1,
                "symbol": "XAUUSD",
                "sleeve": "dsp_spring_close",
                "closed_utc": "2026-09-17T08:00:00Z",
                "exit_class": "orig_stop",
                "rest_r": -0.8,
            },
            {
                "ticket": 2,
                "symbol": "XAUUSD",
                "sleeve": "dsp_spring_close",
                "closed_utc": "2026-09-17T09:00:00Z",
                "exit_class": "orig_stop",
                "rest_r": -0.4,
            },
        ]
    }
    stamp = refuse_remint(
        doc, sleeve="dsp_spring_close", session_day="2026-09-17", symbol="XAUUSD"
    )
    assert stamp.reason == TWO_STOP_KEEP_REASON
    assert stamp.verdict == VERDICT_APPLY_CONSUME
    assert stamp.refuse_remint is True
    assert stamp.orig_stops == 2
    assert stamp.rest_sum_r == pytest.approx(-1.2)
    assert stamp.rest_sum_r_strongly_negative is True
    assert stamp.as_dict()["never_remint"] is True
    one = {
        "closed": [
            {
                "ticket": 3,
                "symbol": "XAUUSD",
                "sleeve": "dsp_spring_close",
                "closed_utc": "2026-09-17T08:00:00Z",
                "exit_class": "orig_stop",
                "rest_r": 0.5,
            }
        ]
    }
    open_circuit = refuse_remint(
        one, sleeve="dsp_spring_close", session_day="2026-09-17", symbol="XAUUSD"
    )
    assert open_circuit.refuse_remint is False
    assert open_circuit.verdict == VERDICT_APPLY_CONSUME
    neg_one = {
        "closed": [
            {
                "ticket": 4,
                "symbol": "XAUUSD",
                "sleeve": "dsp_spring_close",
                "closed_utc": "2026-09-17T08:00:00Z",
                "exit_class": "orig_stop",
                "rest_r": -0.3,
            }
        ]
    }
    neg = refuse_remint(
        neg_one, sleeve="dsp_spring_close", session_day="2026-09-17", symbol="XAUUSD"
    )
    assert neg.orig_stops == 1
    assert neg.refuse_remint is True
    assert neg.rest_sum_r_strongly_negative is True


def test_jev_sleeve_select_shadow_global_kill() -> None:
    assert APPLY_ENABLED is False
    assert RESTING_SHADOW is False
    assert global_shadow_enabled() is False
    assert scoped_xau_conflict_apply_untouched() == SCOPED_XAU_CONFLICT_APPLY_UNTOUCHED
    with pytest.raises(DigBApplyError, match="jev_sleeve_select_shadow"):
        apply_jev_sleeve_select_shadow_global()
    with pytest.raises(DigBApplyError):
        apply_jev_sleeve_select_shadow()
    with pytest.raises(DigBApplyError):
        refuse_apply_killed("jev_sleeve_select_shadow")


def test_fluid_inventory_48_place_path_kill() -> None:
    shape = assert_inventory_shape()
    assert shape["n_fluid"] == EXPECTED_FLUID == 48
    assert shape["ok"] is True
    assert fluid_inventory_48_place_authorized() is False
    assert shape["place_authorized"] is False
    assert shape["dig_b_fluid_inventory_48"] == VERDICT_KILL_ENFORCE
    row = consume_fluid_inventory_48()
    assert row["verdict"] == VERDICT_KILL_ENFORCE
    with pytest.raises(DigBApplyError, match="fluid_inventory_48"):
        apply_fluid_inventory_48()


def test_book_owner_p1_keep_envelope_and_already_kill() -> None:
    queue = close_queue()
    assert queue["book_owner_wholesale_edit"] is False
    assert queue["place"] is False
    for name in KEEP_REASONS:
        assert classify_book_owner_reason(name) == VERDICT_APPLY_CONSUME
        assert is_keep_envelope(name) is True
    for name in KILL_ALREADY_CLOSED:
        assert classify_book_owner_reason(name) == VERDICT_KILL_ENFORCE
        assert is_kill_already_closed(name) is True
    assert classify_book_owner_reason("kill_switch_or_halt_forced_observe_only") == VERDICT_APPLY_CONSUME
    assert classify_book_owner_reason("live_broker_authority_false_observe_only") == VERDICT_APPLY_CONSUME
    assert classify_book_owner_reason("flatten_suppressed_live_broker_authority_false") == VERDICT_APPLY_CONSUME
    assert classify_book_owner_reason("cost_screen_spread_r:0.230>0.100") == VERDICT_APPLY_CONSUME
    assert classify_book_owner_reason("profile_missing_instrument_config") == VERDICT_APPLY_CONSUME
    assert classify_book_owner_reason("cluster_unit_already_placed_today:crypto") == VERDICT_APPLY_CONSUME
    assert classify_book_owner_reason("ai_companion_pause_new_entries:x") is None
    assert consume_keep_envelope()[KEEP_REASONS[0]]["verdict"] == VERDICT_APPLY_CONSUME
    assert consume_kill_already_closed()["no_tick_transient"]["verdict"] == VERDICT_KILL_ENFORCE


def test_unknown_static_reason_and_apply_on_keep_refuses_kill_entry() -> None:
    with pytest.raises(KeyError):
        consume_verdict("not_a_dig_b_reason")
    with pytest.raises(ValueError, match="not Dig B KILL_ENFORCE"):
        refuse_apply_killed("chair_bleed_hard_off")


def test_never_invents_news_protocol_or_broker_send() -> None:
    with pytest.raises(InventedNewsProtocolVeto):
        refuse_invented_news_protocol(("NEWS_PROTOCOL",))
    for path in (
        JUDGMENT_SRC / "dig_b_static.py",
        JUDGMENT_SRC / "sleeve_select.py",
        JUDGMENT_SRC / "two_stop_day_circuit.py",
        JUDGMENT_SRC / "jev_sleeve_select_shadow.py",
        JUDGMENT_SRC / "chair_static_close.py",
        JUDGMENT_SRC / "chair_enforce.py",
        JUDGMENT_SRC / "fluid_gates.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                assert name not in {"order_send", "open_trade", "mt5"}
    assert "do not invent" in RECEIPT_MD.read_text(encoding="utf-8").lower() or "Do not invent" in RECEIPT_MD.read_text(encoding="utf-8")


def test_scoped_xau_apply_wires_left_untouched() -> None:
    closed = static_in_prove_closed()
    assert closed["scoped_xau_conflict_apply_untouched"] == [
        "f5_xau_flow_alignment_size_tilt",
        "ca_cross_asset_size_tilt",
        "F5-JEV-004",
    ]
    shadow = (JUDGMENT_SRC / "jev_sleeve_select_shadow.py").read_text(encoding="utf-8")
    assert "f5_xau_flow_alignment_size_tilt" in shadow
    assert "leave untouched" in shadow.lower() or "does not touch" in shadow
