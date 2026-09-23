"""Verifier for the NOFILL historical local tick/shadow source packet route."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (  # noqa: E402
    NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES,
    NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS,
    validate_nofill_forward_source_capture_row,
)


PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
ROUTE_ID = "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET"
SCHEMA_VERSION = "nofill_historical_source_expansion_builder_local_tick_shadow_packet_v1"
SAFE_FLAG_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
FORBIDDEN_RAW_PACKET_KEYS = set(NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES) | {
    "actual_r",
    "broker_actual_r",
    "realized_r",
    "outcome_r",
    "win_rate",
    "expectancy",
    "slippage_price",
}
FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "canaries/",
)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def scan_safe_flags(obj: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAG_KEYS and value is not False:
                issues.append(f"{child} must be false")
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                issues.append(f"{child} opens a forbidden surface")
            if key == "promotion_verdict" and value != "NO_PROMOTION_VERDICT":
                issues.append(f"{child} must be NO_PROMOTION_VERDICT")
            issues.extend(scan_safe_flags(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            issues.extend(scan_safe_flags(value, f"{path}[{idx}]"))
    return issues


def parse_generated_artifacts() -> list[str]:
    issues: list[str] = []
    for path in ROUTE_DIR.glob("*.json"):
        try:
            obj = load_json(path)
        except Exception as exc:  # pragma: no cover
            issues.append(f"{path.name} JSON parse failed: {exc}")
            continue
        issues.extend(scan_safe_flags(obj, path.name))
    for path in ROUTE_DIR.glob("*.jsonl"):
        try:
            for idx, row in enumerate(read_jsonl(path), start=1):
                issues.extend(scan_safe_flags(row, f"{path.name}:{idx}"))
        except Exception as exc:  # pragma: no cover
            issues.append(f"{path.name} JSONL parse failed: {exc}")
    for path in ROUTE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "NO_PROMOTION_VERDICT" not in text:
            issues.append(f"{path.name} missing NO_PROMOTION_VERDICT")
        if "validation_safe=true" in text or "outcome_review_opened=true" in text or "live_effect=true" in text:
            issues.append(f"{path.name} contains true safe flag text")
    return issues


def resolve_manifest_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def verify_hash_manifest() -> list[str]:
    issues: list[str] = []
    manifest = load_json(ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_MANIFEST_2026-05-10.json")
    for record in manifest.get("records", []):
        if not record.get("exists"):
            issues.append(f"hash manifest record missing: {record.get('role')} {record.get('path')}")
            continue
        path = resolve_manifest_path(str(record.get("path")))
        actual = sha256_file(path)
        if actual != record.get("sha256"):
            issues.append(f"hash mismatch: {record.get('role')} {record.get('path')}")
    return issues


def verify_packet() -> tuple[list[str], list[dict[str, Any]]]:
    issues: list[str] = []
    packet_path = ROUTE_DIR / f"{PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl"
    rows = read_jsonl(packet_path)
    seen_ids = set()
    for row in rows:
        row_id = row.get("packet_row_id")
        if row_id in seen_ids:
            issues.append(f"duplicate packet_row_id: {row_id}")
        seen_ids.add(row_id)
        missing = [field for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS if field not in row]
        if missing:
            issues.append(f"{row_id} missing 55-field contract fields: {missing}")
        future_missing = [field for field in NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS if field not in row]
        if future_missing:
            issues.append(f"{row_id} missing future-20 fields: {future_missing}")
        forbidden_keys = sorted(set(row) & FORBIDDEN_RAW_PACKET_KEYS)
        if forbidden_keys:
            issues.append(f"{row_id} has forbidden raw keys: {forbidden_keys}")
        validation = validate_nofill_forward_source_capture_row(row)
        if not validation["ok"]:
            issues.append(f"{row_id} failed forward source-capture validation: {validation['issues']}")
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False:
            issues.append(f"{row_id} safe flags are not closed")
        if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            issues.append(f"{row_id} promotion verdict not closed")
    return issues, rows


def verify_ledgers(packet_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    manifest = load_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_2026-05-10.json")
    packet_manifest = load_json(ROUTE_DIR / f"{PREFIX}_CANDIDATE_PACKET_MANIFEST_2026-05-10.json")
    admission = load_json(ROUTE_DIR / f"{PREFIX}_CANDIDATE_ADMISSION_LEDGER_2026-05-10.json")
    field_binding = load_json(ROUTE_DIR / f"{PREFIX}_55_FIELD_BINDING_CHECKLIST_2026-05-10.json")
    future20 = load_json(ROUTE_DIR / f"{PREFIX}_FUTURE20_EXTRACTION_FAIL_CLOSED_LEDGER_2026-05-10.json")
    duplicate = load_json(ROUTE_DIR / f"{PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.json")
    noleak = load_json(ROUTE_DIR / f"{PREFIX}_NOLEAK_AUDIT_2026-05-10.json")
    purge = load_json(ROUTE_DIR / f"{PREFIX}_CONTAMINATION_PURGE_LEDGER_2026-05-10.json")
    prompt_pack = ROUTE_DIR / f"{PREFIX}_NEXT_G12_SOURCE_CONTROL_AUDIT_PROMPT_PACK_2026-05-10.md"

    if manifest.get("admitted_packet_row_count") != len(packet_rows):
        issues.append("output manifest packet row count mismatch")
    if packet_manifest.get("packet_row_count") != len(packet_rows):
        issues.append("packet manifest row count mismatch")
    admitted_count = admission.get("status_counts", {}).get("ADMITTED_SOURCE_PACKET_ROW", 0)
    if admitted_count != len(packet_rows):
        issues.append("admission ledger admitted count mismatch")
    expected_binding_rows = len(packet_rows) * len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    if field_binding.get("binding_row_count") != expected_binding_rows:
        issues.append("55-field binding row count mismatch")
    expected_future20 = len(packet_rows) * len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS)
    if len(future20.get("rows", [])) != expected_future20:
        issues.append("future-20 row count mismatch")
    if duplicate.get("row_level_count") != len(packet_rows):
        issues.append("duplicate denominator row-level count mismatch")
    if duplicate.get("primary_duplicate_denominator", {}).get("unique_count") != len(
        {row["nofill_duplicate_key_sha256"] for row in packet_rows}
    ):
        issues.append("primary duplicate denominator unique count mismatch")
    if noleak.get("packet_forbidden_raw_key_hit_count") != 0:
        issues.append("no-leak audit reports forbidden raw key hits")
    if purge.get("admitted_overlap_counts", {}).get("contaminated_or_embargo_date") != 0:
        issues.append("purge ledger reports contaminated/embargo overlap")
    if not prompt_pack.exists():
        issues.append("next G12 prompt pack missing")
    for key, path_text in manifest.get("outputs", {}).items():
        path = resolve_manifest_path(path_text)
        if not path.exists():
            issues.append(f"manifest output missing: {key} -> {path_text}")
    for key, path_text in manifest.get("static_files", {}).items():
        path = resolve_manifest_path(path_text)
        if not path.exists():
            issues.append(f"manifest static file missing: {key} -> {path_text}")
    return issues


def verify_python_syntax() -> list[str]:
    issues: list[str] = []
    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{path.name} syntax parse failed: {exc}")
    return issues


def verify_diff_scope() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    paths = sorted(
        {
            line.strip().replace("\\", "/")
            for line in (result.stdout + "\n" + untracked.stdout).splitlines()
            if line.strip()
        }
    )
    forbidden = [
        path
        for path in paths
        if path.startswith(FORBIDDEN_DIFF_PREFIXES)
        and not path.startswith("src/research_infra/forward_capture.py")
    ]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
        "ok": not forbidden,
    }


def mark_completion_audit(ok: bool, evidence: dict[str, Any]) -> None:
    json_path = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.json"
    audit = load_json(json_path)
    audit["can_mark_goal_complete"] = bool(ok)
    audit["closeout_verification_evidence"] = evidence
    audit["completion_audit_updated_by_verifier"] = True
    audit["completion_audit_update_note"] = (
        "Verifier/test evidence passed; scoped commit and final LIVE_STATE refresh remain external closeout steps."
    )
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_2026-05-10.md"
    md_path.write_text(
        "\n".join(
            [
                "# NOFILL Historical Source Expansion Completion Audit",
                "",
                f"Route: `{ROUTE_ID}`",
                f"Promotion posture: `NO_PROMOTION_VERDICT`",
                "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
                "",
                "## Summary",
                "",
                "```json",
                json.dumps(audit, indent=2, sort_keys=True),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def verify() -> dict[str, Any]:
    issues = parse_generated_artifacts()
    issues.extend(verify_hash_manifest())
    packet_issues, packet_rows = verify_packet()
    issues.extend(packet_issues)
    issues.extend(verify_ledgers(packet_rows))
    issues.extend(verify_python_syntax())
    diff_scope = verify_diff_scope()
    if not diff_scope["ok"]:
        issues.append(f"forbidden live-surface diff paths: {diff_scope['forbidden_live_surface_paths']}")

    result = {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "schema_version": f"{SCHEMA_VERSION}_verifier_v1",
        "failures": issues,
        "packet_row_count": len(packet_rows),
        "field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "future20_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "diff_scope": diff_scope,
        "terminal_decision": load_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-10.json").get(
            "terminal_decision"
        ),
        "can_mark_goal_complete": not issues,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    mark_completion_audit(result["ok"], {"verifier_result": result})
    (ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_2026-05-10.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
