"""Behavioural boundaries for Session CS's fixed-fold evidence driver."""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import importlib.util
import itertools
import json
import math
import sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest


REPO = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO / "src/research_infra/cs_breaker_folds.py"


@pytest.fixture(scope="module")
def cs_tool():
    spec = importlib.util.spec_from_file_location("test_session_cs_breaker_folds", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cs_time_boundary_refuses_february_march_and_cross_capture(cs_tool) -> None:
    april = cs_tool.WINDOWS["april_2026"]
    assert cs_tool._assert_allowed_time(
        "2026-04-16T08:00:00+00:00", april, context="test"
    ).month == 4
    with pytest.raises(cs_tool.CSRefusal, match="february_economics_forbidden"):
        cs_tool._assert_allowed_time(
            "2026-02-16T08:00:00+00:00", april, context="test"
        )
    with pytest.raises(cs_tool.CSRefusal, match="march_outcomes_forbidden"):
        cs_tool._assert_allowed_time(
            "2026-03-16T08:00:00+00:00", april, context="test"
        )
    with pytest.raises(cs_tool.CSRefusal, match="timestamp_outside_capture"):
        cs_tool._assert_allowed_time(
            "2026-05-01T00:00:00+00:00", april, context="test"
        )


def test_executable_constants_match_all_preoutcome_declarations(cs_tool) -> None:
    plan, looks, may_amendment = cs_tool._validate_predeclared_contracts()
    assert plan["self_sha256"] == (
        "31b2ab756bf9be6ae19ca7f5e40447c2de7ea905839a78a921919ca3b5bb3b85"
    )
    assert looks["self_sha256"] == (
        "5ab5414a4de6eb7b0ccf54f10bc2901673205120ac7754291026290303642174"
    )
    assert may_amendment["self_sha256"] == (
        "94f4688dfa89a6998eaf44c25910be6b26052253a58fcd0ad3bf9c2b5d93f44b"
    )


def test_ratified_gate_seals_capture_authority_and_applies_anchored_exact_null(
    cs_tool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = json.loads(cs_tool.OUT_GATE.read_text(encoding="utf-8"))
    hc_complete = json.loads(
        (
            REPO
            / "docs/audits/fable5-vision-audit-20260725/phase20/receipts/"
            / "SESSION_HC_COMPLETE.json"
        ).read_text(encoding="utf-8")
    )
    monkeypatch.setattr(cs_tool, "OUT_GATE", tmp_path / "repaired-gate.json")

    repaired = cs_tool.run_ratified_gate()
    published_verdict = published["gate_result"]["sleeves"][cs_tool.SLEEVE]
    repaired_verdict = repaired["gate_result"]["sleeves"][cs_tool.SLEEVE]

    assert published_verdict["verdict"] == "REJECT"
    # Wave-21 integration (2026-08-10): the artifact-bound slippage authority
    # prices only its reconciled FTMO sample set, so six of this sleeve's
    # sixteen symbols (AUDJPY, CHFJPY, EURJPY, UKOIL.cash, USOIL.cash, XAGUSD)
    # now refuse with no reconciled price-domain slippage sample, the evaluable
    # universe narrows to 63.6% of trades, and the ratified gate's repaired
    # verdict is REJECT on BH significance across the 59 family. The pre-wave-21
    # repaired ADMIT (q 0.0576) is NOT reproducible at current cost authority;
    # its restoration path is a slippage capture for the six symbols, not a
    # threshold change. Registered in WAVE21_INTEGRATION.md open items.
    assert repaired_verdict["verdict"] == "REJECT"
    assert repaired["status"] == "RATIFIED_GATE_REJECTED_OR_NOT_EVALUABLE"
    assert repaired["ceremony"]["status"] == "NOT_QUEUED"
    assert repaired["ceremony"]["arming_authority"] is False
    ceremony_reasons = " ".join(repaired["ceremony"]["reason"])
    assert "PARTIAL UNIVERSE: evaluated on 10 of 16 symbols" in ceremony_reasons
    assert "no reconciled price-domain slippage sample" in ceremony_reasons
    assert published_verdict["gates"]["significance"]["p_raw"] == pytest.approx(
        0.0025997400259974
    )
    assert published_verdict["q_value"] == pytest.approx(0.1533846615338466)
    assert hc_complete["disposition_identity"]["cs"][
        "repaired_raw_p"
    ] == pytest.approx(
        0.0021158854166666665
    )
    assert hc_complete["disposition_identity"]["cs"][
        "repaired_bh_q"
    ] == pytest.approx(
        0.12483723958333333
    )
    # The restricted-universe candidate still shows a large pooled OOS mean and
    # a small raw p; what fails is the multiplicity bill.
    assert repaired_verdict["pooled_oos_mean_r"] == pytest.approx(
        7.208987342426981
    )
    assert repaired_verdict["q_value"] == pytest.approx(0.3169, abs=1e-4)
    assert repaired_verdict["gates"]["significance"]["family_size"] == 59
    assert repaired_verdict["gates"]["significance"]["p_raw"] == pytest.approx(
        0.005371, abs=1e-6
    )
    assert [
        gate
        for gate, row in repaired_verdict["gates"].items()
        if isinstance(row, dict) and row.get("pass") is False
    ] == ["significance"]

    capture = repaired["gate_result"]["family"]["fold_capture_contract"]
    assert capture["schema"] == "gtos.walkforward.capture_windows.v2"
    assert capture["authority"] == "immutable_gate_spec"
    assert capture["declaration_id"] == (
        "CS_BREAKER_FOLD_PLAN_V1+CS_BREAKER_LOOK_ADDENDUM_V1+"
        "CS_MAY_SOURCE_BOUNDARY_AMENDMENT_V1"
    )
    assert capture["declaration_sha256s"] == [
        "31b2ab756bf9be6ae19ca7f5e40447c2de7ea905839a78a921919ca3b5bb3b85",
        "5ab5414a4de6eb7b0ccf54f10bc2901673205120ac7754291026290303642174",
        "94f4688dfa89a6998eaf44c25910be6b26052253a58fcd0ad3bf9c2b5d93f44b",
    ]
    # The integrated current spec is v2 and seals both HDA fidelity policy and HDF capture
    # authority. The capture windows, declaration hashes, 59-member bill, observations,
    # economics and ADMIT disposition above remain unchanged; only the authority schema
    # preimage intentionally moved from HDF's isolated v1 builder.
    assert repaired["gate_result"]["spec"]["schema"] == (
        "gtos.walkforward.gate_spec.v2"
    )
    assert capture["gate_spec_sha256"] == (
        "736872fe5ec2c4b83d4c808dc3720d9be18548654a5f9f43375bed24d85a62b7"
    )
    assert capture["touching_boundaries"] == [
        {"left_end": "2026-04-30", "right_start": "2026-05-01"}
    ]
    null = repaired_verdict["telemetry"]["null"]
    assert null["segment_lengths"] == [11, 11, 9]
    assert null["boundary_policy"] == "null_blocks_restart_at_each_capture"
    assert null["bootstrap"]["p_value"] == pytest.approx(1.0 / 10001.0)
    assert null["permutation"]["phase_policy"] == "none_capture_start_anchored"
    assert null["permutation"]["alignment_policy"] == (
        "first_oos_day_of_each_sealed_capture"
    )
    assert null["permutation"]["enumeration"] == "exact"
    assert null["permutation"]["seed_effective"] is False
    assert null["permutation"]["n_permutations_evaluated"] == 2048
    # Restricted-universe series (wave-21 slippage authority): 11 of 2048 sign
    # assignments reach the observed sum, up from 2 on the full universe.
    assert null["permutation"]["p_value"] == pytest.approx(11.0 / 2048.0)
    diagnostic_gates = repaired["repair_queue"]["diagnostics"][cs_tool.SLEEVE][
        "gates"
    ]
    significance = next(
        row for row in diagnostic_gates if row["gate"] == "significance"
    )
    assert significance["evidence"]["p_floor"]["p_floor"] == pytest.approx(
        1.0 / 2048.0
    )


def test_cs_economics_segments_and_59_member_bill_reproduce_without_run_gate(
    cs_tool,
) -> None:
    from src.costs import load_broker_true_costs
    from src.research_infra.walkforward import era_population
    from src.research_infra.walkforward.options import OPTIONS
    from src.research_infra.walkforward.panel import price_trades

    january, _ = cs_tool.CQ_GATE._load_repair_trades()
    april, _ = cs_tool._load_cs_trade_records(cs_tool.WINDOWS["april_2026"])
    may, _ = cs_tool._load_cs_trade_records(cs_tool.WINDOWS["may_2026"])
    raw_records = [*january, *april, *may]
    assert len(raw_records) == 11_305
    assert all(
        record.entry_utc.month not in (2, 3)
        and record.exit_utc.month not in (2, 3)
        for record in raw_records
    )

    base = OPTIONS["B_balanced"].with_(
        spec_id="hdc_independent_cs_economics",
        account="FTMO",
        cost_artifact_sha256=cs_tool._sha256_file(cs_tool.PHASE17_COSTS),
        spread_band="mid",
    )
    population, priced_spec, mix = era_population.apply(
        "RECORDED",
        {cs_tool.SLEEVE: raw_records},
        base,
        account="FTMO",
        band="mid",
    )
    assert mix == {"kept": 6536, "dropped": 4769, "unpriceable": 0}
    costs = load_broker_true_costs(cs_tool.PHASE17_COSTS)
    priced, coverage = price_trades(
        population[cs_tool.SLEEVE], priced_spec, costs=costs
    )
    assert len(priced) == 6536
    # Wave-21: six symbols lack reconciled slippage samples on FTMO, so the
    # coverage fraction drops from 1.0 to the measured restricted-universe value.
    assert coverage[cs_tool.SLEEVE].coverage_frac == pytest.approx(
        0.6355569155446756
    )

    oos_windows = (
        ("2026-01-16", "2026-01-30"),
        ("2026-04-16", "2026-04-30"),
        ("2026-05-16", "2026-05-30"),
    )
    daily_segments = []
    segment_dates = []
    for lo, hi in oos_windows:
        by_day = defaultdict(list)
        for row in priced:
            day = row.trade.entry_utc.date().isoformat()
            if lo <= day <= hi and row.status == "priced":
                by_day[day].append(row.r_net)
        dates = sorted(by_day)
        segment_dates.append(dates)
        daily_segments.append(
            [math.fsum(by_day[day]) / len(by_day[day]) for day in dates]
        )

    segment_lengths = [len(segment) for segment in daily_segments]
    fold_means = [
        math.fsum(segment) / len(segment) for segment in daily_segments
    ]
    pooled_mean = math.fsum(fold_means) / len(fold_means)
    assert segment_lengths == [11, 11, 9]
    # Wave-21 restricted universe (10 of 16 symbols priceable): the fold means
    # move from the full-universe [11.2523, 7.4536, 3.8520] to the measured
    # values below; the pooled mean matches the repaired gate's 7.20899.
    assert fold_means == pytest.approx(
        [12.24971575505896, 7.666601968036244, 1.710644304185736],
        abs=1e-12,
    )
    assert pooled_mean == pytest.approx(7.20898734242698, abs=1e-12)
    assert [dates[0] for dates in segment_dates] == [
        "2026-01-16",
        "2026-04-16",
        "2026-05-18",
    ]

    pooled_n = sum(segment_lengths)
    weighted_segments = [
        [
            value * pooled_n / (len(daily_segments) * len(segment))
            for value in segment
        ]
        for segment in daily_segments
    ]
    weighted = [value for segment in weighted_segments for value in segment]
    weighted_sha = hashlib.sha256(
        json.dumps(
            [round(value, 12) for value in weighted],
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    # Wave-21 restricted-universe daily series (see the coverage note above).
    assert weighted_sha == (
        "f79285b9130bd67f04829e5361505a93608bc120b466029c530a7dc9694a65e4"
    )
    assert math.fsum(weighted) / len(weighted) == pytest.approx(
        pooled_mean, abs=1e-12
    )

    block_sums = []
    blocks_by_segment = []
    for segment in weighted_segments:
        blocks = [
            math.fsum(segment[start : start + 3])
            for start in range(0, len(segment), 3)
        ]
        blocks_by_segment.append(len(blocks))
        block_sums.extend(blocks)
    observed_sum = math.fsum(block_sums)
    tail = sum(
        math.fsum(sign * value for sign, value in zip(signs, block_sums))
        >= observed_sum - 1e-12
        for signs in itertools.product((-1.0, 1.0), repeat=len(block_sums))
    )
    raw_p = tail / (2 ** len(block_sums))
    assert blocks_by_segment == [4, 4, 3]
    # Wave-21 (2026-08-10): the artifact-bound slippage authority restricts the
    # priceable universe to 10 of 16 symbols (63.6% of trades), the daily
    # segments change, and the exact null's tail count moves 2 -> 11.
    assert tail == 11
    assert raw_p == pytest.approx(11.0 / 2048.0)

    family_payload = json.loads(cs_tool.V27.read_text(encoding="utf-8"))
    family = family_payload["families"]["CANDIDATE_BOOK_V1"]
    members = family["members"]
    assert family["high_water_size"] == len(members) == 59
    assert family["high_water_looks"] == sum(
        bool(member["look_taken"]) for member in members
    ) == 57
    assert len({member["name"] for member in members}) == 59
    breaker = [member for member in members if member["name"] == cs_tool.SLEEVE]
    assert len(breaker) == 1 and breaker[0]["look_taken"] is True
    assert raw_p * 59 == pytest.approx(0.3169, abs=1e-4)
    # The restricted-universe candidate FAILS the sealed admission bar; the
    # pre-wave-21 full-universe pass is not reproducible at current authority.
    assert raw_p > 0.10 / 59


def test_arm_report_distinguishes_full_april_from_bounded_may(
    cs_tool,
    tmp_path: Path,
) -> None:
    def report_for(config):
        route = tmp_path / config.arm_prefix
        route.mkdir()
        ledger = route / f"{config.arm_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"
        ledger.touch()
        report = {
            "error": None,
            "arm": "S0R0",
            "window_start": config.capture_start,
            "stop_after_day": config.runner_stop_after_day,
            "resolved_window_id": config.window_id,
            "output_prefix": config.arm_prefix,
            "route": str(route.resolve()),
            "outputs_retained": True,
            "fingerprint": {"train_engine_version": "test"},
            "purpose": "LANE_ITERATION",
            "repairs_requested": [
                "commission_broker_true_gated",
                "swap_horizon_true",
            ],
            "partition_authorization": {
                "window": [config.capture_start, config.capture_end],
                "dominant_surface": "VAL",
                "may_emit_iteration_evidence": True,
            },
            "lane_input_authority": {
                "window": [config.capture_start, config.capture_end],
                "surface": "VAL",
                "campaign_sealed": False,
                "canonical_source_plan_digest_sha256": (
                    config.expected_source_plan_digest
                ),
            },
        }
        if config.window_id == "may_2026":
            proof_core = {
                "schema": "gtos.lane.rematerialization.prefix_pack_source_rebind.v1",
                "status": "VERIFIED_PREFIX_PACK_SOURCE_IDENTITY_REBIND",
                "window_id": "may_2026",
                "registered_window": ["2026-05-01", "2026-05-31"],
                "effective_window": ["2026-05-01", "2026-05-30"],
                "registered_source_identity_root_sha256": (
                    cs_tool.MAY_REGISTERED_SOURCE_IDENTITY_ROOT
                ),
                "effective_source_identity_root_sha256": (
                    cs_tool.MAY_EFFECTIVE_SOURCE_IDENTITY_ROOT
                ),
                "source_manifest_root_sha256": "manifest-root",
                "effective_source_plan_digest_sha256": (
                    config.expected_source_plan_digest
                ),
                "retained_pack_count": 30,
                "retained_pack_roots_sha256": "pack-roots",
                "excluded_registered_packs": [
                    ["lane_validation", "2026-05-31", "2026-05-31"]
                ],
                "allowed_binding_difference": ["source_identity_root_sha256"],
                "source_manifest_unchanged": True,
                "retained_daily_pack_roots_are_exact_registry_subset": True,
                "pack_contents_remain_authenticated_per_reader_before_use": True,
                "economic_outcomes_read": False,
                "march_outcomes_read": False,
                "broker_live_authority": False,
                "broker_mutation_enabled": False,
            }
            report["lane_input_authority"].update(
                {
                    "source_manifest_root_sha256": "manifest-root",
                    "runtime_verified_rebinds": {
                        "prefix_pack_source_identity_rebind": {
                            **proof_core,
                            "authority_root_sha256": cs_tool._canonical_sha256(
                                proof_core
                            ),
                        },
                        "prefix_pack_rebind_accepted_days": [
                            (dt.date(2026, 5, 1) + dt.timedelta(days=offset)).isoformat()
                            for offset in range(30)
                        ],
                    },
                }
            )
        return report, ledger

    april = cs_tool.WINDOWS["april_2026"]
    april_report, april_ledger = report_for(april)
    assert april_report["stop_after_day"] is None
    cs_tool._validate_arm_report_boundary(april, april_report, april_ledger)
    april_report["stop_after_day"] = april.capture_end
    with pytest.raises(cs_tool.CSRefusal, match="wrong_window"):
        cs_tool._validate_arm_report_boundary(april, april_report, april_ledger)

    may = cs_tool.WINDOWS["may_2026"]
    may_report, may_ledger = report_for(may)
    assert may_report["stop_after_day"] == "2026-05-30"
    cs_tool._validate_arm_report_boundary(may, may_report, may_ledger)
    may_report["stop_after_day"] = None
    with pytest.raises(cs_tool.CSRefusal, match="wrong_window"):
        cs_tool._validate_arm_report_boundary(may, may_report, may_ledger)

    may_report["stop_after_day"] = may.runner_stop_after_day
    may_report["lane_input_authority"]["runtime_verified_rebinds"][
        "prefix_pack_rebind_accepted_days"
    ].pop()
    with pytest.raises(cs_tool.CSRefusal, match="rebind_proof_invalid"):
        cs_tool._validate_arm_report_boundary(may, may_report, may_ledger)


def test_compact_creates_declared_pool_parent_before_writer(
    cs_tool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = cs_tool.WINDOWS["april_2026"]
    config = replace(
        base,
        compact_pool=tmp_path / "not-created-yet" / "pool.jsonl.gz",
        compact_receipt=tmp_path / "compact-receipt.json",
    )
    route = tmp_path / config.arm_prefix
    route.mkdir()
    ledger = route / f"{config.arm_prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl"
    ledger.write_text("{}\n", encoding="utf-8")
    report = {
        "error": None,
        "arm": "S0R0",
        "window_start": config.capture_start,
        "stop_after_day": config.runner_stop_after_day,
        "resolved_window_id": config.window_id,
        "output_prefix": config.arm_prefix,
        "route": str(route.resolve()),
        "outputs_retained": True,
        "fingerprint": {"train_engine_version": "test"},
        "purpose": "LANE_ITERATION",
        "repairs_requested": [
            "commission_broker_true_gated",
            "swap_horizon_true",
        ],
        "partition_authorization": {
            "window": [config.capture_start, config.capture_end],
            "dominant_surface": "VAL",
            "may_emit_iteration_evidence": True,
        },
        "lane_input_authority": {
            "window": [config.capture_start, config.capture_end],
            "surface": "VAL",
            "campaign_sealed": False,
            "canonical_source_plan_digest_sha256": (
                config.expected_source_plan_digest
            ),
        },
    }
    report_path = tmp_path / "arm.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    def assert_parent_then_stop(*_args, **_kwargs):
        assert config.compact_pool.parent.is_dir()
        raise RuntimeError("parent-created")

    monkeypatch.setattr(cs_tool.CD_POOL, "summarise", assert_parent_then_stop)
    with pytest.raises(RuntimeError, match="parent-created"):
        cs_tool.compact_arm(config, ledger=ledger, arm_report=report_path)


def test_fixed_path_scores_only_breaker_and_preserves_m1_ambiguity(
    cs_tool,
    tmp_path: Path,
) -> None:
    """One M1 bar touching both fixed levels remains a conservative stop later."""

    config = replace(
        cs_tool.WINDOWS["april_2026"],
        sidecar=tmp_path / "paths.jsonl.gz",
    )
    rows = [
        {
            "candidate_id": "breaker",
            "decision_time_utc": "2026-04-16T08:00:00+00:00",
            "symbol": "EURUSD",
            "side": "LONG",
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "origin_family": "current_breaker_re_entry",
        },
        {
            "candidate_id": "other",
            "decision_time_utc": "2026-04-16T08:00:00+00:00",
            "symbol": "EURUSD",
            "side": "LONG",
            "entry_price": 100.0,
            "stop_loss": 99.0,
            "take_profit_1": 102.0,
            "origin_family": "liquidity_sweep_reclaim",
        },
    ]
    observation = {
        "time_utc": "2026-04-16T08:01:00+00:00",
        "open": 100.0,
        "high": 101.0,
        "low": 94.0,
        "close": 100.0,
    }
    with gzip.open(config.sidecar, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    {
                        "schema": cs_tool.CQ.SIDECAR_SCHEMA,
                        "arm_id": "S0R0",
                        "candidate_id": row["candidate_id"],
                        "decision_time_utc": row["decision_time_utc"],
                        "horizon_end_utc": "2026-04-16T10:00:00+00:00",
                        "symbol": row["symbol"],
                        "side": row["side"],
                        "ordered_path_observations": [observation],
                    }
                )
                + "\n"
            )

    summaries, modes = cs_tool._fixed_path_summaries(
        config,
        pool_rows=rows,
        tick_sources={},
    )
    assert list(summaries) == [0]
    summary = summaries[0]
    assert int(summary.target_index[0]) == 0
    assert int(summary.stop_index[0]) == 0
    assert summary.source_mode == "M1_CONSERVATIVE"
    assert modes["breaker_rows"] == 1
    assert modes["m1_conservative_rows"] == 1


def test_repaired_trade_identity_includes_decision_time(cs_tool) -> None:
    first = dt.datetime(2026, 4, 16, 8, 0, tzinfo=dt.timezone.utc)
    second = first + dt.timedelta(minutes=15)
    assert cs_tool._candidate_time_key("same-production-id", first) != (
        cs_tool._candidate_time_key("same-production-id", second)
    )
    with pytest.raises(cs_tool.CSRefusal, match="missing_candidate_id"):
        cs_tool._candidate_time_key("", first)


def test_look_accounting_retains_same_spec_runner_errors(
    cs_tool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows: list[dict[str, Any]] = []
    for config in cs_tool.WINDOWS.values():
        span = [config.capture_start, config.capture_end]
        spec = {
            "window": span,
            "lane_window_id": config.window_id,
            "repairs": ["commission_broker_true_gated", "swap_horizon_true"],
        }
        runner = {
            "session": "CS",
            "date_span": span,
            "surface": "VAL",
            "billed": False,
            "verdict": "evaluated",
            "mechanism": "b7_5_broad_v4",
            "sleeve": "",
            "receipt": cs_tool._repo_path(
                config.arm_report.parent
                / f"{config.arm_prefix}_LANE"
                / "LANE_RUN_RECEIPT.json"
            ),
            "run_id": f"{config.window_id}-success",
            "ts": f"{config.capture_end}T12:00:00+00:00",
            "metric": None,
            "metric_name": "",
            "candidate_id": f"{config.window_id}-candidate",
            "candidate_id_windowed": f"{config.window_id}-windowed",
            "spec": spec,
            "spec_digest": f"{config.window_id}-spec",
            "extra": {
                "arm": "S0R0",
                "output_prefix": config.arm_prefix,
                "counts": {"missed": 1},
                "missed_opportunity_pool": {"rows": 1},
            },
        }
        fixed = {
            "session": "CS",
            "date_span": span,
            "surface": "VAL",
            "billed": False,
            "verdict": "evaluated",
            "mechanism": "true_utc_path_complete_fixed_breaker_validation",
            "sleeve": cs_tool.SLEEVE,
            "receipt": cs_tool._repo_path(config.repair_receipt),
            "extra": {
                "look_id": config.fixed_look_id,
                "new_candidate_hypothesis": False,
                "new_graduation_bill": False,
            },
        }
        rows.extend((runner, fixed))
        if config.window_id == "may_2026":
            failed = json.loads(json.dumps(runner))
            failed.update(
                {
                    "verdict": "error",
                    "receipt": cs_tool._repo_path(config.arm_report),
                    "run_id": "may-pre-economics-error",
                    "ts": "2026-05-30T11:00:00+00:00",
                }
            )
            failed["extra"]["counts"] = None
            failed["extra"]["missed_opportunity_pool"] = None
            rows.insert(-1, failed)

    ledger = tmp_path / "iteration-ledger.jsonl"
    ledger.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    monkeypatch.setattr(cs_tool, "DEFAULT_ITERATION_LEDGER", ledger)
    accounting = cs_tool._validate_cs_look_accounting()
    assert accounting["total_rows"] == 5
    assert accounting["completed_declared_val_looks"] == 4
    assert accounting["runner_error_attempts_without_extracted_economics"] == 1
    assert accounting["all_rows_accounted"] is True

    failed["extra"]["counts"] = {"missed": 1}
    ledger.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    with pytest.raises(cs_tool.CSRefusal, match="error_attempt_boundary_invalid"):
        cs_tool._validate_cs_look_accounting()
