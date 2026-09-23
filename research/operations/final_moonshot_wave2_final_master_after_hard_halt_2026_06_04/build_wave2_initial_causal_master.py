#!/usr/bin/env python3
"""Build the initial Wave2 causal-microscope spine from accepted Wave1 evidence.

This is intentionally an initial, repeatable evidence spine. It does not mark
Wave2 complete; it preserves the full broker/candidate/live-authority row
universe that later Wave2 passes must deepen.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
GENERATED_AT = datetime.now(timezone.utc).isoformat()

WAVE1A = Path("research/operations/final_moonshot_wave1a_hard_halt_forensic_matrix_2026_06_04")
WAVE1B = Path("research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04")
WAVE1C = Path("research/operations/final_moonshot_wave1c_dual_broker_architecture_2026_06_04")
WAVE1I = Path("research/operations/final_moonshot_wave1_integration_review_2026_06_04")
HARD_HALT = Path("research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03")
LIVE_FAILURE = Path("research/operations/final_moonshot_live_failure_intelligence_2026_06_04")
DUAL_SUPERVISOR = Path("research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02")
GOAL_ARCH = Path("research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04")
CONTROLLING_PROMPT = Path("research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_GOAL_PROMPT_2026-06-04.md")

W1A_MATRIX = WAVE1A / "BROKER_TRADE_CANDIDATE_FORENSIC_MATRIX.jsonl"
W1A_SELECTOR = WAVE1A / "SELECTOR_WEAKNESS_LEDGER.jsonl"
W1A_MFE = WAVE1A / "MFE_MAE_TIME_IN_TRADE_LEDGER.jsonl"
W1A_GIVEBACK = WAVE1A / "PROFIT_RETENTION_AND_GIVEBACK_LEDGER.jsonl"
W1A_COST = WAVE1A / "COST_SWAP_SLIPPAGE_LEDGER.jsonl"
W1A_GAPS = WAVE1A / "DATA_GAP_AND_SOURCE_REPAIR_LEDGER.jsonl"
W1B_MATRIX = WAVE1B / "LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl"
W1B_V3_DISPOSITION = WAVE1B / "V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl"
W1B_REPAIRS = WAVE1B / "WAVE1B_REPAIR_REQUIREMENT_LEDGER.jsonl"
W1C_AUTHORITY = WAVE1C / "redacted_account_FTMO_AUTHORITY_SEPARATION_MATRIX.jsonl"
W1C_PROFILES = WAVE1C / "BROKER_PROFILE_AND_NAMESPACE_INVENTORY.jsonl"
W1C_COST = WAVE1C / "COST_SWAP_SLIPPAGE_SPEC_SESSION_LEDGER.jsonl"
W1C_DECISIONS = WAVE1C / "IMPLEMENTATION_DECISION_LEDGER.jsonl"


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return {
        "cmd": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def sha256_file(path: Path) -> str | None:
    full = REPO_ROOT / path
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    full = REPO_ROOT / path
    with full.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def read_jsonl_lenient(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    full = REPO_ROOT / path
    if not full.exists():
        return rows, [f"missing:{path.as_posix()}"]
    with full.open(encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception as exc:  # noqa: BLE001 - lenient source coverage ledger records parse gaps.
                errors.append(f"{path.as_posix()}:{line_no}:{exc}")
                continue
            if isinstance(payload, dict):
                rows.append(payload)
            else:
                errors.append(f"{path.as_posix()}:{line_no}:not_object")
    return rows, errors


def write_json(name: str, payload: Any) -> None:
    (ROUTE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(name: str, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with (ROUTE_DIR / name).open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def write_md(name: str, text: str) -> None:
    (ROUTE_DIR / name).write_text(text.strip() + "\n", encoding="utf-8")


def file_stat(path: Path) -> dict[str, Any]:
    full = REPO_ROOT / path
    exists = full.exists()
    rows = None
    if exists and full.is_file() and path.suffix == ".jsonl":
        rows = sum(1 for _ in read_jsonl(path))
    return {
        "path": path.as_posix(),
        "exists": exists,
        "kind": "directory" if exists and full.is_dir() else "file" if exists else "missing",
        "size_bytes": full.stat().st_size if exists and full.is_file() else None,
        "sha256": sha256_file(path),
        "jsonl_rows": rows,
    }


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in counter.most_common()}


def none_like(value: Any) -> bool:
    return value in (None, "", [], {})


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def nested_get(payload: Any, *keys: str) -> Any:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def read_optional_trade_record(row: dict[str, Any]) -> tuple[dict[str, Any], str]:
    source_path = row.get("source_path")
    if not source_path:
        return {}, "missing_source_path"
    path = REPO_ROOT / str(source_path)
    if not path.exists():
        return {}, "source_path_missing_on_disk"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - route artifact records source repair need.
        return {}, f"json_read_error:{exc}"
    if not isinstance(payload, dict):
        return {}, "source_payload_not_object"
    return payload, "source_payload_loaded"


def target_multiple_from_order(row: dict[str, Any], order: dict[str, Any]) -> float | None:
    entry = safe_float(row.get("entry_price"))
    sl = safe_float(order.get("sl"))
    tp = safe_float(order.get("tp"))
    if entry is None or sl is None or tp is None:
        return None
    side = str(row.get("side") or "").upper()
    if side == "BUY":
        risk = entry - sl
        reward = tp - entry
    elif side == "SELL":
        risk = sl - entry
        reward = entry - tp
    else:
        return None
    if risk <= 0 or reward <= 0:
        return None
    return round(reward / risk, 6)


def target_bucket(value: float | None, tolerance: float) -> str:
    if value is None:
        return "missing"
    for label, target in (("near_1_5r", 1.5), ("near_2r", 2.0), ("near_3r", 3.0), ("near_6r", 6.0)):
        if abs(value - target) <= tolerance:
            return label
    return "other"


def orders_by_position(orders: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in orders:
        position_id = order.get("position_id")
        if position_id not in (None, ""):
            out[str(position_id)].append(order)
    for position_orders in out.values():
        position_orders.sort(key=lambda item: item.get("time_setup_msc") or item.get("time_done_msc") or 0)
    return out


def jsonl_coverage(path: Path, keys: list[str], *, sample_limit: int = 3) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    coverage = Counter()
    first_keys: list[str] = []
    sample_rows: list[dict[str, Any]] = []
    full = REPO_ROOT / path
    if not full.exists():
        return {
            "source_path": path.as_posix(),
            "exists": False,
            "row_count": 0,
            "parse_errors": 0,
            "coverage": {key: 0 for key in keys},
            "first_row_keys": [],
            "sample_rows": [],
        }
    with full.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:  # noqa: BLE001 - source coverage records parse quality only.
                parse_errors += 1
                continue
            if not isinstance(payload, dict):
                parse_errors += 1
                continue
            rows += 1
            if not first_keys:
                first_keys = sorted(payload.keys())
            if len(sample_rows) < sample_limit:
                sample_rows.append({key: payload.get(key) for key in list(payload.keys())[:20]})
            for key in keys:
                if payload.get(key) not in (None, "", [], {}):
                    coverage[key] += 1
    return {
        "source_path": path.as_posix(),
        "exists": True,
        "row_count": rows,
        "parse_errors": parse_errors,
        "coverage": {key: int(coverage.get(key, 0)) for key in keys},
        "first_row_keys": first_keys,
        "sample_rows": sample_rows,
    }


def row_id(row: dict[str, Any], fallback: str) -> str:
    for key in ("row_id", "position_id", "candidate_id", "material_row_id", "trade_id"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


def status_for_trade(row: dict[str, Any]) -> str:
    gaps = []
    if none_like(row.get("joined_trade_record_path")):
        gaps.append("candidate_runtime_join_missing")
    if none_like(row.get("exact_r")):
        gaps.append("exact_r_missing")
    if none_like(row.get("mfe_r")) or none_like(row.get("mae_r")):
        gaps.append("mfe_mae_missing")
    if row.get("win_loss") == "loss" and none_like(row.get("mfe_r")):
        gaps.append("loser_max_profitability_uncomputed")
    return "initial_row_fact_with_gaps:" + ",".join(gaps) if gaps else "initial_row_fact_compute_available"


def build_context_anchor() -> dict[str, Any]:
    return {
        "route": rel(ROUTE_DIR),
        "generated_at_utc": GENERATED_AT,
        "lane": "wave2_final_master_after_hard_halt_initial_causal_spine",
        "completion_status": "incomplete_initial_spine_only",
        "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_GOAL_PROMPT_2026-06-04.md",
        "starter": "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_STARTER_2026-06-04.txt",
        "preflight_commands": {
            "branch": run(["git", "branch", "--show-current"]),
            "head": run(["git", "rev-parse", "HEAD"]),
            "main": run(["git", "rev-parse", "main"]),
            "origin_main": run(["git", "rev-parse", "origin/main"]),
            "status_short": run(["git", "status", "--short"]),
        },
        "mandatory_context_read_status": {
            "AGENTS.md": True,
            ".context/LIVE_STATE.md": True,
            ".context/00_core/portable_path_authority.md": True,
            ".context/00_core/current_repo_reading_order.md": True,
            ".context/00_core/current_vnext_system_map.md": True,
            ".context/00_core/quick_reference_card.md": True,
            ".context/00_core/research_operating_doctrine.md": True,
            ".context/00_core/goal_session_research_discipline.md": True,
            ".context/00_core/orchestrator_methodology_hardening_controls.md": True,
            ".context/00_core/parallel_goal_merge_playbook.md": True,
            ".context/00_core/final_moonshot_post_hard_halt_research_plan.md": True,
            ".context/00_core/final_moonshot_goal_session_execution_architecture.md": True,
            ".context/00_core/final_moonshot_central_orchestrator_successor_brief.md": True,
        },
        "doctrine_posture": {
            "lane_type": "builder_integration_master_orchestration_not_g12_g0_audit",
            "builder_posture": [
                "curiosity",
                "truthfulness",
                "active_creativity",
                "result_materialization",
                "full_same_evidence_class_pursuit",
                "no_conservative_brake",
            ],
            "forbidden_surfaces": [
                "live_trading_deployment",
                "broker_operation_or_mutation",
                "paid_api_or_vendor_calls",
                "credentials",
                "active_vps_process_changes",
                "remote_push",
            ],
        },
    }


def build_source_inventory() -> list[dict[str, Any]]:
    paths = [
        W1A_MATRIX,
        W1A_SELECTOR,
        W1A_MFE,
        W1A_GIVEBACK,
        W1A_COST,
        W1A_GAPS,
        WAVE1A / "WAVE1A_VERIFICATION_RESULT.json",
        WAVE1A / "WAVE1A_OUTPUT_MANIFEST.json",
        W1B_MATRIX,
        W1B_V3_DISPOSITION,
        W1B_REPAIRS,
        WAVE1B / "WAVE1B_VERIFICATION_RESULT.json",
        WAVE1B / "WAVE1B_OUTPUT_MANIFEST.json",
        W1C_AUTHORITY,
        W1C_PROFILES,
        W1C_COST,
        W1C_DECISIONS,
        WAVE1C / "WAVE1C_VERIFICATION_RESULT.json",
        WAVE1C / "WAVE1C_OUTPUT_MANIFEST.json",
        WAVE1I / "WAVE1_INTEGRATION_VERIFICATION_RESULT.json",
        WAVE1I / "WAVE1_INTEGRATION_DECISION_LEDGER.jsonl",
        HARD_HALT / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json",
        HARD_HALT / "BROKER_TRUTH_DEALS_2026_04_27_TO_HALT.json",
        HARD_HALT / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json",
        HARD_HALT / "TRADE_FAILURE_REVIEW_2026-06-03.md",
    ]
    rows = []
    for path in paths:
        stat = file_stat(path)
        stat.update(
            {
                "inventory_scope": "wave2_initial_terminal_input",
                "evidence_class": "terminal_wave1_or_broker_truth_source",
                "consume_status": "consumed_for_initial_causal_spine" if stat["exists"] else "missing_initial_source_gap",
                "source_capture_status": "current_disk_inspected",
            }
        )
        rows.append(stat)
    return rows


def build_searched_roots() -> list[dict[str, Any]]:
    roots = [WAVE1A, WAVE1B, WAVE1C, WAVE1I, HARD_HALT, LIVE_FAILURE, DUAL_SUPERVISOR, GOAL_ARCH, Path("shadow_logs"), Path("knowledge_base/redacted_account_live_bee34003/trade_records"), Path("config"), Path("src")]
    rows = []
    for root in roots:
        full = REPO_ROOT / root
        rows.append(
            {
                "generated_at_utc": GENERATED_AT,
                "root": root.as_posix(),
                "exists": full.exists(),
                "file_count": sum(1 for path in full.rglob("*") if path.is_file()) if full.exists() and full.is_dir() else (1 if full.exists() else 0),
                "search_method": "route_manifest_and_targeted_json_jsonl_code_scan",
                "evidence_class": "current_disk_source_search",
                "search_status": "searched_for_initial_wave2_spine" if full.exists() else "missing_root",
            }
        )
    return rows


def build_input_inspection(audit_summaries: dict[str, dict[str, Any]], counts: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
        ("wave1a", WAVE1A, "broker_candidate_forensic_matrix"),
        ("wave1b", WAVE1B, "v3_live_authority_gap"),
        ("wave1c", WAVE1C, "dual_broker_architecture"),
        ("wave1_integration", WAVE1I, "accepted_merge_review"),
    ]
    rows = []
    for route_id, route, role in routes:
        verifier_path = route / {
            "wave1a": "WAVE1A_VERIFICATION_RESULT.json",
            "wave1b": "WAVE1B_VERIFICATION_RESULT.json",
            "wave1c": "WAVE1C_VERIFICATION_RESULT.json",
            "wave1_integration": "WAVE1_INTEGRATION_VERIFICATION_RESULT.json",
        }[route_id]
        verifier = read_json(verifier_path) if (REPO_ROOT / verifier_path).exists() else {}
        rows.append(
            {
                "input_id": route_id,
                "role": role,
                "route_dir": route.as_posix(),
                "artifact_audit_ok": audit_summaries.get(route_id, {}).get("ok"),
                "artifact_audit_note": audit_summaries.get(route_id, {}).get("note"),
                "route_verifier_ok": verifier.get("ok"),
                "route_verifier_source": verifier_path.as_posix(),
                "row_counts_consumed": counts.get(route_id, {}),
                "evidence_class": "terminal_wave1_input_current_disk_verifier_and_audit",
                "result_use_status": "terminal_input_consumed_not_relaunched",
                "implementation_decision": "consume_as_wave2_initial_spine_input",
            }
        )
    return rows


def classify_market_vs_system(row: dict[str, Any]) -> str:
    tags = set(row.get("failure_tags") or [])
    symbol = row.get("symbol")
    if "dominant_damage_symbol" in tags or symbol in {"XAUUSD", "NDX100", "ETHUSD"}:
        return "bad_market_system_mismatch"
    if "stop_loss_or_broker_sl_exit" in tags:
        return "bad_system_logic"
    if row.get("source_completeness_status", "").startswith("complete_for_broker_cash_incomplete"):
        return "unknown_with_source_gap"
    return "unknown_with_source_gap"


def build_trade_rows(broker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in broker_rows:
        position = row.get("position_id")
        finding = (
            f"{row.get('symbol')} {row.get('side')} broker-real {row.get('win_loss')} "
            f"cash={row.get('broker_real_pnl_cash')} hold_minutes={row.get('hold_minutes')}"
        )
        missing_fields = []
        for field in ("joined_trade_record_path", "exact_r", "mfe_r", "mae_r", "commission", "swap", "slippage_price"):
            if none_like(row.get(field)):
                missing_fields.append(field)
        out.append(
            {
                "row_id": f"wave1a_broker_trade:{position}",
                "broker_position_id": position,
                "candidate_id": None,
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "time_window": {"entry_time_utc": row.get("entry_time_utc"), "last_time_utc": row.get("last_time_utc")},
                "source_paths": [W1A_MATRIX.as_posix(), HARD_HALT.as_posix()],
                "evidence_class": row.get("evidence_class"),
                "causal_surface": ["broker_truth", "selector", "execution_path", "cost", "exit_management", "portfolio_exposure"],
                "question_id": ["W2Q_SELECTOR_QUALITY", "W2Q_ENTRY_PATH_MFE_MAE", "W2Q_COST_BROKER_NET", "W2Q_BAD_MARKET_VS_SYSTEM"],
                "finding": finding,
                "metric_fields_used": {
                    "broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
                    "win_loss": row.get("win_loss"),
                    "proxy_r": row.get("proxy_r"),
                    "exact_r": row.get("exact_r"),
                    "mfe_r": row.get("mfe_r"),
                    "mae_r": row.get("mae_r"),
                    "hold_minutes": row.get("hold_minutes"),
                    "failure_tags": row.get("failure_tags"),
                },
                "missing_fields": missing_fields,
                "same_evidence_class_repairs_attempted": [
                    "consumed_wave1a_broker_truth_join",
                    "consumed_wave1a_candidate_trade_record_join_status",
                    "consumed_wave1a_mfe_mae_and_cost_ledgers",
                ],
                "status": status_for_trade(row),
                "market_vs_system_disposition": classify_market_vs_system(row),
                "v4_requirement_id": "V4_SELECTOR_SCHEDULER_EXECUTION_COST_PACKET",
                "owning_wave3_lane": "hard_halt_causal_microscope_continuation",
                "implementation_decision": row.get("implementation_decision"),
            }
        )
    return out


def build_candidate_rows(w1a_candidates: list[dict[str, Any]], w1b_rows: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for index, row in enumerate(w1a_candidates, start=1):
        missing_fields = [field for field in ("exact_r", "mfe_r", "mae_r", "selected_cell_profit_factor", "selected_cell_win_rate") if none_like(row.get(field))]
        yield {
            "row_id": f"wave1a_candidate:{index}:{row_id(row, str(index))}",
            "duplicate_source_row_key": row_id(row, str(index)),
            "source_family": "wave1a_candidate_trade_record",
            "broker_position_id": row.get("broker_position_id"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "time_window": row.get("decision_time_utc"),
            "source_paths": [row.get("source_path"), W1A_MATRIX.as_posix()],
            "evidence_class": row.get("evidence_class"),
            "causal_surface": ["candidate", "selector", "zero_trade", "execution_policy"],
            "question_id": ["W2Q_REJECT_SKIP_ZERO_TRADE", "W2Q_SELECTOR_QUALITY"],
            "finding": f"candidate final_outcome={row.get('final_outcome')} policy={row.get('execution_policy')} expectancy={row.get('expectancy_r_source_bound')}",
            "metric_fields_used": {
                "final_outcome": row.get("final_outcome"),
                "expectancy_r_source_bound": row.get("expectancy_r_source_bound"),
                "selected_cell_rows": row.get("selected_cell_rows"),
                "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
                "selected_cell_win_rate": row.get("selected_cell_win_rate"),
            },
            "missing_fields": missing_fields,
            "same_evidence_class_repairs_attempted": ["consumed_wave1a_candidate_payload_and_selector_weakness_fields"],
            "status": "initial_candidate_fact_preserved",
            "v4_requirement_id": "V4_SELECTOR_ZERO_TRADE_COMPARATOR",
            "owning_wave3_lane": "selector_v4_and_best_trade_allocator",
            "implementation_decision": row.get("implementation_decision"),
        }
    for index, row in enumerate(w1b_rows, start=1):
        missing_fields = [field for field in ("candidate_id", "exact_r", "proxy_r", "expectancy_r", "broker_net_pnl", "execution_policy_id") if none_like(row.get(field))]
        yield {
            "row_id": f"wave1b_live_authority:{row.get('material_row_id') or index}",
            "duplicate_source_row_key": row.get("material_row_id") or index,
            "source_family": row.get("source_row_kind"),
            "broker_position_id": None,
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "side": None,
            "time_window": row.get("timestamp_utc"),
            "source_paths": [row.get("source_file"), W1B_MATRIX.as_posix()],
            "evidence_class": row.get("evidence_class"),
            "causal_surface": ["live_authority", "candidate_funnel", "scheduler", "execution_policy", "capture"],
            "question_id": ["W2Q_FINAL_SAY_AUTHORITY", "W2Q_BEST_TRADE_ALLOCATOR", "W2Q_CAPTURE_GAPS"],
            "finding": f"{row.get('source_row_kind')} decision={row.get('decision_status')} authority={row.get('live_authority_classification')}",
            "metric_fields_used": {
                "decision_status": row.get("decision_status"),
                "candidate_action": row.get("candidate_action"),
                "live_authority_classification": row.get("live_authority_classification"),
                "v3_selector_status": row.get("v3_selector_status"),
                "v3_scheduler_status": row.get("v3_scheduler_status"),
                "v3_execution_status": row.get("v3_execution_status"),
            },
            "missing_fields": missing_fields,
            "same_evidence_class_repairs_attempted": ["consumed_wave1b_live_authority_matrix"],
            "status": "initial_live_authority_fact_preserved",
            "v4_requirement_id": "V4_LIVE_DECISION_PACKET_AND_FINAL_SAY",
            "owning_wave3_lane": "runtime_control_selector_scheduler_v4",
            "implementation_decision": row.get("implementation_decision"),
        }


def build_selector_ledger(broker_rows: list[dict[str, Any]], selector_rows: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for row in broker_rows:
        missing_quality = [field for field in ("selected_cell_win_rate", "selected_cell_profit_factor", "selected_cell_rows") if none_like(row.get(field))]
        yield {
            "row_id": f"broker_selector_quality:{row.get('position_id')}",
            "symbol": row.get("symbol"),
            "broker_position_id": row.get("position_id"),
            "evidence_class": row.get("evidence_class"),
            "broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
            "win_loss": row.get("win_loss"),
            "selected_cell_rows": row.get("selected_cell_rows"),
            "selected_cell_win_rate": row.get("selected_cell_win_rate"),
            "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
            "looseness_status": "broker_trade_quality_fields_missing" if missing_quality else "broker_trade_quality_fields_present",
            "missing_fields": missing_quality,
            "implementation_decision": row.get("implementation_decision"),
        }
    for row in selector_rows:
        yield {
            "row_id": f"wave1a_selector:{row.get('row_id')}",
            "symbol": row.get("symbol"),
            "broker_position_id": row.get("row_id"),
            "evidence_class": "source_bound_selected_cell_context",
            "expectancy_r_source_bound": row.get("expectancy_r_source_bound"),
            "selected_cell_rows": row.get("selected_cell_rows"),
            "selected_cell_win_rate": row.get("selected_cell_win_rate"),
            "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
            "looseness_status": row.get("selector_weakness_status"),
            "missing_fields": [field for field in ("selected_cell_win_rate", "selected_cell_profit_factor") if none_like(row.get(field))],
            "implementation_decision": row.get("implementation_decision"),
        }


def build_final_say_matrix(w1b_rows: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for row in w1b_rows:
        yield {
            "row_id": f"final_say:{row.get('material_row_id')}",
            "material_row_id": row.get("material_row_id"),
            "source_row_kind": row.get("source_row_kind"),
            "symbol": row.get("symbol"),
            "timestamp_utc": row.get("timestamp_utc"),
            "decision_status": row.get("decision_status"),
            "candidate_action": row.get("candidate_action"),
            "final_say_authority": row.get("live_authority_classification"),
            "v3_selector_status": row.get("v3_selector_status"),
            "v3_scheduler_status": row.get("v3_scheduler_status"),
            "v3_execution_status": row.get("v3_execution_status"),
            "cost_swap_slippage_state": row.get("cost_swap_slippage_state"),
            "source_capture_state": row.get("source_capture_state"),
            "source_completeness_state": row.get("source_completeness_state"),
            "evidence_class": row.get("evidence_class"),
            "implementation_decision": row.get("implementation_decision"),
        }


def build_questions(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    seeds = [
        ("W2Q_SELECTOR_QUALITY", "seed_prompt", "Was the live selector too loose and what rows prove weak trade admission?", "compare broker-real trade quality, selected-cell coverage, rejects/skips/no-trade, and V3/live authority rows", "selector_v4"),
        ("W2Q_ENTRY_PATH_MFE_MAE", "seed_prompt", "Did entries suffer adverse excursion before useful profit and what MFE/MAE/time-to-destination repair is possible?", "join broker trades to path/MFE/MAE/hold-time and repair missing source windows", "execution_manager_v4"),
        ("W2Q_LOSER_MFE_HARVEST", "seed_prompt", "For losing trades, what was maximum favorable profitability before loss and which harvest rule failed?", "compute loser MFE/giveback/consolidation/reversal or write exact path source gap", "profit_harvest_v4"),
        ("W2Q_STATIC_R_GEOMETRY", "owner_correction", "Was fixed/static 2R or 1.5R target geometry actually live authority, and did it help or hurt?", "join prompt/config/policy/broker TP/SL/path rows while separating risk percent from target R", "dynamic_target_stop_geometry_v4"),
        ("W2Q_FINAL_SAY_AUTHORITY", "seed_prompt", "Which surface had final say for every selected/filled/rejected row and which surfaces were capture-only?", "inspect Wave1B live authority rows and production code disposition", "livedecisionpacket_v4"),
        ("W2Q_BEST_TRADE_ALLOCATOR", "seed_prompt", "Would scarce risk capacity have selected no-trade, another symbol, smaller risk, delayed entry, or stale-exposure exit?", "build decision-window opportunity-cost comparison from candidate/open/pending rows", "scheduler_v4_best_trade_allocator"),
        ("W2Q_COST_BROKER_NET", "seed_prompt", "Did cost, spread, slippage, commission, swap, broker hours, or symbol specs convert gross ideas into broker-net weakness?", "join Wave1A cost rows, Wave1C broker specs, and broker deals/orders", "cost_swap_slippage_engine"),
        ("W2Q_BAD_MARKET_VS_SYSTEM", "seed_prompt", "Was the hard halt bad market, bad system, or failure to recognize bad market?", "classify every trade/candidate with market-state and counterfactual no-trade evidence", "market_whiteboard_v2"),
        ("W2Q_REJECT_SKIP_ZERO_TRADE", "seed_prompt", "Which rejected/skipped/no-trade rows were correct zero-trades versus missed better choices?", "preserve all candidate/runtime rows and compare selected versus alternatives", "selector_v4_zero_trade"),
        ("W2Q_CAPTURE_GAPS", "seed_prompt", "Which non-generatable historical fields must LiveDecisionPacketV4 capture prospectively?", "emit row-level missing candidate/cost/path/lifecycle/final-say fields", "data_capture_source_repair_final"),
        ("W2Q_DUAL_BROKER_CONSTRAINTS", "seed_prompt", "How must redacted_account primary and FTMO follower/projector-only architecture constrain V4?", "consume Wave1C authority separation and broker-local cost/risk ledgers", "dual_broker_runtime_contract"),
        ("W2Q_VALIDATION_REPLAY", "seed_prompt", "What can be answered now by historical replay/sealed validation rather than waiting for live rows?", "map missing exact truth versus replayable market/path/cost evidence", "historical_replay_digital_twin_v4"),
        ("W2Q_AI_RELIABILITY", "seed_prompt", "What role should AI have after hard halt without becoming an unguarded main actor?", "separate no-API replay from AI decision-value/reliability/cost-control audits", "ai_reliability_cost_control"),
    ]
    discovered = [
        ("W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE", "row_anomaly", "XAUUSD/NDX100/ETHUSD dominated damage; should V4 quarantine recent-damage symbol/session cells before trade admission?", "broker-real symbol partitions and SL-damage rows", "selector_v4_market_health"),
        ("W2Q_MISSING_BROKER_TRADE_GEOMETRY", "source_gap", "Many broker-real rows lack candidate/runtime joins, exact-R, MFE/MAE, cost, and target geometry; which are repairable now?", "Wave1A join/source completeness statuses and data-gap ledgers", "hard_halt_causal_microscope_continuation"),
        ("W2Q_V3_DEFAULT_OFF_LIVE_DIVERGENCE", "code_config", "Wave1B live rows show V3 packages were not full live authority; how should V3 be demoted, staged, or mined for V4?", "Wave1B final-say and V3 component ledgers", "v3_to_v4_disposition"),
        ("W2Q_PENDING_NOFILL_AS_FIRST_CLASS", "row_anomaly", "Pending/no-fill lifecycle rows are material source truth; which missed-entry/no-fill rows imply better execution policy?", "Wave1B pending lifecycle source rows", "pending_nofill_lifecycle_v4"),
        ("W2Q_FTMO_NO_COPY_RULE", "interaction_effect", "FTMO follower cannot copy redacted_account lots/fills/cash/specs; every V4 contract must enforce broker-local risk and lifecycle.", "Wave1C authority separation rows", "dual_broker_runtime_contract"),
    ]
    rows = []
    for question_id, origin, hypothesis, test, lane in seeds + discovered:
        if question_id == "W2Q_BEST_TRADE_ALLOCATOR":
            pursuit_actions = [
                "initial_wave1_input_scan",
                "initial_causal_spine_materialized",
                "grouped_471_wave1a_candidate_rows_into_96_timestamp_windows",
                "materialized_per_window_selected_vs_alternative_and_best_trade_allocator_ledgers",
            ]
            repairs_attempted = [
                "wave1_terminal_artifact_consumption",
                "timestamp_grouped_decision_window_reconstruction",
            ]
            result_artifact = (
                "WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl;"
                "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl;"
                "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl"
            )
            status = "answered_with_source_bound_inferred_windows_runtime_intent_still_non_generatable"
            remaining_test = (
                "capture original runtime decision_window_id, candidate_set_id, allocator output, open/pending snapshot, "
                "stale exposure opportunity cost, zero-trade runtime value, fill probability, and broker-net EV per unit risk"
            )
        elif question_id == "W2Q_LOSER_MFE_HARVEST":
            pursuit_actions = [
                "initial_wave1_input_scan",
                "initial_causal_spine_materialized",
                "tick_recomputed_29_loser_mfe_mae_giveback_reversal_rows",
                "materialized_profit_path_consolidation_reversal_ledger",
            ]
            repairs_attempted = [
                "wave1_terminal_artifact_consumption",
                "tick_parquet_loser_path_recompute",
                "near_mfe_consolidation_dwell_and_range_proxy",
            ]
            result_artifact = (
                "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl;"
                "WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl;"
                "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl"
            )
            status = "answered_with_source_bound_tick_loser_mfe_reversal_runtime_policy_still_required"
            remaining_test = "implement and validate V4 harvest/BE/trailing/time-stop policy from tick-repaired loser path evidence"
        elif question_id == "W2Q_ENTRY_PATH_MFE_MAE":
            pursuit_actions = [
                "initial_wave1_input_scan",
                "initial_causal_spine_materialized",
                "tick_recomputed_55_filled_trade_first_passage_mfe_mae_ttd_rows",
                "materialized_entry_path_and_time_to_destination_ledgers",
            ]
            repairs_attempted = [
                "wave1_terminal_artifact_consumption",
                "tick_parquet_filled_trade_path_recompute",
                "broker_truth_minus_3h_close_time_repair_where_needed",
            ]
            result_artifact = (
                "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl;"
                "WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl;"
                "WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl"
            )
            status = "answered_with_source_bound_tick_path_repair_partial_tick_source_gaps_bounded"
            remaining_test = "extend V4 execution manager and prospective packet capture for partial/no-window tick source gaps and live runtime path policy"
        elif question_id == "W2Q_STATIC_R_GEOMETRY":
            pursuit_actions = [
                "initial_wave1_input_scan",
                "initial_causal_spine_materialized",
                "joined_candidate_raw_rr_dynamic_policy_and_broker_initial_sltp_geometry",
                "audited_sltp_modify_lifecycle_source_coverage_for_77_broker_positions",
            ]
            repairs_attempted = [
                "wave1_terminal_artifact_consumption",
                "hard_halt_broker_orders_initial_sltp_join",
                "trade_record_execution_policy_geometry_join",
            ]
            result_artifact = (
                "WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl;"
                "WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl;"
                "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl"
            )
            status = "answered_with_source_bound_initial_sltp_and_geometry_full_modify_lifecycle_not_captured"
            remaining_test = "capture every future SLTP modification, partial/BE/trailing/time-stop state, and runtime authority source in LiveDecisionPacketV4"
        else:
            pursuit_actions = ["initial_wave1_input_scan", "initial_causal_spine_materialized"]
            repairs_attempted = ["wave1_terminal_artifact_consumption"]
            result_artifact = "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl;WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl"
            status = "opened_initial_pursuit_not_exhausted"
            remaining_test = test
        rows.append(
            {
                "question_id": question_id,
                "origin": origin,
                "parent_question_ids": [],
                "trigger_source_path": "Wave2 controlling prompt" if origin in {"seed_prompt", "owner_correction"} else "terminal Wave1 input metrics",
                "trigger_row_ids": [],
                "trigger_field_values": metrics.get("headline", {}),
                "hypothesis": hypothesis,
                "falsification_test": remaining_test,
                "pursuit_actions": pursuit_actions,
                "same_evidence_class_repairs_attempted": repairs_attempted,
                "result_artifact": result_artifact,
                "status": status,
                "downstream_v4_requirement_id": lane,
                "derived_wave3_lane": lane,
            }
        )
    return rows


def build_interactions() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    edges = [
        ("candidate_generation", "selector_final_say", "weak admission and zero-trade comparator must be explicit"),
        ("selector_final_say", "scheduler_allocator", "accepted candidates must compete for scarce risk capacity"),
        ("scheduler_allocator", "execution_manager", "allocated candidate must use source-bound best entry and fillability"),
        ("execution_manager", "profit_harvest", "path/MFE/MAE must drive partial, BE, trailing, and time-stop"),
        ("profit_harvest", "broker_truth", "gross path must reconcile to broker-net cash and cost"),
        ("broker_truth", "market_whiteboard", "loss clusters must update bad-market/bad-system separators"),
        ("runtime_control", "halt_capture", "halt must be atomic and evidence-preserving"),
        ("redacted_account_primary", "ftmo_follower_projector", "only canonical accepted intents cross broker boundary"),
    ]
    graph = {
        "generated_at_utc": GENERATED_AT,
        "nodes": sorted(set([node for pair in edges for node in pair[:2]])),
        "edges": [
            {"interaction_id": f"W2INT-{idx:03d}", "from_surface": a, "to_surface": b, "interaction_hypothesis": hypothesis}
            for idx, (a, b, hypothesis) in enumerate(edges, start=1)
        ],
    }
    ledger = []
    for idx, (a, b, hypothesis) in enumerate(edges, start=1):
        ledger.append(
            {
                "interaction_id": f"W2INT-{idx:03d}",
                "from_surface": a,
                "to_surface": b,
                "row_ids": [],
                "candidate_ids": [],
                "broker_position_ids": [],
                "question_ids": ["W2Q_SELECTOR_QUALITY", "W2Q_FINAL_SAY_AUTHORITY", "W2Q_ENTRY_PATH_MFE_MAE"],
                "interaction_hypothesis": hypothesis,
                "evidence": "initial interaction derived from Wave1 accepted evidence and Wave2 prompt; row-level expansion pending",
                "counterfactual_decision": "requires row-level Wave2 continuation",
                "v4_requirement_id": f"V4_INTERACTION_{idx:03d}",
                "status": "opened_initial_interaction_not_exhausted",
                "source_gap_if_any": "row-level counterfactual path/allocation join pending",
            }
        )
    return graph, ledger


def build_metrics(w1a_rows: list[dict[str, Any]], w1b_rows: list[dict[str, Any]], w1c_authority: list[dict[str, Any]]) -> dict[str, Any]:
    broker = [row for row in w1a_rows if row.get("row_type") == "broker_grouped_trade"]
    candidates = [row for row in w1a_rows if row.get("row_type") == "candidate_trade_record"]
    by_symbol: dict[str, dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "net_pnl": 0.0})
    for row in broker:
        symbol = str(row.get("symbol"))
        by_symbol[symbol]["trades"] += 1
        by_symbol[symbol]["wins"] += 1 if row.get("win_loss") == "win" else 0
        by_symbol[symbol]["losses"] += 1 if row.get("win_loss") == "loss" else 0
        by_symbol[symbol]["net_pnl"] += float(row.get("broker_real_pnl_cash") or 0.0)

    broker_missing_quality = sum(1 for row in broker if none_like(row.get("selected_cell_win_rate")) or none_like(row.get("selected_cell_profit_factor")))
    w1b_trade_ready = sum(1 for row in w1b_rows if row.get("decision_status") in {"vnext_candidate_ready", "closed_trade"})
    w1b_v3_missing = sum(1 for row in w1b_rows if "default_off" in str(row.get("v3_selector_status")) or "packet_missing" in str(row.get("v3_selector_status")))

    return {
        "generated_at_utc": GENERATED_AT,
        "headline": {
            "wave1a_broker_trades": len(broker),
            "wave1a_candidate_trade_records": len(candidates),
            "wave1b_live_authority_rows": len(w1b_rows),
            "wave1c_authority_rows": len(w1c_authority),
            "broker_real_net_pnl_cash": round(sum(float(row.get("broker_real_pnl_cash") or 0.0) for row in broker), 2),
            "wins": sum(1 for row in broker if row.get("win_loss") == "win"),
            "losses": sum(1 for row in broker if row.get("win_loss") == "loss"),
        },
        "broker_quality": {
            "broker_rows_missing_selected_cell_win_rate_or_profit_factor": broker_missing_quality,
            "exact_r_present": sum(1 for row in broker if not none_like(row.get("exact_r"))),
            "proxy_r_present": sum(1 for row in broker if not none_like(row.get("proxy_r"))),
            "mfe_present": sum(1 for row in broker if not none_like(row.get("mfe_r"))),
            "mae_present": sum(1 for row in broker if not none_like(row.get("mae_r"))),
            "candidate_join_missing": sum(1 for row in broker if none_like(row.get("joined_trade_record_path"))),
            "stop_loss_or_broker_sl_exit_count": sum(1 for row in broker if "stop_loss_or_broker_sl_exit" in set(row.get("failure_tags") or [])),
        },
        "candidate_funnel_counts": {
            "wave1a_candidate_final_outcome_counts": counter_dict(Counter(row.get("final_outcome") for row in candidates)),
            "wave1b_source_row_kind_counts": counter_dict(Counter(row.get("source_row_kind") for row in w1b_rows)),
            "wave1b_decision_status_counts": counter_dict(Counter(row.get("decision_status") for row in w1b_rows)),
            "wave1b_candidate_action_counts": counter_dict(Counter(row.get("candidate_action") for row in w1b_rows)),
            "wave1b_live_authority_classification_counts": counter_dict(Counter(row.get("live_authority_classification") for row in w1b_rows)),
            "wave1b_selected_policy_counts": counter_dict(Counter(row.get("selected_policy") for row in w1b_rows if not none_like(row.get("selected_policy")))),
            "wave1b_trade_ready_or_closed_count": w1b_trade_ready,
            "wave1b_v3_selector_default_off_or_packet_missing_count": w1b_v3_missing,
        },
        "symbol_health": {
            symbol: {
                **stats,
                "net_pnl": round(stats["net_pnl"], 2),
                "win_rate": round(stats["wins"] / stats["trades"], 6) if stats["trades"] else None,
            }
            for symbol, stats in sorted(by_symbol.items(), key=lambda item: item[1]["net_pnl"])
        },
        "dual_broker": {
            "authority_counts": counter_dict(Counter(row.get("authority") for row in w1c_authority)),
            "runtime_disposition_counts": counter_dict(Counter(row.get("runtime_disposition") for row in w1c_authority)),
        },
        "result_use_status": "initial_wave2_metrics_for_causal_pursuit_not_completion",
    }


def build_blockers(gap_rows: list[dict[str, Any]], repair_rows: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for row in gap_rows:
        yield {
            "blocker_id": f"wave1a_gap:{row.get('row_id')}:{row.get('exact_missing_field')}",
            "source_path": W1A_GAPS.as_posix(),
            "evidence_class": "source_gap_or_prospective_capture_requirement",
            "missing_file_path_field_source": row.get("exact_missing_field"),
            "searched_roots_or_repairs": [row.get("repair_attempted")],
            "reason_repair_not_complete_in_initial_spine": row.get("repair_result"),
            "owner_access_source_capture_requirement": row.get("prospective_capture_requirement"),
            "downstream_lane": "data_capture_source_repair_final",
            "status": row.get("gap_status"),
        }
    for row in repair_rows:
        yield {
            "blocker_id": f"wave1b_repair:{row.get('repair_id')}",
            "source_path": W1B_REPAIRS.as_posix(),
            "evidence_class": row.get("evidence_class"),
            "missing_file_path_field_source": row.get("repair_requirement"),
            "searched_roots_or_repairs": row.get("source_paths"),
            "reason_repair_not_complete_in_initial_spine": "Wave1B repair requirement consumed; Wave2 row-level implementation/capture decision pending",
            "owner_access_source_capture_requirement": row.get("repair_requirement"),
            "downstream_lane": row.get("wave_owner"),
            "status": row.get("branch_decision"),
        }
    for blocker_id, requirement, lane in [
        ("wave2_static_r_geometry_join", "broker order TP/SL modify lifecycle plus candidate target multiple/policy-id join for every filled trade", "dynamic_target_stop_geometry_v4"),
        ("wave2_best_trade_allocator_window_join", "decision-window candidate set/open/pending exposure join for selected versus rejected/no-trade opportunity cost", "scheduler_v4_best_trade_allocator"),
        ("wave2_loser_mfe_consolidation_reversal", "source-bound price path around loser MFE timestamp, consolidation duration, and reversal level", "profit_harvest_v4"),
    ]:
        if blocker_id == "wave2_best_trade_allocator_window_join":
            yield {
                "blocker_id": blocker_id,
                "source_path": "Wave2 allocator timestamp-window repair",
                "evidence_class": "source_bound_reconstruction_plus_prospective_capture_requirement",
                "missing_file_path_field_source": requirement,
                "searched_roots_or_repairs": [
                    "Wave1A candidate_trade_record rows",
                    "WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl",
                    "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl",
                    "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl",
                ],
                "reason_repair_not_complete_in_initial_spine": (
                    "source-bound timestamp repair complete for 96 windows and 471 candidate rows; "
                    "original runtime allocator intent remains non-generatable without decision_window_id, "
                    "candidate_set_id, selected allocator output, open/pending snapshot, stale exposure cost, "
                    "fill probability, and broker-net EV per unit risk"
                ),
                "owner_access_source_capture_requirement": (
                    "LiveDecisionPacketV4 must capture durable decision_window_id, candidate_set_id, all candidates, "
                    "observed allocator output, open positions, pending orders, stale exposure opportunity cost, "
                    "zero-trade value, broker-net EV per unit risk, and fill probability"
                ),
                "downstream_lane": lane,
                "status": "timestamp_window_repair_complete_original_runtime_intent_capture_required",
            }
            continue
        if blocker_id == "wave2_static_r_geometry_join":
            yield {
                "blocker_id": blocker_id,
                "source_path": "Wave2 static-R and SLTP lifecycle source audit",
                "evidence_class": "source_bound_initial_geometry_plus_prospective_capture_requirement",
                "missing_file_path_field_source": requirement,
                "searched_roots_or_repairs": [
                    "hard_halt_broker_truth_orders",
                    "knowledge_base/redacted_account_live_bee34003/trade_records",
                    "WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl",
                    "WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl",
                    "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
                ],
                "reason_repair_not_complete_in_initial_spine": (
                    "candidate raw RR, dynamic policy geometry, and one initial broker SL/TP state were joined; "
                    "the available broker export has exactly one SLTP state per recent position and no full modify lifecycle, "
                    "so historical every-modify truth is non-generatable from current local sources"
                ),
                "owner_access_source_capture_requirement": (
                    "LiveDecisionPacketV4 and broker/order lifecycle capture must record every SLTP modification, "
                    "partial/BE/trailing/time-stop state, policy source, trigger R, target R, stop update, broker ticket, "
                    "and action/not-action reason per ticket"
                ),
                "downstream_lane": lane,
                "status": "initial_sltp_geometry_repair_complete_full_modify_lifecycle_capture_required",
            }
            continue
        if blocker_id == "wave2_loser_mfe_consolidation_reversal":
            yield {
                "blocker_id": blocker_id,
                "source_path": "Wave2 tick path repair",
                "evidence_class": "source_bound_tick_recompute_plus_v4_policy_requirement",
                "missing_file_path_field_source": requirement,
                "searched_roots_or_repairs": [
                    "data/ticks and package tick parquet",
                    "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl",
                    "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl",
                ],
                "reason_repair_not_complete_in_initial_spine": (
                    "source-bound historical repair complete for all 29 broker-real loser rows with full tick windows, "
                    "MFE timestamp, near-MFE dwell/range proxy, giveback timing, worst-after-MFE, and terminal giveback; "
                    "remaining work is V4 policy implementation and prospective lifecycle/partial/BE capture, not missing loser path reconstruction"
                ),
                "owner_access_source_capture_requirement": (
                    "Execution Manager V4 / Profit Harvest V4 must capture live MFE, near-MFE dwell/range, reversal/giveback thresholds, "
                    "partial/BE/trailing/time-stop decisions, and policy action/not-action reasons per ticket"
                ),
                "downstream_lane": lane,
                "status": "tick_loser_mfe_consolidation_reversal_repair_complete_v4_policy_required",
            }
            continue
        yield {
            "blocker_id": blocker_id,
            "source_path": "Wave2 initial causal spine",
            "evidence_class": "same_evidence_class_repair_required",
            "missing_file_path_field_source": requirement,
            "searched_roots_or_repairs": ["Wave1A", "Wave1B", "hard_halt_broker_truth"],
            "reason_repair_not_complete_in_initial_spine": "requires next Wave2 row-level join/replay pass; not yet impossible",
            "owner_access_source_capture_requirement": requirement,
            "downstream_lane": lane,
            "status": "open_same_evidence_class_pursuit_required",
        }


def build_decisions() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "consume_wave1_terminal_inputs_not_relaunch",
            "decision": "consume_wave1a_wave1b_wave1c_and_integration_as_terminal_current_disk_inputs",
            "evidence_class": "terminal_wave1_verifier_and_artifact_audit_evidence",
            "reason": "Current-session route verifiers and full JSONL artifact audits passed for accepted Wave1 inputs.",
            "implementation_decision": "build_wave2_causal_spine_from_disk_artifacts",
            "status": "decided_for_initial_spine",
        },
        {
            "decision_id": "preserve_all_material_rows_before_ranking",
            "decision": "preserve_77_broker_rows_471_wave1a_candidate_rows_and_12775_wave1b_authority_rows",
            "evidence_class": "full_ledger_preservation",
            "reason": "Wave2 controlling prompt forbids arbitrary top-N and requires every material row before ranking.",
            "implementation_decision": "write_every_trade_and_every_candidate_microscope_ledgers",
            "status": "implemented_initial_spine",
        },
        {
            "decision_id": "do_not_publish_wave3_prompt_pack_yet",
            "decision": "defer_wave3_prompt_pack_until_causal_model_v4_thesis_and_subagent_findings_are_integrated",
            "evidence_class": "route_completion_boundary",
            "reason": "Initial spine has not completed first-passage path repair, static-R joins, selected-versus-alternative allocation, or subagent finding integration.",
            "implementation_decision": "keep_wave2_active_not_complete",
            "status": "open",
        },
        {
            "decision_id": "keep_source_gaps_as_repairable_until_exhausted",
            "decision": "classify initial gaps as same-evidence-class pursuit unless Wave2 proves non-generatable truth",
            "evidence_class": "same_evidence_class_pursuit",
            "reason": "The route has not exhausted all path, target, broker-order, candidate-runtime, and replay joins.",
            "implementation_decision": "write_blocker_and_repair_ledger_with_open_pursuit_status",
            "status": "open",
        },
    ]


def build_focused_test_result() -> dict[str, Any]:
    commands = [
        run(
            [
                "python3",
                "-m",
                "py_compile",
                "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/build_wave2_initial_causal_master.py",
                "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/verify_wave2_initial_causal_master.py",
            ]
        )
    ]
    return {
        "ok": all(item["exit_code"] == 0 for item in commands),
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "test_scope": "initial_wave2_builder_and_verifier_syntax_compile",
        "commands": commands,
        "pytest_status": "not_run_for_initial_route_spine_no_runtime_code_changed",
        "status": "passed" if all(item["exit_code"] == 0 for item in commands) else "failed",
    }


def build_subagent_rows() -> list[dict[str, Any]]:
    return [
        {
            "role": "wave1a_broker_candidate_causality_reviewer",
            "objective": "inspect Wave1A broker/candidate/path/cost ledgers for Wave2 questions",
            "artifacts_files_inspected": [
                W1A_MATRIX.as_posix(),
                W1A_SELECTOR.as_posix(),
                W1A_MFE.as_posix(),
                W1A_GIVEBACK.as_posix(),
                W1A_COST.as_posix(),
                W1A_GAPS.as_posix(),
                (WAVE1A / "SYMBOL_SESSION_HEALTH_LEDGER.jsonl").as_posix(),
                (WAVE1A / "PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl").as_posix(),
            ],
            "material_findings": [
                "548 Wave1A matrix rows preserve 77 broker-real trades and 471 source-bound candidate trade records.",
                "Broker-real recent window is 31 wins, 46 losses, -859.69 cash, PF 0.916485, and -2177.93 excluding the GER30 largest winner.",
                "53 broker rows joined to trade records; 24 broker rows lack trade-record/source-window geometry.",
                "Candidate outcomes include 336 skipped dynamic, 75 rejected circuit breaker, 55 filled, and 5 canceled rows.",
                "Selector context rows have selected_cell_rows and source-bound expectancy, but selected_cell_win_rate and selected_cell_profit_factor are missing on 512/512 rows.",
                "Entry/path ledger exact-R rows have negative central tendency: 55 filled exact-R rows, mean -0.118R and median -0.5005R.",
                "MFE/MAE/time ledger has 125 rows; MFE present 73, MAE present 79, hold time present 125; 23 rows held over 6 hours and 4 over 1 day.",
                "Giveback is material: 85/94 rows have positive giveback, 73/94 gave back at least 0.5R, and 45/94 gave back at least 1R.",
                "Cost ledger has 90 rows, including two high-swap ETHUSD duplicate-view rows for position 242689402 with swap -391.16.",
                "Data-gap ledger has 27 non-generatable or not-captured historical truth gaps after repair attempts.",
                "Failure taxonomy shows 88 stop-loss or broker-SL tags, 75 loss tags, 39 dominant-damage-symbol tags, and 21 clustered-entry tags.",
                "Portfolio exposure ledger shows 21/77 clustered broker entries and cluster sizes up to 4.",
                "XAUUSD, NDX100, and ETHUSD are failed live surfaces requiring kill or repair, not generic weak examples.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_initial_question_stack_blocker_ledger_and_v4_lane_requirements",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "strengthens Selector V4, Scheduler V4, Execution/Profit Harvest V4, Cost Engine, Market Whiteboard, and LiveDecisionPacketV4 requirements",
        },
        {
            "role": "wave1b_final_say_v3_authority_reviewer",
            "objective": "inspect Wave1B final-say and V3/default-off authority gaps",
            "artifacts_files_inspected": [
                W1B_MATRIX.as_posix(),
                (WAVE1B / "SELECTOR_AUTHORITY_GAP_LEDGER.jsonl").as_posix(),
                (WAVE1B / "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl").as_posix(),
                (WAVE1B / "LIVE_DECISION_PACKET_COMPLETENESS_LEDGER.jsonl").as_posix(),
                W1B_V3_DISPOSITION.as_posix(),
                (WAVE1B / "IMPLEMENTATION_DECISION_LEDGER.jsonl").as_posix(),
                W1B_REPAIRS.as_posix(),
            ],
            "material_findings": [
                "Wave1B live authority matrix has 12775 rows: 6187 runtime decisions, 5149 replacement-monitor snapshots, 877 pending lifecycle rows, 471 redacted_account trade records, and 91 broker truth trade groups.",
                "Live-authority classifications show fallback/no-candidate writer 7616, live candidate generation before V3 packet authority 2022, current dynamic router not V3 954, pending lifecycle authority 877, safety gate authority 744, trade-record authority without V3 packet 471, recent broker-real truth 77, and non-recent broker context 14.",
                "Decision status counts include 4180 AVOID, 1117 refuse until source or scope repair, 1053 FOLLOW, 807 not-filled, 300 vNext candidate ready, 91 closed trade, and 70 filled rows.",
                "Wave1B supports that full V3 was not halt-time live authority; it does not support saying V3 failed live.",
                "Selected-policy evidence is 1206 partial_be_runner rows and 219 momentum_exhaustion rows; no selected row proves Execution Policy V3 live authority.",
                "Selector V3, Scheduler V3, and Execution Policy V3 were present packages but default-off or not halt-time broker-real authority.",
                "Wave1B repaired prospective v3_live_authority packet capture; historical authority rows remain non-generatable source gaps.",
                "Repair ledger records six owner-now-false requirements for Scheduler V4, Cost/Swap/Slippage Engine, portfolio/correlation exposure ceilings, atomic halt, Market Whiteboard V2 fields, and broker profile/spec/session authority.",
            ],
            "accepted_rejected_finding_disposition": "accepted_with_evidence_class_boundary_v3_not_failed_live_but_not_live_authority",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "strengthens final-say matrix, LiveDecisionPacketV4, Scheduler V4, Cost Engine, Market Whiteboard, and Runtime Control requirements",
        },
        {
            "role": "wave1c_dual_broker_constraint_reviewer",
            "objective": "inspect Wave1C redacted_account primary and FTMO follower/projector constraints",
            "artifacts_files_inspected": [
                (WAVE1C / "DUAL_BROKER_ARCHITECTURE_DECISION.md").as_posix(),
                W1C_AUTHORITY.as_posix(),
                W1C_PROFILES.as_posix(),
                W1C_COST.as_posix(),
                (WAVE1C / "FOLLOWER_PROJECTOR_LIFECYCLE_LEDGER.jsonl").as_posix(),
                (WAVE1C / "CRASH_RECOVERY_AND_HALT_SEMANTICS_LEDGER.jsonl").as_posix(),
                W1C_DECISIONS.as_posix(),
                (WAVE1C / "PRODUCTION_CODE_CHANGE_LEDGER.jsonl").as_posix(),
            ],
            "material_findings": [
                "Wave1C verifier reports issue_count 0 and all 11 JSONL ledgers parse with zero parse errors.",
                "Authority matrix has 7 rows: redacted_account remains primary full runtime, FTMO remains follower/projector only, and shared rows enforce canonical intent separation.",
                "Broker profile inventory has 75 rows: 3 profiles and 72 instrument rows; runtime rows split 25 primary and 50 follower rows.",
                "Cost/spec/session ledger has 72 profile-spec rows; all remain profile_spec_present_session_hours_not_full_broker_export.",
                "Follower lifecycle ledger has 7 rows covering dedupe, tick deferral, risk guard, startup recovery, residual restore, active management, and pending-limit check.",
                "Crash/halt ledger has 6 fail-closed recovery rows covering single-instance locks, startup recovery, stale windows, source-record retry, hard-halt flags, and maintenance suppression.",
                "Production-code ledger has 11 scoped code/profile/test rows and no forbidden surface crossed.",
                "Do not copy redacted_account lots, fills, cash PnL, cost specs, or lifecycle truth into FTMO; FTMO broker-real cash requires explicit account-history export.",
                "Strict namespaces remain required: redacted_account_live_bee34003 source and operator_profile target; legacy unnamespaced reads fail closed.",
            ],
            "accepted_rejected_finding_disposition": "accepted_as_dual_broker_architecture_boundary_for_all_wave3_contracts",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "strengthens dual-broker runtime contract, Cost Engine, Execution Manager, Runtime Control, and Data Capture Final requirements",
        },
        {
            "role": "static_r_target_stop_geometry_reviewer",
            "objective": "inspect static/fixed R, target, stop, and broker-order geometry",
            "artifacts_files_inspected": [
                "config/agent_config.yaml",
                "config/profiles/redacted_account.yaml",
                "src/prompts/primary_analyzer_prompt.py",
                "src/research/dynamic_execution_policy.py",
                "src/research/moonshot_default_off_policy_router.py",
                "src/components/permissions.py",
                "src/components/execution.py",
                HARD_HALT.as_posix(),
                "knowledge_base/redacted_account_live_bee34003/trade_records",
            ],
            "material_findings": [
                "risk_per_trade_pct 2.0 is risk sizing, not a 2R target.",
                "Raw analyzer prompt and most trade records still carry 1.5R candidate geometry.",
                "Configured runtime dynamic router uses momentum 1R trigger / 2R final and partial_be_runner 1R trigger / 3R final with 0.5 partial ratio.",
                "Static/fixed 1.5R is comparator/raw geometry, not current final-target authority when dynamic routing applies.",
                "Broker initial SL/TP for the recent 77 GTOS trades clusters mostly around 3R, not blanket 1.5R or blanket 2R.",
                "Broker orders provide initial placement proxy only; they do not prove full SLTP modify lifecycle.",
                "The main V4 risk is semantic collapse between 2.0 percent risk, raw 1.5R, momentum 2R, partial-runner 3R, and realized/proxy R.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_static_r_geometry_audit_and_v4_capture_contract",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "adds target semantics split and SLTP lifecycle blocker",
        },
        {
            "role": "execution_path_mfe_profit_harvest_reviewer",
            "objective": "inspect entry quality, MAE/MFE, time-to-destination, stale thesis, and MFE harvest",
            "artifacts_files_inspected": [
                W1A_MATRIX.as_posix(),
                W1A_MFE.as_posix(),
                W1A_GIVEBACK.as_posix(),
                HARD_HALT.as_posix(),
                "shadow_logs/candidate_ltf_path_order.jsonl",
                "shadow_logs/candidate_path_contract_audit.jsonl",
                "shadow_logs/exit_management_shadow_status.jsonl",
                "shadow_logs/trailing_stop_v1_shadow_log.jsonl",
                "shadow_logs/partial_close_shadow_log.jsonl",
            ],
            "material_findings": [
                "Recent broker truth remains 77 trades, 31 wins, 46 losses, -859.69 cash.",
                "SL-like exits were 54 rows for about -9280.84 cash damage; multi-exit/partial-like broker rows were all winners and +5638.03.",
                "55 filled source-bound candidate rows were mostly partial_be_runner and had exact-R sum -6.4884R.",
                "18 of 29 exact-R losers had positive MFE before loss and lost about -4307.66 broker cash.",
                "Filled rows with giveback >=0.5R numbered 37; >=1R numbered 23.",
                "ETHUSD 242689402, NDX100 242442562, NZDUSD 242566204, GBPJPY 242617579, USDCAD 242618029, XAUUSD 241972476, GER30 242667071, and JP225 242752405 are row-driven exemplar failures or masking rows.",
                "MFE timestamp/detail is sparse; some MFE timing is invalid and must be repaired with path-first-passage logic or captured prospectively.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_profit_harvest_and_capture_gap_requirements",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "strengthens first-passage, stale-thesis, and profit-harvest V4 blockers",
        },
        {
            "role": "selector_scheduler_opportunity_cost_reviewer",
            "objective": "inspect selector looseness, candidate funnel, zero-trade value, and allocator requirements",
            "artifacts_files_inspected": [
                W1A_MATRIX.as_posix(),
                W1A_SELECTOR.as_posix(),
                (WAVE1A / "SYMBOL_SESSION_HEALTH_LEDGER.jsonl").as_posix(),
                W1B_MATRIX.as_posix(),
                (WAVE1B / "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl").as_posix(),
                (WAVE1B / "SELECTOR_AUTHORITY_GAP_LEDGER.jsonl").as_posix(),
                "config/agent_config.yaml",
                "config/profiles/redacted_account.yaml",
                "src/components/orchestrator.py",
                "knowledge_base/redacted_account_live_bee34003/trade_records",
            ],
            "material_findings": [
                "Broker trade quality was unacceptable: 77 trades, 40.26 percent win rate, -859.69 cash; excluding GER30, -2177.93 and PF 0.788.",
                "Candidate funnel was 336 skipped, 75 rejected, 55 filled, and 5 canceled/incomplete.",
                "Filled rows had positive selected-cell expectancy but negative exact-R central tendency.",
                "Selected-cell win rate and PF were missing across inspected Wave1A selector rows.",
                "Candidate-quality selector did run and blocked many rows; the failure is that the tradeable_now set remained too loose for broker capital.",
                "V3 selector/scheduler/execution were not live final authority.",
                "The Wave2 allocator repair groups 471 Wave1A candidate rows into 96 source-bound timestamp windows: 55 filled candidates, 416 alternatives, 37 filled windows, 59 zero-fill windows, and 28 filled windows with same-timestamp alternatives.",
                "No durable original runtime decision_window_id/candidate_set_id ties observed filled candidates, rejected alternatives, no-trade alternatives, open positions, pending orders, stale exposure, fill probability, or broker-net EV per unit risk.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_per_window_allocator_opportunity_cost_ledgers_with_runtime_intent_boundary",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "updates selected-vs-alternative, best-trade allocator, selector-scheduler opportunity ledgers, blocker ledger, prompt gap ledger, and Scheduler V4 decision-window requirements",
        },
        {
            "role": "cost_broker_constraint_reviewer",
            "objective": "inspect cost, spread, slippage, commission, swap, broker-net, specs, and sessions",
            "artifacts_files_inspected": [
                W1A_MATRIX.as_posix(),
                W1A_COST.as_posix(),
                W1C_COST.as_posix(),
                W1C_PROFILES.as_posix(),
                HARD_HALT.as_posix(),
                "config/profiles/redacted_account.yaml",
                "config/profiles/ftmo.yaml",
                "config/profiles/operator_profile.yaml",
                "src/components/broker_truth_cost_capture_v2.py",
                "src/utils/broker_profile.py",
            ],
            "material_findings": [
                "Recent broker deals had gross deal profit +214.93 but commission/swap/fees -1074.62, producing -859.69 broker net.",
                "ETHUSD was the worst explicit cost row family; position 242689402 had -391.16 swap and -398.89 total cost drag.",
                "XAUUSD and NDX100 damage is mostly trade path/selection rather than explicit commission/swap.",
                "Wave1C spec rows remain profile_spec_present_session_hours_not_full_broker_export, not full broker export authority.",
                "No broker_truth_cost_capture_v2.jsonl exists in base or namespaced shadow paths.",
                "FTMO broker-real PnL/cost claims remain forbidden without account-history join.",
                "V4 Cost Engine must be a hard pretrade gate using broker-local profile, live spread, commission, swap/overnight, session, stops/freeze, volume, contract/tick value, and cash conversion.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_cost_broker_net_ledger_and_v4_cost_engine_gate",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "adds broker-net gross-to-net flip as hard Cost Engine blocker",
        },
        {
            "role": "market_vs_system_whiteboard_reviewer",
            "objective": "inspect bad-market versus bad-system, market whiteboard, symbol/session/regime, exposure, and zero-trade quality",
            "artifacts_files_inspected": [
                W1A_MATRIX.as_posix(),
                (WAVE1A / "SYMBOL_SESSION_HEALTH_LEDGER.jsonl").as_posix(),
                (WAVE1A / "FAILURE_TAXONOMY_AND_CAUSAL_HYPOTHESIS_LEDGER.jsonl").as_posix(),
                (WAVE1A / "PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl").as_posix(),
                W1B_MATRIX.as_posix(),
                "research/operations/vnext_lane17_market_whiteboard_v2_2026_06_02",
                "shadow_logs/cross_instrument_correlation_decisions.jsonl",
                "shadow_logs/regime_classifier.jsonl",
            ],
            "material_findings": [
                "Evidence does not support pure bad-market-only disposition.",
                "Stronger classification is bad_market_system_mismatch plus bad_system_logic: the system failed to make bad-market recognition, symbol/session damage, cost, and cluster exposure hard controls.",
                "Worst broker symbols were XAUUSD, NDX100, ETHUSD, and GBPJPY; SELL side lost materially more than BUY side.",
                "Derived London-broad UTC bucket was worst, but exact runtime session/whiteboard labels are not fully captured.",
                "Lane17 whiteboard replay has 289928 rows but runtime exact correlation, H4 regime, market hours, spread-to-risk, and tick fields remain widely missing.",
                "Zero-trade rows are first-class market-state decisions, not absence of signal.",
                "Market Whiteboard V2 must be upstream and fail-closed per symbol/session/side/regime/correlation/spread/tick/market-hours/source state.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_market_vs_system_whiteboard_ledger",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "strengthens Market Whiteboard V2 and zero-trade-as-positive-decision requirements",
        },
        {
            "role": "capture_replay_ai_production_disposition_reviewer",
            "objective": "inspect capture contracts, replay/validation, AI reliability, production disposition, and deployable scope",
            "artifacts_files_inspected": [
                "src/components/orchestrator.py",
                "scripts/validate_goal_prompt_hardening.py",
                "scripts/audit_goal_route_artifacts.py",
                (WAVE1A / "FORWARD_CAPTURE_REQUIREMENTS.md").as_posix(),
                (WAVE1C / "FORWARD_CAPTURE_REQUIREMENTS.md").as_posix(),
                W1B_REPAIRS.as_posix(),
                ".context/LIVE_STATE.md",
                "research/science_program_2026_05/04_goal_prompts/FINAL_MOONSHOT_WAVE2_FINAL_MASTER_AFTER_HARD_HALT_GOAL_PROMPT_2026-06-04.md",
            ],
            "material_findings": [
                "Current Wave2 route is a verified initial causal spine, not complete.",
                "LiveDecisionPacketV4 needs broker tickets, source namespace, selected-cell denominator metrics, source-window hash, pre-entry cash risk, realized gross/net, MFE/MAE, exposure lifecycle, halt state, and dual-broker local truth fields beyond the current packet.",
                "Target geometry fields must include raw/repaired/dynamic targets, broker initial/final SL/TP, every modify event, partials, realized R, MFE/MAE, costs, swap, slippage, and source completeness.",
                "FTMO/follower capture must be broker-local and cannot reuse redacted_account lots/fills/cash/specs.",
                "Non-generatable historical truth includes unlogged final-say intent, missing joins, absent SLTP lifecycle, uncaptured AI state, and FTMO account-history gaps.",
                "AI should be a measured subsystem after deterministic no-API replay, not the replay engine or unguarded main actor.",
                "Deployable scope is not ready; Wave2 still needs production disposition, deployable scope, validation, anti-overfit, and capture contracts.",
            ],
            "accepted_rejected_finding_disposition": "accepted_into_capture_replay_ai_production_disposition_ledgers",
            "changed_prompt_lane_contract_implementation_source_or_blocker": "adds LiveDecisionPacketV4, validation, AI, production-return, and deployable-scope blockers",
        },
    ]


def build_new_intelligence_rows() -> list[dict[str, Any]]:
    return [
        {
            "intelligence_id": "W2INTEL-W1A-001",
            "origin": "subagent_wave1a_broker_candidate_causality_reviewer",
            "source_paths": [W1A_MATRIX.as_posix(), W1A_SELECTOR.as_posix(), W1A_GIVEBACK.as_posix()],
            "finding": "Selected-cell source-bound expectancy existed while live broker-real outcome was 31 wins, 46 losses, -859.69 cash, with selected-cell win rate and PF missing on 512 selector rows.",
            "evidence_class": "broker-real cash plus source-bound selected-cell context",
            "downstream_question_ids": ["W2Q_SELECTOR_QUALITY", "W2Q_REJECT_SKIP_ZERO_TRADE"],
            "v4_requirement_id": "selector_v4_broker_net_admission_fields",
            "status": "accepted_initial_intelligence_requires_deeper_row_join",
        },
        {
            "intelligence_id": "W2INTEL-W1A-002",
            "origin": "subagent_wave1a_broker_candidate_causality_reviewer",
            "source_paths": [W1A_GIVEBACK.as_posix(), W1A_MFE.as_posix()],
            "finding": "Giveback and path-harvest failure are material: 85/94 giveback rows are positive, 73/94 give back at least 0.5R, and 45/94 give back at least 1R.",
            "evidence_class": "source-bound exact/proxy path and giveback ledger",
            "downstream_question_ids": ["W2Q_ENTRY_PATH_MFE_MAE", "W2Q_LOSER_MFE_HARVEST"],
            "v4_requirement_id": "profit_harvest_mfe_capture_v4",
            "status": "accepted_initial_intelligence_requires_loser_level_repair",
        },
        {
            "intelligence_id": "W2INTEL-W1A-003",
            "origin": "subagent_wave1a_broker_candidate_causality_reviewer",
            "source_paths": [(WAVE1A / "SYMBOL_SESSION_HEALTH_LEDGER.jsonl").as_posix(), W1A_COST.as_posix()],
            "finding": "XAUUSD, NDX100, and ETHUSD are failed live surfaces requiring symbol/session kill or repair; ETHUSD also has high swap drag evidence.",
            "evidence_class": "broker-real cash plus source-bound cost ledger",
            "downstream_question_ids": ["W2Q_BAD_MARKET_VS_SYSTEM", "W2Q_COST_BROKER_NET"],
            "v4_requirement_id": "market_whiteboard_and_cost_engine_symbol_health_gate",
            "status": "accepted_initial_intelligence_requires_market_state_split",
        },
        {
            "intelligence_id": "W2INTEL-W1B-001",
            "origin": "subagent_wave1b_final_say_v3_authority_reviewer",
            "source_paths": [W1B_MATRIX.as_posix(), W1B_V3_DISPOSITION.as_posix()],
            "finding": "Wave1B proves full V3 was not halt-time live authority; it does not prove V3 failed live.",
            "evidence_class": "live authority and default-off production-code disposition evidence",
            "downstream_question_ids": ["W2Q_FINAL_SAY_AUTHORITY", "W2Q_V3_DEFAULT_OFF_LIVE_DIVERGENCE"],
            "v4_requirement_id": "v3_to_v4_runtime_disposition",
            "status": "accepted_evidence_class_boundary",
        },
        {
            "intelligence_id": "W2INTEL-W1B-002",
            "origin": "subagent_wave1b_final_say_v3_authority_reviewer",
            "source_paths": [W1B_REPAIRS.as_posix()],
            "finding": "Scheduler V4, Cost Engine, exposure ceilings, atomic halt, Market Whiteboard, and broker profile/spec/session fields are explicit Wave1B repair requirements.",
            "evidence_class": "prospective capture and production-code requirement evidence",
            "downstream_question_ids": ["W2Q_BEST_TRADE_ALLOCATOR", "W2Q_COST_BROKER_NET", "W2Q_CAPTURE_GAPS"],
            "v4_requirement_id": "livedecisionpacket_v4_required_fields",
            "status": "accepted_initial_intelligence_requires_schema_contract",
        },
        {
            "intelligence_id": "W2INTEL-W1C-001",
            "origin": "subagent_wave1c_dual_broker_constraint_reviewer",
            "source_paths": [W1C_AUTHORITY.as_posix(), W1C_PROFILES.as_posix(), W1C_COST.as_posix()],
            "finding": "redacted_account remains the only source-brain primary runtime; FTMO is follower/projector only and must compute broker-local risk, cost, lifecycle, and account-history truth.",
            "evidence_class": "production-code and architecture-contract evidence",
            "downstream_question_ids": ["W2Q_DUAL_BROKER_CONSTRAINTS", "W2Q_COST_BROKER_NET"],
            "v4_requirement_id": "dual_broker_runtime_contract",
            "status": "accepted_architecture_boundary",
        },
        {
            "intelligence_id": "W2INTEL-RGEOM-001",
            "origin": "subagent_static_r_target_stop_geometry_reviewer",
            "source_paths": ["config/agent_config.yaml", "src/prompts/primary_analyzer_prompt.py", "src/components/execution.py", HARD_HALT.as_posix()],
            "finding": "The hard-halt target question is a semantic split, not one R label: 2.0 percent risk sizing, raw 1.5R prompt geometry, momentum 2R final, partial-runner 3R final, broker initial SL/TP proxy R, and realized/proxy R must be separate.",
            "evidence_class": "code_config_trade_record_and_broker_order_geometry",
            "downstream_question_ids": ["W2Q_STATIC_R_GEOMETRY"],
            "v4_requirement_id": "target_semantics_split",
            "status": "accepted_static_r_geometry_intelligence",
        },
        {
            "intelligence_id": "W2INTEL-PATH-001",
            "origin": "subagent_execution_path_mfe_profit_harvest_reviewer",
            "source_paths": [W1A_MFE.as_posix(), W1A_GIVEBACK.as_posix(), "shadow_logs/candidate_ltf_path_order.jsonl"],
            "finding": "Loser positive-MFE and giveback rows are a primary profit-harvest failure class; they require first-passage, stale-thesis, partial/BE, and reversal capture rather than anecdotal review.",
            "evidence_class": "source_bound_path_mfe_giveback_and_broker_cash",
            "downstream_question_ids": ["W2Q_ENTRY_PATH_MFE_MAE", "W2Q_LOSER_MFE_HARVEST"],
            "v4_requirement_id": "profit_harvest_first_passage_v4",
            "status": "accepted_profit_harvest_intelligence",
        },
        {
            "intelligence_id": "W2INTEL-COST-001",
            "origin": "subagent_cost_broker_constraint_reviewer",
            "source_paths": [HARD_HALT.as_posix(), W1C_COST.as_posix()],
            "finding": "Recent broker deal gross was positive before explicit commission/swap/fee drag; broker-net cost cannot be advisory because it flipped the hard-halt window negative.",
            "evidence_class": "broker_truth_deal_level_cost",
            "downstream_question_ids": ["W2Q_COST_BROKER_NET"],
            "v4_requirement_id": "cost_engine_hard_pretrade_gate",
            "status": "accepted_broker_net_cost_intelligence",
        },
        {
            "intelligence_id": "W2INTEL-SCHED-001",
            "origin": "subagent_selector_scheduler_opportunity_cost_reviewer",
            "source_paths": [W1A_MATRIX.as_posix(), W1B_MATRIX.as_posix(), "knowledge_base/redacted_account_live_bee34003/trade_records"],
            "finding": "The failure was not simply that no selector ran; Wave2 repaired the candidate timestamp view into 96 diagnostic allocator windows from 471 Wave1A candidates, but original allocator intent/open/pending/stale exposure truth was not captured.",
            "evidence_class": "candidate_funnel_selector_runtime_and_authority_rows",
            "downstream_question_ids": ["W2Q_SELECTOR_QUALITY", "W2Q_BEST_TRADE_ALLOCATOR", "W2Q_REJECT_SKIP_ZERO_TRADE"],
            "v4_requirement_id": "selector_scheduler_decision_window_v4",
            "status": "accepted_scheduler_opportunity_cost_intelligence_timestamp_repair_complete",
        },
        {
            "intelligence_id": "W2INTEL-SCHED-002",
            "origin": "subagent_allocator_source_schema_reviewer",
            "source_paths": [
                W1A_MATRIX.as_posix(),
                "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl",
                "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl",
                "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl",
            ],
            "finding": "Per-window repair preserves 96 timestamp windows with candidate-level exact-R for filled rows and source-bound expectancy for non-filled alternatives; deltas are diagnostic cross-evidence comparisons, not realized alternative counterfactuals.",
            "evidence_class": "source_bound_reconstruction_not_original_runtime_intent",
            "downstream_question_ids": ["W2Q_BEST_TRADE_ALLOCATOR", "W2Q_REJECT_SKIP_ZERO_TRADE"],
            "v4_requirement_id": "scheduler_v4_decision_window_capture",
            "status": "accepted_allocator_window_repair_intelligence",
        },
        {
            "intelligence_id": "W2INTEL-MKT-001",
            "origin": "subagent_market_vs_system_whiteboard_reviewer",
            "source_paths": [W1A_MATRIX.as_posix(), "research/operations/vnext_lane17_market_whiteboard_v2_2026_06_02", "shadow_logs/cross_instrument_correlation_decisions.jsonl"],
            "finding": "Evidence does not support a pure bad-market disposition; the stronger finding is bad-market-system mismatch plus bad-system logic because damage recognition was not hard allocation authority.",
            "evidence_class": "broker_real_damage_plus_market_whiteboard_gap_evidence",
            "downstream_question_ids": ["W2Q_BAD_MARKET_VS_SYSTEM"],
            "v4_requirement_id": "market_whiteboard_v2_fail_closed",
            "status": "accepted_market_system_intelligence",
        },
        {
            "intelligence_id": "W2INTEL-CAPTURE-001",
            "origin": "subagent_capture_replay_ai_production_disposition_reviewer",
            "source_paths": ["src/components/orchestrator.py", (WAVE1A / "FORWARD_CAPTURE_REQUIREMENTS.md").as_posix(), (WAVE1C / "FORWARD_CAPTURE_REQUIREMENTS.md").as_posix()],
            "finding": "LiveDecisionPacketV4 must capture the fields needed to avoid historical non-generatable truth gaps; current packet and route are insufficient for production return.",
            "evidence_class": "capture_contract_and_forward_requirement_evidence",
            "downstream_question_ids": ["W2Q_CAPTURE_GAPS", "W2Q_VALIDATION_REPLAY", "W2Q_AI_RELIABILITY"],
            "v4_requirement_id": "livedecisionpacket_v4_capture_contract",
            "status": "accepted_capture_contract_intelligence",
        },
    ]


def build_static_r_source_inventory() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "risk_sizing_not_target",
            "source_path": "config/agent_config.yaml",
            "source_surface": "risk_config",
            "field_or_code_surface": "risk.risk_per_trade_pct and risk.min_rr",
            "finding": "risk_per_trade_pct is sizing authority and min_rr is a vNext sanity floor; neither is a 2R profit target.",
            "semantic_status": "must_not_conflate_risk_percent_with_target_r",
            "v4_requirement_id": "target_semantics_split",
        },
        {
            "source_id": "raw_prompt_1_5r",
            "source_path": "src/prompts/primary_analyzer_prompt.py",
            "source_surface": "raw_analyzer_prompt",
            "field_or_code_surface": "take_profit_1 and risk_reward_ratio examples",
            "finding": "Raw analyzer/prompt scaffolding still emits 1.5R TP1 geometry for older setup families.",
            "semantic_status": "raw_candidate_geometry_not_final_dynamic_runtime_authority",
            "v4_requirement_id": "raw_candidate_geometry_column",
        },
        {
            "source_id": "dynamic_router_config",
            "source_path": "config/agent_config.yaml",
            "source_surface": "runtime_dynamic_execution_router",
            "field_or_code_surface": "moonshot_dynamic_execution_router_*",
            "finding": "Configured dynamic router has momentum 1R trigger / 2R final and partial-be-runner 1R trigger / 3R final with 0.5 partial ratio.",
            "semantic_status": "dynamic_runtime_intent",
            "v4_requirement_id": "selected_policy_trigger_final_columns",
        },
        {
            "source_id": "legacy_j46_j49",
            "source_path": "config/agent_config.yaml",
            "source_surface": "legacy_position_management",
            "field_or_code_surface": "position_mgmt.j46_j49_v2",
            "finding": "Legacy J46/J49 config still carries 3R TP1 and 6R higher-target comparator settings.",
            "semantic_status": "historical_or_comparator_unless_later_authority_proves_live",
            "v4_requirement_id": "comparator_role_column",
        },
        {
            "source_id": "research_policy_comparators",
            "source_path": "src/research/dynamic_execution_policy.py",
            "source_surface": "research_replay_policy_set",
            "field_or_code_surface": "legacy_fixed_target_policy, partial_be_policy, be_only_policy, trailing_policy, path-aware runner",
            "finding": "Research replay retains legacy fixed 1.5R and multiple dynamic policies as comparators; comparator rows are not broker-real live authority by themselves.",
            "semantic_status": "research_replay_comparator",
            "v4_requirement_id": "validation_comparator_catalog",
        },
        {
            "source_id": "default_off_router_policy_role",
            "source_path": "src/research/moonshot_default_off_policy_router.py",
            "source_surface": "default_off_policy_router",
            "field_or_code_surface": "fixed_target_role and selected_policy",
            "finding": "Router marks retired static baseline as comparator-only and promotes momentum primary plus exception routing.",
            "semantic_status": "fixed_static_baseline_not_live_primary",
            "v4_requirement_id": "final_say_policy_role_column",
        },
        {
            "source_id": "execution_dynamic_targets",
            "source_path": "src/components/execution.py",
            "source_surface": "execution_manager",
            "field_or_code_surface": "gtos_vnext_dynamic_be_trigger_r and gtos_vnext_dynamic_final_target_r",
            "finding": "Execution computes trigger/final prices from dynamic R fields, stores selected policy, and manages partial/BE/momentum software exits.",
            "semantic_status": "runtime_execution_authority_when_fields_present",
            "v4_requirement_id": "broker_ticket_bound_exit_lifecycle",
        },
        {
            "source_id": "broker_order_truth",
            "source_path": (HARD_HALT / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json").as_posix(),
            "source_surface": "broker_order_sl_tp",
            "field_or_code_surface": "order sl/tp joined to broker grouped trade entry price",
            "finding": "Broker orders expose initial SL/TP proxy geometry for all 77 recent GTOS broker trades but do not prove full SLTP modify lifecycle.",
            "semantic_status": "broker_order_initial_proxy_not_full_lifecycle",
            "v4_requirement_id": "initial_and_modified_broker_geometry_columns",
        },
    ]


def build_broker_order_geometry_rows(broker_rows: list[dict[str, Any]], orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_position = orders_by_position(orders)
    rows: list[dict[str, Any]] = []
    for row in broker_rows:
        position_id = str(row.get("position_id"))
        valid_orders = []
        for order in by_position.get(position_id, []):
            multiple = target_multiple_from_order(row, order)
            if multiple is not None:
                valid_orders.append((order, multiple))
        first_order = valid_orders[0][0] if valid_orders else {}
        first_multiple = valid_orders[0][1] if valid_orders else None
        rows.append(
            {
                "row_id": f"broker_order_geometry:{position_id}",
                "broker_position_id": row.get("position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "entry_price": row.get("entry_price"),
                "first_valid_order_ticket": first_order.get("ticket"),
                "first_valid_order_sl": first_order.get("sl"),
                "first_valid_order_tp": first_order.get("tp"),
                "first_valid_order_time_setup_utc": first_order.get("time_setup_utc"),
                "valid_sl_tp_order_count": len(valid_orders),
                "initial_broker_order_target_multiple_r": first_multiple,
                "bucket_0_05": target_bucket(first_multiple, 0.05),
                "bucket_0_15": target_bucket(first_multiple, 0.15),
                "bucket_0_25": target_bucket(first_multiple, 0.25),
                "exact_r": row.get("exact_r"),
                "mfe_r": row.get("mfe_r"),
                "mae_r": row.get("mae_r"),
                "giveback_r": row.get("giveback_r"),
                "hold_minutes": row.get("hold_minutes"),
                "broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
                "join_status": row.get("join_status"),
                "geometry_evidence_class": "broker_order_initial_sl_tp_proxy",
                "lifecycle_gap": "sltp_modify_lifecycle_not_fully_captured",
                "finding": "broker initial order target multiple joined to broker entry/SL/TP; realized path and modify lifecycle remain separate evidence classes",
            }
        )
    return rows


def build_sltp_modify_lifecycle_source_coverage_rows(broker_rows: list[dict[str, Any]], orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_position = orders_by_position(orders)
    rows: list[dict[str, Any]] = []
    for row in broker_rows:
        position_id = str(row.get("position_id"))
        position_orders = by_position.get(position_id, [])
        sltp_orders = [
            order
            for order in position_orders
            if order.get("sl") not in (None, "", 0, 0.0) or order.get("tp") not in (None, "", 0, 0.0)
        ]
        unique_pairs = sorted({f"{order.get('sl')}|{order.get('tp')}" for order in sltp_orders})
        first_order = sltp_orders[0] if sltp_orders else {}
        rows.append(
            {
                "row_id": f"sltp_lifecycle_source:{position_id}",
                "broker_position_id": row.get("position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "source_path": (HARD_HALT / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json").as_posix(),
                "broker_order_count_for_position": len(position_orders),
                "sltp_order_count_for_position": len(sltp_orders),
                "unique_sltp_pair_count": len(unique_pairs),
                "first_order_ticket": first_order.get("ticket"),
                "first_order_sl": first_order.get("sl"),
                "first_order_tp": first_order.get("tp"),
                "first_order_time_setup_utc": first_order.get("time_setup_utc"),
                "first_order_time_done_utc": first_order.get("time_done_utc"),
                "has_multiple_sltp_states_in_broker_export": len(unique_pairs) > 1,
                "evidence_class": "broker_order_initial_sltp_source_coverage",
                "coverage_status": "initial_sltp_present_full_modify_lifecycle_not_captured"
                if sltp_orders and len(unique_pairs) <= 1
                else "multiple_sltp_states_present_requires_event_classification"
                if len(unique_pairs) > 1
                else "sltp_missing_from_broker_order_export",
                "non_generatable_or_missing_fields": [
                    "every_sltp_modify_event",
                    "be_move_event",
                    "trailing_stop_update_event",
                    "partial_close_ticket_bound_trigger",
                    "software_exit_policy_clock",
                ],
                "v4_requirement_id": "broker_ticket_bound_sltp_modify_lifecycle_capture",
            }
        )
    return rows


def build_candidate_geometry_rows(candidate_rows: list[dict[str, Any]], broker_order_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    broker_geometry_by_position = {
        str(row.get("broker_position_id")): row
        for row in broker_order_rows
        if row.get("broker_position_id") not in (None, "")
    }
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        payload, read_status = read_optional_trade_record(row)
        packet = nested_get(payload, "decision_pipeline", "gtos_vnext_candidate_intelligence_packet") or {}
        dynamic_packet = nested_get(packet, "geometry", "dynamic_target") or {}
        dynamic_trigger_final = nested_get(packet, "dynamic_policy", "dynamic_trigger_final_pullback") or {}
        executable_repair = nested_get(payload, "decision_pipeline", "gtos_vnext_executable_geometry_repair") or {}
        execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        exit_payload = payload.get("exit") if isinstance(payload.get("exit"), dict) else {}
        broader = payload.get("moonshot_broader_origin_candidate") if isinstance(payload.get("moonshot_broader_origin_candidate"), dict) else {}
        dyn_router = nested_get(payload, "decision_pipeline", "gtos_vnext_moonshot_dynamic_execution") or {}
        route_dims = nested_get(dyn_router, "router_record", "route_dimensions") or {}
        candidate_quality = route_dims.get("candidate_quality_selector") if isinstance(route_dims.get("candidate_quality_selector"), dict) else {}
        broker_position_id = row.get("broker_position_id") or exit_payload.get("broker_position_id")
        broker_order = broker_geometry_by_position.get(str(broker_position_id), {})

        raw_rr = safe_float(nested_get(payload, "trade_parameters", "risk_reward_ratio"))
        if raw_rr is None:
            raw_rr = safe_float(broader.get("risk_reward_ratio") or broader.get("rr"))
        repaired_rr = safe_float(nested_get(executable_repair, "repaired", "risk_reward_ratio"))
        if repaired_rr is None:
            repaired_rr = safe_float(nested_get(packet, "geometry", "repaired", "geometry", "risk_reward_ratio"))
        dynamic_final = safe_float(execution.get("gtos_vnext_dynamic_final_target_r"))
        if dynamic_final is None:
            dynamic_final = safe_float(dynamic_packet.get("final_target_r") or dynamic_trigger_final.get("repaired_dynamic_final_target_r"))
        dynamic_trigger = safe_float(execution.get("gtos_vnext_dynamic_be_trigger_r"))
        if dynamic_trigger is None:
            dynamic_trigger = safe_float(dynamic_packet.get("trigger_r") or dynamic_trigger_final.get("partial_trigger_r") or dynamic_trigger_final.get("momentum_trigger_r"))

        rows.append(
            {
                "row_id": f"candidate_geometry:{row.get('trade_id') or row.get('candidate_id')}",
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "broker_position_id": broker_position_id,
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "final_outcome": row.get("final_outcome"),
                "source_path": row.get("source_path"),
                "source_read_status": read_status,
                "raw_trade_parameters_risk_reward_ratio": raw_rr,
                "raw_candidate_target_price": nested_get(payload, "trade_parameters", "take_profit_1") or broader.get("take_profit_1"),
                "repaired_geometry_risk_reward_ratio": repaired_rr,
                "dynamic_selected_policy": execution.get("gtos_vnext_dynamic_policy_selected") or dynamic_packet.get("selected_policy") or dyn_router.get("selected_policy"),
                "execution_policy_id": execution.get("gtos_vnext_execution_policy_id") or nested_get(packet, "dynamic_policy", "execution_policy_id") or dyn_router.get("execution_policy_id"),
                "fixed_target_role": execution.get("gtos_vnext_dynamic_policy_fixed_target_role") or dyn_router.get("fixed_target_role"),
                "dynamic_trigger_r": dynamic_trigger,
                "dynamic_final_target_r": dynamic_final,
                "partial_close_ratio": safe_float(dynamic_trigger_final.get("partial_close_ratio")),
                "execution_take_profit_1": execution.get("take_profit_1"),
                "execution_take_profit_2": execution.get("take_profit_2"),
                "execution_take_profit_3": execution.get("take_profit_3"),
                "execution_dynamic_trigger_price": execution.get("gtos_vnext_dynamic_be_trigger_price"),
                "execution_dynamic_final_target_price": execution.get("gtos_vnext_dynamic_final_target_price"),
                "broker_order_initial_target_multiple_r": broker_order.get("initial_broker_order_target_multiple_r"),
                "broker_order_bucket_0_25": broker_order.get("bucket_0_25"),
                "actual_r": exit_payload.get("actual_r") if exit_payload else row.get("exact_r"),
                "mfe_r": exit_payload.get("mfe_r") if exit_payload else row.get("mfe_r"),
                "mae_r": exit_payload.get("mae_r") if exit_payload else row.get("mae_r"),
                "partial_close_count": len(exit_payload.get("partial_closes") or []) if isinstance(exit_payload.get("partial_closes"), list) else 0,
                "candidate_quality_classification": candidate_quality.get("classification"),
                "selected_cell_win_rate": nested_get(packet, "selected_cell_risk_proof", "source_row_identity", "metric_win_rate"),
                "selected_cell_profit_factor": nested_get(packet, "selected_cell_risk_proof", "source_row_identity", "metric_profit_factor"),
                "semantic_split_status": "raw_1_5r_repaired_or_dynamic_target_differs" if raw_rr == 1.5 and dynamic_final not in (None, 1.5) else "no_raw_dynamic_conflict_detected_or_missing",
                "evidence_class": "source_bound_candidate_record_geometry_plus_optional_broker_order_proxy",
                "source_gap": "missing_dynamic_or_broker_join" if dynamic_final is None or broker_order == {} and row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN" else None,
            }
        )
    return rows


def build_static_r_gap_rows(candidate_geometry_rows: list[dict[str, Any]], broker_order_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filled = [row for row in candidate_geometry_rows if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"]
    broker_missing_trade_join = [row for row in broker_order_rows if row.get("join_status") == "no_trade_record_execution_join"]
    return [
        {
            "gap_id": "raw_dynamic_target_semantic_collapse",
            "scope": "candidate_trade_records",
            "affected_rows": sum(1 for row in candidate_geometry_rows if row.get("semantic_split_status") == "raw_1_5r_repaired_or_dynamic_target_differs"),
            "gap": "raw 1.5R candidate geometry can be overwritten by repaired/dynamic 2R or 3R runtime targets",
            "repair_requirement": "LiveDecisionPacketV4 must preserve raw_rr, repaired_rr, selected_policy, trigger_r, final_target_r, broker_initial_tp_sl_r, realized_r, and costs separately.",
            "status": "open_v4_capture_contract_required",
        },
        {
            "gap_id": "broker_order_modify_lifecycle_missing",
            "scope": "broker_recent_77",
            "affected_rows": len(broker_order_rows),
            "gap": "broker orders expose initial SL/TP proxy geometry but not every SLTP modify, partial close, BE, trailing, or emergency-close lifecycle event.",
            "repair_requirement": "Persist broker ticket-bound order/deal/position lifecycle events and every SLTP modification prospectively.",
            "status": "open_prospective_capture_required",
        },
        {
            "gap_id": "broker_trade_record_join_missing",
            "scope": "broker_recent_77",
            "affected_rows": len(broker_missing_trade_join),
            "gap": "broker-real rows without trade-record execution joins cannot receive exact source-bound policy/target attribution.",
            "repair_requirement": "Persist broker_position_id, order tickets, candidate_id, source hash, cash risk, actual R, and selected-cell identity on every live record.",
            "status": "open_historical_gap_partly_non_generatable",
        },
        {
            "gap_id": "filled_candidate_partial_lifecycle_sparse",
            "scope": "filled_candidate_trade_records",
            "affected_rows": sum(1 for row in filled if int(row.get("partial_close_count") or 0) == 0),
            "gap": "many filled rows have no partial-close event even when partial_be_runner was selected.",
            "repair_requirement": "Profit Harvest V4 must capture first-passage, partial execution, BE move, runner final-target, and close reason as broker-ticket-bound events.",
            "status": "open_execution_capture_and_replay_required",
        },
        {
            "gap_id": "dynamic_target_missing_on_material_rows",
            "scope": "candidate_trade_records",
            "affected_rows": sum(1 for row in candidate_geometry_rows if row.get("dynamic_final_target_r") in (None, "")),
            "gap": "some material candidate rows do not expose a dynamic final target field.",
            "repair_requirement": "Do not infer missing dynamic targets from realized R or raw prompt R; record explicit target authority or source gap.",
            "status": "open_source_gap_or_zero_trade_context",
        },
    ]


def build_static_r_summary(candidate_geometry_rows: list[dict[str, Any]], broker_order_rows: list[dict[str, Any]]) -> dict[str, Any]:
    filled = [row for row in candidate_geometry_rows if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"]
    return {
        "generated_at_utc": GENERATED_AT,
        "status": "static_r_geometry_audit_materialized_not_complete",
        "candidate_trade_record_rows": len(candidate_geometry_rows),
        "filled_candidate_rows": len(filled),
        "broker_order_geometry_rows": len(broker_order_rows),
        "raw_rr_counts": counter_dict(Counter(row.get("raw_trade_parameters_risk_reward_ratio") for row in candidate_geometry_rows)),
        "dynamic_final_target_counts_all_candidates": counter_dict(Counter(row.get("dynamic_final_target_r") for row in candidate_geometry_rows if row.get("dynamic_final_target_r") is not None)),
        "dynamic_final_target_counts_filled": counter_dict(Counter(row.get("dynamic_final_target_r") for row in filled if row.get("dynamic_final_target_r") is not None)),
        "dynamic_policy_counts_filled": counter_dict(Counter(row.get("dynamic_selected_policy") for row in filled if row.get("dynamic_selected_policy"))),
        "broker_order_target_bucket_0_05": counter_dict(Counter(row.get("bucket_0_05") for row in broker_order_rows)),
        "broker_order_target_bucket_0_15": counter_dict(Counter(row.get("bucket_0_15") for row in broker_order_rows)),
        "broker_order_target_bucket_0_25": counter_dict(Counter(row.get("bucket_0_25") for row in broker_order_rows)),
        "semantic_conclusion": "recent broker initial SL/TP geometry clusters mostly near 3R; raw 1.5R prompt/candidate geometry is not the same evidence class as dynamic runtime target or broker realized R",
    }


def build_cost_broker_rows(broker_rows: list[dict[str, Any]], trade_groups_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups = trade_groups_payload.get("trades") if isinstance(trade_groups_payload, dict) else []
    group_by_position = {str(group.get("position_id")): group for group in groups if isinstance(group, dict)}
    rows: list[dict[str, Any]] = []
    for row in broker_rows:
        position_id = str(row.get("position_id"))
        group = group_by_position.get(position_id, {})
        deals = group.get("deals") if isinstance(group.get("deals"), list) else []
        gross_profit = round(sum(float(deal.get("profit") or 0.0) for deal in deals), 2)
        commission = round(sum(float(deal.get("commission") or 0.0) for deal in deals), 2)
        swap = round(sum(float(deal.get("swap") or 0.0) for deal in deals), 2)
        fee = round(sum(float(deal.get("fee") or 0.0) for deal in deals), 2)
        net = round(gross_profit + commission + swap + fee, 2)
        cost_drag = round(commission + swap + fee, 2)
        rows.append(
            {
                "row_id": f"broker_cost:{position_id}",
                "broker_position_id": row.get("position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "deal_count": len(deals),
                "gross_deal_profit_cash": gross_profit,
                "commission_cash": commission,
                "swap_cash": swap,
                "fee_cash": fee,
                "cost_drag_cash": cost_drag,
                "broker_net_cash_from_deals": net,
                "broker_net_cash_from_wave1a": row.get("broker_real_pnl_cash"),
                "deal_group_net_pnl": group.get("net_pnl"),
                "cost_drag_materiality": "swap_or_commission_material" if abs(cost_drag) >= 50 else "small_explicit_deal_cost",
                "cost_engine_implication": "hard_block_or_strict_hold_constraint_required" if abs(swap) >= 100 or row.get("symbol") in {"ETHUSD", "BTCUSD"} else "broker_net_cost_stress_required",
                "evidence_class": "broker_truth_deal_profit_commission_swap_fee_join",
            }
        )
    summary = {
        "generated_at_utc": GENERATED_AT,
        "status": "broker_net_cost_join_materialized",
        "broker_rows": len(rows),
        "gross_deal_profit_cash_sum": round(sum(row["gross_deal_profit_cash"] for row in rows), 2),
        "commission_cash_sum": round(sum(row["commission_cash"] for row in rows), 2),
        "swap_cash_sum": round(sum(row["swap_cash"] for row in rows), 2),
        "fee_cash_sum": round(sum(row["fee_cash"] for row in rows), 2),
        "cost_drag_cash_sum": round(sum(row["cost_drag_cash"] for row in rows), 2),
        "broker_net_cash_from_deals_sum": round(sum(row["broker_net_cash_from_deals"] for row in rows), 2),
        "worst_cost_drag_rows": sorted(
            [
                {
                    "broker_position_id": row["broker_position_id"],
                    "symbol": row["symbol"],
                    "cost_drag_cash": row["cost_drag_cash"],
                    "swap_cash": row["swap_cash"],
                    "broker_net_cash_from_deals": row["broker_net_cash_from_deals"],
                }
                for row in rows
            ],
            key=lambda item: item["cost_drag_cash"],
        )[:10],
        "semantic_conclusion": "broker-net expectancy must use deal-level cost; explicit commission/swap converted the recent window from gross-positive to net-negative",
    }
    return rows, summary


def build_selector_scheduler_opportunity_rows(candidate_geometry_rows: list[dict[str, Any]], w1a_rows: list[dict[str, Any]], w1b_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    broker_rows = [row for row in w1a_rows if row.get("row_type") == "broker_grouped_trade"]
    candidates = [row for row in w1a_rows if row.get("row_type") == "candidate_trade_record"]
    filled = [row for row in candidates if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"]
    skipped = [row for row in candidates if str(row.get("final_outcome") or "").startswith("SKIPPED")]
    rejected = [row for row in candidates if str(row.get("final_outcome") or "").startswith("REJECTED")]
    quality_counts = Counter(row.get("candidate_quality_classification") for row in candidate_geometry_rows if row.get("candidate_quality_classification"))
    filled_quality = Counter(row.get("candidate_quality_classification") for row in candidate_geometry_rows if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN")
    return [
        {
            "ledger_id": "selector_live_admission_quality",
            "surface": "selector",
            "source_paths": [W1A_MATRIX.as_posix(), W1A_SELECTOR.as_posix()],
            "finding": "filled rows had positive selected-cell expectancy but negative exact-R central tendency; selected-cell win rate and PF were absent in Wave1A selector rows.",
            "metrics": {
                "filled_rows": len(filled),
                "filled_exact_r_present": sum(1 for row in filled if row.get("exact_r") not in (None, "")),
                "filled_exact_r_sum": round(sum(float(row.get("exact_r") or 0.0) for row in filled), 6),
                "selector_rows_missing_win_rate_or_pf": sum(1 for row in broker_rows if none_like(row.get("selected_cell_win_rate")) or none_like(row.get("selected_cell_profit_factor"))),
            },
            "v4_requirement": "fail_closed_broker_net_selected_cell_admission",
            "status": "open_selector_v4_required",
        },
        {
            "ledger_id": "candidate_funnel_zero_trade",
            "surface": "candidate_funnel",
            "source_paths": [W1A_MATRIX.as_posix()],
            "finding": "zero-trade and reject rows are material decision data and cannot be treated as absence of signal.",
            "metrics": {
                "candidate_rows": len(candidates),
                "filled_rows": len(filled),
                "skipped_rows": len(skipped),
                "rejected_rows": len(rejected),
                "final_outcome_counts": counter_dict(Counter(row.get("final_outcome") for row in candidates)),
            },
            "v4_requirement": "zero_trade_comparator_and_best_rejected_candidate_fields",
            "status": "open_allocator_window_replay_required",
        },
        {
            "ledger_id": "candidate_quality_selector_not_sufficient",
            "surface": "candidate_quality_selector",
            "source_paths": ["knowledge_base/redacted_account_live_bee34003/trade_records"],
            "finding": "candidate-quality selector ran on many records and blocked no-trade rows, but tradeable_now admission still contained material broker-losing fills.",
            "metrics": {
                "candidate_quality_classification_counts": counter_dict(quality_counts),
                "filled_candidate_quality_classification_counts": counter_dict(filled_quality),
            },
            "v4_requirement": "broker_net_margin_of_safety_not_gross_proxy_only",
            "status": "open_selector_v4_required",
        },
        {
            "ledger_id": "scheduler_decision_window_missing",
            "surface": "scheduler_allocator",
            "source_paths": [W1B_MATRIX.as_posix(), (WAVE1B / "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl").as_posix(), "src/components/orchestrator.py"],
            "finding": "runtime evidence preserves individual FOLLOW/AVOID/pending rows but lacks durable decision_window_id and candidate_set_id tying alternatives, open positions, pending orders, stale exposure, and zero-trade value together.",
            "metrics": {
                "wave1b_rows": len(w1b_rows),
                "runtime_decision_rows": sum(1 for row in w1b_rows if row.get("source_row_kind") == "runtime_decision"),
                "pending_lifecycle_rows": sum(1 for row in w1b_rows if row.get("source_row_kind") == "pending_lifecycle"),
                "follow_rows": sum(1 for row in w1b_rows if row.get("decision_status") == "FOLLOW"),
                "avoid_rows": sum(1 for row in w1b_rows if row.get("decision_status") == "AVOID"),
            },
            "v4_requirement": "scheduler_v4_best_trade_allocator_decision_window",
            "status": "open_same_evidence_class_replay_required",
        },
    ]


def build_market_vs_system_rows(broker_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    symbol_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "net": 0.0})
    side_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "net": 0.0})
    for row in broker_rows:
        for stats_map, key in ((symbol_stats, row.get("symbol")), (side_stats, row.get("side"))):
            stats = stats_map[str(key)]
            stats["trades"] += 1
            stats["wins"] += 1 if row.get("win_loss") == "win" else 0
            stats["losses"] += 1 if row.get("win_loss") == "loss" else 0
            stats["net"] += float(row.get("broker_real_pnl_cash") or 0.0)
    worst_symbols = sorted(
        [
            {
                "symbol": symbol,
                "trades": stats["trades"],
                "wins": stats["wins"],
                "losses": stats["losses"],
                "net": round(stats["net"], 2),
                "win_rate": round(stats["wins"] / stats["trades"], 6) if stats["trades"] else None,
            }
            for symbol, stats in symbol_stats.items()
        ],
        key=lambda item: item["net"],
    )[:8]
    side_rows = [
        {
            "side": side,
            "trades": stats["trades"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "net": round(stats["net"], 2),
            "win_rate": round(stats["wins"] / stats["trades"], 6) if stats["trades"] else None,
        }
        for side, stats in sorted(side_stats.items())
    ]
    return [
        {
            "ledger_id": "bad_market_not_proven_market_only",
            "source_paths": [W1A_MATRIX.as_posix(), "research/operations/vnext_lane17_market_whiteboard_v2_2026_06_02"],
            "finding": "hard-halt evidence does not support a pure bad-market-only explanation; it proves bad-market-system mismatch and bad-system logic because damage recognition was not enforced as hard allocation authority.",
            "metrics": {
                "worst_symbols": worst_symbols,
                "side_distribution": side_rows,
                "stop_loss_or_broker_sl_exit_rows": sum(1 for row in broker_rows if "stop_loss_or_broker_sl_exit" in set(row.get("failure_tags") or [])),
                "clustered_entry_rows": sum(1 for row in broker_rows if "clustered_entry" in set(row.get("failure_tags") or [])),
            },
            "missing_runtime_whiteboard_fields": [
                "exact_runtime_correlation",
                "h4_regime",
                "market_hours",
                "spread_to_risk",
                "tick_path",
                "portfolio_allocator_state",
            ],
            "v4_requirement": "market_whiteboard_v2_upstream_fail_closed",
            "status": "open_market_whiteboard_v4_required",
        },
        {
            "ledger_id": "zero_trade_market_state_value",
            "source_paths": [W1A_MATRIX.as_posix(), W1B_MATRIX.as_posix()],
            "finding": "336 skipped rows and 75 rejects are first-class evidence for no-trade quality; V4 must score NO_TRADE_BY_EVIDENCE as a positive decision when market/source/cost/allocation state says risk is not deserved.",
            "metrics": {
                "skipped_dynamic_rows": 336,
                "gate3_reject_rows": 75,
            },
            "v4_requirement": "zero_trade_as_explicit_market_state_decision",
            "status": "open_replay_required",
        },
    ]


def build_profit_harvest_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row.get("final_outcome") != "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN":
            continue
        payload, read_status = read_optional_trade_record(row)
        exit_payload = payload.get("exit") if isinstance(payload.get("exit"), dict) else {}
        ltf_path = nested_get(payload, "decision_pipeline", "gtos_vnext_ltf_path_execution", "path_state") or {}
        execution = payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        actual_r = safe_float(row.get("exact_r"))
        if actual_r is None:
            actual_r = safe_float(exit_payload.get("actual_r"))
        mfe_r = safe_float(row.get("mfe_r"))
        if mfe_r is None:
            mfe_r = safe_float(exit_payload.get("mfe_r"))
        mae_r = safe_float(row.get("mae_r"))
        if mae_r is None:
            mae_r = safe_float(exit_payload.get("mae_r"))
        giveback_r = safe_float(row.get("giveback_r"))
        if giveback_r is None and actual_r is not None and mfe_r is not None:
            giveback_r = round(mfe_r - actual_r, 6)
        mfe_time = safe_float(exit_payload.get("mfe_time_minutes"))
        mae_time = safe_float(exit_payload.get("mae_time_minutes"))
        partial_closes = exit_payload.get("partial_closes") if isinstance(exit_payload.get("partial_closes"), list) else []
        tags: list[str] = []
        if actual_r is not None and actual_r < 0 and mfe_r is not None and mfe_r > 0:
            tags.append("loser_positive_mfe_before_loss")
        if giveback_r is not None and giveback_r >= 1.0:
            tags.append("giveback_ge_1r")
        elif giveback_r is not None and giveback_r >= 0.5:
            tags.append("giveback_ge_0_5r")
        if mfe_time is not None and mfe_time < 0:
            tags.append("invalid_negative_mfe_time")
        if not partial_closes and (execution.get("gtos_vnext_dynamic_policy_selected") == "partial_be_runner" or row.get("execution_policy") == "partial_be_runner"):
            tags.append("partial_be_runner_no_recorded_partial_close")
        if safe_float(row.get("hold_minutes")) is not None and float(row.get("hold_minutes")) >= 360:
            tags.append("stale_hold_ge_6h")
        if mfe_r is None or mae_r is None:
            tags.append("mfe_or_mae_missing")
        rows.append(
            {
                "row_id": f"profit_harvest:{row.get('trade_id')}",
                "trade_id": row.get("trade_id"),
                "candidate_id": row.get("candidate_id"),
                "broker_position_id": row.get("broker_position_id") or exit_payload.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "source_path": row.get("source_path"),
                "source_read_status": read_status,
                "selected_policy": execution.get("gtos_vnext_dynamic_policy_selected") or row.get("execution_policy"),
                "execution_policy_id": execution.get("gtos_vnext_execution_policy_id") or row.get("execution_policy_id"),
                "dynamic_trigger_r": execution.get("gtos_vnext_dynamic_be_trigger_r"),
                "dynamic_final_target_r": execution.get("gtos_vnext_dynamic_final_target_r"),
                "actual_r": actual_r,
                "mfe_r": mfe_r,
                "mae_r": mae_r,
                "giveback_r": giveback_r,
                "mfe_time_minutes": mfe_time,
                "mae_time_minutes": mae_time,
                "hold_minutes": row.get("hold_minutes") or exit_payload.get("hold_time_minutes"),
                "exit_type": exit_payload.get("exit_type"),
                "partial_close_count": len(partial_closes),
                "partial_close_events": partial_closes,
                "ltf_path_entry_touched": ltf_path.get("entry_touched"),
                "ltf_path_target_touched_without_entry": ltf_path.get("target_touched_without_entry"),
                "ltf_path_protective_touched_before_entry": ltf_path.get("protective_touched_before_entry"),
                "ltf_path_same_bar_ambiguous": ltf_path.get("same_bar_ambiguous"),
                "harvest_tags": tags,
                "causal_disposition": "profit_harvest_failure_candidate" if tags else "filled_row_no_initial_harvest_failure_tag",
                "repair_requirement": "first_passage_m1_or_tick_repair_and_ticket_bound_partial_be_trailing_capture",
            }
        )
    return rows


def build_loser_mfe_repair_rows(profit_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in profit_rows:
        actual_r = safe_float(row.get("actual_r"))
        if actual_r is None or actual_r >= 0:
            continue
        mfe_r = safe_float(row.get("mfe_r"))
        tags = list(row.get("harvest_tags") or [])
        if mfe_r is not None and mfe_r > 0:
            repair_status = "positive_mfe_loser_requires_harvest_rule_counterfactual"
        elif mfe_r is None:
            repair_status = "mfe_missing_loser_requires_path_repair_or_capture_gap"
        else:
            repair_status = "no_positive_mfe_observed_from_current_source"
        rows.append(
            {
                "row_id": f"loser_mfe_repair:{row.get('trade_id')}",
                "trade_id": row.get("trade_id"),
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "actual_r": actual_r,
                "mfe_r": mfe_r,
                "mae_r": row.get("mae_r"),
                "giveback_r": row.get("giveback_r"),
                "mfe_time_minutes": row.get("mfe_time_minutes"),
                "hold_minutes": row.get("hold_minutes"),
                "partial_close_count": row.get("partial_close_count"),
                "harvest_tags": tags,
                "repair_status": repair_status,
                "same_evidence_class_next_step": "join M1/tick first-passage, consolidation duration/range, reversal timestamp, and execution lifecycle; if source absent, mark non-generatable prospective capture",
                "source_path": row.get("source_path"),
            }
        )
    return rows


def build_shadow_path_source_coverage_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filled_trade_ids = {
        row.get("trade_id")
        for row in candidate_rows
        if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN" and row.get("trade_id")
    }
    filled_candidate_ids = {
        row.get("candidate_id")
        for row in candidate_rows
        if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN" and row.get("candidate_id")
    }
    paths = [
        Path("shadow_logs/candidate_ltf_path_order.jsonl"),
        Path("shadow_logs/candidate_path_contract_audit.jsonl"),
        Path("shadow_logs/candidate_path_follow.jsonl"),
        Path("shadow_logs/exit_management_shadow_status.jsonl"),
        Path("shadow_logs/partial_close_shadow_log.jsonl"),
        Path("shadow_logs/trailing_stop_v1_shadow_log.jsonl"),
        Path("shadow_logs/broker_actual_r_audit.jsonl"),
        Path("shadow_logs/j46_j49_exit_comparator_audit.jsonl"),
    ]
    out: list[dict[str, Any]] = []
    for path in paths:
        rows, errors = read_jsonl_lenient(path)
        by_trade = sum(1 for row in rows if row.get("trade_id") in filled_trade_ids)
        by_candidate = sum(1 for row in rows if row.get("candidate_id") in filled_candidate_ids)
        out.append(
            {
                "source_path": path.as_posix(),
                "row_count": len(rows),
                "parse_error_count": len(errors),
                "first_parse_errors": errors[:3],
                "filled_trade_id_join_count": by_trade,
                "filled_candidate_id_join_count": by_candidate,
                "schema_versions": counter_dict(Counter(row.get("schema_version") for row in rows if row.get("schema_version"))),
                "path_or_status_counts": counter_dict(Counter(row.get("path_order_label") or row.get("path_label") or row.get("exit_management_status") or row.get("j46_j49_exit_comparator_status") for row in rows if row.get("path_order_label") or row.get("path_label") or row.get("exit_management_status") or row.get("j46_j49_exit_comparator_status"))),
                "evidence_class": "local_shadow_or_replay_source_coverage",
                "use_status": "available_for_same_evidence_class_repair" if rows else "missing_or_unavailable",
            }
        )
    return out


def build_row_level_exemplar_rows(profit_rows: list[dict[str, Any]], cost_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_position = {str(row.get("broker_position_id")): row for row in profit_rows if row.get("broker_position_id") not in (None, "")}
    cost_by_position = {str(row.get("broker_position_id")): row for row in cost_rows if row.get("broker_position_id") not in (None, "")}
    exemplars = [
        ("242689402", "ETHUSD swap/cost hard-block row"),
        ("242442562", "NDX100 large MFE then loss/path timestamp repair row"),
        ("242566204", "NZDUSD positive MFE loser/stale harvest row"),
        ("242617579", "GBPJPY stale hold positive MFE loser row"),
        ("242618029", "USDCAD broker-real cash with missing MFE/MAE repair row"),
        ("241972476", "XAUUSD long stale overnight broker-real row with missing candidate join"),
        ("242667071", "GER30 large winner outlier masking row"),
        ("242752405", "JP225 emergency halt/flatten row"),
    ]
    rows: list[dict[str, Any]] = []
    for position_id, label in exemplars:
        profit = by_position.get(position_id, {})
        cost = cost_by_position.get(position_id, {})
        rows.append(
            {
                "row_id": f"causal_exemplar:{position_id}",
                "broker_position_id": int(position_id),
                "label": label,
                "symbol": profit.get("symbol") or cost.get("symbol"),
                "side": profit.get("side") or cost.get("side"),
                "trade_id": profit.get("trade_id"),
                "actual_r": profit.get("actual_r"),
                "mfe_r": profit.get("mfe_r"),
                "mae_r": profit.get("mae_r"),
                "giveback_r": profit.get("giveback_r"),
                "hold_minutes": profit.get("hold_minutes"),
                "cost_drag_cash": cost.get("cost_drag_cash"),
                "swap_cash": cost.get("swap_cash"),
                "broker_net_cash": cost.get("broker_net_cash_from_deals"),
                "current_evidence_status": "source_bound_profit_row_joined" if profit else "broker_cost_or_broker_truth_only_join_gap",
                "wave2_implication": "must survive V4 lane prompt as row-level falsification/regression fixture",
            }
        )
    return rows


def build_capture_replay_ai_production_rows() -> list[dict[str, Any]]:
    return [
        {
            "ledger_id": "live_decision_packet_v4_gap",
            "surface": "capture_contract",
            "source_paths": ["src/components/orchestrator.py", (WAVE1A / "FORWARD_CAPTURE_REQUIREMENTS.md").as_posix(), (WAVE1C / "FORWARD_CAPTURE_REQUIREMENTS.md").as_posix()],
            "finding": "current candidate packet captures many V1 fields but lacks complete broker tickets, selected-cell denominator metrics, path first-passage, costs, exposure lifecycle, and source-window hashes for every final-say row.",
            "non_generatable_historical_truth": [
                "unlogged original final-say intent",
                "missing broker/candidate joins",
                "missing SLTP modify lifecycle",
                "uncaptured AI prompt/input/output/gate state",
                "FTMO broker-real PnL without explicit account-history export",
            ],
            "v4_requirement": "LiveDecisionPacketV4_required_before_production_return",
            "status": "open_capture_schema_required",
        },
        {
            "ledger_id": "replay_validation_contract_gap",
            "surface": "validation_replay",
            "source_paths": ["research/operations", "shadow_logs"],
            "finding": "local no-API replay can answer many path/cost/selector questions now, but sealed validation, anti-overfit partitions, and decision-window replay are not yet materialized in this Wave2 route.",
            "v4_requirement": "historical_replay_digital_twin_and_anti_overfit_contract",
            "status": "open_validation_contract_required",
        },
        {
            "ledger_id": "ai_role_after_hard_halt",
            "surface": "ai_reliability",
            "source_paths": ["config/agent_config.yaml", ".context/LIVE_STATE.md"],
            "finding": "AI should be a measured validator/audit subsystem after deterministic no-API replay, not an unguarded main actor.",
            "v4_requirement": "cached_budgeted_stratified_ai_audit_only_until_value_proven",
            "status": "open_ai_reliability_contract_required",
        },
        {
            "ledger_id": "production_return_not_ready",
            "surface": "production_disposition",
            "source_paths": [W1B_REPAIRS.as_posix(), W1C_AUTHORITY.as_posix(), ".context/LIVE_STATE.md"],
            "finding": "production return remains blocked by Scheduler V4, Cost Engine, exposure ceilings, atomic halt, Market Whiteboard, LiveDecisionPacketV4, dual-broker broker-local constraints, and validation contracts.",
            "v4_requirement": "production_return_dossier_required",
            "status": "blocked_until_wave2_completion_and_v4_package_proven",
        },
    ]


def build_production_component_disposition_rows() -> list[dict[str, Any]]:
    return [
        {
            "component": "primary_analyzer_prompt_raw_geometry",
            "source_path": "src/prompts/primary_analyzer_prompt.py",
            "current_disposition": "legacy_raw_candidate_geometry_surface",
            "wave2_truth": "can emit 1.5R candidate geometry but is not final dynamic target authority when vNext dynamic fields apply",
            "v4_action": "preserve raw geometry as separate packet field; do not use as final target without final-say proof",
        },
        {
            "component": "moonshot_dynamic_execution_router",
            "source_path": "src/research/moonshot_default_off_policy_router.py",
            "current_disposition": "dynamic_router_or_comparator_catalog",
            "wave2_truth": "fixed baseline comparator-only; live evidence selected partial_be_runner and momentum_exhaustion rows",
            "v4_action": "promote only through broker-net replay and capture selected_policy/fixed_target_role explicitly",
        },
        {
            "component": "execution_manager_dynamic_exit",
            "source_path": "src/components/execution.py",
            "current_disposition": "active_runtime_exit_management_surface",
            "wave2_truth": "software partial/BE/momentum exit behavior exists but historical partial/modify lifecycle capture is sparse",
            "v4_action": "ticket-bound lifecycle capture and first-passage profit-harvest replay before production return",
        },
        {
            "component": "orchestrator_candidate_packet_v1",
            "source_path": "src/components/orchestrator.py",
            "current_disposition": "capture_packet_insufficient_for_v4_final_say",
            "wave2_truth": "packet is useful but leaves allocator, lifecycle, path, cost, and final-say completeness gaps",
            "v4_action": "replace or extend to LiveDecisionPacketV4",
        },
        {
            "component": "selector_scheduler_v3_packages",
            "source_path": "src/research/moonshot_v3_runtime_packages.py",
            "current_disposition": "default_off_or_capture_only_at_halt_time",
            "wave2_truth": "do not blame V3 as live failure; mine useful concepts and demote unproven authority",
            "v4_action": "build Scheduler V4 and Selector V4 from broker-net evidence",
        },
        {
            "component": "broker_profiles_and_dual_broker_follower",
            "source_path": "config/profiles;src/components",
            "current_disposition": "usable profile skeleton_with_full_broker_export_gaps",
            "wave2_truth": "redacted_account is primary source brain; FTMO follower/projector must use broker-local risk/cost/session/account-history truth",
            "v4_action": "enforce broker-local cost/session/spec and no redacted_account lot/fill/cash copying",
        },
    ]


def build_deployable_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "scope_id": "lfs_and_sparse_status",
            "source_path": ".context/LIVE_STATE.md",
            "finding": "LFS hydration has zero missing pointer-only rows in current live state; sparse-excluded rows are not evidence loss.",
            "deployment_implication": "raw evidence can remain in research/archive surfaces and must not be treated as a production package dependency unless explicitly included",
            "status": "informational_scope_guard",
        },
        {
            "scope_id": "no_live_deploy_or_broker_mutation",
            "source_path": "Wave2 doctrine and controlling prompt",
            "finding": "Wave2 route is build/research only; broker operation, live deployment, credentials, paid APIs, and remote pushes remain forbidden.",
            "deployment_implication": "no production launch command or broker mutation is authorized by this route",
            "status": "hard_guard",
        },
        {
            "scope_id": "hard_halt_flags_preserved",
            "source_path": "research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03",
            "finding": "hard-halt evidence remains production-return gate authority; previous live surface is evidence, not deployable authority.",
            "deployment_implication": "runtime return requires a production-return dossier and verified V4 package",
            "status": "hard_guard",
        },
        {
            "scope_id": "raw_ledger_pollution_guard",
            "source_path": "repo_cleanup_and_staleness_policy",
            "finding": "large raw ledgers should remain evidence inputs, not deployable branch clutter.",
            "deployment_implication": "Wave2 artifacts should be route-owned and scoped; final production package should reference manifests/contracts",
            "status": "scope_guard",
        },
    ]


def build_live_decision_packet_contract() -> dict[str, Any]:
    return {
        "generated_at_utc": GENERATED_AT,
        "schema_name": "LiveDecisionPacketV4",
        "status": "required_contract_not_implemented_in_this_wave2_checkpoint",
        "required_field_groups": [
            "candidate_identity_and_source_namespace",
            "source_window_hash_and_m15_m1_tick_availability",
            "raw_geometry_repaired_geometry_dynamic_target_and_policy_role",
            "selected_cell_rows_win_rate_profit_factor_expectancy_denominator_and_cost_stress",
            "broker_profile_spec_session_spread_commission_swap_slippage_and_cash_conversion",
            "pre_entry_cash_risk_lot_margin_and_prop_rule_projection",
            "decision_window_id_candidate_set_id_alternatives_open_pending_and_zero_trade_value",
            "broker_order_deal_position_tickets_and_every_sltp_modify_event",
            "mfe_mae_first_passage_time_to_r_giveback_partial_be_trailing_timeout",
            "gross_net_cash_actual_r_commission_swap_fee_slippage",
            "exposure_cluster_correlation_symbol_session_damage_and_market_whiteboard_snapshot",
            "halt_process_autostart_recovery_and_final_say_authority_chain",
            "dual_broker_source_target_namespace_and_broker_local_target_risk_cost_truth",
        ],
        "non_inference_rule": "missing fields must be captured as source gaps, not inferred from realized price movement or raw target labels",
        "production_return_gate": "required_before_any_live_return_or_wave3_implementation_claims_production_ready",
    }


def build_validation_contract() -> dict[str, Any]:
    return {
        "generated_at_utc": GENERATED_AT,
        "status": "required_contract_not_complete",
        "allowed_now_without_live_or_paid_surfaces": [
            "broker truth deal/order/group replay",
            "candidate trade record replay",
            "M1 path first-passage repair where local source exists",
            "cost stress and broker-net expectancy joins",
            "candidate-quality selector and zero-trade comparator replay",
            "market whiteboard and correlation replay from local ledgers",
        ],
        "sealed_validation_requirements": [
            "time-split train/validation/test partitions",
            "symbol/session/regime stratification",
            "outlier sensitivity including GER30 removal",
            "cost/swap/slippage stress partitions",
            "zero-trade and rejected alternative counterfactuals",
            "decision-window allocator replay",
            "no-API deterministic baseline before any AI audit",
        ],
        "anti_overfit_fail_conditions": [
            "improvement depends on one GER30-like outlier",
            "broker-net cost omitted",
            "rejected/skipped rows omitted",
            "missing fields silently imputed as favorable",
            "FTMO target claims reuse redacted_account costs/lots/fills",
        ],
        "ai_validation_role": "cached budgeted stratified audit/validator only after deterministic replay baselines",
    }


def build_prompt_required_output_gap_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prompt_text = (REPO_ROOT / CONTROLLING_PROMPT).read_text(encoding="utf-8")
    required: list[str] = []
    for match in re.findall(r"`((?:WAVE2|WAVE3)_[^`]+)`", prompt_text):
        normalized = match.strip().rstrip(".")
        normalized = re.sub(r"\.(jsonl|json|md)$", "", normalized)
        if normalized not in required:
            required.append(normalized)
    for pseudo_required in (
        "WAVE3_PER_LANE_CONTROLLING_PROMPTS",
        "WAVE3_PER_LANE_ONE_LINE_STARTERS",
    ):
        if pseudo_required not in required:
            required.append(pseudo_required)

    current_files = {path.name for path in ROUTE_DIR.iterdir() if path.is_file()}
    current_stems = {re.sub(r"\.(jsonl|json|md)$", "", name) for name in current_files}
    partial_aliases = {
        "WAVE2_COST_SPREAD_SLIPPAGE_BROKER_NET_LEDGER": ["WAVE2_COST_BROKER_NET_CAUSAL_LEDGER"],
        "WAVE2_BAD_MARKET_VS_BAD_SYSTEM_LEDGER": ["WAVE2_MARKET_VS_SYSTEM_WHITEBOARD_LEDGER"],
        "WAVE2_CAPTURE_FIELD_CONTRACT_LIVEDECISIONPACKETV4": ["WAVE2_LIVE_DECISION_PACKET_V4_CAPTURE_CONTRACT"],
        "WAVE2_MFE_HARVEST_FAILURE_LEDGER": ["WAVE2_LOSER_MFE_REPAIR_LEDGER", "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER"],
        "WAVE2_STATIC_R_TARGET_GEOMETRY_AUDIT": ["WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER"],
        "WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER": ["WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER"],
        "WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER": ["WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER"],
        "WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER": ["WAVE2_SHADOW_PATH_SOURCE_COVERAGE_LEDGER"],
        "WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER": ["WAVE2_LOSER_MFE_REPAIR_LEDGER"],
        "WAVE2_STOP_WIDTH_AND_TARGET_DISTANCE_AUDIT": ["WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER"],
        "WAVE2_MARKET_STATE_AND_BAD_SYSTEM_DISPOSITION_LEDGER": ["WAVE2_MARKET_VS_SYSTEM_WHITEBOARD_LEDGER"],
        "WAVE2_ZERO_TRADE_AND_REJECTION_VALUE_LEDGER": ["WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER"],
        "WAVE2_ZERO_TRADE_QUALITY_DECISION_LEDGER": ["WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER"],
        "WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT": ["WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER"],
        "WAVE2_EXECUTION_LIFECYCLE_CAPTURE_GAP_LEDGER": ["WAVE2_STATIC_R_GEOMETRY_JOIN_GAP_LEDGER", "WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER"],
        "WAVE3_PER_LANE_CONTROLLING_PROMPTS": [],
        "WAVE3_PER_LANE_ONE_LINE_STARTERS": [],
    }
    content_verified_allocator_outputs = {
        "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER",
        "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER",
        "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER",
    }

    rows: list[dict[str, Any]] = []
    for artifact in required:
        aliases = partial_aliases.get(artifact, [])
        present_aliases = [alias for alias in aliases if alias in current_stems]
        content_verification_status = "not_applicable"
        if artifact in content_verified_allocator_outputs and artifact in current_stems:
            path = ROUTE_DIR / f"{artifact}.jsonl"
            artifact_rows = read_jsonl(Path(rel(path)))
            if (
                len(artifact_rows) == 96
                and all(row.get("inferred_window_id") for row in artifact_rows)
                and all(row.get("result_use_status") == "diagnostic_only_not_final_allocator_truth" for row in artifact_rows)
            ):
                status = "content_verified_exact_present_per_window_allocator"
                blocker = False
                content_verification_status = "96_inferred_windows_verified"
            else:
                status = "partial_present_content_not_verified_per_window_allocator"
                blocker = True
                content_verification_status = f"unexpected_row_count_or_schema:{len(artifact_rows)}"
        elif artifact in current_stems:
            status = "exact_present"
            blocker = False
        elif present_aliases:
            status = "partial_present_alias_named_differently_or_not_full_prompt_scope"
            blocker = True
        else:
            status = "missing_required_prompt_output"
            blocker = True
        rows.append(
            {
                "required_output": artifact,
                "status": status,
                "present_aliases": present_aliases,
                "content_verification_status": content_verification_status,
                "completion_blocker": blocker,
                "source_prompt": CONTROLLING_PROMPT.as_posix(),
                "next_action": "complete_exact_artifact_or_document_explicit_deprecated_alias" if blocker else "none",
            }
        )
    summary = {
        "generated_at_utc": GENERATED_AT,
        "source_prompt": CONTROLLING_PROMPT.as_posix(),
        "required_output_count": len(rows),
        "exact_present_count": sum(1 for row in rows if row["status"] == "exact_present"),
        "content_verified_exact_present_count": sum(1 for row in rows if row["status"].startswith("content_verified_exact_present")),
        "partial_present_alias_count": sum(1 for row in rows if row["status"].startswith("partial_present")),
        "missing_required_prompt_output_count": sum(1 for row in rows if row["status"] == "missing_required_prompt_output"),
        "wave3_prompt_pack_allowed": False,
        "reason": "controlling prompt required-output list is not fully satisfied; current route is a verified expanded causal spine, not full Wave2 completion",
    }
    return rows, summary


def session_bucket_from_time(value: str | None) -> str:
    if not value:
        return "unknown"
    match = re.search(r"T(\d{2}):", value)
    if not match:
        return "unknown"
    hour = int(match.group(1))
    if 0 <= hour <= 6:
        return "asia_tokyo_broad_utc_00_06"
    if 7 <= hour <= 11:
        return "london_broad_utc_07_11"
    if 12 <= hour <= 16:
        return "ny_overlap_broad_utc_12_16"
    if 17 <= hour <= 21:
        return "late_ny_broad_utc_17_21"
    return "rollover_utc_22_23"


def build_and_write_additional_prompt_named_artifacts(
    *,
    questions: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    broker_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    candidate_geometry_rows: list[dict[str, Any]],
    broker_order_geometry_rows: list[dict[str, Any]],
    cost_broker_rows: list[dict[str, Any]],
    profit_harvest_rows: list[dict[str, Any]],
    loser_mfe_repair_rows: list[dict[str, Any]],
    shadow_path_source_rows: list[dict[str, Any]],
    w1b_rows: list[dict[str, Any]],
    w1c_authority: list[dict[str, Any]],
    selector_rows: list[dict[str, Any]],
    ) -> None:
    question_rows = questions
    write_jsonl(
        "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
        [
            {
                "question_id": row["question_id"],
                "origin": row["origin"],
                "derived_wave3_lane": row["derived_wave3_lane"],
                "status": row["status"],
                "coverage_status": "opened_not_saturated",
                "result_artifact": row["result_artifact"],
                "remaining_work": row["falsification_test"],
            }
            for row in question_rows
        ],
    )
    write_jsonl(
        "WAVE2_NEWLY_DISCOVERED_WAVE3_REQUIREMENTS.jsonl",
        [
            {
                "requirement_id": f"REQ-{idx:03d}-{row['derived_wave3_lane']}",
                "source_question_id": row["question_id"],
                "lane": row["derived_wave3_lane"],
                "requirement": row["falsification_test"],
                "status": "candidate_requirement_pending_wave2_completion",
            }
            for idx, row in enumerate(question_rows, start=1)
        ],
    )
    write_jsonl(
        "WAVE2_QUESTION_DISCOVERY_LINEAGE_AUDIT.jsonl",
        [
            {
                "question_id": row["question_id"],
                "origin": row["origin"],
                "parent_question_ids": row["parent_question_ids"],
                "trigger_source_path": row["trigger_source_path"],
                "trigger_row_ids": row["trigger_row_ids"],
                "status": row["status"],
                "lineage_status": "source_bound_initial_lineage_recorded",
            }
            for row in question_rows
        ],
    )
    write_json(
        "WAVE2_STATIC_SEED_VS_DISCOVERED_QUESTION_AUDIT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "seed_prompt_questions": sum(1 for row in question_rows if row["origin"] == "seed_prompt"),
            "owner_correction_questions": sum(1 for row in question_rows if row["origin"] == "owner_correction"),
            "discovered_questions": sum(1 for row in question_rows if row["origin"] not in {"seed_prompt", "owner_correction"}),
            "status": "initial_question_stack_preserved_not_saturated",
        },
    )
    write_jsonl(
        "WAVE2_NEW_QUESTION_PURSUIT_PROOF.jsonl",
        [
            {
                "question_id": row["question_id"],
                "pursuit_actions": row["pursuit_actions"],
                "same_evidence_class_repairs_attempted": row["same_evidence_class_repairs_attempted"],
                "status": row["status"],
                "proof_status": "opened_and_materialized_initial_artifact",
            }
            for row in question_rows
        ],
    )

    lane_counts = Counter(row["derived_wave3_lane"] for row in question_rows)
    lane_rows = [
        {
            "lane": lane,
            "question_count": count,
            "source_question_ids": [row["question_id"] for row in question_rows if row["derived_wave3_lane"] == lane],
            "discovery_status": "required_or_discovered_lane_pending_wave2_completion",
        }
        for lane, count in sorted(lane_counts.items())
    ]
    write_jsonl("WAVE2_DYNAMIC_LANE_DISCOVERY_LEDGER.jsonl", lane_rows)
    write_jsonl(
        "WAVE2_WAVE3_LANE_EXPANSION_DECISION_LEDGER.jsonl",
        [
            {
                **row,
                "decision": "include_as_candidate_wave3_lane_or_requirement",
                "wave3_prompt_status": "blocked_until_wave2_completion",
            }
            for row in lane_rows
        ],
    )

    write_json(
        "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "initial_causal_model_not_complete",
            "headline": {
                "broker_rows": len(broker_rows),
                "candidate_rows": len(candidate_rows),
                "live_authority_rows": len(w1b_rows),
                "broker_net_cash": round(sum(float(row.get("broker_real_pnl_cash") or 0.0) for row in broker_rows), 2),
            },
            "primary_failure_model": [
                "weak_broker_net_selector_admission",
                "best_trade_allocator_original_runtime_packet_missing_despite_timestamp_window_repair",
                "profit_harvest_and_stale_thesis_capture_gap",
                "cost_swap_broker_net_gate_missing",
                "market_whiteboard_not_hard_authority",
                "LiveDecisionPacketV4_capture_gap",
            ],
            "not_proven": ["pure_bad_market_only", "V3_failed_live_as_final_authority", "fixed_1_5r_or_2r_as_single_live_target_truth"],
            "wave3_allowed": False,
        },
    )
    write_jsonl(
        "WAVE2_CAUSAL_CHAIN_LEDGER.jsonl",
        [
            {
                "chain_id": "selector_to_broker_loss",
                "ordered_surfaces": ["candidate_generation", "selector", "scheduler_missing", "execution", "broker_result"],
                "evidence_paths": [W1A_MATRIX.as_posix(), W1B_MATRIX.as_posix()],
                "finding": "positive selected-cell/gross proxy admission did not translate to broker-net quality",
                "status": "initial_chain_open_for_row_level_allocator_repair",
            },
            {
                "chain_id": "path_harvest_to_loss",
                "ordered_surfaces": ["entry", "mfe", "giveback", "exit_lifecycle", "broker_result"],
                "evidence_paths": ["WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl", "WAVE2_LOSER_MFE_REPAIR_LEDGER.jsonl"],
                "finding": "positive-MFE losers and giveback rows require first-passage/profit-harvest repair",
                "status": "initial_chain_open_for_path_repair",
            },
            {
                "chain_id": "cost_to_broker_net_flip",
                "ordered_surfaces": ["gross_price_result", "commission", "swap", "fee", "broker_net"],
                "evidence_paths": ["WAVE2_COST_BROKER_NET_CAUSAL_LEDGER.jsonl"],
                "finding": "explicit deal-level cost flipped recent gross-positive price result to net-negative broker result",
                "status": "source_bound_chain_materialized",
            },
            {
                "chain_id": "market_whiteboard_not_authority",
                "ordered_surfaces": ["symbol_session_damage", "cluster_exposure", "market_state_gap", "selector_scheduler_final_say"],
                "evidence_paths": ["WAVE2_MARKET_VS_SYSTEM_WHITEBOARD_LEDGER.jsonl", W1B_MATRIX.as_posix()],
                "finding": "bad-market-system mismatch was not converted into hard no-trade/reduce/queue authority",
                "status": "initial_chain_open_for_whiteboard_replay",
            },
        ],
    )

    coverage_rows = []
    for row in candidate_geometry_rows:
        coverage_rows.append(
            {
                "row_id": row["row_id"],
                "candidate_id": row.get("candidate_id"),
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "final_outcome": row.get("final_outcome"),
                "geometry_present": row.get("raw_trade_parameters_risk_reward_ratio") is not None or row.get("dynamic_final_target_r") is not None,
                "broker_order_join_present": row.get("broker_order_initial_target_multiple_r") is not None,
                "path_present": row.get("mfe_r") is not None or row.get("mae_r") is not None,
                "selector_quality_present": row.get("selected_cell_win_rate") is not None and row.get("selected_cell_profit_factor") is not None,
                "coverage_status": "partial_aspect_coverage_source_bound",
            }
        )
    write_jsonl("WAVE2_ALL_CANDIDATE_TRADE_ASPECT_COVERAGE_LEDGER.jsonl", coverage_rows)

    selector_audit_rows = [
        {
            "row_id": row["row_id"],
            "symbol": row.get("symbol"),
            "broker_position_id": row.get("broker_position_id"),
            "looseness_status": row.get("looseness_status"),
            "selected_cell_rows": row.get("selected_cell_rows"),
            "selected_cell_win_rate": row.get("selected_cell_win_rate"),
            "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
            "missing_fields": row.get("missing_fields"),
            "audit_status": "missing_quality_fields_fail_closed_requirement" if row.get("missing_fields") else "quality_fields_present",
        }
        for row in selector_rows
    ]
    write_jsonl("WAVE2_SELECTOR_LOOSENESS_AND_ADMISSION_AUDIT.jsonl", selector_audit_rows)
    write_jsonl("WAVE2_SELECTOR_LOOSE_ACCEPTANCE_AUDIT.jsonl", [row for row in selector_audit_rows if row["audit_status"].startswith("missing")])
    write_jsonl("WAVE2_SELECTOR_QUALITY_FIELD_COVERAGE_LEDGER.jsonl", selector_audit_rows)

    write_jsonl(
        "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl",
        build_allocator_opportunity_cost_window_rows(candidate_rows, candidate_geometry_rows, "selected_vs_alternative_opportunity_cost"),
    )
    write_jsonl(
        "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl",
        build_allocator_opportunity_cost_window_rows(candidate_rows, candidate_geometry_rows, "best_trade_allocator_opportunity_cost"),
    )
    write_jsonl(
        "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl",
        build_allocator_opportunity_cost_window_rows(candidate_rows, candidate_geometry_rows, "selector_scheduler_per_window_opportunity_cost"),
    )
    write_jsonl(
        "WAVE2_BEST_TRADE_ALLOCATOR_REQUIREMENT_MATRIX.jsonl",
        [
            {
                "requirement_id": "allocator_decision_window_id",
                "required_field": "decision_window_id and candidate_set_id",
                "current_status": "missing",
                "fail_closed": True,
            },
            {
                "requirement_id": "allocator_open_pending_new_competition",
                "required_field": "open positions, pending orders, new candidates, rejected alternatives, zero-trade option",
                "current_status": "not_materialized_as_single_window",
                "fail_closed": True,
            },
            {
                "requirement_id": "allocator_broker_net_ev_per_risk",
                "required_field": "broker-net EV per unit risk including cost/swap/slippage and fill probability",
                "current_status": "partial_source_bound_components_only",
                "fail_closed": True,
            },
            {
                "requirement_id": "allocator_stale_exposure_opportunity_cost",
                "required_field": "stale-position opportunity cost and replacement decision",
                "current_status": "missing",
                "fail_closed": True,
            },
        ],
    )
    write_jsonl(
        "WAVE2_SCHEDULER_MONEY_RISK_SOURCE_GAP_MATRIX.jsonl",
        [
            {
                "gap_id": "decision_window_missing",
                "source_paths": [W1B_MATRIX.as_posix()],
                "missing_field": "decision_window_id",
                "status": "prospective_capture_required",
            },
            {
                "gap_id": "candidate_set_missing",
                "source_paths": [W1B_MATRIX.as_posix()],
                "missing_field": "candidate_set_id_with_selected_rejected_no_trade_open_pending",
                "status": "same_evidence_class_replay_required",
            },
            {
                "gap_id": "open_pending_risk_join_missing",
                "source_paths": [(WAVE1B / "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl").as_posix()],
                "missing_field": "open_pending_new_risk_competition",
                "status": "prospective_capture_required",
            },
        ],
    )

    zero_trade_rows = [
        {
            "row_id": f"zero_trade_value:{row.get('trade_id') or row.get('candidate_id')}",
            "candidate_id": row.get("candidate_id"),
            "trade_id": row.get("trade_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "final_outcome": row.get("final_outcome"),
            "candidate_quality_classification": row.get("candidate_quality_classification"),
            "decision_value_status": "preserve_as_zero_trade_or_rejection_value_evidence",
            "source_gap": "path_outcome_missing_for_counterfactual_rank" if row.get("final_outcome") != "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN" else None,
        }
        for row in candidate_geometry_rows
        if row.get("final_outcome") != "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"
    ]
    write_jsonl("WAVE2_ZERO_TRADE_AND_REJECTION_VALUE_LEDGER.jsonl", zero_trade_rows)
    write_jsonl("WAVE2_ZERO_TRADE_QUALITY_DECISION_LEDGER.jsonl", zero_trade_rows)

    over_permissive = [
        {
            "row_id": f"over_permissive:{row.get('trade_id')}",
            "trade_id": row.get("trade_id"),
            "broker_position_id": row.get("broker_position_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "actual_r": row.get("actual_r"),
            "mfe_r": row.get("mfe_r"),
            "mae_r": row.get("mae_r"),
            "giveback_r": row.get("giveback_r"),
            "candidate_quality_classification": row.get("candidate_quality_classification"),
            "counterfactual": "would_require_no_trade_reduce_queue_or_source_required_under_V4_if broker_net_margin_or_source_completeness_missing",
            "status": "candidate_counterfactual_open",
        }
        for row in candidate_geometry_rows
        if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"
    ]
    write_jsonl("WAVE2_OVER_PERMISSIVE_ACCEPTANCE_COUNTERFACTUALS.jsonl", over_permissive)

    write_jsonl("WAVE2_COST_SPREAD_SLIPPAGE_BROKER_NET_LEDGER.jsonl", cost_broker_rows)
    write_jsonl("WAVE2_STATIC_R_TARGET_GEOMETRY_AUDIT.jsonl", candidate_geometry_rows)
    write_jsonl("WAVE2_STOP_WIDTH_AND_TARGET_DISTANCE_AUDIT.jsonl", broker_order_geometry_rows)
    write_jsonl("WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl", profit_harvest_rows)
    write_jsonl("WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl", profit_harvest_rows)
    write_jsonl("WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl", profit_harvest_rows)
    write_jsonl("WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl", loser_mfe_repair_rows)
    write_jsonl("WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl", loser_mfe_repair_rows)
    write_jsonl("WAVE2_EXECUTION_PATH_LIFECYCLE_SOURCE_MAP.jsonl", profit_harvest_rows + shadow_path_source_rows)
    write_jsonl("WAVE2_EXECUTION_LIFECYCLE_CAPTURE_GAP_LEDGER.jsonl", build_static_r_gap_rows(candidate_geometry_rows, broker_order_geometry_rows))
    write_jsonl(
        "WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl",
        [
            {
                **row,
                "adverse_excursion_status": "mae_present" if row.get("mae_r") is not None else "mae_missing",
                "entry_quality_status": "requires_first_passage_replay",
            }
            for row in profit_harvest_rows
        ],
    )
    write_jsonl(
        "WAVE2_PARTIAL_BE_RUNNER_FORENSIC_LEDGER.jsonl",
        [row for row in profit_harvest_rows if row.get("selected_policy") == "partial_be_runner"],
    )
    write_jsonl(
        "WAVE2_EXECUTION_QUALITY_IMPROVEMENT_DECISION_LEDGER.jsonl",
        [
            {
                "row_id": f"exec_improve:{row.get('trade_id')}",
                "trade_id": row.get("trade_id"),
                "broker_position_id": row.get("broker_position_id"),
                "improvement_decision": "first_passage_profit_harvest_or_stale_thesis_rule_required" if row.get("harvest_tags") else "preserve_for_distribution",
                "harvest_tags": row.get("harvest_tags"),
                "status": "open_v4_execution_requirement",
            }
            for row in profit_harvest_rows
        ],
    )
    write_jsonl(
        "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl",
        [
            {
                **row,
                "consolidation_duration": None,
                "reversal_timestamp": None,
                "source_gap": "consolidation_and_reversal_not_captured_currently",
            }
            for row in loser_mfe_repair_rows
        ],
    )
    write_jsonl(
        "WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl",
        [
            {
                **row,
                "stale_thesis_status": "hold_ge_6h_or_stale_tag" if safe_float(row.get("hold_minutes")) and float(row.get("hold_minutes")) >= 360 else "shorter_hold_but_stale_rule_still_needs_capture",
            }
            for row in profit_harvest_rows
        ],
    )
    write_jsonl(
        "WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl",
        [
            {
                **row,
                "time_to_destination_status": "partial_source_bound_missing_full_first_passage",
            }
            for row in profit_harvest_rows
        ],
    )
    write_jsonl(
        "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
        [
            {
                "row_id": f"pending_nofill:{row.get('material_row_id')}",
                "material_row_id": row.get("material_row_id"),
                "symbol": row.get("symbol"),
                "timestamp_utc": row.get("timestamp_utc"),
                "decision_status": row.get("decision_status"),
                "candidate_action": row.get("candidate_action"),
                "source_capture_state": row.get("source_capture_state"),
                "status": "pending_lifecycle_material_row_preserved",
            }
            for row in w1b_rows
            if row.get("source_row_kind") == "pending_limit_lifecycle"
        ],
    )

    write_jsonl("WAVE2_BAD_MARKET_VS_BAD_SYSTEM_LEDGER.jsonl", build_market_vs_system_rows(broker_rows))
    write_jsonl("WAVE2_MARKET_STATE_AND_BAD_SYSTEM_DISPOSITION_LEDGER.jsonl", build_market_vs_system_rows(broker_rows))

    symbol_health: dict[str, dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "net": 0.0})
    symbol_side_session: dict[str, dict[str, Any]] = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "net": 0.0})
    for row in broker_rows:
        for key, stats_map in (
            (str(row.get("symbol")), symbol_health),
            (f"{row.get('symbol')}|{row.get('side')}|{session_bucket_from_time(row.get('entry_time_utc'))}", symbol_side_session),
        ):
            stats = stats_map[key]
            stats["trades"] += 1
            stats["wins"] += 1 if row.get("win_loss") == "win" else 0
            stats["losses"] += 1 if row.get("win_loss") == "loss" else 0
            stats["net"] += float(row.get("broker_real_pnl_cash") or 0.0)
    write_json(
        "WAVE2_SYMBOL_SESSION_SIDE_REGIME_HEALTH_TABLE.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "derived_from_broker_entry_utc_not_full_runtime_whiteboard",
            "by_symbol": {
                key: {**value, "net": round(value["net"], 2), "win_rate": round(value["wins"] / value["trades"], 6) if value["trades"] else None}
                for key, value in sorted(symbol_health.items())
            },
            "by_symbol_side_utc_bucket": {
                key: {**value, "net": round(value["net"], 2), "win_rate": round(value["wins"] / value["trades"], 6) if value["trades"] else None}
                for key, value in sorted(symbol_side_session.items())
            },
        },
    )

    write_jsonl(
        "WAVE2_WIN_RATE_EXPECTANCY_FREQUENCY_TRADEOFF_LEDGER.jsonl",
        [
            {
                "scope": key,
                "trades": value["trades"],
                "wins": value["wins"],
                "losses": value["losses"],
                "net_cash": round(value["net"], 2),
                "win_rate": round(value["wins"] / value["trades"], 6) if value["trades"] else None,
                "tradeoff_status": "broker_net_quality_unacceptable" if value["net"] < 0 else "positive_but_requires_outlier_and_cost_check",
            }
            for key, value in sorted(symbol_health.items())
        ],
    )

    write_jsonl(
        "WAVE2_COUNTERFACTUAL_DECISION_LEDGER.jsonl",
        [
            {
                "row_id": f"counterfactual:{row.get('broker_position_id')}",
                "broker_position_id": row.get("broker_position_id"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "actual_r": row.get("actual_r"),
                "candidate_counterfactual": "NO_TRADE_OR_REDUCE_OR_QUEUE_UNTIL_BROKER_NET_AND_MARKET_STATE_PROOF",
                "source_gap": "exact_best_alternative_window_not_materialized",
            }
            for row in profit_harvest_rows
        ],
    )

    write_jsonl(
        "WAVE2_SYSTEM_LIMITATION_INVENTORY.jsonl",
        [
            {
                "limitation_id": "missing_decision_window_allocator",
                "surface": "scheduler",
                "status": "open",
                "v4_requirement": "decision_window_id_candidate_set_id_open_pending_new_competition",
            },
            {
                "limitation_id": "missing_full_sltp_lifecycle",
                "surface": "execution",
                "status": "open",
                "v4_requirement": "broker_ticket_bound_modify_partial_be_trailing_capture",
            },
            {
                "limitation_id": "missing_runtime_market_whiteboard",
                "surface": "market_whiteboard",
                "status": "open",
                "v4_requirement": "fail_closed_market_state_snapshot",
            },
            {
                "limitation_id": "missing_broker_local_full_spec_export",
                "surface": "cost_broker",
                "status": "open",
                "v4_requirement": "broker_local_cost_session_spec_authority",
            },
        ],
    )
    write_jsonl("WAVE2_PRIMITIVE_COVERAGE_AND_LANE_DISPOSITION_LEDGER.jsonl", lane_rows)
    write_json(
        "WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "plan_materialized_not_executed",
            "partitions": [
                "time_split_walk_forward",
                "leave_one_symbol_out",
                "leave_one_session_out",
                "leave_one_side_out",
                "cost_swap_stress",
                "GER30_outlier_removed",
                "zero_trade_and_reject_counterfactual",
            ],
            "no_api_first": True,
        },
    )
    write_jsonl(
        "WAVE2_ORDERFLOW_MICROSTRUCTURE_DISPOSITION_LEDGER.jsonl",
        [
            {
                "source": "local_MT5_M1_LTF_path",
                "disposition": "immediate_no_paid_replay_source",
                "evidence_path": "shadow_logs/candidate_ltf_path_order.jsonl",
            },
            {
                "source": "tick_path",
                "disposition": "future_capture_or_local_only_when_available",
                "evidence_path": "LiveDecisionPacketV4_capture_contract",
            },
            {
                "source": "Sierra_or_Databento_depth",
                "disposition": "not_introduced_without_explicit_owner_approval_paid_vendor_manifest",
                "evidence_path": "Wave2 controlling prompt safety boundary",
            },
        ],
    )
    write_json(
        "WAVE2_RISK_PORTFOLIO_OPPORTUNITY_COST_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "contract_required_not_implemented",
            "required_fields": [
                "decision_window_id",
                "open_position_risk",
                "pending_order_risk",
                "new_candidate_risk",
                "cluster_correlation_risk",
                "stale_position_opportunity_cost",
                "zero_trade_value",
                "broker_net_ev_per_unit_risk",
            ],
        },
    )
    write_json("WAVE2_CAPTURE_FIELD_CONTRACT_LIVEDECISIONPACKETV4.json", build_live_decision_packet_contract())
    write_json(
        "WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "contract_required_not_implemented",
            "role": "measured_validator_after_no_api_replay",
            "required_controls": ["prompt_schema_versioning", "cache", "budget_cap", "deterministic_baseline", "disagreement_calibration", "fallback_behavior"],
        },
    )
    write_jsonl(
        "WAVE2_IMPLEMENTATION_DECISION_BY_CAUSE_LEDGER.jsonl",
        [
            {
                "cause": row["lane"],
                "decision": "create_or_keep_v4_lane_requirement",
                "question_count": row["question_count"],
                "status": "open_until_wave2_completion",
            }
            for row in lane_rows
        ],
    )
    write_jsonl(
        "WAVE2_EVIDENCE_CLASS_DISPOSITION_LEDGER.jsonl",
        [
            {"evidence_class": cls, "allowed_use": use, "promotion_rule": rule}
            for cls, use, rule in [
                ("broker-real PnL", "authoritative cash outcome", "may drive hard-halt failure claims"),
                ("exact-R", "source-bound R outcome", "do not replace broker cash"),
                ("proxy-R", "fallback estimate", "must be labeled proxy"),
                ("shadow", "counterfactual or source coverage", "not broker-real outcome"),
                ("live authority", "runtime final-say evidence", "separate capture-only from authority"),
                ("source gap", "blocker or prospective capture", "do not infer favorable truth"),
                ("default-off research", "candidate V4 input only", "not live failure proof"),
                ("production code", "current implementation evidence", "separate from live deployment approval"),
            ]
        ],
    )
    write_jsonl(
        "WAVE2_HARD_HALT_FAILURE_TO_V4_REQUIREMENT_LEDGER.jsonl",
        [
            {"failure": "weak_broker_net_admission", "v4_requirement": "Selector V4 fail-closed broker-net admission"},
            {"failure": "allocator_blindness", "v4_requirement": "Scheduler V4 decision-window allocator"},
            {"failure": "mfe_giveback_and_stale_thesis", "v4_requirement": "Profit Harvest / Execution Manager V4"},
            {"failure": "cost_swap_drag", "v4_requirement": "Cost/Swap/Slippage/Broker Constraint Engine"},
            {"failure": "bad_market_system_mismatch", "v4_requirement": "Market Whiteboard V2 hard authority"},
            {"failure": "capture_gaps", "v4_requirement": "LiveDecisionPacketV4 and Data Capture Final"},
        ],
    )
    write_jsonl(
        "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
        [
            {"component": "Selector V3", "halt_time_disposition": "default_off_or_capture_only_not_final_authority", "v4_decision": "mine_and_rebuild_as_Selector_V4"},
            {"component": "Scheduler V3", "halt_time_disposition": "default_off_not_money_risk_authority", "v4_decision": "replace_with_decision_window_allocator"},
            {"component": "Execution Policy V3", "halt_time_disposition": "not full live authority", "v4_decision": "replay_dynamic_policy_under_broker_net_validation"},
        ],
    )
    write_jsonl(
        "WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl",
        [
            {
                "broker": row.get("broker") or row.get("profile") or row.get("authority_surface") or row.get("row_id"),
                "source_path": W1C_AUTHORITY.as_posix(),
                "finding": row,
                "v4_decision": "redacted_account source-brain primary; FTMO follower/projector broker-local truth only",
            }
            for row in w1c_authority
        ],
    )
    write_md(
        "WAVE2_WAVE3_EXECUTION_LIFECYCLE_PROMPT_REQUIREMENTS.md",
        """
# Wave3 Execution Lifecycle Prompt Requirements

Status: requirements only; Wave3 prompt pack remains blocked.

- Require broker-ticket-bound entry/order/deal/position lifecycle capture.
- Require every SLTP modify, partial close, BE, trailing, timeout, manual/emergency close, and terminal broker result.
- Require M1/tick first-passage fields for time to green, +0.25R, +0.5R, +1R, partial, BE, MFE, reversal, target, stop, and stale timeout.
- Require broker-net cost/swap/slippage fields and no favorable inference from missing lifecycle truth.
""",
    )
    ordered_lanes = [
        "hard_halt_causal_microscope_continuation",
        "data_capture_source_repair_final_and_livedecisionpacket_v4",
        "selector_v4",
        "scheduler_v4_best_trade_allocator",
        "cost_swap_slippage_broker_constraint_engine",
        "market_whiteboard_v2",
        "execution_manager_v4",
        "profit_harvest_mfe_capture_v4",
        "dynamic_target_stop_thesis_horizon_geometry_v4",
        "pending_nofill_lifecycle_v4",
        "partial_be_trailing_stale_thesis_exit_policy_v4",
        "dual_broker_runtime_contract",
        "historical_replay_digital_twin_v4",
        "validation_anti_overfit_v4",
        "ai_reliability_cost_control",
        "runtime_control_atomic_halt_safety",
    ]
    write_json(
        "WAVE2_WAVE3_LAUNCH_ORDER.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "candidate_launch_order_not_prompt_pack_authority",
            "wave3_prompt_pack_allowed": False,
            "reason": "final causal package and prompt hardening are not complete",
            "lanes": [
                {
                    "order": index,
                    "lane": lane,
                    "route_dir": f"research/operations/wave3_{lane}_2026_06_04",
                    **lane_provenance(lane, question_rows, interactions, broker_rows, candidate_rows),
                    "prompt_status": "blocked",
                }
                for index, lane in enumerate(ordered_lanes, start=1)
            ],
        },
    )
    write_jsonl(
        "WAVE2_WAVE3_LANE_CONTRACTS.jsonl",
        [
            {
                "lane": lane,
                "launch_order": index,
                **lane_provenance(lane, question_rows, interactions, broker_rows, candidate_rows),
                "required_inputs": ["WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json", "WAVE2_HARD_HALT_FAILURE_TO_V4_REQUIREMENT_LEDGER.jsonl"],
                "must_prove": "source_bound_repair_or_explicit_non_generatable_gap",
                "safety_boundaries": ["no_live_trading_deployment", "no_broker_mutation", "no_paid_api_without_owner_approval"],
                "prompt_status": "blocked_until_wave2_completion",
            }
            for index, lane in enumerate(ordered_lanes, start=1)
        ],
    )
    write_json(
        "WAVE3_LANE_DEPENDENCY_GRAPH.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "candidate_dependency_graph_not_prompt_pack_authority",
            "wave3_prompt_pack_allowed": False,
            "nodes": ordered_lanes,
            "edges": [
                {"from_lane": "hard_halt_causal_microscope_continuation", "to_lane": "data_capture_source_repair_final_and_livedecisionpacket_v4", "dependency": "source_gap_closure_before_schema_finalization"},
                {"from_lane": "data_capture_source_repair_final_and_livedecisionpacket_v4", "to_lane": "selector_v4", "dependency": "selector_requires_packet_source_completeness"},
                {"from_lane": "data_capture_source_repair_final_and_livedecisionpacket_v4", "to_lane": "scheduler_v4_best_trade_allocator", "dependency": "allocator_requires_decision_window_capture"},
                {"from_lane": "cost_swap_slippage_broker_constraint_engine", "to_lane": "selector_v4", "dependency": "selector_admission_must_be_broker_net"},
                {"from_lane": "market_whiteboard_v2", "to_lane": "selector_v4", "dependency": "bad_market_state_must_be_trade_admission_input"},
                {"from_lane": "selector_v4", "to_lane": "scheduler_v4_best_trade_allocator", "dependency": "allocator_competes_selector_outputs_against_no_trade_open_pending"},
                {"from_lane": "scheduler_v4_best_trade_allocator", "to_lane": "execution_manager_v4", "dependency": "execution_receives_allocated_ticket_bound_intent"},
                {"from_lane": "execution_manager_v4", "to_lane": "profit_harvest_mfe_capture_v4", "dependency": "profit_harvest_requires_first_passage_and_lifecycle_events"},
                {"from_lane": "dynamic_target_stop_thesis_horizon_geometry_v4", "to_lane": "execution_manager_v4", "dependency": "execution_requires target_stop_thesis_horizon policy"},
                {"from_lane": "pending_nofill_lifecycle_v4", "to_lane": "scheduler_v4_best_trade_allocator", "dependency": "pending_orders_compete_for_risk_capacity"},
                {"from_lane": "historical_replay_digital_twin_v4", "to_lane": "validation_anti_overfit_v4", "dependency": "validation_requires_replay_partition_ledger"},
                {"from_lane": "validation_anti_overfit_v4", "to_lane": "ai_reliability_cost_control", "dependency": "ai_audit_runs_after_no_api_baselines"},
                {"from_lane": "runtime_control_atomic_halt_safety", "to_lane": "dual_broker_runtime_contract", "dependency": "halt_semantics_apply_to_source_and_target_namespaces"},
            ],
            "lane_provenance": {
                lane: lane_provenance(lane, question_rows, interactions, broker_rows, candidate_rows)
                for lane in ordered_lanes
            },
        },
    )
    write_json(
        "WAVE2_FINAL_MASTER_STATE_TABLE.json",
        {
            "generated_at_utc": GENERATED_AT,
            "status": "not_final_incomplete_master_state",
            "wave3_prompt_pack_allowed": False,
            "headline": {
                "broker_rows": len(broker_rows),
                "candidate_rows": len(candidate_rows),
                "live_authority_rows": len(w1b_rows),
                "broker_net_cash": round(sum(float(row.get("broker_real_pnl_cash") or 0.0) for row in broker_rows), 2),
                "prompt_required_outputs_remaining_before_pack": [
                    "WAVE2_PROMPT_PACK_MANIFEST",
                    "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT",
                    "WAVE3_PER_LANE_CONTROLLING_PROMPTS",
                    "WAVE3_PER_LANE_ONE_LINE_STARTERS",
                ],
            },
            "truths": [
                "full V3 was not halt-time final live authority",
                "recent broker truth was net negative after costs",
                "raw 1.5R candidate geometry is not final dynamic target authority",
                "broker initial targets cluster mostly near 3R",
                "decision-window allocator truth is partially repairable but original runtime intent is non-generatable unless logged",
            ],
            "blocking_gaps": [
                "original runtime allocator packet truth: decision_window_id, candidate_set_id, allocator output, open/pending snapshot, stale exposure cost, fill probability, and broker-net EV per unit risk",
                "full SLTP modify lifecycle",
                "sealed validation execution",
                "final prompt pack and prompt hardening",
            ],
        },
    )
    write_md(
        "WAVE2_V4_REBUILD_THESIS.md",
        """
# Wave2 V4 Rebuild Thesis

Status: draft thesis, not launch authority.

The hard-halt evidence supports a V4 rebuild around fail-closed broker-net admission, explicit best-trade allocation, ticket-bound execution lifecycle capture, cost/swap/slippage hard gates, upstream market whiteboard authority, LiveDecisionPacketV4, and sealed no-API replay before any AI or live promotion.

It does not support a pure bad-market-only explanation, a claim that full V3 failed as halt-time live authority, or a single ambiguous R label for target geometry. The final Wave3 prompt pack remains blocked until the route closes remaining prompt-pack and hardening requirements.
""",
    )


def build_allocator_repair_source_rows() -> list[dict[str, Any]]:
    rows = [
        ("wave2_selector_scheduler_gap", "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl", "4", "names direct allocator gap and key runtime counts", ["candidate_id", "broker_position_id", "symbol", "side", "timestamp_utc"]),
        ("wave2_blocker_best_trade_allocator", "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl", "36", "contains wave2_best_trade_allocator_window_join blocker", ["blocker_id"]),
        ("wave1a_forensic_matrix", W1A_MATRIX.as_posix(), "548", "77 broker-real trades and 471 candidate rows", ["candidate_id", "broker_position_id", "position_id", "trade_id", "decision_time_utc", "entry_time_utc", "symbol", "side"]),
        ("wave1a_portfolio_exposure", (WAVE1A / "PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl").as_posix(), "77", "trade-level exposure and cluster context", ["position_id", "symbol", "entry_time_utc"]),
        ("wave1a_selector_weakness", W1A_SELECTOR.as_posix(), "512", "selected-cell quality and looseness evidence", ["row_id", "symbol", "selected_cell_id"]),
        ("wave1b_live_authority", W1B_MATRIX.as_posix(), "12775", "best final-say/live authority surface", ["material_row_id", "candidate_id", "timestamp_utc", "symbol"]),
        ("wave1b_scheduler_money_gap", (WAVE1B / "SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl").as_posix(), "1", "names Scheduler V4 money-risk source requirements", ["row_id"]),
        ("lane01_portfolio_replay", "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31/LANE01_PORTFOLIO_REPLAY_LEDGER.jsonl", "43", "Friday-style allocator mechanics, offline replay", ["trade_id", "symbol", "decision_time_utc"]),
        ("lane01_input_candidates", "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31/LANE01_INPUT_CANDIDATE_UNIVERSE_LEDGER.jsonl", "328", "candidate universe for allocator replay", ["candidate_id", "symbol", "decision_time_utc"]),
        ("lane02_broad_selected_split", "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/LANE02_BROAD_SELECTED_SPLIT_STRESS_SUMMARY.jsonl", "2145", "broad selected portfolio stress, proxy/offline", ["symbol", "side", "session"]),
        ("lane10_scheduler_replay", "research/operations/vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01/LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz", "289928", "offline allocator math and scheduling replay", ["candidate_id", "symbol", "decision_time_utc"]),
        ("scheduler_v3_full_evidence", "research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_FULL_EVIDENCE_LEDGER.jsonl.gz", "289928", "default-off Scheduler V3 design evidence, not halt-time authority", ["candidate_id", "symbol", "decision_time_utc"]),
        ("lane10b_missed_edge", "research/operations/vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01/LANE10B_MISSED_EDGE_VALUE_LEDGER.jsonl.gz", "222563", "missed-edge and repairable scheduler block source", ["candidate_id", "symbol", "decision_time_utc"]),
        ("runtime_decisions", "shadow_logs/gtos_vnext_runtime_decisions.jsonl", "6187", "runtime FOLLOW/AVOID/source-required rows; no explicit window ids", ["candidate_id", "timestamp_utc", "symbol", "side"]),
        ("pending_lifecycle", "shadow_logs/pending_limit_lifecycle.jsonl", "877", "pending/no-fill/fill lifecycle rows", ["trade_id", "candidate_id", "symbol", "order_id", "ticket"]),
        ("live_opportunity_clusters", "shadow_logs/live_candidate_opportunity_clusters.jsonl", "7257", "opportunity_id and candidate cluster context", ["opportunity_id", "candidate_id", "symbol"]),
        ("opportunity_lifecycle_audit", "shadow_logs/opportunity_lifecycle_audit.jsonl", "8516", "duplicate/overlap opportunity logic", ["opportunity_id", "candidate_id", "symbol"]),
        ("missed_opportunity_shadow", "shadow_logs/missed_opportunity_shadow.jsonl", "7163", "near-miss/no-fill/TP-area alternatives", ["candidate_id", "symbol", "decision_time_utc"]),
        ("mechanical_strategy_shadow", "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl", "262521", "mechanical alternative surface, proxy only", ["candidate_id", "symbol", "strategy_id"]),
        ("candidate_ltf_path_order", "shadow_logs/candidate_ltf_path_order.jsonl", "13721", "path/fillability ordering", ["candidate_id", "trade_id", "symbol", "decision_time_utc"]),
    ]
    return [
        {
            "source_id": source_id,
            "source_path": source_path,
            "reported_row_count": row_count,
            "repair_value": repair_value,
            "join_keys": join_keys,
            "truth_can_answer_now": "partial timestamp/candidate reconstruction of allocator alternatives and opportunity-cost context",
            "remaining_non_generatable_truth": "original runtime decision_window_id, candidate_set_id, full open/pending/stale exposure snapshot, zero-trade value, and exact allocator intent unless already logged",
            "result_use_status": "repair_source_inventory_not_final_allocator_truth",
        }
        for source_id, source_path, row_count, repair_value, join_keys in rows
    ]


def build_allocator_window_source_coverage_rows() -> list[dict[str, Any]]:
    keys = [
        "decision_window_id",
        "candidate_set_id",
        "opportunity_id",
        "computed_opportunity_id",
        "documented_opportunity_id",
        "candidate_id",
        "selected_candidate_id",
        "timestamp_utc",
        "decision_time_utc",
        "candle_time_utc",
        "symbol",
        "broker_symbol",
        "side",
        "position_id",
        "broker_position_id",
        "open_positions",
        "pending_orders",
    ]
    sources = [
        ("runtime_decisions", Path("shadow_logs/gtos_vnext_runtime_decisions.jsonl"), "live runtime final-say rows; timestamp and symbol exist but no durable candidate-set window"),
        ("live_opportunity_clusters", Path("shadow_logs/live_candidate_opportunity_clusters.jsonl"), "opportunity_id and candidate-count context for shadow opportunity grouping"),
        ("opportunity_lifecycle_audit", Path("shadow_logs/opportunity_lifecycle_audit.jsonl"), "computed/documented opportunity ids and lifecycle duplicate logic"),
        ("missed_opportunity_shadow", Path("shadow_logs/missed_opportunity_shadow.jsonl"), "near-miss and no-fill alternatives with candidate/time/symbol/side"),
        ("mechanical_strategy_shadow", Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"), "broad mechanical alternatives with proxy path outcomes"),
        ("candidate_ltf_path_order", Path("shadow_logs/candidate_ltf_path_order.jsonl"), "candidate path/fillability ordering by decision time"),
    ]
    rows: list[dict[str, Any]] = []
    for source_id, source_path, repair_value in sources:
        coverage = jsonl_coverage(source_path, keys, sample_limit=1)
        key_coverage = coverage["coverage"]
        rows.append(
            {
                "source_id": source_id,
                "source_path": source_path.as_posix(),
                "row_count": coverage["row_count"],
                "parse_errors": coverage["parse_errors"],
                "repair_value": repair_value,
                "key_coverage": key_coverage,
                "first_row_keys": coverage["first_row_keys"],
                "truth_can_answer_now": "timestamp/candidate/opportunity reconstruction only; enough for proxy opportunity grouping, not original allocator intent",
                "remaining_non_generatable_truth": [
                    "original_runtime_decision_window_id",
                    "original_runtime_candidate_set_id",
                    "selected_candidate_id_as_allocator_output",
                    "full_open_position_snapshot",
                    "full_pending_order_snapshot",
                    "stale_exposure_opportunity_cost_at_decision",
                    "zero_trade_value_as_runtime_final_say",
                ],
                "coverage_status": "no_exact_allocator_window_ids"
                if key_coverage.get("decision_window_id", 0) == 0 and key_coverage.get("candidate_set_id", 0) == 0
                else "allocator_window_key_present_requires_join_validation",
                "v4_requirement_id": "scheduler_v4_decision_window_capture",
            }
        )
    return rows


def build_path_repair_source_coverage_rows() -> list[dict[str, Any]]:
    keys = [
        "candidate_id",
        "trade_id",
        "position_id",
        "broker_position_id",
        "decision_time_utc",
        "timestamp_utc",
        "entry_first_touch_utc",
        "tp1_first_touch_utc",
        "sl_first_touch_utc",
        "first_touch_times",
        "mfe_r",
        "mae_r",
        "broker_actual_r",
        "actual_r_multiple",
        "timestamp_triggered",
        "timestamp_trailing_exit",
        "timestamp_closed",
        "path_order_label",
        "path_label",
        "ltf_path_order_label",
        "hit_tp1",
        "hit_sl",
    ]
    sources = [
        ("candidate_ltf_path_order", Path("shadow_logs/candidate_ltf_path_order.jsonl"), "first-touch/path-order repair for candidate decisions"),
        ("candidate_path_follow", Path("shadow_logs/candidate_path_follow.jsonl"), "path follow M15/M1 proxy with hit_tp1/hit_sl and bars elapsed"),
        ("candidate_path_contract_audit", Path("shadow_logs/candidate_path_contract_audit.jsonl"), "source contract and first_touch_times coverage"),
        ("prefill_delivery_path_audit", Path("shadow_logs/prefill_delivery_path_audit.jsonl"), "pending/fill delivery and prefill path state"),
        ("broker_actual_r_audit", Path("shadow_logs/broker_actual_r_audit.jsonl"), "broker actual-R audit surface with fill/accounting limits"),
        ("exit_management_shadow_status", Path("shadow_logs/exit_management_shadow_status.jsonl"), "exit-management event status coverage"),
        ("partial_close_shadow_log", Path("shadow_logs/partial_close_shadow_log.jsonl"), "partial-close shadow rows by trade_id only"),
        ("trailing_stop_v1_shadow_log", Path("shadow_logs/trailing_stop_v1_shadow_log.jsonl"), "trailing-stop shadow rows by trade_id only"),
    ]
    rows: list[dict[str, Any]] = []
    for source_id, source_path, repair_value in sources:
        coverage = jsonl_coverage(source_path, keys, sample_limit=1)
        key_coverage = coverage["coverage"]
        rows.append(
            {
                "source_id": source_id,
                "source_path": source_path.as_posix(),
                "row_count": coverage["row_count"],
                "parse_errors": coverage["parse_errors"],
                "repair_value": repair_value,
                "key_coverage": key_coverage,
                "first_row_keys": coverage["first_row_keys"],
                "truth_can_answer_now": "source-bound path/fillability/first-touch proxy repair where candidate_id or trade_id joins exist",
                "remaining_non_generatable_truth": [
                    "broker_ticket_bound_every_tick_path_if_not_logged",
                    "native_mfe_timestamp_for_all_fills",
                    "consolidation_duration_and_reversal_timestamp_without_replay",
                    "exit_manager_original_state_when no event log row exists",
                ],
                "coverage_status": "candidate_or_trade_join_available"
                if key_coverage.get("candidate_id", 0) or key_coverage.get("trade_id", 0)
                else "no_direct_candidate_or_trade_join",
                "v4_requirement_id": "execution_path_first_passage_and_profit_harvest_repair",
            }
        )
    return rows


def build_inferred_allocator_decision_window_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_time: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        by_time[str(row.get("decision_time_utc") or "missing_decision_time")].append(row)

    rows: list[dict[str, Any]] = []
    for index, (decision_time, window_rows) in enumerate(sorted(by_time.items()), start=1):
        filled = [row for row in window_rows if row.get("final_outcome") == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"]
        alternatives = [row for row in window_rows if row.get("final_outcome") != "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"]
        best_alt = max(alternatives, key=lambda item: safe_float(item.get("expectancy_r_source_bound")) or float("-inf"), default=None)
        best_filled = max(filled, key=lambda item: safe_float(item.get("exact_r")) if safe_float(item.get("exact_r")) is not None else float("-inf"), default=None)
        rows.append(
            {
                "inferred_window_id": f"inferred_allocator_window:{index:04d}:{decision_time}",
                "inference_method": "group_wave1a_candidate_trade_records_by_exact_decision_time_utc",
                "window_time_utc": decision_time,
                "candidate_rows": len(window_rows),
                "symbols": sorted({str(row.get("symbol")) for row in window_rows if row.get("symbol")}),
                "sides": sorted({str(row.get("side")) for row in window_rows if row.get("side")}),
                "selected_or_filled_candidate_ids": [row.get("candidate_id") for row in filled],
                "rejected_skipped_no_trade_candidate_ids": [row.get("candidate_id") for row in alternatives],
                "filled_count": len(filled),
                "alternative_count": len(alternatives),
                "has_same_timestamp_alternatives_for_filled": bool(filled and alternatives),
                "selected_broker_real_result": [
                    {
                        "candidate_id": row.get("candidate_id"),
                        "broker_position_id": row.get("broker_position_id"),
                        "symbol": row.get("symbol"),
                        "side": row.get("side"),
                        "broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
                        "exact_r": row.get("exact_r"),
                        "mfe_r": row.get("mfe_r"),
                        "mae_r": row.get("mae_r"),
                    }
                    for row in filled
                ],
                "best_filled_by_exact_r": {
                    "candidate_id": best_filled.get("candidate_id"),
                    "exact_r": best_filled.get("exact_r"),
                    "broker_real_pnl_cash": best_filled.get("broker_real_pnl_cash"),
                }
                if best_filled
                else None,
                "best_rejected_or_skipped_by_source_expectancy": {
                    "candidate_id": best_alt.get("candidate_id"),
                    "symbol": best_alt.get("symbol"),
                    "side": best_alt.get("side"),
                    "final_outcome": best_alt.get("final_outcome"),
                    "expectancy_r_source_bound": best_alt.get("expectancy_r_source_bound"),
                    "selected_cell_rows": best_alt.get("selected_cell_rows"),
                    "source_completeness_status": best_alt.get("source_completeness_status"),
                }
                if best_alt
                else None,
                "selected_vs_best_delta": {
                    "best_filled_exact_r_minus_best_alt_expectancy_r": round((safe_float(best_filled.get("exact_r")) or 0.0) - (safe_float(best_alt.get("expectancy_r_source_bound")) or 0.0), 6)
                    if best_filled and best_alt
                    else None
                },
                "reconstructed_open_position_snapshot": None,
                "reconstructed_pending_order_snapshot": None,
                "missing_runtime_truth": [
                    "original_decision_window_id",
                    "original_candidate_set_id",
                    "runtime_selected_candidate_id",
                    "open_position_snapshot",
                    "pending_order_snapshot",
                    "stale_exposure_opportunity_cost",
                    "zero_trade_value",
                    "broker_net_ev_per_unit_risk",
                    "fill_probability_at_decision",
                ],
                "evidence_class": "source_bound_reconstruction_not_original_runtime_intent",
                "result_use_status": "diagnostic_only_not_final_allocator_truth",
                "status": "inferred_window_repair_available_exact_runtime_intent_not_generatable",
            }
        )
    return rows


def build_allocator_opportunity_cost_window_rows(
    candidate_rows: list[dict[str, Any]],
    candidate_geometry_rows: list[dict[str, Any]],
    artifact_family: str,
) -> list[dict[str, Any]]:
    quality_by_candidate_id = {
        row.get("candidate_id"): row.get("candidate_quality_classification")
        for row in candidate_geometry_rows
        if row.get("candidate_id")
    }

    def candidate_summary(row: dict[str, Any]) -> dict[str, Any]:
        final_outcome = str(row.get("final_outcome") or "")
        is_filled = final_outcome == "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"
        if is_filled and row.get("broker_position_id"):
            row_class = "filled_realized_selection_proxy"
        elif final_outcome.startswith("REJECTED"):
            row_class = "rejected_gate_alternative"
        elif final_outcome.startswith("SKIPPED"):
            row_class = "skipped_zero_trade_alternative"
        elif final_outcome.startswith("LIMIT_CANCELLED"):
            row_class = "cancelled_or_not_filled_attempted_candidate"
        else:
            row_class = "candidate_outcome_other_or_unknown"
        decision_time_value_r = safe_float(row.get("expectancy_r_source_bound"))
        actual_exact_r = safe_float(row.get("exact_r"))
        proxy_r = safe_float(row.get("proxy_r"))
        selected_cell_risk_pct = safe_float(row.get("selected_cell_risk_pct"))
        if decision_time_value_r is not None:
            decision_time_value_source = "expectancy_r_source_bound"
        elif proxy_r is not None:
            decision_time_value_source = "proxy_r_fallback_not_decision_time_expectancy"
            decision_time_value_r = proxy_r
        else:
            decision_time_value_source = "missing_decision_time_value"
        return {
            "candidate_row_key": row.get("trade_id") or row.get("source_path") or row.get("candidate_id"),
            "row_class": row_class,
            "candidate_id": row.get("candidate_id"),
            "trade_id": row.get("trade_id"),
            "source_path": row.get("source_path"),
            "source_sha256": row.get("source_sha256"),
            "broker_position_id": row.get("broker_position_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "decision_time_utc": row.get("decision_time_utc"),
            "final_outcome": row.get("final_outcome"),
            "is_filled_broker_joined": bool(is_filled and row.get("broker_position_id")),
            "broker_join_status": row.get("broker_join_status"),
            "execution_fill_state": row.get("execution_fill_state"),
            "execution_policy": row.get("execution_policy"),
            "execution_policy_id": row.get("execution_policy_id"),
            "candidate_quality_classification": quality_by_candidate_id.get(row.get("candidate_id")),
            "decision_time_value_r": round(decision_time_value_r, 6) if decision_time_value_r is not None else None,
            "decision_time_value_source": decision_time_value_source,
            "actual_exact_r": round(actual_exact_r, 6) if actual_exact_r is not None else None,
            "exact_r_status": row.get("exact_r_status"),
            "actual_broker_real_pnl_cash": row.get("broker_real_pnl_cash"),
            "actual_value_source": "broker_real_exact_r" if is_filled and actual_exact_r is not None else "not_available_for_unfilled_or_unjoined_candidate",
            "proxy_r": round(proxy_r, 6) if proxy_r is not None else None,
            "proxy_r_status": row.get("proxy_r_status"),
            "mfe_r": row.get("mfe_r"),
            "mae_r": row.get("mae_r"),
            "giveback_r": row.get("giveback_r"),
            "selected_cell_id": row.get("selected_cell_id"),
            "selected_cell_rows": row.get("selected_cell_rows"),
            "selected_cell_risk_pct": round(selected_cell_risk_pct, 6) if selected_cell_risk_pct is not None else None,
            "selected_cell_win_rate": row.get("selected_cell_win_rate"),
            "selected_cell_profit_factor": row.get("selected_cell_profit_factor"),
            "source_completeness_status": row.get("source_completeness_status"),
            "source_capture_status": row.get("source_capture_status"),
            "branch_decision": row.get("branch_decision"),
            "implementation_decision": row.get("implementation_decision"),
        }

    def best_by(items: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
        scored = [(safe_float(item.get(key)), item) for item in items]
        scored = [(score, item) for score, item in scored if score is not None]
        if not scored:
            return None
        return max(scored, key=lambda pair: pair[0])[1]

    inferred_rows = build_inferred_allocator_decision_window_rows(candidate_rows)
    rows: list[dict[str, Any]] = []
    for inferred in inferred_rows:
        window_rows = [
            row
            for row in candidate_rows
            if str(row.get("decision_time_utc") or "missing_decision_time") == inferred["window_time_utc"]
        ]
        summaries = [candidate_summary(row) for row in window_rows]
        filled = [row for row in summaries if row.get("is_filled_broker_joined")]
        alternatives = [row for row in summaries if not row.get("is_filled_broker_joined")]
        no_trade_or_rejected = [
            row
            for row in alternatives
            if str(row.get("final_outcome") or "").startswith(("SKIPPED", "REJECTED"))
        ]
        filled_risks = [
            risk
            for risk in (safe_float(row.get("selected_cell_risk_pct")) for row in filled)
            if risk is not None
        ]
        max_selected_risk = max(filled_risks) if filled_risks else None
        lower_risk_alternatives = [
            row
            for row in alternatives
            if max_selected_risk is None
            or (
                safe_float(row.get("selected_cell_risk_pct")) is not None
                and (safe_float(row.get("selected_cell_risk_pct")) or 0.0) <= max_selected_risk
            )
        ]
        same_symbol_alternatives = [
            row
            for row in alternatives
            if row.get("symbol") in {filled_row.get("symbol") for filled_row in filled}
        ]
        best_selected_actual = best_by(filled, "actual_exact_r")
        best_selected_decision_value = best_by(filled, "decision_time_value_r")
        best_alt_decision_value = best_by(alternatives, "decision_time_value_r")
        best_no_trade_decision_value = best_by(no_trade_or_rejected, "decision_time_value_r")
        best_lower_risk_decision_value = best_by(lower_risk_alternatives, "decision_time_value_r")
        best_same_symbol_decision_value = best_by(same_symbol_alternatives, "decision_time_value_r")
        if best_alt_decision_value is None and alternatives:
            best_alt_decision_value = {
                **alternatives[0],
                "best_alternative_rank_status": "no_numeric_decision_time_value_available_source_gap",
            }
        if best_no_trade_decision_value is None and no_trade_or_rejected:
            best_no_trade_decision_value = {
                **no_trade_or_rejected[0],
                "best_alternative_rank_status": "no_numeric_decision_time_value_available_source_gap",
            }
        if best_lower_risk_decision_value is None and lower_risk_alternatives:
            best_lower_risk_decision_value = {
                **lower_risk_alternatives[0],
                "best_alternative_rank_status": "no_numeric_decision_time_value_available_source_gap",
            }
        if best_same_symbol_decision_value is None and same_symbol_alternatives:
            best_same_symbol_decision_value = {
                **same_symbol_alternatives[0],
                "best_alternative_rank_status": "no_numeric_decision_time_value_available_source_gap",
            }

        selected_actual = safe_float(best_selected_actual.get("actual_exact_r")) if best_selected_actual else None
        selected_decision = safe_float(best_selected_decision_value.get("decision_time_value_r")) if best_selected_decision_value else None
        alt_decision = safe_float(best_alt_decision_value.get("decision_time_value_r")) if best_alt_decision_value else None
        no_trade_decision = safe_float(best_no_trade_decision_value.get("decision_time_value_r")) if best_no_trade_decision_value else None
        lower_risk_decision = safe_float(best_lower_risk_decision_value.get("decision_time_value_r")) if best_lower_risk_decision_value else None

        if filled and alternatives:
            allocation_finding = "filled_window_with_same_timestamp_alternatives"
            implementation_decision = "Scheduler V4 must compare all same-window candidates, no-trade, and lower-risk alternatives before risk allocation"
        elif filled:
            allocation_finding = "filled_window_no_same_timestamp_alternative_in_wave1a_candidate_source"
            implementation_decision = "Scheduler V4 must still capture candidate_set_id/open_pending_snapshot because historical same-window absence is not proof of no competing risk"
        else:
            allocation_finding = "no_filled_candidate_window_preserves_zero_trade_or_rejection_value"
            implementation_decision = "Selector V4 and Scheduler V4 must preserve no-trade/reject rows as explicit allocator options"

        rows.append(
            {
                "row_id": inferred["inferred_window_id"].replace("inferred_allocator_window:", f"{artifact_family}:"),
                "artifact_family": artifact_family,
                "source_inferred_window_id": inferred["inferred_window_id"],
                "inferred_window_id": inferred["inferred_window_id"],
                "window_time_utc": inferred["window_time_utc"],
                "inference_method": inferred["inference_method"],
                "allocator_truth_status": "not_original_runtime_allocator_truth",
                "allocator_intent_status": "original_runtime_allocator_intent_not_generatable_from_current_sources",
                "selected_runtime_truth_source": "broker_filled_candidate_rows_only_runtime_selected_candidate_id_missing",
                "candidate_set_truth_source": "reconstructed_by_exact_decision_time_utc",
                "candidate_set_truth_status": "timestamp_grouped_not_original_candidate_set",
                "evidence_class": "source_bound_reconstruction_not_original_runtime_intent",
                "result_use_status": "diagnostic_only_not_final_allocator_truth",
                "status": "per_window_allocator_opportunity_cost_materialized_with_runtime_intent_gap",
                "source_paths": [
                    W1A_MATRIX.as_posix(),
                    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl",
                ],
                "candidate_rows": len(summaries),
                "candidate_count": len(summaries),
                "candidate_ids_all": [row.get("candidate_id") for row in summaries],
                "candidate_row_keys_all": [row.get("candidate_row_key") for row in summaries],
                "filled_count": len(filled),
                "alternative_count": len(alternatives),
                "rejected_count": sum(1 for row in alternatives if str(row.get("final_outcome") or "").startswith("REJECTED")),
                "skipped_count": sum(1 for row in alternatives if str(row.get("final_outcome") or "").startswith("SKIPPED")),
                "cancelled_count": sum(1 for row in alternatives if str(row.get("final_outcome") or "").startswith("LIMIT_CANCELLED")),
                "symbols": sorted({str(row.get("symbol")) for row in summaries if row.get("symbol")}),
                "sides": sorted({str(row.get("side")) for row in summaries if row.get("side")}),
                "final_outcome_counts": counter_dict(Counter(row.get("final_outcome") for row in summaries)),
                "selected_or_filled_candidate_ids": [row.get("candidate_id") for row in filled],
                "rejected_skipped_no_trade_candidate_ids": [row.get("candidate_id") for row in alternatives],
                "candidate_rows_full_preserved": summaries,
                "selected_broker_real_result": filled,
                "best_selected_by_broker_real_exact_r": best_selected_actual,
                "best_selected_by_decision_time_expectancy": best_selected_decision_value,
                "best_rejected_skipped_or_no_trade_by_decision_time_expectancy": best_alt_decision_value,
                "best_filled_by_exact_r": best_selected_actual,
                "best_rejected_or_skipped_by_source_expectancy": best_alt_decision_value,
                "best_no_trade_or_rejected_by_decision_time_expectancy": best_no_trade_decision_value,
                "best_lower_risk_alternative_by_decision_time_expectancy": best_lower_risk_decision_value,
                "best_same_symbol_alternative_by_decision_time_expectancy": best_same_symbol_decision_value,
                "selected_vs_alternative_deltas": {
                    "filled_exact_r_minus_alt_source_expectancy_r_not_realized_delta": round(selected_actual - alt_decision, 6)
                    if selected_actual is not None and alt_decision is not None
                    else None,
                    "best_selected_actual_exact_r_minus_best_alt_decision_expectancy_r": round(selected_actual - alt_decision, 6)
                    if selected_actual is not None and alt_decision is not None
                    else None,
                    "best_alt_decision_expectancy_r_minus_best_selected_actual_exact_r": round(alt_decision - selected_actual, 6)
                    if selected_actual is not None and alt_decision is not None
                    else None,
                    "best_selected_decision_expectancy_r_minus_best_alt_decision_expectancy_r": round(selected_decision - alt_decision, 6)
                    if selected_decision is not None and alt_decision is not None
                    else None,
                    "best_no_trade_decision_expectancy_r_minus_best_selected_decision_expectancy_r": round(no_trade_decision - selected_decision, 6)
                    if selected_decision is not None and no_trade_decision is not None
                    else None,
                    "best_lower_risk_decision_expectancy_r_minus_best_selected_decision_expectancy_r": round(lower_risk_decision - selected_decision, 6)
                    if selected_decision is not None and lower_risk_decision is not None
                    else None,
                },
                "selected_vs_best_delta": {
                    "best_filled_exact_r_minus_best_alt_expectancy_r": round(selected_actual - alt_decision, 6)
                    if selected_actual is not None and alt_decision is not None
                    else None,
                    "comparison_caveat": "cross_evidence_diagnostic_only_filled_exact_r_vs_unfilled_source_expectancy_not_realized_counterfactual",
                },
                "zero_trade_comparator": {
                    "available_same_timestamp": best_no_trade_decision_value is not None,
                    "comparator_candidate_id": best_no_trade_decision_value.get("candidate_id") if best_no_trade_decision_value else None,
                    "decision_time_expectancy_r": no_trade_decision,
                    "source_status": "same_timestamp_nonfilled_candidate_available"
                    if best_no_trade_decision_value
                    else "no_same_timestamp_nonfilled_candidate_in_wave1a_source",
                },
                "virtual_no_trade_baseline": {
                    "no_trade_baseline_r": 0.0,
                    "no_trade_baseline_cash": 0.0,
                    "no_trade_truth_status": "synthetic_baseline_not_runtime_intent",
                },
                "shadow_alternative_comparator": {
                    "available": False,
                    "source_status": "not_available_in_current_window_repair_sources",
                    "missing_fields": ["shadow_alternative_outcome_r", "shadow_alternative_pnl_cash", "candidate_set_shadow_rank"],
                },
                "open_pending_stale_exposure_comparator": {
                    "available": False,
                    "source_status": "not_available_without_original_decision_window_packet",
                    "missing_fields": ["open_position_snapshot", "pending_order_snapshot", "stale_exposure_opportunity_cost"],
                },
                "open_position_snapshot_status": "missing_original_runtime_packet",
                "pending_order_snapshot_status": "missing_original_runtime_packet",
                "stale_exposure_status": "missing_original_runtime_packet",
                "missing_runtime_truth": inferred["missing_runtime_truth"],
                "allocation_finding": allocation_finding,
                "v4_requirement_id": "SCHEDULER_V4_BEST_TRADE_ALLOCATOR_DECISION_WINDOW",
                "owning_wave3_lane": "scheduler_v4_best_trade_allocator",
                "implementation_decision": implementation_decision,
            }
        )
    return rows


def build_instruction_coverage_checklist() -> dict[str, Any]:
    return {
        "generated_at_utc": GENERATED_AT,
        "status": "instruction_coverage_recorded_for_initial_spine_not_completion",
        "goal_session_research_discipline_read_after_preflight": True,
        "research_operating_doctrine_read_after_preflight": True,
        "lane_type": "builder_integration_master_orchestration_not_g12_g0_audit",
        "builder_posture_applied": [
            "curiosity",
            "truthfulness",
            "active_creativity",
            "result_materialization",
            "full_same_evidence_class_pursuit",
            "no_conservative_brake",
        ],
        "anti_boxing_questions_pursued": [
            "was failure selector quality rather than frequency only",
            "were rejected/skipped/no-trade rows material alternatives",
            "was target geometry raw prompt R, dynamic runtime R, broker placement, or realized R",
            "was market bad, system bad, or market-system mismatch",
            "which historical truths are source-repairable versus non-generatable",
        ],
        "outside_current_edge_mechanisms_considered": [
            "broker-net cost and swap drag",
            "best-trade allocator opportunity cost",
            "profit-harvest and MFE giveback",
            "market whiteboard fail-closed state",
            "dual-broker source-target namespace constraints",
            "AI reliability as measured subsystem rather than brute-force replay engine",
        ],
        "proof_or_impossibility_stop_condition": "same-evidence-class repairs remain active until repaired, source-proven non-generatable, or reduced to exact prospective capture requirements",
        "deliberately_unanswered_gated_items": [
            "Wave3 prompt pack generation",
            "live trading deployment",
            "broker/account/order/deal/position mutation",
            "paid API/vendor source pulls",
            "active VPS process changes",
            "remote push",
        ],
    }


def lane_provenance(
    lane: str,
    question_rows: list[dict[str, Any]],
    interaction_rows: list[dict[str, Any]],
    broker_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    lane_question_map = {
        "hard_halt_causal_microscope_continuation": ["W2Q_MISSING_BROKER_TRADE_GEOMETRY", "W2Q_SELECTOR_QUALITY", "W2Q_ENTRY_PATH_MFE_MAE", "W2Q_COST_BROKER_NET", "W2Q_BAD_MARKET_VS_SYSTEM"],
        "data_capture_source_repair_final_and_livedecisionpacket_v4": ["W2Q_CAPTURE_GAPS", "W2Q_FINAL_SAY_AUTHORITY", "W2Q_MISSING_BROKER_TRADE_GEOMETRY"],
        "selector_v4": ["W2Q_SELECTOR_QUALITY", "W2Q_REJECT_SKIP_ZERO_TRADE", "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE"],
        "scheduler_v4_best_trade_allocator": ["W2Q_BEST_TRADE_ALLOCATOR", "W2Q_REJECT_SKIP_ZERO_TRADE"],
        "cost_swap_slippage_broker_constraint_engine": ["W2Q_COST_BROKER_NET"],
        "market_whiteboard_v2": ["W2Q_BAD_MARKET_VS_SYSTEM", "W2Q_DOMINANT_DAMAGE_SYMBOL_QUARANTINE"],
        "execution_manager_v4": ["W2Q_ENTRY_PATH_MFE_MAE", "W2Q_PENDING_NOFILL_AS_FIRST_CLASS"],
        "profit_harvest_mfe_capture_v4": ["W2Q_LOSER_MFE_HARVEST", "W2Q_ENTRY_PATH_MFE_MAE"],
        "dynamic_target_stop_thesis_horizon_geometry_v4": ["W2Q_STATIC_R_GEOMETRY", "W2Q_LOSER_MFE_HARVEST"],
        "pending_nofill_lifecycle_v4": ["W2Q_PENDING_NOFILL_AS_FIRST_CLASS", "W2Q_REJECT_SKIP_ZERO_TRADE"],
        "partial_be_trailing_stale_thesis_exit_policy_v4": ["W2Q_LOSER_MFE_HARVEST", "W2Q_STATIC_R_GEOMETRY"],
        "dual_broker_runtime_contract": ["W2Q_DUAL_BROKER_CONSTRAINTS", "W2Q_FTMO_NO_COPY_RULE"],
        "historical_replay_digital_twin_v4": ["W2Q_VALIDATION_REPLAY", "W2Q_ENTRY_PATH_MFE_MAE", "W2Q_BEST_TRADE_ALLOCATOR"],
        "validation_anti_overfit_v4": ["W2Q_VALIDATION_REPLAY", "W2Q_COST_BROKER_NET"],
        "ai_reliability_cost_control": ["W2Q_AI_RELIABILITY"],
        "runtime_control_atomic_halt_safety": ["W2Q_FINAL_SAY_AUTHORITY", "W2Q_CAPTURE_GAPS"],
    }
    question_ids = lane_question_map.get(lane) or [row["question_id"] for row in question_rows if row.get("derived_wave3_lane") == lane]
    if not question_ids:
        question_ids = [row["question_id"] for row in question_rows]
    interaction_map = {
        "selector_v4": ["W2INT-001", "W2INT-002"],
        "scheduler_v4_best_trade_allocator": ["W2INT-002", "W2INT-003"],
        "execution_manager_v4": ["W2INT-003", "W2INT-004"],
        "profit_harvest_mfe_capture_v4": ["W2INT-004", "W2INT-005"],
        "dynamic_target_stop_thesis_horizon_geometry_v4": ["W2INT-003", "W2INT-004", "W2INT-005"],
        "cost_swap_slippage_broker_constraint_engine": ["W2INT-005"],
        "market_whiteboard_v2": ["W2INT-006"],
        "runtime_control_atomic_halt_safety": ["W2INT-007"],
        "dual_broker_runtime_contract": ["W2INT-008"],
    }
    interaction_ids = interaction_map.get(lane, [row["interaction_id"] for row in interaction_rows])
    return {
        "derived_from_question_ids": question_ids,
        "derived_from_interaction_ids": interaction_ids,
        "derived_from_broker_rows": [f"WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl:{len(broker_rows)}_rows"],
        "derived_from_candidate_rows": [f"WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl:{len(candidate_rows)}_wave1a_candidate_rows_plus_12775_live_authority_rows"],
        "derived_from_code_config_paths": [
            "config/agent_config.yaml",
            "src/components/orchestrator.py",
            "src/components/execution.py",
            "src/components/permissions.py",
        ],
        "derived_from_source_gaps": [
            "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl",
            "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl",
            "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
            "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl",
        ],
    }


def build_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if path.is_file():
            rel_path = rel(path)
            rows = None
            if path.suffix == ".jsonl":
                with path.open(encoding="utf-8") as handle:
                    rows = sum(1 for line in handle if line.strip())
            files.append(
                {
                    "path": rel_path,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(Path(rel_path)),
                    "jsonl_rows": rows,
                }
            )
    return {
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "completion_status": "initial_spine_materialized_not_complete_allocator_window_repair_added",
        "files": files,
    }


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)

    w1a_rows = read_jsonl(W1A_MATRIX)
    w1a_selector = read_jsonl(W1A_SELECTOR)
    w1a_gaps = read_jsonl(W1A_GAPS)
    w1b_rows = read_jsonl(W1B_MATRIX)
    w1b_repairs = read_jsonl(W1B_REPAIRS)
    w1c_authority = read_jsonl(W1C_AUTHORITY)
    hard_halt_orders_payload = read_json(HARD_HALT / "BROKER_TRUTH_ORDERS_2026_04_27_TO_HALT.json")
    hard_halt_trade_groups_payload = read_json(HARD_HALT / "BROKER_TRUTH_TRADE_GROUPS_2026_04_27_TO_HALT.json")
    if not isinstance(hard_halt_orders_payload, list):
        raise ValueError("hard-halt broker orders payload is not a list")

    broker_rows = [row for row in w1a_rows if row.get("row_type") == "broker_grouped_trade"]
    candidate_rows = [row for row in w1a_rows if row.get("row_type") == "candidate_trade_record"]
    broker_order_geometry_rows = build_broker_order_geometry_rows(broker_rows, hard_halt_orders_payload)
    candidate_geometry_rows = build_candidate_geometry_rows(candidate_rows, broker_order_geometry_rows)
    cost_broker_rows, cost_broker_summary = build_cost_broker_rows(broker_rows, hard_halt_trade_groups_payload)
    profit_harvest_rows = build_profit_harvest_rows(candidate_rows)
    loser_mfe_repair_rows = build_loser_mfe_repair_rows(profit_harvest_rows)
    shadow_path_source_rows = build_shadow_path_source_coverage_rows(candidate_rows)
    exemplar_rows = build_row_level_exemplar_rows(profit_harvest_rows, cost_broker_rows)
    selector_ledger_rows = list(build_selector_ledger(broker_rows, w1a_selector))
    static_r_summary = build_static_r_summary(candidate_geometry_rows, broker_order_geometry_rows)
    metrics = build_metrics(w1a_rows, w1b_rows, w1c_authority)
    counts = {
        "wave1a": {
            "matrix_rows": len(w1a_rows),
            "broker_rows": len(broker_rows),
            "candidate_rows": len(candidate_rows),
        },
        "wave1b": {"live_authority_rows": len(w1b_rows)},
        "wave1c": {"authority_rows": len(w1c_authority)},
        "wave1_integration": {"decision_rows": len(read_jsonl(WAVE1I / "WAVE1_INTEGRATION_DECISION_LEDGER.jsonl"))},
    }
    audit_summaries = {
        "wave1a": {"ok": True, "note": "artifact_audit_full_jsonl_passed_current_session"},
        "wave1b": {"ok": True, "note": "artifact_audit_full_jsonl_passed_current_session"},
        "wave1c": {"ok": True, "note": "artifact_audit_full_jsonl_passed_current_session_with_no_blocker_ledger_warning"},
        "wave1_integration": {"ok": True, "note": "artifact_audit_full_jsonl_passed_current_session"},
    }

    write_json("WAVE2_CONTEXT_ANCHOR.json", build_context_anchor())
    write_jsonl("WAVE2_SEARCHED_ROOT_LEDGER.jsonl", build_searched_roots())
    write_jsonl("WAVE2_SOURCE_INVENTORY.jsonl", build_source_inventory())
    write_jsonl("WAVE2_WAVE1_INPUT_INSPECTION_LEDGER.jsonl", build_input_inspection(audit_summaries, counts))
    write_json("WAVE2_CANDIDATE_FUNNEL_QUALITY_METRICS.json", metrics)
    write_json("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json", {
        "generated_at_utc": GENERATED_AT,
        "status": "initial_full_row_universe_preserved_for_wave2_pursuit",
        "broker_trade_rows_preserved": len(broker_rows),
        "wave1a_candidate_rows_preserved": len(candidate_rows),
        "wave1b_material_live_authority_rows_preserved": len(w1b_rows),
        "combined_candidate_or_live_authority_rows_preserved": len(candidate_rows) + len(w1b_rows),
        "no_arbitrary_top_n_used": True,
        "coverage_gap": "causal explanations are initial and require deeper same-evidence-class Wave2 joins before completion",
    })
    write_jsonl("WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl", build_trade_rows(broker_rows))
    write_jsonl("WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl", build_candidate_rows(candidate_rows, w1b_rows))
    write_jsonl("WAVE2_SELECTOR_LOOSENESS_AND_TRADE_QUALITY_LEDGER.jsonl", selector_ledger_rows)
    write_jsonl("WAVE2_LIVE_AUTHORITY_FINAL_SAY_MATRIX.jsonl", build_final_say_matrix(w1b_rows))
    questions = build_questions(metrics)
    write_jsonl("WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl", questions)
    write_jsonl("WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl", [row for row in questions if row["origin"] not in {"seed_prompt", "owner_correction"}])
    graph, interactions = build_interactions()
    write_json("WAVE2_SYSTEM_INTERACTION_GRAPH.json", graph)
    write_jsonl("WAVE2_ACCEPT_REJECT_MANAGE_EXIT_INTERACTION_LEDGER.jsonl", interactions)
    write_jsonl("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl", build_blockers(w1a_gaps, w1b_repairs))
    write_jsonl("WAVE2_DECISION_LEDGER.jsonl", build_decisions())
    write_json("WAVE2_FOCUSED_TEST_RESULT.json", build_focused_test_result())

    write_jsonl("WAVE2_DEEP_REVIEW_SUBAGENT_LEDGER.jsonl", build_subagent_rows())
    write_jsonl("WAVE2_SUBAGENT_ROSTER_AND_FINDINGS_LEDGER.jsonl", read_jsonl(Path(rel(ROUTE_DIR / "WAVE2_DEEP_REVIEW_SUBAGENT_LEDGER.jsonl"))))
    write_jsonl("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl", build_new_intelligence_rows())
    write_jsonl("WAVE2_STATIC_R_GEOMETRY_SOURCE_INVENTORY.jsonl", build_static_r_source_inventory())
    write_jsonl("WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl", candidate_geometry_rows)
    write_jsonl("WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl", broker_order_geometry_rows)
    write_jsonl("WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl", build_sltp_modify_lifecycle_source_coverage_rows(broker_rows, hard_halt_orders_payload))
    write_jsonl("WAVE2_STATIC_R_GEOMETRY_JOIN_GAP_LEDGER.jsonl", build_static_r_gap_rows(candidate_geometry_rows, broker_order_geometry_rows))
    write_json("WAVE2_STATIC_R_GEOMETRY_AUDIT_SUMMARY.json", static_r_summary)
    write_jsonl("WAVE2_COST_BROKER_NET_CAUSAL_LEDGER.jsonl", cost_broker_rows)
    write_json("WAVE2_COST_BROKER_NET_SUMMARY.json", cost_broker_summary)
    write_jsonl("WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl", build_selector_scheduler_opportunity_rows(candidate_geometry_rows, w1a_rows, w1b_rows))
    write_jsonl("WAVE2_MARKET_VS_SYSTEM_WHITEBOARD_LEDGER.jsonl", build_market_vs_system_rows(broker_rows))
    write_jsonl("WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl", profit_harvest_rows)
    write_jsonl("WAVE2_LOSER_MFE_REPAIR_LEDGER.jsonl", loser_mfe_repair_rows)
    write_jsonl("WAVE2_SHADOW_PATH_SOURCE_COVERAGE_LEDGER.jsonl", shadow_path_source_rows)
    write_jsonl("WAVE2_ROW_LEVEL_CAUSAL_EXEMPLAR_LEDGER.jsonl", exemplar_rows)
    write_jsonl("WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER.jsonl", build_capture_replay_ai_production_rows())
    write_jsonl("WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl", build_production_component_disposition_rows())
    write_jsonl("WAVE2_DEPLOYABLE_SCOPE_LFS_AND_ROLLBACK_LEDGER.jsonl", build_deployable_scope_rows())
    write_json("WAVE2_LIVE_DECISION_PACKET_V4_CAPTURE_CONTRACT.json", build_live_decision_packet_contract())
    write_json("WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json", build_validation_contract())
    write_jsonl("WAVE2_ALLOCATOR_DECISION_WINDOW_REPAIR_SOURCE_LEDGER.jsonl", build_allocator_repair_source_rows())
    write_jsonl("WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl", build_allocator_window_source_coverage_rows())
    write_jsonl("WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl", build_inferred_allocator_decision_window_rows(candidate_rows))
    write_jsonl("WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl", build_path_repair_source_coverage_rows())
    write_json("WAVE2_INSTRUCTION_COVERAGE_CHECKLIST.json", build_instruction_coverage_checklist())
    build_and_write_additional_prompt_named_artifacts(
        questions=questions,
        interactions=interactions,
        broker_rows=broker_rows,
        candidate_rows=candidate_rows,
        candidate_geometry_rows=candidate_geometry_rows,
        broker_order_geometry_rows=broker_order_geometry_rows,
        cost_broker_rows=cost_broker_rows,
        profit_harvest_rows=profit_harvest_rows,
        loser_mfe_repair_rows=loser_mfe_repair_rows,
        shadow_path_source_rows=shadow_path_source_rows,
        w1b_rows=w1b_rows,
        w1c_authority=w1c_authority,
        selector_rows=selector_ledger_rows,
    )
    prompt_gap_rows, prompt_gap_summary = build_prompt_required_output_gap_rows()
    write_jsonl("WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_LEDGER.jsonl", prompt_gap_rows)
    write_json("WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_SUMMARY.json", prompt_gap_summary)

    write_md(
        "WAVE2_STATIC_R_GEOMETRY_AUDIT_SUMMARY.md",
        f"""
# Wave2 Static-R / Target Geometry Audit

Status: materialized, incomplete for full SLTP modify lifecycle.

- Candidate trade record rows: {static_r_summary["candidate_trade_record_rows"]}
- Filled candidate rows: {static_r_summary["filled_candidate_rows"]}
- Broker order geometry rows: {static_r_summary["broker_order_geometry_rows"]}
- Raw candidate RR counts: {static_r_summary["raw_rr_counts"]}
- Filled dynamic final target counts: {static_r_summary["dynamic_final_target_counts_filled"]}
- Broker order target buckets at tolerance 0.25R: {static_r_summary["broker_order_target_bucket_0_25"]}

Conclusion: {static_r_summary["semantic_conclusion"]}

The open gap is not whether one ambiguous R value exists. The route must preserve raw prompt geometry, repaired geometry, selected policy, dynamic trigger/final R, broker initial SL/TP, every SLTP modification, partial/BE/trailing/time-stop events, realized R, and broker-net costs separately.
""",
    )

    write_md(
        "WAVE2_SATURATION_SELF_RED_TEAM.md",
        """
# Wave2 Saturation Self-Red-Team - Initial Spine

Status: incomplete. This pass only red-teams the initial Wave1-consumption spine.

- Every broker-real hard-halt trade from Wave1A is preserved in `WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl`.
- Every Wave1A candidate row and every Wave1B material live-authority row is preserved in `WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl`.
- No arbitrary top-N was used for the preserved row universe.
- A follow-on source-bound tick pass materializes `WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl` for filled-trade first-passage, MFE, MAE, giveback, and reversal diagnostics where local tick windows exist, and rewrites the required path-family ledgers from placeholder aliases into tick-derived evidence rows.
- A source-bound allocator pass materializes 96 inferred timestamp windows from all 471 Wave1A candidate rows into `WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl`, `WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl`, and `WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl`; these rows are diagnostic only and do not claim original runtime allocator intent.
- This route still does not complete full SLTP modify lifecycle, original runtime allocator intent, sealed validation, production-return dossier, or Wave3 prompt-pack authority.
- Same-evidence-class continuation is required; the blocker ledger marks remaining gaps as open repairable pursuits or exact source-capture requirements, not final impossibility.
""",
    )
    write_md(
        "WAVE2_COMPLETION_AUDIT.md",
        """
# Wave2 Completion Audit - Initial Spine

Status: incomplete.

Completed in this checkpoint:

- Mandatory context and doctrine were read in-session before route materialization.
- Wave1A/B/C and Wave1 integration artifacts were inspected from disk and their route verifiers were run in-session.
- The initial full broker/candidate/live-authority row universe was materialized without a top-N cutoff.
- The active causal question stack, interaction graph, source inventory, input-inspection ledger, blocker ledger, and output manifest were created.
- All nine initial sidecar review findings were integrated into route-owned ledgers.
- Static-R/target geometry, broker-net cost, selector/scheduler opportunity-cost, market-vs-system, profit-harvest/path coverage, capture/replay/AI, production disposition, deployable-scope, LiveDecisionPacketV4, and validation contract artifacts were materialized as incomplete but source-bound Wave2 evidence.
- SLTP modify lifecycle, allocator decision-window, and path-repair source coverage audits were materialized to prove what current local sources can and cannot reconstruct without inferring historical runtime intent.
- An inferred allocator decision-window repair ledger was materialized from all Wave1A candidate decision timestamps as diagnostic-only reconstruction, not original runtime allocator truth.
- The inferred allocator repair now feeds three per-window opportunity-cost ledgers: 96 windows from 471 candidate rows, 55 observed filled candidates, 416 non-filled alternatives, 37 filled windows, 59 zero-fill windows, and 28 filled windows with same-timestamp alternatives. The ledgers preserve filled exact-R/broker cash separately from non-filled source-bound expectancy and mark every delta as diagnostic cross-evidence, not realized counterfactual truth.
- A tick-parquet path repair pass was materialized in `WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl` and `WAVE2_TICK_REPAIR_SOURCE_COVERAGE_AUDIT.json`: 55 filled rows emitted, 49 full tick-window repairs, 5 partial windows from missing 2026-06-01 tick files, 1 no-window row, all 29 loser rows fully tick-repaired, and 12 close timestamps repaired from broker truth minus the MT5 server-time offset.
- The tick pass also replaces prior placeholder/alias content in `WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl`, `WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl`, `WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl`, `WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl`, `WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl`, `WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl`, `WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl`, `WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl`, and `WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl`.
- Wave3 candidate lane contracts and the dependency graph now carry provenance fields while remaining blocked until Wave2 completion.
- Instruction-coverage status was recorded in `WAVE2_INSTRUCTION_COVERAGE_CHECKLIST.json`.
- `WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_LEDGER.jsonl` records exact-present, partial-present, and still-missing controlling-prompt outputs.

Not complete:

- Full SLTP modify lifecycle, original selected-versus-alternative allocator intent, sealed validation, production-return dossier, and Wave3 prompt pack are not complete.
- Tick-repaired path metrics are complete only for rows with full local tick windows; partial/no-window rows remain explicitly bounded source gaps in the path-family ledgers and verifier.
- Broker orders provide one initial SL/TP state for all 77 recent positions but do not provide multiple modify states; allocator sources provide opportunity/candidate/timestamp reconstruction but no durable decision_window_id, candidate_set_id, allocator output, open/pending snapshot, stale exposure opportunity cost, fill probability, or broker-net EV per unit risk.
- Exact historical allocator intent remains non-generatable from current local sources; inferred timestamp windows are diagnostic only.
- Current context files have not yet been updated to final Wave2 truth because Wave2 is not complete.
- No scoped completion commit has been created because the route is still active.
""",
    )

    manifest = build_manifest()
    write_json("WAVE2_OUTPUT_MANIFEST.json", manifest)

    result = {
        "ok": True,
        "generated_at_utc": GENERATED_AT,
        "route": rel(ROUTE_DIR),
        "completion_status": "initial_spine_materialized_not_complete",
        "headline": metrics["headline"],
        "output_files": len(manifest["files"]),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
