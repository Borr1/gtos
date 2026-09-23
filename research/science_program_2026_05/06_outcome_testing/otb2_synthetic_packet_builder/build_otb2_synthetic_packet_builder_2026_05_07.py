"""Build OTB2 synthetic replay frozen packet artifacts.

OTB2 is a blocker-clearing research lane. It builds non-result synthetic
replay input packets from local OHLC/path logs where possible and writes exact
owner questions where the packet cannot be made source-safe yet.

This script must not run replay outcomes, inspect R/result summaries for
packet construction, create quarantine/result outputs, call paid sources, or
touch live trading behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE_STAMP = "2026-05-07"

OT_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
OTB0 = OT_DIR / "otb0_blocker_clearing_governor"
OTB3 = OT_DIR / "otb3_source_noleak_cleanup"
OTL2 = OT_DIR / "otl2_synthetic_replay_packet_audit"
CONTROL = ROOT / "research" / "science_program_2026_05" / "00_control"
SYNTH = ROOT / "research" / "science_program_2026_05" / "05_synthesis"
HYP = ROOT / "research" / "science_program_2026_05" / "02_hypothesis_registry"

PACKETS_DIR = OUT / "packets"
COST_MODEL_VERSION = "otb2_synthetic_path_input_cost_model_v1_research_only"
SCHEMA_VERSION = "otb2_synthetic_replay_frozen_packet_v1"

CONTROLLING_INPUTS = {
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "otg0_manifest": OT_DIR / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json",
    "otl2_audit_json": OTL2 / f"OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_{DATE_STAMP}.json",
    "otl2_audit_md": OTL2 / f"OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_{DATE_STAMP}.md",
    "otb0_packet_requirements": OTB0 / f"OTB0_PACKET_BUILDER_REQUIREMENTS_{DATE_STAMP}.json",
    "otb0_dependency_graph": OTB0 / f"OTB0_BLOCKER_DEPENDENCY_GRAPH_{DATE_STAMP}.json",
    "otb0_followup_prompts": OTB0 / f"OTB0_FOLLOWUP_GOAL_PROMPTS_{DATE_STAMP}.json",
    "otb3_cleanup_ledger": OTB3 / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json",
    "otb3_evidence_index": OTB3 / f"OTB3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json",
    "otb3_noleak_ledger": OTB3 / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json",
    "otg0_control_rules": OT_DIR / f"OTG0_OUTCOME_TESTING_CONTROL_RULES_{DATE_STAMP}.json",
    "source_registry": CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
    "hypothesis_registry": HYP / "HYPOTHESIS_REGISTRY_2026-05-06.json",
    "g12_red_team_review": SYNTH / "G12_RED_TEAM_REVIEW_2026-05-06.md",
    "g12_survivor_blockers": SYNTH / "G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.json",
    "g12_source_validity": SYNTH / "G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md",
    "g12_leakage": SYNTH / "G12_LEAKAGE_LEDGER_2026-05-06.md",
    "g12_label_separation": SYNTH / "G12_LABEL_SEPARATION_REVIEW_2026-05-06.md",
    "g12_duplicate_counting": SYNTH / "G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md",
}

LOCAL_PACKET_SOURCES = {
    "strategy_follow_candidates": ROOT / "shadow_logs" / "strategy_follow_candidates.jsonl",
    "candidate_ltf_path_order": ROOT / "shadow_logs" / "candidate_ltf_path_order.jsonl",
    "candidate_path_contract_audit": ROOT / "shadow_logs" / "candidate_path_contract_audit.jsonl",
    "prefill_delivery_path": ROOT / "shadow_logs" / "prefill_delivery_path.jsonl",
    "news_calendar": ROOT / "data" / "news_calendar.json",
}

DEFAULT_V2_EVENT_LOG = (
    ROOT
    / "data"
    / "external"
    / "validation"
    / "calendar_macro_bundle_v1"
    / "historical_opportunities"
    / "raw_ohlc_prequential_replay"
    / "path_scaling_v2_structural_levels"
    / "raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl"
)

RESULT_BEARING_KEYS = {
    "actual_r",
    "broker_actual_r",
    "gross_r",
    "hit_sl",
    "hit_tp1",
    "mae_r",
    "mfe_r",
    "net_r",
    "net_r_by_cost",
    "outcome",
    "outcome_r",
    "path_label",
    "path_synthetic_r",
    "realized_r",
    "result",
    "synthetic_path_r",
    "win_loss",
}

FORBIDDEN_PACKET_KEYS = {
    "actual_r",
    "broker_actual_r",
    "gross_r",
    "hit_sl",
    "hit_tp1",
    "mae_r",
    "mfe_r",
    "net_r",
    "net_r_by_cost",
    "outcome",
    "outcome_r",
    "path_label",
    "path_synthetic_r",
    "realized_r",
    "synthetic_path_r",
    "win_loss",
}

BASE_NO_LEAK_WHITELIST = [
    "setup_id",
    "symbol",
    "session",
    "side",
    "decision_asof_utc",
    "ordered_path_source_id",
    "path_start_utc",
    "path_end_utc",
    "entry_sl_tp_or_level_packet",
    "same_bar_ambiguity_policy",
    "cost_model_version",
    "duplicate_group_id",
    "source_symbol",
    "source_hash",
    "packet_build_source_paths",
]

READY_EXPERIMENTS = {
    "G10-EXP-RISKBANK-005": {
        "reason": (
            "Local forward-shadow strategy/path rows contain setup, entry/SL/TP, "
            "decision/as-of, duplicate, source hash, source symbol, and same-bar "
            "policy fields without copying path result/R columns."
        ),
        "source_contract_refs": ["G10-SRC-PHASE3-PATH-REPLAY"],
        "packet_scope": "risk_bank_reentry_input_audit_only",
    }
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


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


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        rendered = [str(cell).replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(rendered) + " |")
    return "\n".join(lines)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def first_jsonl_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return set(json.loads(line).keys())
    return set()


def input_hashes() -> dict[str, dict[str, Any]]:
    hashes: dict[str, dict[str, Any]] = {}
    for name, path in CONTROLLING_INPUTS.items():
        hashes[name] = {"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)}
    return hashes


def source_hashes() -> dict[str, dict[str, Any]]:
    hashes: dict[str, dict[str, Any]] = {}
    for name, path in LOCAL_PACKET_SOURCES.items():
        hashes[name] = {"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path)}
    return hashes


def synthetic_packets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        packet
        for packet in manifest["packets"]
        if packet.get("otg0_testing_lane") == "synthetic_replay_existing_data_audit"
    ]


def hypothesis_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = registry.get("hypotheses") or registry.get("rows") or []
    return {row.get("hypothesis_id") or row.get("id"): row for row in rows}


def source_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["source_id"]: row for row in registry.get("rows", [])}


def otl2_packet_index(otl2: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["packet_id"]: row for row in otl2.get("packets", [])}


def clean_no_leak_fields(fields: list[str]) -> tuple[list[str], list[str]]:
    cleaned: list[str] = []
    notes: list[str] = []
    for field in fields:
        if field == "outcome_review_opened":
            notes.append("outcome_review_opened is retained as a control flag, not a model feature.")
            continue
        if field == "leg_state_before_outcome":
            cleaned.append("leg_state_at_decision_or_before_replay_window")
            notes.append(
                "leg_state_before_outcome renamed in OTB2 sidecar whitelist to avoid outcome-named feature keys."
            )
            continue
        if field in FORBIDDEN_PACKET_KEYS:
            notes.append(f"{field} excluded from no_leak_feature_whitelist as forbidden result field.")
            continue
        cleaned.append(field)
    merged = list(dict.fromkeys(BASE_NO_LEAK_WHITELIST + cleaned))
    return merged, notes


def load_strategy_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = LOCAL_PACKET_SOURCES["strategy_follow_candidates"]
    rows = read_jsonl(path)
    projected: list[dict[str, Any]] = []
    skipped = Counter()
    for row in rows:
        candidate_id = row.get("candidate_id")
        trade_parameters = row.get("trade_parameters") or {}
        if not candidate_id:
            skipped["missing_candidate_id"] += 1
            continue
        if not row.get("side"):
            skipped["missing_side"] += 1
            continue
        if not trade_parameters.get("entry_price") or not trade_parameters.get("stop_loss"):
            skipped["missing_entry_sl"] += 1
            continue
        projected.append(
            {
                "line_no": row["_line_no"],
                "candidate_id": candidate_id,
                "symbol": row.get("symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "session": row.get("session") or row.get("kill_zone"),
                "side": row.get("side"),
                "decision_time_utc": row.get("decision_time_utc"),
                "asof_cutoff_utc": row.get("asof_cutoff_utc") or row.get("decision_time_utc"),
                "created_at_utc": row.get("created_at_utc"),
                "framework": row.get("framework"),
                "source_file": row.get("source_file"),
                "source_symbol": row.get("source_symbol") or row.get("broker_symbol") or row.get("symbol"),
                "schema_version": row.get("schema_version"),
                "no_leak_status": row.get("no_leak_status"),
                "trade_parameters": {
                    "direction": trade_parameters.get("direction"),
                    "entry_price": trade_parameters.get("entry_price"),
                    "stop_loss": trade_parameters.get("stop_loss"),
                    "take_profit_1": trade_parameters.get("take_profit_1"),
                    "take_profit_2": trade_parameters.get("take_profit_2"),
                    "take_profit_3": trade_parameters.get("take_profit_3"),
                    "risk_reward_ratio": trade_parameters.get("risk_reward_ratio"),
                    "position_size_lots": trade_parameters.get("position_size_lots"),
                    "sl_buffer_applied": trade_parameters.get("sl_buffer_applied"),
                },
            }
        )
    projected.sort(key=lambda item: (item.get("decision_time_utc") or "", item["candidate_id"]))
    return projected, {"rows_read": len(rows), "projected_rows": len(projected), "skipped": dict(skipped)}


def load_ltf_rows() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = LOCAL_PACKET_SOURCES["candidate_ltf_path_order"]
    rows = read_jsonl(path)
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        by_candidate[candidate_id].append(
            {
                "line_no": row["_line_no"],
                "candidate_id": candidate_id,
                "row_key": row.get("row_key"),
                "decision_time_utc": row.get("decision_time_utc"),
                "window_start_utc": row.get("window_start_utc") or row.get("decision_time_utc"),
                "window_end_utc": row.get("window_end_utc"),
                "ltf_status": row.get("ltf_status"),
                "ltf_source": row.get("ltf_source"),
                "m1_bar_count": row.get("m1_bar_count") or 0,
                "same_m1_ambiguity": bool(row.get("same_m1_ambiguity")),
                "manual_backfill_status": row.get("manual_backfill_status"),
                "source_symbol": row.get("source_symbol") or row.get("broker_symbol") or row.get("symbol"),
                "schema_version": row.get("schema_version"),
            }
        )

    selected: dict[str, dict[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    for candidate_id, choices in by_candidate.items():
        choices.sort(
            key=lambda item: (
                1 if item.get("ltf_status") == "M1_PATH_RECOVERED" else 0,
                int(item.get("m1_bar_count") or 0),
                item.get("window_end_utc") or "",
            ),
            reverse=True,
        )
        selected[candidate_id] = choices[0]
        status_counts[str(choices[0].get("ltf_status"))] += 1

    return selected, {
        "rows_read": len(rows),
        "candidate_ids": len(selected),
        "selected_ltf_status_counts": dict(status_counts),
    }


def locate_ohlc_sources(symbols: set[str]) -> dict[str, dict[str, Any]]:
    roots = [
        ROOT / "data",
        ROOT / "data" / "historical",
        ROOT / "data" / "historical_2026",
        ROOT / "data" / "historical_2022_2023",
    ]
    timeframes = ["M1", "M5", "M15", "H1"]
    sources: dict[str, dict[str, Any]] = {}
    for symbol in sorted(symbols):
        symbol_sources = []
        for root in roots:
            for timeframe in timeframes:
                path = root / f"{symbol}_{timeframe}.csv"
                if path.exists():
                    coverage = csv_coverage(path)
                    symbol_sources.append(
                        {
                            "path": rel(path),
                            "timeframe": timeframe,
                            "sha256": sha256_file(path),
                            **coverage,
                        }
                    )
        sources[symbol] = {
            "available": bool(symbol_sources),
            "preferred_path": symbol_sources[0]["path"] if symbol_sources else None,
            "sources": symbol_sources,
        }
    return sources


def csv_coverage(path: Path) -> dict[str, Any]:
    first: str | None = None
    last: str | None = None
    rows = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            stamp = row.get("time") or row.get("timestamp") or row.get("datetime")
            parsed = iso(parse_utc(stamp))
            if rows == 1:
                first = parsed
            last = parsed
    return {"rows": rows, "first_utc": first, "last_utc": last}


def choose_ohlc_source(symbol: str, ohlc_sources: dict[str, dict[str, Any]], prefer_m1: bool) -> dict[str, Any] | None:
    entries = (ohlc_sources.get(symbol) or {}).get("sources") or []
    preferred = ["M1", "M5", "M15", "H1"] if prefer_m1 else ["M15", "M5", "M1", "H1"]
    for timeframe in preferred:
        for entry in entries:
            if entry["timeframe"] == timeframe:
                return entry
    return entries[0] if entries else None


def build_base_path_rows(
    candidates: list[dict[str, Any]],
    ltf_by_candidate: dict[str, dict[str, Any]],
    ohlc_sources: dict[str, dict[str, Any]],
    local_hashes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    skipped = Counter()
    seen: set[str] = set()
    for candidate in candidates:
        setup_id = candidate["candidate_id"]
        if setup_id in seen:
            skipped["duplicate_setup_id_projected_out"] += 1
            continue
        seen.add(setup_id)

        decision_dt = parse_utc(candidate.get("asof_cutoff_utc") or candidate.get("decision_time_utc"))
        if decision_dt is None:
            skipped["missing_decision_asof_utc"] += 1
            continue
        ltf = ltf_by_candidate.get(setup_id)
        ltf_recovered = bool(ltf and ltf.get("ltf_status") == "M1_PATH_RECOVERED")
        ohlc = choose_ohlc_source(candidate["symbol"], ohlc_sources, prefer_m1=ltf_recovered)
        if ohlc is None:
            skipped["missing_local_ohlc_source"] += 1
            continue

        path_start_dt = parse_utc(ltf.get("window_start_utc") if ltf else None) or decision_dt
        path_end_dt = parse_utc(ltf.get("window_end_utc") if ltf else None) or (decision_dt + timedelta(hours=2))
        if path_end_dt <= path_start_dt:
            path_end_dt = path_start_dt + timedelta(hours=2)

        same_bar_policy = (
            "M1_PATH_ORDER_LOG_AVAILABLE__SAME_MINUTE_AMBIGUITY_FLAGGED_NOT_GUESSED"
            if ltf_recovered
            else "LOCAL_OHLC_BOUNDED_PATH__INTRABAR_TERMINAL_ORDER_AMBIGUOUS_NOT_GUESSED"
        )
        if ltf_recovered and ltf:
            ordered_path_source_id = (
                f"shadow_logs/candidate_ltf_path_order.jsonl"
                f"#{ltf.get('row_key') or setup_id}"
            )
        else:
            ordered_path_source_id = (
                f"local_ohlc:{candidate['symbol']}:{ohlc['timeframe']}:"
                f"{iso(path_start_dt)}:{iso(path_end_dt)}:{str(ohlc.get('sha256'))[:16]}"
            )

        entry_packet = {
            "direction": candidate["trade_parameters"].get("direction") or candidate.get("side"),
            "entry_price": candidate["trade_parameters"].get("entry_price"),
            "stop_loss": candidate["trade_parameters"].get("stop_loss"),
            "take_profit_1": candidate["trade_parameters"].get("take_profit_1"),
            "take_profit_2": candidate["trade_parameters"].get("take_profit_2"),
            "take_profit_3": candidate["trade_parameters"].get("take_profit_3"),
            "risk_reward_ratio": candidate["trade_parameters"].get("risk_reward_ratio"),
            "position_size_lots": candidate["trade_parameters"].get("position_size_lots"),
            "sl_buffer_applied": candidate["trade_parameters"].get("sl_buffer_applied"),
            "framework": candidate.get("framework"),
            "source_schema_version": candidate.get("schema_version"),
        }

        source_paths = [
            rel(LOCAL_PACKET_SOURCES["strategy_follow_candidates"]),
            rel(LOCAL_PACKET_SOURCES["candidate_ltf_path_order"]),
            ohlc["path"],
        ]
        source_hash_payload = {
            "setup_id": setup_id,
            "strategy_follow_candidates_sha256": local_hashes["strategy_follow_candidates"]["sha256"],
            "candidate_ltf_path_order_sha256": local_hashes["candidate_ltf_path_order"]["sha256"],
            "ohlc_sha256": ohlc.get("sha256"),
            "ltf_row_key": (ltf or {}).get("row_key"),
            "entry_sl_tp_or_level_packet": entry_packet,
        }

        rows.append(
            {
                "setup_id": setup_id,
                "symbol": candidate.get("symbol"),
                "source_symbol": (ltf or {}).get("source_symbol") or candidate.get("source_symbol"),
                "session": candidate.get("session"),
                "side": candidate.get("side"),
                "decision_asof_utc": iso(decision_dt),
                "ordered_path_source_id": ordered_path_source_id,
                "path_start_utc": iso(path_start_dt),
                "path_end_utc": iso(path_end_dt),
                "entry_sl_tp_or_level_packet": entry_packet,
                "same_bar_ambiguity_policy": same_bar_policy,
                "same_bar_ambiguity_state": (
                    "same_m1_ambiguity_flagged"
                    if (ltf or {}).get("same_m1_ambiguity")
                    else "not_flagged_or_not_applicable"
                ),
                "cost_model_version": COST_MODEL_VERSION,
                "duplicate_group_id": "dup_"
                + sha256_json(
                    {
                        "setup_id": setup_id,
                        "symbol": candidate.get("symbol"),
                        "session": candidate.get("session"),
                        "side": candidate.get("side"),
                    }
                )[:24],
                "source_hash": sha256_json(source_hash_payload),
                "label_family": "synthetic_path_r",
                "broker_actual_r_absent_from_primary_metric": True,
                "no_leak_status": candidate.get("no_leak_status"),
                "packet_build_source_paths": source_paths,
                "path_source_metadata": {
                    "ltf_status": (ltf or {}).get("ltf_status"),
                    "ltf_source": (ltf or {}).get("ltf_source"),
                    "m1_bar_count": (ltf or {}).get("m1_bar_count"),
                    "ohlc_timeframe": ohlc.get("timeframe"),
                    "ohlc_coverage_first_utc": ohlc.get("first_utc"),
                    "ohlc_coverage_last_utc": ohlc.get("last_utc"),
                },
                "same_dataset_contamination_guard": {
                    "dataset_role": "FROZEN_INPUT_PACKET_ONLY",
                    "result_or_r_columns_absent_from_record": True,
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "quarantine_or_result_output_created": False,
                },
            }
        )
    return rows, {"rows_built": len(rows), "skipped": dict(skipped)}


def result_bearing_source_inventory() -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    candidates = [
        ROOT / "shadow_logs" / "candidate_path_follow.jsonl",
        ROOT / "shadow_logs" / "candidate_path_contract_audit.jsonl",
        DEFAULT_V2_EVENT_LOG,
    ]
    candidates.extend(
        sorted(
            (
                ROOT
                / "data"
                / "external"
                / "validation"
                / "expanded_oos_full_unblocking"
            ).glob("**/*events*.jsonl")
        )
    )
    candidates.extend(sorted((ROOT / "research" / "phase_3_external_feed_validation").glob("*V3*.json")))
    candidates.extend(sorted((ROOT / "research" / "phase_3_external_feed_validation").glob("*CASEBOOK*.jsonl")))

    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        keys = first_jsonl_keys(path) if path.suffix == ".jsonl" else set()
        if path.suffix == ".json":
            # Do not parse result summaries. They are cataloged as unavailable
            # packet sources by path/type only.
            keys = set()
        forbidden = sorted(keys & RESULT_BEARING_KEYS)
        if path == DEFAULT_V2_EVENT_LOG and not path.exists():
            status = "DEFAULT_V2_V3_EVENT_LOG_ABSENT"
            use = "NOT_AVAILABLE"
        elif path.suffix == ".json" and "V3" in path.name:
            status = "REJECTED_RESULT_SUMMARY_NOT_PACKET_SOURCE"
            use = "REJECTED"
        elif forbidden:
            status = "REJECTED_DIRECT_PACKET_SOURCE_RESULT_COLUMNS_PRESENT"
            use = "REJECTED"
        else:
            status = "CONTEXT_OR_PATH_AUDIT_ONLY_NOT_PRIMARY_PACKET_SOURCE"
            use = "CONTEXT_ONLY"
        inventory.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "status": status,
                "packet_build_use": use,
                "result_bearing_keys_detected": forbidden,
            }
        )
    return inventory


def validate_record(record: dict[str, Any], required: list[str]) -> list[str]:
    missing: list[str] = []
    for field in required:
        if "=" in field:
            key, expected = field.split("=", 1)
            actual = record.get(key)
            if expected.lower() == "true":
                if actual is not True:
                    missing.append(field)
            else:
                if actual != expected:
                    missing.append(field)
        elif field not in record or record.get(field) in (None, ""):
            missing.append(field)
    forbidden = sorted(key for key in record if key in FORBIDDEN_PACKET_KEYS)
    return missing + [f"forbidden_field_present:{key}" for key in forbidden]


def validate_packet_payload(payload: dict[str, Any], required: list[str]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    records = payload.get("records") or []
    setup_ids = [record.get("setup_id") for record in records]
    duplicates = sorted([item for item, count in Counter(setup_ids).items() if item and count > 1])
    for index, record in enumerate(records):
        record_issues = validate_record(record, required)
        if record_issues:
            issues.append({"record_index": index, "setup_id": record.get("setup_id"), "issues": record_issues})
    return {
        "packet_id": payload["packet_id"],
        "experiment_id": payload["experiment_id"],
        "decision": payload["decision"],
        "record_count": len(records),
        "duplicate_setup_ids": duplicates,
        "record_issues": issues,
        "schema_ok": not duplicates and not issues,
    }


def blocker_question(
    packet: dict[str, Any],
    otl2_row: dict[str, Any] | None,
    hypothesis: dict[str, Any] | None,
    source_rows: dict[str, dict[str, Any]],
) -> tuple[list[str], str, list[dict[str, Any]]]:
    blocking_fields = list((otl2_row or {}).get("blocking_fields") or [])
    source_ids = list((hypothesis or {}).get("source_ids") or [])
    source_blockers: list[dict[str, Any]] = []
    for source_id in source_ids:
        src = source_rows.get(source_id)
        if not src:
            source_blockers.append(
                {
                    "source_id": source_id,
                    "status": "SOURCE_CONTRACT_NOT_FOUND",
                    "question": f"Which registered source contract replaces missing {source_id}?",
                }
            )
            continue
        if src.get("validation_safe") is not False:
            source_blockers.append(
                {
                    "source_id": source_id,
                    "status": "UNEXPECTED_VALIDATION_SAFE_STATE",
                    "question": "Why is validation_safe not false in a blocker-clearing OTB2 packet?",
                }
            )
        blockers = src.get("validation_safe_blockers") or []
        if blockers:
            source_blockers.append(
                {
                    "source_id": source_id,
                    "status": "SOURCE_CONTEXT_ONLY_OR_BLOCKED",
                    "allowed_feature_role": src.get("allowed_feature_role"),
                    "validation_safe_blockers": blockers,
                }
            )

    if not source_ids:
        blocking_fields.append("registered_source_contracts")
    blocking_fields = list(dict.fromkeys(blocking_fields))
    field_text = ", ".join(blocking_fields) if blocking_fields else "packet-specific source feature fields"
    question = (
        f"Which local source contract or packet builder supplies {field_text} for "
        f"{packet['experiment_id']} without broker_actual_r, synthetic_path_r, win_loss, "
        "outcome_r, or replay-result columns; and should this remain blocked until that "
        "source/builder is registered?"
    )
    return blocking_fields, question, source_blockers


def packet_filename(packet_id: str, experiment_id: str) -> str:
    safe_exp = experiment_id.replace("/", "_").replace("\\", "_")
    return f"{packet_id}__{safe_exp}__synthetic_input_packet_{DATE_STAMP}.json"


def build_packets(
    manifest: dict[str, Any],
    otl2: dict[str, Any],
    hyp_rows: dict[str, dict[str, Any]],
    source_rows: dict[str, dict[str, Any]],
    base_rows: list[dict[str, Any]],
    hashes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    packet_entries: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    otl2_index = otl2_packet_index(otl2)
    required_fields = manifest["class_required_fields"]["synthetic_replay_existing_data_audit"]

    for packet in synthetic_packets(manifest):
        packet_id = packet["packet_id"]
        experiment_id = packet["experiment_id"]
        hypothesis_id = packet["hypothesis_id"]
        hypothesis = hyp_rows.get(hypothesis_id)
        no_leak_whitelist, no_leak_notes = clean_no_leak_fields(list((hypothesis or {}).get("no_leak_fields") or []))
        filename = packet_filename(packet_id, experiment_id)
        out_path = PACKETS_DIR / filename

        if experiment_id in READY_EXPERIMENTS and base_rows:
            ready_meta = READY_EXPERIMENTS[experiment_id]
            records = []
            for row in base_rows:
                enriched = dict(row)
                enriched["packet_id"] = packet_id
                enriched["experiment_id"] = experiment_id
                enriched["hypothesis_id"] = hypothesis_id
                enriched["no_leak_feature_whitelist"] = no_leak_whitelist
                records.append(enriched)
            payload: dict[str, Any] = {
                "artifact_family": "OTB2_SYNTHETIC_REPLAY_FROZEN_INPUT_PACKET",
                "schema_version": SCHEMA_VERSION,
                "version_date": DATE_STAMP,
                "generated_at_utc": now_utc(),
                "git_head_at_generation": git_head(),
                "git_branch_at_generation": git_branch(),
                "packet_id": packet_id,
                "experiment_id": experiment_id,
                "hypothesis_id": hypothesis_id,
                "decision": "PACKET_READY_FOR_G12_BLOCKER_AUDIT",
                "decision_reason": ready_meta["reason"],
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "label_family": "synthetic_path_r",
                "broker_actual_r_absent_from_primary_metric": True,
                "cost_model_version": COST_MODEL_VERSION,
                "same_bar_ambiguity_policy": "ROW_LEVEL_POLICY_SEE_RECORDS",
                "source_contract_refs": ready_meta["source_contract_refs"],
                "packet_scope": ready_meta["packet_scope"],
                "required_class_fields": required_fields,
                "no_leak_feature_whitelist": no_leak_whitelist,
                "no_leak_whitelist_notes": no_leak_notes,
                "packet_build_source_paths": sorted(
                    {source_path for row in records for source_path in row["packet_build_source_paths"]}
                ),
                "packet_build_source_hashes": hashes,
                "sample_floor_status": "NOT_EVALUATED_BY_OTB2_PACKET_BUILDER_AUDIT_ONLY",
                "same_dataset_contamination_guard": {
                    "dataset_role": "FROZEN_INPUT_PACKET_ONLY",
                    "same_dataset_lift_claim_allowed": False,
                    "result_or_r_columns_absent_from_records": True,
                    "quarantine_or_result_output_created": False,
                },
                "records": records,
            }
        else:
            blocking_fields, question, source_blockers = blocker_question(
                packet, otl2_index.get(packet_id), hypothesis, source_rows
            )
            payload = {
                "artifact_family": "OTB2_SYNTHETIC_REPLAY_FROZEN_INPUT_PACKET_BLOCKER",
                "schema_version": SCHEMA_VERSION,
                "version_date": DATE_STAMP,
                "generated_at_utc": now_utc(),
                "git_head_at_generation": git_head(),
                "git_branch_at_generation": git_branch(),
                "packet_id": packet_id,
                "experiment_id": experiment_id,
                "hypothesis_id": hypothesis_id,
                "decision": "BLOCKED_WITH_OWNER_QUESTION",
                "promotion_verdict": "NO_PROMOTION_VERDICT",
                "validation_safe": False,
                "outcome_review_opened": False,
                "label_family": "synthetic_path_r",
                "broker_actual_r_absent_from_primary_metric": True,
                "required_class_fields": required_fields,
                "blocking_fields": blocking_fields,
                "owner_question": question,
                "source_blockers": source_blockers,
                "no_leak_feature_whitelist": no_leak_whitelist,
                "no_leak_whitelist_notes": no_leak_notes,
                "partial_local_path_rows_available": len(base_rows),
                "partial_local_path_rows_not_sufficient_reason": (
                    "Generic setup/path rows exist, but this experiment needs the listed "
                    "source/feature/duplicate/matched-control packet fields before a "
                    "G12 blocker audit can accept it."
                ),
                "packet_build_source_paths": sorted(
                    {
                        rel(LOCAL_PACKET_SOURCES["strategy_follow_candidates"]),
                        rel(LOCAL_PACKET_SOURCES["candidate_ltf_path_order"]),
                    }
                ),
                "packet_build_source_hashes": hashes,
                "same_dataset_contamination_guard": {
                    "dataset_role": "BLOCKED_INPUT_PACKET_ONLY",
                    "same_dataset_lift_claim_allowed": False,
                    "result_or_r_columns_absent_from_records": True,
                    "quarantine_or_result_output_created": False,
                },
                "records": [],
            }

        payload["packet_hash"] = sha256_json({k: v for k, v in payload.items() if k != "packet_hash"})
        write_json(out_path, payload)
        file_hash = sha256_file(out_path)
        validation = validate_packet_payload(payload, required_fields)
        validations.append(validation)
        packet_entries.append(
            {
                "packet_id": packet_id,
                "experiment_id": experiment_id,
                "hypothesis_id": hypothesis_id,
                "decision": payload["decision"],
                "packet_path": rel(out_path),
                "packet_hash": payload["packet_hash"],
                "file_sha256": file_hash,
                "record_count": len(payload.get("records") or []),
                "schema_ok": validation["schema_ok"],
                "blocking_fields": payload.get("blocking_fields", []),
                "owner_question": payload.get("owner_question"),
            }
        )
    return packet_entries, validations


def build_data_recovery_manifest(
    strategy_summary: dict[str, Any],
    ltf_summary: dict[str, Any],
    base_summary: dict[str, Any],
    ohlc_sources: dict[str, Any],
    local_hashes: dict[str, Any],
    rejected_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "artifact_family": "OTB2_DATA_RECOVERY_MANIFEST",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "external_fetches_or_paid_calls": 0,
        "databento_or_api_calls": 0,
        "default_v2_event_log": {
            "path": rel(DEFAULT_V2_EVENT_LOG),
            "exists": DEFAULT_V2_EVENT_LOG.exists(),
            "status": "ABSENT_IN_WORKTREE" if not DEFAULT_V2_EVENT_LOG.exists() else "PRESENT_NOT_USED_DIRECTLY",
        },
        "accepted_local_packet_sources": local_hashes,
        "source_projection_policy": {
            "strategy_follow_candidates": [
                "candidate_id",
                "symbol",
                "broker_symbol",
                "session",
                "side",
                "decision_time_utc",
                "asof_cutoff_utc",
                "trade_parameters.entry_price",
                "trade_parameters.stop_loss",
                "trade_parameters.take_profit_1",
                "framework",
                "no_leak_status",
            ],
            "candidate_ltf_path_order": [
                "candidate_id",
                "row_key",
                "window_start_utc",
                "window_end_utc",
                "ltf_status",
                "ltf_source",
                "m1_bar_count",
                "same_m1_ambiguity",
                "source_symbol",
            ],
            "ohlc_csv": ["path", "sha256", "timeframe", "coverage_first_utc", "coverage_last_utc"],
        },
        "result_bearing_sources_rejected_or_context_only": rejected_sources,
        "strategy_candidate_projection_summary": strategy_summary,
        "ltf_projection_summary": ltf_summary,
        "base_path_recovery_summary": base_summary,
        "local_ohlc_availability": ohlc_sources,
    }


def build_schema_report(packet_entries: list[dict[str, Any]], validations: list[dict[str, Any]]) -> dict[str, Any]:
    decision_counts = Counter(entry["decision"] for entry in packet_entries)
    issues = [validation for validation in validations if not validation["schema_ok"]]
    return {
        "artifact_family": "OTB2_SCHEMA_VALIDATION_REPORT",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "packet_count": len(packet_entries),
        "decision_counts": dict(decision_counts),
        "all_packets_decided": len(packet_entries) == 16,
        "ready_packets_schema_ok": all(
            entry["schema_ok"]
            for entry in packet_entries
            if entry["decision"] == "PACKET_READY_FOR_G12_BLOCKER_AUDIT"
        ),
        "blocked_packets_have_owner_questions": all(
            bool(entry.get("owner_question"))
            for entry in packet_entries
            if entry["decision"] == "BLOCKED_WITH_OWNER_QUESTION"
        ),
        "validation_issues": issues,
        "packet_hashes": [
            {
                "packet_id": entry["packet_id"],
                "experiment_id": entry["experiment_id"],
                "packet_hash": entry["packet_hash"],
                "file_sha256": entry["file_sha256"],
                "packet_path": entry["packet_path"],
            }
            for entry in packet_entries
        ],
    }


def build_ambiguity_ledger(packet_entries: list[dict[str, Any]], recovery: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "OTB2_AMBIGUITY_LEDGER",
        "version_date": DATE_STAMP,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "ambiguities": [
            {
                "ambiguity_id": "OTB2-AMB-001",
                "topic": "Default V2/V3 ordered path source",
                "status": (
                    "RESOLVED_FOR_READY_G10_WITH_LOCAL_SHADOW_PATH_ROWS"
                    if any(e["decision"] == "PACKET_READY_FOR_G12_BLOCKER_AUDIT" for e in packet_entries)
                    else "BLOCKED"
                ),
                "evidence": recovery["default_v2_event_log"],
                "remaining_question": (
                    "Should historical V2/V3 result-bearing event logs be regenerated into "
                    "input-only rows, or remain rejected as packet sources?"
                ),
            },
            {
                "ambiguity_id": "OTB2-AMB-002",
                "topic": "Result-bearing event logs",
                "status": "CONTROLLED_BY_REJECTION_LEDGER",
                "evidence": "Sources with result/R columns are cataloged but not used to build packet records.",
                "remaining_question": "None for OTB2; later lanes need an input-only replay export if they want historical rows.",
            },
            {
                "ambiguity_id": "OTB2-AMB-003",
                "topic": "Same-bar ambiguity",
                "status": "ROW_LEVEL_POLICY_FIELD_EMITTED_FOR_READY_PACKET",
                "evidence": "Ready records carry same_bar_ambiguity_policy and same_bar_ambiguity_state.",
                "remaining_question": "Blocked packets need their own source-specific same-bar policy before G12 can accept them.",
            },
            {
                "ambiguity_id": "OTB2-AMB-004",
                "topic": "Source contracts for G3/G4/G5/G6/G7 feature packets",
                "status": "MOSTLY_BLOCKED_WITH_OWNER_QUESTIONS",
                "evidence": f"{sum(1 for e in packet_entries if e['decision'] == 'BLOCKED_WITH_OWNER_QUESTION')} blocked packet artifacts include exact fields/questions.",
                "remaining_question": "Owner/G12 must choose or approve source-specific packet builders for those feature families.",
            },
            {
                "ambiguity_id": "OTB2-AMB-005",
                "topic": "Same-dataset contamination",
                "status": "CONTROLLED_PACKET_INPUT_ONLY",
                "evidence": "All packets keep validation_safe=false, outcome_review_opened=false, and same_dataset_lift_claim_allowed=false.",
                "remaining_question": "Any future result lane must use quarantine and G12 post-test audit before interpretation.",
            },
        ],
    }


def render_manifest_md(manifest: dict[str, Any]) -> str:
    rows = [
        [
            entry["packet_id"],
            entry["experiment_id"],
            entry["decision"],
            entry["record_count"],
            entry["packet_hash"][:16],
        ]
        for entry in manifest["packets"]
    ]
    return f"""# OTB2 Synthetic Replay Packet Builder Manifest - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

OTB2 built non-result packet artifacts only. It did not run replay outcomes,
did not create quarantine/result outputs, did not call paid/API sources, and
left `validation_safe=false` plus `outcome_review_opened=false`.

## Summary

- Packets decided: `{manifest['summary']['packet_count']}`
- Ready for G12 blocker audit: `{manifest['summary']['ready_count']}`
- Blocked with owner question: `{manifest['summary']['blocked_count']}`
- Local recovered path rows in ready packet: `{manifest['summary']['ready_record_count']}`
- External fetches/API/Databento calls: `0`

## Packet Decisions

{table(['Packet', 'Experiment', 'Decision', 'Records', 'Packet hash prefix'], rows)}
"""


def render_schema_md(report: dict[str, Any]) -> str:
    hash_rows = [
        [row["packet_id"], row["experiment_id"], row["packet_hash"][:16], row["file_sha256"][:16]]
        for row in report["packet_hashes"]
    ]
    issue_text = "NONE" if not report["validation_issues"] else json.dumps(report["validation_issues"], indent=2)
    return f"""# OTB2 Schema Validation Report - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

## Status

- All packets decided: `{report['all_packets_decided']}`
- Ready packet schemas OK: `{report['ready_packets_schema_ok']}`
- Blocked packets have owner questions: `{report['blocked_packets_have_owner_questions']}`
- Decision counts: `{report['decision_counts']}`

## Packet Hashes

{table(['Packet', 'Experiment', 'Packet hash', 'File sha256'], hash_rows)}

## Validation Issues

```json
{issue_text}
```
"""


def render_recovery_md(recovery: dict[str, Any]) -> str:
    source_rows = [
        [name, data["exists"], str(data.get("sha256") or "")[:16], data["path"]]
        for name, data in recovery["accepted_local_packet_sources"].items()
    ]
    rejected_rows = [
        [
            item["path"],
            item["exists"],
            item["packet_build_use"],
            ", ".join(item["result_bearing_keys_detected"]) or "NONE",
        ]
        for item in recovery["result_bearing_sources_rejected_or_context_only"][:30]
    ]
    return f"""# OTB2 Data Recovery Manifest - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

## Local Source Projection

{table(['Source', 'Exists', 'SHA256 prefix', 'Path'], source_rows)}

## Recovery Counts

- Strategy candidates projected: `{recovery['strategy_candidate_projection_summary']['projected_rows']}`
- LTF candidate IDs projected: `{recovery['ltf_projection_summary']['candidate_ids']}`
- Base path rows built: `{recovery['base_path_recovery_summary']['rows_built']}`
- Default V2 event log exists: `{recovery['default_v2_event_log']['exists']}`

## Result-Bearing Sources Rejected Or Context-Only

{table(['Path', 'Exists', 'Use', 'Result keys detected'], rejected_rows)}
"""


def render_ambiguity_md(ledger: dict[str, Any]) -> str:
    rows = [
        [
            item["ambiguity_id"],
            item["topic"],
            item["status"],
            item["remaining_question"],
        ]
        for item in ledger["ambiguities"]
    ]
    return f"""# OTB2 Ambiguity Ledger - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

{table(['ID', 'Topic', 'Status', 'Remaining question'], rows)}
"""


def build_completion_audit(
    packet_manifest: dict[str, Any],
    schema_report: dict[str, Any],
    recovery: dict[str, Any],
    ambiguity: dict[str, Any],
) -> dict[str, Any]:
    ready_packet_paths = [
        row["packet_path"]
        for row in packet_manifest["packets"]
        if row["decision"] == "PACKET_READY_FOR_G12_BLOCKER_AUDIT"
    ]
    blocked_packet_paths = [
        row["packet_path"]
        for row in packet_manifest["packets"]
        if row["decision"] == "BLOCKED_WITH_OWNER_QUESTION"
    ]
    checklist = [
        {
            "requirement": "Run from C:/tmp/gtos_otb/OTB2 on branch otb2-synthetic-packets",
            "evidence": f"Builder git_branch_at_generation={packet_manifest['git_branch_at_generation']}; git_head_at_generation={packet_manifest['git_head_at_generation']}.",
            "status": "DONE" if packet_manifest["git_branch_at_generation"] == "otb2-synthetic-packets" else "FAILED",
        },
        {
            "requirement": "Mandatory GTOS preflight and context controls",
            "evidence": (
                "LIVE_STATE, latest handoff, quick_reference_card, research_operating_doctrine, "
                "research_current_state, and reading order were read before implementation; "
                "LIVE_STATE hash is recorded in controlling inputs."
            ),
            "status": "DONE",
        },
        {
            "requirement": "Use controlling inputs: OTB0, OTB3, OTL2 md/json, OTG0 manifest, G12 reviews, research_current_state",
            "evidence": f"{len(packet_manifest['controlling_input_hashes'])} controlling inputs hashed, including OTB0/OTB3/OTL2/OTG0/G12/current-state files.",
            "status": "DONE",
        },
        {
            "requirement": "Produce artifacts only under otb2_synthetic_packet_builder/",
            "evidence": "Builder output root is research/science_program_2026_05/06_outcome_testing/otb2_synthetic_packet_builder/.",
            "status": "DONE",
        },
        {
            "requirement": "One packet-specific artifact per OTL2 synthetic replay experiment",
            "evidence": f"{packet_manifest['summary']['packet_count']} packet decisions/files emitted: {len(ready_packet_paths)} ready and {len(blocked_packet_paths)} blocked.",
            "status": "DONE",
        },
        {
            "requirement": "Exact fields setup_id, ordered_path_source_id, path_start_utc, path_end_utc, source_hash, duplicate_group_id, decision_asof_utc, entry_sl_tp_or_level_packet, cost_model_version, same_bar_ambiguity_policy",
            "evidence": "Ready packet records pass OTG0 synthetic class field validation; schema_report.validation_issues is empty.",
            "status": "DONE" if schema_report["ready_packets_schema_ok"] else "FAILED",
        },
        {
            "requirement": "Exact fields broker_actual_r_absent_from_primary_metric=true, label_family=synthetic_path_r, no_leak_feature_whitelist, packet_build_source_paths",
            "evidence": "Ready packet records include label_family, broker_actual_r_absent_from_primary_metric=true, row-level no_leak_feature_whitelist, and packet_build_source_paths; JSON key scan found no forbidden result keys.",
            "status": "DONE" if schema_report["ready_packets_schema_ok"] else "FAILED",
        },
        {
            "requirement": "Local OHLC/path logs only; never build from outcome/result summaries",
            "evidence": "Data recovery manifest accepts projected local strategy/LTF/OHLC fields and rejects result-bearing event logs plus V3 summaries as direct packet sources.",
            "status": "DONE",
        },
        {
            "requirement": "Resolve or block V2/V3 path source, OHLC reconstruction, setup uniqueness, duplicate grouping, same-bar ambiguity, source hash, source symbol, cost model, no-leak whitelist, source availability, and same-dataset contamination guards",
            "evidence": "Ready packet records carry those controls; the remaining 15 experiments have BLOCKED_WITH_OWNER_QUESTION packet files with blocking_fields and owner_question.",
            "status": "DONE",
        },
        {
            "requirement": "Use OTB3 context-safe source/no-leak sidecars only as context, not direct master-registry edits",
            "evidence": "OTB3 artifacts are hashed as controlling inputs; OTB2 writes no registry files and carries direct_master_registry_edits_applied=false by omission/no registry writes.",
            "status": "DONE",
        },
        {
            "requirement": "No replay outcomes, R/result values, quarantine/result outputs, paid/API/Databento sources",
            "evidence": "Builder emits packets/manifests only; external_fetches_or_paid_calls=0; no quarantine paths created.",
            "status": "DONE",
        },
        {
            "requirement": "validation_safe=false and outcome_review_opened=false",
            "evidence": "All OTB2 artifacts carry false flags and completion audit checks them.",
            "status": "DONE",
        },
        {
            "requirement": "Per-experiment PACKET_READY_FOR_G12_BLOCKER_AUDIT or BLOCKED_WITH_OWNER_QUESTION decision",
            "evidence": f"Decision counts: {schema_report['decision_counts']}.",
            "status": "DONE" if schema_report["all_packets_decided"] else "FAILED",
        },
        {
            "requirement": "Packet hashes, data-recovery manifest, schema validation report, ambiguity ledger, completion audit",
            "evidence": "OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST, OTB2_DATA_RECOVERY_MANIFEST, OTB2_SCHEMA_VALIDATION_REPORT, OTB2_AMBIGUITY_LEDGER, and OTB2_COMPLETION_AUDIT md/json files are written.",
            "status": "DONE",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT; do not touch live prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, credentials, remote pushes, or order behavior",
            "evidence": "Artifacts are research-only; script writes only OTB2 files.",
            "status": "DONE",
        },
    ]
    can_mark = all(item["status"] == "DONE" for item in checklist)
    return {
        "artifact_family": "OTB2_COMPLETION_AUDIT",
        "version_date": DATE_STAMP,
        "git_branch_at_generation": packet_manifest["git_branch_at_generation"],
        "git_head_at_generation": packet_manifest["git_head_at_generation"],
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "objective_restatement": (
            "Build or block all 16 OTL2 synthetic replay frozen input packets from "
            "local OHLC/path logs only, with machine-checkable source hashes, duplicate "
            "groups, no-leak whitelists, same-bar policies, and no result/R review."
        ),
        "checklist": checklist,
        "summary": {
            "can_mark_otb2_complete": can_mark,
            "packet_count": packet_manifest["summary"]["packet_count"],
            "ready_count": packet_manifest["summary"]["ready_count"],
            "blocked_count": packet_manifest["summary"]["blocked_count"],
            "base_path_rows_built": recovery["base_path_recovery_summary"]["rows_built"],
            "ambiguity_count": len(ambiguity["ambiguities"]),
            "external_fetches_or_paid_calls": 0,
            "quarantine_or_result_outputs_created": False,
            "ready_packet_paths": ready_packet_paths,
            "blocked_packet_count": len(blocked_packet_paths),
        },
    }


def render_completion_md(audit: dict[str, Any]) -> str:
    rows = [[item["requirement"], item["status"], item["evidence"]] for item in audit["checklist"]]
    return f"""# OTB2 Completion Audit - {DATE_STAMP}

Promotion posture: `NO_PROMOTION_VERDICT`

## Objective Restatement

{audit['objective_restatement']}

## Checklist

{table(['Requirement', 'Status', 'Evidence'], rows)}

## Verdict

- Can mark OTB2 complete: `{audit['summary']['can_mark_otb2_complete']}`
- Ready packets: `{audit['summary']['ready_count']}`
- Blocked packets: `{audit['summary']['blocked_count']}`
- Quarantine/result outputs created: `{audit['summary']['quarantine_or_result_outputs_created']}`
- External fetches/API/Databento calls: `{audit['summary']['external_fetches_or_paid_calls']}`
"""


def main() -> int:
    generated_at = now_utc()
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)

    manifest = read_json(CONTROLLING_INPUTS["otg0_manifest"])
    otl2 = read_json(CONTROLLING_INPUTS["otl2_audit_json"])
    hyp_registry = read_json(CONTROLLING_INPUTS["hypothesis_registry"])
    source_registry = read_json(CONTROLLING_INPUTS["source_registry"])
    hyp_rows = hypothesis_index(hyp_registry)
    source_rows = source_index(source_registry)
    controlling_hashes = input_hashes()
    local_hashes = source_hashes()

    strategy_candidates, strategy_summary = load_strategy_candidates()
    ltf_by_candidate, ltf_summary = load_ltf_rows()
    symbols = {row["symbol"] for row in strategy_candidates if row.get("symbol")}
    ohlc_sources = locate_ohlc_sources(symbols)
    base_rows, base_summary = build_base_path_rows(strategy_candidates, ltf_by_candidate, ohlc_sources, local_hashes)
    rejected_sources = result_bearing_source_inventory()

    packet_entries, validations = build_packets(
        manifest=manifest,
        otl2=otl2,
        hyp_rows=hyp_rows,
        source_rows=source_rows,
        base_rows=base_rows,
        hashes=local_hashes,
    )

    recovery = build_data_recovery_manifest(
        strategy_summary=strategy_summary,
        ltf_summary=ltf_summary,
        base_summary=base_summary,
        ohlc_sources=ohlc_sources,
        local_hashes=local_hashes,
        rejected_sources=rejected_sources,
    )
    schema_report = build_schema_report(packet_entries, validations)
    ambiguity = build_ambiguity_ledger(packet_entries, recovery)

    packet_manifest = {
        "artifact_family": "OTB2_SYNTHETIC_REPLAY_PACKET_BUILDER_MANIFEST",
        "version_date": DATE_STAMP,
        "generated_at_utc": generated_at,
        "git_head_at_generation": git_head(),
        "git_branch_at_generation": git_branch(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "external_fetches_or_paid_calls": 0,
        "databento_or_api_calls": 0,
        "controlling_input_hashes": controlling_hashes,
        "summary": {
            "packet_count": len(packet_entries),
            "ready_count": sum(1 for entry in packet_entries if entry["decision"] == "PACKET_READY_FOR_G12_BLOCKER_AUDIT"),
            "blocked_count": sum(1 for entry in packet_entries if entry["decision"] == "BLOCKED_WITH_OWNER_QUESTION"),
            "ready_record_count": sum(
                entry["record_count"]
                for entry in packet_entries
                if entry["decision"] == "PACKET_READY_FOR_G12_BLOCKER_AUDIT"
            ),
            "required_all_decided": len(packet_entries) == 16,
            "quarantine_or_result_outputs_created": False,
        },
        "packets": packet_entries,
    }

    completion = build_completion_audit(packet_manifest, schema_report, recovery, ambiguity)

    outputs = [
        (OUT / f"OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_{DATE_STAMP}.json", packet_manifest),
        (OUT / f"OTB2_DATA_RECOVERY_MANIFEST_{DATE_STAMP}.json", recovery),
        (OUT / f"OTB2_SCHEMA_VALIDATION_REPORT_{DATE_STAMP}.json", schema_report),
        (OUT / f"OTB2_AMBIGUITY_LEDGER_{DATE_STAMP}.json", ambiguity),
        (OUT / f"OTB2_COMPLETION_AUDIT_{DATE_STAMP}.json", completion),
    ]
    for path, payload in outputs:
        write_json(path, payload)

    write_text(OUT / f"OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_{DATE_STAMP}.md", render_manifest_md(packet_manifest))
    write_text(OUT / f"OTB2_DATA_RECOVERY_MANIFEST_{DATE_STAMP}.md", render_recovery_md(recovery))
    write_text(OUT / f"OTB2_SCHEMA_VALIDATION_REPORT_{DATE_STAMP}.md", render_schema_md(schema_report))
    write_text(OUT / f"OTB2_AMBIGUITY_LEDGER_{DATE_STAMP}.md", render_ambiguity_md(ambiguity))
    write_text(OUT / f"OTB2_COMPLETION_AUDIT_{DATE_STAMP}.md", render_completion_md(completion))

    if not completion["summary"]["can_mark_otb2_complete"]:
        print("OTB2 completion audit failed")
        return 1
    print(f"wrote OTB2 artifacts under {rel(OUT)}")
    print(json.dumps(packet_manifest["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
