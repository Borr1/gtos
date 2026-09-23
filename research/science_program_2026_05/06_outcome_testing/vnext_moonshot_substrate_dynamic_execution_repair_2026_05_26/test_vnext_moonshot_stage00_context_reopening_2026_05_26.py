import json

from verify_vnext_moonshot_stage00_context_reopening_2026_05_26 import verify


def test_stage00_context_reopening_verifier_passes_after_builder_run():
    result = verify()

    assert result["ok"], result["failures"]
    assert result["question_rows"] == 24327
    assert result["first_incomplete_invariant"] != "STAGE_00_PREFLIGHT_CONTEXT_AND_PRIOR_ROUTE_REOPENING"


def test_stage00_result_json_is_parseable():
    result = verify()

    json.dumps(result)
    assert "live_current_j46_j49" in result["dynamic_policy_names"]
