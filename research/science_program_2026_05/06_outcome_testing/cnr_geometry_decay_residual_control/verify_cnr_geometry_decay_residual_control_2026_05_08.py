"""Verify CNR geometry-decay / residual-control artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PROMOTION = "NO_PROMOTION_VERDICT"

REQUIRED_FILES = [
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.md",
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.json",
    "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
    "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.md",
    "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json",
    "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.md",
    "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.json",
    "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
    "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
    "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.md",
    "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
    "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
    "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
    "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
    "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json",
]

FORBIDDEN_TRUE_STRINGS = [
    '"validation_safe": true',
    '"outcome_review_opened": true',
    '"live_effect": true',
]

FORBIDDEN_INPUT_ROW_KEYS = {
    "synthetic_path_r",
    "quarantined_result_status",
    "terminal_event",
    "terminal_timestamp_utc",
    "terminal_bid",
    "terminal_ask",
    "terminal_quote_side",
    "path_coverage",
    "label_family",
    "target_hit_timestamp",
    "stop_hit_timestamp",
    "target_first_touch_utc",
    "stop_first_touch_utc",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "result_status",
}

FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
)
FORBIDDEN_LIVE_SURFACE_CONTAINS = (
    "execution",
    "permissions",
    "safety",
    "selector",
    "mt5",
    "credential",
)


def sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def resolve_source_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def git_changed_files() -> list[str]:
    cmd = [
        "git",
        "-c",
        "safe.directory=C:/tmp/gtos_otb/CNRGEOMCTRL",
        "diff",
        "--name-only",
        "HEAD",
    ]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return [f"GIT_DIFF_FAILED:{result.stderr.strip()}"]
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    issues: list[str] = []

    for name in REQUIRED_FILES:
        if not (OUT_DIR / name).exists():
            issues.append(f"missing_required_file:{name}")

    json_files = sorted(OUT_DIR.glob("CNR_*_2026-05-08.json"))
    for path in json_files:
        obj = read_json(path)
        text = path.read_text(encoding="utf-8")
        if isinstance(obj, dict):
            if obj.get("promotion_verdict") != PROMOTION:
                issues.append(f"promotion_verdict_not_preserved:{path.name}")
            if obj.get("validation_safe") is not False:
                issues.append(f"validation_safe_not_false:{path.name}")
            if obj.get("outcome_review_opened") is not False:
                issues.append(f"outcome_review_opened_not_false:{path.name}")
            if obj.get("live_effect") is not False:
                issues.append(f"live_effect_not_false:{path.name}")
        for forbidden in FORBIDDEN_TRUE_STRINGS:
            if forbidden in text:
                issues.append(f"forbidden_true_flag:{path.name}:{forbidden}")

    matrix_path = OUT_DIR / "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl"
    matrix = read_jsonl(matrix_path)
    if len(matrix) != 102:
        issues.append(f"matrix_row_count_expected_102_got_{len(matrix)}")
    forbidden_hits = []
    for row in matrix:
        hits = sorted(FORBIDDEN_INPUT_ROW_KEYS.intersection(row))
        if hits:
            forbidden_hits.append({"row": row.get("row_number"), "hits": hits})
        if row.get("promotion_verdict") != PROMOTION:
            issues.append(f"matrix_promotion_verdict_not_preserved:{row.get('row_number')}")
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False or row.get("live_effect") is not False:
            issues.append(f"matrix_flag_not_false:{row.get('row_number')}")
    if forbidden_hits:
        issues.append(f"matrix_forbidden_keys:{forbidden_hits[:5]}")

    noleak = read_json(OUT_DIR / "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json")
    if noleak.get("forbidden_input_row_key_hits"):
        issues.append("noleak_audit_reports_forbidden_hits")
    if noleak.get("countable_rows") != 54:
        issues.append(f"countable_rows_expected_54_got_{noleak.get('countable_rows')}")
    if noleak.get("duplicate_context_rows") != 48:
        issues.append(f"duplicate_context_rows_expected_48_got_{noleak.get('duplicate_context_rows')}")
    if noleak.get("sample_floor_status") != "BLOCKED_BELOW_30_UNIQUE_GROUPS_PER_TIMING_TARGET_FAMILY":
        issues.append("sample_floor_status_not_blocked_as_expected")

    source_ledger = read_json(OUT_DIR / "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json")
    if source_ledger.get("matrix_source_hash_status") != "PASS_ALL_MATRIX_SOURCE_HASHES_RECOMPUTED":
        issues.append("matrix_source_hash_status_failed")
    for row in source_ledger.get("source_files", []):
        if row.get("role") != "matrix_source_file":
            continue
        expected = row.get("expected_sha256")
        actual = sha256_path(resolve_source_path(row["path"]))
        if expected and actual != expected:
            issues.append(f"source_hash_recompute_mismatch:{row['path']}")

    next_routes = read_json(OUT_DIR / "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json")
    if len(next_routes.get("blocked_outcome_families_remain_closed", [])) != 6:
        issues.append("blocked_family_count_not_6")
    sidecar = next_routes.get("otg0_pkt061_geometry_horizon_sidecar_findings", {})
    if sidecar.get("source_field_pkt061_rows_with_original_geometry") != 8:
        issues.append("pkt061_source_geometry_count_not_8")
    if sidecar.get("otx_pkt061_rows_with_entry_sl_tp_or_level_packet") != 0:
        issues.append("pkt061_unexpected_unified_entry_sl_tp_packet")

    changed = git_changed_files()
    forbidden_changed = []
    for path in changed:
        if path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES) or any(part in path.lower() for part in FORBIDDEN_LIVE_SURFACE_CONTAINS):
            if "cnr_geometry_decay_residual_control" not in path:
                forbidden_changed.append(path)
    if forbidden_changed:
        issues.append(f"forbidden_live_surface_diff:{forbidden_changed}")

    completion = read_json(OUT_DIR / "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json")
    if completion.get("no_outcome_scoring_or_threshold_rescue_performed") is not True:
        issues.append("completion_audit_missing_no_outcome_scoring_assertion")

    status = "PASS" if not issues else "FAIL"
    report = {
        "status": status,
        "issues": issues,
        "matrix_rows": len(matrix),
        "changed_files": changed,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
