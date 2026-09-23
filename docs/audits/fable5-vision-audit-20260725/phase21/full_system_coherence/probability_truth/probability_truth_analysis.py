#!/usr/bin/env python3
"""Reproduce the Wave 21 action-support falsifier and fit its causal baseline.

This development-only analysis reads exactly the three retained 0.20R stage
ledgers.  It never turns no-fill or unresolved terminal rows into losses.

``fit_wave21_development`` is a pure synthetic evaluator for the separately
preregistered two-stage Jeffreys baseline.  A result-bearing loader/CLI is
deliberately deferred until the upstream occurrence and conservation schemas
are frozen.  The evaluator does not call the legacy Platt diagnostic below,
choose folds, search features, or inspect untouched/reserve data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research_infra.trainer_folds import TrainerFold, audit_fold_leakage
from src.research_infra.validation_anti_overfit_v4 import (
    brier_score as validated_brier_score,
    logloss as validated_logloss,
)


SCHEMA = "gtos.wave21.probability_truth.development_only.v1"
ANALYSIS_SOURCE_HEAD = "3b82310ac94201f79f4a649b7d0d1a9b6cade276"
RETAINED_LEDGER_PRODUCER_TARGET = "875037f1bc787009c6020be82c3883d9fcf85fa8"
TARGET = "target_reached_before_stop"
STOP = "stop_reached_before_target"
CENSORED_TERMINALS = (
    "not_filled_no_trade",
    "entry_fill_executable_terminal_r_ordered_tick_sequence_required",
    "entry_fill_executable_terminal_path_source_gap",
    "time_stop_close_mark_from_m1",
)
KNOWN_TERMINALS = frozenset((TARGET, STOP, *CENSORED_TERMINALS))
LEDGERS = {
    "2025-10-28": {
        "sha256": "89762595a78e7d81003a2595c08e39d9dffb6d0c4bed2c2d0e7970bcbb4a7991",
        "path": (
            "/private/tmp/wave21-minimal-repair-20251028-875037f1b-r4/"
            "harness_wave21_minimal_repair_20251028_875037f1b_r4_stage_ledger.jsonl.gz"
        ),
    },
    "2025-11-03": {
        "sha256": "db84b4d7137b6da9d60741abca4ff069152a73dc89fc0e4243f82329e82711d8",
        "path": (
            "/private/tmp/wave21-minimal-repair-20251103-875037f1b-r1/"
            "harness_wave21_minimal_repair_20251103_875037f1b_r1_stage_ledger.jsonl.gz"
        ),
    },
    "2025-11-07": {
        "sha256": "e135d297cee9631eec76d322a9864a3011941987151940d9b4d69dc4a9a9e835",
        "path": (
            "/private/tmp/wave21-minimal-repair-20251107-875037f1b-r1/"
            "harness_wave21_minimal_repair_20251107_875037f1b_r1_stage_ledger.jsonl.gz"
        ),
    },
}


DEVELOPMENT_FIT_SCHEMA = "gtos.wave21.two_stage_jeffreys.development_fit.v1"
PREREGISTRATION_V1_PAYLOAD_SHA256 = (
    "2db7e5c94348a98b598a203aace7006545a03a77fcb081aeb1239a8ec0c65a95"
)
PRIMARY_EVIDENCE_CLASS = "ALL24_M1_MODELLED_LIFECYCLE_NOT_BROKER_FILL"
TICK_EVIDENCE_CLASS = "ORDERED_BID_ASK_MODELLED_LIFECYCLE_NOT_BROKER_FILL"
DEVELOPMENT_DAYS = (
    "2025-10-27", "2025-10-28", "2025-10-29",
    "2025-11-03", "2025-11-04", "2025-11-07",
)
FROZEN_DEVELOPMENT_FOLDS = (
    ("DEV_FOLD_1", DEVELOPMENT_DAYS[:2], "2025-10-29"),
    ("DEV_FOLD_2", DEVELOPMENT_DAYS[:3], "2025-11-03"),
    ("DEV_FOLD_3", DEVELOPMENT_DAYS[:4], "2025-11-04"),
    ("DEV_FOLD_4", DEVELOPMENT_DAYS[:5], "2025-11-07"),
)
HIERARCHY_LEVELS = (
    "proposed_order_type",
    "proposed_order_type_x_origin_family",
    "proposed_order_type_x_origin_family_x_utc_session",
)
TERMINAL_STATES = ("TARGET", "STOP", "TIME_STOP")
RESOLVED_STATUS_TO_STATE = {
    "RESOLVED_NO_FILL": "NO_FILL",
    "RESOLVED_FILLED_TARGET": "TARGET",
    "RESOLVED_FILLED_STOP": "STOP",
    "RESOLVED_FILLED_TIME_STOP": "TIME_STOP",
}
LIMIT_MIN_RESOLVED_ATTEMPTS = 100
TERMINAL_MIN_RESOLVED_FILLS = 30
TICK_COVERED_SYMBOLS = frozenset(("EURUSD", "USDJPY", "XAGUSD", "XAUUSD"))
TICK_PAIR_FIELDS = (
    "candidate_occurrence_key",
    "proposed_order_policy_hash_sha256",
    "geometry_contract_hash_sha256",
    "arm_id",
)
_UTC = dt.timezone.utc


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _hash(value: Any, field: str) -> str:
    if not (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "009abcdef" for character in value)
    ):
        raise ValueError(f"{field} invalid sha256")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_preregistration(preregistration: Mapping[str, Any]) -> None:
    payload = dict(preregistration)
    expected = _hash(payload.pop("payload_sha256", None), "preregistration.payload_sha256")
    _require(_canonical_hash(payload) == expected, "preregistration payload_sha256 mismatch")
    _require(
        expected == PREREGISTRATION_V1_PAYLOAD_SHA256
        and preregistration.get("schema")
        == "gtos.wave21.outcome_authority.preregistration.v1",
        "exact frozen OUTCOME_AUTHORITY_PREREGISTRATION_V1 required",
    )


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _state(row: Mapping[str, Any]) -> str | None:
    status = str(row.get("lifecycle_label_status") or "")
    if status in RESOLVED_STATUS_TO_STATE:
        return RESOLVED_STATUS_TO_STATE[status]
    if status.startswith("CENSORED_"):
        return None
    raise ValueError(f"unknown lifecycle status: {status!r}")


def _normalize_rows(
    rows: Sequence[Mapping[str, Any]], preregistration: Mapping[str, Any]
) -> list[dict[str, Any]]:
    lifecycle_values = set(
        preregistration["lifecycle_and_label_contract"]["lifecycle_label_statuses"]
    )
    cost_values = set(preregistration["cost_contract"]["cost_label_status_values"])
    normalized, seen = [], set()
    for number, source in enumerate(rows, 1):
        _require(isinstance(source, Mapping), f"row {number} is not an object")
        row = dict(source)
        key = str(row.get("candidate_occurrence_key") or "")
        _require(bool(key) and key not in seen, f"missing/duplicate occurrence at row {number}")
        seen.add(key)
        _require(row.get("row_key") in (None, key), f"row_key mismatch for {key}")
        row["row_key"] = key
        _require(row.get("trading_day") in DEVELOPMENT_DAYS, f"{key} outside development")
        _require(row.get("evidence_class") == PRIMARY_EVIDENCE_CLASS, f"{key} not M1 primary")
        order_type = row.get("proposed_order_type")
        _require(order_type in {"MARKET", "LIMIT"}, f"{key} bad order type")
        _require(bool(row.get("origin_family")), f"{key} missing family")
        _require(bool(row.get("utc_session")), f"{key} missing session")
        _hash(row.get("candidate_source_safe_fingerprint_sha256"), f"{key}.fingerprint")
        _hash(row.get("proposed_order_policy_hash_sha256"), f"{key}.order_policy")
        _hash(row.get("geometry_contract_hash_sha256"), f"{key}.geometry")
        _require(bool(row.get("arm_id")), f"{key} missing arm_id")
        _hash(row.get("source_manifest_hash_sha256"), f"{key}.source_manifest")
        _require(row.get("lifecycle_label_status") in lifecycle_values, f"{key} bad lifecycle")
        _require(row.get("cost_label_status") in cost_values, f"{key} bad cost status")
        state = _state(row)
        if state == "NO_FILL":
            _require(order_type != "MARKET", f"MARKET row {key} cannot resolve as NO_FILL")
            _require(
                row["cost_label_status"] == "NOT_APPLICABLE_NO_FILL",
                f"{key} bad no-fill cost",
            )
        elif state in TERMINAL_STATES:
            _require(
                row["cost_label_status"] != "NOT_APPLICABLE_NO_FILL",
                f"{key} filled with no-fill cost",
            )
            if row["cost_label_status"] == "COMPLETE":
                row["terminal_net_r"] = _finite(row.get("terminal_net_r"), f"{key}.terminal_net_r")
        if state is not None:
            _require(row.get("label_span_status") == "measured", f"{key} span not measured")
            start = _utc(row.get("label_span_start_utc"), f"{key}.label_span_start_utc")
            end = _utc(row.get("label_span_end_utc"), f"{key}.label_span_end_utc")
            _require(end >= start, f"{key} inverted span")
            if row.get("label_available_utc") not in (None, ""):
                _require(
                    _utc(row["label_available_utc"], f"{key}.label_available_utc") >= end,
                    f"{key} label is available before its span ends",
                )
        normalized.append(row)
    return normalized


def _key(row: Mapping[str, Any], level: int) -> tuple[str, ...]:
    return (
        str(row["proposed_order_type"]),
        str(row["origin_family"]),
        str(row["utc_session"]),
    )[: level + 1]


def _blank_cell() -> dict[str, Any]:
    return {
        "attempts": 0, "fills": 0, "no_fill": 0, "states": Counter(),
        "complete": 0, "incomplete": Counter(),
        "net": {state: [] for state in TERMINAL_STATES},
    }


def _tables(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[int, tuple[str, ...]], dict]:
    tables: dict[tuple[int, tuple[str, ...]], dict] = {}
    for row in rows:
        state = _state(row)
        if state is None:
            continue
        for level in range(3):
            cell = tables.setdefault((level, _key(row, level)), _blank_cell())
            cell["attempts"] += 1
            if state == "NO_FILL":
                cell["no_fill"] += 1
                continue
            cell["fills"] += 1
            cell["states"][state] += 1
            if row["cost_label_status"] == "COMPLETE":
                cell["complete"] += 1
                cell["net"][state].append(float(row["terminal_net_r"]))
            else:
                cell["incomplete"][row["cost_label_status"]] += 1
    return tables


def _cell(tables: Mapping, row: Mapping[str, Any], level: int) -> dict:
    return tables.get((level, _key(row, level)), _blank_cell())


def _select(
    tables: Mapping, row: Mapping[str, Any], field: str, minimum: int
) -> tuple[int | None, dict | None]:
    for level in (2, 1, 0):
        cell = _cell(tables, row, level)
        if cell[field] >= minimum:
            return level, cell
    return None, None


def _fraction(numerator: int, denominator: int) -> dict[str, Any]:
    return {"numerator": numerator, "denominator": denominator, "value": numerator / denominator}


def _shortfall(tables: Mapping, row: Mapping[str, Any]) -> dict[str, int]:
    root = _cell(tables, row, 0)
    return {
        "root_resolved_attempts": root["attempts"],
        "root_resolved_fills": root["fills"],
        "additional_resolved_limit_attempts_required": (
            max(0, 100 - root["attempts"]) if row["proposed_order_type"] == "LIMIT" else 0
        ),
        "additional_resolved_attempts_required_for_expected_net": max(
            0, 100 - root["attempts"]
        ),
        "additional_resolved_fills_required": max(0, 30 - root["fills"]),
    }


def _predict(tables: Mapping, row: Mapping[str, Any]) -> dict[str, Any]:
    if row["proposed_order_type"] == "MARKET":
        fill_level, fill_cell = None, None
        p_fill, p_no_fill = _fraction(1, 1), _fraction(0, 1)
    else:
        fill_level, fill_cell = _select(tables, row, "attempts", 100)
        if fill_cell:
            denominator = 2 * fill_cell["attempts"] + 2
            p_fill = _fraction(2 * fill_cell["fills"] + 1, denominator)
            p_no_fill = _fraction(2 * fill_cell["no_fill"] + 1, denominator)
        else:
            p_fill = p_no_fill = None
    terminal_level, terminal_cell = _select(tables, row, "fills", 30)
    expected_level, expected_cell = _select(tables, row, "attempts", 100)
    terminal = None
    if terminal_cell:
        denominator = 2 * terminal_cell["fills"] + 3
        terminal = {
            state: _fraction(2 * terminal_cell["states"][state] + 1, denominator)
            for state in TERMINAL_STATES
        }
    result = {
        "probability_status": (
            "EVALUATED_OUTCOME_BASELINE" if p_fill and terminal else "OUT_OF_SUPPORT"
        ),
        "p_fill": p_fill,
        "p_no_fill": p_no_fill,
        "terminal_probabilities": terminal,
        "fill_hierarchy_level": (
            HIERARCHY_LEVELS[fill_level] if fill_level is not None else "MARKET_EXACT"
        ),
        "terminal_hierarchy_level": (
            HIERARCHY_LEVELS[terminal_level] if terminal_level is not None else None
        ),
        "expected_net_hierarchy_level": (
            HIERARCHY_LEVELS[expected_level] if expected_level is not None else None
        ),
        "support_shortfall_at_order_type_root": _shortfall(tables, row),
        "expected_net_status": "OUT_OF_SUPPORT",
        "expected_modelled_net_r_given_resolved": None,
    }
    if (
        not p_fill
        or not terminal
        or terminal_cell is None
        or terminal_level is None
        or expected_cell is None
    ):
        return result
    selected_cost_cells = [terminal_cell, expected_cell]
    if any(cell["complete"] != cell["fills"] for cell in selected_cost_cells):
        result["expected_net_status"] = "NOT_EVALUABLE_COST"
        return result
    means = {}
    for state in TERMINAL_STATES:
        for level in range(terminal_level, -1, -1):
            candidate = _cell(tables, row, level)
            values = candidate["net"][state]
            if candidate["complete"] == candidate["fills"] and values:
                means[state] = sum(values) / len(values)
                break
        else:
            result["expected_net_status"] = "NOT_EVALUABLE_COST"
            return result
    result["expected_net_status"] = "EVALUATED_EXPECTED_NET"
    result["expected_modelled_net_r_given_resolved"] = p_fill["value"] * sum(
        terminal[state]["value"] * means[state] for state in TERMINAL_STATES
    )
    return result


def _coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts, censored, incomplete = Counter(), Counter(), Counter()
    for row in rows:
        state = _state(row)
        if state is None:
            censored[row["lifecycle_label_status"]] += 1
            continue
        counts["attempts"] += 1
        if state == "NO_FILL":
            counts["no_fill"] += 1
        else:
            counts["fills"] += 1
            counts[state] += 1
            if row["cost_label_status"] == "COMPLETE":
                counts["complete"] += 1
            else:
                incomplete[row["cost_label_status"]] += 1
    return {
        "all_occurrences": len(rows),
        "lifecycle_resolved_attempts": counts["attempts"],
        "lifecycle_resolved_fills": counts["fills"],
        "no_fill": counts["no_fill"],
        "target": counts["TARGET"],
        "stop": counts["STOP"],
        "time_stop": counts["TIME_STOP"],
        "lifecycle_censored_by_reason": dict(sorted(censored.items())),
        "cost_complete_resolved_fills": counts["complete"],
        "cost_incomplete_resolved_fills_by_reason": dict(sorted(incomplete.items())),
    }


def _metric_packet(binary: list, terminal: list, net: list) -> dict[str, Any]:
    if binary:
        predictions, labels = zip(*binary)
        fill = {
            "status": "EVALUATED", "row_count": len(binary),
            "binary_brier": validated_brier_score(predictions, labels),
            "binary_logloss": validated_logloss(predictions, labels),
        }
    else:
        fill = {
            "status": "NOT_EVALUABLE_NO_ROWS", "row_count": 0,
            "binary_brier": None, "binary_logloss": None,
        }
    if terminal:
        brier = sum(
            sum((prob[state] - int(state == observed)) ** 2 for state in TERMINAL_STATES)
            for prob, observed in terminal
        ) / len(terminal)
        loss = sum(-math.log(max(1e-15, prob[observed])) for prob, observed in terminal)
        terminal_metric = {
            "status": "EVALUATED", "row_count": len(terminal),
            "multiclass_brier": brier, "multiclass_logloss": loss / len(terminal),
        }
    else:
        terminal_metric = {
            "status": "NOT_EVALUABLE_NO_ROWS", "row_count": 0,
            "multiclass_brier": None, "multiclass_logloss": None,
        }
    if net:
        errors = [prediction - actual for prediction, actual in net]
        net_metric = {
            "status": "EVALUATED", "row_count": len(net),
            "bias_r": sum(errors) / len(errors),
            "mae_r": sum(abs(error) for error in errors) / len(errors),
        }
    else:
        net_metric = {
            "status": "NOT_EVALUABLE_NO_ROWS", "row_count": 0,
            "bias_r": None, "mae_r": None,
        }
    return {
        "limit_fill_metrics": fill,
        "conditional_terminal_metrics": terminal_metric,
        "expected_net_metrics": net_metric,
    }


def _evaluate(rows: Sequence[Mapping[str, Any]], tables: Mapping) -> tuple[dict, tuple]:
    binary, terminal, net = [], [], []
    probability_status, net_status, backoff = Counter(), Counter(), Counter()
    for row in rows:
        prediction = _predict(tables, row)
        probability_status[prediction["probability_status"]] += 1
        net_status[prediction["expected_net_status"]] += 1
        backoff[f"fill:{prediction['fill_hierarchy_level']}"] += 1
        backoff[f"terminal:{prediction['terminal_hierarchy_level']}"] += 1
        backoff[f"expected_net:{prediction['expected_net_hierarchy_level']}"] += 1
        state = _state(row)
        if state is None:
            continue
        if row["proposed_order_type"] == "LIMIT" and prediction["p_fill"]:
            binary.append((prediction["p_fill"]["value"], int(state != "NO_FILL")))
        if state in TERMINAL_STATES and prediction["terminal_probabilities"]:
            terminal.append(
                ({key: value["value"] for key, value in prediction["terminal_probabilities"].items()}, state)
            )
        if prediction["expected_net_status"] == "EVALUATED_EXPECTED_NET":
            if state == "NO_FILL":
                actual = 0.0
            elif row["cost_label_status"] == "COMPLETE":
                actual = row["terminal_net_r"]
            else:
                continue
            net.append((prediction["expected_modelled_net_r_given_resolved"], actual))
    return ({
        "coverage": _coverage(rows),
        "probability_status_counts": dict(sorted(probability_status.items())),
        "expected_net_status_counts": dict(sorted(net_status.items())),
        "cell_backoff_counts": dict(sorted(backoff.items())),
        **_metric_packet(binary, terminal, net),
    }, (binary, terminal, net))


def _root_support(tables: Mapping) -> list[dict[str, Any]]:
    report = []
    for order_type in ("MARKET", "LIMIT"):
        cell = tables.get((0, (order_type,)), _blank_cell())
        report.append({
            "proposed_order_type": order_type,
            "resolved_attempts": cell["attempts"],
            "resolved_fills": cell["fills"],
            "additional_resolved_limit_attempts_required": (
                max(0, 100 - cell["attempts"]) if order_type == "LIMIT" else 0
            ),
            "additional_resolved_attempts_required_for_expected_net": max(
                0, 100 - cell["attempts"]
            ),
            "additional_resolved_fills_required": max(0, 30 - cell["fills"]),
        })
    return report


def _serialize_tables(tables: Mapping) -> list[dict[str, Any]]:
    output = []
    for (level, key), cell in sorted(tables.items()):
        if key[0] == "MARKET":
            p_fill, p_no = _fraction(1, 1), _fraction(0, 1)
        else:
            denominator = 2 * cell["attempts"] + 2
            p_fill = _fraction(2 * cell["fills"] + 1, denominator)
            p_no = _fraction(2 * cell["no_fill"] + 1, denominator)
        terminal_denominator = 2 * cell["fills"] + 3
        key_fields = {"proposed_order_type": key[0]}
        if level > 0:
            key_fields["origin_family"] = key[1]
        if level > 1:
            key_fields["utc_session"] = key[2]
        output.append({
            "hierarchy_level": HIERARCHY_LEVELS[level],
            "key": key_fields,
            "counts": {
                "resolved_attempts": cell["attempts"], "resolved_fills": cell["fills"],
                "no_fill": cell["no_fill"], "target": cell["states"]["TARGET"],
                "stop": cell["states"]["STOP"], "time_stop": cell["states"]["TIME_STOP"],
                "cost_complete_fills": cell["complete"],
                "cost_incomplete_fills_by_reason": dict(sorted(cell["incomplete"].items())),
            },
            "p_modelled_fill_given_resolved": p_fill,
            "p_modelled_no_fill_given_resolved": p_no,
            "fill_probability_status": (
                "EVALUATED_MARKET_EXACT"
                if key[0] == "MARKET"
                else (
                    "EVALUATED_OUTCOME_BASELINE"
                    if cell["attempts"] >= 100
                    else "OUT_OF_SUPPORT"
                )
            ),
            "p_terminal_given_resolved_fill": {
                state: _fraction(2 * cell["states"][state] + 1, terminal_denominator)
                for state in TERMINAL_STATES
            },
            "terminal_probability_status": (
                "EVALUATED_OUTCOME_BASELINE"
                if cell["fills"] >= 30
                else "OUT_OF_SUPPORT"
            ),
            "all_resolved_fills_cost_complete": cell["complete"] == cell["fills"],
            "complete_net_r_state_means": {
                state: (
                    sum(cell["net"][state]) / len(cell["net"][state])
                    if cell["net"][state]
                    else None
                )
                for state in TERMINAL_STATES
            },
            "complete_net_r_state_counts": {
                state: len(cell["net"][state]) for state in TERMINAL_STATES
            },
        })
    return output


def _tick_report(
    rows: Sequence[Mapping[str, Any]], lifecycle_values: set[str]
) -> dict[str, Any]:
    eligible = paired = fill_disagreement = terminal_disagreement = censored_pairs = 0
    confusion = Counter()
    gross_deltas, net_deltas = [], []
    for row in rows:
        symbol, tick = str(row.get("symbol") or ""), row.get("ordered_tick_sensitivity")
        eligible += int(symbol in TICK_COVERED_SYMBOLS)
        if tick is None:
            continue
        _require(symbol in TICK_COVERED_SYMBOLS, "tick result on uncovered symbol")
        _require(
            isinstance(tick, Mapping) and tick.get("evidence_class") == TICK_EVIDENCE_CLASS,
            "bad tick evidence class",
        )
        _require(
            all(tick.get(field) == row.get(field) for field in TICK_PAIR_FIELDS),
            "tick identical pair key mismatch",
        )
        tick_status = str(tick.get("lifecycle_label_status") or "")
        _require(tick_status in lifecycle_values, "bad tick lifecycle status")
        paired += 1
        primary = _state(row) or str(row["lifecycle_label_status"])
        other = RESOLVED_STATUS_TO_STATE.get(tick_status, tick_status)
        confusion[f"{primary}->{other}"] += 1
        if primary.startswith("CENSORED_") or other.startswith("CENSORED_"):
            censored_pairs += 1
            continue
        primary_fill, other_fill = primary in TERMINAL_STATES, other in TERMINAL_STATES
        fill_disagreement += int(primary_fill != other_fill)
        terminal_disagreement += int(primary_fill and other_fill and primary != other)
        if row.get("terminal_gross_r") is not None and tick.get("terminal_gross_r") is not None:
            gross_deltas.append(
                _finite(tick["terminal_gross_r"], "tick gross R")
                - _finite(row["terminal_gross_r"], "M1 gross R")
            )
        if (
            row.get("terminal_net_r") is not None
            and tick.get("terminal_net_r") is not None
            and row["cost_label_status"] == "COMPLETE"
            and tick.get("cost_label_status") == "COMPLETE"
        ):
            net_deltas.append(
                _finite(tick["terminal_net_r"], "tick net R")
                - _finite(row["terminal_net_r"], "M1 net R")
            )
    return {
        "role": "PAIRED_FOUR_SYMBOL_SENSITIVITY_ONLY_NOT_MODEL_ELIGIBILITY",
        "eligible_covered_symbol_occurrences": eligible,
        "paired_occurrences": paired,
        "missing_paired_occurrences": eligible - paired,
        "state_confusion_matrix": dict(sorted(confusion.items())),
        "fill_disagreement_count": fill_disagreement,
        "terminal_disagreement_count": terminal_disagreement,
        "noncomparable_censored_pair_count": censored_pairs,
        "gross_r_delta_complete_pair_count": len(gross_deltas),
        "gross_r_delta_sum_tick_minus_m1": (
            sum(gross_deltas) if len(gross_deltas) == paired else None
        ),
        "net_r_delta_complete_pair_count": len(net_deltas),
        "net_r_delta_sum_tick_minus_m1": (
            sum(net_deltas) if len(net_deltas) == paired else None
        ),
        "two_arm_treatment_delta_sign_rule_status": (
            "DEFERRED_TO_FROZEN_TWO_ARM_COMPARATOR"
        ),
        "model_count_or_probability_influence": False,
    }


def fit_wave21_development(
    rows: Sequence[Mapping[str, Any]],
    preregistration: Mapping[str, Any],
    *,
    development_freeze_utc: str,
) -> dict[str, Any]:
    _validate_preregistration(preregistration)
    rows = _normalize_rows(rows, preregistration)
    _require(
        {row["trading_day"] for row in rows} == set(DEVELOPMENT_DAYS),
        "all six development days must be represented in the synthetic evaluator",
    )
    freeze = _utc(development_freeze_utc, "development_freeze_utc")
    folds, pooled = [], ([], [], [])
    for number, (name, train_days, test_day) in enumerate(FROZEN_DEVELOPMENT_FOLDS):
        cutoff = (
            dt.datetime.combine(dt.date.fromisoformat(test_day), dt.time.min, tzinfo=_UTC)
            - dt.timedelta(hours=3)
        )
        train, excluded = [], Counter()
        for row in rows:
            if row["trading_day"] not in train_days or _state(row) is None:
                continue
            if row.get("label_available_utc") in (None, ""):
                excluded["label_available_utc_unknown"] += 1
            elif _utc(row["label_available_utc"], "label_available_utc") >= cutoff:
                excluded["label_not_strictly_before_effective_test_start"] += 1
            else:
                train.append(row)
        test = [row for row in rows if row["trading_day"] == test_day]
        audit_fold = TrainerFold(
            fold_id=number, test_start=test_day, test_end=test_day, embargo_days=0,
            train_row_keys=tuple(row["row_key"] for row in train),
            test_row_keys=tuple(row["row_key"] for row in test),
            n_purged_overlap=0, n_purged_unknown_span=0, status="evaluable",
        )
        leakage = audit_fold_leakage([audit_fold], rows)
        _require(leakage["clean"], f"{name} training leakage audit failed: {leakage}")
        tables = _tables(train)
        evaluation, raw = _evaluate(test, tables)
        for destination, values in zip(pooled, raw):
            destination.extend(values)
        folds.append({
            "fold_id": name, "candidate_train_days": list(train_days), "test_day": test_day,
            "effective_test_start_utc": cutoff.isoformat().replace("+00:00", "Z"),
            "training_row_count": len(train), "test_row_count": len(test),
            "availability_exclusions": dict(sorted(excluded.items())),
            "training_leakage_audit": leakage, "root_support": _root_support(tables),
            **evaluation,
        })
    final_rows, final_excluded = [], Counter()
    for row in rows:
        value = row.get("label_available_utc")
        if value in (None, ""):
            final_excluded["label_available_utc_unknown"] += 1
        elif _utc(value, "label_available_utc") > freeze:
            final_excluded["label_available_after_development_freeze"] += 1
        else:
            final_rows.append(row)
    final_tables = _tables(final_rows)
    result = {
        "schema": DEVELOPMENT_FIT_SCHEMA,
        "authority": {
            "input_binding_status": "UNBOUND_SYNTHETIC_ONLY_NOT_RESULT_BEARING",
            "cost_and_scale_authority": (
                "SYNTHETIC_INPUT_ONLY_REAL_ADAPTER_MUST_VERIFY_COST_AND_SCALE_RECEIPTS"
            ),
            "development_only": True, "unseen_or_reserve_data_accessed": False,
            "runtime_or_config_change": False, "broker_fill_truth": False,
            "primary_evidence_class": PRIMARY_EVIDENCE_CLASS,
            "estimator": "TWO_STAGE_JEFFREYS_HAND_COUNT_ONLY",
            "fold_planner_used": False, "learned_embargo_used": False,
            "model_or_feature_search_used": False,
        },
        "preregistration_payload_sha256": preregistration["payload_sha256"],
        "development_freeze_utc": freeze.isoformat().replace("+00:00", "Z"),
        "input_coverage": _coverage(rows),
        "expanding_folds": folds,
        "pooled_out_of_fold_metrics": _metric_packet(*pooled),
        "final_development_fit": {
            "admitted_row_count": len(final_rows),
            "exclusions": dict(sorted(final_excluded.items())),
            "coverage": _coverage(final_rows),
            "root_support": _root_support(final_tables),
            "count_tables": _serialize_tables(final_tables),
        },
        "ordered_tick_sensitivity": _tick_report(
            rows,
            set(
                preregistration["lifecycle_and_label_contract"][
                    "lifecycle_label_statuses"
                ]
            ),
        ),
    }
    result["payload_sha256"] = _canonical_hash(result)
    return result


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        exp_value = math.exp(-value)
        return 1.0 / (1.0 + exp_value)
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _logit(probability: float) -> float:
    bounded = max(1e-15, min(1.0 - 1e-15, probability))
    return math.log(bounded / (1.0 - bounded))


def _fit_platt(
    rows: list[tuple[float, int]],
    *,
    maximum_iterations: int = 100,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Fit sigmoid(intercept + slope * logit(score)) by unregularized MLE."""
    target_rate = sum(outcome for _, outcome in rows) / len(rows)
    intercept = _logit(target_rate)
    slope = 0.0
    converged = False
    for iteration in range(1, maximum_iterations + 1):
        gradient_0 = gradient_1 = 0.0
        information_00 = information_01 = information_11 = 0.0
        for probability, outcome in rows:
            predictor = _logit(probability)
            fitted = _sigmoid(intercept + slope * predictor)
            weight = fitted * (1.0 - fitted)
            residual = outcome - fitted
            gradient_0 += residual
            gradient_1 += residual * predictor
            information_00 += weight
            information_01 += weight * predictor
            information_11 += weight * predictor * predictor
        determinant = (
            information_00 * information_11 - information_01 * information_01
        )
        if determinant <= 1e-24:
            raise RuntimeError("singular Platt information matrix")
        delta_0 = (
            information_11 * gradient_0 - information_01 * gradient_1
        ) / determinant
        delta_1 = (
            -information_01 * gradient_0 + information_00 * gradient_1
        ) / determinant
        intercept += delta_0
        slope += delta_1
        if max(abs(delta_0), abs(delta_1)) < tolerance:
            converged = True
            break
    if not converged:
        raise RuntimeError("Platt fit did not converge")
    return {
        "intercept": intercept,
        "slope": slope,
        "iterations": iteration,
        "converged": converged,
    }


def _auc(rows: list[tuple[float, int]]) -> float | None:
    """Mann-Whitney AUC with average ranks for exact ties."""
    ordered = sorted(rows)
    positive_count = sum(outcome for _, outcome in ordered)
    negative_count = len(ordered) - positive_count
    if not positive_count or not negative_count:
        return None
    rank_sum = 0.0
    index = 0
    next_rank = 1
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = (next_rank + next_rank + end - index - 1) / 2.0
        rank_sum += average_rank * sum(outcome for _, outcome in ordered[index:end])
        next_rank += end - index
        index = end
    return (
        rank_sum - positive_count * (positive_count + 1) / 2.0
    ) / (positive_count * negative_count)


def _metrics(rows: list[tuple[float, int]]) -> dict[str, Any]:
    count = len(rows)
    epsilon = 1e-15
    target_rate = sum(outcome for _, outcome in rows) / count
    brier = sum((probability - outcome) ** 2 for probability, outcome in rows) / count
    logloss = sum(
        -(
            outcome * math.log(max(epsilon, min(1.0 - epsilon, probability)))
            + (1 - outcome)
            * math.log(max(epsilon, min(1.0 - epsilon, 1.0 - probability)))
        )
        for probability, outcome in rows
    ) / count
    ece = 0.0
    bins: list[dict[str, Any]] = []
    for index in range(10):
        lower = index / 10.0
        upper = (index + 1) / 10.0
        bucket = [
            (probability, outcome)
            for probability, outcome in rows
            if lower <= probability < upper or (index == 9 and probability == 1.0)
        ]
        if not bucket:
            continue
        mean_probability = sum(probability for probability, _ in bucket) / len(bucket)
        observed_frequency = sum(outcome for _, outcome in bucket) / len(bucket)
        ece += len(bucket) / count * abs(mean_probability - observed_frequency)
        bins.append(
            {
                "bin": f"{lower:.1f}-{upper:.1f}",
                "count": len(bucket),
                "mean_probability": mean_probability,
                "observed_frequency": observed_frequency,
            }
        )
    return {
        "row_count": count,
        "target_rate": target_rate,
        "Brier": brier,
        "logloss": logloss,
        "ECE_fixed_deciles": ece,
        "AUC": _auc(rows),
        "nonempty_reliability_bins": bins,
    }


def _metric_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key != "nonempty_reliability_bins"
    }


def _parse_overrides(values: Iterable[str]) -> dict[str, Path]:
    resolved = {day: Path(record["path"]) for day, record in LEDGERS.items()}
    for value in values:
        day, separator, path = value.partition("=")
        if not separator or day not in LEDGERS or not path:
            raise ValueError("--ledger must be DATE=/absolute/path for a bound date")
        resolved[day] = Path(path)
    return resolved


def _load_rows(paths: dict[str, Path]) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence: dict[str, Any] = {}
    by_day: dict[str, list[dict[str, Any]]] = {}
    global_occurrence_keys: set[str] = set()
    for day in LEDGERS:
        path = paths[day]
        if not path.is_file():
            raise FileNotFoundError(path)
        observed_sha = _sha256(path)
        expected_sha = LEDGERS[day]["sha256"]
        if observed_sha != expected_sha:
            raise ValueError(
                f"ledger sha256 mismatch for {day}: {observed_sha} != {expected_sha}"
            )
        stages: Counter[str] = Counter()
        terminals: Counter[str] = Counter()
        missed_rows: list[dict[str, Any]] = []
        occurrence_keys: set[str] = set()
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                row = json.loads(line)
                stage = str(row.get("stage") or "")
                stages[stage] += 1
                if stage != "missed":
                    continue
                identity = row.get("identity") or {}
                observables = row.get("observables") or {}
                key = str(identity.get("canonical_replay_candidate_instance_key") or "")
                if not key or key in occurrence_keys:
                    raise ValueError(
                        f"missing/duplicate counterfactual occurrence key at {day}:{line_number}"
                    )
                if key in global_occurrence_keys:
                    raise ValueError(
                        f"cross-day duplicate counterfactual occurrence key at {day}:{line_number}"
                    )
                occurrence_keys.add(key)
                global_occurrence_keys.add(key)
                terminal = str(observables.get("terminal_outcome") or "")
                if terminal not in KNOWN_TERMINALS:
                    raise ValueError(f"unknown terminal {terminal!r} at {day}:{line_number}")
                probability = observables.get("candidate_probability")
                if (
                    isinstance(probability, bool)
                    or not isinstance(probability, (int, float))
                    or not math.isfinite(float(probability))
                    or not 0.0 <= float(probability) <= 1.0
                ):
                    raise ValueError(f"invalid probability at {day}:{line_number}")
                terminals[terminal] += 1
                missed_rows.append(row)
        by_day[day] = missed_rows
        evidence[day] = {
            "path": str(path),
            "sha256": observed_sha,
            "stage_counts": dict(sorted(stages.items())),
            "missed_occurrence_count": len(missed_rows),
            "missed_occurrence_keys_unique": len(occurrence_keys) == len(missed_rows),
            "terminal_counts": dict(sorted(terminals.items())),
        }
    return evidence, by_day


def _labeled(rows: Iterable[dict[str, Any]]) -> list[tuple[float, int]]:
    output: list[tuple[float, int]] = []
    for row in rows:
        observables = row["observables"]
        terminal = observables["terminal_outcome"]
        if terminal == TARGET:
            output.append((float(observables["candidate_probability"]), 1))
        elif terminal == STOP:
            output.append((float(observables["candidate_probability"]), 0))
    return output


def _example(row: dict[str, Any]) -> dict[str, Any]:
    identity = row["identity"]
    observables = row["observables"]
    return {
        "occurrence_key": identity["canonical_replay_candidate_instance_key"],
        "trading_day": identity["trading_day"],
        "symbol": identity["symbol"],
        "side": identity["side"],
        "origin_family": identity["origin_family"],
        "candidate_probability": observables["candidate_probability"],
        "candidate_ev_r": observables["candidate_ev_r"],
        "candidate_expected_net_r": observables["candidate_expected_net_r"],
        "expected_cost_r": observables["expected_cost_r"],
        "raw_selector_action": observables["raw_selector_action"],
        "raw_selector_reason": observables["raw_selector_reason"],
        "terminal_outcome": observables["terminal_outcome"],
    }


def analyze(paths: dict[str, Path]) -> dict[str, Any]:
    evidence, missed_by_day = _load_rows(paths)
    labeled_by_day = {day: _labeled(rows) for day, rows in missed_by_day.items()}
    all_missed = [row for rows in missed_by_day.values() for row in rows]
    all_labeled = [row for rows in labeled_by_day.values() for row in rows]
    pooled_raw = _metrics(all_labeled)

    out_of_fold = {"raw": [], "training_rate_constant": [], "Platt": []}
    folds: list[dict[str, Any]] = []
    for heldout_day in LEDGERS:
        training = [
            row
            for day, rows in labeled_by_day.items()
            if day != heldout_day
            for row in rows
        ]
        heldout = labeled_by_day[heldout_day]
        training_target_rate = sum(outcome for _, outcome in training) / len(training)
        fit = _fit_platt(training)
        raw_predictions = list(heldout)
        constant_predictions = [
            (training_target_rate, outcome) for _, outcome in heldout
        ]
        platt_predictions = [
            (
                _sigmoid(
                    fit["intercept"] + fit["slope"] * _logit(probability)
                ),
                outcome,
            )
            for probability, outcome in heldout
        ]
        out_of_fold["raw"].extend(raw_predictions)
        out_of_fold["training_rate_constant"].extend(constant_predictions)
        out_of_fold["Platt"].extend(platt_predictions)
        raw_metrics = _metrics(raw_predictions)
        constant_metrics = _metrics(constant_predictions)
        platt_metrics = _metrics(platt_predictions)
        folds.append(
            {
                "heldout_day": heldout_day,
                "training_row_count": len(training),
                "training_target_rate": training_target_rate,
                "heldout_row_count": len(heldout),
                "heldout_target_rate": raw_metrics["target_rate"],
                "Platt_fit": fit,
                "raw_metrics": _metric_summary(raw_metrics),
                "training_rate_constant_metrics": _metric_summary(constant_metrics),
                "Platt_metrics": _metric_summary(platt_metrics),
                "Platt_reliability_bins": platt_metrics[
                    "nonempty_reliability_bins"
                ],
                "positive_slope": fit["slope"] > 0.0,
                "Platt_beats_constant_Brier": (
                    platt_metrics["Brier"] < constant_metrics["Brier"]
                ),
                "Platt_beats_constant_logloss": (
                    platt_metrics["logloss"] < constant_metrics["logloss"]
                ),
            }
        )

    success = all(
        fold["positive_slope"]
        and fold["Platt_beats_constant_Brier"]
        and fold["Platt_beats_constant_logloss"]
        for fold in folds
    )
    strict_rows = [
        row
        for row in all_missed
        if row["observables"]["terminal_outcome"] in {TARGET, STOP}
    ]
    stops = [
        row for row in strict_rows if row["observables"]["terminal_outcome"] == STOP
    ]
    targets = [
        row for row in strict_rows if row["observables"]["terminal_outcome"] == TARGET
    ]
    highest_probability_stop = max(
        stops, key=lambda row: row["observables"]["candidate_probability"]
    )
    closest_pair = min(
        ((abs(
            stop["observables"]["candidate_probability"]
            - target["observables"]["candidate_probability"]
        ), stop, target) for stop in stops for target in targets),
        key=lambda item: item[0],
    )
    censored_totals = Counter()
    for record in evidence.values():
        for terminal in CENSORED_TERMINALS:
            censored_totals[terminal] += record["terminal_counts"].get(terminal, 0)
    all_probabilities = [
        float(row["observables"]["candidate_probability"]) for row in all_missed
    ]
    all_candidate_evs = [
        float(row["observables"]["candidate_ev_r"]) for row in all_missed
    ]
    return {
        "schema": SCHEMA,
        "analysis_source_head": ANALYSIS_SOURCE_HEAD,
        "retained_ledger_producer_target": RETAINED_LEDGER_PRODUCER_TARGET,
        "authority": {
            "estate": "three_retained_0p20R_development_ledgers_only",
            "development_only_not_untouched_validation": True,
            "threshold_search_performed": False,
            "broker_live_or_config_mutation": False,
        },
        "analysis_contract": {
            "analysis_unit": "unique_missed_counterfactual_candidate_occurrence",
            "conditional_endpoint": (
                "P(target_before_stop | missed_counterfactual, entry_filled, "
                "terminal_resolved_as_target_or_stop)"
            ),
            "not_unconditional_candidate_win_rate": True,
            "positive_label": TARGET,
            "negative_label": STOP,
            "censored_terminal_classes": list(CENSORED_TERMINALS),
            "time_stop_censor_reason": (
                "retained_stage_observables_have_no_signed_terminal_R_or_close_mark"
            ),
            "Platt_model": (
                "sigmoid(intercept+slope*logit(raw_score)); unregularized_MLE"
            ),
            "folds": "leave_one_retained_day_out",
            "metrics": ["Brier", "logloss", "fixed_decile_ECE", "AUC"],
            "success_gate": (
                "all_folds_positive_slope_and_Platt_strictly_beats_training_rate_"
                "constant_on_Brier_and_logloss"
            ),
        },
        "bound_ledgers": evidence,
        "population": {
            "candidate_occurrences": sum(
                record["stage_counts"].get("candidate", 0)
                for record in evidence.values()
            ),
            "missed_counterfactual_occurrences": len(all_missed),
            "canonical_missed_occurrence_keys_globally_unique": (
                len(
                    {
                        row["identity"]["canonical_replay_candidate_instance_key"]
                        for row in all_missed
                    }
                )
                == len(all_missed)
            ),
            "strict_target_stop_evaluable_occurrences": len(all_labeled),
            "target_count": sum(outcome for _, outcome in all_labeled),
            "stop_count": len(all_labeled) - sum(
                outcome for _, outcome in all_labeled
            ),
            "censored_counts": dict(sorted(censored_totals.items())),
        },
        "raw_score_diagnostics": {
            "minimum": min(all_probabilities),
            "maximum": max(all_probabilities),
            "mean": sum(all_probabilities) / len(all_probabilities),
            "rows_at_or_above_0p58": sum(
                probability >= 0.58 for probability in all_probabilities
            ),
            "positive_candidate_ev_rows": sum(ev > 0.0 for ev in all_candidate_evs),
            "pooled_strict_metrics": pooled_raw,
        },
        "leave_one_day_out_folds": folds,
        "out_of_fold_metrics": {
            name: _metric_summary(_metrics(rows))
            for name, rows in out_of_fold.items()
        },
        "success_gate_passed": success,
        "disposition": (
            "do_not_install_Platt_or_use_action_support_as_outcome_probability;_"
            "source_require_geometry_bound_outcome_calibration"
            if not success
            else "calibration_gate_passed_development_only_not_promotion_authority"
        ),
        "examples": {
            "highest_probability_stop": _example(highest_probability_stop),
            "closest_opposite_outcome_score_pair": {
                "absolute_probability_delta": closest_pair[0],
                "stop": _example(closest_pair[1]),
                "target": _example(closest_pair[2]),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ledger",
        action="append",
        default=[],
        metavar="DATE=/ABSOLUTE/PATH",
        help="override a default retained-ledger path; expected SHA remains fixed",
    )
    parser.add_argument("--compact", action="store_true")
    arguments = parser.parse_args()
    result = analyze(_parse_overrides(arguments.ledger))
    if arguments.compact:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
