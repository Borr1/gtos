#!/usr/bin/env python3
"""Build descriptor-only primitives from source-bound Sierra SCID M15 bars."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

BAR_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_SOURCE_BOUND_BAR_LEDGER_{STAMP}.jsonl"
RESULT_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_FACTORY_RESULT_{STAMP}.json"
EVENT_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_EVENT_LEDGER_{STAMP}.jsonl"
BASELINE_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_BASELINE_LEDGER_{STAMP}.jsonl"
FLAG_SUMMARY_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_FLAG_SUMMARY_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_SCID_M15_PRIMITIVE_FACTORY_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra SCID M15 primitive descriptors only; no target movement, strategy "
    "validation, trade outcome, R/PnL, expectancy, live-readiness, or promotion"
)

FEATURES = [
    "price_change",
    "abs_price_change",
    "price_range",
    "body_abs",
    "upper_wick",
    "lower_wick",
    "volume",
    "num_trades",
    "delta",
    "abs_delta",
    "delta_ratio",
    "close_location",
    "source_records",
]
QUANTILES = [0.1, 0.2, 0.5, 0.8, 0.9, 0.95]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def append_jsonl(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def session_bucket(ts: pd.Timestamp) -> str:
    minute = int(ts.hour) * 60 + int(ts.minute)
    if 0 <= minute < 3 * 60:
        return "tokyo_core_0000_0300"
    if 7 * 60 <= minute < 10 * 60 + 30:
        return "london_core_0700_1030"
    if 13 * 60 <= minute < 17 * 60:
        return "ny_core_1300_1700"
    return "off_core_session"


def safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["bar_start_utc"] = pd.to_datetime(df["bar_start_utc"], utc=True)
    df["bar_end_exclusive_utc"] = pd.to_datetime(df["bar_end_exclusive_utc"], utc=True)
    for col in ("open", "high", "low", "close", "volume", "num_trades", "bid_volume", "ask_volume", "source_records"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["price_change"] = df["close"] - df["open"]
    df["abs_price_change"] = df["price_change"].abs()
    df["price_range"] = (df["high"] - df["low"]).clip(lower=0.0)
    df["body_abs"] = df["abs_price_change"]
    df["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)).clip(lower=0.0)
    df["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]).clip(lower=0.0)
    df["delta"] = df["ask_volume"] - df["bid_volume"]
    df["abs_delta"] = df["delta"].abs()
    df["volume_safe"] = df["volume"].where(df["volume"] > 0, 1.0)
    df["delta_ratio"] = df["delta"] / df["volume_safe"]
    df["close_location"] = None
    mask = df["price_range"] > 0
    df.loc[mask, "close_location"] = (df.loc[mask, "close"] - df.loc[mask, "low"]) / df.loc[mask, "price_range"]
    df["session_bucket"] = df["bar_start_utc"].map(session_bucket)
    df.sort_values(["source_symbol", "bar_start_utc"], inplace=True)
    df["source_gap_minutes"] = (
        df.groupby("source_symbol")["bar_start_utc"].diff().dt.total_seconds().div(60).fillna(15.0)
    )
    return df


def quantile_map(group: pd.DataFrame) -> dict[str, dict[float, float | None]]:
    out: dict[str, dict[float, float | None]] = {}
    for feature in FEATURES:
        series = pd.to_numeric(group[feature], errors="coerce").dropna()
        out[feature] = {
            q: safe_float(series.quantile(q)) if len(series) else None
            for q in QUANTILES
        }
    return out


def build_baseline_rows(df: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, dict[float, float | None]]]]:
    rows: list[dict[str, Any]] = []
    lookup: dict[tuple[str, str], dict[str, dict[float, float | None]]] = {}
    for (symbol, session), group in df.groupby(["source_symbol", "session_bucket"], sort=True):
        qmap = quantile_map(group)
        lookup[(str(symbol), str(session))] = qmap
        rows.append(
            {
                "route_id": ROUTE_ID,
                "source_symbol": symbol,
                "session_bucket": session,
                "n_bars": int(len(group)),
                "feature_quantiles": {
                    feature: {str(q): value for q, value in qvalues.items()}
                    for feature, qvalues in qmap.items()
                },
                "baseline_scope": "same_source_symbol_session_full_distribution_descriptor_only",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows, lookup


def ge(value: Any, threshold: Any) -> bool:
    left = safe_float(value)
    right = safe_float(threshold)
    return left is not None and right is not None and left >= right


def le(value: Any, threshold: Any) -> bool:
    left = safe_float(value)
    right = safe_float(threshold)
    return left is not None and right is not None and left <= right


def primitive_flags(row: Any, qmap: dict[str, dict[float, float | None]]) -> list[str]:
    flags: list[str] = []
    if ge(row.price_range, qmap["price_range"][0.9]):
        flags.append("range_p90")
    if ge(row.price_range, qmap["price_range"][0.95]):
        flags.append("range_p95")
    if ge(row.body_abs, qmap["body_abs"][0.9]):
        flags.append("body_p90")
    if ge(row.volume, qmap["volume"][0.9]):
        flags.append("volume_p90")
    if ge(row.num_trades, qmap["num_trades"][0.9]):
        flags.append("num_trades_p90")
    if ge(row.abs_delta, qmap["abs_delta"][0.9]):
        flags.append("abs_delta_p90")
    if ge(row.delta_ratio, qmap["delta_ratio"][0.8]):
        flags.append("ask_volume_dominant_p80")
    if le(row.delta_ratio, qmap["delta_ratio"][0.2]):
        flags.append("bid_volume_dominant_p20")
    if row.price_range > 0:
        upper_wick_ratio = row.upper_wick / row.price_range
        lower_wick_ratio = row.lower_wick / row.price_range
        if upper_wick_ratio >= 0.6 and ge(row.price_range, qmap["price_range"][0.8]):
            flags.append("upper_wick_rejection_range_p80")
        if lower_wick_ratio >= 0.6 and ge(row.price_range, qmap["price_range"][0.8]):
            flags.append("lower_wick_rejection_range_p80")
    if ge(row.close_location, 0.8) and ge(row.price_range, qmap["price_range"][0.8]):
        flags.append("close_near_high_range_p80")
    if le(row.close_location, 0.2) and ge(row.price_range, qmap["price_range"][0.8]):
        flags.append("close_near_low_range_p80")
    price_sign = 1 if row.price_change > 0 else -1 if row.price_change < 0 else 0
    delta_sign = 1 if row.delta > 0 else -1 if row.delta < 0 else 0
    if (
        price_sign
        and delta_sign
        and price_sign != delta_sign
        and ge(row.abs_delta, qmap["abs_delta"][0.8])
        and ge(row.body_abs, qmap["body_abs"][0.5])
    ):
        flags.append("price_delta_divergence_active")
    if safe_float(row.source_gap_minutes) is not None and float(row.source_gap_minutes) > 15.0:
        flags.append("post_source_gap_first_bar")
    return flags


def build_event_rows(df: pd.DataFrame, baseline_lookup: dict[tuple[str, str], dict[str, dict[float, float | None]]]) -> tuple[int, Counter[str]]:
    flag_counts: Counter[str] = Counter()
    rows_written = 0
    with EVENT_LEDGER.open("w", encoding="utf-8") as handle:
        for row in df.itertuples(index=False):
            qmap = baseline_lookup[(str(row.source_symbol), str(row.session_bucket))]
            flags = primitive_flags(row, qmap)
            flag_counts.update(flags)
            event = {
                "route_id": ROUTE_ID,
                "source_symbol": row.source_symbol,
                "bar_start_utc": row.bar_start_utc.isoformat().replace("+00:00", "Z"),
                "bar_end_exclusive_utc": row.bar_end_exclusive_utc.isoformat().replace("+00:00", "Z"),
                "session_bucket": row.session_bucket,
                "open": safe_float(row.open),
                "high": safe_float(row.high),
                "low": safe_float(row.low),
                "close": safe_float(row.close),
                "price_change": safe_float(row.price_change),
                "abs_price_change": safe_float(row.abs_price_change),
                "price_range": safe_float(row.price_range),
                "body_abs": safe_float(row.body_abs),
                "upper_wick": safe_float(row.upper_wick),
                "lower_wick": safe_float(row.lower_wick),
                "volume": safe_float(row.volume),
                "num_trades": safe_float(row.num_trades),
                "bid_volume": safe_float(row.bid_volume),
                "ask_volume": safe_float(row.ask_volume),
                "delta": safe_float(row.delta),
                "abs_delta": safe_float(row.abs_delta),
                "delta_ratio": safe_float(row.delta_ratio),
                "close_location": safe_float(row.close_location),
                "source_records": safe_float(row.source_records),
                "source_gap_minutes": safe_float(row.source_gap_minutes),
                "primitive_flags": flags,
                "primitive_flag_count": len(flags),
                "source_audit_key": row.source_audit_key,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
            append_jsonl(handle, event)
            rows_written += 1
    return rows_written, flag_counts


def build_flag_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    summary: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {"bars": 0, "flagged": 0})
    for row in pd.read_json(EVENT_LEDGER, lines=True, chunksize=50_000):
        for event in row.itertuples(index=False):
            key_base = (str(event.source_symbol), str(event.session_bucket))
            flags = event.primitive_flags if isinstance(event.primitive_flags, list) else []
            all_key = (*key_base, "__ALL_BARS__")
            summary[all_key]["bars"] += 1
            for flag in flags:
                summary[(*key_base, str(flag))]["flagged"] += 1
            for flag_key in list(summary):
                if flag_key[0] == key_base[0] and flag_key[1] == key_base[1] and flag_key[2] != "__ALL_BARS__":
                    summary[flag_key]["bars"] = summary[all_key]["bars"]
    rows: list[dict[str, Any]] = []
    for (symbol, session, flag), values in sorted(summary.items()):
        if flag == "__ALL_BARS__":
            continue
        bars = int(values.get("bars") or 0)
        flagged = int(values.get("flagged") or 0)
        rows.append(
            {
                "route_id": ROUTE_ID,
                "source_symbol": symbol,
                "session_bucket": session,
                "primitive_flag": flag,
                "n_bars": bars,
                "flagged_bars": flagged,
                "flag_rate": flagged / bars if bars else None,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def build_question_rows(flag_summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flags = sorted({row["primitive_flag"] for row in flag_summary_rows})
    rows: list[dict[str, Any]] = []
    for flag in flags:
        rows.append(
            {
                "route_id": ROUTE_ID,
                "primitive_flag": flag,
                "question": "Does this Sierra futures proxy primitive carry residual forward movement after same-symbol/session controls?",
                "next_action": "Build a source-bound target movement/control packet by horizon using the Sierra SCID M15 bar ledger.",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
        rows.append(
            {
                "route_id": ROUTE_ID,
                "primitive_flag": flag,
                "question": "Is this primitive a tradable entry descriptor, an avoid filter, a timing filter, or generic activity?",
                "next_action": "Compare flagged bars to denominator bars, neighbor placebo bars, and cross-source Route C tick primitives before assigning system role.",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_scid_m15_primitive_factory_builder", "created"),
        (RESULT_PATH, "sierra_scid_m15_primitive_factory_result", "created"),
        (EVENT_LEDGER, "sierra_scid_m15_primitive_event_ledger", "created"),
        (BASELINE_LEDGER, "sierra_scid_m15_primitive_baseline_ledger", "created"),
        (FLAG_SUMMARY_LEDGER, "sierra_scid_m15_primitive_flag_summary_ledger", "created"),
        (QUESTION_LEDGER, "sierra_scid_m15_primitive_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_scid_m15_primitive_factory_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], flag_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_scid_m15_primitive_factory",
        "status": "done",
        "route": "sierra_source_contract_repair",
        "details": (
            "Built descriptor-only primitives over every source-bound Sierra SCID M15 bar. "
            "This opens target/control work but makes no outcome or promotion claim."
        ),
        "counts": counts,
        "flag_counts": flag_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(EVENT_LEDGER),
            relative(BASELINE_LEDGER),
            relative(FLAG_SUMMARY_LEDGER),
            relative(QUESTION_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], flag_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra SCID M15 Primitive Factory",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: primitive descriptors only. No target movement, strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Flag Counts", ""])
    for key, value in sorted(flag_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Same-Resource Work",
            "",
            "- Build same-symbol/session/horizon target movement controls from the Sierra M15 bar ledger.",
            "- Add neighbor-placebo and source-gap controls before interpreting any primitive as residual.",
            "- Compare Sierra futures proxy primitive families against existing Route C tick primitives.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    df = pd.read_json(BAR_LEDGER, lines=True)
    df = build_features(df)
    baseline_rows, baseline_lookup = build_baseline_rows(df)
    event_rows_written, flag_counts = build_event_rows(df, baseline_lookup)
    flag_summary_rows = build_flag_summary(df)
    question_rows = build_question_rows(flag_summary_rows)
    write_jsonl(BASELINE_LEDGER, baseline_rows)
    write_jsonl(FLAG_SUMMARY_LEDGER, flag_summary_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)

    counts = {
        "input_m15_bar_rows": int(len(df)),
        "primitive_event_rows": event_rows_written,
        "baseline_rows": len(baseline_rows),
        "flag_summary_rows": len(flag_summary_rows),
        "question_rows": len(question_rows),
        "source_symbols": int(df["source_symbol"].nunique()),
        "session_buckets": int(df["session_bucket"].nunique()),
        "bars_with_any_flag": int(sum(flag_counts.values() > 0 for _ in [])),
    }
    bars_with_flag = 0
    for chunk in pd.read_json(EVENT_LEDGER, lines=True, chunksize=50_000):
        bars_with_flag += int((chunk["primitive_flag_count"] > 0).sum())
    counts["bars_with_any_flag"] = bars_with_flag

    result = {
        "schema": "sierra_scid_m15_primitive_factory_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SCID_M15_PRIMITIVE_DESCRIPTOR_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "primitive_flag_counts": dict(sorted(flag_counts.items())),
        "feature_family": FEATURES,
        "next_same_resource_work": [
            "build source-bound target movement/control packet by horizon",
            "add neighbor placebo and source-gap controls",
            "compare Sierra futures proxy primitive families against Route C tick primitives",
        ],
        "not_completion": "This creates descriptors for downstream controls; it does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(generated_utc, counts, dict(flag_counts))
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(flag_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
