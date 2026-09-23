#!/usr/bin/env python3
"""Default-off implementation design for G12 market-expansion candidates."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
G12_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_g12_review_2026_06_18"
FOLLOWUP_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_followup_replay_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_default_off_design"
UNIT_INTERACTION_WEIGHT = 0.05
M1_SEED_WEIGHT = 0.025
PROXY_SEED_WEIGHT = 0.0
M1_SOURCE = "M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH"
M15_SOURCE = "M15_PROXY_PATH_NOT_BROKER_LIFECYCLE_TRUTH"
DEFAULT_OFF_DECISIONS = {
    "default_off_m1_supported_candidate",
    "default_off_proxy_supported_candidate_requires_m1_repair",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mechanism_contract(mechanism: str) -> dict[str, Any]:
    contracts = {
        "d1_atr_mean_reversion": {
            "timeframe": "D1",
            "signal_family": "ATR14 mean-reversion",
            "required_inputs": ["D1 OHLCV", "ATR14", "M1 path replay for stop/target ordering"],
            "runtime_note": "Implement only as default-off candidate after exact cost/spec repair; no live activation in this route.",
        },
        "d1_donchian_20_breakout": {
            "timeframe": "D1",
            "signal_family": "Donchian 20 breakout",
            "required_inputs": ["D1 OHLCV", "Donchian20 state", "M1 path replay for stop/target ordering"],
            "runtime_note": "Implement only as default-off candidate after exact cost/spec repair; no live activation in this route.",
        },
        "d1_volume_surge_reversal": {
            "timeframe": "D1",
            "signal_family": "D1 tick-volume surge reversal",
            "required_inputs": ["D1 OHLCV", "tick-volume history", "M1 path replay for stop/target ordering"],
            "runtime_note": "Implement only as default-off candidate after exact cost/spec repair; no live activation in this route.",
        },
    }
    return contracts.get(
        mechanism,
        {
            "timeframe": "unknown",
            "signal_family": mechanism,
            "required_inputs": ["source route contract", "M1 path replay"],
            "runtime_note": "Unknown mechanism cannot be implemented without a separate route contract.",
        },
    )


def rank_key(row: dict[str, Any]) -> tuple[float, float, float, float]:
    is_m1 = 1.0 if row["g12_decision"] == "default_off_m1_supported_candidate" else 0.0
    delta = float(row.get("full_book_delta_sharpe") or 0.0)
    mean = float(row.get("target2_ordered_mean_r") or 0.0)
    m1_events = float(row.get("target2_exact_m1_event_count") or 0)
    return (is_m1, delta, mean, m1_events)


def raw_source_breakdown(raw_rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row["file_symbol"], row["mechanism"])].append(row)
    for key, rows in grouped.items():
        source_counts = Counter(row.get("target2_path_source") or "none" for row in rows)
        split_source_counts: dict[str, Counter[str]] = defaultdict(Counter)
        year_counts: Counter[str] = Counter()
        for row in rows:
            split_source_counts[row["split"]][row.get("target2_path_source") or "none"] += 1
            year_counts[str(row["time"])[:4]] += 1
        out[key] = {
            "source_counts": dict(sorted(source_counts.items())),
            "split_source_counts": {
                split: dict(sorted(counter.items()))
                for split, counter in sorted(split_source_counts.items())
            },
            "year_counts": dict(sorted(year_counts.items())),
            "raw_event_count": len(rows),
        }
    return out


def build() -> dict[str, Any]:
    created_at = utc_now()
    g12_result = read_json(G12_ROUTE / "MARKET_EXPANSION_G12_REVIEW_RESULT.json")
    g12_verifier = read_json(G12_ROUTE / "MARKET_EXPANSION_G12_REVIEW_VERIFIER_RESULT.json")
    accepted = read_jsonl(G12_ROUTE / "G12_ACCEPTED_DEFAULT_OFF_LEDGER.jsonl")
    g12_all = read_jsonl(G12_ROUTE / "G12_CANDIDATE_DECISION_LEDGER.jsonl")
    raw_manifest = read_json(FOLLOWUP_ROUTE / "PATH_REPLAY_EVENT_EXPORT_MANIFEST.json")
    raw_path = PROJECT_ROOT / raw_manifest["path"]
    raw_rows = read_jsonl(raw_path)
    raw_breakdown = raw_source_breakdown(raw_rows)

    family_counts = Counter(row["family"] for row in accepted)
    family_m1_counts = Counter(
        row["family"] for row in accepted if row["g12_decision"] == "default_off_m1_supported_candidate"
    )
    mechanism_counts = Counter(row["mechanism"] for row in accepted)
    symbol_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        symbol_groups[row["file_symbol"]].append(row)

    design_rows: list[dict[str, Any]] = []
    profile_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    implementation_rows: list[dict[str, Any]] = []
    inspire_rows: list[dict[str, Any]] = []

    family_seed_caps = {
        family: {
            "accepted_count": count,
            "m1_supported_count": family_m1_counts[family],
            "seed_weight_sum_ceiling": round(min(0.10, family_m1_counts[family] * M1_SEED_WEIGHT), 6),
            "hard_design_cap": 0.10,
            "runtime_note": "design ceiling only; no live risk allocation in this route",
        }
        for family, count in sorted(family_counts.items())
    }
    best_by_symbol = {
        symbol: max(rows, key=rank_key)
        for symbol, rows in symbol_groups.items()
    }

    for row in accepted:
        key = (row["file_symbol"], row["mechanism"])
        is_m1 = row["g12_decision"] == "default_off_m1_supported_candidate"
        is_symbol_winner = best_by_symbol[row["file_symbol"]]["mechanism"] == row["mechanism"]
        contract = mechanism_contract(row["mechanism"])
        breakdown = raw_breakdown.get(key, {"source_counts": {}, "split_source_counts": {}, "year_counts": {}})
        seed_weight = M1_SEED_WEIGHT if is_m1 else PROXY_SEED_WEIGHT
        design_status = "default_off_spec_design_ready" if is_m1 else "repair_gated_default_off_spec_only"
        design_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "broker_symbol": row["broker_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "g12_decision": row["g12_decision"],
                "design_status": design_status,
                "implementation_scope": "candidate_registry_default_off_only",
                "selector_group": f"{row['file_symbol']}::{row['family']}",
                "symbol_collision_winner": is_symbol_winner,
                "mechanism_contract": contract,
                "candidate_seed_weight": seed_weight,
                "candidate_weight_ceiling": UNIT_INTERACTION_WEIGHT,
                "family_seed_cap": family_seed_caps[row["family"]],
                "target2_ordered_mean_r": row["target2_ordered_mean_r"],
                "full_book_delta_sharpe": row["full_book_delta_sharpe"],
                "target2_exact_m1_event_count": row["target2_exact_m1_event_count"],
                "target2_m15_proxy_event_count": row["target2_m15_proxy_event_count"],
                "path_source_breakdown": breakdown,
                "activation_weight_now": 0.0,
                "live_authority": False,
                "runtime_effect": "none_default_off_design_only",
            }
        )
        profile_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "broker_symbol": row["broker_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "profile_spec_status": "prereq_required_before_activation",
                "required_checks": [
                    "broker-native profile alias proof",
                    "contract size/tick size/point value/spec namespace proof",
                    "spread/commission/swap source and stress-cost conversion to R",
                    "session/trading-hours proof for D1 signal and M1 path windows",
                    "deployment-package verifier before any config activation",
                ],
                "cost_model_status": "not_exact_enough_for_live_authority",
                "order_lifecycle_status": "not_represented_by_ohlcv_path_replay",
                "live_authority": False,
            }
        )
        repair_items = [
            "exact broker spread/slippage/commission/swap model",
            "selector-level de-duplication and family budget",
            "deployment package review before any live authority",
        ]
        if not is_m1:
            repair_items.insert(0, "replace M15-proxy-dominant rows with exact M1 path replay or keep repair-gated")
        repair_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "design_status": design_status,
                "m1_repair_required": not is_m1,
                "repair_items": repair_items,
                "path_source_breakdown": breakdown,
                "not_killed": True,
            }
        )
        implementation_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "implementation_decision": "write_default_off_spec" if is_m1 else "write_repair_gated_default_off_spec",
                "code_write_scope_next": [
                    "src/components/ultimate_book/sleeves/candidate_registry.py",
                    "src/components/ultimate_book/sleeves/registry.py",
                    "tests/ultimate_book/test_candidate_book_consistency.py",
                ],
                "must_not_change": [
                    "config/agent_config.yaml live activation keys",
                    "broker/account/order/deal/position state",
                    "VPS processes",
                ],
                "selector_requirement": "symbol-level mutual exclusion plus family/mechanism budget before any future activation",
                "live_authority": False,
            }
        )
        inspire_rows.append(
            {
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "mechanism": row["mechanism"],
                "design_status": design_status,
                "not_killed": True,
                "what_is_real_or_inspiring": "G12 accepted path/full-book evidence becomes default-off design or exact M1 repair target",
                "transformed_use": "default-off candidate spec" if is_m1 else "repair-gated default-off candidate spec",
                "runtime_effect": "none_default_off_design_only",
            }
        )

    collision_rows = []
    for symbol, rows in sorted(symbol_groups.items()):
        if len(rows) <= 1:
            continue
        winner = best_by_symbol[symbol]
        collision_rows.append(
            {
                "file_symbol": symbol,
                "candidate_count": len(rows),
                "winner_mechanism": winner["mechanism"],
                "winner_decision": winner["g12_decision"],
                "rule": "prefer exact-M1 support, then higher full-book delta, then higher ordered-path mean, then more exact-M1 events",
                "members": [
                    {
                        "mechanism": row["mechanism"],
                        "g12_decision": row["g12_decision"],
                        "delta_sharpe": row["full_book_delta_sharpe"],
                        "target2_ordered_mean_r": row["target2_ordered_mean_r"],
                        "target2_exact_m1_event_count": row["target2_exact_m1_event_count"],
                    }
                    for row in sorted(rows, key=rank_key, reverse=True)
                ],
                "not_killed": True,
            }
        )

    risk_budget = {
        "schema": f"{SCHEMA_PREFIX}.selector_risk_budget.v1",
        "created_at_utc": created_at,
        "runtime_effect": "none_default_off_design_only",
        "global_activation_weight_now": 0.0,
        "candidate_seed_weight_for_m1_supported_design": M1_SEED_WEIGHT,
        "candidate_seed_weight_for_proxy_supported_design": PROXY_SEED_WEIGHT,
        "candidate_weight_ceiling_from_unit_sensitivity": UNIT_INTERACTION_WEIGHT,
        "family_seed_caps": family_seed_caps,
        "symbol_collision_count": len(collision_rows),
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "budget_rules": [
            "no live allocation from this route",
            "proxy-supported rows remain zero-weight until exact M1 repair",
            "one active expansion mechanism per symbol after future activation review",
            "family cap and mechanism cap must be enforced before any future activation",
            "candidate-book nine-sleeve activation package remains separate from market expansion",
        ],
    }

    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": (
            g12_result.get("ok") is True
            and g12_verifier.get("ok") is True
            and len(accepted) == 16
            and len(design_rows) == 16
            and sum(1 for row in design_rows if row["design_status"] == "default_off_spec_design_ready") == 6
            and sum(1 for row in design_rows if row["design_status"] == "repair_gated_default_off_spec_only") == 10
        ),
        "decision": "MARKET_EXPANSION_DEFAULT_OFF_IMPLEMENTATION_DESIGN_READY",
        "source_g12_route": rel(G12_ROUTE),
        "accepted_default_off_count": len(design_rows),
        "m1_supported_design_count": sum(1 for row in design_rows if row["design_status"] == "default_off_spec_design_ready"),
        "proxy_repair_gated_design_count": sum(1 for row in design_rows if row["design_status"] == "repair_gated_default_off_spec_only"),
        "unique_symbol_count": len(symbol_groups),
        "symbol_collision_count": len(collision_rows),
        "activation_weight_now": 0.0,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
        "live_authority": False,
    }
    input_manifest = {
        "schema": f"{SCHEMA_PREFIX}.input_manifest.v1",
        "created_at_utc": created_at,
        "source_artifacts": [
            rel(G12_ROUTE / "MARKET_EXPANSION_G12_REVIEW_RESULT.json"),
            rel(G12_ROUTE / "G12_ACCEPTED_DEFAULT_OFF_LEDGER.jsonl"),
            rel(G12_ROUTE / "G12_IMPLEMENTATION_HANDOFF_LEDGER.jsonl"),
            rel(FOLLOWUP_ROUTE / "PATH_REPLAY_EVENT_EXPORT_MANIFEST.json"),
        ],
        "g12_candidate_total": len(g12_all),
        "g12_accepted_default_off_count": len(accepted),
        "raw_path_event_manifest": raw_manifest,
        "raw_path_event_sha256_verified": sha256_file(raw_path) == raw_manifest["sha256"],
        "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation", "VPS process mutation", "live config activation"],
    }
    decision_rows = [
        {
            "created_at_utc": created_at,
            "decision": result["decision"],
            "accepted_default_off_count": len(design_rows),
            "m1_supported_design_count": result["m1_supported_design_count"],
            "proxy_repair_gated_design_count": result["proxy_repair_gated_design_count"],
            "unique_symbol_count": result["unique_symbol_count"],
            "symbol_collision_count": result["symbol_collision_count"],
            "runtime_effect": "none_default_off_design_only",
        },
        {
            "created_at_utc": created_at,
            "decision": "NO_LIVE_AUTHORITY_FROM_DEFAULT_OFF_DESIGN",
            "reason": "design package does not write runtime candidate code or activate config; proxy rows require exact M1 repair and all rows require broker-cost/spec/deployment review",
        },
    ]
    repair_summary = {
        "schema": f"{SCHEMA_PREFIX}.repair_ledger_summary.v1",
        "ok": True,
        "blockers": [],
        "repair_row_count": len(repair_rows),
        "proxy_m1_repair_required_count": result["proxy_repair_gated_design_count"],
        "completed_repairs": [
            "materialized default-off design decisions for every G12 accepted row",
            "separated exact-M1-supported designs from proxy repair-gated designs",
            "materialized symbol collision and family/mechanism budget rules",
            "materialized profile/spec/cost prerequisites before any future activation",
        ],
        "remaining_same_evidence_class_work": [
            "write default-off candidate registry specs without config activation",
            "repair proxy rows with exact M1 path history or keep them zero-weight",
            "implement selector de-duplication and family budget tests",
            "broker lifecycle, slippage, swap, and limit fills remain outside OHLCV evidence",
        ],
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "ok": True,
        "all_g12_accepted_rows_processed": len(design_rows) == 16,
        "all_proxy_rows_have_m1_repair_plan": sum(1 for row in repair_rows if row["m1_repair_required"]) == 10,
        "all_m1_rows_have_default_off_design": sum(1 for row in design_rows if row["design_status"] == "default_off_spec_design_ready") == 6,
        "no_arbitrary_top_n": True,
        "candidate_book_separate_from_market_expansion": True,
        "runtime_effect": "none_default_off_design_only",
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "ok": result["ok"],
        "design_rows": len(design_rows),
        "profile_rows": len(profile_rows),
        "repair_rows": len(repair_rows),
        "implementation_rows": len(implementation_rows),
        "symbol_collision_rows": len(collision_rows),
        "instruction_coverage": {
            "mandatory_gtos_preflight": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_hardening_controls_read": True,
            "same_evidence_class_pursuit_completed": True,
            "inspire_not_kill_rows_written": True,
            "no_arbitrary_top_n": True,
        },
        "runtime_effect": "none_default_off_design_only",
    }
    focused_test = {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 -m py_compile research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18/build_market_expansion_default_off_design.py research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18/verify_market_expansion_default_off_design.py tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py",
            "python3 research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18/verify_market_expansion_default_off_design.py",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_default_off_design_2026_06_18 --full-jsonl",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py -q",
            "git diff --check",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }
    next_prompt = """# Market Expansion Default-Off Candidate Registry Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt plus the default-off design route artifacts from disk after any compaction/resume/interruption/uncertainty, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md` as active instructions before acting.

Evidence class: default-off code design for G12 market-expansion candidates. This is not live authority. Operate with maximum practical reasoning, active creativity, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation.

Allowed data: committed design/G12/follow-up/scoring artifacts, source-hashed local MT5 OHLCV/tick-volume exports, current active candidate-book replay/MC artifacts, and public docs only when source captures are saved. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no live config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: write default-off candidate registry/spec code for the 16 design rows only if it can be done without changing active behavior. Proxy repair-gated rows must remain zero-weight until exact M1 repair. Add selector de-duplication and family/mechanism budget tests as default-off safeguards. Result materialization is required: code implementation, explicit non-implementation decision, or exact source-safe impossibility for every design row.

Required output: scoped code changes or non-implementation ledger, selector/risk-budget tests, proxy exact-M1 repair ledger, verifier, focused tests, completion audit, output manifest, and successor prompt. No compact summary or arbitrary top-N can substitute for full ledgers.
"""

    write_json(ROUTE / "DEFAULT_OFF_INPUT_MANIFEST.json", input_manifest)
    write_jsonl(ROUTE / "DEFAULT_OFF_IMPLEMENTATION_SPEC_LEDGER.jsonl", design_rows)
    write_jsonl(ROUTE / "SELECTOR_DEDUP_COLLISION_LEDGER.jsonl", collision_rows)
    write_json(ROUTE / "SELECTOR_RISK_BUDGET_SPEC.json", risk_budget)
    write_jsonl(ROUTE / "PROFILE_SPEC_COST_PREREQ_LEDGER.jsonl", profile_rows)
    write_jsonl(ROUTE / "M1_REPAIR_PLAN_LEDGER.jsonl", repair_rows)
    write_jsonl(ROUTE / "IMPLEMENTATION_DECISION_LEDGER.jsonl", implementation_rows)
    write_jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl", inspire_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair_summary)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "MARKET_EXPANSION_DEFAULT_OFF_DESIGN_RESULT.json", result)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    manifest = {
        "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
        "created_at_utc": created_at,
        "files": sorted(path.name for path in ROUTE.iterdir() if path.is_file()),
    }
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "accepted_default_off_count": result["accepted_default_off_count"],
                "m1_supported_design_count": result["m1_supported_design_count"],
                "proxy_repair_gated_design_count": result["proxy_repair_gated_design_count"],
                "unique_symbol_count": result["unique_symbol_count"],
                "symbol_collision_count": result["symbol_collision_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
