#!/usr/bin/env python3
"""Session CS: materialize two fixed breaker folds and rerun CQ's ratified gate.

This is an offline, fail-closed evidence driver.  It does three deliberately
separate jobs:

* project one declared S0R0 LANE arm into a compact scoreable pool;
* join that pool to CJ's authenticated true-UTC M1/tick sources and evaluate
  only CQ's already-selected production transform (inverted, target 5D, stop
  0.25D, fixed entry, 120-minute horizon); and
* combine January, April, and bounded-May repair records under the unchanged
  B-balanced gate, using the committed per-capture fold plan.

No grid is rerun.  No geometry, orientation, population, threshold, cost band,
or multiplicity basis is selected here.  February economics and March outcomes
are refused.  The module imports no broker API and reads no token-bound config.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator, Mapping, Sequence

import numpy as np


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.components.current_breaker_re_entry_repair import (  # noqa: E402
    STOP_DISTANCE_D,
    TARGET_DISTANCE_D,
    TRANSFORM_ID,
    apply_current_breaker_re_entry_repair,
)
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.lane_rematerialization import LaneInputRegistry  # noqa: E402
from src.research_infra.training_lane.append_only import (  # noqa: E402
    atomic_write_json,
    read_rows,
)
from src.research_infra.training_lane.graduation import (  # noqa: E402
    DEFAULT_GRADUATION_LEDGER,
)
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    DEFAULT_ITERATION_LEDGER,
    IterationLedger,
)
from src.research_infra.walkforward import era_population  # noqa: E402
from src.research_infra.walkforward.candidate_family import (  # noqa: E402
    ALL_DECLARED,
    load_candidate_family,
    with_declared_family,
)
from src.research_infra.walkforward.gate import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402


AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
HERE = AUDIT / "phase19/receipts"
POOLS = HERE / "pools"
PHASE18 = AUDIT / "phase18/receipts"
PHASE17_COSTS = (
    AUDIT / "phase17/activation_carry_live_cost_truth/files/BROKER_TRUE_COSTS_V1.json"
)
V27 = PHASE18 / "CANDIDATE_FAMILY_V27.json"
FOLD_PLAN = HERE / "CS_BREAKER_FOLD_PLAN_V1.json"
LOOK_ADDENDUM = HERE / "CS_BREAKER_LOOK_ADDENDUM_V1.json"
MAY_AMENDMENT = HERE / "CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1.json"
OUT_GATE = HERE / "CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json"

CQ_TOOL = PHASE18 / "cq_path_pool_grid.py"
CQ_GATE_TOOL = PHASE18 / "cq_repair_gate.py"
CD_POOL_TOOL = AUDIT / "phase14/receipts/cd_pool.py"

SLEEVE = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
ARM_ID = "S0R0"
HORIZON_MINUTES = 120
EXPECTED_COST_SHA256 = "bde450876421bcd0ae0f087e6bfd149838d6fb22a9b6f1cb45e63e3fb28a69bd"
EXPECTED_V27_SHA256 = "b70c512c52e12c37e2ca5c25de13f5eb90afc29ab73253ddab3038c731cf8251"
MAY_REGISTERED_SOURCE_IDENTITY_ROOT = (
    "5af353d542abca340df4eecb759bc1d17ef5893c6f717df6d728a377832ef50b"
)
MAY_EFFECTIVE_SOURCE_IDENTITY_ROOT = (
    "c5417c4be8f52b41fed02b3736701bfa1392d4b7d7ce63d0334ae406abcf2dbb"
)
REPAIR_TRADE_SCHEMA = "gtos-session-cs-current-breaker-repair-trade-v1"
INF_INDEX = np.iinfo(np.int32).max


class CSRefusal(RuntimeError):
    """An evidence, safety, population, or accounting boundary failed closed."""


@dataclass(frozen=True)
class WindowConfig:
    window_id: str
    label: str
    capture_start: str
    capture_end: str
    arm_prefix: str
    surface_look_id: str
    runner_stop_after_day: str | None
    local_train_end: str
    local_oos_start: str
    source_plan: Path
    expected_source_plan_digest: str
    arm_report: Path
    compact_receipt: Path
    compact_pool: Path
    path_manifest: Path
    sidecar: Path
    repair_receipt: Path
    repair_trades: Path
    fixed_look_id: str


WINDOWS = {
    "april_2026": WindowConfig(
        window_id="april_2026",
        label="APRIL",
        capture_start="2026-04-01",
        capture_end="2026-04-30",
        arm_prefix="CS_APRIL_S0R0_V2",
        surface_look_id="CS_APRIL_S0R0_SURFACE_V1",
        runner_stop_after_day=None,
        local_train_end="2026-04-15",
        local_oos_start="2026-04-16",
        source_plan=HERE / "CS_APRIL_SOURCE_PLAN_V1.json",
        expected_source_plan_digest=(
            "3e898fb049904af95c109fd78d555efcd51507aeebc0e0daa765cf8c9f8c0f51"
        ),
        arm_report=HERE / "CS_APRIL_S0R0_ARM_V1.json",
        compact_receipt=HERE / "CS_APRIL_S0R0_POOL_V1.json",
        compact_pool=POOLS / "CS_APRIL_S0R0_POOL_V1.jsonl.gz",
        path_manifest=HERE / "CS_APRIL_PATH_POOL_V1.json",
        sidecar=POOLS / "CS_APRIL_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",
        repair_receipt=HERE / "CS_APRIL_CURRENT_BREAKER_REPAIR_V1.json",
        repair_trades=POOLS / "CS_APRIL_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz",
        fixed_look_id="CS_APRIL_FIXED_BREAKER_FOLD_V1",
    ),
    "may_2026": WindowConfig(
        window_id="may_2026",
        label="MAY",
        capture_start="2026-05-01",
        capture_end="2026-05-30",
        arm_prefix="CS_MAY_S0R0_V1",
        surface_look_id="CS_MAY_S0R0_SURFACE_V1",
        runner_stop_after_day="2026-05-30",
        local_train_end="2026-05-15",
        local_oos_start="2026-05-16",
        source_plan=HERE / "CS_MAY_SOURCE_PLAN_V1.json",
        expected_source_plan_digest=(
            "dc561abf1635bf5b609e73950f9f0fba0ff4d72e100a7eb610c6f594e6dfe956"
        ),
        arm_report=HERE / "CS_MAY_S0R0_ARM_V1.json",
        compact_receipt=HERE / "CS_MAY_S0R0_POOL_V1.json",
        compact_pool=POOLS / "CS_MAY_S0R0_POOL_V1.jsonl.gz",
        path_manifest=HERE / "CS_MAY_PATH_POOL_V1.json",
        sidecar=POOLS / "CS_MAY_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",
        repair_receipt=HERE / "CS_MAY_CURRENT_BREAKER_REPAIR_V1.json",
        repair_trades=POOLS / "CS_MAY_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz",
        fixed_look_id="CS_MAY_FIXED_BREAKER_FOLD_V1",
    ),
}


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CSRefusal(f"cannot_load_reused_tool:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CQ = _load_module(CQ_TOOL, "gtos_session_cs_reused_cq_path_pool_grid")
CQ_GATE = _load_module(CQ_GATE_TOOL, "gtos_session_cs_reused_cq_repair_gate")
CD_POOL = _load_module(CD_POOL_TOOL, "gtos_session_cs_reused_cd_pool")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _native(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_native(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_self_bound(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    body = _native(dict(payload))
    body["self_sha256"] = _canonical_sha256(body)
    atomic_write_json(path, body, indent=1)
    return body


def _read_bound(path: Path, field: str = "self_sha256") -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stated = payload.get(field)
    actual = _canonical_sha256(
        {key: value for key, value in payload.items() if key != field}
    )
    if stated != actual:
        raise CSRefusal(f"self_hash_invalid:{path}:{stated}!={actual}")
    return payload


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def _utc_now() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).isoformat()


def _parse_utc(value: Any) -> dt.datetime:
    return CQ._parse_utc(value)


def _iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    yield from CQ._iter_gzip_jsonl(path)


def _assert_allowed_time(value: Any, config: WindowConfig, *, context: str) -> dt.datetime:
    stamp = _parse_utc(value)
    day = stamp.date().isoformat()
    if day.startswith("2026-02"):
        raise CSRefusal(f"february_economics_forbidden:{context}:{value}")
    if day.startswith("2026-03"):
        raise CSRefusal(f"march_outcomes_forbidden:{context}:{value}")
    if not (config.capture_start <= day <= config.capture_end):
        raise CSRefusal(
            f"timestamp_outside_capture:{context}:{value}:"
            f"{config.capture_start}..{config.capture_end}"
        )
    return stamp


def _validate_arm_report_boundary(
    config: WindowConfig,
    report: Mapping[str, Any],
    ledger: Path,
) -> None:
    """Bind an arm report to its declared effective window and raw route.

    A full provider window records ``stop_after_day=null``; a deliberately
    shortened prefix records the explicit stop.  In both cases the effective
    boundary of economic authority is the partition and lane-authority window.
    """

    partition = report.get("partition_authorization") or {}
    lane_authority = report.get("lane_input_authority") or {}
    expected_ledger_name = f"{config.arm_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    reported_route = Path(str(report.get("route") or ""))
    if (
        report.get("error") is not None
        or report.get("arm") != ARM_ID
        or report.get("window_start") != config.capture_start
        or report.get("stop_after_day") != config.runner_stop_after_day
        or report.get("resolved_window_id") != config.window_id
        or report.get("output_prefix") != config.arm_prefix
        or report.get("outputs_retained") is not True
        or not report.get("fingerprint")
        or report.get("purpose") != "LANE_ITERATION"
        or report.get("repairs_requested")
        != ["commission_broker_true_gated", "swap_horizon_true"]
        or partition.get("window") != [config.capture_start, config.capture_end]
        or partition.get("dominant_surface") != "VAL"
        or partition.get("may_emit_iteration_evidence") is not True
        or lane_authority.get("window") != [config.capture_start, config.capture_end]
        or lane_authority.get("surface") != "VAL"
        or lane_authority.get("campaign_sealed") is not False
        or lane_authority.get("canonical_source_plan_digest_sha256")
        != config.expected_source_plan_digest
    ):
        raise CSRefusal(
            "lane_arm_not_successful_or_wrong_window:"
            f"{report.get('error')}:{report.get('arm')}:"
            f"{report.get('window_start')}..{report.get('stop_after_day')}:"
            f"retained={report.get('outputs_retained')}"
        )
    if (
        not reported_route.is_absolute()
        or reported_route.name != config.arm_prefix
        or ledger.resolve().parent != reported_route.resolve()
        or ledger.name != expected_ledger_name
    ):
        raise CSRefusal(
            "raw_ledger_not_bound_to_reported_route:"
            f"{ledger}:{reported_route}:{expected_ledger_name}"
        )
    runtime_rebinds = lane_authority.get("runtime_verified_rebinds")
    if config.window_id != "may_2026":
        if runtime_rebinds not in (None, {}):
            raise CSRefusal(f"unexpected_full_window_pack_rebind:{config.window_id}")
        return

    if not isinstance(runtime_rebinds, Mapping):
        raise CSRefusal("may_prefix_pack_rebind_proof_missing")
    proof = runtime_rebinds.get("prefix_pack_source_identity_rebind")
    accepted_days = runtime_rebinds.get("prefix_pack_rebind_accepted_days")
    if not isinstance(proof, Mapping):
        raise CSRefusal("may_prefix_pack_rebind_proof_missing")
    proof_core = dict(proof)
    proof_root = proof_core.pop("authority_root_sha256", None)
    capture_start = dt.date.fromisoformat(config.capture_start)
    capture_end = dt.date.fromisoformat(config.capture_end)
    expected_days = [
        (capture_start + dt.timedelta(days=offset)).isoformat()
        for offset in range((capture_end - capture_start).days + 1)
    ]
    if (
        proof.get("schema")
        != "gtos.lane.rematerialization.prefix_pack_source_rebind.v1"
        or proof.get("status") != "VERIFIED_PREFIX_PACK_SOURCE_IDENTITY_REBIND"
        or proof.get("window_id") != config.window_id
        or proof.get("registered_window") != ["2026-05-01", "2026-05-31"]
        or proof.get("effective_window") != [config.capture_start, config.capture_end]
        or proof.get("registered_source_identity_root_sha256")
        != MAY_REGISTERED_SOURCE_IDENTITY_ROOT
        or proof.get("effective_source_identity_root_sha256")
        != MAY_EFFECTIVE_SOURCE_IDENTITY_ROOT
        or proof.get("source_manifest_root_sha256")
        != lane_authority.get("source_manifest_root_sha256")
        or proof.get("effective_source_plan_digest_sha256")
        != config.expected_source_plan_digest
        or proof.get("retained_pack_count") != 30
        or proof.get("excluded_registered_packs")
        != [["lane_validation", "2026-05-31", "2026-05-31"]]
        or proof.get("allowed_binding_difference")
        != ["source_identity_root_sha256"]
        or proof.get("source_manifest_unchanged") is not True
        or proof.get("retained_daily_pack_roots_are_exact_registry_subset") is not True
        or proof.get("pack_contents_remain_authenticated_per_reader_before_use")
        is not True
        or proof.get("economic_outcomes_read") is not False
        or proof.get("march_outcomes_read") is not False
        or proof.get("broker_live_authority") is not False
        or proof.get("broker_mutation_enabled") is not False
        or proof_root != _canonical_sha256(proof_core)
        or not isinstance(accepted_days, list)
        or len(accepted_days) != len(expected_days)
        or sorted(str(day) for day in accepted_days) != expected_days
    ):
        raise CSRefusal("may_prefix_pack_rebind_proof_invalid")


def _validate_predeclared_contracts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Prove the executable constants still match CS's pre-outcome declarations."""

    fold_plan = _read_bound(FOLD_PLAN)
    look_addendum = _read_bound(LOOK_ADDENDUM)
    may_amendment = _read_bound(MAY_AMENDMENT)
    candidate = fold_plan.get("candidate") or {}
    path_contract = fold_plan.get("path_contract") or {}
    gate_contract = fold_plan.get("gate_contract") or {}
    candidate_path = REPO / str(candidate.get("implementation") or "")
    prior_gate_path = REPO / str(gate_contract.get("prior_receipt") or "")
    look_rows = look_addendum.get("predeclared_validation_looks") or []
    look_by_id = {str(row.get("look_id") or ""): row for row in look_rows}
    expected_look_ids = {
        WINDOWS["april_2026"].surface_look_id,
        WINDOWS["april_2026"].fixed_look_id,
        WINDOWS["may_2026"].surface_look_id,
        WINDOWS["may_2026"].fixed_look_id,
    }
    if (
        fold_plan.get("status") != "FROZEN_BEFORE_APRIL_OR_MAY_ECONOMIC_DECODE"
        or candidate.get("transform_id") != TRANSFORM_ID
        or candidate.get("entry_rule")
        != "preserve the recorded decision timestamp and entry price"
        or candidate.get("direction_rule") != "invert the recorded direction"
        or float(candidate.get("target_distance_D") or -1) != TARGET_DISTANCE_D
        or float(candidate.get("stop_distance_D") or -1) != STOP_DISTANCE_D
        or int(candidate.get("horizon_minutes") or -1) != HORIZON_MINUTES
        or candidate.get("selection_is_frozen") is not True
        or candidate.get("grid_will_not_be_rerun") is not True
        or not candidate_path.is_file()
        or _sha256_file(candidate_path)
        != candidate.get("implementation_sha256")
        or path_contract.get("source") != _repo_path(CQ_TOOL)
        or _sha256_file(CQ_TOOL) != path_contract.get("source_sha256")
        or gate_contract.get("population") != "RECORDED"
        or gate_contract.get("option") != "B_balanced"
        or gate_contract.get("account") != "FTMO"
        or gate_contract.get("server") != "FTMO-Server3"
        or gate_contract.get("spread_band") != "mid"
        or float(gate_contract.get("alpha") or -1) != 0.10
        or gate_contract.get("cost_artifact_sha256") != EXPECTED_COST_SHA256
        or gate_contract.get("candidate_family_declaration_sha256")
        != EXPECTED_V27_SHA256
        or not prior_gate_path.is_file()
        or _sha256_file(prior_gate_path)
        != gate_contract.get("prior_receipt_sha256")
        or int(gate_contract.get("declared_family_size") or -1) != 59
        or int(gate_contract.get("looks_taken_size") or -1) != 57
        or int(gate_contract.get("min_folds_evaluable") or -1) != 3
        or look_addendum.get("status")
        != "FROZEN_BEFORE_APRIL_OR_MAY_ECONOMIC_DECODE"
        or int(look_addendum.get("total_new_val_looks") or -1) != 4
        or look_addendum.get("new_candidate_hypotheses") != 0
        or look_addendum.get("new_graduation_bills") != 0
        or {str(row.get("look_id") or "") for row in look_rows}
        != expected_look_ids
        or look_by_id[WINDOWS["april_2026"].surface_look_id].get("window")
        != ["2026-04-01", "2026-04-30"]
        or look_by_id[WINDOWS["april_2026"].fixed_look_id].get("window")
        != ["2026-04-01", "2026-04-30"]
        or may_amendment.get("status") != "FROZEN_BEFORE_MAY_ECONOMIC_DECODE"
        or (may_amendment.get("revised_may_fold") or {}).get("capture_window")
        != ["2026-05-01", "2026-05-30"]
        or (may_amendment.get("revised_may_fold") or {}).get("local_train")
        != ["2026-05-01", "2026-05-15"]
        or (may_amendment.get("revised_may_fold") or {}).get("oos")
        != ["2026-05-16", "2026-05-30"]
        or (may_amendment.get("look_accounting") or {}).get(
            "new_graduation_bill"
        )
        is not False
        or (may_amendment.get("look_accounting") or {}).get(
            WINDOWS["may_2026"].surface_look_id
        )
        != ["2026-05-01", "2026-05-30"]
        or (may_amendment.get("look_accounting") or {}).get(
            WINDOWS["may_2026"].fixed_look_id
        )
        != ["2026-05-01", "2026-05-30"]
    ):
        raise CSRefusal("predeclared_breaker_contract_drift")
    return fold_plan, look_addendum, may_amendment


def compact_arm(
    config: WindowConfig,
    *,
    ledger: Path,
    arm_report: Path | None = None,
) -> dict[str, Any]:
    """Project one declared arm with CD's reader-complete compact contract."""

    report_path = arm_report or config.arm_report
    if not ledger.is_file() or not report_path.is_file():
        raise CSRefusal(f"compact_input_missing:{ledger}:{report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    _validate_arm_report_boundary(config, report, ledger)
    config.compact_pool.parent.mkdir(parents=True, exist_ok=True)
    summary = CD_POOL.summarise(ledger, config.compact_pool)
    pool_rows, pool_meta = _load_pool_file(config, require_receipt=False)
    stated = summary.get("diagnostic_scoreable_rows")
    if stated is None or int(stated) != len(pool_rows):
        raise CSRefusal(
            f"compact_scoreable_count_mismatch:{stated}!={len(pool_rows)}"
        )
    source_plan = _read_bound(config.source_plan, "receipt_root_sha256")
    payload = _write_self_bound(
        config.compact_receipt,
        {
            "schema": "gtos-session-cs-compact-s0r0-pool-v1",
            "generated_at_utc": _utc_now(),
            "source_head": _git_head(),
            "surface": "VAL",
            "billed": False,
            "window_id": config.window_id,
            "capture_window": [config.capture_start, config.capture_end],
            "source_arm_id": ARM_ID,
            "raw_ledger": {
                "path": _repo_path(ledger),
                "sha256": _sha256_file(ledger),
                "bytes": ledger.stat().st_size,
            },
            "arm_report": {
                "path": _repo_path(report_path),
                "sha256": _sha256_file(report_path),
            },
            "canonical_source_plan": {
                "path": _repo_path(config.source_plan),
                "receipt_root_sha256": source_plan["receipt_root_sha256"],
                "canonical_source_plan_digest_sha256": source_plan[
                    "canonical_source_plan_digest_sha256"
                ],
            },
            "compact_pool": pool_meta,
            "cd_reader_complete_summary": summary,
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "selection_authority": "NONE_SUBSTRATE_ONLY",
            "status": "DECLARED_S0R0_SURFACE_COMPACTED",
        },
    )
    return payload


def _load_pool_file(
    config: WindowConfig,
    *,
    require_receipt: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if require_receipt:
        receipt = _read_bound(config.compact_receipt)
        expected = receipt.get("compact_pool") or {}
        digest = _sha256_file(config.compact_pool)
        if digest != expected.get("sha256"):
            raise CSRefusal(
                f"compact_pool_hash_mismatch:{digest}!={expected.get('sha256')}"
            )
    rows = list(_iter_gzip_jsonl(config.compact_pool))
    if not rows:
        raise CSRefusal(f"compact_pool_empty:{config.window_id}")
    required = {
        "candidate_id",
        "decision_time_utc",
        "symbol",
        "side",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "cost_r",
        "opportunity_net_proxy_r",
        "origin_family",
    }
    missing = sorted(required - set(rows[0]))
    if missing:
        raise CSRefusal(f"compact_pool_required_fields_missing:{','.join(missing)}")
    keys: set[tuple[str, str, str]] = set()
    dates: set[str] = set()
    for index, row in enumerate(rows):
        row_missing = sorted(required - set(row))
        if row_missing:
            raise CSRefusal(
                f"compact_pool_required_fields_missing_at_{index}:"
                + ",".join(row_missing)
            )
        decision = _assert_allowed_time(
            row.get("decision_time_utc"), config, context=f"pool_row_{index}"
        )
        decision_iso = decision.isoformat()
        key = (ARM_ID, str(row.get("candidate_id") or ""), decision_iso)
        if not key[1] or key in keys:
            raise CSRefusal(f"compact_pool_join_key_invalid_or_duplicate:{key}")
        if (
            not str(row.get("symbol") or "")
            or str(row.get("side") or "").upper() not in {"LONG", "SHORT"}
            or not str(row.get("origin_family") or "")
        ):
            raise CSRefusal(f"compact_pool_identity_invalid:{key}")
        keys.add(key)
        dates.add(decision.date().isoformat())
        try:
            entry = float(row["entry_price"])
            stop = float(row["stop_loss"])
            values = (
                entry,
                stop,
                float(row["take_profit_1"]),
                float(row["cost_r"]),
                float(row["opportunity_net_proxy_r"]),
            )
        except (TypeError, ValueError) as exc:
            raise CSRefusal(f"compact_pool_numeric_invalid:{key}") from exc
        if not all(math.isfinite(value) for value in values) or entry == stop:
            raise CSRefusal(f"compact_pool_geometry_invalid:{key}")
    return rows, {
        "path": _repo_path(config.compact_pool),
        "sha256": _sha256_file(config.compact_pool),
        "rows": len(rows),
        "unique_join_keys": len(keys),
        "dates": sorted(dates),
        "train_dates": sorted(day for day in dates if day <= config.local_train_end),
        "oos_dates": sorted(day for day in dates if day >= config.local_oos_start),
    }


def _lane_authority(config: WindowConfig, registry_path: Path):
    source_plan = _read_bound(config.source_plan, "receipt_root_sha256")
    if (
        source_plan.get("canonical_source_plan_digest_sha256")
        != config.expected_source_plan_digest
        or source_plan.get("window")
        != [config.capture_start, config.capture_end]
        or source_plan.get("economic_outcomes_read") is not False
        or source_plan.get("march_outcomes_read") is not False
    ):
        raise CSRefusal(f"canonical_source_plan_boundary_invalid:{config.window_id}")
    resolved = LaneInputRegistry(registry_path).resolve(
        window_id=config.window_id,
        purpose="LANE_ITERATION",
    )
    bounded = resolved.for_prefix(config.capture_end)
    manifest = dict(bounded.source_manifest)
    if (
        bounded.window.start != config.capture_start
        or bounded.window.end != config.capture_end
        or bounded.entry.get("surface") != "VAL"
        or bounded.entry.get("campaign_sealed") is not False
        or manifest.get("economic_outcomes_read") is not False
        or manifest.get("window_id") != config.window_id
        or (manifest.get("clock") or {}).get("time_column_basis") != "true_utc"
        or manifest.get("time_column_basis") == "broker_wall_clock"
        or str(bounded.registry["registry_root_sha256"])
        != source_plan.get("registry_root_sha256")
        or str(manifest["manifest_root_sha256"])
        != source_plan.get("source_manifest_root_sha256")
    ):
        raise CSRefusal(f"lane_authority_boundary_invalid:{config.window_id}")
    disclosure = str(manifest.get("march_source_only_disclosure") or "")
    if config.window_id == "april_2026" and "March" not in disclosure:
        raise CSRefusal("april_march_lookback_disclosure_missing")
    return CQ.LaneAuthority(
        registry_path=bounded.registry_path,
        registry_root_sha256=str(bounded.registry["registry_root_sha256"]),
        manifest_path=bounded.source_manifest_path,
        manifest_root_sha256=str(manifest["manifest_root_sha256"]),
        manifest=manifest,
        pack_count=len(bounded.pack_roots),
    ), source_plan


def _source_records(authority) -> tuple[dict[str, Any], dict[str, Any]]:
    m1: dict[str, Any] = {}
    tick: dict[str, Any] = {}
    for raw in authority.manifest.get("bar_sources") or []:
        if raw.get("timeframe") != "M1":
            continue
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        logical = str(raw.get("lane_relpath") or "")
        record = CQ.SourceRecord(
            symbol=symbol,
            timeframe="M1",
            logical_path=logical,
            path=CQ._safe_lane_path(authority, logical),
            sha256=str(raw.get("sha256") or ""),
            row_count=int(raw.get("row_count") or 0),
        )
        if symbol in m1:
            raise CSRefusal(f"duplicate_m1_source:{symbol}")
        m1[symbol] = record
    for raw in authority.manifest.get("tick_sources") or []:
        if raw.get("timeframe") != "TICK":
            continue
        symbol = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        logical = str(raw.get("lane_relpath") or "")
        record = CQ.SourceRecord(
            symbol=symbol,
            timeframe="TICK",
            logical_path=logical,
            path=CQ._safe_lane_path(authority, logical),
            sha256=str(raw.get("sha256") or ""),
            row_count=int(raw.get("row_count") or 0),
        )
        if symbol in tick:
            raise CSRefusal(f"duplicate_tick_source:{symbol}")
        tick[symbol] = record
    if len(m1) != 24:
        raise CSRefusal(f"m1_source_count:{len(m1)}!=24")
    expected_ticks = int(authority.manifest.get("tick_symbol_count") or 0)
    if len(tick) != expected_ticks:
        raise CSRefusal(f"tick_source_count:{len(tick)}!={expected_ticks}")
    for record in [*m1.values(), *tick.values()]:
        digest = _sha256_file(record.path)
        if digest != record.sha256:
            raise CSRefusal(
                f"lane_source_hash_mismatch:{record.logical_path}:"
                f"{digest}!={record.sha256}"
            )
    return m1, tick


def build_path_sidecar(
    config: WindowConfig,
    *,
    registry_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Build CQ's one-row-per-candidate path sidecar without scoring a grid."""

    protocol = CQ.load_protocol()
    contract = CQ.load_path_contract()
    _validate_predeclared_contracts()
    authority, source_plan = _lane_authority(config, registry_path)
    pool_rows, pool_meta = _load_pool_file(config)
    m1_sources, tick_sources = _source_records(authority)
    missing = sorted({str(row["symbol"]) for row in pool_rows} - set(m1_sources))
    if missing:
        raise CSRefusal(f"pool_symbols_without_m1:{','.join(missing)}")

    series_by_symbol: dict[str, Any] = {}
    source_inventory: dict[str, Any] = {}
    for symbol in sorted(m1_sources):
        source = m1_sources[symbol]
        series_by_symbol[symbol] = CQ.load_m1(source)
        source_inventory[symbol] = {
            "m1": {
                "path": source.logical_path,
                "sha256": source.sha256,
                "rows": source.row_count,
            },
            "tick": (
                {
                    "path": tick_sources[symbol].logical_path,
                    "sha256": tick_sources[symbol].sha256,
                    "rows": tick_sources[symbol].row_count,
                }
                if symbol in tick_sources
                else None
            ),
        }

    observation_count = 0
    min_observations: int | None = None
    max_observations = 0
    tick_pointer_rows = 0
    with CQ._DeterministicGzipWriter(config.sidecar) as handle:
        for index, row in enumerate(pool_rows):
            symbol = str(row["symbol"])
            decision = _assert_allowed_time(
                row["decision_time_utc"], config, context=f"sidecar_row_{index}"
            )
            horizon = decision + dt.timedelta(minutes=HORIZON_MINUTES)
            _assert_allowed_time(
                horizon,
                config,
                context=f"sidecar_horizon_{index}",
            )
            observations = CQ.slice_observations(
                series_by_symbol[symbol],
                decision=decision,
                horizon=horizon,
            )
            count = len(observations)
            observation_count += count
            min_observations = (
                count if min_observations is None else min(min_observations, count)
            )
            max_observations = max(max_observations, count)
            tick = tick_sources.get(symbol)
            if tick is not None:
                tick_pointer_rows += 1
            source = m1_sources[symbol]
            projected = {
                "schema": CQ.SIDECAR_SCHEMA,
                "arm_id": ARM_ID,
                "candidate_id": str(row["candidate_id"]),
                "decision_time_utc": decision.isoformat(),
                "horizon_end_utc": horizon.isoformat(),
                "symbol": symbol,
                "side": str(row["side"]).upper(),
                "source_timeframe": "M1",
                "source_path": source.logical_path,
                "source_sha256": source.sha256,
                "ordered_tick_source": (
                    {
                        "timeframe": "TICK",
                        "path": tick.logical_path,
                        "source_sha256": tick.sha256,
                        "row_count": tick.row_count,
                        "selection_rule": "ordered_tick_priority_over_m1",
                    }
                    if tick is not None
                    else None
                ),
                "ordered_path_observations": list(observations),
            }
            handle.write(
                json.dumps(
                    projected,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )

    manifest = _write_self_bound(
        config.path_manifest,
        {
            "schema": "gtos-session-cs-path-complete-pool-v1",
            "generated_at_utc": _utc_now(),
            "source_head": _git_head(),
            "surface": "VAL",
            "billed": False,
            "campaign_sealed": False,
            "window_id": config.window_id,
            "window": [config.capture_start, config.capture_end],
            "arm_id": ARM_ID,
            "horizon_minutes": HORIZON_MINUTES,
            "path_contract": _repo_path(CQ.DEFAULT_CONTRACT),
            "path_contract_sha256": _sha256_file(CQ.DEFAULT_CONTRACT),
            "path_contract_self_sha256": contract.get("self_sha256"),
            "path_contract_scope": (
                "sidecar_contract subsection only; the contract's January input "
                "inventory is not reused"
            ),
            "protocol": _repo_path(CQ.DEFAULT_PROTOCOL),
            "protocol_sha256": _sha256_file(CQ.DEFAULT_PROTOCOL),
            "protocol_status": protocol.get("status"),
            "canonical_source_plan": {
                "path": _repo_path(config.source_plan),
                "receipt_root_sha256": source_plan["receipt_root_sha256"],
                "canonical_source_plan_digest_sha256": source_plan[
                    "canonical_source_plan_digest_sha256"
                ],
            },
            "base_pool": pool_meta,
            "sidecar": {
                "path": _repo_path(config.sidecar),
                "sha256": _sha256_file(config.sidecar),
                "schema": CQ.SIDECAR_SCHEMA,
                "rows": len(pool_rows),
                "unique_join_keys": len(pool_rows),
                "observation_rows": observation_count,
                "min_observations_per_candidate": min_observations,
                "max_observations_per_candidate": max_observations,
                "tick_pointer_rows": tick_pointer_rows,
            },
            "lane_authority": {
                "registry_path": str(authority.registry_path),
                "registry_root_sha256": authority.registry_root_sha256,
                "source_manifest_path": str(authority.manifest_path),
                "source_manifest_root_sha256": authority.manifest_root_sha256,
                "pack_count": authority.pack_count,
                "purpose": "LANE_ITERATION",
                "clock_rule": (authority.manifest.get("clock") or {}).get(
                    "broker_clock_rule"
                ),
                "time_column_basis": "true_utc",
                "external_estate_boundary": "machine_local_read_only",
            },
            "source_inventory": source_inventory,
            "invariants": {
                "one_sidecar_row_per_pool_row": True,
                "unique_join_key": True,
                "strictly_increasing_observation_times": True,
                "first_observation_strictly_after_decision": True,
                "last_observation_at_or_before_120_minute_horizon": True,
                "all_source_hashes_authenticated": True,
                "ordered_tick_priority_content_bound_where_available": True,
                "path_outcomes_scored_while_building_sidecar": False,
            },
            "march_source_lookback_rows_present": bool(
                authority.manifest.get("march_source_only_disclosure")
            ),
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "status": "PATH_COMPLETE_POOL_MATERIALIZED_WITHOUT_GRID",
        },
    )
    return manifest, pool_rows, m1_sources, tick_sources


def _fixed_path_summaries(
    config: WindowConfig,
    *,
    pool_rows: Sequence[Mapping[str, Any]],
    tick_sources: Mapping[str, Any],
) -> tuple[dict[int, Any], dict[str, Any]]:
    """Score only the already-selected inverted breaker transform."""

    targets = np.asarray([TARGET_DISTANCE_D], dtype=np.float64)
    stops = np.asarray([STOP_DISTANCE_D], dtype=np.float64)
    breaker_indices = [
        index
        for index, row in enumerate(pool_rows)
        if str(row.get("origin_family") or "") == "current_breaker_re_entry"
    ]
    if not breaker_indices:
        raise CSRefusal(f"breaker_population_empty:{config.window_id}")
    breaker_set = set(breaker_indices)
    summaries: dict[int, Any] = {}
    tick_rows: dict[str, list[int]] = {}
    sidecar = _iter_gzip_jsonl(config.sidecar)
    for index, pool_row in enumerate(pool_rows):
        try:
            path_row = next(sidecar)
        except StopIteration as exc:
            raise CSRefusal(f"sidecar_ended_early:{index}") from exc
        expected = (
            ARM_ID,
            str(pool_row["candidate_id"]),
            _parse_utc(pool_row["decision_time_utc"]).isoformat(),
        )
        actual = (
            str(path_row.get("arm_id") or ""),
            str(path_row.get("candidate_id") or ""),
            str(path_row.get("decision_time_utc") or ""),
        )
        if actual != expected:
            raise CSRefusal(f"sidecar_join_mismatch:{index}:{actual}!={expected}")
        if (
            path_row.get("schema") != CQ.SIDECAR_SCHEMA
            or str(path_row.get("symbol") or "") != str(pool_row["symbol"])
            or str(path_row.get("side") or "").upper()
            != str(pool_row["side"]).upper()
        ):
            raise CSRefusal(f"sidecar_identity_mismatch:{index}:{actual}")
        if index not in breaker_set:
            continue
        decision = _assert_allowed_time(
            actual[2], config, context=f"fixed_breaker_path_{index}"
        )
        horizon = _parse_utc(path_row.get("horizon_end_utc"))
        if horizon != decision + dt.timedelta(minutes=HORIZON_MINUTES):
            raise CSRefusal(f"sidecar_horizon_mismatch:{actual}")
        observations = path_row.get("ordered_path_observations")
        if not isinstance(observations, list) or not observations:
            raise CSRefusal(f"sidecar_observations_missing:{actual}")
        entry = float(pool_row["entry_price"])
        base_distance = abs(entry - float(pool_row["stop_loss"]))
        declared_side = str(pool_row["side"]).upper()
        inverted_side = "SHORT" if declared_side == "LONG" else "LONG"
        # Reuse CQ's frozen conservative M1 implementation. The recorded-target
        # fields it also returns are ignored; only the one declared target/stop
        # element is ever read below.
        summaries[index] = CQ.summarize_ohlc_path(
            observations=observations,
            entry=entry,
            base_distance=base_distance,
            side=inverted_side,
            targets=targets,
            stops=stops,
            recorded_target_d=TARGET_DISTANCE_D,
        )
        if str(pool_row["symbol"]) in tick_sources:
            tick_rows.setdefault(str(pool_row["symbol"]), []).append(index)
    try:
        extra = next(sidecar)
    except StopIteration:
        extra = None
    if extra is not None:
        raise CSRefusal("sidecar_has_extra_rows")

    ordered_tick_rows = 0
    m1_fallback_rows = 0
    per_symbol: dict[str, Any] = {}
    for symbol in sorted(tick_rows):
        record = tick_sources[symbol]
        series = CQ.load_ticks(record)
        used = fallback = 0
        for index in tick_rows[symbol]:
            row = pool_rows[index]
            decision = _parse_utc(row["decision_time_utc"])
            entry = float(row["entry_price"])
            base_distance = abs(entry - float(row["stop_loss"]))
            inverted_side = (
                "SHORT" if str(row["side"]).upper() == "LONG" else "LONG"
            )
            summary = CQ.summarize_tick_path(
                series=series,
                decision=decision,
                horizon=decision + dt.timedelta(minutes=HORIZON_MINUTES),
                entry=entry,
                base_distance=base_distance,
                side=inverted_side,
                targets=targets,
                stops=stops,
                recorded_target_d=TARGET_DISTANCE_D,
            )
            if summary is None:
                fallback += 1
                m1_fallback_rows += 1
            else:
                summaries[index] = summary
                used += 1
                ordered_tick_rows += 1
        per_symbol[symbol] = {
            "breaker_pool_rows": len(tick_rows[symbol]),
            "ordered_tick_rows": used,
            "m1_fallback_rows": fallback,
            "source_path": record.logical_path,
            "source_sha256": record.sha256,
            "source_rows": record.row_count,
        }
    return summaries, {
        "breaker_rows": len(breaker_indices),
        "ordered_tick_rows": ordered_tick_rows,
        "m1_fallback_rows_on_tick_symbols": m1_fallback_rows,
        "m1_conservative_rows": len(breaker_indices) - ordered_tick_rows,
        "per_symbol": per_symbol,
    }


def _split_for(config: WindowConfig, decision: dt.datetime) -> str:
    day = decision.date().isoformat()
    return "TRAIN" if day <= config.local_train_end else "OOS"


def _candidate_time_key(candidate_id: Any, decision: dt.datetime) -> tuple[str, str]:
    """Return the lane's composite identity for a candidate occurrence.

    The production transform intentionally does not put decision time into its
    candidate-id digest.  The same semantic source/geometry may therefore recur
    at a later decision without being the same trade occurrence.
    """

    value = str(candidate_id or "")
    if not value:
        raise CSRefusal("candidate_time_key_missing_candidate_id")
    return value, decision.isoformat()


def _record_fixed_look(
    config: WindowConfig,
    *,
    metric: float,
    receipt: Path,
) -> dict[str, Any]:
    matches = [
        row
        for row in read_rows(DEFAULT_ITERATION_LEDGER)
        if row.get("session") == "CS"
        and (row.get("extra") or {}).get("look_id") == config.fixed_look_id
    ]
    if len(matches) > 1:
        raise CSRefusal(f"fixed_look_duplicate:{config.fixed_look_id}:{len(matches)}")
    if matches:
        row = matches[0]
        if (
            row.get("date_span") != [config.capture_start, config.capture_end]
            or row.get("surface") != "VAL"
            or bool(row.get("billed"))
            or row.get("receipt") != _repo_path(receipt)
        ):
            raise CSRefusal(f"existing_fixed_look_boundary_invalid:{config.fixed_look_id}")
        return row
    look_spec = {
        "source_arm_id": ARM_ID,
        "population": "current_breaker_re_entry",
        "candidate_transform_id": TRANSFORM_ID,
        "entry_rule": "fixed",
        "orientation": "inverted",
        "target_distance_D": TARGET_DISTANCE_D,
        "stop_distance_D": STOP_DISTANCE_D,
        "horizon_minutes": HORIZON_MINUTES,
        "path_semantics": "ordered_tick_priority_else_m1_ambiguous_conservative_stop",
    }
    ledger = IterationLedger(
        DEFAULT_ITERATION_LEDGER,
        session="CS",
        run_id=config.fixed_look_id,
    )
    return ledger.record(
        mechanism="true_utc_path_complete_fixed_breaker_validation",
        sleeve=SLEEVE,
        spec=look_spec,
        engine_version="gtos.session_cs.breaker_folds.v1",
        start=config.capture_start,
        end=config.capture_end,
        verdict="evaluated",
        metric=metric,
        metric_name="local_oos_mean_grid_net_r_fixed_transform",
        note=(
            "Unbilled validation of CQ's already-selected fixed transform. No geometry, "
            "orientation, population, threshold, or candidate was selected in this look."
        ),
        receipt=_repo_path(receipt),
        extra={
            "look_id": config.fixed_look_id,
            "decision_authority": "RATIFIED_GATE_INPUT",
            "new_candidate_hypothesis": False,
            "new_graduation_bill": False,
        },
    )


def materialize_fixed_repair(
    config: WindowConfig,
    *,
    registry_path: Path,
) -> dict[str, Any]:
    """Build path authority and exact production-transform TradeRecords."""

    path_manifest, pool_rows, _m1_sources, tick_sources = build_path_sidecar(
        config,
        registry_path=registry_path,
    )
    summaries, path_modes = _fixed_path_summaries(
        config,
        pool_rows=pool_rows,
        tick_sources=tick_sources,
    )
    breaker_indices = sorted(summaries)
    breaker_rows = [pool_rows[index] for index in breaker_indices]
    breaker_masks = {
        "TRAIN": np.asarray(
            [
                str(row["decision_time_utc"])[:10] <= config.local_train_end
                for row in breaker_rows
            ],
            dtype=bool,
        ),
        "OOS": np.asarray(
            [
                str(row["decision_time_utc"])[:10] >= config.local_oos_start
                for row in breaker_rows
            ],
            dtype=bool,
        ),
        "FULL": np.ones(len(breaker_rows), dtype=bool),
    }
    base_costs, cost_report = CQ._broker_true_cost_vector(
        breaker_rows,
        breaker_masks,
        np.zeros(len(breaker_rows), dtype=bool),
    )
    if (
        len(base_costs) != len(breaker_rows)
        or not np.isfinite(base_costs).all()
        or np.any(base_costs < 0.0)
        or int(cost_report.get("rows_repriced") or -1) != len(breaker_rows)
    ):
        raise CSRefusal(f"broker_true_cost_vector_invalid:{config.window_id}")

    split_values = {
        split: {"gross": [], "grid_cost": [], "grid_net": []}
        for split in ("TRAIN", "OOS", "FULL")
    }
    split_counts = {"TRAIN": 0, "OOS": 0}
    ambiguity = {"TRAIN": 0, "OOS": 0, "FULL": 0}
    outcomes: dict[str, int] = {}
    source_modes: dict[str, int] = {}
    source_keys: set[tuple[str, str]] = set()
    transformed_ids: set[str] = set()
    transformed_keys: set[tuple[str, str]] = set()
    min_exit: str | None = None
    max_exit: str | None = None

    with CQ._DeterministicGzipWriter(config.repair_trades) as handle:
        for position, index in enumerate(breaker_indices):
            row = pool_rows[index]
            summary = summaries[index]
            target_index = int(summary.target_index[0])
            stop_index = int(summary.stop_index[0])
            if target_index < stop_index:
                outcome = "TARGET"
                exit_us = int(summary.target_time_us[0])
                gross_r = TARGET_DISTANCE_D / STOP_DISTANCE_D
            elif stop_index < target_index:
                outcome = "STOP"
                exit_us = int(summary.stop_time_us[0])
                gross_r = -1.0
            elif target_index != INF_INDEX:
                outcome = "AMBIGUOUS_CONSERVATIVE_STOP"
                exit_us = int(summary.stop_time_us[0])
                gross_r = -1.0
            else:
                outcome = "HORIZON"
                exit_us = int(summary.terminal_time_us)
                gross_r = float(summary.terminal_signed_d) / STOP_DISTANCE_D

            decision = _assert_allowed_time(
                row["decision_time_utc"], config, context=f"repair_entry_{index}"
            )
            exit_utc = _parse_utc(CQ._iso_from_epoch_us(exit_us))
            if not (
                decision < exit_utc
                <= decision + dt.timedelta(minutes=HORIZON_MINUTES)
            ):
                raise CSRefusal(f"repair_exit_outside_horizon:{index}:{exit_utc}")
            if not (
                config.capture_start
                <= exit_utc.date().isoformat()
                <= config.capture_end
            ):
                raise CSRefusal(
                    f"repair_exit_outside_capture:{index}:{exit_utc.isoformat()}"
                )
            candidate_input = CQ._repair_candidate_input(row)
            repaired = apply_current_breaker_re_entry_repair(
                candidate_input,
                enabled=True,
            )
            if repaired.get("candidate_transform_id") != TRANSFORM_ID:
                raise CSRefusal(f"production_transform_identity_mismatch:{index}")
            entry = float(repaired["entry_price"])
            stop = float(repaired["stop_loss"])
            target = float(repaired["take_profit_1"])
            base_distance = abs(float(row["entry_price"]) - float(row["stop_loss"]))
            sl_distance = abs(entry - stop)
            expected_side = (
                "SHORT" if str(row["side"]).upper() == "LONG" else "LONG"
            )
            if not (
                str(repaired.get("side") or "") == expected_side
                and math.isclose(
                    entry,
                    float(row["entry_price"]),
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    sl_distance,
                    base_distance * STOP_DISTANCE_D,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    abs(target - entry),
                    base_distance * TARGET_DISTANCE_D,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
            ):
                raise CSRefusal(f"repair_transform_geometry_mismatch:{index}")
            grid_cost_r = float(base_costs[position]) / STOP_DISTANCE_D
            grid_net_r = gross_r - grid_cost_r
            split = _split_for(config, decision)
            broker_symbol = CQ.FTMO_BROKER_SYMBOLS.get(
                str(row["symbol"]), str(row["symbol"])
            )
            source_mode = str(summary.source_mode)
            trade = {
                "schema": REPAIR_TRADE_SCHEMA,
                "sleeve": SLEEVE,
                "source_arm_id": ARM_ID,
                "source_window_id": config.window_id,
                "source_candidate_id": str(row["candidate_id"]),
                "repaired_candidate_id": str(repaired["candidate_id"]),
                "decision_split": split,
                "symbol": str(row["symbol"]),
                "broker_symbol": broker_symbol,
                "entry_utc": decision.isoformat(),
                "exit_utc": exit_utc.isoformat(),
                "direction": 1 if str(repaired["side"]) == "LONG" else -1,
                "side": str(repaired["side"]),
                "entry_price": entry,
                "sl_distance_price": sl_distance,
                "stop_loss": stop,
                "take_profit_1": target,
                "r_gross": gross_r,
                "grid_cost_r": grid_cost_r,
                "grid_net_r": grid_net_r,
                "outcome": outcome,
                "path_source_mode": source_mode,
                "candidate_transform_id": TRANSFORM_ID,
                "candidate": repaired,
                "features": {
                    "source_candidate_id": str(row["candidate_id"]),
                    "candidate_transform_id": TRANSFORM_ID,
                    "path_source_mode": source_mode,
                    "exit_reason": outcome,
                    "decision_split": split,
                    "capture_window": [config.capture_start, config.capture_end],
                },
            }
            handle.write(
                json.dumps(
                    trade,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )
            key = _candidate_time_key(row["candidate_id"], decision)
            if key in source_keys:
                raise CSRefusal(f"duplicate_repair_join_key:{key}")
            source_keys.add(key)
            transformed_id = str(repaired["candidate_id"])
            transformed_ids.add(transformed_id)
            transformed_key = _candidate_time_key(transformed_id, decision)
            if transformed_key in transformed_keys:
                raise CSRefusal(f"duplicate_transformed_join_key:{transformed_key}")
            transformed_keys.add(transformed_key)
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            source_modes[source_mode] = source_modes.get(source_mode, 0) + 1
            split_counts[split] += 1
            if outcome == "AMBIGUOUS_CONSERVATIVE_STOP":
                ambiguity[split] += 1
                ambiguity["FULL"] += 1
            for name in (split, "FULL"):
                split_values[name]["gross"].append(gross_r)
                split_values[name]["grid_cost"].append(grid_cost_r)
                split_values[name]["grid_net"].append(grid_net_r)
            exit_iso = exit_utc.isoformat()
            min_exit = min(min_exit or exit_iso, exit_iso)
            max_exit = max(max_exit or exit_iso, exit_iso)

    if (
        split_counts["TRAIN"] == 0
        or split_counts["OOS"] == 0
        or len(source_keys) != len(breaker_indices)
        or len(transformed_keys) != len(breaker_indices)
        or path_modes.get("breaker_rows") != len(breaker_indices)
        or min_exit is None
        or max_exit is None
    ):
        raise CSRefusal(f"fixed_breaker_population_incomplete:{config.window_id}")

    metrics = {
        split: {
            "n": len(values["grid_net"]),
            "mean_gross_r": float(np.mean(values["gross"])),
            "mean_grid_cost_r": float(np.mean(values["grid_cost"])),
            "mean_grid_net_r": float(np.mean(values["grid_net"])),
            "sum_grid_net_r": float(np.sum(values["grid_net"])),
            "ambiguity_count": ambiguity[split],
        }
        for split, values in split_values.items()
    }
    receipt = _write_self_bound(
        config.repair_receipt,
        {
            "schema": "gtos-session-cs-current-breaker-repair-v1",
            "generated_at_utc": _utc_now(),
            "source_head": _git_head(),
            "surface": "VAL",
            "billed": False,
            "window_id": config.window_id,
            "capture_window": [config.capture_start, config.capture_end],
            "local_train": [config.capture_start, config.local_train_end],
            "local_oos": [config.local_oos_start, config.capture_end],
            "selection_authority": (
                "CQ_CURRENT_BREAKER_REPAIR_V1 only; no CS search or selection"
            ),
            "candidate_transform": {
                "id": TRANSFORM_ID,
                "implementation": "src/components/current_breaker_re_entry_repair.py",
                "entry_rule": "fixed",
                "orientation": "inverted",
                "target_distance_D": TARGET_DISTANCE_D,
                "stop_distance_D": STOP_DISTANCE_D,
                "horizon_minutes": HORIZON_MINUTES,
                "runtime_default": "off",
                "outcome_fields_enter_transform": False,
            },
            "path_pool": {
                "path": _repo_path(config.path_manifest),
                "self_sha256": path_manifest["self_sha256"],
                "sidecar_sha256": path_manifest["sidecar"]["sha256"],
            },
            "path_modes": path_modes,
            "broker_true_cost_reprice": cost_report,
            "broker_true_cost_reprice_scope": (
                "fixed current_breaker_re_entry population only; CQ helper's liquidity "
                "report fields receive an all-false mask and carry no additional look"
            ),
            "trade_records": {
                "path": _repo_path(config.repair_trades),
                "sha256": _sha256_file(config.repair_trades),
                "rows": len(breaker_indices),
                "unique_source_join_keys": len(source_keys),
                "unique_transformed_join_keys": len(transformed_keys),
                "unique_transformed_candidate_ids": len(transformed_ids),
                "standalone_transformed_id_recurrences": (
                    len(breaker_indices) - len(transformed_ids)
                ),
                "split_counts": split_counts,
                "outcomes": dict(sorted(outcomes.items())),
                "path_source_modes": dict(sorted(source_modes.items())),
                "min_exit_utc": min_exit,
                "max_exit_utc": max_exit,
                "metrics": metrics,
            },
            "ambiguity_counts_per_fold": {
                "local_oos": ambiguity["OOS"],
                "local_train": ambiguity["TRAIN"],
                "full_capture": ambiguity["FULL"],
            },
            "invariants": {
                "all_rows_current_breaker_re_entry": True,
                "same_entry_and_decision_time": True,
                "all_exits_strictly_after_entry_and_within_120_minutes": True,
                "all_entry_and_exit_dates_inside_capture": True,
                "production_transform_used_for_every_candidate": True,
                "transformed_trade_identity_is_candidate_id_plus_entry_utc": True,
                "only_frozen_fixed_geometry_scored": True,
                "grid_not_rerun": True,
                "broker_module_imported": False,
                "token_bound_config_bytes_read": False,
            },
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "new_candidate_hypotheses": 0,
            "new_graduation_bills": 0,
            "status": "FIXED_BREAKER_FOLD_MATERIALIZED_FOR_RATIFIED_GATE",
        },
    )
    _record_fixed_look(
        config,
        metric=float(metrics["OOS"]["mean_grid_net_r"]),
        receipt=config.repair_receipt,
    )
    return receipt


def _load_cs_trade_records(config: WindowConfig) -> tuple[list[TradeRecord], dict[str, Any]]:
    receipt = _read_bound(config.repair_receipt)
    expected = receipt.get("trade_records") or {}
    digest = _sha256_file(config.repair_trades)
    if digest != expected.get("sha256"):
        raise CSRefusal(f"repair_trade_hash_mismatch:{config.window_id}")
    records: list[TradeRecord] = []
    source_keys: set[tuple[str, str]] = set()
    broker_symbols: set[str] = set()
    for line_number, row in enumerate(_iter_gzip_jsonl(config.repair_trades), start=1):
        if (
            row.get("schema") != REPAIR_TRADE_SCHEMA
            or row.get("sleeve") != SLEEVE
            or row.get("candidate_transform_id") != TRANSFORM_ID
            or row.get("source_window_id") != config.window_id
            or row.get("decision_split") not in {"TRAIN", "OOS"}
        ):
            raise CSRefusal(f"repair_trade_identity_invalid:{config.window_id}:{line_number}")
        entry = _assert_allowed_time(
            row.get("entry_utc"), config, context=f"gate_entry_{line_number}"
        )
        exit_utc = _assert_allowed_time(
            row.get("exit_utc"), config, context=f"gate_exit_{line_number}"
        )
        if not entry < exit_utc <= entry + dt.timedelta(minutes=HORIZON_MINUTES):
            raise CSRefusal(f"repair_trade_horizon_invalid:{line_number}")
        key = (str(row.get("source_candidate_id") or ""), entry.isoformat())
        if not key[0] or key in source_keys:
            raise CSRefusal(f"repair_trade_join_key_invalid:{line_number}:{key}")
        source_keys.add(key)
        broker_symbol = str(row.get("broker_symbol") or "")
        if not broker_symbol:
            raise CSRefusal(f"repair_trade_broker_symbol_missing:{line_number}")
        broker_symbols.add(broker_symbol)
        records.append(
            TradeRecord(
                sleeve=SLEEVE,
                symbol=broker_symbol,
                entry_utc=entry,
                exit_utc=exit_utc,
                direction=int(row["direction"]),
                sl_distance_price=float(row["sl_distance_price"]),
                entry_price=float(row["entry_price"]),
                r_gross=float(row["r_gross"]),
                features=dict(row.get("features") or {}),
            )
        )
    if len(records) != int(expected.get("rows") or -1):
        raise CSRefusal(
            f"repair_trade_count_mismatch:{config.window_id}:"
            f"{len(records)}!={expected.get('rows')}"
        )
    return records, {
        "window_id": config.window_id,
        "capture_window": [config.capture_start, config.capture_end],
        "receipt": _repo_path(config.repair_receipt),
        "receipt_self_sha256": receipt["self_sha256"],
        "trade_file": _repo_path(config.repair_trades),
        "trade_file_sha256": digest,
        "rows": len(records),
        "unique_source_join_keys": len(source_keys),
        "broker_symbols": sorted(broker_symbols),
        "ambiguity_counts_per_fold": receipt["ambiguity_counts_per_fold"],
    }


def _validate_cs_look_accounting() -> dict[str, Any]:
    """Require four completed looks and retain every failed runner attempt.

    The lane logger intentionally appends a row even when a run refuses before
    economics extraction.  Such a row is not one of the four completed VAL
    looks declared by CS, but deleting or silently ignoring it would violate
    the stronger every-look accounting rule.  Accept only same-spec, unbilled
    error rows with null extracted economics, report them separately, and
    still require exactly one completed substrate look plus one fixed-fold
    look for each capture.
    """

    rows = [row for row in read_rows(DEFAULT_ITERATION_LEDGER) if row.get("session") == "CS"]
    bindings: dict[str, Any] = {}
    consumed_indexes: set[int] = set()
    completed_look_rows = 0
    error_attempt_rows = 0
    for config in WINDOWS.values():
        runner = [
            (index, row)
            for index, row in enumerate(rows)
            if (row.get("extra") or {}).get("output_prefix") == config.arm_prefix
        ]
        fixed = [
            (index, row)
            for index, row in enumerate(rows)
            if (row.get("extra") or {}).get("look_id") == config.fixed_look_id
        ]
        evaluated = [item for item in runner if item[1].get("verdict") == "evaluated"]
        errors = [item for item in runner if item[1].get("verdict") == "error"]
        if len(evaluated) != 1 or len(fixed) != 1 or len(runner) != len(evaluated) + len(errors):
            raise CSRefusal(
                f"cs_declared_look_row_count:{config.window_id}:"
                f"runner={len(runner)}:evaluated={len(evaluated)}:"
                f"errors={len(errors)}:fixed={len(fixed)}"
            )
        runner_index, runner_row = evaluated[0]
        fixed_index, fixed_row = fixed[0]
        consumed_indexes.update((runner_index, fixed_index))
        expected_span = [config.capture_start, config.capture_end]
        expected_runner_receipt = _repo_path(
            config.arm_report.parent
            / f"{config.arm_prefix}_LANE"
            / "LANE_RUN_RECEIPT.json"
        )
        if (
            runner_row.get("date_span") != expected_span
            or runner_row.get("surface") != "VAL"
            or bool(runner_row.get("billed"))
            or runner_row.get("verdict") != "evaluated"
            or runner_row.get("mechanism") != "b7_5_broad_v4"
            or runner_row.get("sleeve") != ""
            or runner_row.get("receipt") != expected_runner_receipt
            or not isinstance((runner_row.get("extra") or {}).get("counts"), Mapping)
            or (runner_row.get("extra") or {}).get("arm") != ARM_ID
            or (runner_row.get("spec") or {}).get("window") != expected_span
            or (runner_row.get("spec") or {}).get("lane_window_id")
            != config.window_id
            or (runner_row.get("spec") or {}).get("repairs")
            != ["commission_broker_true_gated", "swap_horizon_true"]
            or fixed_row.get("date_span") != expected_span
            or fixed_row.get("surface") != "VAL"
            or bool(fixed_row.get("billed"))
            or fixed_row.get("verdict") != "evaluated"
            or fixed_row.get("mechanism")
            != "true_utc_path_complete_fixed_breaker_validation"
            or fixed_row.get("sleeve") != SLEEVE
            or fixed_row.get("receipt") != _repo_path(config.repair_receipt)
            or (fixed_row.get("extra") or {}).get("new_candidate_hypothesis")
            is not False
            or (fixed_row.get("extra") or {}).get("new_graduation_bill") is not False
        ):
            raise CSRefusal(f"cs_declared_look_boundary_invalid:{config.window_id}")
        successful_ts = _parse_utc(runner_row.get("ts"))
        error_attempts: list[dict[str, Any]] = []
        for error_index, error_row in errors:
            extra = error_row.get("extra") or {}
            if (
                error_row.get("date_span") != expected_span
                or error_row.get("surface") != "VAL"
                or bool(error_row.get("billed"))
                or error_row.get("mechanism") != "b7_5_broad_v4"
                or error_row.get("sleeve") != ""
                or error_row.get("receipt") != _repo_path(config.arm_report)
                or error_row.get("metric") is not None
                or str(error_row.get("metric_name") or "") != ""
                or extra.get("arm") != ARM_ID
                or extra.get("counts") is not None
                or extra.get("missed_opportunity_pool") is not None
                or error_row.get("spec") != runner_row.get("spec")
                or error_row.get("spec_digest") != runner_row.get("spec_digest")
                or error_row.get("candidate_id") != runner_row.get("candidate_id")
                or error_row.get("candidate_id_windowed")
                != runner_row.get("candidate_id_windowed")
                or _parse_utc(error_row.get("ts")) >= successful_ts
            ):
                raise CSRefusal(
                    f"cs_runner_error_attempt_boundary_invalid:"
                    f"{config.window_id}:{error_row.get('run_id')}"
                )
            consumed_indexes.add(error_index)
            error_attempts.append(
                {
                    "run_id": error_row.get("run_id"),
                    "timestamp_utc": error_row.get("ts"),
                    "receipt_pointer_at_attempt": error_row.get("receipt"),
                    "wall_seconds": extra.get("wall_seconds"),
                    "maxrss_bytes": extra.get("maxrss_bytes"),
                    "extracted_economics": False,
                    "billed": False,
                    "same_declared_spec_as_completed_runner": True,
                }
            )
        completed_look_rows += 2
        error_attempt_rows += len(error_attempts)
        bindings[config.window_id] = {
            "runner_candidate_id": runner_row.get("candidate_id"),
            "runner_candidate_id_windowed": runner_row.get("candidate_id_windowed"),
            "fixed_candidate_id": fixed_row.get("candidate_id"),
            "fixed_candidate_id_windowed": fixed_row.get("candidate_id_windowed"),
            "runner_prefix": config.arm_prefix,
            "declared_surface_look_id": config.surface_look_id,
            "fixed_look_id": config.fixed_look_id,
            "date_span": expected_span,
            "surface": "VAL",
            "billed": False,
            "runner_error_attempts": error_attempts,
        }
    unexpected = [rows[index] for index in range(len(rows)) if index not in consumed_indexes]
    if unexpected or completed_look_rows != 4:
        raise CSRefusal(
            f"cs_iteration_look_total:total={len(rows)}:"
            f"completed={completed_look_rows}:errors={error_attempt_rows}:"
            f"unexpected={len(unexpected)}"
        )
    return {
        "ledger": _repo_path(DEFAULT_ITERATION_LEDGER),
        "ledger_sha256": _sha256_file(DEFAULT_ITERATION_LEDGER),
        "session": "CS",
        "total_rows": len(rows),
        "completed_declared_val_looks": completed_look_rows,
        "expected_completed_declared_val_looks": 4,
        "runner_error_attempts_without_extracted_economics": error_attempt_rows,
        "all_rows_accounted": True,
        "bindings": bindings,
    }


def run_ratified_gate() -> dict[str, Any]:
    """Combine the three fixed captures and run the unchanged ratified gate."""

    fold_plan, look_addendum, may_amendment = _validate_predeclared_contracts()
    january_records, january_binding = CQ_GATE._load_repair_trades()
    april_records, april_binding = _load_cs_trade_records(WINDOWS["april_2026"])
    may_records, may_binding = _load_cs_trade_records(WINDOWS["may_2026"])
    records = [*january_records, *april_records, *may_records]
    if any(
        record.entry_utc.month in (2, 3) or record.exit_utc.month in (2, 3)
        for record in records
    ):
        raise CSRefusal("combined_gate_contains_forbidden_february_or_march_record")

    costs_sha256 = _sha256_file(PHASE17_COSTS)
    if costs_sha256 != EXPECTED_COST_SHA256:
        raise CSRefusal(
            f"broker_true_cost_artifact_drift:{costs_sha256}!={EXPECTED_COST_SHA256}"
        )
    v27_sha256 = _sha256_file(V27)
    if v27_sha256 != EXPECTED_V27_SHA256:
        raise CSRefusal(f"candidate_family_v27_drift:{v27_sha256}!={EXPECTED_V27_SHA256}")
    family = load_candidate_family(V27)
    declared = family.family("CANDIDATE_BOOK_V1")
    if declared.effective_size() != 59 or declared.looks_taken_size() != 57:
        raise CSRefusal(
            "candidate_family_v27_counts_invalid:"
            f"{declared.effective_size()}/{declared.looks_taken_size()}"
        )
    member = [row for row in declared.members if row.name == SLEEVE]
    if len(member) != 1 or not member[0].look_taken:
        raise CSRefusal("candidate_family_v27_missing_billed_breaker_member")

    graduations = [
        row
        for row in read_rows(DEFAULT_GRADUATION_LEDGER)
        if row.get("member_name") == SLEEVE
        and row.get("family_id") == "CANDIDATE_BOOK_V1"
    ]
    billed = sum(int(row.get("billed_looks") or 0) for row in graduations)
    if len(graduations) != 1 or billed != 1:
        raise CSRefusal(
            f"existing_breaker_graduation_bill_invalid:{len(graduations)}:{billed}"
        )

    costs = load_broker_true_costs(PHASE17_COSTS)
    broker_symbols = sorted({record.symbol for record in records})
    base = OPTIONS["B_balanced"].with_(
        spec_id="wf_gate_option_B_balanced_cq_current_breaker_repair_mid",
        account="FTMO",
        cost_artifact_sha256=costs_sha256,
        spread_band="mid",
        sleeve_symbol_allowlist={SLEEVE: tuple(broker_symbols)},
    )
    spec = with_declared_family(
        base,
        "CANDIDATE_BOOK_V1",
        basis=ALL_DECLARED,
        loaded=family,
    )
    population, spec, population_mix = era_population.apply(
        "RECORDED",
        {SLEEVE: records},
        spec,
        account="FTMO",
        band="mid",
    )
    captures = (
        ("2026-01-01", "2026-01-30"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-30"),
    )
    spec = spec.with_(
        capture_windows=captures,
        capture_declaration_id=(
            "CS_BREAKER_FOLD_PLAN_V1+CS_BREAKER_LOOK_ADDENDUM_V1+"
            "CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1"
        ),
        capture_declaration_sha256s=(
            fold_plan["self_sha256"],
            look_addendum["self_sha256"],
            may_amendment["self_sha256"],
        ),
    )
    gate = run_gate(
        population,
        spec,
        costs=costs,
        diagnose=True,
        server="FTMO-Server3",
    )
    gate_result = gate.as_dict()
    verdict = gate_result["sleeves"].get(SLEEVE) or {}
    fold_rows = verdict.get("folds") or []
    if len(fold_rows) != 3:
        raise CSRefusal(f"composite_scored_fold_count:{len(fold_rows)}!=3")
    expected_oos = [
        ["2026-01-16", "2026-01-30"],
        ["2026-04-16", "2026-04-30"],
        ["2026-05-16", "2026-05-30"],
    ]
    actual_oos = [[row.get("oos_start"), row.get("oos_end")] for row in fold_rows]
    if actual_oos != expected_oos:
        raise CSRefusal(f"composite_fold_boundary_drift:{actual_oos}!={expected_oos}")

    fixed_looks = [
        row
        for row in read_rows(DEFAULT_ITERATION_LEDGER)
        if row.get("session") == "CS"
        and (row.get("extra") or {}).get("look_id")
        in {
            WINDOWS["april_2026"].fixed_look_id,
            WINDOWS["may_2026"].fixed_look_id,
        }
    ]
    if len(fixed_looks) != 2 or any(
        row.get("surface") != "VAL" or bool(row.get("billed"))
        for row in fixed_looks
    ):
        raise CSRefusal(f"cs_fixed_look_accounting_invalid:{len(fixed_looks)}")
    cs_look_accounting = _validate_cs_look_accounting()

    ceremony = (
        {
            "status": "ACTIVATION_DOSSIER_REQUIRED_BEFORE_QUEUE",
            "arming_authority": False,
        }
        if verdict.get("verdict") == "ADMIT"
        else {
            "status": "NOT_QUEUED",
            "reason": verdict.get("reasons") or ["no admitting verdict"],
            "arming_authority": False,
        }
    )
    payload = _write_self_bound(
        OUT_GATE,
        {
            "schema": "gtos-session-cs-current-breaker-ratified-gate-v1",
            "generated_at_utc": _utc_now(),
            "source_head": _git_head(),
            "surface": "VAL_TO_RATIFIED_GATE",
            "march_2026_outcomes_read": False,
            "february_2026_economics_read": False,
            "broker_live_authority": False,
            "broker_module_imported": False,
            "token_bound_config_bytes_read": False,
            "fold_plan": {
                "path": _repo_path(FOLD_PLAN),
                "self_sha256": fold_plan["self_sha256"],
                "look_addendum": _repo_path(LOOK_ADDENDUM),
                "look_addendum_self_sha256": look_addendum["self_sha256"],
                "may_amendment": _repo_path(MAY_AMENDMENT),
                "may_amendment_self_sha256": may_amendment["self_sha256"],
                "capture_windows": [list(window) for window in captures],
                "actual_oos_boundaries": actual_oos,
            },
            "repair_trade_bindings": {
                "january": january_binding,
                "april": april_binding,
                "may": may_binding,
                "records_before_population": len(records),
                "records_after_population": len(population.get(SLEEVE, ())),
            },
            "look_accounting": {
                "candidate_family_tip": _repo_path(V27),
                "candidate_family_tip_sha256": v27_sha256,
                "all_declared": 59,
                "looks_taken": 57,
                "new_candidate_hypotheses": 0,
                "new_graduation_bills": 0,
                "existing_member_graduation_rows": len(graduations),
                "existing_member_total_billed_looks": billed,
                "cs_fixed_validation_rows": len(fixed_looks),
                "cs_iteration_ledger": cs_look_accounting,
            },
            "gate_contract": {
                "population": "RECORDED",
                "option": "B_balanced",
                "alpha": 0.10,
                "multiplicity_basis": "CANDIDATE_BOOK_V1/all_declared",
                "spread_band": "mid",
                "account": "FTMO",
                "server_clock": "FTMO-Server3",
                "cost_artifact": _repo_path(PHASE17_COSTS),
                "cost_artifact_sha256": costs_sha256,
                "population_mix": population_mix,
                "spec_sha256": spec.seal(),
                "capture_assembly": (
                    "unchanged equal-calendar builder independently inside each "
                    "predeclared capture; scored slices concatenated"
                ),
            },
            "gate_result": gate_result,
            "repair_queue": gate.repair_queue(
                server="FTMO-Server3",
                run_label="Session CS three-fold current-breaker validation",
                extra={
                    "population": "RECORDED",
                    "spread_band": "mid",
                    "candidate_transform_id": TRANSFORM_ID,
                    "capture_windows": [list(window) for window in captures],
                },
            ),
            "ceremony": ceremony,
            "status": (
                "RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED"
                if verdict.get("verdict") == "ADMIT"
                else "RATIFIED_GATE_REJECTED_OR_NOT_EVALUABLE"
            ),
        },
    )
    return payload


def main() -> int:
    os.chdir(REPO)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    compact = sub.add_parser("compact", help="project one completed arm")
    compact.add_argument("--window", choices=tuple(WINDOWS), required=True)
    compact.add_argument("--ledger", type=Path, required=True)
    compact.add_argument("--arm-report", type=Path)

    materialize = sub.add_parser(
        "materialize", help="build path sidecar and fixed repair records"
    )
    materialize.add_argument("--window", choices=tuple(WINDOWS), required=True)
    materialize.add_argument("--lane-input-registry", type=Path, required=True)

    sub.add_parser("gate", help="run the unchanged three-capture ratified gate")
    ns = parser.parse_args()
    if ns.command == "compact":
        payload = compact_arm(
            WINDOWS[ns.window],
            ledger=ns.ledger,
            arm_report=ns.arm_report,
        )
    elif ns.command == "materialize":
        payload = materialize_fixed_repair(
            WINDOWS[ns.window],
            registry_path=ns.lane_input_registry,
        )
    else:
        payload = run_ratified_gate()
    print(
        json.dumps(
            {
                "command": ns.command,
                "window": getattr(ns, "window", None),
                "status": payload.get("status"),
                "self_sha256": payload.get("self_sha256"),
                "output": (
                    _repo_path(OUT_GATE)
                    if ns.command == "gate"
                    else _repo_path(
                        WINDOWS[ns.window].compact_receipt
                        if ns.command == "compact"
                        else WINDOWS[ns.window].repair_receipt
                    )
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
