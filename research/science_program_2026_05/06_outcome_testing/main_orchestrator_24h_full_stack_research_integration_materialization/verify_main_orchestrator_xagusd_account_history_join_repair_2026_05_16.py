from __future__ import annotations

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
    rows = []
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


def main() -> None:
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_SUMMARY_{DATE}.json"
    summary_md_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_SUMMARY_{DATE}.md"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_VERIFICATION_RESULT_{DATE}.json"

    checks = []
    for path in [ledger_path, summary_path, summary_md_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    ledger = read_jsonl(ledger_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)
    summary_md = summary_md_path.read_text(encoding="utf-8", errors="replace")

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_preserved", summary.get("safe_flags") == SAFE_FLAGS and manifest.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("single_repair_row", len(ledger) == 1, len(ledger)))
    checks.append(check("repair_not_claimed_from_missing_export", summary.get("repair_status") == "NOT_REPAIRABLE_FROM_CURRENT_LOCAL_ACCOUNT_HISTORY_EXPORTS"))
    checks.append(check("j46_outcome_found", summary.get("j46_outcome_rows") == 1, summary.get("j46_outcome_rows")))
    checks.append(check("lto016_action_required_found", summary.get("lto016_action_required_rows") == 1, summary.get("lto016_action_required_rows")))
    checks.append(check("local_exports_searched", summary.get("account_history_exports_searched", 0) >= 1, summary.get("account_history_exports_searched")))
    checks.append(check("no_may14_xagusd_deals", summary.get("account_history_xagusd_2026_05_14_deal_rows") == 0, summary.get("account_history_xagusd_2026_05_14_deal_rows")))
    checks.append(check("cannot_claim_account_history_realized", summary.get("can_claim_account_history_realized") is False))
    checks.append(check("summary_md_has_boundary", "No actual-R" in summary_md and "newer read-only MT5 account-history export" in summary_md))

    manifest_errors = []
    for section in ("artifacts", "input_artifacts"):
        for artifact in manifest.get(section, []):
            path = REPO_ROOT / artifact["path"]
            if not path.exists():
                manifest_errors.append({"path": artifact["path"], "error": "missing"})
                continue
            if path.stat().st_size != artifact.get("size_bytes"):
                manifest_errors.append({"path": artifact["path"], "error": "size_mismatch"})
            actual = sha256(path)
            if actual != artifact.get("sha256"):
                manifest_errors.append({"path": artifact["path"], "error": "sha256_mismatch", "actual": actual})
    checks.append(check("manifest_hashes_match", not manifest_errors, manifest_errors))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "repair_ledger_rows": len(ledger),
            "account_history_exports_searched": summary.get("account_history_exports_searched"),
            "account_history_xagusd_2026_05_14_deal_rows": summary.get("account_history_xagusd_2026_05_14_deal_rows"),
        },
        "can_mark_xagusd_account_history_join_repair_attempt_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
