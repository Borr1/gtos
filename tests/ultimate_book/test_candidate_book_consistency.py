import json
from pathlib import Path


from src.components.ultimate_book.sleeves import candidate_registry


REPO = Path(__file__).resolve().parents[2]
MECH_DIR = REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
MC_RESULT_PATH = MECH_DIR / "UNIFIED_BOOK_MC_RESULT.json"


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    return data


def test_candidate_confidence_and_status_are_complete():
    names = set(candidate_registry.CANDIDATE_NAMES)
    assert set(candidate_registry.CANDIDATES) == names
    assert set(candidate_registry.CANDIDATE_CONFIDENCE) == names
    assert set(candidate_registry.CANDIDATE_STATUS) == names

    for sleeve in ("vol_squeeze", "ny_index_momentum", "structural_retest"):
        assert candidate_registry.CANDIDATE_CONFIDENCE[sleeve] == 0.0
        assert "quarantined" in candidate_registry.CANDIDATE_STATUS[sleeve]
        assert sleeve not in candidate_registry.BOOK_PROMOTION_READY_CANDIDATE_NAMES

    assert set(candidate_registry.BOOK_PROMOTION_READY_CANDIDATE_NAMES) == {
        name for name, confidence in candidate_registry.CANDIDATE_CONFIDENCE.items() if confidence > 0.0
    }


def test_candidate_mc_package_matches_registry_names():
    mc = _read_json(MC_RESULT_PATH)
    names = set(candidate_registry.CANDIDATE_NAMES)
    assert set(mc["conf"]) == names
    assert set(mc["candidate_status"]) == names
    assert set(mc["new_sleeve_firedays"]) == names
    assert set(mc["loo_sharpe"]) == names
    assert "structural_retest" in mc["new_sleeve_firedays"]


def test_ny_crypto_momentum_uses_notlow_replacement_series():
    mc = _read_json(MC_RESULT_PATH)
    assert "kz_ny_crypto_notlow" not in mc["new_sleeve_firedays"], "not-low is a replacement fold"
    assert mc["candidate_status"]["ny_crypto_momentum"] == "promotion_candidate_notlow_replacement_applied"
    assert mc["new_sleeve_firedays"]["ny_crypto_momentum"] == 1182


def test_liq_asia_up_low_metal_uses_survivor_firedays():
    mc = _read_json(MC_RESULT_PATH)
    assert mc["new_sleeve_firedays"]["liq_asia_up_low_metal"] == 419


def test_kz_london_crypto_low_uses_survivor_firedays():
    mc = _read_json(MC_RESULT_PATH)
    assert mc["new_sleeve_firedays"]["kz_london_crypto_low"] == 627


def test_vss_fxcross_london_up_low_uses_survivor_firedays():
    mc = _read_json(MC_RESULT_PATH)
    assert mc["new_sleeve_firedays"]["vss_fxcross_london_up_low"] == 518


def test_unified_book_mc_result_matches_registry_confidence():
    mc = _read_json(MC_RESULT_PATH)
    assert mc["schema"] == "gtos.ultimate_mechanical_edge.unified_book_mc_result.v2"
    assert "NOT_LIVE_AUTHORITY" in mc["decision"]
    assert mc["conf"] == candidate_registry.CANDIDATE_CONFIDENCE
    assert mc["current_canonical"]["confidence"] == candidate_registry.CANDIDATE_CONFIDENCE
    assert set(mc["loo_sharpe"]) == set(candidate_registry.CANDIDATE_NAMES)
    assert mc["current_canonical_scenario"] == "registry_current_corrected"
    assert mc["unified_sharpe"] >= 0.26
    assert mc["best_next_rebuild"]["sharpe"] >= mc["unified_sharpe"]
    assert mc["current_canonical"]["confidence"] == mc["conf"]
    assert mc["source_audit"] == {
        "daily": (
            "research/operations/final_moonshot_principal_full_system_audit_2026_06_17/"
            "CORRECTED_CANDIDATE_DAILY_SERIES_AUDIT.json"
        ),
        "mc": (
            "research/operations/final_moonshot_principal_full_system_audit_2026_06_17/"
            "CORRECTED_UNIFIED_BOOK_MC_AUDIT.json"
        ),
    }
    # NOTE: this assertion pins a POINTER, not evidence -- see
    # test_the_cited_principal_audit_has_never_existed below.


def test_current_mechanical_route_has_no_retired_tokens():
    stale_token = "structural" + "_retest" + "_short"
    for rel in ("UNIFIED_BOOK_MC_RESULT.json",):
        text = (MECH_DIR / rel).read_text(encoding="utf-8")
        assert stale_token not in text
        assert '"vol_squeeze": 0.40' not in text
        assert '"vol_squeeze":0.40' not in text


PHANTOM_AUDIT_DIR = "research/operations/final_moonshot_principal_full_system_audit_2026_06_17"
PHANTOM_AUDIT_FILES = (
    "CORRECTED_UNIFIED_BOOK_MC_AUDIT.json",
    "CORRECTED_CANDIDATE_DAILY_SERIES_AUDIT.json",
    "CORRECTED_UNIFIED_BOOK_MC_VERIFY_RESULT.json",
)


def test_the_cited_principal_audit_has_never_existed():
    """Every confidence weight in the nine-sleeve candidate book cites a 2026-06-17
    principal audit as its provenance. Measured 2026-08-07 (wave-20 lane p4) over all
    9,004 commits reachable from every ref: `git log --all --diff-filter=A --name-only`
    records ZERO additions of any of these files and zero of ANY path under that
    directory. The weights may still be right; nothing in this repository can show where
    they came from.

    This test is deliberately an assertion of ABSENCE, which is the honest shape: it does
    not claim the weights are wrong. It fails the day someone recovers or fabricates the
    audit, and at that point the right move is to rebuild the derivation and delete it.
    Register: docs/audits/fable5-vision-audit-20260725/phase20/forward/SUPERSEDED_CLAIMS_V1.json
    """

    import subprocess

    for name in PHANTOM_AUDIT_FILES:
        assert not (REPO / PHANTOM_AUDIT_DIR / name).exists(), (
            f"{name} appeared on disk. If the principal audit has genuinely been recovered, "
            "rebuild the weight derivation, record it, and delete this assertion."
        )

    added = subprocess.run(
        ["git", "log", "--all", "--diff-filter=A", "--name-only", "--format=", "--", PHANTOM_AUDIT_DIR],
        cwd=REPO, capture_output=True, text=True, timeout=600,
    )
    if added.returncode == 0:
        paths = [ln for ln in added.stdout.splitlines() if ln.strip()]
        assert paths == [], (
            "history now contains the principal audit; reconstruct the weight derivation "
            f"from it and delete this assertion. Found: {paths[:5]}"
        )


def test_the_candidate_weights_size_nothing_that_is_armed():
    """The scope bound on the finding above. A phantom provenance on weights that size
    live money would be an emergency; on weights that size nothing it is a debt. Measured
    rather than assumed, against the single source of truth for arming."""

    from src.components.ultimate_book.sleeves import candidate_registry as CR
    from src.safety.armed_set import armed_sleeves

    overlap = armed_sleeves() & set(CR.CANDIDATE_CONFIDENCE)
    assert overlap == set(), (
        f"a candidate-book sleeve is ARMED: {sorted(overlap)}. Its confidence weight traces to "
        "an audit that has never existed in this repository (see the test above). Rebuild the "
        "derivation before this sleeve carries risk."
    )
