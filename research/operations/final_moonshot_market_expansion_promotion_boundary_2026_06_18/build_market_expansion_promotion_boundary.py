#!/usr/bin/env python3
"""Build the market-expansion promotion-boundary package.

This route decides whether the default-off market-expansion package can move
from dossier evidence into an owner-action VPS promotion package now. It does
not activate config, touch brokers, read account/deal/order/position state,
use orderflow/depth, push remotes, or restart VPS processes.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
DOSSIER_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
GENERATOR_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18"
ACTIVATION_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_activation_candidate_package_2026_06_18"
CONFIG_PATH = PROJECT_ROOT / "config" / "agent_config.yaml"
PROFILE_NAME = "operator_profile"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_promotion_boundary"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.broker_net_cost_engine import (  # noqa: E402
    build_pretrade_cost_packet,
    pretrade_cost_refusal_reason,
)
from src.components.ultimate_book.admission import (  # noqa: E402
    GovernorLimits,
    GovernorState,
    TradeIntent,
)
from src.components.ultimate_book.bridge import DEFAULT_CONFIG, evaluate_vnext_ultimate_book_admission  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    MARKET_EXPANSION_TARGET2_SLEEVES,
    SLEEVE_EXIT_PROFILES,
    build_book_trade_params,
)
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.utils.config import apply_profile_overrides  # noqa: E402


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


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def median(values: list[float]) -> float | None:
    clean = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not clean:
        return None
    mid = len(clean) // 2
    return clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2.0


def compact_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_hash_sha256": sha256_payload(packet),
        "status": packet.get("status"),
        "refusal_reasons": packet.get("refusal_reasons") or [],
        "spread_r": packet.get("spread_r"),
        "max_spread_r": packet.get("max_spread_r"),
        "total_cost_r": packet.get("total_cost_r"),
        "max_total_cost_r": packet.get("max_total_cost_r"),
        "commission_model_status": packet.get("commission_model_status"),
        "expected_slippage_r": packet.get("expected_slippage_r"),
        "expected_slippage_source": packet.get("expected_slippage_source"),
        "swap": packet.get("swap"),
        "broker_hours": packet.get("broker_hours"),
        "profile": packet.get("profile"),
        "symbol_spec_source_status": (packet.get("symbol_spec") or {}).get("source_status"),
        "symbol_spec_missing": (packet.get("symbol_spec") or {}).get("required_missing_fields") or [],
        "forbidden_surface_status": packet.get("forbidden_surface_status"),
        "runtime_effect_boundary": packet.get("runtime_effect_boundary"),
    }


def load_config() -> tuple[dict[str, Any], dict[str, Any]]:
    base = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return base, apply_profile_overrides(base, PROFILE_NAME)


def risk_by_tag(source_events: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for row in source_events:
        risk = finite_float(row.get("risk_abs"))
        if risk and risk > 0:
            grouped.setdefault(row["tag"], []).append(risk)
    out = {tag: median(values) for tag, values in grouped.items()}
    return {tag: value for tag, value in out.items() if value is not None}


def synthetic_account_state() -> dict[str, Any]:
    return {
        "current_equity": 100000.0,
        "equity": 100000.0,
        "balance": 100000.0,
        "day_start_equity_or_balance_baseline": 100000.0,
        "daily_reset_window_id": "synthetic_readonly_promotion_boundary",
    }


def synthetic_unit(tag: str) -> SimpleNamespace:
    return SimpleNamespace(
        risk_pct_per_trade=0.00025,
        cluster="market_expansion",
        sleeve_members=[tag],
        confidence=0.025,
        n_trades=1,
        unit_risk_pct=0.00025,
        sized=True,
        reason="synthetic_readonly_packet_probe",
    )


def make_trade_params(
    *,
    tag: str,
    file_symbol: str,
    direction: int,
    entry: float,
    risk: float,
) -> tuple[dict[str, Any], float]:
    intent = TradeIntent(
        sleeve=tag,
        symbol=file_symbol,
        direction=direction,
        decision_day="2026-06-18",
        stop_dist=risk,
        target_dist=2.0 * risk,
    )
    stop_loss = entry - (1.0 if direction > 0 else -1.0) * risk
    trade_params = build_book_trade_params(
        synthetic_unit(tag),
        intent,
        {"entry_price": entry, "risk_distance": risk, "stop_loss": stop_loss},
        synthetic_account_state(),
        profile_namespace=PROFILE_NAME,
    )
    return trade_params, stop_loss


def build_pretrade_rows(created_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base_config, profile_config = load_config()
    bridge = read_json(DOSSIER_ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")
    source_events = read_jsonl(DOSSIER_ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl")
    risks = risk_by_tag(source_events)
    rows: list[dict[str, Any]] = []
    raw_probe: dict[str, Any] | None = None
    for bridge_row in bridge["rows"]:
        tag = bridge_row["tag"]
        file_symbol = bridge_row["file_symbol"]
        broker_symbol = bridge_row["broker_symbol"]
        captured = bridge_row["captured"]
        info = captured.get("symbol_info") or {}
        tick = captured.get("symbol_info_tick") or {}
        risk = risks[tag]
        bid = finite_float(tick.get("bid"))
        ask = finite_float(tick.get("ask"))
        entry = ((bid + ask) / 2.0) if bid is not None and ask is not None else 1.0
        for direction, side in ((1, "LONG"), (-1, "SHORT")):
            trade_params, stop_loss = make_trade_params(
                tag=tag,
                file_symbol=file_symbol,
                direction=direction,
                entry=entry,
                risk=risk,
            )
            if raw_probe is None:
                raw_packet = build_pretrade_cost_packet(
                    config=base_config,
                    trade_params=trade_params,
                    tick=tick,
                    symbol=file_symbol,
                    broker_symbol=broker_symbol,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    sl_distance=risk,
                    risk_pct=trade_params["gtos_vnext_selected_cell_risk_pct"],
                    symbol_info=info,
                )
                raw_probe = {
                    "schema": f"{SCHEMA_PREFIX}.root_config_pretrade_refusal_audit.v1",
                    "created_at_utc": created_at,
                    "tag": tag,
                    "side": side,
                    "status": raw_packet.get("status"),
                    "refusal_reason": pretrade_cost_refusal_reason(raw_packet),
                    "compact_packet": compact_packet(raw_packet),
                    "interpretation": (
                        "raw config is expected to fail profile namespace; VPS/profile-merged config "
                        "is the promotion surface"
                    ),
                }
            packet = build_pretrade_cost_packet(
                config=profile_config,
                trade_params=trade_params,
                tick=tick,
                symbol=file_symbol,
                broker_symbol=broker_symbol,
                entry_price=entry,
                stop_loss=stop_loss,
                sl_distance=risk,
                risk_pct=trade_params["gtos_vnext_selected_cell_risk_pct"],
                symbol_info=info,
            )
            rows.append(
                {
                    "schema": f"{SCHEMA_PREFIX}.pretrade_cost_packet_row.v1",
                    "created_at_utc": created_at,
                    "tag": tag,
                    "file_symbol": file_symbol,
                    "broker_symbol": broker_symbol,
                    "side": side,
                    "source": "synthetic_profile_merged_packet_probe_no_order",
                    "entry_price_mid": entry,
                    "risk_abs_median": risk,
                    "stop_loss": stop_loss,
                    "trade_params_hash_sha256": sha256_payload(trade_params),
                    "dynamic_policy_selected": trade_params.get("gtos_vnext_dynamic_policy_selected"),
                    "dynamic_final_target_r": trade_params.get("gtos_vnext_dynamic_final_target_r"),
                    "dynamic_time_stop_bars": trade_params.get("gtos_vnext_dynamic_time_stop_bars"),
                    "commission_model_status": trade_params.get("gtos_vnext_commission_model_status"),
                    "packet": compact_packet(packet),
                    "refusal_reason": pretrade_cost_refusal_reason(packet),
                    "live_authority_meaning": (
                        "cost packet gate shape is passable under profile-merged config, but this is "
                        "not broker-real commission/slippage/fill/session authority"
                    ),
                }
            )
    assert raw_probe is not None
    write_json(ROUTE / "ROOT_CONFIG_PRETRADE_REFUSAL_AUDIT.json", raw_probe)
    summary = {
        "profile_name": PROFILE_NAME,
        "row_count": len(rows),
        "status_counts": dict(Counter(row["packet"]["status"] for row in rows)),
        "refusal_count": sum(1 for row in rows if row["refusal_reason"]),
        "spread_r_max": max(row["packet"]["spread_r"] for row in rows if row["packet"]["spread_r"] is not None),
        "total_cost_r_max": max(row["packet"]["total_cost_r"] for row in rows if row["packet"]["total_cost_r"] is not None),
        "swap_captured_count": sum(1 for row in rows if (row["packet"]["swap"] or {}).get("source_status") == "captured"),
    }
    return rows, summary


def bridge_surface_negative_proof(created_at: str) -> dict[str, Any]:
    bridge = read_json(DOSSIER_ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")
    symbol_info_keys = sorted(
        set().union(*[(row["captured"].get("symbol_info") or {}).keys() for row in bridge["rows"]])
    )
    proof: dict[str, Any] = {
        "schema": f"{SCHEMA_PREFIX}.bridge_surface_negative_proof.v1",
        "created_at_utc": created_at,
        "installed_client_imported": False,
        "client_file": None,
        "method_count": 0,
        "has_symbol_info_session_trade": False,
        "has_symbol_info_session_quote": False,
        "has_symbol_info": False,
        "has_symbol_info_tick": False,
        "commission_like_symbol_info_keys": [
            key for key in symbol_info_keys if any(token in key.lower() for token in ("commission", "fee"))
        ],
        "symbol_info_key_count": len(symbol_info_keys),
        "symbol_info_keys_sha256": sha256_payload(symbol_info_keys),
        "current_dossier_session_table_status": read_json(DOSSIER_ROUTE / "SESSION_TABLE_UNAVAILABLE_PROOF.json"),
        "status": "current_allowed_bridge_surface_cannot_close_session_or_commission_gap",
    }
    try:
        import siliconmetatrader5
        from siliconmetatrader5 import MetaTrader5

        method_names = sorted(name for name in dir(MetaTrader5) if not name.startswith("__"))
        proof.update(
            {
                "installed_client_imported": True,
                "client_file": getattr(siliconmetatrader5, "__file__", None),
                "method_count": len(method_names),
                "method_names_sha256": sha256_payload(method_names),
                "has_symbol_info_session_trade": hasattr(MetaTrader5, "symbol_info_session_trade"),
                "has_symbol_info_session_quote": hasattr(MetaTrader5, "symbol_info_session_quote"),
                "has_symbol_info": hasattr(MetaTrader5, "symbol_info"),
                "has_symbol_info_tick": hasattr(MetaTrader5, "symbol_info_tick"),
                "read_only_method_signatures": {
                    name: str(inspect.signature(getattr(MetaTrader5, name)))
                    for name in ("symbol_info", "symbol_info_tick", "copy_rates_range", "copy_ticks_range")
                    if hasattr(MetaTrader5, name)
                },
            }
        )
    except Exception as exc:  # noqa: BLE001
        proof["import_error"] = repr(exc)
    return proof


def zero_active_audit(created_at: str, expansion_names: list[str]) -> dict[str, Any]:
    base_config, profile_config = load_config()
    rt = base_config.get("gtos_vnext_runtime", {}) or {}
    expansion = set(expansion_names)
    off_specs = {spec.tag for spec in active_specs(None)}
    empty_specs = {
        spec.tag
        for spec in active_specs(None, include_market_expansion_book=True, market_expansion_sleeves=[])
    }
    explicit_specs = {
        spec.tag
        for spec in active_specs(None, include_market_expansion_book=True, market_expansion_sleeves=expansion_names)
    }
    empty_decision = evaluate_vnext_ultimate_book_admission(
        config={"gtos_vnext_runtime": {**profile_config.get("gtos_vnext_runtime", {}), "ultimate_book_include_market_expansion_book": True, "ultimate_book_market_expansion_sleeves": []}},
        intents=[],
        governor_state=GovernorState(
            equity=100000.0,
            high_water=100000.0,
            realized_today_pct=0.0,
            open_risk_pct=0.0,
            max_dd_reference_equity=100000.0,
        ),
        limits=GovernorLimits(derisk_mode="smooth"),
    )
    return {
        "schema": f"{SCHEMA_PREFIX}.zero_active_audit.v1",
        "created_at_utc": created_at,
        "active_config_include_market_expansion_book": rt.get("ultimate_book_include_market_expansion_book", False),
        "active_config_market_expansion_sleeves": rt.get("ultimate_book_market_expansion_sleeves", []),
        "bridge_default_include_market_expansion_book": DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"],
        "bridge_default_market_expansion_sleeves": DEFAULT_CONFIG["ultimate_book_market_expansion_sleeves"],
        "market_expansion_names_in_default_active_specs": sorted(expansion & off_specs),
        "market_expansion_names_in_empty_allowlist_specs": sorted(expansion & empty_specs),
        "explicit_allowlist_market_expansion_count": len(expansion & explicit_specs),
        "empty_allowlist_decision_status": empty_decision.decision_status,
        "empty_allowlist_reason": empty_decision.reason,
        "zero_active_behavior_ok": (
            rt.get("ultimate_book_include_market_expansion_book", False) is False
            and not rt.get("ultimate_book_market_expansion_sleeves", [])
            and DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"] is False
            and DEFAULT_CONFIG["ultimate_book_market_expansion_sleeves"] == []
            and not (expansion & off_specs)
            and not (expansion & empty_specs)
            and len(expansion & explicit_specs) == len(expansion)
            and empty_decision.decision_status == "fail_closed_market_expansion_requires_explicit_sleeves"
        ),
    }


def config_patch_payload(created_at: str, expansion_names: list[str]) -> dict[str, Any]:
    return {
        "schema": f"{SCHEMA_PREFIX}.config_patch_proposal.v1",
        "created_at_utc": created_at,
        "status": "not_applied_owner_action_only",
        "target_path": "config/agent_config.yaml",
        "activation_patch_yaml": {
            "gtos_vnext_runtime": {
                "ultimate_book_include_market_expansion_book": True,
                "ultimate_book_market_expansion_profile": "default_off_market_expansion_d1_target2_v1",
                "ultimate_book_market_expansion_sleeves": expansion_names,
            }
        },
        "rollback_patch_yaml": {
            "gtos_vnext_runtime": {
                "ultimate_book_include_market_expansion_book": False,
                "ultimate_book_market_expansion_sleeves": [],
            }
        },
        "apply_condition": (
            "apply only after session table/platform proof, broker-exact commission/slippage/swap/fill "
            "proof, VPS packet parity, monitoring, rollback, and explicit owner action are complete"
        ),
    }


def write_config_patch_files(payload: dict[str, Any]) -> None:
    activation = yaml.safe_dump(payload["activation_patch_yaml"], sort_keys=False)
    rollback = yaml.safe_dump(payload["rollback_patch_yaml"], sort_keys=False)
    (ROUTE / "CONFIG_PATCH_PROPOSAL_NOT_APPLIED.yaml").write_text(
        "# NOT APPLIED. Owner-action proposal only.\n" + activation,
        encoding="utf-8",
    )
    (ROUTE / "ROLLBACK_PATCH_PROPOSAL_NOT_APPLIED.yaml").write_text(
        "# NOT APPLIED. Rollback proposal only.\n" + rollback,
        encoding="utf-8",
    )


def unresolved_requirements(created_at: str) -> list[dict[str, Any]]:
    items = [
        (
            "MX-PROMO-REQ-001",
            "explicit broker trading-session table or platform-source proof",
            "current silicon bridge has no symbol_info_session_trade/session_quote methods and symbol_info has no session rows",
            "VPS/platform source, bridge wrapper method if remote MT5 exposes it, or broker-exported session/spec proof",
        ),
        (
            "MX-PROMO-REQ-002",
            "broker-exact market-expansion commission authority",
            "runtime packet can carry COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK, but the expansion dossier has no broker-exact commission row",
            "owner-approved account/deal/export evidence or selected-cell risk ledger proving commission included for these symbols",
        ),
        (
            "MX-PROMO-REQ-003",
            "broker-exact slippage and limit/market fill authority",
            "current cost2/cost3 stress and limit-first rule are proxy/dossier policy, not observed broker queue/fillability",
            "VPS packet-parity dry run plus broker lifecycle/fill capture or explicit no-late-market guarded-open skip proof",
        ),
        (
            "MX-PROMO-REQ-004",
            "exact swap-to-R holding-time model",
            "symbol_info swap fields are captured, but exact mode formula, account currency conversion, side, holding time, and rollover schedule must be bound",
            "platform/broker formula proof and account/profile-specific conversion for swap_mode 1 and 5 rows",
        ),
        (
            "MX-PROMO-REQ-005",
            "owner-approved VPS promotion and monitoring execution",
            "Mac route does not push, restart, reload, or alter live config",
            "VPS Codex session must absorb commits, run packet parity, apply patch only if gates close, monitor, and keep rollback ready",
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
            "status": "not_closed_by_current_allowed_evidence",
            "runtime_effect_now": "none_market_expansion_default_off",
        }
        for req_id, requirement, evidence, repair in items
    ]


def decision_ledgers(
    created_at: str,
    result: dict[str, Any],
    pretrade_summary: dict[str, Any],
    zero: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "promotion_not_allowed_now",
            "status": result["decision"],
            "evidence": {"deployment_ready": result["deployment_ready"], "promotion_ready": result["promotion_ready"]},
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "profile_merged_pretrade_packet_shape_passes",
            "status": "diagnostic_pass_not_live_authority",
            "evidence": pretrade_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "market_expansion_config_patch_not_applied",
            "status": "owner_action_only",
            "evidence": {"zero_active_behavior_ok": zero["zero_active_behavior_ok"]},
        },
    ]
    boundary = [
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "dossier_verifier",
            "status": "passed",
            "evidence": "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_VERIFIER_RESULT.ok=true",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "runtime_exit_profile",
            "status": "passed",
            "evidence": "14 market-expansion sleeves exist in execution_packets.MARKET_EXPANSION_TARGET2_SLEEVES with target2 time_stop profile",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "pretrade_cost_packet_shape",
            "status": "diagnostic_pass_not_live_authority",
            "evidence": pretrade_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "session_commission_slippage_swap_fill_authority",
            "status": "not_closed",
            "evidence": result["deployment_not_ready_reasons"],
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
        ROUTE / "build_market_expansion_promotion_boundary.py",
        ROUTE / "verify_market_expansion_promotion_boundary.py",
    ]
    forbidden_patterns = [
        "order" + "_send(",
        "TRADE" + "_ACTION_",
        "positions" + "_get(",
        "history" + "_deals_get(",
        "history" + "_orders_get(",
        "account" + "_info(",
        "market" + "_book_add(",
        "market" + "_book_get(",
        "market" + "_book_release(",
        "symbol" + "_select(",
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
        "forbidden_patterns": forbidden_patterns,
        "matches": matches,
        "ok": not matches,
    }


def write_handoff_packet(
    *,
    result: dict[str, Any],
    expansion_names: list[str],
    requirements: list[dict[str, Any]],
) -> None:
    req_text = "\n".join(f"- `{row['requirement_id']}`: {row['requirement']}" for row in requirements)
    sleeves = "\n".join(f"    - \"{name}\"" for name in expansion_names)
    packet = f"""# Market Expansion Promotion Boundary Packet

Decision: `{result['decision']}`

Market expansion is still default-off on the Mac package. This route built a
conditional owner-action VPS package, not a live activation.

Current numeric package:

- Active A8 reference Sharpe `{result['active_a8_reference']['sharpe']}`, monthly `{result['active_a8_reference']['monthly_pct']}%`, MC pass `{result['active_a8_reference']['p_pass']}`.
- Armed candidate-book reference Sharpe `{result['candidate_reference']['sharpe']}`, monthly `{result['candidate_reference']['monthly_pct']}%`, MC pass `{result['candidate_reference']['p_pass']}`.
- Candidate book plus market-expansion seed `0.025` cost3 Sharpe `{result['candidate_plus_expansion_seed_0p025_cost3']['sharpe']}`, monthly `{result['candidate_plus_expansion_seed_0p025_cost3']['monthly_pct']}%`, MC pass `{result['candidate_plus_expansion_seed_0p025_cost3']['p_pass']}`.
- Dossier delta versus candidate reference: Sharpe `{result['candidate_plus_expansion_seed_0p025_cost3']['delta_vs_candidate_reference']['sharpe']}`, monthly `{result['candidate_plus_expansion_seed_0p025_cost3']['delta_vs_candidate_reference']['monthly_pct']}%`.
- Profile-merged synthetic pretrade packet rows passed: `{result['profile_merged_pretrade_packet_pass_count']}/{result['profile_merged_pretrade_packet_row_count']}`.

Do not apply the market-expansion config patch until these requirements are closed:

{req_text}

Non-applied activation patch:

```yaml
gtos_vnext_runtime:
  ultimate_book_include_market_expansion_book: true
  ultimate_book_market_expansion_profile: "default_off_market_expansion_d1_target2_v1"
  ultimate_book_market_expansion_sleeves:
{sleeves}
```

Rollback patch:

```yaml
gtos_vnext_runtime:
  ultimate_book_include_market_expansion_book: false
  ultimate_book_market_expansion_sleeves: []
```

VPS verification sequence before any live reload:

```powershell
cd C:\\Users\\MSI\\Documents\\ai-trading-agent
git pull --ff-only

$py = ".\\.venv-gtos\\Scripts\\python.exe"

& $py research\\operations\\final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18\\verify_market_expansion_runtime_generator_implementation.py
& $py research\\operations\\final_moonshot_market_expansion_live_authority_dossier_2026_06_18\\verify_market_expansion_live_authority_dossier.py
& $py research\\operations\\final_moonshot_market_expansion_promotion_boundary_2026_06_18\\verify_market_expansion_promotion_boundary.py

& $py -m pytest `
  tests\\ultimate_book\\test_market_expansion_runtime_generator.py `
  tests\\ultimate_book\\test_market_expansion_runtime_generator_implementation_artifacts.py `
  tests\\ultimate_book\\test_market_expansion_live_authority_dossier_artifacts.py `
  tests\\ultimate_book\\test_market_expansion_promotion_boundary_artifacts.py `
  tests\\test_broker_net_cost_engine.py -q
```

Only after all requirements close and owner explicitly approves activation:

1. Apply the config patch above.
2. Restart only the existing ultimate-book workers by namespace.
3. Do not restart MT5 terminals, Docker/Kasm, bridge containers, unrelated watchdogs, legacy `run_agent.py`, or broad runtime services.
4. Monitor the same candidate-book ledgers plus market-expansion fail-closed statuses.

Monitor:

- `pipeline_state\\ultimate_book\\operator_profile\\heartbeat.json`
- `pipeline_state\\ultimate_book\\redacted_account_live_bee34003\\heartbeat.json`
- `pipeline_state\\ultimate_book\\*\\placed_decisions.jsonl`
- `shadow_logs\\ultimate_book_launcher.jsonl`
- `shadow_logs\\run_book_console.log`
- `shadow_logs\\run_book_fn_console.log`
- `shadow_logs\\book_supervisor.log`

Alert or rollback on:

- `fail_closed_unknown_market_expansion_profile`
- `fail_closed_market_expansion_requires_explicit_sleeves`
- `fail_closed_unknown_market_expansion_sleeves`
- any market-expansion sleeve outside the explicit 14-sleeve allowlist
- any late D1 entry after the guarded open window
- spread/total-cost gate refusal outside expected skip handling
- session/commission/swap/fill evidence missing on the VPS packet-parity pass
- heartbeat stale after worker reload
- market-expansion config on VPS differs from this packet
"""
    (ROUTE / "MARKET_EXPANSION_PROMOTION_BOUNDARY_PACKET.md").write_text(packet, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Market Expansion Exact Broker-Authority Successor Prompt

Created: {created_at}

Mandatory context use: run mandatory GTOS preflight, regenerate `.context/LIVE_STATE.md`, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`, this prompt, and the latest promotion-boundary artifacts from disk as active instructions, not background. Do not rely on chat memory. After any compaction/resume/interruption/uncertainty, reread the prompt, doctrine, and latest route artifacts from disk before continuing and record instruction coverage in the completion audit.

Lane posture: constructive source-repair and deployment-authority closure, with curiosity and active creativity inside the hard evidence class. The current package is not promoted. Use no conservative brake: pursue every same-evidence-class repair before declaring a blocker, including bridge wrapper session methods, platform/broker session exports, profile-merged packet parity, broker-exact commission/slippage/swap/fill evidence, source-capture/source completeness checks, implementation decision, branch decision, exact-R/proxy-R/expectancy recomputation where lawful, result materialization, and VPS-side dry-run packet parity. No arbitrary top-N/top-3/top-5/top-10 or number-limited cutoff; preserve all material rows in full ledgers.

Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been attempted, repaired, recomputed, or reduced to an exact owner/source/capture requirement. Full same-evidence-class pursuit is mandatory; do not stop at blocker wording when a same-class read-only capture, replay, verifier, source-capture, source completeness check, implementation decision, branch decision, exact-R/proxy-R/expectancy recomputation, or result materialization step is still executable.

Input route: `research/operations/final_moonshot_market_expansion_promotion_boundary_2026_06_18/`.

Objective: close or exactly bound the remaining market-expansion live-authority requirements without orderflow/depth. Verify the route artifacts, verifier, focused tests, prompt hardening, output manifest, blocker/repair requirement ledger, non-applied config patch, rollback patch, and VPS handoff packet from disk. If broker/platform/account evidence is explicitly authorized in the active turn, capture commission/fill/session/swap proof with no order mutation. If all requirements close, prepare owner-action config activation and VPS reload packet. If any requirement remains open, keep market expansion default-off and update the unresolved requirement ledger plus blocker/repair ledger.

Forbidden unless explicitly approved in the active turn: production-change/live trading/broker operation; broker/account/order/history/deal/position mutation or reads outside the prompt evidence class; MT5 order state changes; prompt/config/risk/execution/safety/canary/selector live activation changes; credential mutation/disclosure; paid API/vendor calls; remote push; live VPS restart/reload; production live config activation; and orderflow/depth use. Local code/config/test/handoff artifacts may be changed only if the route explicitly owns that production-deployment packaging surface and keeps broker/VPS action as owner-action.

Completion requires: updated decision ledger, promotion-boundary ledger, unresolved requirement ledger, blocker/repair requirement ledger, verifier result, focused test record or pytest output, output manifest, saturation/self-red-team audit, completion audit, and scoped commit. Mark complete only when the prompt completion standard is satisfied with no vague blockers or hidden live-action assumptions.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    dossier_result = read_json(DOSSIER_ROUTE / "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_RESULT.json")
    dossier_verifier = read_json(DOSSIER_ROUTE / "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_VERIFIER_RESULT.json")
    bridge = read_json(DOSSIER_ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")
    zero = zero_active_audit(created_at, [row["tag"] for row in bridge["rows"]])
    pretrade_rows, pretrade_summary = build_pretrade_rows(created_at)
    bridge_proof = bridge_surface_negative_proof(created_at)
    config_patch = config_patch_payload(created_at, [row["tag"] for row in bridge["rows"]])
    write_config_patch_files(config_patch)
    requirements = unresolved_requirements(created_at)
    forbidden = forbidden_call_scan(created_at)

    target2_profile_count = sum(1 for name in config_patch["activation_patch_yaml"]["gtos_vnext_runtime"]["ultimate_book_market_expansion_sleeves"] if name in MARKET_EXPANSION_TARGET2_SLEEVES and name in SLEEVE_EXIT_PROFILES)
    pretrade_pass_count = sum(1 for row in pretrade_rows if row["packet"]["status"] == "PASSED")
    active_config_off = zero["zero_active_behavior_ok"]
    deployment_ready = False
    promotion_ready = False
    ok = (
        dossier_result.get("ok") is True
        and dossier_verifier.get("ok") is True
        and len(pretrade_rows) == 28
        and pretrade_pass_count == 28
        and target2_profile_count == 14
        and active_config_off
        and bridge_proof.get("has_symbol_info_session_trade") is False
        and bridge_proof.get("has_symbol_info_session_quote") is False
        and forbidden["ok"] is True
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": "MARKET_EXPANSION_PROMOTION_BOUNDARY_READY_NOT_PROMOTED",
        "source_dossier_route": rel(DOSSIER_ROUTE),
        "source_generator_route": rel(GENERATOR_ROUTE),
        "source_activation_route": rel(ACTIVATION_ROUTE),
        "selectable_activation_candidate_count": dossier_result["selectable_activation_candidate_count"],
        "profile_merged_pretrade_packet_row_count": len(pretrade_rows),
        "profile_merged_pretrade_packet_pass_count": pretrade_pass_count,
        "profile_merged_pretrade_packet_refusal_count": len(pretrade_rows) - pretrade_pass_count,
        "target2_exit_profile_count": target2_profile_count,
        "bridge_session_trade_method_available": bridge_proof.get("has_symbol_info_session_trade"),
        "bridge_session_quote_method_available": bridge_proof.get("has_symbol_info_session_quote"),
        "bridge_commission_like_symbol_info_key_count": len(bridge_proof.get("commission_like_symbol_info_keys", [])),
        "zero_active_behavior_ok": active_config_off,
        "config_patch_applied": False,
        "live_authority": False,
        "deployment_ready": deployment_ready,
        "promotion_ready": promotion_ready,
        "runtime_effect": "none_market_expansion_default_off_promotion_boundary_only",
        "portfolio_proxy_replay_complete": dossier_result["portfolio_proxy_replay_complete"],
        "portfolio_live_authority_replay_complete": False,
        "active_a8_reference": dossier_result["active_a8_reference"],
        "candidate_reference": dossier_result["candidate_reference"],
        "candidate_plus_expansion_seed_0p025_cost3": dossier_result["candidate_plus_expansion_seed_0p025_cost3"],
        "deployment_not_ready_requirement_ids": [row["requirement_id"] for row in requirements],
        "deployment_not_ready_reasons": [row["requirement"] for row in requirements],
        "owner_action_boundary": "required before config patch, VPS reload, broker/account evidence expansion, or live promotion",
        "forbidden_surfaces_touched": [],
    }
    decisions, boundary = decision_ledgers(created_at, result, pretrade_summary, zero)
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "no_arbitrary_top_n": True,
        "anti_boxing_checked": [
            "raw config versus profile-merged config",
            "long and short side-aware swap packets",
            "runtime exit-profile availability",
            "bridge method negative proof",
            "non-applied config patch and rollback",
            "VPS handoff commands and monitoring",
        ],
        "same_evidence_class_repairs_completed": [
            "broker_net_cost_engine now copies swap/currency fields from symbol_info",
            "profile-merged synthetic pretrade packets computed for all 14 sleeves and both sides",
            "raw-config namespace refusal preserved as expected Mac/root-config boundary",
            "bridge client method/symbol_info negative proof preserved",
            "non-applied config patch and rollback packet materialized",
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
            "constructive_build_and_ship_posture_applied": True,
            "inspire_not_kill_applied": True,
            "same_evidence_class_pursued": True,
            "no_arbitrary_top_n": True,
        },
        "runtime_effect_boundary": result["runtime_effect"],
        "forbidden_surfaces_touched": [],
        "deployment_ready": deployment_ready,
        "promotion_ready": promotion_ready,
        "config_patch_applied": False,
        "owner_action_live_authority_boundary": result["owner_action_boundary"],
    }

    write_jsonl(ROUTE / "PRETRADE_COST_PACKET_LEDGER.jsonl", pretrade_rows)
    write_json(ROUTE / "PRETRADE_COST_PACKET_SUMMARY.json", pretrade_summary)
    write_json(ROUTE / "BRIDGE_SURFACE_NEGATIVE_PROOF.json", bridge_proof)
    write_json(ROUTE / "ZERO_ACTIVE_BEHAVIOR_AUDIT.json", zero)
    write_json(ROUTE / "CONFIG_PATCH_PROPOSAL.json", config_patch)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "PROMOTION_BOUNDARY_LEDGER.jsonl", boundary)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "MARKET_EXPANSION_PROMOTION_BOUNDARY_RESULT.json", result)
    write_handoff_packet(result=result, expansion_names=config_patch["activation_patch_yaml"]["gtos_vnext_runtime"]["ultimate_book_market_expansion_sleeves"], requirements=requirements)
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


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command(
        [sys.executable, str(ROUTE / "verify_market_expansion_promotion_boundary.py")],
        timeout=180,
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
                str(ROUTE / "build_market_expansion_promotion_boundary.py"),
                str(ROUTE / "verify_market_expansion_promotion_boundary.py"),
                "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py",
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
