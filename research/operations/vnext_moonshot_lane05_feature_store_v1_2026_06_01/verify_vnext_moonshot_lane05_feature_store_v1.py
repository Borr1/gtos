"""Verify vNext moonshot Lane05 Feature Store V1 artifacts."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import build_vnext_moonshot_lane05_feature_store_v1 as builder


ROUTE_DIR = Path(__file__).resolve().parent
OUT_VERIFICATION = ROUTE_DIR / "LANE05_VERIFICATION_RESULT.json"
OUT_MANIFEST = ROUTE_DIR / "LANE05_OUTPUT_MANIFEST.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE05_FOCUSED_TEST_RESULT.xml"


REQUIRED_FAMILIES = {
    "broker_feasibility",
    "correlation_cluster",
    "displacement",
    "failed_displacement",
    "htf_m15_state",
    "liquidity_sweep",
    "m1_state",
    "news_calendar",
    "origin_framework_side",
    "portfolio_state",
    "regime",
    "selected_cell_risk_proof",
    "source_completeness",
    "spread_cost",
    "stale_label_flags",
    "symbol_session_time",
    "tick_state",
    "volatility",
}

REQUIRED_DOWNSTREAM = {
    "Digital Twin",
    "Execution Policy",
    "Label Store",
    "ML",
    "Scheduler",
    "Selector",
}

REQUIRED_GAP_CODES = {
    "broker_cost_lifecycle_missing",
    "correlation_cluster_exact_row_absent",
    "h4_regime_exact_row_absent",
    "news_calendar_exact_snapshot_absent",
    "portfolio_state_exact_row_absent",
    "selected_cell_risk_exact_row_absent",
    "strict_tick_timeline_not_joined",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def output_by_name(manifest: dict[str, Any], name: str) -> dict[str, Any] | None:
    for row in (manifest.get("outputs", []) or []) + (manifest.get("files", []) or []):
        if str(row.get("path", "")).endswith(name):
            return row
    return None


def sample_rows(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    rows = []
    for row in read_jsonl(path):
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def has_forbidden_features(row: dict[str, Any]) -> list[str]:
    return builder.feature_row_has_forbidden_fields(row)


def refresh_manifest_with_verifier_artifacts() -> dict[str, Any]:
    current = read_json(OUT_MANIFEST)
    manifest = builder.write_manifest(current.get("generated_at_utc") or builder.utc_now())
    known = {row.get("path") for row in manifest.get("outputs", [])}
    for path in (Path(__file__), OUT_VERIFICATION, FOCUSED_TEST_RESULT):
        rel = builder.as_posix(path)
        if rel in known or not path.exists():
            continue
        manifest["outputs"].append(
            {
                "bytes": path.stat().st_size,
                "exists": True,
                "line_count": builder.count_lines(path) if path.suffix in {".jsonl", ".gz", ".md", ".py", ".xml"} else None,
                "path": rel,
                "sha256": builder.sha256_file(path),
            }
        )
    manifest["output_count"] = len(manifest.get("outputs", []))
    builder.write_json(OUT_MANIFEST, manifest)
    return manifest


def verify() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    required_files = [
        builder.OUT_FEATURE_SCHEMA,
        builder.OUT_TIMELINE_FEATURES,
        builder.OUT_CANONICAL_FEATURES,
        builder.OUT_COVERAGE,
        builder.OUT_SOURCE_COMPLETENESS,
        builder.OUT_SOURCE_GAPS,
        builder.OUT_NO_LEAK,
        builder.OUT_IMPORTANCE,
        builder.OUT_DOWNSTREAM,
        builder.OUT_DEPENDENCY,
        builder.OUT_BRANCH,
        builder.OUT_RESULT_USE,
        builder.OUT_RUNTIME_BOUNDARY,
        builder.OUT_CONTEXT_ANCHOR,
        builder.OUT_COMPLETION_AUDIT,
        builder.OUT_MANIFEST,
        Path(__file__),
    ]
    missing = [builder.as_posix(path) for path in required_files if not path.exists()]
    checks.append({"check": "required_files_present", "ok": not missing, "missing": missing})

    manifest = read_json(builder.OUT_MANIFEST)
    lane03_expected = output_by_name(read_json(builder.LANE03_MANIFEST), "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz")
    lane04_expected = output_by_name(read_json(builder.LANE04_MANIFEST), "LANE04_ROW_TIMELINE_LEDGER.jsonl")
    canonical_output = output_by_name(manifest, "LANE05_CANONICAL_CANDIDATE_FEATURE_VECTOR_LEDGER.jsonl.gz")
    timeline_output = output_by_name(manifest, "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz")
    checks.append(
        {
            "actual": (canonical_output or {}).get("line_count"),
            "check": "canonical_feature_partition_matches_lane03_canonical_rows",
            "expected": (lane03_expected or {}).get("line_count"),
            "ok": (canonical_output or {}).get("line_count") == (lane03_expected or {}).get("line_count"),
        }
    )
    checks.append(
        {
            "actual": (timeline_output or {}).get("line_count"),
            "check": "timeline_feature_partition_matches_lane04_timeline_rows",
            "expected": (lane04_expected or {}).get("line_count"),
            "ok": (timeline_output or {}).get("line_count") == (lane04_expected or {}).get("line_count"),
        }
    )

    schema = read_json(builder.OUT_FEATURE_SCHEMA)
    families = {row.get("feature_namespace") for row in schema.get("features", [])}
    checks.append(
        {
            "check": "required_feature_families_present",
            "missing": sorted(REQUIRED_FAMILIES - families),
            "ok": REQUIRED_FAMILIES <= families,
            "present_count": len(families),
        }
    )

    no_leak_rows = list(read_jsonl(builder.OUT_NO_LEAK))
    failing_no_leak = [row for row in no_leak_rows if row.get("no_leak_status") != "pass"]
    checks.append({"check": "no_leak_validation_passes", "fail_count": len(failing_no_leak), "ok": not failing_no_leak})

    sampled = sample_rows(builder.OUT_TIMELINE_FEATURES) + sample_rows(builder.OUT_CANONICAL_FEATURES)
    forbidden_samples = []
    timestamp_violations = []
    for row in sampled:
        forbidden = has_forbidden_features(row)
        if forbidden:
            forbidden_samples.append({"row_id": row.get("row_id"), "forbidden": forbidden})
        feature_time = builder.parse_dt(row.get("feature_time_utc"))
        decision_time = builder.parse_dt(row.get("decision_asof_utc"))
        if feature_time and decision_time and feature_time > decision_time:
            timestamp_violations.append(row.get("row_id"))
    checks.append(
        {
            "check": "sample_feature_rows_have_no_forbidden_feature_names",
            "fail_count": len(forbidden_samples),
            "ok": not forbidden_samples,
            "sample_count": len(sampled),
        }
    )
    checks.append(
        {
            "check": "sample_feature_rows_are_asof_valid",
            "fail_count": len(timestamp_violations),
            "ok": not timestamp_violations,
            "sample_count": len(sampled),
        }
    )

    downstream = read_json(builder.OUT_DOWNSTREAM)
    downstream_keys = set((downstream.get("contracts") or {}).keys())
    checks.append(
        {
            "check": "downstream_contract_covers_required_lanes",
            "missing": sorted(REQUIRED_DOWNSTREAM - downstream_keys),
            "ok": REQUIRED_DOWNSTREAM <= downstream_keys,
        }
    )

    gap_codes = {row.get("gap_code") for row in read_jsonl(builder.OUT_SOURCE_GAPS)}
    checks.append(
        {
            "check": "source_gap_ledger_covers_material_gap_families",
            "missing": sorted(REQUIRED_GAP_CODES - gap_codes),
            "ok": REQUIRED_GAP_CODES <= gap_codes,
        }
    )

    completion = read_json(builder.OUT_COMPLETION_AUDIT)
    coverage = completion.get("instruction_coverage") or {}
    false_items = sorted(key for key, value in coverage.items() if value is not True)
    checks.append({"check": "completion_audit_instruction_coverage_true", "false_items": false_items, "ok": not false_items})

    manifest_paths = {row.get("path") for row in manifest.get("outputs", [])}
    route_only = all(
        str(path or "").startswith("research/operations/vnext_moonshot_lane05_feature_store_v1_2026_06_01/")
        for path in manifest_paths
    )
    checks.append({"check": "manifest_outputs_are_route_scoped", "ok": route_only})

    ok = all(row.get("ok") for row in checks)
    result = {
        "checks": checks,
        "feature_set_id": builder.FEATURE_SET_ID,
        "ok": ok,
        "route_id": builder.ROUTE_ID,
        "runtime_effect_boundary": builder.RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane05_verification_result_v1",
    }
    builder.write_json(OUT_VERIFICATION, result)
    completion = read_json(builder.OUT_COMPLETION_AUDIT)
    completion["completion_status"] = "complete_verified" if ok else "verification_failed"
    completion["verification_result"] = {
        "ok": ok,
        "path": builder.as_posix(OUT_VERIFICATION),
        "schema_version": "lane05_verification_result_v1",
    }
    builder.write_json(builder.OUT_COMPLETION_AUDIT, completion)
    refresh_manifest_with_verifier_artifacts()
    return result


def main() -> None:
    result = verify()
    print(json.dumps({"ok": result["ok"], "route_id": result["route_id"]}, sort_keys=True))
    if not result["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
