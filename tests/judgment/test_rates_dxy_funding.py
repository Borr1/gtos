import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.components.ultimate_book.primitives import Bar
from src.judgment.bars import StampedBar
from src.judgment.named_sources import (
    DXY_REJECTED_REASON,
    ICE_DXY_HIGH,
    ICE_DXY_LOW,
    inspect_dxy_csv,
    named_source_inventory,
    usd_return_for_pair,
)
from src.judgment.rates_dxy_funding import (
    NEVER,
    PACK_ID,
    SCHEMA,
    assemble_rates_dxy_funding_v0,
    attach_rdf,
    prove_rdf_challenge_as_of,
    rdf_noul_targets,
)
from src.judgment.rdf_questions import (
    RDF_NOUL_TARGETS,
    compose_rdf_shadow,
    rdf_fanout_questions,
    rdf_noul_ids,
    rdf_systemone_payload,
)
from src.judgment.world_state import assemble_world_state_v0


REPO = Path(__file__).resolve().parents[2]
FIX = Path(__file__).resolve().parent / "fixtures" / "rates_dxy_funding"
AS_OF = datetime(2026, 9, 17, 11, 0, tzinfo=timezone.utc)
SIERRA_ZN = (
    REPO
    / "data"
    / "sierra_ohlcv_roots"
    / "sierra_first_wave_bounded_conversion_20260504"
    / "ZN_CONTROL_D1.csv"
)


def _parse_utc(raw: str) -> datetime:
    text = raw.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _book_from_spec(spec: dict, *, source_path: str) -> list[StampedBar]:
    start = _parse_utc(spec["start"])
    n = int(spec["n"])
    step = float(spec["step_hours"])
    close0 = float(spec["start_close"])
    dclose = float(spec["step_close"])
    out: list[StampedBar] = []
    for i in range(n):
        utc = start + timedelta(hours=step * i)
        close = close0 + dclose * i
        out.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=close, h=close + abs(dclose) * 0.2 + 0.01, l=close - abs(dclose) * 0.2 - 0.01, c=close, v=1.0),
                source_path=source_path,
            )
        )
    return out


def _books_map(raw: dict | None, *, fixture_id: str) -> dict[str, dict[str, list[StampedBar]]]:
    out: dict[str, dict[str, list[StampedBar]]] = {}
    for symbol, tfs in (raw or {}).items():
        out[symbol] = {
            tf: _book_from_spec(spec, source_path=f"fixture:{fixture_id}:{symbol}:{tf}")
            for tf, spec in tfs.items()
        }
    return out


def _load_fixture(name: str) -> dict:
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _assemble_fixture(name: str):
    spec = _load_fixture(name)
    as_of = _parse_utc(spec["as_of_utc"])
    fid = spec["id"]
    return assemble_rates_dxy_funding_v0(
        as_of_utc=as_of,
        focus=spec.get("focus"),
        cross_books=_books_map(spec.get("cross_books"), fixture_id=fid),
        yield_books=_books_map(spec.get("yield_books"), fixture_id=fid) or None,
        funding_rows=spec.get("funding_rows"),
    ), spec


def test_usd_return_mapping():
    assert usd_return_for_pair("EURUSD", 0.01) == -0.01
    assert usd_return_for_pair("USDJPY", 0.01) == 0.01
    assert usd_return_for_pair("NAS100", 0.01) is None


def test_inventory_names_real_paths_and_no_invented_endpoints():
    inv = named_source_inventory()
    assert inv["never_invent_endpoints"] is True
    xau = inv["challenge_true"]["xau"]
    assert xau["m15"]["present"] is True
    assert xau["m15"]["path"].endswith("XAUUSD_M15.csv")
    # Chair 2026-09-18: peer multi + GBPJPY/EURGBP landed. NAS100/UK100 still empty.
    assert inv["challenge_true"]["multi_any_landed"] is True
    for symbol in ("EURUSD", "GBPUSD", "USDJPY", "US30"):
        assert inv["challenge_true"]["multi_fx_index"][symbol]["any"] is True
        assert "h4" in inv["challenge_true"]["multi_fx_index"][symbol]["present_tfs"]
        assert "m15" in inv["challenge_true"]["multi_fx_index"][symbol]["present_tfs"]
    for symbol in ("NAS100", "UK100"):
        assert inv["challenge_true"]["multi_fx_index"][symbol]["any"] is False
    for symbol in ("EURGBP", "GBPJPY"):
        assert inv["challenge_true"]["cross_fx"][symbol]["any"] is True
    assert inv["lab_only"]["historical_2026"]["EURUSD"]["any"] is True
    assert inv["rates"]["named_yield_csvs"] == []
    assert inv["funding"]["named_funding_csvs"] == []
    assert inv["funding"]["fred_cache_dir"]["present"] is False
    assert inv["forbidden_absent"]["NEWS_PROTOCOL"] == []
    dxy = inv["dxy"]
    assert dxy["file_present"] is True
    assert dxy["usable_as_ice_dxy"] is False
    assert dxy["reason"] == DXY_REJECTED_REASON
    assert dxy["last_close"] is not None
    assert dxy["last_close"] < ICE_DXY_LOW
    zn = inv["rates"]["sierra_zn_control_d1"]
    assert zn["present"] is True
    assert zn["n_rows"] == 3
    assert zn["allowed_use"] == "rates_liquidity_control_only"
    ids = {row["id"] for row in inv["repair_items"]}
    assert "land_challenge_multi_fx_index" in ids
    assert "replace_mislabeled_dxy" in ids
    assert "ingest_named_yield" in ids
    assert "ingest_funding_stress_feed" in ids
    assert "do_not_invent_news_protocol" in ids
    blob = json.dumps(inv)
    assert "NEWS_PROTOCOL" in blob  # named as missing
    assert "https://api." not in blob
    assert "wss://" not in blob
    assert "forexfactory" not in blob.lower()
    assert "fred.stlouisfed.org" not in blob


def test_default_assembly_is_null_and_rejects_clone_dxy():
    # Caller can opt out of disk auto-load.
    rdf = assemble_rates_dxy_funding_v0(as_of_utc=AS_OF, cross_books={})
    assert rdf["schema"] == SCHEMA
    for key, flag in NEVER.items():
        assert rdf[key] is flag
    twins = rdf_noul_targets(rdf)
    assert twins == {
        "usd_impulse": None,
        "rates_impulse": None,
        "funding_stress": None,
        "risk_on_off": None,
    }
    assert rdf["usd_impulse"]["challenge_true_target"] is None
    assert rdf["rates_impulse"]["reason"] == "no_named_yield_tape_on_this_clone"
    assert rdf["funding_stress"]["gold_spread_is_not_funding"] is True
    assert rdf["funding_stress"]["vix_is_not_funding"] is True
    assert rdf["dxy"]["usable_as_ice_dxy"] is False
    assert rdf["dxy"]["series"] is None
    assert rdf["dxy"]["reason"] == DXY_REJECTED_REASON
    assert rdf["completeness"]["dxy"] is False
    dumped = json.dumps(rdf)
    assert "NEWS_PROTOCOL" not in dumped
    assert "wss://" not in dumped
    assert "/v1/calendar" not in dumped
    composed = compose_rdf_shadow(rdf)
    assert composed["never_resize"] is True
    assert composed["never_apply_size"] is True
    assert composed["chair_draft"] == "abstain"
    assert composed["disposition"] == "rdf_label_only"
    assert composed["chair_draft"] != "enforce"


def test_challenge_as_of_assembles_usd_and_risk_keeps_rates_funding_null():
    rdf = assemble_rates_dxy_funding_v0(as_of_utc=AS_OF)
    assert rdf["usd_impulse"]["assembled"] is True
    assert rdf["usd_impulse"]["feed_class"] == "challenge_true"
    assert rdf["usd_impulse"]["challenge_true"] is True
    assert rdf["usd_impulse"]["value"] is False
    assert rdf["usd_impulse"]["challenge_true_target"] is False
    assert rdf["usd_impulse"]["stance"] == "flat"
    assert rdf["usd_impulse"]["dxy_used"] is False
    assert set(rdf["usd_impulse"]["present"]) >= {"EURUSD", "GBPUSD", "USDJPY"}
    assert rdf["risk_on_off"]["feed_class"] == "challenge_true"
    assert rdf["risk_on_off"]["challenge_true"] is True
    assert rdf["risk_on_off"]["stance"] == "risk_on"
    assert rdf["risk_on_off"]["value"] is False
    assert rdf["risk_on_off"]["yes_event"] == "risk_off"
    assert "US30" in rdf["risk_on_off"]["present"]
    assert rdf["rates_impulse"]["value"] is None
    assert rdf["rates_impulse"]["assembled"] is False
    assert rdf["rates_impulse"]["reason"] == "no_named_yield_tape_on_this_clone"
    assert rdf["funding_stress"]["value"] is None
    assert rdf["funding_stress"]["assembled"] is False
    assert rdf["funding_stress"]["gold_spread_is_not_funding"] is True
    assert rdf["dxy"]["usable_as_ice_dxy"] is False
    assert rdf["dxy"]["reason"] == DXY_REJECTED_REASON
    assert rdf["dxy"]["series"] is None
    composed = compose_rdf_shadow(rdf)
    assert composed["chair_draft"] == "label"
    assert composed["chair_draft"] != "enforce"
    assert composed["never_apply_size"] is True
    assert composed["disposition"] == "rdf_label_only"
    prove = prove_rdf_challenge_as_of(as_of_utc=AS_OF)
    assert prove["never_apply_size"] is True
    assert prove["chair_draft"] == "label"
    assert prove["challenge_true"]["usd_impulse"] is True
    assert prove["challenge_true"]["risk_on_off"] is True
    assert prove["challenge_true"]["rates_impulse"] is False
    assert prove["challenge_true"]["funding_stress"] is False
    assert prove["dxy"]["usable_as_ice_dxy"] is False
    receipt = json.loads(
        (REPO / "judgment" / "astra" / "lab" / "wires" / "RDF_CHALLENGE_ASOF_RECEIPT_V0.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["never_apply_size"] is True
    assert receipt["chair_draft"] == "label"
    assert receipt["noul_targets"]["rates_impulse"] is None
    assert receipt["noul_targets"]["funding_stress"] is None
    assert receipt["dxy"]["usable_as_ice_dxy"] is False
    assert receipt["dxy"]["reason"] == DXY_REJECTED_REASON


def test_usd_impulse_fixture_is_lab_not_challenge():
    rdf, spec = _assemble_fixture("usd_impulse_stronger.json")
    assert rdf["usd_impulse"]["value"] is True
    assert rdf["usd_impulse"]["lab_target"] is True
    assert rdf["usd_impulse"]["challenge_true"] is False
    assert rdf["usd_impulse"]["challenge_true_target"] is None
    assert rdf["usd_impulse"]["stance"] == spec["expect"]["usd_stance"]
    assert rdf["usd_impulse"]["dxy_used"] is False
    assert rdf["usd_impulse"]["feed_class"] == "lab_or_fixture"
    assert rdf["rates_impulse"]["value"] is None
    assert rdf["funding_stress"]["value"] is None
    assert compose_rdf_shadow(rdf)["chair_draft"] == "label"


def test_risk_off_fixture():
    rdf, spec = _assemble_fixture("risk_off.json")
    assert rdf["risk_on_off"]["value"] is True
    assert rdf["risk_on_off"]["stance"] == spec["expect"]["risk_stance"]
    assert rdf["risk_on_off"]["yes_event"] == "risk_off"
    assert rdf["risk_on_off"]["challenge_true_target"] is None
    assert rdf["risk_on_off"]["vix_used"] is False


def test_injected_yield_assembles_rates_impulse_lab_only():
    rdf, spec = _assemble_fixture("yield_us10y.json")
    assert rdf["rates_impulse"]["value"] is spec["expect"]["rates_impulse"]
    assert rdf["rates_impulse"]["assembled"] is True
    assert rdf["rates_impulse"]["named_yield"] == "US10Y"
    assert rdf["rates_impulse"]["usd_fx_is_not_a_yield"] is True
    assert rdf["rates_impulse"]["challenge_true_target"] is None


def test_injected_ted_assembles_funding_and_gold_spread_does_not():
    rdf, spec = _assemble_fixture("funding_ted.json")
    assert rdf["funding_stress"]["value"] is spec["expect"]["funding_stress"]
    assert rdf["funding_stress"]["named_series"] == ["TED"]
    goldish = assemble_rates_dxy_funding_v0(
        as_of_utc=AS_OF,
        gold={"cost": {"spread_r_of_stop": 0.40}},
    )
    assert goldish["funding_stress"]["value"] is None
    assert goldish["funding_stress"]["gold_spread_is_not_funding"] is True


def test_dxy_inspect_rejects_clone_and_accepts_sane_fixture():
    clone = inspect_dxy_csv()
    assert clone["file_present"] is True
    assert clone["usable_as_ice_dxy"] is False
    assert ICE_DXY_LOW <= ICE_DXY_HIGH
    rejected = inspect_dxy_csv(FIX / "dxy_rejected.csv")
    assert rejected["usable_as_ice_dxy"] is False
    assert rejected["reason"] == DXY_REJECTED_REASON
    sane = inspect_dxy_csv(FIX / "dxy_sane.csv")
    assert sane["usable_as_ice_dxy"] is True
    assert sane["last_close"] == 104.20
    assert sane["source"] == "named_dxy_csv"
    rdf = assemble_rates_dxy_funding_v0(as_of_utc=AS_OF, dxy_path=FIX / "dxy_sane.csv")
    # Usable DXY still does not become a Challenge-true impulse (no series attached).
    assert rdf["dxy"]["usable_as_ice_dxy"] is True
    assert rdf["dxy"]["series"] is None
    assert rdf["dxy"]["challenge_true"] is False
    assert rdf["usd_impulse"]["dxy_used"] is False


def test_sierra_zn_control_does_not_flip_rates_impulse():
    if not SIERRA_ZN.is_file():
        return
    from src.judgment.bars import load_ohlc_csv

    rows = load_ohlc_csv(SIERRA_ZN)
    assert len(rows) == 3
    # April as-of could read the 3 days; still must refuse as rates print.
    rdf = assemble_rates_dxy_funding_v0(
        as_of_utc=datetime(2026, 4, 17, 21, tzinfo=timezone.utc),
        yield_books={"ZN": {"d1": rows}},
    )
    assert rdf["rates_impulse"]["value"] is None
    assert rdf["rates_impulse"]["assembled"] is False
    assert rdf["rates_impulse"]["feed_class"] == "sierra_control"
    assert "control_only" in (rdf["rates_impulse"]["reason"] or "")


def test_april_lab_books_are_stale_on_september_as_of():
    eurusd = REPO / "data" / "historical_2026" / "EURUSD_D1.csv"
    if not eurusd.is_file():
        return
    from src.judgment.bars import load_ohlc_csv

    rdf = assemble_rates_dxy_funding_v0(
        as_of_utc=AS_OF,
        cross_books={"EURUSD": {"d1": load_ohlc_csv(eurusd)}},
    )
    assert rdf["usd_impulse"]["value"] is None
    assert rdf["usd_impulse"]["assembled"] is False
    assert rdf["usd_impulse"]["challenge_true_target"] is None


def test_question_pack_and_no_protocol_url():
    questions = rdf_fanout_questions()
    assert set(rdf_noul_ids()) == set(RDF_NOUL_TARGETS)
    assert set(rdf_noul_ids()) <= set(questions)
    for name, spec in RDF_NOUL_TARGETS.items():
        assert questions[name]["type"] == "noul"
        assert spec["chair"] == "LABEL"
        assert spec["effect"] == "label"
    payload = rdf_systemone_payload({"rdf": {"schema": SCHEMA}})
    assert payload["pack"] == PACK_ID
    assert payload["model"] == "jev-1.13.0"
    packed = json.loads((REPO / "judgment" / "astra" / "lab" / "wires" / "RDF_PACK_V0.json").read_text(encoding="utf-8"))
    assert packed["never_apply_size"] is True
    assert set(packed["noul_targets"]) == set(RDF_NOUL_TARGETS)
    for text in (
        (REPO / "src" / "judgment" / "rates_dxy_funding.py").read_text(encoding="utf-8"),
        (REPO / "src" / "judgment" / "rdf_questions.py").read_text(encoding="utf-8"),
        (REPO / "src" / "judgment" / "named_sources.py").read_text(encoding="utf-8"),
        (REPO / "judgment" / "astra" / "schemas" / "rates_dxy_funding_v0.json").read_text(encoding="utf-8"),
    ):
        assert "https://news" not in text.lower()
        assert "/v1/calendar" not in text
        assert "wss://" not in text.lower()
        assert "api.forexfactory" not in text.lower()


def test_world_state_attaches_rdf_and_does_not_resize():
    world = assemble_world_state_v0(
        as_of_utc=AS_OF,
        spines={"spine_id": "x", "sources": [], "events": [], "n_files": 0},
    )
    assert "rdf" in world
    assert world["rdf"]["schema"] == SCHEMA
    assert world["rdf"]["never_apply_size"] is True
    assert world["usd"]["dxy"]["reason"] == DXY_REJECTED_REASON
    assert world["usd"]["dxy"]["usable_as_ice_dxy"] is False
    assert world["usd"]["dxy"]["series"] is None
    bundled = attach_rdf(world, world["rdf"])
    assert bundled["never_resize"] is True
    assert compose_rdf_shadow(world["rdf"])["never_apply_size"] is True
