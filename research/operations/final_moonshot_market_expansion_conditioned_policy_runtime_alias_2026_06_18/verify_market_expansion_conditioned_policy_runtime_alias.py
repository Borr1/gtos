#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import bridge
from src.components.ultimate_book import admission as P
from src.components.ultimate_book.sleeves import candidate_registry as CR


ROUTE = Path(__file__).resolve().parent
RESULT = ROUTE / "CONDITIONED_POLICY_RUNTIME_ALIAS_VERIFIER_RESULT.json"
MANIFEST = ROUTE / "OUTPUT_MANIFEST.json"


def check() -> dict[str, object]:
    issues: list[str] = []

    policies = P.market_expansion_conditioned_policies()
    expected_names = {
        "all14_swap_adjusted",
        "positive_weighted12_after_swap",
        "robust6_every_split_positive",
    }
    if set(policies) != expected_names:
        issues.append(f"unexpected_policy_names:{sorted(policies)}")
    if len(policies.get("all14_swap_adjusted", ())) != 14:
        issues.append("all14_count_mismatch")
    if len(policies.get("positive_weighted12_after_swap", ())) != 12:
        issues.append("positive12_count_mismatch")
    if len(policies.get("robust6_every_split_positive", ())) != 6:
        issues.append("robust6_count_mismatch")
    if not set(policies.get("robust6_every_split_positive", ())) < set(
        policies.get("positive_weighted12_after_swap", ())
    ):
        issues.append("robust6_not_subset_of_positive12")
    if set(policies.get("all14_swap_adjusted", ())) != set(
        CR.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES
    ):
        issues.append("all14_not_collision_winner_set")

    resolved, err = P.resolve_market_expansion_sleeves(
        policy="robust6_every_split_positive",
        explicit_sleeves=None,
    )
    if err or resolved != policies["robust6_every_split_positive"]:
        issues.append(f"robust6_resolve_failed:{err}:{resolved}")
    resolved, err = P.resolve_market_expansion_sleeves(
        policy=P.MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY,
        explicit_sleeves=[],
    )
    if err or resolved:
        issues.append("explicit_allowlist_empty_should_resolve_empty_without_error")
    _, err = P.resolve_market_expansion_sleeves(policy="not_a_policy", explicit_sleeves=None)
    if err != "unknown_market_expansion_policy:not_a_policy":
        issues.append("unknown_policy_error_mismatch")
    _, err = P.resolve_market_expansion_sleeves(
        policy="robust6_every_split_positive",
        explicit_sleeves=["mx_avausd_d1_donchian_20_breakout"],
    )
    if err != "market_expansion_policy_sleeve_mismatch:robust6_every_split_positive":
        issues.append("mismatch_policy_error_mismatch")

    if bridge.DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"] is not False:
        issues.append("bridge_default_market_expansion_not_false")
    if bridge.DEFAULT_CONFIG["ultimate_book_market_expansion_policy"] != P.MARKET_EXPANSION_EXPLICIT_ALLOWLIST_POLICY:
        issues.append("bridge_default_market_expansion_policy_not_explicit")
    if bridge.DEFAULT_CONFIG["ultimate_book_market_expansion_sleeves"] != []:
        issues.append("bridge_default_market_expansion_sleeves_not_empty")

    cfg = yaml.safe_load((PROJECT_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8"))
    runtime = cfg["gtos_vnext_runtime"]
    if runtime.get("ultimate_book_include_market_expansion_book") is not True:
        issues.append("agent_config_market_expansion_not_owner_activated")
    if runtime.get("ultimate_book_market_expansion_policy") != "positive_weighted12_after_swap":
        issues.append("agent_config_policy_not_positive_weighted12")
    if runtime.get("ultimate_book_market_expansion_sleeves") != []:
        issues.append("agent_config_market_expansion_sleeves_not_empty")

    described = P.describe_book()["market_expansion_book"]
    if set(described.get("conditioned_policies", {})) != expected_names:
        issues.append("describe_book_missing_conditioned_policies")

    return {
        "schema": "gtos.final_moonshot.market_expansion_conditioned_policy_runtime_alias.verifier_result.v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "policy_counts": {name: len(sleeves) for name, sleeves in policies.items()},
        "activation_boundary": {
            "bridge_include_market_expansion_book": bridge.DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"],
            "agent_config_include_market_expansion_book": runtime.get("ultimate_book_include_market_expansion_book"),
            "market_expansion_policy": runtime.get("ultimate_book_market_expansion_policy"),
        },
        "runtime_effect": "none_no_broker_or_vps_reload_executed",
    }


def write_manifest() -> None:
    paths = sorted(p for p in ROUTE.iterdir() if p.is_file())
    MANIFEST.write_text(
        json.dumps(
            {
                "schema": "gtos.final_moonshot.market_expansion_conditioned_policy_runtime_alias.output_manifest.v1",
                "files": [p.relative_to(PROJECT_ROOT).as_posix() for p in paths],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    result = check()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_manifest()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
