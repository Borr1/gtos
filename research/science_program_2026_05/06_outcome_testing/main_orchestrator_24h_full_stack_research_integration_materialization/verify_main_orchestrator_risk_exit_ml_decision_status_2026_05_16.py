from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def ast_parse_ok(path: Path) -> tuple[bool, str | None]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return False, str(exc)
    return True, None


def main() -> None:
    build_script = ROUTE_DIR / "build_main_orchestrator_risk_exit_ml_decision_status_2026_05_16.py"
    verify_script = Path(__file__).resolve()
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_VERIFICATION_RESULT_{DATE}.json"

    checks: list[dict[str, Any]] = []
    for path in [build_script, verify_script, ledger_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    ledger = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    families = {row.get("family") for row in ledger}
    required_families = {
        "S79_SIDE_AWARE",
        "K54_K55",
        "TRAILING_STOP_EXIT_VARIANT",
        "PARTIAL_CLOSE_EXPANSION",
        "PORTFOLIO_VOL_MANAGED_SIZING",
        "EXIT_MANAGEMENT_STATUS",
    }
    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID and manifest.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_preserved", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("required_family_rows_present", families == required_families, sorted(families)))
    checks.append(check("decision_rows_match_summary", summary.get("decision_rows") == len(ledger) == 6, summary.get("decision_rows")))
    checks.append(check("s79_context_rows_current", summary.get("s79_rows_computed", 0) >= 279, summary.get("s79_rows_computed")))
    checks.append(check("k55_inference_disabled", summary.get("k55_prediction_computed_rows") == 0 and summary.get("k55_model_artifact_status") == "MODEL_ARTIFACT_MISSING_INFERENCE_DISABLED"))
    checks.append(check("exit_status_has_current_rows", summary.get("exit_candidate_rows_considered", 0) >= 274, summary.get("exit_candidate_rows_considered")))
    checks.append(check("dedicated_trailing_logger_absent", summary.get("dedicated_trailing_logger_present") is False))
    checks.append(check("portfolio_vol_managed_absent", summary.get("portfolio_vol_managed_present") is False))

    decision_map = {row.get("family"): row for row in ledger}
    checks.append(
        check(
            "partial_expansion_killed_but_variant_c_kept",
            decision_map["PARTIAL_CLOSE_EXPANSION"].get("materialized_decision")
            == "KILL_NEW_PARTIAL_VARIANT_EXPANSION_KEEP_EXISTING_VARIANT_C_SHADOW_ONLY",
        )
    )
    checks.append(
        check(
            "trailing_queued_shadow_only",
            decision_map["TRAILING_STOP_EXIT_VARIANT"].get("materialized_decision")
            == "QUEUE_DEFAULT_OFF_SHADOW_SPEC_ONLY_DO_NOT_IMPLEMENT_LIVE_OR_DEFAULT_ON",
        )
    )
    checks.append(
        check(
            "k54_killed_k55_preserved",
            decision_map["K54_K55"].get("materialized_decision")
            == "KILL_K54_SAME_COHORT_ITERATION_PRESERVE_K55_FEATURE_BUNDLE",
        )
    )

    manifest_errors = []
    for section in ("artifacts", "input_artifacts"):
        for artifact in manifest.get(section, []):
            path = REPO_ROOT / artifact["path"]
            if not artifact.get("exists"):
                if artifact.get("sha256") is not None:
                    manifest_errors.append({"path": artifact["path"], "error": "missing_with_hash"})
                continue
            if not path.exists():
                manifest_errors.append({"path": artifact["path"], "error": "missing"})
                continue
            if path.stat().st_size != artifact.get("size_bytes"):
                manifest_errors.append({"path": artifact["path"], "error": "size_mismatch"})
            actual = sha256(path)
            if actual != artifact.get("sha256"):
                manifest_errors.append({"path": artifact["path"], "error": "sha256_mismatch", "actual": actual})
    checks.append(check("manifest_hashes_match", not manifest_errors, manifest_errors))

    for path in [build_script, verify_script]:
        ok, error = ast_parse_ok(path)
        checks.append(check(f"{path.name}_ast_parse_ok", ok, error))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "decision_rows": len(ledger),
            "s79_rows_computed": summary.get("s79_rows_computed"),
            "k55_rows_computed": summary.get("k55_rows_computed"),
            "exit_candidate_rows_considered": summary.get("exit_candidate_rows_considered"),
            "time_in_trade_event_rows": summary.get("time_in_trade_event_rows"),
            "partial_close_event_rows": summary.get("partial_close_event_rows"),
            "be_event_rows": summary.get("be_event_rows"),
        },
        "can_mark_risk_exit_ml_decision_status_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
