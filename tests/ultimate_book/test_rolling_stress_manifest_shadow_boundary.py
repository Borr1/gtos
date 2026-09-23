import json
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_v4_rolling_stress_manifest_and_foundation_shadow_boundary_2026_06_18")


def _json(name):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def test_rolling_stress_manifest_seals_canonical_inputs():
    verification = _json("ROLLING_STRESS_MANIFEST_VERIFICATION_RESULT.json")
    replay = _json("ROLLING_STRESS_REPLAY_RESULT_SUMMARY.json")

    assert verification["ok"] is True
    assert verification["canonical_day_count"] == 8
    assert verification["rolling_scripts"] == 8
    assert verification["canonical_summaries_present"] is True
    assert verification["canonical_source_manifests_present"] is True
    assert verification["timewarp_manifest_count"] >= 10
    assert replay["all_canonical_summaries_present"] is True
    assert replay["all_canonical_source_manifests_present"] is True


def test_foundation_boundary_is_shadow_only_and_raw_payloads_are_cold():
    verification = _json("ROLLING_STRESS_MANIFEST_VERIFICATION_RESULT.json")
    boundary = _json("FOUNDATION_SHADOW_BOUNDARY_LEDGER.json")
    scope = _json("SCOPE_EXCLUDE_LEDGER.json")

    assert boundary["live_authority"] is False
    assert boundary["runtime_effect_now"] == "none"
    assert "sizing increase" in boundary["forbidden_now"]
    assert "MoE routing" in boundary["forbidden_now"]
    assert scope["orderflow_depth_excluded"] is True
    assert scope["raw_payloads_not_staged_by_this_route"] is True
    assert verification["raw_cold_pointer_rows"] > 0
    assert verification["orderflow_used"] is False
    assert verification["broker_or_order_mutation"] is False
