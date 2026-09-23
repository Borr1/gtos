from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.components.ultimate_book.primitives import Bar
from src.judgment.bars import (
    StampedBar,
    admit_challenge_peer_csv,
    books_for_symbol,
    challenge_tape_present,
    copy_multi_csvs_if_present,
    file_stem_for,
    landed_challenge_symbols,
    load_ohlc_csv,
    normalize_symbol,
    resolve_challenge_tf,
)
from src.judgment.gold_state import assemble_gold_state_v0


def test_file_stems_us30_uk100_cash():
    assert normalize_symbol("US30.cash") == "US30"
    assert normalize_symbol("US30_cash") == "US30"
    assert normalize_symbol("UK100.CASH") == "UK100"
    assert file_stem_for("US30.cash") == "US30_cash"
    assert file_stem_for("UK100") == "UK100_cash"
    assert file_stem_for("EURUSD") == "EURUSD"
    assert file_stem_for("XAUUSD") == "XAUUSD"


def test_april_historical_is_not_challenge_tape():
    """Repo data/GBPUSD_M15.csv is not Challenge-true. Do not wear it."""
    assert not str(resolve_challenge_tf("GBPUSD", "M15")).endswith("data/GBPUSD_M15.csv")
    hist = Path(__file__).resolve().parents[2] / "data" / "GBPUSD_M15.csv"
    challenge = resolve_challenge_tf("GBPUSD", "M15")
    if hist.is_file() and challenge.is_file():
        assert challenge.resolve() != hist.resolve()


def test_search_dir_env_and_stem(tmp_path, monkeypatch):
    monkeypatch.setenv("GTOS_CHALLENGE_BAR_MULTI", str(tmp_path))
    header = "time_utc,open,high,low,close,tick_volume,spread,real_volume,time_server_labeled\n"
    (tmp_path / "US30_cash_M15.csv").write_text(
        header + "2026-09-17T11:00:00Z,1,1.1,0.9,1.0,1,0,0,2026-09-17T14:00:00Z\n",
        encoding="utf-8",
    )
    (tmp_path / "US30_cash_H4.csv").write_text(
        header + "2026-09-17T09:00:00Z,1,1.1,0.9,1.0,1,0,0,2026-09-17T12:00:00Z\n",
        encoding="utf-8",
    )
    assert challenge_tape_present("US30.cash") is True
    assert challenge_tape_present("US30") is True
    assert "US30" in landed_challenge_symbols()
    path = resolve_challenge_tf("US30", "M15")
    assert path.name == "US30_cash_M15.csv"
    rows = load_ohlc_csv(path)
    assert rows[0].utc == datetime(2026, 9, 17, 11, 0, tzinfo=timezone.utc)
    books = books_for_symbol("US30")
    assert books is not None
    assert books["m15"]
    assert books["d1"] == []


def test_copy_does_not_invent(tmp_path):
    result = copy_multi_csvs_if_present(tmp_path)
    assert result["invented"] is False
    assert result["april_historical_used"] is False
    assert result["n_copied"] == 0


def test_admit_rejects_april_exports_and_copy_refuses_them():
    repo = Path(__file__).resolve().parents[2]
    april = repo / "exports" / "multi_instrument" / "EURUSD_M15.csv"
    assert april.is_file()
    admit = admit_challenge_peer_csv(april)
    assert admit["ok"] is False
    assert admit["reason"] == "no_time_utc_column_april_or_broker_naive"
    xau = repo / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "XAUUSD_M15.csv"
    assert admit_challenge_peer_csv(xau)["ok"] is True
    dest = repo / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "multi" / "EURUSD_M15.csv"
    dest_before = dest.read_bytes() if dest.is_file() else None
    dest_admit_before = admit_challenge_peer_csv(dest) if dest.is_file() else None
    result = copy_multi_csvs_if_present(repo / "exports" / "multi_instrument")
    assert result["n_copied"] == 0
    assert result["april_historical_used"] is False
    assert result["n_rejected"] >= 3
    if dest_before is None:
        assert not dest.is_file()
    else:
        # Chair zip may already occupy the landing slot. April copy must not overwrite it.
        assert dest.is_file()
        assert dest.read_bytes() == dest_before
        after = admit_challenge_peer_csv(dest)
        assert after.get("ok") is True
        assert dest_admit_before and dest_admit_before.get("ok") is True
        assert str(after.get("last_utc") or "") >= "2026-09-17"


def _tf_book(n: int, start: datetime, step_hours: float) -> list[StampedBar]:
    out = []
    for i in range(n):
        utc = start + timedelta(hours=step_hours * i)
        out.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=1.0, h=1.1, l=0.9, c=1.0, v=1.0),
                source_path="tmp",
            )
        )
    return out


def test_us30_aliases_admit_when_chair_zip_landed():
    """Chair zip ships US30.cash / US30_cash / US30. Harness admits US30_cash first."""
    repo = Path(__file__).resolve().parents[2]
    multi = repo / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "multi"
    aliases = [
        multi / "US30_cash_M15.csv",
        multi / "US30.cash_M15.csv",
        multi / "US30_M15.csv",
    ]
    present = [p for p in aliases if p.is_file()]
    if not present:
        return
    for path in present:
        admit = admit_challenge_peer_csv(path)
        assert admit["ok"] is True, path.name
        assert str(admit.get("last_utc") or "") >= "2026-09-17"
    assert challenge_tape_present("US30") is True
    assert challenge_tape_present("US30.cash") is True
    assert "US30" in landed_challenge_symbols()
    resolved = resolve_challenge_tf("US30", "M15")
    assert resolved.name in {"US30_cash_M15.csv", "US30.cash_M15.csv", "US30_M15.csv"}
    books = books_for_symbol("US30")
    assert books is not None
    assert books["m15"]
    assert books["d1"] == []


def test_m15_h4_without_d1_is_sufficient():
    as_of = datetime(2026, 9, 17, 11, 5, tzinfo=timezone.utc)
    books = {
        "m15": _tf_book(16, datetime(2026, 9, 17, 7, 0, tzinfo=timezone.utc), 0.25),
        "h4": _tf_book(16, datetime(2026, 9, 16, 1, 0, tzinfo=timezone.utc), 4.0),
        "d1": [],
    }
    state = assemble_gold_state_v0(
        as_of_utc=as_of,
        side="long",
        sleeve="vss_fxcross_london_up_low",
        symbol="GBPUSD",
        origin_organism="f5_challenge",
        books=books,
        spines={"spine_id": None, "sources": [], "events": [], "n_files": 0},
        geometry={"entry": 1.34, "stop": 1.338, "stop_dist": 0.002},
        cost={"spread_r_of_stop": 0.05},
        sleeve_features={"tag": "vss_fxcross_london_up_low"},
    )
    assert state["completeness"]["timeframes_m15_h4"] is True
    assert state["completeness"]["timeframes_m15_h4_d1"] is False
    assert "timeframes.d1" in state["completeness"]["missing_fields"]
    assert "timeframes.m15" not in state["completeness"]["missing_fields"]
    assert state["completeness"]["state_sufficient_for_live"] is True
