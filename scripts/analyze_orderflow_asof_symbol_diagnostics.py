#!/usr/bin/env python3
"""Symbol-stratified as-of orderflow diagnostics.

Research/tooling only. This consumes previously extracted trades-level features
and candidate outcome joins. It reports descriptive separations only; it does
not register or promote a trading rule.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_features import generated_at_utc, median_or_none  # noqa: E402


DEFAULT_FEATURES = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_OF_DATA_3_2026-05-02.json"
)
DEFAULT_OUTCOME_JOIN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_OF_DATA_4_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ASOF_SYMBOL_DIAGNOSTIC_OF_DATA_5_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_ASOF_SYMBOL_DIAGNOSTIC_OF_DATA_5_2026-05-02.md"
)

ASOF_FEATURES = (
    "pre60_signed_volume",
    "pre60_buy_fraction",
    "pre60_absorption_volume_per_tick",
    "event15_signed_volume",
    "event15_buy_fraction",
    "event15_absorption_volume_per_tick",
    "event15_delta_price_divergence",
    "profile_event_price_volume_percentile",
    "profile_nearest_lvn_distance_ticks",
    "profile_nearest_hvn_distance_ticks",
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _numeric_median(rows: list[dict[str, Any]], feature: str) -> float | None:
    return median_or_none([row.get(feature) for row in rows])


def _bool_rate(rows: list[dict[str, Any]], feature: str) -> float | None:
    values = [row.get(feature) for row in rows if isinstance(row.get(feature), bool)]
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def summarize_bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = {"n": len(rows)}
    for feature in ASOF_FEATURES:
        if feature.endswith("_divergence"):
            out[f"{feature}_rate"] = _bool_rate(rows, feature)
        else:
            out[f"median_{feature}"] = _numeric_median(rows, feature)
    return out


def candidate_context_by_symbol(feature_rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [
        row
        for row in feature_rows
        if row.get("is_primary_proxy") and row.get("data_status") == "ok"
    ]
    by_symbol: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in primary:
        klass = "candidate" if row.get("event_class") == "candidate" else "context"
        by_symbol[str(row.get("symbol"))][klass].append(row)

    out: dict[str, Any] = {}
    for symbol, buckets in sorted(by_symbol.items()):
        candidate = buckets.get("candidate", [])
        context = buckets.get("context", [])
        symbol_out = {
            "candidate": summarize_bucket(candidate),
            "context": summarize_bucket(context),
            "candidate_minus_context": {},
        }
        for feature in ASOF_FEATURES:
            if feature.endswith("_divergence"):
                c = symbol_out["candidate"].get(f"{feature}_rate")
                x = symbol_out["context"].get(f"{feature}_rate")
            else:
                c = symbol_out["candidate"].get(f"median_{feature}")
                x = symbol_out["context"].get(f"median_{feature}")
            symbol_out["candidate_minus_context"][feature] = (
                None if c is None or x is None else float(c) - float(x)
            )
        out[symbol] = symbol_out
    return out


def outcome_by_symbol(joined_rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_rows = [
        row
        for row in joined_rows
        if row.get("candidate__synthetic_realized_r") is not None
    ]
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in target_rows:
        symbol = str(row.get("symbol"))
        outcome = "winner" if float(row["candidate__synthetic_realized_r"]) > 0 else "loser"
        buckets[symbol][outcome].append(row)

    out: dict[str, Any] = {}
    for symbol, symbol_buckets in sorted(buckets.items()):
        winners = symbol_buckets.get("winner", [])
        losers = symbol_buckets.get("loser", [])
        out[symbol] = {
            "winner": summarize_bucket(winners),
            "loser": summarize_bucket(losers),
            "winner_minus_loser": {},
        }
        for feature in ASOF_FEATURES:
            if feature.endswith("_divergence"):
                w = out[symbol]["winner"].get(f"{feature}_rate")
                l = out[symbol]["loser"].get(f"{feature}_rate")
            else:
                w = out[symbol]["winner"].get(f"median_{feature}")
                l = out[symbol]["loser"].get(f"median_{feature}")
            out[symbol]["winner_minus_loser"][feature] = (
                None if w is None or l is None else float(w) - float(l)
            )
    return out


def build_readout(candidate_context: dict[str, Any], outcome: dict[str, Any]) -> list[str]:
    bullets = []
    nas = outcome.get("NAS100")
    if nas:
        bullets.append(
            "NAS100 remains the only outcome-joined symbol with enough rows for a useful failure-cluster readout, "
            f"but winner n={nas['winner']['n']} and loser n={nas['loser']['n']} are still too small for inference."
        )
    xau = outcome.get("XAUUSD")
    if xau:
        bullets.append(
            f"XAUUSD has winner n={xau['winner']['n']} and loser n={xau['loser']['n']}; it cannot validate an orderflow rule yet."
        )
    for symbol, row in sorted(outcome.items()):
        if symbol in {"NAS100", "XAUUSD"}:
            continue
        if row["winner"]["n"] and not row["loser"]["n"]:
            bullets.append(
                f"{symbol} has winner n={row['winner']['n']} and loser n=0; it adds coverage but not winner/loser contrast."
            )
        elif row["loser"]["n"] and not row["winner"]["n"]:
            bullets.append(
                f"{symbol} has winner n=0 and loser n={row['loser']['n']}; it can support failure forensics only."
            )
    for symbol, row in candidate_context.items():
        cand_n = row["candidate"]["n"]
        context_n = row["context"]["n"]
        if cand_n and context_n:
            delta_profile = row["candidate_minus_context"].get("profile_event_price_volume_percentile")
            delta_lvn = row["candidate_minus_context"].get("profile_nearest_lvn_distance_ticks")
            bullets.append(
                f"{symbol}: candidate-vs-context n={cand_n}/{context_n}, "
                f"profile-percentile delta={_fmt(delta_profile)}, LVN-distance delta={_fmt(delta_lvn)}."
            )
    bullets.append("No broad rule is justified; next hypothesis must be symbol-stratified and pre-registered.")
    return bullets


def build_payload(feature_payload: dict[str, Any], outcome_payload: dict[str, Any]) -> dict[str, Any]:
    candidate_context = candidate_context_by_symbol(feature_payload["feature_rows"])
    outcome = outcome_by_symbol(outcome_payload["joined_rows"])
    return {
        "schema_version": "orderflow_asof_symbol_diagnostic_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "feature_schema_version": feature_payload.get("schema_version"),
            "outcome_join_schema_version": outcome_payload.get("schema_version"),
            "asof_features": list(ASOF_FEATURES),
            "post_event_features_excluded": True,
        },
        "candidate_context_by_symbol": candidate_context,
        "outcome_by_symbol": outcome,
        "synthesis": {
            "summary": (
                "This report isolates as-of orderflow features by symbol. It separates "
                "candidate-vs-context diagnostics from outcome-joined winner-vs-loser diagnostics."
            ),
            "readout": build_readout(candidate_context, outcome),
            "ambiguities": [
                "Candidate outcomes are mostly synthetic; actual realized-R remains sparse.",
                "Feature thresholds are not optimized or promoted here.",
                "Outcome interpretation requires both winner and loser contrast inside a symbol; all-winner or all-loser symbols are not rule evidence.",
                "XAUUSD outcome coverage is too small to interpret as a continuation-quality rule.",
                "Context rows are structural/no-trade contexts, not randomized market rows.",
            ],
            "open_questions": [
                "Does NAS100 failure separation persist after more candidate outcomes accrue?",
                "Are profile percentile and LVN distance meaningful or just session/instrument artifacts?",
                "Can actual realized-R enrichment replace synthetic labels for this diagnostic?",
                "Which as-of feature family should be registered first: delta failure, LVN/POC location, or absorption?",
            ],
            "next_steps": [
                "Register one NAS100 failure-filter hypothesis with frozen thresholds only after expanding n.",
                "Backfill/forward-collect more XAUUSD and US30 candidate outcomes before symbol claims.",
                "Run a depth-schema pilot only on the NAS100/XAUUSD candidate windows selected by this report.",
            ],
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow As-Of Symbol Diagnostic",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Readout",
        "",
        *[f"- {item}" for item in synth["readout"]],
        "",
        "## Candidate vs Context By Symbol",
        "",
        "| Symbol | candidate n | context n | profile percentile delta | nearest LVN ticks delta | event15 signed vol delta | event15 divergence-rate delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol, row in payload["candidate_context_by_symbol"].items():
        delta = row["candidate_minus_context"]
        lines.append(
            "| "
            f"{symbol} | {row['candidate']['n']} | {row['context']['n']} | "
            f"{_fmt(delta.get('profile_event_price_volume_percentile'))} | "
            f"{_fmt(delta.get('profile_nearest_lvn_distance_ticks'))} | "
            f"{_fmt(delta.get('event15_signed_volume'))} | "
            f"{_fmt(delta.get('event15_delta_price_divergence'))} |"
        )
    lines.extend(
        [
            "",
            "## Outcome By Symbol",
            "",
            "| Symbol | winner n | loser n | profile percentile W-L | nearest LVN ticks W-L | pre60 signed vol W-L | event15 signed vol W-L |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for symbol, row in payload["outcome_by_symbol"].items():
        delta = row["winner_minus_loser"]
        lines.append(
            "| "
            f"{symbol} | {row['winner']['n']} | {row['loser']['n']} | "
            f"{_fmt(delta.get('profile_event_price_volume_percentile'))} | "
            f"{_fmt(delta.get('profile_nearest_lvn_distance_ticks'))} | "
            f"{_fmt(delta.get('pre60_signed_volume'))} | "
            f"{_fmt(delta.get('event15_signed_volume'))} |"
        )
    lines.extend(
        [
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
    parser.add_argument("--features", default=DEFAULT_FEATURES)
    parser.add_argument("--outcome-join", default=DEFAULT_OUTCOME_JOIN)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(load_json(args.features), load_json(args.outcome_join))
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"symbols={list(payload['candidate_context_by_symbol'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
