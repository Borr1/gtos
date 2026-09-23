from __future__ import annotations

import importlib.util
import json
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
TARGET_PACKET_IDS = {"OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-063", "OTG0-PKT-066"}


def load_builder():
    path = OUT_DIR / "build_otb6_g6_blocker_clearing_proof_pack_2026_05_07.py"
    spec = importlib.util.spec_from_file_location("otb6_builder", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_packet_level_decisions_are_blocked_after_partial_subcomponent_clearance():
    builder = load_builder()
    packets = {packet_id: builder.load_json(path) for packet_id, path in builder.PACKET_FILES.items()}
    analysis_060 = builder.analyze_060(packets["OTG0-PKT-060"])
    analysis_066 = builder.analyze_066(
        packets["OTG0-PKT-066"],
        {"target_candidate_matches": 0, "wanted_key_paths_seen": ["mso_detected_sweeps_types"]},
    )

    assert analysis_060["packet_decision"] == "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE"
    assert analysis_060["subcomponent_clearance"]["matched_generic_comparator"] == "PROVED_LOCALLY"
    assert analysis_060["remaining_blocker"]["structured_ob_bounds"] == "NOT_PROVED"
    assert analysis_066["subcomponent_clearance"]["round_number_band_packet"] == "PROVED_LOCALLY"
    assert analysis_066["remaining_blocker"]["structured_liquidity_sweep_join"] == "NOT_PROVED"


def test_builder_outputs_required_control_flags():
    manifest = json.loads((OUT_DIR / "OTB6_G6_ARTIFACT_MANIFEST_2026-05-07.json").read_text(encoding="utf-8"))
    decision_path = OUT_DIR / "OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))

    assert manifest["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert manifest["validation_safe"] is False
    assert manifest["outcome_review_opened"] is False
    assert set(decision["packet_decisions"]) == TARGET_PACKET_IDS
    assert all(row["decision"] == "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE" for row in decision["packet_decisions"].values())


def test_capture_contracts_cover_exact_remaining_blockers():
    contract = json.loads(
        (OUT_DIR / "OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_2026-05-07.json").read_text(encoding="utf-8")
    )
    assert set(contract["contracts"]) == TARGET_PACKET_IDS
    assert "ob_created_utc" in contract["contracts"]["OTG0-PKT-060"]["required_fields"]
    assert "decision_quote_time_msc" in contract["contracts"]["OTG0-PKT-061"]["required_fields"]
    assert "changepoint_model_id" in contract["contracts"]["OTG0-PKT-063"]["required_fields"]
    assert "sweep_level" in contract["contracts"]["OTG0-PKT-066"]["required_fields"]
