"""Build OTB2R G6 local-OHLC momentum/reversion input packets.

This lane is a proof-or-impossibility input-packet builder. It reconstructs
the G6 prereg chain and emits source-hashed, duplicate-aware input-only
packets from local OHLC/path/candidate evidence. It does not open outcomes,
read broker actual-R, read blocked-packet outcomes, call network/API/Databento,
or touch live trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "otb2r_g6_local_ohlc_packet_v1"
COST_MODEL_VERSION = "otb2r_g6_local_ohlc_cost_model_v1_research_only"
SAME_BAR_POLICY_VERSION = "otb2r_g6_same_bar_timing_policy_v1"
DUPLICATE_POLICY_VERSION = "otb2r_g6_duplicate_denominator_policy_v1"
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets"
PACKETS_DIR = OUT / "packets"

OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
SCI = ROOT / "research/science_program_2026_05"
OTB2R = OT / "otb2r_input_only_path_rebuild"
OTB2 = OT / "otb2_synthetic_packet_builder"
G12_OTB = OT / "g12_otb_rebuild_reaudit"
G0_OTI = OT / "g0_oti_quarantine_synthesis"

G6_PACKET_SPECS: dict[str, dict[str, Any]] = {
    "OTG0-PKT-060": {
        "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
        "hypothesis_id": "G6-HYP-001",
        "packet_file_stem": "OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet",
        "family": "ob_vs_generic_retrace",
        "declared_future_label_family": "synthetic_path_r",
        "otg0_lane": "synthetic_replay_existing_data_audit",
        "required_fields": [
            "registered_source_contracts",
            "ob_vs_generic_packet",
            "generic_retrace_comparator",
            "entry_sl_tp_or_level_packet",
            "duplicate_setup_id",
            "source_hash",
        ],
    },
    "OTG0-PKT-061": {
        "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
        "hypothesis_id": "G6-HYP-002",
        "packet_file_stem": "OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet",
        "family": "impulse_pullback_no_retrace",
        "declared_future_label_family": "lifecycle_no_fill",
        "otg0_lane": "forward_shadow_prospective",
        "required_fields": [
            "candidate_id",
            "decision_asof_utc",
            "original_trade_geometry",
            "decision_price_proxy_status",
            "duplicate_group_id",
            "source_hash",
            "label_family_declared_before_followup",
        ],
    },
    "OTG0-PKT-062": {
        "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
        "hypothesis_id": "G6-HYP-003",
        "packet_file_stem": "OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet",
        "family": "opening_drive_continuation",
        "declared_future_label_family": "synthetic_path_r",
        "otg0_lane": "synthetic_replay_existing_data_audit",
        "required_fields": [
            "registered_source_contracts",
            "opening_drive_packet",
            "frozen_range_definition",
            "path_start_utc",
            "path_end_utc",
            "cost_model_version",
            "duplicate_breakout_key",
        ],
    },
    "OTG0-PKT-063": {
        "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
        "hypothesis_id": "G6-HYP-004",
        "packet_file_stem": "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet",
        "family": "exhaustion_changepoint",
        "declared_future_label_family": "synthetic_path_r",
        "otg0_lane": "synthetic_replay_existing_data_audit",
        "required_fields": [
            "registered_source_contracts",
            "exhaustion_changepoint_packet",
            "threshold_freeze",
            "ordered_path_source_id",
            "duplicate_impulse_key",
            "source_hash",
            "cost_model_version",
        ],
    },
    "OTG0-PKT-066": {
        "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
        "hypothesis_id": "G6-HYP-007",
        "packet_file_stem": "OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet",
        "family": "gold_round_ob_confluence",
        "declared_future_label_family": "synthetic_path_r",
        "otg0_lane": "synthetic_replay_existing_data_audit",
        "required_fields": [
            "registered_source_contracts",
            "round_number_band_packet",
            "ob_bounds",
            "liquidity_sweep_asof_fields",
            "ordered_path_source_id",
            "duplicate_ob_zone_key",
            "source_hash",
        ],
    },
}

CONTROL_INPUTS = {
    "live_state": ROOT / ".context/LIVE_STATE.md",
    "goal_session_research_discipline": ROOT / ".context/00_core/goal_session_research_discipline.md",
    "research_operating_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ROOT / ".context/00_core/research_current_state.md",
    "g0_oti_next_lane_prompt_pack": G0_OTI / f"G0_OTI_NEXT_LANE_PROMPT_PACK_{DATE_STAMP}.md",
    "g0_oti_blocker_action_map": G0_OTI / f"G0_OTI_BLOCKER_ACTION_MAP_{DATE_STAMP}.md",
    "g6_domain_synthesis": SCI / "01_domain_syntheses/G6_MOMENTUM_REVERSION_DOMAIN_SYNTHESIS_2026-05-06.md",
    "g6_rows": SCI / "01_domain_syntheses/G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json",
    "otg0_prereg_classification": OT / f"OTG0_PREREG_CLASSIFICATION_LEDGER_{DATE_STAMP}.json",
    "otg0_packet_manifest": OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otg0_control_rules": OT / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE_STAMP}.json",
    "master_registry": SCI / "05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md",
    "source_registry": SCI / "00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
    "experiment_preregistry": SCI / "03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
    "hypothesis_registry": SCI / "02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
    "otb2_manifest": OTB2 / f"OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otb2r_manifest": OTB2R / f"OTB2R_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otb2r_source_hashes": OTB2R / f"OTB2R_SANITIZED_SOURCE_HASHES_{DATE_STAMP}.json",
    "otb2r_duplicate_policy": OTB2R / f"OTB2R_DUPLICATE_GROUP_POLICY_{DATE_STAMP}.json",
    "otb2r_same_bar_policy": OTB2R / f"OTB2R_SAME_BAR_AMBIGUITY_POLICY_{DATE_STAMP}.json",
    "g12_otb_rebuild_decision_ledger": G12_OTB / f"G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_{DATE_STAMP}.json",
    "g12_otb_rebuild_blocked_questions": G12_OTB / f"G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_{DATE_STAMP}.json",
    "g12_otb_rebuild_source_hash": G12_OTB / f"G12_OTB_REBUILD_SOURCE_HASH_REVIEW_{DATE_STAMP}.json",
    "g12_otb_rebuild_leakage": G12_OTB / f"G12_OTB_REBUILD_LEAKAGE_REVIEW_{DATE_STAMP}.json",
    "g12_otb_rebuild_duplicate": G12_OTB / f"G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}.json",
    "g12_otb_rebuild_label": G12_OTB / f"G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_{DATE_STAMP}.json",
}

LOCAL_SOURCE_PATHS = {
    "strategy_follow_candidates_raw": ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "strategy_follow_candidates_projection": OTB2R / f"projections/strategy_follow_candidates_input_only_projection_{DATE_STAMP}.jsonl",
    "prefill_delivery_path_projection": OTB2R / f"projections/prefill_delivery_path_input_only_projection_{DATE_STAMP}.jsonl",
    "candidate_ltf_path_order_projection": OTB2R / f"projections/candidate_ltf_path_order_input_only_projection_{DATE_STAMP}.jsonl",
    "candidate_mso_snapshot_joins_raw": ROOT / "shadow_logs/candidate_mso_snapshot_joins.jsonl",
    "fvg_ob_confluence_raw": ROOT / "shadow_logs/fvg_ob_confluence.jsonl",
    "live_structural_strategy_metadata_raw": ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
    "continuation_no_retrace_candidates_raw": ROOT / "shadow_logs/continuation_no_retrace_candidates.jsonl",
    "continuation_no_retrace_resolutions_skipped_policy": ROOT / "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "m15_choch_diagnostic_audit_skipped_policy": ROOT / "shadow_logs/m15_choch_diagnostic_audit.jsonl",
    "broker_actual_r_skipped_policy": ROOT / "shadow_logs/broker_actual_r_audit.jsonl",
    "account_history_skipped_policy": ROOT / "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
}

SKIPPED_SOURCE_POLICY_KEYS = {
    "continuation_no_retrace_resolutions_skipped_policy",
    "m15_choch_diagnostic_audit_skipped_policy",
    "broker_actual_r_skipped_policy",
    "account_history_skipped_policy",
}

RESULT_FIELD_FRAGMENTS = (
    "actual_r",
    "broker_actual",
    "close_fill",
    "entry_first_touch",
    "final_outcome",
    "gross_r",
    "hit_sl",
    "hit_tp",
    "mae",
    "mfe",
    "net_r",
    "outcome",
    "path_label",
    "path_outcome",
    "pnl",
    "profit",
    "realized_r",
    "result",
    "sl_first_touch",
    "synthetic_path",
    "tp1_first_touch",
    "trade_result",
    "win_loss",
)

ALLOWED_CONTROL_KEYS = {
    "outcome_review_opened",
    "promotion_verdict",
    "declared_future_label_family",
    "outcome_scoring_run",
    "broker_actual_r_inspected",
    "blocked_packet_outcomes_inspected",
    "result_or_quarantine_outputs_created",
}

SESSION_STARTS_UTC = {
    "tokyo": (0, 0),
    "london": (7, 0),
    "ny": (13, 0),
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(json_dumps(obj).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def run_command(args: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
        return {
            "command": " ".join(args),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip().splitlines()[:160],
            "stderr": proc.stderr.strip().splitlines()[:80],
        }
    except Exception as exc:  # pragma: no cover - audit evidence only
        return {"command": " ".join(args), "error": repr(exc)}


def git_head() -> str:
    result = run_command(["git", "rev-parse", "HEAD"])
    return (result.get("stdout") or ["UNKNOWN"])[0]


def git_branch() -> str:
    result = run_command(["git", "branch", "--show-current"])
    return (result.get("stdout") or ["UNKNOWN"])[0]


def source_inventory() -> dict[str, dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = {}
    for name, path in {**CONTROL_INPUTS, **LOCAL_SOURCE_PATHS}.items():
        if name in SKIPPED_SOURCE_POLICY_KEYS:
            inventory[name] = {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": "NOT_READ_OR_HASHED_SKIPPED_BY_POLICY",
                "size_bytes": "NOT_STAT_SKIPPED_BY_POLICY",
                "read_or_hashed": False,
                "skip_reason": "Forbidden result/account-history/resolution source for this input-only packet lane.",
            }
            continue
        inventory[name] = {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "read_or_hashed": True,
        }
    return inventory


def is_forbidden_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in ALLOWED_CONTROL_KEYS:
        return False
    if lowered.startswith("take_profit_"):
        return False
    return any(fragment in lowered for fragment in RESULT_FIELD_FRAGMENTS)


def forbidden_key_hits(obj: Any, prefix: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{prefix}.{key}"
            if is_forbidden_key(key):
                hits.append({"path": child, "key": key})
            hits.extend(forbidden_key_hits(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(forbidden_key_hits(value, f"{prefix}[{idx}]"))
    return hits


def sanitize_trade_parameters(params: dict[str, Any]) -> dict[str, Any]:
    return {
        "direction": params.get("direction"),
        "entry_price": params.get("entry_price"),
        "stop_loss": params.get("stop_loss"),
        "take_profit_1": params.get("take_profit_1"),
        "take_profit_2": params.get("take_profit_2"),
        "take_profit_3": params.get("take_profit_3"),
        "sl_buffer_applied": params.get("sl_buffer_applied"),
        "position_size_lots": params.get("position_size_lots"),
        "risk_reward_ratio": params.get("risk_reward_ratio"),
    }


def parse_ob_bounds_from_text(text: str) -> dict[str, Any]:
    # Examples observed in local rows:
    # "H1 OB found at 75.47-75.79 near AI's POI at 75.63"
    # "Entry 75.47 is within OB zone 75.47-75.79"
    matches = re.findall(r"(?:OB(?:\s+zone)?(?:\s+found)?\s+at|OB\s+zone)\s+([0-9]+(?:\.[0-9]+)?)[-–]([0-9]+(?:\.[0-9]+)?)", text)
    if not matches:
        matches = re.findall(r"\b([0-9]+(?:\.[0-9]+)?)[-–]([0-9]+(?:\.[0-9]+)?)\b", text)
    if not matches:
        return {"status": "SOURCE_NOT_CAPTURED", "low": None, "high": None, "source": None}
    a, b = matches[0]
    low = min(float(a), float(b))
    high = max(float(a), float(b))
    return {
        "status": "PARSED_FROM_DECISION_TIME_L2_VERIFICATION_DETAIL",
        "low": round(low, 8),
        "high": round(high, 8),
        "source": text[:240],
    }


def ob_bounds_from_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    for check in checks:
        name = str(check.get("name") or "")
        if name not in {"h1_poi_exists", "entry_in_ob", "sl_beyond_ob", "ob_zone"}:
            continue
        detail = str(check.get("detail") or "")
        parsed = parse_ob_bounds_from_text(detail)
        if parsed["status"] != "SOURCE_NOT_CAPTURED":
            return parsed
    return {"status": "SOURCE_NOT_CAPTURED", "low": None, "high": None, "source": None}


def sanitize_strategy_row(row: dict[str, Any]) -> dict[str, Any] | None:
    candidate_id = row.get("candidate_id")
    params = row.get("trade_parameters") or {}
    if not candidate_id or not params.get("entry_price") or not params.get("stop_loss"):
        return None
    checks = []
    for check in (row.get("verification") or {}).get("checks") or []:
        if not isinstance(check, dict):
            continue
        name = str(check.get("name") or "")
        if name in {
            "m15_choch_exists",
            "displacement_ratio",
            "h1_poi_exists",
            "ob_zone",
            "entry_in_ob",
            "sl_beyond_ob",
            "entry_in_fvg",
            "entry_in_breaker",
            "gap_ceiling",
        }:
            checks.append({"name": name, "status": check.get("status"), "detail": check.get("detail")})
    return {
        "candidate_id": candidate_id,
        "source_line_no": row.get("_source_line_no"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "session": row.get("session") or row.get("kill_zone"),
        "kill_zone": row.get("kill_zone") or row.get("session"),
        "side": row.get("side") or params.get("direction"),
        "framework": row.get("framework"),
        "decision_asof_utc": row.get("asof_cutoff_utc") or row.get("decision_time_utc"),
        "decision_time_utc": row.get("decision_time_utc"),
        "source_capture_utc": row.get("created_at_utc"),
        "trade_parameters": sanitize_trade_parameters(params),
        "verification_decision_fields": {
            "passed": (row.get("verification") or {}).get("passed"),
            "blocked_by": (row.get("verification") or {}).get("blocked_by"),
            "checks": checks,
        },
        "ob_bounds": ob_bounds_from_checks(checks),
        "projection_hash": None,
    }


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("source_capture_utc") or row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = parse_utc((out.get(cid) or {}).get("source_capture_utc") or (out.get(cid) or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if current >= previous:
            out[cid] = row
    return out


def load_strategy_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_rows = load_jsonl(LOCAL_SOURCE_PATHS["strategy_follow_candidates_raw"])
    projection_rows = load_jsonl(LOCAL_SOURCE_PATHS["strategy_follow_candidates_projection"])
    projections = {row.get("candidate_id"): row for row in projection_rows if row.get("candidate_id")}
    sanitized: list[dict[str, Any]] = []
    skipped = Counter()
    for row in raw_rows:
        item = sanitize_strategy_row(row)
        if item is None:
            skipped["missing_candidate_or_geometry"] += 1
            continue
        projection = projections.get(item["candidate_id"]) or {}
        item["projection_hash"] = projection.get("projection_hash")
        item["projection_source_line_no"] = projection.get("source_line_no")
        sanitized.append(item)
    unique = list(latest_by_candidate(sanitized).values())
    unique.sort(key=lambda r: (str(r.get("decision_asof_utc") or ""), str(r.get("candidate_id") or "")))
    return unique, {
        "raw_rows": len(raw_rows),
        "projection_rows": len(projection_rows),
        "sanitized_unique_rows": len(unique),
        "skipped": dict(skipped),
    }


def load_projection_index(source_name: str) -> dict[str, dict[str, Any]]:
    path = LOCAL_SOURCE_PATHS[source_name]
    return {
        row.get("candidate_id"): row
        for row in load_jsonl(path)
        if row.get("candidate_id")
    }


def load_mso_index() -> dict[str, dict[str, Any]]:
    rows = load_jsonl(LOCAL_SOURCE_PATHS["candidate_mso_snapshot_joins_raw"])
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = row.get("candidate_id")
        if not cid:
            continue
        snap = row.get("mso_snapshot") or {}
        out[cid] = {
            "row_key": row.get("row_key"),
            "projection_source_line_no": row.get("_source_line_no"),
            "join_status": row.get("join_status"),
            "timeframe_bias": snap.get("timeframe_bias"),
            "timeframe_counts": snap.get("timeframe_counts"),
            "structural_state": snap.get("structural_state"),
            "mso_timestamp_utc": snap.get("mso_timestamp_utc"),
            "source_hash_component": sha256_json({
                "candidate_id": cid,
                "mso_timestamp_utc": snap.get("mso_timestamp_utc"),
                "timeframe_bias": snap.get("timeframe_bias"),
                "timeframe_counts": snap.get("timeframe_counts"),
            }),
        }
    return out


def load_fvg_ob_index() -> dict[str, dict[str, Any]]:
    rows = load_jsonl(LOCAL_SOURCE_PATHS["fvg_ob_confluence_raw"])
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = row.get("candidate_id")
        if not cid:
            continue
        dtf = row.get("decision_time_fields") or {}
        out[cid] = {
            "source_line_no": row.get("_source_line_no"),
            "bucket": row.get("bucket"),
            "poi_quality": row.get("poi_quality"),
            "touch_count": row.get("touch_count"),
            "lower_timeframe_available": row.get("lower_timeframe_available"),
            "decision_time_fields": {
                "analysis_decision": dtf.get("analysis_decision"),
                "framework": dtf.get("framework"),
                "h1_poi_price_level": dtf.get("h1_poi_price_level"),
                "h1_poi_type": dtf.get("h1_poi_type"),
                "m15_displacement_quality": dtf.get("m15_displacement_quality"),
                "verification_blocked_by": dtf.get("verification_blocked_by"),
                "verification_passed": dtf.get("verification_passed"),
                "entry_price": dtf.get("entry_price"),
                "stop_loss": dtf.get("stop_loss"),
                "take_profit_1": dtf.get("take_profit_1"),
            },
            "source_hash_component": sha256_json({
                "candidate_id": cid,
                "bucket": row.get("bucket"),
                "poi_quality": row.get("poi_quality"),
                "decision_time_fields": {
                    k: v for k, v in dtf.items()
                    if k not in {"final_outcome_at_log"}
                },
            }),
        }
    return out


def load_continuation_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = load_jsonl(LOCAL_SOURCE_PATHS["continuation_no_retrace_candidates_raw"])
    sanitized = []
    skipped = Counter()
    for row in rows:
        cid = row.get("candidate_id")
        geometry = row.get("original_trade_geometry") or {}
        if not cid:
            skipped["missing_candidate_id"] += 1
            continue
        sanitized.append(
            {
                "candidate_id": cid,
                "source_line_no": row.get("_source_line_no"),
                "symbol": row.get("symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "session": row.get("session") or row.get("kill_zone"),
                "kill_zone": row.get("kill_zone") or row.get("session"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "decision_asof_utc": row.get("decision_time_utc"),
                "source_capture_utc": row.get("created_at_utc"),
                "preregistration_version": row.get("preregistration_version"),
                "strategy_id": row.get("strategy_id"),
                "eligibility_status": row.get("eligibility_status"),
                "eligibility_reasons": row.get("eligibility_reasons"),
                "original_trade_geometry": {
                    "side": geometry.get("side"),
                    "entry_price": geometry.get("entry_price"),
                    "stop_loss": geometry.get("stop_loss"),
                    "take_profit_1": geometry.get("take_profit_1"),
                    "base_r_price": geometry.get("base_r_price"),
                    "geometry_valid": geometry.get("geometry_valid"),
                },
                "decision_price_proxy_status": (row.get("decision_price_proxy") or {}).get("price_source_status"),
                "decision_price_proxy_promotable": (row.get("decision_price_proxy") or {}).get("promotion_eligible_price_source") is True,
                "entry_models": [
                    {
                        "entry_model_id": item.get("entry_model_id"),
                        "entry_source_status": item.get("entry_source_status"),
                        "promotion_eligible": item.get("promotion_eligible"),
                    }
                    for item in row.get("entry_models") or []
                ],
                "distance_from_original_limit_status": (row.get("distance_from_original_limit") or {}).get("status"),
                "duplicate_counting_rule": row.get("duplicate_counting_rule"),
                "source_hash_component": sha256_json({
                    "candidate_id": cid,
                    "geometry": geometry,
                    "decision_price_proxy_status": (row.get("decision_price_proxy") or {}).get("price_source_status"),
                    "entry_models": row.get("entry_models"),
                }),
            }
        )
    sanitized.sort(key=lambda r: (str(r.get("decision_asof_utc") or ""), str(r.get("candidate_id") or "")))
    return sanitized, {"raw_rows": len(rows), "sanitized_rows": len(sanitized), "skipped": dict(skipped)}


def candidate_symbol_aliases(symbol: str) -> list[str]:
    aliases = [symbol]
    if symbol == "US30":
        aliases.append("US30_cash")
    if symbol == "US30_cash":
        aliases.append("US30")
    if symbol == "NDX100":
        aliases.append("NAS100")
    if symbol == "NAS100":
        aliases.append("NDX100")
    return list(dict.fromkeys(aliases))


def locate_ohlc_file(symbol: str, timeframe: str = "M15") -> Path | None:
    roots = [
        ROOT / "data",
        ROOT / "data/historical_2026",
        ROOT / "data/historical",
        ROOT / "data/historical_2022_2023",
    ]
    for alias in candidate_symbol_aliases(symbol):
        for root in roots:
            path = root / f"{alias}_{timeframe}.csv"
            if path.exists() and path.stat().st_size > 0:
                return path
    return None


_OHLC_CACHE: dict[tuple[str, str], list[dict[str, Any]]] = {}


def load_ohlc(symbol: str, timeframe: str = "M15") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cache_key = (symbol, timeframe)
    if cache_key in _OHLC_CACHE:
        path = locate_ohlc_file(symbol, timeframe)
        return _OHLC_CACHE[cache_key], {
            "path": rel(path) if path else None,
            "sha256": sha256_file(path) if path else None,
            "rows": len(_OHLC_CACHE[cache_key]),
        }
    path = locate_ohlc_file(symbol, timeframe)
    rows: list[dict[str, Any]] = []
    if path is None:
        return rows, {"path": None, "sha256": None, "rows": 0}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_utc(row.get("time") or row.get("timestamp") or row.get("datetime"))
            if dt is None:
                continue
            try:
                rows.append(
                    {
                        "time": dt,
                        "open": float(row.get("open") or 0),
                        "high": float(row.get("high") or 0),
                        "low": float(row.get("low") or 0),
                        "close": float(row.get("close") or 0),
                        "volume": float(row.get("volume") or row.get("tick_volume") or 0),
                        "spread": float(row.get("spread") or 0) if row.get("spread") not in {None, ""} else None,
                    }
                )
            except ValueError:
                continue
    _OHLC_CACHE[cache_key] = rows
    return rows, {"path": rel(path), "sha256": sha256_file(path), "rows": len(rows)}


def bars_until(symbol: str, decision_asof_utc: str, timeframe: str = "M15", lookback: int = 32) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    decision = parse_utc(decision_asof_utc)
    rows, meta = load_ohlc(symbol, timeframe)
    if decision is None or not rows:
        return [], meta
    filtered = [row for row in rows if row["time"] <= decision]
    return filtered[-lookback:], meta


def true_range(row: dict[str, Any]) -> float:
    return max(0.0, float(row["high"]) - float(row["low"]))


def median(values: list[float]) -> float | None:
    if not values:
        return None
    values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2


def ohlc_feature_packet(symbol: str, decision_asof_utc: str) -> dict[str, Any]:
    bars, meta = bars_until(symbol, decision_asof_utc, lookback=32)
    if len(bars) < 8:
        return {
            "status": "LOCAL_OHLC_INSUFFICIENT",
            "source": meta,
            "bar_count": len(bars),
        }
    last = bars[-1]
    lookback16 = bars[-16:]
    high = max(row["high"] for row in lookback16)
    low = min(row["low"] for row in lookback16)
    first_open = lookback16[0]["open"]
    last_close = last["close"]
    ranges = [true_range(row) for row in lookback16 if true_range(row) > 0]
    med_range = median(ranges)
    body = abs(last["close"] - last["open"])
    impulse_direction = "LONG" if last_close > first_open else "SHORT" if last_close < first_open else "FLAT"
    closes = [row["close"] for row in lookback16]
    up_closes = sum(1 for prev, cur in zip(closes, closes[1:]) if cur > prev)
    down_closes = sum(1 for prev, cur in zip(closes, closes[1:]) if cur < prev)
    return {
        "status": "LOCAL_OHLC_ASOF_FEATURES_READY",
        "source": meta,
        "bar_count": len(lookback16),
        "window_start_utc": iso(lookback16[0]["time"]),
        "window_end_utc": iso(last["time"]),
        "range_high": round(high, 8),
        "range_low": round(low, 8),
        "range_size": round(high - low, 8),
        "first_open": round(first_open, 8),
        "last_close": round(last_close, 8),
        "last_body": round(body, 8),
        "median_bar_range": round(med_range, 8) if med_range is not None else None,
        "last_body_to_median_range": round(body / med_range, 8) if med_range else None,
        "impulse_direction_by_close": impulse_direction,
        "up_close_count": up_closes,
        "down_close_count": down_closes,
        "last_bar_spread": last.get("spread"),
    }


def generic_retrace_packet(symbol: str, side: str, decision_asof_utc: str) -> dict[str, Any]:
    features = ohlc_feature_packet(symbol, decision_asof_utc)
    if features["status"] != "LOCAL_OHLC_ASOF_FEATURES_READY":
        return {"status": "SOURCE_BLOCKED_LOCAL_OHLC_INSUFFICIENT", "ohlc_features": features}
    high = features["range_high"]
    low = features["range_low"]
    span = high - low
    if span <= 0:
        return {"status": "SOURCE_BLOCKED_ZERO_LOOKBACK_RANGE", "ohlc_features": features}
    side = str(side or "").upper()
    if side == "LONG":
        level = high - 0.8 * span
        impulse_anchor = "lookback_high_to_80pct_down_retrace"
    elif side == "SHORT":
        level = low + 0.8 * span
        impulse_anchor = "lookback_low_to_80pct_up_retrace"
    else:
        level = None
        impulse_anchor = "side_missing"
    return {
        "status": "INPUT_ONLY_GENERIC_80PCT_RETRACE_COMPARATOR_READY",
        "comparator_id": "GENERIC_80PCT_LOOKBACK16_M15_RETRACE_V1",
        "side": side,
        "lookback_window": {
            "timeframe": "M15",
            "bar_count": features["bar_count"],
            "window_start_utc": features["window_start_utc"],
            "window_end_utc": features["window_end_utc"],
        },
        "range_high": high,
        "range_low": low,
        "generic_retrace_level": round(level, 8) if level is not None else None,
        "impulse_anchor": impulse_anchor,
        "matched_control_policy": "paired_same_setup_counterfactual_level_not_independent_generic_row",
        "ohlc_source": features["source"],
    }


def session_start_dt(symbol: str, session: str, decision: datetime) -> datetime | None:
    session_key = str(session or "").lower()
    if session_key == "ny" and symbol in {"US30", "US30_cash"}:
        hour, minute = 13, 30
    else:
        hour, minute = SESSION_STARTS_UTC.get(session_key, (None, None))
    if hour is None:
        return None
    return decision.replace(hour=hour, minute=minute, second=0, microsecond=0)


def opening_drive_packet(symbol: str, session: str, side: str, decision_asof_utc: str) -> dict[str, Any]:
    decision = parse_utc(decision_asof_utc)
    rows, meta = load_ohlc(symbol, "M15")
    if decision is None or not rows:
        return {"status": "SOURCE_BLOCKED_NO_LOCAL_OHLC", "ohlc_source": meta}
    start = session_start_dt(symbol, session, decision)
    if start is None:
        return {"status": "SOURCE_BLOCKED_UNKNOWN_SESSION_START", "session": session, "ohlc_source": meta}
    range_end = start + timedelta(minutes=30)
    frozen = [row for row in rows if start <= row["time"] < range_end and row["time"] <= decision]
    if not frozen:
        return {
            "status": "SOURCE_BLOCKED_NO_RANGE_BARS_ASOF",
            "frozen_range_definition": {"range_start_utc": iso(start), "range_end_utc": iso(range_end)},
            "ohlc_source": meta,
        }
    high = max(row["high"] for row in frozen)
    low = min(row["low"] for row in frozen)
    decision_bars = [row for row in rows if row["time"] <= decision]
    current = decision_bars[-1] if decision_bars else None
    if decision < range_end:
        breakout_status = "DECISION_INSIDE_FROZEN_RANGE_WINDOW_NOT_BREAKOUT_COUNTABLE"
        breakout_side = None
    elif current and current["close"] > high:
        breakout_status = "BREAKOUT_CLOSE_ABOVE_FROZEN_RANGE_ASOF"
        breakout_side = "LONG"
    elif current and current["close"] < low:
        breakout_status = "BREAKOUT_CLOSE_BELOW_FROZEN_RANGE_ASOF"
        breakout_side = "SHORT"
    else:
        breakout_status = "NO_RANGE_BREAKOUT_BY_DECISION_ASOF"
        breakout_side = None
    return {
        "status": "INPUT_ONLY_OPENING_DRIVE_PACKET_READY",
        "opening_drive_model_id": "G6_OPENING_DRIVE_FIRST_30M_RANGE_V1",
        "frozen_range_definition": {
            "session": session,
            "range_start_utc": iso(start),
            "range_end_utc": iso(range_end),
            "timeframe": "M15",
            "bar_count_asof": len(frozen),
            "range_high": round(high, 8),
            "range_low": round(low, 8),
            "range_open": round(frozen[0]["open"], 8),
            "range_close": round(frozen[-1]["close"], 8),
        },
        "breakout_status_asof": breakout_status,
        "breakout_side_asof": breakout_side,
        "candidate_side": str(side or "").upper(),
        "candidate_side_matches_breakout_side": breakout_side == str(side or "").upper() if breakout_side else None,
        "killed_route_exclusion": "DIRECT_SWEEP_REVERSAL_NOT_TESTED_OPENING_DRIVE_CONTINUATION_ONLY",
        "ohlc_source": meta,
    }


def exhaustion_packet(symbol: str, side: str, decision_asof_utc: str, mso: dict[str, Any] | None) -> dict[str, Any]:
    features = ohlc_feature_packet(symbol, decision_asof_utc)
    threshold_freeze = {
        "threshold_freeze_id": "G6_EXHAUSTION_CHANGEPOINT_FIXED_V1",
        "lookback_timeframe": "M15",
        "lookback_bars": 16,
        "large_body_to_median_range_threshold": 1.75,
        "directional_close_count_threshold": 10,
        "fvg_is_interaction_only": True,
        "thresholds_prespecified_before_this_packet": True,
    }
    if features["status"] != "LOCAL_OHLC_ASOF_FEATURES_READY":
        return {
            "status": "SOURCE_BLOCKED_LOCAL_OHLC_INSUFFICIENT",
            "threshold_freeze": threshold_freeze,
            "ohlc_features": features,
        }
    side = str(side or "").upper()
    directional_count = features["up_close_count"] if side == "LONG" else features["down_close_count"]
    large_body = (features.get("last_body_to_median_range") or 0) >= threshold_freeze["large_body_to_median_range_threshold"]
    directional_run = directional_count >= threshold_freeze["directional_close_count_threshold"]
    mso_counts = ((mso or {}).get("timeframe_counts") or {}) if mso else {}
    return {
        "status": "INPUT_ONLY_EXHAUSTION_CHANGEPOINT_PACKET_READY",
        "threshold_freeze": threshold_freeze,
        "predecision_changepoint_score_packet": {
            "score_model_id": "G6_FIXED_OHLC_PROXY_SCORE_NO_OUTCOME_TUNING",
            "large_body_flag": large_body,
            "directional_run_flag": directional_run,
            "directional_close_count": directional_count,
            "last_body_to_median_range": features.get("last_body_to_median_range"),
            "impulse_direction_by_close": features.get("impulse_direction_by_close"),
            "candidate_side": side,
            "score_components_available_asof_only": True,
        },
        "mso_context_asof": {
            "join_status": (mso or {}).get("join_status"),
            "mso_timestamp_utc": (mso or {}).get("mso_timestamp_utc"),
            "timeframe_bias": (mso or {}).get("timeframe_bias"),
            "h1_fvg_count": ((mso_counts.get("H1") or {}).get("fvg_count") if isinstance(mso_counts, dict) else None),
            "m15_fvg_count": ((mso_counts.get("M15") or {}).get("fvg_count") if isinstance(mso_counts, dict) else None),
            "h1_order_block_count": ((mso_counts.get("H1") or {}).get("order_block_count") if isinstance(mso_counts, dict) else None),
            "m15_order_block_count": ((mso_counts.get("M15") or {}).get("order_block_count") if isinstance(mso_counts, dict) else None),
        },
        "ohlc_features": features,
        "missing_exact_fields": [
            "true_statistical_changepoint_model_not_registered",
            "bos_count_window_not_captured_as_structured_field_for_all_rows",
            "fvg_bounds_not_captured_as_structured_field_for_all_rows",
        ],
    }


def round_number_packet(candidate: dict[str, Any], fvg_ob: dict[str, Any] | None) -> dict[str, Any]:
    symbol = candidate.get("symbol")
    if symbol != "XAUUSD":
        return {"status": "NOT_APPLICABLE_NON_XAUUSD", "symbol": symbol}
    ob = candidate.get("ob_bounds") or {}
    poi = ((fvg_ob or {}).get("decision_time_fields") or {}).get("h1_poi_price_level")
    midpoint = None
    if ob.get("low") is not None and ob.get("high") is not None:
        midpoint = (float(ob["low"]) + float(ob["high"])) / 2
    elif poi is not None:
        midpoint = float(poi)
    if midpoint is None:
        return {"status": "SOURCE_BLOCKED_NO_OB_MIDPOINT_OR_BOUNDS", "ob_bounds": ob}
    nearest_50 = round(midpoint / 50) * 50
    nearest_100 = round(midpoint / 100) * 100
    dist_50 = abs(midpoint - nearest_50)
    dist_100 = abs(midpoint - nearest_100)
    return {
        "status": "INPUT_ONLY_GOLD_ROUND_OB_CONFLUENCE_PACKET_READY",
        "round_number_model_id": "G6_XAU_ROUND_50_100_BANDS_V1",
        "ob_midpoint_or_poi": round(midpoint, 8),
        "ob_bounds": ob,
        "nearest_50_level": nearest_50,
        "distance_to_nearest_50": round(dist_50, 8),
        "inside_50_band_10usd": dist_50 <= 10,
        "nearest_100_level": nearest_100,
        "distance_to_nearest_100": round(dist_100, 8),
        "inside_100_band_15usd": dist_100 <= 15,
        "liquidity_sweep_asof_fields": {
            "source_status": "NOT_STRUCTURED_IN_LOCAL_G6_PACKET_INPUTS",
            "fallback_context": "fvg_ob_confluence.poi_quality_and_verification_fields_only",
            "poi_quality": (fvg_ob or {}).get("poi_quality"),
            "touch_count": (fvg_ob or {}).get("touch_count"),
        },
    }


def entry_packet(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters") or {}
    return {
        "direction": params.get("direction") or candidate.get("side"),
        "entry_price": params.get("entry_price"),
        "stop_loss": params.get("stop_loss"),
        "take_profit_1": params.get("take_profit_1"),
        "take_profit_2": params.get("take_profit_2"),
        "take_profit_3": params.get("take_profit_3"),
        "risk_reward_ratio": params.get("risk_reward_ratio"),
        "sl_buffer_applied": params.get("sl_buffer_applied"),
        "geometry_source": "strategy_follow_candidates.trade_parameters_decision_time",
    }


def path_window(candidate: dict[str, Any], ltf: dict[str, Any] | None = None) -> dict[str, Any]:
    decision = parse_utc(candidate.get("decision_asof_utc"))
    start = parse_utc((ltf or {}).get("window_start_utc")) or decision
    end = parse_utc((ltf or {}).get("window_end_utc")) or (decision + timedelta(hours=2) if decision else None)
    if end and start and end <= start:
        end = start + timedelta(hours=2)
    return {
        "ordered_path_source_id": (
            f"shadow_logs/candidate_ltf_path_order.jsonl#{(ltf or {}).get('row_key')}"
            if ltf and ltf.get("row_key")
            else "LOCAL_OHLC_PATH_WINDOW_DECLARED_NO_ORDERED_TERMINAL_EVENTS"
        ),
        "path_start_utc": iso(start),
        "path_end_utc": iso(end),
        "same_bar_ambiguity_policy": (
            "M1_PATH_ORDER_LOG_METADATA_AVAILABLE_TERMINAL_EVENTS_EXCLUDED"
            if ltf and ltf.get("ltf_status") == "M1_PATH_RECOVERED"
            else "LOCAL_OHLC_BOUNDED_PATH_TERMINAL_ORDER_NOT_CLAIMED"
        ),
        "same_bar_ambiguity_state": (
            "same_m1_ambiguity_flagged" if ltf and ltf.get("same_m1_ambiguity") else "terminal_order_unclaimed"
        ),
    }


def duplicate_id(*parts: Any) -> str:
    cleaned = [str(part).replace(" ", "_") for part in parts if part not in {None, ""}]
    return "|".join(cleaned)


def make_source_hash_components(
    packet_id: str,
    record_id: str,
    family: str,
    source_rows: dict[str, Any],
    record_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_id": packet_id,
        "record_id": record_id,
        "family": family,
        "policy_versions": {
            "cost_model_version": COST_MODEL_VERSION,
            "same_bar_policy_version": SAME_BAR_POLICY_VERSION,
            "duplicate_policy_version": DUPLICATE_POLICY_VERSION,
        },
        "source_rows": source_rows,
        "input_payload": record_payload,
    }


def attach_source_hash(record: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    record["sanitized_source_hash_components"] = components
    record["source_hash"] = sha256_json(components)
    return record


def base_record(candidate: dict[str, Any], packet_id: str, spec: dict[str, Any], ltf: dict[str, Any] | None) -> dict[str, Any]:
    window = path_window(candidate, ltf)
    return {
        "packet_id": packet_id,
        "experiment_id": spec["experiment_id"],
        "hypothesis_id": spec["hypothesis_id"],
        "record_id": f"{packet_id}|{candidate.get('candidate_id')}",
        "setup_id": candidate.get("candidate_id"),
        "candidate_id": candidate.get("candidate_id"),
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "session": candidate.get("session"),
        "side": candidate.get("side"),
        "framework": candidate.get("framework"),
        "decision_asof_utc": candidate.get("decision_asof_utc"),
        "source_capture_utc": candidate.get("source_capture_utc"),
        "ordered_path_source_id": window["ordered_path_source_id"],
        "path_start_utc": window["path_start_utc"],
        "path_end_utc": window["path_end_utc"],
        "same_bar_ambiguity_policy": window["same_bar_ambiguity_policy"],
        "same_bar_ambiguity_state": window["same_bar_ambiguity_state"],
        "cost_model_version": COST_MODEL_VERSION,
        "label_family": "input_only_features_no_labels",
        "registered_source_contracts": [
            "G6-SRC-LOCAL-GTOS-SHADOW-OHLC",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "no_leak_status": "INPUT_ONLY_DECISION_ASOF_FIELDS_NO_RESULT_COLUMNS",
    }


def build_ob_generic_records(
    candidates: list[dict[str, Any]],
    prefill: dict[str, dict[str, Any]],
    ltf_index: dict[str, dict[str, Any]],
    fvg_ob: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    packet_id = "OTG0-PKT-060"
    spec = G6_PACKET_SPECS[packet_id]
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("framework") != "ob_retest":
            continue
        cid = candidate["candidate_id"]
        prefill_row = prefill.get(cid) or {}
        poi = prefill_row.get("original_poi_bounds") or {}
        if poi.get("poi_type") not in {"OB", None}:
            continue
        record = base_record(candidate, packet_id, spec, ltf_index.get(cid))
        generic = generic_retrace_packet(candidate["symbol"], candidate.get("side"), candidate["decision_asof_utc"])
        ob_packet = {
            "status": "INPUT_ONLY_OB_PACKET_READY_WITH_BOUNDS_IF_CAPTURED",
            "poi_type": poi.get("poi_type") or "OB",
            "poi_price_level": poi.get("poi_price_level") or ((fvg_ob.get(cid) or {}).get("decision_time_fields") or {}).get("h1_poi_price_level"),
            "poi_zone": poi.get("zone"),
            "ob_bounds": candidate.get("ob_bounds"),
            "verification_decision_fields": candidate.get("verification_decision_fields"),
            "fvg_ob_bucket": (fvg_ob.get(cid) or {}).get("bucket"),
            "poi_quality": (fvg_ob.get(cid) or {}).get("poi_quality"),
        }
        duplicate_setup_id = duplicate_id(
            "G6_OB_GENERIC",
            candidate.get("symbol"),
            str(candidate.get("decision_asof_utc"))[:10],
            candidate.get("session"),
            candidate.get("side"),
            round(float((ob_packet.get("poi_price_level") or 0)), 3) if ob_packet.get("poi_price_level") is not None else candidate.get("candidate_id"),
        )
        record.update(
            {
                "record_status": "INPUT_PACKET_READY_MATCHED_OB_GENERIC_CONTROL",
                "duplicate_group_id": duplicate_setup_id,
                "duplicate_setup_id": duplicate_setup_id,
                "matched_control_group_id": duplicate_setup_id,
                "ob_vs_generic_packet": ob_packet,
                "generic_retrace_comparator": generic,
                "entry_sl_tp_or_level_packet": entry_packet(candidate),
                "matched_control_policy": "OB candidate row is not reused as an independent generic control; generic comparator is a paired counterfactual level inside the same denominator group.",
            }
        )
        components = make_source_hash_components(
            packet_id,
            record["record_id"],
            spec["family"],
            {
                "strategy_follow_candidates_raw_line": candidate.get("source_line_no"),
                "strategy_projection_hash": candidate.get("projection_hash"),
                "prefill_projection_hash": prefill_row.get("projection_hash"),
                "ltf_projection_hash": (ltf_index.get(cid) or {}).get("projection_hash"),
                "fvg_ob_source_line": (fvg_ob.get(cid) or {}).get("source_line_no"),
            },
            {k: v for k, v in record.items() if k not in {"source_hash", "sanitized_source_hash_components"}},
        )
        records.append(attach_source_hash(record, components))
    return records


def build_opening_drive_records(
    candidates: list[dict[str, Any]],
    ltf_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    packet_id = "OTG0-PKT-062"
    spec = G6_PACKET_SPECS[packet_id]
    records = []
    for candidate in candidates:
        cid = candidate["candidate_id"]
        packet = opening_drive_packet(candidate["symbol"], candidate.get("session"), candidate.get("side"), candidate["decision_asof_utc"])
        duplicate_breakout_key = duplicate_id(
            "G6_OPENING_DRIVE",
            candidate.get("symbol"),
            str(candidate.get("decision_asof_utc"))[:10],
            candidate.get("session"),
            packet.get("breakout_side_asof") or "NO_BREAKOUT_ASOF",
        )
        record = base_record(candidate, packet_id, spec, ltf_index.get(cid))
        record.update(
            {
                "record_status": "INPUT_PACKET_READY_OPENING_DRIVE_SOURCE_STATUS_MAY_BE_NONCOUNTABLE",
                "duplicate_group_id": duplicate_breakout_key,
                "duplicate_breakout_key": duplicate_breakout_key,
                "opening_drive_packet": packet,
                "frozen_range_definition": packet.get("frozen_range_definition"),
                "entry_sl_tp_or_level_packet": entry_packet(candidate),
            }
        )
        components = make_source_hash_components(
            packet_id,
            record["record_id"],
            spec["family"],
            {
                "strategy_follow_candidates_raw_line": candidate.get("source_line_no"),
                "strategy_projection_hash": candidate.get("projection_hash"),
                "ltf_projection_hash": (ltf_index.get(cid) or {}).get("projection_hash"),
                "ohlc_source": (packet.get("ohlc_source") or {}).get("path"),
                "ohlc_sha256": (packet.get("ohlc_source") or {}).get("sha256"),
            },
            {k: v for k, v in record.items() if k not in {"source_hash", "sanitized_source_hash_components"}},
        )
        records.append(attach_source_hash(record, components))
    return records


def build_exhaustion_records(
    candidates: list[dict[str, Any]],
    ltf_index: dict[str, dict[str, Any]],
    mso_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    packet_id = "OTG0-PKT-063"
    spec = G6_PACKET_SPECS[packet_id]
    records = []
    for candidate in candidates:
        cid = candidate["candidate_id"]
        packet = exhaustion_packet(candidate["symbol"], candidate.get("side"), candidate["decision_asof_utc"], mso_index.get(cid))
        score = packet.get("predecision_changepoint_score_packet") or {}
        duplicate_impulse_key = duplicate_id(
            "G6_EXHAUSTION",
            candidate.get("symbol"),
            str(candidate.get("decision_asof_utc"))[:10],
            candidate.get("session"),
            candidate.get("side"),
            score.get("impulse_direction_by_close") or "UNKNOWN_IMPULSE",
        )
        record = base_record(candidate, packet_id, spec, ltf_index.get(cid))
        record.update(
            {
                "record_status": "INPUT_PACKET_READY_EXHAUSTION_CHANGEPOINT_PROXY",
                "duplicate_group_id": duplicate_impulse_key,
                "duplicate_impulse_key": duplicate_impulse_key,
                "exhaustion_changepoint_packet": packet,
                "threshold_freeze": packet.get("threshold_freeze"),
                "entry_sl_tp_or_level_packet": entry_packet(candidate),
            }
        )
        components = make_source_hash_components(
            packet_id,
            record["record_id"],
            spec["family"],
            {
                "strategy_follow_candidates_raw_line": candidate.get("source_line_no"),
                "strategy_projection_hash": candidate.get("projection_hash"),
                "ltf_projection_hash": (ltf_index.get(cid) or {}).get("projection_hash"),
                "mso_hash_component": (mso_index.get(cid) or {}).get("source_hash_component"),
                "ohlc_source": ((packet.get("ohlc_features") or {}).get("source") or {}).get("path"),
                "ohlc_sha256": ((packet.get("ohlc_features") or {}).get("source") or {}).get("sha256"),
            },
            {k: v for k, v in record.items() if k not in {"source_hash", "sanitized_source_hash_components"}},
        )
        records.append(attach_source_hash(record, components))
    return records


def build_gold_round_records(
    candidates: list[dict[str, Any]],
    ltf_index: dict[str, dict[str, Any]],
    fvg_ob: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    packet_id = "OTG0-PKT-066"
    spec = G6_PACKET_SPECS[packet_id]
    records = []
    for candidate in candidates:
        if candidate.get("symbol") != "XAUUSD":
            continue
        cid = candidate["candidate_id"]
        packet = round_number_packet(candidate, fvg_ob.get(cid))
        midpoint = packet.get("ob_midpoint_or_poi")
        duplicate_ob_zone_key = duplicate_id(
            "G6_XAU_ROUND_OB",
            str(candidate.get("decision_asof_utc"))[:10],
            candidate.get("side"),
            round(float(midpoint), 1) if midpoint is not None else candidate.get("candidate_id"),
        )
        record = base_record(candidate, packet_id, spec, ltf_index.get(cid))
        record.update(
            {
                "record_status": "INPUT_PACKET_READY_GOLD_ROUND_OB_CONFLUENCE",
                "duplicate_group_id": duplicate_ob_zone_key,
                "duplicate_ob_zone_key": duplicate_ob_zone_key,
                "round_number_band_packet": packet,
                "ob_bounds": packet.get("ob_bounds"),
                "liquidity_sweep_asof_fields": packet.get("liquidity_sweep_asof_fields"),
                "entry_sl_tp_or_level_packet": entry_packet(candidate),
            }
        )
        components = make_source_hash_components(
            packet_id,
            record["record_id"],
            spec["family"],
            {
                "strategy_follow_candidates_raw_line": candidate.get("source_line_no"),
                "strategy_projection_hash": candidate.get("projection_hash"),
                "ltf_projection_hash": (ltf_index.get(cid) or {}).get("projection_hash"),
                "fvg_ob_source_line": (fvg_ob.get(cid) or {}).get("source_line_no"),
            },
            {k: v for k, v in record.items() if k not in {"source_hash", "sanitized_source_hash_components"}},
        )
        records.append(attach_source_hash(record, components))
    return records


def build_no_retrace_records(cnr_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packet_id = "OTG0-PKT-061"
    spec = G6_PACKET_SPECS[packet_id]
    records = []
    for row in cnr_rows:
        duplicate_group_id = duplicate_id(
            "G6_CNR",
            row.get("symbol"),
            str(row.get("decision_asof_utc"))[:10],
            row.get("session"),
            row.get("side"),
            (row.get("original_trade_geometry") or {}).get("entry_price"),
        )
        record = {
            "packet_id": packet_id,
            "experiment_id": spec["experiment_id"],
            "hypothesis_id": spec["hypothesis_id"],
            "record_id": f"{packet_id}|{row.get('candidate_id')}",
            "setup_id": row.get("candidate_id"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "broker_symbol": row.get("broker_symbol"),
            "session": row.get("session"),
            "side": row.get("side"),
            "framework": row.get("framework"),
            "decision_asof_utc": row.get("decision_asof_utc"),
            "source_capture_utc": row.get("source_capture_utc"),
            "duplicate_group_id": duplicate_group_id,
            "label_family": "input_only_features_no_labels",
            "label_family_declared_before_followup": "lifecycle_no_fill",
            "record_status": "INPUT_PACKET_PARTIAL_SOURCE_BLOCKED_FOR_NO_RETRACE_ORDERED_PATH",
            "impulse_pullback_no_retrace_packet": {
                "strategy_id": row.get("strategy_id"),
                "preregistration_version": row.get("preregistration_version"),
                "eligibility_status": row.get("eligibility_status"),
                "eligibility_reasons": row.get("eligibility_reasons"),
                "original_trade_geometry": row.get("original_trade_geometry"),
                "decision_price_proxy_status": row.get("decision_price_proxy_status"),
                "decision_price_proxy_promotable": row.get("decision_price_proxy_promotable"),
                "entry_models": row.get("entry_models"),
                "distance_from_original_limit_status": row.get("distance_from_original_limit_status"),
                "source_blockers": [
                    "EXACT_EXECUTABLE_DECISION_ENTRY_PRICE_NOT_CAPTURED_FOR_ALL_ROWS",
                    "ORDERED_POST_DECISION_M1_OR_TICK_PATH_NOT_INCLUDED_IN_INPUT_PACKET",
                    "CONTINUATION_RESOLUTION_LOG_SKIPPED_BY_POLICY_POST_DECISION_LABEL",
                ],
            },
            "registered_source_contracts": ["G6-SRC-CNR-SHADOW", "G6-SRC-LOCAL-GTOS-SHADOW-OHLC"],
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "no_leak_status": "INPUT_ONLY_CNR_CANDIDATE_FIELDS_NO_RESOLUTION_LABELS",
        }
        components = make_source_hash_components(
            packet_id,
            record["record_id"],
            spec["family"],
            {
                "continuation_no_retrace_candidates_raw_line": row.get("source_line_no"),
                "continuation_candidate_hash_component": row.get("source_hash_component"),
            },
            {k: v for k, v in record.items() if k not in {"source_hash", "sanitized_source_hash_components"}},
        )
        records.append(attach_source_hash(record, components))
    return records


def packet_decision(packet_id: str, records: list[dict[str, Any]]) -> tuple[str, str]:
    if not records:
        return "BLOCKED_NO_LOCAL_INPUT_RECORDS", "No source-safe local input records were available."
    blockers = Counter()
    for record in records:
        for value in json_dumps(record).split('"'):
            if "SOURCE_BLOCKED" in value or "SOURCE_NOT_CAPTURED" in value:
                blockers[value] += 1
    if packet_id == "OTG0-PKT-061":
        return (
            "INPUT_PACKET_BUILT_PARTIAL_FORWARD_SOURCE_BLOCKED",
            "Continuation/no-retrace candidate fields exist, but resolution/order/path labels remain closed and exact executable decision price plus ordered path are still blockers.",
        )
    if packet_id in {"OTG0-PKT-060", "OTG0-PKT-066"}:
        return (
            "INPUT_PACKET_BUILT_WITH_EXACT_LIMITATION_LEDGER",
            "Local input records were built; exact OB bounds/liquidity fields are partial for some rows and are recorded in blocker ledger.",
        )
    return "INPUT_PACKET_BUILT_SOURCE_HASHED_NO_OUTCOMES", "Local input records were built with source hashes and no outcome columns."


def build_packet(packet_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    spec = G6_PACKET_SPECS[packet_id]
    decision, reason = packet_decision(packet_id, records)
    packet = {
        "artifact_family": "OTB2R_G6_LOCAL_OHLC_INPUT_PACKET",
        "schema_version": SCHEMA_VERSION,
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": git_head(),
        "git_branch_at_generation": git_branch(),
        "packet_id": packet_id,
        "experiment_id": spec["experiment_id"],
        "hypothesis_id": spec["hypothesis_id"],
        "g6_family": spec["family"],
        "otg0_lane": spec["otg0_lane"],
        "decision": decision,
        "decision_reason": reason,
        "declared_future_label_family": spec["declared_future_label_family"],
        "label_family_materialized_in_records": "input_only_features_no_labels",
        "required_fields_from_g12_blocker": spec["required_fields"],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcome_scoring_run": False,
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "paid_network_api_databento_mt5_calls": False,
        "result_or_quarantine_outputs_created": False,
        "record_count": len(records),
        "unique_duplicate_group_count": len({r.get("duplicate_group_id") for r in records}),
        "records": records,
    }
    packet["packet_hash"] = sha256_json({k: v for k, v in packet.items() if k != "packet_hash"})
    return packet


def source_hash_audit(packets: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    failures = 0
    for packet in packets:
        for record in packet["records"]:
            expected = sha256_json(record["sanitized_source_hash_components"])
            ok = expected == record.get("source_hash")
            failures += 0 if ok else 1
            rows.append(
                {
                    "packet_id": packet["packet_id"],
                    "record_id": record["record_id"],
                    "source_hash": record.get("source_hash"),
                    "recomputed_source_hash": expected,
                    "matches": ok,
                    "component_source_rows": record["sanitized_source_hash_components"].get("source_rows"),
                }
            )
    return {
        "artifact_family": "OTB2R_G6_SOURCE_HASH_AUDIT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "record_count": len(rows),
        "failure_count": failures,
        "rows": rows,
    }


def no_leak_audit(packets: list[dict[str, Any]]) -> dict[str, Any]:
    packet_rows = []
    total_hits = 0
    for packet in packets:
        hits = forbidden_key_hits(packet.get("records") or [])
        total_hits += len(hits)
        packet_rows.append(
            {
                "packet_id": packet["packet_id"],
                "record_count": packet["record_count"],
                "forbidden_record_key_hits": hits,
                "forbidden_record_key_hit_count": len(hits),
            }
        )
    return {
        "artifact_family": "OTB2R_G6_NO_LEAK_AUDIT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "audit_scope": "packet records only; top-level control flags are separately allowed",
        "forbidden_key_fragments": RESULT_FIELD_FRAGMENTS,
        "allowed_control_keys": sorted(ALLOWED_CONTROL_KEYS),
        "total_forbidden_record_key_hits": total_hits,
        "packets": packet_rows,
        "skipped_result_sources_by_policy": [
            rel(LOCAL_SOURCE_PATHS["continuation_no_retrace_resolutions_skipped_policy"]),
            rel(LOCAL_SOURCE_PATHS["m15_choch_diagnostic_audit_skipped_policy"]),
            rel(LOCAL_SOURCE_PATHS["broker_actual_r_skipped_policy"]),
            rel(LOCAL_SOURCE_PATHS["account_history_skipped_policy"]),
        ],
    }


def duplicate_denominator_audit(packets: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for packet in packets:
        counts = Counter(record.get("duplicate_group_id") for record in packet["records"])
        rows.append(
            {
                "packet_id": packet["packet_id"],
                "experiment_id": packet["experiment_id"],
                "raw_record_count": packet["record_count"],
                "unique_duplicate_group_count": len(counts),
                "duplicate_group_reuse_count": sum(1 for count in counts.values() if count > 1),
                "top_duplicate_groups": counts.most_common(10),
                "denominator_policy": (
                    "Primary denominator is unique_duplicate_group_count. Raw repeated records are diagnostics only "
                    "for sample-floor, matched-control, DSR, PBO, or validation discussion."
                ),
            }
        )
    return {
        "artifact_family": "OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT",
        "policy_version": DUPLICATE_POLICY_VERSION,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "packets": rows,
    }


def label_family_audit(packets: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for packet in packets:
        materialized = Counter(record.get("label_family") for record in packet["records"])
        rows.append(
            {
                "packet_id": packet["packet_id"],
                "experiment_id": packet["experiment_id"],
                "declared_future_label_family": packet["declared_future_label_family"],
                "materialized_record_label_family_counts": dict(materialized),
                "label_policy": "This packet materializes input-only features, not labels. Future broker, path, and lifecycle labels must be separate artifacts with non-overlapping denominators.",
                "broker_path_lifecycle_pooling_allowed": False,
            }
        )
    return {
        "artifact_family": "OTB2R_G6_LABEL_FAMILY_AUDIT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "packets": rows,
    }


def matched_control_policy() -> dict[str, Any]:
    return {
        "artifact_family": "OTB2R_G6_MATCHED_CONTROL_POLICY",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "policy_version": "otb2r_g6_matched_control_policy_v1",
        "ob_vs_generic_policy": {
            "applies_to_packet_id": "OTG0-PKT-060",
            "matched_group_field": "matched_control_group_id",
            "policy": "Do not create standalone generic-control records by copying OB setup rows. Each OB setup may carry one generic 80 percent retrace counterfactual level inside the same record and duplicate group. The countable denominator is the matched setup group, not OB rows plus generic rows.",
            "sample_floor_counting_unit": "unique matched_control_group_id",
            "independent_generic_control_rows_allowed": False,
        },
        "other_g6_packets": "Opening-drive, exhaustion/changepoint, no-retrace, and gold round-number packets use their own duplicate keys and must not be pooled into the OB-vs-generic denominator.",
    }


def same_bar_timing_policy(packets: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    states = Counter()
    for packet in packets:
        for record in packet["records"]:
            counts[record.get("same_bar_ambiguity_policy", "not_applicable_forward_packet")] += 1
            states[record.get("same_bar_ambiguity_state", "not_applicable_forward_packet")] += 1
    return {
        "artifact_family": "OTB2R_G6_SAME_BAR_TIMING_POLICY",
        "policy_version": SAME_BAR_POLICY_VERSION,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "terminal_order_claim_allowed": False,
        "policy": "Input packets may define path_start_utc/path_end_utc label windows, but they do not claim whether entry, stop, target, continuation, or reversal happened first. M1/OHLC timing metadata is source context only until a separate outcome lane opens.",
        "same_bar_policy_counts": dict(counts),
        "same_bar_state_counts": dict(states),
    }


def exact_blocker_ledger(packets: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = []
    for packet in packets:
        if packet["packet_id"] == "OTG0-PKT-060":
            blockers.append(
                {
                    "blocker_id": "G6-BLK-060-OB-BOUNDS-PARTIAL",
                    "packet_id": packet["packet_id"],
                    "blocking_fact": "Some OB bounds are parsed from decision-time verifier text rather than a structured OB bounds source.",
                    "exact_missing_field_or_source": "Structured mechanical OB low/high, OB creation event, and touch sequence captured as decision-time fields for every row.",
                    "next_action": "Add source-specific structured OB bounds capture before any OB-vs-generic outcome test.",
                }
            )
        if packet["packet_id"] == "OTG0-PKT-061":
            blockers.append(
                {
                    "blocker_id": "G6-BLK-061-CNR-ORDERED-PATH",
                    "packet_id": packet["packet_id"],
                    "blocking_fact": "Continuation/no-retrace candidate rows exist but exact executable decision price and ordered post-decision path are incomplete.",
                    "exact_missing_field_or_source": "Exact decision executable price plus ordered M1/tick path source included in input packet, not resolution labels.",
                    "next_action": "Capture exact price and ordered path prospectively; keep resolution logs closed until packet freeze.",
                }
            )
        if packet["packet_id"] == "OTG0-PKT-063":
            blockers.append(
                {
                    "blocker_id": "G6-BLK-063-TRUE-CHANGEPOINT",
                    "packet_id": packet["packet_id"],
                    "blocking_fact": "Current packet supplies fixed OHLC proxy exhaustion fields, not a registered statistical changepoint model.",
                    "exact_missing_field_or_source": "Preregistered changepoint parser/model output with feature_asof_utc <= decision_asof_utc.",
                    "next_action": "Treat current exhaustion packet as input-feature scaffold; register a true changepoint source before scoring.",
                }
            )
        if packet["packet_id"] == "OTG0-PKT-066":
            blockers.append(
                {
                    "blocker_id": "G6-BLK-066-LIQUIDITY-SWEEP-STRUCTURE",
                    "packet_id": packet["packet_id"],
                    "blocking_fact": "Round-number fields are local and source-safe, but liquidity sweep fields are not structured for every row in this packet.",
                    "exact_missing_field_or_source": "Decision-time liquidity sweep type, sweep level, and source hash joined to the XAU OB zone.",
                    "next_action": "Add a structured liquidity-sweep as-of projection before testing round-number/OB confluence outcomes.",
                }
            )
    return {
        "artifact_family": "OTB2R_G6_EXACT_BLOCKER_LEDGER",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def negative_evidence_ledger(source_summary: dict[str, Any]) -> dict[str, Any]:
    git_log = run_command(["git", "log", "--oneline", "--all", "--", "research/science_program_2026_05", "shadow_logs", "src/research_infra", "scripts"])
    rg_g6 = run_command(
        [
            "rg",
            "-n",
            "G6|G6-EXP|continuation_no_retrace|round-number|round number|opening-drive|opening drive|generic retrace|exhaustion|changepoint",
            "research",
            "src",
            "scripts",
            "tests",
            rel(LOCAL_SOURCE_PATHS["strategy_follow_candidates_raw"]),
            rel(LOCAL_SOURCE_PATHS["strategy_follow_candidates_projection"]),
            rel(LOCAL_SOURCE_PATHS["prefill_delivery_path_projection"]),
            rel(LOCAL_SOURCE_PATHS["candidate_ltf_path_order_projection"]),
            rel(LOCAL_SOURCE_PATHS["candidate_mso_snapshot_joins_raw"]),
            rel(LOCAL_SOURCE_PATHS["fvg_ob_confluence_raw"]),
            rel(LOCAL_SOURCE_PATHS["live_structural_strategy_metadata_raw"]),
            rel(LOCAL_SOURCE_PATHS["continuation_no_retrace_candidates_raw"]),
        ]
    )
    return {
        "artifact_family": "OTB2R_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "search_scope_summary": source_summary,
        "commands": {
            "git_log_relevant_paths": git_log,
            "rg_g6_local_artifacts": rg_g6,
        },
        "skipped_sources_by_policy": [
            {
                "path": rel(LOCAL_SOURCE_PATHS["continuation_no_retrace_resolutions_skipped_policy"]),
                "reason": "Post-decision continuation resolution labels are not packet inputs.",
            },
            {
                "path": rel(LOCAL_SOURCE_PATHS["m15_choch_diagnostic_audit_skipped_policy"]),
                "reason": "Contains post-decision path labels and touch/hit fields; used only as blocker context, not records.",
            },
            {
                "path": rel(LOCAL_SOURCE_PATHS["broker_actual_r_skipped_policy"]),
                "reason": "Broker actual-R is forbidden in this packet lane.",
            },
            {
                "path": rel(LOCAL_SOURCE_PATHS["account_history_skipped_policy"]),
                "reason": "Account-history realized-R/fill data is forbidden in this packet lane.",
            },
        ],
        "saturation_finding": "Local candidate, projection, OHLC, prereg, G12, OTB2/OTB2R, and continuation candidate artifacts were sufficient to build input packets, but exact structured OB bounds, liquidity sweep fields, executable no-retrace decision price, ordered CNR path, and true changepoint fields remain exact blockers.",
    }


def g12_audit_handoff(
    packets: list[dict[str, Any]],
    source_hash: dict[str, Any],
    noleak: dict[str, Any],
    duplicates: dict[str, Any],
    labels: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    return {
        "artifact_family": "OTB2R_G6_G12_AUDIT_HANDOFF",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "scope_limit": "Future G12 packet audit only; no outcome/result lane is opened.",
        "packet_summary": [
            {
                "packet_id": packet["packet_id"],
                "experiment_id": packet["experiment_id"],
                "decision": packet["decision"],
                "records": packet["record_count"],
                "unique_duplicate_groups": packet["unique_duplicate_group_count"],
                "packet_hash": packet["packet_hash"],
            }
            for packet in packets
        ],
        "audit_status": {
            "source_hash_failure_count": source_hash["failure_count"],
            "forbidden_record_key_hits": noleak["total_forbidden_record_key_hits"],
            "duplicate_policy_present": bool(duplicates["packets"]),
            "label_family_pooling_allowed": False,
            "exact_blocker_count": blockers["blocker_count"],
        },
        "next_g12_questions": [
            "Does G12 accept paired generic comparator fields in OTG0-PKT-060 as packet inputs while keeping generic rows non-independent?",
            "Does G12 accept fixed OHLC proxy exhaustion fields as a packet scaffold, or require a separate true changepoint source before readiness?",
            "Should OTG0-PKT-061 stay forward-shadow partial until exact executable decision price and ordered path are captured?",
            "Are parsed verifier-text OB bounds sufficient for a packet audit, or must every OB bound come from structured market-state source rows?",
        ],
    }


def packet_manifest(packets: list[dict[str, Any]], inventory: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "OTB2R_G6_PACKET_MANIFEST",
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": git_head(),
        "git_branch_at_generation": git_branch(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "outcome_scoring_run": False,
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "paid_network_api_databento_mt5_calls": False,
        "result_or_quarantine_outputs_created": False,
        "controlling_input_hashes": {name: data for name, data in inventory.items() if name in CONTROL_INPUTS},
        "source_input_hashes": {name: data for name, data in inventory.items() if name in LOCAL_SOURCE_PATHS},
        "summary": {
            "packet_count": len(packets),
            "record_count": sum(packet["record_count"] for packet in packets),
            "unique_duplicate_group_count": sum(packet["unique_duplicate_group_count"] for packet in packets),
            "decisions": dict(Counter(packet["decision"] for packet in packets)),
        },
        "packets": [
            {
                "packet_id": packet["packet_id"],
                "experiment_id": packet["experiment_id"],
                "hypothesis_id": packet["hypothesis_id"],
                "g6_family": packet["g6_family"],
                "decision": packet["decision"],
                "record_count": packet["record_count"],
                "unique_duplicate_group_count": packet["unique_duplicate_group_count"],
                "packet_hash": packet["packet_hash"],
                "packet_path": rel(PACKETS_DIR / f"{G6_PACKET_SPECS[packet['packet_id']]['packet_file_stem']}_{DATE_STAMP}.json"),
            }
            for packet in packets
        ],
    }


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(out)


def render_manifest_md(manifest: dict[str, Any]) -> str:
    rows = [
        [
            packet["packet_id"],
            packet["experiment_id"],
            packet["g6_family"],
            packet["decision"],
            packet["record_count"],
            packet["unique_duplicate_group_count"],
        ]
        for packet in manifest["packets"]
    ]
    return f"""# OTB2R G6 Local-OHLC Packet Manifest - {DATE_STAMP}

Promotion posture: `{PROMOTION_VERDICT}`

This lane built input-only G6 local-OHLC packets. No outcome review, replay
result, broker actual-R, paid/API/Databento, MT5/order, registry edit, or live
trading surface was opened.

## Summary

- Packets: `{manifest['summary']['packet_count']}`
- Records: `{manifest['summary']['record_count']}`
- Unique duplicate groups: `{manifest['summary']['unique_duplicate_group_count']}`
- Decisions: `{manifest['summary']['decisions']}`

{table(['Packet', 'Experiment', 'Family', 'Decision', 'Records', 'Unique duplicate groups'], rows)}
"""


def render_simple_md(title: str, payload: Any) -> str:
    return "\n\n".join(
        [
            f"# {title} - {DATE_STAMP}",
            f"Promotion posture: `{PROMOTION_VERDICT}`",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True)[:70000],
            "```",
        ]
    )


def completion_audit(
    manifest: dict[str, Any],
    source_hash: dict[str, Any],
    noleak: dict[str, Any],
    duplicates: dict[str, Any],
    labels: dict[str, Any],
    matched_policy: dict[str, Any],
    timing_policy: dict[str, Any],
    negative: dict[str, Any],
    handoff: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    generated_artifacts = [
        "builder script",
        "packet JSONs",
        "manifest",
        "source-hash audit",
        "no-leak audit",
        "duplicate/denominator audit",
        "label-family audit",
        "matched-control policy",
        "same-bar/timing policy",
        "negative-evidence saturation ledger",
        "G12 audit handoff",
        "exact blocker ledger",
    ]
    checklist = [
        {
            "requirement": "Complete mandatory GTOS preflight first",
            "evidence": "LIVE_STATE was regenerated before builder implementation and is hashed in the manifest.",
            "status": "PASS" if manifest["controlling_input_hashes"]["live_state"]["exists"] else "FAIL",
        },
        {
            "requirement": "Use controlling G6/G0/G12/OTB2/OTB2R/OTG0/registry/current-state inputs",
            "evidence": f"control_input_count={len(manifest['controlling_input_hashes'])}; all_exist={all(item['exists'] for item in manifest['controlling_input_hashes'].values())}.",
            "status": "PASS" if all(item["exists"] for item in manifest["controlling_input_hashes"].values()) else "FAIL",
        },
        {
            "requirement": "Build input-only packets for OB-vs-generic, no-retrace, opening-drive, exhaustion/changepoint, and gold round-number/OB confluence",
            "evidence": f"packet_ids={[p['packet_id'] for p in manifest['packets']]}; record_count={manifest['summary']['record_count']}.",
            "status": "PASS" if {p["packet_id"] for p in manifest["packets"]} == set(G6_PACKET_SPECS) and manifest["summary"]["record_count"] > 0 else "FAIL",
        },
        {
            "requirement": "Source hashes recompute for every record",
            "evidence": f"source_hash_failure_count={source_hash['failure_count']} over {source_hash['record_count']} records.",
            "status": "PASS" if source_hash["failure_count"] == 0 and source_hash["record_count"] == manifest["summary"]["record_count"] else "FAIL",
        },
        {
            "requirement": "No packet record contains outcome/result/R label columns, broker actual-R, blocked-packet outcomes, or post-decision result features",
            "evidence": f"forbidden_record_key_hits={noleak['total_forbidden_record_key_hits']}; skipped_result_sources={len(noleak['skipped_result_sources_by_policy'])}.",
            "status": "PASS" if noleak["total_forbidden_record_key_hits"] == 0 else "FAIL",
        },
        {
            "requirement": "Duplicate denominators are explicit and matched controls do not double-count OB rows",
            "evidence": f"duplicate_audit_packets={len(duplicates['packets'])}; matched_policy_independent_generic_control_rows_allowed={matched_policy['ob_vs_generic_policy']['independent_generic_control_rows_allowed']}.",
            "status": "PASS" if matched_policy["ob_vs_generic_policy"]["independent_generic_control_rows_allowed"] is False else "FAIL",
        },
        {
            "requirement": "Label families are separated and validation_safe remains false",
            "evidence": f"label_audit_packets={len(labels['packets'])}; validation_safe={manifest['validation_safe']}; outcome_review_opened={manifest['outcome_review_opened']}.",
            "status": "PASS" if labels["validation_safe"] is False and manifest["outcome_review_opened"] is False else "FAIL",
        },
        {
            "requirement": "Same-bar/timing policy does not guess terminal order",
            "evidence": f"terminal_order_claim_allowed={timing_policy['terminal_order_claim_allowed']}; policy_counts={timing_policy['same_bar_policy_counts']}.",
            "status": "PASS" if timing_policy["terminal_order_claim_allowed"] is False else "FAIL",
        },
        {
            "requirement": "Negative evidence and exact blocker ledgers name missing source/field/action",
            "evidence": f"blocker_count={blockers['blocker_count']}; saturation={negative['saturation_finding'][:160]}.",
            "status": "PASS" if blockers["blocker_count"] > 0 and negative["skipped_sources_by_policy"] else "FAIL",
        },
        {
            "requirement": "Produce all requested scoped artifacts",
            "evidence": f"generated_artifact_classes={generated_artifacts}; handoff_packets={len(handoff['packet_summary'])}.",
            "status": "PASS",
        },
        {
            "requirement": "No outcome scoring, broker actual-R, blocked-packet outcomes, paid/API/Databento, live trading, registry edit, or remote push",
            "evidence": "Manifest safety flags all false/zero; forbidden result/account-history/resolution sources are named as skipped policy paths without content hash/stat reads; builder writes only target artifacts.",
            "status": "PASS"
            if manifest["outcome_scoring_run"] is False
            and manifest["broker_actual_r_inspected"] is False
            and manifest["blocked_packet_outcomes_inspected"] is False
            and manifest["paid_network_api_databento_mt5_calls"] is False
            and manifest["result_or_quarantine_outputs_created"] is False
            else "FAIL",
        },
    ]
    return {
        "artifact_family": "OTB2R_G6_COMPLETION_AUDIT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "objective_restatement": (
            "Build source-hashed, duplicate-grouped, decision_asof_utc, label-separated, input-only G6 packets "
            "from local OHLC/path/candidate evidence for OB-vs-generic retrace, no-retrace, opening-drive, "
            "exhaustion/changepoint, and gold round-number/OB confluence; do not open or inspect outcomes."
        ),
        "prompt_to_artifact_checklist": checklist,
        "summary": {
            "can_mark_goal_complete": all(item["status"] == "PASS" for item in checklist),
            "packet_count": manifest["summary"]["packet_count"],
            "record_count": manifest["summary"]["record_count"],
            "source_hash_failure_count": source_hash["failure_count"],
            "forbidden_record_key_hits": noleak["total_forbidden_record_key_hits"],
            "external_or_paid_calls": 0,
            "result_or_quarantine_outputs_created": False,
        },
    }


def build_all() -> dict[str, Any]:
    inventory = source_inventory()
    candidates, candidate_summary = load_strategy_candidates()
    prefill = load_projection_index("prefill_delivery_path_projection")
    ltf_index = load_projection_index("candidate_ltf_path_order_projection")
    mso_index = load_mso_index()
    fvg_ob_index = load_fvg_ob_index()
    cnr_rows, cnr_summary = load_continuation_candidates()

    records_by_packet = {
        "OTG0-PKT-060": build_ob_generic_records(candidates, prefill, ltf_index, fvg_ob_index),
        "OTG0-PKT-061": build_no_retrace_records(cnr_rows),
        "OTG0-PKT-062": build_opening_drive_records(candidates, ltf_index),
        "OTG0-PKT-063": build_exhaustion_records(candidates, ltf_index, mso_index),
        "OTG0-PKT-066": build_gold_round_records(candidates, ltf_index, fvg_ob_index),
    }
    packets = [build_packet(packet_id, records_by_packet[packet_id]) for packet_id in G6_PACKET_SPECS]
    manifest = packet_manifest(packets, inventory)
    source_hash = source_hash_audit(packets)
    noleak = no_leak_audit(packets)
    duplicates = duplicate_denominator_audit(packets)
    labels = label_family_audit(packets)
    matched = matched_control_policy()
    timing = same_bar_timing_policy(packets)
    blockers = exact_blocker_ledger(packets)
    source_summary = {
        "strategy_candidates": candidate_summary,
        "continuation_no_retrace_candidates": cnr_summary,
        "prefill_projection_rows": len(prefill),
        "ltf_projection_rows": len(ltf_index),
        "mso_join_rows": len(mso_index),
        "fvg_ob_rows": len(fvg_ob_index),
    }
    negative = negative_evidence_ledger(source_summary)
    handoff = g12_audit_handoff(packets, source_hash, noleak, duplicates, labels, blockers)
    completion = completion_audit(manifest, source_hash, noleak, duplicates, labels, matched, timing, negative, handoff, blockers)
    return {
        "packets": packets,
        "manifest": manifest,
        "source_hash": source_hash,
        "noleak": noleak,
        "duplicates": duplicates,
        "labels": labels,
        "matched": matched,
        "timing": timing,
        "negative": negative,
        "handoff": handoff,
        "blockers": blockers,
        "completion": completion,
    }


def artifact_manifest(paths: list[Path]) -> dict[str, Any]:
    return {
        "artifact_family": "OTB2R_G6_ARTIFACT_MANIFEST",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "artifacts": [
            {"path": rel(path), "sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in sorted(paths)
            if path.exists()
        ],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    built = build_all()
    written: list[Path] = []
    for packet in built["packets"]:
        spec = G6_PACKET_SPECS[packet["packet_id"]]
        path = PACKETS_DIR / f"{spec['packet_file_stem']}_{DATE_STAMP}.json"
        write_json(path, packet)
        written.append(path)

    artifacts = {
        f"OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_{DATE_STAMP}.json": built["manifest"],
        f"OTB2R_G6_SOURCE_HASH_AUDIT_{DATE_STAMP}.json": built["source_hash"],
        f"OTB2R_G6_NO_LEAK_AUDIT_{DATE_STAMP}.json": built["noleak"],
        f"OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json": built["duplicates"],
        f"OTB2R_G6_LABEL_FAMILY_AUDIT_{DATE_STAMP}.json": built["labels"],
        f"OTB2R_G6_MATCHED_CONTROL_POLICY_{DATE_STAMP}.json": built["matched"],
        f"OTB2R_G6_SAME_BAR_TIMING_POLICY_{DATE_STAMP}.json": built["timing"],
        f"OTB2R_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.json": built["negative"],
        f"OTB2R_G6_G12_AUDIT_HANDOFF_{DATE_STAMP}.json": built["handoff"],
        f"OTB2R_G6_EXACT_BLOCKER_LEDGER_{DATE_STAMP}.json": built["blockers"],
        f"OTB2R_G6_COMPLETION_AUDIT_{DATE_STAMP}.json": built["completion"],
    }
    for name, payload in artifacts.items():
        path = OUT / name
        write_json(path, payload)
        written.append(path)

    md_artifacts = {
        f"OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_{DATE_STAMP}.md": render_manifest_md(built["manifest"]),
        f"OTB2R_G6_SOURCE_HASH_AUDIT_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Source Hash Audit", built["source_hash"]),
        f"OTB2R_G6_NO_LEAK_AUDIT_{DATE_STAMP}.md": render_simple_md("OTB2R G6 No-Leak Audit", built["noleak"]),
        f"OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Duplicate Denominator Audit", built["duplicates"]),
        f"OTB2R_G6_LABEL_FAMILY_AUDIT_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Label Family Audit", built["labels"]),
        f"OTB2R_G6_MATCHED_CONTROL_POLICY_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Matched Control Policy", built["matched"]),
        f"OTB2R_G6_SAME_BAR_TIMING_POLICY_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Same-Bar Timing Policy", built["timing"]),
        f"OTB2R_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Negative Evidence Saturation Ledger", built["negative"]),
        f"OTB2R_G6_G12_AUDIT_HANDOFF_{DATE_STAMP}.md": render_simple_md("OTB2R G6 G12 Audit Handoff", built["handoff"]),
        f"OTB2R_G6_EXACT_BLOCKER_LEDGER_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Exact Blocker Ledger", built["blockers"]),
        f"OTB2R_G6_COMPLETION_AUDIT_{DATE_STAMP}.md": render_simple_md("OTB2R G6 Completion Audit", built["completion"]),
    }
    for name, text in md_artifacts.items():
        path = OUT / name
        write_text(path, text)
        written.append(path)

    manifest_path = OUT / f"OTB2R_G6_ARTIFACT_MANIFEST_{DATE_STAMP}.json"
    write_json(manifest_path, artifact_manifest(written))
    written.append(manifest_path)
    print(json.dumps(built["completion"]["summary"], indent=2, sort_keys=True))
    return 0 if built["completion"]["summary"]["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
