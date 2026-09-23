from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROUTE_DIR.parent
TARGET_DIR = OUTCOME_DIR / "nofill_historical_source_expansion_builder_local_tick_shadow_packet"
PREFIX = "NOFILL_HIST_SRCEXP_HASH_REPAIR"
TARGET_PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
DATE = "2026-05-10"
VERIFIER_PATH = ROUTE_DIR / "verify_nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_2026_05_10.py"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_exact_three_g12_hash_blockers_closed():
    closure = _load_json(ROUTE_DIR / f"{PREFIX}_EXACT_G12_BLOCKER_CLOSURE_LEDGER_{DATE}.json")
    assert closure["exact_repair_requirement_count"] == 3
    assert closure["closed_requirement_count"] == 3
    assert closure["terminal_decision"] == "REPAIR_REBUILD_READY_FOR_G12_REAUDIT"
    assert {row["role"] for row in closure["records"]} == {
        "parser_or_verifier:builder",
        "parser_or_verifier:focused_tests",
        "parser_or_verifier:verifier",
    }
    assert all(row["closed"] is True for row in closure["records"])


def test_target_packet_rows_and_counts_are_unchanged():
    rows = _load_jsonl(TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_{DATE}.jsonl")
    output = _load_json(TARGET_DIR / f"{TARGET_PREFIX}_OUTPUT_MANIFEST_{DATE}.json")
    semantic = _load_json(ROUTE_DIR / f"{PREFIX}_SEMANTIC_NO_ROW_CHANGE_DIFF_LEDGER_{DATE}.json")
    assert output["admitted_packet_row_count"] == len(rows) == 2
    assert output["blocked_candidate_count"] == 37
    assert output["rejected_candidate_count"] == 9
    assert {row["symbol"] for row in rows} == {"NAS100", "US30_cash"}
    assert semantic["semantic_counts_unchanged"] is True
    assert semantic["only_hash_derived_fields_changed"] is True


def test_packet_manifest_and_parser_bindings_are_current():
    verifier = _load_module(VERIFIER_PATH, "repair_verifier_light")
    packet = TARGET_DIR / f"{TARGET_PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_{DATE}.jsonl"
    manifest = _load_json(TARGET_DIR / f"{TARGET_PREFIX}_CANDIDATE_PACKET_MANIFEST_{DATE}.json")
    parser_asof = _load_json(TARGET_DIR / f"{TARGET_PREFIX}_PARSER_ASOF_MANIFEST_{DATE}.json")
    builder_hash = verifier.sha256_file(
        TARGET_DIR / "build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
    )
    rows = _load_jsonl(packet)
    assert manifest["packet_sha256"] == verifier.sha256_file(packet)
    assert parser_asof["parser_hash"] == builder_hash
    assert {row["parser_code_hash"] for row in rows} == {builder_hash}


def test_safe_flags_and_next_g12_prompt_pack_remain_closed():
    noleak = _load_json(ROUTE_DIR / f"{PREFIX}_NOLEAK_SAFE_FLAG_CHECK_{DATE}.json")
    decision = _load_json(ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_{DATE}.json")
    prompt = (ROUTE_DIR / f"{PREFIX}_NEXT_G12_REPAIR_REAUDIT_PROMPT_PACK_{DATE}.md").read_text(
        encoding="utf-8"
    )
    assert noleak["safe_flag_issue_count"] == 0
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert "NO_PROMOTION_VERDICT" in prompt
    assert "validation_safe=false" in prompt
    assert "outcome_review_opened=false" in prompt
    assert "live_effect=false" in prompt


def test_repair_verifier_accepts_repair_route_without_rerunning_target_commands():
    verifier = _load_module(VERIFIER_PATH, "repair_verifier")
    result = verifier.verify(run_target_checks=False)
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["packet_row_count"] == 2
    assert result["blocked_candidate_count"] == 37
    assert result["rejected_candidate_count"] == 9
