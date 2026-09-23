"""V4U VPS/Windows LTF hydration handoff package builder.

This module does not connect to MT5. It turns the existing rolling hydration
oracle's exact source requirements into a compact, broker-labeled execution
package for the later VPS/Windows MT5 phase.
"""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

from scripts.export_mt5_research_ohlcv import (
    ORDERED_PATH_OVERRIDE_SCOPE,
    DEFAULT_SYMBOL_SPECS,
    parse_symbol_specs,
)


SCHEMA_VERSION = "v4u_vps_mt5_ltf_handoff_v1"
REQUIREMENT_SCHEMA_VERSION = "v4u_vps_mt5_ltf_export_requirement_v1"
DEFAULT_SOURCE_BROKER = "FTMO"
DEFAULT_SOURCE_ROLE = "owner_authorized_path_override"


@dataclass(frozen=True)
class HandoffPackage:
    manifest: dict[str, Any]
    requirement_rows: list[dict[str, Any]]
    powershell_text: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def default_mt5_symbol_map() -> dict[str, str]:
    return {
        spec.file_symbol.upper(): spec.mt5_symbol
        for spec in parse_symbol_specs(DEFAULT_SYMBOL_SPECS)
    }


def build_handoff_package(
    *,
    oracle_report: Mapping[str, Any],
    source_broker: str = DEFAULT_SOURCE_BROKER,
    source_role: str = DEFAULT_SOURCE_ROLE,
    python_executable: str = "python",
    output_root: str = "data/mt5_research_exports",
    mt5_symbol_map: Mapping[str, str] | None = None,
    max_requirements: int | None = None,
) -> HandoffPackage:
    _validate_provenance(source_broker=source_broker, source_role=source_role)
    symbol_map = {**default_mt5_symbol_map(), **{k.upper(): v for k, v in (mt5_symbol_map or {}).items()}}
    raw_requirements = list(oracle_report.get("exact_source_requirements") or [])
    selected = raw_requirements[:max_requirements] if max_requirements else raw_requirements
    generated = utc_now_iso()
    rows = [
        _build_requirement_row(
            index=index,
            requirement=requirement,
            source_broker=source_broker,
            source_role=source_role,
            python_executable=python_executable,
            output_root=output_root,
            mt5_symbol_map=symbol_map,
        )
        for index, requirement in enumerate(selected, start=1)
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "handoff_id": f"v4u_vps_mt5_ltf_handoff_{generated.replace(':', '').replace('-', '')}",
        "source_broker": source_broker,
        "source_role": source_role,
        "replaces_missing_frozen_path_source": True,
        "not_redacted_account_native": True,
        "source_truth_scope": ORDERED_PATH_OVERRIDE_SCOPE,
        "source_boundary": {
            "ordered_path_truth_only": True,
            "asof_decision_packet_truth_satisfied": False,
            "broker_ticket_order_deal_account_history_truth_satisfied": False,
            "proxy_or_m15_may_satisfy_ordered_path_truth": False,
            "redacted_account_native_truth_claim": False,
        },
        "input_oracle_report_run_id": oracle_report.get("run_id"),
        "input_oracle_report_metrics": oracle_report.get("metrics"),
        "exact_requirement_groups_input": len(raw_requirements),
        "exact_requirement_groups_packaged": len(rows),
        "candidate_rows_total": sum(int(row.get("candidate_rows") or 0) for row in rows),
        "symbols": sorted({str(row["symbol"]) for row in rows}),
        "sessions": _counts(row["session"] for row in rows),
        "requirements_by_symbol": _counts(row["symbol"] for row in rows),
        "required_export_artifacts_per_requirement": [
            "history_availability_probe_json_with_source_provenance",
            "tick_availability_probe_json_with_source_provenance",
            "m1_export_csv",
            "m1_export_manifest_json_with_source_server_account_row_count_sha",
            "tick_export_jsonl",
            "tick_export_manifest_json_with_source_server_account_row_count_sha",
        ],
        "post_export_next_step": (
            "copy exported M1/tick artifacts back into the V4U source roots, rerun "
            "scripts/build_v4u_ordered_path_hydration_oracle.py, then rerun full "
            "Wave4R/V4U replay if any ordered path rows convert"
        ),
        "hard_boundaries": {
            "broker_operation": False,
            "order_send_modify_cancel": False,
            "broker_account_history_mutation": False,
            "paid_api_or_vendor_call": False,
            "active_vps_process_mutation": False,
        },
    }
    return HandoffPackage(
        manifest=manifest,
        requirement_rows=rows,
        powershell_text=_powershell_script(manifest=manifest, rows=rows),
    )


def _validate_provenance(*, source_broker: str, source_role: str) -> None:
    if source_broker != DEFAULT_SOURCE_BROKER:
        raise ValueError("V4U owner directive requires source_broker=FTMO")
    if source_role != DEFAULT_SOURCE_ROLE:
        raise ValueError(
            "V4U owner directive requires source_role=owner_authorized_path_override"
        )


def _build_requirement_row(
    *,
    index: int,
    requirement: Mapping[str, Any],
    source_broker: str,
    source_role: str,
    python_executable: str,
    output_root: str,
    mt5_symbol_map: Mapping[str, str],
) -> dict[str, Any]:
    symbol = str(requirement.get("symbol") or "").upper()
    date = str(requirement.get("date") or "")
    session = str(requirement.get("session") or "")
    start, end = _extract_window(requirement)
    mt5_symbol = mt5_symbol_map.get(symbol, symbol)
    requirement_id = _requirement_id(symbol, date, session, start, end)
    file_symbol = symbol
    label = f"v4u_ftmo_ltf_{requirement_id}"
    m1_export_label = f"{label}_m1"
    tick_export_label = f"{label}_tick"
    provenance_args = [
        "--source-broker",
        source_broker,
        "--source-role",
        source_role,
        "--replaces-missing-frozen-path-source",
        "--not-redacted_account-native",
        "--source-truth-scope",
        ORDERED_PATH_OVERRIDE_SCOPE,
        "--handoff-requirement-id",
        requirement_id,
        "--require-owner-authorized-path-override",
    ]
    symbol_arg = f"{file_symbol}:{mt5_symbol}"
    history_probe = [
        python_executable,
        "scripts/inspect_mt5_history_availability.py",
        "--start",
        start,
        "--end",
        end,
        "--symbol",
        symbol_arg,
        "--timeframes",
        "M1",
        "--label",
        m1_export_label,
        "--output-root",
        output_root,
        "--write-json",
        "--yes-live-readonly",
        *provenance_args,
    ]
    tick_probe = [
        python_executable,
        "scripts/inspect_mt5_tick_availability.py",
        "--window",
        f"{requirement_id}:{start},{end}",
        "--symbol",
        symbol_arg,
        "--label",
        tick_export_label,
        "--output-root",
        output_root,
        "--write-json",
        "--yes-live-readonly",
        *provenance_args,
    ]
    m1_export = [
        python_executable,
        "scripts/export_mt5_research_ohlcv.py",
        "--start",
        start,
        "--end",
        end,
        "--symbol",
        symbol_arg,
        "--timeframes",
        "M1",
        "--label",
        m1_export_label,
        "--output-root",
        output_root,
        "--yes-live-readonly",
        *provenance_args,
    ]
    tick_export = [
        python_executable,
        "scripts/export_mt5_research_ticks.py",
        "--window",
        f"{requirement_id}:{start},{end}",
        "--symbol",
        symbol_arg,
        "--label",
        tick_export_label,
        "--output-root",
        output_root,
        "--yes-live-readonly",
        *provenance_args,
    ]
    return {
        "schema_version": REQUIREMENT_SCHEMA_VERSION,
        "requirement_id": requirement_id,
        "route_requirement_index": index,
        "symbol": symbol,
        "mt5_symbol": mt5_symbol,
        "date": date,
        "session": session,
        "request_start_utc": start,
        "request_end_utc": end,
        "candidate_rows": int(requirement.get("candidate_rows") or 0),
        "sample_candidate_ids": list(requirement.get("sample_candidate_ids") or []),
        "sample_window_ids": list(requirement.get("sample_window_ids") or []),
        "source_broker": source_broker,
        "source_role": source_role,
        "replaces_missing_frozen_path_source": True,
        "not_redacted_account_native": True,
        "source_truth_scope": ORDERED_PATH_OVERRIDE_SCOPE,
        "not_broker_order_lifecycle_truth": True,
        "not_asof_decision_packet_truth": True,
        "required_source": "FTMO_MT5_M1_or_tick_window_owner_authorized_path_override",
        "required_capture_fields_after_export": [
            "source_server",
            "source_account_login",
            "source_broker",
            "source_role",
            "symbol",
            "mt5_symbol",
            "timeframe",
            "request_start_utc",
            "request_end_utc",
            "row_count",
            "first_time_utc",
            "last_time_utc",
            "sha256",
            "export_tool",
            "manifest_path",
        ],
        "allowed_uses": [
            "post_decision_replay_labels",
            "fillability",
            "target_stop_ordering",
            "mfe_mae",
            "milestone_clocks",
            "giveback_be_partial_harvest_time_stop_replay_evaluation",
        ],
        "forbidden_uses": [
            "asof_decision_packet_input",
            "broker_ticket_order_deal_account_history_truth",
            "broker_real_cash_pnl_truth",
            "redacted_account_native_path_truth_label",
            "proxy_m15_ordered_path_truth",
        ],
        "commands": {
            "history_probe": history_probe,
            "tick_probe": tick_probe,
            "m1_export": m1_export,
            "tick_export": tick_export,
        },
        "command_text": {
            key: _join_command(value)
            for key, value in {
                "history_probe": history_probe,
                "tick_probe": tick_probe,
                "m1_export": m1_export,
                "tick_export": tick_export,
            }.items()
        },
        "source_boundary": {
            "read_only": True,
            "order_send_modify_cancel": False,
            "proxy_sources_used_as_ordered_path_truth": False,
            "binary_cache_is_truth_without_parser_or_export": False,
        },
    }


def _extract_window(requirement: Mapping[str, Any]) -> tuple[str, str]:
    for template in requirement.get("export_command_templates") or []:
        command = str((template or {}).get("command") or "")
        if "export_mt5_research_ohlcv.py" not in command:
            continue
        args = shlex.split(command)
        start = _arg_after(args, "--start")
        end = _arg_after(args, "--end")
        if start and end:
            return _to_z(start), _to_z(end)
    raise ValueError(f"missing export start/end for requirement {requirement!r}")


def _arg_after(args: list[str], key: str) -> str | None:
    try:
        index = args.index(key)
    except ValueError:
        return None
    if index + 1 >= len(args):
        return None
    return args[index + 1]


def _to_z(value: str) -> str:
    raw = str(value).strip()
    if raw.endswith("Z"):
        return raw
    parsed_raw = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    parsed = datetime.fromisoformat(parsed_raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _requirement_id(symbol: str, date: str, session: str, start: str, end: str) -> str:
    material = json.dumps(
        {
            "symbol": symbol,
            "date": date,
            "session": session,
            "start": start,
            "end": end,
            "source_broker": DEFAULT_SOURCE_BROKER,
            "source_role": DEFAULT_SOURCE_ROLE,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "v4u_ltf_" + sha256(material).hexdigest()[:20]


def _counts(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _join_command(args: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in args)


def _powershell_script(*, manifest: Mapping[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# V4U VPS/Windows MT5 LTF hydration handoff",
        "# Read-only probes/exports only. No order send/modify/cancel commands.",
        f"# Handoff source broker: {manifest['source_broker']}",
        f"# Handoff source role: {manifest['source_role']}",
        f"# Requirement groups: {len(rows)}",
        "$ErrorActionPreference = 'Stop'",
        "",
    ]
    for row in rows:
        lines.append(f"# {row['requirement_id']} {row['symbol']} {row['session']} {row['request_start_utc']} -> {row['request_end_utc']}")
        for key in ("history_probe", "tick_probe", "m1_export", "tick_export"):
            lines.append(row["command_text"][key])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")
