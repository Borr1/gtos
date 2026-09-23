"""Wave 21 geometry-bound outcome calibration model (two-stage Jeffreys).

This module is the result-bearing successor to the falsified action-support
score (``PROBABILITY_EV_TRUTH_V1.json``: strict AUC 0.496; probability and EV
authority stripped fail-closed under truth mode).  It implements the exact
estimator preregistered in ``OUTCOME_AUTHORITY_PREREGISTRATION_V1.json``:

* Stage 1 (fill): Beta(1/2, 1/2) Jeffreys fraction over resolved LIMIT
  attempts; MARKET fill is exactly 1 and NO_FILL exactly 0 by contract.
* Stage 2 (terminal given fill): Dirichlet(1/2, 1/2, 1/2) Jeffreys over
  {TARGET, STOP, TIME_STOP} resolved fills.
* Hierarchy: ``proposed_order_type`` -> ``x origin_family`` ->
  ``x utc_session``; deepest cell meeting the fixed support rule wins and the
  level is never chosen by realized performance.
* Support gates: 100 resolved attempts (LIMIT fill), 30 resolved fills
  (terminal).  Below support is ``OUT_OF_SUPPORT`` with the exact shortfall,
  never a default probability.

The licensed endpoint is ``P(target_before_stop | filled, terminal resolved
as target-or-stop)`` -- the Dirichlet posterior restricted to {TARGET, STOP},
i.e. Beta(n_target + 1/2, n_stop + 1/2).  NO_FILL is a separate execution
mass, TIME_STOP a separate terminal mass, and censored rows are coverage
masses; none of them is ever folded into a loss.

Every probability is stored as Jeffreys numerator/denominator integers;
decimal aliases are derived and never primary authority.  The model artifact
and every per-candidate packet are canonically hash-sealed, and a packet is
bound to the candidate's FINAL post-router target/stop geometry contract hash
so any later geometry change makes it stale.

What an accepted packet licenses: honest per-cell outcome frequencies as
probability inputs.  What it does not license: EV-based admission, selection,
sizing, or any live authority -- those require a separate preregistered read.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

MODEL_SCHEMA = "gtos.wave21.geometry_bound_outcome_calibration_model.v1"
PACKET_SCHEMA = "gtos.wave21.geometry_bound_outcome_calibration_packet.v1"
SUPPORTED_MODEL_VERSION = "GEOMETRY_BOUND_OUTCOME_JEFFREYS_V1"
CONDITIONAL_ENDPOINT = (
    "P(target_before_stop | filled, terminal_resolved_as_target_or_stop)"
)
PRIMARY_EVIDENCE_CLASS = "ALL24_M1_MODELLED_LIFECYCLE_NOT_BROKER_FILL"
PREREGISTRATION_V1_PAYLOAD_SHA256 = (
    "2db7e5c94348a98b598a203aace7006545a03a77fcb081aeb1239a8ec0c65a95"
)
HIERARCHY_LEVELS = (
    "proposed_order_type",
    "proposed_order_type_x_origin_family",
    "proposed_order_type_x_origin_family_x_utc_session",
)
MARKET_EXACT_LEVEL = "MARKET_EXACT"
TERMINAL_STATES = ("TARGET", "STOP", "TIME_STOP")
RESOLVED_STATUS_TO_STATE = {
    "RESOLVED_NO_FILL": "NO_FILL",
    "RESOLVED_FILLED_TARGET": "TARGET",
    "RESOLVED_FILLED_STOP": "STOP",
    "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
}
LIMIT_MIN_RESOLVED_ATTEMPTS = 100
TERMINAL_MIN_RESOLVED_FILLS = 30
LABEL_AVAILABILITY_SKEW_HOURS = 3.0

EVALUATED_STATUS = "EVALUATED_OUTCOME_BASELINE"
OUT_OF_SUPPORT_STATUS = "OUT_OF_SUPPORT"
NOT_EVALUABLE_ORDER_POLICY_STATUS = "NOT_EVALUABLE_ORDER_POLICY"
NOT_EVALUABLE_GEOMETRY_STATUS = "NOT_EVALUABLE_GEOMETRY"
FILL_MARKET_EXACT_STATUS = "EVALUATED_MARKET_EXACT"

PACKET_REASON_PREFIX = "geometry_bound_outcome_calibration"
REASON_PACKET_HASH_INVALID = f"{PACKET_REASON_PREFIX}_packet_hash_invalid"
REASON_MODEL_ARTIFACT_UNVERIFIED = f"{PACKET_REASON_PREFIX}_model_artifact_unverified"
REASON_MODEL_ARTIFACT_SHA_MISMATCH = (
    f"{PACKET_REASON_PREFIX}_model_artifact_sha_mismatch"
)
REASON_STALE_GEOMETRY = f"{PACKET_REASON_PREFIX}_stale_after_geometry_change"
REASON_GEOMETRY_HASH_MISSING = f"{PACKET_REASON_PREFIX}_geometry_hash_missing"
REASON_DECISION_ATOMS_INVALID = f"{PACKET_REASON_PREFIX}_decision_atoms_invalid"
REASON_ENDPOINT_CONTRACT_MISMATCH = (
    f"{PACKET_REASON_PREFIX}_endpoint_contract_mismatch"
)
REASON_OUT_OF_SUPPORT = f"{PACKET_REASON_PREFIX}_out_of_support"
REASON_NOT_EVALUABLE_CELL = f"{PACKET_REASON_PREFIX}_cell_not_evaluable"
REASON_SUPPORT_BELOW_MINIMUM = (
    f"{PACKET_REASON_PREFIX}_support_below_preregistered_minimum"
)
REASON_RATIONAL_IDENTITY_MISMATCH = (
    f"{PACKET_REASON_PREFIX}_rational_identity_mismatch"
)
REASON_MODEL_VERSION_UNSUPPORTED = (
    f"{PACKET_REASON_PREFIX}_model_version_unsupported"
)

_UTC = dt.timezone.utc
_DECISION_ACTIONS = frozenset({"LONG", "SHORT"})


def canonical_payload_sha256(payload: Any) -> str:
    """Sha256 of canonical UTF-8 JSON (sorted keys, tight separators, no NaN)."""

    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _utc(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} missing")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValueError(f"{field} must be aware UTC")
    return parsed.astimezone(_UTC)


def _hex_hash(value: Any, field: str) -> str:
    if not (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    ):
        raise ValueError(f"{field} invalid sha256")
    return value


def _state(row: Mapping[str, Any]) -> str | None:
    status = str(row.get("lifecycle_label_status") or "")
    if status in RESOLVED_STATUS_TO_STATE:
        return RESOLVED_STATUS_TO_STATE[status]
    if status.startswith("CENSORED_"):
        return None
    raise ValueError(f"unknown lifecycle status: {status!r}")


def derive_proposed_order_type(
    origin_family: Any, limit_origin_families: Sequence[str]
) -> str:
    return "LIMIT" if str(origin_family or "") in set(limit_origin_families) else "MARKET"


def _cell_key(row: Mapping[str, Any], level: int) -> tuple[str, ...]:
    return (
        str(row["proposed_order_type"]),
        str(row["origin_family"]),
        str(row["utc_session"]),
    )[: level + 1]


def _blank_cell() -> dict[str, int]:
    return {
        "attempts": 0,
        "fills": 0,
        "no_fill": 0,
        "target": 0,
        "stop": 0,
        "time_stop": 0,
    }


def _tables(
    rows: Sequence[Mapping[str, Any]]
) -> dict[tuple[int, tuple[str, ...]], dict[str, int]]:
    tables: dict[tuple[int, tuple[str, ...]], dict[str, int]] = {}
    for row in rows:
        state = _state(row)
        if state is None:
            continue
        for level in range(3):
            cell = tables.setdefault((level, _cell_key(row, level)), _blank_cell())
            cell["attempts"] += 1
            if state == "NO_FILL":
                cell["no_fill"] += 1
            else:
                cell["fills"] += 1
                cell[state.lower()] += 1
    return tables


def _select_cell(
    tables: Mapping[tuple[int, tuple[str, ...]], Mapping[str, int]],
    row: Mapping[str, Any],
    field: str,
    minimum: int,
) -> tuple[int | None, Mapping[str, int] | None]:
    for level in (2, 1, 0):
        cell = tables.get((level, _cell_key(row, level)))
        if cell is not None and cell[field] >= minimum:
            return level, cell
    return None, None


def _fraction(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": int(numerator),
        "denominator": int(denominator),
        "value": numerator / denominator,
    }


def _fill_fractions(cell: Mapping[str, int]) -> tuple[dict[str, Any], dict[str, Any]]:
    denominator = 2 * cell["attempts"] + 2
    return (
        _fraction(2 * cell["fills"] + 1, denominator),
        _fraction(2 * cell["no_fill"] + 1, denominator),
    )


def _terminal_fractions(cell: Mapping[str, int]) -> dict[str, dict[str, Any]]:
    denominator = 2 * cell["fills"] + 3
    return {
        state: _fraction(2 * cell[state.lower()] + 1, denominator)
        for state in TERMINAL_STATES
    }


def _strict_endpoint_fraction(cell: Mapping[str, int]) -> dict[str, Any]:
    return _fraction(
        2 * cell["target"] + 1, 2 * (cell["target"] + cell["stop"]) + 2
    )


def _root_shortfall(
    tables: Mapping[tuple[int, tuple[str, ...]], Mapping[str, int]],
    order_type: str,
) -> dict[str, int]:
    root = tables.get((0, (order_type,)))
    root = root if root is not None else _blank_cell()
    return {
        "root_resolved_attempts": root["attempts"],
        "root_resolved_fills": root["fills"],
        "additional_resolved_limit_attempts_required": (
            max(0, LIMIT_MIN_RESOLVED_ATTEMPTS - root["attempts"])
            if order_type == "LIMIT"
            else 0
        ),
        "additional_resolved_fills_required": max(
            0, TERMINAL_MIN_RESOLVED_FILLS - root["fills"]
        ),
    }


def _validate_preregistration(preregistration: Mapping[str, Any]) -> None:
    payload = dict(preregistration)
    expected = _hex_hash(
        payload.pop("payload_sha256", None), "preregistration.payload_sha256"
    )
    _require(
        canonical_payload_sha256(payload) == expected,
        "preregistration payload_sha256 mismatch",
    )
    _require(
        expected == PREREGISTRATION_V1_PAYLOAD_SHA256
        and preregistration.get("schema")
        == "gtos.wave21.outcome_authority.preregistration.v1",
        "exact frozen OUTCOME_AUTHORITY_PREREGISTRATION_V1 required",
    )


def validate_training_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    allowed_days: Sequence[str],
    limit_origin_families: Sequence[str],
    preregistration: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Normalize and fail-closed validate estate rows for the fitter."""

    lifecycle_values = set(
        preregistration["lifecycle_and_label_contract"]["lifecycle_label_statuses"]
    )
    cost_values = set(preregistration["cost_contract"]["cost_label_status_values"])
    allowed = set(allowed_days)
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for number, source in enumerate(rows, 1):
        _require(isinstance(source, Mapping), f"row {number} is not an object")
        row = dict(source)
        key = str(row.get("candidate_occurrence_key") or "")
        _require(
            bool(key) and key not in seen,
            f"missing/duplicate occurrence at row {number}",
        )
        seen.add(key)
        _require(row.get("row_key") in (None, key), f"row_key mismatch for {key}")
        row["row_key"] = key
        _require(row.get("trading_day") in allowed, f"{key} outside opened estate")
        _require(
            row.get("evidence_class") == PRIMARY_EVIDENCE_CLASS,
            f"{key} not M1 primary evidence",
        )
        order_type = row.get("proposed_order_type")
        _require(order_type in {"MARKET", "LIMIT"}, f"{key} bad order type")
        _require(bool(row.get("origin_family")), f"{key} missing origin_family")
        _require(
            order_type
            == derive_proposed_order_type(
                row.get("origin_family"), limit_origin_families
            ),
            f"{key} order type disagrees with origin-family derivation",
        )
        _require(bool(row.get("utc_session")), f"{key} missing utc_session")
        _hex_hash(
            row.get("candidate_source_safe_fingerprint_sha256"), f"{key}.fingerprint"
        )
        _hex_hash(
            row.get("proposed_order_policy_hash_sha256"), f"{key}.order_policy"
        )
        _hex_hash(row.get("geometry_contract_hash_sha256"), f"{key}.geometry")
        _require(bool(row.get("arm_id")), f"{key} missing arm_id")
        _hex_hash(row.get("source_manifest_hash_sha256"), f"{key}.source_manifest")
        _require(
            row.get("lifecycle_label_status") in lifecycle_values,
            f"{key} bad lifecycle status",
        )
        _require(
            row.get("cost_label_status") in cost_values, f"{key} bad cost status"
        )
        state = _state(row)
        if state == "NO_FILL":
            _require(
                order_type != "MARKET", f"MARKET row {key} cannot resolve as NO_FILL"
            )
            _require(
                row["cost_label_status"] == "NOT_APPLICABLE_NO_FILL",
                f"{key} bad no-fill cost status",
            )
        elif state in TERMINAL_STATES:
            _require(
                row["cost_label_status"] != "NOT_APPLICABLE_NO_FILL",
                f"{key} filled row with no-fill cost status",
            )
            if row["cost_label_status"] == "COMPLETE":
                net = row.get("terminal_net_r")
                _require(
                    isinstance(net, (int, float))
                    and not isinstance(net, bool)
                    and math.isfinite(float(net)),
                    f"{key} COMPLETE cost with non-finite terminal_net_r",
                )
        if state is not None:
            _require(
                row.get("label_span_status") == "measured",
                f"{key} resolved without measured span",
            )
            start = _utc(row.get("label_span_start_utc"), f"{key}.label_span_start_utc")
            end = _utc(row.get("label_span_end_utc"), f"{key}.label_span_end_utc")
            _require(end >= start, f"{key} inverted label span")
            available = _utc(
                row.get("label_available_utc"), f"{key}.label_available_utc"
            )
            _require(
                available >= end, f"{key} label available before its span ends"
            )
        normalized.append(row)
    return normalized


def _brier(pairs: Sequence[tuple[float, int]]) -> float | None:
    if not pairs:
        return None
    return sum(
        (probability - outcome) ** 2 for probability, outcome in pairs
    ) / len(pairs)


def _reliability_deciles(
    pairs: Sequence[tuple[float, int]]
) -> list[dict[str, Any]]:
    bins: list[dict[str, Any]] = []
    for index in range(10):
        lower = index / 10.0
        upper = (index + 1) / 10.0
        bucket = [
            (probability, outcome)
            for probability, outcome in pairs
            if lower <= probability < upper
            or (index == 9 and probability == 1.0)
        ]
        if not bucket:
            continue
        bins.append(
            {
                "bin": f"{lower:.1f}-{upper:.1f}",
                "count": len(bucket),
                "mean_predicted": sum(p for p, _ in bucket) / len(bucket),
                "observed_frequency": sum(y for _, y in bucket) / len(bucket),
            }
        )
    return bins


def _coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    censored: Counter[str] = Counter()
    for row in rows:
        state = _state(row)
        if state is None:
            censored[str(row["lifecycle_label_status"])] += 1
            continue
        counts["resolved_attempts"] += 1
        if state == "NO_FILL":
            counts["no_fill"] += 1
        else:
            counts["resolved_fills"] += 1
            counts[state.lower()] += 1
    return {
        "all_occurrences": len(rows),
        "resolved_attempts": counts["resolved_attempts"],
        "resolved_fills": counts["resolved_fills"],
        "no_fill": counts["no_fill"],
        "target": counts["target"],
        "stop": counts["stop"],
        "time_stop": counts["time_stop"],
        "censored_by_reason": dict(sorted(censored.items())),
    }


def _availability_cutoff(day: str) -> dt.datetime:
    return dt.datetime.combine(
        dt.date.fromisoformat(day), dt.time.min, tzinfo=_UTC
    ) - dt.timedelta(hours=LABEL_AVAILABILITY_SKEW_HOURS)


def _admitted_training_rows(
    prior_rows: Sequence[Mapping[str, Any]], cutoff: dt.datetime
) -> tuple[list[Mapping[str, Any]], dict[str, int]]:
    admitted: list[Mapping[str, Any]] = []
    excluded: Counter[str] = Counter()
    for row in prior_rows:
        if _state(row) is None:
            excluded["lifecycle_censored"] += 1
            continue
        value = row.get("label_available_utc")
        if value in (None, ""):
            excluded["label_available_utc_unknown"] += 1
            continue
        if _utc(value, "label_available_utc") >= cutoff:
            excluded["label_not_strictly_before_effective_test_start"] += 1
            continue
        admitted.append(row)
    return admitted, dict(sorted(excluded.items()))


def _prequential_evaluation(
    rows_by_day: Mapping[str, Sequence[Mapping[str, Any]]],
    days: Sequence[str],
    window_by_day: Mapping[str, str],
) -> dict[str, Any]:
    from src.research_infra.trainer_folds import TrainerFold, audit_fold_leakage

    strict_pairs: list[tuple[float, int]] = []
    strict_base_pairs: list[tuple[float, int]] = []
    fill_pairs: list[tuple[float, int]] = []
    fill_base_pairs: list[tuple[float, int]] = []
    strict_window_pairs: dict[str, list[tuple[float, int]]] = {}
    strict_window_base_pairs: dict[str, list[tuple[float, int]]] = {}
    per_cell: dict[str, dict[str, Any]] = {}
    backoff_counts: Counter[str] = Counter()
    day_reports: list[dict[str, Any]] = []
    folds: list[TrainerFold] = []
    prior_rows: list[Mapping[str, Any]] = []

    for number, day in enumerate(days):
        cutoff = _availability_cutoff(day)
        train, excluded = _admitted_training_rows(prior_rows, cutoff)
        tables = _tables(train)
        strict_train_target = sum(
            1 for row in train if _state(row) == "TARGET"
        )
        strict_train_stop = sum(1 for row in train if _state(row) == "STOP")
        strict_base_probability = (2 * strict_train_target + 1) / (
            2 * (strict_train_target + strict_train_stop) + 2
        )
        limit_train = [
            row for row in train if row["proposed_order_type"] == "LIMIT"
        ]
        limit_train_fills = sum(
            1 for row in limit_train if _state(row) != "NO_FILL"
        )
        fill_base_probability = (2 * limit_train_fills + 1) / (
            2 * len(limit_train) + 2
        )

        day_rows = rows_by_day[day]
        day_strict: list[tuple[float, int]] = []
        day_strict_base: list[tuple[float, int]] = []
        day_fill: list[tuple[float, int]] = []
        day_fill_base: list[tuple[float, int]] = []
        strict_out_of_support = 0
        fill_out_of_support = 0
        strict_rows = 0
        limit_rows = 0
        for row in day_rows:
            state = _state(row)
            if state is None:
                continue
            if state in ("TARGET", "STOP"):
                strict_rows += 1
                level, cell = _select_cell(
                    tables, row, "fills", TERMINAL_MIN_RESOLVED_FILLS
                )
                if cell is None:
                    strict_out_of_support += 1
                else:
                    backoff_counts[f"terminal:{HIERARCHY_LEVELS[level]}"] += 1
                    probability = _strict_endpoint_fraction(cell)["value"]
                    outcome = int(state == "TARGET")
                    day_strict.append((probability, outcome))
                    day_strict_base.append((strict_base_probability, outcome))
                    cell_name = "|".join(_cell_key(row, 2))
                    record = per_cell.setdefault(
                        cell_name,
                        {"scored": 0, "sum_predicted": 0.0, "targets": 0},
                    )
                    record["scored"] += 1
                    record["sum_predicted"] += probability
                    record["targets"] += outcome
            if row["proposed_order_type"] == "LIMIT":
                limit_rows += 1
                level, cell = _select_cell(
                    tables, row, "attempts", LIMIT_MIN_RESOLVED_ATTEMPTS
                )
                if cell is None:
                    fill_out_of_support += 1
                else:
                    backoff_counts[f"fill:{HIERARCHY_LEVELS[level]}"] += 1
                    probability = _fill_fractions(cell)[0]["value"]
                    outcome = int(state != "NO_FILL")
                    day_fill.append((probability, outcome))
                    day_fill_base.append((fill_base_probability, outcome))

        strict_pairs.extend(day_strict)
        strict_base_pairs.extend(day_strict_base)
        fill_pairs.extend(day_fill)
        fill_base_pairs.extend(day_fill_base)
        window = window_by_day[day]
        strict_window_pairs.setdefault(window, []).extend(day_strict)
        strict_window_base_pairs.setdefault(window, []).extend(day_strict_base)
        folds.append(
            TrainerFold(
                fold_id=number,
                test_start=day,
                test_end=day,
                embargo_days=0,
                train_row_keys=tuple(str(row["row_key"]) for row in train),
                test_row_keys=tuple(str(row["row_key"]) for row in day_rows),
                n_purged_overlap=0,
                n_purged_unknown_span=0,
                status="evaluable",
            )
        )
        day_reports.append(
            {
                "trading_day": day,
                "window_id": window,
                "training_rows_admitted": len(train),
                "training_exclusions": excluded,
                "strict_target_or_stop_rows": strict_rows,
                "strict_scored_rows": len(day_strict),
                "strict_out_of_support_rows": strict_out_of_support,
                "strict_brier": _brier(day_strict),
                "strict_base_rate_brier": _brier(day_strict_base),
                "strict_base_rate_probability": strict_base_probability,
                "limit_resolved_rows": limit_rows,
                "limit_fill_scored_rows": len(day_fill),
                "limit_fill_out_of_support_rows": fill_out_of_support,
                "limit_fill_brier": _brier(day_fill),
                "limit_fill_base_rate_brier": _brier(day_fill_base),
            }
        )
        prior_rows.extend(day_rows)

    all_rows = [row for day in days for row in rows_by_day[day]]
    leakage = audit_fold_leakage(folds, all_rows)
    _require(
        bool(leakage["clean"]),
        f"prequential training leakage audit failed: {leakage['reasons']}",
    )

    per_cell_report = {
        name: {
            "scored": record["scored"],
            "mean_predicted": record["sum_predicted"] / record["scored"],
            "observed_target_rate": record["targets"] / record["scored"],
        }
        for name, record in sorted(per_cell.items())
    }
    return {
        "protocol": (
            "day_ordered_prequential_predict_day_k_from_days_before_k_only;"
            " training labels admitted only when label_available_utc is strictly"
            " before test-day UTC midnight minus the 3h broker-calendar skew"
        ),
        "strict_endpoint": {
            "endpoint": CONDITIONAL_ENDPOINT,
            "scored_rows": len(strict_pairs),
            "observed_target_rate": (
                sum(outcome for _, outcome in strict_pairs) / len(strict_pairs)
                if strict_pairs
                else None
            ),
            "brier": _brier(strict_pairs),
            "base_rate_brier": _brier(strict_base_pairs),
            "brier_minus_base_rate": (
                _brier(strict_pairs) - _brier(strict_base_pairs)
                if strict_pairs
                else None
            ),
            "reliability_by_predicted_decile": _reliability_deciles(strict_pairs),
            "by_window": {
                window: {
                    "scored_rows": len(pairs),
                    "observed_target_rate": (
                        sum(outcome for _, outcome in pairs) / len(pairs)
                        if pairs
                        else None
                    ),
                    "brier": _brier(pairs),
                    "base_rate_brier": _brier(strict_window_base_pairs[window]),
                }
                for window, pairs in sorted(strict_window_pairs.items())
            },
        },
        "limit_fill_stage": {
            "scored_rows": len(fill_pairs),
            "observed_fill_rate": (
                sum(outcome for _, outcome in fill_pairs) / len(fill_pairs)
                if fill_pairs
                else None
            ),
            "brier": _brier(fill_pairs),
            "base_rate_brier": _brier(fill_base_pairs),
            "reliability_by_predicted_decile": _reliability_deciles(fill_pairs),
        },
        "cell_backoff_counts": dict(sorted(backoff_counts.items())),
        "per_cell_coverage": per_cell_report,
        "days": day_reports,
        "training_leakage_audit": {
            "clean": leakage["clean"],
            "n_violations": leakage["n_violations"],
            "n_folds": leakage["n_folds"],
        },
    }


def _serialize_cells(
    tables: Mapping[tuple[int, tuple[str, ...]], Mapping[str, int]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for (level, key), cell in sorted(tables.items()):
        order_type = key[0]
        if order_type == "MARKET":
            p_fill, p_no_fill = _fraction(1, 1), _fraction(0, 1)
            fill_status = FILL_MARKET_EXACT_STATUS
        else:
            p_fill, p_no_fill = _fill_fractions(cell)
            fill_status = (
                EVALUATED_STATUS
                if cell["attempts"] >= LIMIT_MIN_RESOLVED_ATTEMPTS
                else OUT_OF_SUPPORT_STATUS
            )
        key_fields: dict[str, str] = {"proposed_order_type": order_type}
        if level > 0:
            key_fields["origin_family"] = key[1]
        if level > 1:
            key_fields["utc_session"] = key[2]
        output.append(
            {
                "hierarchy_level": HIERARCHY_LEVELS[level],
                "key": key_fields,
                "counts": {
                    "resolved_attempts": cell["attempts"],
                    "resolved_fills": cell["fills"],
                    "no_fill": cell["no_fill"],
                    "target": cell["target"],
                    "stop": cell["stop"],
                    "time_stop": cell["time_stop"],
                },
                "p_modelled_fill_given_resolved": p_fill,
                "p_modelled_no_fill_given_resolved": p_no_fill,
                "fill_probability_status": fill_status,
                "p_terminal_given_resolved_fill": _terminal_fractions(cell),
                "terminal_probability_status": (
                    EVALUATED_STATUS
                    if cell["fills"] >= TERMINAL_MIN_RESOLVED_FILLS
                    else OUT_OF_SUPPORT_STATUS
                ),
                "p_target_before_stop_given_filled_terminal_target_or_stop": (
                    _strict_endpoint_fraction(cell)
                ),
            }
        )
    return output


def fit_geometry_bound_outcome_model(
    rows_by_day: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    corpus_days: Sequence[Mapping[str, Any]],
    limit_origin_families: Sequence[str],
    preregistration: Mapping[str, Any],
    created_utc: str,
) -> dict[str, Any]:
    """Fit the artifact on the opened estate; every claim recomputable from counts."""

    _validate_preregistration(preregistration)
    created = _utc(created_utc, "created_utc")
    days = [str(record["trading_day"]) for record in corpus_days]
    _require(len(days) == len(set(days)), "duplicate corpus day")
    _require(days == sorted(days), "corpus days must be in chronological order")
    _require(
        set(rows_by_day) == set(days),
        "rows_by_day must cover exactly the declared corpus days",
    )
    window_by_day = {
        str(record["trading_day"]): str(record["window_id"])
        for record in corpus_days
    }

    validated_by_day: dict[str, list[dict[str, Any]]] = {}
    seen: set[str] = set()
    corpus_records: list[dict[str, Any]] = []
    for record in corpus_days:
        day = str(record["trading_day"])
        rows = validate_training_rows(
            rows_by_day[day],
            allowed_days=(day,),
            limit_origin_families=limit_origin_families,
            preregistration=preregistration,
        )
        for row in rows:
            key = row["candidate_occurrence_key"]
            _require(key not in seen, f"cross-day duplicate occurrence: {key}")
            seen.add(key)
            available = row.get("label_available_utc")
            if available not in (None, ""):
                _require(
                    _utc(available, "label_available_utc") <= created,
                    f"{key} label available after the fit instant",
                )
        validated_by_day[day] = rows
        coverage = _coverage(rows)
        corpus_records.append(
            {
                "trading_day": day,
                "window_id": str(record["window_id"]),
                "compact_root": str(record["compact_root"]),
                "authority_root_sha256": _hex_hash(
                    record.get("authority_root_sha256"),
                    f"{day}.authority_root_sha256",
                ),
                "source_manifest_root_sha256": _hex_hash(
                    record.get("source_manifest_root_sha256"),
                    f"{day}.source_manifest_root_sha256",
                ),
                **coverage,
            }
        )

    evaluation = _prequential_evaluation(validated_by_day, days, window_by_day)

    final_rows = [
        row
        for day in days
        for row in validated_by_day[day]
        if _state(row) is not None
    ]
    final_tables = _tables(final_rows)
    totals = _coverage([row for day in days for row in validated_by_day[day]])

    artifact = {
        "schema": MODEL_SCHEMA,
        "model_version": SUPPORTED_MODEL_VERSION,
        "artifact_status": "RESULT_BEARING_OPENED_ESTATE_FIT",
        "created_utc": created.isoformat().replace("+00:00", "Z"),
        "authority": {
            "conditional_endpoint": CONDITIONAL_ENDPOINT,
            "primary_evidence_class": PRIMARY_EVIDENCE_CLASS,
            "estimator": "TWO_STAGE_JEFFREYS_HAND_COUNT_ONLY",
            "licenses": (
                "honest_per_cell_outcome_frequencies_as_probability_inputs"
            ),
            "does_not_license": (
                "ev_based_admission_selection_sizing_or_live_authority_"
                "until_a_separate_preregistered_read"
            ),
            "broker_fill_truth": False,
            "live_activation_authority": False,
            "model_or_feature_search_used": False,
            "unseen_or_reserve_data_accessed": False,
            "no_fill_is_execution_mass_not_loss": True,
            "time_stop_is_separate_terminal_mass_not_loss": True,
            "censored_rows_are_coverage_masses_not_losses": True,
        },
        "preregistration_payload_sha256": preregistration["payload_sha256"],
        "estimator_contract": {
            "hierarchy": list(HIERARCHY_LEVELS),
            "hierarchy_rule": (
                "deepest level meeting the fixed support rule from"
                " prediction-time keys only; never chosen by realized"
                " performance"
            ),
            "jeffreys_fraction_contract": {
                "limit_fill": {
                    "prior": "Beta(1/2,1/2)",
                    "numerator": "2*n_modelled_limit_fills + 1",
                    "denominator": "2*n_resolved_limit_attempts + 2",
                },
                "terminal_state_given_fill": {
                    "prior": "Dirichlet(1/2,1/2,1/2) over TARGET, STOP, TIME_STOP",
                    "numerator_for_each_state": "2*n_state + 1",
                    "denominator": "2*n_resolved_fills + 3",
                },
                "target_before_stop_given_filled_terminal_target_or_stop": {
                    "prior": (
                        "Dirichlet(1/2,1/2,1/2) restricted to {TARGET,STOP}"
                        " = Beta(n_target+1/2, n_stop+1/2)"
                    ),
                    "numerator": "2*n_target + 1",
                    "denominator": "2*(n_target + n_stop) + 2",
                },
            },
            "support": {
                "fill_min_resolved_attempts_per_cell": LIMIT_MIN_RESOLVED_ATTEMPTS,
                "terminal_min_resolved_fills_per_cell": TERMINAL_MIN_RESOLVED_FILLS,
                "insufficient_action": (
                    "OUT_OF_SUPPORT_with_exact_shortfall_never_a_default"
                ),
            },
            "order_type_derivation": {
                "rule": (
                    "LIMIT iff origin_family in limit_origin_families,"
                    " else MARKET"
                ),
                "limit_origin_families": sorted(set(limit_origin_families)),
            },
            "label_availability_rule": (
                "training rows admitted only when label_available_utc is"
                " strictly before test-day UTC midnight minus"
                f" {LABEL_AVAILABILITY_SKEW_HOURS}h broker-calendar skew"
            ),
        },
        "geometry_binding": {
            "training_outcome_geometry": (
                "every training label was resolved at that candidate's own"
                " immutable approved entry/stop/target geometry; the"
                " endpoint is defined only at the candidate's final"
                " target/stop geometry"
            ),
            "training_geometry_contract_hash": (
                "sha256 of canonical {entry,stop,target,risk,submission,"
                "expiry_and_horizon} per training row"
                " (candidate_funnel_analysis._lifecycle_row)"
            ),
            "consumption_rule": (
                "a per-candidate packet must stamp geometry_contract_hash_"
                "sha256 equal to the candidate's FINAL post-router"
                " target/stop geometry contract packet_hash_sha256;"
                " geometry_bound_outcome_calibration_disposition revalidates"
                " it and any mismatch is NOT_EVALUABLE"
            ),
        },
        "training_corpus": {
            "day_count": len(days),
            "days": corpus_records,
            "totals": totals,
            "opened_estate_only": True,
            "excluded_by_rule": [
                "april_2026_and_may_2026 (frozen read in progress)",
                "held_reserve_days 2025-10-31 and 2025-11-05",
                "anything READ_RESTRICTED",
            ],
        },
        "prequential_evaluation": evaluation,
        "final_fit": {
            "admitted_resolved_row_count": len(final_rows),
            "cells": _serialize_cells(final_tables),
        },
    }
    artifact["payload_sha256"] = canonical_payload_sha256(artifact)
    return artifact


def load_geometry_bound_outcome_model(
    path: str | Path, *, expected_artifact_sha256: str
) -> tuple[dict[str, Any], str]:
    """Load and fail-closed verify a model artifact; returns (model, file sha)."""

    expected = _hex_hash(expected_artifact_sha256, "expected_artifact_sha256")
    raw = Path(path).read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    _require(
        observed == expected,
        f"model artifact sha256 mismatch: {observed} != {expected}",
    )
    model = json.loads(raw.decode("utf-8"))
    _require(isinstance(model, dict), "model artifact is not an object")
    _require(model.get("schema") == MODEL_SCHEMA, "model artifact schema mismatch")
    _require(
        model.get("model_version") == SUPPORTED_MODEL_VERSION,
        "model artifact version unsupported",
    )
    payload = dict(model)
    claimed = _hex_hash(payload.pop("payload_sha256", None), "model.payload_sha256")
    _require(
        canonical_payload_sha256(payload) == claimed,
        "model artifact payload_sha256 mismatch",
    )
    cells = model.get("final_fit", {}).get("cells")
    _require(
        isinstance(cells, list) and bool(cells), "model artifact carries no cells"
    )
    return model, observed


def _cell_index(
    model: Mapping[str, Any]
) -> dict[tuple[int, tuple[str, ...]], Mapping[str, Any]]:
    index: dict[tuple[int, tuple[str, ...]], Mapping[str, Any]] = {}
    for cell in model["final_fit"]["cells"]:
        key_fields = cell["key"]
        key = tuple(
            str(key_fields[field])
            for field in ("proposed_order_type", "origin_family", "utc_session")
            if field in key_fields
        )
        index[(len(key) - 1, key)] = cell
    return index


def build_geometry_bound_outcome_calibration_packet(
    model: Mapping[str, Any],
    *,
    origin_family: Any,
    utc_session: Any,
    decision_action: Any,
    decision_time_utc: Any,
    outcome_horizon_utc: Any,
    geometry_contract_hash_sha256: Any,
    model_artifact_sha256: str,
) -> dict[str, Any]:
    """Build the per-candidate packet from the loaded model; fail-closed."""

    packet: dict[str, Any] = {
        "schema": PACKET_SCHEMA,
        "model_version": str(model.get("model_version") or ""),
        "model_artifact_sha256": str(model_artifact_sha256 or ""),
        "model_payload_sha256": str(model.get("payload_sha256") or ""),
        "endpoint": CONDITIONAL_ENDPOINT,
        "evidence_class": PRIMARY_EVIDENCE_CLASS,
        "decision_action": str(decision_action or "").upper() or None,
        "decision_time_utc": str(decision_time_utc or "") or None,
        "outcome_horizon_utc": str(outcome_horizon_utc or "") or None,
        "geometry_contract_hash_sha256": str(geometry_contract_hash_sha256 or "")
        or None,
        "execution_and_censor_masses": {
            "no_fill_is_execution_mass_not_loss": True,
            "time_stop_is_separate_terminal_mass_not_loss": True,
            "censored_rows_are_coverage_masses_not_losses": True,
        },
        "calibration_provenance": {
            "prequential_report_in_model_artifact": True,
            "model_payload_sha256": str(model.get("payload_sha256") or ""),
        },
    }
    family = str(origin_family or "")
    session = str(utc_session or "")
    limit_families = (
        model.get("estimator_contract", {})
        .get("order_type_derivation", {})
        .get("limit_origin_families", [])
    )
    if not family or not session or packet["decision_action"] not in _DECISION_ACTIONS:
        packet["probability_status"] = NOT_EVALUABLE_ORDER_POLICY_STATUS
        packet["cell"] = {
            "proposed_order_type": None,
            "origin_family": family or None,
            "utc_session": session or None,
        }
        packet["packet_hash_sha256"] = canonical_payload_sha256(packet)
        return packet
    order_type = derive_proposed_order_type(family, limit_families)
    packet["cell"] = {
        "proposed_order_type": order_type,
        "origin_family": family,
        "utc_session": session,
    }
    if not packet["geometry_contract_hash_sha256"]:
        packet["probability_status"] = NOT_EVALUABLE_GEOMETRY_STATUS
        packet["packet_hash_sha256"] = canonical_payload_sha256(packet)
        return packet

    index = _cell_index(model)
    row = {
        "proposed_order_type": order_type,
        "origin_family": family,
        "utc_session": session,
    }

    def select(field: str, minimum: int) -> tuple[int | None, Mapping[str, Any] | None]:
        for level in (2, 1, 0):
            cell = index.get((level, _cell_key(row, level)))
            if cell is not None and cell["counts"][field] >= minimum:
                return level, cell
        return None, None

    fill_block: dict[str, Any] | None
    if order_type == "MARKET":
        fill_block = {
            "hierarchy_level": MARKET_EXACT_LEVEL,
            "counts": None,
            "p_modelled_fill_given_resolved": _fraction(1, 1),
            "p_modelled_no_fill_given_resolved": _fraction(0, 1),
            "status": FILL_MARKET_EXACT_STATUS,
        }
    else:
        fill_level, fill_cell = select(
            "resolved_attempts", LIMIT_MIN_RESOLVED_ATTEMPTS
        )
        if fill_cell is None:
            fill_block = None
        else:
            counts = fill_cell["counts"]
            fill_block = {
                "hierarchy_level": HIERARCHY_LEVELS[fill_level],
                "counts": {
                    "resolved_attempts": counts["resolved_attempts"],
                    "resolved_fills": counts["resolved_fills"],
                    "no_fill": counts["no_fill"],
                },
                "p_modelled_fill_given_resolved": dict(
                    fill_cell["p_modelled_fill_given_resolved"]
                ),
                "p_modelled_no_fill_given_resolved": dict(
                    fill_cell["p_modelled_no_fill_given_resolved"]
                ),
                "status": EVALUATED_STATUS,
            }
    terminal_level, terminal_cell = select(
        "resolved_fills", TERMINAL_MIN_RESOLVED_FILLS
    )
    if fill_block is None or terminal_cell is None:
        packet["probability_status"] = OUT_OF_SUPPORT_STATUS
        root = index.get((0, (order_type,)))
        root_counts = (
            root["counts"]
            if root is not None
            else {"resolved_attempts": 0, "resolved_fills": 0}
        )
        packet["support_shortfall_at_order_type_root"] = {
            "root_resolved_attempts": root_counts["resolved_attempts"],
            "root_resolved_fills": root_counts["resolved_fills"],
            "additional_resolved_limit_attempts_required": (
                max(
                    0,
                    LIMIT_MIN_RESOLVED_ATTEMPTS
                    - root_counts["resolved_attempts"],
                )
                if order_type == "LIMIT"
                else 0
            ),
            "additional_resolved_fills_required": max(
                0, TERMINAL_MIN_RESOLVED_FILLS - root_counts["resolved_fills"]
            ),
        }
        packet["packet_hash_sha256"] = canonical_payload_sha256(packet)
        return packet

    terminal_counts = terminal_cell["counts"]
    packet["probability_status"] = EVALUATED_STATUS
    packet["fill"] = fill_block
    packet["terminal_given_fill"] = {
        "hierarchy_level": HIERARCHY_LEVELS[terminal_level],
        "counts": {
            "resolved_fills": terminal_counts["resolved_fills"],
            "target": terminal_counts["target"],
            "stop": terminal_counts["stop"],
            "time_stop": terminal_counts["time_stop"],
        },
        "p_terminal_given_resolved_fill": {
            state: dict(value)
            for state, value in terminal_cell[
                "p_terminal_given_resolved_fill"
            ].items()
        },
        "status": EVALUATED_STATUS,
    }
    packet["p_target_before_stop_given_filled_terminal_target_or_stop"] = dict(
        terminal_cell[
            "p_target_before_stop_given_filled_terminal_target_or_stop"
        ]
    )
    packet["packet_hash_sha256"] = canonical_payload_sha256(packet)
    return packet


def _check_fraction(
    block: Any, numerator: int, denominator: int
) -> bool:
    return (
        isinstance(block, Mapping)
        and block.get("numerator") == numerator
        and block.get("denominator") == denominator
        and block.get("value") == numerator / denominator
    )


def validate_geometry_bound_outcome_calibration_packet(
    packet: Mapping[str, Any],
    *,
    geometry_contract_hash_sha256: str | None,
    expected_model_artifact_sha256: str | None,
) -> list[str]:
    """Recompute every atom of a per-candidate packet; return failure reasons.

    An empty list means every atom validated.  The first reason is the primary
    disposition reason.  Acceptance additionally requires the caller-attested
    ``expected_model_artifact_sha256`` -- without it the packet is refused as
    unverified, so nothing can self-declare economic authority.
    """

    failures: list[str] = []
    if not isinstance(packet, Mapping):
        return [REASON_PACKET_HASH_INVALID]
    if (
        packet.get("schema") != PACKET_SCHEMA
        or packet.get("model_version") != SUPPORTED_MODEL_VERSION
    ):
        return [REASON_MODEL_VERSION_UNSUPPORTED]

    payload = dict(packet)
    claimed_hash = payload.pop("packet_hash_sha256", None)
    try:
        _hex_hash(claimed_hash, "packet_hash_sha256")
        self_hash_ok = canonical_payload_sha256(payload) == claimed_hash
    except ValueError:
        self_hash_ok = False
    if not self_hash_ok:
        return [REASON_PACKET_HASH_INVALID]

    try:
        artifact_sha = _hex_hash(
            packet.get("model_artifact_sha256"), "model_artifact_sha256"
        )
        _hex_hash(packet.get("model_payload_sha256"), "model_payload_sha256")
    except ValueError:
        failures.append(REASON_MODEL_ARTIFACT_UNVERIFIED)
        artifact_sha = None
    if artifact_sha is not None:
        if expected_model_artifact_sha256 is None:
            failures.append(REASON_MODEL_ARTIFACT_UNVERIFIED)
        elif artifact_sha != expected_model_artifact_sha256:
            failures.append(REASON_MODEL_ARTIFACT_SHA_MISMATCH)

    packet_geometry = str(packet.get("geometry_contract_hash_sha256") or "")
    geometry_hash = str(geometry_contract_hash_sha256 or "")
    if not packet_geometry or not geometry_hash:
        failures.append(REASON_GEOMETRY_HASH_MISSING)
    elif packet_geometry != geometry_hash:
        failures.append(REASON_STALE_GEOMETRY)

    if packet.get("decision_action") not in _DECISION_ACTIONS:
        failures.append(REASON_DECISION_ATOMS_INVALID)
    else:
        try:
            decision_time = _utc(packet.get("decision_time_utc"), "decision_time_utc")
            horizon = _utc(packet.get("outcome_horizon_utc"), "outcome_horizon_utc")
            if horizon <= decision_time:
                failures.append(REASON_DECISION_ATOMS_INVALID)
        except ValueError:
            failures.append(REASON_DECISION_ATOMS_INVALID)

    if (
        packet.get("endpoint") != CONDITIONAL_ENDPOINT
        or packet.get("evidence_class") != PRIMARY_EVIDENCE_CLASS
    ):
        failures.append(REASON_ENDPOINT_CONTRACT_MISMATCH)

    status = packet.get("probability_status")
    if status == OUT_OF_SUPPORT_STATUS:
        failures.append(REASON_OUT_OF_SUPPORT)
        return failures
    if status != EVALUATED_STATUS:
        failures.append(REASON_NOT_EVALUABLE_CELL)
        return failures

    cell = packet.get("cell")
    cell = cell if isinstance(cell, Mapping) else {}
    order_type = cell.get("proposed_order_type")
    if (
        order_type not in {"MARKET", "LIMIT"}
        or not cell.get("origin_family")
        or not cell.get("utc_session")
    ):
        failures.append(REASON_NOT_EVALUABLE_CELL)
        return failures

    fill = packet.get("fill")
    fill = fill if isinstance(fill, Mapping) else {}
    if order_type == "MARKET":
        if not (
            fill.get("hierarchy_level") == MARKET_EXACT_LEVEL
            and fill.get("status") == FILL_MARKET_EXACT_STATUS
            and _check_fraction(fill.get("p_modelled_fill_given_resolved"), 1, 1)
            and _check_fraction(
                fill.get("p_modelled_no_fill_given_resolved"), 0, 1
            )
        ):
            failures.append(REASON_RATIONAL_IDENTITY_MISMATCH)
    else:
        counts = fill.get("counts")
        counts = counts if isinstance(counts, Mapping) else {}
        attempts = counts.get("resolved_attempts")
        fills = counts.get("resolved_fills")
        no_fill = counts.get("no_fill")
        if not (
            isinstance(attempts, int)
            and isinstance(fills, int)
            and isinstance(no_fill, int)
            and attempts == fills + no_fill
            and fill.get("hierarchy_level") in HIERARCHY_LEVELS
            and fill.get("status") == EVALUATED_STATUS
        ):
            failures.append(REASON_RATIONAL_IDENTITY_MISMATCH)
        elif attempts < LIMIT_MIN_RESOLVED_ATTEMPTS:
            failures.append(REASON_SUPPORT_BELOW_MINIMUM)
        elif not (
            _check_fraction(
                fill.get("p_modelled_fill_given_resolved"),
                2 * fills + 1,
                2 * attempts + 2,
            )
            and _check_fraction(
                fill.get("p_modelled_no_fill_given_resolved"),
                2 * no_fill + 1,
                2 * attempts + 2,
            )
        ):
            failures.append(REASON_RATIONAL_IDENTITY_MISMATCH)

    terminal = packet.get("terminal_given_fill")
    terminal = terminal if isinstance(terminal, Mapping) else {}
    terminal_counts = terminal.get("counts")
    terminal_counts = (
        terminal_counts if isinstance(terminal_counts, Mapping) else {}
    )
    fills = terminal_counts.get("resolved_fills")
    n_target = terminal_counts.get("target")
    n_stop = terminal_counts.get("stop")
    n_time_stop = terminal_counts.get("time_stop")
    if not (
        isinstance(fills, int)
        and isinstance(n_target, int)
        and isinstance(n_stop, int)
        and isinstance(n_time_stop, int)
        and fills == n_target + n_stop + n_time_stop
        and terminal.get("hierarchy_level") in HIERARCHY_LEVELS
        and terminal.get("status") == EVALUATED_STATUS
    ):
        failures.append(REASON_RATIONAL_IDENTITY_MISMATCH)
        return failures
    if fills < TERMINAL_MIN_RESOLVED_FILLS:
        failures.append(REASON_SUPPORT_BELOW_MINIMUM)
        return failures
    probabilities = terminal.get("p_terminal_given_resolved_fill")
    probabilities = probabilities if isinstance(probabilities, Mapping) else {}
    denominator = 2 * fills + 3
    for state, count in (
        ("TARGET", n_target),
        ("STOP", n_stop),
        ("TIME_STOP", n_time_stop),
    ):
        if not _check_fraction(
            probabilities.get(state), 2 * count + 1, denominator
        ):
            failures.append(REASON_RATIONAL_IDENTITY_MISMATCH)
            return failures
    if not _check_fraction(
        packet.get("p_target_before_stop_given_filled_terminal_target_or_stop"),
        2 * n_target + 1,
        2 * (n_target + n_stop) + 2,
    ):
        failures.append(REASON_RATIONAL_IDENTITY_MISMATCH)
    return failures


__all__ = [
    "CONDITIONAL_ENDPOINT",
    "EVALUATED_STATUS",
    "FILL_MARKET_EXACT_STATUS",
    "HIERARCHY_LEVELS",
    "LABEL_AVAILABILITY_SKEW_HOURS",
    "LIMIT_MIN_RESOLVED_ATTEMPTS",
    "MODEL_SCHEMA",
    "OUT_OF_SUPPORT_STATUS",
    "PACKET_SCHEMA",
    "PREREGISTRATION_V1_PAYLOAD_SHA256",
    "PRIMARY_EVIDENCE_CLASS",
    "REASON_DECISION_ATOMS_INVALID",
    "REASON_ENDPOINT_CONTRACT_MISMATCH",
    "REASON_GEOMETRY_HASH_MISSING",
    "REASON_MODEL_ARTIFACT_SHA_MISMATCH",
    "REASON_MODEL_ARTIFACT_UNVERIFIED",
    "REASON_MODEL_VERSION_UNSUPPORTED",
    "REASON_NOT_EVALUABLE_CELL",
    "REASON_OUT_OF_SUPPORT",
    "REASON_PACKET_HASH_INVALID",
    "REASON_RATIONAL_IDENTITY_MISMATCH",
    "REASON_STALE_GEOMETRY",
    "REASON_SUPPORT_BELOW_MINIMUM",
    "SUPPORTED_MODEL_VERSION",
    "TERMINAL_MIN_RESOLVED_FILLS",
    "TERMINAL_STATES",
    "build_geometry_bound_outcome_calibration_packet",
    "canonical_payload_sha256",
    "derive_proposed_order_type",
    "fit_geometry_bound_outcome_model",
    "load_geometry_bound_outcome_model",
    "validate_geometry_bound_outcome_calibration_packet",
    "validate_training_rows",
]
