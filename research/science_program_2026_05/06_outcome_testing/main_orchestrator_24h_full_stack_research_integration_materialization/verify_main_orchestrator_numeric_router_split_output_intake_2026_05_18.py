from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
FAMILY_LEDGER_BY_NAME = {
    "scorer_registry_surface": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_SURFACE_LEDGER_{DATE}.jsonl",
    "avoid_comparator_score": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_SCORE_LEDGER_{DATE}.jsonl",
    "context_guard_input": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_LEDGER_{DATE}.jsonl",
    "source_repair_proof": ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_{DATE}.jsonl",
}
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_VERIFY_RESULT_{DATE}.json"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (*FAMILY_LEDGER_BY_NAME.values(), SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    rows_by_family = {
        family: read_jsonl(path) if path.exists() else [] for family, path in FAMILY_LEDGER_BY_NAME.items()
    }

    expected_counts = {
        "scorer_registry_surface": 5341,
        "avoid_comparator_score": 4115,
        "context_guard_input": 1513,
        "source_repair_proof": 17753,
    }
    output_rows_by_family = summary.get("output_rows_by_family") or {}
    for family, expected in expected_counts.items():
        if output_rows_by_family.get(family) != expected:
            issues.append(f"summary_family_count_unexpected:{family}")
            break
        if len(rows_by_family.get(family) or []) != expected:
            issues.append(f"ledger_family_count_unexpected:{family}:{len(rows_by_family.get(family) or [])}")
            break
    if summary.get("total_output_rows") != 28722:
        issues.append("total_output_rows_unexpected")
    for key in (
        "live_effect_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (*FAMILY_LEDGER_BY_NAME.values(), SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
        if path.suffix == ".jsonl" and path.stat().st_size >= 100_000_000:
            issues.append(f"raw_jsonl_over_github_limit:{path.name}")

    for family, rows in rows_by_family.items():
        for row in rows:
            row_id = row.get("numeric_router_output_row_id")
            if row.get("output_family") != family:
                issues.append(f"output_family_mismatch:{row_id}")
                break
            if not row.get("source_row") or not row.get("source_row_keys"):
                issues.append(f"source_row_missing:{row_id}")
                break
            if row.get("runtime_score_allowed") is not False:
                issues.append(f"runtime_score_allowed:{row_id}")
                break
            if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
                issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
                break
            if row.get("live_effect") is not False:
                issues.append(f"live_effect_enabled:{row_id}")
                break
            if row.get("replay_r_reference_counted_as_new_main_result") is not False:
                issues.append(f"replay_r_counted:{row_id}")
                break
        if issues:
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SPLIT_OUTPUT_INTAKE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "output_rows_by_family": {family: len(rows) for family, rows in rows_by_family.items()},
        "total_output_rows": sum(len(rows) for rows in rows_by_family.values()),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
