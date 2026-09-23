#!/usr/bin/env python3
"""Audit whether the NAS100 orderflow failure-filter is ready to register.

Research/tooling only. This is a methodology gate, not a strategy replay.
It reads existing orderflow diagnostics and decides whether the current
evidence is strong enough to freeze a prospective hypothesis without threshold
mining.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_features import generated_at_utc  # noqa: E402


DEFAULT_COVERAGE_AUDIT = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ACTUAL_OUTCOME_COVERAGE_AUDIT_OF_DATA_6_2026-05-02.json"
)
DEFAULT_TRADES_DIAG = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_OF_DATA_3_2026-05-02.json"
)
DEFAULT_MBP1_DIAG = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP1_FEATURE_DIAGNOSTIC_OF_DATA_8_2026-05-02.json"
)
DEFAULT_MBP10_DIAG = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP10_FEATURE_DIAGNOSTIC_OF_DATA_10_2026-05-02.json"
)
DEFAULT_LIMIT_RECON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_LIMIT_INTENT_RECONCILIATION_AUDIT_OF_DATA_11_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_HYPOTHESIS_READINESS_AUDIT_OF_DATA_12_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_HYPOTHESIS_READINESS_AUDIT_OF_DATA_12_2026-05-02.md"
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _get_nested(obj: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_symbol_coverage(coverage_payload: dict[str, Any], symbol: str = "NAS100") -> dict[str, Any]:
    rows = [row for row in coverage_payload.get("audit_rows") or [] if row.get("symbol") == symbol]
    return {
        "symbol": symbol,
        "orderflow_rows": len(rows),
        "synthetic_target_available": sum(bool(row.get("synthetic_realized_r_available")) for row in rows),
        "actual_realized_available": sum(bool(row.get("actual_realized_r_available")) for row in rows),
        "coverage_class_counts": dict(sorted(Counter(row.get("coverage_class") for row in rows).items())),
        "final_outcome_counts": dict(sorted(Counter(row.get("final_outcome") or "none" for row in rows).items())),
        "synthetic_outcome_counts": dict(sorted(Counter(row.get("synthetic_outcome") or "none" for row in rows).items())),
    }


def summarize_feature_rows(diag: dict[str, Any], symbol: str = "NAS100") -> dict[str, Any]:
    rows = [
        row
        for row in diag.get("feature_rows") or []
        if row.get("symbol") == symbol and row.get("is_primary_proxy") and row.get("data_status") == "ok"
    ]
    candidate_rows = [row for row in rows if row.get("event_class") == "candidate"]
    context_rows = [row for row in rows if row.get("event_class") != "candidate"]
    synthetic_rows = [row for row in candidate_rows if row.get("candidate__synthetic_realized_r") is not None]
    winners = [row for row in synthetic_rows if float(row["candidate__synthetic_realized_r"]) > 0]
    losers = [row for row in synthetic_rows if float(row["candidate__synthetic_realized_r"]) <= 0]
    return {
        "feature_rows": len(rows),
        "candidate_rows": len(candidate_rows),
        "context_rows": len(context_rows),
        "candidate_synthetic_rows": len(synthetic_rows),
        "synthetic_winners": len(winners),
        "synthetic_losers": len(losers),
    }


def summarize_synthetic_label_counts(
    *,
    coverage: dict[str, Any],
    feature_counts: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    outcome_counts = coverage.get("synthetic_outcome_counts") or {}
    coverage_winners = int(outcome_counts.get("TP") or 0)
    coverage_losers = int(outcome_counts.get("SL") or 0)
    fallback_name = "coverage"
    winners = coverage_winners
    losers = coverage_losers
    if winners == 0 and losers == 0:
        fallback_name = "feature_rows"
        winners = max(int(row.get("synthetic_winners") or 0) for row in feature_counts.values())
        losers = max(int(row.get("synthetic_losers") or 0) for row in feature_counts.values())
    return {
        "source": fallback_name,
        "synthetic_winners": winners,
        "synthetic_losers": losers,
        "synthetic_tp_count": coverage_winners,
        "synthetic_sl_count": coverage_losers,
        "synthetic_no_entry_count": int(outcome_counts.get("NO_ENTRY") or 0),
        "synthetic_none_count": int(outcome_counts.get("none") or 0),
    }


def extract_diagnostic_summary(diag: dict[str, Any], symbol: str = "NAS100") -> dict[str, Any]:
    synth = diag.get("synthesis") or {}
    return {
        "candidate_context": _get_nested(synth, ["candidate_context_by_symbol", symbol], {}),
        "outcome": _get_nested(synth, ["outcome_by_symbol", symbol], {}),
        "readout": [item for item in synth.get("readout") or [] if symbol in str(item)],
    }


def extract_key_deltas(diag_summary: dict[str, Any], feature_names: list[str]) -> dict[str, Any]:
    cc = (diag_summary.get("candidate_context") or {}).get("candidate_minus_context") or {}
    wl = (diag_summary.get("outcome") or {}).get("winner_minus_loser") or {}
    out: dict[str, Any] = {}
    for feature in feature_names:
        out[f"candidate_minus_context__{feature}"] = _safe_float(cc.get(feature))
        out[f"winner_minus_loser__{feature}"] = _safe_float(wl.get(feature))
    return out


def readiness_gates(
    *,
    coverage: dict[str, Any],
    label_counts: dict[str, Any],
    mbp10_rows: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "actual_r_coverage_min_20": coverage["actual_realized_available"] >= 20,
        "synthetic_winner_min_10": label_counts["synthetic_winners"] >= 10,
        "synthetic_loser_min_10": label_counts["synthetic_losers"] >= 10,
        "mbp10_candidate_min_30": mbp10_rows["candidate_rows"] >= 30,
        "context_min_30": mbp10_rows["context_rows"] >= 30,
    }
    return {
        "gates": gates,
        "passed": all(gates.values()),
        "failed": [name for name, ok in gates.items() if not ok],
    }


def proposed_unregistered_hypothesis() -> dict[str, Any]:
    return {
        "status": "CANDIDATE_NOT_REGISTERED",
        "name": "NAS100 thin-depth adverse-selection filter",
        "scope": "NAS100 GTOS CANDIDATE rows only",
        "as_of_window": "pre60 + event15 only; no post-event features",
        "feature_family": "MBP-10 total depth and thin-depth rate, with trades-level signed-flow diagnostics as covariates",
        "label_policy": "separate actual broker R, synthetic/path R, and fill/no-fill labels",
        "non_registered_reason": "Current evidence is selected, sparse, and winner-poor; freezing a threshold now would be threshold mining.",
    }


def build_readout(payload: dict[str, Any]) -> list[str]:
    cov = payload["coverage"]
    labels = payload["label_counts"]
    mbp10 = payload["feature_row_counts"]["mbp10"]
    mbp10_deltas = payload["diagnostic_deltas"]["mbp10"]
    gates = payload["readiness_gates"]
    return [
        (
            f"NAS100 coverage is actual-R {cov['actual_realized_available']}/{cov['orderflow_rows']} "
            f"and synthetic/path {cov['synthetic_target_available']}/{cov['orderflow_rows']}."
        ),
        (
            f"Synthetic outcome contrast is winner n={labels['synthetic_winners']} and "
            f"loser n={labels['synthetic_losers']} from {labels['source']}; "
            "the winner side is still too sparse for stable winner-minus-loser feature direction."
        ),
        (
            "MBP-10 remains the more relevant depth view than MBP-1, but current candidate sample is "
            f"n={mbp10['candidate_rows']} and context n={mbp10['context_rows']}."
        ),
        (
            "The strongest current MBP-10 clue is thin/depth related: "
            f"candidate-context event15 total-depth delta="
            f"{mbp10_deltas.get('candidate_minus_context__event15_median_total_depth10')}, "
            f"winner-loser total-depth delta="
            f"{mbp10_deltas.get('winner_minus_loser__event15_median_total_depth10')}."
        ),
        (
            f"Registration gate passed={gates['passed']} failed={gates['failed']}; "
            "therefore the correct action is forward data collection plus pre-registration criteria, not replay."
        ),
    ]


def build_payload(
    *,
    coverage_payload: dict[str, Any],
    trades_diag: dict[str, Any],
    mbp1_diag: dict[str, Any],
    mbp10_diag: dict[str, Any],
    limit_recon: dict[str, Any] | None = None,
    symbol: str = "NAS100",
) -> dict[str, Any]:
    coverage = summarize_symbol_coverage(coverage_payload, symbol)
    trades_rows = summarize_feature_rows(trades_diag, symbol)
    mbp1_rows = summarize_feature_rows(mbp1_diag, symbol)
    mbp10_rows = summarize_feature_rows(mbp10_diag, symbol)
    feature_counts = {
        "trades": trades_rows,
        "mbp1": mbp1_rows,
        "mbp10": mbp10_rows,
    }
    label_counts = summarize_synthetic_label_counts(coverage=coverage, feature_counts=feature_counts)
    trades_summary = extract_diagnostic_summary(trades_diag, symbol)
    mbp1_summary = extract_diagnostic_summary(mbp1_diag, symbol)
    mbp10_summary = extract_diagnostic_summary(mbp10_diag, symbol)
    gates = readiness_gates(coverage=coverage, label_counts=label_counts, mbp10_rows=mbp10_rows)
    payload: dict[str, Any] = {
        "schema_version": "orderflow_nas100_hypothesis_readiness_audit_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "registration_verdict": "DO_NOT_REGISTER_REPLAY_HYPOTHESIS_YET",
        "symbol": symbol,
        "coverage": coverage,
        "label_counts": label_counts,
        "feature_row_counts": feature_counts,
        "diagnostic_deltas": {
            "trades": extract_key_deltas(
                trades_summary,
                [
                    "event15_signed_volume",
                    "event15_buy_fraction",
                    "event15_absorption_volume_per_tick",
                    "profile_nearest_lvn_distance_ticks",
                ],
            ),
            "mbp1": extract_key_deltas(
                mbp1_summary,
                [
                    "event15_median_book_imbalance",
                    "event15_thin_top_book_rate",
                    "event15_median_top_liquidity",
                ],
            ),
            "mbp10": extract_key_deltas(
                mbp10_summary,
                [
                    "event15_median_depth10_imbalance",
                    "event15_thin_depth10_rate",
                    "event15_median_total_depth10",
                    "event15_median_near_far_ratio",
                    "event15_median_max_bid_wall",
                    "event15_median_max_ask_wall",
                ],
            ),
        },
        "readiness_gates": gates,
        "candidate_hypothesis": proposed_unregistered_hypothesis(),
        "limit_reconciliation_crosscheck": {
            "loaded": limit_recon is not None,
            "nas100_rows_in_limit_recon": sum(
                1
                for row in ((limit_recon or {}).get("reconciliation_rows") or [])
                if row.get("symbol") == symbol
            ),
        },
    }
    payload["synthesis"] = {
        "summary": (
            "NAS100 orderflow evidence is useful for failure forensics but is not ready for a registered replay "
            "hypothesis. The bottleneck is not feature imagination; it is sparse, selected, winner-poor labels."
        ),
        "readout": build_readout(payload),
        "ambiguities": [
            "Current NAS100 windows are selected from a known failure cluster, not a population-random sample.",
            "Actual broker-R coverage is too sparse to know whether the synthetic/path cluster translates to live P&L.",
            "Winner-minus-loser deltas are dominated by one synthetic winner.",
            "MBP-10 one-second snapshots do not prove causal queue withdrawal or order identity.",
            "No threshold has been frozen; any threshold chosen now would be post-hoc.",
        ],
        "open_questions": [
            "Does thin top-10 depth persist as a NAS100 failure signature in future candidate windows?",
            "Is thin depth a causal adverse-selection condition or merely a correlate of the same structural state?",
            "Do actual broker fills show the same pattern once forward actual-R coverage improves?",
            "Can a no-threshold or rank-only hypothesis be defined before the next replay to avoid threshold mining?",
            "Does MBP-10 add enough over MBP-1 to justify targeted collection beyond forensic windows?",
        ],
        "next_steps": [
            "Do not register or replay a NAS100 orderflow filter yet.",
            "Forward-collect trades + MBP-1 for all supported NAS100 candidate windows; add MBP-10 only for pre-declared forensic buckets.",
            "Before the next replay, freeze a rank-only or quantile-based criterion with explicit train/test separation.",
            "Require materially larger label coverage before promotion: actual-R rows or clean synthetic labels must be separated by label type.",
            "Keep MBO deferred until MBP-10 leaves an explicit queue-behavior question unanswered.",
        ],
    }
    return payload


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    cov = payload["coverage"]
    labels = payload["label_counts"]
    counts = payload["feature_row_counts"]
    gates = payload["readiness_gates"]
    lines = [
        "# NAS100 Orderflow Hypothesis Readiness Audit",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Registration verdict: `{payload['registration_verdict']}`",
        "",
        "## Summary",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Orderflow rows: {cov['orderflow_rows']}",
        f"- Synthetic/path labels: {cov['synthetic_target_available']}",
        f"- Actual broker-R labels: {cov['actual_realized_available']}",
        f"- Coverage classes: {cov['coverage_class_counts']}",
        f"- Final outcomes: {cov['final_outcome_counts']}",
        f"- Synthetic outcomes: {cov['synthetic_outcome_counts']}",
        f"- Label-count source: {labels['source']}",
        f"- Synthetic winners/losers for readiness gates: {labels['synthetic_winners']} / {labels['synthetic_losers']}",
        "",
        "## Feature Counts",
        "",
        "| Schema | feature rows | candidate rows | context rows | synthetic winners | synthetic losers |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in counts.items():
        lines.append(
            "| "
            f"{name} | {row['feature_rows']} | {row['candidate_rows']} | {row['context_rows']} | "
            f"{row['synthetic_winners']} | {row['synthetic_losers']} |"
        )
    lines.extend(
        [
            "",
            "## Key Deltas",
            "",
            "| Schema | Feature | candidate-context | winner-loser |",
            "|---|---|---:|---:|",
        ]
    )
    for schema_name, deltas in payload["diagnostic_deltas"].items():
        features = sorted(
            {
                key.replace("candidate_minus_context__", "").replace("winner_minus_loser__", "")
                for key in deltas
            }
        )
        for feature in features:
            lines.append(
                "| "
                f"{schema_name} | {feature} | "
                f"{_fmt(deltas.get(f'candidate_minus_context__{feature}'))} | "
                f"{_fmt(deltas.get(f'winner_minus_loser__{feature}'))} |"
            )
    lines.extend(
        [
            "",
            "## Readiness Gates",
            "",
            f"- Passed: {gates['passed']}",
            f"- Failed gates: {gates['failed']}",
            f"- Gate states: {gates['gates']}",
            "",
            "## Candidate Hypothesis",
            "",
        ]
    )
    for key, value in payload["candidate_hypothesis"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Readout",
            "",
            *[f"- {item}" for item in synth["readout"]],
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
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
    parser.add_argument("--coverage-audit", default=DEFAULT_COVERAGE_AUDIT)
    parser.add_argument("--trades-diag", default=DEFAULT_TRADES_DIAG)
    parser.add_argument("--mbp1-diag", default=DEFAULT_MBP1_DIAG)
    parser.add_argument("--mbp10-diag", default=DEFAULT_MBP10_DIAG)
    parser.add_argument("--limit-recon", default=DEFAULT_LIMIT_RECON)
    parser.add_argument("--symbol", default="NAS100")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(
        coverage_payload=load_json(args.coverage_audit),
        trades_diag=load_json(args.trades_diag),
        mbp1_diag=load_json(args.mbp1_diag),
        mbp10_diag=load_json(args.mbp10_diag),
        limit_recon=load_json(args.limit_recon) if Path(args.limit_recon).exists() else None,
        symbol=args.symbol,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"registration={payload['registration_verdict']} "
        f"failed_gates={payload['readiness_gates']['failed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
