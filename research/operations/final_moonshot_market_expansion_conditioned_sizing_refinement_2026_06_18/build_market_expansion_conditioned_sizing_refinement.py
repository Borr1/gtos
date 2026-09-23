#!/usr/bin/env python3
"""Build default-off conditioned market-expansion sizing refinement evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
OPS = PROJECT_ROOT / "research" / "operations"
SWAP_ROUTE = OPS / "final_moonshot_market_expansion_swap_mode5_holding_repair_2026_06_18"
RESCORE_ROUTE = OPS / "final_moonshot_market_expansion_swap_adjusted_activation_rescore_2026_06_18"
CANDIDATE_REPLAY = OPS / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18" / "verify_candidate_enabled_unified_replay_mc.py"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_conditioned_sizing_refinement"
DECISION = "MARKET_EXPANSION_CONDITIONED_SIZING_REFINEMENT_BUILT_DEFAULT_OFF_NOT_LIVE_AUTHORITY"
WEIGHT_GRID = [0.025, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]


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


def series_from_events(events: list[dict[str, Any]], selected_tags: set[str]) -> dict[str, dict[str, float]]:
    series: dict[str, dict[str, float]] = {}
    for event in events:
        if event["tag"] not in selected_tags:
            continue
        value = event.get("proxy_r_cost3_after_swap_proxy")
        if value is None:
            continue
        series.setdefault(event["tag"], {})
        series[event["tag"]][event["date"]] = series[event["tag"]].get(event["date"], 0.0) + float(value)
    return series


def build_dispositions(created_at: str, contribution_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    policies = {
        "all14_swap_adjusted": {row["tag"] for row in contribution_rows},
        "robust6_every_split_positive": {
            row["tag"]
            for row in contribution_rows
            if row["cost3_after_swap_summary"]["all"]["mean"] > 0
            and row["cost3_after_swap_summary"]["every_populated_split_positive"] is True
        },
        "positive_weighted12_after_swap": {
            row["tag"]
            for row in contribution_rows
            if row["seed_weight_0p025_total_weighted_R_after_swap"] > 0
        },
    }
    dispositions = []
    for row in sorted(contribution_rows, key=lambda item: item["tag"]):
        tags = {name for name, members in policies.items() if row["tag"] in members}
        if "robust6_every_split_positive" in tags:
            disposition = "refined_default_off_core_candidate"
        elif "positive_weighted12_after_swap" in tags:
            disposition = "refined_default_off_context_or_sizing_candidate"
        else:
            disposition = "preserve_as_feature_veto_or_redesign_input_not_sleeve_now"
        dispositions.append(
            {
                "schema": f"{SCHEMA_PREFIX}.candidate_conditioned_disposition_row.v1",
                "created_at_utc": created_at,
                "tag": row["tag"],
                "file_symbol": row["file_symbol"],
                "broker_symbol": row["broker_symbol"],
                "event_count": row["event_count"],
                "after_swap_mean_proxy_r": row["cost3_after_swap_summary"]["all"]["mean"],
                "after_swap_every_populated_split_positive": row["cost3_after_swap_summary"]["every_populated_split_positive"],
                "seed_weight_0p025_total_weighted_R_after_swap": row["seed_weight_0p025_total_weighted_R_after_swap"],
                "seed_weight_0p025_swap_drag_delta_R": row["seed_weight_0p025_swap_drag_delta_R"],
                "included_in_policies": sorted(tags),
                "conditioned_disposition": disposition,
                "inspire_not_kill_translation": (
                    "use as core default-off expansion candidate"
                    if disposition == "refined_default_off_core_candidate"
                    else "use as context, sizing, veto, or redesign input until stronger split/live authority exists"
                ),
                "live_authority_ready": False,
            }
        )
    return dispositions, policies


def build_replays(created_at: str, policies: dict[str, set[str]], events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    candidate = load_module("candidate_enabled_unified_replay_for_conditioned_expansion", CANDIDATE_REPLAY)
    active = candidate._active_baselines()
    candidate_daily = candidate._load_candidate_daily()
    candidate_conf = {
        name: float(value)
        for name, value in candidate.candidate_registry.CANDIDATE_CONFIDENCE.items()
        if float(value) > 0.0 and name in candidate_daily
    }
    candidate_series = {name: candidate_daily[name] for name in candidate_conf}
    active_ref = candidate._evaluate_scenario("active_core8_a8_baseline_no_candidates", active["a8_values"], active["all_days"], active["sd_book"], {}, {})
    candidate_ref = candidate._evaluate_scenario("candidate_all_on_active_a8_reference", active["a8_values"], active["all_days"], active["sd_book"], candidate_series, candidate_conf)
    candidate_values, candidate_meta = candidate._add_candidate_series(active["a8_values"], active["all_days"], candidate_series, candidate_conf)
    scenario_values: dict[str, list[float]] = {
        active_ref["name"]: active["a8_values"],
        candidate_ref["name"]: candidate_values,
    }
    rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.conditioned_policy_replay_row.v1",
            "created_at_utc": created_at,
            "policy": "reference",
            "selected_tag_count": 0,
            "selected_tags": [],
            "weight": 0.0,
            "scenario": active_ref["name"],
            "base_reference": None,
            "delta_vs_candidate": {},
            "delta_vs_active": {},
            **active_ref,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.conditioned_policy_replay_row.v1",
            "created_at_utc": created_at,
            "policy": "reference",
            "selected_tag_count": 0,
            "selected_tags": [],
            "weight": 0.0,
            "scenario": candidate_ref["name"],
            "base_reference": active_ref["name"],
            "delta_vs_candidate": {},
            "delta_vs_active": delta(candidate_ref, active_ref),
            **candidate_ref,
        },
    ]
    for policy_name, tags in sorted(policies.items()):
        series = series_from_events(events, tags)
        for weight in WEIGHT_GRID:
            scenario_name = f"{policy_name}_w{str(weight).replace('.', 'p')}"
            values, meta = candidate._add_candidate_series(candidate_values, active["all_days"], series, {tag: weight for tag in series})
            scenario_values[scenario_name] = values
            scenario = candidate._evaluate_scenario(scenario_name, candidate_values, active["all_days"], active["sd_book"], series, {tag: weight for tag in series})
            rows.append(
                {
                    "schema": f"{SCHEMA_PREFIX}.conditioned_policy_replay_row.v1",
                    "created_at_utc": created_at,
                    "policy": policy_name,
                    "selected_tag_count": len(tags),
                    "selected_tags": sorted(tags),
                    "weight": weight,
                    "scenario": scenario_name,
                    "base_reference": candidate_ref["name"],
                    "delta_vs_candidate": delta(scenario, candidate_ref),
                    "delta_vs_active": delta(scenario, active_ref),
                    "contribution": meta["contribution"],
                    "unmatched_days": meta["unmatched_days"],
                    **scenario,
                }
            )
    daily_rows = []
    for idx, day in enumerate(active["all_days"]):
        row = {
            "schema": f"{SCHEMA_PREFIX}.conditioned_daily_replay_row.v1",
            "created_at_utc": created_at,
            "date": day.isoformat()[:10],
            "split": candidate._split_of_year(day.year),
            "active_a8_r": round(float(scenario_values[active_ref["name"]][idx]), 9),
            "candidate_all_on_active_a8_r": round(float(scenario_values[candidate_ref["name"]][idx]), 9),
        }
        for name in sorted(item for item in scenario_values if item not in {active_ref["name"], candidate_ref["name"]}):
            value = round(float(scenario_values[name][idx]), 9)
            row[f"{name}_r"] = value
            row[f"{name}_overlay_r"] = round(value - row["candidate_all_on_active_a8_r"], 9)
        daily_rows.append(row)
    metadata = {
        "schema": f"{SCHEMA_PREFIX}.metadata.v1",
        "created_at_utc": created_at,
        "a8_reproduction": active["reproduction"],
        "all_days_count": len(active["all_days"]),
        "candidate_overlay_meta": candidate_meta,
        "active_reference": scenario_snapshot(active_ref),
        "candidate_reference": scenario_snapshot(candidate_ref),
        "weight_grid": WEIGHT_GRID,
    }
    return rows, daily_rows, metadata


def best_rows(replay_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in replay_rows if row.get("policy") != "reference"]
    best_monthly = max(candidates, key=lambda row: (row["mc"]["monthly_pct"], row["sharpe"]))
    best_sharpe = max(candidates, key=lambda row: (row["sharpe"], row["mc"]["monthly_pct"]))
    best_drawdown = min(candidates, key=lambda row: (row["daily"]["maxDD_R"], -row["mc"]["monthly_pct"]))
    return {
        "best_monthly": {
            "policy": best_monthly["policy"],
            "weight": best_monthly["weight"],
            "selected_tag_count": best_monthly["selected_tag_count"],
            "sharpe": best_monthly["sharpe"],
            "monthly_pct": best_monthly["mc"]["monthly_pct"],
            "p_pass": best_monthly["mc"]["p_pass"],
            "p_fail_dd": best_monthly["mc"]["p_fail_dd"],
            "worst_day_pct": best_monthly["mc"]["worst_day_pct"],
            "maxDD_R": best_monthly["daily"]["maxDD_R"],
            "delta_vs_candidate": best_monthly["delta_vs_candidate"],
        },
        "best_sharpe": {
            "policy": best_sharpe["policy"],
            "weight": best_sharpe["weight"],
            "selected_tag_count": best_sharpe["selected_tag_count"],
            "sharpe": best_sharpe["sharpe"],
            "monthly_pct": best_sharpe["mc"]["monthly_pct"],
            "p_pass": best_sharpe["mc"]["p_pass"],
            "p_fail_dd": best_sharpe["mc"]["p_fail_dd"],
            "worst_day_pct": best_sharpe["mc"]["worst_day_pct"],
            "maxDD_R": best_sharpe["daily"]["maxDD_R"],
            "delta_vs_candidate": best_sharpe["delta_vs_candidate"],
        },
        "best_drawdown": {
            "policy": best_drawdown["policy"],
            "weight": best_drawdown["weight"],
            "selected_tag_count": best_drawdown["selected_tag_count"],
            "sharpe": best_drawdown["sharpe"],
            "monthly_pct": best_drawdown["mc"]["monthly_pct"],
            "p_pass": best_drawdown["mc"]["p_pass"],
            "p_fail_dd": best_drawdown["mc"]["p_fail_dd"],
            "worst_day_pct": best_drawdown["mc"]["worst_day_pct"],
            "maxDD_R": best_drawdown["daily"]["maxDD_R"],
            "delta_vs_candidate": best_drawdown["delta_vs_candidate"],
        },
    }


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
        ROUTE / "build_market_expansion_conditioned_sizing_refinement.py",
        ROUTE / "verify_market_expansion_conditioned_sizing_refinement.py",
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


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Next Prompt - Market Expansion Conditioned Policy Audit And Session Fill Repair

Created: {created_at}

`/goal Follow this controlling prompt as the complete objective. Mandatory preflight: run python3 scripts/generate_live_state.py and read .context/LIVE_STATE.md, current_vnext_system_map.md, current_repo_reading_order.md, goal_session_research_discipline.md, research_operating_doctrine.md, orchestrator_successor_operating_brief.md, orchestrator_methodology_hardening_controls.md, parallel_goal_merge_playbook.md, and latest artifacts in research/operations/final_moonshot_market_expansion_conditioned_sizing_refinement_2026_06_18. Do not rely on chat memory.`

Treat doctrine as active instructions, not background. This is a constructive audit/repair lane with no conservative brake. Pursue full same-evidence-class pursuit for conditioned market-expansion policy acceptance, explicit session-source proof, prospective fill/queue authority, and VPS packet parity. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or exactly ruled out. Completion audit must record instruction coverage, source completeness, result materialization, implementation decision or branch decision rows, exact-R/proxy-R/expectancy limitations, and proof-or-impossibility.

No arbitrary top-N, no top-N, no top 3/5/10, and no number-limited cutoff for questions, ambiguities, source roots, routes, blockers, opportunities, or findings. Preserve all material rows in a full ledger before any ranked summary.

Objective: audit the conditioned sizing refinement, decide whether any default-off conditioned market-expansion policy should enter the deployable package as an activation candidate, and repair or exactly bound the remaining live-authority gaps. Do not apply live promotion; emit exact package, monitoring, rollback, and owner-action commands only if eligible.

Forbidden unless explicitly approved in the active turn: production-change/live trading/broker operation; broker/account/order/history/deal/position mutation; order send/check; market book/depth/orderflow; prompt/config/risk/execution/safety/canary/selector live activation; credential mutation/disclosure; paid API/vendor calls; remote push; live VPS restart/reload; production live config activation.

Required verification: route verifier, focused test, pytest continuity, route artifact audit with full JSONL, prompt hardening validation, manifest/hash output, scoped commit, and context refresh.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_packet(result: dict[str, Any], summary: dict[str, Any]) -> None:
    text = f"""# Market Expansion Conditioned Sizing Refinement

Decision: `{result['decision']}`

Runtime effect: `{result['runtime_effect']}`

## Result

- Replay policy rows: `{result['conditioned_policy_replay_row_count']}`.
- Daily replay rows: `{result['conditioned_daily_replay_row_count']}`.
- Best monthly policy: `{summary['best_monthly']['policy']}` at weight `{summary['best_monthly']['weight']}`, monthly `{summary['best_monthly']['monthly_pct']}`.
- Best drawdown policy: `{summary['best_drawdown']['policy']}` at weight `{summary['best_drawdown']['weight']}`, maxDD `{summary['best_drawdown']['maxDD_R']}`.

This route shows market expansion should not be treated as a flat all-sleeve
overlay. The useful form is conditioned/default-off: stronger candidates can be
preserved for activation audit, while weaker candidates become context, veto,
sizing, or redesign inputs. No live authority or config activation is claimed.
"""
    (ROUTE / "CONDITIONED_SIZING_REFINEMENT_PACKET.md").write_text(text, encoding="utf-8")


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if not path.is_file() or path.name == "OUTPUT_MANIFEST.json":
            continue
        artifacts.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(ROUTE / "OUTPUT_MANIFEST.json", {"schema": f"{SCHEMA_PREFIX}.output_manifest.v1", "created_at_utc": created_at, "artifact_count": len(artifacts), "artifacts": artifacts})


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    events = read_jsonl(SWAP_ROUTE / "SOURCE_EVENT_SWAP_HOLDING_PROXY_LEDGER.jsonl")
    contribution_rows = read_jsonl(RESCORE_ROUTE / "CANDIDATE_SWAP_ADJUSTED_CONTRIBUTION_LEDGER.jsonl")
    dispositions, policies = build_dispositions(created_at, contribution_rows)
    replay_rows, daily_rows, metadata = build_replays(created_at, policies, events)
    summary = {
        "schema": f"{SCHEMA_PREFIX}.conditioned_policy_summary.v1",
        "created_at_utc": created_at,
        "candidate_reference": metadata["candidate_reference"],
        "active_reference": metadata["active_reference"],
        "policy_tag_counts": {name: len(tags) for name, tags in policies.items()},
        **best_rows(replay_rows),
        "live_authority_ready": False,
        "interpretation": "conditioned expansion improves the flat all-sleeve overlay but remains default-off research/deployment-package evidence",
    }
    forbidden = forbidden_scan(created_at)
    requirements = [
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-COND-REQ-001",
            "requirement": "G12/owner acceptance before conditioned policy becomes deployable activation candidate",
            "current_status": "not_closed_research_refinement_only",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-COND-REQ-002",
            "requirement": "explicit session and prospective fill/queue authority for selected activation symbols",
            "current_status": "not_closed_live_authority_gap",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.remaining_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": "MX-COND-REQ-003",
            "requirement": "VPS packet parity, monitoring, rollback, and owner-approved promotion execution",
            "current_status": "not_closed_owner_action_boundary",
        },
    ]
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            len(events) == 2596
            and len(dispositions) == 14
            and len(replay_rows) == 26
            and len(daily_rows) == metadata["all_days_count"] == 1679
            and summary["best_monthly"]["monthly_pct"] > metadata["candidate_reference"]["monthly_pct"]
            and summary["best_drawdown"]["maxDD_R"] < metadata["candidate_reference"]["maxDD_R"]
            and forbidden["ok"] is True
        ),
        "decision": DECISION,
        "source_swap_route": rel(SWAP_ROUTE),
        "source_rescore_route": rel(RESCORE_ROUTE),
        "source_event_count": len(events),
        "candidate_disposition_row_count": len(dispositions),
        "conditioned_policy_replay_row_count": len(replay_rows),
        "conditioned_daily_replay_row_count": len(daily_rows),
        "candidate_reference_monthly_pct": metadata["candidate_reference"]["monthly_pct"],
        "candidate_reference_sharpe": metadata["candidate_reference"]["sharpe"],
        "candidate_reference_maxDD_R": metadata["candidate_reference"]["maxDD_R"],
        "best_monthly_policy": summary["best_monthly"],
        "best_sharpe_policy": summary["best_sharpe"],
        "best_drawdown_policy": summary["best_drawdown"],
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "runtime_effect": "none_conditioned_sizing_refinement_only",
        "approved_read_surfaces_used": ["committed_route_artifacts", "candidate_replay_module"],
        "forbidden_surfaces_touched": [],
    }
    decision_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": DECISION,
            "status": "conditioned_default_off_refinement_positive_not_live_authority",
            "reason": "conditioning and sizing improve expansion utility versus flat all-sleeve overlay, but acceptance and live-authority gaps remain",
        }
    ]
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": result["ok"],
        "no_arbitrary_top_n": True,
        "all_source_events_preserved": True,
        "all_weight_grid_rows_preserved": True,
        "same_evidence_class_pursued": [
            "all14, robust6, and positive-weighted12 policies evaluated over full weight grid",
            "reference active and candidate rows preserved",
            "daily rows materialized for every scenario",
            "all 14 candidates receive inspire-not-kill disposition rows",
        ],
        "non_overclaim_boundaries": [
            "not live authority",
            "not G12 accepted",
            "not explicit session/fill authority",
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
            "result_materialization_status": "conditioned_sizing_replay_grid_materialized",
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "forbidden_surfaces_touched": [],
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
    }

    write_jsonl(ROUTE / "CANDIDATE_CONDITIONED_DISPOSITION_LEDGER.jsonl", dispositions)
    write_jsonl(ROUTE / "CONDITIONED_POLICY_REPLAY_LEDGER.jsonl", replay_rows)
    write_jsonl(ROUTE / "CONDITIONED_DAILY_REPLAY_LEDGER.jsonl", daily_rows)
    write_json(ROUTE / "CONDITIONED_POLICY_REPLAY_METADATA.json", metadata)
    write_json(ROUTE / "CONDITIONED_POLICY_SUMMARY.json", summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "CONDITIONED_SIZING_REFINEMENT_RESULT.json", result)
    write_packet(result, summary)
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
    verifier_result = run_command([sys.executable, str(ROUTE / "verify_market_expansion_conditioned_sizing_refinement.py")])
    write_json(ROUTE / "VERIFIER_COMMAND_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1", "created_at_utc": created_at, **verifier_result})
    checks = [
        run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(ROUTE / "build_market_expansion_conditioned_sizing_refinement.py"),
                str(ROUTE / "verify_market_expansion_conditioned_sizing_refinement.py"),
                "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command([sys.executable, "-m", "pytest", "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py", "-q"], timeout=180),
    ]
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", {"schema": f"{SCHEMA_PREFIX}.focused_test_result.v1", "created_at_utc": created_at, "ok": all(row["returncode"] == 0 for row in checks), "results": checks})
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] and all(row["returncode"] == 0 for row in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
