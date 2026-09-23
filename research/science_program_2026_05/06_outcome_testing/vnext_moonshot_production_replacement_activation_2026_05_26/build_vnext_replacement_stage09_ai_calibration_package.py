from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

ACTIVATION_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"
)
MOONSHOT_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE05_SHARD_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE}.jsonl"
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
STAGE08_VERIFIER = ROUTE_DIR / f"VNEXT_REPLACEMENT_SOURCE_MARKET_ACTIVATION_VERIFIER_{DATE}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"

CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
PRODUCTION_PROMPT_PATH = REPO_ROOT / "src/prompts/primary_analyzer_prompt.py"
PRIMARY_ANALYZER_PATH = REPO_ROOT / "src/components/primary_analyzer.py"
AI_SUPERVISOR_PATH = REPO_ROOT / "src/components/ai_supervisor.py"

ACTIVATION_BUDGET_PLAN = ACTIVATION_ROUTE / f"VNEXT_ACTIVATION_AI_VALIDATION_BUDGET_PLAN_{DATE}.json"
ACTIVATION_AI_SUMMARY = ACTIVATION_ROUTE / f"VNEXT_ACTIVATION_AI_VALIDATION_SUMMARY_{DATE}.json"
MOONSHOT_AI_SUMMARY = MOONSHOT_ROUTE / f"VNEXT_MOONSHOT_AI_ROLE_BUDGET_SUMMARY_{DATE}.json"

OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_CALIBRATION_MANIFEST_{DATE}.json"
OUTPUT_PROMPT_PACK = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_PROMPT_PACK_{DATE}.jsonl"
OUTPUT_SPEND_REQUEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_AI_SPEND_REQUEST_{DATE}.md"

TARGET_SMOKE_PACKETS = 32
REQUESTED_HARD_CAP_USD = 5.0
ESTIMATED_OUTPUT_TOKENS_PER_CALL = 900
ESTIMATED_SYSTEM_TOKENS_PER_CALL = 2500

MANDATORY_STRATA = [
    "high_ev_opportunity_branch",
    "fixed_vs_dynamic_live_lost",
    "fixed_vs_dynamic_live_rescued",
    "same_bar_ambiguous",
    "high_quality_live_winner",
    "high_quality_live_loser",
    "costly_live_loser",
    "ai_required_context_rich",
    "no_paid_mechanical_control",
    "source_sensitive_window_incomplete",
    "market_awareness_edge_case",
    "prop_ev_optimized_candidate",
    "mixed_or_policy_disagreement_proxy",
    "nofill_pending_lifecycle",
    "prop_near_boundary_ev_stream",
]

FORBIDDEN_PACKET_KEYS = {
    "accepted_losers",
    "accepted_winners",
    "account_loss_rate",
    "be_after_trigger_final_r",
    "best_expectancy_r",
    "best_pass_probability_proxy",
    "best_total_r",
    "blocked_negative_r",
    "blocked_positive_r",
    "condition_vs_fixed_delta_r",
    "condition_vs_global_be_delta_r",
    "condition_vs_live_current_delta_r",
    "conservative_ambiguous_r",
    "expectancy_r",
    "exit_reason",
    "exit_time_utc",
    "final_r",
    "gross_loss_r",
    "gross_win_r",
    "legacy_final_r",
    "live_current_j46_j49_final_r",
    "live_exit_reason",
    "mae_r",
    "mfe_r",
    "missed_winners",
    "optimistic_ambiguous_r",
    "pass_probability_proxy",
    "pending_lifecycle_state",
    "policy_reversal_bucket",
    "post_trade_equity",
    "profit_factor",
    "selected_policy_final_r",
    "selected_vs_fixed_delta_r",
    "selected_vs_live_delta_r",
    "simulated_r",
    "terminal_order_raw",
    "terminal_outcome",
    "total_r",
    "win_rate",
}

CALIBRATION_SYSTEM_PROMPT = """You are the GTOS production AI calibration validator. Use only the supplied as-of candidate context and source-completeness metadata. Do not infer from hidden outcomes, replay R, terminal path results, or post-trade labels. Return strict JSON matching schema version vnext_replacement_ai_calibration_response_v1. Decide whether the mechanical vNext candidate should be ACCEPT_MECHANICAL, REJECT_MECHANICAL, or NEEDS_MORE_CONTEXT, and identify the AI role: validator_only, mixed_resolver, safety_veto, no_ai_needed, or defer_to_capture. If source or same-bar ambiguity is material, prefer NEEDS_MORE_CONTEXT. Do not add fields outside the schema."""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_line_number"] = line_number
                rows.append(row)
    return rows


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _get_float(row: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_true(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


def _scan_forbidden_keys(data: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_l = str(key).lower()
            if key_l in FORBIDDEN_PACKET_KEYS or key_l.endswith("_r") or key_l.endswith("_outcome"):
                hits.append(f"{path}.{key}")
            hits.extend(_scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            hits.extend(_scan_forbidden_keys(value, f"{path}[{index}]"))
    return hits


def _extract_model_config(config_text: str) -> dict[str, Any]:
    def find(pattern: str, default: str) -> str:
        match = re.search(pattern, config_text, flags=re.MULTILINE)
        return match.group(1).strip().strip("\"'") if match else default

    return {
        "api_timeout_seconds": find(r"^\s*api_timeout_seconds:\s*([^\s#]+)", "90"),
        "monthly_cap_usd": find(r"^\s*monthly_cap_usd:\s*([^\s#]+)", "50.0"),
        "primary_effort": find(r"^\s*primary_effort:\s*([^\s#]+)", "max"),
        "primary_model": find(r"^\s*primary_model:\s*([^\s#]+)", "claude-sonnet-4-6"),
    }


def _iter_stage05_rows() -> Any:
    for manifest_row in _read_jsonl(STAGE05_SHARD_MANIFEST):
        output_path = manifest_row.get("output_path") or manifest_row.get("output_chunk_path")
        if not output_path:
            raise RuntimeError(f"Stage05 shard manifest row lacks output path: {manifest_row.get('shard_id')}")
        shard_path = REPO_ROOT / output_path
        with gzip.open(shard_path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    row = json.loads(line)
                    row["_stage05_shard_id"] = manifest_row.get("shard_id")
                    row["_stage05_shard_line"] = line_number
                    yield row


def _row_strata(row: dict[str, Any], market_class: str) -> list[str]:
    strata: set[str] = set()
    old_r = _get_float(row, "old_gtos_current_shadow", "final_r")
    fixed_r = _get_float(row, "legacy_fixed_1_5r_comparator", "final_r")
    be_r = _get_float(row, "moonshot_be_after_trigger", "final_r")
    condition_r = _get_float(row, "condition_router_projection", "selected_policy_final_r")
    source_complete = _is_true(row.get("source_window_complete"))
    source_mode = str(row.get("source_mode") or "")
    session = str(row.get("session_bucket") or "")
    framework = str(row.get("framework") or "")
    origin = str(row.get("candidate_origin_family") or "")
    activated = row.get("activated_default_router_projection") or {}
    condition = row.get("condition_router_projection") or {}
    dynamic = row.get("dynamic_policy_replay") or {}
    prop = row.get("prop_governor_projection") or {}
    path_modes = row.get("path_modes") if isinstance(row.get("path_modes"), dict) else {}

    same_bar = False
    for policy_result in (dynamic.get("policy_results") or {}).values():
        if isinstance(policy_result, dict) and policy_result.get("same_bar_ambiguity") is True:
            same_bar = True
    for path_row in path_modes.values():
        if isinstance(path_row, dict) and path_row.get("same_bar_ambiguity") is True:
            same_bar = True
    if same_bar:
        strata.add("same_bar_ambiguous")

    if not source_complete or "source_window_incomplete" in " ".join(map(str, activated.get("refusal_reasons") or [])):
        strata.add("source_sensitive_window_incomplete")

    if condition_r >= fixed_r + 0.5 or condition_r >= 2.0:
        strata.add("high_ev_opportunity_branch")
    if old_r < 0.0 and max(be_r, condition_r, fixed_r) > 0.0:
        strata.add("fixed_vs_dynamic_live_lost")
        strata.add("costly_live_loser")
    if fixed_r < 0.0 and max(be_r, condition_r) > 0.0:
        strata.add("fixed_vs_dynamic_live_rescued")
    if old_r > 0.0 and source_complete:
        strata.add("high_quality_live_winner")
    if old_r <= -1.0 and source_complete:
        strata.add("high_quality_live_loser")

    ai_role = str(activated.get("ai_role") or row.get("ai_policy_scenario", {}).get("activation_role") or "")
    if "AI" in ai_role and "NO_AI" not in ai_role:
        strata.add("ai_required_context_rich")

    if source_complete and not same_bar and market_class == "broker_native_live_feed_available_now":
        strata.add("no_paid_mechanical_control")
    if "SIERRA" in source_mode or "LOCAL_TICK" in source_mode or market_class != "broker_native_live_feed_available_now" or session == "off_kz_broad":
        strata.add("market_awareness_edge_case")
    if prop.get("candidate_matches_best_branch") is True or origin == prop.get("best_branch_id"):
        strata.add("prop_ev_optimized_candidate")
    if condition.get("selected_policy") not in (None, "be_after_trigger", "legacy_fixed_1.5r") or (old_r < 0.0 < max(be_r, condition_r)):
        strata.add("mixed_or_policy_disagreement_proxy")

    lifecycle_values = [str((path or {}).get("pending_lifecycle_state") or "") for path in path_modes.values() if isinstance(path, dict)]
    if any("pending" in value or "filled" in value or "no_fill" in value for value in lifecycle_values):
        strata.add("nofill_pending_lifecycle")

    if prop.get("candidate_level_prop_action_available") is True or "near_boundary" in str(prop.get("candidate_level_prop_action_status") or ""):
        strata.add("prop_near_boundary_ev_stream")

    # FVG is the corrected branch that dominated the prior moonshot prop EV package.
    if framework == "fvg_fill" or origin == "origin_current_fvg_fill":
        strata.add("prop_ev_optimized_candidate")

    return [name for name in MANDATORY_STRATA if name in strata]


def _sanitize_path_modes(row: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    path_modes = row.get("path_modes") if isinstance(row.get("path_modes"), dict) else {}
    for mode, path_row in path_modes.items():
        if not isinstance(path_row, dict):
            continue
        sanitized[mode] = {
            "path_row_id": path_row.get("path_row_id"),
            "path_source_status": path_row.get("path_source_status"),
            "price_path_truth_status": path_row.get("price_path_truth_status"),
            "replay_mode": path_row.get("replay_mode"),
            "same_bar_ambiguity": path_row.get("same_bar_ambiguity"),
            "source_evidence_type": path_row.get("source_evidence_type"),
            "source_gap_class": path_row.get("source_gap_class"),
            "source_mode": path_row.get("source_mode"),
            "source_path": path_row.get("source_path"),
            "source_sha256": path_row.get("source_sha256"),
            "source_timeframe": path_row.get("source_timeframe"),
            "source_window_complete": path_row.get("source_window_complete"),
        }
    return sanitized


def _packet_context(row: dict[str, Any], selected_strata: list[str], market_class: str) -> dict[str, Any]:
    activated = row.get("activated_default_router_projection") or {}
    condition = row.get("condition_router_projection") or {}
    prop = row.get("prop_governor_projection") or {}
    context = {
        "as_of_candidate": {
            "candidate_id": row.get("candidate_id"),
            "candidate_origin_family": row.get("candidate_origin_family"),
            "candle_time_utc": row.get("candle_time_utc"),
            "entry_reference": row.get("entry_reference"),
            "framework": row.get("framework"),
            "rr": row.get("rr"),
            "session_bucket": row.get("session_bucket"),
            "side": row.get("side"),
            "stop_or_invalidation": row.get("stop_or_invalidation"),
            "symbol": row.get("symbol"),
            "target_reference": row.get("target_reference"),
            "year": row.get("year"),
        },
        "condition_router_asof_fields": {
            "available": condition.get("available"),
            "current_bar_displacement_bucket": condition.get("current_bar_displacement_bucket"),
            "selected_policy": condition.get("selected_policy"),
            "selector_condition_key": condition.get("selector_condition_key"),
            "selector_avoids_expost_same_bar_label": condition.get("selector_excludes_expost_same_bar_outcome"),
            "selector_uses_only_asof_feature_columns": condition.get("selector_uses_only_asof_feature_columns"),
        },
        "dynamic_execution_asof_policy": {
            "available": (row.get("dynamic_policy_replay") or {}).get("available"),
            "same_bar_policy": (row.get("dynamic_policy_replay") or {}).get("same_bar_policy"),
            "source_replay_mode": (row.get("dynamic_policy_replay") or {}).get("source_replay_mode"),
        },
        "market_source_activation": {
            "market_activation_class": market_class,
            "source_mode": row.get("source_mode"),
            "source_path": row.get("source_path"),
            "source_sha256": row.get("source_sha256"),
            "source_window_complete": _is_true(row.get("source_window_complete")),
        },
        "path_source_status_only": _sanitize_path_modes(row),
        "prop_context_no_results": {
            "best_branch_id": prop.get("best_branch_id"),
            "best_policy_name": prop.get("best_policy_name"),
            "best_prop_policy": prop.get("best_prop_policy"),
            "candidate_level_prop_action_available": prop.get("candidate_level_prop_action_available"),
            "candidate_level_prop_action_status": prop.get("candidate_level_prop_action_status"),
            "candidate_matches_best_branch": prop.get("candidate_matches_best_branch"),
        },
        "replacement_router_asof_fields": {
            "ai_role": activated.get("ai_role"),
            "candidate_action": activated.get("candidate_action"),
            "decision_status": activated.get("decision_status"),
            "refusal_reasons": activated.get("refusal_reasons"),
            "selected_branch": activated.get("selected_branch"),
            "selected_policy": activated.get("selected_policy"),
            "source_quality_action": activated.get("source_quality_action"),
        },
        "selected_calibration_strata": selected_strata,
    }
    hits = _scan_forbidden_keys(context)
    if hits:
        raise RuntimeError(f"forbidden outcome fields leaked into AI packet {row.get('candidate_id')}: {hits[:8]}")
    return context


def _offline_scoring_hash(row: dict[str, Any]) -> str:
    scoring_reference = {
        "activated_replay_disposition": row.get("activated_replay_disposition"),
        "candidate_id": row.get("candidate_id"),
        "condition_router_final_r": _get_float(row, "condition_router_projection", "selected_policy_final_r"),
        "legacy_fixed_final_r": _get_float(row, "legacy_fixed_1_5r_comparator", "final_r"),
        "moonshot_be_final_r": _get_float(row, "moonshot_be_after_trigger", "final_r"),
        "old_gtos_final_r": _get_float(row, "old_gtos_current_shadow", "final_r"),
        "source_window_complete": row.get("source_window_complete"),
        "symbol": row.get("symbol"),
    }
    return _sha256_text(_stable_json(scoring_reference))


def _selection_sort_key(row: dict[str, Any]) -> str:
    base = {
        "candidate_id": row.get("candidate_id"),
        "candle_time_utc": row.get("candle_time_utc"),
        "framework": row.get("framework"),
        "session_bucket": row.get("session_bucket"),
        "side": row.get("side"),
        "symbol": row.get("symbol"),
        "year": row.get("year"),
    }
    return _sha256_text(_stable_json(base))


def _select_prompt_rows(candidates: list[dict[str, Any]], strata_counts: Counter[str]) -> tuple[list[dict[str, Any]], Counter[str]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_counts: Counter[str] = Counter()

    by_stratum: dict[str, list[dict[str, Any]]] = {stratum: [] for stratum in MANDATORY_STRATA}
    for row in candidates:
        for stratum in row["_stage09_strata"]:
            by_stratum[stratum].append(row)
    for rows in by_stratum.values():
        rows.sort(key=_selection_sort_key)

    # Coverage pass: each available mandatory stratum gets one row before breadth fill.
    for stratum in MANDATORY_STRATA:
        for row in by_stratum[stratum]:
            row_id = str(row.get("candidate_id"))
            if row_id in selected_ids:
                continue
            selected.append(row)
            selected_ids.add(row_id)
            selected_counts.update(row["_stage09_strata"])
            break

    # Breadth fill: prefer rows that cover undersampled strata, then deterministic hash.
    while len(selected) < TARGET_SMOKE_PACKETS:
        remaining = [row for row in candidates if str(row.get("candidate_id")) not in selected_ids]
        if not remaining:
            break
        remaining.sort(
            key=lambda row: (
                -sum(1 for stratum in row["_stage09_strata"] if selected_counts[stratum] < 2),
                _selection_sort_key(row),
            )
        )
        row = remaining[0]
        selected.append(row)
        selected_ids.add(str(row.get("candidate_id")))
        selected_counts.update(row["_stage09_strata"])

    return selected, selected_counts


def _build_prompt_pack(
    selected_rows: list[dict[str, Any]],
    market_classes: dict[str, str],
    model_config: dict[str, Any],
    hashes: dict[str, str],
) -> tuple[list[dict[str, Any]], Counter[str], int]:
    response_schema = {
        "confidence": "integer_0_to_100",
        "decision": ["ACCEPT_MECHANICAL", "REJECT_MECHANICAL", "NEEDS_MORE_CONTEXT"],
        "disallowed_fields_used": False,
        "reason_codes": "list[str]",
        "required_context_fields_used": "list[str]",
        "risk_notes": "list[str]",
        "schema_version": "vnext_replacement_ai_calibration_response_v1",
        "recommended_ai_role": ["validator_only", "mixed_resolver", "safety_veto", "no_ai_needed", "defer_to_capture"],
    }
    schema_hash = _sha256_text(_stable_json(response_schema))
    prompt_hash = _sha256_text(CALIBRATION_SYSTEM_PROMPT)
    rows: list[dict[str, Any]] = []
    token_estimate = 0
    selected_strata_counts: Counter[str] = Counter()
    for index, row in enumerate(selected_rows, start=1):
        selected_strata = row["_stage09_strata"]
        selected_strata_counts.update(selected_strata)
        market_class = market_classes.get(str(row.get("symbol")), "unknown_market_source_class")
        context = _packet_context(row, selected_strata, market_class)
        packet_hash = _sha256_text(_stable_json(context))
        cache_key = _sha256_text(
            _stable_json(
                {
                    "cache_key_policy": "sha256(model_id, model_effort, calibration_prompt_hash, production_prompt_hash, config_hash, packet_hash, schema_hash)",
                    "calibration_prompt_hash": prompt_hash,
                    "config_hash": hashes["config_hash"],
                    "model_effort": model_config["primary_effort"],
                    "model_id": model_config["primary_model"],
                    "packet_hash": packet_hash,
                    "production_prompt_hash": hashes["production_prompt_hash"],
                    "schema_hash": schema_hash,
                }
            )
        )
        prompt_payload = {
            "candidate_context": context,
            "instruction": "Return strict JSON only. Validate the mechanical vNext candidate using as-of/source-completeness fields only.",
            "response_schema": response_schema,
        }
        packet_tokens = max(1, len(_stable_json(prompt_payload)) // 4)
        token_estimate += packet_tokens
        rows.append(
            {
                "budget_tier": "smoke_plumbing",
                "cache_key": cache_key,
                "calibration_prompt_hash": prompt_hash,
                "config_hash": hashes["config_hash"],
                "estimated_packet_tokens": packet_tokens,
                "forbidden_outcome_fields_excluded": True,
                "model_effort": model_config["primary_effort"],
                "model_id": model_config["primary_model"],
                "no_paid_call_made": True,
                "offline_scoring_reference_hash": _offline_scoring_hash(row),
                "packet_hash": packet_hash,
                "packet_id": f"VNEXT-REPLACEMENT-AI-SMOKE-{index:03d}",
                "production_prompt_hash": hashes["production_prompt_hash"],
                "prompt_payload": prompt_payload,
                "route_id": ROUTE_ID,
                "schema_hash": schema_hash,
                "schema_version": "vnext_replacement_ai_prompt_packet_v1",
                "selected_strata": selected_strata,
                "source_replay_locator": {
                    "candidate_id": row.get("candidate_id"),
                    "path_row_id": row.get("path_row_id"),
                    "source_path": row.get("source_path"),
                    "stage05_shard_id": row.get("_stage05_shard_id"),
                    "stage05_shard_line": row.get("_stage05_shard_line"),
                },
                "stage_id": "stage_09_ai_calibration_package",
            }
        )
    return rows, selected_strata_counts, token_estimate


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stage05 = _read_json(STAGE05_SUMMARY)
    stage08_map = _read_json(STAGE08_MAP)
    stage08_verifier = _read_json(STAGE08_VERIFIER)
    state = _read_json(STATE_PATH)
    route_manifest = _read_json(MANIFEST_PATH)
    activation_budget = _read_json(ACTIVATION_BUDGET_PLAN)
    activation_summary = _read_json(ACTIVATION_AI_SUMMARY)
    moonshot_ai_summary = _read_json(MOONSHOT_AI_SUMMARY)

    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    model_config = _extract_model_config(config_text)
    hashes = {
        "ai_supervisor_hash": _sha256_file(AI_SUPERVISOR_PATH),
        "config_hash": _sha256_file(CONFIG_PATH),
        "primary_analyzer_hash": _sha256_file(PRIMARY_ANALYZER_PATH),
        "production_prompt_hash": _sha256_file(PRODUCTION_PROMPT_PATH),
    }

    market_classes = {row["symbol"]: row["market_activation_class"] for row in stage08_map["markets"]}
    strata_counts: Counter[str] = Counter()
    source_status_counts: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    scanned_rows = 0

    for row in _iter_stage05_rows():
        scanned_rows += 1
        market_class = market_classes.get(str(row.get("symbol")), "unknown_market_source_class")
        strata = _row_strata(row, market_class)
        row["_stage09_strata"] = strata
        strata_counts.update(strata)
        source_status_counts.update([str(row.get("activated_replay_disposition"))])
        if strata:
            candidates.append(row)

    if scanned_rows != int(stage05["coverage"]["candidate_rows"]):
        raise RuntimeError(f"Stage09 scan row mismatch: {scanned_rows} != {stage05['coverage']['candidate_rows']}")

    selected_rows, selected_strata_counts = _select_prompt_rows(candidates, strata_counts)
    prompt_rows, prompt_selected_counts, packet_token_estimate = _build_prompt_pack(selected_rows, market_classes, model_config, hashes)
    if selected_strata_counts != prompt_selected_counts:
        raise RuntimeError("selected stratum counts changed during prompt pack construction")

    with OUTPUT_PROMPT_PACK.open("w", encoding="utf-8", newline="\n") as handle:
        for row in prompt_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    unavailable_strata = [
        {
            "reason": "No eligible row in Stage05 replacement replay; prior moonshot package noted this needs per-trade prop attempt source state that Stage05 does not contain.",
            "stratum": stratum,
        }
        for stratum in MANDATORY_STRATA
        if strata_counts[stratum] == 0
    ]
    covered_strata = [stratum for stratum in MANDATORY_STRATA if selected_strata_counts[stratum] > 0]
    estimated_total_input_tokens = TARGET_SMOKE_PACKETS * ESTIMATED_SYSTEM_TOKENS_PER_CALL + packet_token_estimate
    estimated_output_tokens = TARGET_SMOKE_PACKETS * ESTIMATED_OUTPUT_TOKENS_PER_CALL
    sonnet_cost = (
        (estimated_total_input_tokens / 1_000_000.0)
        * float(activation_budget["model_plan"]["model_cost_assumptions_usd_per_million_tokens"]["claude-sonnet-4-6"]["input"])
        + (estimated_output_tokens / 1_000_000.0)
        * float(activation_budget["model_plan"]["model_cost_assumptions_usd_per_million_tokens"]["claude-sonnet-4-6"]["output"])
    )

    response_schema = prompt_rows[0]["prompt_payload"]["response_schema"] if prompt_rows else {}
    manifest = {
        "ai_call_execution_state": {
            "budget_cap_present": state["budget_cap_state"].get("route_state_budget_cap_usd") is not None,
            "paid_ai_or_vendor_calls_allowed": False,
            "paid_api_or_vendor_calls_made": 0,
            "reason": "route_state_budget_cap_usd is null; Stage09 writes package and spend request only.",
            "route_state_budget_cap_usd": state["budget_cap_state"].get("route_state_budget_cap_usd"),
        },
        "cache_key_policy": "sha256(model_id, model_effort, calibration_prompt_hash, production_prompt_hash, config_hash, packet_hash, schema_hash)",
        "calibration_prompt_hash": prompt_rows[0]["calibration_prompt_hash"] if prompt_rows else _sha256_text(CALIBRATION_SYSTEM_PROMPT),
        "covered_strata": covered_strata,
        "forbidden_packet_keys": sorted(FORBIDDEN_PACKET_KEYS),
        "generated_at_utc": generated_at,
        "hashes": hashes,
        "input_artifacts": {
            "activation_budget_plan": _rel(ACTIVATION_BUDGET_PLAN),
            "activation_ai_summary": _rel(ACTIVATION_AI_SUMMARY),
            "moonshot_ai_summary": _rel(MOONSHOT_AI_SUMMARY),
            "stage05_summary": _rel(STAGE05_SUMMARY),
            "stage05_shard_manifest": _rel(STAGE05_SHARD_MANIFEST),
            "stage08_map": _rel(STAGE08_MAP),
            "stage08_verifier": _rel(STAGE08_VERIFIER),
        },
        "malformed_response_policy": {
            "repair_function": "src.components.ai_supervisor.repair_ai_response_format_preserving_semantics",
            "stop_tier_if_malformed_rate_gt": 0.05,
            "stop_tier_on_three_consecutive_failures": True,
            "transport_repair_only": True,
        },
        "mandatory_strata": MANDATORY_STRATA,
        "model_binding": model_config,
        "no_live_or_broker_mutation": True,
        "output_schema": response_schema,
        "prior_ai_budget_evidence": {
            "activation_material_stratum_count": activation_summary["material_stratum_count"],
            "activation_selected_candidate_count": activation_summary["selected_candidate_count"],
            "moonshot_manifest_rows": moonshot_ai_summary["manifest_rows"],
            "moonshot_mandatory_strata_covered": moonshot_ai_summary["mandatory_strata_covered"],
            "prior_prompt_hash": moonshot_ai_summary["prompt_hash"],
        },
        "prompt_pack": {
            "forbidden_outcome_fields_excluded": True,
            "packet_rows": len(prompt_rows),
            "path": _rel(OUTPUT_PROMPT_PACK),
            "sha256": _sha256_file(OUTPUT_PROMPT_PACK),
            "target_smoke_packets": TARGET_SMOKE_PACKETS,
        },
        "response_cache_manifest": {
            "cache_write_allowed_before_budget_cap": False,
            "cache_key_count": len({row["cache_key"] for row in prompt_rows}),
            "cache_namespace": "vnext_replacement_ai_calibration",
            "result_path_pattern": f"VNEXT_REPLACEMENT_AI_CALIBRATION_RESULTS_{DATE}_*.jsonl",
        },
        "route_id": ROUTE_ID,
        "sampling_method": {
            "candidate_rows_scanned": scanned_rows,
            "eligible_rows_with_any_stratum": len(candidates),
            "method": "full Stage05 scan; preserve full stratum counts; deterministic coverage pass over mandatory strata; breadth fill by stable packet hash",
            "no_arbitrary_top_n": True,
        },
        "schema_version": "vnext_replacement_stage09_ai_calibration_manifest_v1",
        "selected_stratum_counts": dict(sorted(selected_strata_counts.items())),
        "spend_plan": {
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_packet_tokens": packet_token_estimate,
            "estimated_total_input_tokens": estimated_total_input_tokens,
            "estimated_usd_claude_sonnet_4_6_offline_rate": round(sonnet_cost, 6),
            "hard_cap_requested_usd": REQUESTED_HARD_CAP_USD,
            "price_rate_note": activation_budget["model_plan"]["model_cost_assumptions_usd_per_million_tokens"]["claude-sonnet-4-6"]["rate_source"],
            "run_when_budget_cap_absent": False,
        },
        "stage_id": "stage_09_ai_calibration_package",
        "stage08_source_status": {
            "market_rows": stage08_verifier["market_rows"],
            "source_capture_rows": stage08_verifier["capture_rows"],
            "stage08_verifier_status": stage08_verifier["status"],
        },
        "strata_counts": dict(sorted(strata_counts.items())),
        "unavailable_strata": unavailable_strata,
    }
    _write_json(OUTPUT_MANIFEST, manifest)

    spend_request = f"""# vNext Replacement AI Calibration Spend Request

Route id: `{ROUTE_ID}`
Generated: `{generated_at}`

Stage09 prepared the AI calibration package and made **0 paid API/vendor calls** because `route_state_budget_cap_usd` is null.

## Requested Cap

- Requested hard cap: `${REQUESTED_HARD_CAP_USD:.2f}`
- Target tier: `smoke_plumbing`
- Target calls: `{len(prompt_rows)}`
- Model: `{model_config['primary_model']}`
- Effort: `{model_config['primary_effort']}`
- Estimated input tokens: `{estimated_total_input_tokens}`
- Estimated output tokens: `{estimated_output_tokens}`
- Offline estimated spend at the prior planning rate: `${sonnet_cost:.4f}`
- Price note: refresh provider pricing before any paid run.

## What The Spend Tests

- Cache-key plumbing and prompt hash binding.
- Strict JSON schema compliance.
- Malformed/refusal repair path.
- False accept/reject smoke across selected vNext replacement strata.
- Whether AI should remain validator-only, mixed resolver, safety veto, no-AI-needed, or defer-to-capture for each packet.

## Run Condition

Do not run calls unless the route state is updated with an explicit non-null `route_state_budget_cap_usd` and the cap is at least the requested hard cap. The prompt pack is `{_rel(OUTPUT_PROMPT_PACK)}`.
"""
    OUTPUT_SPEND_REQUEST.write_text(spend_request, encoding="utf-8")

    _upsert_manifest_output(
        route_manifest,
        {"path": OUTPUT_MANIFEST.name, "stage": "stage_09", "status": "created", "prompt_rows": len(prompt_rows)},
    )
    _upsert_manifest_output(
        route_manifest,
        {"path": OUTPUT_PROMPT_PACK.name, "stage": "stage_09", "status": "created", "rows": len(prompt_rows)},
    )
    _upsert_manifest_output(
        route_manifest,
        {"path": OUTPUT_SPEND_REQUEST.name, "stage": "stage_09", "status": "created"},
    )
    route_manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, route_manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["stage09_candidate_rows_scanned"] = scanned_rows
    evidence["stage09_ai_prompt_packet_rows"] = len(prompt_rows)
    evidence["stage09_ai_strata_with_rows"] = sum(1 for value in strata_counts.values() if value > 0)
    evidence["stage09_paid_calls_made"] = 0
    state["current_stage"] = "stage_10_ml_and_monitoring_integration"
    state["first_incomplete_invariant"] = "stage_10_ml_and_monitoring_integration_pending"
    state["exact_next_action"] = "Build ML/monitoring integration map, runtime monitoring schema, and focused tests for vNext apply/router/source/AI/ML monitors."
    state.setdefault("stage_status", {})["stage_09_ai_calibration_package"] = "completed_ai_package_written_no_paid_calls_budget_cap_absent"
    state.setdefault("stage_status", {})["stage_10_ml_and_monitoring_integration"] = "pending"
    state["budget_cap_state"]["paid_ai_or_vendor_calls_allowed"] = False
    state["budget_cap_state"]["decision"] = "Stage09 package and spend request are written; paid calls remain blocked until route_state_budget_cap_usd is non-null."
    _append_test_result(
        state,
        _rel(Path(__file__)),
        "passed; wrote Stage09 AI calibration manifest, prompt pack, and spend request with zero paid calls",
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "stage_09_ai_calibration_package_completed",
            "generated_at_utc": generated_at,
            "paid_api_or_vendor_calls_made": 0,
            "prompt_packet_rows": len(prompt_rows),
            "route_id": ROUTE_ID,
            "stage_id": "stage_09_ai_calibration_package",
        }
    )

    print(
        json.dumps(
            {
                "next": state["first_incomplete_invariant"],
                "paid_calls": 0,
                "prompt_rows": len(prompt_rows),
                "stage": "stage_09_ai_calibration_package",
                "strata_with_rows": evidence["stage09_ai_strata_with_rows"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
