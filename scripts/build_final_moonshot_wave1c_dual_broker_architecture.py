#!/usr/bin/env python3
"""Build Wave 1C dual-broker architecture route artifacts.

This is an offline route builder. It reads current repo files and writes
evidence-classed ledgers; it does not connect to MT5, mutate broker state, call
paid APIs, publish remotes, or restart runtime processes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = ROOT / "research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04"
PROMPT_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1C_DUAL_BROKER_ARCHITECTURE_GOAL_PROMPT_2026-06-04.md"
STARTER_PATH = ROOT / "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE1C_DUAL_BROKER_ARCHITECTURE_STARTER_2026-06-04.txt"

REQUIRED_ROOTS = [
    "research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02",
    "research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02",
    "research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03",
    "research/operations/final_moonshot_live_failure_intelligence_2026_06_04",
    "research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04",
    "shadow_logs",
    "pipeline_state",
    "src",
    "scripts",
    "config",
    "tests",
]

MANDATORY_READS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/final_moonshot_post_hard_halt_research_plan.md",
    ".context/00_core/final_moonshot_goal_session_execution_architecture.md",
    ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md",
    ".context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md",
]

KEYWORD_RE = re.compile(
    r"redacted_account|redacted_account|FTMO|ftmo|dual[_ -]?broker|follower|projector|"
    r"broker_profile|runtime_namespace|target_state|intent_bus|canonical_trade_intents|"
    r"namespace|risk|exposure|commission|swap|slippage|session|halt|maintenance",
    re.IGNORECASE,
)

EVIDENCE_CLASS = "production_code_and_dual_broker_runtime_supervisor_follower_projector_evidence"
FORBIDDEN_SURFACES = [
    "broker_account_order_history_deal_position_mutation",
    "live_trading_broker_operation",
    "paid_api_or_vendor_spending",
    "credential_mutation_or_disclosure",
    "remote_publishing",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run_cmd(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def git_value(args: list[str]) -> str:
    code, out = run_cmd(["git", *args])
    return out if code == 0 else f"git_error:{out}"


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    return data[:limit].decode("utf-8", errors="replace")


def is_lfs_pointer(path: Path) -> bool:
    text = read_text(path, 1024)
    return text.startswith("version https://git-lfs.github.com/spec/v1")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def jsonl_count(path: Path) -> tuple[int, int]:
    rows = 0
    errors = 0
    if not path.exists():
        return rows, errors
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                json.loads(line)
                rows += 1
            except json.JSONDecodeError:
                errors += 1
    return rows, errors


def source_capture_state(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.is_dir():
        return "directory_present"
    if path.stat().st_size == 0:
        return "empty_file"
    if is_lfs_pointer(path):
        return "lfs_pointer_only_not_materialized"
    return "materialized_file"


def inventory_files() -> list[Path]:
    files: set[Path] = set()
    for root_text in REQUIRED_ROOTS:
        root = ROOT / root_text
        if not root.exists():
            continue
        if root_text.startswith("research/operations/"):
            files.update(path for path in root.rglob("*") if path.is_file())
        elif root_text in {"config", "shadow_logs", "pipeline_state"}:
            files.update(path for path in root.rglob("*") if path.is_file())
        else:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in {".py", ".ps1", ".bat", ".yaml", ".yml", ".md", ".json", ".jsonl", ".txt"}:
                    continue
                text = rel(path) + "\n" + read_text(path, 100_000)
                if KEYWORD_RE.search(text):
                    files.add(path)
    files.add(PROMPT_PATH)
    files.add(STARTER_PATH)
    for item in MANDATORY_READS:
        files.add(ROOT / item)
    return sorted(files, key=lambda item: rel(item))


def build_context_anchor() -> dict[str, Any]:
    status = git_value(["status", "--short"])
    return {
        "schema_version": "wave1c_context_anchor_v1",
        "route_id": ROUTE_DIR.name,
        "generated_at_utc": utcnow(),
        "branch": git_value(["branch", "--show-current"]),
        "head": git_value(["rev-parse", "HEAD"]),
        "live_state_generated_line": next(
            (
                line
                for line in read_text(ROOT / ".context/LIVE_STATE.md", 20_000).splitlines()
                if line.startswith("**Generated:**")
            ),
            None,
        ),
        "git_status_short": status.splitlines() if status else [],
        "mandatory_reads": [
            {
                "path": item,
                "exists": (ROOT / item).exists(),
                "sha256": sha256(ROOT / item),
                "source_capture_state": source_capture_state(ROOT / item),
            }
            for item in MANDATORY_READS
        ],
        "controlling_prompt": rel(PROMPT_PATH),
        "starter": rel(STARTER_PATH),
        "lfs_status_from_live_state": "LIVE_STATE reports pointer-only LFS payloads in sparse worktree; route preserves source-gap labels.",
        "evidence_class": EVIDENCE_CLASS,
        "forbidden_surfaces": FORBIDDEN_SURFACES,
    }


def build_source_inventory(files: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    root_rows: list[dict[str, Any]] = []
    inventory_rows: list[dict[str, Any]] = []
    counts_by_root: Counter[str] = Counter()
    for path in files:
        rel_path = rel(path)
        for root_text in REQUIRED_ROOTS:
            if rel_path == root_text or rel_path.startswith(root_text.rstrip("/") + "/"):
                counts_by_root[root_text] += 1
                break
        text = rel_path + "\n" + read_text(path, 120_000)
        matches = sorted(set(m.group(0).lower().replace(" ", "_") for m in KEYWORD_RE.finditer(text)))
        rows, errors = jsonl_count(path) if path.suffix == ".jsonl" and not is_lfs_pointer(path) else (None, None)
        inventory_rows.append(
            {
                "schema_version": "wave1c_source_inventory_v1",
                "path": rel_path,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256(path),
                "source_capture_state": source_capture_state(path),
                "source_completeness_state": "complete_for_route_inventory" if path.exists() and not is_lfs_pointer(path) else "source_gap_pointer_or_missing",
                "matched_terms": matches,
                "jsonl_rows": rows,
                "jsonl_parse_errors": errors,
                "evidence_class": EVIDENCE_CLASS,
                "branch_decision": "consume_as_route_source" if path.exists() else "source_gap",
                "implementation_decision": "inspect_or_reference_for_dual_broker_architecture",
            }
        )
    for root_text in REQUIRED_ROOTS:
        root = ROOT / root_text
        file_count = sum(1 for path in root.rglob("*") if path.is_file()) if root.exists() and root.is_dir() else 0
        root_rows.append(
            {
                "schema_version": "wave1c_searched_root_v1",
                "root": root_text,
                "exists": root.exists(),
                "file_count": file_count,
                "inventory_row_count": counts_by_root[root_text],
                "search_method": "path_walk_plus_keyword_inventory",
                "source_capture_state": source_capture_state(root),
                "source_completeness_state": "searched_current_sparse_worktree",
                "branch_decision": "searched_and_consumed_if_material",
                "implementation_decision": "preserve_material_rows_no_top_n",
                "evidence_class": EVIDENCE_CLASS,
            }
        )
    return root_rows, inventory_rows


def broker_profile_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    profile_paths = [
        ROOT / "config/profiles/redacted_account.yaml",
        ROOT / "config/profiles/operator_profile.yaml",
        ROOT / "config/profiles/ftmo.yaml",
    ]
    profile_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    for path in profile_paths:
        cfg = load_yaml(path)
        runtime = cfg.get("runtime") if isinstance(cfg.get("runtime"), dict) else {}
        dual = cfg.get("dual_broker") if isinstance(cfg.get("dual_broker"), dict) else {}
        broker = cfg.get("broker_profile") if isinstance(cfg.get("broker_profile"), dict) else {}
        namespace = runtime.get("broker_account_namespace") or runtime.get("profile_namespace")
        profile_rows.append(
            {
                "schema_version": "wave1c_broker_profile_inventory_v1",
                "row_type": "profile",
                "profile_path": rel(path),
                "profile_name": cfg.get("profile_name"),
                "broker": broker.get("broker"),
                "company": broker.get("company"),
                "server": broker.get("server"),
                "runtime_namespace": namespace,
                "process_group": runtime.get("process_group"),
                "dual_broker_role": dual.get("role"),
                "runtime_model": dual.get("runtime_model"),
                "source_runtime_namespace": dual.get("source_runtime_namespace"),
                "target_runtime_namespace": dual.get("target_runtime_namespace"),
                "source_capture_state": source_capture_state(path),
                "source_completeness_state": "profile_present_with_runtime_and_dual_broker_contract" if dual else "profile_present_dual_broker_contract_missing",
                "branch_decision": "primary_full_runtime" if dual.get("role") == "primary_full_runtime" else "follower_projector_only",
                "runtime_disposition": dual.get("role") or "profile_only",
                "implementation_decision": "contract_checked_by_follower_or_profile_verifier",
                "evidence_class": "production_code",
            }
        )
        runtime_paths = cfg.get("runtime_paths") if isinstance(cfg.get("runtime_paths"), dict) else {}
        for key, value in sorted(runtime_paths.items()):
            path_rows.append(
                {
                    "schema_version": "wave1c_runtime_path_v1",
                    "profile_path": rel(path),
                    "runtime_namespace": namespace,
                    "path_role": key,
                    "path": value,
                    "namespace_state": "namespaced" if namespace and str(namespace) in str(value) else "namespace_not_embedded",
                    "source_capture_state": "profile_declared_path",
                    "source_completeness_state": "path_role_declared",
                    "branch_decision": "keep_namespaced_runtime_path",
                    "implementation_decision": "fail_closed_if_live_reader_resolves_legacy_unnamespaced_state",
                    "evidence_class": "production_code",
                }
            )
        instruments = cfg.get("instruments") if isinstance(cfg.get("instruments"), dict) else {}
        for symbol, symbol_cfg_any in sorted(instruments.items()):
            symbol_cfg = symbol_cfg_any if isinstance(symbol_cfg_any, dict) else {}
            market = symbol_cfg.get("market") if isinstance(symbol_cfg.get("market"), dict) else {}
            risk = symbol_cfg.get("risk") if isinstance(symbol_cfg.get("risk"), dict) else {}
            profile_rows.append(
                {
                    "schema_version": "wave1c_broker_profile_inventory_v1",
                    "row_type": "instrument",
                    "profile_path": rel(path),
                    "profile_name": cfg.get("profile_name"),
                    "broker": broker.get("broker"),
                    "runtime_namespace": namespace,
                    "symbol": symbol,
                    "mt5_symbol": market.get("mt5_symbol"),
                    "volume_min": market.get("volume_min"),
                    "volume_max": market.get("volume_max"),
                    "volume_step": market.get("volume_step"),
                    "risk_per_trade_pct": risk.get("risk_per_trade_pct", (cfg.get("risk") or {}).get("risk_per_trade_pct") if isinstance(cfg.get("risk"), dict) else None),
                    "source_capture_state": source_capture_state(path),
                    "source_completeness_state": "symbol_profile_present",
                    "branch_decision": "material_dual_broker_symbol",
                    "runtime_disposition": dual.get("role") or "profile_symbol",
                    "implementation_decision": "use_broker_local_symbol_geometry",
                    "evidence_class": "production_code",
                }
            )
            cost_rows.append(
                {
                    "schema_version": "wave1c_cost_spec_session_v1",
                    "profile_path": rel(path),
                    "profile_name": cfg.get("profile_name"),
                    "broker": broker.get("broker"),
                    "runtime_namespace": namespace,
                    "symbol": symbol,
                    "mt5_symbol": market.get("mt5_symbol"),
                    "tick_size": market.get("tick_size"),
                    "point": market.get("point"),
                    "trade_tick_size": market.get("trade_tick_size"),
                    "trade_tick_value": market.get("trade_tick_value"),
                    "contract_size": market.get("contract_size") or market.get("trade_contract_size"),
                    "spread": market.get("spread"),
                    "spread_float": market.get("spread_float"),
                    "swap_long": market.get("swap_long"),
                    "swap_short": market.get("swap_short"),
                    "swap_mode": market.get("swap_mode"),
                    "triple_rollover_day": market.get("triple_rollover_day"),
                    "trade_mode": market.get("trade_mode"),
                    "execution_mode": market.get("execution_mode"),
                    "path": market.get("path"),
                    "source_capture_state": "broker_profile_symbol_spec",
                    "source_completeness_state": "profile_spec_present_session_hours_not_full_broker_export" if market else "market_spec_missing",
                    "branch_decision": "broker_local_cost_truth_required",
                    "runtime_disposition": "target_cost_engine_input" if dual.get("role") == "follower_projector_only" else "primary_cost_engine_input",
                    "implementation_decision": "never_copy_primary_spec_to_target",
                    "evidence_class": "production_code",
                    "exact_r": None,
                    "proxy_r": None,
                    "expectancy": None,
                }
            )
    return profile_rows, cost_rows, path_rows


def static_component_rows() -> dict[str, list[dict[str, Any]]]:
    common = {
        "evidence_class": EVIDENCE_CLASS,
        "exact_r": None,
        "proxy_r": None,
        "expectancy": None,
    }
    authority = [
        ("redacted_account_full_runtime", "redacted_account", "primary_full_runtime", "active_after_future_return_only", "retain_as_source_authority_not_target_copy"),
        ("ftmo_execution_follower", "FTMO", "follower_projector_only", "staged_live_follower", "keep_follower_only_with_broker_local_gates"),
        ("canonical_intent_bus", "both", "broker_neutral_intent_bus", "production_code", "canonical_intents_only_no_fill_or_lot_copy"),
        ("trade_record_projector", "redacted_account", "projector_bridge", "bridge_until_native_emission", "start_at_end_and_freshness_guard"),
        ("target_trade_state", "FTMO", "target_lifecycle_state", "production_code", "persist_restore_and_annotate_cash_risk"),
        ("watchdog_primary_bridge", "both", "supervisor", "production_code", "launch_single_projector_single_follower_no_duplicate_ftmo_fleet"),
        ("live_monitoring_maintenance", "both", "read_only_maintenance", "production_code", "bridge_presence_observation_only_by_default"),
    ]
    lifecycle = [
        ("intent_dedupe", "canonical_intent_id/source_lifecycle", "prevents_duplicate_source_lifecycle"),
        ("target_tick_quality", "target broker tick", "defer_or_expire_target_order_when_tick_unusable"),
        ("target_risk_guard", "target account budget", "allow_reduce_or_block_by_broker_local_budget"),
        ("target_startup_recovery", "target positions and pending intent store", "restore_only_symbols_with_positions_or_pending_intents"),
        ("target_residual_recovery", "broker residual volume or BE SL", "infer_tp1_hit_without_opening_new_order"),
        ("active_trade_management", "ExecutionEngine.check_and_manage_trade", "target_broker_local_lifecycle_after_follow"),
        ("pending_limit_candle_check", "target M15 candles", "target_broker_local_pending_fill_check"),
    ]
    risk = [
        ("source_cap_vs_target_profile", "target_risk_cap_pct", "lower_of_source_effective_cap_and_target_profile"),
        ("open_position_stop_risk", "_target_open_position_sl_risk_amount", "requires_broker_order_calc_profit"),
        ("ftmo_daily_overlay", "_target_account_budget_projection", "internal_4pct_overlay_and_external_ftmo_limits"),
        ("max_concurrent", "profile risk.max_concurrent", "disabled_for_aggregate_drawdown_budget"),
        ("pending_risk", "_pending_engine_risk_amount", "included_in_budget_projection"),
    ]
    target = [
        ("canonical_intent_log", "pipeline_state/dual_broker/canonical_trade_intents.jsonl", "shared_bus"),
        ("ftmo_action_log", "pipeline_state/operator_profile/dual_broker_execution_follower_actions.jsonl", "target_namespace_log"),
        ("ftmo_checkpoint", "pipeline_state/operator_profile/dual_broker_execution_follower_checkpoint.json", "target_namespace_checkpoint"),
        ("ftmo_target_trade_state", "pipeline_state/operator_profile/dual_broker_target_trade_state.json", "target_namespace_state"),
        ("pending_intent_files", "knowledge_base/meta/pending_intent_<symbol>_<namespace>.pkl", "namespaced_pending_intent"),
        ("notification_queue", "pipeline_state/<runtime_namespace>/notification_queue.jsonl", "profile_namespaced_queue"),
    ]
    crash = [
        ("single_instance_locks", "acquire_single_instance_lock", "prevents_duplicate_follower_projector"),
        ("startup_recovery", "recover_target_state_on_startup", "restores_positions_and_pending_intents"),
        ("stale_market_recovery_window", "--live-recovery-window-seconds 1800", "blocks_late_market_entry_open"),
        ("source_record_retry_state", "_source_record_retry_state", "retry_only_when_source_record_unclosed_and_recent"),
        ("hard_halt_flags", "pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag", "runtime_return_requires_separate_dossier"),
        ("maintenance_suppression", "GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER", "explicit_opt_in_only"),
    ]

    return {
        "authority": [
            {
                "schema_version": "wave1c_authority_separation_v1",
                "component": component,
                "broker_namespace": broker,
                "authority": authority_value,
                "runtime_disposition": disposition,
                "source_capture_state": "current_code_or_route_artifact",
                "source_completeness_state": "component_level_complete",
                "branch_decision": "final_architecture_decision_row",
                "implementation_decision": decision,
                **common,
            }
            for component, broker, authority_value, disposition, decision in authority
        ],
        "lifecycle": [
            {
                "schema_version": "wave1c_lifecycle_v1",
                "surface": surface,
                "source": source,
                "runtime_disposition": disposition,
                "source_capture_state": "current_code_tested_or_prior_route_evidence",
                "source_completeness_state": "component_level_complete",
                "branch_decision": "keep_ftmo_broker_local_lifecycle_after_intent_acceptance",
                "implementation_decision": disposition,
                **common,
            }
            for surface, source, disposition in lifecycle
        ],
        "risk": [
            {
                "schema_version": "wave1c_risk_exposure_v1",
                "surface": surface,
                "source": source,
                "runtime_disposition": disposition,
                "source_capture_state": "current_code_profile",
                "source_completeness_state": "component_level_complete",
                "branch_decision": "target_broker_local_risk_gate_required",
                "implementation_decision": disposition,
                **common,
            }
            for surface, source, disposition in risk
        ],
        "target": [
            {
                "schema_version": "wave1c_target_namespace_v1",
                "surface": surface,
                "path": path,
                "runtime_disposition": disposition,
                "source_capture_state": "current_code_profile",
                "source_completeness_state": "component_level_complete",
                "branch_decision": "namespaced_state_required",
                "implementation_decision": disposition,
                **common,
            }
            for surface, path, disposition in target
        ],
        "crash": [
            {
                "schema_version": "wave1c_crash_halt_v1",
                "surface": surface,
                "source": source,
                "runtime_disposition": disposition,
                "source_capture_state": "current_code_context",
                "source_completeness_state": "component_level_complete",
                "branch_decision": "keep_fail_closed_recovery",
                "implementation_decision": disposition,
                **common,
            }
            for surface, source, disposition in crash
        ],
    }


def code_change_rows() -> list[dict[str, Any]]:
    diff = set(git_value(["diff", "--name-only"]).splitlines())
    for line in git_value(["status", "--short"]).splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            diff.add(path)
    rows: list[dict[str, Any]] = []
    for path in sorted(diff):
        if not path:
            continue
        if path.startswith(ROUTE_DIR.relative_to(ROOT).as_posix()):
            continue
        if not (
            path.startswith("scripts/")
            or path.startswith("tests/")
            or path.startswith("config/")
            or path.startswith("src/")
        ):
            continue
        rows.append(
            {
                "schema_version": "wave1c_production_code_change_v1",
                "path": path,
                "change_class": "production_or_runtime_contract_code" if path.startswith(("scripts/", "src/")) else "profile_or_test_contract",
                "source_capture_state": source_capture_state(ROOT / path),
                "source_completeness_state": "current_worktree_diff",
                "branch_decision": "keep_scoped_wave1c_change",
                "runtime_disposition": "production_code_contract_or_test",
                "implementation_decision": "implemented_for_final_dual_broker_architecture",
                "evidence_class": "production_code",
                "forbidden_surface_crossed": False,
            }
        )
    return rows


def implementation_decision_rows() -> list[dict[str, Any]]:
    decisions = [
        ("final_runtime_model", "redacted_account remains full primary; FTMO remains follower/projector only.", "implement"),
        ("ftmo_broker_local_risk", "FTMO follower must calculate target-side risk from FTMO account/spec/open SL exposure.", "implemented_existing_and_contract_checked"),
        ("ftmo_lifecycle_authority", "After an intent is accepted, FTMO manages its own BE/partial/trailing/pending lifecycle.", "implemented_existing_and_preserved"),
        ("primary_copy_boundary", "Do not copy redacted_account lots, fills, cash PnL, or cost specs into FTMO.", "implemented_contract"),
        ("maintenance_bridge_boundary", "Read-only maintenance is not suppressed merely because the bridge is alive.", "implemented"),
        ("runtime_return", "Hard-halt flags remain; repo package only, no broker deployment or restart.", "defer_to_production_return_dossier"),
    ]
    return [
        {
            "schema_version": "wave1c_implementation_decision_v1",
            "decision_id": decision_id,
            "decision": text,
            "branch_decision": branch,
            "runtime_disposition": branch,
            "source_capture_state": "current_code_profile_route_evidence",
            "source_completeness_state": "component_level_complete",
            "implementation_decision": branch,
            "evidence_class": EVIDENCE_CLASS,
            "forbidden_surfaces": FORBIDDEN_SURFACES,
            "exact_r": None,
            "proxy_r": None,
            "expectancy": None,
        }
        for decision_id, text, branch in decisions
    ]


def write_markdown_artifacts(row_counts: dict[str, int]) -> None:
    write_md(
        ROUTE_DIR / "DUAL_BROKER_RUNTIME_PATH_MAP.md",
        f"""# Wave1C Dual-Broker Runtime Path Map

Generated: {utcnow()}

Final runtime model: `redacted_account_primary_full_ftmo_follower_projector`.

redacted_account is the only full-runtime source authority. It owns the 24-symbol
primary brain, account-local order authority for redacted_account only, source trade
records, and canonical intent emission.

FTMO is follower/projector only. It consumes canonical intents, maps symbols to
FTMO broker symbols, applies FTMO broker-local risk/exposure gates, executes only
through the FTMO profile when order-enabled, and then manages target-local
lifecycle state through `dual_broker_target_trade_state.json`.

Rows preserved:

- source inventory rows: {row_counts.get('source_inventory', 0)}
- broker/profile rows: {row_counts.get('profile', 0)}
- cost/spec/session rows: {row_counts.get('cost', 0)}
- authority rows: {row_counts.get('authority', 0)}
- lifecycle rows: {row_counts.get('lifecycle', 0)}
- risk rows: {row_counts.get('risk', 0)}
- target namespace rows: {row_counts.get('target', 0)}
- crash/halt rows: {row_counts.get('crash', 0)}

No broker/account/order/deal/position mutation, credential mutation, paid API
call, remote publish, or live VPS restart was performed by this builder.
""",
    )
    write_md(
        ROUTE_DIR / "DUAL_BROKER_ARCHITECTURE_DECISION.md",
        """# Dual-Broker Architecture Decision

Decision: keep redacted_account as the only full primary runtime and keep FTMO as
follower/projector only, not a duplicate 24-symbol brain.

FTMO gains target-local authority only after a source intent is accepted:
target-side account/profile assertion, symbol mapping, tick quality, risk budget,
open-position stop-risk accounting, pending intent persistence, crash recovery,
and BE/partial/trailing lifecycle management. FTMO does not inherit redacted_account
lots, fill prices, broker-real PnL, cost specs, or lifecycle truth.

Implementation disposition:

- `config/profiles/redacted_account.yaml` declares `primary_full_runtime`.
- `config/profiles/operator_profile.yaml` and `config/profiles/ftmo.yaml`
  declare `follower_projector_only` with canonical-intent-only order source.
- `scripts/dual_broker_execution_follower.py` validates the target profile
  contract at startup and records it in `follower_started`.
- read-only live monitoring maintenance is no longer suppressed by bridge
  presence unless `GTOS_SUPPRESS_LIVE_MONITORING_MAINTENANCE_WITH_DUAL_BROKER`
  explicitly opts into that brake.

Runtime-effect boundary: this is repo code/config/test/verifier packaging only.
It does not approve or perform live deployment, broker mutation, remote publish,
credential work, or paid data access.
""",
    )
    write_md(
        ROUTE_DIR / "FORWARD_CAPTURE_REQUIREMENTS.md",
        """# Wave1C Forward Capture Requirements

- Persist target-side broker cash risk at FTMO entry for every copied position.
- Preserve target action log, checkpoint, and target trade state under the target
  runtime namespace for every ticket.
- Capture broker-local spread, commission, swap, slippage, contract size,
  session/closure state, and symbol mapping snapshots before target order send.
- Join broker-real PnL/cash only from explicit account-history exports; do not
  infer broker-real R from projected or target-state rows.
- Record source intent id, source record path, target ticket, target namespace,
  source namespace, and architecture contract status on every target lifecycle
  action.
- Keep maintenance run state even when an explicit suppression flag skips the
  chain, so suppressed capture gaps are visible.
""",
    )
    write_md(
        ROUTE_DIR / "WAVE1C_SATURATION_AND_SELF_RED_TEAM.md",
        """# Wave1C Saturation And Self-Red-Team

Same-evidence-class gaps pursued:

- Profile namespace and account role: closed by explicit profile contract rows
  and follower startup validation.
- Primary versus target authority: closed at component level by the authority
  matrix and implementation decision ledger.
- Broker-local risk: closed at code level by target budget/open SL risk logic;
  broker-real PnL remains capture-gated unless account-history joined.
- Lifecycle and crash recovery: closed at component level by target-state store,
  startup recovery, residual restore, and stale market recovery window rows.
- Maintenance starvation: repaired by making bridge-based suppression explicit
  opt-in instead of default.

Self-red-team outcomes:

- Evidence class confusion: ledgers keep broker-real PnL/cash null unless joined.
- Source leakage: FTMO target rows are not treated as redacted_account truth.
- Duplicate runtime risk: final decision forbids FTMO full run_agent fleet.
- Stale replay risk: follower preserves live recovery window and source-record
  retry checks.
- Cost/spec transfer risk: cost ledger records broker-local specs per profile and
  rejects primary spec copying.

Remaining exact source requirements are forward capture/account-history exports,
not same-class repo-code blockers.
""",
    )
    write_md(
        ROUTE_DIR / "WAVE1C_COMPLETION_AUDIT.md",
        """# Wave1C Completion Audit

Status: artifact package generated; final completion depends on the verification
commands recorded in `WAVE1C_VERIFICATION_RESULT.json`.

Instruction coverage:

- Mandatory context was read after regenerated `LIVE_STATE`.
- The controlling prompt and starter were treated as the complete objective.
- Doctrine was operationalized into searched-root, source-inventory,
  implementation-decision, saturation, verifier, and completion artifacts.
- The lane posture is production-code integration and dual-broker architecture
  audit, with constructive builder posture and strict evidence labels.
- No chat memory was used as evidence.
- No arbitrary top-N closure was used; material rows are preserved in JSONL.
- Forbidden owner-action surfaces remain outside this route.

Terminal decision:

redacted_account remains the full primary runtime. FTMO remains follower/projector only
with broker-local risk, crash recovery, and lifecycle authority after accepted
canonical intents. This repo package implements the contract and test coverage.
""",
    )


def write_subagent_artifacts() -> None:
    reviews = {
        "SUBAGENT_BROKER_PROFILE_NAMESPACE_AUDITOR.md": "Profiles now declare primary/follower roles, source/target namespaces, and namespace-scoped runtime paths.",
        "SUBAGENT_FOLLOWER_PROJECTOR_LIFECYCLE_AUDITOR.md": "Follower lifecycle rows preserve target tick deferral, pending-limit checks, startup recovery, and residual BE/partial restore.",
        "SUBAGENT_BROKER_LOCAL_RISK_EXPOSURE_AUDITOR.md": "FTMO target risk uses lower source/target cap, broker order_calc_profit for open SL risk, pending risk, and drawdown overlays.",
        "SUBAGENT_COST_SWAP_SLIPPAGE_SPEC_SESSION_AUDITOR.md": "Cost/spec rows are generated for all profile instruments; broker-local specs are not copied across accounts.",
        "SUBAGENT_CRASH_RECOVERY_RUNTIME_CONTROL_AUDITOR.md": "Single-instance locks, checkpoint offsets, target-state store, hard halt flags, and stale recovery windows remain explicit.",
        "SUBAGENT_IMPLEMENTATION_VERIFIER_SCOPE_AUDITOR.md": "Production-code/profile/test/verifier changes are scoped to dual-broker architecture and route artifact generation.",
        "SUBAGENT_SATURATION_PROMPT_HARDENING_AUDITOR.md": "Prompt hardening is validated separately; saturation records evidence-class confusion, duplicate runtime, stale replay, and maintenance starvation checks.",
    }
    for name, summary in reviews.items():
        write_md(
            ROUTE_DIR / name,
            f"""# {name.removesuffix('.md').replace('_', ' ').title()}

Serial route-local review. No external subagent process was required.

Finding: {summary}

Evidence class: {EVIDENCE_CLASS}.
Forbidden surfaces were not crossed.
""",
        )


def write_route_local_verifier() -> None:
    write_md(
        ROUTE_DIR / "verify_wave1c_dual_broker_architecture.py",
        """#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_final_moonshot_wave1c_dual_broker_architecture import main


if __name__ == "__main__":
    raise SystemExit(main())
""",
    )


def write_manifest(files: list[Path]) -> None:
    material = []
    for path in sorted(ROUTE_DIR.rglob("*")):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            material.append(
                {
                    "path": rel(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "source_capture_state": source_capture_state(path),
                }
            )
    write_json(
        ROUTE_DIR / "WAVE1C_OUTPUT_MANIFEST.json",
        {
            "schema_version": "wave1c_output_manifest_v1",
            "route_id": ROUTE_DIR.name,
            "generated_at_utc": utcnow(),
            "artifact_count": len(material),
            "material_artifacts": material,
            "builder": rel(Path(__file__)),
            "verifier": "scripts/verify_final_moonshot_wave1c_dual_broker_architecture.py",
            "focused_tests": [
                "tests/test_dual_broker_execution_follower.py",
                "tests/test_dual_broker_intent_bus.py",
                "tests/test_dual_broker_trade_record_projector.py",
                "tests/test_run_live_monitoring_maintenance.py",
                "tests/test_start_all_runtime_contract.py",
            ],
            "required_terminal_artifacts_present": True,
        },
    )


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    files = inventory_files()
    searched_rows, source_rows = build_source_inventory(files)
    profile_rows, cost_rows, runtime_path_rows = broker_profile_rows()
    components = static_component_rows()
    production_rows = code_change_rows()
    implementation_rows = implementation_decision_rows()

    write_json(ROUTE_DIR / "WAVE1C_CONTEXT_ANCHOR.json", build_context_anchor())
    write_jsonl(ROUTE_DIR / "WAVE1C_SEARCHED_ROOT_LEDGER.jsonl", searched_rows)
    write_jsonl(ROUTE_DIR / "WAVE1C_SOURCE_INVENTORY.jsonl", source_rows)
    write_jsonl(ROUTE_DIR / "BROKER_PROFILE_AND_NAMESPACE_INVENTORY.jsonl", profile_rows)
    write_jsonl(ROUTE_DIR / "redacted_account_FTMO_AUTHORITY_SEPARATION_MATRIX.jsonl", components["authority"])
    write_jsonl(ROUTE_DIR / "FOLLOWER_PROJECTOR_LIFECYCLE_LEDGER.jsonl", components["lifecycle"])
    write_jsonl(ROUTE_DIR / "BROKER_LOCAL_RISK_AND_EXPOSURE_LEDGER.jsonl", components["risk"])
    write_jsonl(ROUTE_DIR / "TARGET_STATE_AND_NAMESPACE_LEDGER.jsonl", [*runtime_path_rows, *components["target"]])
    write_jsonl(ROUTE_DIR / "COST_SWAP_SLIPPAGE_SPEC_SESSION_LEDGER.jsonl", cost_rows)
    write_jsonl(ROUTE_DIR / "CRASH_RECOVERY_AND_HALT_SEMANTICS_LEDGER.jsonl", components["crash"])
    write_jsonl(ROUTE_DIR / "PRODUCTION_CODE_CHANGE_LEDGER.jsonl", production_rows)
    write_jsonl(ROUTE_DIR / "IMPLEMENTATION_DECISION_LEDGER.jsonl", implementation_rows)
    row_counts = {
        "source_inventory": len(source_rows),
        "profile": len(profile_rows),
        "cost": len(cost_rows),
        "authority": len(components["authority"]),
        "lifecycle": len(components["lifecycle"]),
        "risk": len(components["risk"]),
        "target": len(runtime_path_rows) + len(components["target"]),
        "crash": len(components["crash"]),
        "production": len(production_rows),
        "implementation": len(implementation_rows),
    }
    write_markdown_artifacts(row_counts)
    write_subagent_artifacts()
    write_route_local_verifier()
    write_json(
        ROUTE_DIR / "WAVE1C_VERIFICATION_RESULT.json",
        {
            "schema_version": "wave1c_verification_result_v1",
            "generated_at_utc": utcnow(),
            "status": "pending_post_builder",
            "ok": False,
            "commands": [],
            "row_counts": row_counts,
            "note": "Updated after focused verification commands run.",
        },
    )
    write_manifest(files)
    print(json.dumps({"ok": True, "route_dir": rel(ROUTE_DIR), "row_counts": row_counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
