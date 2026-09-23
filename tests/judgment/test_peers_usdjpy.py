"""USDJPY is peer-of-XAU. Missing stays visible null. Never invent DXY/yields/OB."""

from datetime import datetime, timezone
from pathlib import Path

from src.judgment.a1_log import intent_gold_state
from src.judgment.bars import (
    MULTI_SYMBOL_OPTIONAL,
    MULTI_SYMBOL_PRIORITY,
    XAU_PEER_SYMBOLS,
    books_for_symbol,
    challenge_tape_present,
    load_gold_books,
    resolve_challenge_tf,
)
from src.judgment.challenge_shadow import score_position
from tests.judgment.cages import assert_live_cages
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.peers import USDJPY_PEER_FIELDS, assemble_peers_block

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "peers"
AS_OF = datetime(2026, 9, 17, 7, 30, 55, tzinfo=timezone.utc)


class _XauIntent:
    symbol = "XAUUSD"
    sleeve = "dsp_two_bar_t"
    side = "short"
    entry = 4331.45
    stop = 4336.9
    stop_dist = 5.45
    target = 4288.19
    candidate_id = "292667008"
    ticket = "292667008"
    order_type = "MARKET"


class _GbpIntent(_XauIntent):
    symbol = "GBPUSD"
    sleeve = "vss_fxcross_london_up_low"
    entry = 1.34
    stop = 1.338
    stop_dist = 0.002
    target = 1.35
    candidate_id = "gbp-1"


def _fixture_books(symbol: str) -> dict:
    stem = "XAUUSD" if symbol == "XAUUSD" else "USDJPY"
    return load_gold_books(
        {
            "m15": FIXTURE_DIR / f"{stem}_M15.csv",
            "h4": FIXTURE_DIR / f"{stem}_H4.csv",
            "d1": FIXTURE_DIR / "missing_D1.csv",
        }
    )


def _xau_state(**kwargs):
    kwargs.setdefault("as_of_utc", AS_OF)
    kwargs.setdefault("side", "short")
    kwargs.setdefault("sleeve", "dsp_two_bar_t")
    kwargs.setdefault("symbol", "XAUUSD")
    kwargs.setdefault("origin_organism", "f5_challenge")
    kwargs.setdefault("spines", {"spine_id": None, "sources": [], "events": [], "n_files": 0})
    kwargs.setdefault("geometry", {"entry": 4331.45, "stop": 4336.9, "stop_dist": 5.45})
    kwargs.setdefault("cost", {"spread_r_of_stop": 0.05})
    kwargs.setdefault("sleeve_features", {"tag": "dsp_two_bar_t"})
    return assemble_gold_state_v0(**kwargs)


def test_usdjpy_is_priority_peer_of_xau_not_optional():
    assert "USDJPY" in MULTI_SYMBOL_PRIORITY
    assert "USDJPY" not in MULTI_SYMBOL_OPTIONAL
    assert XAU_PEER_SYMBOLS == ("USDJPY",)


def test_april_historical_usdjpy_is_not_challenge_tape():
    challenge = resolve_challenge_tf("USDJPY", "M15")
    hist = Path(__file__).resolve().parents[2] / "data" / "historical" / "USDJPY_M15.csv"
    assert "data/historical" not in str(challenge)
    if hist.is_file() and challenge.is_file():
        assert challenge.resolve() != hist.resolve()


def test_missing_usdjpy_is_visible_null_never_invented():
    state = _xau_state(books=_fixture_books("XAUUSD"), peer_books=None)
    usdjpy = state["peers"]["usdjpy"]
    assert "usdjpy" in state["peers"]
    # PACK 4 may fold named wires (usd_proxy_vs_xau, corr, …) onto peers.
    # The USDJPY tape slot stays the only invented-price surface.
    assert set(usdjpy) == set(USDJPY_PEER_FIELDS)
    assert "dxy" not in state["peers"]
    assert "yields" not in state["peers"]
    assert "ob" not in state["peers"]
    assert usdjpy["present"] is False
    assert usdjpy["m15_atr14"] is None
    assert usdjpy["h4_trend"] is None
    assert usdjpy["xau_usdjpy_comove_20"] is None
    assert usdjpy["atr_ratio"] is None
    assert usdjpy["source"] == "unassembled"
    assert state["completeness"]["peers_usdjpy"] is False
    assert "peers.usdjpy" in state["completeness"]["missing_fields"]
    assert state["completeness"]["state_sufficient_for_live"] is True


def test_fixture_usdjpy_fills_named_peer_metrics():
    xau = _fixture_books("XAUUSD")
    jpy = _fixture_books("USDJPY")
    state = _xau_state(books=xau, peer_books={"USDJPY": jpy})
    usdjpy = state["peers"]["usdjpy"]
    assert usdjpy["present"] is True
    assert usdjpy["source"] == "challenge_csv"
    assert usdjpy["m15_atr14"] is not None and usdjpy["m15_atr14"] > 0
    assert usdjpy["h4_trend"] == 1
    assert usdjpy["xau_usdjpy_comove_20"] is not None
    assert abs(usdjpy["xau_usdjpy_comove_20"] - 1.0) < 1e-9
    assert usdjpy["atr_ratio"] is not None and usdjpy["atr_ratio"] > 0
    assert state["completeness"]["peers_usdjpy"] is True
    assert "peers.usdjpy" not in state["completeness"]["missing_fields"]
    assert "dxy" not in state["peers"]
    assert "yields" not in state["peers"]
    assert "ob" not in state["peers"]


def test_short_peer_tape_leaves_comove_null():
    jpy = _fixture_books("USDJPY")
    jpy["m15"] = jpy["m15"][-5:]
    block = assemble_peers_block(
        symbol="XAUUSD",
        as_of_utc=AS_OF,
        books=_fixture_books("XAUUSD"),
        peer_books={"USDJPY": jpy},
    )
    assert block["usdjpy"]["present"] is True
    assert block["usdjpy"]["xau_usdjpy_comove_20"] is None


def test_non_xau_does_not_attach_usdjpy_peer():
    state = _xau_state(
        symbol="GBPUSD",
        sleeve="vss_fxcross_london_up_low",
        books=_fixture_books("XAUUSD"),
        peer_books={"USDJPY": _fixture_books("USDJPY")},
        geometry={"entry": 1.34, "stop": 1.338, "stop_dist": 0.002},
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
    )
    assert state["peers"]["usdjpy"]["present"] is False
    assert state["peers"]["usdjpy"]["source"] == "not_xau_primary"
    assert "peers.usdjpy" not in state["completeness"]["missing_fields"]


def test_intent_gold_state_attaches_peers_via_books_for_symbol(tmp_path, monkeypatch):
    for name in ("USDJPY_M15.csv", "USDJPY_H4.csv"):
        (tmp_path / name).write_text(
            (FIXTURE_DIR / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    monkeypatch.setenv("GTOS_CHALLENGE_BAR_MULTI", str(tmp_path))
    from src.judgment import a1_log

    a1_log._BOOKS_CACHE.clear()
    assert challenge_tape_present("USDJPY") is True
    loaded = books_for_symbol("USDJPY")
    assert loaded is not None
    assert loaded["m15"]
    state = intent_gold_state(
        _XauIntent(),
        origin="f5_challenge",
        books=_fixture_books("XAUUSD"),
        as_of_utc=AS_OF,
    )
    assert state["identity"]["symbol"] == "XAUUSD"
    assert state["peers"]["usdjpy"]["present"] is True
    assert state["peers"]["usdjpy"]["source"] == "challenge_csv"
    assert state["peers"]["usdjpy"]["xau_usdjpy_comove_20"] is not None
    gbp = intent_gold_state(
        _GbpIntent(),
        origin="f5_challenge",
        books={},
        as_of_utc=AS_OF,
        peer_books={"USDJPY": loaded},
    )
    assert gbp["identity"]["symbol"] == "GBPUSD"
    # Non-XAU intent_gold_state is symbol_state.v0 — class peers, not gold's
    # usdjpy/not_xau_primary dead end (that contract stays on assemble_gold_state_v0).
    assert gbp["schema"] == "gtos.judgment.symbol_state.v0"
    sources = [row.get("source") for row in gbp["peers"].values() if isinstance(row, dict)]
    assert "not_xau_primary" not in sources
    a1_log._BOOKS_CACHE.clear()


def test_score_position_xau_reads_named_peer_from_multi_cache():
    books = {"XAUUSD": _fixture_books("XAUUSD"), "USDJPY": _fixture_books("USDJPY")}
    row = score_position(
        {
            "ticket": 292667008,
            "symbol": "XAUUSD",
            "side": "SHORT",
            "sleeve": "dsp_two_bar_t",
            "entry": 4331.45,
            "orig_sl": 4336.9,
            "stop_dist": 5.45,
            "open_time_utc": "2026-09-17T07:30:55Z",
            "_kind": "slate",
        },
        books=books,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        sit_meta={},
    )
    assert row["state"]["peers"]["usdjpy"]["present"] is True
    assert row["state"]["completeness"]["peers_usdjpy"] is True
    assert_live_cages(row["compose"], ticket=292667008)
