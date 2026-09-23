from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
CONFIG = REPO_ROOT / "config" / "agent_config.yaml"
ALLOWLIST = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_production_replacement_activation_2026_05_26/"
    / "VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_2026-05-26.json"
)
RUNTIME = REPO_ROOT / "src/components/gtos_vnext_runtime.py"
ORCH = REPO_ROOT / "src/components/orchestrator.py"


def read_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check:
        raise SystemExit("--check is required; verifier is non-mutating")

    issues: list[str] = []
    cfg = read_config()
    runtime = cfg.get("gtos_vnext_runtime") or {}
    expected_true = {
        "enabled",
        "apply_to_execution",
        "moonshot_dynamic_execution_router_enabled",
        "moonshot_dynamic_execution_router_apply_to_execution",
        "moonshot_broader_origin_live_generation_enabled",
        "moonshot_broader_origin_execute_pre_ai_pre_l2",
        "replacement_monitoring_enabled",
        "replacement_monitoring_log_enabled",
        "pre_ai_apply_to_ai_call",
        "ltf_path_execution_apply_to_execution",
        "prop_safe_selector_apply_to_execution",
    }
    for key in expected_true:
        if runtime.get(key) is not True:
            issues.append(f"runtime_flag_not_true:{key}:{runtime.get(key)}")
    if runtime.get("mode") != "production_replacement_vnext_moonshot":
        issues.append(f"runtime_mode:{runtime.get('mode')}")
    if runtime.get("moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols") != []:
        issues.append("exact_excluded_symbols_not_empty")
    if len(runtime.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols") or []) != 24:
        issues.append("eligible_symbol_count_not_24")
    if runtime.get("ai_policy_allow_legacy_broad_fallback") is not False:
        issues.append("ai_policy_allow_legacy_broad_fallback_not_false")

    allowlist = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    actions = {entry.get("activation_action") for entry in allowlist.get("entries") or []}
    if actions != {"TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"}:
        issues.append(f"broader_origin_activation_actions:{sorted(str(action) for action in actions)}")
    runtime_text = RUNTIME.read_text(encoding="utf-8")
    orch_text = ORCH.read_text(encoding="utf-8")
    if "trade_default_off_broader_origin_candidate" in runtime_text.casefold():
        issues.append("active_runtime_matches_default_off_broader_origin_action")
    if "Run the default-off moonshot dynamic execution router" in orch_text:
        issues.append("orchestrator_active_docstring_default_off")
    if "Evaluate the default-off moonshot dynamic execution router" in runtime_text:
        issues.append("runtime_active_docstring_default_off")

    result = {
        "mode": "check",
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "eligible_symbols": len(runtime.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols") or []),
        "broader_origin_activation_actions": sorted(str(action) for action in actions),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
