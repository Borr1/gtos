#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROUTE_DIR = Path(__file__).resolve().parent
REQUIRED = [
    "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz",
    "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz",
    "POST_LANE18_SOURCE_COVERAGE_DELTA_LEDGER.jsonl",
    "POST_LANE18_PARSER_HELPER_IMPLEMENTATION_LEDGER.jsonl",
    "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
    "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
    "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz",
    "POST_LANE18_SOURCE_ASOF_NOLEAK_VALIDATION_LEDGER.jsonl",
    "POST_LANE18_DOWNSTREAM_CONTRACTS.json",
    "POST_LANE18_RESULT_USE_STATUS.json",
    "POST_LANE18_SOURCE_CAPTURE_DECISIONS.jsonl",
    "POST_LANE18_SOURCE_COMPLETENESS_DECISIONS.jsonl",
    "POST_LANE18_BRANCH_DECISION_LEDGER.jsonl",
    "POST_LANE18_IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "POST_LANE18_FIELD_FAMILY_SUMMARY.json",
    "POST_LANE18_SOURCE_INDEX.json",
    "POST_LANE18_SOURCE_ROOT_SEARCH_LEDGER.jsonl",
    "POST_LANE18_SATURATION_SELF_RED_TEAM.md",
    "POST_LANE18_CONTEXT_ANCHOR.md",
    "POST_LANE18_OUTPUT_MANIFEST.json",
    "POST_LANE18_COMPLETION_AUDIT.json",
]
VERIFICATION_RESULT = "POST_LANE18_VERIFICATION_RESULT.json"
CRITICAL_LEDGER_ROW_KEYS = {
    "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz": ("source_stats", "superledger_rows"),
    "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz": ("derived_stats", "repaired_rows"),
    "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz": (
        "derived_stats",
        "read_only_export_requirement_rows",
    ),
    "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz": ("derived_stats", "forward_capture_contract_rows"),
    "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz": ("derived_stats", "non_generatable_rows"),
}


def iter_jsonl(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_rows(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel_artifact_path(name: str) -> str:
    return f"research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/{name}"


def upsert_manifest_artifact(name: str, row_count: int | None = None) -> dict:
    path = ROUTE_DIR / name
    manifest_path = ROUTE_DIR / "POST_LANE18_OUTPUT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rel_path = rel_artifact_path(name)
    artifact = {
        "path": rel_path,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if row_count is not None:
        artifact["row_count"] = int(row_count)
    artifacts = [row for row in manifest.get("artifacts", []) if row.get("path") != rel_path]
    artifacts.append(artifact)
    artifacts.sort(key=lambda row: row["path"])
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def update_completion_audit(result: dict, verification_sha256: str, manifest_artifact_count: int) -> None:
    audit_path = ROUTE_DIR / "POST_LANE18_COMPLETION_AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["manifest_artifact_count"] = manifest_artifact_count
    audit["verification_result"] = {
        "path": rel_artifact_path(VERIFICATION_RESULT),
        "sha256": verification_sha256,
        "ok": result["ok"],
        "issue_count": result["issue_count"],
        "superledger_rows": result["superledger_rows"],
        "derived_stats": result["derived_stats"],
        "critical_ledger_checks": result["critical_ledger_checks"],
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def expected_row_count(summary: dict, name: str) -> int:
    top_key, count_key = CRITICAL_LEDGER_ROW_KEYS[name]
    return int((summary.get(top_key) or {}).get(count_key) or 0)


def main() -> int:
    issues: list[str] = []
    for name in REQUIRED:
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append(f"missing_required:{name}")
        elif path.stat().st_size == 0:
            issues.append(f"empty_required:{name}")

    summary = json.loads((ROUTE_DIR / "POST_LANE18_FIELD_FAMILY_SUMMARY.json").read_text(encoding="utf-8"))
    super_rows = int(summary["source_stats"].get("superledger_rows") or 0)
    if super_rows <= 0:
        issues.append("superledger_has_no_rows")

    dispositions = summary["source_stats"].get("disposition_counts") or {}
    for required_disposition in (
        "filled_now",
        "proxy_bound_now",
        "read_only_export_required",
        "forward_capture_required",
        "non_generatable_historical_truth",
    ):
        if int(dispositions.get(required_disposition, 0)) <= 0:
            issues.append(f"missing_disposition:{required_disposition}")

    derived = summary.get("derived_stats") or {}
    for key in (
        "repaired_rows",
        "read_only_export_requirement_rows",
        "forward_capture_contract_rows",
        "non_generatable_rows",
        "validation_rows",
    ):
        if int(derived.get(key) or 0) <= 0:
            issues.append(f"derived_count_zero:{key}")

    field_dispositions = summary["source_stats"].get("field_disposition_counts") or {}
    forbidden_generic_blockers = (
        "unspecified_source_gap|blocked_with_exact_source_requirement",
        "joined_microscope_label_replay_scheduler|blocked_with_exact_source_requirement",
        "cost_adjusted_r|blocked_with_exact_source_requirement",
        "net_r|blocked_with_exact_source_requirement",
        "missing_replay_gap_capture_or_repair|blocked_with_exact_source_requirement",
        "news_calendar|blocked_with_exact_source_requirement",
        "selected_cell_risk_proof|blocked_with_exact_source_requirement",
        "portfolio_state|blocked_with_exact_source_requirement",
    )
    for key in forbidden_generic_blockers:
        if int(field_dispositions.get(key, 0)) > 0:
            issues.append(f"forbidden_generic_blocker:{key}:{field_dispositions[key]}")

    manifest = json.loads((ROUTE_DIR / "POST_LANE18_OUTPUT_MANIFEST.json").read_text(encoding="utf-8"))
    manifest_rows = {row["path"].replace("\\", "/"): row for row in manifest.get("artifacts", [])}
    manifest_paths = set(manifest_rows)
    for name in REQUIRED:
        rel = f"research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/{name}"
        if rel not in manifest_paths:
            issues.append(f"manifest_missing:{name}")

    ledger_checks = {}
    for name in CRITICAL_LEDGER_ROW_KEYS:
        rel = f"research/operations/vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01/{name}"
        path = ROUTE_DIR / name
        manifest_row = manifest_rows.get(rel)
        if not manifest_row:
            continue
        current_size = path.stat().st_size
        current_sha = sha256_file(path)
        current_rows = count_rows(path)
        expected_rows = expected_row_count(summary, name)
        ledger_checks[name] = {
            "manifest_size_bytes": manifest_row.get("size_bytes"),
            "current_size_bytes": current_size,
            "manifest_sha256": manifest_row.get("sha256"),
            "current_sha256": current_sha,
            "manifest_row_count": manifest_row.get("row_count"),
            "expected_row_count": expected_rows,
            "current_row_count": current_rows,
        }
        if int(manifest_row.get("size_bytes") or -1) != current_size:
            issues.append(f"manifest_size_mismatch:{name}")
        if manifest_row.get("sha256") != current_sha:
            issues.append(f"manifest_sha256_mismatch:{name}")
        if int(manifest_row.get("row_count") or -1) != expected_rows:
            issues.append(f"manifest_row_count_summary_mismatch:{name}")
        if current_rows != expected_rows:
            issues.append(f"ledger_row_count_mismatch:{name}:current={current_rows}:expected={expected_rows}")

    first = next(iter_jsonl(ROUTE_DIR / "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz"))
    for key in ("superledger_row_id", "source_input_path", "source_line", "field_dispositions", "downstream_consumers"):
        if key not in first:
            issues.append(f"superledger_missing_key:{key}")
    for field in first.get("field_dispositions", []):
        for key in ("field_family", "disposition", "source_class", "exact_source_requirement", "asof_status", "no_leak_status"):
            if not field.get(key):
                issues.append(f"field_disposition_missing:{key}")

    result = {
        "schema_version": "post_lane18_verification_result_v1",
        "route_id": "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues[:100],
        "superledger_rows": super_rows,
        "derived_stats": derived,
        "critical_ledger_checks": ledger_checks,
    }
    (ROUTE_DIR / "POST_LANE18_VERIFICATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verification_sha = sha256_file(ROUTE_DIR / VERIFICATION_RESULT)
    manifest = upsert_manifest_artifact(VERIFICATION_RESULT)
    update_completion_audit(result, verification_sha, manifest["artifact_count"])
    upsert_manifest_artifact("POST_LANE18_COMPLETION_AUDIT.json")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
