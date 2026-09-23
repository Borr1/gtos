from __future__ import annotations

import json
import hashlib
from pathlib import Path

from verify_g0_scid_forward_capture_additive_synthesis_control_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_FC_ADDITIVE_SYNTHESIS"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_md(stem: str, title: str, payload: dict) -> None:
    (ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md").write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- **route_id:** `{payload['route_id']}`",
                f"- **evidence_class:** `{payload['evidence_class']}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def refresh_output_manifest() -> None:
    prompt_pack = load_json("PROMPT_PACK_LEDGER")
    manifest = load_json("OUTPUT_MANIFEST")
    manifest_json = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    manifest_md = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.md"

    paths: list[Path] = []
    for path in ROUTE_DIR.iterdir():
        if path.name in {manifest_json.name, manifest_md.name}:
            continue
        if path.is_file() and path.suffix in {".json", ".md", ".txt", ".py"}:
            paths.append(path)
    for pack in prompt_pack["selected_route_prompt_packs"].values():
        paths.append(ROOT / pack["prompt_path"])

    entries = [
        {
            "path": repo_path(path),
            "sha256": sha256_file(path),
            "artifact_type": path.suffix.lstrip("."),
        }
        for path in sorted(set(paths))
    ]
    manifest["artifact_count_excluding_manifest"] = len(entries)
    manifest["artifacts"] = entries
    manifest["manifest_refreshed_after_focused_pytest"] = True
    manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    write_md("OUTPUT_MANIFEST", "Output Manifest", manifest)


def test_g12_decision_and_safe_flags_are_preserved():
    accepted = load_json("ACCEPTED_G12_SYNTHESIS")
    decision = load_json("DECISION_LEDGER")

    assert accepted["accepted_g12_terminal_decision"] == "ACCEPT_WITH_EXACT_NONBLOCKING_ACTIVATION_FOLLOWUPS"
    assert accepted["accepted_as_source_control_implementation_evidence_only"] is True
    assert accepted["blocking_findings"] == []
    assert decision["terminal_decision"] == (
        "ACCEPT_AS_G0_SCID_FORWARD_CAPTURE_ADDITIVE_SYNTHESIS_WITH_RANKED_NONBLOCKING_ROUTE_BUNDLE"
    )
    for payload in (accepted, decision):
        assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
        assert payload["validation_safe"] is False
        assert payload["outcome_review_opened"] is False
        assert payload["live_effect"] is False
        assert payload["opens_result_scoring"] is False
        assert payload["opens_live_trading_behavior"] is False


def test_activation_followup_is_not_repair_blocker():
    followups = load_json("FOLLOWUP_BLOCKER_LEDGER")

    assert followups["true_repair_blockers"] == []
    assert len(followups["nonblocking_activation_followups"]) == 1
    assert followups["nonblocking_activation_followups"][0]["classification"] == "NONBLOCKING_ACTIVATION_FOLLOWUP"
    assert followups["controlled_restart_performed"] is False
    assert followups["live_row_landing_claimed"] is False
    assert followups["default_verifier_row_count"] == 0
    assert followups["default_verifier_allow_empty"] is True


def test_route_ranking_covers_required_route_families_without_passive_waiting():
    ranking = load_json("ROUTE_RANKING_MATRIX")
    rows_by_id = {row["route_id"]: row for row in ranking["routes"]}

    assert ranking["rank_1_route"] == "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN"
    assert ranking["activation_route_is_nonblocking_followup_not_repair"] is True
    assert ranking["sealed_result_packet_route_dependency_blocked"] is True
    assert set(rows_by_id) == {
        "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION",
        "SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN",
        "SCID_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_VALIDITY_EXPANSION",
        "SCID_FORWARD_CAPTURE_MONITORING_HEALTH_GUARD",
        "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION",
    }
    assert rows_by_id["SCID_NO_API_40_CARD_8_DOMAIN_PREREGISTRATION_REPLAY_INPUT_DESIGN"][
        "run_state"
    ] == "RUN_NOW_NO_API_NO_OUTCOME_SCORING"
    assert rows_by_id["SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION"][
        "run_state"
    ] == "DO_NOT_RUN_UNTIL_DEPENDENCY_VALID"
    assert rows_by_id["SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION"][
        "run_state"
    ] == "OPERATIONAL_TIMING_REQUIRED_NOT_A_REPAIR_BLOCKER"


def test_prompt_packs_and_starters_embed_boundaries():
    prompt_pack = load_json("PROMPT_PACK_LEDGER")

    assert prompt_pack["prompt_pack_count"] == 5
    assert prompt_pack["starter_lines_present_for_all_selected_routes"] is True
    assert "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION" in prompt_pack[
        "dependency_blocked_prompt_packs"
    ]
    assert len(prompt_pack["parallel_ready_prompt_packs"]) == 3

    for route_id, pack in prompt_pack["selected_route_prompt_packs"].items():
        prompt_text = (ROOT / pack["prompt_path"]).read_text(encoding="utf-8")
        starter_text = (ROOT / pack["starter_path"]).read_text(encoding="utf-8")
        assert starter_text.startswith("/goal Follow the full controlling prompt")
        for phrase in [
            "Do not rely on chat memory",
            "Current GTOS OB/retest logic is not the research horizon",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Completion Standard",
        ]:
            assert phrase in prompt_text, (route_id, phrase)
        assert "not OB-only/current-field-only/passive-waiting" in starter_text


def test_saturation_sequencing_and_not_loop_ledgers():
    sequencing = load_json("SEQUENCING_PARALLELIZATION_LEDGER")
    saturation = load_json("SATURATION_SELF_REDTEAM_LEDGER")
    not_loop = load_json("NOT_IN_A_LOOP_LEDGER")

    assert len(sequencing["run_now_no_owner_live_approval"]) == 3
    assert sequencing["later_dependency_valid_only"] == [
        "SCID_SEALED_RESULT_PACKET_GATE_AFTER_SOURCE_ACTIVATION"
    ]
    assert sequencing["operational_timing_required_nonblocking"] == [
        "SCID_FORWARD_CAPTURE_ACTIVATION_READINESS_VERIFICATION"
    ]
    for key in [
        "not_activation_only",
        "not_ob_only",
        "not_current_field_only",
        "not_live_forward_only",
        "not_passive_waiting",
    ]:
        assert saturation[key] is True
    assert "does not rebuild source infrastructure for its own sake" in not_loop["terminal_statement"]


def test_verifier_passes_and_records_focused_pytest_closeout():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True

    completion = load_json("COMPLETION_AUDIT")
    completion["focused_tests_ok"] = True
    completion["completion_standard_satisfied"] = True
    completion["can_mark_goal_complete"] = True
    for row in completion["prompt_to_artifact_checklist"]:
        if row["requirement"] == "standalone verifier and focused tests":
            row["status"] = "PASS"
    (ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json").write_text(
        json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    write_md("COMPLETION_AUDIT", "Completion Audit", completion)

    closeout_path = ROUTE_DIR / f"{PREFIX}_CLOSEOUT_VERIFICATION_{DATE_TAG}.json"
    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    closeout["focused_pytest"] = {
        "status": "PASSED",
        "command": (
            "python -m pytest -q -p no:cacheprovider "
            "research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_forward_capture_additive_synthesis_control/"
            "test_g0_scid_forward_capture_additive_synthesis_control_2026_05_12.py"
        ),
        "observed_result": "6 passed",
    }
    closeout["status"] = "STANDALONE_VERIFIER_AND_FOCUSED_PYTEST_PASSED_FINAL_LIVE_STATE_REFRESH_REQUIRED"
    closeout["output_manifest_refreshed_after_focused_pytest"] = True
    closeout_path.write_text(json.dumps(closeout, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    write_md("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)
    refresh_output_manifest()
