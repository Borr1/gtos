#!/usr/bin/env python3
"""Fetch Phase 3 external free feeds into the shadow cache.

This is a data-ingestion utility only. It writes under ``data/external`` by
default and does not connect to, import, or mutate live trading components.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:  # pragma: no cover - operator convenience
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    load_dotenv(PROJECT_ROOT / ".env.local", override=True)
except ImportError:  # pragma: no cover
    pass

from src.components.external_feeds import (  # noqa: E402
    CftcCotFeed,
    DEFAULT_EXTERNAL_DATA_ROOT,
    ExternalFeedError,
    ExternalFeedStore,
    FlashAlphaGexFeed,
    FredFeed,
    LbmaFixCalendar,
    FeedStatus,
    WgcGoldhubImport,
    date_to_utc,
    safe_slug,
    utc_now,
)


CFTC_DATASET_ALIASES = {
    "disagg_combined": (CftcCotFeed.DISAGG_COMBINED, "disagg_combined"),
    "disagg_futures_only": (
        CftcCotFeed.DISAGG_FUTURES_ONLY,
        "disagg_futures_only",
    ),
    "tff_futures_only": (CftcCotFeed.TFF_FUTURES_ONLY, "tff_futures_only"),
}

DEFAULT_CFTC_CONTRACTS = {
    "088691": "XAUUSD",  # COMEX gold; verified in existing session9 COT scripts.
}

DEFAULT_FRED_SERIES = (
    "DGS10",
    "DGS2",
    "DFII10",
    "T10YIE",
    "VIXCLS",
    "GVZCLS",
    "DTWEXBGS",
)
DEFAULT_EXTERNAL_FEED_HISTORY_START = "2022-01-01"
DEFAULT_FLASHALPHA_PROXIES = (
    "QQQ:NAS100",
    "DIA:US30",
    "SPY:US30",
    "GLD:XAUUSD",
    "SLV:XAGUSD",
)
DAILY_FETCH_STEPS = ("fred", "cftc", "lbma_calendar", "flashalpha_gex", "wgc")


def next_monthly_options_expiration(today: date | None = None) -> date:
    current = today or date.today()
    expiration = _third_friday(current.year, current.month)
    if current > expiration:
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        expiration = _third_friday(year, month)
    return expiration


def _third_friday(year: int, month: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != 4:
        current += timedelta(days=1)
    return current + timedelta(days=14)


def parse_contract_map(items: list[str] | None) -> dict[str, str]:
    mapping = dict(DEFAULT_CFTC_CONTRACTS)
    for item in items or []:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"contract mapping must be CODE:SYMBOL, got {item!r}"
            )
        code, symbol = item.split(":", 1)
        mapping[code.strip()] = symbol.strip().upper()
    return mapping


def parse_proxy_map(items: list[str] | None) -> list[tuple[str, str]]:
    raw_items = items or list(DEFAULT_FLASHALPHA_PROXIES)
    proxies: list[tuple[str, str]] = []
    for item in raw_items:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"proxy mapping must be PROXY:GTOS_SYMBOL, got {item!r}"
            )
        proxy, symbol = item.split(":", 1)
        proxies.append((proxy.strip().upper(), symbol.strip().upper()))
    return proxies


def parse_metals(value: str) -> tuple[str, ...]:
    return tuple(part.strip().lower() for part in value.split(",") if part.strip())


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external)",
    )


def cmd_fred(args: argparse.Namespace) -> int:
    store = ExternalFeedStore(args.root)
    feed = FredFeed(store)
    series_ids = args.series or list(DEFAULT_FRED_SERIES)
    total_rows = 0
    for series_id in series_ids:
        rows = feed.fetch_series(
            safe_slug(series_id.upper()),
            start_date=args.start,
            end_date=args.end,
        )
        total_rows += len(rows)
        print(f"fred {series_id}: {len(rows)} rows")
    print(f"fred total: {total_rows} rows")
    return 0


def cmd_cftc(args: argparse.Namespace) -> int:
    dataset_id, report_type = CFTC_DATASET_ALIASES[args.dataset]
    contract_map = parse_contract_map(args.contract)
    store = ExternalFeedStore(args.root)
    feed = CftcCotFeed(store)
    rows = feed.fetch_dataset(
        dataset_id=dataset_id,
        report_type=report_type,
        contract_map=contract_map,
        where=args.where,
        limit=args.limit,
    )
    print(f"cftc {report_type}: {len(rows)} mapped rows")
    return 0


def cmd_lbma_calendar(args: argparse.Namespace) -> int:
    store = ExternalFeedStore(args.root)
    rows = LbmaFixCalendar.generate(
        args.start,
        args.end,
        metals=parse_metals(args.metals),
    )
    fetched_at = utc_now()
    store.write_normalized_rows(
        "lbma_calendar",
        "fix_calendar",
        rows,
        fetched_at_utc=fetched_at,
    )
    latest = max(date_to_utc(row["trading_date_london"]) for row in rows)
    store.write_status(
        FeedStatus(
            source="lbma_calendar",
            status_key="fix_calendar",
            status="fresh",
            fetched_at_utc=fetched_at,
            latest_observation_utc=latest,
            latest_publication_utc=fetched_at,
            row_count=len(rows),
            message=f"Generated LBMA calendar {args.start} to {args.end}",
        )
    )
    print(f"lbma_calendar: {len(rows)} rows")
    return 0


def cmd_flashalpha(args: argparse.Namespace) -> int:
    store = ExternalFeedStore(args.root)
    feed = FlashAlphaGexFeed(store)
    total = 0
    for proxy_symbol, gtos_symbol in parse_proxy_map(args.proxy):
        row = feed.fetch_gex(
            proxy_symbol,
            gtos_symbol=gtos_symbol,
            expiration=args.expiration,
        )
        total += 1
        print(
            f"flashalpha {proxy_symbol}->{gtos_symbol}: "
            f"expiration={row['expiration']} as_of={row['as_of_utc']} "
            f"net_gex={row['net_gex']}"
        )
    print(f"flashalpha total: {total} snapshots")
    return 0


def cmd_wgc_import(args: argparse.Namespace) -> int:
    store = ExternalFeedStore(args.root)
    importer = WgcGoldhubImport(store)
    rows = importer.import_file(
        args.file,
        dataset=args.dataset,
        default_gtos_symbol=args.symbol,
    )
    print(f"wgc {args.dataset}: imported {len(rows)} rows from {args.file}")
    return 0


def cmd_daily(args: argparse.Namespace) -> int:
    """Run the approved shadow-only daily refresh sequence."""

    store = ExternalFeedStore(args.root)
    summary: list[dict[str, Any]] = []
    skipped = set(args.skip or ())
    had_error = False

    def record(
        step: str,
        status: str,
        *,
        rows: int = 0,
        message: str = "",
        extra: dict[str, Any] | None = None,
    ) -> None:
        summary.append(
            {
                "step": step,
                "status": status,
                "rows": rows,
                "message": message,
                "extra": extra or {},
            }
        )

    def run_step(step: str, action) -> None:
        nonlocal had_error
        if step in skipped:
            record(step, "skipped", message="operator skipped")
            return
        try:
            action()
        except (ExternalFeedError, OSError, ValueError) as exc:
            had_error = True
            record(step, "error", message=str(exc))
            if args.fail_fast:
                raise

    def fetch_fred() -> None:
        feed = FredFeed(store)
        total = 0
        series_ids = args.fred_series or list(DEFAULT_FRED_SERIES)
        for series_id in series_ids:
            rows = feed.fetch_series(
                safe_slug(series_id.upper()),
                start_date=args.fred_start,
                end_date=args.end,
            )
            total += len(rows)
        record(
            "fred",
            "ok",
            rows=total,
            message=f"Fetched {len(series_ids)} frozen macro series",
            extra={"series": series_ids},
        )

    def fetch_cftc() -> None:
        dataset_id, report_type = CFTC_DATASET_ALIASES[args.cftc_dataset]
        rows = CftcCotFeed(store).fetch_dataset(
            dataset_id=dataset_id,
            report_type=report_type,
            contract_map=parse_contract_map(args.contract),
            where=args.cftc_where,
            limit=args.cftc_limit,
        )
        record(
            "cftc",
            "ok",
            rows=len(rows),
            message=f"Fetched CFTC {report_type}",
            extra={"dataset": args.cftc_dataset},
        )

    def fetch_lbma() -> None:
        start = date.fromisoformat(args.lbma_start) if args.lbma_start else date.today()
        end = start + timedelta(days=args.lbma_days)
        rows = LbmaFixCalendar.generate(
            start,
            end,
            metals=parse_metals(args.lbma_metals),
        )
        fetched_at = utc_now()
        store.write_normalized_rows(
            "lbma_calendar",
            "fix_calendar",
            rows,
            fetched_at_utc=fetched_at,
        )
        latest = max(date_to_utc(row["trading_date_london"]) for row in rows)
        store.write_status(
            FeedStatus(
                source="lbma_calendar",
                status_key="fix_calendar",
                status="fresh",
                fetched_at_utc=fetched_at,
                latest_observation_utc=latest,
                latest_publication_utc=fetched_at,
                row_count=len(rows),
                message=f"Generated LBMA calendar {start.isoformat()} to {end.isoformat()}",
                extra={
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "metals": parse_metals(args.lbma_metals),
                },
            )
        )
        record(
            "lbma_calendar",
            "ok",
            rows=len(rows),
            message="Generated LBMA fix calendar",
        )

    def fetch_flashalpha() -> None:
        feed = FlashAlphaGexFeed(store)
        proxies = parse_proxy_map(args.proxy)
        for proxy_symbol, gtos_symbol in proxies:
            feed.fetch_gex(
                proxy_symbol,
                gtos_symbol=gtos_symbol,
                expiration=args.expiration,
            )
        record(
            "flashalpha_gex",
            "ok",
            rows=len(proxies),
            message="Fetched single-expiry GEX proxies",
            extra={
                "expiration": args.expiration,
                "proxies": [f"{proxy}:{symbol}" for proxy, symbol in proxies],
            },
        )

    run_step("fred", fetch_fred)
    run_step("cftc", fetch_cftc)
    run_step("lbma_calendar", fetch_lbma)
    run_step("flashalpha_gex", fetch_flashalpha)
    if "wgc" in skipped:
        record("wgc", "skipped", message="operator skipped")
    else:
        record(
            "wgc",
            "operator_required",
            message="WGC workbook imports remain operator-triggered via wgc-import",
        )

    if args.json:
        print(json.dumps({"root": str(Path(args.root)), "steps": summary}, indent=2))
    else:
        print(f"External feed daily fetch root: {Path(args.root)}")
        for item in summary:
            print(
                f"{item['step']}: {item['status']} rows={item['rows']} "
                f"message={item['message']}"
            )
    return 1 if had_error else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    fred = sub.add_parser("fred", help="Fetch FRED series observations")
    add_common_args(fred)
    fred.add_argument("--series", action="append", help="FRED series ID")
    fred.add_argument("--start", help="Observation start YYYY-MM-DD")
    fred.add_argument("--end", help="Observation end YYYY-MM-DD")
    fred.set_defaults(func=cmd_fred)

    cftc = sub.add_parser("cftc", help="Fetch CFTC COT rows")
    add_common_args(cftc)
    cftc.add_argument(
        "--dataset",
        choices=sorted(CFTC_DATASET_ALIASES),
        default="disagg_combined",
    )
    cftc.add_argument(
        "--contract",
        action="append",
        help="Contract mapping CODE:GTOS_SYMBOL; default includes 088691:XAUUSD",
    )
    cftc.add_argument("--where", help="Optional Socrata $where clause")
    cftc.add_argument("--limit", type=int, default=50_000)
    cftc.set_defaults(func=cmd_cftc)

    lbma = sub.add_parser("lbma-calendar", help="Generate LBMA fix calendar")
    add_common_args(lbma)
    default_start = date.today().replace(month=1, day=1)
    default_end = default_start + timedelta(days=370)
    lbma.add_argument("--start", default=default_start.isoformat())
    lbma.add_argument("--end", default=default_end.isoformat())
    lbma.add_argument("--metals", default="gold,silver")
    lbma.set_defaults(func=cmd_lbma_calendar)

    flashalpha = sub.add_parser(
        "flashalpha-gex",
        help="Fetch FlashAlpha GEX proxy snapshots",
    )
    add_common_args(flashalpha)
    flashalpha.add_argument(
        "--proxy",
        action="append",
        help="Proxy mapping PROXY:GTOS_SYMBOL; default QQQ:NAS100, DIA:US30, SPY:US30",
    )
    flashalpha.add_argument(
        "--expiration",
        default=next_monthly_options_expiration().isoformat(),
        help="Single option expiry YYYY-MM-DD; Basic plan requires this",
    )
    flashalpha.set_defaults(func=cmd_flashalpha)

    wgc = sub.add_parser(
        "wgc-import",
        help="Import operator-downloaded WGC Goldhub CSV/XLSX into the shadow cache",
    )
    add_common_args(wgc)
    wgc.add_argument("--file", required=True, help="Path to downloaded WGC CSV/XLSX")
    wgc.add_argument(
        "--dataset",
        required=True,
        help="Dataset slug, e.g. gold_etf_flows or central_bank_demand",
    )
    wgc.add_argument("--symbol", default="XAUUSD", help="GTOS symbol for as-of joins")
    wgc.set_defaults(func=cmd_wgc_import)

    daily = sub.add_parser(
        "daily",
        help="Run the approved shadow-only daily fetch sequence",
    )
    add_common_args(daily)
    daily.add_argument(
        "--fred-series",
        action="append",
        help="FRED series ID; repeatable. Default uses the frozen macro list.",
    )
    daily.add_argument(
        "--fred-start",
        default=DEFAULT_EXTERNAL_FEED_HISTORY_START,
        help="FRED observation start YYYY-MM-DD (default: 2022-01-01)",
    )
    daily.add_argument("--end", help="Optional observation end YYYY-MM-DD")
    daily.add_argument(
        "--cftc-dataset",
        choices=sorted(CFTC_DATASET_ALIASES),
        default="disagg_combined",
    )
    daily.add_argument(
        "--contract",
        action="append",
        help="CFTC contract mapping CODE:GTOS_SYMBOL; default includes 088691:XAUUSD",
    )
    daily.add_argument("--cftc-where", help="Optional Socrata $where clause")
    daily.add_argument("--cftc-limit", type=int, default=50_000)
    daily.add_argument("--lbma-start", help="LBMA calendar start YYYY-MM-DD")
    daily.add_argument("--lbma-days", type=int, default=370)
    daily.add_argument("--lbma-metals", default="gold,silver")
    daily.add_argument(
        "--proxy",
        action="append",
        help=(
            "FlashAlpha proxy mapping PROXY:GTOS_SYMBOL; default "
            "QQQ/DIA/SPY/GLD/SLV"
        ),
    )
    daily.add_argument(
        "--expiration",
        default=next_monthly_options_expiration().isoformat(),
        help="Single option expiry YYYY-MM-DD; Basic plan requires this",
    )
    daily.add_argument(
        "--skip",
        action="append",
        choices=DAILY_FETCH_STEPS,
        help="Skip a daily step; repeatable.",
    )
    daily.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first failed source instead of continuing the report.",
    )
    daily.add_argument("--json", action="store_true", help="Emit JSON summary.")
    daily.set_defaults(func=cmd_daily)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
