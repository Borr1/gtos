#!/usr/bin/env python3
"""Extract MBP-1 top-of-book depth diagnostics for selected orderflow windows.

Research/tooling only. MBP-1 is not a full footprint/heatmap ladder; it gives
top-of-book updates that can test whether a narrower depth pilot is worth more
Databento spend.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_event_manifest import FUTURES_PROXY_MAP  # noqa: E402
from src.research_infra.orderflow_features import generated_at_utc, median_or_none, parse_utc, tick_size  # noqa: E402


DEFAULT_MANIFEST = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json"
)
DEFAULT_FETCH_PLAN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP1_PILOT_FETCH_PLAN_OF_DATA_7_2026-05-02.json"
)
DEFAULT_OUTCOME_JOIN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_OF_DATA_4_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP1_FEATURE_DIAGNOSTIC_OF_DATA_8_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP1_FEATURE_DIAGNOSTIC_OF_DATA_8_2026-05-02.md"
)

DEPTH_COLUMNS = (
    "ts_event",
    "symbol",
    "bid_px_00",
    "ask_px_00",
    "bid_sz_00",
    "ask_sz_00",
    "bid_ct_00",
    "ask_ct_00",
)

SUMMARY_FEATURES = (
    "event15_median_spread_ticks",
    "event15_median_book_imbalance",
    "event15_last_book_imbalance",
    "event15_thin_top_book_rate",
    "event15_mid_change_ticks",
    "pre60_median_spread_ticks",
    "pre60_median_book_imbalance",
    "pre60_median_top_liquidity",
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_symbol(symbol: str | None) -> str | None:
    if symbol == "US30_cash":
        return "US30"
    return symbol


def is_primary_proxy(gtos_symbol: str, futures_symbol: str) -> bool:
    proxies = FUTURES_PROXY_MAP.get(gtos_symbol) or ()
    return bool(proxies) and futures_symbol == proxies[0]


def candidate_key(symbol: str | None, candle_close_utc: str | None) -> tuple[str | None, str | None]:
    return (normalize_symbol(symbol), candle_close_utc)


def index_outcome_rows(outcome_payload: dict[str, Any]) -> dict[tuple[str | None, str | None], dict[str, Any]]:
    indexed: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    for row in outcome_payload.get("joined_rows") or []:
        key = candidate_key(row.get("symbol"), row.get("canonical_m15_close_utc"))
        indexed[key] = row
    return indexed


def load_databento_mbp1(path: Path | str, *, chunk_size: int = 1_000_000) -> pd.DataFrame:
    import databento as db  # Local import keeps unit tests dependency-light.

    store = db.DBNStore.from_file(str(path))
    frames: list[pd.DataFrame] = []
    for chunk in store.to_df(count=chunk_size):
        if chunk.empty:
            continue
        missing = set(DEPTH_COLUMNS) - set(chunk.columns)
        if missing:
            raise ValueError(f"MBP-1 DBN missing columns {sorted(missing)}: {path}")
        frame = chunk.loc[:, DEPTH_COLUMNS].copy()
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=list(DEPTH_COLUMNS))
    out = pd.concat(frames, axis=0, ignore_index=True)
    out["ts_event"] = pd.to_datetime(out["ts_event"], utc=True)
    out["symbol"] = out["symbol"].astype(str)
    for col in ("bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00", "bid_ct_00", "ask_ct_00"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.sort_values("ts_event")


def slice_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if df.empty or end <= start:
        return df.iloc[0:0].copy()
    return df[(df["ts_event"] >= start) & (df["ts_event"] < end)].copy()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _sign_change_rate(values: pd.Series) -> float | None:
    signs = np.sign(values.dropna().to_numpy(dtype=float))
    signs = signs[signs != 0]
    if len(signs) < 2:
        return None
    return _safe_float(np.mean(signs[1:] != signs[:-1]))


def depth_stats(
    df: pd.DataFrame,
    futures_symbol: str,
    prefix: str,
    *,
    thin_threshold: float | None = None,
) -> dict[str, Any]:
    if df.empty:
        return {
            f"{prefix}_update_count": 0,
            f"{prefix}_median_spread_ticks": None,
            f"{prefix}_p95_spread_ticks": None,
            f"{prefix}_median_book_imbalance": None,
            f"{prefix}_mean_book_imbalance": None,
            f"{prefix}_last_book_imbalance": None,
            f"{prefix}_median_top_liquidity": None,
            f"{prefix}_thin_top_book_rate": None,
            f"{prefix}_imbalance_flip_rate": None,
            f"{prefix}_mid_change_ticks": None,
        }
    ts = tick_size(futures_symbol)
    bid = df["bid_px_00"].astype(float)
    ask = df["ask_px_00"].astype(float)
    bid_size = df["bid_sz_00"].astype(float)
    ask_size = df["ask_sz_00"].astype(float)
    top_liquidity = bid_size + ask_size
    imbalance = (bid_size - ask_size) / top_liquidity.replace(0, np.nan)
    spread_ticks = (ask - bid) / ts
    mid = (bid + ask) / 2.0
    if thin_threshold is None and prefix == "pre60":
        thin_threshold = _safe_float(top_liquidity.quantile(0.2))
    thin_rate = None
    if thin_threshold is not None:
        thin_rate = _safe_float((top_liquidity <= thin_threshold).mean())
    mid_change_ticks = None
    if len(mid.dropna()) >= 2:
        mid_change_ticks = _safe_float((mid.dropna().iloc[-1] - mid.dropna().iloc[0]) / ts)
    return {
        f"{prefix}_update_count": int(len(df)),
        f"{prefix}_median_spread_ticks": _safe_float(spread_ticks.median()),
        f"{prefix}_p95_spread_ticks": _safe_float(spread_ticks.quantile(0.95)),
        f"{prefix}_median_book_imbalance": _safe_float(imbalance.median()),
        f"{prefix}_mean_book_imbalance": _safe_float(imbalance.mean()),
        f"{prefix}_last_book_imbalance": _safe_float(imbalance.dropna().iloc[-1]) if not imbalance.dropna().empty else None,
        f"{prefix}_median_top_liquidity": _safe_float(top_liquidity.median()),
        f"{prefix}_thin_top_book_rate": thin_rate,
        f"{prefix}_imbalance_flip_rate": _sign_change_rate(imbalance),
        f"{prefix}_mid_change_ticks": mid_change_ticks,
    }


def compute_event_depth_features(event: dict[str, Any], mbp1: pd.DataFrame, futures_symbol: str) -> dict[str, Any]:
    symbol_df = mbp1[mbp1["symbol"] == futures_symbol].copy()
    canonical = parse_utc(event["canonical_m15_close_utc"])
    window_start = parse_utc(event["window_start_utc"])
    pre60 = slice_window(symbol_df, window_start, canonical)
    event15 = slice_window(symbol_df, canonical - pd.Timedelta(minutes=15), canonical)
    pre_top = (pre60["bid_sz_00"].astype(float) + pre60["ask_sz_00"].astype(float)) if not pre60.empty else pd.Series(dtype=float)
    pre_thin_threshold = _safe_float(pre_top.quantile(0.2)) if not pre_top.empty else None
    row: dict[str, Any] = {
        "event_id": event["event_id"],
        "symbol": event["symbol"],
        "futures_symbol": futures_symbol,
        "is_primary_proxy": is_primary_proxy(str(event["symbol"]), futures_symbol),
        "event_class": event["event_class"],
        "decision": event.get("decision"),
        "framework": event.get("framework"),
        "direction": event.get("direction"),
        "canonical_m15_close_utc": event["canonical_m15_close_utc"],
        "window_start_utc": event["window_start_utc"],
        "window_end_utc": event["window_end_utc"],
        "data_status": "ok" if not symbol_df.empty else "no_data",
        "pre60_thin_top_book_threshold": pre_thin_threshold,
        "total_mbp1_updates_in_group_symbol": int(len(symbol_df)),
    }
    row.update(depth_stats(pre60, futures_symbol, "pre60"))
    row.update(depth_stats(event15, futures_symbol, "event15", thin_threshold=pre_thin_threshold))
    return row


def _group_fetch_paths(fetch_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["group_id"]: row for row in fetch_plan.get("groups") or []}


def build_feature_rows(manifest: dict[str, Any], fetch_plan: dict[str, Any]) -> list[dict[str, Any]]:
    events = {event["event_id"]: event for event in manifest.get("events") or []}
    manifest_groups = {group["group_id"]: group for group in manifest.get("fetch_groups") or []}
    fetch_groups = _group_fetch_paths(fetch_plan)
    rows: list[dict[str, Any]] = []
    for group_id, fetch_group in sorted(fetch_groups.items()):
        manifest_group = manifest_groups.get(group_id, {})
        event_ids = fetch_group.get("event_ids") or manifest_group.get("event_ids") or []
        group_events = [events[event_id] for event_id in event_ids if event_id in events]
        output_path = Path(fetch_group["output_path"])
        if not output_path.exists():
            for event in group_events:
                for futures_symbol in fetch_group["request"]["symbols"]:
                    rows.append(
                        {
                            "event_id": event["event_id"],
                            "symbol": event["symbol"],
                            "futures_symbol": futures_symbol,
                            "event_class": event["event_class"],
                            "canonical_m15_close_utc": event["canonical_m15_close_utc"],
                            "data_status": "missing_raw",
                        }
                    )
            continue
        mbp1 = load_databento_mbp1(output_path)
        for event in group_events:
            for futures_symbol in fetch_group["request"]["symbols"]:
                row = compute_event_depth_features(event, mbp1, futures_symbol)
                row["group_id"] = group_id
                rows.append(row)
    return rows


def attach_outcomes(rows: list[dict[str, Any]], outcome_index: dict[tuple[str | None, str | None], dict[str, Any]]) -> None:
    for row in rows:
        key = candidate_key(row.get("symbol"), row.get("canonical_m15_close_utc"))
        outcome = outcome_index.get(key)
        row["candidate_outcome_join_matched"] = outcome is not None
        if outcome is not None:
            row["candidate__synthetic_realized_r"] = outcome.get("candidate__synthetic_realized_r")
            row["candidate__synthetic_outcome"] = outcome.get("candidate__synthetic_outcome")
            row["candidate__realized_r"] = outcome.get("candidate__realized_r")
            row["candidate__realized_r_available"] = outcome.get("candidate__realized_r_available")


def summarize_bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"n": len(rows)}
    for feature in SUMMARY_FEATURES:
        out[f"median_{feature}"] = median_or_none([row.get(feature) for row in rows])
    return out


def candidate_context_by_symbol(rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [row for row in rows if row.get("is_primary_proxy") and row.get("data_status") == "ok"]
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in primary:
        klass = "candidate" if row.get("event_class") == "candidate" else "context"
        buckets[str(row.get("symbol"))][klass].append(row)
    out: dict[str, Any] = {}
    for symbol, symbol_buckets in sorted(buckets.items()):
        candidate = summarize_bucket(symbol_buckets.get("candidate", []))
        context = summarize_bucket(symbol_buckets.get("context", []))
        deltas = {}
        for feature in SUMMARY_FEATURES:
            c = candidate.get(f"median_{feature}")
            x = context.get(f"median_{feature}")
            deltas[feature] = None if c is None or x is None else float(c) - float(x)
        out[symbol] = {
            "candidate": candidate,
            "context": context,
            "candidate_minus_context": deltas,
        }
    return out


def outcome_by_symbol(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_rows = [
        row
        for row in rows
        if row.get("is_primary_proxy")
        and row.get("event_class") == "candidate"
        and row.get("candidate__synthetic_realized_r") is not None
    ]
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in target_rows:
        outcome = "winner" if float(row["candidate__synthetic_realized_r"]) > 0 else "loser"
        buckets[str(row.get("symbol"))][outcome].append(row)
    out: dict[str, Any] = {}
    for symbol, symbol_buckets in sorted(buckets.items()):
        winner = summarize_bucket(symbol_buckets.get("winner", []))
        loser = summarize_bucket(symbol_buckets.get("loser", []))
        deltas = {}
        for feature in SUMMARY_FEATURES:
            w = winner.get(f"median_{feature}")
            l = loser.get(f"median_{feature}")
            deltas[feature] = None if w is None or l is None else float(w) - float(l)
        out[symbol] = {"winner": winner, "loser": loser, "winner_minus_loser": deltas}
    return out


def build_readout(candidate_context: dict[str, Any], outcome: dict[str, Any]) -> list[str]:
    bullets = []
    for symbol, row in outcome.items():
        winner_n = row["winner"]["n"]
        loser_n = row["loser"]["n"]
        if winner_n and loser_n:
            bullets.append(f"{symbol} MBP-1 outcome contrast exists: winner n={winner_n}, loser n={loser_n}.")
        else:
            bullets.append(
                f"{symbol} MBP-1 outcome rows are one-sided or sparse: winner n={winner_n}, loser n={loser_n}; no {symbol} depth rule can be inferred."
            )
    for symbol, row in candidate_context.items():
        cand = row["candidate"]
        context = row["context"]
        delta = row["candidate_minus_context"]
        if cand["n"] and context["n"]:
            bullets.append(
                f"{symbol}: candidate/context n={cand['n']}/{context['n']}, "
                f"event15 imbalance delta={_fmt(delta.get('event15_median_book_imbalance'))}, "
                f"event15 thin-rate delta={_fmt(delta.get('event15_thin_top_book_rate'))}."
            )
    bullets.append("MBP-1 can support top-of-book diagnostics, but it cannot validate full footprint/heatmap claims.")
    bullets.append("No promotion or parameter change is justified from this pilot.")
    return bullets


def build_payload(manifest: dict[str, Any], fetch_plan: dict[str, Any], outcome_payload: dict[str, Any]) -> dict[str, Any]:
    rows = build_feature_rows(manifest, fetch_plan)
    attach_outcomes(rows, index_outcome_rows(outcome_payload))
    candidate_context = candidate_context_by_symbol(rows)
    outcome = outcome_by_symbol(rows)
    status_counts = {}
    for row in rows:
        status_counts[row.get("data_status")] = status_counts.get(row.get("data_status"), 0) + 1
    return {
        "schema_version": "orderflow_depth_mbp1_feature_diagnostic_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "manifest_schema_version": manifest.get("schema_version"),
            "fetch_plan_schema_version": fetch_plan.get("schema_version"),
            "outcome_join_schema_version": outcome_payload.get("schema_version"),
            "fetch_group_count": len(fetch_plan.get("groups") or []),
            "feature_fields": list(SUMMARY_FEATURES),
            "mbp1_depth_limitation": "top_of_book_only",
        },
        "feature_rows": rows,
        "synthesis": {
            "summary": (
                "MBP-1 top-of-book depth features were extracted for scoped candidate windows across current primary futures proxies. "
                "This is a spend-controlled diagnostic, not a trading rule."
            ),
            "feature_row_count": len(rows),
            "data_status_counts": dict(sorted(status_counts.items())),
            "candidate_context_by_symbol": candidate_context,
            "outcome_by_symbol": outcome,
            "readout": build_readout(candidate_context, outcome),
            "ambiguities": [
                "MBP-1 only gives best bid/ask depth; it does not reconstruct the full ladder, LVN/HVN heatmap, queue position, or iceberg behavior.",
                "The sample was selected from already-interesting windows, so candidate/context differences are diagnostic and not a population claim.",
                "Outcome labels remain mostly synthetic/path labels; broker actual-R coverage is still too sparse.",
                "Top-of-book imbalance can be quote-noisy and may reflect liquidity provision/cancellation rather than executed intent.",
                "No thresholds were optimized or registered in this pilot.",
            ],
            "open_questions": [
                "Does any symbol-specific depth separation persist after more live candidate windows accrue?",
                "Would MBP-10 or MBO expose ladder-level LVN/liquidity-pocket behavior that MBP-1 cannot see?",
                "Can top-of-book thinness/imbalance be transformed into a pre-registered structural hypothesis without post-hoc thresholding?",
                "Do one-sided winner or loser cohorts gain enough opposite labels to support outcome contrast?",
            ],
            "next_steps": [
                "Use this MBP-1 pilot to decide whether deeper MBP-10/MBO pulls are worth spending on a specific symbol/failure cluster.",
                "Keep depth features separate from trades-level footprint features until a registered hypothesis is written.",
                "Do not spend on broad depth history until candidate/outcome coverage expands.",
                "Forward-collect executed-trade actual R so depth diagnostics can eventually be scored against broker outcomes.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow MBP-1 Depth Feature Diagnostic",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Feature rows: {synth['feature_row_count']}",
        f"- Data status counts: {synth['data_status_counts']}",
        f"- Limitation: {payload['inputs']['mbp1_depth_limitation']}",
        "",
        "## Readout",
        "",
        *[f"- {item}" for item in synth["readout"]],
        "",
        "## Candidate vs Context",
        "",
        "| Symbol | candidate n | context n | event15 imbalance delta | event15 thin-rate delta | event15 spread delta | pre60 top liquidity delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol, row in synth["candidate_context_by_symbol"].items():
        delta = row["candidate_minus_context"]
        lines.append(
            "| "
            f"{symbol} | {row['candidate']['n']} | {row['context']['n']} | "
            f"{_fmt(delta.get('event15_median_book_imbalance'))} | "
            f"{_fmt(delta.get('event15_thin_top_book_rate'))} | "
            f"{_fmt(delta.get('event15_median_spread_ticks'))} | "
            f"{_fmt(delta.get('pre60_median_top_liquidity'))} |"
        )
    lines.extend(
        [
            "",
            "## Outcome By Symbol",
            "",
            "| Symbol | winner n | loser n | event15 imbalance W-L | event15 thin-rate W-L | event15 spread W-L | pre60 top liquidity W-L |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for symbol, row in synth["outcome_by_symbol"].items():
        delta = row["winner_minus_loser"]
        lines.append(
            "| "
            f"{symbol} | {row['winner']['n']} | {row['loser']['n']} | "
            f"{_fmt(delta.get('event15_median_book_imbalance'))} | "
            f"{_fmt(delta.get('event15_thin_top_book_rate'))} | "
            f"{_fmt(delta.get('event15_median_spread_ticks'))} | "
            f"{_fmt(delta.get('pre60_median_top_liquidity'))} |"
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
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--fetch-plan", default=DEFAULT_FETCH_PLAN)
    parser.add_argument("--outcome-join", default=DEFAULT_OUTCOME_JOIN)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(load_json(args.manifest), load_json(args.fetch_plan), load_json(args.outcome_join))
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"feature_rows={payload['synthesis']['feature_row_count']} status={payload['synthesis']['data_status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
