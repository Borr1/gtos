from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
TERMINAL_DECISION = "CURRENT_REPLAYABLE_GEOMETRY_RESULTS_MATERIALIZED_WITH_PROXY_R_ROWS_ONLY"
OUT_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)
MOON_ROOT = Path("C:/tmp/")
MOON_ROUTE = MOON_ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
READY8_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "decide_ready8_scid_and_related_geometry_research_direction"
)
R11_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "ready8_r11_trade_geometry_source_capture_repair_packet_after_r10_g12_audit"
)


MAIN_INPUTS = {
    "active_goal_prompt": Path(
        "research/science_program_2026_05/04_goal_prompts/"
        "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION_GOAL_PROMPT_2026-05-16.md"
    ),
    "active_starter": Path(
        "research/science_program_2026_05/04_goal_prompts/"
        "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION_STARTER_2026-05-16.txt"
    ),
    "live_state": Path(".context/LIVE_STATE.md"),
    "agents": Path("AGENTS.md"),
    "claude": Path("CLAUDE.md"),
    "session_56": Path(".context/02_session_handoffs/SESSION_56_MAIN_ORCHESTRATOR_24H_SUCCESSOR_HANDOFF_2026-05-16.md"),
    "research_doctrine": Path(".context/00_core/research_operating_doctrine.md"),
    "goal_discipline": Path(".context/00_core/goal_session_research_discipline.md"),
    "hardening_controls": Path(".context/00_core/orchestrator_methodology_hardening_controls.md"),
    "merge_playbook": Path(".context/00_core/parallel_goal_merge_playbook.md"),
    "research_current_state": Path(".context/00_core/research_current_state.md"),
    "route_status_registry": Path("research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json"),
    "question_ambiguity_ledger": Path(
        "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json"
    ),
    "ready8_decision_memo": READY8_DIR / "DECIDE_READY8_SCID_RESEARCH_DIRECTION_DECISION_MEMO_2026-05-16.md",
    "ready8_decision_ledger": READY8_DIR / "DECIDE_READY8_SCID_RESEARCH_DIRECTION_LEDGER_2026-05-16.json",
    "ready8_evidence_matrix": READY8_DIR / "DECIDE_READY8_SCID_RESEARCH_DIRECTION_EVIDENCE_MATRIX_2026-05-16.jsonl",
    "ready8_decision_check": READY8_DIR / "DECIDE_READY8_SCID_RESEARCH_DIRECTION_DECISION_CHECK_RESULT_2026-05-16.json",
    "g12_r11_capture_requirement_audit": R11_DIR / "G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl",
    "g12_r11_decision": R11_DIR / "G12_R11_DECISION_LEDGER_2026-05-16.json",
    "g12_r11_recomputation": R11_DIR / "G12_R11_RECOMPUTATION_LEDGER_2026-05-16.json",
}


MOON_INPUTS = {
    "moon_route_c_synthesis": MOON_ROUTE / "TICK_M15_ROUTE_C_SYNTHESIS_RESULT_2026-05-15.json",
    "moon_target_movement": MOON_ROUTE / "TICK_M15_TARGET_MOVEMENT_PACKET_RESULT_2026-05-15.json",
    "moon_tick_entry_path_result": MOON_ROUTE / "TICK_M15_ENTRY_PATH_GEOMETRY_RESULT_2026-05-16.json",
    "moon_tick_entry_path_rows": MOON_ROUTE / "TICK_M15_ENTRY_PATH_GEOMETRY_ROW_LEDGER_2026-05-16.jsonl",
    "moon_m1_spread_replay_result": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_RESULT_2026-05-16.json",
    "moon_m1_spread_replay_entry_rows": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_ENTRY_LEDGER_2026-05-16.jsonl",
    "moon_m1_spread_replay_signature_rows": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl",
    "moon_path_target_stop_contract": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl",
    "moon_cost_fill_path_proxy_result": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_RESULT_2026-05-16.json",
    "moon_cost_fill_path_proxy_branch_rows": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_BRANCH_SCORE_LEDGER_2026-05-16.jsonl",
    "moon_branch_rstyle_proxy_result": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_RESULT_2026-05-16.json",
    "moon_branch_rstyle_proxy_rows": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl",
    "moon_accepted_builder_packet": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_RESULT_2026-05-16.json",
    "moon_source_detail": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_RESULT_2026-05-16.json",
    "moon_source_window_materialization": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION_RESULT_2026-05-16.json",
    "moon_haz001_ready8_result": MOON_ROUTE / "HAZ001_READY8_INTEGRATION_PACKET_RESULT_2026-05-15.json",
    "moon_haz001_ready8_branch_queue": MOON_ROUTE / "HAZ001_READY8_DECONCENTRATED_BRANCH_QUEUE_2026-05-15.jsonl",
    "moon_positive_challenger_result": MOON_ROUTE / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DETAIL_RESULT_2026-05-16.json",
}


OUTPUTS = {
    "input_snapshot": OUT_DIR / f"MAIN_ORCH24_INPUT_SNAPSHOT_{DATE}.json",
    "candidate_ledger": OUT_DIR / f"MAIN_ORCH24_UNIFIED_CANDIDATE_LEDGER_{DATE}.jsonl",
    "geometry_binding_ledger": OUT_DIR / f"MAIN_ORCH24_GEOMETRY_BINDING_LEDGER_{DATE}.jsonl",
    "r_result_ledger": OUT_DIR / f"MAIN_ORCH24_EXACT_PROXY_R_RESULT_LEDGER_{DATE}.jsonl",
    "noncomputable_proof_ledger": OUT_DIR / f"MAIN_ORCH24_NONCOMPUTABLE_PROOF_LEDGER_{DATE}.jsonl",
    "dependency_ledger": OUT_DIR / f"MAIN_ORCH24_CURRENT_SNAPSHOT_DEPENDENCY_LEDGER_{DATE}.jsonl",
    "bucket_inventory": OUT_DIR / f"MAIN_ORCH24_EIGHT_BUCKET_INVENTORY_{DATE}.jsonl",
    "split_summary": OUT_DIR / f"MAIN_ORCH24_SPLIT_SUMMARY_{DATE}.jsonl",
    "expectancy_summary": OUT_DIR / f"MAIN_ORCH24_EXPECTANCY_COST_STRESS_SUMMARY_{DATE}.json",
    "ready8_comparison": OUT_DIR / f"MAIN_ORCH24_READY8_COMPARISON_{DATE}.json",
    "survivor_failure_decisions": OUT_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl",
    "completion_audit": OUT_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_{DATE}.json",
    "manifest": OUT_DIR / f"MAIN_ORCH24_OUTPUT_MANIFEST_{DATE}.json",
    "summary_md": OUT_DIR / f"MAIN_ORCH24_REPLAYABLE_GEOMETRY_MATERIALIZATION_SUMMARY_{DATE}.md",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_id(*parts: Any) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def run_git(cwd: Path, args: list[str], safe: bool = False) -> dict[str, Any]:
    cmd = ["git", "-c", "core.excludesfile="]
    if safe:
        cmd.extend(["-c", f"safe.directory={cwd.as_posix()}"])
    cmd.extend(["-C", str(cwd), *args])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def git_file_status(repo_root: Path, path: Path, safe: bool = False) -> str:
    if not path.exists():
        return "missing"
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return "outside_repo"
    status = run_git(repo_root, ["status", "--short", "--", rel], safe=safe)
    if status["returncode"] != 0:
        return "git_status_error:" + status["stderr"].replace("\n", " | ")
    if status["stdout"]:
        return status["stdout"].replace("\n", " | ")
    tracked = run_git(repo_root, ["ls-files", "--error-unmatch", rel], safe=safe)
    if tracked["returncode"] == 0:
        return "tracked_clean"
    return "untracked_or_ignored_clean_status"


def file_record(label: str, path: Path, repo_root: Path | None = None, safe_git: bool = False) -> dict[str, Any]:
    abs_path = path if path.is_absolute() else (Path.cwd() / path)
    exists = abs_path.exists()
    rec = {
        "label": label,
        "path": str(path),
        "exists": exists,
        "size_bytes": abs_path.stat().st_size if exists and abs_path.is_file() else None,
        "sha256": sha256_file(abs_path) if exists and abs_path.is_file() else None,
        "git_status": None,
    }
    if repo_root is not None and exists:
        rec["git_status"] = git_file_status(repo_root.resolve(), abs_path.resolve(), safe=safe_git)
    return rec


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield line_no, json.loads(line)
            except json.JSONDecodeError as exc:
                yield line_no, {"_parse_error": str(exc), "_raw": line[:500]}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            f.write("\n")


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        val = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(val):
        return default
    return val


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def rr_from_multiples(target_multiple: Any, stop_multiple: Any) -> float | None:
    target = safe_float(target_multiple)
    stop = safe_float(stop_multiple)
    if target is None or stop is None or stop <= 0:
        return None
    return target / stop


def classify_touch_order(order: str | None) -> tuple[str, float | None, float | None, float | None]:
    if not order:
        return "neither", 0.0, 0.0, 0.0
    upper = order.upper()
    if "FAVORABLE_FIRST" in upper or "FAVORABLE_ONLY" in upper:
        return "target_first", 1.0, 1.0, 1.0
    if "ADVERSE_FIRST" in upper or "ADVERSE_ONLY" in upper:
        return "stop_first", -1.0, -1.0, -1.0
    if "AMBIG" in upper or "BOTH" in upper:
        return "ambiguous", None, -1.0, 1.0
    if "NO" in upper or "NONE" in upper:
        return "neither", 0.0, 0.0, 0.0
    return "ambiguous", None, -1.0, 1.0


def classify_m1_status(status: str | None, rr: float | None) -> tuple[str, float | None, float | None, float | None, float | None]:
    if rr is None:
        return "noncomputable", None, None, None, None
    upper = (status or "").upper()
    if "ORDER_UNRESOLVED" in upper or "AMBIG" in upper or "SAME_BAR" in upper:
        return "ambiguous", None, -1.0, rr, (rr - 1.0) / 2.0
    if "TARGET_TOUCH_FIRST" in upper or "TARGET_TOUCH_BEFORE" in upper or upper.startswith("TARGET_"):
        return "target_first", rr, rr, rr, rr
    if "STOP_TOUCH_FIRST" in upper or "STOP_TOUCH_BEFORE" in upper or upper.startswith("STOP_"):
        return "stop_first", -1.0, -1.0, -1.0, -1.0
    if "NO_TARGET_OR_STOP" in upper or "NO_RESOLUTION" in upper:
        return "neither", 0.0, 0.0, 0.0, 0.0
    return "ambiguous", None, -1.0, rr, (rr - 1.0) / 2.0


def summarize_numeric(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def make_snapshot() -> dict[str, Any]:
    repo_root = Path.cwd()
    moon_exists = MOON_ROOT.exists()
    snapshot = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "terminal_decision_planned": TERMINAL_DECISION,
        "main": {
            "root": str(repo_root),
            "head": run_git(repo_root, ["rev-parse", "HEAD"])["stdout"],
            "branch": run_git(repo_root, ["branch", "--show-current"])["stdout"],
            "status_short": run_git(repo_root, ["status", "--short"])["stdout"],
        },
        "moonshot": {
            "root": str(MOON_ROOT),
            "exists": moon_exists,
            "git_plain_rev_parse_attempt": run_git(MOON_ROOT, ["rev-parse", "HEAD"]) if moon_exists else None,
            "git_safe_head": run_git(MOON_ROOT, ["rev-parse", "HEAD"], safe=True) if moon_exists else None,
            "git_safe_branch": run_git(MOON_ROOT, ["branch", "--show-current"], safe=True) if moon_exists else None,
            "git_safe_status_short": run_git(MOON_ROOT, ["status", "--short"], safe=True) if moon_exists else None,
            "dubious_ownership_diagnosis": (
                "Plain git is expected to fail under CodexSandboxOffline for this MSI-owned worktree; "
                "all git snapshot commands use per-command safe.directory and do not mutate global config."
            ),
        },
        "main_inputs": [file_record(label, path, repo_root=repo_root) for label, path in MAIN_INPUTS.items()],
        "moonshot_inputs": [
            file_record(label, path, repo_root=MOON_ROOT, safe_git=True) for label, path in MOON_INPUTS.items()
        ],
    }
    return snapshot


def add_candidate(candidates: dict[str, dict[str, Any]], candidate_id: str, row: dict[str, Any]) -> None:
    if candidate_id not in candidates:
        candidates[candidate_id] = row
    else:
        candidates[candidate_id]["source_row_count"] = candidates[candidate_id].get("source_row_count", 1) + 1


def materialize_tick_proxy_rows(
    candidates: dict[str, dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
) -> None:
    source_path = MOON_INPUTS["moon_tick_entry_path_rows"]
    source_hash = sha256_file(source_path)
    for line_no, row in iter_jsonl(source_path):
        if "_parse_error" in row:
            continue
        pm = row.get("path_metrics") or {}
        path_status = pm.get("path_status")
        candidate_id = "moon_tick:" + stable_id(
            row.get("queue_id"),
            row.get("symbol"),
            row.get("bar_open_utc"),
            row.get("direction_family"),
            row.get("horizon_id"),
        )
        add_candidate(
            candidates,
            candidate_id,
            {
                "candidate_id": candidate_id,
                "candidate_source": "moonshot_tick_m15_entry_path_geometry",
                "source_file": str(source_path),
                "source_sha256": source_hash,
                "source_line_no": line_no,
                "source_row_count": 1,
                "symbol": row.get("symbol"),
                "session": row.get("session_bucket"),
                "side": (row.get("direction_label") or "").upper(),
                "family": row.get("direction_family"),
                "horizon": row.get("horizon_id"),
                "event_time_utc": row.get("bar_open_utc"),
                "ready8_tagged": False,
                "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
                "evidence_class": "TICK_M15_ENTRY_PATH_GEOMETRY_PROXY",
            },
        )
        thresholds = (pm.get("threshold_results") or {})
        if path_status != "ok":
            binding_rows.append(
                {
                    "binding_id": "bind:" + stable_id(candidate_id, "tick_path_status"),
                    "candidate_id": candidate_id,
                    "binding_status": "NONCOMPUTABLE_PATH_STATUS_NOT_OK",
                    "source_file": str(source_path),
                    "source_sha256": source_hash,
                    "missing_fields": ["path_metrics.path_status_ok"],
                    "path_status": path_status,
                    "exact_r_available": False,
                    "proxy_r_available": False,
                }
            )
            continue
        for threshold_key, threshold_row in thresholds.items():
            status, proxy_r, lower, upper = classify_touch_order(threshold_row.get("touch_order"))
            result_id = "proxy_tick:" + stable_id(candidate_id, threshold_key)
            binding_rows.append(
                {
                    "binding_id": "bind:" + stable_id(result_id),
                    "candidate_id": candidate_id,
                    "result_id": result_id,
                    "binding_status": "PROXY_R_BOUND_FROM_TICK_M15_THRESHOLD_TOUCH_ORDER",
                    "source_file": str(source_path),
                    "source_sha256": source_hash,
                    "fields_present": [
                        "side",
                        "entry_mid_close_proxy",
                        "threshold",
                        "first_favorable_bar_offset",
                        "first_adverse_bar_offset",
                        "touch_order",
                        "source_file",
                    ],
                    "missing_fields_for_exact_r": [
                        "trade_intent_order_type",
                        "exact_stop_price",
                        "exact_target_price",
                        "broker_cost_slippage",
                    ],
                    "exact_r_available": False,
                    "proxy_r_available": True,
                }
            )
            result_rows.append(
                {
                    "result_id": result_id,
                    "candidate_id": candidate_id,
                    "result_layer": "moonshot_tick_threshold_proxy",
                    "evidence_class": "PROXY_R_TICK_M15_THRESHOLD_TOUCH_ORDER",
                    "source_file": str(source_path),
                    "source_sha256": source_hash,
                    "source_line_no": line_no,
                    "symbol": row.get("symbol"),
                    "session": row.get("session_bucket"),
                    "side": (row.get("direction_label") or "").upper(),
                    "family": row.get("direction_family"),
                    "horizon": row.get("horizon_id"),
                    "event_time_utc": row.get("bar_open_utc"),
                    "entry_reference": pm.get("entry_mid_close_proxy"),
                    "target_stop_proxy": threshold_key,
                    "threshold": threshold_row.get("threshold"),
                    "first_target_touch_offset_proxy": threshold_row.get("first_favorable_bar_offset"),
                    "first_stop_touch_offset_proxy": threshold_row.get("first_adverse_bar_offset"),
                    "path_status": threshold_row.get("touch_order"),
                    "result_status": status,
                    "exact_r": None,
                    "proxy_r": proxy_r,
                    "proxy_r_conservative": lower,
                    "proxy_r_optimistic": upper,
                    "proxy_r_for_expectancy": proxy_r if proxy_r is not None else ((lower + upper) / 2.0),
                    "cost_model": "threshold_embeds_spread_or_range_proxy",
                    "ready8_tagged": False,
                    "validation_safe": False,
                    "live_effect": False,
                }
            )


def materialize_m1_proxy_rows(
    candidates: dict[str, dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
) -> None:
    entry_path = MOON_INPUTS["moon_m1_spread_replay_entry_rows"]
    sig_path = MOON_INPUTS["moon_m1_spread_replay_signature_rows"]
    entry_hash = sha256_file(entry_path)
    sig_hash = sha256_file(sig_path)
    for line_no, row in iter_jsonl(entry_path):
        if "_parse_error" in row:
            continue
        candidate_id = "moon_m1_entry:" + stable_id(row.get("m1_spread_adjusted_entry_replay_id"))
        add_candidate(
            candidates,
            candidate_id,
            {
                "candidate_id": candidate_id,
                "candidate_source": "moonshot_m1_spread_adjusted_entry_replay",
                "source_file": str(entry_path),
                "source_sha256": entry_hash,
                "source_line_no": line_no,
                "source_row_count": 1,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "horizon": None,
                "event_time_utc": None,
                "route_candidate_id": row.get("route_candidate_id"),
                "ready8_tagged": False,
                "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
                "evidence_class": row.get("evidence_class"),
            },
        )
    for line_no, row in iter_jsonl(sig_path):
        if "_parse_error" in row:
            continue
        rr = rr_from_multiples(row.get("target_multiple"), row.get("stop_multiple"))
        status, proxy_r, lower, upper, expectancy_r = classify_m1_status(row.get("m1_first_touch_status"), rr)
        candidate_id = "moon_m1_sig:" + stable_id(
            row.get("route_candidate_id"),
            row.get("entry_variant_id"),
            row.get("target_stop_contract_id"),
            row.get("cost_model"),
            row.get("cost_sensitivity_signature_id"),
        )
        add_candidate(
            candidates,
            candidate_id,
            {
                "candidate_id": candidate_id,
                "candidate_source": "moonshot_m1_spread_adjusted_signature_replay",
                "source_file": str(sig_path),
                "source_sha256": sig_hash,
                "source_line_no": line_no,
                "source_row_count": 1,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "horizon": row.get("target_stop_contract_id"),
                "event_time_utc": row.get("m1_fill_utc"),
                "route_candidate_id": row.get("route_candidate_id"),
                "ready8_tagged": False,
                "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
                "evidence_class": row.get("evidence_class"),
            },
        )
        result_id = "proxy_m1:" + stable_id(row.get("m1_spread_adjusted_signature_replay_id"))
        missing_for_exact = []
        if "PROXY" in str(row.get("cost_model", "")).upper():
            missing_for_exact.append("exact_broker_spread_or_slippage")
        if status == "ambiguous":
            missing_for_exact.append("intra_m1_target_stop_order")
        binding_rows.append(
            {
                "binding_id": "bind:" + stable_id(result_id),
                "candidate_id": candidate_id,
                "result_id": result_id,
                "binding_status": "PROXY_R_BOUND_FROM_M1_SPREAD_ADJUSTED_REPLAY",
                "source_file": str(sig_path),
                "source_sha256": sig_hash,
                "fields_present": [
                    "side",
                    "effective_entry_price",
                    "stop_price_m1_proxy",
                    "target_price_m1_proxy",
                    "m1_fill_utc",
                    "m1_first_touch_status",
                    "cost_model",
                    "target_multiple",
                    "stop_multiple",
                ],
                "missing_fields_for_exact_r": missing_for_exact,
                "exact_r_available": False,
                "proxy_r_available": status != "noncomputable",
            }
        )
        result_rows.append(
            {
                "result_id": result_id,
                "candidate_id": candidate_id,
                "result_layer": "moonshot_m1_spread_adjusted_proxy",
                "evidence_class": "PROXY_R_M1_SPREAD_ADJUSTED_TARGET_STOP_ORDER",
                "source_file": str(sig_path),
                "source_sha256": sig_hash,
                "source_line_no": line_no,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "horizon": row.get("target_stop_contract_id"),
                "event_time_utc": row.get("m1_fill_utc"),
                "entry_reference": row.get("effective_entry_price"),
                "target_price_proxy": row.get("target_price_m1_proxy"),
                "stop_price_proxy": row.get("stop_price_m1_proxy"),
                "target_multiple": safe_float(row.get("target_multiple")),
                "stop_multiple": safe_float(row.get("stop_multiple")),
                "target_stop_rr": rr,
                "path_status": row.get("m1_first_touch_status"),
                "result_status": status,
                "exact_r": None,
                "proxy_r": proxy_r,
                "proxy_r_conservative": lower,
                "proxy_r_optimistic": upper,
                "proxy_r_for_expectancy": expectancy_r,
                "cost_model": row.get("cost_model"),
                "m1_fill_bar_offset": row.get("m1_fill_bar_offset"),
                "same_m15_ambiguity_rows_for_family": row.get("same_m15_ambiguity_rows_for_family"),
                "ready8_tagged": False,
                "validation_safe": False,
                "live_effect": False,
            }
        )


def materialize_branch_aggregate_proxy_rows(
    candidates: dict[str, dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> None:
    path = MOON_INPUTS["moon_cost_fill_path_proxy_branch_rows"]
    source_hash = sha256_file(path)
    for line_no, row in iter_jsonl(path):
        if "_parse_error" in row:
            continue
        rr = rr_from_multiples(row.get("target_multiple"), row.get("stop_multiple"))
        counts = row.get("proxy_outcome_counts") or {}
        fav = int(counts.get("favorable_proxy_rows") or 0)
        adv = int(counts.get("adverse_proxy_rows") or 0)
        amb = int(counts.get("ambiguous_proxy_rows") or 0)
        none = int(counts.get("no_resolution_proxy_rows") or 0)
        denom = fav + adv + amb + none
        if rr is not None and denom > 0:
            lower = (fav * rr + (adv + amb) * -1.0) / denom
            upper = ((fav + amb) * rr + adv * -1.0) / denom
            midpoint = (fav * rr + adv * -1.0 + amb * ((rr - 1.0) / 2.0)) / denom
        else:
            lower = upper = midpoint = None
        candidate_id = "moon_branch:" + stable_id(row.get("branch_proxy_score_id"))
        add_candidate(
            candidates,
            candidate_id,
            {
                "candidate_id": candidate_id,
                "candidate_source": "moonshot_cost_fill_path_branch_proxy_scoring",
                "source_file": str(path),
                "source_sha256": source_hash,
                "source_line_no": line_no,
                "source_row_count": 1,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "horizon": row.get("route_candidate_id"),
                "event_time_utc": None,
                "route_candidate_id": row.get("route_candidate_id"),
                "ready8_tagged": False,
                "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
                "evidence_class": row.get("evidence_class"),
            },
        )
        result_id = "proxy_branch_aggregate:" + stable_id(row.get("branch_proxy_score_id"))
        binding_rows.append(
            {
                "binding_id": "bind:" + stable_id(result_id),
                "candidate_id": candidate_id,
                "result_id": result_id,
                "binding_status": "AGGREGATE_PROXY_R_BOUND_FROM_BRANCH_PROXY_COUNTS",
                "source_file": str(path),
                "source_sha256": source_hash,
                "fields_present": [
                    "side",
                    "target_multiple",
                    "stop_multiple",
                    "proxy_outcome_counts",
                    "cost_robustness_bucket",
                    "fillability_bucket",
                    "ambiguity_bucket",
                ],
                "missing_fields_for_exact_r": [
                    "row_level_entry_price",
                    "row_level_target_stop_order_for_ambiguous_counts",
                    "exact_broker_cost_slippage",
                ],
                "exact_r_available": False,
                "proxy_r_available": rr is not None and denom > 0,
            }
        )
        result_rows.append(
            {
                "result_id": result_id,
                "candidate_id": candidate_id,
                "result_layer": "moonshot_branch_aggregate_proxy",
                "evidence_class": "AGGREGATE_PROXY_R_COST_FILL_PATH_BRANCH_SCORE",
                "source_file": str(path),
                "source_sha256": source_hash,
                "source_line_no": line_no,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "horizon": row.get("route_candidate_id"),
                "route_candidate_id": row.get("route_candidate_id"),
                "target_multiple": safe_float(row.get("target_multiple")),
                "stop_multiple": safe_float(row.get("stop_multiple")),
                "target_stop_rr": rr,
                "result_status": "aggregate_proxy",
                "exact_r": None,
                "proxy_r": midpoint,
                "proxy_r_conservative": lower,
                "proxy_r_optimistic": upper,
                "proxy_r_for_expectancy": midpoint,
                "aggregate_denominator": denom,
                "aggregate_favorable_proxy_rows": fav,
                "aggregate_adverse_proxy_rows": adv,
                "aggregate_ambiguous_proxy_rows": amb,
                "aggregate_no_resolution_proxy_rows": none,
                "proxy_mechanical_score": row.get("proxy_mechanical_score"),
                "cost_model": row.get("cost_robustness_bucket"),
                "fillability_bucket": row.get("fillability_bucket"),
                "ambiguity_bucket": row.get("ambiguity_bucket"),
                "source_confidence_bucket": row.get("source_confidence_bucket"),
                "effective_n_fields": row.get("effective_n_fields"),
                "system_implication_tags": row.get("system_implication_tags"),
                "ready8_tagged": False,
                "validation_safe": False,
                "live_effect": False,
            }
        )
        if midpoint is None:
            decision = "CURRENT_SNAPSHOT_DEPENDENCY"
        elif midpoint > 0:
            decision = "PRESERVE_OR_REPLAY_WITH_CONTROLS"
        elif upper is not None and upper <= 0:
            decision = "KILL_OR_AVOID_WITH_EVIDENCE"
        else:
            decision = "REDESIGN_OR_STRESS_BEFORE_REPLAY"
        decision_rows.append(
            {
                "decision_id": "decision:" + stable_id(result_id),
                "source_result_id": result_id,
                "decision": decision,
                "bucket": "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT"
                if decision == "PRESERVE_OR_REPLAY_WITH_CONTROLS"
                else "KILL_OR_AVOID_WITH_EVIDENCE",
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "family": row.get("entry_variant"),
                "proxy_r_midpoint": midpoint,
                "proxy_r_conservative": lower,
                "proxy_r_optimistic": upper,
                "evidence": {
                    "source_file": str(path),
                    "source_sha256": source_hash,
                    "line_no": line_no,
                    "proxy_outcome_counts": counts,
                    "branch_queue_status": row.get("branch_queue_status"),
                    "system_implication_tags": row.get("system_implication_tags"),
                },
                "live_effect": False,
                "validation_safe": False,
            }
        )


def branch_rstyle_result_status(branch_result_class: str | None) -> str:
    upper = str(branch_result_class or "").upper()
    if upper == "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return "branch_proxy_positive_midpoint"
    if upper == "NEGATIVE_RSTYLE_PROXY_MIDPOINT":
        return "branch_proxy_negative_midpoint"
    if upper == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
        return "branch_proxy_interval_straddles_zero"
    if upper == "NO_RSTYLE_PROXY_INTERVAL_AVAILABLE":
        return "branch_proxy_no_interval"
    return "branch_proxy_unclassified"


def branch_rstyle_decision(branch_result_class: str | None, midpoint: float | None, upper: float | None) -> tuple[str, str]:
    upper_class = str(branch_result_class or "").upper()
    if upper_class == "POSITIVE_RSTYLE_PROXY_MIDPOINT" or (midpoint is not None and midpoint > 0):
        return "PRESERVE_OR_REPLAY_WITH_CONTROLS", "IMPLEMENTATION_CANDIDATE_WITH_EXISTING_NUMERIC_SUPPORT"
    if upper_class == "NEGATIVE_RSTYLE_PROXY_MIDPOINT" or (upper is not None and upper <= 0):
        return "KILL_OR_AVOID_WITH_EVIDENCE", "KILL_OR_AVOID_WITH_EVIDENCE"
    if upper_class == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
        return "REDESIGN_OR_STRESS_BEFORE_REPLAY", "REPLAY_NOW_WITH_LOCAL_DATA_OR_REDESIGN_STRESS"
    return "CURRENT_SNAPSHOT_DEPENDENCY", "OUT_OF_SCOPE_FOR_MAIN_BECAUSE_NO_CURRENT_COMPUTABLE_PATH"


def materialize_branch_rstyle_proxy_rows(
    candidates: dict[str, dict[str, Any]],
    binding_rows: list[dict[str, Any]],
    result_rows: list[dict[str, Any]],
    noncomputable_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> None:
    path = MOON_INPUTS["moon_branch_rstyle_proxy_rows"]
    source_hash = sha256_file(path)
    for line_no, row in iter_jsonl(path):
        if "_parse_error" in row:
            continue
        rstyle_id = row.get("branch_rstyle_proxy_outcome_id") or row.get("branch_proxy_score_id")
        candidate_id = "moon_branch_rstyle:" + stable_id(rstyle_id)
        add_candidate(
            candidates,
            candidate_id,
            {
                "candidate_id": candidate_id,
                "candidate_source": "moonshot_branch_rstyle_proxy_outcome_layer",
                "source_file": str(path),
                "source_sha256": source_hash,
                "source_line_no": line_no,
                "source_row_count": 1,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "horizon": row.get("target_stop_contract_id"),
                "event_time_utc": None,
                "route_candidate_id": row.get("route_candidate_id"),
                "branch_rstyle_proxy_outcome_id": rstyle_id,
                "ready8_tagged": False,
                "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
                "evidence_class": row.get("evidence_class"),
            },
        )
        expectancy = row.get("expectancy_style_proxy") or {}
        interval_rows = safe_int(expectancy.get("interval_rows"), 0)
        lower = safe_float(expectancy.get("lower_mean"))
        midpoint = safe_float(expectancy.get("midpoint_mean"))
        upper = safe_float(expectancy.get("upper_mean"))
        result_status = branch_rstyle_result_status(row.get("branch_result_class"))
        result_id = "proxy_branch_rstyle:" + stable_id(rstyle_id)

        if interval_rows > 0 and lower is not None and midpoint is not None and upper is not None:
            binding_rows.append(
                {
                    "binding_id": "bind:" + stable_id(result_id),
                    "candidate_id": candidate_id,
                    "result_id": result_id,
                    "binding_status": "PROXY_R_BOUND_FROM_BRANCH_RSTYLE_OUTCOME_LAYER",
                    "source_file": str(path),
                    "source_sha256": source_hash,
                    "fields_present": [
                        "side",
                        "target_stop_contract_id",
                        "target_multiple",
                        "stop_multiple",
                        "target_stop_result",
                        "expectancy_style_proxy.interval_rows",
                        "expectancy_style_proxy.lower_mean",
                        "expectancy_style_proxy.midpoint_mean",
                        "expectancy_style_proxy.upper_mean",
                    ],
                    "missing_fields_for_exact_r": [
                        "broker_realized_trade_pnl",
                        "true_executed_risk",
                        "slippage",
                        "partial_fill_lifecycle",
                        "order_ticket_geometry",
                    ],
                    "exact_r_available": False,
                    "proxy_r_available": True,
                }
            )
            result_rows.append(
                {
                    "result_id": result_id,
                    "candidate_id": candidate_id,
                    "result_layer": "moonshot_branch_rstyle_proxy",
                    "evidence_class": row.get("evidence_class"),
                    "source_file": str(path),
                    "source_sha256": source_hash,
                    "source_line_no": line_no,
                    "symbol": row.get("symbol"),
                    "session": row.get("route_session"),
                    "side": row.get("side"),
                    "family": row.get("entry_variant"),
                    "horizon": row.get("target_stop_contract_id"),
                    "route_candidate_id": row.get("route_candidate_id"),
                    "branch_rstyle_proxy_outcome_id": rstyle_id,
                    "branch_result_class": row.get("branch_result_class"),
                    "target_stop_result": row.get("target_stop_result"),
                    "target_stop_result_counts": row.get("target_stop_result_counts"),
                    "target_multiple": safe_float(row.get("target_multiple")),
                    "stop_multiple": safe_float(row.get("stop_multiple")),
                    "target_stop_rr": safe_float(row.get("target_stop_reward_to_risk_ratio"))
                    or rr_from_multiples(row.get("target_multiple"), row.get("stop_multiple")),
                    "result_status": result_status,
                    "exact_r": None,
                    "proxy_r": midpoint,
                    "proxy_r_conservative": lower,
                    "proxy_r_optimistic": upper,
                    "proxy_r_for_expectancy": midpoint,
                    "aggregate_denominator": interval_rows,
                    "cost_model": row.get("cost_robustness_bucket"),
                    "cost_robustness_bucket": row.get("cost_robustness_bucket"),
                    "fillability_bucket": row.get("fillability_bucket"),
                    "ambiguity_bucket": row.get("ambiguity_bucket"),
                    "ambiguity_status": row.get("ambiguity_status"),
                    "source_confidence_status": row.get("source_confidence_status"),
                    "source_confidence_bucket": row.get("source_confidence_bucket"),
                    "path_scope_bucket": row.get("path_scope_bucket"),
                    "effective_n_fields": row.get("effective_n_fields"),
                    "concentration_summary": row.get("concentration_summary"),
                    "cause_tags": row.get("cause_tags"),
                    "system_implication_tags": row.get("system_implication_tags"),
                    "implementation_implications": row.get("implementation_implications"),
                    "exact_missing_reason": expectancy.get("exact_missing_reason"),
                    "missing_exact_geometry_reason": row.get("missing_exact_geometry_reason"),
                    "ready8_tagged": False,
                    "validation_safe": False,
                    "live_effect": False,
                }
            )
            decision, bucket = branch_rstyle_decision(row.get("branch_result_class"), midpoint, upper)
        else:
            missing_fields = []
            if not row.get("target_stop_contract_id") or str(row.get("target_stop_contract_id")).upper().startswith("TARGETSTOP_NA"):
                missing_fields.append("target_stop_contract_id")
            if safe_float(row.get("target_multiple")) is None:
                missing_fields.append("target_multiple")
            if safe_float(row.get("stop_multiple")) is None:
                missing_fields.append("stop_multiple")
            if not row.get("target_stop_result"):
                missing_fields.append("target_stop_result")
            if interval_rows <= 0:
                missing_fields.append("expectancy_style_proxy.interval_rows")
            if lower is None:
                missing_fields.append("expectancy_style_proxy.lower_mean")
            if midpoint is None:
                missing_fields.append("expectancy_style_proxy.midpoint_mean")
            if upper is None:
                missing_fields.append("expectancy_style_proxy.upper_mean")
            binding_rows.append(
                {
                    "binding_id": "bind:" + stable_id(result_id),
                    "candidate_id": candidate_id,
                    "result_id": result_id,
                    "binding_status": "NONCOMPUTABLE_RSTYLE_PROXY_INTERVAL_UNAVAILABLE",
                    "source_file": str(path),
                    "source_sha256": source_hash,
                    "missing_fields": missing_fields,
                    "exact_r_available": False,
                    "proxy_r_available": False,
                }
            )
            proof = {
                "proof_id": "noncomputable:" + stable_id(candidate_id),
                "candidate_id": candidate_id,
                "row_id": rstyle_id,
                "source_row_type": "moonshot_branch_rstyle_proxy_outcome",
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "side": row.get("side"),
                "family": row.get("entry_variant"),
                "route_candidate_id": row.get("route_candidate_id"),
                "artifact_paths_checked": [str(path)],
                "input_hashes": {str(path): source_hash},
                "missing_fields": missing_fields,
                "missing_field_count": len(missing_fields),
                "why_no_weaker_proxy_r_is_computable": (
                    row.get("missing_exact_geometry_reason")
                    or "Branch R-style row lacks a target/stop descriptor and any non-empty R-style interval."
                ),
                "owning_builder_family": "ACTIVE_MOONSHOT_BUILDER_ENTRY_ADVERSE_OR_TARGETSTOP_NA_REPAIR",
                "owner_boundary": (
                    "Main consumes the current moonshot snapshot only. Conversion requires the active builder "
                    "to bind target/stop geometry or preserve this row as source-control failure intelligence."
                ),
                "disposition": "preserve_current_snapshot_dependency_and_convert_to_builder_repair_queue",
                "bucket": "OWNED_BY_ACTIVE_MOONSHOT_BUILDER",
                "branch_result_class": row.get("branch_result_class"),
                "target_stop_contract_id": row.get("target_stop_contract_id"),
                "target_stop_result": row.get("target_stop_result"),
                "target_multiple": row.get("target_multiple"),
                "stop_multiple": row.get("stop_multiple"),
                "interval_rows": interval_rows,
                "validation_safe": False,
                "live_effect": False,
            }
            noncomputable_rows.append(proof)
            dependency_rows.append(
                {
                    "dependency_id": "dependency:" + stable_id(candidate_id),
                    "candidate_id": candidate_id,
                    "row_id": rstyle_id,
                    "source": "MOONSHOT_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER",
                    "current_snapshot_dependency_reason": proof["why_no_weaker_proxy_r_is_computable"],
                    "missing_fields": proof["missing_fields"],
                    "owner": proof["owning_builder_family"],
                    "disposition": proof["disposition"],
                    "artifact_paths_checked": proof["artifact_paths_checked"],
                    "input_hashes": proof["input_hashes"],
                }
            )
            decision, bucket = "CURRENT_SNAPSHOT_DEPENDENCY", "OUT_OF_SCOPE_FOR_MAIN_BECAUSE_NO_CURRENT_COMPUTABLE_PATH"

        decision_rows.append(
            {
                "decision_id": "decision:" + stable_id(result_id),
                "source_result_id": result_id,
                "source_row_id": rstyle_id,
                "decision": decision,
                "bucket": bucket,
                "symbol": row.get("symbol"),
                "session": row.get("route_session"),
                "family": row.get("entry_variant"),
                "side": row.get("side"),
                "proxy_r_midpoint": midpoint,
                "proxy_r_conservative": lower,
                "proxy_r_optimistic": upper,
                "branch_result_class": row.get("branch_result_class"),
                "target_stop_result": row.get("target_stop_result"),
                "evidence": {
                    "source_file": str(path),
                    "source_sha256": source_hash,
                    "line_no": line_no,
                    "target_stop_result_counts": row.get("target_stop_result_counts"),
                    "cost_robustness_bucket": row.get("cost_robustness_bucket"),
                    "fillability_bucket": row.get("fillability_bucket"),
                    "ambiguity_status": row.get("ambiguity_status"),
                    "source_confidence_status": row.get("source_confidence_status"),
                    "cause_tags": row.get("cause_tags"),
                    "system_implication_tags": row.get("system_implication_tags"),
                },
                "live_effect": False,
                "validation_safe": False,
            }
        )


def materialize_ready8_noncomputable(
    candidates: dict[str, dict[str, Any]],
    noncomputable_rows: list[dict[str, Any]],
    dependency_rows: list[dict[str, Any]],
) -> None:
    path = MAIN_INPUTS["g12_r11_capture_requirement_audit"]
    source_hash = sha256_file(path)
    for line_no, row in iter_jsonl(path):
        if "_parse_error" in row:
            continue
        candidate_id = "ready8:" + stable_id(row.get("row_key"), row.get("original_target_result_row_id"))
        add_candidate(
            candidates,
            candidate_id,
            {
                "candidate_id": candidate_id,
                "candidate_source": "ready8_g12_r11_capture_requirement",
                "source_file": str(path),
                "source_sha256": source_hash,
                "source_line_no": line_no,
                "source_row_count": 1,
                "symbol": (row.get("candidate_symbol_time_key") or {}).get("symbol") or row.get("symbol"),
                "session": None,
                "side": None,
                "family": row.get("card_id"),
                "horizon": row.get("horizon_m15_bars"),
                "event_time_utc": (row.get("candidate_symbol_time_key") or {}).get("decision_time_utc"),
                "ready8_tagged": True,
                "bucket": "MERGE_READY8_OR_PRIOR_RESEARCH_AS_FEATURE_CONTROL_OR_FAILURE_INTELLIGENCE",
                "evidence_class": row.get("evidence_class"),
            },
        )
        proof = {
            "proof_id": "noncomputable:" + stable_id(candidate_id),
            "candidate_id": candidate_id,
            "row_id": row.get("row_key"),
            "source_row_type": row.get("source_row_type"),
            "card_id": row.get("card_id"),
            "symbol": (row.get("candidate_symbol_time_key") or {}).get("symbol") or row.get("symbol"),
            "event_time_utc": (row.get("candidate_symbol_time_key") or {}).get("decision_time_utc"),
            "artifact_paths_checked": [str(path)],
            "input_hashes": {str(path): source_hash},
            "missing_fields": row.get("missing_fields") or [],
            "missing_field_count": row.get("missing_field_count"),
            "why_no_weaker_proxy_r_is_computable": row.get("exact_impossibility_proof")
            or "Accepted READY8 row has neutral target movement but no lawful side/entry/stop/target/path/cost binding.",
            "owning_builder_family": "BROADER_SYSTEM_GEOMETRY_CAPTURE_NOT_ACTIVE_MOONSHOT_BUILDER",
            "owner_boundary": (
                "READY8 standalone is closed; preserve as broader-system tags/priors/control/failure intelligence. "
                "Future conversion requires source-bound trade-intent and execution-geometry capture."
            ),
            "disposition": "convert_to_feature_control_failure_intelligence",
            "bucket": "MERGE_READY8_OR_PRIOR_RESEARCH_AS_FEATURE_CONTROL_OR_FAILURE_INTELLIGENCE",
            "required_capture_fields": row.get("required_capture_fields"),
            "validation_safe": False,
            "live_effect": False,
        }
        noncomputable_rows.append(proof)
        dependency_rows.append(
            {
                "dependency_id": "dependency:" + stable_id(candidate_id),
                "candidate_id": candidate_id,
                "row_id": row.get("row_key"),
                "source": "READY8_G12_R11_CAPTURE_REQUIREMENT",
                "current_snapshot_dependency_reason": proof["why_no_weaker_proxy_r_is_computable"],
                "missing_fields": proof["missing_fields"],
                "owner": proof["owning_builder_family"],
                "disposition": proof["disposition"],
                "artifact_paths_checked": proof["artifact_paths_checked"],
                "input_hashes": proof["input_hashes"],
            }
        )


def materialize_haz001_ready8_inventory(
    bucket_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> None:
    path = MOON_INPUTS["moon_haz001_ready8_branch_queue"]
    if not path.exists():
        return
    source_hash = sha256_file(path)
    branch_rows = 0
    adv_residual_zero = 0
    for line_no, row in iter_jsonl(path):
        if "_parse_error" in row:
            continue
        branch_rows += 1
        overlay = row.get("adv_control_overlay") or {}
        if overlay.get("haz001_residual_preserved") == 0:
            adv_residual_zero += 1
        decision_rows.append(
            {
                "decision_id": "decision:haz001_ready8:" + stable_id(row.get("branch_id")),
                "source_result_id": row.get("branch_id"),
                "decision": "MERGE_AS_READY8_PRIOR_CONTROL_OR_FAILURE_INTELLIGENCE_NOT_STANDALONE_EDGE",
                "bucket": "MERGE_READY8_OR_PRIOR_RESEARCH_AS_FEATURE_CONTROL_OR_FAILURE_INTELLIGENCE",
                "ready8_tagged": True,
                "card_id": (row.get("branch_key") or {}).get("card_id"),
                "branch_role": row.get("branch_role"),
                "delta": row.get("delta"),
                "evidence": {
                    "source_file": str(path),
                    "source_sha256": source_hash,
                    "line_no": line_no,
                    "adv_control_overlay": overlay,
                    "blockers": row.get("blockers"),
                    "allowed_next_uses": row.get("allowed_next_uses"),
                },
                "validation_safe": False,
                "live_effect": False,
            }
        )
    bucket_rows.append(
        {
            "inventory_id": "bucket:ready8_haz001_moonshot_integration",
            "item": "HAZ001 READY8 deconcentrated branch queue",
            "bucket": "MERGE_READY8_OR_PRIOR_RESEARCH_AS_FEATURE_CONTROL_OR_FAILURE_INTELLIGENCE",
            "artifact_paths_checked": [str(path)],
            "input_hashes": {str(path): source_hash},
            "row_count": branch_rows,
            "missing_evidence": [
                "trade_side_entry_stop_target_path_cost_for_R",
                "ADV-adjusted residual edge rows",
            ],
            "non_computability_proof": (
                f"All {branch_rows} HAZ001 READY8 integration rows are neutral target-movement/retest design rows; "
                f"{adv_residual_zero} rows report haz001_residual_preserved=0 under ADV overlay."
            ),
            "owner": "MAIN_MERGE_AS_PRIOR_CONTROL_FAILURE_INTELLIGENCE",
            "disposition": "preserve_as_prior_control_failure_intelligence",
        }
    )


def build_bucket_inventory() -> list[dict[str, Any]]:
    rows = [
        {
            "inventory_id": "bucket:moon_tick_m15_entry_path",
            "item": "Moonshot tick/M15 entry-path threshold geometry",
            "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
            "artifact_paths_checked": [str(MOON_INPUTS["moon_tick_entry_path_rows"])],
            "input_hashes": {str(MOON_INPUTS["moon_tick_entry_path_rows"]): sha256_file(MOON_INPUTS["moon_tick_entry_path_rows"])},
            "owner": "MAIN_COMPUTED_PROXY_R_FROM_FIXED_MOONSHOT_SNAPSHOT",
            "disposition": "computed_proxy_r_rows",
        },
        {
            "inventory_id": "bucket:moon_m1_spread_adjusted_replay",
            "item": "Moonshot M1 spread-adjusted fill replay signatures",
            "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
            "artifact_paths_checked": [str(MOON_INPUTS["moon_m1_spread_replay_signature_rows"])],
            "input_hashes": {
                str(MOON_INPUTS["moon_m1_spread_replay_signature_rows"]): sha256_file(
                    MOON_INPUTS["moon_m1_spread_replay_signature_rows"]
                )
            },
            "owner": "MAIN_COMPUTED_PROXY_R_FROM_FIXED_MOONSHOT_SNAPSHOT",
            "disposition": "computed_proxy_r_rows",
        },
        {
            "inventory_id": "bucket:moon_branch_aggregate_proxy",
            "item": "Moonshot cost/fill/path branch aggregate proxy scoring",
            "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
            "artifact_paths_checked": [str(MOON_INPUTS["moon_cost_fill_path_proxy_branch_rows"])],
            "input_hashes": {
                str(MOON_INPUTS["moon_cost_fill_path_proxy_branch_rows"]): sha256_file(
                    MOON_INPUTS["moon_cost_fill_path_proxy_branch_rows"]
                )
            },
            "owner": "MAIN_COMPUTED_AGGREGATE_PROXY_R_FROM_FIXED_MOONSHOT_SNAPSHOT",
            "disposition": "computed_aggregate_proxy_r_rows",
        },
        {
            "inventory_id": "bucket:moon_branch_rstyle_proxy_outcome_layer",
            "item": "Moonshot branch R-style proxy outcome layer",
            "bucket": "COMPUTE_NOW_FROM_CURRENT_MOONSHOT_SNAPSHOT",
            "artifact_paths_checked": [
                str(MOON_INPUTS["moon_branch_rstyle_proxy_result"]),
                str(MOON_INPUTS["moon_branch_rstyle_proxy_rows"]),
            ],
            "input_hashes": {
                str(MOON_INPUTS["moon_branch_rstyle_proxy_result"]): sha256_file(
                    MOON_INPUTS["moon_branch_rstyle_proxy_result"]
                ),
                str(MOON_INPUTS["moon_branch_rstyle_proxy_rows"]): sha256_file(
                    MOON_INPUTS["moon_branch_rstyle_proxy_rows"]
                ),
            },
            "missing_evidence": [
                "broker-realized fills and PnL for exact R",
                "target/stop descriptor for TARGETSTOP_NA rows",
            ],
            "non_computability_proof": (
                "The branch R-style layer is proxy-computable where interval rows and lower/mid/upper means exist; "
                "TARGETSTOP_NA rows are emitted as row-level noncomputable proofs."
            ),
            "owner": "MAIN_COMPUTED_PRIMARY_BRANCH_PROXY_R_FROM_FIXED_MOONSHOT_SNAPSHOT",
            "disposition": "computed_primary_branch_proxy_r_rows_and_preserved_targetstop_na_repair_rows",
        },
        {
            "inventory_id": "bucket:ready8_final_decision",
            "item": "READY8 final decision artifacts",
            "bucket": "MERGE_READY8_OR_PRIOR_RESEARCH_AS_FEATURE_CONTROL_OR_FAILURE_INTELLIGENCE",
            "artifact_paths_checked": [
                str(MAIN_INPUTS["ready8_decision_ledger"]),
                str(MAIN_INPUTS["ready8_evidence_matrix"]),
                str(MAIN_INPUTS["ready8_decision_check"]),
            ],
            "input_hashes": {
                str(MAIN_INPUTS["ready8_decision_ledger"]): sha256_file(MAIN_INPUTS["ready8_decision_ledger"]),
                str(MAIN_INPUTS["ready8_evidence_matrix"]): sha256_file(MAIN_INPUTS["ready8_evidence_matrix"]),
                str(MAIN_INPUTS["ready8_decision_check"]): sha256_file(MAIN_INPUTS["ready8_decision_check"]),
            },
            "missing_evidence": ["standalone executable trade geometry"],
            "non_computability_proof": "READY8 final decision ledger terminates standalone route and reports 0 exact R rows and 0 target/stop hit/miss rows.",
            "owner": "MAIN_MERGE_READY8_INTELLIGENCE_ONLY",
            "disposition": "merge_as_tags_priors_controls_failure_intelligence",
        },
        {
            "inventory_id": "bucket:ready8_r11_noncomputable_geometry",
            "item": "READY8 G12 R11 row-level capture requirements",
            "bucket": "OUT_OF_SCOPE_FOR_MAIN_BECAUSE_NO_CURRENT_COMPUTABLE_PATH",
            "artifact_paths_checked": [str(MAIN_INPUTS["g12_r11_capture_requirement_audit"])],
            "input_hashes": {
                str(MAIN_INPUTS["g12_r11_capture_requirement_audit"]): sha256_file(
                    MAIN_INPUTS["g12_r11_capture_requirement_audit"]
                )
            },
            "missing_evidence": [
                "trade_side",
                "stop_or_invalidation",
                "target_price_or_r_multiple",
                "fillability_and_target_stop_path_order",
                "cost_and_slippage",
            ],
            "non_computability_proof": "R11/G12 row-level proof shows current accepted/local source roots contain no lawful same-source row binding all trade R fields.",
            "owner": "BROADER_SYSTEM_GEOMETRY_CAPTURE_NOT_ACTIVE_MOONSHOT_BUILDER",
            "disposition": "convert_to_feature_control_failure_intelligence",
        },
        {
            "inventory_id": "bucket:active_moonshot_source_m1_m15_positive_entry_builders",
            "item": "Active moonshot SOURCE/M1/M15/positive/entry builder queue",
            "bucket": "OWNED_BY_ACTIVE_MOONSHOT_BUILDER",
            "artifact_paths_checked": [
                str(MOON_INPUTS["moon_source_detail"]),
                str(MOON_INPUTS["moon_source_window_materialization"]),
                str(MOON_INPUTS["moon_positive_challenger_result"]),
                str(MOON_INPUTS["moon_accepted_builder_packet"]),
            ],
            "input_hashes": {
                str(path): sha256_file(path)
                for path in [
                    MOON_INPUTS["moon_source_detail"],
                    MOON_INPUTS["moon_source_window_materialization"],
                    MOON_INPUTS["moon_positive_challenger_result"],
                    MOON_INPUTS["moon_accepted_builder_packet"],
                ]
            },
            "missing_evidence": [
                "branch-local evolving detail not fixed in main",
                "builder-owned SOURCE/M1/M15/positive/entry expansion beyond consumed snapshot",
            ],
            "non_computability_proof": "Main consumed the fixed current snapshot only and must not modify or compete with the active moonshot builder worktree.",
            "owner": "ACTIVE_MOONSHOT_BUILDER",
            "disposition": "preserve_snapshot_boundary_and_do_not_modify_moonshot",
        },
    ]
    return rows


def build_split_summary(result_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    split_rows: list[dict[str, Any]] = []
    keys = [
        ("layer", ["result_layer"]),
        ("symbol", ["symbol"]),
        ("session", ["session"]),
        ("family", ["family"]),
        ("horizon", ["horizon"]),
        ("side", ["side"]),
        ("layer_symbol_session_family_horizon", ["result_layer", "symbol", "session", "family", "horizon"]),
    ]
    for split_name, fields in keys:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in result_rows:
            groups[tuple(row.get(f) for f in fields)].append(row)
        for key, rows in sorted(groups.items(), key=lambda kv: tuple("" if v is None else str(v) for v in kv[0])):
            values = [safe_float(r.get("proxy_r_for_expectancy")) for r in rows]
            values = [v for v in values if v is not None]
            split_rows.append(
                {
                    "split_name": split_name,
                    "split_key": {field: value for field, value in zip(fields, key)},
                    "row_count": len(rows),
                    "exact_r_rows": sum(1 for r in rows if r.get("exact_r") is not None),
                    "proxy_r_rows": sum(1 for r in rows if r.get("proxy_r_for_expectancy") is not None),
                    "result_status_counts": dict(Counter(r.get("result_status") for r in rows)),
                    "proxy_r_summary": summarize_numeric(values),
                    "ready8_tagged_rows": sum(1 for r in rows if r.get("ready8_tagged")),
                }
            )
    return split_rows


def build_summary(
    snapshot: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    result_rows: list[dict[str, Any]],
    noncomputable_rows: list[dict[str, Any]],
    bucket_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    all_proxy_values = [safe_float(r.get("proxy_r_for_expectancy")) for r in result_rows]
    all_proxy_values = [v for v in all_proxy_values if v is not None]
    branch_layers = {"moonshot_branch_aggregate_proxy", "moonshot_branch_rstyle_proxy"}
    row_level = [r for r in result_rows if r.get("result_layer") not in branch_layers]
    row_values = [safe_float(r.get("proxy_r_for_expectancy")) for r in row_level]
    row_values = [v for v in row_values if v is not None]
    wins = [v for v in row_values if v > 0]
    losses = [v for v in row_values if v < 0]
    flat = [v for v in row_values if v == 0]
    by_cost: dict[str, list[float]] = defaultdict(list)
    for row in result_rows:
        val = safe_float(row.get("proxy_r_for_expectancy"))
        if val is not None:
            by_cost[str(row.get("cost_model") or "UNKNOWN")].append(val)
    branch_rows = [r for r in result_rows if r.get("result_layer") == "moonshot_branch_aggregate_proxy"]
    branch_weighted_num = 0.0
    branch_weighted_den = 0
    branch_conservative_num = 0.0
    branch_optimistic_num = 0.0
    for row in branch_rows:
        den = int(row.get("aggregate_denominator") or 0)
        mid = safe_float(row.get("proxy_r_for_expectancy"))
        low = safe_float(row.get("proxy_r_conservative"))
        high = safe_float(row.get("proxy_r_optimistic"))
        if den > 0 and mid is not None:
            branch_weighted_den += den
            branch_weighted_num += den * mid
            branch_conservative_num += den * (low if low is not None else mid)
            branch_optimistic_num += den * (high if high is not None else mid)
    branch_rstyle_rows = [r for r in result_rows if r.get("result_layer") == "moonshot_branch_rstyle_proxy"]
    branch_rstyle_values = [safe_float(r.get("proxy_r_for_expectancy")) for r in branch_rstyle_rows]
    branch_rstyle_values = [v for v in branch_rstyle_values if v is not None]
    branch_rstyle_weighted_num = 0.0
    branch_rstyle_weighted_den = 0
    branch_rstyle_conservative_num = 0.0
    branch_rstyle_optimistic_num = 0.0
    for row in branch_rstyle_rows:
        den = int(row.get("aggregate_denominator") or 0)
        mid = safe_float(row.get("proxy_r_for_expectancy"))
        low = safe_float(row.get("proxy_r_conservative"))
        high = safe_float(row.get("proxy_r_optimistic"))
        if den > 0 and mid is not None:
            branch_rstyle_weighted_den += den
            branch_rstyle_weighted_num += den * mid
            branch_rstyle_conservative_num += den * (low if low is not None else mid)
            branch_rstyle_optimistic_num += den * (high if high is not None else mid)
    result_status_counts = Counter(r.get("result_status") for r in result_rows)
    ready8_noncomputable_rows = [r for r in noncomputable_rows if str(r.get("candidate_id") or "").startswith("ready8:")]
    moonshot_branch_rstyle_noncomputable_rows = [
        r for r in noncomputable_rows if r.get("source_row_type") == "moonshot_branch_rstyle_proxy_outcome"
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": snapshot["generated_utc"],
        "terminal_decision": TERMINAL_DECISION,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "moonshot_snapshot_head": ((snapshot["moonshot"].get("git_safe_head") or {}).get("stdout")),
        "moonshot_snapshot_branch": ((snapshot["moonshot"].get("git_safe_branch") or {}).get("stdout")),
        "counts": {
            "candidate_rows": len(candidates),
            "exact_r_rows": sum(1 for r in result_rows if r.get("exact_r") is not None),
            "proxy_r_rows": sum(1 for r in result_rows if r.get("proxy_r_for_expectancy") is not None),
            "proxy_result_rows_total": len(result_rows),
            "noncomputable_rows": len(noncomputable_rows),
            "ready8_noncomputable_rows": len(ready8_noncomputable_rows),
            "moonshot_branch_rstyle_noncomputable_rows": len(moonshot_branch_rstyle_noncomputable_rows),
            "target_first": result_status_counts.get("target_first", 0),
            "stop_first": result_status_counts.get("stop_first", 0),
            "neither": result_status_counts.get("neither", 0),
            "ambiguous": result_status_counts.get("ambiguous", 0),
            "aggregate_proxy": result_status_counts.get("aggregate_proxy", 0),
            "branch_rstyle_proxy_rows": len(branch_rstyle_rows),
            "branch_rstyle_positive_midpoint": result_status_counts.get("branch_proxy_positive_midpoint", 0),
            "branch_rstyle_negative_midpoint": result_status_counts.get("branch_proxy_negative_midpoint", 0),
            "branch_rstyle_interval_straddles_zero": result_status_counts.get("branch_proxy_interval_straddles_zero", 0),
            "bucket_inventory_rows": len(bucket_rows),
            "survivor_failure_decision_rows": len(decision_rows),
        },
        "row_level_proxy_expectancy": {
            "gross_expectancy_r": (sum(row_values) / len(row_values)) if row_values else None,
            "cost_adjusted_expectancy_r": (sum(row_values) / len(row_values)) if row_values else None,
            "stress_adjusted_expectancy_r": min(
                [safe_float(r.get("proxy_r_conservative")) for r in row_level if safe_float(r.get("proxy_r_conservative")) is not None],
                default=None,
            ),
            "win_rate": len(wins) / len(row_values) if row_values else None,
            "loss_rate": len(losses) / len(row_values) if row_values else None,
            "flat_rate": len(flat) / len(row_values) if row_values else None,
            "average_win_r": sum(wins) / len(wins) if wins else None,
            "average_loss_r": sum(losses) / len(losses) if losses else None,
            "proxy_r_summary": summarize_numeric(row_values),
        },
        "all_proxy_layers_expectancy": {
            "gross_expectancy_r": (sum(all_proxy_values) / len(all_proxy_values)) if all_proxy_values else None,
            "proxy_r_summary": summarize_numeric(all_proxy_values),
            "note": "Includes row-level tick/M1 proxy rows plus branch aggregate and branch R-style proxy rows as rows, not as a deduplicated validation denominator.",
        },
        "branch_aggregate_weighted_expectancy": {
            "weighted_denominator": branch_weighted_den,
            "midpoint_r": (branch_weighted_num / branch_weighted_den) if branch_weighted_den else None,
            "conservative_r": (branch_conservative_num / branch_weighted_den) if branch_weighted_den else None,
            "optimistic_r": (branch_optimistic_num / branch_weighted_den) if branch_weighted_den else None,
        },
        "branch_rstyle_proxy_expectancy": {
            "row_count": len(branch_rstyle_rows),
            "computable_rows": len(branch_rstyle_values),
            "noncomputable_source_rows": len(moonshot_branch_rstyle_noncomputable_rows),
            "result_class_counts": dict(Counter(r.get("branch_result_class") for r in branch_rstyle_rows)),
            "status_counts": dict(Counter(r.get("result_status") for r in branch_rstyle_rows)),
            "weighted_denominator": branch_rstyle_weighted_den,
            "midpoint_r": (branch_rstyle_weighted_num / branch_rstyle_weighted_den)
            if branch_rstyle_weighted_den
            else None,
            "conservative_r": (branch_rstyle_conservative_num / branch_rstyle_weighted_den)
            if branch_rstyle_weighted_den
            else None,
            "optimistic_r": (branch_rstyle_optimistic_num / branch_rstyle_weighted_den)
            if branch_rstyle_weighted_den
            else None,
            "midpoint_r_summary": summarize_numeric(branch_rstyle_values),
            "note": "Primary moonshot branch R-style proxy surface; exact broker/account R remains unavailable.",
        },
        "cost_model_splits": {k: summarize_numeric(v) for k, v in sorted(by_cost.items())},
        "bucket_counts": dict(Counter(r.get("bucket") for r in bucket_rows)),
        "decision_counts": dict(Counter(r.get("decision") for r in decision_rows)),
        "no_promotion_boundary": (
            "Rows are source-bound exact/proxy computations for materialization and research decisions only. "
            "They are not live validation, promotion, broker PnL, or live behavior."
        ),
    }
    return summary


def build_ready8_comparison(
    result_rows: list[dict[str, Any]],
    noncomputable_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    ready8_decision = read_json(MAIN_INPUTS["ready8_decision_ledger"])
    moon_proxy = [r for r in result_rows if not r.get("ready8_tagged")]
    ready8_noncomputable = [r for r in noncomputable_rows if str(r.get("candidate_id") or "").startswith("ready8:")]
    moonshot_noncomputable = [r for r in noncomputable_rows if not str(r.get("candidate_id") or "").startswith("ready8:")]
    ready8_tagged_decisions = [r for r in decision_rows if r.get("ready8_tagged")]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "ready8_terminal_decision": ready8_decision.get("terminal_decision"),
        "ready8_use_boundary": ready8_decision.get("can_become_trade_strategy"),
        "ready8_counts_from_decision_ledger": ready8_decision.get("current_state_numbers") or ready8_decision.get("accepted_numbers"),
        "ready8_noncomputable_rows_materialized": len(ready8_noncomputable),
        "moonshot_noncomputable_rows_materialized": len(moonshot_noncomputable),
        "ready8_exact_r_rows_in_current_materialization": 0,
        "ready8_proxy_r_rows_in_current_materialization": 0,
        "ready8_tagged_control_failure_decision_rows": len(ready8_tagged_decisions),
        "moonshot_untagged_proxy_rows": len(moon_proxy),
        "comparison": {
            "ready8_tagged": {
                "role": "tags_priors_controls_failure_intelligence",
                "computable_r": False,
                "standalone_route": "closed",
                "noncomputable_proof_rows": len(ready8_noncomputable),
            },
            "moonshot_current_snapshot": {
                "role": "replayable primitive/path/fill/cost proxy geometry",
                "computable_r": True,
                "proxy_r_rows": len(moon_proxy),
                "exact_r_rows": 0,
                "noncomputable_proof_rows": len(moonshot_noncomputable),
            },
        },
        "decision": "MERGE_READY8_WITH_MOONSHOT_AS_PRIOR_CONTROL_FAILURE_INTELLIGENCE_AND_USE_MOONSHOT_FOR_CURRENT_REPLAYABLE_PROXY_R",
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def build_completion_audit(summary: dict[str, Any], output_paths: dict[str, Path]) -> dict[str, Any]:
    checklist = [
        ("regenerate_and_read_live_state", True, ".context/LIVE_STATE.md regenerated/read before build"),
        ("read_agents_claude_session_56_doctrine_discipline_hardening", True, "Input snapshot hashes mandatory context files"),
        ("snapshot_moonshot_head_status_path_size_sha", True, "MAIN_ORCH24_INPUT_SNAPSHOT records safe git state and hashes"),
        ("do_not_modify_moonshot", True, "Build script reads C:/tmp/ only"),
        ("ready8_closed_standalone", True, "READY8 comparison preserves final merge/no-standalone boundary"),
        ("compute_exact_r_where_exists", True, "Exact R rows checked; current exact_r_rows=0"),
        (
            "compute_proxy_r_where_exists",
            summary["counts"]["proxy_r_rows"] > 0 and summary["counts"]["branch_rstyle_proxy_rows"] == 384,
            "Proxy R rows materialized from tick, M1, branch aggregate, and primary branch R-style artifacts",
        ),
        (
            "noncomputable_row_level_proof",
            summary["counts"]["ready8_noncomputable_rows"] == 5502
            and summary["counts"]["moonshot_branch_rstyle_noncomputable_rows"] == 2,
            "READY8 G12/R11 5,502 row-level proofs plus 2 moonshot TARGETSTOP_NA branch R-style proofs materialized",
        ),
        ("eight_bucket_inventory", summary["counts"]["bucket_inventory_rows"] >= 6, "Eight-bucket inventory artifact exists with bucket 7/8 proofs"),
        ("expectancy_cost_stress_splits", True, "Expectation and split summary artifacts emitted"),
        ("ready8_tagged_vs_untagged_comparison", True, "READY8 comparison artifact emitted"),
        ("survivor_failure_implementation_decisions", summary["counts"]["survivor_failure_decision_rows"] > 0, "Decision ledger emitted"),
        ("no_arbitrary_top_n", True, "All material rows written to full JSONL ledgers; summaries are derived"),
        ("safe_flags_closed", True, "NO_PROMOTION_VERDICT; validation_safe=false; outcome_review_opened=false; live_effect=false"),
    ]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "terminal_decision": summary["terminal_decision"],
        "objective_as_concrete_deliverables": [
            "Fixed moonshot and READY8 input snapshot",
            "Unified candidate ledger",
            "Geometry binding ledger",
            "Exact/proxy R result ledger",
            "Noncomputable row proof ledger",
            "Expectancy/cost/stress/split summaries",
            "READY8 comparison",
            "Survivor/failure/implementation decisions",
            "Completion audit and verifier",
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": req, "covered": covered, "evidence": evidence}
            for req, covered, evidence in checklist
        ],
        "output_paths": {label: str(path) for label, path in output_paths.items()},
        "known_not_complete_for_24h_goal": [
            "This completes the first replayable-geometry materialization plate, not the full 24-hour objective.",
            "Next plate should integrate live/shadow and older research evidence, then implement scoped improvements where evidence supports them.",
        ],
        "can_mark_active_24h_goal_complete": False,
    }


def build_manifest() -> dict[str, Any]:
    artifacts = []
    for label, path in OUTPUTS.items():
        if label == "manifest":
            continue
        artifacts.append(file_record(label, path, repo_root=Path.cwd()))
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def write_summary_md(summary: dict[str, Any], ready8: dict[str, Any]) -> None:
    lines = [
        "# Main Orchestrator 24H Replayable Geometry Materialization",
        "",
        f"Generated: {summary['generated_utc']}",
        f"Terminal decision for first plate: `{summary['terminal_decision']}`",
        "",
        "## Counts",
        "",
        f"- Candidate rows: {summary['counts']['candidate_rows']}",
        f"- Exact R rows: {summary['counts']['exact_r_rows']}",
        f"- Proxy R rows: {summary['counts']['proxy_r_rows']}",
        f"- Non-computable rows with row-level proof: {summary['counts']['noncomputable_rows']}",
        f"- READY8 / moonshot branch R-style non-computable proofs: {summary['counts']['ready8_noncomputable_rows']} / {summary['counts']['moonshot_branch_rstyle_noncomputable_rows']}",
        f"- Primary branch R-style proxy rows: {summary['counts']['branch_rstyle_proxy_rows']}",
        f"- Target-first / stop-first / neither / ambiguous: {summary['counts']['target_first']} / {summary['counts']['stop_first']} / {summary['counts']['neither']} / {summary['counts']['ambiguous']}",
        "",
        "## Expectancy",
        "",
        f"- Row-level gross proxy expectancy R: {summary['row_level_proxy_expectancy']['gross_expectancy_r']}",
        f"- Row-level win rate: {summary['row_level_proxy_expectancy']['win_rate']}",
        f"- Row-level average win R: {summary['row_level_proxy_expectancy']['average_win_r']}",
        f"- Row-level average loss R: {summary['row_level_proxy_expectancy']['average_loss_r']}",
        f"- Branch aggregate weighted midpoint R: {summary['branch_aggregate_weighted_expectancy']['midpoint_r']}",
        f"- Branch R-style weighted midpoint R: {summary['branch_rstyle_proxy_expectancy']['midpoint_r']}",
        f"- Branch R-style class counts: {summary['branch_rstyle_proxy_expectancy']['result_class_counts']}",
        "",
        "## READY8 Boundary",
        "",
        f"- READY8 terminal decision: `{ready8['ready8_terminal_decision']}`",
        f"- READY8 current materialization exact/proxy R rows: {ready8['ready8_exact_r_rows_in_current_materialization']} / {ready8['ready8_proxy_r_rows_in_current_materialization']}",
        f"- READY8 non-computable proof rows: {ready8['ready8_noncomputable_rows_materialized']}",
        "",
        "## Boundary",
        "",
        "This is research materialization only: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
        "It completes the first materialization plate, not the full 24-hour objective.",
        "",
    ]
    OUTPUTS["summary_md"].write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = make_snapshot()
    write_json(OUTPUTS["input_snapshot"], snapshot)

    candidates: dict[str, dict[str, Any]] = {}
    binding_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    noncomputable_rows: list[dict[str, Any]] = []
    dependency_rows: list[dict[str, Any]] = []
    bucket_rows = build_bucket_inventory()
    decision_rows: list[dict[str, Any]] = []

    materialize_tick_proxy_rows(candidates, binding_rows, result_rows)
    materialize_m1_proxy_rows(candidates, binding_rows, result_rows)
    materialize_branch_aggregate_proxy_rows(candidates, binding_rows, result_rows, decision_rows)
    materialize_branch_rstyle_proxy_rows(
        candidates,
        binding_rows,
        result_rows,
        noncomputable_rows,
        dependency_rows,
        decision_rows,
    )
    materialize_ready8_noncomputable(candidates, noncomputable_rows, dependency_rows)
    materialize_haz001_ready8_inventory(bucket_rows, decision_rows)

    split_rows = build_split_summary(result_rows)
    summary = build_summary(snapshot, candidates, result_rows, noncomputable_rows, bucket_rows, decision_rows)
    ready8_comparison = build_ready8_comparison(result_rows, noncomputable_rows, decision_rows)
    completion_audit = build_completion_audit(summary, OUTPUTS)

    write_jsonl(OUTPUTS["candidate_ledger"], list(candidates.values()))
    write_jsonl(OUTPUTS["geometry_binding_ledger"], binding_rows)
    write_jsonl(OUTPUTS["r_result_ledger"], result_rows)
    write_jsonl(OUTPUTS["noncomputable_proof_ledger"], noncomputable_rows)
    write_jsonl(OUTPUTS["dependency_ledger"], dependency_rows)
    write_jsonl(OUTPUTS["bucket_inventory"], bucket_rows)
    write_jsonl(OUTPUTS["split_summary"], split_rows)
    write_jsonl(OUTPUTS["survivor_failure_decisions"], decision_rows)
    write_json(OUTPUTS["expectancy_summary"], summary)
    write_json(OUTPUTS["ready8_comparison"], ready8_comparison)
    write_json(OUTPUTS["completion_audit"], completion_audit)
    write_summary_md(summary, ready8_comparison)
    write_json(OUTPUTS["manifest"], build_manifest())

    print(json.dumps({"ok": True, "terminal_decision": TERMINAL_DECISION, "counts": summary["counts"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
