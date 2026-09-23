#!/usr/bin/env python3
"""Run a Databento Live shadow collector.

This process is shadow-only. It subscribes to Databento Live when explicitly
enabled and appends raw/normalized live records to
``shadow_logs/databento_live_confluence.jsonl``. It does not interact with MT5,
orders, risk, prompts, or live trade decisions.

Network/cost guard:
  Set ``GTOS_DATABENTO_LIVE_SHADOW_ENABLED=1`` and ``DATABENTO_API_KEY`` before
  running without ``--dry-run``. Otherwise the script writes a status row and
  exits without connecting.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.databento_live_shadow import (  # noqa: E402
    DEFAULT_BUDGET_LOG_PATH,
    DEFAULT_LOG_PATH,
    GTOS_TO_DATABENTO,
    append_budget_row,
    append_live_row,
    build_budget_ledger_row,
    build_live_status_row,
    evaluate_live_trigger_policy,
    load_budget_rows,
    normalize_record,
    schema_feature_class,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", default="NAS100")
    parser.add_argument("--schemas", default="trades,mbp-10")
    parser.add_argument("--dataset", default="GLBX.MDP3")
    parser.add_argument("--output", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--budget-log", default=str(DEFAULT_BUDGET_LOG_PATH))
    parser.add_argument("--trigger-id")
    parser.add_argument("--source-candidate-id")
    parser.add_argument("--reason")
    parser.add_argument("--source-opportunity-id")
    parser.add_argument("--asof-cutoff-utc")
    parser.add_argument("--window-start-utc")
    parser.add_argument("--window-end-utc")
    parser.add_argument("--signal-use-case", default="LIVE_CANDIDATE_ORDERFLOW_CONFLUENCE")
    parser.add_argument("--estimated-cost-usd", type=float, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument(
        "--max-records",
        type=int,
        default=5000,
        help="Stop after this many live records per GTOS symbol; must stay within the policy cap.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = Path(args.output)
    budget_log = Path(args.budget_log)
    symbols = [item.strip() for item in args.symbols.split(",") if item.strip()]
    schemas = [item.strip() for item in args.schemas.split(",") if item.strip()]
    trigger_id = args.trigger_id or ("manual_dry_run" if args.dry_run else None)
    reason = args.reason or ("dry-run policy evaluation; no paid fetch" if args.dry_run else None)
    policy_decision = evaluate_live_trigger_policy(
        symbols=symbols,
        schemas=schemas,
        trigger_id=trigger_id,
        reason=reason,
        estimated_cost_usd=args.estimated_cost_usd,
        timeout_seconds=args.timeout_seconds,
        max_records=args.max_records,
        env=os.environ,
        budget_rows=load_budget_rows(budget_log),
    )

    status = (
        "DRY_RUN_OR_DISABLED"
        if args.dry_run and not policy_decision["live_fetch_allowed"]
        else policy_decision["trigger_status"]
    )
    append_live_row(
        build_live_status_row(
            status=status,
            trigger_id=trigger_id,
            source_candidate_id=args.source_candidate_id,
            source_opportunity_id=args.source_opportunity_id,
            asof_cutoff_utc=args.asof_cutoff_utc,
            window_start_utc=args.window_start_utc,
            window_end_utc=args.window_end_utc,
            signal_use_case=args.signal_use_case,
            dataset=args.dataset,
            schema=",".join(schemas),
            policy_decision=policy_decision,
            feature_class=",".join(policy_decision.get("feature_classes") or []),
            message=(
                f"dry_run={args.dry_run} decision={policy_decision['decision']} "
                f"trigger_status={policy_decision['trigger_status']} symbols={symbols} schemas={schemas}"
            ),
        ),
        output,
    )
    if args.dry_run or not policy_decision["live_fetch_allowed"]:
        append_budget_row(
            build_budget_ledger_row(
                budget_status=(
                    "BUDGET_NOT_RESERVED_DRY_RUN"
                    if args.dry_run
                    else "BUDGET_NOT_RESERVED_POLICY_BLOCKED"
                ),
                policy_decision=policy_decision,
            ),
            budget_log,
        )
        print(policy_decision["trigger_status"])
        return 0

    import databento as db  # type: ignore

    append_budget_row(
        build_budget_ledger_row(
            budget_status="BUDGET_RESERVED",
            policy_decision=policy_decision,
        ),
        budget_log,
    )

    clients = []
    final_budget_status = "LIVE_SESSION_CLOSED_ACTUAL_COST_UNKNOWN"
    exit_code = 0
    try:
        for gtos_symbol in symbols:
            mapping = GTOS_TO_DATABENTO.get(gtos_symbol)
            if not mapping:
                append_live_row(
                    build_live_status_row(
                        status="NO_SYMBOL_MAPPING",
                        gtos_symbol=gtos_symbol,
                        dataset=args.dataset,
                        trigger_id=trigger_id,
                        source_candidate_id=args.source_candidate_id,
                        source_opportunity_id=args.source_opportunity_id,
                        asof_cutoff_utc=args.asof_cutoff_utc,
                        window_start_utc=args.window_start_utc,
                        window_end_utc=args.window_end_utc,
                        signal_use_case=args.signal_use_case,
                        policy_decision=policy_decision,
                    ),
                    output,
                )
                continue
            client = db.Live()
            raw_symbol = mapping["raw_symbol"]
            stype_in = mapping.get("stype_in", "parent")
            records_seen = 0

            def _callback(record, *, gs=gtos_symbol, rs=raw_symbol, c=client):
                nonlocal records_seen
                features = normalize_record(record)
                schema_seen = features.get("rtype") or features.get("record_type")
                append_live_row(
                    build_live_status_row(
                        status="LIVE_RECORD",
                        gtos_symbol=gs,
                        raw_symbol=rs,
                        schema=str(schema_seen) if schema_seen is not None else None,
                        dataset=args.dataset,
                        features=features,
                        trigger_id=trigger_id,
                        source_candidate_id=args.source_candidate_id,
                        source_opportunity_id=args.source_opportunity_id,
                        asof_cutoff_utc=args.asof_cutoff_utc,
                        window_start_utc=args.window_start_utc,
                        window_end_utc=args.window_end_utc,
                        signal_use_case=args.signal_use_case,
                        policy_decision=policy_decision,
                        feature_class=schema_feature_class(str(schema_seen) if schema_seen is not None else None),
                        paid_fetch_attempted=True,
                        paid_data_calls=1,
                        databento_calls=1,
                    ),
                    output,
                )
                records_seen += 1
                if args.max_records and records_seen >= args.max_records:
                    append_live_row(
                        build_live_status_row(
                            status="MAX_RECORDS_REACHED_STOPPING",
                            gtos_symbol=gs,
                            raw_symbol=rs,
                            dataset=args.dataset,
                            message=f"records_seen={records_seen}",
                            trigger_id=trigger_id,
                            source_candidate_id=args.source_candidate_id,
                            source_opportunity_id=args.source_opportunity_id,
                            asof_cutoff_utc=args.asof_cutoff_utc,
                            window_start_utc=args.window_start_utc,
                            window_end_utc=args.window_end_utc,
                            signal_use_case=args.signal_use_case,
                            policy_decision=policy_decision,
                            paid_fetch_attempted=True,
                            paid_data_calls=1,
                            databento_calls=1,
                        ),
                        output,
                    )
                    try:
                        c.stop()
                    except Exception:
                        pass

            client.add_callback(_callback)
            for schema in schemas:
                client.subscribe(
                    dataset=args.dataset,
                    schema=schema,
                    symbols=raw_symbol,
                    stype_in=stype_in,
                )
                append_live_row(
                    build_live_status_row(
                        status="SUBSCRIBED",
                        gtos_symbol=gtos_symbol,
                        raw_symbol=raw_symbol,
                        schema=schema,
                        dataset=args.dataset,
                        trigger_id=trigger_id,
                        source_candidate_id=args.source_candidate_id,
                        source_opportunity_id=args.source_opportunity_id,
                        asof_cutoff_utc=args.asof_cutoff_utc,
                        window_start_utc=args.window_start_utc,
                        window_end_utc=args.window_end_utc,
                        signal_use_case=args.signal_use_case,
                        policy_decision=policy_decision,
                        paid_fetch_attempted=True,
                        paid_data_calls=1,
                        databento_calls=1,
                    ),
                    output,
                )
            clients.append(client)
            client.start()
        for client in clients:
            client.block_for_close(timeout=args.timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        message = f"{type(exc).__name__}: {exc}"
        final_budget_status = (
            "LIVE_SESSION_FAILED_NO_LICENSE"
            if "license" in message.lower() or "entitlement" in message.lower()
            else "LIVE_SESSION_FAILED_API_ERROR"
        )
        append_live_row(
            build_live_status_row(
                status=final_budget_status,
                dataset=args.dataset,
                schema=",".join(schemas),
                message=message,
                trigger_id=trigger_id,
                source_candidate_id=args.source_candidate_id,
                source_opportunity_id=args.source_opportunity_id,
                asof_cutoff_utc=args.asof_cutoff_utc,
                window_start_utc=args.window_start_utc,
                window_end_utc=args.window_end_utc,
                signal_use_case=args.signal_use_case,
                policy_decision=policy_decision,
                feature_class=",".join(policy_decision.get("feature_classes") or []),
                paid_fetch_attempted=True,
                paid_data_calls=0,
                databento_calls=1,
            ),
            output,
        )
        print(final_budget_status)
        exit_code = 2
    finally:
        for client in clients:
            try:
                client.stop()
            except Exception:
                try:
                    client.terminate()
                except Exception:
                    pass
        append_budget_row(
            build_budget_ledger_row(
                budget_status=final_budget_status,
                policy_decision=policy_decision,
            ),
            budget_log,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
