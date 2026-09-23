#!/usr/bin/env python3
"""Verify OTI3 G3 geometry quarantined outcome-audit artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE = "2026-05-07"
EXPECTED_PACKETS = ["OTG0-PKT-031", "OTG0-PKT-032", "OTG0-PKT-036"]
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> dict[str, Any]:
    with (OUT / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(name: str) -> list[dict[str, Any]]:
    with (OUT / name).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def expect_common_flags(errors: list[str], label: str, payload: dict[str, Any]) -> None:
    expect(errors, payload.get("promotion_verdict") == PROMOTION_VERDICT, f"{label}: promotion verdict drifted")
    expect(errors, payload.get("validation_safe") is False, f"{label}: validation_safe is not false")
    expect(errors, payload.get("outcome_review_opened") is False, f"{label}: outcome_review_opened is not false")


def packet_result(result: dict[str, Any], packet_id: str) -> dict[str, Any]:
    for item in result["packet_results"]:
        if item["packet_id"] == packet_id:
            return item
    raise AssertionError(f"missing packet result {packet_id}")


def main() -> int:
    errors: list[str] = []
    result = load_json(f"OTI3_G3_GEOMETRY_RESULT_LEDGER_{DATE}.json")
    source = load_json(f"OTI3_G3_GEOMETRY_SOURCE_HASH_COVERAGE_REPORT_{DATE}.json")
    duplicate = load_json(f"OTI3_G3_GEOMETRY_DUPLICATE_DENOMINATOR_REPORT_{DATE}.json")
    label = load_json(f"OTI3_G3_GEOMETRY_LABEL_FAMILY_SEPARATION_REPORT_{DATE}.json")
    ambiguity = load_json(f"OTI3_G3_GEOMETRY_AMBIGUITY_RESOLUTION_LEDGER_{DATE}.json")
    blocker = load_json(f"OTI3_G3_GEOMETRY_BLOCKER_LEDGER_{DATE}.json")
    self_review = load_json(f"OTI3_G3_GEOMETRY_SELF_REVIEW_{DATE}.json")
    completion = load_json(f"OTI3_G3_GEOMETRY_COMPLETION_AUDIT_{DATE}.json")
    method = load_json(f"OTI3_G3_GEOMETRY_METHOD_FREEZE_{DATE}.json")
    manifest = load_json(f"OTI3_G3_GEOMETRY_ARTIFACT_MANIFEST_{DATE}.json")
    rows = load_jsonl(f"OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_{DATE}.jsonl")

    for name, payload in {
        "result": result,
        "source": source,
        "duplicate": duplicate,
        "label": label,
        "ambiguity": ambiguity,
        "blocker": blocker,
        "self_review": self_review,
        "completion": completion,
        "method": method,
        "manifest": manifest,
    }.items():
        expect_common_flags(errors, name, payload)

    expect(errors, method.get("frozen_before_g3_path_label_inspection") is True, "method freeze does not assert pre-label freeze")
    expect(errors, method["scope"]["allowed_packet_ids"] == EXPECTED_PACKETS, "method freeze packet scope drifted")
    expect(errors, result["scope_packet_ids"] == EXPECTED_PACKETS, "result packet scope drifted")
    expect(errors, completion.get("can_mark_oti3_complete") is True, "completion audit is not complete")
    expect(errors, result.get("broker_actual_r_inspected") is False, "broker actual-R was inspected")
    expect(errors, result.get("blocked_packet_outcomes_inspected") is False, "blocked-packet outcomes were inspected")
    expect(errors, result.get("live_trade_results_inspected") is False, "live trade results were inspected")
    expect(errors, label.get("packet_forbidden_record_key_hits") == [], "packet hidden-result scan has hits")
    expect(errors, label.get("broker_actual_r_inspected") is False, "label report broker actual-R flag drifted")
    expect(errors, label.get("blocked_packet_outcomes_inspected") is False, "label report blocked-outcome flag drifted")
    expect(errors, label.get("live_trade_results_inspected") is False, "label report live-results flag drifted")
    expect(errors, label.get("lifecycle_no_fill_labels_inspected") is False, "label report lifecycle flag drifted")

    expect(errors, len(rows) == 199, f"row ledger count drifted: {len(rows)}")
    expect(errors, result["raw_rows_across_packets"] == 199, "result raw row count drifted")
    expect(errors, duplicate["raw_rows_across_packets"] == 199, "duplicate raw row count drifted")
    expect(errors, duplicate["unique_parent_duplicate_groups_unpooled"] == 96, "parent duplicate denominator drifted")
    expect(errors, duplicate["parent_groups_appearing_in_multiple_packets"] == 95, "cross-packet duplicate trap count drifted")

    expected_raw = {"OTG0-PKT-031": 95, "OTG0-PKT-032": 8, "OTG0-PKT-036": 96}
    expected_resolved = {"OTG0-PKT-031": 46, "OTG0-PKT-032": 7, "OTG0-PKT-036": 46}
    for packet_id in EXPECTED_PACKETS:
        item = packet_result(result, packet_id)
        expect(errors, item["raw_rows"] == expected_raw[packet_id], f"{packet_id}: raw row count drifted")
        expect(errors, item["non_ambiguous_resolved_count"] == expected_resolved[packet_id], f"{packet_id}: resolved count drifted")
        expect(errors, item["primary_prereg_metric_status"] == "not_computable", f"{packet_id}: primary metric became computable")
        expect(errors, bool(item["primary_prereg_metric_not_computable_reasons"]), f"{packet_id}: missing not-computable reasons")
        expect(errors, item["sample_floor_warning"], f"{packet_id}: missing sample floor warning")

    source_counts = source["outcome_source_status_counts"]
    expect(errors, source_counts.get("M1_OUTCOME_SOURCE_SELECTED") == 123, "M1 selected source count drifted")
    expect(errors, source_counts.get("NO_PRICE_COMPATIBLE_M1_SOURCE") == 69, "USDJPY price-scale blocker count drifted")
    expect(errors, source_counts.get("NO_LOCAL_M1_SOURCE_FOR_SYMBOL") == 7, "GBPJPY no-source blocker count drifted")
    expect(errors, source["packet_source_hash_failure_count"] == 0, "packet source hash failures present")
    expect(errors, all(item["sha256_match"] and item["row_source_hash_failures"] == 0 for item in source["packet_file_hashes"]), "packet file or row source hashes failed")

    stats = result["statistics_status"]
    expect(errors, stats["raw_p"]["status"] == "not_computable", "raw p unexpectedly computable")
    expect(errors, stats["dsr"]["status"] == "not_computable", "DSR unexpectedly computable")
    expect(errors, stats["pbo"]["status"] == "not_computable", "PBO unexpectedly computable")
    expect(errors, stats["sample_floor_pass_by_packet"] == {packet_id: False for packet_id in EXPECTED_PACKETS}, "sample floor pass flags drifted")

    feature_031 = [
        item for item in result["feature_diagnostics"]
        if item["packet_id"] == "OTG0-PKT-031" and item["feature"] == "max_dc_overshoot_ratio"
    ][0]
    expect(errors, feature_031["non_ambiguous_pair_count"] == 46, "OTG0-PKT-031 feature diagnostic lost resolved pairs")
    expect(errors, feature_031["raw_p_status"] == "not_computable", "OTG0-PKT-031 raw p unexpectedly computable")

    expect(errors, ambiguity["terminal_order_claim_allowed"] is False, "same-bar terminal order claims are allowed")
    expect(errors, ambiguity["same_bar_ambiguous_row_count"] == 26, "same-bar ambiguity count drifted")
    expect(errors, any("PRICE-SCALE" in item["blocker_id"] for item in blocker["blockers"]), "missing price-scale blocker")
    expect(errors, any("MISSING-M1-SOURCE" in item["blocker_id"] for item in blocker["blockers"]), "missing M1-source blocker")
    expect(
        errors,
        self_review["strongest_reason_status"] == "MITIGATED_BUT_RECORDED_AS_RESIDUAL_G12_PACKETIZATION_QUESTION",
        "self-review residual status drifted",
    )

    manifest_paths = {item["path"]: item for item in manifest["artifacts"]}
    required_manifest_paths = [
        rel(OUT / f"build_oti3_g3_geometry_quarantined_results_2026_05_07.py"),
        rel(OUT / f"verify_oti3_g3_geometry_quarantined_results_2026_05_07.py"),
        rel(OUT / f"OTI3_G3_GEOMETRY_RESULT_LEDGER_{DATE}.json"),
        rel(OUT / f"OTI3_G3_GEOMETRY_COMPLETION_AUDIT_{DATE}.json"),
        rel(OUT / f"OTI3_G3_GEOMETRY_METHOD_FREEZE_{DATE}.json"),
    ]
    for manifest_path in required_manifest_paths:
        expect(errors, manifest_path in manifest_paths, f"manifest missing {manifest_path}")
    for manifest_path, item in manifest_paths.items():
        path = ROOT / manifest_path
        expect(errors, path.exists(), f"manifest path missing on disk: {manifest_path}")
        if path.exists():
            expect(errors, sha256_file(path) == item["sha256"], f"manifest hash mismatch: {manifest_path}")
            expect(errors, path.stat().st_size == item["size_bytes"], f"manifest size mismatch: {manifest_path}")

    if errors:
        print(json.dumps({"status": "FAIL", "error_count": len(errors), "errors": errors}, indent=2, sort_keys=True))
        return 1
    print(json.dumps({"status": "PASS", "checked_packets": EXPECTED_PACKETS, "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
