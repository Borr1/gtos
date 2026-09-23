"""Verify the prefill delivery adverse-redesign integration plate."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent

LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_ADVERSE_REDESIGN_INTEGRATION_VERIFICATION_RESULT_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
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
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    errors: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            errors.append(f"missing:{path.name}")

    ledger = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    numeric = [value for row in ledger if (value := safe_float(row.get("selected_proxy_r"))) is not None]

    checks = {
        "ledger_rows": len(ledger),
        "summary_rows": summary.get("rows"),
        "candidate_rows": len({row.get("candidate_id") for row in ledger}),
        "summary_candidate_rows": summary.get("candidate_rows"),
        "exact_r_rows": sum(1 for row in ledger if row.get("exact_r") is not None),
        "summary_exact_r_rows": summary.get("exact_r_rows"),
        "prefill_adverse_no_fill_rows": sum(1 for row in ledger if row.get("prefill_adverse_no_fill_denominator")),
        "summary_prefill_adverse_no_fill_rows": summary.get("prefill_adverse_no_fill_rows"),
        "numeric_proxy_rows": len(numeric),
        "summary_numeric_proxy_rows": summary.get("numeric_proxy_rows"),
        "proxy_r_sum": round(sum(numeric), 8),
        "summary_proxy_r_sum": round(float(summary.get("proxy_r_sum") or 0.0), 8),
        "branch_decision_counts": dict(Counter(str(row.get("branch_decision")) for row in ledger)),
        "summary_branch_decision_counts": summary.get("branch_decision_counts"),
        "action_class_counts": dict(Counter(str(row.get("action_class")) for row in ledger)),
        "summary_action_class_counts": summary.get("action_class_counts"),
        "safe_flags": summary.get("safe_flags"),
        "plate_decision": summary.get("plate_decision"),
    }
    if checks["ledger_rows"] != checks["summary_rows"]:
        errors.append("summary_rows_mismatch")
    if checks["candidate_rows"] != checks["summary_candidate_rows"]:
        errors.append("candidate_rows_mismatch")
    if checks["exact_r_rows"] != 0 or checks["summary_exact_r_rows"] != 0:
        errors.append("exact_r_rows_must_be_zero")
    if checks["prefill_adverse_no_fill_rows"] != checks["summary_prefill_adverse_no_fill_rows"]:
        errors.append("prefill_adverse_no_fill_rows_mismatch")
    if checks["numeric_proxy_rows"] != checks["summary_numeric_proxy_rows"]:
        errors.append("numeric_proxy_rows_mismatch")
    if checks["proxy_r_sum"] != checks["summary_proxy_r_sum"]:
        errors.append("proxy_r_sum_mismatch")
    if checks["branch_decision_counts"] != checks["summary_branch_decision_counts"]:
        errors.append("branch_decision_counts_mismatch")
    if checks["action_class_counts"] != checks["summary_action_class_counts"]:
        errors.append("action_class_counts_mismatch")
    if checks["safe_flags"] != SAFE_FLAGS:
        errors.append("safe_flags_mismatch")
    if checks["plate_decision"] != "PREFILL_DELIVERY_ADVERSE_NO_FILL_ROWS_INTEGRATED_WITH_ENTRY_OFFSET_050R_SCORER_DECISIONS":
        errors.append("unexpected_plate_decision")
    if any(row.get("no_live_behavior") is not True for row in ledger):
        errors.append("live_behavior_flag_missing")
    if any(row.get("no_shadow_log_append") is not True for row in ledger):
        errors.append("shadow_append_flag_missing")

    for section in ("inputs", "outputs"):
        for label, info in (manifest.get(section) or {}).items():
            path = Path(info.get("path") or "")
            if not path.exists():
                errors.append(f"manifest_{section}_{label}_missing_path")
                continue
            actual = sha256_file(path)
            if actual != info.get("sha256"):
                errors.append(f"manifest_{section}_{label}_sha_mismatch")

    result = {
        "ok": not errors,
        "errors": errors,
        "checks": checks,
        "verification": str(VERIFY_OUT),
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "verification": str(VERIFY_OUT)}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
