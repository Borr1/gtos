import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.components.ultimate_book.primitives import Bar
from src.judgment.bars import StampedBar
from src.judgment.gold_state import assemble_gold_state_v0
from src.judgment.occupancy import trades_from_dicts
from src.judgment.world_questions import (
    PACK_ID,
    WORLD_NOUL_TARGETS,
    calendar_honest_world_named,
    compose_world_shadow,
    gold_fights_risk_named,
    noul_ids,
    world_fanout_questions,
    world_systemone_payload,
)
from src.judgment.world_state import (
    DXY_REJECTED_REASON,
    SCHEMA,
    YIELD_ABSENT_REASON,
    assemble_world_state_v0,
    attach_world,
    gold_sold_into_usd_strength,
    pearson,
)


AS_OF = datetime(2026, 9, 17, 11, 0, tzinfo=timezone.utc)
REPO = Path(__file__).resolve().parents[2]


def _book(
    n: int,
    start: datetime,
    step_hours: float,
    closes: list[float] | None = None,
    *,
    half_range: float = 0.0005,
) -> list[StampedBar]:
    out: list[StampedBar] = []
    for i in range(n):
        utc = start + timedelta(hours=step_hours * i)
        if closes and i < len(closes):
            close = closes[i]
        elif closes:
            close = closes[-1] + (closes[-1] - closes[-2] if len(closes) > 1 else 0.01) * (
                i - len(closes) + 1
            )
        else:
            close = 1.0
        out.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=close, h=close + half_range, l=close - half_range, c=close, v=1.0),
                source_path="tmp",
            )
        )
    return out


def _trending(n: int, start: float, step: float) -> list[float]:
    return [start + step * i for i in range(n)]


def test_unassembled_world_does_not_invent_dxy_yield_or_high():
    world = assemble_world_state_v0(
        as_of_utc=datetime(2026, 4, 15, 12, tzinfo=timezone.utc),
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
        host_events=[],
    )
    assert world["schema"] == SCHEMA
    assert world["never_place"] is True
    assert world["never_invent_news_protocol"] is True
    assert world["never_ingest_raw_x"] is True
    assert world["usd"]["dxy"]["reason"] == DXY_REJECTED_REASON
    assert world["usd"]["dxy"]["series"] is None
    assert world["usd"]["dxy"]["usable_as_ice_dxy"] is False
    assert world["usd"]["dxy"]["file_present"] is True
    assert world["rates"]["named_yield"]["reason"] == YIELD_ABSENT_REASON
    assert world["rates"]["assembled"] is False
    assert world["completeness"]["named_yield"] is False
    assert world["completeness"]["dxy"] is False
    assert world["news"]["spine_empty"] is True
    assert world["news"]["events"] == []
    assert world["news"]["high_in_f5_window"] is None
    assert world["narrative"]["raw_x_forbidden"] is True
    assert world["narrative"]["source"] == "unassembled"
    assert world["completeness"]["state_sufficient_for_desk"] is False
    assert "rates.named_yield" in world["completeness"]["missing_fields"]
    assert "usd.dxy" in world["completeness"]["missing_fields"]
    dumped = str(world)
    assert "/v1/calendar" not in dumped
    assert "wss://" not in dumped.lower()
    assert "https://news" not in dumped.lower()


def test_expost_rejected_on_live_intent_world():
    try:
        assemble_world_state_v0(
            as_of_utc=AS_OF,
            as_of_clock="live_intent",
            forbid_expost={"broker_net": -12.0},
            spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
        )
    except ValueError as exc:
        assert "EXPOST" in str(exc)
    else:
        raise AssertionError("expected EXPOST refuse")


def test_usd_stance_from_named_eurusd_and_usdjpy():
    # EURUSD down + USDJPY up → USD stronger (two agreeing proxies).
    eurusd = _book(20, datetime(2026, 9, 1, tzinfo=timezone.utc), 24, _trending(20, 1.20, -0.01))
    usdjpy = _book(20, datetime(2026, 9, 1, tzinfo=timezone.utc), 24, _trending(20, 140.0, 0.8))
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        focus={"symbol": "XAUUSD", "side": "short", "sleeve": "dsp_two_bar_t"},
        cross_books={"EURUSD": {"d1": eurusd, "h4": []}, "USDJPY": {"d1": usdjpy, "h4": []}},
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    assert world["usd"]["source"] == "usd_fx_basket"
    assert world["usd"]["stance"] == "stronger"
    assert world["rates"]["path_named"] == "usd_proxy_basket"
    assert world["rates"]["usd_proxy_only"] is True
    assert world["rates"]["assembled"] is False
    assert world["corr"]["code_gold_sold_into_usd_strength"] is True
    assert world["completeness"]["state_sufficient_for_desk"] is True
    assert gold_sold_into_usd_strength(world["focus"], world["usd"]) is True


def test_gold_usd_corr_against_on_inverse_series():
    gold = _book(40, datetime(2026, 8, 1, tzinfo=timezone.utc), 24, _trending(40, 2600.0, 5.0))
    eurusd = _book(40, datetime(2026, 8, 1, tzinfo=timezone.utc), 24, _trending(40, 1.05, 0.002))
    # Gold up, EURUSD up → inv EURUSD (USD) down → gold against USD.
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        gold_books={"d1": gold},
        cross_books={"EURUSD": {"d1": eurusd, "h4": []}},
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    rel = world["corr"]["gold_vs_usd"]
    assert rel["source"] == "named_d1_returns"
    assert rel["pair"] == "XAUUSD_vs_inv_EURUSD"
    assert rel["corr_20d"] is not None
    assert rel["relation"] == "against_usd"


def test_pearson_and_thin_series_unassembled():
    assert pearson([1, 2, 3], [1, 2, 3]) is None  # n < 10
    xs = list(range(12))
    assert pearson(xs, xs) == 1.0
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        gold_books={"d1": _book(3, datetime(2026, 9, 14, tzinfo=timezone.utc), 24)},
        cross_books={"EURUSD": {"d1": _book(3, datetime(2026, 9, 14, tzinfo=timezone.utc), 24)}},
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    assert world["corr"]["gold_vs_usd"]["source"] == "unassembled"


def test_occupancy_missing_tape_is_not_crowded():
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        focus={"symbol": "XAUUSD", "side": "long"},
        trades=None,
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    assert world["occupancy"]["source"] == "unassembled"
    assert world["occupancy"]["focus_cluster_crowded"] is None
    assert world["occupancy"]["focus_cluster"] == "metals"


def test_cluster_crowded_from_challenge_deals():
    trades = trades_from_dicts(
        [
            {
                "ticket": "1",
                "symbol": "XAGUSD",
                "sleeve": "metals",
                "open_time_utc": "2026-09-17T08:00:00Z",
                "still_open": True,
                "_kind": "open",
            }
        ],
        stamp=lambda row: datetime(2026, 9, 17, 8, tzinfo=timezone.utc)
        if row.get("open_time_utc")
        else None,
    )
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        focus={"symbol": "XAUUSD", "side": "short", "candidate_id": "xau-1"},
        trades=trades,
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    assert world["occupancy"]["source"] == "challenge_deals"
    assert world["occupancy"]["focus_cluster_crowded"] is True
    assert "XAGUSD" in world["occupancy"]["clusters"]["metals"]["open_symbols"]
    assert compose_world_shadow(world)["chair_draft"] == "veto"


def test_calendar_honest_false_when_host_not_read():
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        spines={
            "spine_id": "h",
            "sources": ["data/news/f5_high_calendar_host_20260916.json"],
            "events": [
                {
                    "datetime_utc": "2026-09-17T11:00:00Z",
                    "event": "BOE",
                    "impact": "HIGH",
                    "currency": "GBP",
                    "challenge_axis": True,
                    "_dt": datetime(2026, 9, 17, 11, tzinfo=timezone.utc),
                }
            ],
            "n_files": 1,
        },
        host_events=[
            {
                "event": "news_t15_pending_cancel",
                "ts_utc": "2026-09-17T10:50:00Z",
                "inventory_status": "NOT_READ",
                "n_events_in_window": 1,
            }
        ],
    )
    assert world["news"]["spine_empty"] is False
    assert world["host_news"]["host_news_inventory_status"] == "NOT_READ"
    assert calendar_honest_world_named(world) is False


def test_attach_world_and_compose_never_resizes():
    gold = assemble_gold_state_v0(
        as_of_utc=AS_OF,
        side="short",
        sleeve="dsp_two_bar_t",
        origin_organism="f5_challenge",
        cost={"spread_r_of_stop": 0.12},
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        gold=gold,
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    assert world["liquidity"]["source"] == "gold_cost_and_session"
    assert world["liquidity"]["spread_r_of_stop"] == 0.12
    bundled = attach_world(gold, world)
    assert bundled["schema"] == "gtos.judgment.jev_state.gold_plus_world.v0"
    assert bundled["never_place"] is True
    composed = compose_world_shadow(world)
    assert composed["never_resize"] is True
    assert composed["chair_draft"] in {"abstain", "label", "veto"}
    assert composed["chair_draft"] != "enforce"
    assert composed["disposition"] == "world_label_only"


def test_gold_fights_risk_named():
    world = {
        "focus": {"side": "short"},
        "risk": {"stance": "risk_on"},
    }
    assert gold_fights_risk_named(world) is True
    world["risk"]["stance"] = "risk_off"
    assert gold_fights_risk_named(world) is False
    world["risk"]["stance"] = "unassembled"
    assert gold_fights_risk_named(world) is None


def test_question_pack_ids_and_no_protocol_url():
    questions = world_fanout_questions()
    assert set(noul_ids()) <= set(questions)
    assert set(WORLD_NOUL_TARGETS) == set(noul_ids())
    for name, spec in WORLD_NOUL_TARGETS.items():
        assert questions[name]["type"] == "noul"
        assert spec["chair"] in {"LABEL", "VETO", "ENFORCE"}
        assert spec["yes"]
        assert spec["challenge_true"]
    payload = world_systemone_payload({"world": {"schema": SCHEMA}})
    assert payload["pack"] == PACK_ID
    assert payload["model"] == "jev-1.13.0"
    blob = str(questions) + str(WORLD_NOUL_TARGETS)
    assert "api.forexfactory" not in blob.lower()
    src = (REPO / "src" / "judgment" / "world_state.py").read_text(encoding="utf-8")
    qs = (REPO / "src" / "judgment" / "world_questions.py").read_text(encoding="utf-8")
    schema = (REPO / "judgment" / "astra" / "schemas" / "world_state_v0.json").read_text(encoding="utf-8")
    for text in (src, qs, schema):
        assert "https://news" not in text.lower()
        assert "/v1/calendar" not in text
        assert "wss://" not in text.lower()


def test_world_pack_json_matches_noul_targets():
    packed = json.loads((REPO / "judgment" / "astra" / "lab" / "wires" / "WORLD_PACK_V0.json").read_text(encoding="utf-8"))
    assert packed["schema"] == PACK_ID
    assert packed["never_place"] is True
    assert packed["never_resize"] is True
    assert set(packed["noul_targets"]) == set(WORLD_NOUL_TARGETS)
