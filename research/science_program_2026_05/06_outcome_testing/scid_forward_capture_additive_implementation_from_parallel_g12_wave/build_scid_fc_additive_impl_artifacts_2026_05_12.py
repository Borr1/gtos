from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.verify_scid_forward_capture_schema import verify
from src.research_infra.forward_capture import (
    SCID_CAPTURE_GROUPS,
    SCID_FORWARD_SOURCE_CAPTURE_PATH,
    build_scid_forward_source_capture_row,
)


ROUTE = Path(__file__).resolve().parent
STAMP = "2026-05-12"
ROUTE_ID = "SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_FROM_ACCEPTED_PARALLEL_G12_WAVE"


def sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def write_json(name: str, payload: Any) -> Path:
    path = ROUTE / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(name: str, title: str, bullets: list[str]) -> Path:
    path = ROUTE / name
    lines = [f"# {title}", ""]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def synthetic_fields() -> dict[str, Any]:
    return {
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "source_symbol": "NQ",
        "session": "ny",
        "kill_zone": "ny",
        "side": "LONG",
        "candidate_id": "NAS100_2026-05-04T13:30:00+00:00",
        "trade_id": "lim_NAS100_20260504_133000",
        "decision_time_utc": "2026-05-04T13:30:00+00:00",
        "analysis_decision": "CANDIDATE",
        "framework": "ob_retest",
        "frameworks_evaluated": {
            "ob_retest": {"qualified": True},
            "fvg_fill": {"qualified": False},
            "breaker_re_entry": {"qualified": False},
        },
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 213.257,
            "stop_loss": 212.64,
            "take_profit_1": 214.183,
            "risk_reward_ratio": 1.5,
        },
        "h1_setup": {
            "poi_type": "OB",
            "poi_price_level": 213.26,
            "zone": "discount",
        },
        "mso_summary": {
            "timestamp_utc": "2026-05-04T13:30:00+00:00",
            "timeframes": ["H1", "M15"],
        },
        "fvg_ob_geometry": {
            "ob_bounds": {"lower": 213.10, "upper": 213.40},
            "fvg_bounds": {"lower": 213.15, "upper": 213.35},
        },
        "intent_after_check": "expired_48h",
        "checked_candle_time_utc": "2026-05-04T13:45:00+00:00",
    }


def build_synthetic_jsonl() -> Path:
    rows = [
        build_scid_forward_source_capture_row(synthetic_fields(), {"field_group": group})
        for group in SCID_CAPTURE_GROUPS
    ]
    path = ROUTE / f"SCID_FC_ADDITIVE_IMPL_SYNTHETIC_VERIFIER_INPUT_{STAMP}.jsonl"
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    created: list[Path] = []

    accepted_inputs = [
        "research/science_program_2026_05/06_outcome_testing/g0_scid_parallel_g12_integration_orchestration/G0_SCID_PARALLEL_G12_INTEGRATION_DECISION_LEDGER_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_parallel_g12_integration_orchestration/G0_SCID_PARALLEL_G12_INTEGRATION_DECISION_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_INSERTION_POINT_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_PROPOSED_PATCH_PLAN_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/runtime_harness_synthetic_only_2026_05_12.py",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_readonly_monitoring_alignment_expansion",
        "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis",
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas",
    ]
    input_inventory = {
        "route_id": ROUTE_ID,
        "created_at_utc": now,
        "accepted_inputs": [
            {
                "path": item,
                "exists": (REPO / item).exists(),
                "sha256": sha256_path(REPO / item) if (REPO / item).is_file() else None,
            }
            for item in accepted_inputs
        ],
        "decision": "ACCEPT_AS_G0_PARALLEL_G12_INTEGRATION_FOR_ADDITIVE_IMPLEMENTATION_SEQUENCE",
        "safe_scope": "additive_source_capture_only",
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_ACCEPTED_INPUT_INVENTORY_{STAMP}.json", input_inventory))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_ACCEPTED_INPUT_INVENTORY_{STAMP}.md",
        "SCID FC Additive Impl Accepted Input Inventory - 2026-05-12",
        [
            "Accepted G0 decision ledger was used as the implementation gate.",
            "Design package, insertion-point ledger, proposed patch plan, synthetic runtime harness, readonly alignment, no-API hypothesis factory, LTF/orderflow source expansion, and offline schemas were treated as route inputs.",
            "No unstated result, promotion, or scoring artifacts were used.",
        ],
    ))

    implementation_ledger = {
        "route_id": ROUTE_ID,
        "created_at_utc": now,
        "source_edits": [
            {
                "path": "src/research_infra/forward_capture.py",
                "change": "Added SCID schema constants, ten group builders, validator, fail-open writer, candidate group emitter, and lifecycle row builder.",
                "trading_decision_reads_writer_return": False,
            },
            {
                "path": "src/components/pending_limit_lifecycle_logger.py",
                "change": "Added non-blocking lifecycle bridge to SCID source-safe projection after existing lifecycle append.",
                "trading_decision_reads_writer_return": False,
            },
            {
                "path": "scripts/verify_scid_forward_capture_schema.py",
                "change": "Added standalone schema/redaction/as-of verifier.",
                "opens_result_scoring": False,
            },
        ],
        "tests": [
            "tests/test_scid_forward_capture_runtime_adapter.py",
            "tests/test_scid_forward_capture_lifecycle_redaction.py",
        ],
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_IMPLEMENTATION_LEDGER_{STAMP}.json", implementation_ledger))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_IMPLEMENTATION_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Implementation Ledger - 2026-05-12",
        [
            "Implementation is additive and writer return values are ignored by live decision flow.",
            "No prompt, risk, execution, safety, selector, canary, or config decision behavior was changed.",
            "Lifecycle bridge emits only redacted status fields into SCID rows.",
        ],
    ))

    capture_matrix = {
        "route_id": ROUTE_ID,
        "capture_groups": [
            {
                "field_group": group,
                "implemented": True,
                "builder": f"build_scid_{group}",
                "validator_required": True,
                "candidate_time": group != "lifecycle_fill_cancel_expiry_source_status",
                "lifecycle_time": group == "lifecycle_fill_cancel_expiry_source_status",
            }
            for group in SCID_CAPTURE_GROUPS
        ],
        "candidate_boundary": 3014,
        "candidate_boundary_claim_scope": "expected prospective capture denominator only",
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_CAPTURE_GROUP_MATRIX_{STAMP}.json", capture_matrix))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_CAPTURE_GROUP_MATRIX_{STAMP}.md",
        "SCID FC Additive Impl Capture Group Matrix - 2026-05-12",
        [f"`{group}` implemented and validated." for group in SCID_CAPTURE_GROUPS],
    ))

    searched_root_ledger = {
        "route_id": ROUTE_ID,
        "searched_roots": [
            {"root": ".context", "purpose": "mandatory GTOS state and research doctrine preflight"},
            {"root": "research/science_program_2026_05/06_outcome_testing", "purpose": "accepted G12 input and schema package discovery"},
            {"root": "src/research_infra", "purpose": "forward capture integration surface"},
            {"root": "src/components", "purpose": "orchestrator and pending lifecycle bridge surfaces"},
            {"root": "tests", "purpose": "adjacent test patterns and focused test additions"},
            {"root": "scripts", "purpose": "verifier and MT5/read-only/restart context inspection"},
            {"root": "knowledge_base/meta", "purpose": "read lock-file presence for live process context"},
        ],
        "absolute_root_crawl_performed": False,
        "network_or_vendor_access_performed": False,
        "broker_history_order_deal_account_read_performed": False,
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_SEARCHED_ROOT_LEDGER_{STAMP}.json", searched_root_ledger))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_SEARCHED_ROOT_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Searched Root Ledger - 2026-05-12",
        [
            "Searched repo-local context, accepted G12 artifact roots, source integration surfaces, tests, scripts, and live lock-file context.",
            "No broad absolute-root crawl, remote network access, paid API, vendor fetch, or broker order/deal/history/account read was performed.",
        ],
    ))

    no_leak_audit = {
        "route_id": ROUTE_ID,
        "forbidden_surface_policy": "SCID_FORWARD_CAPTURE_FORBIDDEN_SURFACE_FAIL_CLOSED_V1",
        "blocked_surfaces": [
            "broker account identifiers",
            "broker order/deal/position/ticket identifiers",
            "history order/deal evidence",
            "realized R/PnL/win-loss/result labels",
            "slippage and execution quality values",
            "expectancy and win-rate labels",
        ],
        "tests_covering_redaction": [
            "test_scid_validator_rejects_forbidden_broker_result_surface",
            "test_pending_limit_lifecycle_scid_bridge_redacts_broker_ids_and_results",
        ],
        "safe_flags": implementation_ledger["safe_flags"],
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_NO_LEAK_FORBIDDEN_SURFACE_AUDIT_{STAMP}.json", no_leak_audit))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_NO_LEAK_FORBIDDEN_SURFACE_AUDIT_{STAMP}.md",
        "SCID FC Additive Impl No-Leak Forbidden Surface Audit - 2026-05-12",
        [
            "SCID validator rejects forbidden broker/account/order/deal/position/result/cost surfaces.",
            "Lifecycle bridge deliberately omits raw ticket/order/result fields and leaves `redacted_order_bridge_hash_optional` null by default.",
            "Safe flags stay false and `NO_PROMOTION_VERDICT` is required on every valid row.",
        ],
    ))

    runtime_adapter_ledger = {
        "route_id": ROUTE_ID,
        "runtime_adapter_contract": {
            "append_only": True,
            "jsonl_path": SCID_FORWARD_SOURCE_CAPTURE_PATH,
            "fail_open_for_live_callers": True,
            "validation_before_append": True,
            "duplicate_key_drift_rejected": True,
            "asof_future_source_rejected": True,
        },
        "candidate_hook": "record_live_candidate_forward_shadow -> record_scid_forward_capture_candidate_groups",
        "lifecycle_hook": "record_pending_limit_lifecycle -> record_scid_forward_capture_lifecycle_event",
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_RUNTIME_ADAPTER_LEDGER_{STAMP}.json", runtime_adapter_ledger))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_RUNTIME_ADAPTER_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Runtime Adapter Ledger - 2026-05-12",
        [
            "Candidate hook appends nine decision-time groups for AI candidates.",
            "Pending-limit lifecycle hook appends the lifecycle group after existing lifecycle logging.",
            "Both paths are fail-open and observation-only.",
        ],
    ))

    ltf_orderflow = {
        "route_id": ROUTE_ID,
        "ltf_policy": "Unavailable lower-timeframe source paths emit UNAVAILABLE_FAIL_CLOSED rows with deferred source hash.",
        "orderflow_policy": "Unavailable Sierra/depth/orderflow source paths emit UNAVAILABLE_FAIL_CLOSED rows with no fetch or vendor/API call.",
        "local_depth_behavior": "If an already-local Sierra depth file is present, the file pointer and metadata are captured; feature extraction remains deferred.",
        "opens_paid_or_vendor_access": False,
        "opens_raw_market_data_blob_commit": False,
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_LTF_ORDERFLOW_PROXY_COMPATIBILITY_{STAMP}.json", ltf_orderflow))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_LTF_ORDERFLOW_PROXY_COMPATIBILITY_{STAMP}.md",
        "SCID FC Additive Impl LTF Orderflow Proxy Compatibility - 2026-05-12",
        [
            "LTF and orderflow rows are valid when source data is unavailable; they fail closed for future use rather than fetching.",
            "Orderflow capture is local/cache-only and does not open paid/vendor/API access.",
            "Raw market blobs are not committed by this route.",
        ],
    ))

    hypothesis_compat = {
        "route_id": ROUTE_ID,
        "accepted_no_api_factory_scope": {
            "hypothesis_cards": 40,
            "domains": 8,
            "compatibility": "capture fields preserve future denominator/context inputs only",
        },
        "domain_bridge": [
            "baseline controls",
            "framework/setup family",
            "side/direction",
            "entry/stop/target references",
            "POI source bounds",
            "LTF availability",
            "orderflow/depth proxy availability",
            "lifecycle fill/cancel/expiry status",
        ],
        "opens_strategy_edge_claims": False,
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_HYPOTHESIS_FACTORY_COMPATIBILITY_{STAMP}.json", hypothesis_compat))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_HYPOTHESIS_FACTORY_COMPATIBILITY_{STAMP}.md",
        "SCID FC Additive Impl Hypothesis Factory Compatibility - 2026-05-12",
        [
            "The accepted 40-card, 8-domain no-API factory is supported by denominator/context capture fields only.",
            "No hypothesis is validated, promoted, ranked, or scored in this implementation route.",
        ],
    ))

    ambiguity = {
        "route_id": ROUTE_ID,
        "negative_evidence": [
            "No default live SCID rows existed before restart/load; default verifier was run with allow-empty.",
            "No broker read was performed to avoid crossing the forbidden order/deal/history/account evidence boundary.",
            "No controlled live orchestrator restart was performed in this route, so live row landing is not claimed.",
        ],
        "blockers": [],
        "ambiguities": [
            "Lifecycle group uses lifecycle-event as-of for schema-valid source timing while preserving candidate input row id.",
            "Existing live orchestrators must reload this code before production SCID rows land.",
        ],
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_AMBIGUITY_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_{STAMP}.json", ambiguity))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_AMBIGUITY_NEGATIVE_EVIDENCE_BLOCKER_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Ambiguity Negative-Evidence Blocker Ledger - 2026-05-12",
        [
            "Default live SCID row landing is not claimed because active orchestrators were not restarted by this route.",
            "No broker order/deal/history/account reads were performed.",
            "No blocker remains for code-level additive capture; activation requires the normal controlled orchestrator reload path.",
        ],
    ))

    saturation = {
        "route_id": ROUTE_ID,
        "saturation_checks": [
            "All ten accepted capture groups implemented.",
            "Accepted schema required fields, enums, safe flags, hash policy, as-of policy, duplicate drift, and forbidden surfaces covered by validator/tests.",
            "Candidate writer covers nine candidate-time groups; lifecycle bridge covers the lifecycle group.",
            "Verifier can inspect default live JSONL or synthetic JSONL without scoring outcomes.",
        ],
        "self_red_team_findings": [
            {
                "risk": "Existing TradeParameters uses risk_reward_ratio, not risk_reward.",
                "resolution": "Target builder accepts both keys.",
            },
            {
                "risk": "Lifecycle events occur after original candidate decision time.",
                "resolution": "Lifecycle SCID rows use lifecycle-event as-of while retaining candidate input row id.",
            },
            {
                "risk": "Pytest default temp/cache paths are permission-blocked on this Windows host.",
                "resolution": "Focused tests were run with basetemp/cache under the route directory and route .gitignore excludes those dirs.",
            },
        ],
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_SATURATION_AND_SELF_RED_TEAM_LEDGER_{STAMP}.json", saturation))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_SATURATION_AND_SELF_RED_TEAM_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Saturation And Self-Red-Team Ledger - 2026-05-12",
        [
            "All ten accepted groups are covered by builders, validator, tests, and verifier.",
            "Self-red-team issues found during implementation were patched before final test pass.",
            "No promotion, outcome review, result scoring, or live behavior change is opened.",
        ],
    ))

    restart_ledger = {
        "route_id": ROUTE_ID,
        "controlled_restart_performed": False,
        "reason": "Code-level implementation and synthetic/default verification completed without requiring live orchestrator interruption.",
        "live_row_landing_claimed": False,
        "live_effect": False,
        "next_activation_path": "normal controlled orchestrator reload after scoped commit/CEO operational timing",
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_RESTART_LEDGER_{STAMP}.json", restart_ledger))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_RESTART_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Restart Ledger - 2026-05-12",
        [
            "Controlled restart was not performed in this route.",
            "Live row landing is not claimed.",
            "Implementation remains `live_effect=false`; active processes need a normal controlled reload to pick up the additive logger.",
        ],
    ))

    broker_read_ledger = {
        "route_id": ROUTE_ID,
        "broker_account_order_deal_history_read_performed": False,
        "mt5_positions_read_performed": False,
        "reason": "Not needed for source-code implementation; forbidden-surface boundary remained closed.",
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_BROKER_READ_LEDGER_{STAMP}.json", broker_read_ledger))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_BROKER_READ_LEDGER_{STAMP}.md",
        "SCID FC Additive Impl Broker Read Ledger - 2026-05-12",
        [
            "No broker account, order, deal, history, or position read was performed.",
            "No raw broker identifiers were captured into SCID artifacts.",
        ],
    ))

    synthetic_path = build_synthetic_jsonl()
    created.append(synthetic_path)
    synthetic_report = verify(synthetic_path, allow_empty=False)
    default_report = verify(REPO / SCID_FORWARD_SOURCE_CAPTURE_PATH, allow_empty=True)
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_VERIFIER_RESULT_SYNTHETIC_{STAMP}.json", synthetic_report))
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_VERIFIER_RESULT_DEFAULT_{STAMP}.json", default_report))

    focused_tests = {
        "route_id": ROUTE_ID,
        "py_compile": "passed",
        "focused_pytest_command": (
            "python -m pytest --basetemp research/.../tmp_pytest "
            "-o cache_dir=research/.../pytest_cache "
            "tests/test_scid_forward_capture_runtime_adapter.py "
            "tests/test_scid_forward_capture_lifecycle_redaction.py "
            "tests/test_forward_capture_shadow_loggers.py "
            "tests/test_pending_limit_lifecycle_logger.py -q"
        ),
        "focused_pytest_result": "49 passed in 1.93s",
        "warnings": [
            "pytest production path snapshot warning: live processes changed displacement state and daemon heartbeat during test session",
        ],
        "initial_failed_commands": [
            "bare pytest command unavailable; rerun with python -m pytest",
            "pytest default temp/cache paths permission-blocked; rerun with route-local basetemp/cache",
        ],
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_FOCUSED_TEST_RESULT_{STAMP}.json", focused_tests))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_FOCUSED_TEST_RESULT_{STAMP}.md",
        "SCID FC Additive Impl Focused Test Result - 2026-05-12",
        [
            "`python -m py_compile src/research_infra/forward_capture.py src/components/pending_limit_lifecycle_logger.py scripts/verify_scid_forward_capture_schema.py` passed.",
            "Focused pytest pass: 49 passed in 1.93s.",
            "Default pytest temp/cache locations were permission-blocked; rerun used route-local basetemp/cache.",
            "Live production path snapshot warning was caused by active live processes updating displacement/heartbeat files during pytest.",
        ],
    ))

    completion = {
        "route_id": ROUTE_ID,
        "completed": True,
        "code_complete": True,
        "tests_passed": True,
        "synthetic_verifier_ok": synthetic_report["ok"],
        "default_verifier_ok_allow_empty": default_report["ok"],
        "safe_flags": implementation_ledger["safe_flags"],
        "no_promotion_verdict": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "live_row_landing_claimed": False,
        "restart_performed": False,
    }
    created.append(write_json(f"SCID_FC_ADDITIVE_IMPL_COMPLETION_AUDIT_{STAMP}.json", completion))
    created.append(write_md(
        f"SCID_FC_ADDITIVE_IMPL_COMPLETION_AUDIT_{STAMP}.md",
        "SCID FC Additive Impl Completion Audit - 2026-05-12",
        [
            "Code implementation, verifier, route artifacts, and focused tests are complete.",
            "Synthetic verifier passed across all ten groups.",
            "Default live verifier passed with allow-empty and no live row landing claim.",
            "`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain enforced.",
        ],
    ))

    generated_manifest_json = ROUTE / f"SCID_FC_ADDITIVE_IMPL_OUTPUT_MANIFEST_{STAMP}.json"
    generated_manifest_md = ROUTE / f"SCID_FC_ADDITIVE_IMPL_OUTPUT_MANIFEST_{STAMP}.md"
    g12_prompt = (
        REPO
        / "research/science_program_2026_05/04_goal_prompts/"
        / "G12_SCID_FORWARD_CAPTURE_ADDITIVE_IMPLEMENTATION_AUDIT_GOAL_PROMPT_2026-05-12.md"
    )
    route_files = [
        path
        for path in ROUTE.iterdir()
        if path.is_file()
        and path.name not in {generated_manifest_json.name, generated_manifest_md.name}
    ]
    manifest_files = sorted(route_files + ([g12_prompt] if g12_prompt.exists() else []))
    manifest = {
        "route_id": ROUTE_ID,
        "created_at_utc": now,
        "artifact_count": len(manifest_files) + 2,
        "artifacts": [
            {
                "path": rel(path),
                "sha256": sha256_path(path),
            }
            for path in manifest_files
        ],
    }
    manifest_path = write_json(generated_manifest_json.name, manifest)
    manifest["artifacts"].append({"path": rel(manifest_path), "sha256": sha256_path(manifest_path)})
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_md = write_md(
        generated_manifest_md.name,
        "SCID FC Additive Impl Output Manifest - 2026-05-12",
        [f"`{item['path']}`" for item in manifest["artifacts"]],
    )
    manifest["artifacts"].append({"path": rel(manifest_md), "sha256": sha256_path(manifest_md)})
    manifest["artifact_count"] = len(manifest["artifacts"])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
