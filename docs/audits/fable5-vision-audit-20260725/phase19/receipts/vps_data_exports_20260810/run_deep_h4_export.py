"""T1: deep-H4 source export for the five symbols blocking the Mac's W7 recost.

Reuses ``scripts/export_mt5_research_ohlcv.py``'s own functions so the CSV schema,
the gap/row statistics and the manifest shape are byte-for-byte the convention the
``bridge_ftmo_deep_h4_*`` exports already use — no re-implementation, no drift.

The only thing this driver changes is the MT5 attach: it initializes with
``portable=True``, exactly like the read-only probes that already proved they land
on the intended live terminal, instead of the shared script's plain ``path=``.

READ-ONLY. Places, modifies and cancels nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

import MetaTrader5 as mt5  # noqa: E402

from scripts.export_mt5_research_ohlcv import (  # noqa: E402
    SymbolSpec,
    account_identity_payload,
    enrich_export_result_for_manifest,
    export_research_ohlcv,
)
from src.components.external_feeds import utc_now  # noqa: E402

# canonical file_symbol -> broker spelling, resolved from the terminal by
# probe_prestate_and_symbols.py (see PROBE_PRESTATE_SYMBOLS.json)
SPECS = [
    SymbolSpec(file_symbol="CORN_c", mt5_symbol="CORN.c"),
    SymbolSpec(file_symbol="COTTON_c", mt5_symbol="COTTON.c"),
    SymbolSpec(file_symbol="EU50_cash", mt5_symbol="EU50.cash"),
    SymbolSpec(file_symbol="FRA40_cash", mt5_symbol="FRA40.cash"),
    SymbolSpec(file_symbol="US2000_cash", mt5_symbol="US2000.cash"),
]

PROVENANCE = {
    "source_broker": "FTMO",
    "source_role": "research_deep_history_backfill",
    "source_truth_scope": "ordered_price_path_only_not_broker_order_lifecycle_truth",
    "replaces_missing_frozen_path_source": True,
    "not_redacted_account_native": True,
    "handoff_run_id": None,
    "handoff_requirement_id": None,
    "broker_lifecycle_truth_satisfied": False,
    "asof_decision_truth_satisfied": False,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--terminal-path", default=r"C:\MT5\FTMO\terminal64.exe")
    ap.add_argument("--label", default="bridge_ftmo_deep_h4_w7recost_20260810")
    ap.add_argument("--start", default="2014-01-01T00:00:00+00:00")
    ap.add_argument("--end", required=True)
    ap.add_argument("--chunk-days", type=float, default=365.0)
    ap.add_argument("--output-root", default="data/mt5_research_exports")
    args = ap.parse_args()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    output_dir = PROJECT_ROOT / args.output_root / args.label

    if not mt5.initialize(path=args.terminal_path, portable=True):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError("account_info returned None")

        result = export_research_ohlcv(
            mt5_module=mt5,
            specs=SPECS,
            timeframe_names=["H4"],
            start=start,
            end=end,
            output_dir=output_dir,
            chunk=timedelta(days=args.chunk_days),
        )
        manifest_path = output_dir / "manifest.json"
        result = enrich_export_result_for_manifest(
            export_result=result,
            account=account,
            provenance=PROVENANCE,
            start=start,
            end=end,
            manifest_path=manifest_path,
        )
        manifest = {
            "schema_version": "mt5_research_ohlcv_export_v1",
            "created_at_utc": utc_now().isoformat(),
            "read_only": True,
            "label": args.label,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
            "chunk_days": args.chunk_days,
            "output_dir": str(Path(args.output_root) / args.label),
            "mt5_client_kind": "MetaTrader5_python_portable",
            "account": account_identity_payload(account),
            "symbols": [s.__dict__ for s in SPECS],
            "timeframes": ["H4"],
            "source_provenance": PROVENANCE,
            "manifest_path": str(manifest_path),
            "timebase_note": (
                "the CSV 'time' column is the MT5 bar epoch rendered as if UTC; MT5 bar "
                "epochs are BROKER WALL CLOCK (server local). This matches the existing "
                "bridge_ftmo_deep_h4_* convention exactly - convert via broker_clock, "
                "do not assume UTC."
            ),
            "purpose": (
                "W7 recost: the five deep-history H4 symbols missing on the research side. "
                "The prior bridge_ftmo_deep_h4_backfill_2014_2026 export was never committed "
                "because data/mt5_research_exports/ is gitignored."
            ),
            **result,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0 if not manifest["errors"] else 2
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
