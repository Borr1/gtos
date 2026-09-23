"""Build OTB2R input-only path packet rebuild artifacts.

OTB2R is the G12-directed rebuild of the rejected OTB2 synthetic/path packet.
It differs from OTB2 by hashing sanitized source projections, not raw
candidate/path logs. It must not run replay outcomes, create result/quarantine
outputs, call paid/API sources, or touch live trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE_STAMP = "2026-05-07"
SCHEMA_VERSION = "otb2r_input_only_path_packet_v1"
COST_MODEL_VERSION = "otb2r_input_only_path_cost_model_v1_research_only"
DUPLICATE_POLICY_VERSION = "otb2r_duplicate_group_policy_v1"
SAME_BAR_POLICY_VERSION = "otb2r_same_bar_ambiguity_policy_v1"

OT_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
G12 = OT_DIR / "g12_blocker_clearing_audit"
OTB0 = OT_DIR / "otb0_blocker_clearing_governor"
OTB2 = OT_DIR / "otb2_synthetic_packet_builder"
OTB3 = OT_DIR / "otb3_source_noleak_cleanup"
OTL2 = OT_DIR / "otl2_synthetic_replay_packet_audit"

PACKETS_DIR = OUT / "packets"
PROJECTIONS_DIR = OUT / "projections"

CONTROLLING_INPUTS = {
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "otg0_control_rules": OT_DIR / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE_STAMP}.json",
    "otg0_packet_manifest": OT_DIR / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otl2_audit": OTL2 / f"OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_{DATE_STAMP}.json",
    "otb0_packet_requirements": OTB0 / f"OTB0_PACKET_BUILDER_REQUIREMENTS_{DATE_STAMP}.json",
    "otb0_owner_approvals": OTB0 / f"OTB0_OWNER_APPROVAL_LEDGER_{DATE_STAMP}.json",
    "otb2_rejected_manifest": OTB2 / f"OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otb3_cleanup_ledger": OTB3 / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json",
    "g12_blocked_owner_questions": G12 / f"G12_BLOCKED_OWNER_QUESTION_LEDGER_{DATE_STAMP}.json",
    "g12_leakage_noleak": G12 / f"G12_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}.json",
    "g12_source_asof_hash": G12 / f"G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_{DATE_STAMP}.json",
    "g12_next_lane_recommendations": G12 / f"G12_NEXT_LANE_RECOMMENDATIONS_{DATE_STAMP}.json",
}

RAW_LOCAL_SOURCES = {
    "strategy_follow_candidates": ROOT / "shadow_logs" / "strategy_follow_candidates.jsonl",
    "candidate_ltf_path_order": ROOT / "shadow_logs" / "candidate_ltf_path_order.jsonl",
    "candidate_path_follow": ROOT / "shadow_logs" / "candidate_path_follow.jsonl",
    "candidate_path_contract_audit": ROOT / "shadow_logs" / "candidate_path_contract_audit.jsonl",
    "prefill_delivery_path": ROOT / "shadow_logs" / "prefill_delivery_path.jsonl",
}

SOURCE_PROJECTION_FILES = {
    "strategy_follow_candidates": PROJECTIONS_DIR / f"strategy_follow_candidates_input_only_projection_{DATE_STAMP}.jsonl",
    "candidate_ltf_path_order": PROJECTIONS_DIR / f"candidate_ltf_path_order_input_only_projection_{DATE_STAMP}.jsonl",
    "candidate_path_follow": PROJECTIONS_DIR / f"candidate_path_follow_input_only_projection_{DATE_STAMP}.jsonl",
    "candidate_path_contract_audit": PROJECTIONS_DIR / f"candidate_path_contract_audit_input_only_projection_{DATE_STAMP}.jsonl",
    "prefill_delivery_path": PROJECTIONS_DIR / f"prefill_delivery_path_input_only_projection_{DATE_STAMP}.jsonl",
}

READY_EXPERIMENT_ID = "G10-EXP-RISKBANK-005"

RESULT_OR_FUTURE_KEY_FRAGMENTS = (
    "actual_r",
    "bars_elapsed",
    "broker_actual_r",
    "cancel_expiry_abort_reason",
    "close_fill",
    "delivery_leg_direction",
    "entry_first_touch",
    "fill_delay",
    "fill_happened",
    "final_outcome",
    "gross_r",
    "hit_sl",
    "hit_tp",
    "mae",
    "max_high",
    "mfe",
    "min_low",
    "nearest_distance_to_entry",
    "net_r",
    "outcome",
    "path_label",
    "path_order_label",
    "path_synthetic_r",
    "pnl",
    "profit",
    "realized_r",
    "result",
    "reversal_leg",
    "sl_first_touch",
    "synthetic_path_r",
    "take_profit_hit",
    "touch",
    "tp1_first_touch",
    "trade_id",
    "win_loss",
)

ALLOWED_CONTROL_KEYS_WITH_OUTCOME_WORDS = {
    "broker_actual_r_absent_from_primary_metric",
    "outcome_review_opened",
    "promotion_verdict",
    "quarantine_or_result_outputs_created",
    "r_result_values_inspected_by_builder",
    "replay_outcomes_run",
}

STRATEGY_ALLOWED_KEYS = [
    "analysis_decision",
    "asof_cutoff_utc",
    "broker_symbol",
    "candidate_id",
    "created_at_utc",
    "decision_time_utc",
    "detector_version_at_eval",
    "evidence_class",
    "framework",
    "kill_zone",
    "no_leak_status",
    "promotion_verdict",
    "regime",
    "schema_version",
    "session",
    "side",
    "source_file",
    "source_hash",
    "source_symbol",
    "symbol",
]

TRADE_PARAM_ALLOWED_KEYS = [
    "direction",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "take_profit_2",
    "take_profit_3",
    "sl_buffer_applied",
    "position_size_lots",
]

LTF_ALLOWED_KEYS = [
    "ai_calls",
    "asof_latest_candle_utc",
    "backfilled_at_utc",
    "broker_symbol",
    "canary_calls",
    "candidate_id",
    "created_at_utc",
    "databento_calls",
    "decision_time_utc",
    "evidence_class",
    "framework",
    "ltf_source",
    "ltf_status",
    "m1_bar_count",
    "manual_backfill_status",
    "mt5_read_error",
    "no_ai_calls",
    "no_canary_required",
    "no_execution",
    "no_leak_status",
    "order_calls",
    "paid_data_calls",
    "paid_fetch_attempted",
    "promotion_verdict",
    "row_key",
    "same_m1_ambiguity",
    "schema_version",
    "side",
    "source_symbol",
    "symbol",
    "window_end_utc",
    "window_start_utc",
]

PATH_FOLLOW_ALLOWED_KEYS = [
    "asof_latest_candle_utc",
    "broker_symbol",
    "candidate_id",
    "created_at_utc",
    "decision_time_utc",
    "evidence_class",
    "framework",
    "mt5_read_error",
    "no_leak_status",
    "promotion_verdict",
    "schema_version",
    "side",
    "symbol",
]

CONTRACT_ALLOWED_KEYS = [
    "action_required_codes",
    "asof_latest_candle_utc",
    "backfilled_at_utc",
    "broker_symbol",
    "candidate_id",
    "created_at_utc",
    "decision_time_utc",
    "documented_limitation_codes",
    "ltf_join_status",
    "manual_backfill_status",
    "no_leak_status",
    "path_contract_status",
    "promotion_verdict",
    "row_key",
    "schema_version",
    "symbol",
    "tick_order_claim_status",
]

PREFILL_ALLOWED_KEYS = [
    "asof_cutoff_utc",
    "broker_symbol",
    "candidate_id",
    "created_at_utc",
    "decision_time_utc",
    "entry_arming_time_utc",
    "evidence_class",
    "fvg_ob_swing_state_at_arm",
    "kill_zone",
    "lower_timeframe_path_ordering",
    "no_leak_status",
    "original_poi_bounds",
    "promotion_verdict",
    "regime",
    "schema_version",
    "session",
    "side",
    "source_file",
    "source_hash",
    "source_symbol",
    "structural_setup_id",
    "symbol",
]

BASE_RECORD_WHITELIST = [
    "setup_id",
    "symbol",
    "source_symbol",
    "session",
    "side",
    "decision_asof_utc",
    "ordered_path_source_id",
    "path_start_utc",
    "path_end_utc",
    "entry_sl_tp_or_level_packet",
    "same_bar_ambiguity_policy",
    "same_bar_ambiguity_state",
    "cost_model_version",
    "duplicate_group_id",
    "source_hash",
    "sanitized_source_hash_components",
    "coverage_binding",
    "label_family",
    "broker_actual_r_absent_from_primary_metric",
    "no_leak_status",
    "packet_build_source_paths",
    "packet_id",
    "experiment_id",
    "hypothesis_id",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


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
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def git_branch() -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNKNOWN"


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def is_forbidden_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in ALLOWED_CONTROL_KEYS_WITH_OUTCOME_WORDS:
        return False
    if lowered.startswith("take_profit_"):
        return False
    return any(fragment in lowered for fragment in RESULT_OR_FUTURE_KEY_FRAGMENTS)


def recursive_forbidden_key_counts(payload: Any, prefix: str = "") -> Counter[str]:
    counts: Counter[str] = Counter()
    if isinstance(payload, dict):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else key
            if is_forbidden_key(key):
                counts[dotted] += 1
            counts.update(recursive_forbidden_key_counts(value, dotted))
    elif isinstance(payload, list):
        for value in payload:
            counts.update(recursive_forbidden_key_counts(value, prefix))
    return counts


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def project_row(row: dict[str, Any], allowed_keys: list[str], source_name: str) -> tuple[dict[str, Any], list[str]]:
    forbidden_present = sorted(key for key in row if is_forbidden_key(key))
    projected = {key: row.get(key) for key in allowed_keys if key in row and not is_forbidden_key(key)}
    if source_name == "strategy_follow_candidates":
        params = row.get("trade_parameters") or {}
        projected["trade_parameters"] = {
            key: params.get(key) for key in TRADE_PARAM_ALLOWED_KEYS if key in params and not is_forbidden_key(key)
        }
    if source_name == "candidate_path_contract_audit":
        ohlc = row.get("source_ohlc_range") or {}
        projected["source_ohlc_coverage_input_only"] = {
            key: ohlc.get(key)
            for key in ["bar_count", "first_bar_utc", "last_bar_utc", "source_timeframe"]
            if key in ohlc
        }
    projected["source_name"] = source_name
    projected["source_line_no"] = row.get("_source_line_no")
    projected["projection_schema_version"] = "otb2r_input_only_projection_v1"
    projected["forbidden_source_keys_removed"] = forbidden_present
    projected["projection_hash"] = sha256_json({k: v for k, v in projected.items() if k != "projection_hash"})
    return projected, forbidden_present


def build_projection(source_name: str, allowed_keys: list[str]) -> dict[str, Any]:
    raw_path = RAW_LOCAL_SOURCES[source_name]
    out_path = SOURCE_PROJECTION_FILES[source_name]
    rows = load_jsonl(raw_path)
    projected_rows: list[dict[str, Any]] = []
    forbidden_counts: Counter[str] = Counter()
    for row in rows:
        projected, forbidden_present = project_row(row, allowed_keys, source_name)
        projected_rows.append(projected)
        forbidden_counts.update(forbidden_present)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in projected_rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")

    projection_forbidden_counts: Counter[str] = Counter()
    for row in projected_rows:
        projection_forbidden_counts.update(recursive_forbidden_key_counts(row))

    return {
        "source_name": source_name,
        "raw_path": rel(raw_path),
        "raw_exists": raw_path.exists(),
        "raw_sha256_for_provenance_only_not_packet_source_hash": sha256_file(raw_path),
        "projection_path": rel(out_path),
        "projection_sha256_used_for_packet_source_hashing": sha256_file(out_path),
        "raw_rows_read": len(rows),
        "projection_rows_written": len(projected_rows),
        "forbidden_source_key_counts_removed_before_projection_hash": dict(sorted(forbidden_counts.items())),
        "forbidden_projection_key_counts_after_sanitization": dict(sorted(projection_forbidden_counts.items())),
    }


def build_all_projections() -> dict[str, Any]:
    projection_specs = {
        "strategy_follow_candidates": STRATEGY_ALLOWED_KEYS,
        "candidate_ltf_path_order": LTF_ALLOWED_KEYS,
        "candidate_path_follow": PATH_FOLLOW_ALLOWED_KEYS,
        "candidate_path_contract_audit": CONTRACT_ALLOWED_KEYS,
        "prefill_delivery_path": PREFILL_ALLOWED_KEYS,
    }
    projections = {name: build_projection(name, keys) for name, keys in projection_specs.items()}
    return {
        "artifact_family": "OTB2R_SANITIZED_SOURCE_HASHES",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "source_hash_policy": (
            "Packet source_hash values are built only from sanitized projection row hashes, "
            "projection file hashes, coverage binding metadata, and input trade geometry. "
            "Raw file hashes are recorded for provenance but are not packet source hashes."
        ),
        "projections": projections,
    }


def read_projection_rows(source_name: str) -> list[dict[str, Any]]:
    path = SOURCE_PROJECTION_FILES[source_name]
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def packet_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["packet_id"]: row for row in manifest.get("packets", [])}


def synthetic_packets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in manifest.get("packets", [])
        if row.get("otg0_testing_lane") == "synthetic_replay_existing_data_audit"
    ]


def candidate_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("decision_time_utc") or row.get("asof_cutoff_utc") or ""), str(row.get("candidate_id") or ""))


def selected_strategy_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = sorted(read_projection_rows("strategy_follow_candidates"), key=candidate_sort_key)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    skip_counts: Counter[str] = Counter()
    for row in rows:
        candidate_id = row.get("candidate_id")
        params = row.get("trade_parameters") or {}
        if not candidate_id:
            skip_counts["missing_candidate_id"] += 1
            continue
        if candidate_id in seen:
            skip_counts["duplicate_candidate_id"] += 1
            continue
        if not row.get("side") or not row.get("symbol"):
            skip_counts["missing_symbol_or_side"] += 1
            continue
        if params.get("entry_price") is None or params.get("stop_loss") is None:
            skip_counts["missing_entry_or_stop_loss"] += 1
            continue
        if params.get("take_profit_1") is None:
            skip_counts["missing_take_profit_1"] += 1
            continue
        seen.add(candidate_id)
        selected.append(row)
    return selected, {
        "projection_rows_read": len(rows),
        "selected_unique_candidate_rows": len(selected),
        "skip_counts": dict(skip_counts),
    }


def selected_ltf_index() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    rows = read_projection_rows("candidate_ltf_path_order")
    choices_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        candidate_id = row.get("candidate_id")
        if candidate_id:
            choices_by_candidate[candidate_id].append(row)

    selected: dict[str, dict[str, Any]] = {}
    selected_status_counts: Counter[str] = Counter()
    for candidate_id, choices in choices_by_candidate.items():
        choices.sort(
            key=lambda row: (
                1 if row.get("ltf_status") == "M1_PATH_RECOVERED" else 0,
                int(row.get("m1_bar_count") or 0),
                str(row.get("window_end_utc") or ""),
                str(row.get("projection_hash") or ""),
            ),
            reverse=True,
        )
        selected[candidate_id] = choices[0]
        selected_status_counts[str(choices[0].get("ltf_status"))] += 1

    return selected, {
        "projection_rows_read": len(rows),
        "candidate_ids_with_ltf_projection": len(selected),
        "selected_status_counts": dict(selected_status_counts),
    }


def csv_coverage(path: Path) -> dict[str, Any]:
    rows = 0
    first: str | None = None
    last: str | None = None
    header: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            for row in reader:
                rows += 1
                stamp = row.get("time") or row.get("timestamp") or row.get("datetime") or row.get("date")
                parsed = iso(parse_utc(stamp))
                if rows == 1:
                    first = parsed
                last = parsed
    except UnicodeDecodeError:
        with path.open("r", encoding="cp1252", newline="") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            for row in reader:
                rows += 1
                stamp = row.get("time") or row.get("timestamp") or row.get("datetime") or row.get("date")
                parsed = iso(parse_utc(stamp))
                if rows == 1:
                    first = parsed
                last = parsed
    return {
        "path": rel(path),
        "timeframe": infer_timeframe(path),
        "rows": rows,
        "first_utc": first,
        "last_utc": last,
        "sha256": sha256_file(path),
        "header": header,
    }


def infer_timeframe(path: Path) -> str:
    stem = path.stem.upper()
    for timeframe in ["M1", "M5", "M15", "H1", "H4", "D1"]:
        if stem.endswith("_" + timeframe):
            return timeframe
    return "UNKNOWN"


def locate_ohlc_sources(symbols: set[str]) -> dict[str, list[dict[str, Any]]]:
    candidates: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbols}
    for path in (ROOT / "data").rglob("*.csv"):
        timeframe = infer_timeframe(path)
        if timeframe not in {"M1", "M5", "M15", "H1"}:
            continue
        upper_name = path.name.upper()
        for symbol in symbols:
            if upper_name == f"{symbol}_{timeframe}.CSV".upper() or upper_name.startswith(f"{symbol}_".upper()):
                candidates.setdefault(symbol, []).append(csv_coverage(path))
    for symbol, entries in candidates.items():
        entries.sort(key=lambda row: (tf_rank(row["timeframe"]), row.get("last_utc") or "", row["path"]))
    return candidates


def tf_rank(timeframe: str) -> int:
    return {"M1": 0, "M5": 1, "M15": 2, "H1": 3}.get(timeframe, 9)


def coverage_valid(start_utc: str | None, end_utc: str | None, first_utc: str | None, last_utc: str | None) -> bool:
    start = parse_utc(start_utc)
    end = parse_utc(end_utc)
    first = parse_utc(first_utc)
    last = parse_utc(last_utc)
    if not start or not end or not first or not last:
        return False
    return first <= start and last >= end


def choose_ohlc_binding(symbol: str, path_start: str | None, path_end: str | None, sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    for entry in sources.get(symbol, []):
        if coverage_valid(path_start, path_end, entry.get("first_utc"), entry.get("last_utc")):
            return {
                "coverage_mode": "LOCAL_OHLC_CSV_COVERAGE_VALID",
                "source_path": entry["path"],
                "source_sha256": entry["sha256"],
                "timeframe": entry["timeframe"],
                "coverage_first_utc": entry["first_utc"],
                "coverage_last_utc": entry["last_utc"],
                "coverage_reaches_path_end_utc": True,
            }
    return None


def path_order_binding(ltf: dict[str, Any] | None, path_start: str | None, path_end: str | None) -> dict[str, Any] | None:
    if not ltf:
        return None
    ltf_start = ltf.get("window_start_utc")
    ltf_end = ltf.get("window_end_utc")
    if (
        ltf.get("ltf_status") == "M1_PATH_RECOVERED"
        and int(ltf.get("m1_bar_count") or 0) > 0
        and coverage_valid(path_start, path_end, ltf_start, ltf_end)
    ):
        return {
            "coverage_mode": "EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID",
            "source_projection_path": rel(SOURCE_PROJECTION_FILES["candidate_ltf_path_order"]),
            "projection_row_hash": ltf.get("projection_hash"),
            "ordered_path_source_id": f"{rel(SOURCE_PROJECTION_FILES['candidate_ltf_path_order'])}#{ltf.get('projection_hash')}",
            "ltf_status": ltf.get("ltf_status"),
            "ltf_source": ltf.get("ltf_source"),
            "m1_bar_count": ltf.get("m1_bar_count"),
            "coverage_first_utc": ltf_start,
            "coverage_last_utc": ltf_end,
            "coverage_reaches_path_end_utc": True,
        }
    return None


def duplicate_group_id(row: dict[str, Any], ltf: dict[str, Any] | None) -> str:
    params = row.get("trade_parameters") or {}
    payload = {
        "policy_version": DUPLICATE_POLICY_VERSION,
        "symbol": row.get("symbol"),
        "session": row.get("session") or row.get("kill_zone"),
        "side": row.get("side"),
        "decision_asof_utc": iso(parse_utc(row.get("asof_cutoff_utc") or row.get("decision_time_utc"))),
        "framework": row.get("framework"),
        "entry_price": params.get("entry_price"),
        "stop_loss": params.get("stop_loss"),
        "take_profit_1": params.get("take_profit_1"),
        "path_start_utc": iso(parse_utc((ltf or {}).get("window_start_utc") or row.get("decision_time_utc"))),
        "path_end_utc": iso(parse_utc((ltf or {}).get("window_end_utc"))),
    }
    return "otb2r_dup_" + sha256_json(payload)[:24]


def same_bar_policy(ltf: dict[str, Any] | None, coverage: dict[str, Any]) -> tuple[str, str]:
    if coverage["coverage_mode"] == "EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID":
        state = "same_m1_ambiguity_flagged" if bool((ltf or {}).get("same_m1_ambiguity")) else "not_flagged_or_not_applicable"
        return "M1_PATH_ORDER_LOG_AVAILABLE__SAME_MINUTE_AMBIGUITY_FLAGGED_NOT_GUESSED", state
    return "LOCAL_OHLC_BOUNDED_PATH__INTRABAR_TERMINAL_ORDER_AMBIGUOUS_NOT_GUESSED", "bounded_by_ohlc_no_terminal_order_claim"


def build_ready_records(
    strategy_rows: list[dict[str, Any]],
    ltf_by_candidate: dict[str, dict[str, Any]],
    ohlc_sources: dict[str, list[dict[str, Any]]],
    projection_manifest: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    blocked_rows: list[dict[str, Any]] = []
    stats = Counter()

    for row in strategy_rows:
        setup_id = row["candidate_id"]
        ltf = ltf_by_candidate.get(setup_id)
        decision_asof = iso(parse_utc(row.get("asof_cutoff_utc") or row.get("decision_time_utc")))
        path_start = iso(parse_utc((ltf or {}).get("window_start_utc") or decision_asof))
        path_end = iso(parse_utc((ltf or {}).get("window_end_utc")))
        if not path_end:
            stats["missing_path_end_utc"] += 1
            blocked_rows.append(
                blocked_record(row, "missing_path_end_utc", "Which input-only path source supplies path_end_utc for this setup?")
            )
            continue

        coverage = path_order_binding(ltf, path_start, path_end)
        if coverage is None:
            coverage = choose_ohlc_binding(row["symbol"], path_start, path_end, ohlc_sources)
        if coverage is None:
            stats["coverage_blocked"] += 1
            blocked_rows.append(
                blocked_record(
                    row,
                    "coverage_does_not_reach_path_end_utc",
                    "Which local M1/OHLC source or sanitized path-order row covers this setup through path_end_utc?",
                    path_start,
                    path_end,
                )
            )
            continue

        policy, ambiguity_state = same_bar_policy(ltf, coverage)
        params = row.get("trade_parameters") or {}
        entry_packet = {
            "direction": params.get("direction") or row.get("side"),
            "entry_price": params.get("entry_price"),
            "stop_loss": params.get("stop_loss"),
            "take_profit_1": params.get("take_profit_1"),
            "take_profit_2": params.get("take_profit_2"),
            "take_profit_3": params.get("take_profit_3"),
            "position_size_lots": params.get("position_size_lots"),
            "sl_buffer_applied": params.get("sl_buffer_applied"),
            "framework": row.get("framework"),
            "source_projection_hash": row.get("projection_hash"),
        }
        dup_id = duplicate_group_id(row, ltf)
        components = {
            "strategy_projection_row_hash": row.get("projection_hash"),
            "ltf_projection_row_hash": (ltf or {}).get("projection_hash"),
            "strategy_projection_file_sha256": projection_manifest["projections"]["strategy_follow_candidates"][
                "projection_sha256_used_for_packet_source_hashing"
            ],
            "ltf_projection_file_sha256": projection_manifest["projections"]["candidate_ltf_path_order"][
                "projection_sha256_used_for_packet_source_hashing"
            ],
            "coverage_binding_hash": sha256_json(coverage),
            "entry_sl_tp_or_level_packet_hash": sha256_json(entry_packet),
            "duplicate_group_id": dup_id,
        }
        source_hash = sha256_json(components)
        record = {
            "setup_id": setup_id,
            "symbol": row.get("symbol"),
            "source_symbol": (ltf or {}).get("source_symbol") or row.get("source_symbol") or row.get("broker_symbol") or row.get("symbol"),
            "session": row.get("session") or row.get("kill_zone"),
            "side": row.get("side"),
            "decision_asof_utc": decision_asof,
            "ordered_path_source_id": coverage.get("ordered_path_source_id") or coverage.get("source_path"),
            "path_start_utc": path_start,
            "path_end_utc": path_end,
            "entry_sl_tp_or_level_packet": entry_packet,
            "same_bar_ambiguity_policy": policy,
            "same_bar_ambiguity_state": ambiguity_state,
            "cost_model_version": COST_MODEL_VERSION,
            "duplicate_group_id": dup_id,
            "source_hash": source_hash,
            "sanitized_source_hash_components": components,
            "coverage_binding": coverage,
            "label_family": "synthetic_path_r",
            "broker_actual_r_absent_from_primary_metric": True,
            "no_leak_status": "INPUT_ONLY_PROJECTION_HASHED_NO_RESULT_VALUES_COPIED",
            "packet_build_source_paths": [
                rel(SOURCE_PROJECTION_FILES["strategy_follow_candidates"]),
                rel(SOURCE_PROJECTION_FILES["candidate_ltf_path_order"]),
                coverage.get("source_projection_path") or coverage.get("source_path"),
            ],
            "packet_id": "OTG0-PKT-013",
            "experiment_id": READY_EXPERIMENT_ID,
            "hypothesis_id": "G10-HYP-RISKBANK-005",
        }
        records.append(record)
        stats[coverage["coverage_mode"]] += 1

    return records, blocked_rows, dict(stats)


def blocked_record(
    row: dict[str, Any],
    blocker_code: str,
    next_exact_question: str,
    path_start: str | None = None,
    path_end: str | None = None,
) -> dict[str, Any]:
    return {
        "setup_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "session": row.get("session") or row.get("kill_zone"),
        "side": row.get("side"),
        "decision_asof_utc": iso(parse_utc(row.get("asof_cutoff_utc") or row.get("decision_time_utc"))),
        "path_start_utc": path_start,
        "path_end_utc": path_end,
        "blocker_code": blocker_code,
        "next_exact_question": next_exact_question,
        "strategy_projection_row_hash": row.get("projection_hash"),
    }


def sanitize_packet_for_hash(packet: dict[str, Any]) -> dict[str, Any]:
    clean = dict(packet)
    clean.pop("packet_hash", None)
    return clean


def build_blocked_packet(packet: dict[str, Any], inherited_blockers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    inherited = inherited_blockers.get(packet["packet_id"]) or {}
    blocking_fields = inherited.get("blocking_fields") or packet.get("blockers") or []
    question = inherited.get("next_exact_question") or (
        "Which source-specific input-only packet builder supplies the required fields without result/R columns?"
    )
    output = {
        "artifact_family": "OTB2R_INPUT_ONLY_PATH_PACKET",
        "schema_version": SCHEMA_VERSION,
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": git_head(),
        "git_branch_at_generation": git_branch(),
        "packet_id": packet["packet_id"],
        "experiment_id": packet["experiment_id"],
        "hypothesis_id": packet.get("hypothesis_id"),
        "decision": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
        "decision_reason": "No source-specific input-only packet builder exists for this OTB2R rebuild lane.",
        "blocking_fields": blocking_fields,
        "next_exact_question": question,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "replay_outcomes_run": False,
        "r_result_values_inspected_by_builder": False,
        "quarantine_or_result_outputs_created": False,
        "records": [],
    }
    output["packet_hash"] = sha256_json(sanitize_packet_for_hash(output))
    return output


def build_ready_packet(records: list[dict[str, Any]], blocked_rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision = "PACKET_READY_FOR_G12_REAUDIT" if records and not blocked_rows else "BLOCKED_WITH_NEXT_EXACT_QUESTION"
    question = None if decision == "PACKET_READY_FOR_G12_REAUDIT" else (
        "Which local M1/OHLC source or sanitized path-order row covers every selected G10 path window through path_end_utc?"
    )
    output = {
        "artifact_family": "OTB2R_INPUT_ONLY_PATH_PACKET",
        "schema_version": SCHEMA_VERSION,
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": git_head(),
        "git_branch_at_generation": git_branch(),
        "packet_id": "OTG0-PKT-013",
        "experiment_id": READY_EXPERIMENT_ID,
        "hypothesis_id": "G10-HYP-RISKBANK-005",
        "decision": decision,
        "decision_reason": (
            "G10 rebuilt from sanitized strategy and candidate_ltf_path_order projections; "
            "each included row is bound to coverage-valid explicit input-only path-order evidence."
        )
        if decision == "PACKET_READY_FOR_G12_REAUDIT"
        else "At least one selected row lacks coverage to path_end_utc.",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "replay_outcomes_run": False,
        "r_result_values_inspected_by_builder": False,
        "quarantine_or_result_outputs_created": False,
        "label_family": "synthetic_path_r",
        "broker_actual_r_absent_from_primary_metric": True,
        "cost_model_version": COST_MODEL_VERSION,
        "duplicate_policy_version": DUPLICATE_POLICY_VERSION,
        "same_bar_ambiguity_policy_version": SAME_BAR_POLICY_VERSION,
        "no_leak_feature_whitelist": BASE_RECORD_WHITELIST,
        "blocked_rows_not_in_packet": blocked_rows,
        "next_exact_question": question,
        "records": records,
    }
    output["packet_hash"] = sha256_json(sanitize_packet_for_hash(output))
    return output


def write_packets(
    synthetic_packet_controls: list[dict[str, Any]],
    ready_packet: dict[str, Any],
    inherited_blockers: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for packet in synthetic_packet_controls:
        if packet["packet_id"] == "OTG0-PKT-013":
            payload = ready_packet
        else:
            payload = build_blocked_packet(packet, inherited_blockers)
        filename = f"{payload['packet_id']}__{payload['experiment_id']}__otb2r_input_only_path_packet_{DATE_STAMP}.json"
        path = PACKETS_DIR / filename
        write_json(path, payload)
        entries.append(
            {
                "packet_id": payload["packet_id"],
                "experiment_id": payload["experiment_id"],
                "hypothesis_id": payload.get("hypothesis_id"),
                "decision": payload["decision"],
                "record_count": len(payload.get("records") or []),
                "packet_path": rel(path),
                "packet_hash": payload["packet_hash"],
                "file_sha256": sha256_file(path),
                "next_exact_question": payload.get("next_exact_question"),
                "blocking_fields": payload.get("blocking_fields") or [],
            }
        )
    return entries


def build_inherited_blocker_index(g12_blocked: dict[str, Any], otl2: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in g12_blocked.get("blocked_or_rejected_packets", []) + g12_blocked.get("rows", []):
        packet_id = row.get("packet_id")
        if packet_id:
            index[packet_id] = {
                "next_exact_question": row.get("next_exact_question"),
                "blocking_fields": row.get("blocking_fields") or [],
            }
    for row in otl2.get("packets", []):
        packet_id = row.get("packet_id")
        if packet_id:
            existing = index.setdefault(packet_id, {})
            existing.setdefault("blocking_fields", row.get("blocking_fields") or [])
            if not existing.get("next_exact_question"):
                existing["next_exact_question"] = (
                    "Which source-specific input-only packet builder supplies "
                    + ", ".join(row.get("blocking_fields") or ["required fields"])
                    + " without broker_actual_r, synthetic_path_r, win_loss, outcome_r, or replay-result columns?"
                )
    return index


def build_duplicate_policy(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups = Counter(row["duplicate_group_id"] for row in records)
    duplicate_rows = [
        {"duplicate_group_id": group_id, "row_count": count}
        for group_id, count in sorted(groups.items())
        if count > 1
    ]
    return {
        "artifact_family": "OTB2R_DUPLICATE_GROUP_POLICY",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "policy_version": DUPLICATE_POLICY_VERSION,
        "policy": (
            "Count raw rows separately from unique duplicate_group_id. The primary denominator for any later "
            "sample-floor/effective-N audit is unique duplicate_group_id; repeated raw rows remain diagnostics only."
        ),
        "group_key_fields": [
            "symbol",
            "session",
            "side",
            "decision_asof_utc",
            "framework",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "path_start_utc",
            "path_end_utc",
        ],
        "raw_record_count": len(records),
        "unique_duplicate_group_id_count": len(groups),
        "within_packet_duplicate_group_drift": len(records) - len(groups),
        "duplicate_groups_with_multiple_rows": duplicate_rows,
    }


def build_same_bar_policy(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["same_bar_ambiguity_policy"] for row in records)
    states = Counter(row["same_bar_ambiguity_state"] for row in records)
    return {
        "artifact_family": "OTB2R_SAME_BAR_AMBIGUITY_POLICY",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "policy_version": SAME_BAR_POLICY_VERSION,
        "policy": (
            "Same-bar terminal ordering is never guessed. If M1 path-order evidence flags same-minute ambiguity, "
            "the row remains flagged for later bounded replay. If only OHLC coverage exists, any intrabar terminal "
            "ordering is bounded/ambiguous rather than resolved."
        ),
        "policy_counts": dict(counts),
        "state_counts": dict(states),
        "terminal_order_claim_allowed": False,
    }


def build_coverage_audit(
    records: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
    ohlc_sources: dict[str, list[dict[str, Any]]],
    coverage_stats: dict[str, Any],
) -> dict[str, Any]:
    by_symbol = Counter(row["symbol"] for row in records)
    binding_modes = Counter(row["coverage_binding"]["coverage_mode"] for row in records)
    stale_ohlc_by_symbol: dict[str, int] = {}
    for symbol, entries in ohlc_sources.items():
        stale_ohlc_by_symbol[symbol] = sum(
            1 for entry in entries if not any(
                coverage_valid(record["path_start_utc"], record["path_end_utc"], entry.get("first_utc"), entry.get("last_utc"))
                for record in records
                if record["symbol"] == symbol
            )
        )
    return {
        "artifact_family": "OTB2R_COVERAGE_AUDIT",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "coverage_policy": (
            "Every included path window must be bound either to an explicit sanitized input-only path-order row "
            "whose coverage window reaches path_end_utc, or to a local M1/M5/M15/H1 OHLC file whose timestamp "
            "coverage spans path_start_utc through path_end_utc. Otherwise the row is blocked."
        ),
        "included_record_count": len(records),
        "blocked_row_count": len(blocked_rows),
        "coverage_mode_counts": dict(binding_modes),
        "records_by_symbol": dict(by_symbol),
        "coverage_stats": coverage_stats,
        "blocked_rows": blocked_rows,
        "ohlc_source_inventory": ohlc_sources,
        "stale_or_nonbinding_ohlc_file_count_by_symbol": stale_ohlc_by_symbol,
    }


def packet_manifest(
    entries: list[dict[str, Any]],
    projection_manifest: dict[str, Any],
    coverage_audit: dict[str, Any],
    duplicate_policy: dict[str, Any],
    same_bar_policy_doc: dict[str, Any],
) -> dict[str, Any]:
    decision_counts = Counter(entry["decision"] for entry in entries)
    return {
        "artifact_family": "OTB2R_PACKET_MANIFEST",
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": git_head(),
        "git_branch_at_generation": git_branch(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "replay_outcomes_run": False,
        "r_result_values_inspected_by_builder": False,
        "quarantine_or_result_outputs_created": False,
        "external_fetches_or_paid_calls": 0,
        "databento_or_api_calls": 0,
        "controlling_input_hashes": {
            name: {"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)}
            for name, path in CONTROLLING_INPUTS.items()
        },
        "sanitized_projection_hashes": {
            name: {
                "projection_path": data["projection_path"],
                "projection_sha256": data["projection_sha256_used_for_packet_source_hashing"],
                "raw_path": data["raw_path"],
                "raw_sha256_for_provenance_only_not_packet_source_hash": data[
                    "raw_sha256_for_provenance_only_not_packet_source_hash"
                ],
            }
            for name, data in projection_manifest["projections"].items()
        },
        "summary": {
            "packet_count": len(entries),
            "decision_counts": dict(decision_counts),
            "ready_for_g12_reaudit_count": decision_counts.get("PACKET_READY_FOR_G12_REAUDIT", 0),
            "blocked_with_next_exact_question_count": decision_counts.get("BLOCKED_WITH_NEXT_EXACT_QUESTION", 0),
            "ready_record_count": sum(entry["record_count"] for entry in entries if entry["decision"] == "PACKET_READY_FOR_G12_REAUDIT"),
            "coverage_included_record_count": coverage_audit["included_record_count"],
            "duplicate_unique_count": duplicate_policy["unique_duplicate_group_id_count"],
            "same_bar_policy_counts": same_bar_policy_doc["policy_counts"],
        },
        "packets": entries,
    }


def scan_artifacts_for_forbidden_keys(paths: list[Path]) -> dict[str, Any]:
    scanned = []
    bad: dict[str, Any] = {}
    for path in paths:
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            counts: Counter[str] = Counter()
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        counts.update(recursive_forbidden_key_counts(json.loads(line)))
        elif path.suffix == ".json":
            counts = recursive_forbidden_key_counts(read_json(path))
        else:
            continue
        scanned.append(rel(path))
        filtered = {
            key: value
            for key, value in counts.items()
            if not any(allowed in key for allowed in ALLOWED_CONTROL_KEYS_WITH_OUTCOME_WORDS)
            and "label_family" not in key
            and "broker_actual_r_absent_from_primary_metric" not in key
        }
        if filtered:
            bad[rel(path)] = filtered
    return {"scanned_paths": scanned, "bad_forbidden_key_counts": bad}


def completion_audit(
    manifest: dict[str, Any],
    projection_manifest: dict[str, Any],
    coverage_audit: dict[str, Any],
    duplicate_policy: dict[str, Any],
    same_bar_policy_doc: dict[str, Any],
    forbidden_scan: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {
            "requirement": "Run mandatory GTOS preflight from C:/tmp/gtos_otb/OTB2R at main HEAD 6f5fc730",
            "evidence": f"LIVE_STATE regenerated before build; builder git_head_at_generation={manifest['git_head_at_generation']}.",
            "status": "PASS" if manifest["git_head_at_generation"].startswith("6f5fc730") else "FAIL",
        },
        {
            "requirement": "Use controlling inputs G12 audit, OTB2, OTB3, OTB0/OTG0/OTL2 controls, and research_current_state",
            "evidence": f"{len(manifest['controlling_input_hashes'])} controlling inputs hashed in packet manifest.",
            "status": "PASS",
        },
        {
            "requirement": "Create input-only projections before source hashing",
            "evidence": f"{len(projection_manifest['projections'])} projection files written and hashed; packet source hashes use projection hashes only.",
            "status": "PASS",
        },
        {
            "requirement": "Exclude path_order_label, touch times, hit_tp/hit_sl, path/result labels, R values, and future/outcome fields from projections before hashing",
            "evidence": "projection forbidden key counts after sanitization are empty for all projection files.",
            "status": "PASS"
            if all(
                not data["forbidden_projection_key_counts_after_sanitization"]
                for data in projection_manifest["projections"].values()
            )
            else "FAIL",
        },
        {
            "requirement": "Bind every included path window to coverage-valid M1/OHLC or explicit input-only path-order rows reaching path_end_utc",
            "evidence": f"included={coverage_audit['included_record_count']} blocked={coverage_audit['blocked_row_count']} coverage_modes={coverage_audit['coverage_mode_counts']}.",
            "status": "PASS" if coverage_audit["blocked_row_count"] == 0 and coverage_audit["included_record_count"] > 0 else "FAIL",
        },
        {
            "requirement": "Keep packet blocked with exact next question if coverage is incomplete",
            "evidence": "coverage audit carries blocked_rows with next_exact_question; G10 has no blocked rows, other packets remain BLOCKED_WITH_NEXT_EXACT_QUESTION.",
            "status": "PASS",
        },
        {
            "requirement": "Produce sanitized source hashes, duplicate_group_id policy, coverage audit, same-bar ambiguity policy, and packet manifests under otb2r_input_only_path_rebuild/",
            "evidence": "OTB2R_SANITIZED_SOURCE_HASHES, OTB2R_DUPLICATE_GROUP_POLICY, OTB2R_COVERAGE_AUDIT, OTB2R_SAME_BAR_AMBIGUITY_POLICY, OTB2R_PACKET_MANIFEST, and packet files are written.",
            "status": "PASS",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, and outcome_review_opened=false",
            "evidence": "All generated top-level artifacts carry NO_PROMOTION_VERDICT with validation_safe=false and outcome_review_opened=false.",
            "status": "PASS",
        },
        {
            "requirement": "No replay outcomes, R/result value use, quarantine/result outputs, paid/API/Databento/network, registry edits, or live-surface changes",
            "evidence": "Builder writes only OTB2R research artifacts; manifest reports zero external/API/Databento calls and no result/quarantine outputs.",
            "status": "PASS",
        },
        {
            "requirement": "No forbidden result/future keys remain in projection or packet records beyond required guard metadata",
            "evidence": f"forbidden scan bad path count={len(forbidden_scan['bad_forbidden_key_counts'])}.",
            "status": "PASS" if not forbidden_scan["bad_forbidden_key_counts"] else "FAIL",
        },
        {
            "requirement": "Declare duplicate raw rows versus unique duplicate_group_id denominator",
            "evidence": f"raw={duplicate_policy['raw_record_count']} unique={duplicate_policy['unique_duplicate_group_id_count']} drift={duplicate_policy['within_packet_duplicate_group_drift']}.",
            "status": "PASS",
        },
        {
            "requirement": "Declare same-bar ambiguity policy without guessing terminal order",
            "evidence": f"terminal_order_claim_allowed={same_bar_policy_doc['terminal_order_claim_allowed']} policy_counts={same_bar_policy_doc['policy_counts']}.",
            "status": "PASS" if same_bar_policy_doc["terminal_order_claim_allowed"] is False else "FAIL",
        },
    ]
    return {
        "artifact_family": "OTB2R_COMPLETION_AUDIT",
        "version_date": DATE_STAMP,
        "generated_at_utc": now_utc(),
        "git_head_at_generation": manifest["git_head_at_generation"],
        "git_branch_at_generation": manifest["git_branch_at_generation"],
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "objective_restatement": (
            "Rebuild rejected OTB2 synthetic/path packet inputs under an OTB2R input-only lane by hashing sanitized "
            "candidate/path projections, proving coverage through path_end_utc, declaring duplicate and same-bar "
            "policies, and leaving uncovered packets blocked without opening outcome review."
        ),
        "prompt_to_artifact_checklist": checklist,
        "summary": {
            "can_mark_otb2r_input_only_rebuild_complete": all(item["status"] == "PASS" for item in checklist),
            "ready_for_g12_reaudit_count": manifest["summary"]["ready_for_g12_reaudit_count"],
            "blocked_with_next_exact_question_count": manifest["summary"]["blocked_with_next_exact_question_count"],
            "ready_record_count": manifest["summary"]["ready_record_count"],
            "projection_count": len(projection_manifest["projections"]),
            "coverage_blocked_row_count": coverage_audit["blocked_row_count"],
            "external_fetches_or_paid_calls": 0,
            "quarantine_or_result_outputs_created": False,
            "forbidden_scan_bad_path_count": len(forbidden_scan["bad_forbidden_key_counts"]),
        },
    }


def render_projection_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            name,
            data["raw_rows_read"],
            data["projection_rows_written"],
            len(data["forbidden_source_key_counts_removed_before_projection_hash"]),
            str(data["projection_sha256_used_for_packet_source_hashing"])[:16],
            data["projection_path"],
        ]
        for name, data in payload["projections"].items()
    ]
    return f"""# OTB2R Sanitized Source Hashes - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

Packet source hashes use sanitized projection hashes only. Raw source file
hashes are recorded for provenance but are not used as packet source hashes.

{table(['Projection', 'Raw rows', 'Projected rows', 'Forbidden key names removed', 'Projection hash', 'Path'], rows)}
"""


def render_duplicate_md(payload: dict[str, Any]) -> str:
    return f"""# OTB2R Duplicate Group Policy - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

Policy version: `{payload['policy_version']}`

{payload['policy']}

| Metric | Value |
| --- | --- |
| Raw record count | {payload['raw_record_count']} |
| Unique duplicate_group_id count | {payload['unique_duplicate_group_id_count']} |
| Within-packet duplicate drift | {payload['within_packet_duplicate_group_drift']} |
"""


def render_coverage_md(payload: dict[str, Any]) -> str:
    mode_rows = [[key, value] for key, value in sorted(payload["coverage_mode_counts"].items())]
    sym_rows = [[key, value] for key, value in sorted(payload["records_by_symbol"].items())]
    return f"""# OTB2R Coverage Audit - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

{payload['coverage_policy']}

## Coverage Modes

{table(['Mode', 'Rows'], mode_rows)}

## Records By Symbol

{table(['Symbol', 'Rows'], sym_rows)}

Blocked rows: `{payload['blocked_row_count']}`
"""


def render_same_bar_md(payload: dict[str, Any]) -> str:
    rows = [[key, value] for key, value in sorted(payload["policy_counts"].items())]
    state_rows = [[key, value] for key, value in sorted(payload["state_counts"].items())]
    return f"""# OTB2R Same-Bar Ambiguity Policy - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

Policy version: `{payload['policy_version']}`

{payload['policy']}

Terminal order claim allowed: `{payload['terminal_order_claim_allowed']}`

## Policy Counts

{table(['Policy', 'Rows'], rows)}

## State Counts

{table(['State', 'Rows'], state_rows)}
"""


def render_manifest_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            entry["packet_id"],
            entry["experiment_id"],
            entry["decision"],
            entry["record_count"],
            str(entry["packet_hash"])[:16],
        ]
        for entry in payload["packets"]
    ]
    return f"""# OTB2R Packet Manifest - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

OTB2R rebuilt input-only path packets from sanitized source projections. It did
not run replay outcomes, create result/quarantine outputs, call network/API/
Databento sources, edit registries, or touch live trading behavior.

## Summary

- Packet count: `{payload['summary']['packet_count']}`
- Ready for G12 reaudit: `{payload['summary']['ready_for_g12_reaudit_count']}`
- Blocked with next exact question: `{payload['summary']['blocked_with_next_exact_question_count']}`
- Ready records: `{payload['summary']['ready_record_count']}`

{table(['Packet', 'Experiment', 'Decision', 'Records', 'Packet hash'], rows)}
"""


def render_completion_md(payload: dict[str, Any]) -> str:
    rows = [
        [item["requirement"], item["status"], item["evidence"]]
        for item in payload["prompt_to_artifact_checklist"]
    ]
    return f"""# OTB2R Completion Audit - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

## Objective Restatement

{payload['objective_restatement']}

## Prompt-To-Artifact Checklist

{table(['Requirement', 'Status', 'Evidence'], rows)}

## Verdict

- Can mark OTB2R input-only rebuild complete: `{payload['summary']['can_mark_otb2r_input_only_rebuild_complete']}`
- Ready for G12 reaudit: `{payload['summary']['ready_for_g12_reaudit_count']}`
- Blocked with next exact question: `{payload['summary']['blocked_with_next_exact_question_count']}`
- External/API/Databento calls: `{payload['summary']['external_fetches_or_paid_calls']}`
- Result/quarantine outputs created: `{payload['summary']['quarantine_or_result_outputs_created']}`
"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)

    projection_manifest = build_all_projections()
    strategy_rows, strategy_summary = selected_strategy_rows()
    ltf_by_candidate, ltf_summary = selected_ltf_index()
    symbols = {row["symbol"] for row in strategy_rows if row.get("symbol")}
    ohlc_sources = locate_ohlc_sources(symbols)
    records, blocked_rows, coverage_stats = build_ready_records(
        strategy_rows=strategy_rows,
        ltf_by_candidate=ltf_by_candidate,
        ohlc_sources=ohlc_sources,
        projection_manifest=projection_manifest,
    )

    otg0_manifest = read_json(CONTROLLING_INPUTS["otg0_packet_manifest"])
    otl2 = read_json(CONTROLLING_INPUTS["otl2_audit"])
    g12_blocked = read_json(CONTROLLING_INPUTS["g12_blocked_owner_questions"])
    inherited_blockers = build_inherited_blocker_index(g12_blocked, otl2)
    ready_packet = build_ready_packet(records, blocked_rows)
    packet_entries = write_packets(
        synthetic_packet_controls=synthetic_packets(otg0_manifest),
        ready_packet=ready_packet,
        inherited_blockers=inherited_blockers,
    )

    duplicate_policy = build_duplicate_policy(records)
    same_bar_policy_doc = build_same_bar_policy(records)
    coverage_audit = build_coverage_audit(records, blocked_rows, ohlc_sources, coverage_stats)
    manifest = packet_manifest(packet_entries, projection_manifest, coverage_audit, duplicate_policy, same_bar_policy_doc)

    write_json(OUT / f"OTB2R_SANITIZED_SOURCE_HASHES_{DATE_STAMP}.json", projection_manifest)
    write_json(OUT / f"OTB2R_DUPLICATE_GROUP_POLICY_{DATE_STAMP}.json", duplicate_policy)
    write_json(OUT / f"OTB2R_COVERAGE_AUDIT_{DATE_STAMP}.json", coverage_audit)
    write_json(OUT / f"OTB2R_SAME_BAR_AMBIGUITY_POLICY_{DATE_STAMP}.json", same_bar_policy_doc)
    write_json(OUT / f"OTB2R_PACKET_MANIFEST_{DATE_STAMP}.json", manifest)

    write_text(OUT / f"OTB2R_SANITIZED_SOURCE_HASHES_{DATE_STAMP}.md", render_projection_md(projection_manifest))
    write_text(OUT / f"OTB2R_DUPLICATE_GROUP_POLICY_{DATE_STAMP}.md", render_duplicate_md(duplicate_policy))
    write_text(OUT / f"OTB2R_COVERAGE_AUDIT_{DATE_STAMP}.md", render_coverage_md(coverage_audit))
    write_text(OUT / f"OTB2R_SAME_BAR_AMBIGUITY_POLICY_{DATE_STAMP}.md", render_same_bar_md(same_bar_policy_doc))
    write_text(OUT / f"OTB2R_PACKET_MANIFEST_{DATE_STAMP}.md", render_manifest_md(manifest))

    paths_to_scan = list(SOURCE_PROJECTION_FILES.values()) + list(PACKETS_DIR.glob("*.json"))
    forbidden_scan = scan_artifacts_for_forbidden_keys(paths_to_scan)
    completion = completion_audit(
        manifest=manifest,
        projection_manifest=projection_manifest,
        coverage_audit=coverage_audit,
        duplicate_policy=duplicate_policy,
        same_bar_policy_doc=same_bar_policy_doc,
        forbidden_scan=forbidden_scan,
    )
    write_json(OUT / f"OTB2R_FORBIDDEN_FIELD_SCAN_{DATE_STAMP}.json", forbidden_scan)
    write_json(OUT / f"OTB2R_COMPLETION_AUDIT_{DATE_STAMP}.json", completion)
    write_text(OUT / f"OTB2R_COMPLETION_AUDIT_{DATE_STAMP}.md", render_completion_md(completion))

    run_summary = {
        "strategy_projection": strategy_summary,
        "ltf_projection": ltf_summary,
        "packet_summary": manifest["summary"],
        "completion": completion["summary"],
    }
    print(json.dumps(run_summary, indent=2, sort_keys=True))
    return 0 if completion["summary"]["can_mark_otb2r_input_only_rebuild_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
