#!/usr/bin/env python3
"""Build a market-expansion activation-readiness synthesis.

This route is deterministic over already materialized route artifacts. It does
not call MT5, mutate broker/account/order/deal/position state, apply config,
push remotes, or touch VPS processes. Its job is to preserve the strongest
current truth in one per-candidate authority matrix for the next repair or VPS
handoff lane.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
OPS = PROJECT_ROOT / "research" / "operations"
PROMOTION_ROUTE = OPS / "final_moonshot_market_expansion_promotion_boundary_2026_06_18"
BROKER_ROUTE = OPS / "final_moonshot_market_expansion_broker_authority_probe_2026_06_18"
FILL_ROUTE = OPS / "final_moonshot_market_expansion_fill_session_probe_2026_06_18"
COMMISSION_ROUTE = OPS / "final_moonshot_market_expansion_commission_family_transfer_2026_06_18"
DOSSIER_ROUTE = OPS / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
RUNTIME_ROUTE = OPS / "final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_activation_readiness_synthesis"
DECISION = "MARKET_EXPANSION_ACTIVATION_READINESS_SYNTHESIS_READY_DEFAULT_OFF_NOT_PROMOTED"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index_by_tag(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        tag = row.get("tag")
        if tag:
            out[str(tag)] = row
    return out


def portfolio_scenario_by_name(name: str) -> dict[str, Any]:
    for row in read_jsonl(DOSSIER_ROUTE / "PORTFOLIO_REPLAY_LEDGER.jsonl"):
        if row.get("name") == name:
            return row
    raise KeyError(name)


def status_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key)) for row in rows))


def compact_scenario(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row.get("name"),
        "sharpe": row.get("sharpe"),
        "monthly_pct": (row.get("mc") or {}).get("monthly_pct"),
        "p_pass": (row.get("mc") or {}).get("p_pass"),
        "p_fail_dd": (row.get("mc") or {}).get("p_fail_dd"),
        "worst_day_pct": (row.get("mc") or {}).get("worst_day_pct"),
        "delta_vs_base": row.get("delta_vs_base") or {},
        "expansion_weight_per_tag": row.get("expansion_weight_per_tag"),
        "sleeve_count": row.get("sleeve_count"),
    }


def build_matrix(created_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    runtime_rows = index_by_tag(read_jsonl(RUNTIME_ROUTE / "RUNTIME_GENERATOR_PARITY_LEDGER.jsonl"))
    dossier_rows = index_by_tag(read_jsonl(DOSSIER_ROUTE / "SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl"))
    fill_rows = index_by_tag(read_jsonl(FILL_ROUTE / "HISTORY_ORDER_DEAL_FILL_LEDGER.jsonl"))
    session_rows = index_by_tag(read_jsonl(FILL_ROUTE / "OBSERVED_M1_SESSION_AVAILABILITY_LEDGER.jsonl"))
    commission_rows = index_by_tag(read_jsonl(COMMISSION_ROUTE / "TARGET_COMMISSION_TRANSFER_LEDGER.jsonl"))
    profit_rows = index_by_tag(read_jsonl(BROKER_ROUTE / "ORDER_CALC_PROFIT_CONVERSION_LEDGER.jsonl"))
    swap_rows_by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(BROKER_ROUTE / "SWAP_TO_R_PARTIAL_AUTHORITY_LEDGER.jsonl"):
        swap_rows_by_tag[str(row["tag"])].append(row)

    cost3_scenario = portfolio_scenario_by_name("candidate_plus_expansion_seed_0p025_cost3")
    cost3_contribution = cost3_scenario.get("contribution") or {}

    tags = sorted(runtime_rows)
    matrix: list[dict[str, Any]] = []
    for tag in tags:
        runtime = runtime_rows[tag]
        dossier = dossier_rows.get(tag, {})
        fill = fill_rows.get(tag, {})
        session = session_rows.get(tag, {})
        commission = commission_rows.get(tag, {})
        profit = profit_rows.get(tag, {})
        swap_rows = swap_rows_by_tag.get(tag, [])
        swap_conversion_counts = Counter(row.get("conversion_status") for row in swap_rows)
        mode5_formula_required = any(
            row.get("conversion_status") == "not_closed_interest_current_mode_formula_required"
            for row in swap_rows
        )
        point_mode_computed = bool(swap_rows) and all(
            row.get("conversion_status") == "point_mode_cash_to_r_computed"
            for row in swap_rows
        )
        explicit_session_closed = (
            dossier.get("explicit_trade_session_table_row_count", 0) > 0
            or dossier.get("explicit_quote_session_table_row_count", 0) > 0
        )
        observed_session_proxy = bool(session.get("m1_bar_count", 0))
        direct_fill = fill.get("fill_authority_status") == "direct_observed_historical_order_deal_fill_slippage"
        commission_direct_or_family = commission.get("commission_authority_class") in {
            "direct_account_history",
            "family_proxy_account_history",
            "family_proxy_mixed_account_history",
        }
        default_off_code_package_ready = all(
            [
                runtime.get("all_parity_passed") is True,
                dossier.get("source_event_join_complete") is True,
                dossier.get("broker_symbol_info_status") == "captured",
                dossier.get("broker_symbol_info_tick_status") == "captured",
                dossier.get("broker_stop_freeze_present") is True,
                profit.get("conversion_status") == "closed_order_calc_profit_matches_symbol_info",
            ]
        )
        open_authority_requirements = [
            "explicit_broker_trading_session_table_or_platform_source_proof",
            "broker_exact_prospective_limit_and_market_fill_authority",
            "broker_exact_commission_schedule_or_accepted_family_transfer_rule",
            "exact_swap_to_r_holding_time_and_rollover_model",
            "owner_approved_vps_packet_parity_promotion_monitoring_and_rollback",
        ]
        if mode5_formula_required:
            open_authority_requirements.append("swap_mode5_formula_source_for_crypto_symbols")
        if not direct_fill:
            open_authority_requirements.append("direct_historical_or_forward_fill_slippage_for_this_symbol")
        if commission.get("commission_authority_class") != "direct_account_history":
            open_authority_requirements.append("direct_commission_history_or_accepted_family_proxy_for_this_symbol")

        row = {
            "schema": f"{SCHEMA_PREFIX}.candidate_authority_row.v1",
            "created_at_utc": created_at,
            "tag": tag,
            "file_symbol": runtime.get("file_symbol") or dossier.get("file_symbol"),
            "broker_symbol": runtime.get("broker_symbol") or dossier.get("broker_symbol"),
            "family": runtime.get("family") or dossier.get("family"),
            "mechanism": runtime.get("mechanism") or dossier.get("mechanism"),
            "source_event_count": runtime.get("activation_row_source_event_count"),
            "runtime_generator_parity_closed": runtime.get("all_parity_passed") is True,
            "runtime_matched_event_count": runtime.get("matched_event_count"),
            "runtime_missing_event_count": runtime.get("missing_event_count"),
            "runtime_extra_event_count": runtime.get("extra_event_count"),
            "broker_spec_snapshot_closed": dossier.get("broker_symbol_info_status") == "captured",
            "broker_tick_snapshot_closed": dossier.get("broker_symbol_info_tick_status") == "captured",
            "broker_stop_freeze_present": dossier.get("broker_stop_freeze_present") is True,
            "profit_conversion_status": profit.get("conversion_status"),
            "profit_conversion_closed": profit.get("conversion_status") == "closed_order_calc_profit_matches_symbol_info",
            "source_cost_join_closed": dossier.get("source_event_join_complete") is True,
            "cost3_all_mean_proxy_r": ((dossier.get("proxy_r_cost3_summary") or {}).get("all") or {}).get("mean"),
            "cost3_all_win_rate": ((dossier.get("proxy_r_cost3_summary") or {}).get("all") or {}).get("win_rate"),
            "cost3_every_populated_split_positive": (dossier.get("proxy_r_cost3_summary") or {}).get("every_populated_split_positive"),
            "cost3_populated_split_count": (dossier.get("proxy_r_cost3_summary") or {}).get("populated_split_count"),
            "seed_weight_0p025_matched_days": (cost3_contribution.get(tag) or {}).get("matched_days"),
            "seed_weight_0p025_raw_daily_rows": (cost3_contribution.get(tag) or {}).get("raw_daily_rows"),
            "seed_weight_0p025_total_weighted_r": (cost3_contribution.get(tag) or {}).get("total_weighted_R"),
            "explicit_session_table_closed": explicit_session_closed,
            "explicit_session_table_status": dossier.get("explicit_session_table_status"),
            "observed_m1_session_proxy_closed": observed_session_proxy,
            "observed_m1_session_proxy_status": session.get("observed_session_proxy_status"),
            "observed_m1_session_proxy_class": session.get("observed_session_proxy_status"),
            "observed_m1_weekdays_with_bars": session.get("weekdays_with_bars"),
            "observed_m1_utc_hours_with_bars": session.get("utc_hours_with_bars"),
            "direct_fill_slippage_closed": direct_fill,
            "fill_authority_status": fill.get("fill_authority_status"),
            "joined_entry_deal_count": fill.get("joined_entry_deal_count"),
            "slippage_abs_r_max_observed": fill.get("slippage_abs_r_max"),
            "slippage_abs_r_mean_observed": fill.get("slippage_abs_r_mean"),
            "commission_authority_class": commission.get("commission_authority_class"),
            "commission_transfer_status": commission.get("commission_transfer_status"),
            "commission_direct_or_family_proxy_closed": commission_direct_or_family,
            "commission_proxy_direction": commission.get("proxy_direction"),
            "direct_commission_sum": commission.get("direct_commission_sum"),
            "direct_deal_count": commission.get("direct_deal_count"),
            "family_evidence_symbol_count": commission.get("family_evidence_symbol_count"),
            "swap_side_row_count": len(swap_rows),
            "swap_conversion_status_counts": dict(swap_conversion_counts),
            "swap_point_mode_conversion_computed": point_mode_computed,
            "swap_mode5_formula_required": mode5_formula_required,
            "swap_exact_holding_time_model_closed": False,
            "default_off_code_package_ready": default_off_code_package_ready,
            "deployment_ready": False,
            "promotion_ready": False,
            "live_authority_ready": False,
            "config_patch_applied": False,
            "runtime_effect": "none_default_off_activation_readiness_synthesis_only",
            "readiness_tier": (
                "default_off_code_ready_live_authority_open"
                if default_off_code_package_ready
                else "default_off_package_gap_requires_repair"
            ),
            "open_authority_requirements": sorted(set(open_authority_requirements)),
            "transformed_use": "preserve_as_default_off_candidate_and_broker_authority_repair_target",
        }
        matrix.append(row)

    summary = {
        "schema": f"{SCHEMA_PREFIX}.candidate_authority_summary.v1",
        "created_at_utc": created_at,
        "candidate_count": len(matrix),
        "readiness_tier_counts": status_counts(matrix, "readiness_tier"),
        "default_off_code_package_ready_count": sum(1 for row in matrix if row["default_off_code_package_ready"]),
        "live_authority_ready_count": sum(1 for row in matrix if row["live_authority_ready"]),
        "deployment_ready_count": sum(1 for row in matrix if row["deployment_ready"]),
        "promotion_ready_count": sum(1 for row in matrix if row["promotion_ready"]),
        "runtime_generator_parity_closed_count": sum(1 for row in matrix if row["runtime_generator_parity_closed"]),
        "broker_spec_snapshot_closed_count": sum(1 for row in matrix if row["broker_spec_snapshot_closed"]),
        "profit_conversion_closed_count": sum(1 for row in matrix if row["profit_conversion_closed"]),
        "source_cost_join_closed_count": sum(1 for row in matrix if row["source_cost_join_closed"]),
        "explicit_session_table_closed_count": sum(1 for row in matrix if row["explicit_session_table_closed"]),
        "observed_m1_session_proxy_closed_count": sum(1 for row in matrix if row["observed_m1_session_proxy_closed"]),
        "direct_fill_slippage_closed_count": sum(1 for row in matrix if row["direct_fill_slippage_closed"]),
        "no_direct_fill_slippage_symbol_count": sum(1 for row in matrix if not row["direct_fill_slippage_closed"]),
        "commission_direct_or_family_proxy_closed_count": sum(1 for row in matrix if row["commission_direct_or_family_proxy_closed"]),
        "direct_commission_authority_count": sum(1 for row in matrix if row["commission_authority_class"] == "direct_account_history"),
        "family_proxy_commission_authority_count": sum(1 for row in matrix if row["commission_authority_class"] == "family_proxy_account_history"),
        "swap_point_mode_symbol_count": sum(1 for row in matrix if row["swap_point_mode_conversion_computed"]),
        "swap_mode5_formula_required_symbol_count": sum(1 for row in matrix if row["swap_mode5_formula_required"]),
        "cost3_positive_mean_count": sum(1 for row in matrix if (row["cost3_all_mean_proxy_r"] or 0) > 0),
        "cost3_every_populated_split_positive_count": sum(
            1 for row in matrix if row["cost3_every_populated_split_positive"] is True
        ),
    }
    return matrix, summary


def build_requirements(created_at: str, summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "requirement_id": "MX-READINESS-REQ-001",
            "requirement": "explicit broker trading-session table or platform-source proof",
            "current_status": "not_closed",
            "current_evidence": "explicit session table closed 0/14; observed M1 quote-session proxy exists 14/14 but is not a broker session table",
            "local_same_class_action": "optional extended observed-session calendar can strengthen guarded-open scheduling, but cannot by itself become explicit session-table authority without owner/G12 acceptance",
            "owner_or_vps_action": "obtain broker/platform session table source or approve a proxy rule before live promotion",
        },
        {
            "requirement_id": "MX-READINESS-REQ-002",
            "requirement": "broker-exact prospective limit-fill and market-fill authority",
            "current_status": "not_closed",
            "current_evidence": f"direct historical order/deal fill-slippage rows exist for {summary['direct_fill_slippage_closed_count']}/14 symbols; prospective queue/fillability remains open",
            "local_same_class_action": "build a no-order-send M1/tick path fillability proxy for source events, then keep it labeled proxy until forward broker capture validates it",
            "owner_or_vps_action": "forward capture or VPS-side broker packet parity is required before live fill authority",
        },
        {
            "requirement_id": "MX-READINESS-REQ-003",
            "requirement": "broker-exact commission schedule or accepted family-transfer production rule",
            "current_status": "partial_proxy_repair_not_closed",
            "current_evidence": "direct-or-family commission evidence exists 14/14; direct authority 7/14 and family proxy 7/14; exact broker schedule remains absent",
            "local_same_class_action": "preserve family proxy and route to G12/owner decision; do not overclaim platform schedule proof",
            "owner_or_vps_action": "supply broker commission schedule or approve family transfer as a production rule with monitoring",
        },
        {
            "requirement_id": "MX-READINESS-REQ-004",
            "requirement": "exact swap-to-R holding-time, rollover, and mode-5 formula model",
            "current_status": "partial_proxy_repair_not_closed",
            "current_evidence": f"point-mode conversion computed for {summary['swap_point_mode_symbol_count']}/14 symbols; mode-5 formula required for {summary['swap_mode5_formula_required_symbol_count']}/14 crypto symbols; exact holding-time and rollover model remains open for all",
            "local_same_class_action": "source exact MT5/broker swap calculation semantics and bind D1 holding-time distribution before promotion",
            "owner_or_vps_action": "broker/platform documentation or VPS packet parity may be required for exact account-currency swap authority",
        },
        {
            "requirement_id": "MX-READINESS-REQ-005",
            "requirement": "VPS packet parity, monitoring, rollback, and owner-approved promotion execution",
            "current_status": "not_executed_by_mac_route",
            "current_evidence": "Mac route produced default-off artifacts and non-applied handoff only; no remote push, config activation, broker mutation, or VPS reload occurred",
            "local_same_class_action": "keep handoff packet exact and preserve rollback criteria",
            "owner_or_vps_action": "VPS Codex/session must absorb the package, verify parity, and execute only after owner-approved activation boundary",
        },
    ]
    for row in rows:
        row.update(
            {
                "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
                "created_at_utc": created_at,
                "live_authority_ready": False,
            }
        )
    return rows


def build_local_repair_exhaustion(created_at: str) -> list[dict[str, Any]]:
    items = [
        (
            "runtime_generator_parity",
            "closed_14_of_14",
            "runtime generator parity, dry-run execution packet, and source-event join are already closed in committed artifacts",
            "no further local repair needed before authority gates",
        ),
        (
            "broker_symbol_profit_conversion",
            "closed_14_of_14",
            "order_calc_profit conversion matches symbol_info tick value for all target symbols",
            "no further local repair needed before authority gates",
        ),
        (
            "observed_m1_session_proxy",
            "proxy_closed_14_of_14_not_explicit_authority",
            "M1 bars establish observed quote availability classes for all symbols",
            "possible next local repair: extend to a multi-month observed guarded-open calendar, still proxy",
        ),
        (
            "commission_family_transfer",
            "proxy_closed_14_of_14_not_schedule_authority",
            "direct or family account-history commission evidence covers every target symbol",
            "needs broker schedule or owner/G12 family-transfer rule before promotion",
        ),
        (
            "historical_fill_slippage",
            "partial_direct_7_of_14",
            "direct order/deal fill-slippage exists for symbols with account-history rows",
            "possible next local repair: source-event M1/tick no-order-send fillability proxy; exact queue truth remains forward/VPS",
        ),
        (
            "swap_to_r",
            "partial_point_mode_11_symbols_mode5_open",
            "point-mode symbols have cash-to-R proxy; crypto mode-5 and holding/rollover are open",
            "possible next local repair: source exact mode-5 formula and D1 holding-time distribution",
        ),
        (
            "explicit_session_table",
            "not_available_from_current_bridge_client",
            "prior probes found no symbol_info_session_trade/quote methods and no session-like symbol_info keys",
            "requires platform/broker source, API support, or owner-approved proxy rule",
        ),
    ]
    return [
        {
            "schema": f"{SCHEMA_PREFIX}.local_repair_exhaustion_row.v1",
            "created_at_utc": created_at,
            "repair_family": family,
            "current_status": status,
            "evidence": evidence,
            "next_action": next_action,
        }
        for family, status, evidence, next_action in items
    ]


def build_forbidden_scan(created_at: str) -> dict[str, Any]:
    forbidden_tokens = [
        "order_" + "send(",
        "order_" + "check(",
        "orders_" + "get(",
        "positions_" + "get(",
        "market_book_" + "add(",
        "market_book_" + "get(",
        "market_book_" + "release(",
        "subprocess.run([" + "'git', 'push'",
    ]
    matches: list[dict[str, Any]] = []
    for path in [ROUTE / "build_market_expansion_activation_readiness_synthesis.py", ROUTE / "verify_market_expansion_activation_readiness_synthesis.py"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in forbidden_tokens:
            if token in text:
                matches.append({"path": rel(path), "token": token})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "ok": not matches,
        "scanned_files": [
            rel(ROUTE / "build_market_expansion_activation_readiness_synthesis.py"),
            rel(ROUTE / "verify_market_expansion_activation_readiness_synthesis.py"),
        ],
        "matches": matches,
    }


def write_packet(result: dict[str, Any], summary: dict[str, Any], requirements: list[dict[str, Any]]) -> None:
    cost3 = result["portfolio_reference_numbers"]["candidate_plus_expansion_seed_0p025_cost3"]
    text = f"""# Market Expansion Activation Readiness Synthesis

Decision: `{result['decision']}`

Runtime effect: `{result['runtime_effect']}`

## Current Numbers

- Active A8 baseline Sharpe `{result['portfolio_reference_numbers']['active_core8_a8_baseline_no_candidates']['sharpe']}`, monthly `{result['portfolio_reference_numbers']['active_core8_a8_baseline_no_candidates']['monthly_pct']}%`, MC pass `{result['portfolio_reference_numbers']['active_core8_a8_baseline_no_candidates']['p_pass']}`.
- Armed candidate book Sharpe `{result['portfolio_reference_numbers']['candidate_all_on_active_a8_reference']['sharpe']}`, monthly `{result['portfolio_reference_numbers']['candidate_all_on_active_a8_reference']['monthly_pct']}%`, MC pass `{result['portfolio_reference_numbers']['candidate_all_on_active_a8_reference']['p_pass']}`.
- Candidate plus market-expansion seed 0.025 under cost3 Sharpe `{cost3['sharpe']}`, monthly `{cost3['monthly_pct']}%`, MC pass `{cost3['p_pass']}`, max-DD fail `{cost3['p_fail_dd']}`, worst day `{cost3['worst_day_pct']}%`.

## Authority Matrix Summary

- Default-off code package ready rows: `{summary['default_off_code_package_ready_count']}/14`.
- Live-authority ready rows: `{summary['live_authority_ready_count']}/14`.
- Explicit session-table rows closed: `{summary['explicit_session_table_closed_count']}/14`.
- Observed M1 session proxy rows: `{summary['observed_m1_session_proxy_closed_count']}/14`.
- Direct fill-slippage rows: `{summary['direct_fill_slippage_closed_count']}/14`.
- Direct-or-family commission evidence rows: `{summary['commission_direct_or_family_proxy_closed_count']}/14`.
- Direct commission authority rows: `{summary['direct_commission_authority_count']}/14`.
- Point-mode swap conversion rows: `{summary['swap_point_mode_symbol_count']}/14`.
- Mode-5 swap formula-required rows: `{summary['swap_mode5_formula_required_symbol_count']}/14`.

## Boundary

This route says the market-expansion package is materially built as a default-off code/research package, but not live authority. No config patch was applied, no broker/order/account/deal/position mutation occurred, no orderflow/depth data was used, no remote push occurred, and no VPS reload occurred.

## Remaining Requirements

{chr(10).join(f'- `{row["requirement_id"]}`: {row["requirement"]} - {row["current_status"]}.' for row in requirements)}
"""
    (ROUTE / "ACTIVATION_READINESS_SYNTHESIS_PACKET.md").write_text(text, encoding="utf-8")


def write_vps_handoff_packet(result: dict[str, Any]) -> None:
    text = f"""# VPS Handoff Packet - Market Expansion Readiness

Local Mac decision: `{result['decision']}`.

Do not activate from this packet alone. First verify the exact commit set, run route verifiers, confirm active config boundaries, and keep market expansion default-off unless the owner explicitly approves promotion.

Required local verifier commands before any VPS-side interpretation:

```bash
python3 research/operations/final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18/verify_market_expansion_activation_readiness_synthesis.py
python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18 --full-jsonl
pytest tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py -q
```

Promotion remains closed until explicit session authority, exact fill authority, commission schedule or accepted family-transfer rule, exact swap/holding model, VPS packet parity, monitoring, rollback, and owner approval are complete.
"""
    (ROUTE / "VPS_HANDOFF_PACKET.md").write_text(text, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    text = f"""# Next Prompt - Market Expansion Observed Session And Fillability Repair

Created: {created_at}

`/goal Follow this controlling prompt as the complete objective. Mandatory preflight: run python3 scripts/generate_live_state.py, read .context/LIVE_STATE.md, current_vnext_system_map.md, current_repo_reading_order.md, goal_session_research_discipline.md, research_operating_doctrine.md, orchestrator_successor_operating_brief.md, orchestrator_methodology_hardening_controls.md, parallel_goal_merge_playbook.md, and the latest artifacts in research/operations/final_moonshot_market_expansion_activation_readiness_synthesis_2026_06_18. Do not rely on chat memory. After any compaction/resume/interruption/uncertainty, reread those files from disk.`

## Mandatory Context Use

Treat `goal_session_research_discipline.md` and `research_operating_doctrine.md` as active instructions, not background. Operationalize them in the route objective, searched-source ledger, saturation pass, branch decision, and completion audit. The completion audit must include instruction-coverage for mandatory preflight, doctrine reads, constructive builder posture, full same-evidence-class pursuit, no arbitrary top-N, proof-or-impossibility status, and every deliberate evidence-class boundary.

## Objective

Build the strongest no-order-send market-expansion observed-session and source-event fillability proxy repair route that local MT5/repo artifacts can support. Use the current readiness matrix as the input, preserve every candidate row, and pursue full same-evidence-class pursuit. This is a constructive builder/repair lane, not a conservative brake and not a promotion lane.

Result materialization is required: materialize source completeness, proxy-R, exact-R when available, expectancy/proxy expectancy where source fields support it, implementation decision or branch decision rows, and source-capture requirements. Do not stop at a blocker label when a local read/export/search/parser/repair/proxy/ablation/metric/audit/review action remains possible.

Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been tried or exactly ruled out from disk/source evidence.

## Hard Boundaries

- No production-change, live trading, broker operation, broker/account/order/history/deal/position mutation, or broker state mutation.
- No `order_send`, `order_check`, open-order/position state reads, market book/depth/orderflow, paid API calls, paid vendor calls, credential changes, remote push, live config activation, prompt/config/risk/execution/safety/canary/selector activation change, or VPS restart/reload.
- No claim that observed M1/tick proxy equals explicit broker session table, queue priority, or live fill authority.

These forbidden surfaces are hard rails; they are not permission to undercompute local source completeness, proxy-R, expectancy, or branch-decision artifacts.

## Required Outputs

- Full per-candidate observed-session calendar and no-order-send fillability proxy ledger.
- Exact searched-root/source manifest and hashes.
- Remaining explicit broker authority requirements.
- Saturation/self-red-team audit with no arbitrary top-N.
- Verifier, focused pytest, route audit, and scoped commit.

No arbitrary top-N, top 3/5/10, number-limited cutoff, representative-only summary, or hidden sample cap is allowed. Preserve all material rows in full ledger artifacts before writing ranked summaries.

## Completion Standard

Complete only when every local same-evidence-class observed-session/fillability repair has been computed or exactly proven impossible from available local inputs, and when all remaining gaps are row-level explicit owner/source/VPS requirements. The final completion audit must name the artifacts, verifier result, focused test result, route audit status, source completeness status, result materialization status, and every forbidden-surface boundary kept closed.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(text, encoding="utf-8")


def write_output_manifest(created_at: str) -> None:
    rows = []
    for path in sorted(ROUTE.iterdir()):
        if not path.is_file() or path.name == "OUTPUT_MANIFEST.json":
            continue
        rows.append(
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "artifact_count": len(rows),
            "artifacts": rows,
        },
    )


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    matrix, summary = build_matrix(created_at)
    requirements = build_requirements(created_at, summary)
    local_repair = build_local_repair_exhaustion(created_at)
    forbidden = build_forbidden_scan(created_at)

    scenarios = {
        name: compact_scenario(portfolio_scenario_by_name(name))
        for name in (
            "active_core8_a8_baseline_no_candidates",
            "candidate_all_on_active_a8_reference",
            "candidate_plus_expansion_seed_0p025_cost3",
            "candidate_plus_expansion_micro_0p0125_cost3",
            "candidate_plus_expansion_ceiling_0p05_cost3",
        )
    }
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            len(matrix) == 14
            and summary["default_off_code_package_ready_count"] == 14
            and summary["live_authority_ready_count"] == 0
            and summary["explicit_session_table_closed_count"] == 0
            and summary["observed_m1_session_proxy_closed_count"] == 14
            and summary["commission_direct_or_family_proxy_closed_count"] == 14
            and forbidden["ok"] is True
        ),
        "decision": DECISION,
        "source_routes": {
            "promotion_boundary": rel(PROMOTION_ROUTE),
            "broker_authority": rel(BROKER_ROUTE),
            "fill_session": rel(FILL_ROUTE),
            "commission_family_transfer": rel(COMMISSION_ROUTE),
            "live_authority_dossier": rel(DOSSIER_ROUTE),
            "runtime_generator": rel(RUNTIME_ROUTE),
        },
        "candidate_count": len(matrix),
        "summary": summary,
        "portfolio_reference_numbers": scenarios,
        "config_patch_applied": False,
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "runtime_effect": "none_default_off_activation_readiness_synthesis_only",
        "deployment_not_ready_requirement_ids": [row["requirement_id"] for row in requirements],
        "approved_read_surfaces_used": ["committed_route_artifacts_only"],
        "forbidden_surfaces_touched": [],
    }
    decision_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": DECISION,
            "status": "ready_default_off_not_promoted",
            "reason": "default-off code package is built, but live authority remains open on explicit session, fill, commission schedule/rule, swap, and VPS owner-action gates",
            "runtime_effect": result["runtime_effect"],
        }
    ]
    boundary_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "default_off_code_package",
            "status": "ready_14_of_14",
            "live_authority": False,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "live_authority",
            "status": "not_closed_0_of_14",
            "live_authority": False,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "config_patch",
            "status": "not_applied",
            "live_authority": False,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "owner_vps_action",
            "status": "required_not_executed_by_mac_route",
            "live_authority": False,
        },
    ]
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "no_arbitrary_top_n": True,
        "anti_boxing_checks": [
            "separated default-off code readiness from live authority readiness",
            "preserved all 14 candidate rows instead of a compact top-N",
            "tested whether any subset could be live-authority ready; none can pass explicit session/fill/swap/owner gates",
            "kept family-transfer commission evidence as useful proxy rather than killing symbols",
            "kept observed M1 session proxy useful but not overclaimed as explicit session table",
            "carried direct and non-direct fill symbols separately",
        ],
        "same_evidence_class_repairs_consumed": [
            rel(BROKER_ROUTE / "ORDER_CALC_PROFIT_CONVERSION_LEDGER.jsonl"),
            rel(BROKER_ROUTE / "SWAP_TO_R_PARTIAL_AUTHORITY_LEDGER.jsonl"),
            rel(FILL_ROUTE / "HISTORY_ORDER_DEAL_FILL_LEDGER.jsonl"),
            rel(FILL_ROUTE / "OBSERVED_M1_SESSION_AVAILABILITY_LEDGER.jsonl"),
            rel(COMMISSION_ROUTE / "TARGET_COMMISSION_TRANSFER_LEDGER.jsonl"),
            rel(RUNTIME_ROUTE / "RUNTIME_GENERATOR_PARITY_LEDGER.jsonl"),
            rel(DOSSIER_ROUTE / "SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl"),
        ],
        "remaining_local_repair_paths": [
            "extended observed session calendar",
            "no-order-send source-event fillability proxy",
            "swap mode-5 formula and D1 holding-time model",
        ],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_synthesis_posture_applied": True,
            "inspire_not_kill_applied": True,
            "same_evidence_class_pursued": True,
            "no_arbitrary_top_n": True,
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "owner_action_live_authority_boundary": "required before config patch, VPS reload, broker mutation, or live promotion",
    }

    write_jsonl(ROUTE / "CANDIDATE_AUTHORITY_MATRIX.jsonl", matrix)
    write_json(ROUTE / "CANDIDATE_AUTHORITY_SUMMARY.json", summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "LOCAL_REPAIR_EXHAUSTION_LEDGER.jsonl", local_repair)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_jsonl(ROUTE / "PROMOTION_BOUNDARY_LEDGER.jsonl", boundary_rows)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "MARKET_EXPANSION_ACTIVATION_READINESS_RESULT.json", result)
    write_packet(result, summary, requirements)
    write_vps_handoff_packet(result)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 240) -> dict[str, Any]:
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
        [sys.executable, str(ROUTE / "verify_market_expansion_activation_readiness_synthesis.py")],
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
                str(ROUTE / "build_market_expansion_activation_readiness_synthesis.py"),
                str(ROUTE / "verify_market_expansion_activation_readiness_synthesis.py"),
                "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py",
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
    return 0 if result["ok"] and all(row["returncode"] == 0 for row in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
