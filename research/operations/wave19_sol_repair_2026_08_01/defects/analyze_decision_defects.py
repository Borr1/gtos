#!/usr/bin/env python3
"""Bounded January/February reproduction for Session FD.

The script is intentionally path-explicit and refuses March.  February is used
only under the owner's 2026-08-01 attribution mandate.  It streams the source
ledgers once, joins candidate exposure only on candidate_id + decision_time_utc,
and never calls a replay, broker, or live surface.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterator


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from src.research_infra.train_engine import decision_semantics as SEM  # noqa: E402


OWNER_MANDATE = "owner_mandate_20260801"
TARGET_FALLBACK_SYMBOLS = frozenset({"GER40", "UKOIL_cash", "USOIL_cash"})
PLACEHOLDER_SPREADS = {
    "BTCUSD": 0.0001,
    "UKOIL_cash": 0.0258,
    "USOIL_cash": 0.027,
}
SCHEMA_FIELDS = (
    "pretrade_cost_packet_status",
    "commission_r_repair_status",
    "commission_r_broker_true_measured",
    "swap_horizon_repair_status",
    "final_blocker_class",
    "missed_package_replay_order_executable_final_blocker_class",
)


def num(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def is_scoreable(row: dict[str, Any]) -> bool:
    return bool(
        row.get("missed_opportunity_non_executable_diagnostic_scoreable") is True
        or row.get("missed_opportunity_r_scoreability_status")
        == "diagnostic_opportunity_r_scoreable"
    )


def candidate_key(row: dict[str, Any]) -> str | None:
    candidate_id = str(
        row.get("candidate_id") or row.get("selected_candidate_id") or ""
    ).strip()
    decision_time = str(
        row.get("decision_time_utc")
        or row.get("candidate_instance_time_utc")
        or row.get("decision_time")
        or ""
    ).strip()
    if not candidate_id or not decision_time:
        return None
    expected = f"{candidate_id}@@{decision_time}"
    declared = str(
        row.get("canonical_replay_candidate_instance_key")
        or row.get("selected_candidate_instance_key")
        or ""
    ).strip()
    if declared and declared != expected:
        raise ValueError(
            f"composite identity conflict: declared={declared!r} expected={expected!r}"
        )
    return expected


def assert_allowed_path(path: Path) -> None:
    text = str(path).lower()
    forbidden = ("2026-03", "march", "live-forward", "live_forward")
    if any(token in text for token in forbidden):
        raise ValueError(f"forbidden Session FD source path: {path}")
    if not path.is_file():
        raise FileNotFoundError(path)


class JsonlEvidence:
    def __init__(self, path: Path) -> None:
        assert_allowed_path(path)
        self.path = path
        self.sha256 = hashlib.sha256()
        self.rows = 0

    def __iter__(self) -> Iterator[dict[str, Any]]:
        with self.path.open("rb") as handle:
            for raw in handle:
                self.sha256.update(raw)
                if not raw.strip():
                    continue
                self.rows += 1
                yield json.loads(raw)

    def receipt(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "bytes": self.path.stat().st_size,
            "rows": self.rows,
            "sha256": self.sha256.hexdigest(),
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def _mean(total: float, count: int) -> float | None:
    return round(total / count, 9) if count else None


def _month_guard(label: str, decision_time: Any) -> None:
    text = str(decision_time or "")
    expected = "2026-01" if label == "january" else "2026-02"
    if text and not text.startswith(expected):
        raise ValueError(f"{label} source contains out-of-scope decision time {text!r}")


def scan_missed(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence = JsonlEvidence(path)
    scoreable_rows = 0
    schema_present = Counter()
    schema_non_null = Counter()
    scoreable_keys: set[str] = set()
    blocker_by_key: dict[str, Any] = {}

    fallback = {
        symbol: {
            "physical_rows": 0,
            "scoreable_rows": 0,
            "complete_component_rows": 0,
            "recorded_cost_r_sum": 0.0,
            "redecoded_cost_r_sum": 0.0,
            "recorded_minus_redecoded_r_sum": 0.0,
            "scoreable_recorded_net_r_sum": 0.0,
            "scoreable_redecoded_net_r_sum": 0.0,
            "scoreable_sign_flips": 0,
            "component_delta_min_r": None,
            "component_delta_max_r": None,
        }
        for symbol in sorted(TARGET_FALLBACK_SYMBOLS)
    }
    fallback_total = 0
    fallback_scoreable = 0
    placeholder = {
        symbol: {
            "template_spread_r": value,
            "physical_exact_value_rows": 0,
            "scoreable_exact_value_rows": 0,
            "emitted_quote_source_rows": 0,
        }
        for symbol, value in PLACEHOLDER_SPREADS.items()
    }

    exact_stop = exact_target = terminal_stop = terminal_target = 0
    terminal_missing = 0
    reinjection_keys: set[str] = set()
    reinjection_net: dict[str, float] = {}
    reinjection_physical = reinjection_scoreable = 0
    reinjection_net_sum = 0.0

    authority_classes = Counter()
    authority_reasons = Counter()
    authority_failure_payload_rows = 0
    authority_rows = 0

    ev = Counter()
    ev_delta_max = 0.0
    slippage = Counter()

    for row in evidence:
        _month_guard(label, row.get("decision_time_utc") or row.get("decision_time"))
        key = candidate_key(row)
        scoreable = is_scoreable(row)
        if scoreable:
            scoreable_rows += 1
            if key:
                scoreable_keys.add(key)
                blocker_by_key[key] = row.get(
                    "final_blocker_class",
                    row.get(
                        "missed_package_replay_order_executable_final_blocker_class"
                    ),
                )

        for field in SCHEMA_FIELDS:
            if field in row:
                schema_present[field] += 1
            if row.get(field) is not None:
                schema_non_null[field] += 1

        symbol = str(row.get("symbol") or "")
        cost = num(row.get("cost_r"))
        if symbol in TARGET_FALLBACK_SYMBOLS and cost is not None and math.isclose(
            cost, 0.12, rel_tol=0.0, abs_tol=1e-12
        ):
            fallback_total += 1
            stats = fallback[symbol]
            stats["physical_rows"] += 1
            if scoreable:
                fallback_scoreable += 1
                stats["scoreable_rows"] += 1
            components = [
                num(row.get("spread_r")),
                num(row.get("expected_slippage_r")),
                num(row.get("swap_cost_r")),
                num(row.get("commission_r")),
            ]
            if all(value is not None for value in components):
                redecoded = sum(value for value in components if value is not None)
                delta = cost - redecoded
                stats["complete_component_rows"] += 1
                stats["recorded_cost_r_sum"] += cost
                stats["redecoded_cost_r_sum"] += redecoded
                stats["recorded_minus_redecoded_r_sum"] += delta
                stats["component_delta_min_r"] = (
                    delta
                    if stats["component_delta_min_r"] is None
                    else min(stats["component_delta_min_r"], delta)
                )
                stats["component_delta_max_r"] = (
                    delta
                    if stats["component_delta_max_r"] is None
                    else max(stats["component_delta_max_r"], delta)
                )
                net = num(row.get("opportunity_net_proxy_r"))
                if scoreable and net is not None:
                    corrected_net = net + delta
                    stats["scoreable_recorded_net_r_sum"] += net
                    stats["scoreable_redecoded_net_r_sum"] += corrected_net
                    if (net > 0) != (corrected_net > 0):
                        stats["scoreable_sign_flips"] += 1

        template = PLACEHOLDER_SPREADS.get(symbol)
        spread = num(row.get("spread_r"))
        if template is not None and spread is not None and math.isclose(
            spread, template, rel_tol=0.0, abs_tol=1e-12
        ):
            placeholder[symbol]["physical_exact_value_rows"] += 1
            if scoreable:
                placeholder[symbol]["scoreable_exact_value_rows"] += 1
            if row.get("cost_quote_source") is not None:
                placeholder[symbol]["emitted_quote_source_rows"] += 1

        if scoreable:
            net = num(row.get("opportunity_net_proxy_r"))
            if net is not None and cost is not None:
                gross = net + cost
                if math.isclose(gross, -1.0, rel_tol=0.0, abs_tol=1e-9):
                    exact_stop += 1
                elif math.isclose(gross, 2.0, rel_tol=0.0, abs_tol=1e-9):
                    exact_target += 1
            terminal = str(row.get("terminal_outcome") or "")
            if terminal == "stop_reached_before_target":
                terminal_stop += 1
            elif terminal == "target_reached_before_stop":
                terminal_target += 1
            elif "terminal_outcome" not in row:
                terminal_missing += 1

        reinjected = bool(
            row.get("selector_action") == "reject"
            and row.get("effective_selector_action") == "open-reduced-risk"
            and row.get("scheduler_materialization_status")
            == "scheduler_option_materialized"
        )
        if reinjected:
            reinjection_physical += 1
            if key:
                reinjection_keys.add(key)
            if scoreable:
                reinjection_scoreable += 1
                net = num(row.get("opportunity_net_proxy_r"))
                if net is not None:
                    reinjection_net_sum += net
                    if key:
                        reinjection_net[key] = net

        reason = str(row.get("miss_reason") or "")
        authority_class = None
        if "package_positive_reduce_risk_signed_authority_invalid" in reason:
            authority_class = "signed_reduce_risk_authority_invalid"
        elif "numeric_disagreement_open_reduced_risk_disabled_by_config" in reason:
            authority_class = "numeric_disagreement_intentionally_disabled"
        elif "signed_package_new_entry_authority_surface_missing" in reason:
            authority_class = "signed_authority_surface_missing"
        if authority_class:
            authority_rows += 1
            authority_classes[authority_class] += 1
            authority_reasons[reason] += 1
            normalized = SEM.normalize_evidence_row(row)
            if normalized.get("package_authority_failure_capture_status") in {
                "captured",
                "captured_in_reason_only",
            }:
                authority_failure_payload_rows += 1

        candidate_ev = num(row.get("candidate_ev_r"))
        if candidate_ev is not None:
            ev["candidate_ev_rows"] += 1
            expected_net = num(row.get("expected_net_r"))
            if cost is not None and expected_net is not None:
                delta = abs(expected_net - (candidate_ev - cost))
                ev_delta_max = max(ev_delta_max, delta)
                if delta <= 1e-9:
                    ev["expected_net_equals_ev_minus_cost_rows"] += 1
            if num(row.get("policy_target_r")) == 2.0:
                ev["two_r_execution_geometry_rows"] += 1
            if row.get("origin_family") not in (None, ""):
                ev["origin_family_hash_input_rows"] += 1
        confidence = num(row.get("candidate_confidence"))
        defaulted = bool(
            row.get("confidence_missing_degraded_default_applied")
            or row.get("confidence_default_applied")
        )
        if confidence is not None and math.isclose(confidence, 0.55, abs_tol=1e-12):
            ev["confidence_0p55_rows"] += 1
            if defaulted:
                ev["confidence_0p55_explicit_default_rows"] += 1
        fill = num(row.get("execution_fill_probability"))
        if fill is not None and math.isclose(fill, 0.92, abs_tol=1e-12):
            ev["execution_fill_probability_0p92_rows"] += 1
        slip = num(row.get("expected_slippage_r"))
        if slip is not None and math.isclose(slip, 0.02, abs_tol=1e-12):
            slippage["flat_0p02_rows"] += 1
            if row.get("expected_slippage_source") is None:
                slippage["flat_0p02_source_dropped_rows"] += 1

    for stats in fallback.values():
        n = int(stats["physical_rows"])
        stats["recorded_mean_cost_r"] = _mean(stats["recorded_cost_r_sum"], n)
        stats["redecoded_mean_cost_r"] = _mean(stats["redecoded_cost_r_sum"], n)
        stats["recorded_minus_redecoded_mean_r"] = _mean(
            stats["recorded_minus_redecoded_r_sum"], n
        )
        score_n = int(stats["scoreable_rows"])
        stats["scoreable_recorded_mean_net_r"] = _mean(
            stats["scoreable_recorded_net_r_sum"], score_n
        )
        stats["scoreable_redecoded_mean_net_r"] = _mean(
            stats["scoreable_redecoded_net_r_sum"], score_n
        )
        for key, value in list(stats.items()):
            if isinstance(value, float):
                stats[key] = round(value, 9)

    exact_n = exact_stop + exact_target
    terminal_n = terminal_stop + terminal_target
    public = {
        "source": evidence.receipt(),
        "rows": evidence.rows,
        "scoreable_rows": scoreable_rows,
        "schema_field_presence": {
            field: {
                "key_present_rows": schema_present[field],
                "non_null_rows": schema_non_null[field],
            }
            for field in SCHEMA_FIELDS
        },
        "flat_0p12_cost": {
            "symbols": fallback,
            "physical_rows": fallback_total,
            "scoreable_rows": fallback_scoreable,
            "bias_sign_convention": (
                "recorded_minus_redecoded: positive means the 0.12 emitter "
                "fallback overcharged; negative means it undercharged"
            ),
        },
        "spread_placeholders": placeholder,
        "binary_populations": {
            "exact_contract_endpoint_population": {
                "definition": "scoreable net proxy + recorded cost exactly -1R or +2R",
                "n_stop": exact_stop,
                "n_target": exact_target,
                "hit_rate": round(exact_target / exact_n, 9) if exact_n else None,
            },
            "terminal_outcome_first_touch_population": {
                "definition": "scoreable row terminal_outcome stop/target label",
                "n_stop": terminal_stop,
                "n_target": terminal_target,
                "hit_rate": round(terminal_target / terminal_n, 9) if terminal_n else None,
                "rows_missing_terminal_outcome_key": terminal_missing,
            },
        },
        "selector_router_reinjection": {
            "definition": (
                "raw selector reject + effective open-reduced-risk + "
                "scheduler_option_materialized"
            ),
            "physical_rows": reinjection_physical,
            "scoreable_rows": reinjection_scoreable,
            "scoreable_net_r_sum": round(reinjection_net_sum, 9),
            "scoreable_mean_net_r": _mean(reinjection_net_sum, reinjection_scoreable),
        },
        "authority_gates": {
            "rows": authority_rows,
            "classes": _counter(authority_classes),
            "exact_miss_reasons": _counter(authority_reasons),
            "rows_with_machine_readable_failure_capture": authority_failure_payload_rows,
            "rows_missing_machine_readable_failure_capture": (
                authority_rows - authority_failure_payload_rows
            ),
        },
        "ev_and_defaults": {
            **_counter(ev),
            "expected_net_identity_max_abs_delta_r": round(ev_delta_max, 12),
            "slippage": _counter(slippage),
        },
    }
    internal = {
        "scoreable_keys": scoreable_keys,
        "blocker_by_key": blocker_by_key,
        "reinjection_keys": reinjection_keys,
        "reinjection_net": reinjection_net,
    }
    return public, internal


def scan_terminal_ledgers(
    root: Path, prefix: str, label: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    order_path = root / f"{prefix}_ORDER_LEDGER.jsonl"
    trade_path = root / f"{prefix}_TRADE_LEDGER.jsonl"
    orders = JsonlEvidence(order_path)
    trades = JsonlEvidence(trade_path)

    order_keys: set[str] = set()
    accepted_keys: set[str] = set()
    accepted_risk: dict[str, float] = defaultdict(float)
    order_stages = Counter()
    identity_incomplete = 0
    for row in orders:
        _month_guard(label, row.get("decision_time_utc") or row.get("decision_time"))
        key = candidate_key(row)
        if key is None:
            identity_incomplete += 1
            continue
        order_keys.add(key)
        stage = str(row.get("order_event_stage") or "")
        order_stages[stage] += 1
        if stage == "accepted_pending":
            accepted_keys.add(key)
            risk = num(
                row.get("final_approved_risk_pct") or row.get("approved_risk_pct")
            )
            if risk is not None:
                accepted_risk[key] += risk

    trade_keys: set[str] = set()
    trade_net: dict[str, float | None] = {}
    trade_headline_eligible: dict[str, bool] = {}
    close_sources = Counter()
    terminal_outcomes = Counter()
    close_reasons = Counter()
    semantic_source_status = Counter()
    cost_accounting = Counter()
    unscoreable: list[dict[str, Any]] = []
    flat_slippage = 0
    for row in trades:
        _month_guard(label, row.get("decision_time_utc") or row.get("decision_time"))
        key = candidate_key(row)
        if key is None:
            identity_incomplete += 1
            continue
        trade_keys.add(key)
        trade_net[key] = num(row.get("net_r"))
        eligible = row.get("headline_result_exclusion_reason") == "headline_result_eligible"
        trade_headline_eligible[key] = eligible
        close_sources[str(row.get("close_mark_source"))] += 1
        terminal_outcomes[str(row.get("terminal_outcome"))] += 1
        close_reasons[str(row.get("close_reason"))] += 1
        normalized = SEM.normalize_evidence_row(row, row_kind="trade")
        semantic_source_status[
            str(normalized.get("close_mark_source_semantics_status"))
        ] += 1
        cost_accounting[str(normalized.get("cost_accounting_status"))] += 1
        if (
            normalized.get("terminal_outcome_scoreability")
            == "unscoreable_diagnostic_only"
        ):
            unscoreable.append(
                {
                    "composite_candidate_key": key,
                    "legacy_close_reason": normalized.get("legacy_close_reason"),
                    "terminal_scoreability_status": normalized.get(
                        "terminal_scoreability_status"
                    ),
                    "recorded_net_r": normalized.get("recorded_net_r"),
                    "authoritative_net_r": normalized.get("authoritative_net_r"),
                }
            )
        slip = num(row.get("expected_slippage_r"))
        if slip is not None and math.isclose(slip, 0.02, abs_tol=1e-12):
            flat_slippage += 1

    public = {
        "order_source": orders.receipt(),
        "trade_source": trades.receipt(),
        "orders": {
            "rows": orders.rows,
            "unique_composite_candidate_instances": len(order_keys),
            "accepted_pending_unique_instances": len(accepted_keys),
            "event_stages": _counter(order_stages),
        },
        "trades": {
            "rows": trades.rows,
            "unique_composite_candidate_instances": len(trade_keys),
            "legacy_close_mark_source": _counter(close_sources),
            "terminal_outcome": _counter(terminal_outcomes),
            "close_reason": _counter(close_reasons),
            "repaired_close_source_semantics": _counter(semantic_source_status),
            "cost_accounting_status": _counter(cost_accounting),
            "flat_0p02_slippage_rows": flat_slippage,
            "terminally_unscoreable": unscoreable,
        },
        "composite_identity_incomplete_rows": identity_incomplete,
    }
    internal = {
        "order_keys": order_keys,
        "accepted_keys": accepted_keys,
        "accepted_risk": accepted_risk,
        "trade_keys": trade_keys,
        "trade_net": trade_net,
        "trade_headline_eligible": trade_headline_eligible,
    }
    return public, internal


def scan_compact(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    assert_allowed_path(path)
    keys: set[str] = set()
    blocker_by_key: dict[str, Any] = {}
    presence = Counter()
    non_null = Counter()
    templates = Counter()
    rows = 0
    digest = hashlib.sha256()
    with path.open("rb") as raw_handle:
        for chunk in iter(lambda: raw_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows += 1
            _month_guard(label, row.get("decision_time_utc"))
            key = candidate_key(row)
            if key:
                keys.add(key)
                blocker_by_key[key] = row.get("final_blocker_class")
            for field in SCHEMA_FIELDS:
                if field in row:
                    presence[field] += 1
                if row.get(field) is not None:
                    non_null[field] += 1
            if num(row.get("candidate_ev_r")) is not None:
                templates["candidate_ev_rows"] += 1
            if num(row.get("policy_target_r")) == 2.0:
                templates["two_r_execution_geometry_rows"] += 1
            confidence = num(row.get("candidate_confidence"))
            if confidence is not None and math.isclose(
                confidence, 0.55, abs_tol=1e-12
            ):
                templates["confidence_0p55_rows"] += 1
                if row.get("confidence_default_applied") is True:
                    templates["confidence_0p55_explicit_default_rows"] += 1
            fill = num(row.get("execution_fill_probability"))
            if fill is not None and math.isclose(fill, 0.92, abs_tol=1e-12):
                templates["execution_fill_probability_0p92_rows"] += 1
            slip = num(row.get("expected_slippage_r"))
            if slip is not None and math.isclose(slip, 0.02, abs_tol=1e-12):
                templates["flat_slippage_0p02_rows"] += 1
                if row.get("expected_slippage_source") is None:
                    templates["flat_slippage_source_missing_rows"] += 1
    public = {
        "source": {
            "path": str(path),
            "bytes": path.stat().st_size,
            "rows": rows,
            "sha256": digest.hexdigest(),
        },
        "schema_field_presence": {
            field: {
                "key_present_rows": presence[field],
                "non_null_rows": non_null[field],
            }
            for field in SCHEMA_FIELDS
        },
        "ev_and_default_templates": _counter(templates),
    }
    return public, {"keys": keys, "blocker_by_key": blocker_by_key}


def exposure_census(missed: dict[str, Any], terminal: dict[str, Any]) -> dict[str, Any]:
    targets = missed["reinjection_keys"]
    accepted = targets & terminal["accepted_keys"]
    traded = targets & terminal["trade_keys"]
    recorded_net = [
        terminal["trade_net"][key]
        for key in traded
        if terminal["trade_net"].get(key) is not None
    ]
    eligible_net = [
        terminal["trade_net"][key]
        for key in traded
        if terminal["trade_net"].get(key) is not None
        and terminal["trade_headline_eligible"].get(key)
    ]
    return {
        "join_contract": "candidate_id_plus_decision_time_utc_only",
        "reinjected_unique_instances": len(targets),
        "accepted_pending_unique_instances": len(accepted),
        "accepted_risk_pct_sum": round(
            sum(terminal["accepted_risk"].get(key, 0.0) for key in accepted), 9
        ),
        "filled_trade_unique_instances": len(traded),
        "recorded_trade_net_r_n": len(recorded_net),
        "recorded_trade_net_r_sum": round(sum(recorded_net), 9),
        "recorded_trade_net_r_mean": _mean(sum(recorded_net), len(recorded_net)),
        "headline_eligible_trade_net_r_n": len(eligible_net),
        "headline_eligible_trade_net_r_sum": round(sum(eligible_net), 9),
        "authority": "local_replay_only_no_broker_authority",
    }


def compact_parity(full: dict[str, Any], compact: dict[str, Any]) -> dict[str, Any]:
    full_keys = full["scoreable_keys"]
    compact_keys = compact["keys"]
    common = full_keys & compact_keys
    blocker_mismatches = sum(
        1
        for key in common
        if full["blocker_by_key"].get(key) != compact["blocker_by_key"].get(key)
    )
    return {
        "join_contract": "candidate_id_plus_decision_time_utc_only",
        "full_scoreable_unique_instances": len(full_keys),
        "compact_unique_instances": len(compact_keys),
        "missing_from_compact": len(full_keys - compact_keys),
        "extra_in_compact": len(compact_keys - full_keys),
        "canonical_blocker_value_mismatches_on_common_keys": blocker_mismatches,
        "key_drift_repair": (
            "normalize missed_package_replay_order_executable_final_blocker_class "
            "to final_blocker_class before projection"
        ),
    }


def validate_february_repair_receipt(
    path: Path, february: dict[str, Any]
) -> dict[str, Any]:
    assert_allowed_path(path)
    receipt = json.loads(path.read_text())
    report = receipt["repair_report"]["commission_broker_true_gated"]
    per_symbol = report["per_symbol"]
    checks: dict[str, bool] = {
        "all_calls_priced": report["calls"] == report["applied"],
        "zero_unpriced": report["unpriced"] == 0,
    }
    for symbol in sorted(TARGET_FALLBACK_SYMBOLS):
        observed = february["flat_0p12_cost"]["symbols"][symbol]["physical_rows"]
        checks[f"{symbol}_receipt_count_matches"] = per_symbol[symbol]["n"] == observed
        checks[f"{symbol}_receipt_commission_is_zero"] = math.isclose(
            float(per_symbol[symbol]["mean_r"]), 0.0, abs_tol=1e-15
        )
    status = "PASS_ARM_RECEIPT_BINDS_COMPONENT_REDECODE" if all(checks.values()) else "FAIL"
    if status == "FAIL":
        raise ValueError(f"February commission repair receipt binding failed: {checks}")
    return {
        "status": status,
        "owner_mandate": OWNER_MANDATE,
        "purpose": "February defect attribution only",
        "path": str(path),
        "sha256": sha256_file(path),
        "checks": checks,
        "conclusion": (
            "The arm receipt proves every commission lookup applied with zero "
            "unpriced calls and binds zero commission to all affected symbols. "
            "Complete row-level spread/slippage/swap/commission components may "
            "therefore re-decode the 0.12 emitter fallback for this arm only."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jan-root", type=Path, required=True)
    parser.add_argument("--jan-prefix", required=True)
    parser.add_argument("--jan-compact", type=Path, required=True)
    parser.add_argument("--feb-root", type=Path, required=True)
    parser.add_argument("--feb-prefix", required=True)
    parser.add_argument("--feb-compact", type=Path, required=True)
    parser.add_argument("--feb-repair-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()

    for path in (
        ns.jan_root / f"{ns.jan_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        ns.jan_compact,
        ns.feb_root / f"{ns.feb_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        ns.feb_compact,
        ns.feb_repair_receipt,
    ):
        assert_allowed_path(path)

    jan, jan_internal = scan_missed(
        ns.jan_root / f"{ns.jan_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        "january",
    )
    jan_terminal, jan_terminal_internal = scan_terminal_ledgers(
        ns.jan_root, ns.jan_prefix, "january"
    )
    jan_compact, jan_compact_internal = scan_compact(ns.jan_compact, "january")

    feb, feb_internal = scan_missed(
        ns.feb_root / f"{ns.feb_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        "february",
    )
    feb_terminal, feb_terminal_internal = scan_terminal_ledgers(
        ns.feb_root, ns.feb_prefix, "february"
    )
    feb_compact, feb_compact_internal = scan_compact(ns.feb_compact, "february")
    feb_receipt = validate_february_repair_receipt(ns.feb_repair_receipt, feb)

    result = {
        "schema": "gtos.wave19.session_fd.defect_reproduction.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "allowed_months": ["2026-01", "2026-02"],
            "forbidden": ["2026-03", "live-forward outcomes"],
            "february_provenance": OWNER_MANDATE,
            "february_use": "defect attribution only",
            "execution": "streaming read-only ledger census; no replay; no broker",
            "candidate_join": "candidate_id + decision_time_utc only",
        },
        "january": {
            "missed": jan,
            "terminal_ledgers": jan_terminal,
            "compact": jan_compact,
            "compact_parity": compact_parity(jan_internal, jan_compact_internal),
            "selector_router_reinjection_exposure": exposure_census(
                jan_internal, jan_terminal_internal
            ),
        },
        "february": {
            "provenance": OWNER_MANDATE,
            "missed": feb,
            "terminal_ledgers": feb_terminal,
            "compact": feb_compact,
            "compact_parity": compact_parity(feb_internal, feb_compact_internal),
            "selector_router_reinjection_exposure": exposure_census(
                feb_internal, feb_terminal_internal
            ),
            "commission_repair_receipt_binding": feb_receipt,
        },
        "verdict_boundaries": {
            "flat_0p12": (
                "arm-bound component re-decode is authoritative only because the "
                "February repair receipt proves all lookups applied; generic "
                "legacy rows remain non-authoritative without that binding"
            ),
            "spread_templates": (
                "affected rows are countable; decision-time spread bias is not "
                "recoverable without a historical predecision tick"
            ),
            "selector_reinjection": (
                "exposure is a local replay census, not broker authority and not "
                "a promotion result"
            ),
            "january_terminal_population": (
                "the January missed projection dropped terminal_outcome; its exact "
                "endpoint population is measurable but first-touch population is not"
            ),
        },
    }
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "out": str(ns.out),
                "jan_rows": jan["rows"],
                "feb_rows": feb["rows"],
                "feb_flat_0p12": feb["flat_0p12_cost"]["physical_rows"],
                "feb_receipt_binding": feb_receipt["status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
