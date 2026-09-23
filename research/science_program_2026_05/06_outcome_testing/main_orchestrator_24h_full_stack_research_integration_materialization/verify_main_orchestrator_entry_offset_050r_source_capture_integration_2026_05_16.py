"""Verify entry-offset 0.50R source-capture/scorer integration artifacts."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
BUILDER = ROUTE_DIR / "build_main_orchestrator_entry_offset_050r_source_capture_integration_2026_05_16.py"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SOURCE_CAPTURE_INTEGRATION_VERIFICATION_RESULT_{DATE}.json"
EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
EXPECTED_SURFACES = [
    "forward_capture_strategy_registry",
    "live_mechanical_shadow_scorer_guard",
    "current_scorer_output_denominator",
]
EXPECTED_STRATEGY_STATUS_COUNTS = {
    "KILLED_ENTRY_OFFSET_050R_NO_FILL": 82,
    "NOT_APPLICABLE_NOT_ENTRY_REDESIGN_DENOMINATOR": 177,
    "SCORED_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_PROXY": 10,
    "SCORED_ENTRY_OFFSET_050R_TICK_REPLAY_PROXY_DEFAULT_OFF": 3,
    "SOURCE_REPAIR_REQUIRED_TICK_REPLAY_INCOMPLETE": 2,
}


def sha256_file(path: Path) -> str:
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


def approx_equal(left: float, right: float, tol: float = 1e-9) -> bool:
    return abs(float(left) - float(right)) <= tol


def assert_ast_parse(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing python artifact: {path.name}")
        return
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        errors.append(f"syntax parse failed for {path.name}: {exc}")


def main() -> None:
    errors: list[str] = []
    for path in [BUILDER, LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    assert_ast_parse(BUILDER, errors)
    assert_ast_parse(Path(__file__), errors)

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != 3 or summary.get("rows") != 3:
        errors.append(f"expected 3 integration rows, got ledger={len(rows)} summary={summary.get('rows')}")
    surfaces = [row.get("surface") for row in rows]
    if surfaces != EXPECTED_SURFACES:
        errors.append(f"surface order/count mismatch: {surfaces}")
    if summary.get("implemented_surfaces") != EXPECTED_SURFACES:
        errors.append(f"summary implemented surfaces mismatch: {summary.get('implemented_surfaces')}")
    if summary.get("current_denominator_rows") != 274:
        errors.append("current denominator rows mismatch")
    if summary.get("current_exact_r_rows") != 0:
        errors.append("exact R rows must remain 0")
    if summary.get("current_numeric_proxy_rows") != 95:
        errors.append("numeric proxy rows mismatch")
    if not approx_equal(summary.get("current_proxy_r_sum"), 8.66977687):
        errors.append(f"proxy R sum mismatch: {summary.get('current_proxy_r_sum')}")
    if summary.get("strategy_status_counts") != EXPECTED_STRATEGY_STATUS_COUNTS:
        errors.append(f"strategy status counts mismatch: {summary.get('strategy_status_counts')}")
    if any(row.get("safe_flags") != EXPECTED_SAFE_FLAGS for row in rows):
        errors.append("row safe flags mismatch")
    if summary.get("safe_flags") != EXPECTED_SAFE_FLAGS or manifest.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        errors.append("summary or manifest safe flags mismatch")
    for code_key, evidence in (summary.get("code_evidence") or {}).items():
        tokens = evidence.get("required_token_presence") or {}
        if not tokens or not all(tokens.values()):
            errors.append(f"missing required token in {code_key}: {tokens}")
        path = Path(evidence.get("path") or "")
        if not path.exists():
            errors.append(f"code evidence path missing: {path}")
            continue
        if evidence.get("sha256") != sha256_file(path):
            errors.append(f"code evidence hash mismatch: {path}")
    for group_name in ("inputs", "outputs"):
        for name, artifact in (manifest.get(group_name) or {}).items():
            path = Path(str(artifact.get("path") or ""))
            if not path.exists():
                errors.append(f"manifest {group_name} path missing: {name}")
                continue
            if artifact.get("bytes") != path.stat().st_size:
                errors.append(f"manifest byte mismatch: {name}")
            if artifact.get("sha256") != sha256_file(path):
                errors.append(f"manifest hash mismatch: {name}")

    result = {
        "ok": not errors,
        "errors": errors,
        "rows": len(rows),
        "implemented_surfaces": surfaces,
        "current_denominator_rows": summary.get("current_denominator_rows"),
        "current_exact_r_rows": summary.get("current_exact_r_rows"),
        "current_numeric_proxy_rows": summary.get("current_numeric_proxy_rows"),
        "current_proxy_r_sum": summary.get("current_proxy_r_sum"),
        "plate_decision": summary.get("plate_decision"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
