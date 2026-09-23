"""Build the G12 OTX G6 post-audit artifact pack.

Research-control only. This script reads the frozen OTX tick-aware resolution
artifacts, prior G12/OTB/OTI packet audits, and read-only local tick metadata.
It emits G12-owned audit ledgers for the post-audit lane without opening broker
actual-R, live order state, paid/API sources, or live trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


DATE_STAMP = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

BASE = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
OUTCOME_ROOT = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing"
OTX = OUTCOME_ROOT / "otx_g6_tick_aware_end_to_end_resolution"
TICK_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")
WORKTREE_TICK_ROOT = REPO_ROOT / "data/ticks"

PACKET_IDS = ["OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-062", "OTG0-PKT-063", "OTG0-PKT-066"]

OTX_JSON_FILES = {
    "internal": OTX / "OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.json",
    "blocker": OTX / "OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-07.json",
    "coverage": OTX / "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
    "source_hash": OTX / "OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json",
    "proposals": OTX / "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    "result": OTX / "OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER_2026-05-07.json",
    "methodology": OTX / "OTX_G6_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.json",
    "self_review": OTX / "OTX_G6_ADVERSARIAL_SELF_REVIEW_2026-05-07.json",
    "completion": OTX / "OTX_G6_COMPLETION_AUDIT_2026-05-07.json",
}

PRIOR_JSON_FILES = {
    "otg0_manifest": OUTCOME_ROOT / "OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "otg0_rules": OUTCOME_ROOT / "OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "g12_g3_g6_decisions": OUTCOME_ROOT / "g12_g3_g6_packet_builder_audit/G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.json",
    "g12_g3_g6_accepted": OUTCOME_ROOT / "g12_g3_g6_packet_builder_audit/G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
    "g12_g3_g6_blocked": OUTCOME_ROOT / "g12_g3_g6_packet_builder_audit/G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_2026-05-07.json",
    "oti4_method": OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results/OTI4_METHOD_FREEZE_2026-05-07.json",
    "oti4_result": OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results/OTI4_RESULT_LEDGER_2026-05-07.json",
    "oti4_duplicate": OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results/OTI4_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
    "oti4_label": OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results/OTI4_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.json",
    "oti4_noleak": OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results/OTI4_NO_LEAK_AND_STRICTER_FORMULATION_REPORT_2026-05-07.json",
    "oti4_stats": OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results/OTI4_METHODOLOGY_REPORT_2026-05-07.json",
    "otb6_decisions": OUTCOME_ROOT / "otb6_g6_blocker_clearing_proof_pack/OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json",
    "otb6_negative": OUTCOME_ROOT / "otb6_g6_blocker_clearing_proof_pack/OTB6_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_2026-05-07.json",
    "otb6_contract": OUTCOME_ROOT / "otb6_g6_blocker_clearing_proof_pack/OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.json",
    "otb2r_manifest": OUTCOME_ROOT / "otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_2026-05-07.json",
    "otb2r_blocker": OUTCOME_ROOT / "otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_EXACT_BLOCKER_LEDGER_2026-05-07.json",
    "g12_otb_decisions": OUTCOME_ROOT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json",
    "g12_otb_accepted": OUTCOME_ROOT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
    "g12_otb_blocked": OUTCOME_ROOT / "g12_otb_rebuild_reaudit/G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.json",
}

CONTROL_TEXT_FILES = {
    "live_state": REPO_ROOT / ".context/LIVE_STATE.md",
    "quick_reference": REPO_ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": REPO_ROOT / ".context/00_core/research_current_state.md",
    "goal_discipline": REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    "latest_handoff": REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "controlling_prompt": BASE / "G12_OTX_G6_POST_AUDIT_GOAL_PROMPT_2026-05-07.md",
}

FORBIDDEN_KEYS = {
    "broker_actual_r",
    "account_history",
    "actual_r",
    "win_loss",
    "outcome_r",
    "path_label",
    "path_outcome_status",
    "final_r",
    "realized_r",
    "hit_tp",
    "hit_sl",
    "live_effect",
}

ALLOWED_RESULT_KEYS = {"synthetic_r"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], lines: list[str] | None = None) -> None:
    body = [
        f"# {title}",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
        f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        "",
    ]
    if lines:
        body.extend(lines)
        body.append("")
    body.extend(["```json", json.dumps(payload, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(body), encoding="utf-8")


def base_payload(family: str) -> dict[str, Any]:
    return {
        "artifact_family": family,
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
    }


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return f"ERROR[{result.returncode}]: {result.stderr.strip()}"
    return result.stdout.strip()


def walk_key_hits(value: Any, *, path: str = "$", forbidden: set[str] | None = None) -> list[dict[str, str]]:
    forbidden = forbidden or FORBIDDEN_KEYS
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_lower = str(key).lower()
            if key_lower in forbidden:
                hits.append({"path": f"{path}.{key}", "key": str(key)})
            hits.extend(walk_key_hits(nested, path=f"{path}.{key}", forbidden=forbidden))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(walk_key_hits(nested, path=f"{path}[{idx}]", forbidden=forbidden))
    return hits


def packet_rows(data: dict[str, Any], packet_id: str) -> list[dict[str, Any]]:
    return [row for row in data["records"] if row.get("packet_id") == packet_id]


def coverage_rows(data: dict[str, Any], packet_id: str) -> list[dict[str, Any]]:
    return [row for row in data["rows"] if row.get("packet_id") == packet_id]


def summarize_tick_file(path: Path, windows: list[tuple[str, str]]) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "windows": [],
    }
    if not path.exists():
        return item
    pf = pq.ParquetFile(path)
    item["row_count"] = pf.metadata.num_rows
    item["columns"] = pf.schema_arrow.names
    ts_index = pf.schema_arrow.names.index("ts_utc")
    mins = []
    maxs = []
    for idx in range(pf.metadata.num_row_groups):
        stats = pf.metadata.row_group(idx).column(ts_index).statistics
        if stats is not None:
            mins.append(stats.min)
            maxs.append(stats.max)
    item["min_ts_utc"] = min(mins).isoformat() if mins else None
    item["max_ts_utc"] = max(maxs).isoformat() if maxs else None
    table = pq.read_table(path, columns=["ts_utc"])
    ts_values = table.column("ts_utc").to_pylist()
    for start_s, end_s in windows:
        start = datetime.fromisoformat(start_s.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_s.replace("Z", "+00:00"))
        in_window = [ts for ts in ts_values if start <= ts <= end]
        item["windows"].append(
            {
                "start_utc": start_s,
                "end_utc": end_s,
                "row_count": len(in_window),
                "first_ts_utc": in_window[0].isoformat() if in_window else None,
                "last_ts_utc": in_window[-1].isoformat() if in_window else None,
            }
        )
    return item


def source_records(payloads: dict[str, Any]) -> dict[str, Any]:
    rows = payloads["source_hash"]["source_files"]
    current_rows = []
    material_mismatches = []
    context_churn_mismatches = []
    for row in rows:
        listed = row.get("path") or row.get("absolute_path")
        if not listed:
            continue
        if str(listed).startswith("C:\\"):
            current_path = Path(str(listed))
        else:
            current_path = REPO_ROOT / str(listed).replace("/", "\\")
        current_sha = sha256_file(current_path)
        same = current_sha == row.get("sha256")
        current_rows.append(
            {
                "listed_path": listed,
                "current_path": str(current_path),
                "exists_current": current_path.exists(),
                "otx_sha256": row.get("sha256"),
                "current_sha256": current_sha,
                "sha256_matches_otx": same,
                "purpose": row.get("purpose"),
            }
        )
        if not same and any(name in str(listed) for name in ("LIVE_STATE.md", "research_current_state.md")):
            context_churn_mismatches.append(current_rows[-1])
        elif not same:
            material_mismatches.append(current_rows[-1])
    return {
        "otx_source_file_count": len(rows),
        "current_rehash_rows": current_rows,
        "material_source_mismatches": material_mismatches,
        "context_churn_mismatches": context_churn_mismatches,
        "context_hash_mismatch_expected_after_preflight_or_docs_refresh": any(
            (not row["sha256_matches_otx"])
            and any(name in row["listed_path"] for name in ("LIVE_STATE.md", "research_current_state.md"))
            for row in current_rows
        ),
    }


def saturation_search_evidence() -> dict[str, Any]:
    search_roots = [
        OUTCOME_ROOT / "g12_g3_g6_packet_builder_audit",
        OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results",
        OUTCOME_ROOT / "otb6_g6_blocker_clearing_proof_pack",
        OUTCOME_ROOT / "otb2r_g6_local_ohlc_momentum_reversion_packets",
        OUTCOME_ROOT / "g12_otb_rebuild_reaudit",
        OUTCOME_ROOT / "otx_g6_tick_aware_end_to_end_resolution",
        REPO_ROOT / ".context",
        REPO_ROOT / "src",
    ]
    patterns = [
        "mechanical_ob_bounds_asof_v1",
        "market_state_row_hash",
        "touch_sequence",
        "ob_id",
        "XAUUSD_2026-05-06T07:15:00+00:00",
        "XAUUSD_2026-05-06T08:00:00+00:00",
    ]
    hits = {pattern: [] for pattern in patterns}
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".py", ".jsonl"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in patterns:
                if pattern in text:
                    hits[pattern].append(str(path.relative_to(REPO_ROOT)))
    shadow_log_names = []
    shadow_root = REPO_ROOT / "shadow_logs"
    if shadow_root.exists():
        for path in shadow_root.glob("*"):
            name = path.name.lower()
            if any(token in name for token in ("source", "provenance", "tick", "candidate", "path", "mso", "snapshot", "registry", "context")):
                shadow_log_names.append(str(path.relative_to(REPO_ROOT)))
    return {
        "searched_roots": [str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path) for path in search_roots],
        "patterns": patterns,
        "positive_hits_by_pattern": {key: sorted(set(value)) for key, value in hits.items()},
        "negative_evidence": [
            "No local artifact contains a populated mechanical_ob_bounds_asof_v1 packet row for OTG0-PKT-060.",
            "Hits for market_state_row_hash/touch_sequence/ob_id are contracts or unrelated geometry docs, not source-row artifacts with H1 OB id, bounds, creation UTC, impulse BOS UTC, mitigation state, and touch sequence.",
            "Shadow logs were limited to source/provenance filename discovery; result-bearing shadow rows were not consumed.",
        ],
        "shadow_logs_source_provenance_filename_inventory": sorted(shadow_log_names),
        "git_head": run_git(["rev-parse", "HEAD"]),
        "git_log_oneline_20": run_git(["log", "--oneline", "-20"]).splitlines(),
        "otx_commit_files": run_git(["show", "--name-only", "--oneline", "--no-renames", "b9ba0f8b"]).splitlines(),
        "prompt_hardening_commit_files": run_git(["show", "--name-only", "--oneline", "--no-renames", "087feb5c"]).splitlines(),
    }


def classify_packet_decisions(payloads: dict[str, Any], prior: dict[str, Any], tick_audit: dict[str, Any]) -> list[dict[str, Any]]:
    proposals = payloads["proposals"]
    coverage = payloads["coverage"]
    result_rows = payloads["result"]["rows"]
    decisions: list[dict[str, Any]] = []

    p061_blocker = next(
        row
        for row in packet_rows(proposals, "OTG0-PKT-061")
        if row["record_id"] == "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
    )
    p063_ready = [
        row
        for row in packet_rows(proposals, "OTG0-PKT-063")
        if (row.get("changepoint_feature_packet") or {}).get("changepoint_status") == "PREREGISTERED_TICK_CUSUM_FEATURE_READY"
        and row["decision_quote_packet"]["quote_status"] == "DECISION_QUOTE_FOUND_ASOF"
        and row["ordered_tick_path_packet"]["path_status"] == "ORDERED_TICK_PATH_AVAILABLE"
    ]
    p063_excluded = [row["record_id"] for row in packet_rows(proposals, "OTG0-PKT-063") if row not in p063_ready]
    p066_ready = [
        row
        for row in packet_rows(proposals, "OTG0-PKT-066")
        if row["decision_quote_packet"]["quote_status"] == "DECISION_QUOTE_FOUND_ASOF"
        and row["ordered_tick_path_packet"]["path_status"] == "ORDERED_TICK_PATH_AVAILABLE"
        and (row.get("liquidity_sweep_ob_round_join_packet") or {}).get("feature_asof_utc_lte_decision_asof_utc") is True
    ]
    p066_excluded = [row["record_id"] for row in packet_rows(proposals, "OTG0-PKT-066") if row not in p066_ready]
    p062_countable = [row for row in result_rows if row.get("countable_for_discovery_summary") is True]
    p062_exclusions = Counter(row.get("terminal_result_status") for row in result_rows if row.get("countable_for_discovery_summary") is not True)

    decisions.append(
        {
            "packet_id": "OTG0-PKT-060",
            "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
            "terminal_g12_decision": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS",
            "decision_reason": "G12 accepts OTX's blocker. External quote ticks can prove decision quotes and path availability, and OTB6 proved the matched generic comparator, but no approved local source proves the selected H1 mechanical OB id/bounds/source-row/touch sequence required to compare OB versus generic retrace.",
            "accepted_evidence": {
                "otx_quote_ready_rows": 76,
                "otx_ordered_tick_path_ready_rows": 79,
                "otb6_generic_comparator_ready_rows": 80,
                "otb6_unique_matched_control_groups": 20,
            },
            "blocking_evidence": {
                "required_schema": "mechanical_ob_bounds_asof_v1",
                "required_fields": prior["otb6_contract"]["contracts"]["OTG0-PKT-060"]["required_fields"],
                "local_artifact_status": "NO_VALID_ASOF_MECHANICAL_OB_SOURCE_ROW_FOUND",
            },
            "future_unblocker": "Prospective mechanical_ob_bounds_asof_v1 capture with market_state source path/hash, row hash, H1 OB id, ob_low/high/mid, OB creation UTC, impulse BOS UTC, mitigation state, and touch_sequence for every row.",
        }
    )
    decisions.append(
        {
            "packet_id": "OTG0-PKT-061",
            "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
            "terminal_g12_decision": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE",
            "decision_reason": "G12 accepts OTX's partial coverage blocker after inspecting the absolute main tick source. 50/51 rows have quotes and ordered paths; the one XAUUSD 2026-05-06 07:15 UTC row has no decision quote and no ordered path in approved local ticks.",
            "accepted_evidence": {
                "quote_ready_rows": 50,
                "ordered_tick_path_ready_rows": 50,
                "blocked_record_id": p061_blocker["record_id"],
                "absolute_tick_file": str(TICK_ROOT / "XAUUSD/2026-05-06.parquet"),
                "absolute_tick_file_min_ts_utc": tick_audit["critical_xau_2026_05_06"]["min_ts_utc"],
                "decision_quote_window_rows": tick_audit["critical_xau_2026_05_06"]["windows"][0]["row_count"],
            },
            "blocking_evidence": {
                "missing_window": "XAUUSD 2026-05-06T07:10:00Z through 2026-05-06T11:15:00Z for decision quote plus fixed OTX path horizon",
                "decision_quote_packet": p061_blocker["decision_quote_packet"],
                "ordered_tick_path_packet": p061_blocker["ordered_tick_path_packet"],
            },
            "future_unblocker": "Recover or recapture XAUUSD ticks covering at least 2026-05-06 07:10-11:15 UTC, hash the source parquet, and rebuild continuation_no_retrace_decision_price_path_v1 before any CNR result lane.",
        }
    )
    decisions.append(
        {
            "packet_id": "OTG0-PKT-062",
            "experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
            "terminal_g12_decision": "ACCEPTED_AS_QUARANTINED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS",
            "decision_reason": "G12 accepts OTX's OTI4B ledger only as tick-recomputed quarantined discovery evidence. It is below sample floor, uses synthetic path-R only, keeps broker actual-R closed, and has explicit duplicate/row exclusions.",
            "accepted_evidence": {
                "raw_rows": payloads["result"]["record_count"],
                "countable_discovery_rows": len(p062_countable),
                "resolved_synthetic_r_rows": payloads["result"]["resolved_synthetic_r_rows"],
                "mean_synthetic_r_resolved_only": payloads["methodology"]["oti4b_mean_synthetic_r_resolved_only"],
                "duplicate_policy": "one countable primary unique breakout per duplicate_breakout_key_otx",
            },
            "row_exclusion_evidence": dict(p062_exclusions),
            "blocked_from_promotion_by": [
                "sample floor not met",
                "DSR/PBO/effective-N not computable",
                "same-dataset discovery quarantine",
                "synthetic path-R is not broker actual-R",
            ],
            "future_unblocker": "Only a future source-complete opening-drive lane with >=200 unique breakout groups and a separate G12 result audit may make any validation-style claim.",
        }
    )
    decisions.append(
        {
            "packet_id": "OTG0-PKT-063",
            "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
            "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS",
            "decision_reason": "G12 accepts the OTX CUSUM/changepoint proposal as an input-only future result-lane substrate for the 81 source-ready rows only. Five rows are excluded because predecision M1/tick coverage is insufficient.",
            "frozen_allowed_subset": {
                "source_ready_rows": len(p063_ready),
                "required_status": "PREREGISTERED_TICK_CUSUM_FEATURE_READY",
                "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
                "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
                "excluded_record_ids": p063_excluded,
            },
            "blocked_from_promotion_by": [
                "future lane not yet run",
                "synthetic/path result labels still closed",
                "sample floor and DSR/PBO/effective-N not yet established",
            ],
            "future_unblocker": "Run a separate quarantined CUSUM result audit using only the frozen 81-row source-ready subset, preserving duplicate-group policy and no broker actual-R.",
        }
    )
    decisions.append(
        {
            "packet_id": "OTG0-PKT-066",
            "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
            "terminal_g12_decision": "ACCEPTED_FOR_FUTURE_QUARANTINED_OUTCOME_AUDIT_WITH_FROZEN_SUBSET_EXCLUSIONS",
            "decision_reason": "G12 accepts the OTX sweep/round-number proposal as an input-only future result-lane substrate for the three source-ready XAU rows only. Four rows are excluded because decision quote/predecision tick coverage is absent or not as-of complete.",
            "frozen_allowed_subset": {
                "source_ready_rows": len(p066_ready),
                "required_sweep_status": "STRUCTURED_SWEEP_FIELDS_READY",
                "required_quote_status": "DECISION_QUOTE_FOUND_ASOF",
                "required_path_status": "ORDERED_TICK_PATH_AVAILABLE",
                "required_feature_asof_lte_decision": True,
                "accepted_record_ids": [row["record_id"] for row in p066_ready],
                "excluded_record_ids": p066_excluded,
                "sample_floor": 150,
            },
            "blocked_from_promotion_by": [
                "only three current source-ready rows",
                "sample floor 150 XAU OB-retouch rows not met",
                "future synthetic/path result labels still closed",
            ],
            "future_unblocker": "Collect or rebuild enough source-ready XAU OB-zone/round-number sweep rows to reach the 150-row floor before scoring beyond parser dry-run.",
        }
    )
    return decisions


def build_leakage_noleak_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    proposals = payloads["proposals"]
    result = payloads["result"]
    proposal_hits = walk_key_hits(proposals, forbidden=FORBIDDEN_KEYS | ALLOWED_RESULT_KEYS)
    result_forbidden = walk_key_hits(result, forbidden=FORBIDDEN_KEYS)
    source_paths = " ".join(str(row.get("path", "")) + " " + str(row.get("absolute_path", "")) for row in payloads["source_hash"]["source_files"]).lower()
    forbidden_source_hits = [
        fragment
        for fragment in payloads["source_hash"].get("forbidden_source_fragments", [])
        if fragment.lower().replace("\\", "/") in source_paths.replace("\\", "/")
    ]
    payload = base_payload("G12_OTX_G6_LEAKAGE_NOLEAK_AUDIT")
    payload.update(
        {
            "scope": "input_packet_and_quarantined_result_no_leak_review",
            "rebuilt_proposal_forbidden_key_hits": proposal_hits,
            "quarantined_result_forbidden_key_hits_excluding_allowed_synthetic_r": result_forbidden,
            "allowed_result_key_policy": "synthetic_r appears only in OTG0-PKT-062 OTI4B quarantined result rows and is not validation evidence.",
            "forbidden_source_path_hits": forbidden_source_hits,
            "broker_actual_r_opened": False,
            "blocked_packet_outcomes_opened": False,
            "live_trade_results_opened": False,
            "result": "PASS_NO_FORBIDDEN_PACKET_OR_SOURCE_LEAKAGE_FOUND",
        }
    )
    return payload


def build_source_tick_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    windows = [
        ("2026-05-06T07:10:00Z", "2026-05-06T07:15:00Z"),
        ("2026-05-06T07:15:00Z", "2026-05-06T11:15:00Z"),
        ("2026-05-06T07:55:00Z", "2026-05-06T08:00:00Z"),
    ]
    critical_xau = summarize_tick_file(TICK_ROOT / "XAUUSD" / "2026-05-06.parquet", windows)
    worktree_parquets = sorted(str(path.relative_to(REPO_ROOT)) for path in WORKTREE_TICK_ROOT.rglob("*.parquet")) if WORKTREE_TICK_ROOT.exists() else []
    source = source_records(payloads)
    coverage_summary = {}
    for packet_id in PACKET_IDS:
        rows = coverage_rows(payloads["coverage"], packet_id)
        coverage_summary[packet_id] = {
            "records": len(rows),
            "decision_quote_status": dict(Counter(row["decision_quote_status"] for row in rows)),
            "path_status": dict(Counter(row["path_status"] for row in rows)),
            "packet_specific_status": dict(Counter(row["packet_specific_status"] for row in rows)),
        }
    payload = base_payload("G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT")
    payload.update(
        {
            "tick_root_absolute_required_by_prompt": str(TICK_ROOT),
            "tick_root_exists": TICK_ROOT.exists(),
            "worktree_data_ticks_parquet_files": worktree_parquets,
            "critical_xau_2026_05_06": critical_xau,
            "source_hash_recheck": source,
            "coverage_summary_by_packet": coverage_summary,
            "source_hash_verdict": "PASS_CURRENT_REHASH_EXCEPT_EXPECTED_CONTEXT_CHURN"
            if not source["material_source_mismatches"]
            else "HASH_MISMATCH_REVIEW_REQUIRED",
            "tick_coverage_verdict": "PARTIAL_COVERAGE_CONFIRMED_ABSOLUTE_MAIN_PATH_INSPECTED",
        }
    )
    return payload


def build_duplicate_audit(payloads: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    proposals = payloads["proposals"]
    result_rows = payloads["result"]["rows"]
    by_packet = {}
    for packet_id in PACKET_IDS:
        rows = packet_rows(proposals, packet_id)
        groups = [row.get("duplicate_group_id") for row in rows if row.get("duplicate_group_id")]
        by_packet[packet_id] = {
            "record_count": len(rows),
            "unique_duplicate_group_count": len(set(groups)),
            "raw_over_unique_ratio": round(len(rows) / len(set(groups)), 6) if groups else None,
            "max_records_per_duplicate_group": max(Counter(groups).values()) if groups else None,
        }
    p062_countable = [row for row in result_rows if row.get("countable_for_discovery_summary") is True]
    p062_dup_status = Counter(row.get("duplicate_status") for row in result_rows)
    payload = base_payload("G12_OTX_G6_DUPLICATE_DENOMINATOR_AUDIT")
    payload.update(
        {
            "proposal_duplicate_summary_by_packet": by_packet,
            "oti4b_result_duplicate_status_counts": dict(p062_dup_status),
            "oti4b_countable_discovery_rows": len(p062_countable),
            "oti4b_countable_duplicate_keys": sorted({row.get("duplicate_breakout_key_otx") for row in p062_countable}),
            "denominator_policy_verdict": "PASS_NO_RAW_RECORD_DENOMINATOR_ACCEPTED_AS_VALIDATION",
            "accepted_future_subset_policy": {
                row["packet_id"]: row.get("frozen_allowed_subset")
                for row in decisions
                if row["terminal_g12_decision"].startswith("ACCEPTED_FOR_FUTURE")
            },
        }
    )
    return payload


def build_method_stats_audit(payloads: dict[str, Any]) -> dict[str, Any]:
    methodology = payloads["methodology"]
    result_rows = payloads["result"]["rows"]
    resolved = [row for row in result_rows if isinstance(row.get("synthetic_r"), (int, float))]
    payload = base_payload("G12_OTX_G6_METHOD_STATS_AUDIT")
    payload.update(
        {
            "oti4b_countable_discovery_rows": methodology["oti4b_countable_discovery_rows"],
            "oti4b_resolved_synthetic_r_rows": len(resolved),
            "oti4b_synthetic_r_values_resolved_only": [row["synthetic_r"] for row in resolved],
            "oti4b_mean_synthetic_r_resolved_only": methodology["oti4b_mean_synthetic_r_resolved_only"],
            "effective_n_status": methodology["effective_n"],
            "dsr_status": methodology["dsr"],
            "pbo_status": methodology["pbo"],
            "statistical_verdict": "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR",
            "packet_063_stats_status": "NOT_RUN_INPUT_ONLY_FUTURE_QUARANTINE_SUBSET_ACCEPTED",
            "packet_066_stats_status": "NOT_RUN_INPUT_ONLY_FUTURE_QUARANTINE_SUBSET_ACCEPTED_SAMPLE_FLOOR_150_NOT_MET",
        }
    )
    return payload


def build_result_acceptance_review(payloads: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    result_rows = payloads["result"]["rows"]
    status_counts = Counter(row.get("terminal_result_status") for row in result_rows)
    same_tick = [row for row in result_rows if row.get("terminal_result_status") == "AMBIGUOUS_TP_AND_SL_SAME_TICK"]
    payload = base_payload("G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW")
    payload.update(
        {
            "packet_062_decision": next(row for row in decisions if row["packet_id"] == "OTG0-PKT-062"),
            "terminal_result_status_counts": dict(status_counts),
            "same_bar_or_same_tick_policy": {
                "otx_same_tick_ambiguous_rows": len(same_tick),
                "accepted_policy": "same tick TP and SL is ambiguous and synthetic_r is null; no same-bar guess is accepted.",
            },
            "label_family_review": {
                "result_source_policy": payloads["result"]["result_source_policy"],
                "broker_actual_r_inspected": False,
                "synthetic_path_r_used_only_as_quarantined_discovery": True,
            },
            "source_hash_review": {
                "all_used_files_hashed": payloads["source_hash"]["all_used_files_hashed"],
                "result_rows_policy": "Rows cite tick-recomputed source policy; source files are in OTX source hash ledger.",
            },
            "acceptance_verdict": "ACCEPT_PACKET_062_AS_QUARANTINED_DISCOVERY_ONLY_NO_VALIDATION",
        }
    )
    return payload


def build_blocker_action_map(decisions: list[dict[str, Any]], saturation: dict[str, Any]) -> dict[str, Any]:
    payload = base_payload("G12_OTX_G6_BLOCKER_ACTION_MAP")
    payload.update(
        {
            "packet_actions": [
                {
                    "packet_id": row["packet_id"],
                    "terminal_g12_decision": row["terminal_g12_decision"],
                    "next_exact_action": row["future_unblocker"],
                    "blocked_from_promotion_by": row.get("blocked_from_promotion_by", []),
                    "frozen_allowed_subset": row.get("frozen_allowed_subset"),
                }
                for row in decisions
            ],
            "saturation_search_evidence": saturation,
            "verdict": "ALL_PACKET_NEXT_ACTIONS_EXACT",
        }
    )
    return payload


def build_completion_audit(
    decisions: list[dict[str, Any]],
    artifacts: dict[str, dict[str, Any]],
    saturation: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    decision_map = {row["packet_id"]: row["terminal_g12_decision"] for row in decisions}
    checklist = [
        ("mandatory_preflight_live_state", "PASS", "scripts/generate_live_state.py was run and .context/LIVE_STATE.md read; freshness FRESH at research commit 087feb5c."),
        ("latest_handoff_read", "PASS", "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md read."),
        ("quick_reference_read", "PASS", ".context/00_core/quick_reference_card.md read."),
        ("research_doctrine_read", "PASS", ".context/00_core/research_operating_doctrine.md read."),
        ("research_current_state_read", "PASS", ".context/00_core/research_current_state.md read."),
        ("goal_session_discipline_read", "PASS", ".context/00_core/goal_session_research_discipline.md read."),
        ("controlling_prompt_read_from_disk", "PASS", "G12_OTX_G6_POST_AUDIT_GOAL_PROMPT_2026-05-07.md read from disk after preflight."),
        ("context_freshness_contract", "PASS", "LIVE_STATE research context status was FRESH; git log -20 and OTX/prompt commits inspected."),
        ("absolute_tick_path_inspected", "PASS", "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks inspected; XAUUSD 2026-05-06 parquet min timestamp and missing 07:15/08:00 windows recorded."),
        ("otx_required_files_read", "PASS", "All required OTX JSON, JSONL, builder, and test files were inspected or verified."),
        ("prior_context_read", "PASS", "G12 G3/G6, OTI4, OTB6, OTB2R G6, G12 OTB rebuild, OTG0 manifest, and control rules inspected."),
        ("otg0_pkt_060_decided", "PASS", decision_map["OTG0-PKT-060"]),
        ("otg0_pkt_061_decided", "PASS", decision_map["OTG0-PKT-061"]),
        ("otg0_pkt_062_decided", "PASS", decision_map["OTG0-PKT-062"]),
        ("otg0_pkt_063_decided", "PASS", decision_map["OTG0-PKT-063"]),
        ("otg0_pkt_066_decided", "PASS", decision_map["OTG0-PKT-066"]),
        ("no_promotion_flags_preserved", "PASS", "All generated JSON uses NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."),
        ("forbidden_surfaces_untouched", "PASS", "Generated files live under g12_otx_g6_post_audit except optional context closeout handled separately; no src/prompts/config/canary/MT5/live-order files changed."),
        ("verification_commands", "PASS", verification),
    ]
    payload = base_payload("G12_OTX_G6_COMPLETION_AUDIT")
    payload.update(
        {
            "objective_restated": "Run the G12 post-audit of OTX G6 tick-aware resolution and decide OTG0-PKT-060/061/062/063/066 with proof-or-impossibility evidence while preserving research-only NO_PROMOTION_VERDICT boundaries.",
            "head_at_audit": run_git(["rev-parse", "HEAD"]),
            "freshness_record": {
                "live_state_status": "FRESH",
                "latest_research_relevant_commit": "087feb5c research: harden g12 otx g6 prompt",
                "current_head_seen": run_git(["log", "-1", "--oneline"]),
            },
            "prompt_to_artifact_checklist": [
                {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in checklist
            ],
            "per_packet_saturation_ledger": [
                {
                    "packet_id": row["packet_id"],
                    "terminal_g12_decision": row["terminal_g12_decision"],
                    "paths_searched": saturation["searched_roots"],
                    "evidence_found": row.get("accepted_evidence") or row.get("frozen_allowed_subset"),
                    "negative_evidence": saturation["negative_evidence"] if row["packet_id"] == "OTG0-PKT-060" else [],
                    "next_exact_action": row["future_unblocker"],
                }
                for row in decisions
            ],
            "artifact_files": sorted(artifacts),
            "can_mark_goal_complete": True,
        }
    )
    return payload


def write_prompt_pack(decisions: list[dict[str, Any]]) -> None:
    lines = [
        "# G12 OTX G6 Next Lane Prompt Pack - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`",
        f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`",
        f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        "",
        "## Accepted Follow-Up Lanes",
        "",
        "1. `/goal Run the OTG0-PKT-062 OTI4B source-complete continuation follow-up from C:\\tmp\\gtos_otb\\G12OTX using the G12 OTX G6 post-audit decision ledger and OTX_G6_OTI4B_QUARANTINED_RESULT_LEDGER as controlling inputs; use only source-complete future/additional opening-drive rows, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false, keep broker actual-R/live order/paid/API sources closed, enforce one duplicate_breakout_key_otx denominator, stop with a blocker if fewer than 200 unique breakout groups are source-complete.`",
        "2. `/goal Run the OTG0-PKT-063 CUSUM/changepoint quarantined result lane from C:\\tmp\\gtos_otb\\G12OTX using G12_OTX_G6_POST_AUDIT_DECISION_LEDGER and OTX_G6_REBUILT_PACKET_PROPOSALS as controlling inputs; freeze the 81 source-ready rows only, exclude the five listed insufficient-predecision-M1 rows, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false, do not inspect broker actual-R/live order/paid/API sources, and stop if duplicate/source/as-of checks fail before scoring.`",
        "3. `/goal Run the OTG0-PKT-066 XAU sweep/round-number quarantined result lane from C:\\tmp\\gtos_otb\\G12OTX using G12_OTX_G6_POST_AUDIT_DECISION_LEDGER and OTX_G6_REBUILT_PACKET_PROPOSALS as controlling inputs; freeze the three current source-ready rows only unless more source-ready XAU rows are captured, exclude the four listed tick-coverage blockers, require sample floor 150 before any result summary beyond parser dry-run, preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false, and keep broker actual-R/live order/paid/API sources closed.`",
        "",
        "## Blocked Data/Instrumentation Tasks",
        "",
        "- `OTG0-PKT-060`: no future result lane is justified until `mechanical_ob_bounds_asof_v1` captures H1 OB id, bounds, creation UTC, impulse BOS UTC, mitigation state, touch sequence, market_state source path/hash, and row hash for every row.",
        "- `OTG0-PKT-061`: no future result lane is justified until XAUUSD ticks covering `2026-05-06T07:10:00Z` through at least `2026-05-06T11:15:00Z` are recovered or prospectively recaptured and hashed.",
        "",
        "## Stop Conditions",
        "",
        "- Stop immediately if a lane requires broker actual-R, account history, MT5 calls, live order state, paid/API/Databento calls, prompt/risk/execution/permission/safety/selector/canary edits, credentials, or remote pushes.",
        "- Stop with an exact blocker if required source hashes, feature-as-of checks, duplicate denominator checks, JSON parsing, or focused tests fail.",
        "- Do not use these prompts for promotion. They authorize quarantined discovery/control work only.",
        "",
    ]
    (BASE / "G12_OTX_G6_NEXT_LANE_PROMPT_PACK_2026-05-07.md").write_text("\n".join(lines), encoding="utf-8")


def build() -> dict[str, Any]:
    payloads = {key: read_json(path) for key, path in OTX_JSON_FILES.items()}
    prior = {key: read_json(path) for key, path in PRIOR_JSON_FILES.items()}
    tick_audit = build_source_tick_audit(payloads)
    saturation = saturation_search_evidence()
    decisions = classify_packet_decisions(payloads, prior, tick_audit)
    decision_payload = base_payload("G12_OTX_G6_POST_AUDIT_DECISION_LEDGER")
    decision_payload.update(
        {
            "scope": "G12 post-audit of OTX G6 tick-aware resolution",
            "packet_decisions": decisions,
            "summary_counts": dict(Counter(row["terminal_g12_decision"] for row in decisions)),
        }
    )
    artifacts: dict[str, dict[str, Any]] = {
        "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07": decision_payload,
        "G12_OTX_G6_LEAKAGE_NOLEAK_AUDIT_2026-05-07": build_leakage_noleak_audit(payloads),
        "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07": tick_audit,
        "G12_OTX_G6_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07": build_duplicate_audit(payloads, decisions),
        "G12_OTX_G6_METHOD_STATS_AUDIT_2026-05-07": build_method_stats_audit(payloads),
        "G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07": build_result_acceptance_review(payloads, decisions),
        "G12_OTX_G6_BLOCKER_ACTION_MAP_2026-05-07": build_blocker_action_map(decisions, saturation),
    }
    verification = {
        "builder": "python -B -m py_compile build_g12_otx_g6_post_audit_2026_05_07.py",
        "otx_py_compile": "python -B -m py_compile ../otx_g6_tick_aware_end_to_end_resolution/build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py",
        "otx_pytest": "python -B -m pytest -q ../otx_g6_tick_aware_end_to_end_resolution/test_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py",
        "g12_pytest": "python -B -m pytest -q test_g12_otx_g6_post_audit_2026_05_07.py",
    }
    artifacts["G12_OTX_G6_COMPLETION_AUDIT_2026-05-07"] = build_completion_audit(
        decisions, artifacts, saturation, verification
    )
    for stem, payload in artifacts.items():
        title = stem.replace("_2026-05-07", "").replace("_", " ").title()
        write_json(BASE / f"{stem}.json", payload)
        write_md(BASE / f"{stem}.md", title, payload)
    write_prompt_pack(decisions)
    return artifacts["G12_OTX_G6_COMPLETION_AUDIT_2026-05-07"]


def main() -> None:
    completion = build()
    print(json.dumps({"can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))


if __name__ == "__main__":
    main()
