#!/usr/bin/env python3
"""Certify the bounded B7.5 XAU ordered-tick replacement-value proof.

By default the analyzer compares the completed 24-symbol June R2 baseline with
the bound XAU-only ordered-tick replay.  It does not compare their headline
economics: the symbol universes differ, so the only admissible comparison is
the exact 07:30/07:45 XAU candidate chronology and its serialized authority
surfaces.  ``--full-portfolio-mode`` instead requires exact configured
24-symbol universes and exact terminal candidate/trade/missed identity
partitions before exposing same-day simulated R/cash/risk deltas.

Importing this module performs no reads or writes.  A completed target summary
is a hard precondition.  Successful execution emits summary, row ledger, and
dossier first, then writes the completion manifest last.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROUTE = Path(__file__).resolve().parent
REPO = ROUTE.parents[2]
PROFILE = "repaired_package_conversion_v3"
DAY = "2026-06-04"

DEFAULT_BASELINE_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_"
    "CAUSAL_STOP_HAZARD_RISK_EXPRESSION_TARGETED_R2"
)
DEFAULT_TARGET_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_06_04_"
    "XAU_ORDERED_TICK_REPLACEMENT_VALUE_TARGETED_R1"
)
DEFAULT_OUTPUT_PREFIX = "B7_5_XAU_ORDERED_TICK_REPLACEMENT_VALUE_PROOF"

EARLY_IDENTITY = (
    "broadorigin_27432b7392759e5a5dbe7658"
    "@@2026-06-04T07:30:00+00:00"
)
LATE_IDENTITY = (
    "broadorigin_730290b8b2d3fc07f83c9320"
    "@@2026-06-04T07:45:00+00:00"
)

BASELINE_SHARED_DIGEST = (
    "199fa37cdf521d4c21e00686763437a85549297b9a700ee3281512785eb95500"
)
BASELINE_SOURCE_DIGEST = (
    "396908d4392fcf78bda52f19b31792407ec01af3f47f42cf9870f59337aa3281"
)
TARGET_SHARED_DIGEST = (
    "2a87ca1f7b1c9bbd8e16d4ce1823073224be7cd9f22bb9b714330bde69322e00"
)
TARGET_SOURCE_DIGEST = (
    "59c93b3301fdd9f5a538bcfebf4071552fe94b4c90f0288ef643d7087edc86db"
)
PROFILE_DIGEST = (
    "fb84f087043ac89461be0ef592528eb49bd3ef3e12b775b75ebb94e11f81f67a"
)
TARGET_TICK_SHA256 = (
    "ca81d8319f3ca21f4955e5e70fa106a25dcb7e7f26e235895b3378a6b3f689fe"
)
TARGET_TICK_ROWS = 1_167_336

SUMMARY_SCHEMA = "gtos.b7_5.xau_ordered_tick_replacement_value.summary.v1"
ROW_SCHEMA = "gtos.b7_5.xau_ordered_tick_replacement_value.row.v1"
MANIFEST_SCHEMA = (
    "gtos.b7_5.xau_ordered_tick_replacement_value.completion_manifest.v1"
)
FLOAT_TOLERANCE = 1e-8
RISK_BEARING_SELECTOR_ACTIONS = {"trade", "reduce-risk", "open-reduced-risk"}

IDENTITY_FIELDS = (
    "canonical_replay_candidate_instance_key",
    "candidate_instance_parity_key",
    "source_bound_replay_candidate_instance_key",
)


class ArtifactError(RuntimeError):
    """Raised when the analyzer cannot safely consume its inputs."""


@dataclass(frozen=True)
class AnalyzerConfig:
    artifact_root: Path = ROUTE
    baseline_prefix: str = DEFAULT_BASELINE_PREFIX
    target_prefix: str = DEFAULT_TARGET_PREFIX
    output_prefix: str = DEFAULT_OUTPUT_PREFIX
    day: str = DAY
    early_identity: str = EARLY_IDENTITY
    late_identity: str = LATE_IDENTITY
    expected_baseline_shared_digest: str = BASELINE_SHARED_DIGEST
    expected_baseline_source_digest: str = BASELINE_SOURCE_DIGEST
    expected_target_shared_digest: str = TARGET_SHARED_DIGEST
    expected_target_source_digest: str = TARGET_SOURCE_DIGEST
    expected_profile_digest: str = PROFILE_DIGEST
    expected_tick_sha256: str = TARGET_TICK_SHA256
    expected_tick_rows: int = TARGET_TICK_ROWS
    full_portfolio_mode: bool = False


@dataclass
class JsonlScan:
    path: Path
    sha256: str
    byte_count: int
    row_count: int
    rows: list[dict[str, Any]]
    matches: dict[str, list[dict[str, Any]]]
    identity_counts: Counter[str]
    missing_identity_rows: int

    def metadata(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "row_count": self.row_count,
            "identity_count": len(self.identity_counts),
            "missing_identity_rows": self.missing_identity_rows,
        }


@dataclass
class Surface:
    label: str
    prefix: str
    summary: dict[str, Any]
    summary_meta: dict[str, Any]
    trades: JsonlScan
    missed: JsonlScan
    scorecards: JsonlScan
    orders: JsonlScan
    oracle: JsonlScan
    sources: JsonlScan


def canonical_json_bytes(payload: Any) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(16 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json_object(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.is_file():
        raise ArtifactError(f"missing_json_artifact:{path}")
    raw = path.read_bytes()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArtifactError(f"invalid_json_artifact:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise ArtifactError(f"json_artifact_not_object:{path}")
    return payload, {
        "path": str(path),
        "sha256": sha256_bytes(raw),
        "byte_count": len(raw),
    }


def identity_key(row: Mapping[str, Any]) -> str:
    for field in IDENTITY_FIELDS:
        value = str(row.get(field) or "").strip()
        if value:
            return value
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc") or row.get("decision_time") or ""
    ).strip()
    return f"{candidate_id}@@{decision_time}" if candidate_id or decision_time else ""


def scan_jsonl(
    path: Path,
    *,
    capture_identities: set[str],
    retain_all: bool = False,
) -> JsonlScan:
    if not path.is_file():
        raise ArtifactError(f"missing_jsonl_artifact:{path}")
    digest = hashlib.sha256()
    byte_count = 0
    row_count = 0
    rows: list[dict[str, Any]] = []
    matches = {key: [] for key in sorted(capture_identities)}
    identity_counts: Counter[str] = Counter()
    missing_identity_rows = 0
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            digest.update(raw_line)
            byte_count += len(raw_line)
            if not raw_line.strip():
                continue
            row_count += 1
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ArtifactError(f"invalid_jsonl:{path}:{line_number}:{exc}") from exc
            if not isinstance(row, dict):
                raise ArtifactError(f"jsonl_row_not_object:{path}:{line_number}")
            if retain_all:
                rows.append(row)
            key = identity_key(row)
            if key:
                identity_counts[key] += 1
            else:
                missing_identity_rows += 1
            if key in matches:
                matches[key].append(row)
    return JsonlScan(
        path=path,
        sha256=digest.hexdigest(),
        byte_count=byte_count,
        row_count=row_count,
        rows=rows,
        matches=matches,
        identity_counts=identity_counts,
        missing_identity_rows=missing_identity_rows,
    )


def artifact_path(root: Path, prefix: str, suffix: str) -> Path:
    return root / f"{prefix}_{suffix}"


def validate_prefix(prefix: str) -> None:
    if not prefix or Path(prefix).name != prefix or prefix in {".", ".."}:
        raise ArtifactError(f"invalid_artifact_prefix:{prefix}")


def completed_summary(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not path.is_file():
        raise ArtifactError(f"{label}_summary_incomplete:missing:{path}")
    summary, meta = read_json_object(path)
    complete = bool(
        summary.get("status") == "broad_live_as_if_replay_materialized_broker_live_closed"
        and summary.get("terminal_execution_materialized") is True
        and summary.get("terminal_execution_materialization_status")
        == "terminal_execution_ledgers_materialized"
        and isinstance(summary.get("artifact_materialization_status"), Mapping)
        and summary["artifact_materialization_status"].get("summary") == "materialized"
        and summary["artifact_materialization_status"].get("trade") == "materialized"
        and summary["artifact_materialization_status"].get("missed")
        == "materialized_compact_missed_opportunity_ledger"
        and summary["artifact_materialization_status"].get("source") == "materialized"
    )
    if not complete:
        raise ArtifactError(f"{label}_summary_incomplete:not_final:{path}")
    return summary, meta


def load_surface(config: AnalyzerConfig, label: str, prefix: str) -> Surface:
    validate_prefix(prefix)
    root = config.artifact_root
    summary, summary_meta = completed_summary(
        artifact_path(root, prefix, "SUMMARY.json"), label
    )
    captures = {config.early_identity, config.late_identity}
    return Surface(
        label=label,
        prefix=prefix,
        summary=summary,
        summary_meta=summary_meta,
        trades=scan_jsonl(
            artifact_path(root, prefix, "TRADE_LEDGER.jsonl"),
            capture_identities=captures,
            retain_all=True,
        ),
        missed=scan_jsonl(
            artifact_path(root, prefix, "MISSED_OPPORTUNITY_LEDGER.jsonl"),
            capture_identities=captures,
        ),
        scorecards=scan_jsonl(
            artifact_path(root, prefix, "SCORECARD_LEDGER.jsonl"),
            capture_identities=captures,
        ),
        orders=scan_jsonl(
            artifact_path(root, prefix, "ORDER_LEDGER.jsonl"),
            capture_identities=captures,
        ),
        oracle=scan_jsonl(
            artifact_path(root, prefix, "ORDERED_PATH_ORACLE_LEDGER.jsonl"),
            capture_identities=captures,
        ),
        sources=scan_jsonl(
            artifact_path(root, prefix, "SOURCE_UNIVERSE_LEDGER.jsonl"),
            capture_identities=set(),
            retain_all=True,
        ),
    )


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def first_number(row: Mapping[str, Any], fields: Sequence[str]) -> float | None:
    for field in fields:
        parsed = number(row.get(field))
        if parsed is not None:
            return parsed
    return None


def fnum(row: Mapping[str, Any], fields: Sequence[str]) -> float:
    parsed = first_number(row, fields)
    return parsed if parsed is not None else 0.0


def rounded(value: float) -> float:
    return round(value, 8)


def parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def trade_rollup(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    scoreable = [
        row
        for row in materialized
        if row.get("terminal_r_scoreable") is True
        and first_number(row, ("net_r", "net_proxy_r")) is not None
    ]
    unscoreable = [row for row in materialized if row not in scoreable]
    headline = [row for row in scoreable if row.get("headline_result_eligible") is True]
    scoreable_net = [fnum(row, ("net_r", "net_proxy_r")) for row in scoreable]
    headline_net = [fnum(row, ("net_r", "net_proxy_r")) for row in headline]
    return {
        "physical_trade_rows": len(materialized),
        "physical_scoreable_trade_rows": len(scoreable),
        "physical_unscoreable_trade_rows": len(unscoreable),
        "physical_win_count": sum(value > 0 for value in scoreable_net),
        "physical_loss_count": sum(value < 0 for value in scoreable_net),
        "physical_flat_count": sum(value == 0 for value in scoreable_net),
        "physical_net_r": rounded(sum(scoreable_net)),
        "physical_gross_r": rounded(sum(fnum(row, ("gross_r",)) for row in scoreable)),
        "physical_final_r": rounded(sum(fnum(row, ("final_r",)) for row in scoreable)),
        "physical_cash_pnl": rounded(
            sum(fnum(row, ("pnl_cash", "cash_pnl")) for row in scoreable)
        ),
        "physical_risk_cash": rounded(
            sum(fnum(row, ("risk_cash",)) for row in materialized)
        ),
        "physical_risk_pct": rounded(
            sum(fnum(row, ("risk_pct",)) for row in materialized)
        ),
        "physical_scoreable_expected_cost_r": rounded(
            sum(fnum(row, ("expected_cost_r",)) for row in scoreable)
        ),
        "physical_unscoreable_expected_cost_r": rounded(
            sum(fnum(row, ("expected_cost_r",)) for row in unscoreable)
        ),
        "physical_expected_cost_r": rounded(
            sum(fnum(row, ("expected_cost_r",)) for row in materialized)
        ),
        "headline_trade_rows": len(headline),
        "headline_win_count": sum(value > 0 for value in headline_net),
        "headline_loss_count": sum(value < 0 for value in headline_net),
        "headline_flat_count": sum(value == 0 for value in headline_net),
        "headline_net_r": rounded(sum(headline_net)),
        "headline_gross_r": rounded(
            sum(fnum(row, ("gross_r",)) for row in headline)
        ),
        "headline_final_r": rounded(
            sum(fnum(row, ("final_r",)) for row in headline)
        ),
        "headline_cash_pnl": rounded(
            sum(fnum(row, ("pnl_cash", "cash_pnl")) for row in headline)
        ),
    }


def values_match(actual: Any, declared: Any) -> bool:
    actual_number = number(actual)
    declared_number = number(declared)
    if actual_number is not None and declared_number is not None:
        return math.isclose(
            actual_number,
            declared_number,
            rel_tol=0.0,
            abs_tol=FLOAT_TOLERANCE,
        )
    return actual == declared


def physical_parity(surface: Surface) -> dict[str, Any]:
    rollup = trade_rollup(surface.trades.rows)
    stats_rows = [
        row
        for row in surface.summary.get("split_profile_stats", [])
        if isinstance(row, Mapping) and row.get("profile") == PROFILE
    ]
    stats = stats_rows[0] if len(stats_rows) == 1 else {}
    comparisons: list[dict[str, Any]] = []
    for metric, actual in rollup.items():
        if metric == "physical_trade_rows":
            declared = surface.summary.get("trade_rows")
        elif metric == "headline_cash_pnl":
            declared = stats.get("cash_pnl")
        else:
            declared = stats.get(metric)
        comparisons.append(
            {
                "metric": metric,
                "ledger_value": actual,
                "summary_value": declared,
                "match": values_match(actual, declared),
            }
        )
    row_count_bindings = {
        "trade_rows": surface.trades.row_count,
        "missed_opportunity_rows": surface.missed.row_count,
        "scorecard_rows": surface.scorecards.row_count,
        "order_rows": surface.orders.row_count,
        "oracle_rows": surface.oracle.row_count,
        "source_universe_rows": surface.sources.row_count,
    }
    row_count_checks = [
        {
            "metric": field,
            "ledger_value": actual,
            "summary_value": surface.summary.get(field),
            "match": values_match(actual, surface.summary.get(field)),
        }
        for field, actual in row_count_bindings.items()
    ]
    candidate_partition_check = {
        "metric": "candidate_rows_equals_trade_plus_missed",
        "ledger_value": surface.trades.row_count + surface.missed.row_count,
        "summary_value": surface.summary.get("candidate_rows"),
        "match": values_match(
            surface.trades.row_count + surface.missed.row_count,
            surface.summary.get("candidate_rows"),
        ),
    }
    declared_contract = surface.summary.get(
        "physical_trade_summary_serialized_ledger_parity_contract"
    )
    declared_contract_valid = bool(
        isinstance(declared_contract, Mapping)
        and declared_contract.get("serialized_trade_ledger_is_physical_summary_authority")
        is True
        and declared_contract.get("canonical_result_ledger_normalization_before_summary")
        is True
        and declared_contract.get("scoreable_unscoreable_cost_partition_required")
        is True
    )
    all_checks = [*comparisons, *row_count_checks, candidate_partition_check]
    return {
        "valid": bool(
            len(stats_rows) == 1
            and declared_contract_valid
            and all(item["match"] for item in all_checks)
        ),
        "profile_stats_row_count": len(stats_rows),
        "declared_parity_contract_valid": declared_contract_valid,
        "recomputed": rollup,
        "metric_checks": comparisons,
        "row_count_checks": row_count_checks,
        "candidate_partition_check": candidate_partition_check,
    }


def identity_set_sha256(values: Iterable[str]) -> str:
    payload = "".join(f"{value}\n" for value in sorted(set(values))).encode("utf-8")
    return sha256_bytes(payload)


def terminal_identity_partition_proof(
    baseline: Surface,
    target: Surface,
) -> dict[str, Any]:
    baseline_trade = set(baseline.trades.identity_counts)
    baseline_missed = set(baseline.missed.identity_counts)
    target_trade = set(target.trades.identity_counts)
    target_missed = set(target.missed.identity_counts)
    baseline_candidate = baseline_trade | baseline_missed
    target_candidate = target_trade | target_missed
    baseline_trade_rows = {
        identity_key(row): row for row in baseline.trades.rows if identity_key(row)
    }
    target_trade_rows = {
        identity_key(row): row for row in target.trades.rows if identity_key(row)
    }
    shared_trades = sorted(baseline_trade & target_trade)
    scoreability_enrichments = [
        key
        for key in shared_trades
        if baseline_trade_rows[key].get("terminal_r_scoreable") is False
        and target_trade_rows[key].get("terminal_r_scoreable") is True
    ]
    scoreability_regressions = [
        key
        for key in shared_trades
        if baseline_trade_rows[key].get("terminal_r_scoreable") is True
        and target_trade_rows[key].get("terminal_r_scoreable") is not True
    ]
    duplicate_samples = {
        "baseline_trade": sorted(
            key for key, count in baseline.trades.identity_counts.items() if count != 1
        )[:25],
        "baseline_missed": sorted(
            key for key, count in baseline.missed.identity_counts.items() if count != 1
        )[:25],
        "target_trade": sorted(
            key for key, count in target.trades.identity_counts.items() if count != 1
        )[:25],
        "target_missed": sorted(
            key for key, count in target.missed.identity_counts.items() if count != 1
        )[:25],
    }
    checks = {
        "all_terminal_rows_have_identity": all(
            scan.missing_identity_rows == 0
            for scan in (
                baseline.trades,
                baseline.missed,
                target.trades,
                target.missed,
            )
        ),
        "all_terminal_identities_unique_within_ledgers": not any(
            duplicate_samples.values()
        ),
        "baseline_trade_missed_partition_disjoint": not (
            baseline_trade & baseline_missed
        ),
        "target_trade_missed_partition_disjoint": not (target_trade & target_missed),
        "candidate_identity_partition_exact": baseline_candidate == target_candidate,
        "trade_identity_partition_exact": baseline_trade == target_trade,
        "missed_identity_partition_exact": baseline_missed == target_missed,
        "terminal_scoreability_has_no_regression": not scoreability_regressions,
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "counts": {
            "baseline_candidate": len(baseline_candidate),
            "target_candidate": len(target_candidate),
            "baseline_trade": len(baseline_trade),
            "target_trade": len(target_trade),
            "baseline_missed": len(baseline_missed),
            "target_missed": len(target_missed),
        },
        "hashes": {
            "baseline_candidate": identity_set_sha256(baseline_candidate),
            "target_candidate": identity_set_sha256(target_candidate),
            "baseline_trade": identity_set_sha256(baseline_trade),
            "target_trade": identity_set_sha256(target_trade),
            "baseline_missed": identity_set_sha256(baseline_missed),
            "target_missed": identity_set_sha256(target_missed),
        },
        "candidate_added": sorted(target_candidate - baseline_candidate)[:100],
        "candidate_removed": sorted(baseline_candidate - target_candidate)[:100],
        "trade_added": sorted(target_trade - baseline_trade)[:100],
        "trade_removed": sorted(baseline_trade - target_trade)[:100],
        "missed_added": sorted(target_missed - baseline_missed)[:100],
        "missed_removed": sorted(baseline_missed - target_missed)[:100],
        "terminal_scoreability_enrichment_count": len(scoreability_enrichments),
        "terminal_scoreability_enrichment_identities": scoreability_enrichments[:100],
        "terminal_scoreability_regression_count": len(scoreability_regressions),
        "terminal_scoreability_regression_identities": scoreability_regressions[:100],
        "duplicate_identity_samples": duplicate_samples,
        "contract": (
            "exact terminal candidate/trade/missed identity partitions; terminal "
            "scoreability may enrich from false to true but may not regress"
        ),
    }
def summary_contract(
    surface: Surface,
    *,
    expected_shared_digest: str,
    expected_source_digest: str,
    expected_universe: Sequence[str],
) -> dict[str, Any]:
    binding = surface.summary.get("b7_5_contract_binding")
    shared = surface.summary.get("shared_execution_contract")
    invariance = surface.summary.get("source_authority_chunk_invariance_contract")
    binding = binding if isinstance(binding, Mapping) else {}
    shared = shared if isinstance(shared, Mapping) else {}
    invariance = invariance if isinstance(invariance, Mapping) else {}
    actual_sources = binding.get("actual_source_plan_digests_sha256")
    universe = surface.summary.get("active_replay_symbol_universe")
    checks = {
        "binding_valid": binding.get("valid") is True,
        "binding_required": binding.get("required") is True,
        "actual_shared_digest_exact": binding.get(
            "actual_shared_execution_contract_digest_sha256"
        )
        == expected_shared_digest,
        "expected_shared_digest_exact": binding.get(
            "expected_shared_execution_contract_digest_sha256"
        )
        == expected_shared_digest,
        "shared_contract_digest_exact": shared.get(
            "shared_execution_contract_digest_sha256"
        )
        == expected_shared_digest,
        "actual_source_digest_exact": actual_sources == [expected_source_digest],
        "expected_source_digest_exact": binding.get(
            "expected_source_plan_digest_sha256"
        )
        == expected_source_digest,
        "profile_digest_exact": (
            isinstance(shared.get("effective_profile_config_hashes"), Mapping)
            and shared["effective_profile_config_hashes"].get(PROFILE)
            == surface.summary.get("shared_execution_contract", {})
            .get("effective_profile_config_hashes", {})
            .get(PROFILE)
        ),
        "symbol_universe_exact": universe == list(expected_universe),
        "source_plans_valid": invariance.get("all_source_plans_valid") is True,
        "chunk_source_plans_invariant": invariance.get(
            "all_chunk_source_plans_match_canonical"
        )
        is True,
        "broker_mutation_closed": surface.summary.get("broker_mutation_enabled") is False,
        "live_broker_authority_closed": surface.summary.get("live_broker_authority")
        is False,
        "final_selection_closed": surface.summary.get("final_selection_claim") is False,
    }
    actual_profile = (
        shared.get("effective_profile_config_hashes", {}).get(PROFILE)
        if isinstance(shared.get("effective_profile_config_hashes"), Mapping)
        else None
    )
    checks["profile_digest_exact"] = actual_profile == PROFILE_DIGEST
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "expected_shared_digest": expected_shared_digest,
        "actual_shared_digest": shared.get("shared_execution_contract_digest_sha256"),
        "expected_source_digest": expected_source_digest,
        "actual_source_digests": actual_sources,
        "expected_profile_digest": PROFILE_DIGEST,
        "actual_profile_digest": actual_profile,
        "expected_symbol_universe": list(expected_universe),
        "actual_symbol_universe": universe,
    }


def resolve_artifact_path(value: Any) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else REPO / path


def file_sha_and_rows(path: Path) -> tuple[str, int, int]:
    if not path.is_file():
        return "", 0, 0
    digest = hashlib.sha256()
    rows = 0
    byte_count = 0
    with path.open("rb") as handle:
        for raw_line in handle:
            digest.update(raw_line)
            byte_count += len(raw_line)
            if raw_line.strip():
                rows += 1
    return digest.hexdigest(), rows, byte_count


def selected_tick_integrity(
    target: Surface,
    config: AnalyzerConfig,
    required_until: datetime | None,
) -> dict[str, Any]:
    candidates = [
        row
        for row in target.sources.rows
        if str(row.get("symbol") or "").upper() == "XAUUSD"
        and str(row.get("timeframe") or "").upper() == "TICK"
        and str(row.get("sha256") or row.get("source_sha256") or "")
        == config.expected_tick_sha256
    ]
    if len(candidates) != 1:
        return {
            "valid": False,
            "candidate_row_count": len(candidates),
            "expected_tick_sha256": config.expected_tick_sha256,
            "checks": {"exact_expected_tick_row_unique": False},
        }
    row = candidates[0]
    tick_path = resolve_artifact_path(row.get("path") or row.get("source_path"))
    manifest_path = resolve_artifact_path(row.get("manifest_path"))
    actual_sha, actual_rows, byte_count = file_sha_and_rows(tick_path)
    manifest: dict[str, Any] = {}
    manifest_meta: dict[str, Any] = {
        "path": str(manifest_path),
        "present": manifest_path.is_file(),
    }
    if manifest_path.is_file():
        manifest, loaded_meta = read_json_object(manifest_path)
        manifest_meta.update(loaded_meta)
    files = manifest.get("files")
    manifest_xau_rows = [
        value
        for value in (files.values() if isinstance(files, Mapping) else [])
        if isinstance(value, Mapping)
        and str(value.get("file_symbol") or "").upper() == "XAUUSD"
        and str(value.get("timeframe") or "").upper() == "TICK"
        and str(value.get("sha256") or "") == config.expected_tick_sha256
    ]
    manifest_xau = manifest_xau_rows[0] if len(manifest_xau_rows) == 1 else {}
    manifest_tick_path = resolve_artifact_path(manifest_xau.get("path"))
    start = parse_time(row.get("start_utc"))
    end = parse_time(row.get("end_utc"))
    early_decision = parse_time(config.early_identity.rsplit("@@", 1)[-1])
    coverage_end = required_until or parse_time(config.late_identity.rsplit("@@", 1)[-1])
    checks = {
        "exact_expected_tick_row_unique": len(candidates) == 1,
        "selected_priority_tick_source": (
            row.get("status") == "selected_priority_tick_source"
            and row.get("selected_status") == "selected_priority_tick_source"
        ),
        "ordered_tick_truth_satisfied": row.get("ordered_tick_truth_satisfied") is True,
        "source_truth_scope_exact": row.get("source_truth_scope")
        == "ordered_price_path_only_not_broker_order_lifecycle_truth",
        "broker_lifecycle_truth_closed": row.get("broker_lifecycle_truth_satisfied")
        is False,
        "live_broker_authority_closed": row.get("live_broker_authority") is False,
        "broker_mutation_closed": row.get("broker_mutation_enabled") is False,
        "declared_sha_exact": str(row.get("sha256") or row.get("source_sha256") or "")
        == config.expected_tick_sha256,
        "declared_rows_exact": int(row.get("rows") or row.get("row_count") or -1)
        == config.expected_tick_rows,
        "tick_file_present": tick_path.is_file(),
        "tick_file_sha_exact": actual_sha == config.expected_tick_sha256,
        "tick_file_rows_exact": actual_rows == config.expected_tick_rows,
        "tick_range_covers_required_chronology": bool(
            start
            and end
            and early_decision
            and coverage_end
            and start <= early_decision
            and end >= coverage_end
        ),
        "manifest_present": manifest_path.is_file(),
        "manifest_schema_exact": manifest.get("schema_version")
        == "mt5_research_tick_export_v1",
        "manifest_read_only": manifest.get("read_only") is True,
        "manifest_errors_empty": manifest.get("errors") == [],
        "manifest_xau_row_unique": len(manifest_xau_rows) == 1,
        "manifest_xau_sha_exact": manifest_xau.get("sha256")
        == config.expected_tick_sha256,
        "manifest_xau_rows_exact": int(
            manifest_xau.get("rows") or manifest_xau.get("row_count") or -1
        )
        == config.expected_tick_rows,
        "manifest_xau_path_exact": bool(
            manifest_xau and manifest_tick_path.resolve() == tick_path.resolve()
        ),
        "manifest_source_scope_exact": (
            isinstance(manifest.get("source_provenance"), Mapping)
            and manifest["source_provenance"].get("source_truth_scope")
            == "ordered_price_path_only_not_broker_order_lifecycle_truth"
        ),
    }
    return {
        "valid": all(checks.values()),
        "candidate_row_count": len(candidates),
        "checks": checks,
        "source_row": {
            "status": row.get("status"),
            "path": str(tick_path),
            "sha256": row.get("sha256") or row.get("source_sha256"),
            "rows": row.get("rows") or row.get("row_count"),
            "start_utc": row.get("start_utc"),
            "end_utc": row.get("end_utc"),
            "source_broker": row.get("source_broker"),
            "source_role": row.get("source_role"),
            "source_truth_scope": row.get("source_truth_scope"),
            "not_redacted_account_native": row.get("not_redacted_account_native"),
        },
        "physical_file": {
            "path": str(tick_path),
            "sha256": actual_sha or None,
            "row_count": actual_rows,
            "byte_count": byte_count,
        },
        "manifest": manifest_meta,
        "manifest_xau_row": dict(manifest_xau),
    }


def terminal_rows(surface: Surface, key: str) -> tuple[str, list[dict[str, Any]]]:
    trades = surface.trades.matches.get(key, [])
    missed = surface.missed.matches.get(key, [])
    if trades and missed:
        return "conflict_trade_and_missed", [*trades, *missed]
    if len(trades) == 1:
        return "trade", trades
    if len(missed) == 1:
        return "missed", missed
    if len(trades) > 1:
        return "duplicate_trade", trades
    if len(missed) > 1:
        return "duplicate_missed", missed
    return "missing", []


def compact_candidate_row(
    surface: Surface,
    key: str,
    expected_time: str,
) -> dict[str, Any]:
    disposition, rows = terminal_rows(surface, key)
    row = rows[0] if len(rows) == 1 else {}
    context = row.get("same_symbol_replay_exposure_context")
    context = context if isinstance(context, Mapping) else {}
    return {
        "surface": surface.label,
        "identity_key": key,
        "disposition": disposition,
        "terminal_row_count": len(rows),
        "identity_exact": identity_key(row) == key if row else False,
        "candidate_id": row.get("candidate_id"),
        "decision_time_utc": row.get("decision_time_utc") or row.get("decision_time"),
        "decision_time_exact": (
            parse_time(row.get("decision_time_utc") or row.get("decision_time"))
            == parse_time(expected_time)
            if row
            else False
        ),
        "symbol": row.get("symbol"),
        "side": row.get("side") or row.get("direction"),
        "selector_action": row.get("selector_action"),
        "raw_selector_action": row.get("raw_selector_action"),
        "effective_selector_action": row.get("effective_selector_action"),
        "effective_selector_reason": row.get("effective_selector_reason"),
        "pretrade_cost_packet_status": row.get("pretrade_cost_packet_status"),
        "cost_authority": row.get("cost_authority"),
        "cost_source_gap_status": row.get("cost_source_gap_status"),
        "candidate_cost_r_fallback_is_authority": row.get(
            "candidate_cost_r_fallback_is_authority"
        ),
        "broker_pretrade_cost_executable": row.get(
            "broker_pretrade_cost_executable"
        ),
        "broker_pretrade_cost_executable_block_reason": row.get(
            "broker_pretrade_cost_executable_block_reason"
        ),
        "scheduler_materialization_skip_reason": row.get(
            "scheduler_materialization_skip_reason"
        ),
        "scheduler_materialization_action_intent": row.get(
            "scheduler_materialization_action_intent"
        ),
        "scheduler_selection_disposition": row.get(
            "scheduler_selection_disposition"
        ),
        "simulated_trade_id": row.get("simulated_trade_id"),
        "entry_time_utc": row.get("entry_time_utc") or row.get("fill_time_utc"),
        "exit_time_utc": row.get("exit_time_utc") or row.get("close_time_utc"),
        "terminal_r_scoreable": row.get("terminal_r_scoreable"),
        "terminal_r_scoreability_status": row.get("terminal_r_scoreability_status"),
        "terminal_outcome": row.get("limit_first_terminal_outcome")
        or row.get("terminal_outcome"),
        "headline_result_eligible": row.get("headline_result_eligible"),
        "net_r": first_number(row, ("net_r", "net_proxy_r")),
        "final_r": number(row.get("final_r")),
        "cash_pnl": first_number(row, ("pnl_cash", "cash_pnl")),
        "risk_pct": number(row.get("risk_pct")),
        "miss_reason": row.get("miss_reason"),
        "missed_opportunity_r_scoreability_status": row.get(
            "missed_opportunity_r_scoreability_status"
        ),
        "diagnostic_opportunity_r": number(row.get("opportunity_net_proxy_r")),
        "same_symbol_lifecycle_action": row.get("same_symbol_lifecycle_action"),
        "same_symbol_exposure_status": row.get(
            "same_symbol_replay_exposure_context_status"
        ),
        "same_symbol_exposure_synthesized_empty": row.get(
            "same_symbol_replay_exposure_context_synthesized_empty"
        ),
        "same_side_open_count": context.get("same_side_open_count"),
        "same_side_open_ids": context.get("same_side_open_ids"),
        "same_side_open_risk_pct": context.get("same_side_open_risk_pct"),
        "package_final_blocker_class": row.get(
            "package_replay_order_executable_final_blocker_class"
        ),
        "package_final_blocker_reason": row.get(
            "package_replay_order_executable_final_blocker_reason"
        ),
        "scorecard_row_count": len(surface.scorecards.matches.get(key, [])),
        "order_event_row_count": len(surface.orders.matches.get(key, [])),
        "oracle_row_count": len(surface.oracle.matches.get(key, [])),
    }


def target_terminal_scoreability(target: Surface, key: str) -> dict[str, Any]:
    disposition, rows = terminal_rows(target, key)
    row = rows[0] if disposition == "trade" and len(rows) == 1 else {}
    authority = row.get("ordered_tick_truth_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    checks = {
        "early_identity_is_trade": disposition == "trade" and len(rows) == 1,
        "terminal_r_scoreable": row.get("terminal_r_scoreable") is True,
        "scoreability_status_ordered_tick": row.get("terminal_r_scoreability_status")
        == "ordered_tick_terminal_r_scoreable",
        "ordered_tick_final_r_authority": row.get("ordered_tick_final_r_authority")
        is True,
        "ordered_tick_truth_satisfied": row.get("ordered_tick_truth_satisfied") is True,
        "ordered_tick_truth_satisfied_for_terminal_r": row.get(
            "ordered_tick_truth_satisfied_for_terminal_r"
        )
        is True,
        "ordered_tick_source_satisfied": row.get("ordered_tick_truth_source_satisfied")
        is True,
        "ordered_tick_oracle_satisfied": row.get("ordered_tick_truth_oracle_satisfied")
        is True,
        "limit_first_tick_window_covers_candidate": row.get(
            "limit_first_tick_window_covers_candidate"
        )
        is True,
        "limit_first_tick_rows_positive": (
            number(row.get("limit_first_tick_query_rows_returned")) or 0
        )
        > 0,
        "limit_first_path_is_tick": row.get("limit_first_path_source") == "tick"
        and row.get("limit_first_path_source_timeframe") == "TICK",
        "truth_authority_is_tick": authority.get("source") == "tick"
        and authority.get("source_timeframe") == "TICK",
        "net_r_finite": first_number(row, ("net_r", "net_proxy_r")) is not None,
        "final_r_finite": number(row.get("final_r")) is not None,
        "cash_pnl_finite": first_number(row, ("pnl_cash", "cash_pnl")) is not None,
        "exit_time_present": parse_time(
            row.get("exit_time_utc") or row.get("close_time_utc")
        )
        is not None,
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "terminal_r_scoreability_status": row.get("terminal_r_scoreability_status"),
        "terminal_outcome": row.get("limit_first_terminal_outcome"),
        "net_r": first_number(row, ("net_r", "net_proxy_r")),
        "final_r": number(row.get("final_r")),
        "cash_pnl": first_number(row, ("pnl_cash", "cash_pnl")),
        "query_tick_rows": row.get("limit_first_tick_query_rows_returned"),
        "truth_authority": dict(authority),
    }


def prior_cost_block_precedence(row: Mapping[str, Any]) -> dict[str, Any]:
    block_reason = str(
        row.get("broker_pretrade_cost_executable_block_reason") or ""
    ).strip()
    checks = {
        "pretrade_packet_refused": row.get("pretrade_cost_packet_status") == "REFUSED",
        "broker_calibrated_cost_authority": row.get("cost_authority")
        == "broker_calibrated_replay_cost",
        "source_bound_cost_authority_present": row.get("cost_source_gap_status")
        == "source_bound_cost_authority_present",
        "fallback_not_authority": row.get("candidate_cost_r_fallback_is_authority")
        is False,
        "pretrade_cost_not_executable": row.get("broker_pretrade_cost_executable")
        is False,
        "threshold_refusal_serialized": block_reason.startswith(
            "broker_cost_packet_refused:"
        )
        and any(
            token in block_reason
            for token in (
                "spread_r_exceeds",
                "total_cost_r_exceeds",
                "commission_r_exceeds",
                "slippage_r_exceeds",
                "swap_r_exceeds",
                "untradeable_cost_floor",
            )
        ),
        "selector_skip_reason_exact": row.get("scheduler_materialization_skip_reason")
        == "selector_not_risk_bearing_cost_failed",
        "action_intent_not_evaluated_exact": row.get(
            "scheduler_materialization_action_intent"
        )
        == "not_evaluated_selector_not_risk_bearing",
        "candidate_skipped_before_scheduler": row.get("scheduler_selection_disposition")
        == "candidate_materialization_skipped_before_scheduler",
        "terminal_blocker_is_cost_authority": row.get(
            "package_replay_order_executable_final_blocker_class"
        )
        == "cost_authority"
        and row.get("package_replay_order_executable_final_blocker_reason")
        == "broker_cost_authority_blocked_non_executable",
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "block_reason": block_reason or None,
        "producer_control_flow": (
            "selector_not_risk_bearing_cost_failed continues before "
            "same_symbol_replay_exposure_context evaluation"
        ),
        "producer_source": (
            "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
        ),
    }


def chronology_and_same_symbol(
    target: Surface,
    config: AnalyzerConfig,
) -> tuple[dict[str, Any], dict[str, Any]]:
    early_disposition, early_rows = terminal_rows(target, config.early_identity)
    late_disposition, late_rows = terminal_rows(target, config.late_identity)
    early = early_rows[0] if early_disposition == "trade" and len(early_rows) == 1 else {}
    late = late_rows[0] if len(late_rows) == 1 else {}
    early_decision = parse_time(early.get("decision_time_utc") or early.get("decision_time"))
    fill = parse_time(early.get("entry_time_utc") or early.get("fill_time_utc"))
    close = parse_time(early.get("exit_time_utc") or early.get("close_time_utc"))
    late_decision = parse_time(late.get("decision_time_utc") or late.get("decision_time"))
    ordered = bool(
        early_decision
        and fill
        and late_decision
        and early_decision <= fill <= late_decision
    )
    open_at_late = bool(
        ordered and fill and late_decision and (close is None or close > late_decision)
    )
    context = late.get("same_symbol_replay_exposure_context")
    context = context if isinstance(context, Mapping) else {}
    early_trade_id = str(early.get("simulated_trade_id") or "")
    open_ids = [str(value) for value in context.get("same_side_open_ids") or []]
    context_claims_early_open = bool(
        (number(context.get("same_side_open_count")) or 0) >= 1
        and early_trade_id
        and early_trade_id in open_ids
    )
    context_observed = bool(
        late.get("same_symbol_replay_exposure_context_status") == "source_observed"
        and late.get("same_symbol_replay_exposure_context_synthesized_empty") is False
    )
    same_instrument = bool(
        early.get("symbol") == late.get("symbol") == "XAUUSD"
        and (early.get("side") or early.get("direction"))
        == (late.get("side") or late.get("direction"))
        == "SHORT"
    )
    cost_precedence = prior_cost_block_precedence(late)
    effective_action = str(
        late.get("effective_selector_action")
        or late.get("raw_selector_action")
        or late.get("selector_action")
        or ""
    ).strip()
    risk_bearing_at_lifecycle_gate = effective_action in RISK_BEARING_SELECTOR_ACTIONS
    lifecycle_authority_reached = bool(
        risk_bearing_at_lifecycle_gate
        and not cost_precedence["valid"]
        and (
            context_observed
            or late.get("scheduler_materialization_replay_lifecycle_action_resolver_enabled")
            is not None
            or late.get("scheduler_materialization_lifecycle_action_resolution_required")
            is not None
            or late.get("same_symbol_lifecycle_action") not in (None, "")
        )
    )
    context_required = lifecycle_authority_reached
    raw_context_matches_chronology = bool(
        (open_at_late and context_claims_early_open)
        or (not open_at_late and not context_claims_early_open)
    )
    provenance_label_caveat = None
    if not ordered:
        authority_status = "chronology_not_proven"
        consistent = False
    elif cost_precedence["valid"]:
        authority_status = "lifecycle_not_evaluated_due_prior_cost_block"
        consistent = same_instrument
        if context_observed:
            provenance_label_caveat = (
                "serialized_source_observed_context_is_provenance_only_not_"
                "decision_authority_after_pre_lifecycle_cost_continue"
            )
    elif not context_required:
        authority_status = "lifecycle_context_not_required_or_not_reached"
        consistent = same_instrument
    elif open_at_late and context_claims_early_open and late_disposition == "missed":
        authority_status = "early_open_exposure_observed_and_late_candidate_not_executed"
        consistent = context_observed and same_instrument
    elif open_at_late and context_claims_early_open and late_disposition == "trade":
        authority_status = "additional_entry_observed_while_early_trade_open"
        consistent = context_observed and same_instrument
    elif open_at_late and not context_claims_early_open:
        authority_status = "early_trade_open_but_late_source_observed_context_missing_it"
        consistent = False
    elif not open_at_late and context_claims_early_open:
        authority_status = "early_trade_closed_but_late_context_reports_it_open"
        consistent = False
    else:
        authority_status = "early_trade_not_open_at_late_decision_and_no_open_block_observed"
        consistent = context_observed and same_instrument
    chronology = {
        "valid": ordered and same_instrument,
        "early_decision_utc": early_decision.isoformat() if early_decision else None,
        "early_fill_utc": fill.isoformat() if fill else None,
        "late_decision_utc": late_decision.isoformat() if late_decision else None,
        "early_exit_utc": close.isoformat() if close else None,
        "decision_fill_late_order_exact": ordered,
        "same_symbol_side_exact": same_instrument,
        "early_trade_open_at_late_decision": open_at_late,
    }
    authority = {
        "consistent": consistent,
        "status": authority_status,
        "late_disposition": late_disposition,
        "context_status": late.get("same_symbol_replay_exposure_context_status"),
        "context_synthesized_empty": late.get(
            "same_symbol_replay_exposure_context_synthesized_empty"
        ),
        "same_side_open_count": context.get("same_side_open_count"),
        "same_side_open_ids": context.get("same_side_open_ids"),
        "same_side_open_risk_pct": context.get("same_side_open_risk_pct"),
        "early_trade_id": early_trade_id or None,
        "early_trade_id_observed_in_context": context_claims_early_open,
        "raw_context_matches_chronology": raw_context_matches_chronology,
        "context_required_for_terminal_decision": context_required,
        "context_decision_authoritative": context_required,
        "risk_bearing_at_lifecycle_gate": risk_bearing_at_lifecycle_gate,
        "lifecycle_authority_reached": lifecycle_authority_reached,
        "prior_cost_block_precedence": cost_precedence,
        "provenance_label_caveat": provenance_label_caveat,
        "late_selector_action": late.get("selector_action"),
        "late_effective_selector_action": late.get("effective_selector_action"),
        "late_miss_reason": late.get("miss_reason"),
        "late_package_final_blocker_class": late.get(
            "package_replay_order_executable_final_blocker_class"
        ),
        "late_package_final_blocker_reason": late.get(
            "package_replay_order_executable_final_blocker_reason"
        ),
    }
    return chronology, authority


def input_metadata(surface: Surface) -> dict[str, Any]:
    return {
        "prefix": surface.prefix,
        "summary": surface.summary_meta,
        "trade_ledger": surface.trades.metadata(),
        "missed_ledger": surface.missed.metadata(),
        "scorecard_ledger": surface.scorecards.metadata(),
        "order_ledger": surface.orders.metadata(),
        "oracle_ledger": surface.oracle.metadata(),
        "source_ledger": surface.sources.metadata(),
    }


def build_analysis(config: AnalyzerConfig) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    full_portfolio_mode = config.full_portfolio_mode
    baseline = load_surface(config, "baseline", config.baseline_prefix)
    target = load_surface(config, "target", config.target_prefix)

    baseline_contract = summary_contract(
        baseline,
        expected_shared_digest=config.expected_baseline_shared_digest,
        expected_source_digest=config.expected_baseline_source_digest,
        expected_universe=baseline.summary.get("configured_symbol_universe") or [],
    )
    # The baseline must be the completed 24-symbol June R2 authority surface.
    baseline_universe = baseline.summary.get("active_replay_symbol_universe")
    baseline_contract["checks"]["exact_24_symbol_baseline"] = bool(
        isinstance(baseline_universe, list)
        and len(baseline_universe) == 24
        and "XAUUSD" in baseline_universe
    )
    baseline_contract["checks"]["baseline_active_equals_configured_universe"] = (
        baseline_universe == baseline.summary.get("configured_symbol_universe")
    )
    baseline_contract["valid"] = all(baseline_contract["checks"].values())

    target_expected_universe = (
        list(baseline_universe or []) if full_portfolio_mode else ["XAUUSD"]
    )
    target_contract = summary_contract(
        target,
        expected_shared_digest=config.expected_target_shared_digest,
        expected_source_digest=config.expected_target_source_digest,
        expected_universe=target_expected_universe,
    )
    if full_portfolio_mode:
        target_contract["checks"]["exact_24_symbol_target"] = bool(
            isinstance(target.summary.get("active_replay_symbol_universe"), list)
            and target.summary["active_replay_symbol_universe"] == baseline_universe
            and len(target.summary["active_replay_symbol_universe"]) == 24
        )
        target_contract["checks"]["target_active_equals_configured_universe"] = (
            target.summary.get("active_replay_symbol_universe")
            == target.summary.get("configured_symbol_universe")
        )
        target_contract["valid"] = all(target_contract["checks"].values())
    # Configurable profile digest is bound here; the production default is the
    # predeclared B7.5 repaired-profile hash.
    for contract in (baseline_contract, target_contract):
        actual_profile = contract.get("actual_profile_digest")
        contract["expected_profile_digest"] = config.expected_profile_digest
        contract["checks"]["profile_digest_exact"] = (
            actual_profile == config.expected_profile_digest
        )
        contract["valid"] = all(contract["checks"].values())

    baseline_parity = physical_parity(baseline)
    target_parity = physical_parity(target)
    early_time = config.early_identity.rsplit("@@", 1)[-1]
    late_time = config.late_identity.rsplit("@@", 1)[-1]
    baseline_early = compact_candidate_row(
        baseline, config.early_identity, early_time
    )
    baseline_late = compact_candidate_row(baseline, config.late_identity, late_time)
    target_early = compact_candidate_row(target, config.early_identity, early_time)
    target_late = compact_candidate_row(target, config.late_identity, late_time)
    chronology, same_symbol = chronology_and_same_symbol(target, config)
    scoreability = target_terminal_scoreability(target, config.early_identity)
    required_until = parse_time(target_early.get("exit_time_utc"))
    tick_integrity = selected_tick_integrity(target, config, required_until)
    identity_partition = terminal_identity_partition_proof(baseline, target)

    identity_checks = {
        "baseline_early_exact_trade": baseline_early["disposition"] == "trade"
        and baseline_early["identity_exact"]
        and baseline_early["decision_time_exact"],
        "baseline_late_exact_missed": baseline_late["disposition"] == "missed"
        and baseline_late["identity_exact"]
        and baseline_late["decision_time_exact"],
        "target_early_exact_trade": target_early["disposition"] == "trade"
        and target_early["identity_exact"]
        and target_early["decision_time_exact"],
        "target_late_exact_terminal_disposition": target_late["disposition"]
        in {"trade", "missed"}
        and target_late["identity_exact"]
        and target_late["decision_time_exact"],
        "all_exact_rows_xau_short": all(
            row.get("symbol") == "XAUUSD" and row.get("side") == "SHORT"
            for row in (baseline_early, baseline_late, target_early, target_late)
        ),
    }
    identity_valid = all(identity_checks.values())

    structural_issues: list[str] = []
    for status, valid in (
        ("baseline_contract_invalid", baseline_contract["valid"]),
        ("target_contract_invalid", target_contract["valid"]),
        ("baseline_physical_summary_parity_failed", baseline_parity["valid"]),
        ("target_physical_summary_parity_failed", target_parity["valid"]),
        ("target_tick_integrity_failed", tick_integrity["valid"]),
        ("exact_candidate_identity_failed", identity_valid),
        ("target_chronology_failed", chronology["valid"]),
    ):
        if not valid:
            structural_issues.append(status)
    if full_portfolio_mode and not identity_partition["valid"]:
        structural_issues.append("full_portfolio_terminal_identity_partition_drift")
    if (
        full_portfolio_mode
        and same_symbol["context_required_for_terminal_decision"]
        and not same_symbol["consistent"]
    ):
        structural_issues.append("full_portfolio_same_symbol_context_drift")

    if structural_issues:
        causal_disposition = "INVALID_EVIDENCE"
    elif not scoreability["valid"]:
        causal_disposition = "ORDERED_TICK_TERMINAL_PROOF_INCOMPLETE"
    elif not same_symbol["consistent"]:
        causal_disposition = "DEEPER_SAME_SYMBOL_AUTHORITY_INCONSISTENCY"
    elif same_symbol["status"] == "lifecycle_not_evaluated_due_prior_cost_block":
        causal_disposition = (
            "TERMINAL_TRUTH_GREEN_LIFECYCLE_NOT_EVALUATED_DUE_PRIOR_COST_BLOCK"
        )
    elif chronology["early_trade_open_at_late_decision"]:
        if target_late["disposition"] == "missed":
            causal_disposition = (
                "PROOF_COMPLETE_OPEN_EXPOSURE_AND_LATE_NON_EXECUTION_OBSERVED"
            )
        else:
            causal_disposition = (
                "PROOF_COMPLETE_ADDITIONAL_ENTRY_WHILE_EARLY_TRADE_OPEN"
            )
    else:
        causal_disposition = "PROOF_COMPLETE_EARLY_TRADE_CLOSED_BEFORE_LATE_DECISION"

    if causal_disposition in {
        "INVALID_EVIDENCE",
        "ORDERED_TICK_TERMINAL_PROOF_INCOMPLETE",
    }:
        decision = causal_disposition
    elif full_portfolio_mode:
        decision = "FULL_PORTFOLIO_RECONCILIATION_COMPLETE"
    elif causal_disposition == (
        "TERMINAL_TRUTH_GREEN_LIFECYCLE_NOT_EVALUATED_DUE_PRIOR_COST_BLOCK"
    ):
        decision = "TERMINAL_TRUTH_GREEN_ESCALATE_FULL_PORTFOLIO"
    else:
        # Preserve the exact XAU-local causal result.  Its required next gate is
        # carried separately so escalation cannot be mistaken for a finding.
        decision = causal_disposition

    portfolio_disposition = (
        "FULL_PORTFOLIO_RECONCILIATION_COMPLETE"
        if full_portfolio_mode and not structural_issues
        else (
            "ESCALATE_FULL_PORTFOLIO"
            if not full_portfolio_mode
            and causal_disposition
            not in {"INVALID_EVIDENCE", "ORDERED_TICK_TERMINAL_PROOF_INCOMPLETE"}
            else "NOT_READY_FOR_PORTFOLIO_RECONCILIATION"
        )
    )
    full_portfolio_economics_available = bool(
        full_portfolio_mode
        and baseline_contract["valid"]
        and target_contract["valid"]
        and baseline_parity["valid"]
        and target_parity["valid"]
        and identity_partition["valid"]
        and same_symbol["consistent"]
        and baseline_universe == target.summary.get("active_replay_symbol_universe")
    )
    economic_metrics = (
        "physical_trade_rows",
        "physical_scoreable_trade_rows",
        "physical_unscoreable_trade_rows",
        "physical_net_r",
        "physical_gross_r",
        "physical_final_r",
        "physical_cash_pnl",
        "physical_risk_cash",
        "physical_risk_pct",
        "physical_expected_cost_r",
        "headline_trade_rows",
        "headline_net_r",
        "headline_gross_r",
        "headline_final_r",
        "headline_cash_pnl",
    )
    full_portfolio_economics: dict[str, Any] = {
        "status": (
            "same_day_simulated_portfolio_reconciliation_available"
            if full_portfolio_economics_available
            else (
                "not_available_full_mode_contract_failed"
                if full_portfolio_mode
                else "not_computed_xau_only_target_scope"
            )
        ),
        "available": full_portfolio_economics_available,
        "evidence_class": (
            "same_day_24_symbol_simulated_portfolio_reconciliation"
            if full_portfolio_economics_available
            else "cross_scope_comparison_not_economic_authority"
        ),
        "drawdown_recomputed": False,
        "account_return_recomputed": False,
        "broker_real": False,
    }
    if full_portfolio_economics_available:
        baseline_rollup = baseline_parity["recomputed"]
        target_rollup = target_parity["recomputed"]
        full_portfolio_economics["metrics"] = {
            metric: {
                "baseline": baseline_rollup[metric],
                "target": target_rollup[metric],
                "delta": rounded(
                    float(target_rollup[metric]) - float(baseline_rollup[metric])
                ),
            }
            for metric in economic_metrics
        }

    evidence_scope = {
        "target_scope_mode": (
            "full_portfolio_reconciliation" if full_portfolio_mode else "xau_only"
        ),
        "evidence_class": (
            "bounded_xau_only_ordered_tick_local_replay"
            if not full_portfolio_mode
            else "bounded_24_symbol_ordered_tick_portfolio_reconciliation_replay"
        ),
        "baseline_scope": "completed_24_symbol_june_r2_context_only",
        "target_scope": (
            "single_day_xauusd_only_ordered_tick_discriminator"
            if not full_portfolio_mode
            else "single_day_24_symbol_ordered_tick_portfolio_reconciliation"
        ),
        "target_symbol_universe": target.summary.get("active_replay_symbol_universe"),
        "same_day_simulated_portfolio_reconciliation_authorized": (
            full_portfolio_economics_available
        ),
        "same_day_simulated_cash_delta_authorized": full_portfolio_economics_available,
        "same_day_simulated_r_delta_authorized": full_portfolio_economics_available,
        "same_day_simulated_risk_delta_authorized": full_portfolio_economics_available,
        "cross_scope_headline_delta_computed": full_portfolio_economics_available,
        "full_portfolio_economic_claim_authorized": False,
        "portfolio_cash_pnl_delta_authorized": False,
        "portfolio_replay_r_delta_authorized": False,
        "portfolio_return_delta_authorized": False,
        "broad_generalization_claim_authorized": False,
        "policy_preference_authorized": False,
        "policy_change_authorized": False,
        "broker_real_claim_authorized": False,
        "live_authority": False,
        "final_selection_claim": False,
        "policy_assumption_count": 0,
        "portfolio_disposition": portfolio_disposition,
        "required_next_evidence": (
            "completed_24_symbol_same_day_ordered_tick_portfolio_reconciliation"
            if not full_portfolio_mode
            else "causal repair or successor discriminator selected from full reconciliation"
        ),
    }
    replacement_value = {
        "target_early_executed_net_r": target_early.get("net_r"),
        "target_early_executed_cash_pnl": target_early.get("cash_pnl"),
        "target_late_disposition": target_late.get("disposition"),
        "target_late_diagnostic_opportunity_r": target_late.get(
            "diagnostic_opportunity_r"
        ),
        "baseline_late_diagnostic_opportunity_r": baseline_late.get(
            "diagnostic_opportunity_r"
        ),
        "joint_execution_counterfactual_available": False,
        "arithmetic_netting_authorized": False,
        "portfolio_economic_delta": None,
        "interpretation": (
            "descriptive candidate-level trace; diagnostic late opportunity is "
            "not arithmetically netted with the executed early trade"
        ),
    }
    generated_at = datetime.now(timezone.utc).isoformat()
    summary: dict[str, Any] = {
        "schema": SUMMARY_SCHEMA,
        "generated_at_utc": generated_at,
        "status": "analysis_complete",
        "decision": decision,
        "causal_disposition": causal_disposition,
        "portfolio_disposition": portfolio_disposition,
        "analysis_valid": not structural_issues,
        "structural_issue_count": len(structural_issues),
        "structural_issues": structural_issues,
        "baseline_prefix": config.baseline_prefix,
        "target_prefix": config.target_prefix,
        "day": config.day,
        "bound_identities": {
            "early_0730": config.early_identity,
            "late_0745": config.late_identity,
        },
        "input_artifacts": {
            "baseline": input_metadata(baseline),
            "target": input_metadata(target),
        },
        "source_and_execution_contracts": {
            "baseline": baseline_contract,
            "target": target_contract,
        },
        "tick_source_integrity": tick_integrity,
        "physical_summary_parity": {
            "baseline": baseline_parity,
            "target": target_parity,
        },
        "identity_proof": {
            "valid": identity_valid,
            "checks": identity_checks,
            "baseline_0730": baseline_early,
            "baseline_0745": baseline_late,
            "target_0730": target_early,
            "target_0745": target_late,
        },
        "terminal_identity_partition_proof": identity_partition,
        "target_terminal_scoreability": scoreability,
        "target_chronology": chronology,
        "same_symbol_block_authority": same_symbol,
        "replacement_value_observation": replacement_value,
        "full_portfolio_economics": full_portfolio_economics,
        "evidence_scope": evidence_scope,
        "established_findings": [
            "target ordered-tick source and physical ledgers are accepted only when all serialized checks are green",
            "the exact 07:30 and 07:45 identities are traced without candidate substitution",
            "same-symbol authority is classified from serialized chronology and exposure context",
        ],
        "not_established": [
            (
                "broad, multi-day, or generalized portfolio economics"
                if full_portfolio_mode
                else "same-day or full-portfolio economics"
            ),
            "broker-real profitability",
            "optimal scale-in, reserve, rejection, or allocation policy",
            "a joint counterfactual in which both exact candidates execute",
        ],
    }
    rows = [
        {
            "schema": ROW_SCHEMA,
            "row_type": "source_tick_integrity",
            **tick_integrity,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "candidate_identity",
            **baseline_early,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "candidate_identity",
            **baseline_late,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "candidate_identity",
            **target_early,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "candidate_identity",
            **target_late,
        },
        {"schema": ROW_SCHEMA, "row_type": "target_chronology", **chronology},
        {
            "schema": ROW_SCHEMA,
            "row_type": "same_symbol_block_authority",
            **same_symbol,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "target_terminal_scoreability",
            **scoreability,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "replacement_value_observation",
            **replacement_value,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "terminal_identity_partition_proof",
            **identity_partition,
        },
        {
            "schema": ROW_SCHEMA,
            "row_type": "full_portfolio_economics",
            **full_portfolio_economics,
        },
        {"schema": ROW_SCHEMA, "row_type": "evidence_scope", **evidence_scope},
    ]
    return summary, rows


def render_dossier(summary: Mapping[str, Any]) -> str:
    identity = summary["identity_proof"]
    chronology = summary["target_chronology"]
    same_symbol = summary["same_symbol_block_authority"]
    scoreability = summary["target_terminal_scoreability"]
    replacement = summary["replacement_value_observation"]
    portfolio = summary["full_portfolio_economics"]
    scope = summary["evidence_scope"]
    lines = [
        "# B7.5 XAU Ordered-Tick Replacement-Value Proof",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- Causal disposition: `{summary['causal_disposition']}`",
        f"- Portfolio disposition: `{summary['portfolio_disposition']}`",
        f"- Analysis valid: `{str(summary['analysis_valid']).lower()}`",
        f"- Structural issues: `{summary['structural_issue_count']}`",
        f"- Evidence class: `{scope['evidence_class']}`",
        "- Full-portfolio economic claim authorized: `false`",
        "- Policy change authorized: `false`",
        "- Broker/live/final authority: `false / false / false`",
        "",
        "## Exact candidate trace",
        "",
        "| Surface | Time | Identity | Disposition | Scoreable | Net R | Cash |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for label, row in (
        ("baseline", identity["baseline_0730"]),
        ("baseline", identity["baseline_0745"]),
        ("target", identity["target_0730"]),
        ("target", identity["target_0745"]),
    ):
        lines.append(
            f"| {label} | {row.get('decision_time_utc')} | `{row.get('identity_key')}` "
            f"| {row.get('disposition')} | {row.get('terminal_r_scoreable')} "
            f"| {row.get('net_r')} | {row.get('cash_pnl')} |"
        )
    lines.extend(
        [
            "",
            "## Ordered-tick terminal proof",
            "",
            f"- Contract valid: `{str(scoreability['valid']).lower()}`",
            f"- Outcome: `{scoreability.get('terminal_outcome')}`",
            f"- Target 07:30 net R: `{scoreability.get('net_r')}`",
            f"- Target 07:30 cash PnL: `{scoreability.get('cash_pnl')}`",
            f"- Tick query rows: `{scoreability.get('query_tick_rows')}`",
            "",
            "## Chronology and same-symbol authority",
            "",
            f"- 07:30 decision -> fill -> 07:45 decision exact: `{str(chronology['decision_fill_late_order_exact']).lower()}`",
            f"- 07:30 trade open at 07:45: `{str(chronology['early_trade_open_at_late_decision']).lower()}`",
            f"- Same-symbol authority status: `{same_symbol['status']}`",
            f"- Serialized context consistent with chronology: `{str(same_symbol['consistent']).lower()}`",
            f"- Context required for terminal decision: `{str(same_symbol['context_required_for_terminal_decision']).lower()}`",
            f"- Valid prior cost-block precedence: `{str(same_symbol['prior_cost_block_precedence']['valid']).lower()}`",
            f"- Provenance-label caveat: `{same_symbol.get('provenance_label_caveat')}`",
            f"- Late effective selector action: `{same_symbol.get('late_effective_selector_action')}`",
            f"- Late terminal blocker: `{same_symbol.get('late_package_final_blocker_reason')}`",
            "",
            "## Replacement-value boundary",
            "",
            f"- Executed early net R: `{replacement.get('target_early_executed_net_r')}`",
            f"- Late diagnostic opportunity R: `{replacement.get('target_late_diagnostic_opportunity_r')}`",
            "- These values are not arithmetically netted. The late value is diagnostic and joint execution was not replayed.",
            "- No scale-in, reserve, rejection, allocation, or other policy preference is inferred.",
            "",
            "## Same-day simulated portfolio reconciliation",
            "",
            f"- Status: `{portfolio['status']}`",
            f"- Authorized: `{str(scope['same_day_simulated_portfolio_reconciliation_authorized']).lower()}`",
            "- Broad/generalization, policy, broker, live, and final claims remain unauthorized.",
            "",
            "## Evidence boundary",
            "",
            (
                "This is a one-day XAUUSD-only ordered-tick local replay discriminator anchored to a completed 24-symbol baseline. It requires a completed 24-symbol reconciliation before any same-day simulated portfolio delta."
                if scope["target_scope_mode"] == "xau_only"
                else "This is a same-day 24-symbol simulated portfolio reconciliation only. It does not establish broad robustness, generalization, account return, drawdown, payout probability, broker-real behavior, policy preference, live authority, or final selection."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def output_metadata(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "byte_count": path.stat().st_size,
    }


def run(config: AnalyzerConfig) -> dict[str, Any]:
    validate_prefix(config.output_prefix)
    # All input validation and analysis happens before the first output write.
    # An incomplete target therefore cannot mutate or certify output artifacts.
    summary, rows = build_analysis(config)
    root = config.artifact_root
    summary_path = artifact_path(root, config.output_prefix, "SUMMARY.json")
    ledger_path = artifact_path(root, config.output_prefix, "ROW_LEDGER.jsonl")
    dossier_path = artifact_path(root, config.output_prefix, "DOSSIER.md")
    manifest_path = artifact_path(root, config.output_prefix, "COMPLETION_MANIFEST.json")
    manifest_path.unlink(missing_ok=True)
    atomic_write(summary_path, canonical_json_bytes(summary))
    ledger_payload = "".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows
    ).encode("utf-8")
    atomic_write(ledger_path, ledger_payload)
    atomic_write(dossier_path, render_dossier(summary).encode("utf-8"))
    artifacts = [
        output_metadata(summary_path),
        output_metadata(ledger_path),
        output_metadata(dossier_path),
    ]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "completion_manifest_written_last",
        "analysis_valid": summary["analysis_valid"],
        "decision": summary["decision"],
        "output_prefix": config.output_prefix,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "row_ledger_rows": len(rows),
        "generator": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "evidence_scope": summary["evidence_scope"],
    }
    # Completion authority appears only after every preceding artifact exists
    # and its hash has been recomputed from physical bytes.
    atomic_write(manifest_path, canonical_json_bytes(manifest))
    return {
        "summary": summary,
        "manifest": manifest,
        "paths": {
            "summary": str(summary_path),
            "row_ledger": str(ledger_path),
            "dossier": str(dossier_path),
            "completion_manifest": str(manifest_path),
        },
    }


def parse_args(argv: Sequence[str] | None = None) -> AnalyzerConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=ROUTE)
    parser.add_argument("--baseline-prefix", default=DEFAULT_BASELINE_PREFIX)
    parser.add_argument("--target-prefix", default=DEFAULT_TARGET_PREFIX)
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    parser.add_argument(
        "--expected-baseline-shared-digest", default=BASELINE_SHARED_DIGEST
    )
    parser.add_argument(
        "--expected-baseline-source-digest", default=BASELINE_SOURCE_DIGEST
    )
    parser.add_argument("--expected-target-shared-digest", default=TARGET_SHARED_DIGEST)
    parser.add_argument("--expected-target-source-digest", default=TARGET_SOURCE_DIGEST)
    parser.add_argument("--expected-profile-digest", default=PROFILE_DIGEST)
    parser.add_argument("--expected-tick-sha256", default=TARGET_TICK_SHA256)
    parser.add_argument("--expected-tick-rows", type=int, default=TARGET_TICK_ROWS)
    parser.add_argument(
        "--full-portfolio-mode",
        action="store_true",
        help=(
            "Require baseline and target to share the exact configured 24-symbol "
            "universe and exact terminal candidate/trade/missed identity partitions."
        ),
    )
    args = parser.parse_args(argv)
    return AnalyzerConfig(
        artifact_root=args.artifact_root,
        baseline_prefix=args.baseline_prefix,
        target_prefix=args.target_prefix,
        output_prefix=args.output_prefix,
        expected_baseline_shared_digest=args.expected_baseline_shared_digest,
        expected_baseline_source_digest=args.expected_baseline_source_digest,
        expected_target_shared_digest=args.expected_target_shared_digest,
        expected_target_source_digest=args.expected_target_source_digest,
        expected_profile_digest=args.expected_profile_digest,
        expected_tick_sha256=args.expected_tick_sha256,
        expected_tick_rows=args.expected_tick_rows,
        full_portfolio_mode=args.full_portfolio_mode,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = run(parse_args(argv))
    print(json.dumps(result["paths"], indent=2, sort_keys=True))
    print(f"decision={result['summary']['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
