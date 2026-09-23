from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
OUTCOME_DIR = ROUTE_DIR.parent
PREFIX = "NOFILL_HIST_SOURCE_EXPANSION"
VERIFIER_PATH = ROUTE_DIR / "verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"


def _load_json(name: str):
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _load_jsonl(name: str):
    rows = []
    with (ROUTE_DIR / name).open(encoding="utf-8") as handle:
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


def test_packet_manifest_and_rows_are_source_control_only():
    manifest = _load_json(f"{PREFIX}_CANDIDATE_PACKET_MANIFEST_2026-05-10.json")
    rows = _load_jsonl(f"{PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl")
    assert manifest["terminal_decision"] == "ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT"
    assert manifest["packet_row_count"] == len(rows) == 2
    assert manifest["validation_safe"] is False
    assert manifest["outcome_review_opened"] is False
    assert manifest["live_effect"] is False
    assert {row["source_date"] for row in rows} == {"2026-05-08"}
    assert {row["symbol"] for row in rows} == {"NAS100", "US30_cash"}
    assert all(row["promotion_verdict"] == "NO_PROMOTION_VERDICT" for row in rows)


def test_every_packet_row_has_55_fields_and_future20_fields():
    rows = _load_jsonl(f"{PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl")
    binding = _load_json(f"{PREFIX}_55_FIELD_BINDING_CHECKLIST_2026-05-10.json")
    future20 = _load_json(f"{PREFIX}_FUTURE20_EXTRACTION_FAIL_CLOSED_LEDGER_2026-05-10.json")
    parent_checklist = json.loads(
        (
            OUTCOME_DIR
            / "g0_nofill_historical_partition_source_binding_synthesis_control_review"
            / "G0_NOFILL_HIST_SYNTHESIS_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json"
        ).read_text(encoding="utf-8")
    )
    expected_fields = {item["field_name"] for item in parent_checklist.get("fields", [])}
    for row in rows:
        assert expected_fields.issubset(row.keys())
        assert row["field_count"] == 55
        assert row["future_logger_field_count"] == 20
    assert binding["binding_row_count"] == len(rows) * 55
    assert len(future20["rows"]) == len(rows) * 20


def test_purge_duplicate_and_noleak_ledgers_pass():
    purge = _load_json(f"{PREFIX}_CONTAMINATION_PURGE_LEDGER_2026-05-10.json")
    duplicate = _load_json(f"{PREFIX}_DUPLICATE_DENOMINATOR_LEDGER_2026-05-10.json")
    noleak = _load_json(f"{PREFIX}_NOLEAK_AUDIT_2026-05-10.json")
    rows = _load_jsonl(f"{PREFIX}_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl")
    assert purge["admitted_overlap_counts"]["contaminated_or_embargo_date"] == 0
    assert duplicate["row_level_count"] == len(rows)
    assert duplicate["primary_duplicate_denominator"]["unique_count"] == len(rows)
    assert duplicate["secondary_duplicate_denominator"]["unique_count"] == len(rows)
    assert noleak["packet_forbidden_raw_key_hit_count"] == 0
    assert noleak["result_cost_broker_fields_entered_admitted_rows"] is False


def test_source_hash_manifest_covers_raw_and_parser_sources():
    manifest = _load_json(f"{PREFIX}_SOURCE_HASH_MANIFEST_2026-05-10.json")
    roles = {row["role"] for row in manifest["records"]}
    assert "raw_tick_parquet_admitted_row_source" in roles
    assert "raw_shadow_log" in roles
    assert "parser_or_verifier:builder" in roles
    assert "parser_or_verifier:verifier" in roles
    assert manifest["missing_source_record_count"] == 0
    for row in manifest["records"]:
        assert isinstance(row["sha256"], str)
        assert len(row["sha256"]) == 64


def test_next_g12_prompt_pack_exists_and_keeps_validation_closed():
    prompt = (ROUTE_DIR / f"{PREFIX}_NEXT_G12_SOURCE_CONTROL_AUDIT_PROMPT_PACK_2026-05-10.md").read_text(
        encoding="utf-8"
    )
    assert "NO_PROMOTION_VERDICT" in prompt
    assert "validation_safe=false" in prompt
    assert "Do not open result" in prompt
    assert "ACCEPT_AS_G12_SOURCE_CONTROL_PACKET" in prompt


def test_verifier_accepts_generated_route():
    verifier = _load_module(VERIFIER_PATH, "nofill_source_expansion_verifier")
    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["packet_row_count"] == 2
