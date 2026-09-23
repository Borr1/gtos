#!/usr/bin/env python3
"""Extract sampled MBP-10 ladder-depth diagnostics for selected windows.

Research/tooling only. The MBP-10 raw files can be very large, so this report
uses one-second last-quote snapshots to study durable ladder state without
pretending to reconstruct every queue event.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import analyze_orderflow_depth_mbp1_features as mbp1  # noqa: E402
from src.research_infra.orderflow_event_manifest import FUTURES_PROXY_MAP  # noqa: E402
from src.research_infra.orderflow_features import generated_at_utc, median_or_none, parse_utc, tick_size  # noqa: E402


DEFAULT_MANIFEST = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json"
)
DEFAULT_FETCH_PLAN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP10_ESTIMATE_OF_DATA_9_2026-05-02.json"
)
DEFAULT_OUTCOME_JOIN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_CANDIDATE_OUTCOME_JOIN_OF_DATA_4_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP10_FEATURE_DIAGNOSTIC_OF_DATA_10_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_DEPTH_MBP10_FEATURE_DIAGNOSTIC_OF_DATA_10_2026-05-02.md"
)

LEVELS = tuple(range(10))
LEVEL_TAGS = tuple(f"{idx:02d}" for idx in LEVELS)
MBP10_COLUMNS = (
    ["ts_event", "symbol"]
    + [f"bid_px_{tag}" for tag in LEVEL_TAGS]
    + [f"ask_px_{tag}" for tag in LEVEL_TAGS]
    + [f"bid_sz_{tag}" for tag in LEVEL_TAGS]
    + [f"ask_sz_{tag}" for tag in LEVEL_TAGS]
)
SUMMARY_FEATURES = (
    "event15_median_depth10_imbalance",
    "event15_last_depth10_imbalance",
    "event15_thin_depth10_rate",
    "event15_median_total_depth10",
    "event15_median_near_far_ratio",
    "event15_median_max_bid_wall",
    "event15_median_max_ask_wall",
    "event15_mid_change_ticks",
    "pre60_median_depth10_imbalance",
    "pre60_median_total_depth10",
)


def is_primary_proxy(gtos_symbol: str, futures_symbol: str) -> bool:
    proxies = FUTURES_PROXY_MAP.get(gtos_symbol) or ()
    return bool(proxies) and futures_symbol == proxies[0]


def load_databento_mbp10_sampled(
    path: Path | str,
    *,
    chunk_size: int = 1_000_000,
    sample_interval: str = "1s",
) -> pd.DataFrame:
    import databento as db  # Local import keeps unit tests dependency-light.

    empty_columns = ["symbol", "sample_ts", *[col for col in MBP10_COLUMNS if col != "symbol"]]
    store = db.DBNStore.from_file(str(path))
    frames: list[pd.DataFrame] = []
    for chunk in store.to_df(count=chunk_size):
        if chunk.empty:
            continue
        chunk = chunk.loc[:, ~chunk.columns.duplicated()].copy()
        missing = set(MBP10_COLUMNS) - set(chunk.columns)
        if missing:
            raise ValueError(f"MBP-10 DBN missing columns {sorted(missing)}: {path}")
        frame = chunk.loc[:, MBP10_COLUMNS].copy()
        frame["ts_event"] = pd.to_datetime(frame["ts_event"], utc=True)
        frame["sample_ts"] = frame["ts_event"].dt.floor(sample_interval)
        frame = frame.groupby(["symbol", "sample_ts"], sort=True, as_index=False).last()
        frame = frame.loc[:, ~frame.columns.duplicated()].copy()
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=empty_columns)
    out = pd.concat(frames, axis=0, ignore_index=True)
    out = out.groupby(["symbol", "sample_ts"], sort=True, as_index=False).last()
    out = out.loc[:, ~out.columns.duplicated()].copy()
    out["ts_event"] = pd.to_datetime(out["sample_ts"], utc=True)
    out["symbol"] = out["symbol"].astype(str)
    for col in MBP10_COLUMNS:
        if col not in {"ts_event", "symbol"}:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.sort_values("ts_event")


def add_ladder_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    bid_sizes = out[[f"bid_sz_{tag}" for tag in LEVEL_TAGS]].astype(float)
    ask_sizes = out[[f"ask_sz_{tag}" for tag in LEVEL_TAGS]].astype(float)
    near_bid = out[[f"bid_sz_{tag}" for tag in LEVEL_TAGS[:3]]].astype(float).sum(axis=1)
    near_ask = out[[f"ask_sz_{tag}" for tag in LEVEL_TAGS[:3]]].astype(float).sum(axis=1)
    bid10 = bid_sizes.sum(axis=1)
    ask10 = ask_sizes.sum(axis=1)
    total10 = bid10 + ask10
    near_total = near_bid + near_ask
    far_total = (total10 - near_total).replace(0, np.nan)
    out["mid_px"] = (out["bid_px_00"].astype(float) + out["ask_px_00"].astype(float)) / 2.0
    out["spread_ticks_raw"] = out["ask_px_00"].astype(float) - out["bid_px_00"].astype(float)
    out["bid_depth10"] = bid10
    out["ask_depth10"] = ask10
    out["total_depth10"] = total10
    out["depth10_imbalance"] = (bid10 - ask10) / total10.replace(0, np.nan)
    out["near3_imbalance"] = (near_bid - near_ask) / near_total.replace(0, np.nan)
    out["near_far_ratio"] = near_total / far_total
    out["max_bid_wall"] = bid_sizes.max(axis=1)
    out["max_ask_wall"] = ask_sizes.max(axis=1)
    return out


def _safe_float(value: Any) -> float | None:
    return mbp1._safe_float(value)


def _sign_change_rate(values: pd.Series) -> float | None:
    return mbp1._sign_change_rate(values)


def ladder_stats(
    df: pd.DataFrame,
    futures_symbol: str,
    prefix: str,
    *,
    thin_threshold: float | None = None,
) -> dict[str, Any]:
    if df.empty:
        return {
            f"{prefix}_sample_count": 0,
            f"{prefix}_median_spread_ticks": None,
            f"{prefix}_median_depth10_imbalance": None,
            f"{prefix}_last_depth10_imbalance": None,
            f"{prefix}_median_near3_imbalance": None,
            f"{prefix}_median_total_depth10": None,
            f"{prefix}_thin_depth10_rate": None,
            f"{prefix}_median_near_far_ratio": None,
            f"{prefix}_median_max_bid_wall": None,
            f"{prefix}_median_max_ask_wall": None,
            f"{prefix}_depth10_imbalance_flip_rate": None,
            f"{prefix}_mid_change_ticks": None,
        }
    enriched = add_ladder_columns(df)
    ts = tick_size(futures_symbol)
    spread_ticks = enriched["spread_ticks_raw"] / ts
    thin_rate = None
    if thin_threshold is None and prefix == "pre60":
        thin_threshold = _safe_float(enriched["total_depth10"].quantile(0.2))
    if thin_threshold is not None:
        thin_rate = _safe_float((enriched["total_depth10"] <= thin_threshold).mean())
    mid_change = None
    mid = enriched["mid_px"].dropna()
    if len(mid) >= 2:
        mid_change = _safe_float((mid.iloc[-1] - mid.iloc[0]) / ts)
    return {
        f"{prefix}_sample_count": int(len(enriched)),
        f"{prefix}_median_spread_ticks": _safe_float(spread_ticks.median()),
        f"{prefix}_median_depth10_imbalance": _safe_float(enriched["depth10_imbalance"].median()),
        f"{prefix}_last_depth10_imbalance": _safe_float(enriched["depth10_imbalance"].dropna().iloc[-1])
        if not enriched["depth10_imbalance"].dropna().empty
        else None,
        f"{prefix}_median_near3_imbalance": _safe_float(enriched["near3_imbalance"].median()),
        f"{prefix}_median_total_depth10": _safe_float(enriched["total_depth10"].median()),
        f"{prefix}_thin_depth10_rate": thin_rate,
        f"{prefix}_median_near_far_ratio": _safe_float(enriched["near_far_ratio"].median()),
        f"{prefix}_median_max_bid_wall": _safe_float(enriched["max_bid_wall"].median()),
        f"{prefix}_median_max_ask_wall": _safe_float(enriched["max_ask_wall"].median()),
        f"{prefix}_depth10_imbalance_flip_rate": _sign_change_rate(enriched["depth10_imbalance"]),
        f"{prefix}_mid_change_ticks": mid_change,
    }


def compute_event_ladder_features(event: dict[str, Any], mbp10: pd.DataFrame, futures_symbol: str) -> dict[str, Any]:
    symbol_df = mbp10[mbp10["symbol"] == futures_symbol].copy()
    canonical = parse_utc(event["canonical_m15_close_utc"])
    window_start = parse_utc(event["window_start_utc"])
    pre60 = mbp1.slice_window(symbol_df, window_start, canonical)
    event15 = mbp1.slice_window(symbol_df, canonical - pd.Timedelta(minutes=15), canonical)
    pre_total = add_ladder_columns(pre60)["total_depth10"] if not pre60.empty else pd.Series(dtype=float)
    pre_thin_threshold = _safe_float(pre_total.quantile(0.2)) if not pre_total.empty else None
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
        "sample_interval": "1s_last_quote",
        "pre60_thin_depth10_threshold": pre_thin_threshold,
        "total_sampled_quotes_in_group_symbol": int(len(symbol_df)),
    }
    row.update(ladder_stats(pre60, futures_symbol, "pre60"))
    row.update(ladder_stats(event15, futures_symbol, "event15", thin_threshold=pre_thin_threshold))
    return row


def build_feature_rows(manifest: dict[str, Any], fetch_plan: dict[str, Any]) -> list[dict[str, Any]]:
    events = {event["event_id"]: event for event in manifest.get("events") or []}
    manifest_groups = {group["group_id"]: group for group in manifest.get("fetch_groups") or []}
    rows: list[dict[str, Any]] = []
    for fetch_group in fetch_plan.get("groups") or []:
        group_id = fetch_group["group_id"]
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
        mbp10 = load_databento_mbp10_sampled(output_path)
        for event in group_events:
            for futures_symbol in fetch_group["request"]["symbols"]:
                row = compute_event_ladder_features(event, mbp10, futures_symbol)
                row["group_id"] = group_id
                rows.append(row)
    return rows


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
        out[symbol] = {"candidate": candidate, "context": context, "candidate_minus_context": deltas}
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
        if not (winner_n and loser_n):
            bullets.append(
                f"{symbol} MBP-10 outcome rows are one-sided or sparse: winner n={winner_n}, loser n={loser_n}; no {symbol} ladder claim can be made."
            )
    nas = outcome.get("NAS100")
    if nas and nas["winner"]["n"] and nas["loser"]["n"]:
        bullets.append(
            "NAS100 MBP-10 outcome rows remain failure-cluster dominated: "
            f"winner n={nas['winner']['n']}, loser n={nas['loser']['n']}."
        )
        delta = nas["winner_minus_loser"]
        bullets.append(
            "NAS100 winner-minus-loser ladder deltas: "
            f"depth10 imbalance={_fmt(delta.get('event15_median_depth10_imbalance'))}, "
            f"thin-rate={_fmt(delta.get('event15_thin_depth10_rate'))}, "
            f"total-depth={_fmt(delta.get('event15_median_total_depth10'))}."
        )
    for symbol, row in candidate_context.items():
        candidate = row["candidate"]
        context = row["context"]
        delta = row["candidate_minus_context"]
        if candidate["n"] and context["n"]:
            bullets.append(
                f"{symbol}: candidate/context n={candidate['n']}/{context['n']}, "
                f"event15 depth10 imbalance delta={_fmt(delta.get('event15_median_depth10_imbalance'))}, "
                f"event15 total-depth delta={_fmt(delta.get('event15_median_total_depth10'))}."
            )
    bullets.append("MBP-10 answers more of the ladder question than MBP-1, but this sampled pilot is not promotion-grade.")
    return bullets


def build_payload(manifest: dict[str, Any], fetch_plan: dict[str, Any], outcome_payload: dict[str, Any]) -> dict[str, Any]:
    rows = build_feature_rows(manifest, fetch_plan)
    mbp1.attach_outcomes(rows, mbp1.index_outcome_rows(outcome_payload))
    candidate_context = candidate_context_by_symbol(rows)
    outcome = outcome_by_symbol(rows)
    status_counts = {}
    for row in rows:
        status_counts[row.get("data_status")] = status_counts.get(row.get("data_status"), 0) + 1
    return {
        "schema_version": "orderflow_depth_mbp10_feature_diagnostic_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "manifest_schema_version": manifest.get("schema_version"),
            "fetch_plan_schema_version": fetch_plan.get("schema_version"),
            "outcome_join_schema_version": outcome_payload.get("schema_version"),
            "fetch_group_count": len(fetch_plan.get("groups") or []),
            "feature_fields": list(SUMMARY_FEATURES),
            "sample_method": "one_second_last_quote_per_symbol",
            "mbp10_depth_scope": "top_10_levels",
        },
        "feature_rows": rows,
        "synthesis": {
            "summary": (
                "Sampled MBP-10 ladder-depth features were extracted for scoped candidate windows across current primary futures proxies. "
                "This tests whether deeper book state opens a defensible next hypothesis."
            ),
            "feature_row_count": len(rows),
            "data_status_counts": dict(sorted(status_counts.items())),
            "candidate_context_by_symbol": candidate_context,
            "outcome_by_symbol": outcome,
            "readout": build_readout(candidate_context, outcome),
            "ambiguities": [
                "This uses one-second last-quote snapshots, so it does not capture every queue addition/cancellation or intra-second spoof/cancel pattern.",
                "MBP-10 gives the top 10 levels, not full MBO order identity or queue position.",
                "The sample is selected from known interesting windows and is not population-random.",
                "Actual broker realized-R coverage remains too sparse; outcome rows are mostly synthetic/path labels.",
                "No depth thresholds were optimized, registered, or promoted.",
            ],
            "open_questions": [
                "Does any symbol-specific failure cluster show a repeatable ladder-depth signature in future windows?",
                "Is the observed ladder state a cause of failure or just a byproduct of the same structural regime?",
                "Would MBO add materially more than MBP-10 for our purposes, or is the storage/cost burden unjustified?",
                "Can ladder-thinness or depth imbalance be turned into a single pre-registered hypothesis with fixed windows and no threshold mining?",
            ],
            "next_steps": [
                "Do not buy broad MBP-10/MBO history yet; wait for more candidate outcomes or a precise hypothesis.",
                "Use MBP-10 only for targeted forensic windows until actual-R coverage improves.",
                "If a hypothesis is registered, freeze the feature family, lookback window, and threshold before replay.",
                "Forward-collect candidate windows with trades + MBP-1 by default, and promote MBP-10 collection only when a candidate enters a high-value forensic bucket.",
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
        "# Orderflow MBP-10 Ladder Feature Diagnostic",
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
        f"- Sample method: {payload['inputs']['sample_method']}",
        f"- Depth scope: {payload['inputs']['mbp10_depth_scope']}",
        "",
        "## Readout",
        "",
        *[f"- {item}" for item in synth["readout"]],
        "",
        "## Candidate vs Context",
        "",
        "| Symbol | candidate n | context n | depth10 imbalance delta | thin-rate delta | total-depth delta | near/far delta | max bid wall delta | max ask wall delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for symbol, row in synth["candidate_context_by_symbol"].items():
        delta = row["candidate_minus_context"]
        lines.append(
            "| "
            f"{symbol} | {row['candidate']['n']} | {row['context']['n']} | "
            f"{_fmt(delta.get('event15_median_depth10_imbalance'))} | "
            f"{_fmt(delta.get('event15_thin_depth10_rate'))} | "
            f"{_fmt(delta.get('event15_median_total_depth10'))} | "
            f"{_fmt(delta.get('event15_median_near_far_ratio'))} | "
            f"{_fmt(delta.get('event15_median_max_bid_wall'))} | "
            f"{_fmt(delta.get('event15_median_max_ask_wall'))} |"
        )
    lines.extend(
        [
            "",
            "## Outcome By Symbol",
            "",
            "| Symbol | winner n | loser n | depth10 imbalance W-L | thin-rate W-L | total-depth W-L | near/far W-L | max bid wall W-L | max ask wall W-L |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for symbol, row in synth["outcome_by_symbol"].items():
        delta = row["winner_minus_loser"]
        lines.append(
            "| "
            f"{symbol} | {row['winner']['n']} | {row['loser']['n']} | "
            f"{_fmt(delta.get('event15_median_depth10_imbalance'))} | "
            f"{_fmt(delta.get('event15_thin_depth10_rate'))} | "
            f"{_fmt(delta.get('event15_median_total_depth10'))} | "
            f"{_fmt(delta.get('event15_median_near_far_ratio'))} | "
            f"{_fmt(delta.get('event15_median_max_bid_wall'))} | "
            f"{_fmt(delta.get('event15_median_max_ask_wall'))} |"
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
    payload = build_payload(mbp1.load_json(args.manifest), mbp1.load_json(args.fetch_plan), mbp1.load_json(args.outcome_join))
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"feature_rows={payload['synthesis']['feature_row_count']} status={payload['synthesis']['data_status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
