#!/usr/bin/env python3
"""Fetch CME futures research data from Databento.

Research/tooling only. This script never touches live trading logic. It loads
credentials from `.env` and `.env.local`, estimates billable size and cost
before any time-series fetch, and writes raw DBN output under ignored
`data/external/raw/databento/` by default.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.databento_futures import (  # noqa: E402
    DEFAULT_DATABENTO_DATASET,
    DEFAULT_DATABENTO_RAW_ROOT,
    DEFAULT_DATABENTO_SCHEMA,
    DEFAULT_DATABENTO_STYPE_IN,
    DEFAULT_DATABENTO_SYMBOLS,
    DatabentoRequest,
    DatabentoSetupError,
    databento_env_status,
    dataset_status,
    estimate_request,
    estimate_to_dict,
    fetch_request,
    historical_client,
    load_databento_env,
    parse_symbols,
    request_output_path,
)


def _print(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            print(f"{key}: {json.dumps(value, indent=2, sort_keys=True)}")
        else:
            print(f"{key}: {value}")


def build_request(args: argparse.Namespace) -> DatabentoRequest:
    return DatabentoRequest(
        dataset=args.dataset,
        schema=args.schema,
        symbols=parse_symbols(args.symbols),
        start=args.start,
        end=args.end,
        stype_in=args.stype_in,
        stype_out=args.stype_out,
        limit=args.limit,
    )


def cmd_status(args: argparse.Namespace) -> int:
    load_databento_env(PROJECT_ROOT)
    client = historical_client()
    payload = {
        "credentials_present": databento_env_status(),
        "databento": dataset_status(client, dataset=args.dataset),
    }
    _print(payload, as_json=args.json)
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    load_databento_env(PROJECT_ROOT)
    client = historical_client()
    request = build_request(args)
    estimate = estimate_request(client, request)
    payload = {
        "request": asdict(request),
        "output_path_if_fetched": str(request_output_path(request, args.root)),
        "estimate": estimate_to_dict(estimate),
    }
    _print(payload, as_json=args.json)
    return 0


def cmd_fetch(args: argparse.Namespace) -> int:
    load_databento_env(PROJECT_ROOT)
    client = historical_client()
    request = build_request(args)
    if args.dry_run:
        estimate = estimate_request(client, request)
        payload = {
            "dry_run": True,
            "request": asdict(request),
            "output_path_if_fetched": str(request_output_path(request, args.root)),
            "estimate": estimate_to_dict(estimate),
        }
        _print(payload, as_json=args.json)
        return 0

    result = fetch_request(
        client,
        request,
        root=args.root,
        max_cost_usd=args.max_cost_usd,
        force=args.force,
    )
    payload = {
        "dry_run": False,
        "request": asdict(result.request),
        "estimate": estimate_to_dict(result.estimate),
        "output_path": result.output_path,
        "metadata_path": result.metadata_path,
    }
    _print(payload, as_json=args.json)
    return 0


def add_request_args(parser: argparse.ArgumentParser, *, start_required: bool) -> None:
    parser.add_argument("--dataset", default=DEFAULT_DATABENTO_DATASET)
    parser.add_argument("--schema", default=DEFAULT_DATABENTO_SCHEMA)
    parser.add_argument(
        "--symbols",
        default=DEFAULT_DATABENTO_SYMBOLS,
        help=(
            "Comma-separated symbols, ALL_SYMBOLS, or a continuous symbol such "
            "as ES.v.0. Default: ES.v.0"
        ),
    )
    parser.add_argument("--stype-in", default=DEFAULT_DATABENTO_STYPE_IN)
    parser.add_argument("--stype-out")
    parser.add_argument("--start", required=start_required)
    parser.add_argument("--end")
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--root",
        default=str(DEFAULT_DATABENTO_RAW_ROOT),
        help="Ignored raw output root for fetches.",
    )
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show Databento dataset readiness")
    status.add_argument("--dataset", default=DEFAULT_DATABENTO_DATASET)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    estimate = sub.add_parser("estimate", help="Estimate records, bytes, and cost")
    add_request_args(estimate, start_required=True)
    estimate.set_defaults(func=cmd_estimate)

    fetch = sub.add_parser("fetch", help="Fetch raw DBN after passing cost cap")
    add_request_args(fetch, start_required=True)
    fetch.add_argument(
        "--max-cost-usd",
        type=float,
        default=0.25,
        help="Hard cap checked before fetch. Default: 0.25",
    )
    fetch.add_argument("--dry-run", action="store_true")
    fetch.add_argument("--force", action="store_true")
    fetch.set_defaults(func=cmd_fetch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except DatabentoSetupError as exc:
        parser.exit(2, f"setup error: {exc}\n")
    except Exception as exc:
        if os.getenv("GTOS_DATABENTO_DEBUG"):
            raise
        parser.exit(1, f"databento error: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
