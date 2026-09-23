from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[2]

ACTIVE_SYMBOLS = {
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
}

LANE04_MANIFEST = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01" / "LANE04_OUTPUT_MANIFEST.json"
LANE10_MANIFEST = ROOT / "research" / "operations" / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01" / "LANE10_OUTPUT_MANIFEST.json"


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with open_text(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def manifest_line_count(manifest_path: Path, artifact_name: str) -> int | None:
    manifest = read_json(manifest_path, {})
    for item in manifest.get("outputs") or []:
        if str(item.get("path") or "").endswith(artifact_name):
            value = item.get("line_count")
            return int(value) if isinstance(value, int) else None
    return None


def scan_event_ledger(path: Path) -> dict[str, Any]:
    count = 0
    missing_identity = 0
    missing_events = 0
    gap_rows = 0
    materialized_state_counts: dict[str, int] = {}
    symbols: set[str] = set()
    for row in iter_jsonl(path):
        count += 1
        if not row.get("row_id") or not row.get("selected_row_id"):
            missing_identity += 1
        if not isinstance(row.get("ordered_events"), list) or not row.get("ordered_events"):
            missing_events += 1
        if row.get("source_gap_count"):
            gap_rows += 1
        state = str(row.get("cross_lane_materialization_state") or "UNKNOWN")
        materialized_state_counts[state] = materialized_state_counts.get(state, 0) + 1
        if row.get("symbol"):
            symbols.add(str(row["symbol"]))
    return {
        "rows": count,
        "missing_identity": missing_identity,
        "missing_events": missing_events,
        "gap_rows": gap_rows,
        "materialized_state_counts": materialized_state_counts,
        "symbols": symbols,
    }


def scan_anatomy_ledger(path: Path) -> dict[str, Any]:
    count = 0
    missing_identity = 0
    missing_join_fields = 0
    policy_joined = 0
    scheduler_joined = 0
    for row in iter_jsonl(path):
        count += 1
        if not row.get("row_id") or not row.get("selected_row_id"):
            missing_identity += 1
        if not row.get("feature_join_state") or not row.get("label_join_state") or not row.get("scheduler_join_state"):
            missing_join_fields += 1
        if str(row.get("policy_join_state") or "").startswith("joined_"):
            policy_joined += 1
        if str(row.get("scheduler_join_state") or "").startswith("joined_"):
            scheduler_joined += 1
    return {
        "rows": count,
        "missing_identity": missing_identity,
        "missing_join_fields": missing_join_fields,
        "policy_joined": policy_joined,
        "scheduler_joined": scheduler_joined,
    }


def scan_source_gap_ledger(path: Path) -> dict[str, Any]:
    count = 0
    missing_identity = 0
    gap_families: dict[str, int] = {}
    source_families: dict[str, int] = {}
    for row in iter_jsonl(path):
        count += 1
        if not row.get("gap_id") or not row.get("candidate_id"):
            missing_identity += 1
        source_family = str(row.get("gap_source_family") or "UNKNOWN")
        source_families[source_family] = source_families.get(source_family, 0) + 1
        for family in row.get("source_gap_families") or []:
            family = str(family)
            gap_families[family] = gap_families.get(family, 0) + 1
    return {
        "rows": count,
        "missing_identity": missing_identity,
        "gap_families": gap_families,
        "source_families": source_families,
    }


def scan_split_summary(path: Path) -> dict[str, Any]:
    count = 0
    scopes: set[str] = set()
    families: set[str] = set()
    top_n_key_rows = 0
    for row in iter_jsonl(path):
        count += 1
        scopes.add(str(row.get("split_scope")))
        families.add(str(row.get("summary_family")))
        if any("top_" in key.lower() for key in row.keys()):
            top_n_key_rows += 1
    return {"rows": count, "scopes": scopes, "families": families, "top_n_key_rows": top_n_key_rows}


def scan_coverage(path: Path) -> dict[str, Any]:
    count = 0
    source_artifacts = 0
    symbol_day = 0
    symbols: set[str] = set()
    for row in iter_jsonl(path):
        count += 1
        scope = row.get("coverage_scope")
        if scope == "source_artifact":
            source_artifacts += 1
        if scope == "symbol_day_window":
            symbol_day += 1
            if row.get("symbol"):
                symbols.add(str(row["symbol"]))
    return {"rows": count, "source_artifacts": source_artifacts, "symbol_day_rows": symbol_day, "symbols": symbols}


def verify_route(route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    issues: list[str] = []
    paths = {
        "event": route_dir / "LANE16_MICROSCOPE_EVENT_LEDGER.jsonl.gz",
        "anatomy": route_dir / "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz",
        "source_gap": route_dir / "LANE16_SOURCE_GAP_LEDGER.jsonl.gz",
        "coverage": route_dir / "LANE16_COVERAGE_INVENTORY.jsonl",
        "split": route_dir / "LANE16_SPLIT_STRESS_SUMMARY.jsonl",
        "source_completeness": route_dir / "LANE16_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
        "dependency": route_dir / "LANE16_DEPENDENCY_STATE_LEDGER.jsonl",
        "decision": route_dir / "LANE16_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "contract": route_dir / "LANE16_DOWNSTREAM_CONTRACT.json",
        "source_use": route_dir / "LANE16_SOURCE_USE_STATE.json",
        "result_use": route_dir / "LANE16_RESULT_USE_STATUS.json",
        "runtime": route_dir / "LANE16_RUNTIME_EFFECT_BOUNDARY.json",
        "audit": route_dir / "LANE16_COMPLETION_AUDIT.json",
        "manifest": route_dir / "LANE16_OUTPUT_MANIFEST.json",
        "builder": route_dir / "build_vnext_absolute_moonshot_lane16_historical_microscope_scale.py",
        "verifier": route_dir / "verify_vnext_absolute_moonshot_lane16_historical_microscope_scale.py",
    }
    for name, path in paths.items():
        if not path.exists():
            issues.append(f"missing_required_output:{name}:{path.name}")
    if issues:
        return {
            "ok": False,
            "issue_count": len(issues),
            "issues": issues,
            "schema_version": "lane16_verification_result_v1",
        }

    expected_event_rows = manifest_line_count(LANE04_MANIFEST, "LANE04_ROW_TIMELINE_LEDGER.jsonl")
    expected_non_reconstructable_gaps = manifest_line_count(LANE10_MANIFEST, "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz")

    event_scan = scan_event_ledger(paths["event"])
    anatomy_scan = scan_anatomy_ledger(paths["anatomy"])
    gap_scan = scan_source_gap_ledger(paths["source_gap"])
    split_scan = scan_split_summary(paths["split"])
    coverage_scan = scan_coverage(paths["coverage"])

    event_rows = event_scan["rows"]
    path_anatomy_rows = anatomy_scan["rows"]
    source_gap_rows = gap_scan["rows"]
    coverage_rows = coverage_scan["rows"]
    split_rows = split_scan["rows"]

    if expected_event_rows is None:
        issues.append("missing_expected_event_row_count_from_lane04_manifest")
    elif event_rows != expected_event_rows:
        issues.append(f"event_rows_expected_{expected_event_rows}_actual_{event_rows}")
    if path_anatomy_rows != event_rows:
        issues.append(f"path_anatomy_rows_mismatch_event_rows:{path_anatomy_rows}!={event_rows}")
    if event_scan["missing_identity"]:
        issues.append(f"event_rows_missing_identity:{event_scan['missing_identity']}")
    if event_scan["missing_events"]:
        issues.append(f"event_rows_missing_ordered_events:{event_scan['missing_events']}")
    if anatomy_scan["missing_identity"]:
        issues.append(f"anatomy_rows_missing_identity:{anatomy_scan['missing_identity']}")
    if anatomy_scan["missing_join_fields"]:
        issues.append(f"anatomy_rows_missing_join_fields:{anatomy_scan['missing_join_fields']}")
    if anatomy_scan["policy_joined"] != event_rows:
        issues.append(f"policy_joined_rows_expected_{event_rows}_actual_{anatomy_scan['policy_joined']}")
    if anatomy_scan["scheduler_joined"] != event_rows:
        issues.append(f"scheduler_joined_rows_expected_{event_rows}_actual_{anatomy_scan['scheduler_joined']}")
    if expected_non_reconstructable_gaps is None:
        issues.append("missing_expected_non_reconstructable_gap_count_from_lane10_manifest")
    elif gap_scan["source_families"].get("canonical_candidate_without_joined_microscope_label_replay_scheduler", 0) != expected_non_reconstructable_gaps:
        issues.append(
            "non_reconstructable_gap_rows_expected_"
            f"{expected_non_reconstructable_gaps}_actual_{gap_scan['source_families'].get('canonical_candidate_without_joined_microscope_label_replay_scheduler', 0)}"
        )
    if source_gap_rows <= event_scan["gap_rows"]:
        issues.append("source_gap_ledger_does_not_include_non_reconstructable_gap_rows")
    if gap_scan["missing_identity"]:
        issues.append(f"source_gap_rows_missing_identity:{gap_scan['missing_identity']}")
    if "microscope_event_materialized_with_missing_fields" not in gap_scan["source_families"]:
        issues.append("materialized_microscope_source_gap_family_missing")
    if "canonical_candidate_without_joined_microscope_label_replay_scheduler" not in gap_scan["source_families"]:
        issues.append("canonical_non_reconstructable_gap_family_missing")

    required_scopes = {
        "all",
        "date",
        "week",
        "month",
        "symbol",
        "session",
        "origin_family",
        "framework",
        "side",
        "regime_h4_state",
        "scheduler_decision",
        "current_router_policy",
        "symbol_day",
    }
    missing_scopes = sorted(required_scopes - split_scan["scopes"])
    if missing_scopes:
        issues.append(f"missing_split_scopes:{missing_scopes}")
    if "source_gap_split" not in split_scan["families"]:
        issues.append("source_gap_split_rows_missing")
    if split_scan["top_n_key_rows"]:
        issues.append(f"top_n_fields_found_in_split_summary:{split_scan['top_n_key_rows']}")

    missing_symbols = sorted(ACTIVE_SYMBOLS - coverage_scan["symbols"])
    if missing_symbols:
        issues.append(f"active_symbols_missing_from_coverage:{missing_symbols}")
    if coverage_scan["source_artifacts"] < 10:
        issues.append("coverage_source_artifact_rows_too_few")
    if coverage_scan["symbol_day_rows"] <= 0:
        issues.append("coverage_symbol_day_windows_missing")

    contract = read_json(paths["contract"], {})
    consumers = set((contract.get("consumer_contracts") or {}).keys())
    required_consumers = {"Market Awareness", "Selector V3", "Scheduler V3", "Execution V3", "ML", "Repair Companion", "Command Center"}
    if consumers != required_consumers:
        issues.append(f"downstream_consumers_mismatch:{sorted(consumers)}")

    runtime = read_json(paths["runtime"], {})
    if runtime.get("live_broker_order_operation") is not False or runtime.get("paid_api_vendor_call") is not False:
        issues.append("runtime_boundary_forbidden_surface_not_false")
    audit = read_json(paths["audit"], {})
    mandatory = audit.get("mandatory_context_use") or {}
    for key in (
        "live_state_regenerated",
        "goal_session_research_discipline_read",
        "research_operating_doctrine_read",
        "moonshot_vision_read",
        "master_read_from_disk",
        "lane01_lane11_lane09b_lane10b_read_from_disk",
    ):
        if mandatory.get(key) is not True:
            issues.append(f"mandatory_context_use_not_recorded:{key}")
    dependency_rows = list(iter_jsonl(paths["dependency"]))
    dependencies = {str(row.get("dependency_id")) for row in dependency_rows}
    for required in {"MASTER", "01", "02", "03", "04", "05", "06", "07", "08", "09", "09B", "10", "10B", "11"}:
        if required not in dependencies:
            issues.append(f"missing_dependency_row:{required}")

    manifest = read_json(paths["manifest"], {})
    manifest_counts = {
        Path(item.get("path", "")).name: item.get("line_count")
        for item in manifest.get("outputs") or []
    }
    expected_counts = {
        "LANE16_MICROSCOPE_EVENT_LEDGER.jsonl.gz": event_rows,
        "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz": path_anatomy_rows,
        "LANE16_SOURCE_GAP_LEDGER.jsonl.gz": source_gap_rows,
        "LANE16_COVERAGE_INVENTORY.jsonl": coverage_rows,
        "LANE16_SPLIT_STRESS_SUMMARY.jsonl": split_rows,
    }
    for artifact_name, expected_count in expected_counts.items():
        if manifest_counts.get(artifact_name) != expected_count:
            issues.append(f"manifest_line_count_mismatch:{artifact_name}:{manifest_counts.get(artifact_name)}!={expected_count}")

    return {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "event_rows": event_rows,
        "path_anatomy_rows": path_anatomy_rows,
        "source_gap_rows": source_gap_rows,
        "non_reconstructable_gap_rows": gap_scan["source_families"].get("canonical_candidate_without_joined_microscope_label_replay_scheduler", 0),
        "coverage_inventory_rows": coverage_rows,
        "split_stress_rows": split_rows,
        "event_gap_rows": event_scan["gap_rows"],
        "materialized_state_counts": event_scan["materialized_state_counts"],
        "coverage_symbol_count": len(coverage_scan["symbols"]),
        "schema_version": "lane16_verification_result_v1",
        "route_id": "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01",
    }


def main() -> int:
    result = verify_route()
    (ROUTE_DIR / "LANE16_VERIFICATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
