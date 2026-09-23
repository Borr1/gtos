from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DATE_ID = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_06_legacy_vs_vnext_delta"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE_ID}.json"
STAGE05_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_VERIFIER_{DATE_ID}.json"
STAGE05_SHARD_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE_ID}.jsonl"
)
OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_LEDGER_{DATE_ID}.jsonl"
OUTPUT_REPORT = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_REPORT_{DATE_ID}.md"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_SUMMARY_{DATE_ID}.json"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE_ID}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE_ID}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE_ID}.jsonl"

SCENARIOS = (
    "old_gtos_live_current_j46_j49",
    "legacy_fixed_1_5r_comparator",
    "moonshot_be_after_trigger",
    "condition_router_challenger",
    "activated_default_source_bound_primary",
)
DIMENSIONS = (
    "overall",
    "symbol",
    "framework",
    "candidate_origin_family",
    "session_bucket",
    "year",
    "month",
    "week",
    "day",
    "source_window_complete",
    "activated_replay_disposition",
    "activated_selected_policy",
    "condition_selected_policy",
    "timeout_behavior",
    "nofill_behavior",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fnum(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def parse_time(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def minutes_between(start: Any, end: Any) -> float | None:
    start_dt = parse_time(start)
    end_dt = parse_time(end)
    if start_dt is None or end_dt is None:
        return None
    return (end_dt - start_dt).total_seconds() / 60.0


@dataclass
class Aggregate:
    candidate_count: int = 0
    selected_count: int = 0
    performance_count: int = 0
    total_r: float = 0.0
    wins: int = 0
    losses: int = 0
    zeros: int = 0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0
    blocked_winner_count: int = 0
    blocked_positive_r: float = 0.0
    avoided_loser_count: int = 0
    avoided_negative_r_abs: float = 0.0
    saved_loser_count: int = 0
    saved_loser_delta_r: float = 0.0
    missed_condition_winner_count: int = 0
    missed_condition_positive_r: float = 0.0
    old_live_leakage_count: int = 0
    timeout_count: int = 0
    nofill_count: int = 0
    hold_minutes_sum: float = 0.0
    hold_minutes_count: int = 0

    def update_performance(self, value: float | None) -> None:
        if value is None:
            return
        self.performance_count += 1
        self.total_r += value
        if value > 0:
            self.wins += 1
            self.gross_win_r += value
        elif value < 0:
            self.losses += 1
            self.gross_loss_r += abs(value)
        else:
            self.zeros += 1

    def to_row(self, scenario: str, dimension_type: str, dimension_value: str) -> dict[str, Any]:
        return {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "schema_version": "vnext_replacement_stage06_aggregate_delta_v1",
            "record_type": "aggregate_delta",
            "scenario": scenario,
            "dimension_type": dimension_type,
            "dimension_value": dimension_value,
            "candidate_count": self.candidate_count,
            "selected_count": self.selected_count,
            "performance_count": self.performance_count,
            "total_r": self.total_r,
            "expectancy_r": (
                self.total_r / self.performance_count if self.performance_count else None
            ),
            "win_rate": self.wins / self.performance_count if self.performance_count else None,
            "profit_factor": (
                self.gross_win_r / self.gross_loss_r if self.gross_loss_r else None
            ),
            "wins": self.wins,
            "losses": self.losses,
            "zeros": self.zeros,
            "gross_win_r": self.gross_win_r,
            "gross_loss_r": self.gross_loss_r,
            "blocked_winner_count": self.blocked_winner_count,
            "blocked_positive_r": self.blocked_positive_r,
            "avoided_loser_count": self.avoided_loser_count,
            "avoided_negative_r_abs": self.avoided_negative_r_abs,
            "saved_loser_count": self.saved_loser_count,
            "saved_loser_delta_r": self.saved_loser_delta_r,
            "missed_condition_winner_count": self.missed_condition_winner_count,
            "missed_condition_positive_r": self.missed_condition_positive_r,
            "old_live_leakage_count": self.old_live_leakage_count,
            "timeout_count": self.timeout_count,
            "nofill_count": self.nofill_count,
            "avg_hold_minutes": (
                self.hold_minutes_sum / self.hold_minutes_count
                if self.hold_minutes_count
                else None
            ),
        }


def scenario_value(row: dict[str, Any], scenario: str) -> float | None:
    if scenario == "old_gtos_live_current_j46_j49":
        return fnum((row.get("old_gtos_current_shadow") or {}).get("final_r"))
    if scenario == "legacy_fixed_1_5r_comparator":
        return fnum((row.get("legacy_fixed_1_5r_comparator") or {}).get("final_r"))
    if scenario == "moonshot_be_after_trigger":
        return fnum((row.get("moonshot_be_after_trigger") or {}).get("final_r"))
    if scenario == "condition_router_challenger":
        return fnum((row.get("condition_router_projection") or {}).get("selected_policy_final_r"))
    if scenario == "activated_default_source_bound_primary":
        activated = row.get("activated_default_router_projection") or {}
        if activated.get("activated_runtime_effect_would_apply") is True:
            return fnum(activated.get("selected_policy_final_r"))
    return None


def scenario_selected(row: dict[str, Any], scenario: str) -> bool:
    dynamic_available = (row.get("dynamic_policy_replay") or {}).get("available") is True
    if scenario == "activated_default_source_bound_primary":
        return (row.get("activated_default_router_projection") or {}).get(
            "activated_runtime_effect_would_apply"
        ) is True
    return dynamic_available


def policy_exit(row: dict[str, Any], policy: str | None) -> dict[str, Any]:
    if not policy:
        return {}
    return ((row.get("dynamic_policy_replay") or {}).get("policy_results") or {}).get(policy) or {}


def scenario_exit_reason(row: dict[str, Any], scenario: str) -> str | None:
    if scenario == "old_gtos_live_current_j46_j49":
        return (row.get("old_gtos_current_shadow") or {}).get("exit_reason")
    if scenario == "moonshot_be_after_trigger":
        return (row.get("moonshot_be_after_trigger") or {}).get("exit_reason")
    if scenario == "activated_default_source_bound_primary":
        policy = (row.get("activated_default_router_projection") or {}).get("selected_policy")
        return policy_exit(row, policy).get("exit_reason")
    if scenario == "condition_router_challenger":
        policy = (row.get("condition_router_projection") or {}).get("selected_policy")
        return policy_exit(row, policy).get("exit_reason")
    if scenario == "legacy_fixed_1_5r_comparator":
        return policy_exit(row, "legacy_fixed_1.5r").get("exit_reason")
    return None


def scenario_hold_minutes(row: dict[str, Any], scenario: str) -> float | None:
    if scenario == "activated_default_source_bound_primary":
        policy = (row.get("activated_default_router_projection") or {}).get("selected_policy")
    elif scenario == "condition_router_challenger":
        policy = (row.get("condition_router_projection") or {}).get("selected_policy")
    elif scenario == "old_gtos_live_current_j46_j49":
        policy = "live_current_j46_j49"
    elif scenario == "legacy_fixed_1_5r_comparator":
        policy = "legacy_fixed_1.5r"
    elif scenario == "moonshot_be_after_trigger":
        policy = "be_after_trigger"
    else:
        policy = None
    exit_time = policy_exit(row, policy).get("exit_time_utc")
    entry_time = ((row.get("bar_close_m15_path") or {}).get("entry_first_touch_utc"))
    return minutes_between(entry_time, exit_time)


def calendar_parts(row: dict[str, Any]) -> dict[str, str]:
    text = str(row.get("candle_time_utc") or "")
    dt = parse_time(text)
    if dt is None:
        return {"day": "unknown", "week": "unknown", "month": "unknown", "year": "unknown"}
    iso = dt.isocalendar()
    return {
        "day": dt.date().isoformat(),
        "week": f"{iso.year}-W{iso.week:02d}",
        "month": f"{dt.year}-{dt.month:02d}",
        "year": str(dt.year),
    }


def nofill_behavior(row: dict[str, Any]) -> str:
    reason = ((row.get("dynamic_policy_replay") or {}).get("exclusion_reason"))
    if reason == "entry_not_touched_within_replay_horizon":
        return "no_fill_entry_not_touched"
    state = ((row.get("bar_close_m15_path") or {}).get("pending_lifecycle_state"))
    if state and "no_fill" in str(state):
        return str(state)
    return "filled_or_not_applicable"


def timeout_behavior(row: dict[str, Any], scenario: str) -> str:
    exit_reason = scenario_exit_reason(row, scenario)
    if not exit_reason:
        return "no_exit_reason"
    text = str(exit_reason)
    if "time" in text or "path_end" in text:
        return text
    return "not_timeout"


def dimension_values(row: dict[str, Any], scenario: str) -> dict[str, str]:
    calendar = calendar_parts(row)
    activated = row.get("activated_default_router_projection") or {}
    condition = row.get("condition_router_projection") or {}
    return {
        "overall": "ALL",
        "symbol": str(row.get("symbol")),
        "framework": str(row.get("framework")),
        "candidate_origin_family": str(row.get("candidate_origin_family")),
        "session_bucket": str(row.get("session_bucket")),
        "year": calendar["year"],
        "month": calendar["month"],
        "week": calendar["week"],
        "day": calendar["day"],
        "source_window_complete": str(row.get("source_window_complete")),
        "activated_replay_disposition": str(row.get("activated_replay_disposition")),
        "activated_selected_policy": str(activated.get("selected_policy")),
        "condition_selected_policy": str(condition.get("selected_policy")),
        "timeout_behavior": timeout_behavior(row, scenario),
        "nofill_behavior": nofill_behavior(row),
    }


def update_aggregate(agg: Aggregate, row: dict[str, Any], scenario: str) -> None:
    agg.candidate_count += 1
    value = scenario_value(row, scenario)
    selected = scenario_selected(row, scenario)
    if selected:
        agg.selected_count += 1
    agg.update_performance(value)
    if scenario == "activated_default_source_bound_primary":
        old_r = scenario_value(row, "old_gtos_live_current_j46_j49")
        condition_r = scenario_value(row, "condition_router_challenger")
        if not selected and old_r is not None and old_r > 0:
            agg.blocked_winner_count += 1
            agg.blocked_positive_r += old_r
        if not selected and old_r is not None and old_r < 0:
            agg.avoided_loser_count += 1
            agg.avoided_negative_r_abs += abs(old_r)
        if selected and old_r is not None and old_r < 0 and value is not None and value > old_r:
            agg.saved_loser_count += 1
            agg.saved_loser_delta_r += value - old_r
        if not selected and condition_r is not None and condition_r > 0:
            agg.missed_condition_winner_count += 1
            agg.missed_condition_positive_r += condition_r
        if (
            row.get("activated_default_router_projection", {}).get("selected_policy")
            == "live_current_j46_j49"
        ):
            agg.old_live_leakage_count += 1
    reason = scenario_exit_reason(row, scenario)
    if reason and ("time" in str(reason) or "path_end" in str(reason)):
        agg.timeout_count += 1
    if nofill_behavior(row) != "filled_or_not_applicable":
        agg.nofill_count += 1
    hold = scenario_hold_minutes(row, scenario)
    if hold is not None:
        agg.hold_minutes_sum += hold
        agg.hold_minutes_count += 1


def candidate_delta_row(row: dict[str, Any]) -> dict[str, Any]:
    activated = row.get("activated_default_router_projection") or {}
    condition = row.get("condition_router_projection") or {}
    old_r = scenario_value(row, "old_gtos_live_current_j46_j49")
    be_r = scenario_value(row, "moonshot_be_after_trigger")
    fixed_r = scenario_value(row, "legacy_fixed_1_5r_comparator")
    condition_r = scenario_value(row, "condition_router_challenger")
    activated_r = scenario_value(row, "activated_default_source_bound_primary")
    selected = scenario_selected(row, "activated_default_source_bound_primary")
    return {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage06_candidate_delta_v1",
        "record_type": "candidate_delta",
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "candidate_origin_family": row.get("candidate_origin_family"),
        "session_bucket": row.get("session_bucket"),
        "candle_time_utc": row.get("candle_time_utc"),
        "calendar": calendar_parts(row),
        "source_window_complete": row.get("source_window_complete"),
        "activated_replay_disposition": row.get("activated_replay_disposition"),
        "current_config_shadow_route_decision": (
            ((row.get("runtime_reference") or {}).get("current_config_shadow") or {}).get(
                "route_decision"
            )
        ),
        "hypothetical_pre_stage04_vnext_route_decision": (
            ((row.get("runtime_reference") or {}).get("hypothetical_activated_vnext") or {}).get(
                "route_decision"
            )
        ),
        "old_gtos_live_current_j46_j49_r": old_r,
        "legacy_fixed_1_5r_r": fixed_r,
        "moonshot_be_after_trigger_r": be_r,
        "condition_router_r": condition_r,
        "activated_default_source_bound_primary_r": activated_r,
        "activated_selected": selected,
        "activated_selected_policy": activated.get("selected_policy"),
        "activated_decision_status": activated.get("decision_status"),
        "activated_candidate_action": activated.get("candidate_action"),
        "activated_source_quality_action": activated.get("source_quality_action"),
        "activated_refusal_reasons": activated.get("refusal_reasons"),
        "condition_selected_policy": condition.get("selected_policy"),
        "condition_selector_key": condition.get("selector_condition_key"),
        "delta_be_vs_old_r": (be_r - old_r if be_r is not None and old_r is not None else None),
        "delta_condition_vs_old_r": (
            condition_r - old_r if condition_r is not None and old_r is not None else None
        ),
        "delta_activated_vs_old_r": (
            activated_r - old_r if activated_r is not None and old_r is not None else None
        ),
        "blocked_winner_vs_old": (not selected and old_r is not None and old_r > 0),
        "blocked_positive_r_vs_old": old_r if not selected and old_r is not None and old_r > 0 else 0.0,
        "avoided_loser_vs_old": (not selected and old_r is not None and old_r < 0),
        "avoided_negative_r_abs_vs_old": (
            abs(old_r) if not selected and old_r is not None and old_r < 0 else 0.0
        ),
        "saved_loser_vs_old": (
            selected
            and old_r is not None
            and old_r < 0
            and activated_r is not None
            and activated_r > old_r
        ),
        "saved_loser_delta_r_vs_old": (
            activated_r - old_r
            if selected
            and old_r is not None
            and old_r < 0
            and activated_r is not None
            and activated_r > old_r
            else 0.0
        ),
        "missed_condition_winner": (
            not selected and condition_r is not None and condition_r > 0
        ),
        "missed_condition_positive_r": (
            condition_r if not selected and condition_r is not None and condition_r > 0 else 0.0
        ),
        "timeout_behavior": {
            scenario: timeout_behavior(row, scenario) for scenario in SCENARIOS
        },
        "nofill_behavior": nofill_behavior(row),
        "hold_minutes": {
            scenario: scenario_hold_minutes(row, scenario) for scenario in SCENARIOS
        },
        "old_live_leakage_under_activated_overlay": activated.get("selected_policy")
        == "live_current_j46_j49",
        "no_live_trading_or_broker_mutation": True,
    }


def write_manifest_entry(entries: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    for index, item in enumerate(entries):
        if isinstance(item, dict) and item.get("path") == entry.get("path"):
            entries[index] = entry
            return
    entries.append(entry)


def update_output_manifest(summary: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    entries = [
        {
            "path": "VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_LEDGER_2026-05-26.jsonl",
            "stage": "stage_06",
            "status": "created",
            "rows": summary["output_rows"]["delta_ledger_rows"],
        },
        {
            "path": "VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_REPORT_2026-05-26.md",
            "stage": "stage_06",
            "status": "created",
        },
        {
            "path": "VNEXT_REPLACEMENT_LEGACY_VS_VNEXT_DELTA_SUMMARY_2026-05-26.json",
            "stage": "stage_06",
            "status": "created",
        },
    ]
    if isinstance(outputs, list):
        for entry in entries:
            write_manifest_entry(outputs, entry)
    elif isinstance(outputs, dict):
        outputs["stage06_delta_ledger"] = rel(OUTPUT_LEDGER)
        outputs["stage06_delta_report"] = rel(OUTPUT_REPORT)
        outputs["stage06_delta_summary"] = rel(OUTPUT_SUMMARY)
    manifest["last_updated_utc"] = utc_now()
    manifest["stage06_status"] = "completed_delta_ledger_written"
    write_json(OUTPUT_MANIFEST, manifest)


def update_state(summary: dict[str, Any]) -> None:
    state = read_json(OUTPUT_STATE)
    state["last_updated_utc"] = utc_now()
    state["current_stage"] = "stage_07_question_ledger_closure"
    state["first_incomplete_invariant"] = "stage_07_question_ledger_closure_pending"
    state["exact_next_action"] = (
        "Import activation and moonshot question ledgers, answer each row from disk evidence, "
        "and classify remaining rows as implemented, killed/redesigned, source-capture required, "
        "AI-budget required, activation-config-applied, or exact external-surface handoff."
    )
    state.setdefault("stage_status", {})[
        "stage_06_legacy_vs_vnext_delta"
    ] = "completed_delta_ledger_written"
    state.setdefault("stage_status", {})["stage_07_question_ledger_closure"] = "pending"
    rows = state.setdefault("evidence_rows_scanned", {})
    rows["stage06_candidate_delta_rows"] = summary["output_rows"]["candidate_delta_rows"]
    rows["stage06_aggregate_delta_rows"] = summary["output_rows"]["aggregate_delta_rows"]
    rows["stage06_delta_ledger_rows"] = summary["output_rows"]["delta_ledger_rows"]
    state.setdefault("tests_verifiers_run", []).append(
        {
            "command": rel(Path(__file__)),
            "result": "passed; wrote Stage06 legacy-vs-vNext delta ledger",
            "timestamp_utc": utc_now(),
        }
    )
    write_json(OUTPUT_STATE, state)


def write_report(summary: dict[str, Any], aggregate_rows: list[dict[str, Any]]) -> None:
    overall = {
        row["scenario"]: row
        for row in aggregate_rows
        if row["dimension_type"] == "overall" and row["dimension_value"] == "ALL"
    }
    lines = [
        "# vNext Replacement Stage06 Legacy-vs-vNext Delta",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "## Overall Scenarios",
        "",
    ]
    for scenario in SCENARIOS:
        row = overall.get(scenario, {})
        lines.append(
            "- `{}`: selected `{}`, performance `{}`, total R `{}`, expectancy `{}`, WR `{}`, PF `{}`".format(
                scenario,
                row.get("selected_count"),
                row.get("performance_count"),
                row.get("total_r"),
                row.get("expectancy_r"),
                row.get("win_rate"),
                row.get("profit_factor"),
            )
        )
    lines.extend(
        [
            "",
            "## Activation Warning",
            "",
            "Stage05/Stage06 preserve the current activated default-router projection, but its source-bound primary slice is negative. Stage12 must fail any production activation overlay that uses this default slice without a repaired branch/selector.",
            "",
        ]
    )
    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    stage05_summary = read_json(STAGE05_SUMMARY)
    stage05_verifier = read_json(STAGE05_VERIFIER)
    if stage05_verifier.get("status") != "passed":
        raise SystemExit("Stage05 verifier must pass before Stage06 delta build")

    aggregates: defaultdict[tuple[str, str, str], Aggregate] = defaultdict(Aggregate)
    scenario_counts: Counter[str] = Counter()
    candidate_rows = 0
    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as output_handle:
        for manifest_row in iter_jsonl(STAGE05_SHARD_MANIFEST):
            shard_path = REPO_ROOT / manifest_row["output_chunk_path"]
            for row in iter_gzip_jsonl(shard_path):
                candidate_rows += 1
                candidate_delta = candidate_delta_row(row)
                output_handle.write(json.dumps(candidate_delta, sort_keys=True) + "\n")
                for scenario in SCENARIOS:
                    dims = dimension_values(row, scenario)
                    for dimension in DIMENSIONS:
                        key = (scenario, dimension, dims[dimension])
                        update_aggregate(aggregates[key], row, scenario)
                    scenario_counts[scenario] += 1

        aggregate_rows = []
        for (scenario, dimension_type, dimension_value), aggregate in sorted(aggregates.items()):
            aggregate_row = aggregate.to_row(scenario, dimension_type, dimension_value)
            aggregate_rows.append(aggregate_row)
            output_handle.write(json.dumps(aggregate_row, sort_keys=True) + "\n")

    summary = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage06_delta_summary_v1",
        "generated_at_utc": utc_now(),
        "input_stage05_summary": rel(STAGE05_SUMMARY),
        "input_stage05_verifier": rel(STAGE05_VERIFIER),
        "output_paths": {
            "delta_ledger": rel(OUTPUT_LEDGER),
            "delta_report": rel(OUTPUT_REPORT),
            "delta_summary": rel(OUTPUT_SUMMARY),
        },
        "output_rows": {
            "candidate_delta_rows": candidate_rows,
            "aggregate_delta_rows": len(aggregate_rows),
            "delta_ledger_rows": candidate_rows + len(aggregate_rows),
        },
        "stage05_warning_carried_forward": stage05_verifier.get("warnings", []),
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "aggregate_dimensions": list(DIMENSIONS),
        "prop_projection_boundary": (
            "Prop pass/account-abandon metrics are branch aggregate evidence from Stage05; "
            "candidate-level prop action sequence was not present upstream and remains a "
            "source/capture requirement."
        ),
        "ledger_sha256": sha256_file(OUTPUT_LEDGER),
        "first_incomplete_invariant_after_stage06": "stage_07_question_ledger_closure_pending",
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_report(summary, aggregate_rows)
    update_output_manifest(summary)
    update_state(summary)
    append_jsonl(
        CONTROL_LEDGER,
        {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "timestamp_utc": utc_now(),
            "status": "completed_delta_ledger_written",
            "candidate_delta_rows": candidate_rows,
            "aggregate_delta_rows": len(aggregate_rows),
            "first_incomplete_invariant_after_stage": summary[
                "first_incomplete_invariant_after_stage06"
            ],
        },
    )
    print(
        json.dumps(
            {
                "stage": STAGE_ID,
                "candidate_delta_rows": candidate_rows,
                "aggregate_delta_rows": len(aggregate_rows),
                "next": summary["first_incomplete_invariant_after_stage06"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
