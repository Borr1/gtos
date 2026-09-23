#!/usr/bin/env python3
"""Verify NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS."""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
LANE_PREFIX = "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_quarantined_categorical_synthesis_forensics/"

EXPECTED_PARTITION = {
    "accepted": 225,
    "blocked": 8,
    "rejected": 65,
    "universe": 298,
}
EXPECTED_ACCEPTED_LABELS = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_ACCEPTED_SOURCE_LANES = {
    "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 32,
    "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT_V2": 29,
    "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 58,
    "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 51,
    "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 3,
    "prior_g12_categorical_packet_audit": 52,
}
EXPECTED_BLOCKER_CODES = {
    "BLOCK_FILL_PATH_SAME_TICK_ORDER_UNRESOLVABLE": 4,
    "BLOCK_OTI2_ACTIVE_WINDOW_TICK_COVERAGE_GAP": 1,
    "BLOCK_OTI2_ENTRY_TOUCH_NOT_SIDE_AWARE_TICK_CONFIRMED": 1,
    "BLOCK_OTI4_RANGE_TICK_WINDOW_EMPTY_OR_LOCAL_SOURCE_GAP": 3,
}
EXPECTED_REJECT_DECISIONS = {
    "REJECT_FROM_REBUILD_CONTRACT_EXCLUDED": 26,
    "REJECT_FROM_REBUILD_NONCANONICAL_DUPLICATE": 39,
}

JSON_ARTIFACTS = [
    f"NOFILL_CAT_V2_FORENSICS_SYNTHESIS_{DATE}.json",
    f"NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json",
    f"NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_{DATE}.json",
    f"NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_{DATE}.json",
    f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.json",
    f"NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_{DATE}.json",
]
MD_ARTIFACTS = [
    f"NOFILL_CAT_V2_FORENSICS_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_SYNTHESIS_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_{DATE}.md",
]
PY_FILES = [
    "build_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
    "verify_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
    "test_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py",
]

FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/fn_smoke_trade",
    "scripts/mt5",
    "run_agent.py",
    "tests/canary",
)
FORBIDDEN_OUTPUT_KEY_PARTS = (
    "actual_r",
    "account_history",
    "broker_actual",
    "broker_deal",
    "broker_order",
    "broker_position",
    "expectancy",
    "hidden_label",
    "live_order",
    "live_trade_result",
    "mt5_account",
    "mt5_deal",
    "mt5_history",
    "mt5_order",
    "mt5_position",
    "pbo",
    "profit",
    "r_multiple",
    "reward_r",
    "synthetic_r",
    "win_rate",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def payloads() -> dict[str, dict[str, Any]]:
    return {name: load_json(name) for name in JSON_ARTIFACTS if (OUT_DIR / name).exists()}


def scan_forbidden_keys(payload: Any, path: str = "") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_l = str(key).lower()
            if any(part in key_l for part in FORBIDDEN_OUTPUT_KEY_PARTS):
                hits.append({"path": f"{path}.{key}" if path else str(key), "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}" if path else str(key)))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            hits.extend(scan_forbidden_keys(item, f"{path}[{index}]"))
    return hits


def check_artifact_presence() -> dict[str, Any]:
    expected = JSON_ARTIFACTS + MD_ARTIFACTS + PY_FILES
    missing = [name for name in expected if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "expected_count": len(expected), "missing": missing}


def check_json_parse() -> dict[str, Any]:
    errors = []
    for name in JSON_ARTIFACTS:
        try:
            load_json(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def check_markdown_promotion() -> dict[str, Any]:
    missing = []
    for name in MD_ARTIFACTS:
        path = OUT_DIR / name
        if path.exists() and PROMOTION_VERDICT not in path.read_text(encoding="utf-8"):
            missing.append(name)
    return {"status": "PASS" if not missing else "FAIL", "missing_promotion_verdict": missing}


def check_flags(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for name, payload in items.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{name}: promotion_verdict")
        if payload.get("validation_safe") is not False:
            issues.append(f"{name}: validation_safe")
        if payload.get("outcome_review_opened") is not False:
            issues.append(f"{name}: outcome_review_opened")
        if payload.get("live_effect") is not False:
            issues.append(f"{name}: live_effect")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_counts_and_slices(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    synthesis = items[f"NOFILL_CAT_V2_FORENSICS_SYNTHESIS_{DATE}.json"]
    slices = items[f"NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_{DATE}.json"]
    labels = items[f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json"]

    if synthesis["partition_counts"] != EXPECTED_PARTITION:
        issues.append({"partition_counts": synthesis["partition_counts"]})
    if synthesis["accepted_label_counts"] != EXPECTED_ACCEPTED_LABELS:
        issues.append({"accepted_label_counts": synthesis["accepted_label_counts"]})
    if synthesis["accepted_source_lane_counts"] != EXPECTED_ACCEPTED_SOURCE_LANES:
        issues.append({"accepted_source_lane_counts": synthesis["accepted_source_lane_counts"]})
    if slices["partition_counts"] != EXPECTED_PARTITION:
        issues.append({"slice_partition_counts": slices["partition_counts"]})
    if slices["accepted_denominator"] != 225:
        issues.append("accepted denominator != 225")
    by_label_sum = sum(item["row_count"] for item in slices["accepted_slices"]["by_label"])
    by_source_sum = sum(item["row_count"] for item in slices["accepted_slices"]["by_source_lane"])
    by_symbol_sum = sum(item["row_count"] for item in slices["accepted_slices"]["by_symbol"])
    by_session_sum = sum(item["row_count"] for item in slices["accepted_slices"]["by_session"])
    by_side_sum = sum(item["row_count"] for item in slices["accepted_slices"]["by_side"])
    if {by_label_sum, by_source_sum, by_symbol_sum, by_session_sum, by_side_sum} != {225}:
        issues.append(
            {
                "slice_sums": {
                    "label": by_label_sum,
                    "source": by_source_sum,
                    "symbol": by_symbol_sum,
                    "session": by_session_sum,
                    "side": by_side_sum,
                }
            }
        )
    if sorted(labels["label_families"]) != sorted(EXPECTED_ACCEPTED_LABELS):
        issues.append("label family set mismatch")
    for label, count in EXPECTED_ACCEPTED_LABELS.items():
        if labels["label_families"][label]["row_count"] != count:
            issues.append({label: labels["label_families"][label]["row_count"]})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_label_learning(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    labels = items[f"NOFILL_CAT_V2_FORENSICS_LABEL_FAMILY_ANALYSIS_{DATE}.json"]
    required = {
        "plain_mechanism",
        "what_it_proves",
        "what_it_does_not_prove",
        "failure_anatomy",
        "stronger_future_fields",
        "future_hypothesis",
    }
    for label, item in labels["label_families"].items():
        missing = required - set(item)
        if missing:
            issues.append({label: sorted(missing)})
        if item["descriptive_only"] is not True or item["validation_safe"] is not False:
            issues.append({label: "descriptive/validation flags"})
        nonclaims = set(item["what_it_does_not_prove"])
        for phrase in ("not R/performance", "not validation", "not promotion"):
            if phrase not in nonclaims:
                issues.append({label: f"missing nonclaim {phrase}"})
    rollup = labels["oti2_fill_path_family_rollup"]
    if rollup["row_count"] != 29:
        issues.append({"oti2_rollup": rollup["row_count"]})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_blocker_reject_learning(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    learning = items[f"NOFILL_CAT_V2_FORENSICS_BLOCKER_REJECT_LEARNING_{DATE}.json"]
    if learning["blocked_row_count"] != 8 or learning["rejected_row_count"] != 65:
        issues.append("blocked/rejected counts")
    if learning["blocker_code_counts"] != EXPECTED_BLOCKER_CODES:
        issues.append({"blocker_code_counts": learning["blocker_code_counts"]})
    if learning["reject_decision_counts"] != EXPECTED_REJECT_DECISIONS:
        issues.append({"reject_decision_counts": learning["reject_decision_counts"]})
    families = learning["blocker_families"]
    expected_families = {
        "oti4_may3_source_gaps": 3,
        "oti3_same_tick_order_ambiguities": 4,
        "original_oti2_source_gap": 1,
    }
    for name, count in expected_families.items():
        if families[name]["row_count"] != count:
            issues.append({name: families[name]["row_count"]})
        if not families[name].get("unblocker"):
            issues.append({name: "missing exact unblocker"})
    rejects = learning["reject_families"]
    if rejects["oti4_contract_excluded"]["row_count"] != 26:
        issues.append("oti4 reject count")
    if rejects["oti5_noncanonical_duplicate_projections"]["row_count"] != 39:
        issues.append("oti5 reject count")
    proofs = learning["g12_recomputed_proofs_referenced"]
    if proofs != {"original_oti2_source_gap_rows": 1, "oti3_same_tick_checks": 4, "oti4_may3_source_gap_checks": 3}:
        issues.append({"proofs": proofs})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_noleak_duplicate_source(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    audit = items[f"NOFILL_CAT_V2_FORENSICS_NO_LEAK_DUPLICATE_SOURCE_AUDIT_{DATE}.json"]
    slices = items[f"NOFILL_CAT_V2_FORENSICS_SLICE_LEDGER_{DATE}.json"]
    if audit["status"] != "PASS":
        issues.append("audit status")
    failing_checks = [item for item in audit["contradiction_checks"] if item["status"] != "PASS"]
    if failing_checks:
        issues.append({"failing_checks": failing_checks})
    if audit["missing_control_inputs"]:
        issues.append("missing control inputs")
    if audit["path_result_leakage_status"] != "PASS_NO_RESULT_VALUES_OPENED":
        issues.append("path/result leakage status")
    duplicate = slices["duplicate_and_canonical_policy"]
    if duplicate["accepted_unique_nofill_duplicate_keys"] != 182:
        issues.append("accepted unique duplicate keys")
    if duplicate["duplicate_key_collision_count"] != 5 or duplicate["rows_in_duplicate_key_collisions"] != 48:
        issues.append({"duplicate": duplicate})
    if duplicate["oti5_canonical_duplicate_rows_accepted"] != 3:
        issues.append("oti5 canonical accepted")
    if duplicate["oti5_noncanonical_duplicate_rows_rejected"] != 39:
        issues.append("oti5 duplicate rejected")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_future_and_completion(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    future = items[f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.json"]
    completion = items[f"NOFILL_CAT_V2_FORENSICS_COMPLETION_AUDIT_{DATE}.json"]
    route = future["route_decision"]
    if route["primary_next_route"] != "G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT":
        issues.append("primary route")
    if route["quantitative_result_lane_status"] != "FORBIDDEN_UNTIL_SEPARATE_FROZEN_PREREG_G12_GATE_AND_SAMPLE_FLOOR":
        issues.append("quant result gate")
    if not any(lane["lane"] == "Residual 8 blocker-clear access lane" for lane in future["future_control_lanes"]):
        issues.append("missing blocker-clear lane")
    if completion["can_mark_goal_complete"] is not True:
        issues.append("completion audit not final true")
    if completion["completion_status"] != "PASS":
        issues.append({"completion_status": completion["completion_status"]})
    failing = [item for item in completion["prompt_to_artifact_checklist"] if item["status"] != "PASS"]
    if failing:
        issues.append({"completion_failing": failing})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_future_routes(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    issues = []
    future = items[f"NOFILL_CAT_V2_FORENSICS_FUTURE_HYPOTHESIS_AND_CAPTURE_LEDGER_{DATE}.json"]
    route = future["route_decision"]
    if route["primary_next_route"] != "G12_NOFILL_CAT_V2_QUARANTINED_CATEGORICAL_SYNTHESIS_FORENSICS_AUDIT":
        issues.append("primary route")
    if route["secondary_route"] != "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE":
        issues.append("secondary route")
    if route["quantitative_result_lane_status"] != "FORBIDDEN_UNTIL_SEPARATE_FROZEN_PREREG_G12_GATE_AND_SAMPLE_FLOOR":
        issues.append("quant result gate")
    if not any(lane["lane"] == "Residual 8 blocker-clear access lane" for lane in future["future_control_lanes"]):
        issues.append("missing blocker-clear lane")
    if not any(lane["lane"] == "Future quantitative result dossier gate" for lane in future["future_control_lanes"]):
        issues.append("missing quantitative gate lane")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_forbidden_generated_keys(items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    hits = []
    for name, payload in items.items():
        # The no-leak artifact records the scanner output; scanning that artifact would
        # recursively flag its evidence fields rather than generated source semantics.
        if "NO_LEAK_DUPLICATE_SOURCE_AUDIT" in name:
            continue
        for hit in scan_forbidden_keys(payload):
            hits.append({"artifact": name, **hit})
    return {"status": "PASS" if not hits else "FAIL", "hits": hits[:50], "hit_count": len(hits)}


def check_py_compile() -> dict[str, Any]:
    results = []
    cache_dir = OUT_DIR / "__pycache__"
    cache_dir.mkdir(exist_ok=True)
    for index, name in enumerate(PY_FILES):
        cfile = cache_dir / f"v{index}.pyc"
        try:
            py_compile.compile(str(OUT_DIR / name), cfile=str(cfile), doraise=True)
            if cfile.exists():
                cfile.unlink()
            results.append({"path": name, "status": "PASS"})
        except Exception as exc:
            results.append({"path": name, "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("NOFILL_CAT_V2_FORENSICS_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "NOFILL_CAT_V2_FORENSICS_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["NOFILL_CAT_V2_FORENSICS_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(OUT_DIR / "test_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py"),
            "-q",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
        "command": f"{sys.executable} -B -m pytest -p no:cacheprovider {OUT_DIR / 'test_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py'} -q",
    }


def changed_paths_from_status() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    paths = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"').replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def changed_paths_from_head_diff() -> tuple[list[str], bool]:
    proc = subprocess.run(["git", "diff", "--name-only", "HEAD^", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [], False
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()], True


def check_live_surface_diff() -> dict[str, Any]:
    workspace_paths = changed_paths_from_status()
    committed_paths, committed_ok = changed_paths_from_head_diff()
    committed_scope_relevant = committed_ok and any(path.startswith(LANE_PREFIX) for path in committed_paths)
    checked_paths = committed_paths if committed_scope_relevant else workspace_paths
    forbidden = [path for path in checked_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    workspace_forbidden = [path for path in workspace_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    status_ok = not forbidden and (committed_scope_relevant or not workspace_forbidden)
    return {
        "status": "PASS" if status_ok else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if committed_scope_relevant else "workspace_status",
        "changed_paths": checked_paths,
        "workspace_changed_paths_observed": workspace_paths,
        "forbidden_live_surface_changed_paths": forbidden,
        "workspace_forbidden_live_surface_changed_paths": workspace_forbidden,
        "checked_prefixes": list(FORBIDDEN_LIVE_PREFIXES),
    }


def write_completion(verification: dict[str, Any]) -> None:
    builder_path = OUT_DIR / "build_nofill_cat_v2_quarantined_categorical_synthesis_forensics_2026_05_09.py"
    spec = importlib.util.spec_from_file_location("nofill_cat_v2_forensics_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load forensics builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_completion_audit(status="VERIFIED_BY_FORENSICS_VERIFIER", verification=verification)


def verify_forensics(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    results: dict[str, Any] = {
        "artifact_presence": check_artifact_presence(),
        "json_parse": check_json_parse(),
        "markdown_promotion": check_markdown_promotion(),
    }
    items = payloads()
    if results["json_parse"]["status"] == "PASS":
        results.update(
            {
                "flags": check_flags(items),
                "counts_and_slices": check_counts_and_slices(items),
                "label_learning": check_label_learning(items),
                "blocker_reject_learning": check_blocker_reject_learning(items),
                "noleak_duplicate_source": check_noleak_duplicate_source(items),
                "future_routes": check_future_routes(items),
                "forbidden_generated_keys": check_forbidden_generated_keys(items),
            }
        )
    results["py_compile"] = check_py_compile()
    results["live_surface_diff"] = check_live_surface_diff()
    preliminary_status = "PASS" if all(item.get("status") in {"PASS", "SKIPPED"} for item in results.values() if isinstance(item, dict)) else "FAIL"
    if write_audit and preliminary_status == "PASS":
        preliminary = {
            "artifact_family": "NOFILL_CAT_V2_FORENSICS_VERIFICATION",
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "verification_status": {"status": "PASS"},
            "can_mark_goal_complete": True,
            "results": {**results, "focused_pytest": {"status": "PENDING_PREWRITE_FOR_NESTED_TESTS"}},
        }
        write_completion(preliminary)
    results["focused_pytest"] = run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "called with run_pytest=False"}
    status = "PASS" if all(item.get("status") in {"PASS", "SKIPPED"} for item in results.values() if isinstance(item, dict)) else "FAIL"

    verification = {
        "artifact_family": "NOFILL_CAT_V2_FORENSICS_VERIFICATION",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "verification_status": {"status": status},
        "can_mark_goal_complete": status == "PASS",
        "results": results,
    }
    if write_audit:
        write_completion(verification)
    return verification


def main() -> int:
    report = verify_forensics(run_pytest=True, write_audit=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verification_status"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
