from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research_infra import p1_upstream_m1_provenance_verifier as subject


UTC = timezone.utc


def _rows(times: list[datetime]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for number, timestamp in enumerate(times):
        price = 100.0 + number
        output.append({
            "time": timestamp.isoformat(), "time_utc": timestamp.isoformat(),
            "symbol": "XAUUSD", "open": price, "high": price + 2.0,
            "low": price - 1.0, "close": price + 1.0, "volume": 1.0,
        })
    return output


def _bound_bar(
    timestamp: datetime,
    *,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
) -> dict[str, object]:
    return {
        "time": timestamp.isoformat(), "time_utc": timestamp.isoformat(),
        "symbol": "XAUUSD", "open": open_, "high": high,
        "low": low, "close": close, "volume": volume,
    }


def test_partial_bucket_and_session_gap_known_answer() -> None:
    first = datetime(2026, 1, 2, 0, 10, tzinfo=UTC)
    second = datetime(2026, 1, 2, 1, 0, tzinfo=UTC)
    rows = _rows(
        [first + timedelta(minutes=offset) for offset in range(5)]
        + [second + timedelta(minutes=offset) for offset in range(15)]
    )
    derived = subject.aggregate_m1_rows(rows, symbol="XAUUSD")

    assert list(derived) == [
        datetime(2026, 1, 2, 0, 0, tzinfo=UTC),
        datetime(2026, 1, 2, 1, 0, tzinfo=UTC),
    ]
    assert derived[datetime(2026, 1, 2, 0, 0, tzinfo=UTC)]["open"] == 100.0
    assert derived[datetime(2026, 1, 2, 0, 0, tzinfo=UTC)]["close"] == 105.0
    assert derived[datetime(2026, 1, 2, 1, 0, tzinfo=UTC)]["volume"] == 15.0


def test_sparse_minute_inside_m15_bucket_matches_independent_m15() -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    derived = subject.aggregate_m1_rows(
        _rows([start, start + timedelta(minutes=1), start + timedelta(minutes=3)]),
        symbol="XAUUSD",
    )
    bound = {
        start: _bound_bar(
            start, open_=100.0, high=104.0, low=99.0, close=103.0, volume=3.0,
        )
    }

    subject.verify_m1_m15_equivalence(derived, bound, source_label="fixture:XAUUSD")


def test_sparse_minute_across_adjacent_m15_buckets_matches_independent_m15() -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    second = start + timedelta(minutes=15)
    derived = subject.aggregate_m1_rows(
        _rows([
            start + timedelta(minutes=14),
            start + timedelta(minutes=16),
            start + timedelta(minutes=17),
        ]),
        symbol="XAUUSD",
    )
    bound = {
        start: _bound_bar(
            start, open_=100.0, high=102.0, low=99.0, close=101.0, volume=1.0,
        ),
        second: _bound_bar(
            second, open_=101.0, high=104.0, low=100.0, close=103.0, volume=2.0,
        ),
    }

    subject.verify_m1_m15_equivalence(derived, bound, source_label="fixture:XAUUSD")
    assert derived[second]["open"] == 101.0


def test_deleting_positive_volume_m1_row_fails_bound_m15() -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    rows = _rows([start + timedelta(minutes=offset) for offset in range(3)])
    bound = subject.aggregate_m1_rows(rows, symbol="XAUUSD")
    derived = subject.aggregate_m1_rows([rows[0], rows[2]], symbol="XAUUSD")

    with pytest.raises(subject.M1ProvenanceError, match="m1_m15_ohlcv_mismatch"):
        subject.verify_m1_m15_equivalence(derived, bound, source_label="fixture:XAUUSD")


@pytest.mark.parametrize(("field", "value"), [("high", 999.0), ("volume", 7.0)])
def test_mutated_m1_price_or_volume_fails_bound_m15(field: str, value: float) -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    rows = _rows([start + timedelta(minutes=offset) for offset in range(3)])
    bound = subject.aggregate_m1_rows(rows, symbol="XAUUSD")
    mutated = deepcopy(rows)
    mutated[1][field] = value
    derived = subject.aggregate_m1_rows(mutated, symbol="XAUUSD")

    with pytest.raises(subject.M1ProvenanceError, match="m1_m15_ohlcv_mismatch"):
        subject.verify_m1_m15_equivalence(derived, bound, source_label="fixture:XAUUSD")


@pytest.mark.parametrize("field", ["open", "high", "low", "close", "volume"])
def test_mutated_bound_m15_ohlcv_is_refused(field: str) -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    rows = _rows([start + timedelta(minutes=offset) for offset in range(3)])
    derived = subject.aggregate_m1_rows(rows, symbol="XAUUSD")
    bound = deepcopy(derived)
    bound[start][field] = float(bound[start][field]) + 1.0

    with pytest.raises(subject.M1ProvenanceError, match="m1_m15_ohlcv_mismatch"):
        subject.verify_m1_m15_equivalence(derived, bound, source_label="fixture:XAUUSD")


@pytest.mark.parametrize(
    "drifted_volume",
    [1, True],
    ids=["int-versus-float", "bool-versus-number"],
)
def test_canonical_numeric_type_drift_is_refused(drifted_volume: object) -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    derived = subject.aggregate_m1_rows(_rows([start]), symbol="XAUUSD")
    bound = deepcopy(derived)
    bound[start]["volume"] = drifted_volume

    with pytest.raises(subject.M1ProvenanceError, match="m1_m15_ohlcv_mismatch"):
        subject.verify_m1_m15_equivalence(derived, bound, source_label="fixture:XAUUSD")


def test_missing_interior_whole_m15_bucket_fails_bound_domain() -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    rows = _rows([
        start,
        start + timedelta(minutes=15),
        start + timedelta(minutes=30),
    ])
    bound = subject.aggregate_m1_rows(rows, symbol="XAUUSD")
    derived = subject.aggregate_m1_rows([rows[0], rows[2]], symbol="XAUUSD")
    packet_rows = {
        bucket: row
        for bucket, row in bound.items()
        if min(derived) <= bucket <= max(derived)
    }

    with pytest.raises(subject.M1ProvenanceError, match="m1_m15_bucket_domain_mismatch"):
        subject.verify_m1_m15_equivalence(derived, packet_rows, source_label="fixture:XAUUSD")


@pytest.mark.parametrize(
    "offsets",
    [
        [0, 1, 1],
        [0, 2, 1],
    ],
    ids=["duplicate", "reversed"],
)
def test_duplicate_or_reversed_m1_timestamp_is_refused(offsets: list[int]) -> None:
    start = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    rows = _rows([start + timedelta(minutes=offset) for offset in offsets])

    with pytest.raises(subject.M1ProvenanceError, match="m1_time_order_invalid"):
        subject.aggregate_m1_rows(rows, symbol="XAUUSD")


def test_m1_file_binding_rejects_path_and_hash_drift(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text("bound", encoding="utf-8")

    with pytest.raises(subject.M1ProvenanceError, match="path_not_relative_contained"):
        subject._relative("../source.csv", label="fixture")
    with pytest.raises(subject.M1ProvenanceError, match="sha256_mismatch"):
        subject._file(tmp_path, "source.csv", digest="0" * 64)
