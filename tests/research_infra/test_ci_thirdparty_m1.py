from __future__ import annotations

import csv
import datetime as dt
import gzip
import importlib.util
import json
import lzma
import struct
import sys
from pathlib import Path

import pytest

from src.research_infra.replay_policy.generation import CsvBarSource
from src.utils.research_timebase import TRUE_UTC, write_sidecar


REPO = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/ci_thirdparty_m1.py"
)


def _load_script(name: str):
    path = SCRIPT.with_name(name)
    spec = importlib.util.spec_from_file_location(f"test_{name.replace('.', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def ci_module():
    return _load_script("ci_thirdparty_m1.py")


def _payload(*rows: tuple[int, int, int, int, int, float]) -> bytes:
    raw = b"".join(struct.pack(">5if", *row) for row in rows)
    return lzma.compress(raw)


def _tick_payload(*rows: tuple[int, int, int, float, float]) -> bytes:
    raw = b"".join(struct.pack(">3i2f", *row) for row in rows)
    return lzma.compress(raw)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "wt", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=(
                "time", "open", "high", "low", "close", "tick_volume", "spread",
                "real_volume",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)
    write_sidecar(path, basis=TRUE_UTC, rule=None, evidence="synthetic unit fixture")


def _row(stamp: str, price: float = 100.0, volume: float = 1.0) -> dict:
    return {
        "time": stamp,
        "open": price,
        "high": price + 1,
        "low": price - 1,
        "close": price + 0.5,
        "tick_volume": volume,
        "spread": 0,
        "real_volume": 0,
    }


def test_decoder_uses_utc_day_and_open_close_low_high_wire_order(ci_module):
    inst = ci_module.INSTRUMENTS[0]
    rows = ci_module.decode_bi5(
        _payload(
            (0, 100_000, 100_250, 99_500, 100_500, 1.5),
            (60, 100_250, 100_100, 99_900, 100_600, 0.0),
        ),
        day=dt.date(2024, 1, 2),
        inst=inst,
    )
    assert rows == [
        {
            "time": "2024-01-02T00:00:00+00:00",
            "open": 100.0,
            "high": 100.5,
            "low": 99.5,
            "close": 100.25,
            "tick_volume": 1.5,
            "spread": 0,
            "real_volume": 0,
        },
        {
            "time": "2024-01-02T00:01:00+00:00",
            "open": 100.25,
            "high": 100.6,
            "low": 99.9,
            "close": 100.1,
            "tick_volume": 0.0,
            "spread": 0,
            "real_volume": 0,
        },
    ]
    assert ci_module._url(inst, dt.date(2025, 12, 1)).endswith(
        "/2025/11/01/BID_candles_min_1.bi5"
    )


def test_decoder_refuses_bad_minute_grid_and_ohlc(ci_module):
    inst = ci_module.INSTRUMENTS[0]
    with pytest.raises(ValueError, match="invalid minute offset"):
        ci_module.decode_bi5(
            _payload((1, 100_000, 100_000, 99_000, 101_000, 1.0)),
            day=dt.date(2024, 1, 2),
            inst=inst,
        )
    with pytest.raises(ValueError, match="invalid OHLC ordering"):
        ci_module.decode_bi5(
            _payload((0, 100_000, 100_000, 101_000, 102_000, 1.0)),
            day=dt.date(2024, 1, 2),
            inst=inst,
        )


def test_convert_writes_sanctioned_true_utc_sidecars_accepted_by_loader(
    ci_module, tmp_path, monkeypatch
):
    root = tmp_path / "estate"
    monkeypatch.setattr(ci_module, "SOURCE_RECEIPT", tmp_path / "source_receipt.json")
    (root / "fetch_summary.json").parent.mkdir(parents=True)
    (root / "fetch_summary.json").write_text(json.dumps({"fixture": True}))
    for inst in ci_module.INSTRUMENTS:
        path = ci_module._raw_path(inst, dt.date(2024, 1, 2), root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_payload((0, 100_000, 100_100, 99_900, 100_200, 1.0)))

    receipt = ci_module.convert(root=root)
    hashes_before = {
        inst.canonical: receipt["converted"][inst.canonical]["sha256"]
        for inst in ci_module.INSTRUMENTS
    }
    receipt_again = ci_module.convert(root=root)
    assert {
        inst.canonical: receipt_again["converted"][inst.canonical]["sha256"]
        for inst in ci_module.INSTRUMENTS
    } == hashes_before
    for inst in ci_module.INSTRUMENTS:
        path = ci_module._converted_path(inst, root)
        sidecar = json.loads(Path(str(path) + ".timebase.json").read_text())
        assert sidecar["time_column_basis"] == "true_utc"
        assert sidecar["not_broker_bars"] is True
        assert "THIRD-PARTY, provenance-declared:" in sidecar["broker_clock_evidence"]
        assert "NOT an MT5 tick count" in sidecar["source_volume_semantics"]
        loaded = CsvBarSource({(inst.broker_symbol, 1): path})._load((inst.broker_symbol, 1))
        assert len(loaded) == 1
        assert loaded[0]["time"] == "2024-01-02T00:00:00+00:00"
        assert receipt["converted"][inst.canonical]["rows"] == 1


def test_fetch_refuses_more_than_two_workers_before_network(ci_module, tmp_path):
    with pytest.raises(SystemExit, match="must be 1 or 2"):
        ci_module.fetch(
            start=dt.date(2024, 1, 1),
            end=dt.date(2024, 1, 1),
            workers=3,
            root=tmp_path,
        )


def test_raw_tick_repair_counts_provider_ticks_by_utc_minute(tmp_path):
    module = _load_script("ci_tick_count_repair.py")
    inst = module.base.INSTRUMENTS[0]
    day = dt.date(2026, 5, 18)
    first = module.tick_path(inst, day, 8, tmp_path)
    first.parent.mkdir(parents=True)
    first.write_bytes(
        _tick_payload(
            (0, 100_100, 100_000, 1.0, 2.0),
            (59_999, 100_200, 100_100, 1.5, 2.5),
            (60_000, 100_300, 100_200, 1.0, 2.0),
        )
    )
    counts, stats = module._aggregate_counts(inst, start=day, end=day, root=tmp_path)
    assert counts == {
        "2026-05-18T08:00:00+00:00": 2,
        "2026-05-18T08:01:00+00:00": 1,
    }
    assert stats == {"n_payloads_present": 1, "n_ticks": 3, "n_active_minutes": 2}
    assert module.tick_url(inst, day, 8).endswith("/2026/04/18/08h_ticks.bi5")


def test_raw_tick_repair_refuses_bad_ticks_and_more_than_two_workers(tmp_path):
    module = _load_script("ci_tick_count_repair.py")
    with pytest.raises(ValueError, match="invalid bid/ask"):
        module.decode_ticks(_tick_payload((0, 100_000, 100_100, 1.0, 1.0)))
    with pytest.raises(SystemExit, match="must be 1 or 2"):
        module.fetch_ticks(workers=3, root=tmp_path)


def test_overlap_comparator_publishes_bps_and_structural_rule(ci_module, tmp_path):
    inst = ci_module.INSTRUMENTS[0]
    start = dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc)
    third_rows = []
    broker_rows = []
    for n in range(20_000):
        stamp = (start + dt.timedelta(minutes=n)).isoformat()
        third_rows.append(_row(stamp, 100.0))
        broker_rows.append(_row(stamp, 100.0))
    third = tmp_path / "third.csv.gz"
    broker = tmp_path / "broker.csv"
    _write_csv(third, third_rows)
    _write_csv(broker, broker_rows)
    result = ci_module._overlap_for(inst, third, broker)
    assert result["n_common_minute_stamps"] == 20_000
    assert result["ohlc_absolute_divergence_bps"]["close"]["p95"] == 0.0
    assert result["structurally_comparable"] is True
    assert result["dst"]["spring_2026_transition_observable"] is False


def test_splice_uses_broker_at_join_and_removes_march_before_gate(
    ci_module, tmp_path, monkeypatch
):
    root = tmp_path / "estate"
    broker_root = tmp_path / "broker"
    overlap = tmp_path / "overlap.json"
    splice_receipt = tmp_path / "splice.json"
    overlap.write_text(json.dumps({"gate_permitted": True}))
    monkeypatch.setattr(ci_module, "BROKER_ROOT", broker_root)
    monkeypatch.setattr(ci_module, "OVERLAP_RECEIPT", overlap)
    monkeypatch.setattr(ci_module, "SPLICE_RECEIPT", splice_receipt)

    third_rows = [
        _row("2026-02-28T23:59:00+00:00", 99.0),
        _row("2026-03-01T00:00:00+00:00", 98.0),
        _row("2026-03-31T23:59:00+00:00", 97.0),
        _row("2026-04-27T00:00:00+00:00", 96.0),
    ]
    broker_rows = [
        _row("2026-04-27T00:00:00+00:00", 100.0),
        _row("2026-04-27T00:01:00+00:00", 101.0),
    ]
    for inst in ci_module.INSTRUMENTS:
        _write_csv(ci_module._converted_path(inst, root), third_rows)
        _write_csv(broker_root / f"{inst.canonical}_M1.csv", broker_rows)

    receipt = ci_module.splice(root=root)
    for inst in ci_module.INSTRUMENTS:
        meta = receipt["gate_view"][inst.canonical]
        assert meta["n_march_rows_removed_before_gate"] == 2
        assert meta["n_thirdparty_rows_before_join"] == 1
        assert meta["n_broker_rows_from_join"] == 2
        rows = CsvBarSource(
            {(inst.broker_symbol, 1): ci_module._gate_path(inst, root)}
        )._load((inst.broker_symbol, 1))
        assert [r["time"] for r in rows] == [
            "2026-02-28T23:59:00+00:00",
            "2026-04-27T00:00:00+00:00",
            "2026-04-27T00:01:00+00:00",
        ]


def test_generation_refuses_label_horizon_before_replay_when_it_can_touch_march():
    module = _load_script("ci_vp_generate.py")
    utc = dt.timezone.utc
    assert module._label_horizon_touches_protected(
        dt.datetime(2026, 2, 20, tzinfo=utc),
        dt.datetime(2026, 3, 2, tzinfo=utc),
    )
    assert not module._label_horizon_touches_protected(
        dt.datetime(2026, 2, 1, tzinfo=utc),
        dt.datetime(2026, 2, 28, 23, 59, tzinfo=utc),
    )
    assert not module._label_horizon_touches_protected(
        dt.datetime(2026, 4, 1, tzinfo=utc),
        dt.datetime(2026, 4, 10, tzinfo=utc),
    )


@pytest.mark.parametrize(
    ("admits", "not_evaluable", "live_admits", "expected"),
    [
        (["low", "mid"], [], [], "REVIVAL_CANDIDATE"),
        ([], ["mid", "high"], ["low", "mid"], "NOT_EVALUABLE"),
        ([], [], ["low", "high"], "CONDITIONAL"),
        (["mid"], [], ["mid"], "STAYS_DEAD"),
    ],
)
def test_gate_verdict_uses_two_of_three_real_bands(
    admits, not_evaluable, live_admits, expected
):
    module = _load_script("ci_vp_gate.py")
    assert module._session_verdict(
        admits=admits,
        not_evaluable=not_evaluable,
        live_admits=live_admits,
    ) == expected
