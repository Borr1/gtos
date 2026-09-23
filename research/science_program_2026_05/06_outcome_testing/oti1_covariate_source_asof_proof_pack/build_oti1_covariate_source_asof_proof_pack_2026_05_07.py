"""Build the OTI1 covariate source/as-of proof pack.

This is a research-control builder only. It reconstructs accepted OTI1
lifecycle packet provenance and audits covariate source/as-of proof without
running outcomes, scoring covariate-conditioned results, inspecting broker
actual-R values, opening blocked-packet outcomes, calling paid/API sources, or
touching live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_STAMP = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
CONTROL = ROOT / "research/science_program_2026_05/00_control"
PREREG = ROOT / "research/science_program_2026_05/03_experiment_specs"

OTB1R = OT / "otb1r_input_only_lifecycle_rebuild"
OTI1 = OT / "oti1_lifecycle_quarantined_results"
G12_OTB = OT / "g12_otb_rebuild_reaudit"
G12_OTI = OT / "g12_oti_post_test_audit"
OTL3 = OT / "otl3_source_asof_cleanup"
OTB3 = OT / "otb3_source_noleak_cleanup"
G0_OTI = OT / "g0_oti_quarantine_synthesis"

ACCEPTED_PACKET_IDS = [
    "OTG0-PKT-011",
    "OTG0-PKT-016",
    "OTG0-PKT-025",
    "OTG0-PKT-029",
    "OTG0-PKT-045",
    "OTG0-PKT-055",
    "OTG0-PKT-059",
    "OTG0-PKT-071",
    "OTG0-PKT-079",
]

PACKET_TO_COVARIATE_FOCUS = {
    "OTG0-PKT-016": ["friction"],
    "OTG0-PKT-025": ["realized_volatility", "volatility_of_volatility"],
    "OTG0-PKT-029": ["source_freshness_context"],
    "OTG0-PKT-045": ["footprint_absorption_orderflow_context"],
    "OTG0-PKT-055": ["local_news_schedule"],
    "OTG0-PKT-059": ["macro_attention", "local_news_schedule"],
    "OTG0-PKT-071": ["fomc_event_windows"],
    "OTG0-PKT-079": ["cboe_short_vol_context", "friction"],
}

COVARIATES: dict[str, dict[str, Any]] = {
    "source_freshness_context": {
        "label": "source-freshness context",
        "source_ids": ["OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS"],
        "allowed_feature_role": "Lifecycle source provenance only: decision_asof_utc/source_capture_utc/source_hash for existing lifecycle/no-fill rows.",
        "label_family_boundary": "May support lifecycle_no_fill provenance only; not synthetic_path_r, broker_actual_r, win/loss, or return labels.",
        "clear_packet_ids": ACCEPTED_PACKET_IDS,
        "next_evidence_needed": "",
    },
    "local_news_schedule": {
        "label": "local news schedule",
        "source_ids": ["SRC-G5-NEWS-CALENDAR-LOCAL-001"],
        "allowed_feature_role": "Schedule and stale-calendar context only; no release result, surprise, sentiment, or live-filter change.",
        "label_family_boundary": "May label local calendar context separately from lifecycle_no_fill rows; must not merge with broker actual-R or synthetic path-R.",
        "clear_packet_ids": ["OTG0-PKT-055", "OTG0-PKT-059"],
        "next_evidence_needed": "For any event-window result claim: source-hashed event-window matcher rows with event_id, event_time_utc, calendar_updated_at_utc, stale-state policy, decision_asof_utc, parser version, and no-lookahead fixtures.",
    },
    "friction": {
        "label": "friction",
        "source_ids": ["G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE", "SRC-G11-LOCAL-INSTRUMENT-EXPANSION"],
        "allowed_feature_role": "Blocked for packet-bound decision-time friction features; existing sidecars are context-only proposals.",
        "label_family_boundary": "Friction eligibility must be computed before outcome labels and kept separate from lifecycle/no-fill counts.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Packet-bound spread_at_decision, spread_atr_ratio_at_decision, tick_value_asof, contract_spec_version_asof, commission_schedule_asof, min_stop_distance_asof, source hash, parser/version, and feature_asof_utc <= decision_asof_utc.",
    },
    "realized_volatility": {
        "label": "realized volatility",
        "source_ids": ["SRC-G2-FORWARD-SHADOW-LIFECYCLE"],
        "allowed_feature_role": "Blocked until realized-vol features are source-hashed and packet-bound as of decision time.",
        "label_family_boundary": "Volatility covariates may condition lifecycle_no_fill only after packet-bound proof; they do not create return labels.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Frozen realized-vol formula/window, raw OHLC/tick input file path and sha256, parser/version, feature_window_end_utc <= decision_asof_utc, feature_asof_utc, per-row source_hash, and no-lookahead fixture.",
    },
    "volatility_of_volatility": {
        "label": "volatility-of-volatility",
        "source_ids": ["SRC-G2-FORWARD-SHADOW-LIFECYCLE"],
        "allowed_feature_role": "Blocked until vol-of-vol features are source-hashed and packet-bound as of decision time.",
        "label_family_boundary": "Vol-of-vol covariates may condition lifecycle_no_fill only after packet-bound proof; they do not create return labels.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Frozen vol-of-vol formula/window, raw realized-vol source lineage, parser/version, feature_window_end_utc <= decision_asof_utc, feature_asof_utc, per-row source_hash, and no-lookahead fixture.",
    },
    "footprint_absorption_orderflow_context": {
        "label": "footprint/absorption/orderflow context",
        "source_ids": [
            "SRC-G4-DATABENTO-GLBX-MDP3",
            "SRC-G4-SIERRA-DEPTH-SCID",
            "SRC-G4-LOCAL-GTOS-ORDERFLOW-ARTIFACTS",
        ],
        "allowed_feature_role": "Blocked for packet-bound orderflow/absorption features; local and official references are source-contract context only.",
        "label_family_boundary": "Orderflow features must be pre-decision context only and must not include fill outcomes or broker account history.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Packet-bound orderflow source id, license/access state, raw cache path/hash, source symbol/proxy map, parser/version, feature window start/end <= decision_asof_utc, absorption classifier version, and no-lookahead fixture.",
    },
    "macro_attention": {
        "label": "macro-attention",
        "source_ids": [
            "SRC-G5-NEWS-CALENDAR-LOCAL-001",
            "SRC-G7-FED-FOMC-001",
            "SRC-G7-FRED-RATES-001",
            "SRC-G7-BIS-STATS-001",
            "SRC-G7-ICE-DXY-001",
            "SRC-G7-LOCAL-GTOS-MACRO-001",
        ],
        "allowed_feature_role": "Blocked beyond local schedule/stale-calendar context; macro-attention source stack is not packet-bound.",
        "label_family_boundary": "Macro-attention features must remain context labels separate from lifecycle and return labels.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Official/raw source cache paths and hashes, exact series/table ids, publication/vintage/as-of rules, parser versions, event/source freshness state, feature_asof_utc <= decision_asof_utc, and no-lookahead fixtures.",
    },
    "fomc_event_windows": {
        "label": "FOMC/event windows",
        "source_ids": ["SRC-G7-FED-FOMC-001", "SRC-G5-NEWS-CALENDAR-LOCAL-001"],
        "allowed_feature_role": "Blocked for FOMC window classification; cached official page currently supports date-only/context evidence, not packet-bound event-time windows.",
        "label_family_boundary": "FOMC/event-window labels must be separate covariates and cannot include post-release surprise/outcome.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Source-hashed event-window parser output with event_time_utc, source/cache time, raw official cache hash, parser/version, stale-source handling, decision_asof_utc, and no-lookahead fixture.",
    },
    "cboe_short_vol_context": {
        "label": "Cboe/short-vol context",
        "source_ids": ["SRC-G8-CBOE-METHODOLOGY-002", "SRC-G8-CBOE-VOL-CSV-001"],
        "allowed_feature_role": "Blocked for decision-row short-vol context; methodology pages are context-only and CSV publication/legal/no-lookahead proof remains unresolved.",
        "label_family_boundary": "Short-vol context must be pre-decision context only and separate from lifecycle/no-fill and return labels.",
        "clear_packet_ids": [],
        "next_evidence_needed": "Legal/license allowance, official publication_asof_utc or conservative next-day rule, raw CSV cache path/hash, parser/version, feature_asof_utc, date alignment rule, and no-lookahead fixture.",
    },
}

FORBIDDEN_PRIMARY_KEY_NAMES = {
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "win_loss",
    "outcome_r",
    "trade_result",
    "future_return",
    "post_entry_path",
    "post_signal_path",
    "post_signal_continuation",
    "tp_sl_hit",
    "take_profit_hit",
    "stop_loss_hit",
}

SKIPPED_FOR_POLICY = [
    "data/account_history/**",
    "shadow_logs/*broker*actual*",
    "shadow_logs/*account*truth*",
    "shadow_logs/*pnl*truth*",
    "broker actual-R row/value files",
    "blocked packet outcome/result rows outside the 9 G12-accepted OTB1R lifecycle packets",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(path), "exists": False, "sha256": None}
    stat = path.stat()
    return {
        "path": rel(path),
        "exists": True,
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
    }


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def rows_from_registry(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("rows", "packets", "source_records", "accepted_packets", "packet_results", "lane_decisions"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def run_command(args: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError as exc:
        return {"command": args, "status": "NOT_AVAILABLE", "error": str(exc), "stdout": [], "stderr": []}
    except subprocess.TimeoutExpired as exc:
        return {"command": args, "status": "TIMEOUT", "error": str(exc), "stdout": [], "stderr": []}
    return {
        "command": args,
        "returncode": proc.returncode,
        "status": "OK" if proc.returncode in (0, 1) else "ERROR",
        "stdout": [line for line in proc.stdout.splitlines() if line.strip()],
        "stderr": [line for line in proc.stderr.splitlines() if line.strip()],
    }


def scan_key_hits(value: Any, forbidden: set[str], prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).lower() in forbidden:
                hits.append(child_path)
            hits.extend(scan_key_hits(child, forbidden, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(scan_key_hits(child, forbidden, f"{prefix}[{idx}]"))
    return hits


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def write_json(name: str, obj: Any) -> Path:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    return path


def write_md(name: str, lines: list[str]) -> Path:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    return path


def load_inputs() -> dict[str, Any]:
    paths = {
        "live_state": ROOT / ".context/LIVE_STATE.md",
        "research_current_state": ROOT / ".context/00_core/research_current_state.md",
        "research_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
        "goal_session_discipline": ROOT / ".context/00_core/goal_session_research_discipline.md",
        "otg0_manifest": OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json",
        "preregistry": PREREG / "EXPERIMENT_PREREGISTRY_2026-05-06.json",
        "source_registry": CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
        "otb1r_ledger": OTB1R / f"OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_{DATE_STAMP}.json",
        "otb1r_schema": OTB1R / f"OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_{DATE_STAMP}.json",
        "otb1r_duplicate": OTB1R / f"OTB1R_DUPLICATE_DENOMINATOR_REPORT_{DATE_STAMP}.json",
        "otb1r_projection": OTB1R / f"source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_{DATE_STAMP}.jsonl",
        "oti1_result": OTI1 / f"OTI1_RESULT_LEDGER_{DATE_STAMP}.json",
        "oti1_method": OTI1 / f"OTI1_METHODOLOGY_REPORT_{DATE_STAMP}.json",
        "oti1_duplicate": OTI1 / f"OTI1_DUPLICATE_DENOMINATOR_REPORT_{DATE_STAMP}.json",
        "oti1_label": OTI1 / f"OTI1_LABEL_FAMILY_SEPARATION_REPORT_{DATE_STAMP}.json",
        "oti1_blocker": OTI1 / f"OTI1_BLOCKER_LEDGER_{DATE_STAMP}.json",
        "oti1_completion": OTI1 / f"OTI1_COMPLETION_AUDIT_{DATE_STAMP}.json",
        "g12_otb_shortlist": G12_OTB / f"G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_{DATE_STAMP}.json",
        "g12_otb_decision": G12_OTB / f"G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_{DATE_STAMP}.json",
        "g12_otb_leakage": G12_OTB / f"G12_OTB_REBUILD_LEAKAGE_REVIEW_{DATE_STAMP}.json",
        "g12_otb_duplicate": G12_OTB / f"G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}.json",
        "g12_otb_label": G12_OTB / f"G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_{DATE_STAMP}.json",
        "g12_oti_decision": G12_OTI / f"G12_OTI_POST_TEST_DECISION_LEDGER_{DATE_STAMP}.json",
        "g12_oti_leakage": G12_OTI / f"G12_OTI_POST_TEST_LEAKAGE_NOLEAK_AUDIT_{DATE_STAMP}.json",
        "g12_oti_duplicate": G12_OTI / f"G12_OTI_POST_TEST_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json",
        "g12_oti_label": G12_OTI / f"G12_OTI_POST_TEST_LABEL_FAMILY_AUDIT_{DATE_STAMP}.json",
        "g12_oti_summary": G12_OTI / f"G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_{DATE_STAMP}.json",
        "otl3_evidence": OTL3 / f"OTL3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json",
        "otl3_triage": OTL3 / f"OTL3_SOURCE_ASOF_CLEANUP_TRIAGE_{DATE_STAMP}.json",
        "otb3_cleanup": OTB3 / f"OTB3_SOURCE_NOLEAK_CLEANUP_LEDGER_{DATE_STAMP}.json",
        "otb3_evidence": OTB3 / f"OTB3_SOURCE_EVIDENCE_INDEX_{DATE_STAMP}.json",
        "otb3_g11": OTB3 / f"OTB3_G11_NO_LEAK_REWRITE_LEDGER_{DATE_STAMP}.json",
        "otb3_patchset": OTB3 / f"OTB3_PROPOSED_PATCHSET_{DATE_STAMP}.json",
        "g0_prompt": G0_OTI / f"G0_OTI_NEXT_LANE_PROMPT_PACK_{DATE_STAMP}.md",
        "g0_blocker_map": G0_OTI / f"G0_OTI_BLOCKER_ACTION_MAP_{DATE_STAMP}.md",
        "g0_synthesis": G0_OTI / f"G0_OTI_QUARANTINE_SYNTHESIS_{DATE_STAMP}.md",
        "local_news_calendar": ROOT / "data/news_calendar.json",
        "economic_calendar_csv": ROOT / "data/economic_calendar.csv",
        "dxy_d1": ROOT / "data/DXY_D1.csv",
        "news_calendar_component": ROOT / "src/components/news_calendar.py",
        "external_feeds_component": ROOT / "src/components/external_feeds.py",
        "session_vol_monitor": ROOT / "scripts/session_volatility_monitor.py",
        "orderflow_primitives_test": ROOT / "tests/test_orderflow_primitives.py",
        "news_calendar_test": ROOT / "tests/test_news_calendar.py",
        "external_feeds_test": ROOT / "tests/test_external_feeds.py",
        "session_vol_cache": ROOT / "knowledge_base/ai_tools_cache/session_vol_30d.json",
    }
    data: dict[str, Any] = {"paths": paths, "file_metadata": {key: file_meta(path) for key, path in paths.items()}}
    for key, path in paths.items():
        if path.suffix == ".json" and path.exists():
            data[key] = read_json(path)
        elif path.suffix == ".jsonl" and path.exists():
            data[key] = read_jsonl(path)
        elif path.suffix in {".md", ".py", ".csv"} and path.exists():
            data[key] = {"text_sha256": sha256_file(path), "path": rel(path)}
    return data


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if isinstance(value, str):
            indexed[value] = row
    return indexed


def build_packet_chain(data: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    shortlist = rows_from_registry(data["g12_otb_shortlist"])
    otb1r_packets = rows_from_registry(data["otb1r_ledger"].get("packets", []))
    prereg_rows = rows_from_registry(data["preregistry"])
    manifest_packets = rows_from_registry(data["otg0_manifest"])
    oti1_packets = rows_from_registry(data["oti1_result"])
    g12_decisions = rows_from_registry(data["g12_oti_decision"])
    projections = data.get("otb1r_projection", [])

    shortlist_by_packet = index_by(shortlist, "packet_id")
    otb1r_by_packet = index_by(otb1r_packets, "packet_id")
    prereg_by_experiment = index_by(prereg_rows, "experiment_id")
    manifest_by_packet = index_by(manifest_packets, "packet_id")
    oti1_by_packet = index_by(oti1_packets, "packet_id")
    projection_by_hash = index_by(projections, "source_hash")

    chain: list[dict[str, Any]] = []
    source_hash_issues: list[dict[str, Any]] = []
    forbidden_primary_hits: list[dict[str, Any]] = []

    for packet_id in ACCEPTED_PACKET_IDS:
        short = shortlist_by_packet[packet_id]
        packet_path = ROOT / short["packet_artifact"]
        packet = read_json(packet_path)
        metadata = packet.get("packet_metadata", {})
        rows = packet.get("primary_lifecycle_rows", [])
        experiment_id = short["experiment_id"]
        prereg = prereg_by_experiment.get(experiment_id, {})
        manifest = manifest_by_packet.get(packet_id, {})
        otb1r_row = otb1r_by_packet.get(packet_id, {})
        oti1_row = oti1_by_packet.get(packet_id, {})
        g12_lane = next(
            (
                row
                for row in g12_decisions
                if row.get("lane_id") == "OTI1"
                or row.get("lane") == "OTI1"
                or row.get("result_lane") == "OTI1"
                or row.get("artifact_family") == "oti1_lifecycle_quarantined_results"
            ),
            {},
        )
        row_summaries: list[dict[str, Any]] = []
        for idx, row in enumerate(rows):
            source_hash = row.get("source_hash")
            projection = projection_by_hash.get(source_hash)
            if not projection:
                source_hash_issues.append({"packet_id": packet_id, "row_index": idx, "source_hash": source_hash})
            hits = scan_key_hits(row, FORBIDDEN_PRIMARY_KEY_NAMES)
            for hit in hits:
                forbidden_primary_hits.append({"packet_id": packet_id, "row_index": idx, "key_path": hit})
            row_summaries.append(
                {
                    "row_index": idx,
                    "setup_id_or_candidate_id": row.get("setup_id_or_candidate_id"),
                    "decision_asof_utc": row.get("decision_asof_utc"),
                    "source_capture_utc": row.get("source_capture_utc"),
                    "pending_created_utc_if_applicable": row.get("pending_created_utc_if_applicable"),
                    "source_hash": source_hash,
                    "source_hash_resolves_to_projection": bool(projection),
                    "source_symbol": row.get("source_symbol"),
                    "duplicate_group_id": row.get("duplicate_group_id"),
                    "label_family": row.get("label_family"),
                    "forbidden_primary_fields_absent": row.get("forbidden_primary_fields_absent"),
                    "packet_build_source_paths": row.get("packet_build_source_paths"),
                }
            )
        chain.append(
            {
                "packet_id": packet_id,
                "experiment_id": experiment_id,
                "hypothesis_id": metadata.get("hypothesis_id") or prereg.get("hypothesis_id"),
                "packet_artifact": rel(packet_path),
                "packet_sha256": sha256_file(packet_path),
                "g12_otb_accepted_scope": short.get("accepted_scope"),
                "g12_otb_row_count": short.get("row_count"),
                "g12_otb_unique_duplicate_group_count": short.get("unique_duplicate_group_count"),
                "g12_otb_residual_question": short.get("residual_nonblocking_question"),
                "preregistry": {
                    "metric": prereg.get("metric_preregistered") or prereg.get("metric"),
                    "null": prereg.get("null_definition"),
                    "alternative": prereg.get("alternative_definition"),
                    "sample_floor": prereg.get("sample_floor"),
                    "duplicate_policy": prereg.get("duplicate_policy"),
                    "label_separation_policy": prereg.get("label_separation_policy"),
                    "registered_source_contracts": prereg.get("registered_source_contracts"),
                    "source_gate_status": prereg.get("source_gate_status"),
                    "outcome_review_opened_preregistry": prereg.get("outcome_review_opened_preregistry"),
                    "promotion_verdict": prereg.get("promotion_verdict"),
                },
                "otg0_frozen_packet": {
                    "packet_status": manifest.get("packet_status"),
                    "testing_lane": manifest.get("otg0_testing_lane"),
                    "owner_testing_class": manifest.get("owner_testing_class"),
                    "required_packet_fields": manifest.get("required_packet_fields"),
                    "source_gate_status": manifest.get("source_gate_status"),
                    "blockers": manifest.get("blockers"),
                    "validation_safe": manifest.get("validation_safe"),
                    "outcome_review_opened_owner_review": manifest.get("outcome_review_opened_owner_review"),
                    "promotion_verdict": manifest.get("promotion_verdict"),
                },
                "otb1r_rebuilt_packet": {
                    "decision": otb1r_row.get("packet_decision") or metadata.get("packet_decision"),
                    "primary_raw_row_count": metadata.get("primary_raw_row_count"),
                    "unique_duplicate_group_id_count": metadata.get("unique_duplicate_group_id_count"),
                    "source_projection_file": metadata.get("source_projection_file"),
                    "source_hash_family": metadata.get("source_hash_family"),
                    "source_projection_excludes_before_hashing": metadata.get("source_projection_excludes_before_hashing"),
                    "forbidden_primary_fields_absent": metadata.get("forbidden_primary_fields_absent"),
                    "context_safe_sidecars": metadata.get("context_safe_sidecars"),
                    "residual_blockers_or_owner_questions": metadata.get("residual_blockers_or_owner_questions"),
                    "validation_safe": metadata.get("validation_safe"),
                    "outcome_review_opened": metadata.get("outcome_review_opened"),
                    "promotion_verdict": metadata.get("promotion_verdict"),
                },
                "oti1_quarantined_result": {
                    "result_status": data["oti1_result"].get("result_status"),
                    "packet_status": oti1_row.get("packet_status") or oti1_row.get("status"),
                    "covariate_source_complete_claim_status": oti1_row.get("covariate_source_complete_claim_status"),
                    "covariate_source_complete_claim_reason": oti1_row.get("covariate_source_complete_claim_reason"),
                    "raw_rows": oti1_row.get("raw_rows"),
                    "unique_duplicate_groups": oti1_row.get("unique_duplicate_groups"),
                    "validation_safe": data["oti1_result"].get("validation_safe"),
                    "outcome_review_opened": data["oti1_result"].get("outcome_review_opened"),
                    "promotion_verdict": data["oti1_result"].get("promotion_verdict"),
                },
                "g12_oti_acceptance": {
                    "accepted_as_quarantined_discovery": "ACCEPT" in json.dumps(g12_lane).upper(),
                    "lane_decision_record": g12_lane,
                    "blocked_packet_outcomes_inspected_by_this_audit": data["g12_oti_decision"].get("blocked_packet_outcomes_inspected_by_this_audit"),
                    "broker_actual_r_or_live_trade_results_inspected_by_this_audit": data["g12_oti_decision"].get("broker_actual_r_or_live_trade_results_inspected_by_this_audit"),
                    "validation_safe": data["g12_oti_decision"].get("validation_safe"),
                    "outcome_review_opened": data["g12_oti_decision"].get("outcome_review_opened"),
                    "promotion_verdict": data["g12_oti_decision"].get("promotion_verdict"),
                },
                "primary_lifecycle_row_summaries": row_summaries,
            }
        )

    diagnostics = {
        "accepted_packet_count": len(chain),
        "source_hash_issues": source_hash_issues,
        "forbidden_primary_key_hits": forbidden_primary_hits,
        "projection_hash_count": len(projection_by_hash),
    }
    return chain, diagnostics


def source_record_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for source in rows_from_registry(data["source_registry"]):
        if source.get("source_id"):
            records[source["source_id"]] = {"master_source_registry": source}
    for source in rows_from_registry(data["otl3_evidence"]):
        records.setdefault(source.get("source_id", ""), {})["otl3_evidence"] = source
    cleanup = data.get("otb3_cleanup", {})
    assignments = cleanup.get("source_assignments") or cleanup.get("assignments") or []
    for assignment in assignments if isinstance(assignments, list) else []:
        for source_id in as_list(assignment.get("source_id")) + as_list(assignment.get("source_ids")):
            if source_id:
                records.setdefault(source_id, {})["otb3_cleanup_assignment"] = assignment
    return {key: value for key, value in records.items() if key}


def build_source_asof_ledger(data: dict[str, Any], chain: list[dict[str, Any]]) -> dict[str, Any]:
    records = source_record_index(data)
    otb3_probes = data["otb3_evidence"].get("parser_cache_probes", {})
    projection_path = data["paths"]["otb1r_projection"]
    lifecycle_row_count = sum(len(packet["primary_lifecycle_row_summaries"]) for packet in chain)
    ledger_records = [
        {
            "source_or_context_id": "OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS",
            "classification": "CLEARED_FOR_LIFECYCLE_SOURCE_FRESHNESS_CONTEXT_ONLY",
            "packet_ids": ACCEPTED_PACKET_IDS,
            "file_path": rel(projection_path),
            "raw_cache_hash": sha256_file(projection_path),
            "parser_or_builder": rel(OTB1R / "build_otb1r_input_only_lifecycle_rebuild_2026_05_07.py"),
            "parser_or_builder_sha256": sha256_file(OTB1R / "build_otb1r_input_only_lifecycle_rebuild_2026_05_07.py"),
            "publication_asof_utc_or_decision_rule": "Each primary row carries decision_asof_utc and source_capture_utc; source_hash resolves to sanitized lifecycle projection; source_capture is lifecycle capture/audit time, not a return label.",
            "allowed_feature_role": COVARIATES["source_freshness_context"]["allowed_feature_role"],
            "label_family_boundary": COVARIATES["source_freshness_context"]["label_family_boundary"],
            "no_lookahead_proof": {
                "rows_checked": lifecycle_row_count,
                "projection_forbidden_issues": sum(
                    len(row.get("forbidden_key_paths_after_projection", []))
                    for row in data.get("otb1r_projection", [])
                ),
                "hash_excludes_key_values_all": all(
                    bool(row.get("hash_excludes_key_values")) for row in data.get("otb1r_projection", [])
                ),
                "excluded_key_values_stored_any": any(
                    bool(row.get("excluded_key_values_stored")) for row in data.get("otb1r_projection", [])
                ),
            },
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "SRC-G5-NEWS-CALENDAR-LOCAL-001",
            "classification": "CLEARED_FOR_PACKET_BUILDING_CONTEXT_ONLY",
            "packet_ids": ["OTG0-PKT-055", "OTG0-PKT-059"],
            "file_path": rel(data["paths"]["local_news_calendar"]),
            "raw_cache_hash": sha256_file(data["paths"]["local_news_calendar"]),
            "parser_or_builder": rel(data["paths"]["news_calendar_component"]),
            "parser_or_builder_sha256": sha256_file(data["paths"]["news_calendar_component"]),
            "cache_probe": otb3_probes.get("local_news_calendar"),
            "source_registry_record": records.get("SRC-G5-NEWS-CALENDAR-LOCAL-001"),
            "publication_asof_utc_or_decision_rule": "Use recorded calendar updated_at/source timestamp and candidate decision timestamp; stale calendar state must be excluded or separately labeled.",
            "allowed_feature_role": COVARIATES["local_news_schedule"]["allowed_feature_role"],
            "label_family_boundary": COVARIATES["local_news_schedule"]["label_family_boundary"],
            "no_lookahead_proof": "Context-only calendar schedule proof. Event-window matcher/no-lookahead fixtures are still required before event-conditioned results.",
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "SRC-G7-FED-FOMC-001",
            "classification": "BLOCKED_WITH_NEXT_EXACT_EVIDENCE",
            "packet_ids": ["OTG0-PKT-071"],
            "cache_probe": otb3_probes.get("fed_fomc_calendar"),
            "source_registry_record": records.get("SRC-G7-FED-FOMC-001"),
            "blocker": COVARIATES["fomc_event_windows"]["next_evidence_needed"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "SRC-G8-CBOE-VOL-CSV-001",
            "classification": "BLOCKED_WITH_NEXT_EXACT_EVIDENCE",
            "packet_ids": ["OTG0-PKT-079"],
            "cache_probe": otb3_probes.get("cboe_vol_csv"),
            "source_registry_record": records.get("SRC-G8-CBOE-VOL-CSV-001"),
            "blocker": COVARIATES["cboe_short_vol_context"]["next_evidence_needed"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "SRC-G8-CBOE-METHODOLOGY-002",
            "classification": "CONTEXT_ONLY_NOT_TIME_SERIES_DECISION_ROWS",
            "packet_ids": ["OTG0-PKT-079"],
            "source_registry_record": records.get("SRC-G8-CBOE-METHODOLOGY-002"),
            "blocker": "Methodology/spec references cannot supply per-decision short-vol values; CSV/legal/publication/parser proof is still required.",
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE",
            "classification": "BLOCKED_FOR_DECISION_TIME_FRICTION_COVARIATE",
            "packet_ids": ["OTG0-PKT-016", "OTG0-PKT-079"],
            "source_registry_record": records.get("G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE"),
            "blocker": COVARIATES["friction"]["next_evidence_needed"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "G2-REALIZED-VOL-VOL-OF-VOL-SIDECAR",
            "classification": "SOURCE_NOT_PACKET_BOUND",
            "packet_ids": ["OTG0-PKT-025"],
            "local_probe": file_meta(data["paths"]["session_vol_cache"]),
            "blocker": COVARIATES["realized_volatility"]["next_evidence_needed"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "G4-ORDERFLOW-ABSORPTION-SIDECAR",
            "classification": "SOURCE_NOT_PACKET_BOUND",
            "packet_ids": ["OTG0-PKT-045"],
            "source_registry_records": {
                source_id: records.get(source_id)
                for source_id in COVARIATES["footprint_absorption_orderflow_context"]["source_ids"]
            },
            "blocker": COVARIATES["footprint_absorption_orderflow_context"]["next_evidence_needed"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
        {
            "source_or_context_id": "G7-G5-MACRO-ATTENTION-SIDECAR",
            "classification": "SOURCE_NOT_PACKET_BOUND",
            "packet_ids": ["OTG0-PKT-059"],
            "source_registry_records": {
                source_id: records.get(source_id) for source_id in COVARIATES["macro_attention"]["source_ids"]
            },
            "blocker": COVARIATES["macro_attention"]["next_evidence_needed"],
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        },
    ]
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "source_asof_legality_freshness_ledger",
        "generated_at_utc": now_utc(),
        "scope": "9 G12-accepted OTB1R lifecycle/no-fill packets only",
        "network_or_paid_calls_performed": False,
        "official_fetches_performed": False,
        "official_fetch_note": "No new fetch was needed to reach proof-or-impossibility status because local official/cache probes already identify the current FOMC/Cboe blockers. Missing proof is parser/legal/publication-asof/schema evidence, not mere raw page absence.",
        "records": ledger_records,
    }


def build_covariate_matrix(data: dict[str, Any], chain: list[dict[str, Any]], source_ledger: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    packet_by_id = {packet["packet_id"]: packet for packet in chain}
    source_records = {record["source_or_context_id"]: record for record in source_ledger["records"]}
    matrix_records: list[dict[str, Any]] = []
    by_covariate: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for cov_key, cov in COVARIATES.items():
        for packet_id in ACCEPTED_PACKET_IDS:
            packet = packet_by_id[packet_id]
            clear_packet_ids = set(cov.get("clear_packet_ids", []))
            packet_focus = cov_key in PACKET_TO_COVARIATE_FOCUS.get(packet_id, []) or cov_key == "source_freshness_context"
            if packet_id in clear_packet_ids:
                status = "CLEARED_FOR_PACKET_CONTEXT_ONLY"
                proof_or_blocker = {
                    "proof_status": "context_only_not_validation_safe",
                    "source_ids": cov["source_ids"],
                    "file_path_or_source": [
                        record.get("file_path")
                        for source_id, record in source_records.items()
                        if source_id in cov["source_ids"] or source_id == "OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS"
                    ],
                    "raw_or_cache_hash": [
                        record.get("raw_cache_hash")
                        for source_id, record in source_records.items()
                        if source_id in cov["source_ids"] or source_id == "OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS"
                    ],
                    "parser_or_builder": [
                        record.get("parser_or_builder")
                        for source_id, record in source_records.items()
                        if source_id in cov["source_ids"] or source_id == "OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS"
                    ],
                    "publication_asof_utc_or_decision_rule": "See source/as-of ledger records for this covariate.",
                    "allowed_feature_role": cov["allowed_feature_role"],
                    "label_family_boundary": cov["label_family_boundary"],
                    "no_lookahead_proof": "Context-only proof; no outcomes or R values are used.",
                }
            else:
                status = "BLOCKED_WITH_NEXT_EXACT_EVIDENCE" if packet_focus else "NOT_PACKET_BOUND_BLOCKED_IF_USED"
                proof_or_blocker = {
                    "blocked_status": status,
                    "source_ids": cov["source_ids"],
                    "searched_evidence": [
                        "OTB1R packet metadata/context sidecars",
                        "OTB1R sanitized source projections",
                        "OTI1 blocker/result ledger metadata",
                        "G12 OTB and G12 OTI audits",
                        "OTL3 and OTB3 source/as-of cleanup artifacts",
                        "master source registry and preregistry rows",
                        "local data/scripts/tests/shadow-log path inventory excluding broker actual-R policy paths",
                        "git history for controlling lanes",
                    ],
                    "precise_blocker": cov["next_evidence_needed"]
                    if packet_focus
                    else "This covariate is not registered or packet-bound for this packet. If used later, it needs the same source/as-of, parser, hash, legality, label-boundary, and no-lookahead proof before any result claim.",
                    "allowed_feature_role_if_fixed": cov["allowed_feature_role"],
                    "label_family_boundary": cov["label_family_boundary"],
                }
            record = {
                "packet_id": packet_id,
                "experiment_id": packet["experiment_id"],
                "covariate_key": cov_key,
                "covariate_label": cov["label"],
                "status": status,
                "validation_safe": False,
                "outcome_review_opened": False,
                "promotion_verdict": PROMOTION_VERDICT,
                "proof_or_blocker": proof_or_blocker,
            }
            matrix_records.append(record)
            by_covariate[cov_key].append(record)

    matrix = {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "packet_covariate_coverage_matrix",
        "generated_at_utc": now_utc(),
        "packet_count": len(ACCEPTED_PACKET_IDS),
        "covariate_count": len(COVARIATES),
        "matrix_record_count": len(matrix_records),
        "status_counts": dict(Counter(record["status"] for record in matrix_records)),
        "records": matrix_records,
    }
    proof_ledger = {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "per_covariate_proof_ledger",
        "generated_at_utc": now_utc(),
        "covariates": [
            {
                "covariate_key": cov_key,
                "covariate_label": COVARIATES[cov_key]["label"],
                "source_ids": COVARIATES[cov_key]["source_ids"],
                "allowed_feature_role": COVARIATES[cov_key]["allowed_feature_role"],
                "label_family_boundary": COVARIATES[cov_key]["label_family_boundary"],
                "packet_status_counts": dict(Counter(record["status"] for record in records)),
                "packet_records": records,
            }
            for cov_key, records in by_covariate.items()
        ],
    }
    return matrix, proof_ledger


def build_no_leak_audit(data: dict[str, Any], chain: list[dict[str, Any]], diagnostics: dict[str, Any]) -> dict[str, Any]:
    flag_issues: list[dict[str, Any]] = []
    for artifact_name in ("oti1_result", "g12_oti_decision", "g12_otb_shortlist", "otb1r_ledger"):
        artifact = data.get(artifact_name, {})
        if isinstance(artifact, dict):
            if artifact.get("validation_safe") not in (False, None):
                flag_issues.append({"artifact": artifact_name, "field": "validation_safe", "value": artifact.get("validation_safe")})
            if artifact.get("outcome_review_opened") not in (False, None):
                flag_issues.append({"artifact": artifact_name, "field": "outcome_review_opened", "value": artifact.get("outcome_review_opened")})
            if artifact.get("promotion_verdict") not in (PROMOTION_VERDICT, None):
                flag_issues.append({"artifact": artifact_name, "field": "promotion_verdict", "value": artifact.get("promotion_verdict")})
    packet_flag_issues: list[dict[str, Any]] = []
    for packet in chain:
        meta = packet["otb1r_rebuilt_packet"]
        for field in ("validation_safe", "outcome_review_opened"):
            if meta.get(field) is not False:
                packet_flag_issues.append({"packet_id": packet["packet_id"], "field": field, "value": meta.get(field)})
        if meta.get("promotion_verdict") != PROMOTION_VERDICT:
            packet_flag_issues.append({"packet_id": packet["packet_id"], "field": "promotion_verdict", "value": meta.get("promotion_verdict")})

    projection_forbidden_issues = [
        {
            "source_hash": row.get("source_hash"),
            "forbidden_key_paths_after_projection": row.get("forbidden_key_paths_after_projection"),
        }
        for row in data.get("otb1r_projection", [])
        if row.get("forbidden_key_paths_after_projection")
    ]
    projection_excluded_values_stored = [
        row.get("source_hash") for row in data.get("otb1r_projection", []) if row.get("excluded_key_values_stored")
    ]
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "no_leak_audit",
        "generated_at_utc": now_utc(),
        "scope": "Accepted OTI1 OTB1R lifecycle packets, packet rows, and sanitized source projections only.",
        "policy_exclusions": SKIPPED_FOR_POLICY,
        "blocked_packet_outcomes_inspected": False,
        "broker_actual_r_values_inspected": False,
        "synthetic_path_r_values_inspected": False,
        "covariate_conditioned_performance_computed": False,
        "flag_issues": flag_issues,
        "packet_flag_issues": packet_flag_issues,
        "primary_row_forbidden_key_hits": diagnostics["forbidden_primary_key_hits"],
        "projection_forbidden_issues": projection_forbidden_issues,
        "projection_excluded_key_values_stored": projection_excluded_values_stored,
        "accidental_prior_account_history_grep_note": "A broad exploratory rg earlier matched account_history path text. No broker actual-R/account values were consumed, joined, summarized, persisted, or used in this proof pack.",
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "pass": not flag_issues
        and not packet_flag_issues
        and not diagnostics["forbidden_primary_key_hits"]
        and not projection_forbidden_issues
        and not projection_excluded_values_stored,
    }


def build_duplicate_audit(data: dict[str, Any], chain: list[dict[str, Any]]) -> dict[str, Any]:
    packet_rows: list[dict[str, Any]] = []
    for packet in chain:
        for row in packet["primary_lifecycle_row_summaries"]:
            packet_rows.append({"packet_id": packet["packet_id"], **row})
    raw_rows = len(packet_rows)
    packet_units = {(row["packet_id"], row.get("duplicate_group_id")) for row in packet_rows}
    duplicate_ids = [row.get("duplicate_group_id") for row in packet_rows]
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "duplicate_denominator_audit",
        "generated_at_utc": now_utc(),
        "raw_rows_recount": raw_rows,
        "packet_level_unique_duplicate_group_units_recount": len(packet_units),
        "duplicate_group_id_counts": dict(Counter(duplicate_ids)),
        "oti1_reported_raw_rows": data["oti1_result"].get("raw_rows_audit_only"),
        "oti1_reported_unique_packet_units": data["oti1_result"].get("unique_duplicate_group_packet_units"),
        "oti1_reported_cross_packet_units": data["oti1_result"].get("unique_duplicate_group_cross_packet_units"),
        "source_duplicate_group_id_units_unpooled": data["oti1_result"].get("source_duplicate_group_id_units_unpooled"),
        "source_opportunity_id_units_after_unwrapping_shared_family_prefixes": data["oti1_result"].get("source_opportunity_id_units_after_unwrapping_shared_family_prefixes"),
        "denominator_policy": "Counts are duplicate/denominator audit only. They are not validation effective-N and are not a covariate-conditioned performance result.",
        "mismatches": [
            item
            for item in [
                {
                    "field": "raw_rows_audit_only",
                    "expected": raw_rows,
                    "observed": data["oti1_result"].get("raw_rows_audit_only"),
                }
                if data["oti1_result"].get("raw_rows_audit_only") != raw_rows
                else None,
                {
                    "field": "unique_duplicate_group_packet_units",
                    "expected": len(packet_units),
                    "observed": data["oti1_result"].get("unique_duplicate_group_packet_units"),
                }
                if data["oti1_result"].get("unique_duplicate_group_packet_units") != len(packet_units)
                else None,
            ]
            if item
        ],
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
    }


def build_label_family_audit(data: dict[str, Any], chain: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    non_lifecycle_rows: list[dict[str, Any]] = []
    for packet in chain:
        for row in packet["primary_lifecycle_row_summaries"]:
            label = row.get("label_family")
            label_counts[str(label)] += 1
            if label != "lifecycle_no_fill":
                non_lifecycle_rows.append({"packet_id": packet["packet_id"], "row": row})
            rows.append(row)
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "label_family_separation_audit",
        "generated_at_utc": now_utc(),
        "primary_label_family_counts": dict(label_counts),
        "non_lifecycle_primary_rows": non_lifecycle_rows,
        "boundary_statement": "The proof pack audits lifecycle_no_fill source/as-of context only. It does not merge broker actual-R, synthetic path-R, win/loss, or return labels.",
        "source_projection_forbidden_issues": [
            row.get("forbidden_key_paths_after_projection") for row in data.get("otb1r_projection", []) if row.get("forbidden_key_paths_after_projection")
        ],
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "pass": not non_lifecycle_rows,
    }


def build_contradiction_ledger(data: dict[str, Any]) -> dict[str, Any]:
    records = [
        {
            "issue": "OTL1 all-blocked historical state versus OTB1R/G12 accepted OTI1 packet state",
            "resolution": "Treat later OTB1R rebuild plus G12 OTB rebuild reaudit plus G12 OTI acceptance as controlling only for the 9 accepted OTB1R lifecycle packets. OTL1 remains historical for the blocked pre-rebuild packet state.",
            "evidence": [
                rel(data["paths"]["g12_otb_shortlist"]),
                rel(data["paths"]["g12_oti_decision"]),
                rel(data["paths"]["g0_synthesis"]),
            ],
        },
        {
            "issue": "OTI1 lifecycle descriptive result accepted while covariate source-complete claims are blocked",
            "resolution": "No contradiction. Lifecycle/no-fill source truth and covariate-conditioned/source-complete claims are separate. This proof pack keeps covariates context-only or blocked.",
            "evidence": [rel(data["paths"]["oti1_result"]), rel(data["paths"]["g0_blocker_map"])],
        },
        {
            "issue": "Local news calendar path mismatch in older source registry text",
            "resolution": "Use OTB3/OTL3 resolved local evidence path data/news_calendar.json for schedule/stale context only. The older data/news/forexfactory_calendar.json path remains non-existent historical context.",
            "evidence": [rel(data["paths"]["local_news_calendar"]), rel(data["paths"]["otb3_evidence"])],
        },
        {
            "issue": "FOMC official page cache exists but FOMC event-window packet proof remains blocked",
            "resolution": "Cached official page evidence is date-only/context evidence in current probes; packet-bound event_time_utc parser output and no-lookahead fixtures are missing.",
            "evidence": [rel(data["paths"]["otb3_evidence"]), rel(data["paths"]["otl3_evidence"])],
        },
        {
            "issue": "Cboe CSV caches exist but short-vol context remains blocked",
            "resolution": "Cboe cache existence does not prove legal use, publication_asof timing, parser/date alignment, or no-lookahead safety. Keep OTG0-PKT-079 blocked.",
            "evidence": [rel(data["paths"]["otb3_evidence"]), rel(data["paths"]["otl3_evidence"])],
        },
        {
            "issue": "G11 friction no-leak rewrite clears context-only sidecar but not packet-bound friction features",
            "resolution": "OTB3 proposed decision-time friction field names are context-only proposed fields. OTI1 packet rows do not carry those fields with source hashes/as-of proof.",
            "evidence": [rel(data["paths"]["otb3_g11"])],
        },
        {
            "issue": "Earlier exploratory rg matched account_history paths",
            "resolution": "Forbidden account/broker actual-R paths are excluded from this builder's searches and ledgers. No broker actual-R values were consumed.",
            "evidence": ["This proof pack no-leak audit policy exclusions"],
        },
    ]
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "contradiction_stale_context_ledger",
        "generated_at_utc": now_utc(),
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "records": records,
    }


def build_negative_evidence_ledger(data: dict[str, Any]) -> dict[str, Any]:
    rg_globs = [
        "-g",
        "!data/account_history/**",
        "-g",
        "!shadow_logs/*broker*actual*",
        "-g",
        "!shadow_logs/*account*truth*",
        "-g",
        "!shadow_logs/*pnl*truth*",
    ]
    search_specs = {
        "friction_spread_contract": r"friction|spread_at_decision|spread_atr|contract_spec|commission_schedule|min_stop_distance|tick_value_asof",
        "realized_vol_vol_of_vol": r"realized.?vol|vol.?of.?vol|session_vol|volatility",
        "footprint_absorption_orderflow": r"footprint|absorb|absorption|orderflow|ofi|sierra|databento|depth",
        "news_macro_fomc": r"news_calendar|calendar_updated|event_time_utc|macro_attention|FOMC|Federal Reserve|fed_fomc",
        "cboe_short_vol": r"Cboe|VIX1D|VIX9D|VVIX|GVZ|short.?vol|publication_asof",
        "source_freshness": r"source_capture_utc|decision_asof_utc|source_hash|source_projection",
    }
    scopes = [
        "research/science_program_2026_05",
        "src",
        "scripts",
        "tests",
        "data",
        "shadow_logs",
        "knowledge_base/ai_tools_cache",
    ]
    searches: list[dict[str, Any]] = []
    for name, pattern in search_specs.items():
        result = run_command(["rg", "-l", "--ignore-case", pattern, *scopes, *rg_globs])
        hits = [line for line in result.get("stdout", []) if line]
        searches.append(
            {
                "search_name": name,
                "pattern": pattern,
                "scopes": scopes,
                "exclusions": SKIPPED_FOR_POLICY,
                "path_hit_count": len(hits),
                "path_hits": hits[:250],
                "truncated": len(hits) > 250,
                "status": result.get("status"),
                "returncode": result.get("returncode"),
            }
        )
    file_inventory = run_command(
        [
            "rg",
            "--files",
            "research/science_program_2026_05",
            "src",
            "scripts",
            "tests",
            "data",
            "shadow_logs",
            "knowledge_base/ai_tools_cache",
        ]
    )
    inventory_pattern = re.compile(
        r"(news|calendar|vol|vix|cboe|fomc|fred|bis|dxy|sierra|depth|tick|ohlc|orderflow|session_vol)",
        re.IGNORECASE,
    )
    inventory_hits = [
        line
        for line in file_inventory.get("stdout", [])
        if inventory_pattern.search(line)
        and "data/account_history" not in line.replace("\\", "/")
        and "broker_actual" not in line.lower()
        and "account_truth" not in line.lower()
    ]
    git_history = run_command(
        [
            "git",
            "log",
            "--oneline",
            "--",
            rel(OTI1),
            rel(OTB1R),
            rel(G12_OTI),
            rel(G12_OTB),
            rel(OTL3),
            rel(OTB3),
            rel(G0_OTI),
            rel(OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json"),
            rel(PREREG / "EXPERIMENT_PREREGISTRY_2026-05-06.json"),
            rel(CONTROL / "SOURCE_CONTRACT_REGISTRY_2026-05-06.json"),
        ]
    )
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "negative_evidence_saturation_ledger",
        "generated_at_utc": now_utc(),
        "searches": searches,
        "file_inventory_relevant_hits": inventory_hits[:500],
        "file_inventory_hit_count": len(inventory_hits),
        "git_history_relevant_commits": git_history.get("stdout", []),
        "local_file_metadata_probes": data["file_metadata"],
        "policy_exclusions": SKIPPED_FOR_POLICY,
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "saturation_conclusion": "Local pursuit is saturated for the 9 accepted OTI1 packets: lifecycle source freshness and local news schedule context are provable; decision-time friction, realized-vol/vol-of-vol, orderflow/absorption, macro-attention, FOMC event-window, and Cboe short-vol covariates are not packet-bound with required source/as-of/legal/parser/no-lookahead proof.",
    }


def build_blocker_owner_ledger(matrix: dict[str, Any]) -> dict[str, Any]:
    blockers: dict[str, dict[str, Any]] = {}
    for record in matrix["records"]:
        if record["status"] == "CLEARED_FOR_PACKET_CONTEXT_ONLY":
            continue
        cov_key = record["covariate_key"]
        cov = COVARIATES[cov_key]
        blocker = blockers.setdefault(
            cov_key,
            {
                "covariate_key": cov_key,
                "covariate_label": cov["label"],
                "affected_packet_ids": [],
                "source_ids": cov["source_ids"],
                "exact_next_evidence_needed": cov["next_evidence_needed"]
                or "No further evidence needed for context-only lifecycle source freshness.",
                "owner_or_approval_needed": [],
                "status": "BLOCKED_WITH_NEXT_EXACT_EVIDENCE",
                "validation_safe": False,
                "outcome_review_opened": False,
                "promotion_verdict": PROMOTION_VERDICT,
            },
        )
        blocker["affected_packet_ids"].append(record["packet_id"])
    owner_map = {
        "friction": [
            "Owner/G12 approval for which friction source is authoritative: pending lifecycle spread, contract-spec snapshots, or a separate source-contract sidecar.",
            "Source owner for commission/min-stop/contract-spec snapshot cache and parser.",
        ],
        "realized_volatility": ["Owner/G12 approval of realized-vol formula/window and source input family."],
        "volatility_of_volatility": ["Owner/G12 approval of vol-of-vol formula/window and source input family."],
        "footprint_absorption_orderflow_context": [
            "Owner approval for Sierra/GTOS local orderflow source use or separate official source-contract dossier.",
            "No Databento paid/API call may be made by this proof pack.",
        ],
        "macro_attention": [
            "Owner/G12 approval of official macro source stack, series/table ids, vintage rules, and parser fixtures.",
        ],
        "fomc_event_windows": [
            "Owner/G12 approval of FOMC event-window parser, source freshness fixtures, and date/time resolution policy.",
        ],
        "cboe_short_vol_context": [
            "Owner/G12 approval of Cboe legal/license state, publication timing rule, and parser/no-lookahead fixtures.",
        ],
        "local_news_schedule": [
            "No owner approval needed for schedule/stale context already cleared; owner/G12 approval needed before event-window result claims.",
        ],
    }
    for key, value in blockers.items():
        value["affected_packet_ids"] = sorted(set(value["affected_packet_ids"]))
        value["owner_or_approval_needed"] = owner_map.get(key, ["Owner/G12 approval of packet-bound source/as-of contract."])
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "blocker_owner_approval_ledger",
        "generated_at_utc": now_utc(),
        "records": list(blockers.values()),
    }


def build_future_schema_fixes() -> dict[str, Any]:
    common_fields = [
        "packet_id",
        "experiment_id",
        "covariate_key",
        "source_contract_id",
        "source_contract_version",
        "raw_cache_path",
        "raw_cache_sha256",
        "parser_path",
        "parser_sha256",
        "parser_version",
        "decision_asof_utc",
        "publication_asof_utc",
        "source_capture_utc",
        "feature_asof_utc",
        "feature_window_start_utc",
        "feature_window_end_utc",
        "feature_window_end_lte_decision_asof",
        "allowed_feature_role",
        "label_family_boundary",
        "duplicate_group_id",
        "no_lookahead_fixture_id",
        "license_or_owner_approval_id",
        "validation_safe=false",
        "outcome_review_opened=false",
        "promotion_verdict=NO_PROMOTION_VERDICT",
    ]
    covariate_specific = {
        "friction": ["spread_at_decision", "spread_atr_ratio_at_decision", "tick_value_asof", "contract_spec_version_asof", "commission_schedule_asof", "min_stop_distance_asof"],
        "realized_volatility": ["realized_vol_window", "realized_vol_value", "ohlc_input_hash", "timezone_policy"],
        "volatility_of_volatility": ["vol_of_vol_window", "vol_of_vol_value", "realized_vol_source_hashes"],
        "footprint_absorption_orderflow_context": ["orderflow_source_symbol", "proxy_map_version", "ofi_value", "absorption_class", "absorption_classifier_version", "depth_schema_version"],
        "local_news_schedule": ["event_id", "event_time_utc", "calendar_updated_at_utc", "event_importance_asof", "stale_calendar_state"],
        "macro_attention": ["macro_source_id", "series_or_table_id", "release_or_vintage_timestamp_utc", "attention_class", "freshness_bucket"],
        "fomc_event_windows": ["fomc_meeting_id", "event_time_utc", "window_class", "official_page_hash", "stale_source_state"],
        "cboe_short_vol_context": ["index_symbol", "csv_trade_date", "cboe_publication_asof_utc", "value_asof", "next_day_conservative_rule_applied", "legal_use_state"],
    }
    records = []
    for cov_key, fields in covariate_specific.items():
        records.append(
            {
                "covariate_key": cov_key,
                "recommended_packet_schema_fields": common_fields + fields,
                "apply_to_packet_ids": sorted(
                    packet_id
                    for packet_id, covariates in PACKET_TO_COVARIATE_FOCUS.items()
                    if cov_key in covariates
                ),
                "registry_patch_policy": "Proposed schema only; do not edit master registries in this proof pack.",
            }
        )
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "proposed_future_packet_schema_fixes",
        "generated_at_utc": now_utc(),
        "common_source_asof_contract_fields": common_fields,
        "records": records,
    }


def build_completion_audit(
    chain: list[dict[str, Any]],
    diagnostics: dict[str, Any],
    matrix: dict[str, Any],
    no_leak: dict[str, Any],
    duplicate: dict[str, Any],
    label: dict[str, Any],
    source_ledger: dict[str, Any],
    blocker_owner: dict[str, Any],
) -> dict[str, Any]:
    completion_checks = {
        "accepted_packet_count_is_9": len(chain) == 9,
        "accepted_packet_ids_match_g12_oti1_scope": [packet["packet_id"] for packet in chain] == ACCEPTED_PACKET_IDS,
        "covariate_count_is_9": len(COVARIATES) == 9,
        "packet_covariate_matrix_complete": matrix["matrix_record_count"] == len(ACCEPTED_PACKET_IDS) * len(COVARIATES),
        "each_matrix_record_has_status": all(record.get("status") for record in matrix["records"]),
        "each_covariate_packet_cleared_or_blocked": all(
            record["status"] in {"CLEARED_FOR_PACKET_CONTEXT_ONLY", "BLOCKED_WITH_NEXT_EXACT_EVIDENCE", "NOT_PACKET_BOUND_BLOCKED_IF_USED"}
            for record in matrix["records"]
        ),
        "source_hash_resolution_issues_zero": not diagnostics["source_hash_issues"],
        "forbidden_primary_key_hits_zero": not diagnostics["forbidden_primary_key_hits"],
        "no_leak_audit_pass": no_leak["pass"],
        "duplicate_mismatches_zero": not duplicate["mismatches"],
        "label_family_audit_pass": label["pass"],
        "validation_safe_false": True,
        "outcome_review_opened_false": True,
        "promotion_verdict_no_promotion": True,
        "no_new_official_fetches_or_paid_calls": not source_ledger["network_or_paid_calls_performed"],
        "blocker_owner_ledger_has_exact_next_evidence": all(
            record.get("exact_next_evidence_needed") for record in blocker_owner["records"]
        ),
    }
    cleared_context_records = [
        record for record in matrix["records"] if record["status"] == "CLEARED_FOR_PACKET_CONTEXT_ONLY"
    ]
    blocked_records = [record for record in matrix["records"] if record["status"] != "CLEARED_FOR_PACKET_CONTEXT_ONLY"]
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "completion_audit",
        "generated_at_utc": now_utc(),
        "completion_checks": completion_checks,
        "can_mark_goal_complete": all(completion_checks.values()),
        "cleared_context_record_count": len(cleared_context_records),
        "blocked_or_not_bound_record_count": len(blocked_records),
        "cleared_context_summary": dict(Counter(record["covariate_key"] for record in cleared_context_records)),
        "blocked_summary": dict(Counter(record["covariate_key"] for record in blocked_records)),
        "preserved_flags": {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "NO_PROMOTION_VERDICT": True,
        },
        "forbidden_actions_not_performed": {
            "covariate_conditioned_performance_computed": False,
            "outcome_scoring_run": False,
            "broker_actual_r_inspected": False,
            "blocked_packet_outcomes_inspected": False,
            "paid_api_databento_calls": False,
            "master_registries_edited": False,
            "live_trading_surfaces_touched": False,
            "remote_push": False,
        },
        "residual_truth": "OTI1 remains quarantined discovery-only lifecycle/no-fill evidence. This proof pack clears lifecycle source freshness for all 9 packets and local news schedule context for OTG0-PKT-055/059 only; all source-complete covariate result claims remain blocked until the exact recorded evidence is supplied and audited.",
    }


def build_artifact_manifest(paths: list[Path]) -> dict[str, Any]:
    return {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "artifact_manifest",
        "generated_at_utc": now_utc(),
        "artifact_count": len(paths),
        "artifacts": [
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in sorted(paths)
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
    }


def md_packet_chain(chain: list[dict[str, Any]]) -> list[str]:
    lines = [
        "# OTI1 Packet Chain Reconstruction",
        "",
        "Scope: 9 G12-accepted OTB1R lifecycle/no-fill packets only. No outcomes, broker actual-R, blocked-packet outcomes, or covariate-conditioned performance are opened here.",
        "",
        "| Packet | Experiment | Rows | Unique duplicate units | Lifecycle source proof | Covariate source status |",
        "|---|---|---:|---:|---|---|",
    ]
    for packet in chain:
        rows = packet["otb1r_rebuilt_packet"]["primary_raw_row_count"]
        uniq = packet["otb1r_rebuilt_packet"]["unique_duplicate_group_id_count"]
        proof = "source_hash rows resolve to sanitized OTB1R projections"
        cov_status = packet["oti1_quarantined_result"].get("covariate_source_complete_claim_status") or "see matrix"
        lines.append(f"| {packet['packet_id']} | {packet['experiment_id']} | {rows} | {uniq} | {proof} | {cov_status} |")
    return lines


def md_matrix(matrix: dict[str, Any]) -> list[str]:
    lines = [
        "# OTI1 Packet-Covariate Coverage Matrix",
        "",
        "Status values are context-only or blocked. None are validation-safe.",
        "",
        "| Packet | Covariate | Status |",
        "|---|---|---|",
    ]
    for record in matrix["records"]:
        lines.append(f"| {record['packet_id']} | {record['covariate_key']} | {record['status']} |")
    return lines


def md_covariate_ledger(proof_ledger: dict[str, Any]) -> list[str]:
    lines = ["# OTI1 Per-Covariate Proof Ledger", ""]
    for cov in proof_ledger["covariates"]:
        lines.extend(
            [
                f"## {cov['covariate_key']}",
                "",
                f"- Source IDs: {', '.join(cov['source_ids'])}",
                f"- Allowed role: {cov['allowed_feature_role']}",
                f"- Label boundary: {cov['label_family_boundary']}",
                f"- Packet status counts: {cov['packet_status_counts']}",
                "",
            ]
        )
    return lines


def md_source_ledger(ledger: dict[str, Any]) -> list[str]:
    lines = [
        "# OTI1 Source/As-Of Legality And Freshness Ledger",
        "",
        "| Source/context | Classification | Packets | Blocker or role |",
        "|---|---|---|---|",
    ]
    for record in ledger["records"]:
        role = record.get("allowed_feature_role") or record.get("blocker") or ""
        packets = ", ".join(record.get("packet_ids", []))
        lines.append(f"| {record['source_or_context_id']} | {record['classification']} | {packets} | {role} |")
    return lines


def md_simple(title: str, obj: dict[str, Any]) -> list[str]:
    lines = [f"# {title}", ""]
    for key, value in obj.items():
        if key in {"records", "searches", "artifacts", "covariates"}:
            continue
        lines.append(f"- {key}: {value}")
    if "records" in obj:
        lines.extend(["", "## Records", ""])
        for record in obj["records"]:
            name = record.get("covariate_key") or record.get("source_or_context_id") or record.get("issue") or record.get("search_name") or "record"
            lines.append(f"- {name}: {record.get('status') or record.get('classification') or record.get('resolution') or record.get('exact_next_evidence_needed')}")
    if "searches" in obj:
        lines.extend(["", "## Searches", ""])
        for search in obj["searches"]:
            lines.append(f"- {search['search_name']}: {search['path_hit_count']} path hits in {search['scopes']}")
    return lines


def write_per_covariate_ledgers(proof_ledger: dict[str, Any], written: list[Path]) -> None:
    for cov in proof_ledger["covariates"]:
        slug = cov["covariate_key"].upper()
        obj = {
            "artifact_family": proof_ledger["artifact_family"],
            "artifact_type": "single_covariate_proof_ledger",
            "generated_at_utc": proof_ledger["generated_at_utc"],
            **cov,
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": PROMOTION_VERDICT,
        }
        written.append(write_json(f"covariates/OTI1_COVARIATE_{slug}_PROOF_LEDGER_{DATE_STAMP}.json", obj))
        lines = [
            f"# OTI1 Covariate Proof Ledger: {cov['covariate_key']}",
            "",
            f"- Source IDs: {', '.join(cov['source_ids'])}",
            f"- Allowed role: {cov['allowed_feature_role']}",
            f"- Label boundary: {cov['label_family_boundary']}",
            f"- Packet status counts: {cov['packet_status_counts']}",
            "",
            "| Packet | Status |",
            "|---|---|",
        ]
        for record in cov["packet_records"]:
            lines.append(f"| {record['packet_id']} | {record['status']} |")
        written.append(write_md(f"covariates/OTI1_COVARIATE_{slug}_PROOF_LEDGER_{DATE_STAMP}.md", lines))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data = load_inputs()
    chain, diagnostics = build_packet_chain(data)
    source_ledger = build_source_asof_ledger(data, chain)
    matrix, proof_ledger = build_covariate_matrix(data, chain, source_ledger)
    no_leak = build_no_leak_audit(data, chain, diagnostics)
    duplicate = build_duplicate_audit(data, chain)
    label = build_label_family_audit(data, chain)
    contradiction = build_contradiction_ledger(data)
    negative = build_negative_evidence_ledger(data)
    blocker_owner = build_blocker_owner_ledger(matrix)
    schema_fixes = build_future_schema_fixes()
    completion = build_completion_audit(
        chain,
        diagnostics,
        matrix,
        no_leak,
        duplicate,
        label,
        source_ledger,
        blocker_owner,
    )

    if not completion["can_mark_goal_complete"]:
        raise SystemExit(f"completion audit failed: {completion['completion_checks']}")

    written: list[Path] = []
    written.append(write_json(f"OTI1_PACKET_CHAIN_RECONSTRUCTION_{DATE_STAMP}.json", {
        "artifact_family": "OTI1_COVARIATE_SOURCE_ASOF_PROOF_PACK",
        "artifact_type": "packet_chain_reconstruction",
        "generated_at_utc": now_utc(),
        "accepted_packet_count": len(chain),
        "diagnostics": diagnostics,
        "packets": chain,
        "validation_safe": False,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
    }))
    written.append(write_md(f"OTI1_PACKET_CHAIN_RECONSTRUCTION_{DATE_STAMP}.md", md_packet_chain(chain)))
    written.append(write_json(f"OTI1_COVARIATE_PROOF_LEDGER_{DATE_STAMP}.json", proof_ledger))
    written.append(write_md(f"OTI1_COVARIATE_PROOF_LEDGER_{DATE_STAMP}.md", md_covariate_ledger(proof_ledger)))
    write_per_covariate_ledgers(proof_ledger, written)
    written.append(write_json(f"OTI1_PACKET_COVARIATE_COVERAGE_MATRIX_{DATE_STAMP}.json", matrix))
    written.append(write_md(f"OTI1_PACKET_COVARIATE_COVERAGE_MATRIX_{DATE_STAMP}.md", md_matrix(matrix)))
    written.append(write_json(f"OTI1_SOURCE_ASOF_LEGALITY_FRESHNESS_LEDGER_{DATE_STAMP}.json", source_ledger))
    written.append(write_md(f"OTI1_SOURCE_ASOF_LEGALITY_FRESHNESS_LEDGER_{DATE_STAMP}.md", md_source_ledger(source_ledger)))
    written.append(write_json(f"OTI1_NO_LEAK_AUDIT_{DATE_STAMP}.json", no_leak))
    written.append(write_md(f"OTI1_NO_LEAK_AUDIT_{DATE_STAMP}.md", md_simple("OTI1 No-Leak Audit", no_leak)))
    written.append(write_json(f"OTI1_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json", duplicate))
    written.append(write_md(f"OTI1_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.md", md_simple("OTI1 Duplicate Denominator Audit", duplicate)))
    written.append(write_json(f"OTI1_LABEL_FAMILY_SEPARATION_AUDIT_{DATE_STAMP}.json", label))
    written.append(write_md(f"OTI1_LABEL_FAMILY_SEPARATION_AUDIT_{DATE_STAMP}.md", md_simple("OTI1 Label-Family Separation Audit", label)))
    written.append(write_json(f"OTI1_CONTRADICTION_STALE_CONTEXT_LEDGER_{DATE_STAMP}.json", contradiction))
    written.append(write_md(f"OTI1_CONTRADICTION_STALE_CONTEXT_LEDGER_{DATE_STAMP}.md", md_simple("OTI1 Contradiction/Stale-Context Ledger", contradiction)))
    written.append(write_json(f"OTI1_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.json", negative))
    written.append(write_md(f"OTI1_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.md", md_simple("OTI1 Negative-Evidence Saturation Ledger", negative)))
    written.append(write_json(f"OTI1_BLOCKER_OWNER_APPROVAL_LEDGER_{DATE_STAMP}.json", blocker_owner))
    written.append(write_md(f"OTI1_BLOCKER_OWNER_APPROVAL_LEDGER_{DATE_STAMP}.md", md_simple("OTI1 Blocker/Owner-Approval Ledger", blocker_owner)))
    written.append(write_json(f"OTI1_PROPOSED_FUTURE_PACKET_SCHEMA_FIXES_{DATE_STAMP}.json", schema_fixes))
    written.append(write_md(f"OTI1_PROPOSED_FUTURE_PACKET_SCHEMA_FIXES_{DATE_STAMP}.md", md_simple("OTI1 Proposed Future Packet Schema Fixes", schema_fixes)))
    written.append(write_json(f"OTI1_COVARIATE_SOURCE_ASOF_COMPLETION_AUDIT_{DATE_STAMP}.json", completion))
    written.append(write_md(f"OTI1_COVARIATE_SOURCE_ASOF_COMPLETION_AUDIT_{DATE_STAMP}.md", md_simple("OTI1 Covariate Source/As-Of Completion Audit", completion)))

    manifest_path = write_json(f"OTI1_COVARIATE_SOURCE_ASOF_ARTIFACT_MANIFEST_{DATE_STAMP}.json", build_artifact_manifest(written))
    written.append(manifest_path)

    print(json.dumps({
        "output_dir": rel(OUT),
        "artifacts_written": len(written),
        "packet_count": len(chain),
        "matrix_records": matrix["matrix_record_count"],
        "completion": completion["can_mark_goal_complete"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
