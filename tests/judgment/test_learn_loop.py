import os
from pathlib import Path

os.environ.setdefault("GTOS_JEV_A1_CALL", "0")

from src.judgment.bars import books_for_symbol, challenge_tape_present, normalize_symbol
from src.judgment.hold_from_tape import classify_close, named_exit_class, realized_r
from src.judgment.learn_loop import (
    CHAIR_TICKETS,
    CLOSE_LOOP_BATCH,
    CLOSE_LOOP_LOCK,
    CLOSE_LOOP_SCHEMA,
    DEFAULT_FIXTURES,
    LOCKED_EXIT,
    LearnLoopStore,
    asset_class,
    batch_identity_ok,
    learn_from_close,
    learn_loop_enabled,
    load_close_fixtures,
    load_close_loop_batch,
    load_close_loop_lock,
    maybe_learn_from_close,
    prove_asset_class_split,
    propose_noul_choices,
    run_close_harness,
    scoreboard,
    tape_uses_april_historical,
)
from src.judgment.gold_state import assemble_gold_state_v0, assemble_symbol_state_v0
from src.judgment.two_stop import closed_doc_from_deals
from src.judgment.challenge_shadow import challenge_as_of


FIXTURES = load_close_fixtures()
TICKETS = {int(r["ticket"]) for r in FIXTURES}
EMPTY_SPINE = {"spine_id": None, "sources": [], "events": [], "n_files": 0}


def _harness(tmp_path, deals=None):
    store = LearnLoopStore(tmp_path / "store.jsonl")
    return run_close_harness(
        deals if deals is not None else FIXTURES,
        spines=EMPTY_SPINE,
        store=store,
    ), store


def test_symbol_state_alias_is_gold_state():
    assert assemble_symbol_state_v0 is assemble_gold_state_v0


def test_close_loop_v1_lock_includes_orig_tp():
    lock = load_close_loop_lock()
    assert CLOSE_LOOP_LOCK.is_file()
    assert lock["schema"] == "gtos.close_loop.v1"
    assert lock["locked"] is True
    assert lock["orig_tp_locked"] is True
    assert "orig_tp" in lock["exit_class"]
    assert set(lock["exit_class"]) == set(LOCKED_EXIT)
    assert "event_gap" in lock["miss_type"]
    assert "ok_win" in lock["miss_type"]
    seeded = lock["seeded_tickets"]
    assert seeded["293611741"]["exit_class"] == "orig_stop"
    assert seeded["293611741"]["R"] == -1.03
    assert seeded["293611741"]["miss_type"] == "event_gap"
    assert seeded["293540988"]["exit_class"] == "orig_tp"
    assert seeded["293540988"]["R"] == 2.96
    assert seeded["293540988"]["miss_type"] == "ok_win"
    assert lock["news_protocol_invented"] is False
    assert lock["batch"] == "CLOSE_LOOP_BATCH_V1.json"


def test_asset_class_split_does_not_wear_xau():
    assert asset_class("XAUUSD") == "XAU"
    assert asset_class("GBPJPY") == "FX"
    assert asset_class("EURUSD") == "FX"
    assert asset_class("US30.cash") == "INDEX"
    assert asset_class("BTCUSD") == "CRYPTO"


def test_named_exit_class_is_challenge_scoreboard():
    assert named_exit_class(None, "orig_stop") == "orig_stop"
    assert named_exit_class(None, "orig_tp") == "orig_tp"
    assert named_exit_class("SL|[sl 1.16357]", None) == "orig_stop"
    assert named_exit_class("TP|[tp 0.85824]", None) == "orig_tp"
    assert named_exit_class("EXPERT|close_vnext_time_stop", None) == "time_stop"
    assert classify_close("orig_tp") == "broker_tp"
    assert classify_close("TP|[tp 0.85824]") == "broker_tp"


def test_fixtures_cover_chair_xau_gbpjpy_fx_us30():
    assert DEFAULT_FIXTURES.is_file()
    assert 293611741 in TICKETS
    assert 293540988 in TICKETS
    assert 291076386 in TICKETS  # EURUSD FX
    assert 291113462 in TICKETS  # US30
    assert 291816474 in TICKETS  # EURGBP orig_tp with broker print
    symbols = {normalize_symbol(str(r["symbol"])) for r in FIXTURES}
    assert "XAUUSD" in symbols
    assert "GBPJPY" in symbols
    assert "EURUSD" in symbols or "EURGBP" in symbols
    assert "US30" in symbols
    assert CHAIR_TICKETS <= TICKETS


def test_harness_scores_all_closes_without_place(tmp_path):
    pack, store = _harness(tmp_path)
    assert pack["never_place"] is True
    assert pack["apply"] is False
    assert pack["silent_apply"] is False
    assert pack["news_protocol_invented"] is False
    assert pack["april_historical_used"] is False
    assert pack["n_rows"] == len(FIXTURES)
    by_ticket = {int(r["ticket"]): r for r in pack["rows"]}
    xau = by_ticket[293611741]
    assert xau["exit_class"] == "orig_stop"
    assert xau["close_label"] == "orig_stop"
    assert xau["close_loop"] == CLOSE_LOOP_SCHEMA
    assert xau["never_place"] is True
    assert xau["apply"] is False
    assert xau["R"] == -1.03
    assert xau["r_source"] == "sit_backstop"
    assert abs((xau.get("geometry_R") or 0) + 1.0) < 1e-9
    assert xau["geometry_R"] == realized_r(entry=4347.32, exit_px=4343.11, stop_dist=4.21, side="BUY")
    assert xau["miss_type"] == "event_gap"
    assert "BOJ" in str(xau["prove_next"])
    assert xau["asset_class"] == "XAU"
    assert "close:orig_stop" in xau["regime_tags"]
    assert "miss:event_gap" in xau["regime_tags"]
    assert "session:unassembled" in xau["regime_tags"]  # no close_time in this workspace
    gbp = by_ticket[293540988]
    assert gbp["symbol"] == "GBPJPY"
    assert gbp["exit_class"] == "orig_tp"
    assert gbp["close_label"] == "broker_tp"
    assert gbp["close_loop"] == CLOSE_LOOP_SCHEMA
    assert gbp["R"] == 2.96
    assert gbp["r_source"] == "sit_backstop"
    assert gbp["geometry_R"] is None  # do not invent GBPJPY prices
    assert gbp["miss_type"] == "ok_win"
    assert "Warsh" in str(gbp["prove_next"])
    assert gbp["asset_class"] == "FX"
    # Host-safe: file presence ≠ assembled M15. This fixture has no close_time
    # (as_of falls through to now()); a stale Challenge file stays
    # missing_state. A live host drop can assemble. Never invent tape.
    m15_missing = "timeframes.m15" in (gbp.get("missing_state") or [])
    if m15_missing:
        assert gbp.get("snapshot", {}).get("completeness.timeframes_m15_h4") is not True
    else:
        assert challenge_tape_present("GBPJPY")
    assert "session:unassembled" in gbp["regime_tags"]
    assert "miss:ok_win" in gbp["regime_tags"]
    fx = by_ticket[291076386]
    assert fx["symbol"] == "EURUSD"
    assert fx["exit_class"] == "orig_stop"
    assert fx["house"]["family_class"] == "house_hard_off"
    assert "session:london" in fx["regime_tags"]
    us30 = by_ticket[291113462]
    assert normalize_symbol(us30["symbol"]) == "US30"
    assert us30["exit_class"] == "orig_stop"
    assert us30["house"]["hard_off_family"] == "mx_us30"
    eurgbp = by_ticket[291816474]
    assert eurgbp["exit_class"] == "orig_tp"
    assert eurgbp["r_source"] == "broker_exit"
    assert eurgbp["R"] is not None and eurgbp["R"] > 0
    spring = by_ticket[291794419]
    assert spring["exit_class"] == "time_stop"
    board = pack["scoreboard"]
    assert board["account"] == 0
    assert board["close_loop"] == CLOSE_LOOP_SCHEMA
    assert "orig_stop" in board["by_exit_class"]
    assert "orig_tp" in board["by_exit_class"]
    assert "time_stop" in board["by_exit_class"]
    assert board["by_asset_class"]["XAU"]["n"] >= 1
    assert board["by_asset_class"]["FX"]["n"] >= 1
    assert board["by_asset_class"]["INDEX"]["n"] >= 1
    assert board["by_miss_type"]["event_gap"] == 1
    assert board["by_miss_type"]["ok_win"] == 1
    assert board["seeded"]["293611741"]["R"] == -1.03
    assert board["seeded"]["293540988"]["exit_class"] == "orig_tp"
    assert "Challenge-true" in board["language"]
    assert board["sample_n"] == len(FIXTURES)
    assert board["sample_n"] != 48
    batch = board["batch"]
    assert batch is not None
    assert batch["n"] == 48
    assert batch["tickets_invented"] is False
    prove = pack["asset_class_prove"]
    assert prove["apply"] is False
    assert prove["batch_identity_ok"] is True
    assert store.path.is_file()
    assert len(store.load()) == len(FIXTURES)


def test_gbpjpy_does_not_wear_xau_tape():
    xau_books = books_for_symbol("XAUUSD")
    row = learn_from_close(
        {
            "ticket": 293540988,
            "symbol": "GBPJPY",
            "exit_class": "orig_tp",
            "still_open": False,
        },
        books=xau_books or {},
        spines=EMPTY_SPINE,
    )
    assert row["symbol"] == "GBPJPY"
    gbp_books = books_for_symbol("GBPJPY", xau_books)
    if gbp_books is None:
        assert "timeframes.m15" in row["missing_state"]
        sources = [
            ((row.get("state") or {}).get("timeframes") or {}).get("m15", {}).get("source_path")
        ]
        assert all("XAUUSD" not in str(s) for s in sources if s)
    assert row["never_place"] is True


def test_store_is_append_only(tmp_path):
    store = LearnLoopStore(tmp_path / "loop.jsonl")
    first = learn_from_close(
        {
            "ticket": 291076386,
            "symbol": "EURUSD",
            "side": "BUY",
            "sleeve": "xa_huge_20_ex",
            "entry": 1.16408,
            "exit": 1.16355,
            "orig_sl": 1.16357,
            "stop_dist": 0.00051,
            "close_reason": "SL|[sl 1.16357]",
            "close_time_utc": "2026-09-09T11:30:38+00:00",
            "still_open": False,
        },
        books={},
        spines=EMPTY_SPINE,
        store=store,
    )
    assert first["appended"] is True
    again = learn_from_close(
        {
            "ticket": 291076386,
            "symbol": "EURUSD",
            "side": "BUY",
            "close_reason": "SL|[sl 1.16357]",
            "close_time_utc": "2026-09-09T11:30:38+00:00",
            "still_open": False,
        },
        books={},
        spines=EMPTY_SPINE,
        store=store,
    )
    assert again["duplicate"] is True
    assert again["appended"] is False
    assert len(store.load()) == 1
    learn_from_close(
        {
            "ticket": 293540988,
            "symbol": "GBPJPY",
            "exit_class": "orig_tp",
            "still_open": False,
        },
        books={},
        spines=EMPTY_SPINE,
        store=store,
    )
    assert len(store.load()) == 2
    raw = (tmp_path / "loop.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(raw) == 2


def test_promotion_never_silent_apply(tmp_path):
    pack, _ = _harness(tmp_path)
    promo = pack["promotion"]
    assert promo["silent_apply"] is False
    assert promo["apply"] is False
    assert promo["never_place"] is True
    assert promo["n_underpowered"] == promo["n_candidates"]
    assert all(c["apply"] is False for c in promo["candidates"])
    assert all(c["status"] == "UNDERPOWERED_SHADOW" for c in promo["candidates"])
    assert all(c["chair"] == "LABEL" for c in promo["candidates"])
    assert "Chair ENFORCE/VETO/LABEL" in promo["path"]
    # Existing inventory questions only — no invented NEWS_PROTOCOL gate.
    questions = {c["proposed_question"] for c in promo["candidates"]}
    assert questions <= {
        "admit",
        "close_label",
        "hold_too_late",
        "time_stop_vs_orig",
        "event_proximity",
    }
    event_gap = next(c for c in promo["candidates"] if c["miss_type"] == "event_gap")
    assert event_gap["proposed_question"] == "event_proximity"
    assert event_gap["apply"] is False
    ok_win = next(c for c in promo["candidates"] if c["miss_type"] == "ok_win")
    assert ok_win["proposed_question"] == "admit"
    assert "Warsh" in str(ok_win["prove_next"])


def test_maybe_learn_default_off(tmp_path, monkeypatch):
    monkeypatch.delenv("GTOS_JEV_LEARN_LOOP", raising=False)
    assert learn_loop_enabled() is False
    skipped = maybe_learn_from_close({"ticket": 1, "symbol": "XAUUSD", "still_open": False})
    assert skipped["skipped"] == "GTOS_JEV_LEARN_LOOP_off"
    assert skipped["never_place"] is True
    monkeypatch.setenv("GTOS_JEV_LEARN_LOOP", "1")
    monkeypatch.setenv("GTOS_JEV_LEARN_LOOP_PATH", str(tmp_path / "on.jsonl"))
    row = maybe_learn_from_close(
        {
            "ticket": 293540988,
            "symbol": "GBPJPY",
            "exit_class": "orig_tp",
            "still_open": False,
        },
        books={},
        spines=EMPTY_SPINE,
    )
    assert row["schema"] == "gtos.judgment.learn_loop.v0"
    assert row["close_loop"] == CLOSE_LOOP_SCHEMA
    assert row.get("skipped") != "GTOS_JEV_LEARN_LOOP_off"
    assert row["never_place"] is True


def test_closed_doc_label_only_from_learn_rows():
    doc = closed_doc_from_deals(FIXTURES, stamp=challenge_as_of)
    assert doc is not None
    assert doc["two_stop_source"] == "challenge_deals_label_not_count"
    tickets = {row["ticket"] for row in doc["closed"]}
    # Chair XAU 293611741 is orig_stop but has no close_time in this
    # workspace — LABEL needs a stamp. Do not invent one.
    assert 293611741 not in tickets
    assert 291076386 in tickets
    assert 291113462 in tickets
    assert 293540988 not in tickets  # orig_tp is not a 2-stop COUNT row
    assert 291816474 not in tickets
    assert 291794419 not in tickets


def test_april_historical_flag_is_visible():
    fake = {
        "timeframes": {
            "m15": {"source_path": "data/historical_2026/XAUUSD_M15.csv"},
        }
    }
    assert tape_uses_april_historical(fake) is True
    assert tape_uses_april_historical({"timeframes": {}}) is False


def test_scoreboard_and_propose_helpers():
    rows = [
        {
            "schema": "gtos.judgment.learn_loop.v0",
            "ticket": 1,
            "symbol": "XAUUSD",
            "symbol_norm": "XAUUSD",
            "exit_class": "orig_stop",
            "miss_type": "false_structure",
            "asset_class": "XAU",
            "R": -1.0,
            "snapshot": {
                "identity.family_class": "study",
                "sessions.named": "london",
                "flow.stance": "against_flow",
            },
        }
    ]
    board = scoreboard(rows)
    assert board["n_closes"] == 1
    assert board["by_exit_class"]["orig_stop"] == 1
    assert board["by_asset_class"]["XAU"]["n"] == 1
    promo = propose_noul_choices(rows)
    assert promo["candidates"][0]["proposed_question"] == "admit"
    assert promo["candidates"][0]["silent_apply"] is False


def test_close_loop_batch_n48_identities():
    assert CLOSE_LOOP_BATCH.is_file()
    batch = load_close_loop_batch()
    assert batch is not None
    assert batch["schema"] == "gtos.close_loop.v1"
    assert batch["account"] == 0
    assert batch["n"] == 48
    assert batch["sum_R"] == -28.43
    assert batch["mean_R"] == -0.59
    assert batch["approx"] is True
    assert batch["exit_class"] == {"orig_stop": 42, "time_stop": 4, "orig_tp": 2}
    assert batch["miss_type"] == {
        "false_structure": 39,
        "ok_win": 6,
        "event_gap": 3,
    }
    assets = batch["by_asset_class"]
    assert assets["XAU"] == {"n": 23, "mean_R": -0.37}
    assert assets["INDEX"]["n"] == 16
    assert assets["INDEX"]["mean_R"] == -1.04
    assert assets["INDEX"]["wins"] == 0
    assert assets["FX"]["n"] == 6
    assert assets["FX"]["mean_R"] == 0.0
    assert assets["FX"]["mean_R_note"] == "approx_flat"
    assert assets["CRYPTO"]["n"] == 3
    assert assets["CRYPTO"]["wins"] == 0
    assert assets["CRYPTO"]["mean_R"] is None
    assert assets["CRYPTO"]["note"] == "all_stops"
    assert batch["per_ticket_labels"] is False
    assert batch["tickets_invented"] is False
    assert batch["news_protocol_invented"] is False
    assert batch["apply"] is False
    assert "tickets" not in batch
    assert batch_identity_ok(batch) is True
    assert batch_identity_ok({**batch, "tickets_invented": True}) is False
    assert batch_identity_ok({**batch, "n": 6}) is False


def test_asset_class_split_prove_never_apply():
    prove = prove_asset_class_split()
    assert prove["schema"] == "gtos.judgment.learn_loop.asset_split_prove.v0"
    assert prove["close_loop"] == CLOSE_LOOP_SCHEMA
    assert prove["apply"] is False
    assert prove["silent_apply"] is False
    assert prove["never_place"] is True
    assert prove["never_remint"] is True
    assert prove["never_flatten"] is True
    assert prove["batch_n"] == 48
    assert prove["batch_identity_ok"] is True
    by_pattern = {c["pattern"]: c for c in prove["candidates"]}
    assert by_pattern["batch_asset=INDEX"]["n"] == 16
    assert by_pattern["batch_asset=INDEX"]["mean_R"] == -1.04
    assert by_pattern["batch_asset=INDEX"]["wins"] == 0
    assert by_pattern["batch_asset=INDEX"]["status"] == "SHADOW"
    assert by_pattern["batch_asset=INDEX"]["proposed_question"] == "admit"
    assert by_pattern["batch_asset=CRYPTO"]["n"] == 3
    assert by_pattern["batch_asset=CRYPTO"]["mean_R"] is None
    assert by_pattern["batch_asset=CRYPTO"]["status"] == "UNDERPOWERED_SHADOW"
    assert by_pattern["batch_asset=XAU"]["n"] == 23
    assert by_pattern["batch_asset=XAU"]["proposed_question"] == "event_proximity"
    assert by_pattern["batch_asset=FX"]["n"] == 6
    assert by_pattern["batch_asset=FX"]["status"] == "SHADOW"
    assert by_pattern["batch_miss=false_structure"]["n"] == 39
    assert by_pattern["batch_miss=false_structure"]["proposed_question"] == "admit"
    assert all(c["apply"] is False for c in prove["candidates"])
    assert all(c["silent_apply"] is False for c in prove["candidates"])
    assert all(c["chair"] == "LABEL" for c in prove["candidates"])
    questions = {c["proposed_question"] for c in prove["candidates"]}
    assert questions <= {"admit", "event_proximity"}
    assert "NEWS_PROTOCOL" not in questions
    assert all("NEWS_PROTOCOL" not in str(c.get("proposed_question") or "") for c in prove["candidates"])


def test_module_never_places():
    src = Path(__file__).resolve().parents[2] / "src" / "judgment" / "learn_loop.py"
    text = src.read_text(encoding="utf-8")
    assert "order_send" not in text
    assert "mt5.order" not in text
    assert "never silent APPLY" in text
    assert "Jev never places" in text
