from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
ROWS_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl"


def load_builder():
    path = LANE_DIR / "build_nofill_blocked_family_source_correction_router_2026_05_08.py"
    spec = importlib.util.spec_from_file_location("nofill_router_builder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_family_routing_counts_match_frozen_starting_facts():
    builder = load_builder()
    rows = load_jsonl(ROWS_PATH)
    blocked = [row for row in rows if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"]
    counts = Counter(builder.route_family(row) for row in blocked)
    assert len(blocked) == 246
    assert counts == {
        "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": 80,
        "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": 54,
        "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": 69,
        "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": 42,
        "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": 1,
    }


def test_blocker_code_counts_preserve_overlap_row():
    rows = load_jsonl(ROWS_PATH)
    blocked = [row for row in rows if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"]
    code_counts = Counter()
    tuple_counts = Counter()
    for row in blocked:
        for code in row["result_blocker_codes"]:
            code_counts[code] += 1
        tuple_counts["+".join(row["result_blocker_codes"])] += 1
    assert code_counts["BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED"] == 1
    assert code_counts["BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS"] == 1
    assert tuple_counts["BLOCK_RESULT_SEPARATE_FILL_PATH_CONTRACT_REQUIRED+BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS"] == 1
    assert sum(tuple_counts.values()) == 246
    assert sum(code_counts.values()) == 247


def test_generated_route_ledger_covers_only_blocked_rows():
    route_path = LANE_DIR / "NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json"
    assert route_path.exists()
    route = json.loads(route_path.read_text(encoding="utf-8"))
    source_rows = load_jsonl(ROWS_PATH)
    blocked_ids = {row["packet_row_id"] for row in source_rows if row["eligibility_decision"] == "BLOCKED_BEFORE_LABEL"}
    eligible_ids = {row["packet_row_id"] for row in source_rows if row["eligibility_decision"] == "ELIGIBLE_LABEL_ASSIGNED"}
    routed_ids = {row["packet_row_id"] for row in route["row_route_decisions"]}
    assert routed_ids == blocked_ids
    assert not routed_ids & eligible_ids


def test_access_request_is_limited_to_missing_usdjpy_tick_dates():
    access_path = LANE_DIR / "NOFILL_ROUTER_ACCESS_REQUEST_LEDGER_2026-05-08.json"
    assert access_path.exists()
    access = json.loads(access_path.read_text(encoding="utf-8"))
    assert access["access_request_count"] == 1
    assert access["row_count_requiring_access_or_source_capture"] == 7
    request = access["requests"][0]
    assert request["family"] == "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT"
    assert "2026-04-17" in request["needed_source"]
    assert "2026-04-20" in request["needed_source"]
    assert request["authorized_in_router"] is False
