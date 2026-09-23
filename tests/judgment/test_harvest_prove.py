"""SHADOW prove for harvest P0-1. Research-only. Never places."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.judgment.bars import load_all_landed_challenge_books, normalize_symbol
from src.judgment.harvest_patterns import (
    CHALLENGE_LOGIN,
    CHALLENGE_MAGIC,
    CHALLENGE_NS,
    SCHEMA_LOCK,
    allowed_route_classes,
    chair_route_class_for,
)
from src.judgment.harvest_prove import (
    DEFAULT_P0_2,
    DEFAULT_P0_5,
    DEFAULT_RECEIPT,
    build_p0_1_shadow,
    load_challenge_intents,
    prove_p0_1,
    prove_p0_2,
    prove_p0_5,
    score_harvest_row,
)
from src.judgment.news_spine import load_spines
from src.judgment.process_lock import PROVE_BARS_FLUID_SIZE

REPO = Path(__file__).resolve().parents[2]
HARVEST_PROVE_SRC = REPO / "src" / "judgment" / "harvest_prove.py"
TYPED_MAPS = REPO / "judgment" / "astra" / "oss_harvest" / "TYPED_FIELD_MAPS.json"


def _row(**kwargs):
    base = {
        "noul": {"decidable": True, "noul": True, "moved": False},
        "live_multiplier": 1.0,
        "symbol": "XAUUSD",
        "identity_symbol": "XAUUSD",
        "xau_substituted": False,
        "state": {"news": {"spine_empty": True, "high_in_f5_window": False, "events": []}},
    }
    base.update(kwargs)
    return base


def _enough_for_bars(*, extra=None):
    honest = [_row() for _ in range(22)]
    moved = [
        _row(noul={"decidable": True, "noul": False, "moved": True}) for _ in range(5)
    ]
    rows = honest + moved
    if extra:
        rows.extend(extra)
    return rows


def test_missing_symbol_never_defaults_to_xau(tmp_path):
    sit = tmp_path / "sit.json"
    sit.write_text(
        json.dumps(
            {
                "login": CHALLENGE_LOGIN,
                "positions": [
                    {"ticket": 1, "symbol": "", "side": "sell"},
                    {"ticket": 2, "symbol": "EURUSD", "side": "buy"},
                ],
            }
        ),
        encoding="utf-8",
    )
    deals = tmp_path / "deals.jsonl"
    deals.write_text(
        json.dumps({"ticket": 3, "symbol": "GBPUSD", "side": "sell"}) + "\n"
        + json.dumps({"ticket": 4, "side": "buy"}) + "\n",
        encoding="utf-8",
    )
    rows = load_challenge_intents(deals_path=deals, sit_path=sit)
    symbols = [str(r.get("symbol")) for r in rows]
    assert symbols == ["EURUSD", "GBPUSD"]
    assert all(s.strip() for s in symbols)


def test_eurusd_does_not_wear_xau_tape():
    cache = load_all_landed_challenge_books()
    spines = load_spines()
    row = score_harvest_row(
        {
            "ticket": 291076386,
            "symbol": "EURUSD",
            "side": "buy",
            "sleeve": "xa_huge_20_ex",
            "entry": 1.16408,
            "orig_sl": 1.16357,
            "open_time_utc": "2026-09-09T09:27:27+00:00",
            "open_time_server": "2026-09-09 09:27:27",
            "_kind": "deal",
        },
        books_cache=cache,
        spines=spines,
    )
    assert row is not None
    assert row["symbol"] == "EURUSD"
    assert row["identity_symbol"] == "EURUSD"
    assert row["xau_substituted"] is False
    assert row["live_multiplier"] == 1.0
    assert row["tape_present"] is True
    rc = (row.get("harvest") or {}).get("route_class") or {}
    assert rc.get("choice") == "fx_major"
    assert rc.get("house_hard_off") is False
    assert ((row.get("harvest") or {}).get("route") or {}).get("tf_route") == "multi_m15_h4"
    news = row["state"]["news"]
    if news.get("spine_empty"):
        assert news.get("events") == []
        assert news.get("high_in_f5_window") is not True


def test_empty_spine_stays_empty():
    cache = load_all_landed_challenge_books()
    empty = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    row = score_harvest_row(
        {
            "ticket": 291072108,
            "symbol": "XAUUSD",
            "side": "sell",
            "sleeve": "dsp_walked_hi",
            "entry": 4401.15,
            "orig_sl": 4406.89,
            "open_time_utc": "2026-09-09T09:03:48+00:00",
            "open_time_server": "2026-09-09 09:03:48",
            "_kind": "deal",
        },
        books_cache=cache,
        spines=empty,
    )
    assert row is not None
    news = row["state"]["news"]
    assert news["events"] == []
    assert news["spine_empty"] is True
    assert news.get("high_in_f5_window") is not True


def test_injected_future_ac60_moves_noul():
    cache = load_all_landed_challenge_books()
    spines = load_spines()
    pos = {
        "ticket": 291072108,
        "symbol": "XAUUSD",
        "side": "sell",
        "sleeve": "dsp_walked_hi",
        "entry": 4401.15,
        "orig_sl": 4406.89,
        "open_time_utc": "2026-09-09T09:03:48+00:00",
        "open_time_server": "2026-09-09 09:03:48",
        "_kind": "deal",
    }
    honest = score_harvest_row(pos, books_cache=cache, spines=spines, inject_future_ac60=False)
    leak = score_harvest_row(pos, books_cache=cache, spines=spines, inject_future_ac60=True)
    assert honest is not None and leak is not None
    assert honest["noul"]["decidable"] is True
    assert honest["noul"]["noul"] is True
    assert honest["noul"]["moved"] is False
    assert leak["noul"]["decidable"] is True
    assert leak["noul"]["noul"] is False
    assert leak["noul"]["moved"] is True
    assert "ac60" in leak["noul"]["leakage_keys"]
    assert leak["live_multiplier"] == 1.0


def test_prove_rejects_invented_high():
    bad = _row(state={"news": {"spine_empty": True, "high_in_f5_window": True, "events": []}})
    rec = prove_p0_1(_enough_for_bars(extra=[bad]))
    assert rec["verdict"] == "NOT_PROVED"
    assert rec["n_invented_high"] == 1
    assert any("invented_high" in r for r in rec["reasons"])
    assert rec["ready_to_apply"] is False


def test_prove_rejects_live_multiplier_not_one_and_xau_default():
    live = prove_p0_1(_enough_for_bars(extra=[_row(live_multiplier=1.05)]))
    assert live["verdict"] == "NOT_PROVED"
    assert any("live_multiplier_not_one" in r for r in live["reasons"])
    xau = prove_p0_1(
        _enough_for_bars(extra=[_row(symbol="EURUSD", identity_symbol="XAUUSD")])
    )
    assert xau["verdict"] == "NOT_PROVED"
    assert any("xau_default" in r for r in xau["reasons"])


def test_prove_passes_when_bars_met_without_invented_high():
    rec = prove_p0_1(_enough_for_bars())
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["n_decidable"] >= PROVE_BARS_FLUID_SIZE["min_decidable"]
    assert rec["n_moved"] >= PROVE_BARS_FLUID_SIZE["min_moved"]
    assert rec["n_invented_high"] == 0
    assert rec["ready_to_apply"] is False
    assert rec["chair_named_atom"] is False
    assert rec["login"] == CHALLENGE_LOGIN
    assert rec["ns"] == CHALLENGE_NS
    assert rec["magic"] == CHALLENGE_MAGIC
    assert rec["schema_lock"] == SCHEMA_LOCK
    assert rec["never_place"] is True
    assert rec["never_vendor"] is True


def test_challenge_pack_p0_1_p0_2_p0_5():
    rows = build_p0_1_shadow()
    rec = prove_p0_1(rows)
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["n_decidable"] >= 20
    assert rec["n_moved"] >= 5
    assert rec["n_invented_high"] == 0
    assert rec["n_live_not_one"] == 0
    assert rec["n_xau_substituted"] == 0
    assert rec["ready_to_apply"] is False
    assert rec["multi_fx_books_present"] is True
    assert "XAUUSD" in rec["landed_books"]
    assert "EURUSD" in rec["landed_books"]
    for row in rows:
        assert row["live_multiplier"] == 1.0
        news = (row.get("state") or {}).get("news") or {}
        if news.get("spine_empty"):
            assert news.get("events") == []
            assert news.get("high_in_f5_window") is not True
        if row.get("injected_future_ac60"):
            continue
        if normalize_symbol(str(row.get("symbol") or "")) not in {"XAUUSD", "XAU"}:
            assert row["identity_symbol"] == row["symbol"]
            assert row["xau_substituted"] is False
            rc = (row.get("harvest") or {}).get("route_class") or {}
            expected = chair_route_class_for(str(row.get("symbol") or ""))
            assert rc.get("choice") == expected
            assert rc.get("choice") in allowed_route_classes(str(row.get("symbol") or ""))
            if expected == "index":
                assert rc.get("house_hard_off") is True
    p02 = prove_p0_2(rows)
    assert p02["verdict"] == "PROVED_SHADOW"
    assert p02["n_non_xau_tf_attached"] >= 5
    assert p02["n_invented_route_class"] == 0
    assert p02["n_invented_route_class_non_xau"] == 0
    assert p02["ready_to_apply"] is False
    assert p02["chair_named_atom"] is True
    assert p02["chair_named_scope"] == "shadow_labels_only"
    assert p02["n_unknown_until_landed"] >= 1
    assert p02["n_us30_house_hard_off"] >= 1
    assert set(p02["route_classes"]).issubset({"metal", "fx_major", "fx_cross", "index", "unknown", "multi"})
    assert "crypto" not in p02["route_classes"]
    p05 = prove_p0_5(rows)
    assert p05["verdict"] == "PROVED_SHADOW"
    assert p05["n_decidable"] >= 20
    assert p05["n_moved"] >= 5
    assert p05["ready_to_apply"] is False


def test_prove_p0_2_rejects_invented_non_xau_route_class():
    rows = []
    for _ in range(22):
        rows.append(
            _row(
                harvest={
                    "route": {"tf_route": "multi_m15_h4"},
                    "route_class": {"decidable": True, "choice": "metal", "moved": True},
                }
            )
        )
    for _ in range(6):
        rows.append(
            _row(
                symbol="EURUSD",
                identity_symbol="EURUSD",
                harvest={
                    "route": {"tf_route": "multi_m15_h4"},
                    "route_class": {"decidable": True, "choice": "multi", "moved": True},
                },
            )
        )
    rec = prove_p0_2(rows)
    assert rec["verdict"] == "NOT_PROVED"
    assert rec["n_invented_route_class_non_xau"] == 6
    assert rec["ready_to_apply"] is False


def test_prove_p0_2_rejects_uk100_as_index_and_btc_as_crypto():
    rows = []
    for _ in range(22):
        rows.append(
            _row(
                harvest={
                    "route": {"tf_route": "multi_m15_h4"},
                    "route_class": {"decidable": True, "choice": "metal", "moved": True},
                }
            )
        )
    rows.append(
        _row(
            symbol="UK100.cash",
            identity_symbol="UK100.cash",
            harvest={
                "route": {"tf_route": "unknown"},
                "route_class": {
                    "decidable": True,
                    "choice": "index",
                    "moved": True,
                    "house_hard_off": False,
                },
            },
        )
    )
    rows.append(
        _row(
            symbol="BTCUSD",
            identity_symbol="BTCUSD",
            harvest={
                "route": {"tf_route": "unknown"},
                "route_class": {"decidable": True, "choice": "crypto", "moved": True},
            },
        )
    )
    rec = prove_p0_2(rows)
    assert rec["verdict"] == "NOT_PROVED"
    assert rec["n_invented_route_class"] == 2
    assert rec["ready_to_apply"] is False


def test_prove_p0_2_rejects_us30_index_without_house_hard_off():
    rows = [
        _row(
            harvest={
                "route": {"tf_route": "multi_m15_h4"},
                "route_class": {"decidable": True, "choice": "metal", "moved": True},
            }
        )
        for _ in range(22)
    ]
    for _ in range(6):
        rows.append(
            _row(
                symbol="US30.cash",
                identity_symbol="US30.cash",
                harvest={
                    "route": {"tf_route": "multi_m15_h4"},
                    "route_class": {
                        "decidable": True,
                        "choice": "index",
                        "moved": True,
                        "house_hard_off": False,
                    },
                },
            )
        )
    rec = prove_p0_2(rows)
    assert rec["verdict"] == "NOT_PROVED"
    assert any("house_hard_off" in r for r in rec["reasons"])
    assert rec["ready_to_apply"] is False


def test_prove_p0_2_accepts_chair_table():
    rows = [
        _row(
            harvest={
                "route": {"tf_route": "multi_m15_h4"},
                "route_class": {"decidable": True, "choice": "metal", "moved": True},
            }
        )
        for _ in range(10)
    ]
    rows.extend(
        _row(
            harvest={
                "route": {"tf_route": "multi_m15_h4"},
                "route_class": {"decidable": True, "choice": "multi", "moved": True},
            }
        )
        for _ in range(5)
    )
    for symbol, choice, house_off in (
        ("EURUSD", "fx_major", False),
        ("GBPUSD", "fx_major", False),
        ("USDJPY", "fx_major", False),
        ("EURGBP", "fx_major", False),
        ("GBPJPY", "fx_cross", False),
        ("US30.cash", "index", True),
        ("UK100.cash", "unknown", False),
        ("BTCUSD", "unknown", False),
        ("ETHUSD", "unknown", False),
    ):
        rows.append(
            _row(
                symbol=symbol,
                identity_symbol=symbol,
                harvest={
                    "route": {"tf_route": "multi_m15_h4" if choice != "unknown" else "unknown"},
                    "route_class": {
                        "decidable": True,
                        "choice": choice,
                        "moved": choice != "unknown",
                        "house_hard_off": house_off,
                    },
                },
            )
        )
    rec = prove_p0_2(rows)
    assert rec["verdict"] == "PROVED_SHADOW"
    assert rec["n_invented_route_class"] == 0
    assert rec["n_moved"] >= 5
    assert rec["ready_to_apply"] is False
    assert rec["chair_named_atom"] is True


def test_receipt_and_typed_field_maps():
    payload = json.loads(DEFAULT_RECEIPT.read_text(encoding="utf-8"))
    assert payload["verdict"] == "PROVED_SHADOW"
    assert payload["login"] == CHALLENGE_LOGIN
    assert payload["n_decidable"] >= 20
    assert payload["n_moved"] >= 5
    assert payload["n_invented_high"] == 0
    p02 = payload.get("p0_2") or payload.get("p0_2_stub") or {}
    assert p02.get("verdict") == "PROVED_SHADOW"
    assert p02.get("n_invented_route_class_non_xau") == 0
    assert (payload.get("p0_5") or {}).get("verdict") == "PROVED_SHADOW"
    assert DEFAULT_RECEIPT.with_suffix(".md").is_file()
    assert DEFAULT_P0_2.is_file()
    assert DEFAULT_P0_5.is_file()
    maps = json.loads(TYPED_MAPS.read_text(encoding="utf-8"))
    assert maps["chair_prove_order"][:2] == ["P0-1", "P0-2"]
    by_id = {row["id"]: row for row in maps["maps"]}
    assert by_id["P0-1"]["question"] == "feature_as_of_honest"
    assert by_id["P0-1"]["field"] == "harvest.pit.feature_as_of"
    assert by_id["P0-1"]["status"] == "PROVED_SHADOW"
    assert by_id["P0-2"]["status"] == "PROVED_SHADOW"
    assert by_id["P0-2"]["field"] == "identity.tf_route"
    assert by_id["P0-2"].get("chair_named_table") is True
    assert by_id["P0-2"].get("ready_to_apply") is False
    assert by_id["P0-5"]["status"] == "PROVED_SHADOW"
    assert by_id["P0-5"]["question"] == "fill_realism"


def test_harvest_prove_import_isolation():
    tree = ast.parse(HARVEST_PROVE_SRC.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            imported.add(root)
            if node.module:
                imported.add(node.module)
    forbidden = {
        "mt5",
        "MetaTrader5",
        "src.mt5",
        "src.components.execution",
        "execution",
        "src.judgment.apply_size",
        "src.judgment.compose",
    }
    assert imported.isdisjoint(forbidden)
    text = HARVEST_PROVE_SRC.read_text(encoding="utf-8")
    for needle in ("order_send", "open_trade", "mt5.order", "RealMT5"):
        assert needle not in text
    assert "Never places" in text
