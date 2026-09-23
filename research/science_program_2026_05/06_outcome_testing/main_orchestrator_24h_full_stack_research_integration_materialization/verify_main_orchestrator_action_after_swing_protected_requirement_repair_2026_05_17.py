"""Verify swing-protected source requirement repair action ledger."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_VERIFICATION_RESULT_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_BRANCH = "PRESERVE_SWING_PROTECTED_SOURCE_REQUIREMENT_AFTER_STRUCTURAL_METADATA_REPAIR"
REPAIRED_BRANCH = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_SOURCE_REPAIRED_LTF_PROXY"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def approx(left: float | None, right: float | None, tolerance: float = 1e-8) -> bool:
    if left is None or right is None:
        return left is right
    return abs(left - right) <= tolerance


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def main() -> None:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    action_counts = Counter(str(row.get("action_class") or "") for row in rows)
    numeric_count, proxy_sum = proxy_summary(rows)
    repaired = [
        row
        for row in rows
        if row.get("swing_protected_requirement_repair_status")
        == "REPAIRED_TO_DEFAULT_OFF_PROXY_FROM_TICK_DERIVED_SWING_AND_LTF"
    ]
    remaining_target = [row for row in rows if row.get("branch_decision") == TARGET_BRANCH]
    repaired_values = [safe_float(row.get("after_proxy_r")) for row in repaired]
    repaired_values = [value for value in repaired_values if value is not None]

    if len(rows) != 3426:
        issues.append(f"expected_3426_rows_got_{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append("summary row count mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS or manifest.get("safe_flags") != SAFE_FLAGS:
        issues.append("safe flags changed")
    if summary.get("exact_r_rows") != 0:
        issues.append("exact R rows opened unexpectedly")
    if len(repaired) != 26:
        issues.append(f"expected_26_repaired_rows_got_{len(repaired)}")
    if remaining_target:
        issues.append(f"remaining swing source requirements:{len(remaining_target)}")
    if len(repaired_values) != 26 or not approx(round(sum(repaired_values), 8), -26.0):
        issues.append("repaired proxy sum mismatch")
    if numeric_count != 723 or not approx(proxy_sum, 31.40613887):
        issues.append(f"proxy total mismatch:{numeric_count}:{proxy_sum}")
    if summary.get("numeric_proxy_row_delta") != 26 or not approx(summary.get("proxy_r_sum_delta"), -26.0):
        issues.append("summary proxy delta mismatch")
    expected_delta = {"IMPLEMENT_DEFAULT_OFF": 26, "PRESERVE_REQUIREMENT": -26}
    if summary.get("action_class_delta_vs_previous") != expected_delta:
        issues.append(f"action delta mismatch:{summary.get('action_class_delta_vs_previous')}")
    expected_counts = {
        "IMPLEMENT_DEFAULT_OFF": 444,
        "KEEP": 435,
        "KILL": 967,
        "PRESERVE_REQUIREMENT": 72,
        "REDESIGN": 1508,
    }
    for key, expected in expected_counts.items():
        if action_counts.get(key) != expected:
            issues.append(f"action_count_{key}_expected_{expected}_got_{action_counts.get(key)}")
    if summary.get("rows_requiring_source_cost_fill_repair_after") != 72:
        issues.append("source/cost/fill requirement count after not 72")
    if summary.get("redesign_preserve_kill_missing_audit_after") != 0:
        issues.append("missing audit on redesign/preserve/kill row")
    if summary.get("kill_count_delta") != 0 or action_counts.get("KILL") != 967:
        issues.append("kill count changed")

    for row in repaired:
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            issues.append("repaired row not implementation default-off")
            break
        if row.get("branch_decision") != REPAIRED_BRANCH:
            issues.append("repaired branch mismatch")
            break
        if row.get("after_score_status") != "COMPUTED_FROM_LTF_PATH_ORDER":
            issues.append("repaired row missing LTF score status")
            break
        if row.get("after_outcome_status") != "ENTRY_TOUCHED_THEN_SL":
            issues.append("repaired row outcome mismatch")
            break
        if row.get("after_proxy_r") != -1.0:
            issues.append("repaired row proxy not -1R")
            break
        if row.get("swing_protected_stop_status") != "SWING_PROTECTED_STOP_CONFIRMED":
            issues.append("repaired row lacks confirmed swing-protected status")
            break
        source = row.get("structural_ltf_repair_source")
        if not isinstance(source, dict) or source.get("ltf_terminal_outcome_status") != "ENTRY_THEN_SL":
            issues.append("repaired row lacks source LTF ENTRY_THEN_SL")
            break
        audit = row.get("missed_opportunity_audit")
        if not isinstance(audit, dict) or audit.get("kill_scope") != "NOT_KILLED_SOURCE_REQUIREMENT_REPAIRED_TO_SCORER_OUTPUT":
            issues.append("repaired row missing repaired-source audit")
            break
        if row.get("safe_flags") != SAFE_FLAGS or row.get("no_live_behavior") is not True:
            issues.append("repaired row safe flags missing")
            break

    if LEDGER.exists() and manifest.get("outputs", {}).get("ledger", {}).get("sha256") != sha256_file(LEDGER):
        issues.append("ledger manifest hash mismatch")
    if SUMMARY.exists() and manifest.get("outputs", {}).get("summary", {}).get("sha256") != sha256_file(SUMMARY):
        issues.append("summary manifest hash mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "target_rows_repaired": len(repaired),
        "target_proxy_rows_added": len(repaired_values),
        "target_proxy_r_sum_added": round(sum(repaired_values), 8),
        "numeric_proxy_rows_after": numeric_count,
        "proxy_r_sum_after": proxy_sum,
        "rows_requiring_source_cost_fill_repair_after": len(
            [row for row in rows if row.get("action_class") == "PRESERVE_REQUIREMENT"]
        ),
        "action_class_counts_after": dict(sorted(action_counts.items())),
        "safe_flags": SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
