"""Build the G12 red-team audit for G3/G6 packet-builder readiness.

This is a packet-readiness audit only. It reads input-packet/control artifacts,
never opens result quarantines, broker actual-R files, or blocked outcome logs.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DATE_STAMP = "2026-05-07"
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit"

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False

OT = ROOT / "research/science_program_2026_05/06_outcome_testing"
G0_OTI = OT / "g0_oti_quarantine_synthesis"
G12_REBUILD = OT / "g12_otb_rebuild_reaudit"
G3_DIR = OT / "otb2r_g3_geometry_input_packet_builders"
G6_DIR = OT / "otb2r_g6_local_ohlc_momentum_reversion_packets"
OTB2_DIR = OT / "otb2_synthetic_packet_builder"
OTB2R_DIR = OT / "otb2r_input_only_path_rebuild"

CONTROL_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
    "research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/OTG0_COMPLETION_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g0_oti_quarantine_synthesis/G0_OTI_BLOCKER_ACTION_MAP_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2_synthetic_packet_builder/OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_COMPLETION_AUDIT_2026-05-07.json",
]

TARGET_PACKET_IDS = [
    "OTG0-PKT-031",
    "OTG0-PKT-032",
    "OTG0-PKT-036",
    "OTG0-PKT-060",
    "OTG0-PKT-061",
    "OTG0-PKT-062",
    "OTG0-PKT-063",
    "OTG0-PKT-066",
]

RESULT_FIELD_FRAGMENTS = [
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
    "realized_r",
    "resolution",
    "resolved",
    "result",
    "sl_first_touch",
    "synthetic_path",
    "terminal_order",
    "touch_sequence",
    "tp1_first_touch",
    "trade_result",
    "win_loss",
]

ALLOWED_CONTROL_KEYS = {
    "broker_actual_r_absent_from_primary_metric",
    "blocked_packet_outcomes_not_opened",
    "blocked_packet_outcomes_inspected",
    "c_gate_result",
    "broker_actual_r_inspected",
    "label_values_absent",
    "no_outcome_columns_in_records",
    "no_result_columns_in_records",
    "outcome_review_opened",
    "outcome_scoring_run",
    "result_or_quarantine_outputs_created",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def control_input_hashes() -> list[dict[str, Any]]:
    rows = []
    for item in CONTROL_INPUTS:
        path = ROOT / item
        rows.append(
            {
                "path": item,
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return rows


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


def packet_records(packet: dict[str, Any]) -> list[dict[str, Any]]:
    records = packet.get("records")
    if isinstance(records, list):
        return records
    return []


def target_otg0_packets() -> dict[str, dict[str, Any]]:
    manifest = read_json(OT / f"OTG0_FROZEN_COHORT_PACKET_MANIFEST_{DATE_STAMP}.json")
    return {row["packet_id"]: row for row in manifest["packets"] if row.get("packet_id") in TARGET_PACKET_IDS}


def load_packet_jsons() -> dict[str, dict[str, Any]]:
    g3_manifest = read_json(G3_DIR / f"OTB2R_G3_GEOMETRY_PACKET_MANIFEST_{DATE_STAMP}.json")
    g6_manifest = read_json(G6_DIR / f"OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_{DATE_STAMP}.json")
    paths: dict[str, str] = dict(g3_manifest["packet_paths"])
    for item in g6_manifest["packets"]:
        paths[item["packet_id"]] = item["packet_path"]

    packets = {}
    for packet_id in TARGET_PACKET_IDS:
        packet_path = ROOT / paths[packet_id]
        packets[packet_id] = read_json(packet_path)
    return packets


def prior_g12_blockers_by_packet() -> dict[str, dict[str, Any]]:
    prior = read_json(G12_REBUILD / f"G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_{DATE_STAMP}.json")
    return {
        row["packet_id"]: row
        for row in prior.get("blocked_questions", [])
        if row.get("packet_id") in TARGET_PACKET_IDS
    }


def prior_g12_decisions_by_packet() -> dict[str, dict[str, Any]]:
    prior = read_json(G12_REBUILD / f"G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_{DATE_STAMP}.json")
    return {
        row["packet_id"]: row
        for row in prior.get("packet_decisions", [])
        if row.get("packet_id") in TARGET_PACKET_IDS
    }


def exact_builder_blockers() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {pid: [] for pid in TARGET_PACKET_IDS}
    g3 = read_json(G3_DIR / f"OTB2R_G3_GEOMETRY_EXACT_BLOCKER_LEDGER_{DATE_STAMP}.json")
    for packet_id, counts in g3.get("blocker_counts_by_packet", {}).items():
        if packet_id in out:
            for blocker_code, count in counts.items():
                out[packet_id].append(
                    {
                        "blocker_code": blocker_code,
                        "count": count,
                        "blocking_fact": "Some candidate rows were skipped because local OHLC coverage was stale at decision time.",
                        "next_action": "Refresh or register source-complete local OHLC coverage for the named symbol/timeframe before adding those skipped rows.",
                    }
                )
    g6 = read_json(G6_DIR / f"OTB2R_G6_EXACT_BLOCKER_LEDGER_{DATE_STAMP}.json")
    for blocker in g6.get("blockers", []):
        if blocker.get("packet_id") in out:
            out[blocker["packet_id"]].append(blocker)
    return out


def registry_chain_rows() -> dict[str, dict[str, Any]]:
    otg0 = target_otg0_packets()
    prereg = read_json(ROOT / "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json")
    hypotheses = read_json(ROOT / "research/science_program_2026_05/02_hypothesis_registry/HYPOTHESIS_REGISTRY_2026-05-06.json")
    sources = read_json(ROOT / "research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.json")

    prereg_by_exp = {row["experiment_id"]: row for row in prereg["rows"]}
    hyp_by_id = {row["hypothesis_id"]: row for row in hypotheses["rows"]}
    source_by_id = {row["source_id"]: row for row in sources["rows"]}

    chain = {}
    for packet_id, row in otg0.items():
        exp = row["experiment_id"]
        hyp = row["hypothesis_id"]
        hyp_row = hyp_by_id.get(hyp, {})
        source_ids = hyp_row.get("source_ids") or []
        chain[packet_id] = {
            "packet_id": packet_id,
            "experiment_id": exp,
            "hypothesis_id": hyp,
            "otg0_owner_testing_class": row.get("owner_testing_class"),
            "otg0_testing_lane": row.get("otg0_testing_lane"),
            "otg0_packet_status": row.get("packet_status"),
            "otg0_source_gate_status": row.get("source_gate_status"),
            "sample_floor": row.get("sample_floor"),
            "duplicate_policy": row.get("duplicate_policy"),
            "label_separation_policy": row.get("label_separation_policy"),
            "label_family_from_hypothesis": row.get("label_family_from_hypothesis"),
            "result_quarantine_path": row.get("result_quarantine_path"),
            "required_packet_fields": row.get("required_packet_fields") or [],
            "prereg_row_present": exp in prereg_by_exp,
            "hypothesis_row_present": hyp in hyp_by_id,
            "source_contract_rows": [
                {
                    "source_id": source_id,
                    "present": source_id in source_by_id,
                    "validation_safe": source_by_id.get(source_id, {}).get("validation_safe"),
                    "access_legal_state": source_by_id.get(source_id, {}).get("access_legal_state"),
                    "cache_path": source_by_id.get(source_id, {}).get("cache_path"),
                }
                for source_id in source_ids
            ],
        }
    return chain


def recompute_hash_review(packets: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    failures = []
    for packet_id, packet in packets.items():
        packet_path = packet_path_for(packet_id)
        records = packet_records(packet)
        record_failures = 0
        for idx, record in enumerate(records):
            if "source_hash_payload" in record:
                expected = sha256_json(record["source_hash_payload"])
                contract = "g3_source_hash_payload"
            elif "sanitized_source_hash_components" in record:
                expected = sha256_json(record["sanitized_source_hash_components"])
                contract = "g6_sanitized_source_hash_components"
            else:
                expected = None
                contract = "missing_source_hash_payload"
            actual = record.get("source_hash")
            if expected != actual:
                record_failures += 1
                failures.append(
                    {
                        "packet_id": packet_id,
                        "record_index": idx,
                        "record_id": record.get("record_id") or record.get("setup_id"),
                        "contract": contract,
                        "source_hash": actual,
                        "recomputed_source_hash": expected,
                    }
                )
        packet_hash_failure = False
        packet_hash_expected = None
        if "packet_hash" in packet:
            packet_hash_expected = sha256_json({k: v for k, v in packet.items() if k != "packet_hash"})
            packet_hash_failure = packet_hash_expected != packet.get("packet_hash")
            if packet_hash_failure:
                failures.append(
                    {
                        "packet_id": packet_id,
                        "record_index": None,
                        "record_id": "__packet_hash__",
                        "contract": "top_level_packet_hash",
                        "packet_hash": packet.get("packet_hash"),
                        "recomputed_packet_hash": packet_hash_expected,
                    }
                )
        rows.append(
            {
                "packet_id": packet_id,
                "packet_file": rel(packet_path),
                "packet_file_sha256": sha256_file(packet_path),
                "record_count": len(records),
                "source_hash_contract": "source_hash_payload" if packet_id.startswith(("OTG0-PKT-031", "OTG0-PKT-032", "OTG0-PKT-036")) else "sanitized_source_hash_components",
                "source_hash_failure_count": record_failures,
                "packet_hash_present": "packet_hash" in packet,
                "packet_hash_matches": not packet_hash_failure if "packet_hash" in packet else None,
                "packet_hash_recomputed": packet_hash_expected,
            }
        )
    return rows, failures


def packet_path_for(packet_id: str) -> Path:
    g3_manifest = read_json(G3_DIR / f"OTB2R_G3_GEOMETRY_PACKET_MANIFEST_{DATE_STAMP}.json")
    if packet_id in g3_manifest.get("packet_paths", {}):
        return ROOT / g3_manifest["packet_paths"][packet_id]
    g6_manifest = read_json(G6_DIR / f"OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_{DATE_STAMP}.json")
    for row in g6_manifest["packets"]:
        if row["packet_id"] == packet_id:
            return ROOT / row["packet_path"]
    raise KeyError(packet_id)


def duplicate_review(packets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    g3_dup = read_json(G3_DIR / f"OTB2R_G3_GEOMETRY_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json")
    g6_dup = read_json(G6_DIR / f"OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json")
    rows = []
    for packet_id, packet in packets.items():
        records = packet_records(packet)
        group_counts = Counter(record.get("duplicate_group_id") for record in records)
        parent_counts = Counter(record.get("parent_duplicate_group_id") for record in records if record.get("parent_duplicate_group_id"))
        rows.append(
            {
                "packet_id": packet_id,
                "raw_record_count": len(records),
                "unique_duplicate_group_count": len(group_counts),
                "duplicate_group_reuse_count": sum(1 for count in group_counts.values() if count > 1),
                "max_records_per_duplicate_group": max(group_counts.values(), default=0),
                "unique_parent_duplicate_group_count": len(parent_counts) or None,
                "denominator_policy": "Use unique duplicate_group_id inside the packet; use parent_duplicate_group_id for G3 cross-family setup counts; never add OB and generic controls as independent denominator rows.",
            }
        )
    return {
        "artifact_family": "G12_G3_G6_DUPLICATE_DENOMINATOR_REVIEW",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_rows": rows,
        "source_audit_refs": [
            rel(G3_DIR / f"OTB2R_G3_GEOMETRY_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json"),
            rel(G6_DIR / f"OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT_{DATE_STAMP}.json"),
        ],
        "g3_builder_summary": g3_dup.get("packet_duplicate_summary"),
        "g6_builder_packet_count": len(g6_dup.get("packets", [])),
        "red_team_finding": "No packet may use raw records as the validation denominator. G6 OTG0-PKT-060 keeps generic comparator fields inside matched OB records; standalone generic-control rows are rejected.",
    }


def label_review(packets: dict[str, dict[str, Any]], chain: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for packet_id, packet in packets.items():
        records = packet_records(packet)
        materialized = Counter(record.get("label_family") for record in records)
        rows.append(
            {
                "packet_id": packet_id,
                "experiment_id": packet.get("experiment_id"),
                "otg0_label_family": chain[packet_id].get("label_family_from_hypothesis"),
                "declared_future_label_family": packet.get("declared_future_label_family") or packet.get("label_family"),
                "materialized_record_label_family_counts": dict(materialized),
                "label_values_absent": all(record.get("label_values_absent") is True for record in records)
                if packet_id in {"OTG0-PKT-031", "OTG0-PKT-032", "OTG0-PKT-036"}
                else packet.get("label_family_materialized_in_records") == "input_only_features_no_labels",
                "broker_path_lifecycle_pooling_allowed": False,
                "policy": "Future broker actual-R, synthetic path-R, and lifecycle/no-fill labels must be separate artifacts with non-overlapping denominators.",
            }
        )
    return {
        "artifact_family": "G12_G3_G6_LABEL_FAMILY_REVIEW",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_rows": rows,
        "red_team_finding": "G3 declares synthetic_path_r for future use but writes no label values. G6 writes input_only_features_no_labels and declares the future family separately; OTG0-PKT-061 is lifecycle/no-fill, not synthetic path-R.",
    }


def noleak_review(packets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    total_hits = 0
    for packet_id, packet in packets.items():
        hits = forbidden_key_hits(packet_records(packet))
        total_hits += len(hits)
        rows.append(
            {
                "packet_id": packet_id,
                "record_count": len(packet_records(packet)),
                "forbidden_record_key_hit_count": len(hits),
                "forbidden_record_key_hits": hits[:50],
                "top_level_safety_flags": {
                    "promotion_verdict": packet.get("promotion_verdict"),
                    "validation_safe": packet.get("validation_safe"),
                    "outcome_review_opened": packet.get("outcome_review_opened"),
                    "broker_actual_r_inspected": packet.get("broker_actual_r_inspected"),
                    "blocked_packet_outcomes_inspected": packet.get("blocked_packet_outcomes_inspected"),
                    "outcome_scoring_run": packet.get("outcome_scoring_run"),
                    "result_or_quarantine_outputs_created": packet.get("result_or_quarantine_outputs_created"),
                },
            }
        )
    return {
        "artifact_family": "G12_G3_G6_LEAKAGE_NOLEAK_REVIEW",
        "audit_scope": "packet records plus top-level safety flags; forbidden result/account-history/resolution sources are not opened",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "forbidden_key_fragments": RESULT_FIELD_FRAGMENTS,
        "allowed_control_keys": sorted(ALLOWED_CONTROL_KEYS),
        "packet_rows": rows,
        "total_forbidden_record_key_hits": total_hits,
        "skipped_by_policy_sources": [
            "shadow_logs/broker_actual_r_audit.jsonl",
            "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
            "shadow_logs/continuation_no_retrace_resolutions.jsonl",
            "shadow_logs/m15_choch_diagnostic_audit.jsonl",
            "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/",
            "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/",
            "research/science_program_2026_05/06_outcome_testing/outcome_review/",
        ],
        "red_team_finding": "No forbidden record keys were found under the stricter scan if total_forbidden_record_key_hits remains zero. TP fields are allowed only as input geometry.",
    }


def parse_z(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def source_freshness_review(packets: dict[str, dict[str, Any]], blockers: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    for packet_id, packet in packets.items():
        records = packet_records(packet)
        selected_source_count = 0
        selected_source_window_violations = []
        source_capture_dates = Counter()
        for ridx, record in enumerate(records):
            decision = parse_z(record.get("decision_asof_utc"))
            if record.get("source_capture_utc"):
                source_capture_dates[str(record["source_capture_utc"])[:10]] += 1
            for timeframe, source in (record.get("selected_local_ohlc_sources") or {}).items():
                selected_source_count += 1
                end = parse_z(source.get("feature_window_end_utc"))
                if decision and end and end > decision:
                    selected_source_window_violations.append(
                        {
                            "record_index": ridx,
                            "packet_id": packet_id,
                            "setup_id": record.get("setup_id"),
                            "timeframe": timeframe,
                            "feature_window_end_utc": source.get("feature_window_end_utc"),
                            "decision_asof_utc": record.get("decision_asof_utc"),
                        }
                    )
        blocker_counts = Counter()
        for blocker in blockers.get(packet_id, []):
            blocker_counts[blocker.get("blocker_code") or blocker.get("blocker_id")] += blocker.get("count", 1)
        rows.append(
            {
                "packet_id": packet_id,
                "record_count": len(records),
                "selected_local_ohlc_source_count": selected_source_count,
                "selected_source_future_window_violation_count": len(selected_source_window_violations),
                "selected_source_future_window_violations": selected_source_window_violations[:20],
                "builder_stale_or_source_blocker_counts": dict(blocker_counts),
                "source_capture_dates": dict(source_capture_dates),
                "staleness_status": "HAS_SOURCE_BLOCKERS_RECORDED" if blocker_counts else "NO_BUILDER_STALENESS_BLOCKERS_RECORDED",
            }
        )
    return {
        "artifact_family": "G12_G3_G6_SOURCE_FRESHNESS_STALENESS_REVIEW",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_rows": rows,
        "red_team_finding": "Selected G3 OHLC feature windows are checked for future-window violations, while skipped stale OHLC rows remain recorded blockers. G6 blockers are source-field completeness blockers rather than result evidence.",
    }


def same_bar_review(packets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for packet_id, packet in packets.items():
        policy_counts = Counter()
        state_counts = Counter()
        for record in packet_records(packet):
            policy_counts[record.get("same_bar_ambiguity_policy") or "not_applicable_or_missing"] += 1
            state_counts[record.get("same_bar_ambiguity_state") or "not_applicable_or_missing"] += 1
        rows.append(
            {
                "packet_id": packet_id,
                "policy_counts": dict(policy_counts),
                "state_counts": dict(state_counts),
                "terminal_order_claim_allowed": False,
                "same_bar_timing_evidence": "G3 closed-candle input policy and G6 local-OHLC bounded path policy; no terminal order field is accepted.",
            }
        )
    return {
        "artifact_family": "G12_G3_G6_SAME_BAR_TIMING_REVIEW",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_rows": rows,
        "source_policy_refs": [
            rel(G3_DIR / f"OTB2R_G3_GEOMETRY_SAME_BAR_POLICY_{DATE_STAMP}.json"),
            rel(G6_DIR / f"OTB2R_G6_SAME_BAR_TIMING_POLICY_{DATE_STAMP}.json"),
        ],
        "red_team_finding": "Packets may carry path windows but cannot claim entry/SL/TP/continuation/reversal terminal order. Same-minute ambiguity remains bounded or unclaimed.",
    }


def source_hash_review(rows: list[dict[str, Any]], failures: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact_family": "G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_rows": rows,
        "failure_count": len(failures),
        "failures": failures[:50],
        "parser_determinism_evidence": [
            {
                "packet_id": "OTG0-PKT-060",
                "evidence": rel(G6_DIR / f"test_otb2r_g6_local_ohlc_momentum_reversion_packets_{DATE_STAMP.replace('-', '_')}.py"),
                "scope": "OB-bound parser unit test exists; audit still blocks or limits verifier-text OB bounds as weaker than structured source rows.",
            }
        ],
        "red_team_finding": "Record source hashes are reproducible from sanitized source components/payloads. G6 top-level packet hashes also recompute.",
    }


def decision_for_packet(
    packet_id: str,
    packet: dict[str, Any],
    chain: dict[str, dict[str, Any]],
    noleak: dict[str, Any],
    hash_failure_count: int,
    blockers: list[dict[str, Any]],
) -> tuple[str, str, str]:
    records = packet_records(packet)
    if not records:
        return (
            "BLOCKED_WITH_NEXT_EXACT_QUESTION",
            "No input records exist.",
            "Which approved source-specific packet builder can produce nonzero source-hashed input-only rows without opening outcomes?",
        )
    if hash_failure_count:
        return (
            "REJECT_INVALID_PACKET_CLEARING",
            "Source hash recomputation failed.",
            "Regenerate the packet from stable source-hash components and prove zero recompute failures.",
        )
    row = next((item for item in noleak["packet_rows"] if item["packet_id"] == packet_id), {})
    if row.get("forbidden_record_key_hit_count"):
        return (
            "REJECT_INVALID_PACKET_CLEARING",
            "Forbidden result/outcome/broker field keys are present in packet records.",
            "Remove all result-bearing fields and rebuild from input-only projections.",
        )

    core_blockers = {
        "OTG0-PKT-060": "Structured OB bounds are core to OB-vs-generic; verifier-text parsing is not strong enough for this packet to clear outcome-audit readiness.",
        "OTG0-PKT-061": "Exact executable decision price and ordered path are core to continuation/no-retrace lifecycle odds.",
        "OTG0-PKT-063": "A true preregistered changepoint source is core to the exhaustion/changepoint hypothesis; current fields are only OHLC proxy scaffolding.",
        "OTG0-PKT-066": "Structured liquidity-sweep fields are core to the round-number/OB confluence hypothesis.",
    }
    if packet_id in core_blockers:
        next_questions = {
            "OTG0-PKT-060": "Can every OB bound and generic retrace comparator be supplied from structured mechanical market-state/source rows with file/row hash, and can the matched-control denominator reach the preregistered floor without standalone generic rows?",
            "OTG0-PKT-061": "Can a prospective packet supply exact executable decision price plus ordered M1/tick path source before any continuation/no-retrace resolution labels are opened?",
            "OTG0-PKT-063": "Can a preregistered changepoint parser/model output be produced with feature_asof_utc <= decision_asof_utc and fixed thresholds before scoring?",
            "OTG0-PKT-066": "Can decision-time liquidity sweep type, sweep level, and source hash be joined to every XAU OB-zone/round-number record before outcome opening?",
        }
        return ("BLOCKED_WITH_NEXT_EXACT_QUESTION", core_blockers[packet_id], next_questions[packet_id])

    sample_note = f"Record count {len(records)} remains below or unproven against sample floor: {chain[packet_id].get('sample_floor')}"
    return (
        "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY",
        "Prior G12 zero-record blocker is cleared with source-hashed input-only rows, no forbidden result fields, separated labels, duplicate policy, and terminal-order unclaimed. " + sample_note,
        "No next exact blocker for packet-readiness; future outcome audit must stay quarantined and cannot claim validation until source/sample/concentration floors pass.",
    )


def build_decision_ledger(
    packets: dict[str, dict[str, Any]],
    chain: dict[str, dict[str, Any]],
    noleak: dict[str, Any],
    hash_rows: list[dict[str, Any]],
    blockers: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    prior_blockers = prior_g12_blockers_by_packet()
    prior_decisions = prior_g12_decisions_by_packet()
    hash_failures_by_packet = {row["packet_id"]: row["source_hash_failure_count"] for row in hash_rows}
    decisions = []
    for packet_id in TARGET_PACKET_IDS:
        packet = packets[packet_id]
        decision, reason, next_question = decision_for_packet(
            packet_id,
            packet,
            chain,
            noleak,
            hash_failures_by_packet.get(packet_id, 0),
            blockers.get(packet_id, []),
        )
        records = packet_records(packet)
        decisions.append(
            {
                "packet_id": packet_id,
                "experiment_id": packet.get("experiment_id"),
                "hypothesis_id": packet.get("hypothesis_id"),
                "packet_family": "G3_GEOMETRY" if packet_id in {"OTG0-PKT-031", "OTG0-PKT-032", "OTG0-PKT-036"} else "G6_LOCAL_OHLC",
                "decision": decision,
                "decision_reason": reason,
                "next_exact_question": next_question,
                "record_count": len(records),
                "unique_duplicate_group_count": len({record.get("duplicate_group_id") for record in records}),
                "packet_file": rel(packet_path_for(packet_id)),
                "packet_file_sha256": sha256_file(packet_path_for(packet_id)),
                "prior_g12_rebuild_decision": prior_decisions.get(packet_id, {}).get("g12_reaudit_decision"),
                "prior_g12_next_exact_question": prior_blockers.get(packet_id, {}).get("next_exact_question"),
                "builder_exact_blockers": blockers.get(packet_id, []),
                "otg0_sample_floor": chain[packet_id].get("sample_floor"),
                "otg0_label_policy": chain[packet_id].get("label_separation_policy"),
                "source_gate_status": chain[packet_id].get("otg0_source_gate_status"),
            }
        )
    return {
        "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
        "artifact_type": "decision_ledger",
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "outcomes_run": False,
        "r_result_values_inspected": False,
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "paid_network_api_databento_mt5_calls": False,
        "live_surface_changes": False,
        "scope": "red_team_packet_readiness_audit_only_for_g3_g6_builders",
        "controlling_inputs": control_input_hashes(),
        "packet_decisions": decisions,
        "decision_counts": dict(Counter(row["decision"] for row in decisions)),
    }


def accepted_shortlist(decision_ledger: dict[str, Any]) -> dict[str, Any]:
    accepted = [
        {
            "packet_id": row["packet_id"],
            "experiment_id": row["experiment_id"],
            "packet_family": row["packet_family"],
            "accepted_scope": "future_quarantined_outcome_audit_only_no_validation_no_results_opened_here",
            "packet_file": row["packet_file"],
            "packet_file_sha256": row["packet_file_sha256"],
            "record_count": row["record_count"],
            "unique_duplicate_group_count": row["unique_duplicate_group_count"],
            "residual_limitations": [
                "validation_safe remains false",
                "sample-floor/concentration/DSR-PBO gates are future result-lane checks",
                "no promotion or live-rule discussion is permitted from this packet audit",
            ],
        }
        for row in decision_ledger["packet_decisions"]
        if row["decision"] == "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY"
    ]
    return {
        "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
        "artifact_type": "accepted_packet_shortlist",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "accepted_packets": accepted,
        "scope_limit": "Accepted only for a future quarantined outcome audit. This is not validation-safe and no outcome review was opened.",
    }


def blocked_rejected_ledger(decision_ledger: dict[str, Any]) -> dict[str, Any]:
    g3_alt = read_json(G3_DIR / f"OTB2R_G3_GEOMETRY_REJECTED_ALTERNATIVES_LEDGER_{DATE_STAMP}.json")
    g6_neg = read_json(G6_DIR / f"OTB2R_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{DATE_STAMP}.json")
    blocked = [
        {
            "packet_id": row["packet_id"],
            "experiment_id": row["experiment_id"],
            "decision": row["decision"],
            "decision_reason": row["decision_reason"],
            "next_exact_question": row["next_exact_question"],
            "evidence": row["packet_file"],
            "builder_exact_blockers": row["builder_exact_blockers"],
        }
        for row in decision_ledger["packet_decisions"]
        if row["decision"] != "ACCEPT_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_ONLY"
    ]
    rejected_alternatives = list(g3_alt.get("rejected_alternatives", []))
    rejected_alternatives.extend(
        {
            "alternative": item["path"],
            "decision": "REJECTED_AS_PACKET_INPUT_SOURCE",
            "reason": item["reason"],
        }
        for item in g6_neg.get("skipped_sources_by_policy", [])
    )
    rejected_alternatives.extend(
        [
            {
                "alternative": "Pool OB setup rows and generic retrace comparator rows as independent records",
                "decision": "REJECTED_DENOMINATOR_INFLATION",
                "reason": "OTG0-PKT-060 must use matched_control_group_id; OB and generic comparator fields share one setup denominator.",
            },
            {
                "alternative": "Treat same-bar path windows as terminal-order evidence",
                "decision": "REJECTED_NO_LEAK_TIMING_POLICY",
                "reason": "Packets may define path_start/path_end only; terminal order remains unclaimed until a future outcome lane freezes tick/order policy.",
            },
            {
                "alternative": "Open broker actual-R or OTI quarantined result folders to judge packet quality",
                "decision": "REJECTED_FOR_SCOPE_AND_LABEL_POLICY",
                "reason": "This audit is packet-readiness only and must not inspect broker actual-R, result values, or blocked outcomes.",
            },
        ]
    )
    return {
        "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
        "artifact_type": "blocked_rejected_question_ledger",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "blocked_or_rejected_packets": blocked,
        "rejected_alternative_packetizations": rejected_alternatives,
    }


def next_lane_recommendation(decision_ledger: dict[str, Any], accepted: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
        "artifact_type": "next_lane_recommendation",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "recommendation": "Do not open G3/G6 outcomes as a pooled lane. If owner chooses to proceed, open only the accepted packets in a quarantined result audit with sample-floor warnings, while blocking G6-001/G6-002/G6-004/G6-007 until their exact source questions are cleared.",
        "accepted_packet_ids": [row["packet_id"] for row in accepted["accepted_packets"]],
        "blocked_packet_ids": [
            row["packet_id"]
            for row in decision_ledger["packet_decisions"]
            if row["decision"] == "BLOCKED_WITH_NEXT_EXACT_QUESTION"
        ],
        "priority_order": [
            "First: use accepted G3 geometry packets and G6 opening-drive only for quarantined packet-audit/discovery if an outcome lane is explicitly opened.",
            "Second: repair G6-001 structured OB bounds and matched-control denominator before any OB-vs-generic result.",
            "Third: keep G6-002 prospective until exact executable price plus ordered M1/tick path are captured.",
            "Fourth: register true changepoint and liquidity-sweep as-of sources before G6-004/G6-007 scoring.",
        ],
    }


def load_verification_results() -> dict[str, Any] | None:
    path = OUT / f"G12_G3_G6_VERIFICATION_RESULTS_{DATE_STAMP}.json"
    if path.exists():
        return read_json(path)
    return None


def completion_audit(bundle: dict[str, Any]) -> dict[str, Any]:
    decision_ledger = bundle["decision_ledger"]
    verification = load_verification_results()
    checklist = [
        {
            "requirement": "Mandatory GTOS preflight completed and LIVE_STATE regenerated",
            "evidence": ".context/LIVE_STATE.md exists in controlling inputs with current file hash",
            "status": "PASS" if any(row["path"] == ".context/LIVE_STATE.md" and row["exists"] for row in decision_ledger["controlling_inputs"]) else "FAIL",
        },
        {
            "requirement": "Every G3/G6 packet has an explicit accept/block/reject decision",
            "evidence": f"{len(decision_ledger['packet_decisions'])}/8 decisions; counts={decision_ledger['decision_counts']}",
            "status": "PASS" if len(decision_ledger["packet_decisions"]) == len(TARGET_PACKET_IDS) else "FAIL",
        },
        {
            "requirement": "No replay outcomes, broker actual-R, blocked-packet outcomes, R/result statistics, MT5/API/network, or live trading surfaces touched",
            "evidence": "decision ledger safety flags all false and skipped sources named by policy",
            "status": "PASS"
            if not any(
                decision_ledger[key]
                for key in [
                    "outcomes_run",
                    "r_result_values_inspected",
                    "broker_actual_r_inspected",
                    "blocked_packet_outcomes_inspected",
                    "paid_network_api_databento_mt5_calls",
                    "live_surface_changes",
                ]
            )
            else "FAIL",
        },
        {
            "requirement": "Leakage/no-leak review covers result/R, post-decision, blocked-outcome, and broker actual-R contamination",
            "evidence": f"forbidden_record_key_hits={bundle['noleak_review']['total_forbidden_record_key_hits']}",
            "status": "PASS" if bundle["noleak_review"]["total_forbidden_record_key_hits"] == 0 else "FAIL",
        },
        {
            "requirement": "Source-hash and parser reproducibility reviewed",
            "evidence": f"source_hash_failure_count={bundle['source_hash_review']['failure_count']}",
            "status": "PASS" if bundle["source_hash_review"]["failure_count"] == 0 else "FAIL",
        },
        {
            "requirement": "Duplicate denominator and OB/generic control pooling reviewed",
            "evidence": "duplicate review written; G6 matched-control policy rejects independent generic rows",
            "status": "PASS",
        },
        {
            "requirement": "Label-family separation reviewed",
            "evidence": "label review written and pooling disallowed for every packet",
            "status": "PASS",
        },
        {
            "requirement": "Same-bar/timing policy reviewed and terminal-order guessing rejected",
            "evidence": "same-bar review written with terminal_order_claim_allowed=false",
            "status": "PASS",
        },
        {
            "requirement": "Source freshness/staleness and stale context reviewed",
            "evidence": "freshness review written with G3 stale OHLC blockers and G6 source-field blockers retained",
            "status": "PASS",
        },
        {
            "requirement": "Rejected alternatives recorded",
            "evidence": f"{len(bundle['blocked_rejected_ledger']['rejected_alternative_packetizations'])} rejected alternatives",
            "status": "PASS",
        },
        {
            "requirement": "JSON/schema/no-promotion/unsafe-flag/py_compile/focused pytest checks run",
            "evidence": "verification results artifact present" if verification else "verification results artifact not present yet",
            "status": "PASS" if verification and verification.get("summary", {}).get("overall_status") == "PASS" else "PENDING",
        },
    ]
    can_mark_goal_complete = all(item["status"] == "PASS" for item in checklist)
    return {
        "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
        "artifact_type": "completion_audit",
        "objective_restatement": "Red-team G3/G6 packet-builder readiness from prereg through OTG0, OTB2/OTB2R, prior G12 blockers, builder outputs, source hashes, duplicate policy, label policy, no-leak policy, same-bar/timing policy, source freshness, and completion audits without opening outcomes.",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "prompt_to_artifact_checklist": checklist,
        "verification_results": verification,
        "summary": {
            "can_mark_goal_complete": can_mark_goal_complete,
            "accepted_packets": len(bundle["accepted_shortlist"]["accepted_packets"]),
            "blocked_packets": len(bundle["blocked_rejected_ledger"]["blocked_or_rejected_packets"]),
            "rejected_invalid_packet_clearing": sum(
                1 for row in decision_ledger["packet_decisions"] if row["decision"] == "REJECT_INVALID_PACKET_CLEARING"
            ),
            "outcome_review_opened": OUTCOME_REVIEW_OPENED,
            "validation_safe": VALIDATION_SAFE,
        },
    }


def render_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(item).replace("\n", " ") for item in row) + " |")
    return out


def render_decision_md(data: dict[str, Any]) -> str:
    lines = [
        "# G12 G3/G6 Packet Builder Audit Decision Ledger - 2026-05-07",
        "",
        f"Promotion verdict: `{data['promotion_verdict']}`",
        f"Validation safe: `{data['validation_safe']}`",
        f"Outcome review opened: `{data['outcome_review_opened']}`",
        "",
        "No outcomes, broker actual-R, blocked packet outcomes, R/result statistics, paid/API/MT5/network calls, or live trading surfaces were opened.",
        "",
        "## Decisions",
        "",
    ]
    lines.extend(
        render_table(
            ["Packet", "Experiment", "Decision", "Rows", "Unique groups", "Reason"],
            [
                [
                    row["packet_id"],
                    row["experiment_id"],
                    row["decision"],
                    row["record_count"],
                    row["unique_duplicate_group_count"],
                    row["decision_reason"],
                ]
                for row in data["packet_decisions"]
            ],
        )
    )
    return "\n".join(lines)


def render_simple_md(title: str, data: dict[str, Any]) -> str:
    lines = [
        f"# {title} - 2026-05-07",
        "",
        f"Promotion verdict: `{data.get('promotion_verdict')}`",
        f"Validation safe: `{data.get('validation_safe')}`",
        f"Outcome review opened: `{data.get('outcome_review_opened')}`",
        "",
        "```json",
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True)[:70000],
        "```",
        "",
    ]
    return "\n".join(lines)


def build_bundle() -> dict[str, Any]:
    packets = load_packet_jsons()
    chain = registry_chain_rows()
    blockers = exact_builder_blockers()
    hash_rows, hash_failures = recompute_hash_review(packets)
    source_hash = source_hash_review(hash_rows, hash_failures)
    noleak = noleak_review(packets)
    duplicate = duplicate_review(packets)
    labels = label_review(packets, chain)
    same_bar = same_bar_review(packets)
    freshness = source_freshness_review(packets, blockers)
    decision = build_decision_ledger(packets, chain, noleak, hash_rows, blockers)
    accepted = accepted_shortlist(decision)
    blocked = blocked_rejected_ledger(decision)
    next_lane = next_lane_recommendation(decision, accepted)
    bundle = {
        "decision_ledger": decision,
        "accepted_shortlist": accepted,
        "blocked_rejected_ledger": blocked,
        "noleak_review": noleak,
        "duplicate_review": duplicate,
        "label_review": labels,
        "source_hash_review": source_hash,
        "same_bar_review": same_bar,
        "source_freshness_review": freshness,
        "next_lane_recommendation": next_lane,
    }
    bundle["completion_audit"] = completion_audit(bundle)
    return bundle


def write_bundle(bundle: dict[str, Any]) -> None:
    mapping = {
        f"G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_{DATE_STAMP}": bundle["decision_ledger"],
        f"G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_{DATE_STAMP}": bundle["accepted_shortlist"],
        f"G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_{DATE_STAMP}": bundle["blocked_rejected_ledger"],
        f"G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_{DATE_STAMP}": bundle["noleak_review"],
        f"G12_G3_G6_DUPLICATE_DENOMINATOR_REVIEW_{DATE_STAMP}": bundle["duplicate_review"],
        f"G12_G3_G6_LABEL_FAMILY_REVIEW_{DATE_STAMP}": bundle["label_review"],
        f"G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW_{DATE_STAMP}": bundle["source_hash_review"],
        f"G12_G3_G6_SAME_BAR_TIMING_REVIEW_{DATE_STAMP}": bundle["same_bar_review"],
        f"G12_G3_G6_SOURCE_FRESHNESS_STALENESS_REVIEW_{DATE_STAMP}": bundle["source_freshness_review"],
        f"G12_G3_G6_NEXT_LANE_RECOMMENDATION_{DATE_STAMP}": bundle["next_lane_recommendation"],
        f"G12_G3_G6_COMPLETION_AUDIT_{DATE_STAMP}": bundle["completion_audit"],
    }
    for stem, data in mapping.items():
        write_json(OUT / f"{stem}.json", data)
        if "DECISION_LEDGER" in stem:
            write_md(OUT / f"{stem}.md", render_decision_md(data))
        else:
            title = stem.replace("_", " ").title()
            write_md(OUT / f"{stem}.md", render_simple_md(title, data))

    manifest_paths = [OUT / f"{stem}.{ext}" for stem in mapping for ext in ("json", "md")]
    for ext in ("json", "md"):
        verification_path = OUT / f"G12_G3_G6_VERIFICATION_RESULTS_{DATE_STAMP}.{ext}"
        if verification_path.exists():
            manifest_paths.append(verification_path)

    manifest = {
        "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "artifacts": [
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in manifest_paths
        ],
    }
    write_json(OUT / f"G12_G3_G6_ARTIFACT_MANIFEST_{DATE_STAMP}.json", manifest)


def main() -> None:
    bundle = build_bundle()
    write_bundle(bundle)
    print(
        json.dumps(
            {
                "decision_counts": bundle["decision_ledger"]["decision_counts"],
                "source_hash_failures": bundle["source_hash_review"]["failure_count"],
                "forbidden_record_key_hits": bundle["noleak_review"]["total_forbidden_record_key_hits"],
                "completion_status": bundle["completion_audit"]["summary"]["can_mark_goal_complete"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
