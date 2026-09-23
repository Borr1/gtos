import math
from datetime import datetime, timedelta, timezone

from src.components.ultimate_book.primitives import Bar
from src.judgment.bars import StampedBar, books_for_symbol, challenge_tape_present
from src.judgment.cross_asset import (
    assemble_cross_asset_v0,
    event_join_features,
    gold_vs_usd_corr,
    pearson,
    session_liquidity_flags,
    usd_proxy_returns,
)
from src.judgment.cross_asset_prove import run_prove, survey_challenge_surface
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.occupancy import occupancy_book_at, trades_from_dicts
from src.judgment.world_state import assemble_world_state_v0, load_peer_books


AS_OF = datetime(2026, 9, 17, 13, 5, tzinfo=timezone.utc)


def _book(closes: list[float], start: datetime, *, step_minutes: int = 15) -> list[StampedBar]:
    out: list[StampedBar] = []
    for i, close in enumerate(closes):
        utc = start + timedelta(minutes=step_minutes * i)
        out.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=close, h=close + 0.1, l=close - 0.1, c=close, v=1.0),
                source_path="tmp",
            )
        )
    return out


def _ramp(n: int, start: float, step: float) -> list[float]:
    return [start + step * i for i in range(n)]


def _from_rets(start: float, rets: list[float]) -> list[float]:
    out = [float(start)]
    for ret in rets:
        out.append(out[-1] * math.exp(ret))
    return out


def _shared_rets(n_rets: int, mean: float = 0.00015, amp: float = 0.00008) -> list[float]:
    """Varying same-signed log-returns. Constant series make Pearson None (var=0)."""
    return [mean + amp * math.sin(i / 3.0) for i in range(n_rets)]


def test_pearson_none_below_min_n_never_zero():
    assert pearson([0.1, 0.2], [0.1, 0.2]) is None
    assert pearson([0.0] * 20, [0.1] * 20) is None


def test_missing_peers_stay_unassembled_not_zero():
    features = assemble_cross_asset_v0(
        as_of_utc=AS_OF,
        peer_books={},
        xau_books={"m15": _book(_ramp(40, 4300.0, 1.0), AS_OF - timedelta(hours=10))},
        news={"spine_empty": True, "events": []},
        utc_hour=13,
        is_friday=False,
        challenge_true=True,
    )
    assert features["usd_proxy"]["named"] == "unassembled"
    assert features["usd_proxy"]["ret"] is None
    assert features["usd_proxy"]["dxy_used"] is False
    assert features["gold_vs_usd"]["named"] == "unassembled"
    assert features["gold_vs_usd"]["corr"]["w16"] is None
    assert features["gold_vs_index"]["named"] == "unassembled"
    assert features["risk_on"]["named"] == "unassembled"
    assert features["april_historical_used"] is False
    assert features["completeness"]["usd_proxy"] is False
    assert "world.usd_proxy" in features["completeness"]["missing_fields"]


def test_usd_proxy_and_gold_with_usd_from_fx_majors():
    n = 100
    start = AS_OF - timedelta(minutes=15 * (n - 1))
    # Shared varying log-returns: gold up with the FX USD basket.
    # Arithmetic ramps invert Pearson; constant log-returns make it None (var=0).
    rets = _shared_rets(n - 1)
    gold = _book(_from_rets(4300.0, rets), start)
    eurusd = _book(_from_rets(1.10, [-r for r in rets]), start)
    gbpusd = _book(_from_rets(1.28, [-r for r in rets]), start)
    usdjpy = _book(_from_rets(148.0, rets), start)
    peers = {
        "EURUSD": {"m15": eurusd},
        "GBPUSD": {"m15": gbpusd},
        "USDJPY": {"m15": usdjpy},
    }
    proxy = usd_proxy_returns(peers, AS_OF, n=32)
    assert proxy["source"] == "fx_majors_equal_weight"
    assert proxy["named"] == "usd_up"
    assert proxy["dxy_used"] is False
    packed = gold_vs_usd_corr(gold, peers, AS_OF)
    assert packed["corr"]["w16"] is not None
    assert packed["corr"]["w16"] > 0.8
    assert packed["named"] == "gold_with_usd"


def test_gold_against_usd_when_xau_fights_the_proxy():
    n = 100
    start = AS_OF - timedelta(minutes=15 * (n - 1))
    rets = _shared_rets(n - 1)
    gold = _book(_from_rets(4400.0, [-r for r in rets]), start)
    peers = {
        "EURUSD": {"m15": _book(_from_rets(1.10, [-r for r in rets]), start)},
        "GBPUSD": {"m15": _book(_from_rets(1.28, [-r for r in rets]), start)},
        "USDJPY": {"m15": _book(_from_rets(148.0, rets), start)},
    }
    packed = gold_vs_usd_corr(gold, peers, AS_OF)
    assert packed["named"] == "gold_against_usd"
    assert packed["corr"]["w16"] < -0.8


def test_risk_on_needs_us30_not_usdjpy_alone():
    n = 40
    start = AS_OF - timedelta(minutes=15 * (n - 1))
    usdjpy = _book(_ramp(n, 148.0, 0.05), start)
    features = assemble_cross_asset_v0(
        as_of_utc=AS_OF,
        peer_books={"USDJPY": {"m15": usdjpy}},
        utc_hour=13,
        challenge_true=False,
    )
    assert features["rates_proxy"]["named"] in {"yen_offered", "flat"}
    assert features["risk_on"]["named"] == "unassembled"
    us30 = _book(_from_rets(42000.0, _shared_rets(n - 1, mean=0.00025)), start)
    features2 = assemble_cross_asset_v0(
        as_of_utc=AS_OF,
        peer_books={"USDJPY": {"m15": usdjpy}, "US30": {"m15": us30}},
        utc_hour=13,
        challenge_true=False,
    )
    assert features2["risk_on"]["named"] == "risk_on"
    gold = _book(_from_rets(4300.0, _shared_rets(n - 1, mean=0.0002)), start)
    features3 = assemble_cross_asset_v0(
        as_of_utc=AS_OF,
        peer_books={"US30": {"m15": us30}},
        xau_books={"m15": gold},
        utc_hour=13,
        challenge_true=False,
    )
    assert features3["gold_vs_index"]["named"] == "gold_with_us30"


def test_session_liquidity_overlap_and_thin():
    overlap = session_liquidity_flags(13, False)
    assert overlap["named"] == "overlap_london_ny"
    assert overlap["overlap"] is True
    assert overlap["thin"] is False
    asia = session_liquidity_flags(3, False)
    assert asia["thin"] is True
    friday = session_liquidity_flags(17, True)
    assert friday["named"] == "friday_cutoff"
    assert session_liquidity_flags(None, False)["named"] == "unknown"


def test_event_join_empty_spine_is_not_no_high():
    empty = event_join_features({"spine_empty": True, "events": []})
    assert empty["usd_high_in_window"] is None
    assert empty["source"] == "news_spine_empty"
    news = {
        "spine_empty": False,
        "events": [
            {"impact": "HIGH", "currency": "USD", "minutes_from_as_of": 10, "event": "CPI"},
            {"impact": "HIGH", "currency": "GBP", "minutes_from_as_of": 200, "event": "BOE"},
        ],
    }
    joined = event_join_features(news)
    assert joined["usd_high_in_window"] is True
    assert joined["gbp_high_in_window"] is False
    assert "USD" in joined["joined_currencies"]
    assert "GBP" in joined["joined_currencies"]


def test_occupancy_book_counts_clusters():
    trades = trades_from_dicts(
        [
            {
                "ticket": 1,
                "symbol": "XAUUSD",
                "open_time_utc": "2026-09-17T07:30:55Z",
                "still_open": True,
                "_kind": "open",
            },
            {
                "ticket": 2,
                "symbol": "US30.cash",
                "open_time_utc": "2026-09-17T11:00:00Z",
                "still_open": True,
                "_kind": "open",
            },
            {
                "ticket": 3,
                "symbol": "EURUSD",
                "open_time_utc": "2026-09-17T08:00:00Z",
                "close_time_utc": "2026-09-17T09:00:00Z",
                "still_open": False,
            },
        ],
        stamp=lambda r: datetime.fromisoformat(str(r["open_time_utc"]).replace("Z", "+00:00")),
    )
    book = occupancy_book_at(trades, as_of_utc=AS_OF, this_ticket="x")
    assert book["clusters_open"]["metals"] == 1
    assert book["clusters_open"]["index"] == 1
    assert book["clusters_open"]["fx_major"] == 0
    assert book["n_clusters_open"] == 2
    assert book["book_open_n"] == 2
    absent = occupancy_book_at(None, as_of_utc=AS_OF)
    assert absent["clusters_open"] is None
    assert absent["occupancy_source"] == "deal_tape_absent"


def test_gold_state_world_does_not_fail_sufficient():
    state = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        origin_organism="f5_challenge",
        books=None,
        peer_books={},
    )
    assert "world" in state
    assert state["world"]["usd_proxy"]["named"] == "unassembled"
    assert state["completeness"]["cross_asset_peers"] is False
    assert state["completeness"]["state_sufficient_for_live"] is False
    assert "world.usd_proxy" not in state["completeness"]["missing_fields"]


def test_world_state_historical_lab_is_not_challenge_true():
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        origin_organism="historical_lab",
        peer_books={},
    )
    assert world["challenge_true"] is False
    assert world["april_historical_used"] is False
    assert world["dxy_used"] is False


def test_load_peer_books_does_not_invent_fx():
    peers = load_peer_books()
    assert "EURUSD" not in peers or challenge_tape_present("EURUSD")
    assert challenge_tape_present("XAUUSD") is True
    gbp = books_for_symbol("GBPUSD")
    assert gbp is None or challenge_tape_present("GBPUSD")


def test_survey_and_prove_harness_on_challenge_pack():
    survey = survey_challenge_surface()
    landed = survey["landed_challenge_symbols"]
    wanted = survey["wanted_challenge_m15"]
    fx = bool(wanted.get("EURUSD") and wanted.get("GBPUSD") and wanted.get("USDJPY"))
    us30 = bool(wanted.get("US30"))
    assert "XAUUSD" in landed
    assert wanted["XAUUSD"] is True
    assert survey["april_historical_is_not_challenge"] is True
    assert survey["dxy_is_not_challenge"] is True
    assert survey["chair_vps_claim_20260918"]["EURUSD"]["claimed"] is True
    assert survey["chair_vps_claim_20260918"]["EURUSD"]["hydrated_here"] is fx
    assert survey["this_vm_hydrated_from_vps"] is fx
    if fx:
        assert survey["hydrate_channel"] == "chair_attached_zip"
        for sym in ("EURUSD", "GBPUSD", "USDJPY"):
            assert sym in landed
            admit = (survey.get("peer_admit") or {}).get(sym) or {}
            assert admit.get("ok") is True
            assert str(admit.get("last_utc") or "") >= "2026-09-17"
    else:
        assert landed == ["XAUUSD"]
        assert wanted["EURUSD"] is False
        assert survey["hydrate_channel"] is None
    us30_claim = survey["chair_vps_claim_20260918"]["US30"]
    if us30:
        assert "US30" in landed
        assert us30_claim["claimed"] is True
        assert us30_claim["hydrated_here"] is True
        assert "US30_cash" in us30_claim.get("aliases_on_disk", [])
        assert us30_claim.get("first_pass") == "ftmo_symbol_resolve_failed"
    else:
        assert us30_claim["claimed"] is False
        assert us30_claim["hydrated_here"] is False
        assert us30_claim.get("reason") == "ftmo_symbol_resolve_failed"
    assert "metals" in survey["deal_clusters"]
    payload = run_prove(write=False)
    assert payload["never_place"] is True
    assert payload["physical_size"]["stays_flow_x_cost"] is True
    assert payload["physical_size"]["new_size_axis_applied"] is False
    assert payload["hydrate"]["copy"]["april_historical_used"] is False
    assert payload["hydrate"]["copy"]["n_copied"] == 0
    assert payload.get("apply_any") is False
    assert payload.get("no_ca_apply_flip") is True
    assert all(t["apply"] is False for t in payload["targets"])
    assert all((f.get("to") or "") != "APPLIED_NAMED" for f in (payload.get("flips_vs_prior") or []))
    by_id = {t["id"]: t for t in payload["targets"]}
    if fx:
        assert by_id["CA-USD-001"]["verdict"] == "PROVED_SHADOW"
        assert by_id["CA-CORR-001"]["verdict"] == "PROVED_SHADOW"
        assert by_id["CA-USD-001"]["apply"] is False
        assert by_id["CA-CORR-001"]["apply"] is False
    else:
        assert by_id["CA-USD-001"]["verdict"] == "NOT_PROVED"
        assert by_id["CA-CORR-001"]["verdict"] == "NOT_PROVED"
        assert "peer Challenge M15 not landed" in " ".join(by_id["CA-USD-001"]["reasons"])
    if us30:
        assert by_id["CA-IDX-001"]["verdict"] == "PROVED_SHADOW"
        assert by_id["CA-IDX-001"]["apply"] is False
    else:
        assert by_id["CA-IDX-001"]["verdict"] == "NOT_PROVED"
    if us30 and wanted.get("USDJPY"):
        assert by_id["CA-RSK-001"]["verdict"] == "PROVED_SHADOW"
        assert by_id["CA-RSK-001"]["apply"] is False
    else:
        assert by_id["CA-RSK-001"]["verdict"] == "NOT_PROVED"
    # Clock + news + occupancy can move on the current pack.
    assert by_id["CA-LIQ-001"]["n_decidable"] >= 20
    assert by_id["CA-EVT-001"]["n_decidable"] >= 20
    assert by_id["CA-OCC-001"]["n_decidable"] >= 20
    assert payload["n_rows"] >= 20
