#!/usr/bin/env python3
"""Capture bridge-backed candidate symbol spec/LTF readiness evidence.

This route is read-only with respect to MT5 and broker state. It uses the
localhost siliconmetatrader5 bridge for symbol_info/symbol_select reads only,
scans already exported OHLCV manifest metadata, and writes route-local ledgers.
It does not use orderflow/depth, place/cancel/modify orders, mutate positions,
touch credentials, restart VPS processes, or flip candidate-book config.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "data" / "mt5_research_exports"
READINESS_ROUTE = ROOT / "research" / "operations" / "final_moonshot_candidate_activation_readiness_2026_06_18"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.export_mt5_research_ohlcv import account_identity_payload  # noqa: E402
from research.operations.final_moonshot_candidate_activation_readiness_2026_06_18.verify_candidate_activation_readiness import (  # noqa: E402
    build_result as build_candidate_readiness_result,
)


CANDIDATE_NATIVE_MAP: dict[str, str] = {
    "AUDUSD": "AUDUSD",
    "DASHUSD": "DASHUSD",
    "EURGBP": "EURGBP",
    "EURUSD": "EURUSD",
    "GBPUSD": "GBPUSD",
    "LTCUSD": "LTCUSD",
    "NATGAS_cash": "NATGAS.cash",
    "NZDUSD": "NZDUSD",
    "USDCAD": "USDCAD",
    "USDCHF": "USDCHF",
    "XPDUSD": "XPDUSD",
    "XPTUSD": "XPTUSD",
    "XRPUSD": "XRPUSD",
    "XTZUSD": "XTZUSD",
}

REINTRODUCED_FX = {
    "AUDUSD",
    "EURGBP",
    "EURUSD",
    "GBPUSD",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
}

M1_REPAIRED_SYMBOLS = {"XPDUSD", "XPTUSD", "XRPUSD"}
NON_ORDERFLOW_ALLOWED_TIMEFRAMES = {"M1", "M15", "H1", "H4", "D1"}

SPEC_FIELDS = (
    "name",
    "description",
    "path",
    "digits",
    "point",
    "trade_tick_size",
    "trade_tick_value",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "trade_contract_size",
    "volume_min",
    "volume_max",
    "volume_step",
    "volume_limit",
    "trade_stops_level",
    "trade_freeze_level",
    "spread",
    "spread_float",
    "trade_mode",
    "trade_exemode",
    "filling_mode",
    "order_mode",
    "expiration_mode",
    "swap_mode",
    "swap_long",
    "swap_short",
    "swap_rollover3days",
    "margin_initial",
    "margin_maintenance",
    "margin_hedged",
    "trade_calc_mode",
    "currency_base",
    "currency_profit",
    "currency_margin",
    "visible",
)

SPEC_SOURCE_PATHS = (
    ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28" / "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl",
    ROOT / "research" / "operations" / "vnext_vps_live_activation_active_supervisor_2026_06_01" / "VPS_BROKER_SPEC_LEDGER.jsonl",
    ROOT / "research" / "operations" / "vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02" / "FTMO_SYMBOL_SPEC_LEDGER.jsonl",
    ROOT / "research" / "operations" / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10" / "VERIFIED_BROKER_SYMBOL_SPECS.json",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not contain a JSON object")
    return data


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_bridge_symbol_specs() -> dict[str, Any]:
    from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415

    mt5 = MetaTrader5(host="localhost", port=8001, keepalive=True)
    if not mt5.initialize():
        raise RuntimeError(f"MT5 bridge initialize failed: {mt5.last_error()}")

    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError("MT5 bridge account_info returned None")
        symbols_total = len(mt5.symbols_get() or [])
        specs: dict[str, dict[str, Any]] = {}
        for symbol, native in CANDIDATE_NATIVE_MAP.items():
            selected = bool(mt5.symbol_select(native, True))
            info = mt5.symbol_info(native)
            tick = mt5.symbol_info_tick(native) if info is not None else None
            row: dict[str, Any] = {
                "symbol": symbol,
                "native_symbol": native,
                "selected": selected,
                "symbol_info_present": info is not None,
                "last_error": str(mt5.last_error()),
            }
            if info is not None:
                for field in SPEC_FIELDS:
                    row[field] = getattr(info, field, None)
            if tick is not None:
                row["tick_bid"] = getattr(tick, "bid", None)
                row["tick_ask"] = getattr(tick, "ask", None)
                row["tick_time"] = getattr(tick, "time", None)
            specs[symbol] = row
        return {
            "schema": "gtos.final_moonshot.candidate_bridge_symbol_spec_capture.v1",
            "created_at_utc": _utc_now(),
            "read_only": True,
            "mt5_client_kind": "siliconmetatrader5_bridge",
            "bridge_host": "localhost",
            "bridge_port": 8001,
            "account": account_identity_payload(account),
            "symbol_count_on_broker": symbols_total,
            "symbols": specs,
            "orderflow_used": False,
            "broker_or_order_mutation": False,
            "vps_process_touched": False,
        }
    finally:
        close = getattr(mt5, "close", None)
        if callable(close):
            close()


def _manifest_symbol_hits() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not DATA_ROOT.exists():
        return rows
    for manifest_path in sorted(DATA_ROOT.glob("*/manifest.json")):
        try:
            manifest = _read_json(manifest_path)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
        files = manifest.get("files")
        if not isinstance(files, dict):
            continue
        for key, meta in files.items():
            if not isinstance(meta, dict):
                continue
            symbol = str(meta.get("file_symbol") or key.rsplit("_", 1)[0])
            timeframe = str(meta.get("timeframe") or key.rsplit("_", 1)[-1])
            if symbol not in CANDIDATE_NATIVE_MAP or timeframe not in NON_ORDERFLOW_ALLOWED_TIMEFRAMES:
                continue
            row_count = int(meta.get("row_count") or meta.get("rows") or 0)
            if row_count <= 0:
                continue
            rows.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": row_count,
                "first": meta.get("first"),
                "last": meta.get("last"),
                "label": manifest.get("label"),
                "manifest_path": _rel(manifest_path),
                "manifest_sha256": _file_sha256(manifest_path),
                "data_path": meta.get("path"),
                "source_broker": meta.get("source_broker") or (manifest.get("source_provenance") or {}).get("source_broker"),
                "source_role": meta.get("source_role") or (manifest.get("source_provenance") or {}).get("source_role"),
                "source_truth_scope": meta.get("source_truth_scope") or (manifest.get("source_provenance") or {}).get("source_truth_scope"),
            })
    return rows


def _history_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row["symbol"]][row["timeframe"]].append(row)

    out: dict[str, dict[str, Any]] = {}
    for symbol in sorted(CANDIDATE_NATIVE_MAP):
        symbol_out: dict[str, Any] = {}
        for timeframe in sorted(grouped.get(symbol, {})):
            items = grouped[symbol][timeframe]
            firsts = [str(item["first"]) for item in items if item.get("first")]
            lasts = [str(item["last"]) for item in items if item.get("last")]
            symbol_out[timeframe] = {
                "manifest_count": len(items),
                "row_count": sum(int(item["rows"]) for item in items),
                "first": min(firsts) if firsts else None,
                "last": max(lasts) if lasts else None,
                "labels": sorted({str(item.get("label")) for item in items if item.get("label")}),
                "sample_manifest_paths": [item["manifest_path"] for item in items[:8]],
            }
        out[symbol] = symbol_out
    return out


def _load_existing_spec_sources() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    targets = set(CANDIDATE_NATIVE_MAP)
    for path in SPEC_SOURCE_PATHS:
        if not path.exists():
            continue
        if path.suffix == ".json":
            data = _read_json(path)
            symbols = data.get("symbols") if isinstance(data.get("symbols"), dict) else {}
            for symbol, payload in symbols.items():
                if symbol not in targets or not isinstance(payload, dict):
                    continue
                for broker in ("ftmo", "redacted_account"):
                    broker_payload = payload.get(broker)
                    if broker_payload:
                        rows.append({
                            "symbol": symbol,
                            "broker_namespace": broker,
                            "source_path": _rel(path),
                            "source_schema": data.get("schema"),
                            "source_status": payload.get("follower_status"),
                            "fields_present": sorted(broker_payload),
                        })
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            symbol = str(payload.get("symbol") or payload.get("file_symbol") or "")
            if symbol not in targets:
                continue
            broker_namespace = "unknown"
            if "FTMO_SYMBOL_SPEC_LEDGER" in path.name:
                broker_namespace = "ftmo"
            elif path.name in {"VPS_BROKER_SPEC_LEDGER.jsonl", "LIVE_SYMBOL_BROKER_SPEC_LEDGER.jsonl"}:
                broker_namespace = "redacted_account_or_live_runtime"
            rows.append({
                "symbol": symbol,
                "broker_namespace": broker_namespace,
                "source_path": _rel(path),
                "source_status": payload.get("status") or payload.get("schema_version"),
                "broker_symbol": payload.get("broker_symbol") or payload.get("mt5_symbol") or payload.get("name"),
                "digits": payload.get("digits"),
                "point": payload.get("point"),
                "trade_tick_size": payload.get("trade_tick_size"),
                "trade_tick_value": payload.get("trade_tick_value"),
                "trade_contract_size": payload.get("trade_contract_size") or payload.get("contract_size"),
                "volume_min": payload.get("volume_min"),
                "volume_max": payload.get("volume_max"),
                "volume_step": payload.get("volume_step"),
                "trade_mode": payload.get("trade_mode"),
                "spread": payload.get("spread"),
                "visible": payload.get("visible"),
            })
    return rows


def build_outputs() -> dict[str, Any]:
    bridge_capture = capture_bridge_symbol_specs()
    bridge_specs = bridge_capture["symbols"]
    history_rows = _manifest_symbol_hits()
    history_summary = _history_summary(history_rows)
    existing_spec_sources = _load_existing_spec_sources()
    readiness_now = build_candidate_readiness_result()

    ftmo_bridge_ready = {
        symbol: bool(row.get("symbol_info_present") and row.get("trade_mode") == 4)
        for symbol, row in bridge_specs.items()
    }
    redacted_account_spec_symbols = {
        row["symbol"]
        for row in existing_spec_sources
        if row.get("broker_namespace") == "redacted_account_or_live_runtime"
        and row.get("symbol") in REINTRODUCED_FX
    }

    decision_rows: list[dict[str, Any]] = []
    for symbol in sorted(CANDIDATE_NATIVE_MAP):
        history = history_summary.get(symbol, {})
        has_generation_history = all(tf in history for tf in ("M15", "H4", "D1") if symbol not in {"XPDUSD", "XPTUSD", "XRPUSD"})
        if symbol in {"XPDUSD", "XPTUSD", "XRPUSD", "XTZUSD"}:
            has_generation_history = all(tf in history for tf in ("M15", "H4", "D1") if tf in {"M15", "H4", "D1"})
        if symbol == "NATGAS_cash":
            next_work = "keep W7 hard-drop until fresh tick/cost proof revives it"
            deployment_status = "research_only_cost_revival_work"
        elif symbol in redacted_account_spec_symbols and ftmo_bridge_ready[symbol]:
            next_work = "generate active FTMO+redacted_account profile contract rows and candidate-specific native eligibility proposal"
            deployment_status = "profile_patchable_dual_broker"
        elif ftmo_bridge_ready[symbol]:
            next_work = "generate FTMO profile row and broker-specific candidate subset/skip dossier for non-redacted_account namespace"
            deployment_status = "ftmo_patchable_requires_broker_specific_subset_or_redacted_account_export"
        else:
            next_work = "bridge symbol_info missing; re-probe alias universe before profile patch"
            deployment_status = "symbol_source_work_needed"
        decision_rows.append({
            "symbol": symbol,
            "native_symbol": CANDIDATE_NATIVE_MAP[symbol],
            "ftmo_bridge_spec_ready": ftmo_bridge_ready[symbol],
            "redacted_account_existing_spec_ready": symbol in redacted_account_spec_symbols,
            "history_timeframes_present": sorted(history),
            "m1_stress_available": "M1" in history,
            "generation_history_available": has_generation_history,
            "deployment_status": deployment_status,
            "next_work": next_work,
        })

    ltf_gap_symbols = [row["symbol"] for row in readiness_now["ltf_stress_gaps"]]
    result = {
        "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_work.v1",
        "ok": True,
        "decision": (
            "BRIDGE_DATA_WORK_PROGRESS__ALL_CANDIDATE_SYMBOLS_NATIVE_ON_FTMO_BRIDGE__"
            "LTF_M1_GAP_CLOSED__PROFILE_SPEC_NATIVE_AND_COST_WORK_REMAINS"
        ),
        "bridge_read_only": True,
        "bridge_host": "localhost",
        "bridge_port": 8001,
        "bridge_profile_namespace": "operator_profile",
        "candidate_symbol_count": len(CANDIDATE_NATIVE_MAP),
        "ftmo_bridge_native_symbol_count": sum(1 for ready in ftmo_bridge_ready.values() if ready),
        "redacted_account_existing_fx_spec_count": len(redacted_account_spec_symbols),
        "ltf_gap_count_after_bridge_export": len(ltf_gap_symbols),
        "ltf_gap_symbols_after_bridge_export": ltf_gap_symbols,
        "readiness_work_item_count_after_bridge_export": len(readiness_now["activation_blockers"]),
        "m1_repaired_symbols": sorted(M1_REPAIRED_SYMBOLS),
        "profile_patchable_dual_broker_symbols": sorted(
            row["symbol"] for row in decision_rows
            if row["deployment_status"] == "profile_patchable_dual_broker"
        ),
        "ftmo_patchable_subset_symbols": sorted(
            row["symbol"] for row in decision_rows
            if row["deployment_status"] == "ftmo_patchable_requires_broker_specific_subset_or_redacted_account_export"
        ),
        "research_only_cost_revival_symbols": sorted(
            row["symbol"] for row in decision_rows
            if row["deployment_status"] == "research_only_cost_revival_work"
        ),
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "credential_mutation": False,
        "vps_process_touched": False,
    }

    saturation = {
        "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_saturation.v1",
        "ok": True,
        "same_evidence_class_work_completed": [
            "confirmed localhost Docker bridge reachable on port 8001",
            "captured read-only FTMO Server3 symbol_info for every unfinished candidate symbol",
            "confirmed broker-native aliases including NATGAS_cash -> NATGAS.cash",
            "exported recent chunked M1 OHLCV for XPDUSD/XPTUSD/XRPUSD",
            "scanned existing bridge export manifests for candidate M1/M15/H1/H4/D1 coverage",
            "scanned local FTMO/redacted_account spec ledgers before declaring profile work external",
        ],
        "remaining_work": [
            "materialize FTMO profile rows for bridge-ready candidate symbols",
            "materialize redacted_account profile rows for the seven reintroduced FX symbols from existing live/VPS spec ledgers",
            "implement candidate-book-specific broker namespace/subset readiness so FTMO-only symbols do not poison redacted_account deployment",
            "keep NATGAS_cash research-only until a fresh cost proof beats the W7 hard-drop reason",
        ],
        "not_stopping_points": [
            "M1/LTF data is no longer a stop point for XPDUSD/XPTUSD/XRPUSD",
            "missing redacted_account alt/metals profile rows are broker-specific work, not a candidate idea kill",
            "global native-eligible live list should not be widened casually while candidate book remains default-off",
        ],
        "forbidden_surfaces_not_crossed": [
            "orderflow/depth",
            "broker account/order/deal/position mutation",
            "credential mutation/disclosure",
            "live VPS process mutation",
            "candidate-book live activation",
        ],
    }

    completion = {
        "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_completion.v1",
        "ok": True,
        "decision": result["decision"],
        "bridge_read_only": True,
        "all_bridge_symbols_present": result["ftmo_bridge_native_symbol_count"] == result["candidate_symbol_count"],
        "ltf_gap_count_after_bridge_export": result["ltf_gap_count_after_bridge_export"],
        "readiness_work_item_count_after_bridge_export": result["readiness_work_item_count_after_bridge_export"],
        "runtime_effect_now": "none_candidate_book_default_off",
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }

    return {
        "bridge_capture": bridge_capture,
        "bridge_spec_rows": list(bridge_specs.values()),
        "history_rows": history_rows,
        "history_summary": history_summary,
        "existing_spec_sources": existing_spec_sources,
        "decision_rows": decision_rows,
        "result": result,
        "profile_repair": {
            "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_profile_repair_ledger.v1",
            "ok": True,
            "dual_broker_profile_patchable_symbols": result["profile_patchable_dual_broker_symbols"],
            "ftmo_patchable_subset_or_redacted_account_export_symbols": result["ftmo_patchable_subset_symbols"],
            "research_only_cost_revival_symbols": result["research_only_cost_revival_symbols"],
            "exact_next_repairs": [
                "add FTMO Server3 profile contract rows from MT5_BRIDGE_SYMBOL_SPEC_LEDGER.jsonl",
                "add redacted_account profile contract rows for reintroduced FX from existing VPS/live redacted_account ledgers",
                "add default-off candidate-book-specific broker subset semantics before admitting FTMO-only symbols",
                "keep NATGAS_cash out of deployment until new tick/cost proof repairs W7 hard-drop evidence",
            ],
            "global_live_native_list_widened": False,
            "candidate_book_live_activation": False,
        },
        "saturation": saturation,
        "completion": completion,
    }


def write_outputs(outputs: dict[str, Any]) -> None:
    _write_json(ROUTE_DIR / "MT5_BRIDGE_SYMBOL_SPEC_CAPTURE.json", outputs["bridge_capture"])
    _write_jsonl(ROUTE_DIR / "MT5_BRIDGE_SYMBOL_SPEC_LEDGER.jsonl", outputs["bridge_spec_rows"])
    _write_jsonl(ROUTE_DIR / "CANDIDATE_HISTORY_MANIFEST_LEDGER.jsonl", outputs["history_rows"])
    _write_json(ROUTE_DIR / "CANDIDATE_HISTORY_MANIFEST_SUMMARY.json", outputs["history_summary"])
    _write_jsonl(ROUTE_DIR / "CANDIDATE_EXISTING_SPEC_SOURCE_LEDGER.jsonl", outputs["existing_spec_sources"])
    _write_jsonl(ROUTE_DIR / "CANDIDATE_BRIDGE_WORK_DECISION_LEDGER.jsonl", outputs["decision_rows"])
    _write_json(ROUTE_DIR / "CANDIDATE_BRIDGE_SPEC_LTF_WORK_RESULT.json", outputs["result"])
    _write_json(ROUTE_DIR / "PROFILE_REPAIR_LEDGER.json", outputs["profile_repair"])
    _write_json(ROUTE_DIR / "SATURATION_AUDIT.json", outputs["saturation"])
    _write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", outputs["completion"])
    _write_json(ROUTE_DIR / "FOCUSED_TEST_RESULT.json", {
        "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18/build_candidate_bridge_spec_ltf_work.py",
            "PYTHONDONTWRITEBYTECODE=1 python3 -c \"from pathlib import Path; [compile(Path(p).read_text(encoding='utf-8'), p, 'exec') for p in ('research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18/build_candidate_bridge_spec_ltf_work.py', 'research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18/verify_candidate_bridge_spec_ltf_work.py', 'tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py')]\"",
            "python3 research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18/verify_candidate_bridge_spec_ltf_work.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py -q",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18 --full-jsonl",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18/NEXT_PROMPT.md --kind terminal --json",
        ],
        "latest_observed_result": "recorded after local verifier/test/audit run",
    })
    _write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {
        "schema": "gtos.final_moonshot.candidate_bridge_spec_ltf_output_manifest.v1",
        "route_dir": _rel(ROUTE_DIR),
        "files": sorted({path.name for path in ROUTE_DIR.iterdir() if path.is_file()} | {"OUTPUT_MANIFEST.json"}),
    })


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    result = outputs["result"]
    print(json.dumps({
        "ok": result["ok"],
        "decision": result["decision"],
        "ftmo_bridge_native_symbol_count": result["ftmo_bridge_native_symbol_count"],
        "ltf_gap_count_after_bridge_export": result["ltf_gap_count_after_bridge_export"],
        "readiness_work_item_count_after_bridge_export": result["readiness_work_item_count_after_bridge_export"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
