"""Verifier for the READY8 discriminative card rowset repair artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN"
EVIDENCE_CLASS = "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY"
DATE = "2026-05-13"
ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
READY_CARDS = ["ADV-001", "ADV-003", "BEH-001", "HAZ-001", "HAZ-005", "MAC-001", "MAC-004", "UNC-004"]

OUTPUTS = {
    "decision_ledger": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_DECISION_LEDGER_{DATE}.json",
    "source_field_map": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SOURCE_FIELD_MAP_LEDGER_{DATE}.json",
    "predicate_ledger": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_PREDICATE_DESCRIPTOR_CONTRAST_LEDGER_{DATE}.json",
    "rowset_rows": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_{DATE}.jsonl",
    "rowset_manifest": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_MANIFEST_{DATE}.json",
    "denominator_duplicate_policy": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_DENOMINATOR_DUPLICATE_POLICY_LEDGER_{DATE}.json",
    "fail_closed_policy": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_FAIL_CLOSED_POLICY_LEDGER_{DATE}.json",
    "partition_design": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SEALED_STRESS_PARTITION_DESIGN_LEDGER_{DATE}.json",
    "target_prereq": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_TARGET_OPENING_PREREQUISITE_LEDGER_{DATE}.json",
    "blocker_source_repair": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_BLOCKER_SOURCE_REPAIR_LEDGER_{DATE}.json",
    "searched_root": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SEARCHED_ROOT_LEDGER_{DATE}.json",
    "saturation": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "completion_audit": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_COMPLETION_AUDIT_{DATE}.json",
    "synthesis": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_SYNTHESIS_{DATE}.md",
    "output_manifest": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_OUTPUT_MANIFEST_{DATE}.json",
    "verification_result": ROUTE_DIR / f"SCID_READY8_DISCRIMINATIVE_VERIFICATION_RESULT_{DATE}.json",
}

FORBIDDEN_FIELDS = {
    "target_hit",
    "stop_hit",
    "actual_r",
    "pnl",
    "win_rate",
    "expectancy",
    "performance_metric",
    "validated_edge",
    "broker_account",
    "order_ticket",
    "deal_id",
    "position_id",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def collect_keys(obj: Any) -> set[str]:
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.add(str(key))
            keys.update(collect_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(collect_keys(item))
    return keys


def verify_outputs() -> dict[str, Any]:
    checks = []

    for key, path in OUTPUTS.items():
        if key == "verification_result":
            continue
        checks.append({"check": f"{key}_exists", "ok": path.exists(), "path": rel(path)})

    json_artifacts = {k: read_json(p) for k, p in OUTPUTS.items() if p.exists() and p.suffix == ".json" and k != "verification_result"}
    rows = read_jsonl(OUTPUTS["rowset_rows"]) if OUTPUTS["rowset_rows"].exists() else []
    manifest = json_artifacts.get("rowset_manifest", {})

    cards_in_rows = sorted({row.get("card_id") for row in rows})
    checks.append({"check": "exact_ready8_cards_in_rowset", "ok": cards_in_rows == READY_CARDS, "value": cards_in_rows})
    checks.append({"check": "rowset_row_count_24112", "ok": len(rows) == 24112, "value": len(rows)})
    checks.append({"check": "candidate_universe_3014", "ok": manifest.get("candidate_universe_count") == 3014, "value": manifest.get("candidate_universe_count")})
    checks.append({"check": "rowset_hash_matches_manifest", "ok": file_sha256(OUTPUTS["rowset_rows"]) == manifest.get("rowset_rows_sha256"), "value": manifest.get("rowset_rows_sha256")})

    source_cards = sorted(row["card_id"] for row in json_artifacts["source_field_map"]["cards"])
    predicate_cards = sorted(row["card_id"] for row in json_artifacts["predicate_ledger"]["cards"])
    checks.append({"check": "source_field_map_all_cards", "ok": source_cards == READY_CARDS, "value": source_cards})
    checks.append({"check": "predicate_ledger_all_cards", "ok": predicate_cards == READY_CARDS, "value": predicate_cards})

    per_card_counts = {}
    for card_id in READY_CARDS:
        card_rows = [row for row in rows if row["card_id"] == card_id]
        status_counts = Counter(row["card_row_status"] for row in card_rows)
        contrast_count = len({row["descriptor_contrast_key"] for row in card_rows})
        predicate_count = len({row["card_predicate_id"] for row in card_rows})
        per_card_counts[card_id] = {
            "row_count": len(card_rows),
            "status_counts": dict(status_counts),
            "contrast_count": contrast_count,
            "predicate_count": predicate_count,
        }
        checks.append({
            "check": f"{card_id}_not_merely_repeated",
            "ok": len(card_rows) == 3014 and contrast_count > 1 and predicate_count == 1,
            "value": per_card_counts[card_id],
        })

    fail_closed_count = sum(1 for row in rows if row["denominator_role"] == "per_card_fail_closed_row")
    non_applicable_count = sum(1 for row in rows if row["denominator_role"] == "per_card_non_applicable_row")
    checks.append({"check": "fail_closed_rows_retained", "ok": fail_closed_count > 0, "value": fail_closed_count})
    checks.append({"check": "non_applicable_rows_retained", "ok": non_applicable_count > 0, "value": non_applicable_count})

    denominator = json_artifacts["denominator_duplicate_policy"]
    checks.append({"check": "denominator_roles_explicit", "ok": set(denominator["per_card_denominator_policy"]) == {"per_card_pass_rows", "per_card_contrast_rows", "per_card_fail_closed_rows", "per_card_non_applicable_rows"}})
    checks.append({"check": "duplicate_policy_explicit", "ok": denominator["duplicate_policy"]["primary_duplicate_key"] == "duplicate_proxy_denominator_key"})

    fail_closed = json_artifacts["fail_closed_policy"]
    checks.append({"check": "fail_closed_policy_retains_rows", "ok": "not inferred, dropped, or counted as passes" in fail_closed["policy"]})
    partition = json_artifacts["partition_design"]
    checks.append({"check": "existing_partitions_source_control_only", "ok": partition["existing_ready8_partition_labels_are_source_control_only"] is True})
    target = json_artifacts["target_prereq"]
    checks.append({"check": "target_opening_closed", "ok": target["target_opening_current_status"] == "CLOSED" and target["target_opening_allowed_in_this_route"] is False})
    blockers = json_artifacts["blocker_source_repair"]
    checks.append({"check": "same_evidence_class_blockers_zero", "ok": blockers["same_evidence_class_blockers_remaining"] == 0})
    saturation = json_artifacts["saturation"]
    checks.append({"check": "saturation_remaining_zero", "ok": saturation["same_evidence_class_repair_design_intelligence_remaining"] == 0})

    safe_ok = True
    forbidden_ok = True
    forbidden_hits = defaultdict(list)
    for artifact_id, obj in json_artifacts.items():
        if obj.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            safe_ok = False
        if obj.get("validation_safe") is not False:
            safe_ok = False
        if obj.get("outcome_review_opened") is not False:
            safe_ok = False
        if obj.get("live_effect") is not False:
            safe_ok = False
        for flag in [
            "opens_result_scoring",
            "opens_validation",
            "opens_strategy_edge_claims",
            "opens_live_trading_behavior",
            "opens_ai_api",
            "opens_paid_or_vendor_access",
            "opens_broker_account_order_history_deal_position_evidence",
            "opens_raw_market_data_blob_commit",
            "opens_registry_edit",
            "opens_remote_push",
        ]:
            if obj.get(flag) is not False:
                forbidden_ok = False
        bad_keys = collect_keys(obj) & FORBIDDEN_FIELDS
        if bad_keys:
            forbidden_ok = False
            forbidden_hits[artifact_id].extend(sorted(bad_keys))

    for row in rows[:500] + rows[-500:]:
        bad_keys = set(row) & FORBIDDEN_FIELDS
        if bad_keys:
            forbidden_ok = False
            forbidden_hits["rowset_rows_sample"].extend(sorted(bad_keys))

    checks.append({"check": "safe_flags_preserved", "ok": safe_ok})
    checks.append({"check": "forbidden_surfaces_closed", "ok": forbidden_ok, "forbidden_hits": dict(forbidden_hits)})

    completion = json_artifacts["completion_audit"]
    checklist_ok = all(item.get("status") == "PASS" for item in completion["prompt_to_artifact_checklist"])
    checks.append({"check": "completion_checklist_passes", "ok": checklist_ok})
    checks.append({"check": "completion_can_mark_after_commits", "ok": completion["can_mark_goal_complete_after_verifier_and_scoped_commits"] is True})

    ok = all(check["ok"] for check in checks)
    return {
        "artifact_family": "verification_result",
        "schema_version": "scid_ready8_discriminative_card_rowset_repair_verification_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "ok": ok,
        "checks": checks,
        "per_card_counts": per_card_counts,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "opens_live_trading_behavior": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = verify_outputs()
    if args.write:
        OUTPUTS["verification_result"].write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"ok": result["ok"], "checks": len(result["checks"]), "path": rel(OUTPUTS["verification_result"])}, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
