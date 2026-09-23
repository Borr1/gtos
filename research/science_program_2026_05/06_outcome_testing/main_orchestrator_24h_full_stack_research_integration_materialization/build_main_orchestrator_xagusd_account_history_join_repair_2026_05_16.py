from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
FILL_ID = "XAGUSD_2026-05-14_ny_1315"
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


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() else None,
    }


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lto016_report = REPO_ROOT / "research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json"
    j46_outcomes_path = REPO_ROOT / "shadow_logs/j46_j49_shadow_outcomes.jsonl"
    broker_audit_path = REPO_ROOT / "shadow_logs/broker_actual_r_audit.jsonl"
    account_truth_path = REPO_ROOT / "shadow_logs/account_pnl_truth_reconciliation.jsonl"
    account_status_path = REPO_ROOT / "shadow_logs/account_truth_reconciliation_status.jsonl"
    account_history_files = sorted((REPO_ROOT / "data/account_history").glob("mt5_deals_*.jsonl"))

    report = json.loads(lto016_report.read_text(encoding="utf-8"))
    action_examples = report.get("action_required_examples") or []
    target_examples = [row for row in action_examples if row.get("fill_id") == FILL_ID]

    j46_matches = [
        {"line_no": line_no, "row": row}
        for line_no, row in read_jsonl(j46_outcomes_path)
        if row.get("fill_id") == FILL_ID
    ]
    broker_matches = [
        {"line_no": line_no, "row": row}
        for line_no, row in read_jsonl(broker_audit_path)
        if row.get("fill_id") == FILL_ID or row.get("trade_id") == FILL_ID
    ]
    account_truth_matches = [
        {"line_no": line_no, "row": row}
        for line_no, row in read_jsonl(account_truth_path)
        if row.get("trade_id") in {FILL_ID, "lim_filled_XAGUSD_2026-05-14_131524"}
    ]
    account_status_matches = [
        {"line_no": line_no, "row": row}
        for line_no, row in read_jsonl(account_status_path)
        if row.get("trade_id") in {FILL_ID, "lim_XAGUSD_2026-05-14_131524"}
        or row.get("candidate_id") == "XAGUSD_2026-05-14T13:15:00+00:00"
    ]

    account_history_search: list[dict[str, Any]] = []
    matching_deals: list[dict[str, Any]] = []
    for path in account_history_files:
        rows = read_jsonl(path)
        time_values = [row.get("time_utc") for _, row in rows if row.get("time_utc")]
        xagusd_rows = [(line_no, row) for line_no, row in rows if row.get("symbol") == "XAGUSD"]
        may14_rows = [
            {"line_no": line_no, "row": row}
            for line_no, row in xagusd_rows
            if str(row.get("time_utc") or "").startswith("2026-05-14")
        ]
        matching_deals.extend(may14_rows)
        account_history_search.append(
            {
                "path": rel(path),
                "sha256": sha256(path),
                "rows": len(rows),
                "min_time_utc": min(time_values) if time_values else None,
                "max_time_utc": max(time_values) if time_values else None,
                "xagusd_rows": len(xagusd_rows),
                "xagusd_2026_05_14_rows": len(may14_rows),
            }
        )

    repair_status = (
        "REPAIRED_ACCOUNT_HISTORY_JOIN"
        if matching_deals and any(row.get("actual_r_claim_allowed") for row in broker_matches)
        else "NOT_REPAIRABLE_FROM_CURRENT_LOCAL_ACCOUNT_HISTORY_EXPORTS"
    )

    ledger_rows = [
        {
            "row_id": "MAIN-ORCH24-XAGUSD-J46-J49-ACCOUNT-HISTORY-001",
            "fill_id": FILL_ID,
            "legacy_decision": "KEEP_AND_REPAIR_XAGUSD_ACCOUNT_HISTORY_JOIN",
            "repair_status": repair_status,
            "j46_outcome_rows": len(j46_matches),
            "lto016_action_required_rows": len(target_examples),
            "broker_actual_r_rows_for_fill": len(broker_matches),
            "account_truth_reconciliation_rows": len(account_truth_matches),
            "account_truth_status_rows": len(account_status_matches),
            "account_history_exports_searched": len(account_history_search),
            "account_history_xagusd_2026_05_14_deal_rows": len(matching_deals),
            "current_disk_conclusion": "Current local exports do not include the 2026-05-14 XAGUSD account-history close deal, so the J46/J49 row must remain missing ACCOUNT_HISTORY_REALIZED evidence.",
            "missing_source": "read-only MT5 account-history deal export covering XAGUSD close deal for 2026-05-14T16:45:27Z / fill_id XAGUSD_2026-05-14_ny_1315",
            "exact_next_unblocker": r"py -3 scripts\export_mt5_account_history_readonly.py --start 2026-05-14 --end 2026-05-15 --output data\account_history\mt5_deals_2026-05-14_2026-05-15.jsonl --execute",
            "next_unblocker_boundary": "Requires explicit operational approval if treated as a live MT5 account-history read; no broker order/trade modification is involved.",
            "safe_flags": SAFE_FLAGS,
        }
    ]

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "fill_id": FILL_ID,
        "repair_status": repair_status,
        "j46_outcome_rows": len(j46_matches),
        "lto016_action_required_rows": len(target_examples),
        "broker_actual_r_rows_for_fill": len(broker_matches),
        "account_truth_reconciliation_rows": len(account_truth_matches),
        "account_truth_status_rows": len(account_status_matches),
        "account_history_exports_searched": len(account_history_search),
        "account_history_search": account_history_search,
        "account_history_xagusd_2026_05_14_deal_rows": len(matching_deals),
        "matching_deals": matching_deals,
        "can_claim_account_history_realized": False,
        "can_mark_join_repaired_from_current_disk": repair_status == "REPAIRED_ACCOUNT_HISTORY_JOIN",
        "safe_flags": SAFE_FLAGS,
    }

    summary_md = "\n".join(
        [
            "# XAGUSD Account-History Join Repair Attempt",
            "",
            f"Generated: `{generated_utc}`",
            f"Fill: `{FILL_ID}`",
            f"Repair status: `{repair_status}`",
            "",
            "The J46/J49 shadow outcome exists for the XAGUSD 2026-05-14 NY fill, and LTO-016 correctly marks it action-required because it lacks `ACCOUNT_HISTORY_REALIZED` broker evidence.",
            "",
            "Current local `data/account_history/mt5_deals_*.jsonl` exports were searched and contain no XAGUSD 2026-05-14 deal rows. The current disk state therefore cannot repair the account-history join without a newer read-only MT5 account-history export.",
            "",
            "No actual-R, validation-safe, promotion, live-effect, or broker-operation claim is opened by this artifact.",
            "",
        ]
    )

    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_SUMMARY_{DATE}.json"
    summary_md_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_SUMMARY_{DATE}.md"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

    write_jsonl(ledger_path, ledger_rows)
    write_json(summary_path, summary)
    summary_md_path.write_text(summary_md, encoding="utf-8")

    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 3,
        "artifacts": [
            artifact_record("repair_ledger", ledger_path),
            artifact_record("summary_json", summary_path),
            artifact_record("summary_md", summary_md_path),
        ],
        "input_artifacts": [
            artifact_record("lto016_report", lto016_report),
            artifact_record("j46_outcomes", j46_outcomes_path),
            artifact_record("broker_actual_r_audit", broker_audit_path),
            artifact_record("account_pnl_truth_reconciliation", account_truth_path),
            artifact_record("account_truth_status", account_status_path),
            *[artifact_record(f"account_history_{path.stem}", path) for path in account_history_files],
        ],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)

    print(json.dumps({"ok": True, "repair_status": repair_status, "manifest": rel(manifest_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
