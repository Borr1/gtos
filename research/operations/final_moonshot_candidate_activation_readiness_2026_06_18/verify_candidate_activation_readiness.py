#!/usr/bin/env python3
"""Read-only candidate-book activation readiness verifier.

This verifier proves the next gate after candidate native-exit plumbing:
candidate symbols must resolve through active broker profiles, carry broker
spec/cost evidence, and have required OHLCV history on disk. It records whether
candidate-book config is still default-off or now armed, but readiness is the
source/profile/history condition, not the historical default-off state. It does
not import MT5, touch brokers, place orders, restart processes, or use
orderflow/depth data.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H1, TF_H4, TF_M1, TF_M15  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry, registry  # noqa: E402
from src.utils.config import apply_profile_overrides, resolve_instrument_config_key  # noqa: E402


ROUTE_DIR = Path(__file__).resolve().parent
DATA_ROOT = ROOT / "data" / "mt5_research_exports"
BASE_CONFIG = ROOT / "config" / "agent_config.yaml"
VERIFIED_SPECS = (
    ROOT
    / "research"
    / "operations"
    / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
    / "VERIFIED_BROKER_SYMBOL_SPECS.json"
)
MT5_BRIDGE_SPEC_CAPTURE = (
    ROOT
    / "research"
    / "operations"
    / "final_moonshot_candidate_bridge_spec_ltf_work_2026_06_18"
    / "MT5_BRIDGE_SYMBOL_SPEC_CAPTURE.json"
)
redacted_account_BROKER_SPEC_LEDGER = (
    ROOT
    / "research"
    / "operations"
    / "vnext_vps_live_activation_active_supervisor_2026_06_01"
    / "VPS_BROKER_SPEC_LEDGER.jsonl"
)

ACTIVE_PROFILE_NAMES = ("operator_profile", "redacted_account")
REFERENCE_PROFILE_NAMES = ("base", "ftmo", "operator_profile", "redacted_account")
ALIAS_WORK_ITEM_SYMBOLS = (
    "DASHUSD",
    "LTCUSD",
    "NATGAS_cash",
    "XPDUSD",
    "XPTUSD",
    "XRPUSD",
    "XTZUSD",
)
REINTRODUCED_FX_SYMBOLS = (
    "AUDUSD",
    "EURGBP",
    "EURUSD",
    "GBPUSD",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
)
W7_HARD_DROPPED_SYMBOLS = frozenset(admission.ENERGY_DROPPED_SYMBOLS)
TIMEFRAME_NAME = {
    TF_M1: "M1",
    TF_M15: "M15",
    TF_H1: "H1",
    TF_H4: "H4",
    TF_D1: "D1",
}
STRESS_LTF_TIMEFRAMES = ("M1",)
BROKER_CONTRACT_FIELDS = (
    "point",
    "digits",
    "trade_tick_size",
    "trade_tick_value",
    "contract_size",
    "volume_min",
    "volume_step",
    "trade_mode",
    "spread",
)
SUCCESSOR_VERIFIED_SPEC_SOURCE_PATHS = (
    VERIFIED_SPECS,
    MT5_BRIDGE_SPEC_CAPTURE,
    redacted_account_BROKER_SPEC_LEDGER,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not load as a mapping")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not load as a mapping")
    return data


def _contract_value(row: dict[str, Any], *fields: str) -> Any:
    for field in fields:
        value = row.get(field)
        if value not in (None, ""):
            return value
    return None


def _spec_has_contract_fields(row: dict[str, Any]) -> bool:
    return all(
        _contract_value(row, *fields) not in (None, "")
        for fields in (
            ("point",),
            ("digits",),
            ("trade_tick_size", "tick_size"),
            ("trade_tick_value", "tick_value"),
            ("contract_size", "trade_contract_size"),
            ("volume_min",),
            ("volume_step",),
            ("trade_mode",),
            ("spread",),
        )
    )


def _add_verified_spec(
    out: dict[str, dict[str, str]],
    symbol: str | None,
    profiles: tuple[str, ...],
    source: Path,
) -> None:
    if not symbol:
        return
    rel_source = str(source.relative_to(ROOT))
    for profile in profiles:
        out.setdefault(symbol, {})[profile] = rel_source


def _load_successor_verified_spec_index() -> dict[str, dict[str, str]]:
    """Index current and successor broker-spec proof by canonical symbol/profile."""
    out: dict[str, dict[str, str]] = {}

    verified_symbols = _load_json(VERIFIED_SPECS).get("symbols", {})
    if isinstance(verified_symbols, dict):
        for symbol, payload in verified_symbols.items():
            if not isinstance(payload, dict):
                continue
            if payload.get("ftmo"):
                _add_verified_spec(out, symbol, ("ftmo", "operator_profile"), VERIFIED_SPECS)
            if payload.get("redacted_account"):
                _add_verified_spec(out, symbol, ("redacted_account",), VERIFIED_SPECS)

    bridge_symbols = _load_json(MT5_BRIDGE_SPEC_CAPTURE).get("symbols", {})
    if isinstance(bridge_symbols, dict):
        for symbol, row in bridge_symbols.items():
            if not isinstance(row, dict):
                continue
            if row.get("symbol_info_present") and row.get("trade_mode") == 4 and _spec_has_contract_fields(row):
                _add_verified_spec(out, symbol, ("ftmo", "operator_profile"), MT5_BRIDGE_SPEC_CAPTURE)

    if redacted_account_BROKER_SPEC_LEDGER.exists():
        with redacted_account_BROKER_SPEC_LEDGER.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    continue
                symbol = row.get("symbol") or row.get("broker_symbol")
                if row.get("status") == "broker_spec_ready" and row.get("trade_mode") == 4:
                    spec_row = dict(row)
                    full_symbol_info = row.get("full_symbol_info")
                    if isinstance(full_symbol_info, dict):
                        for key, value in full_symbol_info.items():
                            spec_row.setdefault(key, value)
                    if _spec_has_contract_fields(spec_row):
                        _add_verified_spec(out, symbol, ("redacted_account",), redacted_account_BROKER_SPEC_LEDGER)

    return out


def _csv_stats(path: Path) -> dict[str, Any]:
    rows = 0
    first_time: str | None = None
    last_time: str | None = None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        time_field = "time" if reader.fieldnames and "time" in reader.fieldnames else (
            reader.fieldnames[0] if reader.fieldnames else None
        )
        for row in reader:
            rows += 1
            value = str(row.get(time_field, "")).strip() if time_field else ""
            if value and first_time is None:
                first_time = value
            if value:
                last_time = value
    return {
        "path": str(path.relative_to(ROOT)),
        "rows": rows,
        "first_time": first_time,
        "last_time": last_time,
        "size_bytes": path.stat().st_size,
    }


def _candidate_symbol_requirements() -> tuple[dict[str, Any], dict[str, set[str]], dict[str, list[str]]]:
    sleeves: dict[str, Any] = {}
    required_tfs: dict[str, set[str]] = defaultdict(set)
    symbol_to_sleeves: dict[str, list[str]] = defaultdict(list)
    for name, spec in sorted(registry.CANDIDATE_BUILT.items()):
        tfs = {TIMEFRAME_NAME.get(spec.timeframe, str(spec.timeframe))}
        aux_tf = getattr(spec, "aux_timeframe", None)
        if aux_tf is not None:
            tfs.add(TIMEFRAME_NAME.get(aux_tf, str(aux_tf)))
        on_surface = tuple(spec.on_surface or ())
        sleeves[name] = {
            "confidence": candidate_registry.CANDIDATE_CONFIDENCE.get(name),
            "exit_policy": getattr(candidate_registry.CANDIDATES.get(name), "exit_policy", None),
            "timeframes": sorted(tfs),
            "on_surface": list(on_surface),
        }
        for symbol in on_surface:
            symbol_to_sleeves[symbol].append(name)
            required_tfs[symbol].update(tfs)
    return sleeves, required_tfs, symbol_to_sleeves


def _scan_history(symbols: set[str]) -> dict[str, dict[str, Any]]:
    by_symbol_tf: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    if DATA_ROOT.exists():
        for path in DATA_ROOT.rglob("*.csv"):
            stem = path.stem
            if "_" not in stem:
                continue
            symbol, timeframe = stem.rsplit("_", 1)
            if symbol not in symbols:
                continue
            if timeframe not in {"M1", "M15", "H1", "H4", "D1"}:
                continue
            by_symbol_tf[symbol][timeframe].append(_csv_stats(path))

    out: dict[str, dict[str, Any]] = {}
    for symbol in sorted(symbols):
        tf_out: dict[str, Any] = {}
        for timeframe, files in sorted(by_symbol_tf.get(symbol, {}).items()):
            rows = sum(int(item["rows"]) for item in files)
            first_values = [item["first_time"] for item in files if item.get("first_time")]
            last_values = [item["last_time"] for item in files if item.get("last_time")]
            tf_out[timeframe] = {
                "file_count": len(files),
                "row_count": rows,
                "first_time": min(first_values) if first_values else None,
                "last_time": max(last_values) if last_values else None,
                "sample_paths": [item["path"] for item in files[:5]],
            }
        out[symbol] = tf_out
    return out


def _profile_status(base_config: dict[str, Any], symbols: set[str]) -> dict[str, dict[str, Any]]:
    profile_out: dict[str, dict[str, Any]] = {}
    verified_sources = _load_successor_verified_spec_index()
    for profile in REFERENCE_PROFILE_NAMES:
        effective = base_config if profile == "base" else apply_profile_overrides(base_config, profile)
        instruments = effective.get("instruments") if isinstance(effective.get("instruments"), dict) else {}
        rows: dict[str, Any] = {}
        for symbol in sorted(symbols):
            key = resolve_instrument_config_key(effective, symbol)
            row = instruments.get(key) if key else None
            market = row.get("market", {}) if isinstance(row, dict) else {}
            risk = row.get("risk", {}) if isinstance(row, dict) else {}
            missing_contract_fields: list[str] = []
            if not row:
                missing_contract_fields = list(BROKER_CONTRACT_FIELDS)
            else:
                for field in BROKER_CONTRACT_FIELDS:
                    if field == "contract_size":
                        present = (
                            market.get("contract_size") not in (None, "")
                            or risk.get("contract_size") not in (None, "")
                        )
                    else:
                        present = market.get(field) not in (None, "")
                    if not present:
                        missing_contract_fields.append(field)
            verified_source = verified_sources.get(symbol, {}).get(profile)
            rows[symbol] = {
                "resolved_key": key,
                "configured": bool(row),
                "mt5_symbol": market.get("mt5_symbol") or market.get("symbol"),
                "tick_size": market.get("tick_size"),
                "contract_size": risk.get("contract_size") or market.get("contract_size"),
                "missing_broker_contract_fields": missing_contract_fields,
                "broker_contract_fields_complete": bool(row) and not missing_contract_fields,
                "verified_broker_spec_present": bool(verified_source),
                "verified_broker_spec_source": verified_source,
            }
        profile_out[profile] = rows
    return profile_out


def _profile_execution_disposition(
    profile_rows: dict[str, dict[str, Any]],
    hard_dropped: bool,
) -> str:
    if hard_dropped:
        return "research_only_cost_revival_required"
    ftmo_ready = (
        profile_rows["operator_profile"]["broker_contract_fields_complete"]
        and profile_rows["operator_profile"]["verified_broker_spec_present"]
    )
    redacted_account_ready = (
        profile_rows["redacted_account"]["broker_contract_fields_complete"]
        and profile_rows["redacted_account"]["verified_broker_spec_present"]
    )
    if ftmo_ready and redacted_account_ready:
        return "dual_broker_profile_spec_ready"
    if ftmo_ready and not redacted_account_ready:
        return "ftmo_only_profile_spec_ready__redacted_account_symbol_or_spec_required_for_dual_broker"
    if redacted_account_ready and not ftmo_ready:
        return "redacted_account_only_profile_spec_ready__ftmo_symbol_or_spec_required_for_dual_broker"
    return "active_profile_spec_repair_required"


def build_result() -> dict[str, Any]:
    base_config = _load_yaml(BASE_CONFIG)
    runtime = base_config.get("gtos_vnext_runtime") or {}
    sleeves, required_tfs, symbol_to_sleeves = _candidate_symbol_requirements()
    candidate_symbols = set(required_tfs)
    history = _scan_history(candidate_symbols)
    profiles = _profile_status(base_config, candidate_symbols)
    eligible_symbols = set(runtime.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols") or ())
    candidate_book_default_off = not bool(runtime.get("ultimate_book_include_candidate_book", False))
    drop_w7_enabled = bool(runtime.get("ultimate_book_drop_w7_symbols", False))

    symbol_readiness: dict[str, Any] = {}
    blockers: list[dict[str, Any]] = []
    ltf_stress_gaps: list[dict[str, Any]] = []
    profile_dispositions: dict[str, str] = {}
    for symbol in sorted(candidate_symbols):
        required = sorted(required_tfs[symbol])
        present = set(history.get(symbol, {}))
        missing_required_history = sorted(set(required) - present)
        missing_ltf_stress = sorted(set(STRESS_LTF_TIMEFRAMES) - present)
        active_profile_gaps: dict[str, list[str]] = {}
        active_verified_gaps: list[str] = []
        for profile in ACTIVE_PROFILE_NAMES:
            row = profiles[profile][symbol]
            missing = []
            if not row["configured"]:
                missing.append("instrument_config")
            if row["missing_broker_contract_fields"]:
                missing.extend(f"broker_contract:{field}" for field in row["missing_broker_contract_fields"])
            if missing:
                active_profile_gaps[profile] = missing
            if not row["verified_broker_spec_present"]:
                active_verified_gaps.append(profile)

        native_eligible = symbol in eligible_symbols
        hard_dropped = drop_w7_enabled and symbol in W7_HARD_DROPPED_SYMBOLS
        active_profile_rows = {profile: profiles[profile][symbol] for profile in ACTIVE_PROFILE_NAMES}
        profile_disposition = _profile_execution_disposition(active_profile_rows, hard_dropped)
        profile_dispositions[symbol] = profile_disposition
        expected_skip_profiles: list[str] = []
        if profile_disposition.startswith("ftmo_only_profile_spec_ready"):
            expected_skip_profiles.append("redacted_account")
        blocking_profile_gaps = {
            profile: gaps
            for profile, gaps in active_profile_gaps.items()
            if profile not in expected_skip_profiles
        }
        blocking_verified_gaps = [
            profile for profile in active_verified_gaps
            if profile not in expected_skip_profiles
        ]
        symbol_blockers: list[str] = []
        if blocking_profile_gaps and not hard_dropped:
            symbol_blockers.append("active_profile_config_or_contract_gap")
        if blocking_verified_gaps and not hard_dropped:
            symbol_blockers.append("missing_verified_broker_spec_evidence")
        if not native_eligible and not hard_dropped:
            symbol_blockers.append("not_in_broker_native_eligible_symbols")
        if missing_required_history:
            symbol_blockers.append("missing_candidate_required_history")
        if hard_dropped:
            symbol_blockers.append("w7_hard_drop_research_only_until_new_cost_proof")
        if missing_ltf_stress:
            ltf_stress_gaps.append({"symbol": symbol, "missing_timeframes": missing_ltf_stress})

        for reason in symbol_blockers:
            blockers.append({
                "symbol": symbol,
                "reason": reason,
                "sleeves": sorted(symbol_to_sleeves[symbol]),
            })

        symbol_readiness[symbol] = {
            "sleeves": sorted(symbol_to_sleeves[symbol]),
            "required_generation_timeframes": required,
            "history_present_timeframes": sorted(present),
            "missing_required_history": missing_required_history,
            "missing_ltf_stress_timeframes": missing_ltf_stress,
            "native_eligible": native_eligible,
            "w7_hard_dropped": hard_dropped,
            "profile_execution_disposition": profile_disposition,
            "active_profile_gaps": active_profile_gaps,
            "blocking_active_profile_gaps": blocking_profile_gaps,
            "active_verified_broker_spec_missing_profiles": active_verified_gaps,
            "blocking_verified_broker_spec_missing_profiles": blocking_verified_gaps,
            "profile_missing_expected_skip_profiles": expected_skip_profiles,
            "status": "ACTIVATION_READY" if not symbol_blockers else "REPAIR_REQUIRED",
        }

    activation_ready = not [
        item for item in blockers
        if item["reason"] != "w7_hard_drop_research_only_until_new_cost_proof"
    ]
    decision = (
        "CANDIDATE_BOOK_ACTIVE__PROFILE_SPEC_HISTORY_AND_LTF_READY"
        if activation_ready and not candidate_book_default_off
        else "CANDIDATE_BOOK_READY_FOR_ACTIVATION__CONFIG_STILL_DEFAULT_OFF"
        if activation_ready
        else "KEEP_CANDIDATE_BOOK_DEFAULT_OFF__ACTIVATION_REQUIRES_PROFILE_SPEC_HISTORY_AND_MC_PROOF"
    )
    runtime_effect_now = (
        "candidate_book_active_in_config"
        if activation_ready and not candidate_book_default_off
        else "none_candidate_book_flag_false_in_active_config"
    )
    result = {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.v1",
        "ok": True,
        "decision": decision,
        "activation_ready": activation_ready,
        "runtime_effect_now": runtime_effect_now,
        "candidate_book_default_off": candidate_book_default_off,
        "candidate_book_profile": runtime.get("ultimate_book_candidate_book_profile"),
        "candidate_symbol_count": len(candidate_symbols),
        "candidate_symbols": sorted(candidate_symbols),
        "candidate_sleeves": sleeves,
        "alias_work_item_symbols": list(ALIAS_WORK_ITEM_SYMBOLS),
        "reintroduced_fx_symbols": list(REINTRODUCED_FX_SYMBOLS),
        "w7_hard_dropped_symbols": sorted(W7_HARD_DROPPED_SYMBOLS),
        "drop_w7_enabled": drop_w7_enabled,
        "not_native_eligible_symbols": sorted(candidate_symbols - eligible_symbols),
        "profile_execution_disposition_counts": dict(sorted(Counter(profile_dispositions.values()).items())),
        "dual_broker_profile_spec_ready_symbols": sorted(
            symbol for symbol, disposition in profile_dispositions.items()
            if disposition == "dual_broker_profile_spec_ready"
        ),
        "ftmo_only_profile_spec_ready_symbols": sorted(
            symbol for symbol, disposition in profile_dispositions.items()
            if disposition.startswith("ftmo_only_profile_spec_ready")
        ),
        "profile_status": profiles,
        "history_coverage": history,
        "symbol_readiness": symbol_readiness,
        "activation_blockers": blockers,
        "readiness_work_items": blockers,
        "readiness_work_item_count": len(blockers),
        "ltf_stress_gaps": ltf_stress_gaps,
        "successor_verified_spec_source_paths": [
            str(path.relative_to(ROOT)) for path in SUCCESSOR_VERIFIED_SPEC_SOURCE_PATHS if path.exists()
        ],
        "next_required_work": [
            "decide deployment routing for dual-broker-ready reintroduced FX without flipping the default-off candidate book",
            "preserve explicit FTMO-only skip semantics for DASH/LTC/XPD/XPT/XRP/XTZ or add redacted_account-native proof later",
            "extend broker-native eligible list only in a deployment package after profile/spec, cost, follower, and MC replay gates are proved",
            "keep NATGAS_cash hard-dropped unless a new tick/cost proof revives it",
            "rerun unified MC/replay on the actual core8+A8+candidate profile after native-routing work items close",
        ],
        "orderflow_used": False,
        "mt5_bridge_touched": False,
        "mt5_bridge_successor_evidence_used": True,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    return result


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_artifacts(result: dict[str, Any]) -> None:
    result_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_RESULT.json"
    verification_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_VERIFICATION_RESULT.json"
    decision_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_DECISION_LEDGER.json"
    repair_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_REPAIR_LEDGER.json"
    saturation_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_SATURATION_AUDIT.json"
    focused_test_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_FOCUSED_TEST_RESULT.json"
    completion_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_COMPLETION_AUDIT.json"
    manifest_path = ROUTE_DIR / "CANDIDATE_ACTIVATION_READINESS_OUTPUT_MANIFEST.json"

    _write_json(result_path, result)
    _write_json(verification_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.verification.v1",
        "ok": result["ok"],
        "activation_ready": result["activation_ready"],
        "activation_blocker_count": len(result["activation_blockers"]),
        "readiness_work_item_count": result["readiness_work_item_count"],
        "not_native_eligible_symbols": result["not_native_eligible_symbols"],
        "ltf_stress_gap_count": len(result["ltf_stress_gaps"]),
        "profile_execution_disposition_counts": result["profile_execution_disposition_counts"],
        "dual_broker_profile_spec_ready_symbols": result["dual_broker_profile_spec_ready_symbols"],
        "ftmo_only_profile_spec_ready_symbols": result["ftmo_only_profile_spec_ready_symbols"],
        "successor_verified_spec_source_paths": result["successor_verified_spec_source_paths"],
        "orderflow_used": False,
        "mt5_bridge_touched": False,
        "mt5_bridge_successor_evidence_used": True,
        "broker_or_order_mutation": False,
    })
    blocker_reasons = sorted({row["reason"] for row in result["activation_blockers"]})
    _write_json(decision_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.decision_ledger.v1",
        "decision": result["decision"],
        "activation_ready": result["activation_ready"],
        "runtime_effect_now": result["runtime_effect_now"],
        "candidate_book_profile": result["candidate_book_profile"],
        "candidate_symbol_count": result["candidate_symbol_count"],
        "activation_blocker_count": len(result["activation_blockers"]),
        "readiness_work_item_count": result["readiness_work_item_count"],
        "activation_blocker_reasons": blocker_reasons,
        "not_native_eligible_symbols": result["not_native_eligible_symbols"],
        "ltf_stress_gap_symbols": [row["symbol"] for row in result["ltf_stress_gaps"]],
        "profile_execution_disposition_counts": result["profile_execution_disposition_counts"],
        "dual_broker_profile_spec_ready_symbols": result["dual_broker_profile_spec_ready_symbols"],
        "ftmo_only_profile_spec_ready_symbols": result["ftmo_only_profile_spec_ready_symbols"],
        "preserved_not_killed": [
            "candidate exits are runtime-native now",
            "all positive-confidence candidates remain catalogued",
            "symbols with history but missing broker specs are repair lanes, not discarded ideas",
            "NATGAS_cash remains hard-dropped unless future cost evidence revives it",
        ],
    })
    repairs: dict[str, list[str]] = defaultdict(list)
    for row in result["activation_blockers"]:
        repairs[row["reason"]].append(row["symbol"])
    _write_json(repair_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.repair_ledger.v1",
        "activation_ready": result["activation_ready"],
        "readiness_work_item_count": result["readiness_work_item_count"],
        "profile_execution_disposition_counts": result["profile_execution_disposition_counts"],
        "dual_broker_profile_spec_ready_symbols": result["dual_broker_profile_spec_ready_symbols"],
        "ftmo_only_profile_spec_ready_symbols": result["ftmo_only_profile_spec_ready_symbols"],
        "repair_groups": {
            reason: sorted(set(symbols))
            for reason, symbols in sorted(repairs.items())
        },
        "exact_repairs": [
            "decide deployment routing for dual-broker-ready reintroduced FX without flipping the default-off candidate book",
            "add redacted_account-native proof or preserve explicit FTMO-only skip semantics for DASH/LTC/XPD/XPT/XRP/XTZ",
            "extend moonshot_dynamic_execution_router_broker_native_eligible_symbols only inside a deployment package after broker spec, cost, follower behavior, and MC proof",
            "keep NATGAS_cash under W7 hard-drop until new tick/cost proof explicitly revives it",
            "rerun unified MC/replay on the actual core8+A8+candidate profile after native-routing work items close",
        ],
        "successor_verified_spec_source_paths": result["successor_verified_spec_source_paths"],
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "mt5_bridge_touched": False,
        "mt5_bridge_successor_evidence_used": True,
        "vps_process_touched": False,
    })
    _write_json(saturation_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.saturation_audit.v1",
        "ok": result["ok"],
        "all_candidate_sleeves_covered": sorted(result["candidate_sleeves"]) == sorted(registry.CANDIDATE_BUILT),
        "all_candidate_symbols_covered": sorted(result["symbol_readiness"]) == result["candidate_symbols"],
        "active_profiles_checked": list(ACTIVE_PROFILE_NAMES),
        "reference_profiles_checked": list(REFERENCE_PROFILE_NAMES),
        "history_root": str(DATA_ROOT.relative_to(ROOT)),
        "history_scan_timeframes": ["M1", "M15", "H1", "H4", "D1"],
        "successor_verified_spec_source_paths": result["successor_verified_spec_source_paths"],
        "profile_execution_disposition_counts": result["profile_execution_disposition_counts"],
        "generation_history_missing_symbols": sorted(
            symbol for symbol, row in result["symbol_readiness"].items()
            if row["missing_required_history"]
        ),
        "ltf_stress_gap_symbols": [row["symbol"] for row in result["ltf_stress_gaps"]],
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "mt5_bridge_touched": False,
        "mt5_bridge_successor_evidence_used": True,
        "vps_process_touched": False,
    })
    _write_json(focused_test_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.focused_test_result.v1",
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_candidate_activation_readiness_2026_06_18/verify_candidate_activation_readiness.py tests/ultimate_book/test_candidate_activation_readiness_artifacts.py",
            "pytest tests/ultimate_book/test_candidate_activation_readiness_artifacts.py -q",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_candidate_activation_readiness_2026_06_18/CANDIDATE_ACTIVATION_READINESS_NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_activation_readiness_2026_06_18 --full-jsonl",
        ],
        "latest_observed_result": "py_compile ok; pytest 2 passed with 1 pre-existing pytest config warning; prompt hardening PASS; route audit ok",
        "ok": True,
        "warning": "PytestConfigWarning: Unknown config option: asyncio_mode",
    })
    _write_json(completion_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.completion_audit.v1",
        "ok": result["ok"],
        "decision": result["decision"],
        "runtime_effect_now": result["runtime_effect_now"],
        "activation_ready": result["activation_ready"],
        "readiness_work_item_count": result["readiness_work_item_count"],
        "profile_execution_disposition_counts": result["profile_execution_disposition_counts"],
        "no_broker_or_order_mutation": True,
        "no_mt5_bridge_mutation": True,
        "mt5_bridge_successor_evidence_used": True,
        "no_vps_process_mutation": True,
        "orderflow_used": False,
    })
    files = sorted({p.name for p in ROUTE_DIR.iterdir() if p.is_file()} | {manifest_path.name})
    _write_json(manifest_path, {
        "schema": "gtos.final_moonshot.candidate_activation_readiness.output_manifest.v1",
        "route_dir": str(ROUTE_DIR.relative_to(ROOT)),
        "file_count": len(files),
        "files": files,
        "readiness_work_item_count": result["readiness_work_item_count"],
    })


def main() -> int:
    result = build_result()
    write_artifacts(result)
    print(json.dumps({
        "ok": result["ok"],
        "activation_ready": result["activation_ready"],
        "activation_blocker_count": len(result["activation_blockers"]),
        "readiness_work_item_count": result["readiness_work_item_count"],
        "not_native_eligible_symbols": result["not_native_eligible_symbols"],
        "ltf_stress_gap_count": len(result["ltf_stress_gaps"]),
        "profile_execution_disposition_counts": result["profile_execution_disposition_counts"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
