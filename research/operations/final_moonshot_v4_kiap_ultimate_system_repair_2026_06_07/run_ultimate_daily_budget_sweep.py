from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    CampaignConfig,
    REPAIRED_PENDING_EXPIRY_MINUTES,
    atomic_write_json,
    build_source_package,
    load_config,
    run_campaign,
    summarize_campaign,
    utc_now,
)


ROUTE = Path(__file__).resolve().parent
PROBE_DAY = "2026-04-21"
CAPS: tuple[int | None, ...] = (None, 6, 8, 10, 12, 14, 16, 20)


def _json_clone(payload: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, default=str))


def _config_for_cap(base_config: Mapping[str, Any], cap: int | None) -> dict[str, Any]:
    config = _json_clone(base_config)
    runtime = config.setdefault("gtos_vnext_runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
        config["gtos_vnext_runtime"] = runtime
    runtime["scheduler_v4_best_trade_allocator_daily_risk_order_budget_enabled"] = cap is not None
    if cap is None:
        runtime.pop("scheduler_v4_best_trade_allocator_max_risk_orders_per_day", None)
    else:
        runtime["scheduler_v4_best_trade_allocator_max_risk_orders_per_day"] = int(cap)
    return config


def _risk_reason_counts(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("risk_decision_reason") or "missing")
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def main() -> int:
    base_config = load_config(REPO_ROOT / "config/agent_config.yaml")
    source_package = build_source_package((PROBE_DAY,))
    output: dict[str, Any] = {
        "schema_version": "ultimate_daily_risk_order_budget_sweep_v1",
        "generated_at_utc": utc_now(),
        "route_id": "final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07",
        "probe_day": PROBE_DAY,
        "source_package_primary_hydration_complete": source_package.get(
            "primary_hydration_complete"
        ),
        "missing_symbols": source_package.get("missing_symbols"),
        "variant_surface": {
            "sweep_use": "post_dynamic_allocator_count_circuit_breaker_diagnostic_only",
            "trade_count_policy": "optimizer_output_not_primary_control",
            "static_count_cap_policy": "disabled_in_active_config_unless_additive_after_dynamic_allocator",
            "dynamic_daily_drawdown_budget_allocator_enabled": (
                (base_config.get("gtos_vnext_runtime") or {}).get(
                    "scheduler_v4_best_trade_allocator_dynamic_daily_drawdown_budget_enabled"
                )
                if isinstance(base_config.get("gtos_vnext_runtime"), Mapping)
                else None
            ),
            "partial_exception_origin_families": (
                (base_config.get("gtos_vnext_runtime") or {}).get(
                    "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
                )
                if isinstance(base_config.get("gtos_vnext_runtime"), Mapping)
                else None
            ),
            "selector_v4_admission_quality_guard_enabled": (
                (base_config.get("gtos_vnext_runtime") or {}).get(
                    "selector_v4_admission_quality_guard_enabled"
                )
                if isinstance(base_config.get("gtos_vnext_runtime"), Mapping)
                else None
            ),
            "prop_safe_selector_internal_daily_overlay_enabled": (
                (base_config.get("gtos_vnext_runtime") or {}).get(
                    "prop_safe_selector_internal_daily_overlay_enabled"
                )
                if isinstance(base_config.get("gtos_vnext_runtime"), Mapping)
                else None
            ),
        },
        "caps": [],
        "status": "not_run",
    }
    if source_package.get("primary_hydration_complete") is not True:
        output["status"] = "not_run_primary_hydration_incomplete"
        atomic_write_json(ROUTE / "ULTIMATE_DAILY_RISK_ORDER_BUDGET_SWEEP.json", output)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 1

    for cap in CAPS:
        campaign = CampaignConfig(
            name=f"daily_budget_sweep_{cap if cap is not None else 'disabled'}",
            phase="ultimate_daily_budget_sweep",
            days=(PROBE_DAY,),
            pending_expiry_minutes=REPAIRED_PENDING_EXPIRY_MINUTES,
            use_repaired_pending_expiry=True,
            partial_be_runner=False,
        )
        result = run_campaign(
            campaign=campaign,
            config=_config_for_cap(base_config, cap),
            sources=source_package["sources"],
        )
        ledgers = result["ledgers"]
        summary = summarize_campaign(result, phase="ultimate_daily_budget_sweep")
        output["caps"].append(
            {
                "max_risk_orders_per_day": cap,
                "campaign_summary": summary,
                "risk_decision_reason_counts": _risk_reason_counts(
                    ledgers.get("order", [])
                ),
                "accepted_order_rows": len(
                    [
                        row
                        for row in ledgers.get("order", [])
                        if row.get("risk_decision") in {"trade", "reduce-risk"}
                    ]
                ),
                "daily_budget_exhausted_order_rows": len(
                    [
                        row
                        for row in ledgers.get("order", [])
                        if row.get("risk_decision_reason")
                        == "daily_risk_order_budget_exhausted"
                    ]
                ),
            }
        )
        atomic_write_json(ROUTE / "ULTIMATE_DAILY_RISK_ORDER_BUDGET_SWEEP.json", output)

    output["status"] = "completed"
    output["best_by_net_proxy_r"] = max(
        output["caps"],
        key=lambda row: row["campaign_summary"]["net_proxy_r"],
    )
    atomic_write_json(ROUTE / "ULTIMATE_DAILY_RISK_ORDER_BUDGET_SWEEP.json", output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
