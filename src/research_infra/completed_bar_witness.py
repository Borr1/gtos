"""Conservative completed-bar selection for bounded research comparisons.

The production timewarp currently estimates a bar close as ``open + timeframe``.
This opt-in adapter instead exposes a row only after the immediate next row in
the same resolved source stream has opened.  The successor contributes its
timestamp only; none of its market values are exposed to the generator.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterable, Iterator, Mapping, MutableMapping


WITNESS_TYPE = "observed_successor_open_utc_upper_bound"
COMPLETION_SEMANTICS = "next_bound_open_not_exact_close"
EVIDENCE_CLASS = "engineering_successor_witness_not_loader_receipt"
ROW_WITNESS_FIELD = "wave21_completed_bar_witness"
WITNESS_FIELDS = frozenset(
    {
        "witness_type",
        "completion_semantics",
        "timeframe",
        "predecessor_source_ordinal",
        "successor_source_ordinal",
        "predecessor_open_utc",
        "successor_open_utc",
        "successor_market_values_consumed",
    }
)


class CompletedBarWitnessError(ValueError):
    """Raised when a source stream cannot support the conservative witness."""


def _aware_utc(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise CompletedBarWitnessError(f"{field}_invalid") from exc
    else:
        raise CompletedBarWitnessError(f"{field}_missing_or_unsupported")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CompletedBarWitnessError(f"{field}_naive")
    return parsed.astimezone(timezone.utc)


def _row_open_utc(row: Mapping[str, Any], *, ordinal: int) -> datetime:
    observed: list[tuple[str, datetime]] = []
    for key in ("time_utc", "time"):
        if row.get(key) is not None:
            observed.append(
                (key, _aware_utc(row[key], field=f"row_{ordinal}_{key}"))
            )
    if not observed:
        raise CompletedBarWitnessError(f"row_{ordinal}_open_missing")
    if any(value != observed[0][1] for _key, value in observed[1:]):
        raise CompletedBarWitnessError(f"row_{ordinal}_open_alias_conflict")
    return observed[0][1]


def observed_successor_closed_bar_rows_until(
    rows: Iterable[Mapping[str, Any]],
    *,
    timeframe: str,
    asof: datetime,
    max_rows: int | None = None,
    audit: MutableMapping[str, Any] | None = None,
    attach_witness: bool = False,
) -> tuple[dict[str, Any], ...]:
    """Return prior rows whose immediate successor opened by ``asof``.

    ``timeframe`` is retained in the drop-in call contract but is deliberately
    not used to infer a duration.  The final row has no successor and therefore
    remains unavailable.
    """

    if not isinstance(timeframe, str) or not timeframe.strip():
        raise CompletedBarWitnessError("timeframe_missing")
    cutoff = _aware_utc(asof, field="asof")
    materialized = tuple(rows)
    if not materialized:
        return ()
    if any(not isinstance(row, Mapping) for row in materialized):
        raise CompletedBarWitnessError("row_not_mapping")

    opens = tuple(
        _row_open_utc(row, ordinal=ordinal)
        for ordinal, row in enumerate(materialized)
    )
    for ordinal, (prior_open, successor_open) in enumerate(
        zip(opens, opens[1:])
    ):
        if not prior_open < successor_open:
            raise CompletedBarWitnessError(
                f"row_stream_not_strictly_increasing:{ordinal}"
            )

    end = 0
    for ordinal in range(len(materialized) - 1):
        if opens[ordinal + 1] <= cutoff:
            end = ordinal + 1
        else:
            break
    start = 0
    if max_rows is not None:
        if isinstance(max_rows, bool) or not isinstance(max_rows, int):
            raise CompletedBarWitnessError("max_rows_not_integer")
        if max_rows > 0:
            start = max(0, end - max_rows)

    selected_rows: list[dict[str, Any]] = []
    for ordinal in range(start, end):
        row = dict(materialized[ordinal])
        if attach_witness:
            row[ROW_WITNESS_FIELD] = {
                "witness_type": WITNESS_TYPE,
                "completion_semantics": COMPLETION_SEMANTICS,
                "timeframe": timeframe.strip().upper(),
                "predecessor_source_ordinal": ordinal,
                "successor_source_ordinal": ordinal + 1,
                "predecessor_open_utc": opens[ordinal].isoformat(),
                "successor_open_utc": opens[ordinal + 1].isoformat(),
                "successor_market_values_consumed": False,
            }
        selected_rows.append(row)
    selected = tuple(selected_rows)
    if audit is not None:
        audit["calls"] = int(audit.get("calls") or 0) + 1
        audit["input_rows_observed"] = int(
            audit.get("input_rows_observed") or 0
        ) + len(materialized)
        audit["rows_returned"] = int(audit.get("rows_returned") or 0) + len(
            selected
        )
        audit["terminal_rows_without_successor_excluded"] = int(
            audit.get("terminal_rows_without_successor_excluded") or 0
        ) + 1
    return selected


def validate_completed_bar_witness(
    witness: Any,
    *,
    timeframe: str,
    row_open: Any,
    asof: Any,
) -> dict[str, Any]:
    """Validate one attached successor-open witness without reading successor values."""

    tf_name = str(timeframe).strip().upper()
    if not isinstance(witness, Mapping) or set(witness) != WITNESS_FIELDS:
        raise CompletedBarWitnessError("completion_witness_fields_invalid")
    prior = _aware_utc(row_open, field=f"{tf_name}_row_open")
    predecessor = _aware_utc(
        witness.get("predecessor_open_utc"), field=f"{tf_name}_predecessor_open"
    )
    successor = _aware_utc(
        witness.get("successor_open_utc"), field=f"{tf_name}_successor_open"
    )
    predecessor_ordinal = witness.get("predecessor_source_ordinal")
    successor_ordinal = witness.get("successor_source_ordinal")
    if (
        witness.get("witness_type") != WITNESS_TYPE
        or witness.get("completion_semantics") != COMPLETION_SEMANTICS
        or str(witness.get("timeframe") or "").upper() != tf_name
        or witness.get("successor_market_values_consumed") is not False
        or predecessor != prior
        or isinstance(predecessor_ordinal, bool)
        or not isinstance(predecessor_ordinal, int)
        or isinstance(successor_ordinal, bool)
        or not isinstance(successor_ordinal, int)
        or successor_ordinal != predecessor_ordinal + 1
        or not prior < successor <= _aware_utc(asof, field="asof")
    ):
        raise CompletedBarWitnessError("completion_witness_contract_invalid")
    return dict(witness)


@contextmanager
def installed_observed_successor_witness(
    timewarp_module: Any,
    sources: Mapping[str, Mapping[str, Any]],
) -> Iterator[dict[str, Any]]:
    """Temporarily install the witness for the exact resolved source objects."""

    original = timewarp_module.closed_bar_rows_until
    streams: dict[tuple[int, str], str] = {}
    registered_source_streams = 0
    for symbol, by_timeframe in sources.items():
        for timeframe, source in by_timeframe.items():
            rows = source.rows
            tf_name = str(timeframe).upper()
            key = (id(rows), tf_name)
            prior_symbol = streams.setdefault(key, str(symbol))
            if prior_symbol != str(symbol) and rows:
                raise CompletedBarWitnessError("source_rows_identity_reused")
            registered_source_streams += 1

    audit: dict[str, Any] = {
        "witness_type": WITNESS_TYPE,
        "completion_semantics": COMPLETION_SEMANTICS,
        "evidence_class": EVIDENCE_CLASS,
        "registered_source_streams": registered_source_streams,
        "calls": 0,
        "input_rows_observed": 0,
        "rows_returned": 0,
        "terminal_rows_without_successor_excluded": 0,
    }

    def replacement(
        rows: Iterable[Mapping[str, Any]],
        *,
        timeframe: str,
        asof: datetime,
        max_rows: int | None = None,
    ) -> tuple[dict[str, Any], ...]:
        tf_name = str(timeframe).upper()
        if (id(rows), tf_name) not in streams:
            raise CompletedBarWitnessError("unregistered_source_stream")
        return observed_successor_closed_bar_rows_until(
            rows,
            timeframe=timeframe,
            asof=asof,
            max_rows=max_rows,
            audit=audit,
        )

    timewarp_module.closed_bar_rows_until = replacement
    try:
        yield audit
    finally:
        timewarp_module.closed_bar_rows_until = original


__all__ = [
    "COMPLETION_SEMANTICS",
    "EVIDENCE_CLASS",
    "ROW_WITNESS_FIELD",
    "WITNESS_TYPE",
    "WITNESS_FIELDS",
    "CompletedBarWitnessError",
    "installed_observed_successor_witness",
    "observed_successor_closed_bar_rows_until",
    "validate_completed_bar_witness",
]
