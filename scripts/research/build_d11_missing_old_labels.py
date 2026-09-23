#!/usr/bin/env python3
"""Build D-11 missing old mechanical labels for GBPJPY and US30_cash.

Research/tooling only. This is a versioned supplement to the original
``data/historical_2022_2023/trade_cohort.*`` artifacts. It does not overwrite
the canonical five-symbol cohort and it does not touch live trading behavior.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.ob_zone_test import (  # noqa: E402
    BOSEvent,
    Outcome,
    extract_bos_events,
    find_ob_retest_outcome,
)

DEFAULT_SYMBOLS = ("GBPJPY", "US30_cash")
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data" / "historical"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "historical_2022_2023"
DEFAULT_LABEL_STEM = "trade_cohort_missing_symbols_2026-05-03"
DEFAULT_REPORT_JSON = (
    PROJECT_ROOT
    / "research"
    / "ml_program"
    / "audit"
    / "D11_MISSING_OLD_LABELS_REGENERATION_2026-05-03.json"
)
DEFAULT_REPORT_MD = (
    PROJECT_ROOT
    / "research"
    / "ml_program"
    / "audit"
    / "D11_MISSING_OLD_LABELS_REGENERATION_2026-05-03.md"
)
DEFAULT_REGIME_PATH = PROJECT_ROOT / "shadow_logs" / "structure_detector_backfill_2022_2023.jsonl"

START = dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc)
END = dt.datetime(2024, 2, 20, tzinfo=dt.timezone.utc)

K54_FIELDNAMES = [
    "trade_id",
    "source",
    "date_iso",
    "symbol",
    "instrument_class",
    "direction_long_short",
    "kill_zone",
    "hour_utc",
    "day_of_week",
    "framework",
    "setup_grade",
    "regime_tag",
    "counter_direction_flag",
    "ob_distance_atr",
    "ob_age_candles",
    "displacement_quality_score",
    "fvg_present",
    "touch_count",
    "ai_confidence",
    "walk_level_signal",
    "cross_instrument_xau_dir",
    "realized_r",
    "win_label",
]

INSTRUMENT_CLASS_MAP = {
    "GBPJPY": "fx",
    "US30_cash": "indices",
}


def normalize_symbol(symbol: str | None) -> str:
    text = str(symbol or "").strip()
    upper = text.upper()
    if upper in {"US30", "US30_CASH", "US30.CASH"}:
        return "US30_cash"
    return upper


def symbol_file_stem(symbol: str) -> str:
    return "US30_cash" if normalize_symbol(symbol) == "US30_cash" else normalize_symbol(symbol)


def kill_zone_from_hour(hour_utc: int) -> str:
    if 7 <= hour_utc < 12:
        return "london"
    if 13 <= hour_utc < 17:
        return "ny"
    if 0 <= hour_utc < 4:
        return "tokyo"
    return "other"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat()
    return value


def serialize_dataclass(obj: Any) -> dict[str, Any]:
    raw = asdict(obj)
    return {key: _json_safe(value) for key, value in raw.items()}


def load_regime_index(path: str | Path) -> dict[tuple[str, str], dict[str, Any]]:
    p = Path(path)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    if not p.exists():
        return out
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                symbol = normalize_symbol(payload.get("symbol"))
                ts = dt.datetime.fromisoformat(str(payload.get("ts")).replace("Z", "+00:00"))
            except Exception:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            ts = ts.astimezone(dt.timezone.utc)
            h4_hour = (ts.hour // 4) * 4
            h4_ts = ts.replace(hour=h4_hour, minute=0, second=0, microsecond=0).isoformat()
            out[(symbol, h4_ts)] = {
                "regime": payload.get("v2_direction") or payload.get("production_label"),
                "score": payload.get("v2_score"),
                "dead_zone": payload.get("v2_dead_zone"),
            }
    return out


def regime_lookup(regime_index: dict[tuple[str, str], dict[str, Any]], symbol: str, ts: dt.datetime | None) -> dict[str, Any]:
    if ts is None or not regime_index:
        return {"regime": None, "score": None, "dead_zone": None}
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    ts = ts.astimezone(dt.timezone.utc)
    symbol_key = normalize_symbol(symbol)
    for hours_back in (0, 4, 8, 12):
        probe = ts - dt.timedelta(hours=hours_back)
        h4_hour = (probe.hour // 4) * 4
        key = (symbol_key, probe.replace(hour=h4_hour, minute=0, second=0, microsecond=0).isoformat())
        if key in regime_index:
            return regime_index[key]
    return {"regime": None, "score": None, "dead_zone": None}


def bos_to_k54_row(bos: BOSEvent, outcome: Outcome, regime_index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    symbol = normalize_symbol(bos.symbol)
    bos_time = bos.bos_time
    ob_time = bos.ob_time
    ob_age = 0
    if bos_time and ob_time:
        ob_age = max(0, int((bos_time - ob_time).total_seconds() // (15 * 60)))

    ob_distance_atr = 0.0
    if outcome.entry is not None and bos.atr_at_bos and bos.ob_high is not None and bos.ob_low is not None:
        mid = (float(bos.ob_high) + float(bos.ob_low)) / 2.0
        ob_distance_atr = (float(outcome.entry) - mid) / float(bos.atr_at_bos)

    hour_utc = bos_time.hour if bos_time else -1
    regime = regime_lookup(regime_index, symbol, bos_time)
    counter_direction = 0
    if regime.get("regime"):
        label = str(regime["regime"])
        if (label == "bullish" and bos.direction == "SHORT") or (label == "bearish" and bos.direction == "LONG"):
            counter_direction = 1

    realized = outcome.realized_r
    return {
        "trade_id": outcome.bos_id or f"{symbol}|{bos_time.isoformat()}|d11_missing",
        "source": "f11_mechanical_d11_missing_old_labels",
        "date_iso": bos_time.isoformat() if bos_time else "",
        "symbol": symbol,
        "instrument_class": INSTRUMENT_CLASS_MAP.get(symbol, "other"),
        "direction_long_short": bos.direction,
        "kill_zone": kill_zone_from_hour(hour_utc) if hour_utc >= 0 else "other",
        "hour_utc": hour_utc,
        "day_of_week": bos_time.weekday() if bos_time else -1,
        "framework": "ob_retest",
        "setup_grade": "",
        "regime_tag": regime.get("regime") or "",
        "counter_direction_flag": counter_direction,
        "ob_distance_atr": ob_distance_atr,
        "ob_age_candles": ob_age,
        "displacement_quality_score": 0.5,
        "fvg_present": 0,
        "touch_count": 0,
        "ai_confidence": -1,
        "walk_level_signal": -1,
        "cross_instrument_xau_dir": "",
        "realized_r": float(realized) if realized is not None else "",
        "win_label": 1 if (realized is not None and float(realized) > 0) else 0,
    }


def build_missing_labels(
    *,
    source_dir: str | Path = DEFAULT_SOURCE_DIR,
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS,
    regime_path: str | Path = DEFAULT_REGIME_PATH,
) -> dict[str, Any]:
    src = Path(source_dir)
    regime_index = load_regime_index(regime_path)
    jsonl_rows: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    symbol_summaries: dict[str, dict[str, Any]] = {}

    for raw_symbol in symbols:
        symbol = normalize_symbol(raw_symbol)
        stem = symbol_file_stem(symbol)
        h1_path = src / f"{stem}_H1.csv"
        m15_path = src / f"{stem}_M15.csv"
        if not h1_path.exists() or not m15_path.exists():
            symbol_summaries[symbol] = {
                "status": "MISSING_SOURCE_CSV",
                "h1_path": str(h1_path),
                "m15_path": str(m15_path),
                "h1_exists": h1_path.exists(),
                "m15_exists": m15_path.exists(),
                "bos": 0,
                "filled": 0,
                "no_entry": 0,
                "skipped": 0,
            }
            continue

        bos_events = extract_bos_events(h1_path, symbol=symbol, start=START, end=END)
        summary = Counter()
        for bos in bos_events:
            outcome = find_ob_retest_outcome(bos, h1_path, m15_ohlcv_dir=src)
            jsonl_rows.append({"bos": serialize_dataclass(bos), "ob_retest": serialize_dataclass(outcome)})
            outcome_label = str(outcome.outcome or "")
            if outcome_label in {"TP", "SL", "TIMEOUT"}:
                summary["filled"] += 1
                csv_rows.append(bos_to_k54_row(bos, outcome, regime_index))
            elif outcome_label == "NO_ENTRY":
                summary["no_entry"] += 1
            else:
                summary["skipped"] += 1

        symbol_summaries[symbol] = {
            "status": "OK",
            "h1_path": str(h1_path),
            "m15_path": str(m15_path),
            "bos": len(bos_events),
            "filled": summary["filled"],
            "no_entry": summary["no_entry"],
            "skipped": summary["skipped"],
        }

    csv_rows.sort(key=lambda row: (row["date_iso"], row["symbol"], row["trade_id"]))
    return {
        "schema_version": "d11_missing_old_labels_v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "hypothesis_before_outputs": (
            "GBPJPY and US30_cash old mechanical labels can be regenerated from local "
            "data/historical OHLCV with the same F11-style BOS/OB-retest resolver, "
            "but must remain a versioned supplement with explicit source flags."
        ),
        "input_source_dir": str(src),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "symbols": list(symbols),
        "source_flags": {
            "source_period": "old_backfill_builder_window_2022-01-01_to_2024-02-20",
            "mechanical_vs_live_like": "mechanical_f11_ob_retest_filled_only",
            "label_type": "synthetic_mechanical_r",
            "as_of_policy": "local_static_ohlcv_no_external_fetch",
            "merge_policy": "supplement_do_not_overwrite_canonical_trade_cohort",
        },
        "symbol_summaries": symbol_summaries,
        "total_bos": sum(item["bos"] for item in symbol_summaries.values()),
        "total_filled": len(csv_rows),
        "total_jsonl_rows": len(jsonl_rows),
        "csv_rows": csv_rows,
        "jsonl_rows": jsonl_rows,
    }


def _without_rows(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.pop("csv_rows", None)
    out.pop("jsonl_rows", None)
    return out


def display_path(path: str | Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def render_markdown(payload: dict[str, Any], *, csv_path: Path, jsonl_path: Path) -> str:
    lines = [
        "# D-11 Missing Old Labels Regeneration",
        "",
        f"Generated: {payload['generated_at_utc']}",
        "Scope: research/tooling only",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "",
        "## Question Registered Before Output",
        "",
        payload["hypothesis_before_outputs"],
        "",
        "## Headline",
        "",
        "- Verdict: `DONE_SUPPLEMENT_GENERATED`.",
        "- GBPJPY and US30_cash labels were generated as a versioned supplement, not merged into the canonical five-symbol cohort.",
        f"- Supplemental CSV: `{display_path(csv_path)}`.",
        f"- Supplemental JSONL: `{display_path(jsonl_path)}`.",
        "",
        "## Source Flags",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for key, value in payload["source_flags"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend(
        [
            "",
            "## Symbol Summary",
            "",
            "| Symbol | Status | BOS | Filled | NO_ENTRY | Skipped | H1 Source | M15 Source |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for symbol, summary in payload["symbol_summaries"].items():
        lines.append(
            "| "
            + " | ".join(
                [
                    symbol,
                    summary["status"],
                    str(summary["bos"]),
                    str(summary["filled"]),
                    str(summary["no_entry"]),
                    str(summary["skipped"]),
                    display_path(summary["h1_path"]),
                    display_path(summary["m15_path"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- BOS rows: `{payload['total_bos']}`.",
            f"- Supplemental JSONL rows: `{payload['total_jsonl_rows']}`.",
            f"- Supplemental filled CSV rows: `{payload['total_filled']}`.",
            "",
            "## Use Constraints",
            "",
            "- These rows are synthetic mechanical labels, not broker-realized R and not live-equivalent AI outcomes.",
            "- Any future all-symbol training merge must carry `source_period` and `mechanical_vs_live_like` explicitly.",
            "- This report does not validate a trading rule, model, risk setting, prompt, or live filter.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    label_stem: str = DEFAULT_LABEL_STEM,
    report_json: str | Path = DEFAULT_REPORT_JSON,
    report_md: str | Path = DEFAULT_REPORT_MD,
    overwrite: bool = False,
) -> dict[str, Path]:
    out_dir = Path(output_dir)
    csv_path = out_dir / f"{label_stem}.csv"
    jsonl_path = out_dir / f"{label_stem}.jsonl"
    report_json_path = Path(report_json)
    report_md_path = Path(report_md)
    paths = {
        "csv": csv_path,
        "jsonl": jsonl_path,
        "report_json": report_json_path,
        "report_md": report_md_path,
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        existing_text = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing artifact(s): {existing_text}")

    out_dir.mkdir(parents=True, exist_ok=True)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in payload["jsonl_rows"]:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=K54_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(payload["csv_rows"])

    report_payload = _without_rows(payload)
    report_payload["outputs"] = {key: display_path(path) for key, path in paths.items()}
    report_json_path.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md_path.write_text(render_markdown(report_payload, csv_path=csv_path, jsonl_path=jsonl_path), encoding="utf-8")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--label-stem", default=DEFAULT_LABEL_STEM)
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    payload = build_missing_labels(source_dir=args.source_dir, symbols=tuple(args.symbols))
    paths = write_outputs(
        payload,
        output_dir=args.output_dir,
        label_stem=args.label_stem,
        report_json=args.report_json,
        report_md=args.report_md,
        overwrite=args.overwrite,
    )
    print(f"Wrote {paths['csv']}")
    print(f"Wrote {paths['jsonl']}")
    print(f"Wrote {paths['report_json']}")
    print(f"Wrote {paths['report_md']}")
    print(f"Supplemental filled rows: {payload['total_filled']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
