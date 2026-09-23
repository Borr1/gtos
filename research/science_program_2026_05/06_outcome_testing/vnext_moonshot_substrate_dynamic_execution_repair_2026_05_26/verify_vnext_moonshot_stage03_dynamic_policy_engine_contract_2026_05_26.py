from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

POLICY_MANIFEST = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_MANIFEST_{DATE_ID}.jsonl"
CONTRACT = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_ENGINE_CONTRACT_{DATE_ID}.json"
MATRIX = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_TEST_MATRIX_{DATE_ID}.jsonl"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_DYNAMIC_POLICY_ENGINE_REPORT_{DATE_ID}.md"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE03_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_POLICIES = {
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    failures = []
    policy_rows = load_jsonl(POLICY_MANIFEST) if POLICY_MANIFEST.exists() else []
    matrix_rows = load_jsonl(MATRIX) if MATRIX.exists() else []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8")) if CONTRACT.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    policy_names = {row.get("policy_name") for row in policy_rows}
    missing = sorted(REQUIRED_POLICIES - policy_names)
    matrix_by_policy = Counter(row.get("policy_name") for row in matrix_rows)

    if missing:
        failures.append(f"missing required policies: {missing}")
    if contract.get("banned_imports"):
        failures.append(f"engine has banned imports: {contract.get('banned_imports')}")
    if contract.get("policy_count") != len(policy_rows):
        failures.append("contract policy_count mismatch")
    if contract.get("matrix_rows") != len(matrix_rows):
        failures.append("contract matrix_rows mismatch")
    if contract.get("ambiguous_case_rows", 0) <= 0:
        failures.append("ambiguous same-bar policy case missing")
    if state.get("first_incomplete_invariant") != "STAGE_04_FULL_POLICY_DYNAMIC_REPLAY":
        failures.append("state did not advance first incomplete invariant to Stage04")
    if state.get("dynamic_policy_manifest_path") is None:
        failures.append("state missing dynamic policy manifest path")
    if not REPORT.exists() or REPORT.stat().st_size < 500:
        failures.append("Stage03 report missing or too small")
    for policy in REQUIRED_POLICIES:
        if matrix_by_policy[policy] < 4:
            failures.append(f"policy {policy} has insufficient matrix rows: {matrix_by_policy[policy]}")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "policy_count": len(policy_rows),
        "policy_names": sorted(policy_names),
        "matrix_rows": len(matrix_rows),
        "matrix_by_policy": dict(sorted(matrix_by_policy.items())),
        "banned_imports": contract.get("banned_imports"),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
