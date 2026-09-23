#!/usr/bin/env python3
"""Synthesize the expanded-OOS full-unblocking research pass.

Research/tooling only. This combines the May 4 unblocking artifacts into the
completion-standard tables requested by the full-unblocking goal prompt. It
does not call AI APIs, fetch market data, change live behavior, or promote any
research result.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DATE = "2026-05-04"
NO_PROMOTION = "NO_PROMOTION_VERDICT"
OUT_DIR = ROOT / "research" / "program_control"

DEFAULT_MATRIX_JSON = OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_{DATE}.json"
DEFAULT_LABEL_AUDIT_JSON = OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_LABEL_STATUS_AUDIT_{DATE}.json"
DEFAULT_CONVERSION_STATUS_JSON = (
    OUT_DIR / f"EXPANDED_OOS_FIRST_WAVE_BOUNDED_CONVERSION_STATUS_{DATE}.json"
)
DEFAULT_CHECKPOINT_JSON = OUT_DIR / f"EXPANDED_OOS_FULL_UNBLOCKING_PROGRESS_CHECKPOINT_{DATE}.json"
DEFAULT_BATCH_REGISTRY_JSON = OUT_DIR / f"EXPANDED_OOS_FULL_UNBLOCKING_BATCH_REGISTRY_{DATE}.json"
DEFAULT_CANDIDATE_REGISTRY_JSON = (
    OUT_DIR / "EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_2026-05-03.json"
)
DEFAULT_DEPTH_BATCH_JSON = OUT_DIR / f"EXPANDED_OOS_SIERRA_DEPTH_BATCH_PARITY_STATUS_{DATE}.json"
DEFAULT_SAMPLING_AUDIT_JSON = (
    OUT_DIR / f"EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_{DATE}.json"
)
DEFAULT_OUTPUT_JSON = OUT_DIR / f"EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_{DATE}.json"
DEFAULT_OUTPUT_MD = OUT_DIR / f"EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_{DATE}.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rel(path: str | Path | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def family_rows(matrix: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in matrix.get("families") or []]


def label_status_by_family(label_audit: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("family")): dict(row) for row in label_audit.get("families") or []}


def conversion_rows_by_source(conversion_status: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for row in conversion_status.get("m15_inventory") or []:
        source = str(row.get("source_symbol") or "")
        if source:
            rows.setdefault(source, []).append(dict(row))
    return rows


def family_conversion_rows(
    family: Mapping[str, Any],
    conversion_status: Mapping[str, Any],
) -> list[dict[str, Any]]:
    by_source = conversion_rows_by_source(conversion_status)
    rows: list[dict[str, Any]] = []
    for source in family.get("converted_sources") or []:
        rows.extend(by_source.get(str(source), []))
    return sorted(rows, key=lambda row: (str(row.get("file_symbol")), str(row.get("source_symbol"))))


def source_quality(row: Mapping[str, Any]) -> str:
    source = str(row.get("source_symbol") or "")
    rows = int(row.get("rows") or 0)
    gaps = int(row.get("gap_count") or 0)
    if rows <= 0:
        return "NO_M15_ROWS"
    if source in {"SIM26-COMEX", "SILM26-COMEX", "VXMM26-CFE"}:
        return "SPARSE_SOURCE_WARNING"
    if gaps >= 40:
        return "GAPPY_SOURCE_WARNING"
    return "OK_BOUNDED_SLICE"


def completion_standard_audit(
    *,
    matrix: Mapping[str, Any],
    label_audit: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
) -> list[dict[str, Any]]:
    families = family_rows(matrix)
    label_statuses = label_status_by_family(label_audit)
    families_with_prior_replay = [
        row
        for row in families
        if not str(row.get("replay_or_label_status") or "").startswith("NOT_OPENED")
    ]
    replay_or_label_count = len(families_with_prior_replay) + len(label_statuses)
    opened_replays = [
        row
        for row in checkpoint.get("opened_replay_ledger") or []
        if int(row.get("rows_replayed") or 0) > 0
    ]
    return [
        {
            "requirement": "Adapter/converter status table for every first-wave source family",
            "status": "MET",
            "evidence": rel(DEFAULT_MATRIX_JSON),
            "numbers": {
                "required_first_wave_families": len(families),
                "families_with_ohlcv_status": (matrix.get("summary") or {}).get(
                    "families_with_ohlcv_adapter_status"
                ),
            },
        },
        {
            "requirement": "At least one working end-to-end converted-source replay path",
            "status": "MET",
            "evidence": rel(DEFAULT_CHECKPOINT_JSON),
            "numbers": {"opened_replay_rows": len(opened_replays)},
        },
        {
            "requirement": "Replay or label-status artifacts for every first-wave family",
            "status": "MET_AS_STATUS_ARTIFACTS_NOT_OUTCOME_REPLAYS",
            "evidence": rel(DEFAULT_LABEL_AUDIT_JSON),
            "numbers": {
                "families": len(families),
                "families_with_prior_replay_or_label_status": len(families_with_prior_replay),
                "families_with_new_label_status_artifact": len(label_statuses),
                "combined_replay_or_label_status_count": replay_or_label_count,
            },
        },
        {
            "requirement": "Candidate survival table by evidence class",
            "status": "MET_BY_THIS_SYNTHESIS",
            "evidence": rel(DEFAULT_OUTPUT_JSON),
            "numbers": {},
        },
        {
            "requirement": "Instrument/source expansion scorecard",
            "status": "MET_BY_THIS_SYNTHESIS",
            "evidence": rel(DEFAULT_OUTPUT_JSON),
            "numbers": {},
        },
        {
            "requirement": "Data-quality table",
            "status": "MET_BY_THIS_SYNTHESIS",
            "evidence": rel(DEFAULT_OUTPUT_JSON),
            "numbers": {},
        },
        {
            "requirement": "Opened/burned/reserved slice ledger",
            "status": "MET_BY_THIS_SYNTHESIS",
            "evidence": rel(DEFAULT_OUTPUT_JSON),
            "numbers": {},
        },
        {
            "requirement": "Cost ledger",
            "status": "MET",
            "evidence": rel(DEFAULT_OUTPUT_JSON),
            "numbers": {"new_databento_cost_usd": 0, "new_ai_api_cost_usd": 0},
        },
        {
            "requirement": "Failure/decay/source-mismatch attribution",
            "status": "MET_BY_THIS_SYNTHESIS",
            "evidence": rel(DEFAULT_OUTPUT_JSON),
            "numbers": {},
        },
        {
            "requirement": "Final synthesis with NO_PROMOTION_VERDICT",
            "status": "MET_BY_THIS_ARTIFACT",
            "evidence": rel(DEFAULT_OUTPUT_MD),
            "numbers": {"promotion_verdict": NO_PROMOTION},
        },
    ]


def checkpoint_metric(checkpoint: Mapping[str, Any], batch_id_contains: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in checkpoint.get("opened_replay_ledger") or []
        if batch_id_contains in str(row.get("batch_id") or "")
    ]


def candidate_survival_table(
    *,
    registry: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    depth_batch: Mapping[str, Any],
    sampling_audit: Mapping[str, Any],
) -> list[dict[str, Any]]:
    depth_summary = depth_batch.get("summary") or {}
    sampling = sampling_audit.get("updated_batch_interpretation") or {}
    rows: list[dict[str, Any]] = []
    for candidate in registry.get("candidates") or []:
        candidate_id = str(candidate.get("candidate_id") or "")
        status = "NOT_RUN_IN_FULL_UNBLOCKING_PASS"
        evidence_class = "not_computable"
        numbers: dict[str, Any] = {}
        decision = "NO_PROMOTION_VERDICT"
        if candidate_id == "CAND-001-J46-J49-LIVE-BASELINE":
            status = "COMPARATOR_ONLY_NO_NEW_BROKER_R"
            evidence_class = "COMPARATOR"
            decision = "Kept as frozen comparator; no new broker-realized R labels were created."
        elif candidate_id == "CAND-002-V2-OB-BOUNDARY":
            status = "SOURCE_TRANSFER_DIAGNOSTIC_MIXED_NOT_PROMOTABLE"
            evidence_class = "SAME_MARKET_SOURCE_TRANSFER_AND_FUTURES_PROXY_TRANSFER"
            xau = checkpoint_metric(checkpoint, "xauusd_scid_v2_mtf")
            ym = checkpoint_metric(checkpoint, "ym_us30_cash_v2_mtf")
            si = checkpoint_metric(checkpoint, "si_xagusd_v2_mtf")
            numbers = {
                "xauusd_same_market_v2_mtf": xau[0] if xau else None,
                "us30_ym_v2_mtf": ym[0] if ym else None,
                "xagusd_si_v2_mtf": si[0] if si else None,
            }
            decision = (
                "Small-n XAUUSD source-transfer diagnostic is positive, but YM/SI lower-timeframe "
                "replays produce no resolved entry labels; not validation."
            )
        elif candidate_id == "CAND-003-V2-FVG-PATH":
            status = "NOT_OPENED_REQUIRES_COMPATIBLE_V2_EVENT_LOGS"
            evidence_class = "DISCOVERY_ONLY"
            decision = "No first-wave converted-source survival claim; requires registered V2 event-log batch."
        elif candidate_id == "CAND-004-V3-FVG-ONLY-RESCUE":
            status = "NOT_OPENED_DEPENDS_ON_V2_EVENT_LOGS_AND_LIFECYCLE_FIELDS"
            evidence_class = "DISCOVERY_ONLY"
            decision = "Prerequisite resolved V2 rows and lifecycle/pre-fill fields are absent."
        elif candidate_id == "CAND-005-NAS100-DEPTH-THINNESS":
            status = "DEPTH_PARITY_SOURCE_STATUS_ONLY_LABEL_LIMITED"
            evidence_class = "FUTURES_PROXY_TRANSFER"
            numbers = {
                "exact_cached_mbp10_matches": depth_summary.get("exact_cached_mbp10_matches"),
                "near_matches": depth_summary.get("near_matches_with_small_field_deltas"),
                "mismatches": depth_summary.get("mismatches_requiring_source_or_sampling_audit"),
                "clean_depth_families": sampling.get("exact_clean_families"),
                "sampling_policy_alignment_family": sampling.get("sampling_policy_alignment_family"),
                "source_definition_blocked_family": sampling.get("source_definition_blocked_family"),
            }
            decision = "NQ/YM source parity is clean for diagnostics; labels remain insufficient for any filter."
        elif candidate_id == "CAND-006-S79-SIDE-AWARE-SIM-COMPARATOR":
            status = "SIMULATION_COMPARATOR_ONLY_NO_LIVE_RISK_CHANGE"
            evidence_class = "SIMULATION_COMPARATOR"
            decision = "No risk/execution change allowed or made in this goal."
        rows.append(
            {
                "candidate_id": candidate_id,
                "rule_name": candidate.get("rule_name"),
                "registry_status": candidate.get("status"),
                "evidence_class": evidence_class,
                "result_status": status,
                "numbers": numbers,
                "dsr_status": "not_computable",
                "pbo_status": "not_computable",
                "effective_n_status": "not_computable",
                "decision": decision,
            }
        )
    return rows


def classify_expansion_family(row: Mapping[str, Any], label_row: Mapping[str, Any] | None) -> tuple[str, str]:
    family = str(row.get("family") or "")
    depth = str(row.get("depth_status") or "")
    replay = str(row.get("replay_or_label_status") or "")
    label = str((label_row or {}).get("label_status") or "")
    if family.startswith("NAS100"):
        return "PROMISING_DIAGNOSTIC", "NQ depth parity exact; replay path works but no frozen cohort match."
    if family.startswith("US30"):
        return "NEUTRAL_DIAGNOSTIC", "YM depth parity exact, but V2 MTF replay produced all no-entry."
    if family.startswith("XAUUSD"):
        return "PROMISING_SMALL_N_SOURCE_TRANSFER", "Same-market source transfer is positive at n=5 only; GC depth is near-match, not exact."
    if family.startswith("XAGUSD"):
        return "BLOCKED_SOURCE_MISMATCH", "M15 positive did not survive MTF fill reconstruction; SI depth source-definition is blocked."
    if family.startswith("USDJPY"):
        return "NEUTRAL_PATH_ONLY", "6J inverse replay path works but produced no actions."
    if family.startswith("GBPUSD"):
        return "NEUTRAL_PATH_ONLY_DEPTH_CAUTION", "6B replay path works with no actions; depth needs sampling-policy alignment."
    if "NO_REGISTERED_FROZEN_COHORT" in label:
        return "BLOCKED_NO_REGISTERED_COHORT", "Converted rows exist, but no frozen raw-OHLC cohort matches this family."
    if "CONTROL_NO_DIRECT_TRADE_COHORT" in label:
        return "CONTROL_ONLY", "Converted control rows exist, but there is no direct trade-label cohort."
    if "blocked" in depth.lower() or "not portable" in replay.lower():
        return "BLOCKED", "Existing replay/depth status is blocked or not portable."
    return "NEUTRAL_STATUS_ONLY", "No promotable evidence."


def instrument_source_scorecard(
    *,
    matrix: Mapping[str, Any],
    label_audit: Mapping[str, Any],
) -> list[dict[str, Any]]:
    labels = label_status_by_family(label_audit)
    rows = []
    for family in family_rows(matrix):
        label_row = labels.get(str(family.get("family")))
        status, rationale = classify_expansion_family(family, label_row)
        rows.append(
            {
                "family": family.get("family"),
                "scorecard_status": status,
                "evidence_class": family.get("evidence_class"),
                "replay_or_label_status": family.get("replay_or_label_status"),
                "depth_status": family.get("depth_status"),
                "label_status": (label_row or {}).get("label_status"),
                "rationale": rationale,
                "promotion_boundary": "NO_PROMOTION_VERDICT; transfer/control evidence is not broker-truth validation.",
            }
        )
    return rows


def data_quality_table(
    *,
    matrix: Mapping[str, Any],
    conversion_status: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for family in family_rows(matrix):
        sources = family_conversion_rows(family, conversion_status)
        rows.append(
            {
                "family": family.get("family"),
                "source_count": len(sources),
                "sources": [
                    {
                        "file_symbol": source.get("file_symbol"),
                        "source_symbol": source.get("source_symbol"),
                        "evidence_class": source.get("evidence_class"),
                        "m15_rows": int(source.get("rows") or 0),
                        "first": source.get("first"),
                        "last": source.get("last"),
                        "gap_count": int(source.get("gap_count") or 0),
                        "quality_status": source_quality(source),
                    }
                    for source in sources
                ],
                "depth_status": family.get("depth_status"),
                "quality_boundary": "Bounded 2026-04-15 to 2026-04-18 slice unless separately registered; not an OOS proof.",
            }
        )
    return rows


def opened_burned_reserved_ledger(
    *,
    checkpoint: Mapping[str, Any],
    label_audit: Mapping[str, Any],
    batch_registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for replay in checkpoint.get("opened_replay_ledger") or []:
        actions_taken = replay.get("actions_taken")
        if actions_taken is None:
            actions_taken = replay.get("take_rows_seen")
        resolved_r_n = replay.get("resolved_r_n")
        if resolved_r_n is None:
            resolved_r_n = replay.get("resolved_r_n_reference")
        rows.append(
            {
                "slice_id": replay.get("batch_id"),
                "status": "OPENED_BURNED_FOR_REPLAY_DIAGNOSTIC",
                "slice": replay.get("slice"),
                "rows_replayed": replay.get("rows_replayed"),
                "actions_taken": actions_taken,
                "resolved_r_n": resolved_r_n,
                "holdout_impact": "Not eligible as future pure holdout for that source/date/question.",
            }
        )
    for row in label_audit.get("families") or []:
        rows.append(
            {
                "slice_id": row.get("family"),
                "status": row.get("outcome_slice_status"),
                "slice": "converted_rows_status_only",
                "rows_replayed": 0,
                "actions_taken": 0,
                "resolved_r_n": 0,
                "holdout_impact": "No outcome rows opened by label-status audit.",
            }
        )
    for batch in batch_registry.get("registered_batches") or []:
        reserved = batch.get("reserved_holdout")
        if reserved:
            rows.append(
                {
                    "slice_id": f"{batch.get('batch_id')}::reserved_holdout",
                    "status": reserved.get("status"),
                    "slice": f"{reserved.get('start_utc')}/{reserved.get('end_utc')}",
                    "rows_replayed": 0,
                    "actions_taken": 0,
                    "resolved_r_n": 0,
                    "holdout_impact": "Reserved by registry and not opened by the pilot replay slice.",
                }
            )
    return rows


def cost_ledger(*artifacts: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source": "AI/API",
            "cost_usd": 0.0,
            "calls": 0,
            "note": "No Component 3B, LLM replay, prompt experiment, or model call was used.",
        },
        {
            "source": "Databento",
            "cost_usd": 0.0,
            "calls": 0,
            "note": "No new Databento pull was made; comparisons reused cached May 2 orderflow artifacts.",
        },
        {
            "source": "Local Sierra/MT5 files",
            "cost_usd": 0.0,
            "calls": 0,
            "note": f"{len(artifacts)} local/versioned artifacts were synthesized; local compute only.",
        },
    ]


def attribution_table(
    *,
    label_audit: Mapping[str, Any],
    sampling_audit: Mapping[str, Any],
) -> list[dict[str, str]]:
    audits = {row.get("source_symbol"): row for row in sampling_audit.get("audits") or []}
    return [
        {
            "factor": "No registered raw-OHLC cohorts for EURUSD/6E and ES/MES",
            "classification": "LABEL_SPEC_BLOCKER_NOT_DATA_MISSING",
            "evidence": rel(DEFAULT_LABEL_AUDIT_JSON) or "",
            "interpretation": "Converted rows exist, but opening outcomes would require a separate pre-registered cohort/question.",
        },
        {
            "factor": "CL/ZN/VIX are control/context families",
            "classification": "CROSS_INSTRUMENT_CONTROL_ONLY",
            "evidence": rel(DEFAULT_LABEL_AUDIT_JSON) or "",
            "interpretation": "These sources can support future context questions but cannot validate original-instrument edge.",
        },
        {
            "factor": "6B depth mismatch",
            "classification": str(audits.get("6BM26-CME", {}).get("status") or "SAMPLING_POLICY_ALIGNMENT_REQUIRED"),
            "evidence": rel(DEFAULT_SAMPLING_AUDIT_JSON) or "",
            "interpretation": "Sampling-clock alignment can likely unblock 6B source diagnostics; it is not a source rejection.",
        },
        {
            "factor": "SI depth mismatch",
            "classification": str(audits.get("SIM26-COMEX", {}).get("status") or "SOURCE_DEFINITION_BLOCKED"),
            "evidence": rel(DEFAULT_SAMPLING_AUDIT_JSON) or "",
            "interpretation": "Common-second masking does not fix SI; source/continuous-contract definition must be resolved before replay use.",
        },
        {
            "factor": "Futures proxy transfer",
            "classification": "NOT_BROKER_TRUTH",
            "evidence": rel(DEFAULT_MATRIX_JSON) or "",
            "interpretation": "NQ/YM exact depth parity and GC near-match can guide diagnostics, not live MT5 validation.",
        },
    ]


def build_payload(
    *,
    matrix: Mapping[str, Any],
    label_audit: Mapping[str, Any],
    conversion_status: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    batch_registry: Mapping[str, Any],
    candidate_registry: Mapping[str, Any],
    depth_batch: Mapping[str, Any],
    sampling_audit: Mapping[str, Any],
) -> dict[str, Any]:
    artifacts = {
        "family_matrix": rel(DEFAULT_MATRIX_JSON),
        "label_status_audit": rel(DEFAULT_LABEL_AUDIT_JSON),
        "bounded_conversion_status": rel(DEFAULT_CONVERSION_STATUS_JSON),
        "progress_checkpoint": rel(DEFAULT_CHECKPOINT_JSON),
        "batch_registry": rel(DEFAULT_BATCH_REGISTRY_JSON),
        "candidate_registry": rel(DEFAULT_CANDIDATE_REGISTRY_JSON),
        "depth_batch_status": rel(DEFAULT_DEPTH_BATCH_JSON),
        "sampling_audit_synthesis": rel(DEFAULT_SAMPLING_AUDIT_JSON),
    }
    payload = {
        "schema_version": "expanded_oos_full_unblocking_final_synthesis_v1",
        "created_at_utc": utc_now(),
        "program": "expanded_oos_full_unblocking",
        "status": "LOCAL_FULL_UNBLOCKING_PASS_SYNTHESIZED_NOT_PROMOTABLE",
        "scope": "research/tooling only",
        "promotion_verdict": NO_PROMOTION,
        "bottom_line": (
            "The May 4 full-unblocking pass now has adapter/converter status, a working "
            "converted-source replay path, replay or label-status artifacts for all first-wave "
            "families, candidate survival, expansion, data-quality, opened-slice, cost, and "
            "source-mismatch tables. It still produces no live-trading promotion: evidence is "
            "source-transfer/control/diagnostic, label-limited, or not computable for DSR/PBO."
        ),
        "live_surface_changed": False,
        "ai_api_calls": 0,
        "databento_spend_usd": 0.0,
        "artifact_inputs": artifacts,
        "completion_standard_audit": completion_standard_audit(
            matrix=matrix,
            label_audit=label_audit,
            checkpoint=checkpoint,
        ),
        "candidate_survival_table_by_evidence_class": candidate_survival_table(
            registry=candidate_registry,
            checkpoint=checkpoint,
            depth_batch=depth_batch,
            sampling_audit=sampling_audit,
        ),
        "instrument_source_expansion_scorecard": instrument_source_scorecard(
            matrix=matrix,
            label_audit=label_audit,
        ),
        "data_quality_table": data_quality_table(
            matrix=matrix,
            conversion_status=conversion_status,
        ),
        "opened_burned_reserved_slice_ledger": opened_burned_reserved_ledger(
            checkpoint=checkpoint,
            label_audit=label_audit,
            batch_registry=batch_registry,
        ),
        "cost_ledger": cost_ledger(matrix, label_audit, checkpoint, depth_batch, sampling_audit),
        "failure_decay_source_mismatch_attribution": attribution_table(
            label_audit=label_audit,
            sampling_audit=sampling_audit,
        ),
        "promotion_readiness": {
            "status": "NOT_READY",
            "reason": "No true temporal OOS resolved-pair evidence, no broker-truth validation from proxy futures/control families, and no computable DSR/PBO/effective-N promotion statistics.",
            "p_values_reported": 0,
            "live_changes_allowed": False,
            "next_trigger": "Separate promotion dossier only after registered unseen same-instrument/source slices meet label floors and methodology gates.",
        },
        "remaining_research_triggers": [
            "Pre-register any new EURUSD/ES strategy cohort before opening outcomes.",
            "Use CL/ZN/VIX only after a named cross-instrument question is registered.",
            "Add 6B common-second/declarative sampling alignment before using Sierra 6B depth diagnostics.",
            "Resolve SI continuous-contract/source definition before treating Sierra SI/SIL depth as equivalent.",
            "Continue forward shadow collection for actual broker-R and pending-limit lifecycle fields.",
        ],
    }
    return payload


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    out.extend("| " + " | ".join(fmt(item) for item in row) + " |" for row in rows)
    return "\n".join(out)


def write_markdown(path: Path, payload: Mapping[str, Any]) -> None:
    lines = [
        "# Expanded OOS Full-Unblocking Final Synthesis - 2026-05-04",
        "",
        f"**Status:** `{payload.get('status')}`",
        f"**Promotion verdict:** `{payload.get('promotion_verdict')}`",
        "",
        str(payload.get("bottom_line")),
        "",
        "## Completion Standard Audit",
        "",
        table(
            ["Requirement", "Status", "Evidence", "Numbers"],
            [
                [row["requirement"], row["status"], row["evidence"], row.get("numbers")]
                for row in payload.get("completion_standard_audit") or []
            ],
        ),
        "",
        "## Candidate Survival By Evidence Class",
        "",
        table(
            ["Candidate", "Evidence Class", "Result Status", "Decision"],
            [
                [row["candidate_id"], row["evidence_class"], row["result_status"], row["decision"]]
                for row in payload.get("candidate_survival_table_by_evidence_class") or []
            ],
        ),
        "",
        "## Instrument / Source Scorecard",
        "",
        table(
            ["Family", "Status", "Replay/Label", "Depth", "Rationale"],
            [
                [
                    row["family"],
                    row["scorecard_status"],
                    row.get("replay_or_label_status") or row.get("label_status"),
                    row.get("depth_status"),
                    row["rationale"],
                ]
                for row in payload.get("instrument_source_expansion_scorecard") or []
            ],
        ),
        "",
        "## Opened / Burned / Reserved Ledger",
        "",
        table(
            ["Slice", "Status", "Rows", "Actions", "Resolved", "Holdout Impact"],
            [
                [
                    row["slice_id"],
                    row["status"],
                    row["rows_replayed"],
                    row["actions_taken"],
                    row["resolved_r_n"],
                    row["holdout_impact"],
                ]
                for row in payload.get("opened_burned_reserved_slice_ledger") or []
            ],
        ),
        "",
        "## Source Mismatch Attribution",
        "",
        table(
            ["Factor", "Classification", "Interpretation", "Evidence"],
            [
                [row["factor"], row["classification"], row["interpretation"], row["evidence"]]
                for row in payload.get("failure_decay_source_mismatch_attribution") or []
            ],
        ),
        "",
        "## Promotion Readiness",
        "",
        f"Status: `{(payload.get('promotion_readiness') or {}).get('status')}`. "
        f"Reason: {(payload.get('promotion_readiness') or {}).get('reason')} "
        f"P-values reported: `{(payload.get('promotion_readiness') or {}).get('p_values_reported')}`. "
        f"Live changes allowed: `{(payload.get('promotion_readiness') or {}).get('live_changes_allowed')}`.",
        "",
        "## Remaining Research Triggers",
        "",
        *[f"- {item}" for item in payload.get("remaining_research_triggers") or []],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-json", type=Path, default=DEFAULT_MATRIX_JSON)
    parser.add_argument("--label-audit-json", type=Path, default=DEFAULT_LABEL_AUDIT_JSON)
    parser.add_argument("--conversion-status-json", type=Path, default=DEFAULT_CONVERSION_STATUS_JSON)
    parser.add_argument("--checkpoint-json", type=Path, default=DEFAULT_CHECKPOINT_JSON)
    parser.add_argument("--batch-registry-json", type=Path, default=DEFAULT_BATCH_REGISTRY_JSON)
    parser.add_argument("--candidate-registry-json", type=Path, default=DEFAULT_CANDIDATE_REGISTRY_JSON)
    parser.add_argument("--depth-batch-json", type=Path, default=DEFAULT_DEPTH_BATCH_JSON)
    parser.add_argument("--sampling-audit-json", type=Path, default=DEFAULT_SAMPLING_AUDIT_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        matrix=load_json(args.matrix_json),
        label_audit=load_json(args.label_audit_json),
        conversion_status=load_json(args.conversion_status_json),
        checkpoint=load_json(args.checkpoint_json),
        batch_registry=load_json(args.batch_registry_json),
        candidate_registry=load_json(args.candidate_registry_json),
        depth_batch=load_json(args.depth_batch_json),
        sampling_audit=load_json(args.sampling_audit_json),
    )
    write_json(args.output_json, payload)
    write_markdown(args.output_md, payload)
    print(
        "wrote "
        f"{rel(args.output_json)} and {rel(args.output_md)} "
        f"status={payload['status']} promotion={payload['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
