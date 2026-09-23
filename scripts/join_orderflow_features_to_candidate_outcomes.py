#!/usr/bin/env python3
"""Join orderflow features to available GTOS candidate outcomes.

Research/tooling only. Uses existing synthetic/actual candidate outcome joins
for diagnostics. No promotion language is allowed from this artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_features import generated_at_utc, median_or_none  # noqa: E402


DEFAULT_FEATURES = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_FEATURE_DIAGNOSTIC_OF_DATA_3_2026-05-02.json"
)
DEFAULT_CANDIDATE_JOIN = (
    "data/external/validation/calendar_macro_bundle_v1/candidate_join/"
    "phase3_candidate_calendar_macro_join_2022_2026_plus_gap_m5_sim_v2_20260501T015608Z.jsonl"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_OF_DATA_4_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_OF_DATA_4_2026-05-02.md"
)

ASOF_FEATURES = (
    "pre60_signed_volume",
    "pre60_buy_fraction",
    "pre60_absorption_volume_per_tick",
    "event15_signed_volume",
    "event15_buy_fraction",
    "event15_absorption_volume_per_tick",
    "profile_event_price_volume_percentile",
    "profile_nearest_lvn_distance_ticks",
)


def normalize_symbol(symbol: str | None) -> str | None:
    if symbol == "US30_cash":
        return "US30"
    return symbol


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def candidate_key(symbol: str | None, candle_close_utc: str | None) -> tuple[str | None, str | None]:
    return (normalize_symbol(symbol), candle_close_utc)


def index_candidate_rows(rows: list[dict[str, Any]]) -> dict[tuple[str | None, str | None], dict[str, Any]]:
    indexed = {}
    for row in rows:
        key = candidate_key(row.get("candidate__symbol") or row.get("symbol"), row.get("candidate__candle_close_utc") or row.get("candle_close_utc"))
        indexed[key] = row
    return indexed


def build_joined_rows(feature_payload: dict[str, Any], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = index_candidate_rows(candidate_rows)
    joined: list[dict[str, Any]] = []
    for row in feature_payload["feature_rows"]:
        if not row.get("is_primary_proxy"):
            continue
        if row.get("event_class") != "candidate":
            continue
        key = candidate_key(row.get("symbol"), row.get("canonical_m15_close_utc"))
        candidate = candidates.get(key)
        out = dict(row)
        out["candidate_join_matched"] = candidate is not None
        if candidate is not None:
            out.update(
                {
                    "candidate__synthetic_realized_r": candidate.get("candidate__synthetic_realized_r"),
                    "candidate__synthetic_outcome": candidate.get("candidate__synthetic_outcome"),
                    "candidate__realized_r": candidate.get("candidate__realized_r"),
                    "candidate__realized_r_available": candidate.get("candidate__realized_r_available"),
                    "candidate__realized_r_missing_reason": candidate.get("candidate__realized_r_missing_reason"),
                    "candidate__timestamp_candle_lag_seconds": candidate.get("candidate__timestamp_candle_lag_seconds"),
                    "candidate__source_line": candidate.get("candidate__source_line"),
                }
            )
        joined.append(out)
    return joined


def summarize(joined: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in joined if row.get("candidate_join_matched")]
    target_rows = [row for row in matched if row.get("candidate__synthetic_realized_r") is not None]
    winners = [row for row in target_rows if float(row["candidate__synthetic_realized_r"]) > 0]
    losers = [row for row in target_rows if float(row["candidate__synthetic_realized_r"]) <= 0]

    def _feature_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {feature: median_or_none([row.get(feature) for row in rows]) for feature in ASOF_FEATURES}

    by_symbol = defaultdict(list)
    for row in target_rows:
        by_symbol[normalize_symbol(row.get("symbol"))].append(row)

    symbol_summary = {}
    for symbol, rows in sorted(by_symbol.items()):
        r_values = [float(row["candidate__synthetic_realized_r"]) for row in rows]
        symbol_summary[symbol] = {
            "n": len(rows),
            "wins": sum(value > 0 for value in r_values),
            "losses": sum(value <= 0 for value in r_values),
            "mean_synthetic_r": sum(r_values) / len(r_values),
            "win_rate": sum(value > 0 for value in r_values) / len(r_values),
            **_feature_summary(rows),
        }

    status_counts = Counter(
        "target_available" if row.get("candidate__synthetic_realized_r") is not None else (
            "join_matched_no_target" if row.get("candidate_join_matched") else "join_missing"
        )
        for row in joined
    )
    return {
        "candidate_feature_rows": len(joined),
        "join_matched": len(matched),
        "target_available": len(target_rows),
        "winner_count": len(winners),
        "loser_count": len(losers),
        "status_counts": dict(sorted(status_counts.items())),
        "winner_medians": _feature_summary(winners),
        "loser_medians": _feature_summary(losers),
        "by_symbol": symbol_summary,
        "readout_bullets": build_readout_bullets(len(target_rows), symbol_summary),
    }


def build_readout_bullets(target_n: int, symbol_summary: dict[str, Any]) -> list[str]:
    bullets = [
        f"Outcome-joined target count is {target_n}; this is below promotion-grade sample size.",
    ]
    if symbol_summary:
        compact = {
            symbol: {
                "n": row["n"],
                "wins": row["wins"],
                "losses": row["losses"],
                "mean_r": round(float(row["mean_synthetic_r"]), 4),
            }
            for symbol, row in symbol_summary.items()
        }
        bullets.append(f"Target coverage by symbol: {compact}.")
    for symbol, row in sorted(symbol_summary.items()):
        if row.get("losses", 0) == 0:
            bullets.append(
                f"{symbol} has no loser contrast in this join, so it cannot validate a winner-versus-loser orderflow rule yet."
            )
        elif row.get("wins", 0) == 0:
            bullets.append(
                f"{symbol} has no winner contrast in this join, so it can only support failure forensics."
            )
    if "NAS100" in symbol_summary and symbol_summary["NAS100"].get("win_rate", 1.0) < 0.25:
        bullets.append("The clearest current signal is a NAS100 candidate failure cluster, not a universal orderflow edge.")
    bullets.append("Any next hypothesis should be symbol-stratified and as-of only.")
    return bullets


def build_payload(feature_payload: dict[str, Any], candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined = build_joined_rows(feature_payload, candidate_rows)
    summary = summarize(joined)
    return {
        "schema_version": "orderflow_candidate_outcome_join_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "feature_schema_version": feature_payload.get("schema_version"),
            "candidate_rows_loaded": len(candidate_rows),
            "asof_feature_fields": list(ASOF_FEATURES),
        },
        "joined_rows": joined,
        "synthesis": {
            "summary": (
                "Primary-proxy candidate orderflow features were joined to available "
                "candidate synthetic/actual outcomes. This is a small diagnostic join, "
                "not an alpha test or promotion claim."
            ),
            **summary,
            "ambiguities": [
                "Synthetic realized R is not the same as broker actual realized R; actual realized coverage remains sparse.",
                "Only primary futures proxies are used in the outcome readout; ES remains a US30 comparator.",
                "The sample is recent live/shadow candidate coverage, not a historical population replay.",
                "Winner/loser feature medians are descriptive and not DSR/PBO/effective_N validated.",
                "Post-event features are deliberately excluded from this as-of outcome readout.",
            ],
            "open_questions": [
                "Do any as-of orderflow features retain separation after symbol/session stratification?",
                "Is apparent separation mostly a NAS100 failure signature rather than a universal orderflow mechanism?",
                "Can actual realized-R coverage be enriched enough to replace synthetic labels?",
                "Which one or two structural hypotheses deserve registration for a controlled replay?",
            ],
            "next_steps": [
                "Run a symbol-stratified candidate diagnostic on as-of features only.",
                "Treat NAS100 separately before forming any broad orderflow rule.",
                "Backfill or forward-collect actual realized outcomes for these event rows.",
                "If a hypothesis is registered, freeze thresholds before any replay-style evaluation.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    return f"{float(value):.4f}"


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow Candidate Outcome Join",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Candidate feature rows: {synth['candidate_feature_rows']}",
        f"- Join matched: {synth['join_matched']}",
        f"- Target available: {synth['target_available']}",
        f"- Winner / loser: {synth['winner_count']} / {synth['loser_count']}",
        f"- Status counts: {synth['status_counts']}",
        "",
        "## Winner vs Loser As-Of Medians",
        "",
        "| Feature | Winners | Losers |",
        "|---|---:|---:|",
    ]
    for feature in ASOF_FEATURES:
        lines.append(
            f"| {feature} | {_fmt(synth['winner_medians'].get(feature))} | {_fmt(synth['loser_medians'].get(feature))} |"
        )
    lines.extend(
        [
            "",
            "## Readout",
            "",
            *[f"- {item}" for item in synth["readout_bullets"]],
        ]
    )
    lines.extend(
        [
            "",
            "## By Symbol",
            "",
            "| Symbol | n | wins | losses | mean synthetic R | win rate | event15 signed vol | event15 buy fraction | profile percentile | nearest LVN ticks |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for symbol, row in synth["by_symbol"].items():
        lines.append(
            "| "
            f"{symbol} | {row['n']} | "
            f"{row['wins']} | "
            f"{row['losses']} | "
            f"{_fmt(row['mean_synthetic_r'])} | "
            f"{_fmt(row['win_rate'])} | "
            f"{_fmt(row.get('event15_signed_volume'))} | "
            f"{_fmt(row.get('event15_buy_fraction'))} | "
            f"{_fmt(row.get('profile_event_price_volume_percentile'))} | "
            f"{_fmt(row.get('profile_nearest_lvn_distance_ticks'))} |"
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
    parser.add_argument("--candidate-join", default=DEFAULT_CANDIDATE_JOIN)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    feature_path = Path(args.features)
    candidate_path = Path(args.candidate_join)
    if not feature_path.exists():
        parser.exit(2, f"features not found: {feature_path}\n")
    if not candidate_path.exists():
        parser.exit(2, f"candidate join not found: {candidate_path}\n")
    payload = build_payload(load_json(feature_path), read_jsonl(candidate_path))
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"target_available={payload['synthesis']['target_available']} "
        f"winners={payload['synthesis']['winner_count']} "
        f"losers={payload['synthesis']['loser_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
