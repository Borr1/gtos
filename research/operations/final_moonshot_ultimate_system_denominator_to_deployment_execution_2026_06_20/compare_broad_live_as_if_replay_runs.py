#!/usr/bin/env python3
"""Compare two broad live-as-if replay runs over the same replay window.

This is a route-owned deterministic parser. It does not run replay and does not
make broker/live/final claims. It compares completed broker-live-closed replay
artifacts already on disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Iterable as IterableABC
from collections.abc import Mapping as MappingABC
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROUTE = Path(__file__).resolve().parent
BROAD_PREFIX_STEM = "BROAD_LIVE_AS_IF_REPLAY_"
MAX_COMPARISON_ARTIFACT_STEM_CHARS = 180
AXIS_SCOPE_ALIGNMENT_FIELDS = {
    "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": (
        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window",
        "source_bound_r_available_inside_replay_window",
    ),
    "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window": (
        "non_additive_executable_gated_package_source_bound_signal_r_inside_replay_window",
        "package_source_bound_r_available_inside_replay_window",
    ),
    "package_axes_available_inside_replay_window": (
        "package_axes_available_inside_replay_window",
    ),
    "package_axis_rows_in_parity_scope": (
        "package_axis_rows_in_parity_scope",
    ),
    "package_axes_in_global_diagnostic_surface": (
        "package_axes_in_global_diagnostic_surface",
    ),
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_jsonl(path: Path, *, max_retries: int = 6) -> Iterable[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return
    offset = 0
    line_no = 0
    retries = 0
    while True:
        try:
            with path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                while True:
                    line = handle.readline()
                    if line == "":
                        return
                    offset = handle.tell()
                    line_no += 1
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            f"{path}:{line_no}: invalid JSONL: {exc}"
                        ) from exc
                    if isinstance(data, dict):
                        yield data
        except (OSError, TimeoutError):
            retries += 1
            if retries > max_retries:
                raise
            time.sleep(min(0.5 * retries, 3.0))


def fnum(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def inum(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def tag_for_prefix(prefix: str) -> str:
    if prefix.startswith(BROAD_PREFIX_STEM):
        return prefix[len(BROAD_PREFIX_STEM) :]
    if prefix == "BROAD_LIVE_AS_IF_REPLAY":
        return ""
    return prefix


def artifact_root(root: Path | None = None) -> Path:
    return Path(root) if root is not None else ROUTE


def summary_path(prefix: str, *, root: Path | None = None) -> Path:
    return artifact_root(root) / f"{prefix}_SUMMARY.json"


def flow_summary_path(prefix: str, *, root: Path | None = None) -> Path:
    return artifact_root(root) / f"{prefix}_FLOW_DIAGNOSTIC_SUMMARY.json"


def trade_path(prefix: str, *, root: Path | None = None) -> Path:
    return artifact_root(root) / f"{prefix}_TRADE_LEDGER.jsonl"


def order_path(prefix: str, *, root: Path | None = None) -> Path:
    return artifact_root(root) / f"{prefix}_ORDER_LEDGER.jsonl"


def missed_path(prefix: str, *, root: Path | None = None) -> Path:
    return artifact_root(root) / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"


def scorecard_path(prefix: str, *, root: Path | None = None) -> Path:
    return artifact_root(root) / f"{prefix}_SCORECARD_LEDGER.jsonl"


def parity_summary_path(prefix: str, *, root: Path | None = None) -> Path:
    root = artifact_root(root)
    tag = tag_for_prefix(prefix)
    suffix = f"_{tag}" if tag else ""
    direct = root / f"SOURCE_BOUND_TO_EXECUTED_PARITY{suffix}_SUMMARY.json"
    if direct.exists():
        return direct
    target_summary_name = summary_path(prefix, root=root).name
    matches: list[tuple[str, str, Path]] = []
    for path in root.glob("SOURCE_BOUND_TO_EXECUTED_PARITY*_SUMMARY.json"):
        payload = read_json(path)
        exact = payload.get("exact_replay_window_transfer")
        exact_prefix = (
            exact.get("broad_replay_prefix") if isinstance(exact, MappingABC) else None
        )
        artifact_summary = (
            payload.get("artifacts", {}).get("broad_replay_summary")
            if isinstance(payload.get("artifacts"), MappingABC)
            else None
        )
        artifact_name = Path(str(artifact_summary)).name if artifact_summary else ""
        if exact_prefix == prefix or artifact_name == target_summary_name:
            generated = str(
                payload.get("generated_utc") or payload.get("generated_at_utc") or ""
            )
            matches.append((generated, path.name, path))
    if not matches:
        return direct
    matches.sort(reverse=True)
    return matches[0][2]


def candidate_projection_path(prefix: str, *, root: Path | None = None) -> Path:
    root = artifact_root(root)
    tag = tag_for_prefix(prefix)
    suffix = f"_{tag}" if tag else ""
    return root / f"CANDIDATE_INSTANCE_PARITY_PROJECTION{suffix}_LEDGER.jsonl"


def first_profile_stats(summary: Mapping[str, Any]) -> dict[str, Any]:
    stats = summary.get("split_profile_stats")
    if isinstance(stats, list) and stats and isinstance(stats[0], dict):
        return stats[0]
    return {}


def order_status_counts(stats: Mapping[str, Any]) -> dict[str, int]:
    counts = stats.get("order_status_counts")
    if not isinstance(counts, dict):
        return {}
    return {str(k): inum(v) for k, v in counts.items()}


def summary_profiles(summary: Mapping[str, Any]) -> list[str]:
    profiles = summary.get("profiles")
    if isinstance(profiles, list):
        return [str(profile) for profile in profiles if str(profile).strip()]
    stats = summary.get("split_profile_stats")
    if isinstance(stats, list):
        found = [
            str(row.get("profile") or row.get("profile_name") or "").strip()
            for row in stats
            if isinstance(row, MappingABC)
            and str(row.get("profile") or row.get("profile_name") or "").strip()
        ]
        if found:
            return found
    profile = summary.get("profile") or summary.get("broad_replay_profile")
    if profile not in (None, ""):
        return [str(profile)]
    return []


def flow_profile_split_metric(
    flow_summary: Mapping[str, Any],
    surface: str,
    stats: Mapping[str, Any],
) -> dict[str, Any]:
    rows = flow_summary.get(surface)
    if not isinstance(rows, MappingABC):
        return {}
    profile_name = str(
        stats.get("profile") or stats.get("profile_name") or ""
    ).strip()
    split_name = str(stats.get("split") or "holdout").strip()
    exact_key = f"profile_split|{profile_name}|{split_name}|all"
    exact = rows.get(exact_key)
    if isinstance(exact, MappingABC):
        return dict(exact)
    for key, row in rows.items():
        if not isinstance(row, MappingABC):
            continue
        if not str(key).startswith("profile_split|"):
            continue
        if profile_name and str(row.get("profile") or "") != profile_name:
            continue
        if split_name and str(row.get("split_or_segment") or "") != split_name:
            continue
        return dict(row)
    return {}


def prefer_metric(
    primary: Mapping[str, Any], key: str, fallback: Any = None
) -> Any:
    value = primary.get(key)
    return fallback if value is None else value


def run_metrics(prefix: str, *, root: Path | None = None) -> dict[str, Any]:
    summary = read_json(summary_path(prefix, root=root))
    stats = first_profile_stats(summary)
    flow_summary = read_json(flow_summary_path(prefix, root=root))
    trade_flow = flow_profile_split_metric(flow_summary, "trade_overall", stats)
    missed_flow = flow_profile_split_metric(
        flow_summary, "missed_opportunity_overall", stats
    )
    order_counts = order_status_counts(stats)
    stress = stats.get("stress") if isinstance(stats.get("stress"), dict) else {}
    monte_carlo = (
        stats.get("monte_carlo") if isinstance(stats.get("monte_carlo"), dict) else {}
    )
    headline_trades = inum(
        stats.get("headline_trade_rows")
        if stats.get("headline_trade_rows") is not None
        else stats.get("filled_trade_count")
    )
    headline_net_r = fnum(
        stats.get("headline_net_r")
        if stats.get("headline_net_r") is not None
        else stats.get("net_r")
    )
    headline_gross_r = fnum(
        stats.get("headline_gross_r")
        if stats.get("headline_gross_r") is not None
        else stats.get("gross_r")
    )
    headline_final_r = fnum(
        stats.get("headline_final_r")
        if stats.get("headline_final_r") is not None
        else stats.get("final_r")
    )
    headline_cash_pnl = fnum(
        prefer_metric(
            trade_flow,
            "cash_pnl",
            stats.get("headline_cash_pnl")
            if stats.get("headline_cash_pnl") is not None
            else stats.get("cash_pnl"),
        )
    )
    physical_trades = inum(
        prefer_metric(
            trade_flow,
            "all_trade_rows",
            stats.get("physical_trade_rows")
            if stats.get("physical_trade_rows") is not None
            else stats.get("trade_rows"),
        )
    )
    physical_net_r = fnum(
        prefer_metric(
            trade_flow,
            "all_trade_net_r",
            stats.get("physical_net_r")
            if stats.get("physical_net_r") is not None
            else headline_net_r + fnum(stats.get("diagnostic_only_net_r")),
        )
    )
    physical_gross_r = fnum(
        prefer_metric(
            trade_flow,
            "all_trade_gross_r",
            stats.get("physical_gross_r")
            if stats.get("physical_gross_r") is not None
            else stats.get("gross_r"),
        )
    )
    physical_final_r = fnum(
        prefer_metric(
            trade_flow,
            "all_trade_final_r",
            stats.get("physical_final_r")
            if stats.get("physical_final_r") is not None
            else stats.get("final_r"),
        )
    )
    physical_cash_pnl = fnum(
        prefer_metric(
            trade_flow,
            "all_trade_cash_pnl",
            stats.get("physical_cash_pnl")
            if stats.get("physical_cash_pnl") is not None
            else stats.get("cash_pnl"),
        )
    )
    physical_risk_cash = fnum(
        prefer_metric(
            trade_flow,
            "all_trade_risk_cash",
            stats.get("physical_risk_cash")
            if stats.get("physical_risk_cash") is not None
            else stats.get("risk_cash"),
        )
    )
    physical_risk_pct = fnum(
        prefer_metric(
            trade_flow,
            "all_trade_risk_pct",
            stats.get("physical_risk_pct")
            if stats.get("physical_risk_pct") is not None
            else stats.get("risk_pct"),
        )
    )
    return {
        "prefix": prefix,
        "status": summary.get("status"),
        "date_start": summary.get("date_start"),
        "date_end": summary.get("date_end"),
        "coverage_status": summary.get("coverage_status"),
        "tick_source_mode": summary.get("tick_source_mode"),
        "profiles": summary_profiles(summary),
        "live_broker_authority": summary.get("live_broker_authority"),
        "broker_mutation_enabled": summary.get("broker_mutation_enabled"),
        "final_selection_claim": summary.get("final_selection_claim"),
        "order_send_attempts": summary.get("order_send_attempts"),
        "candidate_rows": inum(summary.get("candidate_rows")),
        "decision_rows": inum(stats.get("decision_rows") or summary.get("decision_rows")),
        "scorecard_rows": inum(summary.get("scorecard_rows")),
        "order_event_rows": inum(stats.get("order_event_rows") or summary.get("order_rows")),
        "order_rows": inum(stats.get("order_rows")),
        "trades": inum(stats.get("trade_rows") or summary.get("trade_rows")),
        "filled_trade_count": inum(stats.get("filled_trade_count")),
        "net_r": fnum(stats.get("net_r")),
        "gross_r": fnum(stats.get("gross_r")),
        "final_r": fnum(stats.get("final_r")),
        "cash_pnl": fnum(stats.get("cash_pnl")),
        "risk_cash": fnum(stats.get("risk_cash")),
        "risk_pct": fnum(stats.get("risk_pct")),
        "wins": inum(stats.get("win_count")),
        "losses": inum(stats.get("loss_count")),
        "flats": inum(stats.get("flat_count")),
        "headline_trades": headline_trades,
        "headline_net_r": headline_net_r,
        "headline_gross_r": headline_gross_r,
        "headline_final_r": headline_final_r,
        "headline_cash_pnl": headline_cash_pnl,
        "headline_wins": inum(
            stats.get("headline_win_count")
            if stats.get("headline_win_count") is not None
            else stats.get("win_count")
        ),
        "headline_losses": inum(
            stats.get("headline_loss_count")
            if stats.get("headline_loss_count") is not None
            else stats.get("loss_count")
        ),
        "headline_flats": inum(
            stats.get("headline_flat_count")
            if stats.get("headline_flat_count") is not None
            else stats.get("flat_count")
        ),
        "physical_trades": physical_trades,
        "physical_scoreable_trades": inum(
            prefer_metric(
                trade_flow,
                "all_trade_scoreable_rows",
                stats.get("physical_scoreable_trade_rows")
                if stats.get("physical_scoreable_trade_rows") is not None
                else physical_trades,
            )
        ),
        "physical_unscoreable_trades": inum(
            prefer_metric(
                trade_flow,
                "all_trade_missing_r_rows",
                stats.get("physical_unscoreable_trade_rows"),
            )
        ),
        "entry_fill_executable_trades": inum(
            prefer_metric(trade_flow, "entry_fill_executable_rows", physical_trades)
        ),
        "terminal_r_unscoreable_trades": inum(
            prefer_metric(
                trade_flow,
                "terminal_r_unscoreable_rows",
                stats.get("entry_fill_executable_terminal_r_unscoreable_trade_rows"),
            )
        ),
        "physical_net_r": physical_net_r,
        "physical_gross_r": physical_gross_r,
        "physical_final_r": physical_final_r,
        "physical_cash_pnl": physical_cash_pnl,
        "physical_risk_cash": physical_risk_cash,
        "physical_risk_pct": physical_risk_pct,
        "physical_wins": inum(
            prefer_metric(
                trade_flow,
                "all_trade_win_count",
                stats.get("physical_win_count")
                if stats.get("physical_win_count") is not None
                else stats.get("win_count"),
            )
        ),
        "physical_losses": inum(
            prefer_metric(
                trade_flow,
                "all_trade_loss_count",
                stats.get("physical_loss_count")
                if stats.get("physical_loss_count") is not None
                else stats.get("loss_count"),
            )
        ),
        "physical_flats": inum(
            prefer_metric(
                trade_flow,
                "all_trade_flat_count",
                stats.get("physical_flat_count")
                if stats.get("physical_flat_count") is not None
                else stats.get("flat_count"),
            )
        ),
        "diagnostic_trades": inum(
            prefer_metric(
                trade_flow,
                "diagnostic_only_trade_rows",
                stats.get("diagnostic_only_trade_rows"),
            )
        ),
        "diagnostic_net_r": fnum(
            prefer_metric(
                trade_flow, "diagnostic_only_net_r", stats.get("diagnostic_only_net_r")
            )
        ),
        "diagnostic_wins": inum(
            prefer_metric(trade_flow, "diagnostic_only_win_count", 0)
        ),
        "diagnostic_losses": inum(
            prefer_metric(trade_flow, "diagnostic_only_loss_count", 0)
        ),
        "diagnostic_flats": inum(
            prefer_metric(trade_flow, "diagnostic_only_flat_count", 0)
        ),
        "expired_unfilled": inum(order_counts.get("expired_unfilled")),
        "order_status_counts": order_counts,
        "missed_rows": inum(stats.get("missed_opportunity_rows") or summary.get("missed_opportunity_rows")),
        "missed_scoreable": inum(
            prefer_metric(
                missed_flow,
                "missed_scoreable_count",
                stats.get("missed_counterfactual_scoreable_rows"),
            )
        ),
        "missed_unscoreable": inum(
            prefer_metric(missed_flow, "missed_unscoreable_count", 0)
        ),
        "missed_positive_rows": inum(
            prefer_metric(
                missed_flow,
                "missed_executable_positive_count",
                stats.get("missed_counterfactual_positive_rows"),
            )
        )
        + inum(prefer_metric(missed_flow, "missed_diagnostic_positive_count", 0)),
        "missed_positive_net_r": fnum(
            prefer_metric(
                missed_flow, "missed_positive_net_r", stats.get("missed_positive_net_r")
            )
        ),
        "missed_negative_rows": inum(
            prefer_metric(
                missed_flow,
                "missed_executable_negative_count",
                stats.get("missed_counterfactual_negative_rows"),
            )
        )
        + inum(prefer_metric(missed_flow, "missed_diagnostic_negative_count", 0)),
        "missed_negative_net_r": fnum(
            prefer_metric(
                missed_flow, "missed_negative_net_r", stats.get("missed_negative_net_r")
            )
        ),
        "missed_total_scoreable_net_r": fnum(
            prefer_metric(
                missed_flow, "missed_net_r", stats.get("missed_total_scoreable_net_r")
            )
        ),
        "missed_executable_scoreable": inum(
            prefer_metric(
                missed_flow,
                "missed_executable_scoreable_count",
                stats.get("missed_executable_counterfactual_scoreable_rows"),
            )
        ),
        "missed_executable_net_r": fnum(
            prefer_metric(
                missed_flow,
                "missed_executable_net_r",
                stats.get("missed_executable_scoreable_net_r"),
            )
        ),
        "missed_diagnostic_scoreable": inum(
            prefer_metric(
                missed_flow,
                "missed_diagnostic_scoreable_count",
                stats.get("missed_diagnostic_counterfactual_scoreable_rows"),
            )
        ),
        "missed_diagnostic_net_r": fnum(
            prefer_metric(
                missed_flow,
                "missed_diagnostic_net_r",
                stats.get("missed_diagnostic_opportunity_net_r"),
            )
        ),
        "missed_diagnostic_positive_rows": inum(
            prefer_metric(missed_flow, "missed_diagnostic_positive_count", 0)
        ),
        "missed_diagnostic_positive_net_r": fnum(
            prefer_metric(missed_flow, "missed_diagnostic_positive_net_r", 0.0)
        ),
        "missed_diagnostic_negative_rows": inum(
            prefer_metric(missed_flow, "missed_diagnostic_negative_count", 0)
        ),
        "missed_diagnostic_negative_net_r": fnum(
            prefer_metric(missed_flow, "missed_diagnostic_negative_net_r", 0.0)
        ),
        "stress": stress,
        "monte_carlo": monte_carlo,
        "risk_finalizer": summary.get("risk_admitted_scheduler_finalizer_evidence"),
    }


def axis_transfer_status(
    *,
    prefix: str,
    role: str,
    status: str,
    path: Path,
    profile: str | None = None,
    selected_profile: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "prefix": prefix,
        "role": role,
        "status": status,
        "path": str(path),
    }
    if profile:
        output["requested_profile"] = profile
    if selected_profile:
        output["selected_profile"] = selected_profile
    if detail:
        output["detail"] = detail
    return output


def load_axis_transfer_with_status(
    prefix: str,
    profile: str | None = None,
    *,
    role: str = "run",
    root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = parity_summary_path(prefix, root=root)
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}, axis_transfer_status(
            prefix=prefix,
            role=role,
            status=f"missing_{role}_parity_summary",
            path=path,
            profile=profile,
        )
    parity = read_json(path)
    exact = parity.get("exact_replay_window_transfer")
    if not isinstance(exact, dict):
        return {}, axis_transfer_status(
            prefix=prefix,
            role=role,
            status=f"missing_{role}_exact_replay_window_transfer",
            path=path,
            profile=profile,
        )
    profiles = exact.get("profiles")
    if isinstance(profiles, dict):
        selected_profile = profile or next(iter(profiles), None)
        row = profiles.get(str(selected_profile)) if selected_profile else None
        if isinstance(row, dict):
            return row, axis_transfer_status(
                prefix=prefix,
                role=role,
                status="present",
                path=path,
                profile=profile,
                selected_profile=str(selected_profile),
            )
        return {}, axis_transfer_status(
            prefix=prefix,
            role=role,
            status=f"missing_{role}_profile_axis_transfer",
            path=path,
            profile=profile,
            selected_profile=str(selected_profile) if selected_profile else None,
            detail="requested_or_default_profile_not_present",
        )
    return exact, axis_transfer_status(
        prefix=prefix,
        role=role,
        status="present",
        path=path,
        profile=profile,
    )


def load_axis_transfer(
    prefix: str,
    profile: str | None = None,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    transfer, _status = load_axis_transfer_with_status(
        prefix,
        profile=profile,
        root=root,
    )
    return transfer


def trade_key(row: Mapping[str, Any]) -> str:
    key = str(
        row.get("canonical_replay_candidate_instance_key")
        or row.get("candidate_instance_parity_key")
        or row.get("source_bound_replay_candidate_instance_key")
        or ""
    ).strip()
    if key:
        return key
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc") or row.get("decision_time") or ""
    ).strip()
    return f"{candidate_id}@@{decision_time}" if candidate_id or decision_time else ""


def row_in_summary_window(row: Mapping[str, Any], summary: Mapping[str, Any]) -> bool:
    start = str(summary.get("date_start") or "").strip()
    end = str(summary.get("date_end") or "").strip()
    if not start and not end:
        return True
    day = str(
        row.get("trading_day")
        or row.get("replay_trading_day")
        or row.get("decision_day")
        or row.get("decision_time_utc")
        or row.get("decision_time")
        or row.get("order_time_utc")
        or row.get("created_time_utc")
        or row.get("event_time_utc")
        or row.get("asof_utc")
        or row.get("timestamp_utc")
        or row.get("entry_time_utc")
        or row.get("close_time_utc")
        or ""
    )[:10]
    if not day:
        return False
    if start and day < start:
        return False
    if end and day > end:
        return False
    return True


def load_trade_map(
    prefix: str,
    summary: Mapping[str, Any],
    *,
    root: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], Counter[str], int]:
    rows: dict[str, dict[str, Any]] = {}
    dupes: Counter[str] = Counter()
    outside_window = 0
    for row in iter_jsonl(trade_path(prefix, root=root)):
        if not row_in_summary_window(row, summary):
            outside_window += 1
            continue
        key = trade_key(row)
        if not key:
            continue
        if key in rows:
            dupes[key] += 1
            continue
        rows[key] = row
    return rows, dupes, outside_window


def trade_identity_ledger_status(
    *,
    prefix: str,
    role: str,
    metrics: Mapping[str, Any],
    rows: Mapping[str, Mapping[str, Any]],
    duplicate_keys: Mapping[str, int],
    outside_window: int,
    root: Path | None = None,
) -> dict[str, Any]:
    path = trade_path(prefix, root=root)
    expected_rows = inum(
        metrics.get("physical_trades")
        if metrics.get("physical_trades") is not None
        else metrics.get("trades")
    )
    duplicate_rows = sum(inum(value) for value in duplicate_keys.values())
    observed_rows = len(rows) + duplicate_rows
    path_present = path.exists()
    path_nonempty = path_present and path.stat().st_size > 0

    if duplicate_rows:
        status = f"{role}_trade_ledger_duplicate_identity_keys"
        comparable = False
    elif observed_rows != expected_rows:
        if not path_present and expected_rows > 0:
            status = f"missing_{role}_trade_ledger"
        elif not path_nonempty and expected_rows > 0:
            status = f"empty_{role}_trade_ledger"
        else:
            status = f"{role}_trade_ledger_row_count_mismatch"
        comparable = False
    elif expected_rows == 0:
        status = f"{role}_zero_expected_trades"
        comparable = True
    elif not path_nonempty:
        status = f"missing_{role}_trade_ledger"
        comparable = False
    else:
        status = "present"
        comparable = True

    result = {
        "role": role,
        "status": status,
        "comparable": comparable,
        "path": str(path),
        "path_present": path_present,
        "path_nonempty": path_nonempty,
        "expected_rows_inside_summary_window": expected_rows,
        "observed_rows_inside_summary_window": observed_rows,
        "unique_identity_keys_inside_summary_window": len(rows),
        "duplicate_identity_rows_inside_summary_window": duplicate_rows,
        "rows_outside_summary_window": outside_window,
    }
    if path_nonempty:
        result["byte_count"] = path.stat().st_size
        result["sha256"] = sha256_file(path)
    return result


def trade_identity_comparison_status(
    baseline_status: Mapping[str, Any],
    candidate_status: Mapping[str, Any],
) -> str:
    unavailable = [
        str(status.get("status") or f"{role}_trade_identity_unavailable")
        for role, status in (
            ("baseline", baseline_status),
            ("candidate", candidate_status),
        )
        if not value_bool_true(status.get("comparable"))
    ]
    if not unavailable:
        return "computed"
    return "not_computed_" + "_and_".join(unavailable)


def load_candidate_projection_map(
    prefix: str,
    summary: Mapping[str, Any],
    *,
    root: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], Counter[str], int, Path]:
    path = candidate_projection_path(prefix, root=root)
    rows: dict[str, dict[str, Any]] = {}
    dupes: Counter[str] = Counter()
    outside_window = 0
    for row in iter_jsonl(path):
        if not row_in_summary_window(row, summary):
            outside_window += 1
            continue
        key = trade_key(row)
        if not key:
            continue
        if key in rows:
            dupes[key] += 1
            continue
        rows[key] = row
    return rows, dupes, outside_window, path


def baseline_result_authority_class(row: Mapping[str, Any]) -> str:
    if value_bool_true(row.get("headline_result_authority")) or value_bool_true(
        row.get("ordered_tick_final_r_authority")
    ):
        return "ordered_tick_headline_authority"
    authority_text = " ".join(
        str(row.get(field) or "").lower()
        for field in (
            "terminal_r_path_authority",
            "terminal_r_authority_status",
            "selected_execution_policy_replay_final_r_authority_status",
            "fill_realism_class",
        )
    )
    if value_bool_true(row.get("m1_proxy_replay_authority")) or "m1_proxy" in authority_text:
        return "m1_proxy_diagnostic_authority"
    return "replay_proxy_authority_unspecified"


def removed_trade_blocker_stage(projection: Mapping[str, Any] | None) -> str:
    if not isinstance(projection, MappingABC) or not projection:
        return "candidate_generation_absent_current_config"
    exact_stage = str(projection.get("exact_deviation_stage") or "").strip()
    if exact_stage == "selector":
        return "selector_admission"
    if exact_stage == "scheduler":
        return "scheduler_allocation"
    if exact_stage in {"terminal_fallback", "fill", "fillability"}:
        return "order_fillability_lifecycle"
    if projection.get("scorecard_present") is not True:
        return "selector_admission"
    if projection.get("scheduler_selected") is not True:
        return "scheduler_allocation"
    if projection.get("order_present") is not True:
        return "order_materialization"
    if projection.get("trade_present") is not True:
        return "order_fillability_lifecycle"
    return "current_trade_present_identity_mismatch"


def removed_trade_projection_classification(
    *,
    removed_keys: Iterable[str],
    baseline_trades: Mapping[str, Mapping[str, Any]],
    candidate_projection: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    stage_counts: Counter[str] = Counter()
    stage_outcome_counts: Counter[str] = Counter()
    authority_counts: Counter[str] = Counter()
    net_r_by_stage: defaultdict[str, float] = defaultdict(float)
    net_r_by_authority: defaultdict[str, float] = defaultdict(float)
    projection_matches = 0

    for key in sorted(removed_keys):
        baseline = baseline_trades.get(key, {})
        projection = candidate_projection.get(key)
        projection_present = isinstance(projection, MappingABC) and bool(projection)
        projection_row = projection if projection_present else {}
        if projection_present:
            projection_matches += 1
        stage = removed_trade_blocker_stage(projection)
        net_r = fnum(
            baseline.get("net_proxy_r")
            if baseline.get("net_proxy_r") not in (None, "")
            else baseline.get("net_r")
        )
        outcome = "positive" if net_r > 0 else "negative" if net_r < 0 else "flat"
        authority_class = baseline_result_authority_class(baseline)
        stage_counts[stage] += 1
        stage_outcome_counts[f"{stage}:{outcome}"] += 1
        authority_counts[authority_class] += 1
        net_r_by_stage[stage] += net_r
        net_r_by_authority[authority_class] += net_r
        blocker_reason = str(
            projection_row.get("exact_deviation_reason")
            or projection_row.get("package_order_executable_blocker_reason")
            or projection_row.get("effective_selector_reason")
            or projection_row.get("risk_finalizer_reason")
            or projection_row.get("miss_reason")
            or "candidate_instance_absent_from_current_projection"
        )
        rows.append(
            {
                "candidate_instance_key": key,
                "candidate_id": baseline.get("candidate_id"),
                "decision_time_utc": baseline.get("decision_time_utc")
                or baseline.get("decision_time"),
                "symbol": baseline.get("symbol"),
                "side": baseline.get("side") or baseline.get("direction"),
                "baseline_net_r": round(net_r, 8),
                "baseline_gross_r": round(fnum(baseline.get("gross_r")), 8),
                "baseline_final_r": round(fnum(baseline.get("final_r")), 8),
                "baseline_cash_pnl": round(
                    fnum(baseline.get("pnl_cash") or baseline.get("cash_pnl")),
                    8,
                ),
                "baseline_terminal_outcome": baseline.get("terminal_outcome"),
                "baseline_result_authority_class": authority_class,
                "candidate_projection_present": projection_present,
                "current_blocker_stage": stage,
                "current_blocker_reason": blocker_reason,
                "effective_selector_action": projection_row.get(
                    "effective_selector_action"
                ),
                "effective_selector_reason": projection_row.get(
                    "effective_selector_reason"
                ),
                "scorecard_present": projection_row.get("scorecard_present"),
                "scheduler_selected": projection_row.get("scheduler_selected"),
                "scheduler_rank": projection_row.get("scheduler_rank"),
                "risk_behavior": projection_row.get("risk_behavior"),
                "risk_finalizer_action": projection_row.get(
                    "risk_finalizer_action"
                ),
                "risk_finalizer_reason": projection_row.get(
                    "risk_finalizer_reason"
                ),
                "package_order_executable_allowed": projection_row.get(
                    "package_order_executable_allowed"
                ),
                "package_order_executable_transfer_status": projection_row.get(
                    "package_order_executable_transfer_status"
                ),
                "package_order_executable_blocker_class": projection_row.get(
                    "package_order_executable_blocker_class"
                ),
                "package_order_executable_blocker_reason": projection_row.get(
                    "package_order_executable_blocker_reason"
                ),
                "order_present": projection_row.get("order_present"),
                "order_status": projection_row.get("order_status"),
                "trade_present": projection_row.get("trade_present"),
                "missed_present": projection_row.get("missed_present"),
                "miss_reason": projection_row.get("miss_reason"),
                "lifecycle_action": projection_row.get("lifecycle_action"),
                "lifecycle_reason": projection_row.get("lifecycle_reason"),
                "terminal_fill_status": projection_row.get("terminal_fill_status"),
                "current_terminal_outcome": projection_row.get("terminal_outcome"),
            }
        )

    rollup = {
        "removed_trade_count": len(rows),
        "candidate_projection_match_count": projection_matches,
        "candidate_projection_missing_count": len(rows) - projection_matches,
        "blocker_stage_counts": dict(sorted(stage_counts.items())),
        "blocker_stage_outcome_counts": dict(sorted(stage_outcome_counts.items())),
        "baseline_net_r_by_blocker_stage": {
            key: round(value, 8) for key, value in sorted(net_r_by_stage.items())
        },
        "baseline_result_authority_counts": dict(sorted(authority_counts.items())),
        "baseline_net_r_by_result_authority": {
            key: round(value, 8)
            for key, value in sorted(net_r_by_authority.items())
        },
    }
    return rows, rollup


ORDER_EXECUTABLE_ALLOWED_KEYS = (
    "package_replay_order_executable_candidate_use_allowed",
    "package_new_entry_authority_package_replay_order_executable_candidate_use_allowed",
    "scorecard_reported_package_replay_order_executable_candidate_use_allowed",
    "risk_finalizer_best_package_probe_package_replay_order_executable_candidate_use_allowed",
    "finalizer_primary_probe_package_replay_order_executable_candidate_use_allowed",
    "risk_finalizer_package_replay_order_executable_candidate_use_allowed",
)


def value_bool_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def value_bool_false(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip().lower() in {"0", "false", "no", "n"}
    return False


def order_executable_transfer_allowed(row: Mapping[str, Any]) -> bool | None:
    for key in ORDER_EXECUTABLE_ALLOWED_KEYS:
        if key not in row or row.get(key) in (None, ""):
            continue
        if value_bool_true(row.get(key)):
            return True
        if value_bool_false(row.get(key)):
            return False
    return None


def order_executable_transfer_rollup(
    prefix: str,
    summary: Mapping[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    ledgers = {
        "scorecard": scorecard_path(prefix, root=root),
        "order": order_path(prefix, root=root),
        "trade": trade_path(prefix, root=root),
        "missed": missed_path(prefix, root=root),
    }
    row_counts: Counter[str] = Counter()
    transfer_status_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    blocker_reason_counts: Counter[str] = Counter()
    unbound_allowed_counts: Counter[str] = Counter()
    net_r_by_ledger_status: defaultdict[str, float] = defaultdict(float)
    outside_window: Counter[str] = Counter()
    missing_ledgers: list[str] = []
    sample_unbound: list[dict[str, Any]] = []

    expected_ledger_rows = {
        "scorecard": inum(summary.get("scorecard_rows")),
        "order": inum(
            first_profile_stats(summary).get("order_event_rows")
            or first_profile_stats(summary).get("order_rows")
            or summary.get("order_rows")
        ),
        "trade": inum(
            first_profile_stats(summary).get("trade_rows")
            or summary.get("trade_rows")
        ),
        "missed": inum(
            first_profile_stats(summary).get("missed_opportunity_rows")
            or summary.get("missed_opportunity_rows")
        ),
    }
    materialized_missing_ledgers: list[str] = []
    comparator_failures: Counter[str] = Counter()

    for ledger_name, path in ledgers.items():
        if not path.exists():
            missing_ledgers.append(ledger_name)
            if expected_ledger_rows.get(ledger_name, 0) > 0:
                materialized_missing_ledgers.append(ledger_name)
                comparator_failures[f"{ledger_name}:expected_ledger_missing"] += 1
            continue
        for row in iter_jsonl(path):
            if not row_in_summary_window(row, summary):
                outside_window[ledger_name] += 1
                continue
            row_counts[f"{ledger_name}_rows"] += 1
            allowed = order_executable_transfer_allowed(row)
            if allowed is True:
                row_counts[f"{ledger_name}_order_executable_true_rows"] += 1
            elif allowed is False:
                row_counts[f"{ledger_name}_order_executable_false_rows"] += 1
                continue
            else:
                row_counts[f"{ledger_name}_order_executable_unknown_rows"] += 1
                continue
            status = str(
                row.get("package_replay_order_executable_transfer_status") or "missing"
            ).strip() or "missing"
            blocker = str(
                row.get("package_replay_order_executable_final_blocker_class")
                or "missing"
            ).strip() or "missing"
            reason = str(
                row.get("package_replay_order_executable_final_blocker_reason")
                or "missing"
            ).strip() or "missing"
            transfer_status_counts[f"{ledger_name}:{status}"] += 1
            if status == "final_blocked" or blocker != "missing":
                blocker_counts[f"{ledger_name}:{blocker}"] += 1
                blocker_reason_counts[f"{ledger_name}:{reason}"] += 1
            if status not in {"order_bound", "trade_bound", "final_blocked"}:
                unbound_allowed_counts[f"{ledger_name}:{status}"] += 1
                if ledger_name in {"order", "trade"}:
                    comparator_failures[
                        f"{ledger_name}:order_executable_true_without_transfer_status"
                        if status == "missing"
                        else f"{ledger_name}:order_executable_true_unbound:{status}"
                    ] += 1
                if len(sample_unbound) < 16:
                    sample_unbound.append(
                        {
                            "ledger": ledger_name,
                            "candidate_id": row.get("candidate_id")
                            or row.get("scorecard_candidate_id"),
                            "decision_time_utc": row.get("decision_time_utc")
                            or row.get("decision_time"),
                            "symbol": row.get("symbol"),
                            "side": row.get("side") or row.get("direction"),
                            "transfer_status": status,
                            "blocker_class": blocker if blocker != "missing" else None,
                            "blocker_reason": reason if reason != "missing" else None,
                        }
                    )
            net_r_by_ledger_status[f"{ledger_name}:{status}"] += fnum(
                row.get("net_r")
                or row.get("missed_opportunity_net_r")
                or row.get("counterfactual_net_r")
            )

    return {
        "paths": {name: str(path) for name, path in ledgers.items()},
        "missing_ledgers": missing_ledgers,
        "materialized_missing_ledgers": materialized_missing_ledgers,
        "comparator_failures": dict(sorted(comparator_failures.items())),
        "row_counts": dict(sorted(row_counts.items())),
        "outside_summary_window": dict(sorted(outside_window.items())),
        "transfer_status_counts": dict(sorted(transfer_status_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "blocker_reason_counts": dict(sorted(blocker_reason_counts.items())),
        "unbound_allowed_counts": dict(sorted(unbound_allowed_counts.items())),
        "net_r_by_ledger_status": {
            key: round(value, 8)
            for key, value in sorted(net_r_by_ledger_status.items())
        },
        "sample_unbound": sample_unbound,
    }


def risk_ladder(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("risk_expression_ladder")
    if isinstance(value, MappingABC):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, MappingABC) else {}
    return {}


def row_list_values(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    if isinstance(value, IterableABC) and not isinstance(value, (bytes, bytearray, MappingABC)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def trade_rollup(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(rows)

    def row_net_r(row: Mapping[str, Any]) -> float | None:
        for field in ("net_r", "net_proxy_r"):
            value = row.get(field)
            if value in (None, ""):
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        return None

    symbol_net: defaultdict[str, float] = defaultdict(float)
    side_counts: Counter[str] = Counter()
    day_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    close_reason_counts: Counter[str] = Counter()
    risk_ladder_tier_counts: Counter[str] = Counter()
    ladder_cause_histogram: Counter[str] = Counter()
    fill_realism_class_counts: Counter[str] = Counter()
    fill_realism_executable_counts: Counter[str] = Counter()
    fill_realism_reason_counts: Counter[str] = Counter()
    fill_realism_class_net_r: defaultdict[str, float] = defaultdict(float)
    scoreable_rows = 0
    terminal_r_unscoreable_rows = 0
    for row in rows:
        symbol = str(row.get("symbol") or "unknown")
        net_r_value = row_net_r(row)
        if net_r_value is not None:
            scoreable_rows += 1
            symbol_net[symbol] += net_r_value
        if row.get("terminal_r_scoreable") is False:
            terminal_r_unscoreable_rows += 1
        side_counts[str(row.get("side") or row.get("direction") or "unknown")] += 1
        day_counts[str(row.get("decision_time_utc") or "")[:10] or "unknown"] += 1
        session_counts[
            str(row.get("route_session") or row.get("session") or row.get("session_bucket") or "unknown")
        ] += 1
        close_reason_counts[str(row.get("close_reason") or "unknown")] += 1
        ladder = risk_ladder(row)
        tier = str(
            row.get("risk_expression_ladder_tier")
            or ladder.get("ladder_tier")
            or row.get("risk_decision")
            or "unknown"
        ).strip() or "unknown"
        risk_ladder_tier_counts[tier] += 1
        for cause in row_list_values(
            row.get("risk_expression_ladder_tier_causes")
            or ladder.get("tier_causes")
            or ladder.get("ladder_tier_causes")
        ):
            ladder_cause_histogram[cause] += 1
        fill_realism = str(row.get("fill_realism_class") or "unknown").strip() or "unknown"
        fill_realism_class_counts[fill_realism] += 1
        fill_realism_executable_counts[
            str(row.get("fill_realism_executable"))
        ] += 1
        fill_realism_reason_counts[
            str(row.get("fill_realism_reason") or "unknown")
        ] += 1
        if net_r_value is not None:
            fill_realism_class_net_r[fill_realism] += net_r_value
    scoreable_net_values = [
        value for row in rows if (value := row_net_r(row)) is not None
    ]
    wins = sum(value > 0 for value in scoreable_net_values)
    losses = sum(value < 0 for value in scoreable_net_values)
    flats = sum(value == 0 for value in scoreable_net_values)
    return {
        "count": len(rows),
        "scoreable_count": scoreable_rows,
        "unscoreable_count": len(rows) - scoreable_rows,
        "terminal_r_unscoreable_count": terminal_r_unscoreable_rows,
        "net_r": round(sum(scoreable_net_values), 8),
        "gross_r": round(sum(fnum(row.get("gross_r")) for row in rows), 8),
        "final_r": round(sum(fnum(row.get("final_r")) for row in rows), 8),
        "cash_pnl": round(
            sum(
                fnum(
                    row.get("pnl_cash")
                    if row.get("pnl_cash") not in (None, "")
                    else row.get("cash_pnl")
                )
                for row in rows
            ),
            8,
        ),
        "risk_cash": round(sum(fnum(row.get("risk_cash")) for row in rows), 8),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "net_by_symbol": {k: round(v, 8) for k, v in sorted(symbol_net.items())},
        "side_counts": dict(sorted(side_counts.items())),
        "day_counts": dict(sorted(day_counts.items())),
        "session_counts": dict(sorted(session_counts.items())),
        "close_reason_counts": dict(sorted(close_reason_counts.items())),
        "risk_ladder_tier_counts": dict(sorted(risk_ladder_tier_counts.items())),
        "full_risk_count": risk_ladder_tier_counts.get("full", 0),
        "reduced_risk_count": (
            risk_ladder_tier_counts.get("reduced", 0)
            + risk_ladder_tier_counts.get("open-reduced-risk", 0)
        ),
        "ladder_cause_histogram": dict(sorted(ladder_cause_histogram.items())),
        "fill_realism_class_counts": dict(sorted(fill_realism_class_counts.items())),
        "fill_realism_executable_counts": dict(sorted(fill_realism_executable_counts.items())),
        "fill_realism_reason_counts": dict(sorted(fill_realism_reason_counts.items())),
        "fill_realism_class_net_r": {
            k: round(v, 8) for k, v in sorted(fill_realism_class_net_r.items())
        },
        "sample_keys": [trade_key(row) for row in rows[:25]],
    }


def diff_metrics(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    keys = [
        "candidate_rows",
        "decision_rows",
        "scorecard_rows",
        "order_event_rows",
        "order_rows",
        "trades",
        "filled_trade_count",
        "headline_trades",
        "headline_net_r",
        "headline_gross_r",
        "headline_final_r",
        "headline_cash_pnl",
        "headline_wins",
        "headline_losses",
        "headline_flats",
        "physical_trades",
        "physical_scoreable_trades",
        "physical_unscoreable_trades",
        "entry_fill_executable_trades",
        "terminal_r_unscoreable_trades",
        "physical_net_r",
        "physical_gross_r",
        "physical_final_r",
        "physical_cash_pnl",
        "physical_risk_cash",
        "physical_risk_pct",
        "physical_wins",
        "physical_losses",
        "physical_flats",
        "diagnostic_trades",
        "diagnostic_net_r",
        "diagnostic_wins",
        "diagnostic_losses",
        "diagnostic_flats",
        "net_r",
        "gross_r",
        "final_r",
        "cash_pnl",
        "risk_cash",
        "risk_pct",
        "wins",
        "losses",
        "flats",
        "expired_unfilled",
        "missed_rows",
        "missed_scoreable",
        "missed_unscoreable",
        "missed_positive_rows",
        "missed_positive_net_r",
        "missed_negative_rows",
        "missed_negative_net_r",
        "missed_total_scoreable_net_r",
        "missed_executable_scoreable",
        "missed_executable_net_r",
        "missed_diagnostic_scoreable",
        "missed_diagnostic_net_r",
        "missed_diagnostic_positive_rows",
        "missed_diagnostic_positive_net_r",
        "missed_diagnostic_negative_rows",
        "missed_diagnostic_negative_net_r",
    ]
    return {key: round(fnum(b.get(key)) - fnum(a.get(key)), 8) for key in keys}


def axis_delta(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    keys = sorted(set(a) | set(b))
    return {
        key: round(fnum(b.get(key)) - fnum(a.get(key)), 8)
        for key in keys
        if isinstance(a.get(key, 0), (int, float, str, type(None)))
        and isinstance(b.get(key, 0), (int, float, str, type(None)))
    }


def axis_delta_status(
    baseline_status: Mapping[str, Any],
    candidate_status: Mapping[str, Any],
) -> str:
    baseline = str(baseline_status.get("status") or "")
    candidate = str(candidate_status.get("status") or "")
    if baseline == "present" and candidate == "present":
        return "computed"
    missing = []
    if baseline != "present":
        missing.append(baseline or "baseline_axis_transfer_not_present")
    if candidate != "present":
        missing.append(candidate or "candidate_axis_transfer_not_present")
    return "not_computed_" + "_and_".join(missing)


def axis_scope_comparison(
    baseline_axis: Mapping[str, Any],
    candidate_axis: Mapping[str, Any],
    *,
    delta_status: str,
) -> dict[str, Any]:
    if delta_status != "computed":
        return {
            "status": "not_computed_axis_transfer_delta_not_computed",
            "source_bound_signal_additive_allowed": False,
            "executable_r_percentage_allowed": False,
            "field_deltas": {},
            "different_fields": [],
        }
    deltas: dict[str, float] = {}
    different: list[str] = []
    for field, aliases in AXIS_SCOPE_ALIGNMENT_FIELDS.items():
        baseline_value = fnum(
            next(
                (
                    baseline_axis.get(alias)
                    for alias in aliases
                    if baseline_axis.get(alias) not in (None, "")
                ),
                0.0,
            )
        )
        candidate_value = fnum(
            next(
                (
                    candidate_axis.get(alias)
                    for alias in aliases
                    if candidate_axis.get(alias) not in (None, "")
                ),
                0.0,
            )
        )
        delta = round(candidate_value - baseline_value, 8)
        deltas[field] = delta
        if abs(delta) > 1e-8:
            different.append(field)
    return {
        "status": (
            "same_window_axis_scope_values_differ"
            if different
            else "same_window_axis_scope_values_match"
        ),
        "source_bound_signal_additive_allowed": False,
        "executable_r_percentage_allowed": False,
        "field_deltas": deltas,
        "different_fields": different,
    }


def compare(
    baseline_prefix: str,
    candidate_prefix: str,
    *,
    baseline_root: Path | None = None,
    candidate_root: Path | None = None,
) -> dict[str, Any]:
    baseline_root = artifact_root(baseline_root)
    candidate_root = artifact_root(candidate_root)
    baseline = run_metrics(baseline_prefix, root=baseline_root)
    candidate = run_metrics(candidate_prefix, root=candidate_root)
    baseline_window = (baseline.get("date_start"), baseline.get("date_end"))
    candidate_window = (candidate.get("date_start"), candidate.get("date_end"))
    if baseline_window != candidate_window:
        raise ValueError(
            "comparison_requires_same_summary_window:"
            f"{baseline_prefix}={baseline_window},"
            f"{candidate_prefix}={candidate_window}"
        )
    profile = None
    profiles = candidate.get("profiles")
    if isinstance(profiles, list) and profiles:
        profile = str(profiles[0])
    baseline_axis, baseline_axis_status = load_axis_transfer_with_status(
        baseline_prefix,
        profile=profile,
        role="baseline",
        root=baseline_root,
    )
    candidate_axis, candidate_axis_status = load_axis_transfer_with_status(
        candidate_prefix,
        profile=profile,
        role="candidate",
        root=candidate_root,
    )
    transfer_delta_status = axis_delta_status(
        baseline_axis_status,
        candidate_axis_status,
    )
    scope_comparison = axis_scope_comparison(
        baseline_axis,
        candidate_axis,
        delta_status=transfer_delta_status,
    )
    baseline_trades, baseline_dupes, baseline_outside_window = load_trade_map(
        baseline_prefix,
        baseline,
        root=baseline_root,
    )
    candidate_trades, candidate_dupes, candidate_outside_window = load_trade_map(
        candidate_prefix,
        candidate,
        root=candidate_root,
    )
    baseline_trade_identity_status = trade_identity_ledger_status(
        prefix=baseline_prefix,
        role="baseline",
        metrics=baseline,
        rows=baseline_trades,
        duplicate_keys=baseline_dupes,
        outside_window=baseline_outside_window,
        root=baseline_root,
    )
    candidate_trade_identity_status = trade_identity_ledger_status(
        prefix=candidate_prefix,
        role="candidate",
        metrics=candidate,
        rows=candidate_trades,
        duplicate_keys=candidate_dupes,
        outside_window=candidate_outside_window,
        root=candidate_root,
    )
    identity_status = trade_identity_comparison_status(
        baseline_trade_identity_status,
        candidate_trade_identity_status,
    )
    identity_comparison_computed = identity_status == "computed"
    baseline_keys = set(baseline_trades)
    candidate_keys = set(candidate_trades)
    added_keys = (
        sorted(candidate_keys - baseline_keys) if identity_comparison_computed else []
    )
    removed_keys = (
        sorted(baseline_keys - candidate_keys) if identity_comparison_computed else []
    )
    common_keys = (
        sorted(baseline_keys & candidate_keys) if identity_comparison_computed else []
    )
    added = trade_rollup(candidate_trades[key] for key in added_keys)
    removed = trade_rollup(baseline_trades[key] for key in removed_keys)
    candidate_projection_ledger_path = candidate_projection_path(
        candidate_prefix,
        root=candidate_root,
    )
    candidate_projection: dict[str, dict[str, Any]] = {}
    candidate_projection_dupes: Counter[str] = Counter()
    candidate_projection_outside_window = 0
    if identity_comparison_computed and removed_keys:
        (
            candidate_projection,
            candidate_projection_dupes,
            candidate_projection_outside_window,
            candidate_projection_ledger_path,
        ) = load_candidate_projection_map(
            candidate_prefix,
            candidate,
            root=candidate_root,
        )
    if identity_comparison_computed:
        removed_projection_rows, removed_projection_rollup = (
            removed_trade_projection_classification(
                removed_keys=removed_keys,
                baseline_trades=baseline_trades,
                candidate_projection=candidate_projection,
            )
        )
    else:
        removed_projection_rows = []
        removed_projection_rollup = {
            "status": identity_status,
            "removed_trade_count": None,
            "candidate_projection_match_count": None,
            "candidate_projection_missing_count": None,
            "blocker_stage_counts": {},
            "blocker_stage_outcome_counts": {},
            "baseline_net_r_by_blocker_stage": {},
            "baseline_result_authority_counts": {},
            "baseline_net_r_by_result_authority": {},
        }
    return {
        "schema": "gtos.final_moonshot.broad_live_as_if_replay.same_window_comparison.v1",
        "baseline_prefix": baseline_prefix,
        "candidate_prefix": candidate_prefix,
        "window": f"{candidate.get('date_start') or baseline.get('date_start')}..{candidate.get('date_end') or baseline.get('date_end')}",
        "interpretation": "This smoke proves or disproves the local repair; it does not prove total reservoir conversion.",
        "baseline": baseline,
        "candidate": candidate,
        "summary_delta": diff_metrics(baseline, candidate),
        "baseline_axis_transfer": baseline_axis,
        "candidate_axis_transfer": candidate_axis,
        "baseline_axis_transfer_status": baseline_axis_status,
        "candidate_axis_transfer_status": candidate_axis_status,
        "axis_transfer_delta_status": transfer_delta_status,
        "axis_transfer_delta": (
            axis_delta(baseline_axis, candidate_axis)
            if transfer_delta_status == "computed"
            else {}
        ),
        "axis_transfer_scope_comparison": scope_comparison,
        "axis_transfer_denominator_comparison": {
            "status": "deprecated_non_additive_signal_not_denominator",
            "replacement": "axis_transfer_scope_comparison",
            "source_bound_signal_additive_allowed": False,
        },
        "trade_identity_comparison_status": identity_status,
        "trade_identity_comparison_authority": {
            "baseline": baseline_trade_identity_status,
            "candidate": candidate_trade_identity_status,
        },
        "baseline_trade_window_rollup": trade_rollup(baseline_trades.values()),
        "candidate_trade_window_rollup": trade_rollup(candidate_trades.values()),
        "baseline_order_executable_transfer_rollup": (
            order_executable_transfer_rollup(
                baseline_prefix,
                baseline,
                root=baseline_root,
            )
        ),
        "candidate_order_executable_transfer_rollup": (
            order_executable_transfer_rollup(
                candidate_prefix,
                candidate,
                root=candidate_root,
            )
        ),
        "trade_key_counts": {
            "baseline": len(baseline_trades),
            "candidate": len(candidate_trades),
            "common": len(common_keys) if identity_comparison_computed else None,
            "added": len(added_keys) if identity_comparison_computed else None,
            "removed": len(removed_keys) if identity_comparison_computed else None,
            "baseline_dups": sum(baseline_dupes.values()),
            "candidate_dups": sum(candidate_dupes.values()),
            "baseline_outside_summary_window": baseline_outside_window,
            "candidate_outside_summary_window": candidate_outside_window,
        },
        "added_trade_keys": added_keys,
        "removed_trade_keys": removed_keys,
        "common_trade_keys": common_keys,
        "removed_trade_current_projection_rows": removed_projection_rows,
        "removed_trade_current_projection_rollup": {
            **removed_projection_rollup,
            "candidate_projection_ledger_present": (
                candidate_projection_ledger_path.exists()
            ),
            "candidate_projection_ledger_row_count": len(candidate_projection),
            "candidate_projection_duplicate_key_count": sum(
                candidate_projection_dupes.values()
            ),
            "candidate_projection_outside_summary_window": (
                candidate_projection_outside_window
            ),
        },
        "added_trades": added,
        "removed_trades": removed,
        "added_transfer_net_positive": (
            added["net_r"] > 0 if identity_comparison_computed else None
        ),
        "removed_transfer_net_positive": (
            removed["net_r"] > 0 if identity_comparison_computed else None
        ),
        "added_minus_removed_net_r": (
            round(added["net_r"] - removed["net_r"], 8)
            if identity_comparison_computed
            else None
        ),
        "artifacts": {
            "baseline_artifact_root": str(baseline_root),
            "candidate_artifact_root": str(candidate_root),
            "baseline_summary": str(summary_path(baseline_prefix, root=baseline_root)),
            "candidate_summary": str(summary_path(candidate_prefix, root=candidate_root)),
            "baseline_trade_ledger": str(trade_path(baseline_prefix, root=baseline_root)),
            "candidate_trade_ledger": str(trade_path(candidate_prefix, root=candidate_root)),
            "baseline_order_ledger": str(order_path(baseline_prefix, root=baseline_root)),
            "candidate_order_ledger": str(order_path(candidate_prefix, root=candidate_root)),
            "baseline_scorecard_ledger": str(scorecard_path(baseline_prefix, root=baseline_root)),
            "candidate_scorecard_ledger": str(scorecard_path(candidate_prefix, root=candidate_root)),
            "baseline_missed_ledger": str(missed_path(baseline_prefix, root=baseline_root)),
            "candidate_missed_ledger": str(missed_path(candidate_prefix, root=candidate_root)),
            "baseline_parity_summary": str(parity_summary_path(baseline_prefix, root=baseline_root)),
            "candidate_parity_summary": str(parity_summary_path(candidate_prefix, root=candidate_root)),
            "candidate_instance_parity_projection": str(
                candidate_projection_ledger_path
            ),
        },
    }


def behavior_dossier(result: Mapping[str, Any]) -> str:
    baseline = result.get("baseline") if isinstance(result.get("baseline"), MappingABC) else {}
    candidate = result.get("candidate") if isinstance(result.get("candidate"), MappingABC) else {}
    delta = result.get("summary_delta") if isinstance(result.get("summary_delta"), MappingABC) else {}
    added = result.get("added_trades") if isinstance(result.get("added_trades"), MappingABC) else {}
    removed = result.get("removed_trades") if isinstance(result.get("removed_trades"), MappingABC) else {}
    candidate_rollup = (
        result.get("candidate_trade_window_rollup")
        if isinstance(result.get("candidate_trade_window_rollup"), MappingABC)
        else {}
    )
    order_transfer = (
        result.get("candidate_order_executable_transfer_rollup")
        if isinstance(result.get("candidate_order_executable_transfer_rollup"), MappingABC)
        else {}
    )
    row_counts = (
        order_transfer.get("row_counts")
        if isinstance(order_transfer.get("row_counts"), MappingABC)
        else {}
    )
    blocker_counts = (
        order_transfer.get("blocker_counts")
        if isinstance(order_transfer.get("blocker_counts"), MappingABC)
        else {}
    )
    baseline_axis_status = (
        result.get("baseline_axis_transfer_status")
        if isinstance(result.get("baseline_axis_transfer_status"), MappingABC)
        else {}
    )
    candidate_axis_status = (
        result.get("candidate_axis_transfer_status")
        if isinstance(result.get("candidate_axis_transfer_status"), MappingABC)
        else {}
    )
    axis_scope = (
        result.get("axis_transfer_scope_comparison")
        if isinstance(result.get("axis_transfer_scope_comparison"), MappingABC)
        else {}
    )
    identity_authority = (
        result.get("trade_identity_comparison_authority")
        if isinstance(result.get("trade_identity_comparison_authority"), MappingABC)
        else {}
    )
    removed_projection = (
        result.get("removed_trade_current_projection_rollup")
        if isinstance(
            result.get("removed_trade_current_projection_rollup"), MappingABC
        )
        else {}
    )
    lines = [
        f"# Broad Live-As-If Replay Behavior - {candidate.get('prefix')}",
        "",
        "Broker/live/final authority remains closed. This is replay/proxy behavior only.",
        "",
        "## Same-Window Result",
        "",
        f"- Window: `{result.get('window')}`",
        (
            "- Baseline headline: "
            f"trades `{baseline.get('headline_trades')}`, "
            f"net `{baseline.get('headline_net_r')}`, "
            f"gross `{baseline.get('headline_gross_r')}`, "
            f"final `{baseline.get('headline_final_r')}`, "
            f"cash `{baseline.get('headline_cash_pnl')}`, W/L/F "
            f"`{baseline.get('headline_wins')}/{baseline.get('headline_losses')}/{baseline.get('headline_flats')}`"
        ),
        (
            "- Candidate headline: "
            f"trades `{candidate.get('headline_trades')}`, "
            f"net `{candidate.get('headline_net_r')}`, "
            f"gross `{candidate.get('headline_gross_r')}`, "
            f"final `{candidate.get('headline_final_r')}`, "
            f"cash `{candidate.get('headline_cash_pnl')}`, W/L/F "
            f"`{candidate.get('headline_wins')}/{candidate.get('headline_losses')}/{candidate.get('headline_flats')}`"
        ),
        (
            "- Headline delta: "
            f"trades `{delta.get('headline_trades')}`, "
            f"net `{delta.get('headline_net_r')}`, "
            f"gross `{delta.get('headline_gross_r')}`, "
            f"final `{delta.get('headline_final_r')}`, "
            f"cash `{delta.get('headline_cash_pnl')}`, "
            f"W/L/F `{delta.get('headline_wins')}/{delta.get('headline_losses')}/{delta.get('headline_flats')}`"
        ),
        (
            "- Baseline all physical: "
            f"trades `{baseline.get('physical_trades')}`, "
            f"net `{baseline.get('physical_net_r')}`, "
            f"gross `{baseline.get('physical_gross_r')}`, "
            f"final `{baseline.get('physical_final_r')}`, "
            f"cash `{baseline.get('physical_cash_pnl')}`, W/L/F "
            f"`{baseline.get('physical_wins')}/{baseline.get('physical_losses')}/{baseline.get('physical_flats')}`"
        ),
        (
            "- Candidate all physical: "
            f"trades `{candidate.get('physical_trades')}`, "
            f"net `{candidate.get('physical_net_r')}`, "
            f"gross `{candidate.get('physical_gross_r')}`, "
            f"final `{candidate.get('physical_final_r')}`, "
            f"cash `{candidate.get('physical_cash_pnl')}`, W/L/F "
            f"`{candidate.get('physical_wins')}/{candidate.get('physical_losses')}/{candidate.get('physical_flats')}`"
        ),
        (
            "- Physical delta: "
            f"trades `{delta.get('physical_trades')}`, "
            f"net `{delta.get('physical_net_r')}`, "
            f"gross `{delta.get('physical_gross_r')}`, "
            f"final `{delta.get('physical_final_r')}`, "
            f"cash `{delta.get('physical_cash_pnl')}`, "
            f"W/L/F `{delta.get('physical_wins')}/{delta.get('physical_losses')}/{delta.get('physical_flats')}`"
        ),
        "",
        "## Added / Removed Transfers",
        "",
        f"- Identity comparison status: `{result.get('trade_identity_comparison_status')}`",
        f"- Baseline identity authority: `{identity_authority.get('baseline')}`",
        f"- Candidate identity authority: `{identity_authority.get('candidate')}`",
        (
            "- Added: "
            f"count `{added.get('count')}`, net `{added.get('net_r')}`, "
            f"gross `{added.get('gross_r')}`, final `{added.get('final_r')}`, "
            f"W/L/F `{added.get('wins')}/{added.get('losses')}/{added.get('flats')}`"
        ),
        (
            "- Removed: "
            f"count `{removed.get('count')}`, net `{removed.get('net_r')}`, "
            f"gross `{removed.get('gross_r')}`, final `{removed.get('final_r')}`, "
            f"W/L/F `{removed.get('wins')}/{removed.get('losses')}/{removed.get('flats')}`"
        ),
        f"- Added transfer net positive: `{result.get('added_transfer_net_positive')}`",
        f"- Removed transfer net positive: `{result.get('removed_transfer_net_positive')}`",
        f"- Added minus removed net R: `{result.get('added_minus_removed_net_r')}`",
        f"- Removed current-projection matches / missing: `{removed_projection.get('candidate_projection_match_count')}` / `{removed_projection.get('candidate_projection_missing_count')}`",
        f"- Removed blocker stages: `{removed_projection.get('blocker_stage_counts')}`",
        f"- Removed baseline net R by current blocker: `{removed_projection.get('baseline_net_r_by_blocker_stage')}`",
        f"- Removed baseline result authority: `{removed_projection.get('baseline_result_authority_counts')}`",
        "",
        "## Candidate Behavior",
        "",
        f"- Candidate rows: `{candidate.get('candidate_rows')}`",
        f"- Decision rows: `{candidate.get('decision_rows')}`",
        f"- Scorecard rows: `{candidate.get('scorecard_rows')}`",
        f"- Order events / orders: `{candidate.get('order_event_rows')}` / `{candidate.get('order_rows')}`",
        f"- Missed rows / scoreable: `{candidate.get('missed_rows')}` / `{candidate.get('missed_scoreable')}`",
        f"- Risk cash / risk pct: `{candidate.get('risk_cash')}` / `{candidate.get('risk_pct')}`",
        f"- Trade sessions: `{candidate_rollup.get('session_counts')}`",
        f"- Trade sides: `{candidate_rollup.get('side_counts')}`",
        f"- Net by symbol: `{candidate_rollup.get('net_by_symbol')}`",
        f"- Close reasons: `{candidate_rollup.get('close_reason_counts')}`",
        f"- Risk ladder tiers: `{candidate_rollup.get('risk_ladder_tier_counts')}`",
        f"- Baseline axis transfer status: `{baseline_axis_status.get('status')}`",
        f"- Candidate axis transfer status: `{candidate_axis_status.get('status')}`",
        f"- Axis transfer delta status: `{result.get('axis_transfer_delta_status')}`",
        f"- Axis scope comparison: `{axis_scope.get('status')}`",
        "",
        "## Order-Executable Transfer",
        "",
        f"- Row counts: `{row_counts}`",
        f"- Transfer status counts: `{order_transfer.get('transfer_status_counts')}`",
        f"- Blocker counts: `{blocker_counts}`",
        f"- Comparator failures: `{order_transfer.get('comparator_failures')}`",
        "",
        "## Interpretation",
        "",
        "- This artifact is normalized to the replay window shown above.",
        "- It does not compare the one-day result to the global source-bound reservoir.",
        "- Improvement is only valid if verifier scans remain clean and opportunity is not merely suppressed.",
        "",
    ]
    return "\n".join(lines)


def comparison_artifact_stem(candidate_prefix: str, baseline_prefix: str) -> str:
    full = f"{candidate_prefix}_VS_{baseline_prefix}"
    if len(full) <= MAX_COMPARISON_ARTIFACT_STEM_CHARS:
        return full
    digest = hashlib.sha256(full.encode("utf-8")).hexdigest()[:16]
    candidate = candidate_prefix.removeprefix(BROAD_PREFIX_STEM)
    baseline = baseline_prefix.removeprefix(BROAD_PREFIX_STEM)
    shortened = f"{candidate[:86]}_VS_{baseline[:64]}_{digest}"
    return shortened[:MAX_COMPARISON_ARTIFACT_STEM_CHARS]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-prefix", required=True)
    parser.add_argument("--candidate-prefix", required=True)
    parser.add_argument(
        "--baseline-root",
        default=None,
        help="Artifact directory for the baseline prefix; defaults to this route.",
    )
    parser.add_argument(
        "--candidate-root",
        default=None,
        help="Artifact directory for the candidate prefix; defaults to this route.",
    )
    parser.add_argument("--output-path", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_root = (
        Path(args.baseline_root).expanduser().resolve()
        if args.baseline_root
        else ROUTE
    )
    candidate_root = (
        Path(args.candidate_root).expanduser().resolve()
        if args.candidate_root
        else ROUTE
    )
    result = compare(
        args.baseline_prefix,
        args.candidate_prefix,
        baseline_root=baseline_root,
        candidate_root=candidate_root,
    )
    output_path = (
        Path(args.output_path)
        if args.output_path
        else ROUTE
        / f"{comparison_artifact_stem(args.candidate_prefix, args.baseline_prefix)}_COMPARISON.json"
    )
    if not output_path.is_absolute():
        output_path = ROUTE / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_stem = comparison_artifact_stem(args.candidate_prefix, args.baseline_prefix)
    behavior_summary_path = ROUTE / f"{artifact_stem}_BEHAVIOR_COMPARISON_SUMMARY.json"
    behavior_dossier_path = ROUTE / f"{artifact_stem}_BEHAVIOR_DOSSIER.md"
    result["artifacts"]["behavior_comparison_summary"] = str(behavior_summary_path)
    result["artifacts"]["behavior_dossier"] = str(behavior_dossier_path)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    behavior_summary_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    behavior_dossier_path.write_text(behavior_dossier(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "broad_replay_same_window_comparison_materialized",
                "baseline_prefix": args.baseline_prefix,
                "candidate_prefix": args.candidate_prefix,
                "output_path": str(output_path),
                "behavior_summary_path": str(behavior_summary_path),
                "behavior_dossier_path": str(behavior_dossier_path),
                "trades_delta": result["summary_delta"]["trades"],
                "net_r_delta": result["summary_delta"]["net_r"],
                "trade_identity_comparison_status": result[
                    "trade_identity_comparison_status"
                ],
                "added_trade_count": result["added_trades"]["count"],
                "added_trade_net_r": result["added_trades"]["net_r"],
                "removed_trade_count": result["removed_trades"]["count"],
                "removed_trade_net_r": result["removed_trades"]["net_r"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
