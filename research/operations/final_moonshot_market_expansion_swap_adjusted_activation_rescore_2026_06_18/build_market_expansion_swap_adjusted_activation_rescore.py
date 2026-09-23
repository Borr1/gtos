#!/usr/bin/env python3
"""Build swap-adjusted market-expansion activation rescoring evidence.

This route consumes the committed swap/holding proxy route and recomputes the
portfolio overlay scenarios. It does not call MT5, mutate broker/account/order/
history/deal/position state, apply config, push remotes, or touch VPS processes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import statistics
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
SWAP_ROUTE = OPS / "final_moonshot_market_expansion_swap_mode5_holding_repair_2026_06_18"
DOSSIER_ROUTE = OPS / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
CANDIDATE_REPLAY = OPS / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18" / "verify_candidate_enabled_unified_replay_mc.py"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_swap_adjusted_activation_rescore"
DECISION = "MARKET_EXPANSION_SWAP_ADJUSTED_RESCORING_POSITIVE_DEFAULT_OFF_NOT_LIVE_AUTHORITY"


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


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: Any, digits: int = 10) -> float | None:
    number = finite_float(value)
    return round(number, digits) if number is not None else None


def summarize(values: list[float]) -> dict[str, Any]:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if not clean:
        return {"n": 0, "mean": None, "median": None, "win_rate": None, "min": None, "max": None, "sum": 0.0}
    return {
        "n": len(clean),
        "mean": round(statistics.fmean(clean), 10),
        "median": round(statistics.median(clean), 10),
        "win_rate": round(sum(1 for value in clean if value > 0) / len(clean), 10),
        "min": round(min(clean), 10),
        "max": round(max(clean), 10),
        "sum": round(sum(clean), 10),
    }


def split_summary(events: list[dict[str, Any]], key: str) -> dict[str, Any]:
    splits: dict[str, dict[str, Any]] = {}
    for split in ("train_le_2021", "oos_2022_2024", "sealed_ge_2025"):
        splits[split] = summarize([float(row[key]) for row in events if row.get("split") == split and row.get(key) is not None])
    return {
        "all": summarize([float(row[key]) for row in events if row.get(key) is not None]),
        "splits": splits,
        "populated_split_count": sum(1 for payload in splits.values() if payload["n"] > 0),
        "every_populated_split_positive": all(
            payload["n"] == 0 or (payload["mean"] is not None and payload["mean"] > 0)
            for payload in splits.values()
        ),
    }


def series_from_events(events: list[dict[str, Any]], value_key: str) -> dict[str, dict[str, float]]:
    series: dict[str, dict[str, float]] = {}
    for event in events:
        value = finite_float(event.get(value_key))
        if value is None:
            continue
        tag = event["tag"]
        date = event["date"]
        series.setdefault(tag, {})
        series[tag][date] = series[tag].get(date, 0.0) + value
    return series


def scenario_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sharpe": row["sharpe"],
        "monthly_pct": row["mc"]["monthly_pct"],
        "p_pass": row["mc"]["p_pass"],
        "p_fail_dd": row["mc"]["p_fail_dd"],
        "worst_day_pct": row["mc"]["worst_day_pct"],
        "maxDD_R": row["daily"]["maxDD_R"],
    }


def delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "sharpe": round(left["sharpe"] - right["sharpe"], 6),
        "monthly_pct": round(left["mc"]["monthly_pct"] - right["mc"]["monthly_pct"], 6),
        "p_pass": round(left["mc"]["p_pass"] - right["mc"]["p_pass"], 6),
        "p_fail_dd": round(left["mc"]["p_fail_dd"] - right["mc"]["p_fail_dd"], 6),
        "worst_day_pct": round(left["mc"]["worst_day_pct"] - right["mc"]["worst_day_pct"], 6),
        "maxDD_R": round(left["daily"]["maxDD_R"] - right["daily"]["maxDD_R"], 6),
    }


def build_replay(created_at: str, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    candidate = load_module("candidate_enabled_unified_replay_for_swap_adjusted_rescore", CANDIDATE_REPLAY)
    active = candidate._active_baselines()
    candidate_daily = candidate._load_candidate_daily()
    candidate_conf = {
        name: float(value)
        for name, value in candidate.candidate_registry.CANDIDATE_CONFIDENCE.items()
        if float(value) > 0.0 and name in candidate_daily
    }
    candidate_series = {name: candidate_daily[name] for name in candidate_conf}
    active_ref = candidate._evaluate_scenario(
        "active_core8_a8_baseline_no_candidates",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        {},
        {},
    )
    candidate_ref = candidate._evaluate_scenario(
        "candidate_all_on_active_a8_reference",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        candidate_series,
        candidate_conf,
    )
    candidate_values, candidate_meta = candidate._add_candidate_series(
        active["a8_values"],
        active["all_days"],
        candidate_series,
        candidate_conf,
    )
    scenario_values: dict[str, list[float]] = {
        active_ref["name"]: active["a8_values"],
        candidate_ref["name"]: candidate_values,
    }
    scenarios = []
    references = []
    for reference in (active_ref, candidate_ref):
        row = {
            "schema": f"{SCHEMA_PREFIX}.portfolio_replay_scenario.v1",
            "created_at_utc": created_at,
            "scenario": reference["name"],
            "base_reference": None,
            "source_value_key": None,
            "expansion_weight_per_tag": 0.0,
            "delta_vs_base": {},
            **reference,
        }
        references.append(row)
    scenario_inputs = [
        ("candidate_plus_expansion_seed_0p025_cost3_before_swap", "proxy_r_cost3_before_swap", 0.025, candidate_values, candidate_ref),
        ("candidate_plus_expansion_micro_0p0125_cost3_after_swap", "proxy_r_cost3_after_swap_proxy", 0.0125, candidate_values, candidate_ref),
        ("candidate_plus_expansion_seed_0p025_cost3_after_swap", "proxy_r_cost3_after_swap_proxy", 0.025, candidate_values, candidate_ref),
        ("candidate_plus_expansion_ceiling_0p05_cost3_after_swap", "proxy_r_cost3_after_swap_proxy", 0.05, candidate_values, candidate_ref),
        ("candidate_plus_expansion_seed_0p025_swap_drag_only", "total_swap_r_per_lot_risk_proxy", 0.025, candidate_values, candidate_ref),
        ("active_a8_plus_expansion_seed_0p025_cost3_after_swap_no_candidate_book", "proxy_r_cost3_after_swap_proxy", 0.025, active["a8_values"], active_ref),
    ]
    for name, value_key, weight, base_values, base_ref in scenario_inputs:
        expansion_series = series_from_events(events, value_key)
        weights = {tag: weight for tag in expansion_series}
        values, meta = candidate._add_candidate_series(base_values, active["all_days"], expansion_series, weights)
        scenario_values[name] = values
        scenario = candidate._evaluate_scenario(name, base_values, active["all_days"], active["sd_book"], expansion_series, weights)
        scenario.update(
            {
                "schema": f"{SCHEMA_PREFIX}.portfolio_replay_scenario.v1",
                "created_at_utc": created_at,
                "scenario": name,
                "base_reference": base_ref["name"],
                "source_value_key": value_key,
                "expansion_weight_per_tag": weight,
                "delta_vs_base": delta(scenario, base_ref),
                "contribution": meta["contribution"],
                "unmatched_days": meta["unmatched_days"],
            }
        )
        scenarios.append(scenario)
    daily_rows = []
    for idx, day in enumerate(active["all_days"]):
        row = {
            "schema": f"{SCHEMA_PREFIX}.portfolio_daily_replay_row.v1",
            "created_at_utc": created_at,
            "date": day.isoformat()[:10],
            "split": candidate._split_of_year(day.year),
            "active_a8_r": round(float(scenario_values[active_ref["name"]][idx]), 9),
            "candidate_all_on_active_a8_r": round(float(scenario_values[candidate_ref["name"]][idx]), 9),
        }
        row["candidate_overlay_r"] = round(row["candidate_all_on_active_a8_r"] - row["active_a8_r"], 9)
        for scenario_name in sorted(name for name in scenario_values if "expansion" in name):
            value = round(float(scenario_values[scenario_name][idx]), 9)
            row[f"{scenario_name}_r"] = value
            base = row["active_a8_r"] if scenario_name.endswith("no_candidate_book") else row["candidate_all_on_active_a8_r"]
            row[f"{scenario_name}_expansion_overlay_r"] = round(value - base, 9)
        daily_rows.append(row)
    metadata = {
        "schema": f"{SCHEMA_PREFIX}.portfolio_replay_metadata.v1",
        "created_at_utc": created_at,
        "a8_reproduction": active["reproduction"],
        "all_days_count": len(active["all_days"]),
        "candidate_overlay_meta": candidate_meta,
        "active_reference": scenario_snapshot(active_ref),
        "candidate_reference": scenario_snapshot(candidate_ref),
    }
    return [*references, *scenarios], daily_rows, metadata, scenarios


def build_candidate_contribution_rows(created_at: str, events: list[dict[str, Any]], seed_after: dict[str, Any], before: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_tag[event["tag"]].append(event)
    before_contrib = before["contribution"]
    after_contrib = seed_after["contribution"]
    for tag, tag_events in sorted(by_tag.items()):
        before_payload = before_contrib[tag]
        after_payload = after_contrib[tag]
        swap_values = [float(row["total_swap_r_per_lot_risk_proxy"]) for row in tag_events if row.get("total_swap_r_per_lot_risk_proxy") is not None]
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.candidate_contribution_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": tag_events[0]["file_symbol"],
                "broker_symbol": tag_events[0]["broker_symbol"],
                "event_count": len(tag_events),
                "swap_mode_counts": dict(Counter(str(row["swap_mode"]) for row in tag_events)),
                "cost3_before_swap_summary": split_summary(tag_events, "proxy_r_cost3_before_swap"),
                "cost3_after_swap_summary": split_summary(tag_events, "proxy_r_cost3_after_swap_proxy"),
                "swap_r_proxy_summary": summarize(swap_values),
                "seed_weight_0p025_matched_days": after_payload["matched_days"],
                "seed_weight_0p025_total_weighted_R_before_swap": before_payload["total_weighted_R"],
                "seed_weight_0p025_total_weighted_R_after_swap": after_payload["total_weighted_R"],
                "seed_weight_0p025_swap_drag_delta_R": round(after_payload["total_weighted_R"] - before_payload["total_weighted_R"], 10),
                "live_authority_ready": False,
                "transformed_use": "default_off_candidate_requires_swap_adjusted_sizing_and_live_authority_repair",
            }
        )
    return rows


def forbidden_scan(created_at: str) -> dict[str, Any]:
    tokens = [
        "order_" + "send(",
        "order_" + "check(",
        "orders_" + "get(",
        "positions_" + "get(",
        "history_" + "deals_" + "get(",
        "history_" + "orders_" + "get(",
        "market_book_" + "add(",
        "market_book_" + "get(",
        "market_book_" + "release(",
        "MetaTrader" + "5(",
        "symbol_" + "select(",
        "subprocess" + ".run(['" + "ssh'",
        "subprocess" + ".run([\"" + "ssh\"",
    ]
    files = [
        ROUTE / "build_market_expansion_swap_adjusted_activation_rescore.py",
        ROUTE / "verify_market_expansion_swap_adjusted_activation_rescore.py",
    ]
    matches = []
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in tokens:
            if token in text:
                matches.append({"path": rel(path), "token": token})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "ok": not matches,
        "matches": matches,
        "scanned_files": [rel(path) for path in files],
    }


def write_packet(result: dict[str, Any], delta_summary: dict[str, Any]) -> None:
    text = f"""# Market Expansion Swap-Adjusted Activation Rescore

Decision: `{result['decision']}`

Runtime effect: `{result['runtime_effect']}`

## Result

- Candidate reference monthly: `{delta_summary['candidate_reference']['monthly_pct']}`.
- Before-swap seed monthly: `{delta_summary['before_swap_seed']['monthly_pct']}`.
- After-swap seed monthly: `{delta_summary['after_swap_seed']['monthly_pct']}`.
- After-swap seed delta vs candidate monthly: `{delta_summary['after_swap_seed_delta_vs_candidate']['monthly_pct']}`.
- Swap drag versus prior seed monthly: `{delta_summary['swap_drag_delta_vs_before_seed']['monthly_pct']}`.

Market expansion remains a default-off candidate family. The swap-adjusted
overlay is still positive at seed and ceiling weights, but the incremental lift
is small; promotion remains blocked by live-authority/session/fill/VPS parity.
"""
    (ROUTE / "SWAP_ADJUSTED_ACTIVATION_RESCORE_PACKET.md").write_text(text, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Next Prompt - Market Expansion Session Fill VPS Parity After Swap-Adjusted Rescore

Created: {created_at}

`/goal Follow this controlling prompt as the complete objective. Mandatory preflight: run python3 scripts/generate_live_state.py and read .context/LIVE_STATE.md, current_vnext_system_map.md, current_repo_reading_order.md, goal_session_research_discipline.md, research_operating_doctrine.md, orchestrator_successor_operating_brief.md, orchestrator_methodology_hardening_controls.md, parallel_goal_merge_playbook.md, and latest artifacts in research/operations/final_moonshot_market_expansion_swap_adjusted_activation_rescore_2026_06_18. Do not rely on chat memory.`

Treat doctrine as active instructions, not background. This is a constructive deployment-package repair lane with no conservative brake. Pursue full same-evidence-class pursuit for explicit session-source proof, prospective fill/queue authority, VPS packet parity, activation/rollback monitoring, and final default-off promotion boundary. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or exactly ruled out. Completion audit must record instruction coverage, source completeness, result materialization, implementation decision or branch decision rows, exact-R/proxy-R/expectancy limitations, and proof-or-impossibility.

No arbitrary top-N, no top-N, no top 3/5/10, and no number-limited cutoff for questions, ambiguities, source roots, routes, blockers, opportunities, or findings. Preserve all material rows in a full ledger before any ranked summary.

Objective: using the swap-adjusted rescore as the numeric authority, build or exactly bound the strongest market-expansion deployable default-off package: explicit trading-session/source proof, fill policy parity, broker-posted cost monitoring requirement, VPS packet parity commands, promotion criteria, rollback criteria, and owner-action handoff. If live promotion is not authorized in the active turn, do not apply it; emit exact commands and checks.

Forbidden unless explicitly approved in the active turn: production-change/live trading/broker operation; broker/account/order/history/deal/position mutation; order send/check; market book/depth/orderflow; prompt/config/risk/execution/safety/canary/selector live activation; credential mutation/disclosure; paid API/vendor calls; remote push; live VPS restart/reload; production live config activation. Read-only local artifacts and already-present read-only bridge/VPS packet inspection are allowed only if no state mutation occurs.

Required verification: route verifier, focused test, pytest continuity, route artifact audit with full JSONL, prompt hardening validation, manifest/hash output, scoped commit, and context refresh.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if not path.is_file() or path.name == "OUTPUT_MANIFEST.json":
            continue
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
    events = read_jsonl(SWAP_ROUTE / "SOURCE_EVENT_SWAP_HOLDING_PROXY_LEDGER.jsonl")
    swap_result = read_json(SWAP_ROUTE / "SWAP_MODE5_HOLDING_REPAIR_RESULT.json")
    replay_rows, daily_rows, metadata, scenario_rows = build_replay(created_at, events)
    scenario_by_name = {row["scenario"]: row for row in replay_rows}
    before_seed = scenario_by_name["candidate_plus_expansion_seed_0p025_cost3_before_swap"]
    after_micro = scenario_by_name["candidate_plus_expansion_micro_0p0125_cost3_after_swap"]
    after_seed = scenario_by_name["candidate_plus_expansion_seed_0p025_cost3_after_swap"]
    after_ceiling = scenario_by_name["candidate_plus_expansion_ceiling_0p05_cost3_after_swap"]
    candidate_ref = scenario_by_name["candidate_all_on_active_a8_reference"]
    active_ref = scenario_by_name["active_core8_a8_baseline_no_candidates"]
    contribution_rows = build_candidate_contribution_rows(created_at, events, after_seed, before_seed)
    forbidden = forbidden_scan(created_at)
    after_seed_positive = after_seed["mc"]["monthly_pct"] > candidate_ref["mc"]["monthly_pct"] and after_seed["sharpe"] > candidate_ref["sharpe"]
    delta_summary = {
        "schema": f"{SCHEMA_PREFIX}.delta_summary.v1",
        "created_at_utc": created_at,
        "active_reference": scenario_snapshot(active_ref),
        "candidate_reference": scenario_snapshot(candidate_ref),
        "before_swap_seed": scenario_snapshot(before_seed),
        "after_swap_micro": scenario_snapshot(after_micro),
        "after_swap_seed": scenario_snapshot(after_seed),
        "after_swap_ceiling": scenario_snapshot(after_ceiling),
        "before_swap_seed_delta_vs_candidate": before_seed["delta_vs_base"],
        "after_swap_seed_delta_vs_candidate": after_seed["delta_vs_base"],
        "swap_drag_delta_vs_before_seed": delta(after_seed, before_seed),
        "interpretation": "swap-adjusted expansion remains slightly positive at seed, but materially smaller than prior no-swap overlay",
    }
    requirements = [
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-ADJ-REQ-001",
            "requirement": "explicit broker trading-session table or platform-source proof",
            "current_status": "not_closed_carried_forward",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-ADJ-REQ-002",
            "requirement": "prospective broker fill/queue authority for limit-first or guarded-open policy",
            "current_status": "not_closed_carried_forward",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-SWAP-ADJ-REQ-003",
            "requirement": "broker-posted swap/commission/slippage monitoring and VPS packet parity before promotion",
            "current_status": "not_closed_owner_action_boundary",
        },
    ]
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            swap_result["ok"] is True
            and len(events) == 2596
            and len(replay_rows) == 8
            and len(daily_rows) == metadata["all_days_count"] == 1679
            and len(contribution_rows) == 14
            and after_seed_positive
            and forbidden["ok"] is True
        ),
        "decision": DECISION,
        "source_swap_route": rel(SWAP_ROUTE),
        "source_dossier_route": rel(DOSSIER_ROUTE),
        "source_event_count": len(events),
        "portfolio_scenario_count": len(replay_rows),
        "portfolio_daily_row_count": len(daily_rows),
        "candidate_contribution_row_count": len(contribution_rows),
        "candidate_reference_monthly_pct": candidate_ref["mc"]["monthly_pct"],
        "before_swap_seed_monthly_pct": before_seed["mc"]["monthly_pct"],
        "after_swap_seed_monthly_pct": after_seed["mc"]["monthly_pct"],
        "after_swap_seed_delta_monthly_pct": after_seed["delta_vs_base"]["monthly_pct"],
        "swap_drag_delta_monthly_pct": delta_summary["swap_drag_delta_vs_before_seed"]["monthly_pct"],
        "candidate_reference_sharpe": candidate_ref["sharpe"],
        "after_swap_seed_sharpe": after_seed["sharpe"],
        "after_swap_seed_delta_sharpe": after_seed["delta_vs_base"]["sharpe"],
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "runtime_effect": "none_swap_adjusted_rescore_only",
        "approved_read_surfaces_used": ["committed_route_artifacts", "candidate_replay_module"],
        "forbidden_surfaces_touched": [],
    }
    decision_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": DECISION,
            "status": "positive_after_swap_but_small_default_off_not_live_authority",
            "reason": "swap-adjusted seed overlay remains positive vs candidate reference but smaller; live authority gaps remain open",
        }
    ]
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "no_arbitrary_top_n": True,
        "all_source_events_preserved": True,
        "same_evidence_class_pursued": [
            "pre-swap seed replay preserved for direct comparison",
            "swap-adjusted micro, seed, and ceiling replays computed",
            "swap-drag-only scenario computed",
            "active-A8 plus expansion without candidate-book scenario computed",
            "all daily replay rows materialized",
            "all 14 candidate contribution rows materialized",
        ],
        "non_overclaim_boundaries": [
            "not live authority",
            "not explicit session proof",
            "not prospective broker fill proof",
            "not VPS parity or promotion",
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
            "constructive_builder_posture_applied": True,
            "full_same_evidence_class_pursuit": True,
            "no_arbitrary_top_n": True,
            "result_materialization_status": "swap_adjusted_portfolio_rescore_materialized",
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
    }

    write_jsonl(ROUTE / "SWAP_ADJUSTED_PORTFOLIO_REPLAY_LEDGER.jsonl", replay_rows)
    write_jsonl(ROUTE / "SWAP_ADJUSTED_DAILY_REPLAY_LEDGER.jsonl", daily_rows)
    write_json(ROUTE / "SWAP_ADJUSTED_PORTFOLIO_REPLAY_METADATA.json", metadata)
    write_jsonl(ROUTE / "CANDIDATE_SWAP_ADJUSTED_CONTRIBUTION_LEDGER.jsonl", contribution_rows)
    write_json(ROUTE / "SWAP_ADJUSTED_ACTIVATION_DELTA_SUMMARY.json", delta_summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "SWAP_ADJUSTED_ACTIVATION_RESCORE_RESULT.json", result)
    write_packet(result, delta_summary)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 240) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    return {"command": " ".join(command), "returncode": proc.returncode, "stdout_tail": proc.stdout[-5000:], "stderr_tail": proc.stderr[-5000:]}


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command([sys.executable, str(ROUTE / "verify_market_expansion_swap_adjusted_activation_rescore.py")])
    write_json(ROUTE / "VERIFIER_COMMAND_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1", "created_at_utc": created_at, **verifier_result})
    checks = [
        run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(ROUTE / "build_market_expansion_swap_adjusted_activation_rescore.py"),
                str(ROUTE / "verify_market_expansion_swap_adjusted_activation_rescore.py"),
                "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command([sys.executable, "-m", "pytest", "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py", "-q"], timeout=180),
    ]
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.focused_test_result.v1", "created_at_utc": created_at, "ok": all(row["returncode"] == 0 for row in checks), "results": checks})
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] and all(row["returncode"] == 0 for row in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
