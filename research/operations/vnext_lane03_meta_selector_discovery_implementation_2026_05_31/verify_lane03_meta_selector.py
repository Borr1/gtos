"""Verify Lane03 meta-selector route artifacts."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROUTE_ID = "vnext_lane03_meta_selector_discovery_implementation_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID


def _repo(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _update_manifest_with_verification_result(path: Path) -> None:
    manifest_path = ROUTE_DIR / "LANE03_OUTPUT_MANIFEST.json"
    if not manifest_path.exists():
        return
    manifest = _read_json(manifest_path)
    outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), list) else []
    outputs = [entry for entry in outputs if entry.get("path") != _repo(path)]
    outputs.append(
        {
            "path": _repo(path),
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "line_count": None,
        }
    )
    manifest["outputs"] = outputs
    manifest["verification_result_recorded"] = _repo(path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    issues: list[str] = []
    required = [
        "LANE03_CONTEXT_ANCHOR.md",
        "LANE03_SELECTED_DENOMINATOR_METRIC_LEDGER.jsonl",
        "LANE03_META_SELECTOR_BRANCH_DECISION_LEDGER.jsonl",
        "LANE03_META_SELECTOR_RULE_PACKAGE.json",
        "LANE03_SOURCE_COMPLETENESS_CAPTURE_REPAIR_LEDGER.jsonl",
        "LANE03_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "LANE03_CONCENTRATION_GUARD_LEDGER.jsonl",
        "LANE03_SATURATION_SELF_RED_TEAM.md",
        "LANE03_COMPLETION_AUDIT.json",
        "LANE03_OUTPUT_MANIFEST.json",
        "verify_lane03_meta_selector.py",
    ]
    for name in required:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing required output {name}")

    package_path = ROUTE_DIR / "LANE03_META_SELECTOR_RULE_PACKAGE.json"
    package = _read_json(package_path) if package_path.exists() else {}
    if package.get("package_id") != "lane03_broad_selected_meta_selector_v1":
        issues.append("unexpected package_id")
    counts = package.get("rule_counts") if isinstance(package.get("rule_counts"), dict) else {}
    if int(counts.get("tradeable_rules") or 0) < 30:
        issues.append("tradeable rule count is too narrow")
    if int(counts.get("avoid_rules") or 0) <= 0:
        issues.append("missing negative risk-cell avoid rules")
    if int(counts.get("reduce_rules") or 0) <= 0:
        issues.append("missing weak risk-cell reduce rules")
    all_rules = []
    for key in ("tradeable_rules", "avoid_rules", "reduce_rules", "capture_repair_rules"):
        value = package.get(key)
        if isinstance(value, list):
            all_rules.extend(value)
    if len(all_rules) <= 2:
        issues.append("selector package collapsed to Friday two-rule subset")
    if any("friday_broad" in str(rule.get("rule_id", "")) for rule in all_rules):
        issues.append("package retained old hard-coded friday rule id")

    tradeable_keys = {
        (rule.get("session"), rule.get("origin_family"))
        for rule in package.get("tradeable_rules", [])
        if isinstance(rule, dict)
    }
    required_tradeables = {
        ("london_broad", "liquidity_sweep_reclaim"),
        ("london_broad", "displacement_continuation"),
        ("ny_broad", "current_fvg_fill"),
        ("tokyo_broad", "structural_distance_extreme"),
        ("off_kz_broad", "cross_asset_lead_lag"),
    }
    missing_tradeables = sorted(required_tradeables - tradeable_keys)
    if missing_tradeables:
        issues.append(f"missing broad tradeable mechanisms {missing_tradeables}")

    avoid_cells = {rule.get("risk_cell_id") for rule in package.get("avoid_rules", [])}
    if "USDCAD|breaker_re_entry|ny_broad|current_breaker_re_entry|SHORT" not in avoid_cells:
        issues.append("missing current negative selected-denominator USDCAD breaker avoid cell")
    reduce_cells = {rule.get("risk_cell_id") for rule in package.get("reduce_rules", [])}
    if "USDJPY|ob_retest|london_broad|current_ob_retest|LONG" not in reduce_cells:
        issues.append("missing weak accepted expectancy USDJPY ob_retest reduce cell")

    metric_count = _jsonl_count(ROUTE_DIR / "LANE03_SELECTED_DENOMINATOR_METRIC_LEDGER.jsonl")
    if metric_count < 500:
        issues.append("metric ledger too small for full selected-denominator preservation")
    branch_count = _jsonl_count(ROUTE_DIR / "LANE03_META_SELECTOR_BRANCH_DECISION_LEDGER.jsonl")
    if branch_count != metric_count:
        issues.append("branch decision ledger does not preserve every metric row")

    source_text = (ROUTE_DIR / "LANE03_SOURCE_COMPLETENESS_CAPTURE_REPAIR_LEDGER.jsonl").read_text(encoding="utf-8")
    for needle in ("broker_net_r_cost_truth", "tick_coverage", "spread_r_at_candidate"):
        if needle not in source_text:
            issues.append(f"source completeness ledger missing {needle}")

    config_text = (ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")
    if _repo(package_path) not in config_text:
        issues.append("config does not point to Lane03 selector package")
    router_text = (ROOT / "src" / "research" / "moonshot_default_off_policy_router.py").read_text(encoding="utf-8")
    if "DEFAULT_CANDIDATE_QUALITY_SELECTOR_RULES: tuple[dict[str, Any], ...] = ()" not in router_text:
        issues.append("router default Friday fallback was not removed")
    for needle in (
        "candidate_quality_negative_selected_denominator_rule",
        "reduce_risk_by_evidence",
        "candidate_quality_session_origin_not_in_selected_denominator_package",
    ):
        if needle not in router_text:
            issues.append(f"router missing selector behavior {needle}")
    runtime_text = (ROOT / "src" / "components" / "gtos_vnext_runtime.py").read_text(encoding="utf-8")
    if "_moonshot_candidate_quality_selector_package" not in runtime_text:
        issues.append("runtime package loader missing")
    tests_text = (ROOT / "tests" / "test_moonshot_default_off_policy_router.py").read_text(encoding="utf-8")
    for needle in (
        "test_candidate_quality_selector_matches_broad_session_alias",
        "test_candidate_quality_selector_avoid_rule_overrides_tradeable_rule",
        "test_candidate_quality_selector_reduce_rule_stays_tradeable_with_risk_multiplier",
        "test_candidate_quality_selector_missing_spread_requires_source_capture",
    ):
        if needle not in tests_text:
            issues.append(f"focused router test missing {needle}")

    audit = _read_json(ROUTE_DIR / "LANE03_COMPLETION_AUDIT.json")
    if audit.get("status") != "complete":
        issues.append("completion audit is not complete")
    if audit.get("forbidden_surfaces_touched") not in ([], None):
        issues.append("completion audit records forbidden surface touches")

    result = {
        "schema_version": "lane03_verification_result_v1",
        "route_id": ROUTE_ID,
        "status": "verified" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "checked_outputs": required,
        "package_rule_counts": counts,
        "metric_row_count": metric_count,
        "branch_row_count": branch_count,
    }
    result_path = ROUTE_DIR / "LANE03_VERIFICATION_RESULT.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _update_manifest_with_verification_result(result_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
