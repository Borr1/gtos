#!/usr/bin/env python3
"""Build the Databento/Sierra orderflow shadow-data acceleration plan.

This is a durable planning artifact, not a data collector. It reads the current
LTO-011/LTO-012/LTO-013 reports and writes the near-term policy for using
Sierra now, Databento historical replay now, and Databento live only through
the approved collector gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.forward_capture import PROMOTION_VERDICT  # noqa: E402

SCHEMA_VERSION = "orderflow_shadow_data_acceleration_plan_v1"
DEFAULT_LTO011 = Path("research/program_control/LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.json")
DEFAULT_LTO012 = Path("research/program_control/LTO012_SIERRA_LOCAL_DEPTH_CONFLUENCE_2026-05-05.json")
DEFAULT_LTO013 = Path("research/program_control/LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.json")
DEFAULT_OUTPUT_JSON = Path("research/program_control/ORDERFLOW_SHADOW_DATA_ACCELERATION_PLAN_2026-05-05.json")
DEFAULT_OUTPUT_MD = Path("research/program_control/ORDERFLOW_SHADOW_DATA_ACCELERATION_PLAN_2026-05-05.md")

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_signature(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(_file_hash(path)).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def _get(payload: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def build_payload(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    lto011_path: Path = DEFAULT_LTO011,
    lto012_path: Path = DEFAULT_LTO012,
    lto013_path: Path = DEFAULT_LTO013,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    lto011 = read_json(root / lto011_path)
    lto012 = read_json(root / lto012_path)
    lto013 = read_json(root / lto013_path)
    signature = source_signature([root / lto011_path, root / lto012_path, root / lto013_path])

    databento_live_status = _get(lto011, ("status",), "MISSING_LTO011_REPORT")
    databento_license_blocker = bool(_get(lto011, ("status_row", "databento_live_status", "license_blocker"), False))
    sierra_depth_status = _get(lto012, ("status",), "MISSING_LTO012_REPORT")
    sierra_registry_status = _get(lto013, ("status",), "MISSING_LTO013_REPORT")

    status = "SIERRA_ACTIVE_DATABENTO_HISTORICAL_REPLAY_DATABENTO_LIVE_LICENSE_BLOCKED"
    if not databento_license_blocker:
        status = "SIERRA_ACTIVE_DATABENTO_LIVE_COLLECTOR_GATE_AVAILABLE"
    if not lto012 or not lto013:
        status = "ACTION_REQUIRED_MISSING_SIERRA_ARTIFACTS"

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated,
        "status": status,
        "promotion_verdict": PROMOTION_VERDICT,
        "source_dependency_signature": signature,
        "source_paths": [str(lto011_path), str(lto012_path), str(lto013_path)],
        "boundary": (
            "This plan accelerates shadow-data capture and validation only. It does not alter live entries, "
            "filters, risk, execution, prompts, or safety gates."
        ),
        "current_state": {
            "databento": {
                "lto011_status": databento_live_status,
                "live_license_blocker": databento_license_blocker,
                "broker_actual_r_rows_nas100_unique": _get(
                    lto011, ("status_row", "current_counts", "broker_actual_r_rows_nas100_unique"), 0
                ),
                "cached_mbp10_candidate_rows": _get(lto011, ("status_row", "current_counts", "cached_mbp10_candidate_rows"), 0),
                "live_mbp10_candidate_rows": _get(lto011, ("status_row", "current_counts", "live_mbp10_candidate_rows"), 0),
                "declared_nas100_nq_requests": _get(lto011, ("status_row", "current_counts", "declared_nas100_nq_requests"), 0),
                "historical_replay_policy": (
                    "Use Databento historical as post-event replay with features capped at decision_time_utc. "
                    "Do not treat historical availability as same as live feed availability."
                ),
            },
            "sierra": {
                "lto012_status": sierra_depth_status,
                "lto013_status": sierra_registry_status,
                "candidate_rows": _get(lto012, ("status_row", "current_counts", "latest_candidate_rows"), 0),
                "depth_features_extracted": _get(lto012, ("status_row", "current_counts", "features_extracted"), 0),
                "background_queue_candidates": _get(lto012, ("status_row", "current_counts", "background_queue_candidates"), 0),
                "usable_depth_context_rows": _get(lto013, ("current_counts", "usable_depth_context_rows"), 0),
                "blocked_or_no_proxy_rows": _get(lto013, ("current_counts", "blocked_or_no_proxy_rows"), 0),
            },
        },
        "data_comparison": {
            "overlap": [
                "Both can represent futures trade prints and price-level depth for registered futures symbols.",
                "Sierra .depth can approximate MBP-10 style ladder state when source/parity and sampling are registered.",
            ],
            "databento_unique": [
                "Clean API with stable schemas, cost estimation, and reproducible historical/live request records.",
                "MBO order-level events for add, pull, and queue-flow diagnostics that Sierra MBP snapshots do not fully reconstruct.",
                "Canonical programmatic source for cross-session research and replay once licensed for live.",
            ],
            "sierra_unique": [
                "Local live capture and visual heatmap/replay evidence available before a Databento live subscription.",
                ".scid bid/ask-volume and local platform state that can support operator-visible source sanity checks.",
                "Redundant local source for registered futures depth when Databento live is license-blocked.",
            ],
        },
        "ict_to_orderflow_translation": {
            "hypothesis": (
                "Orderflow should not replace GTOS structure first. It should explain the quality of a structural "
                "setup at the decision point, then test whether it improves timing, stop efficiency, target expansion, "
                "or bad-condition vetoes."
            ),
            "feature_families": [
                {
                    "family": "footprint_delta_absorption",
                    "source": "Sierra footprint/.scid bid-ask volume first; Databento trades and MBO later",
                    "examples": [
                        "aggressive buy/sell delta into POI",
                        "delta divergence at retest",
                        "absorption at OB/FVG boundary",
                        "stacked imbalance near entry",
                    ],
                    "decision_role_to_test": "entry_timing_or_veto_shadow_only",
                },
                {
                    "family": "volume_profile_context",
                    "source": "Sierra .scid-derived session profile and operator chart profile",
                    "examples": ["POC proximity", "VAH/VAL reaction", "HVN acceptance", "LVN rejection/air pocket"],
                    "decision_role_to_test": "target_selection_and_rr_expansion_shadow_only",
                },
                {
                    "family": "ladder_depth_liquidity",
                    "source": "Sierra .depth now; Databento MBP-10/MBO for canonical replay/live once licensed",
                    "examples": [
                        "thin depth into entry",
                        "liquidity pull before fill",
                        "near-touch add/remove pressure",
                        "wall concentration",
                    ],
                    "decision_role_to_test": "market_condition_awareness_and_adverse_selection_shadow_only",
                },
            ],
            "success_question": (
                "Given the same GTOS structural candidate, do footprint/profile/depth features explain which rows "
                "deserved wider targets, tighter invalidation, skipped entry, or more patient entry timing?"
            ),
        },
        "execution_lanes": [
            {
                "lane_id": "SIERRA_REGISTRY_FIRST",
                "status": sierra_registry_status,
                "command": "python scripts/audit_sierra_proxy_registry.py",
                "value": "Prevents false confidence by forcing every candidate into validated, caution, blocked, no-proxy, or control-only use.",
            },
            {
                "lane_id": "SIERRA_GUARDED_DEPTH_ENRICHMENT",
                "status": sierra_depth_status,
                "command": "python scripts/enrich_sierra_live_candidate_depth_features.py --max-hours 24 --max-file-size-mb 128 --max-per-symbol 2 --limit 6",
                "value": "Turns local .depth capture into pre-decision shadow features without letting large files stall candidate capture.",
            },
            {
                "lane_id": "SIERRA_FOOTPRINT_AND_VOLUME_PROFILE_DESIGN",
                "status": "NEXT_AFTER_DEPTH_REGISTRY",
                "command": "python scripts/convert_sierra_scid_to_ohlcv.py",
                "value": "Use Sierra .scid as the source for footprint-style bid/ask volume, delta, and volume-profile context around GTOS POIs.",
            },
            {
                "lane_id": "SIERRA_OFF_KZ_BACKGROUND_QUEUE",
                "status": "READY_FOR_OPERATOR_WINDOW",
                "command": "python scripts/enrich_sierra_live_candidate_depth_features.py --max-hours 72 --max-file-size-mb 1024 --max-per-symbol 10 --limit 40",
                "value": "Backfills guarded large-file rows outside active trading windows when runtime is acceptable.",
            },
            {
                "lane_id": "DATABENTO_HISTORICAL_COUNTERFACTUAL_REPLAY",
                "status": "ESTIMATE_FIRST_EXECUTE_ONLY_UNDER_COST_CAP",
                "command": "python scripts/fetch_databento_manifest.py --schema mbp-10 --max-group-cost-usd 1 --max-total-cost-usd 8",
                "value": "Measures what a live Databento collector would have seen, using decision-time cutoffs and no lookahead.",
            },
            {
                "lane_id": "DATABENTO_LIVE_COLLECTOR",
                "status": databento_live_status,
                "command": "python scripts/databento_live_shadow_collector.py",
                "value": "Runs only when the live license/env/cooldown/budget trigger policy allows it.",
            },
            {
                "lane_id": "ACCOUNT_HISTORY_OUTCOME_JOIN",
                "status": "JOIN_ROWS_AS_ACCOUNT_HISTORY_REALIZED_ONLY",
                "command": "python scripts/audit_nas100_orderflow_adverse_selection.py",
                "value": "Orderflow only matters after candidate features join to broker actual-R, costs, and lifecycle truth.",
            },
        ],
        "promotion_gates": [
            "No promotion from source presence, historical replay alone, synthetic labels, or a single proxy-transfer report.",
            "Review after event-count gates, not after a fixed month: each new block of broker actual-R rows should update the dossier.",
            "LTO-011 floors remain the first NAS100 orderflow minimum: 20 broker actual-R rows and 30 MBP10 candidate rows before filter claims.",
            "Any live-filter, signal, risk-modifier, entry-timing, or execution change still requires a separate CEO approval and source/prompt/src diff.",
        ],
        "why_this_is_not_slow_conservative": [
            "Sierra is used now for every captured candidate with registry and depth enrichment lanes.",
            "Databento historical is used aggressively for counterfactual replay under cost caps instead of sitting idle.",
            "Databento live is blocked only by the live data license gate, not by a no-API posture.",
            "Promotion timing is evidence-count driven and can accelerate as soon as forward broker-R rows support it.",
        ],
        **NO_DECISION_COUNTERS,
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).replace("|", r"\|")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_fmt(item) for item in row) + " |")
    return out


def render_markdown(payload: dict[str, Any]) -> str:
    lanes = payload["execution_lanes"]
    state = payload["current_state"]
    lines = [
        "# Orderflow Shadow Data Acceleration Plan - 2026-05-05",
        "",
        f"**Status:** `{payload['status']}`",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Boundary",
        "",
        payload["boundary"],
        "",
        "## Current State",
        "",
        *_table(
            ["Source", "Metric", "Value"],
            [
                ["Databento", key, value] for key, value in state["databento"].items()
            ]
            + [["Sierra", key, value] for key, value in state["sierra"].items()],
        ),
        "",
        "## Execution Lanes",
        "",
        *_table(
            ["Lane", "Status", "Command", "Value"],
            [[row["lane_id"], row["status"], row["command"], row["value"]] for row in lanes],
        ),
        "",
        "## What Each Source Adds",
        "",
        "### Databento Unique",
        "",
        *[f"- {item}" for item in payload["data_comparison"]["databento_unique"]],
        "",
        "### Sierra Unique",
        "",
        *[f"- {item}" for item in payload["data_comparison"]["sierra_unique"]],
        "",
        "## ICT To Orderflow Translation",
        "",
        payload["ict_to_orderflow_translation"]["hypothesis"],
        "",
        *_table(
            ["Family", "Source", "Role To Test"],
            [
                [row["family"], row["source"], row["decision_role_to_test"]]
                for row in payload["ict_to_orderflow_translation"]["feature_families"]
            ],
        ),
        "",
        "## Promotion Gates",
        "",
        *[f"- {item}" for item in payload["promotion_gates"]],
        "",
        "## Acceleration Policy",
        "",
        *[f"- {item}" for item in payload["why_this_is_not_slow_conservative"]],
        "",
    ]
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--lto011", default=str(DEFAULT_LTO011))
    parser.add_argument("--lto012", default=str(DEFAULT_LTO012))
    parser.add_argument("--lto013", default=str(DEFAULT_LTO013))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        root=Path(args.root),
        lto011_path=Path(args.lto011),
        lto012_path=Path(args.lto012),
        lto013_path=Path(args.lto013),
    )
    write_outputs(payload, Path(args.output_json), Path(args.output_md))
    print(
        json.dumps(
            {
                "status": payload["status"],
                "promotion_verdict": payload["promotion_verdict"],
                "sierra_candidate_rows": payload["current_state"]["sierra"]["candidate_rows"],
                "databento_live_license_blocker": payload["current_state"]["databento"]["live_license_blocker"],
                "paid_data_calls_made_by_plan": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
