#!/usr/bin/env python3
"""Verify READY8 adversarial control/placebo drift audit outputs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import build_ready8_adversarial_control_placebo_drift_audit_2026_05_15 as b


def count_jsonl(path: Path) -> int:
    rows = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                json.loads(line)
                rows += 1
    return rows


def safe_flag_errors(path: Path) -> list[str]:
    errors: list[str] = []
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else [payload]
    elif path.suffix == ".jsonl":
        records = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    else:
        return errors
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        for key, expected in {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }.items():
            if key in record and record.get(key) != expected:
                errors.append(f"{path.name}:{idx}:{key}={record.get(key)!r}")
    return errors


def recompute_expected_counts() -> dict[str, Any]:
    all_branch_rows = 0
    card_counts = Counter()
    baseline_axis_rows = 0
    duplicate_bucket_branch_rows = 0
    stress_pair_keys = set()
    for record in b.iter_jsonl(b.ALL_BRANCHES):
        all_branch_rows += 1
        card = (record.get("branch_key") or {}).get("card_id")
        card_counts[card] += 1
        axis, _ = b.axis_from_branch(record)
        if axis is not None:
            baseline_axis_rows += 1
        if record.get("branch_family") == "card_duplicate_hash_bucket_target_family_horizon":
            duplicate_bucket_branch_rows += 1
        stress_pair_keys.add(b.stress_pair_key(record))

    pass_control_rows = 0
    non_adv_comparison_rows = 0
    for record in b.iter_jsonl(b.PASS_CONTROL):
        pass_control_rows += 1
        if (record.get("branch_key") or {}).get("card_id") not in b.CONTROL_CARDS:
            non_adv_comparison_rows += 1

    dup_effective_rows = count_jsonl(b.DUP_EFFECTIVE)
    return {
        "all_branch_rows": all_branch_rows,
        "adv001_rows": card_counts["ADV-001"],
        "adv003_rows": card_counts["ADV-003"],
        "baseline_axis_rows": baseline_axis_rows,
        "duplicate_artifact_rows": duplicate_bucket_branch_rows + dup_effective_rows,
        "non_adv_comparison_rows": non_adv_comparison_rows,
        "stress_vs_sealed_rows": len(stress_pair_keys),
    }


def main() -> None:
    expected = recompute_expected_counts()
    actual = {
        "adv001_rows": count_jsonl(b.OUTPUTS["adv001_placebo"]),
        "adv003_rows": count_jsonl(b.OUTPUTS["adv003_placebo"]),
        "baseline_axis_rows": count_jsonl(b.OUTPUTS["baseline_drift"]),
        "duplicate_artifact_rows": count_jsonl(b.OUTPUTS["duplicate_artifact"]),
        "non_adv_comparison_rows": count_jsonl(b.OUTPUTS["comparison_mapping"]),
        "stress_vs_sealed_rows": count_jsonl(b.OUTPUTS["stress_vs_sealed"]),
        "underpower_rows": count_jsonl(b.OUTPUTS["underpower"]),
        "concentration_rows": count_jsonl(b.OUTPUTS["concentration_adjusted"]),
    }

    issues: list[str] = []
    for key, expected_value in expected.items():
        actual_key = key
        if key == "all_branch_rows":
            continue
        if actual.get(actual_key) != expected_value:
            issues.append(f"{actual_key}: expected {expected_value}, got {actual.get(actual_key)}")
    if actual["underpower_rows"] != expected["all_branch_rows"]:
        issues.append(f"underpower_rows: expected {expected['all_branch_rows']}, got {actual['underpower_rows']}")
    if actual["concentration_rows"] != expected["all_branch_rows"]:
        issues.append(f"concentration_rows: expected {expected['all_branch_rows']}, got {actual['concentration_rows']}")

    required_keys = [
        "context_anchor",
        "control_design",
        "negative_controls",
        "explained_weakened",
        "adjustment_rules",
        "saturation",
        "synthesis",
        "g12_prompt",
        "g12_starter",
        "completion_audit",
        "focused_test",
        "manifest",
    ]
    missing = [key for key in required_keys if not b.OUTPUTS[key].exists()]
    if missing:
        issues.append(f"missing outputs: {missing}")

    focused = json.loads(b.OUTPUTS["focused_test"].read_text(encoding="utf-8"))
    if focused.get("status") != "PASSED":
        issues.append(f"focused test status is {focused.get('status')!r}")

    safe_errors: list[str] = []
    for key, path in b.OUTPUTS.items():
        if key == "verification" or not path.exists():
            continue
        safe_errors.extend(safe_flag_errors(path))
    if safe_errors:
        issues.append(f"safe flag errors: {safe_errors[:20]}")

    adjustment = json.loads(b.OUTPUTS["adjustment_rules"].read_text(encoding="utf-8"))
    for card in b.DOWNSTREAM_CARDS:
        if card not in adjustment.get("per_card_rules", {}):
            issues.append(f"missing downstream adjustment rules for {card}")

    saturation = json.loads(b.OUTPUTS["saturation"].read_text(encoding="utf-8"))
    if saturation.get("same_evidence_class_blockers_remaining") != 0:
        issues.append("same evidence class blockers remaining is not zero")

    result = {
        "schema_version": "ready8_adv_control_verification_result_v1",
        "route_id": b.ROUTE_ID,
        "evidence_class": b.EVIDENCE_CLASS,
        "generated_at_utc": b.now_utc(),
        **b.SAFE_FLAGS,
        "ok": not issues,
        "issues": issues,
        "expected_counts": expected,
        "actual_counts": actual,
        "can_mark_goal_complete": not issues,
    }
    b.write_json(b.OUTPUTS["verification"], result)
    b.write_manifest()
    print(json.dumps(result, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
