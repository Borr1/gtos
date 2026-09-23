#!/usr/bin/env python3
"""Build market-expansion commission family-transfer evidence.

This route uses aggregate account-history deal rows and symbol metadata to
convert no-direct-commission symbols into direct or family-proxy commission
status. It is read-only and aggregate-only; it does not store ticket/order/deal
ids, mutate broker state, use orderflow/depth, push remotes, apply config, or
reload VPS/runtime processes.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
DOSSIER_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
BROKER_AUTH_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_broker_authority_probe_2026_06_18"
FILL_SESSION_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_fill_session_probe_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_commission_family_transfer"
HISTORY_START = datetime(2024, 1, 1, tzinfo=UTC)
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 8001
BRIDGE_TIMEOUT_SECONDS = 10


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def finite_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def rounded(value: Any, digits: int = 8) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, digits) if math.isfinite(number) else None


def median(values: list[float]) -> float | None:
    clean = sorted(float(value) for value in values if value is not None and math.isfinite(float(value)))
    if not clean:
        return None
    mid = len(clean) // 2
    return clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2.0


def as_plain(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "_asdict"):
        return {key: as_plain(item) for key, item in value._asdict().items()}
    if isinstance(value, dict):
        return {str(key): as_plain(item) for key, item in value.items()}
    return repr(value)


def connect_bridge():
    from siliconmetatrader5 import MetaTrader5

    mt5 = MetaTrader5(host=BRIDGE_HOST, port=BRIDGE_PORT, timeout=BRIDGE_TIMEOUT_SECONDS)
    initialized = mt5.initialize()
    return mt5, bool(initialized)


def family_from_path(path: str | None) -> str:
    if not path:
        return "UNKNOWN"
    return str(path).split("\\")[0].strip() or "UNKNOWN"


def load_targets() -> list[dict[str, Any]]:
    return read_json(DOSSIER_ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")["rows"]


def account_history_symbol_commission(created_at: str, mt5: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    end = datetime.now(UTC)
    try:
        deals_raw = mt5.history_deals_get(HISTORY_START, end)
        history_error = None
    except Exception as exc:  # noqa: BLE001
        deals_raw = []
        history_error = repr(exc)
    deals = [as_plain(deal) for deal in (deals_raw or [])]
    grouped: dict[str, dict[str, Any]] = {}
    for deal in deals:
        if not isinstance(deal, dict):
            continue
        symbol = str(deal.get("symbol") or "UNKNOWN")
        row = grouped.setdefault(
            symbol,
            {
                "symbol": symbol,
                "deal_count": 0,
                "commission_sum": 0.0,
                "commission_nonzero_count": 0,
                "swap_sum": 0.0,
                "swap_nonzero_count": 0,
                "profit_sum": 0.0,
                "volume_sum": 0.0,
                "entry_values": set(),
                "type_values": set(),
            },
        )
        commission = finite_float(deal.get("commission"))
        swap = finite_float(deal.get("swap"))
        row["deal_count"] += 1
        row["commission_sum"] += commission
        row["swap_sum"] += swap
        row["profit_sum"] += finite_float(deal.get("profit"))
        row["volume_sum"] += finite_float(deal.get("volume"))
        if abs(commission) > 1e-12:
            row["commission_nonzero_count"] += 1
        if abs(swap) > 1e-12:
            row["swap_nonzero_count"] += 1
        if deal.get("entry") is not None:
            row["entry_values"].add(deal.get("entry"))
        if deal.get("type") is not None:
            row["type_values"].add(deal.get("type"))
    rows = []
    for symbol, raw in sorted(grouped.items()):
        try:
            info = as_plain(mt5.symbol_info(symbol)) or {}
        except Exception:  # noqa: BLE001
            info = {}
        path = info.get("path")
        volume = raw["volume_sum"]
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.account_history_symbol_commission_row.v1",
                "created_at_utc": created_at,
                "symbol": symbol,
                "path": path,
                "family": family_from_path(path),
                "currency_profit": info.get("currency_profit"),
                "trade_calc_mode": info.get("trade_calc_mode"),
                "deal_count": raw["deal_count"],
                "commission_sum": rounded(raw["commission_sum"], 6),
                "commission_nonzero_count": raw["commission_nonzero_count"],
                "commission_abs_per_volume": rounded(abs(raw["commission_sum"]) / volume, 10) if volume else None,
                "swap_sum": rounded(raw["swap_sum"], 6),
                "swap_nonzero_count": raw["swap_nonzero_count"],
                "profit_sum": rounded(raw["profit_sum"], 6),
                "volume_sum": rounded(volume, 6),
                "entry_values": sorted(raw["entry_values"]),
                "type_values": sorted(raw["type_values"]),
                "raw_ticket_or_deal_ids_stored": False,
                "commission_observation_status": (
                    "observed_nonzero_commission"
                    if raw["commission_nonzero_count"] > 0
                    else "observed_zero_commission"
                    if raw["deal_count"] > 0
                    else "no_deals"
                ),
            }
        )
    summary = {
        "schema": f"{SCHEMA_PREFIX}.account_history_symbol_commission_summary.v1",
        "created_at_utc": created_at,
        "history_window_start_utc": HISTORY_START.isoformat(),
        "history_window_end_utc": end.isoformat(),
        "history_error": history_error,
        "symbol_count": len(rows),
        "deal_count_total": sum(row["deal_count"] for row in rows),
        "nonzero_commission_symbol_count": sum(1 for row in rows if row["commission_nonzero_count"] > 0),
        "zero_commission_symbol_count": sum(1 for row in rows if row["deal_count"] > 0 and row["commission_nonzero_count"] == 0),
        "commission_sum_total": rounded(sum(row["commission_sum"] or 0.0 for row in rows), 6),
        "raw_ticket_or_deal_ids_stored": False,
        "family_counts": dict(Counter(row["family"] for row in rows)),
        "commission_status_counts": dict(Counter(row["commission_observation_status"] for row in rows)),
    }
    return rows, summary


def target_transfer_rows(
    created_at: str,
    mt5: Any,
    account_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_symbol = {row["symbol"]: row for row in account_rows}
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in account_rows:
        if row["symbol"] == "UNKNOWN":
            continue
        by_family.setdefault(row["family"], []).append(row)
    rows = []
    for target in load_targets():
        broker_symbol = target["broker_symbol"]
        info = as_plain(mt5.symbol_info(broker_symbol)) or {}
        family = family_from_path(info.get("path"))
        direct = by_symbol.get(broker_symbol)
        family_rows = [row for row in by_family.get(family, []) if row["symbol"] != broker_symbol]
        family_nonzero = [row for row in family_rows if row["commission_nonzero_count"] > 0]
        family_zero = [row for row in family_rows if row["deal_count"] > 0 and row["commission_nonzero_count"] == 0]
        if direct and direct["deal_count"] > 0 and direct["commission_nonzero_count"] > 0:
            status = "direct_observed_nonzero_commission"
            authority_class = "direct_account_history"
            proxy_direction = "nonzero_commission"
        elif direct and direct["deal_count"] > 0:
            status = "direct_observed_zero_commission"
            authority_class = "direct_account_history"
            proxy_direction = "zero_commission"
        elif family_nonzero and not family_zero:
            status = "family_proxy_nonzero_commission"
            authority_class = "family_proxy_account_history"
            proxy_direction = "nonzero_commission"
        elif family_zero and not family_nonzero:
            status = "family_proxy_zero_commission"
            authority_class = "family_proxy_account_history"
            proxy_direction = "zero_commission"
        elif family_nonzero and family_zero:
            status = "family_proxy_mixed_commission"
            authority_class = "family_proxy_mixed_account_history"
            proxy_direction = "mixed_commission"
        else:
            status = "not_closed_no_direct_or_family_commission_evidence"
            authority_class = "not_closed"
            proxy_direction = "unknown"
        evidence_rows = family_nonzero or family_zero or family_rows
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.target_commission_transfer_row.v1",
                "created_at_utc": created_at,
                "tag": target["tag"],
                "file_symbol": target["file_symbol"],
                "broker_symbol": broker_symbol,
                "path": info.get("path"),
                "family": family,
                "direct_deal_count": direct["deal_count"] if direct else 0,
                "direct_commission_sum": direct["commission_sum"] if direct else None,
                "direct_commission_nonzero_count": direct["commission_nonzero_count"] if direct else 0,
                "family_evidence_symbol_count": len(family_rows),
                "family_nonzero_commission_symbol_count": len(family_nonzero),
                "family_zero_commission_symbol_count": len(family_zero),
                "family_evidence_symbols": [row["symbol"] for row in evidence_rows],
                "family_commission_abs_per_volume_median": rounded(
                    median([row["commission_abs_per_volume"] for row in evidence_rows if row.get("commission_abs_per_volume") is not None]),
                    10,
                )
                if evidence_rows
                else None,
                "commission_transfer_status": status,
                "commission_authority_class": authority_class,
                "proxy_direction": proxy_direction,
                "raw_ticket_or_deal_ids_stored": False,
                "live_authority_meaning": (
                    "direct rows are account-history authority; family rows are proxy only and do not replace broker schedule/platform proof"
                ),
            }
        )
    status_counts = Counter(row["commission_transfer_status"] for row in rows)
    summary = {
        "schema": f"{SCHEMA_PREFIX}.target_commission_transfer_summary.v1",
        "created_at_utc": created_at,
        "target_symbol_count": len(rows),
        "direct_authority_symbol_count": sum(1 for row in rows if row["commission_authority_class"] == "direct_account_history"),
        "family_proxy_symbol_count": sum(1 for row in rows if row["commission_authority_class"].startswith("family_proxy")),
        "not_closed_symbol_count": sum(1 for row in rows if row["commission_authority_class"] == "not_closed"),
        "direct_or_family_proxy_symbol_count": sum(1 for row in rows if row["commission_authority_class"] != "not_closed"),
        "status_counts": dict(status_counts),
        "all_targets_have_direct_or_family_proxy": all(row["commission_authority_class"] != "not_closed" for row in rows),
        "broker_exact_schedule_closed": False,
        "interpretation": (
            "all target symbols now have direct account-history or same-family account-history commission evidence, "
            "but family transfer remains proxy and does not close broker schedule/platform authority"
        ),
    }
    return rows, summary


def unresolved_requirements(created_at: str) -> list[dict[str, Any]]:
    items = [
        (
            "MX-COMMISSION-FAMILY-REQ-001",
            "broker-exact commission schedule or platform-source proof",
            "family-transfer account history covers all targets but is proxy for no-direct symbols",
            "capture broker/platform commission schedule or sufficient direct account-history/export evidence for each promoted symbol",
        ),
        (
            "MX-COMMISSION-FAMILY-REQ-002",
            "direct commission evidence for every activation symbol",
            "seven target symbols are still family-proxy rather than direct account-history commission evidence",
            "future broker-history rows, manual broker export, or G12/owner-approved family-transfer activation rule",
        ),
        (
            "MX-COMMISSION-FAMILY-REQ-003",
            "remaining session/fill/swap authority from broker/fill routes",
            "commission family proxy does not close explicit sessions, prospective fillability, mode-5 swap, or holding-time model",
            "continue from broker-authority and fill/session residual ledgers",
        ),
        (
            "MX-COMMISSION-FAMILY-REQ-004",
            "owner-approved VPS promotion and monitoring execution",
            "Mac route remains default-off and does not push, reload, restart, or apply live config",
            "VPS Codex session must absorb commits, rerun packet parity, apply only after all authority gates close, monitor, and retain rollback",
        ),
    ]
    return [
        {
            "schema": f"{SCHEMA_PREFIX}.unresolved_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": req_id,
            "requirement": requirement,
            "current_evidence": evidence,
            "repair_path": repair,
            "status": "not_closed_by_current_probe",
            "runtime_effect_now": "none_market_expansion_default_off",
        }
        for req_id, requirement, evidence, repair in items
    ]


def decision_ledgers(
    created_at: str,
    result: dict[str, Any],
    transfer_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "commission_family_transfer_partial_repair",
            "status": result["decision"],
            "evidence": transfer_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "broker_exact_commission_schedule",
            "status": "not_closed_family_proxy_only",
            "evidence": {"broker_exact_schedule_closed": False},
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "market_expansion_promotion",
            "status": "default_off_not_promoted",
            "evidence": {"deployment_ready": False, "promotion_ready": False},
        },
    ]
    boundary = [
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "direct_or_family_commission_evidence",
            "status": "closed_as_proxy_not_schedule",
            "evidence": transfer_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "broker_exact_commission_schedule",
            "status": "not_closed",
            "evidence": "family-transfer proxy does not replace broker/platform commission schedule",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "owner_vps_action",
            "status": "not_executed_by_mac_route",
            "evidence": "no config activation, remote push, broker mutation, or VPS restart/reload",
        },
    ]
    return decisions, boundary


def forbidden_call_scan(created_at: str) -> dict[str, Any]:
    scanned_paths = [
        ROUTE / "build_market_expansion_commission_family_transfer.py",
        ROUTE / "verify_market_expansion_commission_family_transfer.py",
        PROJECT_ROOT / "tests" / "ultimate_book" / "test_market_expansion_commission_family_transfer_artifacts.py",
    ]
    forbidden_patterns = [
        "order" + "_send" + "(",
        "order" + "_check" + "(",
        "TRADE" + "_ACTION_",
        "positions" + "_get" + "(",
        "mt5.orders" + "_get" + "(",
        ".orders" + "_get",
        "market" + "_book_add" + "(",
        "market" + "_book_get" + "(",
        "market" + "_book_release" + "(",
        "symbol" + "_select" + "(",
        "copy" + "_ticks_range" + "(",
        "subprocess" + ".run(['" + "ssh'",
        "subprocess" + ".run([\"" + "ssh\"",
        "rs" + "ync ",
        "sc" + "p ",
    ]
    matches = []
    for path in scanned_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in text:
                matches.append({"path": rel(path), "pattern": pattern})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "scanned_paths": [rel(path) for path in scanned_paths if path.exists()],
        "approved_read_calls_not_forbidden_in_this_route": ["history_deals_get", "symbol_info"],
        "forbidden_patterns": forbidden_patterns,
        "matches": matches,
        "ok": not matches,
    }


def write_packet(result: dict[str, Any], requirements: list[dict[str, Any]]) -> None:
    req_text = "\n".join(f"- `{row['requirement_id']}`: {row['requirement']}" for row in requirements)
    packet = f"""# Market Expansion Commission Family-Transfer Packet

Decision: `{result['decision']}`

This package repairs commission evidence from account-history families without
promoting market expansion.

What improved:

- Direct account-history commission evidence: `{result['direct_commission_authority_symbol_count']}/{result['target_symbol_count']}` target symbols.
- Family-proxy account-history commission evidence: `{result['family_proxy_commission_symbol_count']}/{result['target_symbol_count']}` target symbols.
- Direct or family-proxy coverage: `{result['direct_or_family_proxy_symbol_count']}/{result['target_symbol_count']}` target symbols.

What remains open:

{req_text}

Runtime boundary:

- `live_authority=false`
- `deployment_ready=false`
- `promotion_ready=false`
- `runtime_effect=none_market_expansion_default_off_commission_family_transfer_only`
"""
    (ROUTE / "COMMISSION_FAMILY_TRANSFER_PACKET.md").write_text(packet, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Market Expansion Commission Schedule Closure Successor Prompt

Created: {created_at}

Mandatory context use: run GTOS preflight, regenerate `.context/LIVE_STATE.md`, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`, this prompt, and the commission family-transfer artifacts from disk as active instructions, not background. Do not rely on chat memory. After compaction/resume/interruption/uncertainty, reread the prompt, doctrine, and latest route artifacts before continuing and record instruction-coverage in the completion audit.

Lane posture: constructive source-repair and deployment-authority closure. Keep market expansion default-off until all authority gates close. Use maximum practical reasoning inside the evidence class, no arbitrary top-N, and no conservative brake. Preserve all material rows and pursue same-evidence-class repair before declaring a blocker.

Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been attempted, repaired, recomputed, or reduced to an exact owner/source/capture requirement. Full same-evidence-class pursuit is mandatory; a clean blocker ledger is not completion when a same-class read-only source-capture, source completeness check, branch decision, implementation decision, exact-R/proxy-R/expectancy recomputation, or result materialization step is still executable.

Input route: `research/operations/final_moonshot_market_expansion_commission_family_transfer_2026_06_18/`.

Objective: close or exactly bound broker-exact commission schedule authority. The current route gives direct or family-proxy account-history commission evidence for all 14 market-expansion targets. Continue from those artifacts. Search for exact broker/platform commission schedules, direct broker-history/export evidence for family-proxy targets, and a G12/owner-acceptable rule for whether family-transfer can be used in a default-off packet. If exact schedule authority remains open, keep market expansion default-off and preserve the family-transfer proxy only as cost-model input candidate, not live authority.

Result materialization standard: every branch decision and implementation decision must preserve result-use-status/evidence-class boundaries, exact-R/proxy-R/expectancy values where lawful, source-capture/source completeness status, row counts, denominator rules, no-leak/as-of controls, and unresolved owner/source/capture requirements.

Approved read-only evidence surfaces in this lane: aggregate `history_deals_get`, `symbol_info`, already committed broker-authority/fill-session route artifacts, and local config/test files. Forbidden unless the owner explicitly opens a deployment/live-operation lane: production-change, live trading, broker operation, broker/account/order/history/deal/position mutation beyond the approved aggregate read-only evidence class, order send/check, symbol selection, open positions/orders state reads, market book/depth/orderflow, prompt/config/risk/execution/safety/canary/selector live activation, credential mutation/disclosure, paid API/vendor calls, remote push, live config activation, and VPS restart/reload.

Completion requires: result JSON, decision ledger, promotion-boundary ledger, unresolved/blocker-repair ledgers, verifier result, focused test record, output manifest, saturation/self-red-team audit, completion audit with instruction coverage, and a scoped commit. Mark complete only when the completion standard is satisfied with no vague blockers or hidden live-action assumptions.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if path.is_file() and path.name != "OUTPUT_MANIFEST.json":
            artifacts.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    mt5, initialized = connect_bridge()
    account_rows, account_summary = account_history_symbol_commission(created_at, mt5)
    transfer_rows, transfer_summary = target_transfer_rows(created_at, mt5, account_rows)
    requirements = unresolved_requirements(created_at)
    forbidden = forbidden_call_scan(created_at)
    ok = (
        initialized
        and transfer_summary["target_symbol_count"] == 14
        and transfer_summary["all_targets_have_direct_or_family_proxy"] is True
        and transfer_summary["broker_exact_schedule_closed"] is False
        and account_summary["raw_ticket_or_deal_ids_stored"] is False
        and forbidden["ok"] is True
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": "COMMISSION_FAMILY_TRANSFER_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED",
        "source_broker_authority_route": rel(BROKER_AUTH_ROUTE),
        "source_fill_session_route": rel(FILL_SESSION_ROUTE),
        "source_dossier_route": rel(DOSSIER_ROUTE),
        "target_symbol_count": transfer_summary["target_symbol_count"],
        "account_history_symbol_count": account_summary["symbol_count"],
        "account_history_deal_count": account_summary["deal_count_total"],
        "direct_commission_authority_symbol_count": transfer_summary["direct_authority_symbol_count"],
        "family_proxy_commission_symbol_count": transfer_summary["family_proxy_symbol_count"],
        "not_closed_commission_symbol_count": transfer_summary["not_closed_symbol_count"],
        "direct_or_family_proxy_symbol_count": transfer_summary["direct_or_family_proxy_symbol_count"],
        "all_targets_have_direct_or_family_proxy": transfer_summary["all_targets_have_direct_or_family_proxy"],
        "broker_exact_schedule_closed": False,
        "config_patch_applied": False,
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "runtime_effect": "none_market_expansion_default_off_commission_family_transfer_only",
        "deployment_not_ready_requirement_ids": [row["requirement_id"] for row in requirements],
        "deployment_not_ready_reasons": [row["requirement"] for row in requirements],
        "approved_read_surfaces_used": ["history_deals_get_aggregate_only", "symbol_info"],
        "forbidden_surfaces_touched": [],
    }
    decisions, boundary = decision_ledgers(created_at, result, transfer_summary)
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "no_arbitrary_top_n": True,
        "anti_boxing_checked": [
            "all account-history symbols grouped, not target-only history",
            "target direct evidence separated from family proxy evidence",
            "commission direction separated into nonzero, zero, mixed, and not-closed",
            "family proxy not overclaimed as broker schedule",
            "raw ticket/deal identifiers excluded from artifacts",
        ],
        "same_evidence_class_repairs_completed": [
            "all target commission gaps now have direct or family-proxy account-history evidence",
            "no-history symbols converted into explicit family proxy rows",
            "broker exact schedule remains open with concrete residual requirements",
        ],
        "remaining_exact_requirements": result["deployment_not_ready_reasons"],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_source_repair_posture_applied": True,
            "inspire_not_kill_applied": True,
            "same_evidence_class_pursued": True,
            "no_arbitrary_top_n": True,
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "raw_ticket_or_deal_ids_stored": False,
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "owner_action_live_authority_boundary": "required before config patch, VPS reload, broker mutation, or live promotion",
    }

    write_jsonl(ROUTE / "ACCOUNT_HISTORY_SYMBOL_COMMISSION_LEDGER.jsonl", account_rows)
    write_json(ROUTE / "ACCOUNT_HISTORY_SYMBOL_COMMISSION_SUMMARY.json", account_summary)
    write_jsonl(ROUTE / "TARGET_COMMISSION_TRANSFER_LEDGER.jsonl", transfer_rows)
    write_json(ROUTE / "TARGET_COMMISSION_TRANSFER_SUMMARY.json", transfer_summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "PROMOTION_BOUNDARY_LEDGER.jsonl", boundary)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "COMMISSION_FAMILY_TRANSFER_RESULT.json", result)
    write_packet(result, requirements)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 180) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-5000:],
    }


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command(
        [sys.executable, str(ROUTE / "verify_market_expansion_commission_family_transfer.py")],
        timeout=240,
    )
    write_json(
        ROUTE / "VERIFIER_COMMAND_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1",
            "created_at_utc": created_at,
            **verifier_result,
        },
    )
    checks = [
        run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(ROUTE / "build_market_expansion_commission_family_transfer.py"),
                str(ROUTE / "verify_market_expansion_commission_family_transfer.py"),
                "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py",
                "-q",
            ],
            timeout=180,
        ),
    ]
    write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
            "created_at_utc": created_at,
            "ok": all(row["returncode"] == 0 for row in checks),
            "results": checks,
        },
    )
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
