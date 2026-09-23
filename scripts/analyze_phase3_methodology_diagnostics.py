#!/usr/bin/env python3
"""Phase 3 methodology diagnostics harness.

Research/tooling only. This records DSR/PBO/effective-N computability and
misuse guards for current Phase 3 claims. It does not promote claims and does
not invent statistics when the validation design is absent.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DSR_DIAGNOSTICS = "research/ml_program/audit/dsr_diagnostics.json"
DEFAULT_CLAIM_LEDGER = (
    "research/databento_orderflow_capture_2026-05-02/"
    "PHASE3_RESEARCH_CLAIM_VERIFICATION_LEDGER_2026-05-02.md"
)
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md"
)

CLAIM_REGISTRY = [
    {
        "claim_id": "path_v2_structural_selector",
        "artifact": "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json",
        "evidence_class": "same_dataset_discovery",
        "claim_family": "path_scaling",
    },
    {
        "claim_id": "path_v2b_rolling_status",
        "artifact": "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.json",
        "evidence_class": "prospective_blocked_no_resolved_pairs",
        "claim_family": "path_scaling",
    },
    {
        "claim_id": "path_v3_risk_bank_replay",
        "artifact": "research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json",
        "evidence_class": "same_dataset_discovery_variants",
        "claim_family": "path_scaling",
    },
    {
        "claim_id": "nas100_cached_orderflow_forensics",
        "artifact": "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json",
        "evidence_class": "label_limited_orderflow_diagnostic",
        "claim_family": "orderflow",
    },
    {
        "claim_id": "proxy_mapping_weekend_forensics",
        "artifact": "research/databento_orderflow_capture_2026-05-02/ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.json",
        "evidence_class": "price_transfer_not_alpha",
        "claim_family": "proxy_mapping",
    },
]


def load_json_if_exists(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def promotion_verdict_from_artifact(path: str | Path, payload: dict[str, Any] | None) -> str | None:
    if payload is not None:
        verdict = payload.get("promotion_verdict")
        return str(verdict) if verdict is not None else None
    p = Path(path)
    if not p.exists():
        return None
    match = re.search(r"Promotion verdict:\s*`?([^`\n]+)`?", p.read_text(encoding="utf-8", errors="ignore"))
    return match.group(1).strip() if match else None


def diagnostic_policy(evidence_class: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if evidence_class in {"same_dataset_discovery", "same_dataset_discovery_variants"}:
        return {
            "dsr": {"status": "not_computable", "reason": "same_dataset_discovery_not_frozen_unseen_validation"},
            "pbo": {"status": "not_computable", "reason": "no_pre_registered_cscv_matrix_for_this_claim"},
            "effective_n": {"status": "proxy_required", "reason": "use concentration/effective-N diagnostics only as blockers, not promotion proof"},
            "promotion_p_value_allowed": False,
        }
    if evidence_class == "prospective_blocked_no_resolved_pairs":
        resolved = (((payload or {}).get("scope_counters") or {}).get("wanted_resolved_rows_after_cutoff"))
        return {
            "dsr": {"status": "not_computable", "reason": "no_resolved_prospective_pairs", "resolved_pairs": resolved},
            "pbo": {"status": "not_computable", "reason": "no_resolved_prospective_matrix"},
            "effective_n": {"status": "not_computable", "reason": "sample_floor_not_reached"},
            "promotion_p_value_allowed": False,
        }
    if evidence_class == "label_limited_orderflow_diagnostic":
        feeds = (payload or {}).get("feeds") or {}
        actual_counts = {
            feed: (((row.get("label_coverage") or {}).get("actual_r_n")) if isinstance(row, dict) else None)
            for feed, row in feeds.items()
        }
        return {
            "dsr": {"status": "not_computable", "reason": "actual_broker_r_sparse_or_one_sided", "actual_r_counts": actual_counts},
            "pbo": {"status": "not_computable", "reason": "no_strategy_matrix_and_synthetic_labels_dominate"},
            "effective_n": {"status": "not_computable", "reason": "label_limited_diagnostic"},
            "promotion_p_value_allowed": False,
        }
    if evidence_class == "price_transfer_not_alpha":
        return {
            "dsr": {"status": "not_applicable", "reason": "transfer_quality_diagnostic_not_alpha_lift"},
            "pbo": {"status": "not_applicable", "reason": "no_strategy_selection"},
            "effective_n": {"status": "not_applicable", "reason": "proxy_mapping_quality_not_return_claim"},
            "promotion_p_value_allowed": False,
        }
    return {
        "dsr": {"status": "unknown", "reason": "unclassified_evidence_class"},
        "pbo": {"status": "unknown", "reason": "unclassified_evidence_class"},
        "effective_n": {"status": "unknown", "reason": "unclassified_evidence_class"},
        "promotion_p_value_allowed": False,
    }


def analyze_claim(row: dict[str, Any]) -> dict[str, Any]:
    artifact = row["artifact"]
    payload = load_json_if_exists(artifact)
    exists = Path(artifact).exists()
    verdict = promotion_verdict_from_artifact(artifact, payload)
    policy = diagnostic_policy(row["evidence_class"], payload)
    return {
        **row,
        "artifact_exists": exists,
        "promotion_verdict_seen": verdict,
        "promotion_verdict_ok": verdict in {"NO_PROMOTION_VERDICT", "NOT_ALLOWED_POSTHOC_DIAGNOSTIC_ONLY"},
        "methodology": policy,
        "misuse_guard": "DO_NOT_REPORT_PROMOTION_P_VALUES" if not policy["promotion_p_value_allowed"] else "PROMOTION_STATS_ALLOWED",
    }


def dsr_reference_summary(path: str | Path) -> dict[str, Any]:
    payload = load_json_if_exists(path) or {}
    rows = payload.get("rows") or []
    counts: dict[str, int] = {}
    for row in rows:
        verdict = str(row.get("verdict") or "UNKNOWN")
        counts[verdict] = counts.get(verdict, 0) + 1
    return {
        "path": str(path),
        "rows": len(rows),
        "verdict_counts": dict(sorted(counts.items())),
        "decision_rule": payload.get("decision_rule"),
        "note": "Reference only; do not transplant ML-program DSR rows onto Phase 3 discovery claims.",
    }


def stale_ledger_diagnostics(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"status": "missing", "path": str(path)}
    text = p.read_text(encoding="utf-8", errors="ignore")
    stale_markers = [
        {
            "marker": "V2b has no post-cutoff prospective rows",
            "replacement": "V2b has post-cutoff rows but no resolved post-cutoff OB-boundary/J46 pairs",
        },
        {
            "marker": "validation_status=BLOCKED_NO_PROSPECTIVE_ROWS",
            "replacement": "validation_status=BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS",
        },
    ]
    hits = [item for item in stale_markers if item["marker"] in text]
    return {
        "status": "STALE_MARKERS_FOUND" if hits else "NO_STALE_MARKERS_FOUND",
        "path": str(path),
        "hits": hits,
    }


def build_payload(
    *,
    dsr_path: str | Path = DEFAULT_DSR_DIAGNOSTICS,
    claim_ledger_path: str | Path = DEFAULT_CLAIM_LEDGER,
) -> dict[str, Any]:
    claims = [analyze_claim(row) for row in CLAIM_REGISTRY]
    return {
        "schema_version": "phase3_methodology_diagnostics_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "claim_count": len(claims),
        "claims": claims,
        "summary": {
            "promotion_p_value_allowed_claims": [row["claim_id"] for row in claims if row["methodology"]["promotion_p_value_allowed"]],
            "promotion_p_value_forbidden_claims": [row["claim_id"] for row in claims if not row["methodology"]["promotion_p_value_allowed"]],
            "missing_artifacts": [row["claim_id"] for row in claims if not row["artifact_exists"]],
            "bad_or_missing_promotion_verdict": [
                row["claim_id"] for row in claims if not row["promotion_verdict_ok"]
            ],
        },
        "dsr_reference": dsr_reference_summary(dsr_path),
        "claim_ledger_hardening": {
            "stale_ledger_diagnostics": stale_ledger_diagnostics(claim_ledger_path),
            "recommended_columns": [
                "methodology_status",
                "dsr_status",
                "pbo_status",
                "effective_n_status",
                "promotion_p_value_allowed",
                "not_computable_reason",
                "latest_artifact_path",
            ],
            "misuse_guards": [
                "Discovery-only claims must say not_computable instead of showing raw p-values.",
                "Blocked prospective claims must report the blocker state before any statistic.",
                "Transfer-quality proxy claims must not be mixed with alpha/return claims.",
                "Label-limited orderflow diagnostics must separate actual broker R from synthetic/path labels.",
            ],
        },
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True).replace("|", r"\|")
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    lines = [
        "# Phase 3 Methodology Diagnostics",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        f"- Claims checked: `{payload['claim_count']}`.",
        f"- Promotion p-values allowed: `{payload['summary']['promotion_p_value_allowed_claims']}`.",
        f"- Promotion p-values forbidden: `{payload['summary']['promotion_p_value_forbidden_claims']}`.",
        f"- Missing artifacts: `{payload['summary']['missing_artifacts']}`.",
        f"- Bad/missing promotion verdicts: `{payload['summary']['bad_or_missing_promotion_verdict']}`.",
        "",
        "## Claim Diagnostics",
        "",
        *table(
            ["claim", "class", "artifact", "verdict ok", "DSR", "PBO", "effective-N", "guard"],
            [
                [
                    row["claim_id"],
                    row["evidence_class"],
                    row["artifact_exists"],
                    row["promotion_verdict_ok"],
                    row["methodology"]["dsr"]["status"],
                    row["methodology"]["pbo"]["status"],
                    row["methodology"]["effective_n"]["status"],
                    row["misuse_guard"],
                ]
                for row in payload["claims"]
            ],
        ),
        "",
        "## Ledger Hardening",
        "",
        f"- Stale ledger status: `{payload['claim_ledger_hardening']['stale_ledger_diagnostics']['status']}`.",
        f"- Stale hits: `{payload['claim_ledger_hardening']['stale_ledger_diagnostics'].get('hits')}`.",
        "",
        "Recommended columns:",
        "",
        *[f"- {item}" for item in payload["claim_ledger_hardening"]["recommended_columns"]],
        "",
        "Misuse guards:",
        "",
        *[f"- {item}" for item in payload["claim_ledger_hardening"]["misuse_guards"]],
        "",
        "## DSR Reference",
        "",
        f"- Rows: `{payload['dsr_reference']['rows']}`.",
        f"- Verdict counts: `{payload['dsr_reference']['verdict_counts']}`.",
        f"- Note: {payload['dsr_reference']['note']}",
        "",
        "## Non-Claims",
        "",
        "- This harness does not validate or promote Phase 3 claims.",
        "- `not_computable` is an explicit result, not a failure of the tool.",
        "- Existing DSR rows are reference material only unless the claim shares the same registered trial design.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsr-diagnostics", default=DEFAULT_DSR_DIAGNOSTICS)
    parser.add_argument("--claim-ledger", default=DEFAULT_CLAIM_LEDGER)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(dsr_path=args.dsr_diagnostics, claim_ledger_path=args.claim_ledger)
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"claims={payload['claim_count']} "
        f"p_values_forbidden={len(payload['summary']['promotion_p_value_forbidden_claims'])} "
        f"ledger_status={payload['claim_ledger_hardening']['stale_ledger_diagnostics']['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
