from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from src.research_infra.completed_bar_witness import (
    COMPLETION_SEMANTICS,
    ROW_WITNESS_FIELD,
    WITNESS_TYPE,
    CompletedBarWitnessError,
    installed_observed_successor_witness,
    observed_successor_closed_bar_rows_until,
)


def _row(stamp: str, close: float) -> dict[str, object]:
    return {"time_utc": stamp, "close": close}


def test_successor_open_is_conservative_and_successor_values_are_not_exposed():
    rows = (
        _row("2025-10-27T00:00:00+00:00", 10.0),
        _row("2025-10-27T01:00:00+00:00", 999.0),
        _row("2025-10-27T01:15:00+00:00", 20.0),
    )

    assert observed_successor_closed_bar_rows_until(
        rows,
        timeframe="M15",
        asof=datetime(2025, 10, 27, 0, 15, tzinfo=timezone.utc),
    ) == ()
    selected = observed_successor_closed_bar_rows_until(
        rows,
        timeframe="M15",
        asof=datetime(2025, 10, 27, 1, 0, tzinfo=timezone.utc),
    )
    assert selected == ({"time_utc": rows[0]["time_utc"], "close": 10.0},)
    assert 999.0 not in {row["close"] for row in selected}


def test_terminal_row_without_successor_stays_unavailable_and_max_rows_applies():
    rows = tuple(
        _row(f"2025-10-27T00:{minute:02d}:00+00:00", float(minute))
        for minute in (0, 15, 30, 45)
    )
    selected = observed_successor_closed_bar_rows_until(
        rows,
        timeframe="M15",
        asof=datetime(2025, 10, 27, 1, 0, tzinfo=timezone.utc),
        max_rows=2,
    )
    assert [row["close"] for row in selected] == [15.0, 30.0]


def test_attached_witness_binds_only_adjacent_ordinals_and_aware_opens():
    rows = (
        _row("2025-10-27T00:00:00+00:00", 10.0),
        _row("2025-10-27T00:15:00+00:00", 999.0),
    )

    selected = observed_successor_closed_bar_rows_until(
        rows,
        timeframe="M15",
        asof=datetime(2025, 10, 27, 0, 15, tzinfo=timezone.utc),
        attach_witness=True,
    )

    assert len(selected) == 1
    witness = selected[0][ROW_WITNESS_FIELD]
    assert witness == {
        "witness_type": WITNESS_TYPE,
        "completion_semantics": COMPLETION_SEMANTICS,
        "timeframe": "M15",
        "predecessor_source_ordinal": 0,
        "successor_source_ordinal": 1,
        "predecessor_open_utc": "2025-10-27T00:00:00+00:00",
        "successor_open_utc": "2025-10-27T00:15:00+00:00",
        "successor_market_values_consumed": False,
    }
    assert selected[0]["close"] == 10.0
    assert 999.0 not in selected[0].values()


@pytest.mark.parametrize(
    "rows, reason",
    [
        (
            (
                _row("2025-10-27T00:00:00", 1.0),
                _row("2025-10-27T00:15:00+00:00", 2.0),
            ),
            "row_0_time_utc_naive",
        ),
        (
            (
                _row("2025-10-27T00:15:00+00:00", 1.0),
                _row("2025-10-27T00:15:00+00:00", 2.0),
            ),
            "row_stream_not_strictly_increasing:0",
        ),
    ],
)
def test_invalid_chronology_refuses(rows, reason):
    with pytest.raises(CompletedBarWitnessError, match=reason):
        observed_successor_closed_bar_rows_until(
            rows,
            timeframe="M15",
            asof=datetime(2025, 10, 27, 1, 0, tzinfo=timezone.utc),
        )


def test_context_manager_accepts_only_registered_stream_and_restores_original():
    rows = (
        _row("2025-10-27T00:00:00+00:00", 1.0),
        _row("2025-10-27T00:15:00+00:00", 2.0),
    )
    original = lambda *args, **kwargs: ("legacy",)
    module = SimpleNamespace(closed_bar_rows_until=original)
    source = SimpleNamespace(rows=rows)
    sources = {"XAUUSD": {"M15": source}}

    with installed_observed_successor_witness(module, sources) as audit:
        selected = module.closed_bar_rows_until(
            rows,
            timeframe="M15",
            asof=datetime(2025, 10, 27, 0, 15, tzinfo=timezone.utc),
        )
        assert selected == (dict(rows[0]),)
        assert audit["witness_type"] == WITNESS_TYPE
        assert audit["completion_semantics"] == COMPLETION_SEMANTICS
        assert audit["calls"] == 1
        with pytest.raises(
            CompletedBarWitnessError, match="unregistered_source_stream"
        ):
            module.closed_bar_rows_until(
                tuple(dict(row) for row in rows),
                timeframe="M15",
                asof=datetime(2025, 10, 27, 0, 15, tzinfo=timezone.utc),
            )

    assert module.closed_bar_rows_until is original
