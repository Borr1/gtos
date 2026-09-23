from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

MOONSHOT_ROUTE_DIR = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
INPUT_LEDGER = (
    MOONSHOT_ROUTE_DIR
    / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
)
INPUT_RESULT = (
    MOONSHOT_ROUTE_DIR
    / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UPGRADED_DEGRADED_IMPLICATION_RESULT_2026-05-16.json"
)

DECISION_MAP = {
    "PRESERVE_SOURCE_ACCEPTED_CHALLENGER_CANDIDATE": (
        "KEEP_SOURCE_ACCEPTED_CONFIRMED_CHALLENGER_REPLAY_QUEUE",
        "PRESERVE_DEFAULT_OFF_REPLAY_OR_CHALLENGER_PACKET_ONLY",
        "keep_confirmed_source",
    ),
    "DOWNGRADE_ACCEPTED_SOURCE_UNTIL_EXACT_SOURCE_OR_ALTERNATIVE_SOURCE_REPAIR": (
        "DOWNGRADE_OR_AVOID_ACCEPTED_SOURCE_BRANCH",
        "KILL_OR_AVOID_UNTIL_EXACT_SOURCE_REPAIR",
        "degrade_avoid_or_repair",
    ),
    "OPEN_SOURCE_CHALLENGER_REVIEW_FROM_REPAIR_BRANCH": (
        "UPGRADE_REPAIR_TO_SOURCE_CHALLENGER_REVIEW",
        "OPEN_DEFAULT_OFF_CHALLENGER_REVIEW_FROM_REPAIR_BRANCH",
        "upgraded_challenger_review",
    ),
    "OPEN_CHALLENGER_REVIEW_AFTER_M15_ORDERING_REPAIR": (
        "M15_ORDERING_REPAIR_THEN_CHALLENGER_REVIEW",
        "ROUTE_TO_M15_ORDERING_REPAIR_BEFORE_CHALLENGER_REVIEW",
        "m15_ordering_repair",
    ),
    "SPLIT_TO_M15_ORDERING_REPAIR_BEFORE_KEEPING_SOURCE_ACCEPTED": (
        "M15_ORDERING_REPAIR_BEFORE_KEEPING_SOURCE_ACCEPTED",
        "ROUTE_TO_M15_ORDERING_REPAIR_BEFORE_KEEP_OR_REPLAY",
        "m15_ordering_repair",
    ),
    "KEEP_SOURCE_REPAIR_OR_AVOID_DECISION": (
        "KEEP_REPAIR_OR_AVOID_DECISION",
        "KEEP_REPAIR_OR_AVOID_BRANCH_NOT_PROMOTION",
        "repair_or_avoid",
    ),
    "KEEP_REPAIR_DECISION_AND_ROUTE_AMBIGUITY_TO_M15_ORDERING_REPAIR": (
        "KEEP_REPAIR_WITH_M15_ORDERING_AMBIGUITY",
        "ROUTE_AMBIGUITY_TO_M15_ORDERING_REPAIR",
        "m15_ordering_repair",
    ),
    "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR_DECISION": (
        "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR",
        "PRESERVE_REQUIREMENT_ONLY_NO_R_OR_PROXY_DECISION",
        "source_requirement_only",
    ),
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def manifest_path_to_file(name: str) -> Path:
    return ROUTE_DIR / name


def expected_counts_from_map(source_rows: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, int]]:
    branch_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    for row in source_rows:
        proposed = str(row.get("proposed_system_use") or "")
        branch, _, bucket = DECISION_MAP[proposed]
        branch_counts[branch] += 1
        bucket_counts[bucket] += 1
    return dict(branch_counts), dict(bucket_counts)


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_source_implication_branch_decisions_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, INPUT_LEDGER, INPUT_RESULT, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    source_rows = read_jsonl(INPUT_LEDGER)
    source_result = read_json(INPUT_RESULT)
    decision_rows = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    source_counts = source_result.get("counts", {})
    source_distributions = source_result.get("bucket_distributions", {})
    branch_counts_expected, bucket_counts_expected = expected_counts_from_map(source_rows)
    source_ids = Counter(str(row.get("source_implication_implementation_id")) for row in source_rows)
    decision_source_ids = Counter(str(row.get("source_implication_implementation_id")) for row in decision_rows)

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("source_result_safe_flags_closed", source_result.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("summary_manifest_safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(
        check(
            "source_row_counts_match_result",
            len(source_rows)
            == source_counts.get("branch_implication_rows")
            == source_counts.get("implementation_rows")
            == 138,
            {"source_rows": len(source_rows), "source_counts": source_counts},
        )
    )
    checks.append(
        check(
            "decision_row_count_preserves_all_source_rows",
            len(decision_rows) == len(source_rows) == summary.get("decision_rows") == summary.get("input_rows"),
            {"decision_rows": len(decision_rows), "summary_decision_rows": summary.get("decision_rows")},
        )
    )
    checks.append(check("source_implementation_ids_preserved_once", source_ids == decision_source_ids))
    checks.append(
        check(
            "no_unmapped_decision_rows",
            "UNMAPPED_SOURCE_IMPLICATION_REQUIRES_REVIEW" not in counter(decision_rows, "branch_decision"),
            counter(decision_rows, "branch_decision"),
        )
    )

    mapping_errors = []
    for row in decision_rows:
        proposed = str(row.get("proposed_system_use") or "")
        if proposed not in DECISION_MAP:
            mapping_errors.append({"line": row["_line_no"], "proposed_system_use": proposed, "error": "unmapped"})
            continue
        expected_branch, expected_action, expected_bucket = DECISION_MAP[proposed]
        if (
            row.get("branch_decision") != expected_branch
            or row.get("current_main_action") != expected_action
            or row.get("implementation_bucket") != expected_bucket
        ):
            mapping_errors.append(
                {
                    "line": row["_line_no"],
                    "proposed_system_use": proposed,
                    "branch_decision": row.get("branch_decision"),
                    "current_main_action": row.get("current_main_action"),
                    "implementation_bucket": row.get("implementation_bucket"),
                    "expected": [expected_branch, expected_action, expected_bucket],
                }
            )
    checks.append(check("decision_mapping_matches_contract", not mapping_errors, mapping_errors[:10]))

    checks.append(
        check(
            "source_implication_class_counts_match_source_result",
            summary.get("source_implication_class_counts")
            == counter(decision_rows, "source_implication_class")
            == source_distributions.get("source_implication_class"),
            {
                "summary": summary.get("source_implication_class_counts"),
                "source": source_distributions.get("source_implication_class"),
            },
        )
    )
    checks.append(
        check(
            "proposed_system_use_counts_match_source_result",
            summary.get("proposed_system_use_counts")
            == counter(decision_rows, "proposed_system_use")
            == source_distributions.get("next_same_resource_action"),
            {
                "summary": summary.get("proposed_system_use_counts"),
                "source": source_distributions.get("next_same_resource_action"),
            },
        )
    )
    checks.append(
        check(
            "m15_ordering_requirement_counts_match_source_result",
            summary.get("m15_ordering_requirement_counts")
            == counter(decision_rows, "m15_ordering_requirement")
            == source_distributions.get("m15_ordering_requirement"),
            summary.get("m15_ordering_requirement_counts"),
        )
    )
    checks.append(check("branch_decision_counts_match_contract", summary.get("branch_decision_counts") == branch_counts_expected))
    checks.append(check("implementation_bucket_counts_match_contract", summary.get("implementation_bucket_counts") == bucket_counts_expected))
    checks.append(check("summary_source_result_counts_preserved", summary.get("source_result_counts") == source_counts))
    checks.append(check("summary_source_score_stats_preserved", summary.get("source_score_stats") == source_result.get("score_stats", {})))
    checks.append(check("summary_source_system_decision_preserved", summary.get("source_system_decision") == source_result.get("system_decision", {})))
    checks.append(
        check(
            "summary_upstream_counts_preserved",
            summary.get("upstream_materialization_counts") == source_result.get("upstream_materialization_counts", {})
            and summary.get("upstream_source_bar_counts") == source_result.get("upstream_source_bar_counts", {}),
        )
    )

    row_flag_errors = [
        {"line": row["_line_no"], "safe_flags": row.get("safe_flags")}
        for row in decision_rows
        if row.get("safe_flags") != SAFE_FLAGS or row.get("no_live_behavior") is not True or row.get("no_promotion") is not True
    ]
    checks.append(check("all_decision_rows_have_closed_safe_flags", not row_flag_errors, row_flag_errors[:10]))

    input_hashes = {
        str(INPUT_LEDGER): sha256(INPUT_LEDGER),
        str(INPUT_RESULT): sha256(INPUT_RESULT),
    }
    checks.append(check("summary_input_hashes_match_current_inputs", summary.get("source_input_hashes") == input_hashes))
    checks.append(check("manifest_input_hashes_match_current_inputs", manifest.get("input_artifacts") == input_hashes))

    snapshot_errors = []
    for path_str, expected_hash in input_hashes.items():
        snapshot = manifest.get("input_artifact_snapshots", {}).get(path_str)
        if not snapshot:
            snapshot_errors.append({"path": path_str, "error": "missing_snapshot"})
            continue
        path = Path(path_str)
        if snapshot.get("sha256") != expected_hash:
            snapshot_errors.append({"path": path_str, "error": "snapshot_hash_mismatch"})
        if snapshot.get("size_bytes") != path.stat().st_size:
            snapshot_errors.append({"path": path_str, "error": "snapshot_size_mismatch"})
        if snapshot.get("exists") is not True:
            snapshot_errors.append({"path": path_str, "error": "snapshot_missing_exists_true"})
    checks.append(check("manifest_input_snapshots_match_inputs", not snapshot_errors, snapshot_errors))

    output_hash_errors = []
    for relpath, artifact in manifest.get("output_artifacts", {}).items():
        path = manifest_path_to_file(relpath)
        if not path.exists():
            output_hash_errors.append({"path": relpath, "error": "missing"})
            continue
        if artifact.get("sha256") != sha256(path):
            output_hash_errors.append({"path": relpath, "error": "sha256_mismatch"})
        if artifact.get("size_bytes") != path.stat().st_size:
            output_hash_errors.append({"path": relpath, "error": "size_mismatch"})
    checks.append(check("manifest_output_hashes_match", not output_hash_errors, output_hash_errors))

    checks.append(
        check(
            "moonshot_snapshot_present",
            bool(manifest.get("moonshot_git_snapshot", {}).get("head"))
            and bool(manifest.get("moonshot_git_snapshot", {}).get("branch")),
            manifest.get("moonshot_git_snapshot"),
        )
    )

    for path in [build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "source_rows": len(source_rows),
            "decision_rows": len(decision_rows),
            "accepted_confirmed_rows": source_counts.get("accepted_confirmed_rows"),
            "accepted_degraded_rows": source_counts.get("accepted_degraded_rows"),
            "upgraded_challenger_review_rows": source_counts.get("upgraded_challenger_review_rows"),
            "m15_ambiguity_review_rows": source_counts.get("m15_ambiguity_review_rows"),
            "no_scalar_rows": source_counts.get("no_scalar_rows"),
            "repair_confirmed_rows": source_counts.get("repair_confirmed_rows"),
            "bar_spread_rstyle_mean_mean": source_result.get("score_stats", {}).get("bar_spread_rstyle_mean_mean"),
            "bar_minus_source_midpoint_mean": source_result.get("score_stats", {}).get("bar_minus_source_midpoint_mean"),
            "branch_decision_counts": summary.get("branch_decision_counts"),
            "implementation_bucket_counts": summary.get("implementation_bucket_counts"),
        },
        "plate_decision": "SOURCE_UPGRADED_DEGRADED_IMPLICATIONS_MATERIALIZED_INTO_MAIN_BRANCH_DECISIONS",
        "can_mark_source_implication_branch_decision_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
