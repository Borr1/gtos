import json
from collections import Counter
from pathlib import Path


ROUTE = Path("research/operations/final_moonshot_market_expansion_followup_replay_2026_06_18")
PROJECT_ROOT = Path(".")
M1_SOURCE = "M1_ORDERED_PRICE_PATH_REPLAY_NOT_BROKER_LIFECYCLE_TRUTH"
M15_SOURCE = "M15_PROXY_PATH_NOT_BROKER_LIFECYCLE_TRUTH"


def _load(name: str):
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def _jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_followup_replay_denominator_and_boundaries():
    result = _load("MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json")
    verification = _load("MARKET_EXPANSION_FOLLOWUP_REPLAY_VERIFIER_RESULT.json")
    completion = _load("COMPLETION_AUDIT.json")
    saturation = _load("SATURATION_AUDIT.json")
    path_manifest = _load("PATH_REPLAY_EVENT_EXPORT_MANIFEST.json")
    candidate_rows = _jsonl(ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl")

    assert result["ok"] is True
    assert verification["ok"] is True
    assert result["candidate_result_count"] == 820
    assert len(candidate_rows) == 820
    assert result["source_event_count"] == 190617
    assert result["first_pass_promoted_count"] == 33
    assert result["near_miss_positive_proxy_count"] == 42
    assert result["deep_replay_selected_count"] == 75
    assert result["deep_replay_source_event_count"] == 19121
    assert result["path_replay_event_count"] == 19121
    assert path_manifest["row_count"] == result["path_replay_event_count"]
    assert path_manifest["path"].startswith("data/mt5_research_exports/")
    assert len(path_manifest["sha256"]) == 64
    assert (PROJECT_ROOT / path_manifest["path"]).exists()
    assert result["orderflow_used"] is False
    assert result["broker_or_order_mutation"] is False
    assert result["config_or_live_activation_changed"] is False
    assert result["vps_process_touched"] is False
    assert result["live_authority"] is False
    assert completion["runtime_effect"] == "none_research_replay_only"
    assert saturation["ok"] is True
    assert saturation["no_arbitrary_top_n"] is True
    assert saturation["all_candidate_rows_processed"] is True
    assert saturation["deep_replay_event_rows_processed"] is True
    assert {"SPCX", "NATGAS_cash", "HEATOIL_c"}.isdisjoint({row["file_symbol"] for row in candidate_rows})


def test_followup_replay_path_evidence_and_interaction_ledgers():
    result = _load("MARKET_EXPANSION_FOLLOWUP_REPLAY_RESULT.json")
    path_manifest = _load("PATH_REPLAY_EVENT_EXPORT_MANIFEST.json")
    candidate_rows = _jsonl(ROUTE / "CANDIDATE_FOLLOWUP_REPLAY_LEDGER.jsonl")
    full_book_rows = _jsonl(ROUTE / "FULL_BOOK_INTERACTION_LEDGER.jsonl")
    geometry_rows = _jsonl(ROUTE / "GEOMETRY_STATUS_LEDGER.jsonl")
    inspire_rows = _jsonl(ROUTE / "INSPIRE_NOT_KILL_LEDGER.jsonl")
    decision_rows = _jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    raw_rows = _jsonl(PROJECT_ROOT / path_manifest["path"])

    class_counts = Counter(row["followup_class"] for row in candidate_rows)
    assert class_counts == {
        "context_only_single_stock_cfd": 290,
        "context_or_negative_proxy": 383,
        "first_pass_promoted": 33,
        "near_miss_positive_proxy": 42,
        "positive_proxy_underpowered_or_unstable": 72,
    }
    assert len(raw_rows) == result["path_replay_event_count"]
    source_counts = Counter(row.get("target2_path_source") or "none" for row in raw_rows)
    assert source_counts[M1_SOURCE] > 0
    assert source_counts[M15_SOURCE] > 0
    assert source_counts[M1_SOURCE] == sum(row["target2_exact_m1_event_count"] for row in candidate_rows)
    assert source_counts[M15_SOURCE] == sum(row["target2_m15_proxy_event_count"] for row in candidate_rows)
    assert sum(row["target2_ordered_path_event_count"] for row in candidate_rows) == (
        source_counts[M1_SOURCE] + source_counts[M15_SOURCE]
    )
    status_counts = Counter(row.get("target2_path_status") for row in raw_rows)
    assert status_counts["target_first"] > 0
    assert status_counts["stop_first"] > 0
    assert status_counts["horizon_close"] > 0
    assert sum(row["event_count"] for row in geometry_rows) == len(raw_rows)

    assert result["m1_path_ready_candidate_count"] == 41
    assert result["ordered_path_ready_candidate_count"] == 75
    assert result["full_book_interaction_row_count"] == 75
    assert result["full_book_interaction_computed_count"] == 75
    assert len(full_book_rows) == 75
    assert all(row["policy"] == "target2_ordered_path_unit_sensitivity" for row in full_book_rows)
    assert all(row["status"] == "computed_sensitivity_not_live_authority" for row in full_book_rows)
    assert any(row["delta_sharpe"] > 0 for row in full_book_rows)
    assert all("target2_ordered_path_summary" in row for row in candidate_rows)
    assert all("target2_m1_summary" not in row for row in candidate_rows)
    assert len(inspire_rows) == len(candidate_rows)
    assert all(row["not_killed"] is True for row in inspire_rows)
    assert any(row["decision"] == result["decision"] for row in decision_rows)
