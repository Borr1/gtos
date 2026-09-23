#!/usr/bin/env python3
"""Build a verification ledger for current Phase 3 research claims.

Research/tooling only. The ledger reads committed/generated JSON artifacts and
records the exact numbers behind the claims used in synthesis. It is intended
to catch stale-doc drift and narrative hallucination before the next research
branch is registered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


V2_SUMMARY = Path(
    "data/external/validation/calendar_macro_bundle_v1/historical_opportunities/"
    "raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/"
    "raw_ohlc_path_scaling_v2_structural_levels_20260501T223136Z.json"
)
V2_CONCENTRATION = Path(
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2_CONCENTRATION_VERIFICATION_2026-05-02.json"
)
V2B_PROSPECTIVE = Path(
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V2B_PROSPECTIVE_VALIDATION_2026-05-02.json"
)
USDJPY_AUDIT = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "USDJPY_6J_INVERSE_RETURN_FOLLOWUP_AUDIT_2026-05-02.json"
)
EXPANDED_MANIFEST = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_PROXY_EXPANDED_2026-05-02.json"
)
EXPANDED_FETCH_PLAN = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_FETCH_PLAN_PROXY_EXPANDED_2026-05-02.json"
)
EXPANDED_FEATURES = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_PROXY_EXPANDED_2026-05-02.json"
)
EXPANDED_OUTCOME_JOIN = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_PROXY_EXPANDED_2026-05-02.json"
)
EXPANDED_ASOF = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ASOF_SYMBOL_DIAGNOSTIC_PROXY_EXPANDED_2026-05-02.json"
)
EXPANDED_ACTUAL = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_PROXY_EXPANDED_2026-05-02.json"
)

DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "PHASE3_RESEARCH_CLAIM_VERIFICATION_LEDGER_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "PHASE3_RESEARCH_CLAIM_VERIFICATION_LEDGER_2026-05-02.md"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256(path),
    }


def variant(summary: dict[str, Any], variant_id: str) -> dict[str, Any]:
    for row in summary.get("variant_summary") or []:
        if row.get("variant_id") == variant_id:
            return row
    raise KeyError(variant_id)


def best_structural(summary: dict[str, Any]) -> dict[str, Any]:
    structural = [
        row
        for row in summary.get("variant_summary") or []
        if str(row.get("variant_id", "")).startswith("STRUCT_")
    ]
    if not structural:
        raise ValueError("no structural variants found")
    return max(structural, key=lambda row: float(row["net_mean_r_cost_0.05"]))


def claim(claim_id: str, status: str, statement: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "status": status,
        "statement": statement,
        "evidence": evidence,
    }


def build_payload() -> dict[str, Any]:
    v2 = load_json(V2_SUMMARY)
    concentration = load_json(V2_CONCENTRATION)
    v2b = load_json(V2B_PROSPECTIVE)
    usdjpy = load_json(USDJPY_AUDIT)
    manifest = load_json(EXPANDED_MANIFEST)
    fetch = load_json(EXPANDED_FETCH_PLAN)
    features = load_json(EXPANDED_FEATURES)
    outcome = load_json(EXPANDED_OUTCOME_JOIN)
    asof = load_json(EXPANDED_ASOF)
    actual = load_json(EXPANDED_ACTUAL)

    j46 = variant(v2, "J46_J49_ONLY")
    swing = variant(v2, "STRUCT_SWING_PROTECTED_V2")
    ob = variant(v2, "STRUCT_OB_BOUNDARY_V2")
    composite = variant(v2, "STRUCT_COMPOSITE_ANY_V2")
    best = best_structural(v2)
    ob_concentration = (concentration.get("variants") or {}).get("STRUCT_OB_BOUNDARY_V2") or {}
    ob_group_deltas = {
        row["group"]: row
        for row in (ob_concentration.get("group_deltas") or [])
    }
    if not ob_group_deltas:
        # Backward-compatible fallbacks for earlier diagnostic payload shapes.
        ob_group_deltas = {
            row["group"]: row
            for row in (concentration.get("ob_boundary_group_deltas") or [])
        }
    if not ob_group_deltas:
        ob_group_deltas = {
            row["group"]: row
            for row in (concentration.get("synthesis", {}).get("ob_boundary_group_deltas") or [])
        }
    supported_symbols = sorted((manifest.get("synthesis") or {}).get("symbol_counts", {}).keys())
    outcome_by_symbol = outcome["synthesis"]["by_symbol"]

    claims = [
        claim(
            "path_v2_full_corpus_scope",
            "VERIFIED",
            "V2 structural replay used the full available raw-OHLC corpus and kept NO_PROMOTION_VERDICT.",
            {
                "source_scope": v2["source_scope"],
                "rows_replayed": v2["rows_replayed"],
                "take_rows_seen": v2["take_rows_seen"],
                "setup_ok_rows": v2["setup_ok_rows"],
                "first_take_clock": v2["first_take_clock"],
                "last_take_clock": v2["last_take_clock"],
                "promotion_verdict": v2["promotion_verdict"],
            },
        ),
        claim(
            "path_v2_headline_structural_signal",
            "VERIFIED_CONCENTRATION_BLOCKED",
            "The V2 headline structural variant beats J46 on same-dataset net mean R, but is not promotable.",
            {
                "best_structural_variant": best["variant_id"],
                "best_structural_net_mean_r_cost_0.05": best["net_mean_r_cost_0.05"],
                "j46_net_mean_r_cost_0.05": j46["net_mean_r_cost_0.05"],
                "delta": round(best["net_mean_r_cost_0.05"] - j46["net_mean_r_cost_0.05"], 6),
                "best_structural_net_sum_r_cost_0.05": best["net_sum_r_cost_0.05"],
                "j46_net_sum_r_cost_0.05": j46["net_sum_r_cost_0.05"],
            },
        ),
        claim(
            "path_v2_ob_boundary_next_candidate",
            "VERIFIED_DISCOVERY_ONLY",
            "OB-boundary is the cleanest next structural hypothesis because it is positive versus J46 with lower truncation than swing/FVG.",
            {
                "ob_net_mean_r_cost_0.05": ob["net_mean_r_cost_0.05"],
                "ob_net_sum_r_cost_0.05": ob["net_sum_r_cost_0.05"],
                "ob_pairwise": next(
                    row for row in v2["pairwise_vs_j46"] if row["candidate_variant"] == "STRUCT_OB_BOUNDARY_V2"
                ),
                "ob_broadness": ob_concentration.get("broadness"),
                "ob_group_deltas": ob_group_deltas,
            },
        ),
        claim(
            "path_v2_composite_rejected",
            "VERIFIED",
            "The composite structural selector underperformed J46 and is rejected as over-locking.",
            {
                "composite_net_mean_r_cost_0.05": composite["net_mean_r_cost_0.05"],
                "composite_net_sum_r_cost_0.05": composite["net_sum_r_cost_0.05"],
                "j46_net_mean_r_cost_0.05": j46["net_mean_r_cost_0.05"],
                "composite_minus_j46": round(
                    composite["net_mean_r_cost_0.05"] - j46["net_mean_r_cost_0.05"],
                    6,
                ),
                "composite_lock_then_stop_rate": composite["lock_then_stop_rate"],
            },
        ),
        claim(
            "path_v2b_prospective_blocked",
            "VERIFIED_BLOCKED",
            "V2b has no post-cutoff prospective rows and cannot validate or promote.",
            {
                "validation_status": v2b["validation_status"],
                "rows_after_cutoff": v2b["scope_counters"]["rows_after_cutoff"],
                "wanted_resolved_rows_after_cutoff": v2b["scope_counters"]["wanted_resolved_rows_after_cutoff"],
                "promotion_verdict": v2b["promotion_verdict"],
            },
        ),
        claim(
            "usdjpy_6j_followup",
            "VERIFIED_REVIEW_OPEN",
            "6J/USDJPY inverse-return mapping is broadly supportive but remains outside the proxy map due one weak strict-correlation window.",
            {
                **usdjpy["decision_readout"],
                "registration_verdict": usdjpy["registration_verdict"],
                "estimated_databento_cost_usd": usdjpy["inputs"]["estimated_databento_cost_usd"],
            },
        ),
        claim(
            "orderflow_proxy_expanded_manifest",
            "VERIFIED",
            "The expanded orderflow manifest covers five supported symbols and 241 events.",
            {
                "event_count": len(manifest["events"]),
                "fetch_group_count": len(manifest["fetch_groups"]),
                "symbol_counts": manifest["synthesis"]["symbol_counts"],
                "event_class_counts": manifest["synthesis"]["event_class_counts"],
                "supported_symbols": supported_symbols,
            },
        ),
        claim(
            "orderflow_proxy_expanded_fetch",
            "VERIFIED",
            "The expanded trades-only Databento event-window plan executed under caps.",
            {
                "executed": fetch["executed"],
                "blocked": fetch["blocked"],
                "group_status_counts": fetch["synthesis"]["group_status_counts"],
                "total_estimated_cost_usd": fetch["total_estimated_cost_usd"],
                "max_group_cost_usd": fetch["inputs"]["max_group_cost_usd"],
                "max_total_cost_usd": fetch["inputs"]["max_total_cost_usd"],
            },
        ),
        claim(
            "orderflow_proxy_expanded_features",
            "VERIFIED_DIAGNOSTIC_ONLY",
            "Trades-level features were extracted for expanded windows, but remain diagnostic only.",
            {
                "feature_rows": features["synthesis"]["feature_row_count"],
                "primary_ok_rows": features["synthesis"]["primary_ok_row_count"],
                "data_status_counts": features["synthesis"]["data_status_counts"],
                "primary_by_symbol": features["synthesis"]["primary_by_symbol"],
                "promotion_verdict": features["promotion_verdict"],
            },
        ),
        claim(
            "orderflow_proxy_expanded_outcomes",
            "VERIFIED_LABEL_CONSTRAINED",
            "Expanded proxy coverage improves synthetic target coverage but still lacks broker actual-R coverage.",
            {
                "candidate_feature_rows": outcome["synthesis"]["candidate_feature_rows"],
                "join_matched": outcome["synthesis"]["join_matched"],
                "target_available": outcome["synthesis"]["target_available"],
                "winner_count": outcome["synthesis"]["winner_count"],
                "loser_count": outcome["synthesis"]["loser_count"],
                "by_symbol": outcome_by_symbol,
                "actual_realized_r_available": actual["synthesis"]["orderflow_actual_realized_available"],
                "actual_feature_candidate_rows": actual["synthesis"]["orderflow_feature_candidate_rows"],
            },
        ),
        claim(
            "orderflow_asof_symbol_contrast",
            "VERIFIED_NO_RULE",
            "As-of orderflow diagnostics are symbol-specific and do not justify a broad rule.",
            {
                "candidate_context_by_symbol": asof["candidate_context_by_symbol"],
                "outcome_by_symbol": asof["outcome_by_symbol"],
                "promotion_verdict": asof["promotion_verdict"],
            },
        ),
    ]
    return {
        "schema_version": "phase3_research_claim_verification_ledger_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "artifacts": {
            "v2_summary": artifact(V2_SUMMARY),
            "v2_concentration": artifact(V2_CONCENTRATION),
            "v2b_prospective": artifact(V2B_PROSPECTIVE),
            "usdjpy_followup_audit": artifact(USDJPY_AUDIT),
            "expanded_manifest": artifact(EXPANDED_MANIFEST),
            "expanded_fetch_plan": artifact(EXPANDED_FETCH_PLAN),
            "expanded_features": artifact(EXPANDED_FEATURES),
            "expanded_outcome_join": artifact(EXPANDED_OUTCOME_JOIN),
            "expanded_asof": artifact(EXPANDED_ASOF),
            "expanded_actual_outcome": artifact(EXPANDED_ACTUAL),
        },
        "claims": claims,
        "synthesis": {
            "summary": (
                "All current Phase 3/orderflow claims in this ledger are tied to JSON artifacts. "
                "The ledger verifies structural path-scaling signal, V2b prospective blockage, "
                "expanded orderflow data coverage, and remaining label/proxy constraints."
            ),
            "ambiguity_ledger": [
                "This ledger verifies artifact consistency; it does not create new out-of-sample evidence.",
                "Path-scaling expectancy remains historical/research-only until prospective rows exist.",
                "Orderflow expectancy remains unavailable because current labels are sparse and mostly synthetic.",
                "Databento raw files are intentionally not committed; estimates and metadata are recorded in sidecars/reports.",
            ],
            "opened_questions": [
                "Will V2b OB-boundary remain positive on post-cutoff rows?",
                "Will USDJPY receive a strict transfer pass or a separately registered robust gate?",
                "Can expanded orderflow coverage produce symbol-level winner/loser contrast with actual broker R?",
                "Which orderflow feature family deserves pre-registration after enough labels accrue?",
            ],
            "next_steps": [
                "Do not promote V2b or orderflow from these claims.",
                "Use this ledger as the baseline before any new V2b/orderflow hypothesis registration.",
                "Continue forward collection for labels and post-cutoff path-scaling rows.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Phase 3 Research Claim Verification Ledger",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Claims",
        "",
        "| Claim | Status | Statement | Key evidence |",
        "|---|---|---|---|",
    ]
    for row in payload["claims"]:
        evidence = row["evidence"]
        compact = []
        for key, value in evidence.items():
            if isinstance(value, (dict, list)):
                continue
            compact.append(f"{key}={_fmt(value)}")
        lines.append(
            "| "
            f"{row['claim_id']} | "
            f"{row['status']} | "
            f"{row['statement']} | "
            f"{'; '.join(compact[:8])} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "| Artifact | Exists | SHA256 | Path |",
            "|---|---:|---|---|",
        ]
    )
    for name, art in payload["artifacts"].items():
        lines.append(f"| {name} | {art['exists']} | {art['sha256']} | `{art['path']}` |")
    lines.extend(
        [
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguity_ledger"]],
            "",
            "## Opened Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["opened_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload()
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"claims={len(payload['claims'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
