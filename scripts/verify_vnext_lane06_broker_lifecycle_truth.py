from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_vnext_lane06_broker_lifecycle_truth as lane06


RESULT_PATH = lane06.VERIFICATION_RESULT_PATH


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
    except (OSError, json.JSONDecodeError):
        return []
    return rows


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_route(route_dir: Path | None = None) -> dict[str, Any]:
    route_dir = route_dir or lane06.ROUTE_DIR
    paths = {
        "snapshot": route_dir / lane06.MT5_SNAPSHOT_PATH.name,
        "lifecycle": route_dir / lane06.BROKER_LIFECYCLE_LEDGER_PATH.name,
        "cost": route_dir / lane06.COST_CALIBRATION_LEDGER_PATH.name,
        "projected": route_dir / lane06.PROJECTED_RECONCILIATION_LEDGER_PATH.name,
        "telegram": route_dir / lane06.TELEGRAM_PARITY_LEDGER_PATH.name,
        "manual": route_dir / lane06.MANUAL_INTERVENTION_LEDGER_PATH.name,
        "source": route_dir / lane06.SOURCE_COMPLETENESS_LEDGER_PATH.name,
        "runtime_logs": route_dir / lane06.RUNTIME_LOG_FORENSICS_LEDGER_PATH.name,
        "summary": route_dir / lane06.SUMMARY_PATH.name,
        "manifest": route_dir / lane06.MANIFEST_PATH.name,
        "completion_audit": route_dir / lane06.COMPLETION_AUDIT_PATH.name,
    }
    issues: list[str] = []

    for name, path in paths.items():
        if not path.exists():
            issues.append(f"missing_output:{name}:{path}")
        elif path.stat().st_size <= 0:
            issues.append(f"empty_output:{name}:{path}")

    lifecycle = _read_jsonl(paths["lifecycle"])
    cost = _read_jsonl(paths["cost"])
    projected = _read_jsonl(paths["projected"])
    telegram = _read_jsonl(paths["telegram"])
    manual = _read_jsonl(paths["manual"])
    source = _read_jsonl(paths["source"])
    summary = _read_json(paths["summary"], {})

    lifecycle_by_ticket = {row.get("ticket"): row for row in lifecycle}
    missing_friday = sorted(lane06.FRIDAY_TICKETS - set(lifecycle_by_ticket))
    if missing_friday:
        issues.append(f"missing_friday_tickets:{missing_friday}")

    for ticket in [241779188, 241972476]:
        row = lifecycle_by_ticket.get(ticket)
        if not row or not row.get("open_position_present"):
            issues.append(f"expected_open_broker_position:{ticket}")

    row_241948220 = lifecycle_by_ticket.get(241948220, {})
    if 225795604 not in (row_241948220.get("manual_or_client_deal_tickets") or []):
        issues.append("missing_manual_client_residual_close_deal:241948220:225795604")
    if row_241948220.get("broker_lifecycle_status") != "PARTIAL_AND_RESIDUAL_CLOSED_BROKER_HISTORY":
        issues.append("wrong_lifecycle_status_for_241948220")

    cost_by_ticket = {row.get("ticket"): row for row in cost}
    for ticket in lane06.FRIDAY_TICKETS:
        row = cost_by_ticket.get(ticket)
        if not row:
            issues.append(f"missing_cost_row:{ticket}")
            continue
        if row.get("initial_cash_risk_status") != "CAPTURED_FROM_BROKER_ENTRY_AND_LOCAL_STOP_GEOMETRY":
            issues.append(f"missing_initial_cash_risk:{ticket}")
        if ticket in {241779188, 241972476}:
            if row.get("broker_final_net_r_status") != "OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE":
                issues.append(f"open_ticket_final_net_r_not_pending:{ticket}")
        elif row.get("broker_final_net_r_status") != "CAPTURED":
            issues.append(f"closed_ticket_net_r_not_captured:{ticket}")

    false_close_tickets = {
        row.get("ticket")
        for row in projected
        if row.get("reconciliation_status")
        == "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
    }
    if {241779188, 241972476} - false_close_tickets:
        issues.append(f"missing_false_close_projection_tickets:{sorted({241779188, 241972476} - false_close_tickets)}")

    if not any(
        row.get("source_type") == "telegram_queue_message"
        and row.get("ticket") == 241779188
        and row.get("parity_status") == "FALSE_CLOSE_TELEGRAM_SENT"
        for row in telegram
    ):
        issues.append("missing_nas100_false_close_telegram_queue_row")

    if not any(
        row.get("ticket") == 241948220
        and row.get("deal_ticket") == 225795604
        and row.get("manual_intervention_status") == "BROKER_HISTORY_CLIENT_OR_MANUAL_CLOSE_DEAL"
        for row in manual
    ):
        issues.append("missing_manual_intervention_ledger_row_for_241948220_225795604")

    if not any(
        row.get("requirement") == "live_behavior_code_patch"
        and "PATCHED_EXECUTION" in str(row.get("status"))
        for row in source
    ):
        issues.append("missing_code_patch_source_completeness_row")

    if summary.get("source_completeness_status") != "COMPLETE_WITH_OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE":
        issues.append("summary_source_completeness_status_not_complete")

    result = {
        "schema_version": "lane06_verification_result_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ok": not issues,
        "issues": issues,
        "counts": {
            "lifecycle_rows": len(lifecycle),
            "cost_rows": len(cost),
            "projected_rows": len(projected),
            "telegram_rows": len(telegram),
            "manual_rows": len(manual),
            "source_rows": len(source),
        },
    }
    _write_json(route_dir / RESULT_PATH.name, result)
    if route_dir == lane06.ROUTE_DIR:
        lane06._write_manifest(datetime.now(timezone.utc))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route()
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
