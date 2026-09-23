"""Verify G0 NOFILL forward projection synthesis/control artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import build_g0_nofill_forward_projection_synthesis_control_route_2026_05_09 as builder


BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parents[3]
RESULT_JSON = BASE / "G0_NOFILL_FORWARD_VERIFICATION_RESULT_2026-05-09.json"


def _git_diff_names() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    names = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    result_untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    names.extend(line.strip().replace("\\", "/") for line in result_untracked.stdout.splitlines() if line.strip())
    return sorted(set(names))


def verify() -> dict:
    issues: list[str] = []
    warnings: list[str] = []

    required = builder.REQUIRED_MD + builder.REQUIRED_JSON + [
        "build_g0_nofill_forward_projection_synthesis_control_route_2026_05_09.py",
        "verify_g0_nofill_forward_projection_synthesis_control_route_2026_05_09.py",
        "test_g0_nofill_forward_projection_synthesis_control_route_2026_05_09.py",
    ]
    for name in required:
        if not (BASE / name).exists():
            issues.append(f"missing_required_artifact:{name}")

    json_payloads = {}
    for path in sorted(BASE.glob("*.json")):
        try:
            json_payloads[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - diagnostic branch
            issues.append(f"json_parse_failed:{path.name}:{exc}")

    for name in builder.REQUIRED_JSON:
        payload = json_payloads.get(name)
        if not isinstance(payload, dict):
            continue
        if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
            issues.append(f"bad_promotion_verdict:{name}")
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if payload.get(flag) is not False:
                issues.append(f"bad_flag:{name}:{flag}={payload.get(flag)!r}")
        for flag in (
            "opens_result_scoring",
            "opens_live_wiring",
            "opens_paid_api_or_databento_route",
            "opens_registry_edit",
            "changes_live_trading_behavior",
        ):
            if payload.get(flag) is not False:
                issues.append(f"bad_boundary_flag:{name}:{flag}={payload.get(flag)!r}")

    schema = json_payloads.get("G0_NOFILL_FORWARD_CAPTURE_SCHEMA_REQUIREMENTS_2026-05-09.json", {})
    ranking = schema.get("route_ranking", [])
    if not ranking or ranking[0].get("route") != "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE":
        issues.append("rank_1_route_not_expected_source_capture_contract_prototype")
    fields = {row.get("field_name") for row in schema.get("future_capture_field_requirements", [])}
    for field_name in (
        "capture_write_completed_at_utc",
        "capture_clock_skew_ms",
        "pending_order_mode_source_safe",
        "entry_touch_spread_value_source_safe",
        "terminal_area_touch_status",
        "mt5_order_ticket_redaction_status",
        "nofill_duplicate_key_sha256",
        "forbidden_field_scan_status",
    ):
        if field_name not in fields:
            issues.append(f"missing_schema_requirement:{field_name}")

    matrix = json_payloads.get("G0_NOFILL_FORWARD_PROJECTION_FIELD_REQUIREMENT_MATRIX_2026-05-09.json", {})
    if "mt5_order_ticket" not in matrix.get("forbidden_fields", []):
        issues.append("forbidden_ticket_field_not_listed")
    if matrix.get("field_family_counts", {}).get("total_future_capture_requirement_rows", 0) < 40:
        issues.append("field_requirement_matrix_too_small")

    md_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in BASE.glob("*.md"))
    for forbidden_literal in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
        if forbidden_literal in md_text:
            issues.append(f"forbidden_true_flag_literal:{forbidden_literal}")

    dirty_names = _git_diff_names()
    allowed_prefixes = {
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    }
    route_prefix = "research/science_program_2026_05/06_outcome_testing/g0_nofill_forward_projection_synthesis_control_route/"
    forbidden_dirty = [
        name
        for name in dirty_names
        if not name.startswith(route_prefix) and name not in allowed_prefixes
    ]
    if forbidden_dirty:
        issues.append(f"forbidden_dirty_paths:{forbidden_dirty}")

    generated_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in BASE.glob("*")
        if path.is_file() and path.suffix in {".md", ".json"}
    )
    for token in ("broker_actual_r=", "actual_r=", "synthetic_path_r=", "win_rate=", "expectancy="):
        if token in generated_text:
            issues.append(f"forbidden_value_assignment_token:{token}")

    result = {
        "artifact": "G0_NOFILL_FORWARD_VERIFICATION_RESULT",
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        **builder.base_flags(),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "warnings": warnings,
        "json_files_parsed": sorted(json_payloads),
        "required_artifacts_checked": required,
        "dirty_paths_reviewed": dirty_names,
        "can_mark_goal_complete_after_commit": not issues,
    }
    RESULT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
