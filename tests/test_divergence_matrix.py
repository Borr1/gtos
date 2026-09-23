"""Behavioural tests for the replay-vs-live divergence matrix.

These are deliberately mutation-shaped.  A test that builds a matrix and asserts it
verifies proves only that the happy path runs; it would pass against a `verify_matrix`
that returned immediately.  So for every guard the generator claims, there is a test
that breaks exactly that property and asserts the specific error code.

Nothing here greps source.  `CLAUDE.md` §6 and the Wave-2 working agreement both note
that a source-string assertion passes against a wrong implementation, and this wave
already found one that did.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research_infra import divergence_matrix as dm


ROOT = Path(__file__).resolve().parents[1]

# The four sealed January arms live in the producing worktree and are read-only.
JANUARY_ARMS = {
    "S0R0": "PHASE_D_JANUARY_S0R0_R2_20260724T062502Z",
    "S1R0": "PHASE_D_JANUARY_S1R0_R1_20260724T103515Z",
    "S0R1": "PHASE_D_JANUARY_S0R1_R1_20260724T151015Z",
    "S1R1": "PHASE_D_JANUARY_S1R1_R1_20260724T195321Z",
}
SEALED_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/research/operations"
    "/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    "/attempt_5_typed_sparse"
)


def _synthetic_receipt(tmp_path: Path, *, arm_id: str = "S0R0") -> Path:
    """A minimal arm receipt.

    The generator only reads identity fields, so a synthetic receipt exercises exactly
    the same code path as a sealed one and keeps the suite runnable on a machine that
    has no sealed corpus.
    """

    core = {
        "schema": "gtos.b7_5.post_acceleration_arm_execution.v1",
        "status": "POST_ACCELERATION_ARM_EXECUTION_COMPLETE",
        "arm_id": arm_id,
        "window": {"start": "2026-01-01", "end": "2026-01-31"},
        "decision_contract_self_hash_sha256": "a" * 64,
        "execution_seal_root_sha256": "b" * 64,
        "arm_fingerprint_sha256": "c" * 64,
    }
    core["receipt_root_sha256"] = dm.stable_sha256(core)
    path = tmp_path / f"{arm_id}_B7_5_POST_ACCELERATION_ARM_RECEIPT.json"
    path.write_text(json.dumps(core, indent=2, sort_keys=True), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def receipt_and_matrix(tmp_path_factory) -> tuple[dict, dict]:
    tmp_path = tmp_path_factory.mktemp("divergence")
    receipt_path = _synthetic_receipt(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    matrix = dm.build_matrix(arm_receipt_path=receipt_path, root=ROOT)
    return receipt, matrix


# --------------------------------------------------------------------- happy path


def test_a_generated_matrix_verifies_against_its_own_arm(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix
    dm.verify_matrix(matrix, arm_receipt=receipt)


def test_the_matrix_is_bound_to_the_arm_it_was_generated_for(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix
    binding = matrix["arm_binding"]
    assert binding["arm_id"] == receipt["arm_id"]
    assert binding["window"] == receipt["window"]
    assert binding["receipt_root_sha256"] == receipt["receipt_root_sha256"]
    assert binding["arm_fingerprint_sha256"] == receipt["arm_fingerprint_sha256"]


def test_todays_verdict_is_that_replay_r_is_not_a_live_claim(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    assert matrix["transfer_verdict"] == dm.VERDICT_BLOCKED


def test_every_family_the_session_was_asked_to_cover_has_rows(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    by_family = matrix["rows_by_family"]
    # execution model (E1), strategy family (F1), clock (F7) are the three the plan
    # names; data and live_only were added by this session.
    assert by_family["execution_model"] > 0
    assert by_family["strategy_family"] > 0
    assert by_family["clock"] > 0


# --------------------------------------------------- the probe can see what it seeks


def test_the_config_diff_actually_finds_the_known_allocator_divergence(receipt_and_matrix):
    """Prove the probe works before trusting any zero it reports.

    The Scheduler V4 allocator is the single largest known replay-only surface.  If the
    config diff silently returned nothing — a broken import, an empty overlay — every
    other 'no divergence found' result in this matrix would be meaningless.
    """

    _, matrix = receipt_and_matrix
    allocator = [
        row
        for row in matrix["rows"]
        if row["row_id"].startswith("E1.PORTFOLIO_ALLOCATOR@")
    ]
    assert allocator, "the allocator row vanished — the config diff is not running"
    for row in allocator:
        assert row["config_key_counts"]["replay_only"] > 100
        assert row["direction"] in {"REPLAY_ONLY", "BOTH_DIFFERENT"}


def test_the_residual_row_is_always_present_even_when_empty(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    residual = [
        row
        for row in matrix["rows"]
        if row["row_id"].startswith("UNCLASSIFIED_CONFIG_DIVERGENCE")
    ]
    assert residual, "the residual row must exist so its absence is never read as clean"


def test_an_unclaimed_config_key_lands_in_the_residual_as_unknown():
    """The mechanism that stops this artifact decaying.

    A key no rule claims must surface, not vanish.  `_classify_key` is the whole
    decision, so drive it directly with a key nobody has ever written.
    """

    assert dm._classify_key("gtos_vnext_runtime.some_future_policy_nobody_wrote") is None
    assert dm._classify_key("a_top_level_section_added_next_month.value") is None
    # ...while keys that ARE claimed do not leak into the residual
    assert (
        dm._classify_key("gtos_vnext_runtime.scheduler_v4_best_trade_allocator_x")
        == "E1.PORTFOLIO_ALLOCATOR"
    )
    assert dm._classify_key("instruments.NAS100.market.spread") == "DATA.SYMBOL_MARKET_SPEC"


def test_a_residual_with_entries_forces_unknown_and_blocks_transfer():
    rows = [
        dm._row(
            row_id="UNCLASSIFIED_CONFIG_DIVERGENCE@x",
            family="execution_model",
            finding=None,
            dimension="residual",
            replay_value="1 key",
            replay_locator="residual",
            live_value="1 key",
            live_locator="residual",
            direction="UNKNOWN",
            transfer_risk="BLOCKS_TRANSFER",
            rule="config_surface_diff_residual",
            sources=[{"path": "config/agent_config.yaml", "sha256": "0" * 64, "locator": "x"}],
        )
    ]
    assert dm.compute_transfer_verdict(rows) == dm.VERDICT_BLOCKED


# ------------------------------------------------------------------- mutation tests


def _mutated(matrix: dict, mutate) -> dict:
    clone = copy.deepcopy(matrix)
    mutate(clone)
    return clone


def _reseal(matrix: dict) -> dict:
    core = {k: v for k, v in matrix.items() if k != "matrix_root_sha256"}
    return {**core, "matrix_root_sha256": dm.stable_sha256(core)}


def test_editing_the_matrix_without_resealing_is_caught(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        clone["transfer_verdict"] = dm.VERDICT_CLEAR

    with pytest.raises(dm.DivergenceMatrixError, match="root_mismatch"):
        dm.verify_matrix(_mutated(matrix, mutate), arm_receipt=receipt)


def test_a_forged_clean_verdict_is_caught_even_after_resealing(receipt_and_matrix):
    """The important one.

    Someone who wants a replay number to read as a live number will edit the verdict
    and recompute the hash.  The verdict is recomputed from the rows, so that fails.
    """

    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        clone["transfer_verdict"] = dm.VERDICT_CLEAR

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(dm.DivergenceMatrixError, match="verdict_mismatch"):
        dm.verify_matrix(forged, arm_receipt=receipt)


def test_deleting_the_residual_row_is_caught_even_after_resealing(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        clone["rows"] = [
            row
            for row in clone["rows"]
            if not str(row["row_id"]).startswith("UNCLASSIFIED_CONFIG_DIVERGENCE")
        ]

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(dm.DivergenceMatrixError, match="residual_row_missing"):
        dm.verify_matrix(forged, arm_receipt=receipt)


def test_deleting_every_blocking_row_still_cannot_produce_a_clean_verdict(
    receipt_and_matrix,
):
    """Removing rows does not launder the verdict — it trips the residual guard.

    And if the residual is kept, its own UNKNOWN keeps the verdict blocked.
    """

    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        clone["rows"] = [
            row
            for row in clone["rows"]
            if str(row["row_id"]).startswith("UNCLASSIFIED_CONFIG_DIVERGENCE")
            or row["transfer_risk"] != "BLOCKS_TRANSFER"
        ]
        clone["transfer_verdict"] = dm.compute_transfer_verdict(clone["rows"])

    forged = _reseal(_mutated(matrix, mutate))
    # It verifies structurally — the residual was kept, so no guard trips. But the
    # verdict it is forced to carry is still not clean, because the surviving rows
    # include the residual's own UNKNOWN and several unquantified declarations.
    dm.verify_matrix(forged, arm_receipt=receipt)
    assert forged["transfer_verdict"] != dm.VERDICT_CLEAR


def test_a_matrix_from_another_arm_is_rejected(tmp_path, receipt_and_matrix):
    _, matrix = receipt_and_matrix
    other = json.loads(
        _synthetic_receipt(tmp_path, arm_id="S1R1").read_text(encoding="utf-8")
    )
    with pytest.raises(dm.DivergenceMatrixError, match="arm_binding_mismatch:arm_id"):
        dm.verify_matrix(matrix, arm_receipt=other)


def test_a_matrix_whose_window_was_swapped_is_rejected(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix
    other = copy.deepcopy(receipt)
    other["window"] = {"start": "2026-04-01", "end": "2026-04-30"}
    with pytest.raises(dm.DivergenceMatrixError, match="arm_binding_mismatch:window"):
        dm.verify_matrix(matrix, arm_receipt=other)


def test_a_derived_row_with_an_unhashed_source_is_rejected(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        for row in clone["rows"]:
            if row["derivation"]["mode"] == "DERIVED":
                row["derivation"]["sources"][0]["sha256"] = None
                row["derivation"]["sources"][0].pop("present", None)
                break

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(dm.DivergenceMatrixError, match="source_unhashed"):
        dm.verify_matrix(forged, arm_receipt=receipt)


def test_a_declared_row_without_an_owner_is_rejected(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        for row in clone["rows"]:
            if row["derivation"]["mode"] == "DECLARED":
                row["derivation"]["owner"] = None
                break

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(dm.DivergenceMatrixError, match="declaration_unowned"):
        dm.verify_matrix(forged, arm_receipt=receipt)


def test_a_row_with_no_sources_at_all_is_rejected(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        clone["rows"][0]["derivation"]["sources"] = []

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(dm.DivergenceMatrixError, match="unsourced"):
        dm.verify_matrix(forged, arm_receipt=receipt)


def test_equivalent_without_both_locators_is_rejected(receipt_and_matrix):
    """Session D's rule: EQUIVALENT requires that nothing was unknown."""

    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        row = clone["rows"][0]
        row["direction"] = "EQUIVALENT"
        row["live_behavior"]["locator"] = None

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(
        dm.DivergenceMatrixError, match="equivalent_without_both_sides"
    ):
        dm.verify_matrix(forged, arm_receipt=receipt)


def test_the_row_builder_refuses_to_call_a_one_sided_row_equivalent():
    row = dm._row(
        row_id="X.Y",
        family="execution_model",
        finding=None,
        dimension="d",
        replay_value="v",
        replay_locator="a:1",
        live_value="v",
        live_locator=None,
        direction="EQUIVALENT",
        transfer_risk="INFORMATIONAL",
        rule="r",
        sources=[{"path": "p", "sha256": "0" * 64, "locator": "l"}],
    )
    assert row["direction"] == "UNKNOWN"


def test_a_row_with_no_derivation_mode_at_all_is_rejected(receipt_and_matrix):
    receipt, matrix = receipt_and_matrix

    def mutate(clone):
        clone["rows"][0]["derivation"]["mode"] = "SOMEHOW"

    forged = _reseal(_mutated(matrix, mutate))
    with pytest.raises(dm.DivergenceMatrixError, match="derivation_invalid"):
        dm.verify_matrix(forged, arm_receipt=receipt)


# -------------------------------------------------------------- Session E's row set


def test_an_absent_live_row_set_yields_one_loud_unknown_not_a_silent_pass(
    receipt_and_matrix,
):
    _, matrix = receipt_and_matrix
    live_rows = [row for row in matrix["rows"] if row["family"] == "live_only"]
    assert len(live_rows) == 1
    assert live_rows[0]["row_id"] == "LIVE_ONLY.ROW_SET_NOT_SUPPLIED"
    assert live_rows[0]["direction"] == "UNKNOWN"
    assert live_rows[0]["transfer_risk"] == "BLOCKS_TRANSFER"


def test_a_supplied_live_row_set_is_merged(tmp_path):
    receipt_path = _synthetic_receipt(tmp_path)
    rows_path = tmp_path / "live_rows.json"
    rows_path.write_text(
        json.dumps(
            {
                "schema": dm.LIVE_ROWS_SCHEMA,
                "rows": [
                    {
                        "row_id": "LIVE_ONLY.W7_FILL_SLIPPAGE",
                        "family": "live_only",
                        "finding": "OD-1",
                        "dimension": "Measured live fill slippage",
                        "replay_behavior": {"value": "flat constant", "locator": "x:1"},
                        "live_behavior": {"value": "measured", "locator": "y:2"},
                        "direction": "BOTH_DIFFERENT",
                        "transfer_risk": "BOUNDS_TRANSFER",
                        "quantification": {
                            "status": "QUANTIFIED",
                            "metric": "mean_slippage_r",
                            "value": 0.03,
                            "unit": "R",
                            "source": "w7",
                        },
                        "derivation": {
                            "mode": "DERIVED",
                            "rule": "w7_forensics",
                            "sources": [
                                {"path": "shadow_logs/slippage.jsonl", "sha256": "0" * 64,
                                 "locator": "rows"}
                            ],
                            "owner": None,
                            "declared_utc": None,
                            "justification": None,
                            "review_by": None,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    matrix = dm.build_matrix(
        arm_receipt_path=receipt_path, live_rows_path=rows_path, root=ROOT
    )
    ids = {row["row_id"] for row in matrix["rows"]}
    assert "LIVE_ONLY.W7_FILL_SLIPPAGE" in ids
    assert "LIVE_ONLY.ROW_SET_NOT_SUPPLIED" not in ids
    dm.verify_matrix(matrix, arm_receipt=json.loads(receipt_path.read_text()))


def test_a_live_row_set_smuggling_a_non_live_family_is_rejected(tmp_path):
    receipt_path = _synthetic_receipt(tmp_path)
    rows_path = tmp_path / "live_rows.json"
    rows_path.write_text(
        json.dumps(
            {
                "schema": dm.LIVE_ROWS_SCHEMA,
                "rows": [{"row_id": "X", "family": "execution_model"}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(dm.DivergenceMatrixError, match="live_divergence_row_family_invalid"):
        dm.build_matrix(
            arm_receipt_path=receipt_path, live_rows_path=rows_path, root=ROOT
        )


def test_a_live_row_set_with_the_wrong_schema_is_rejected(tmp_path):
    receipt_path = _synthetic_receipt(tmp_path)
    rows_path = tmp_path / "live_rows.json"
    rows_path.write_text(json.dumps({"schema": "something.else", "rows": []}), encoding="utf-8")
    with pytest.raises(dm.DivergenceMatrixError, match="live_divergence_rows_schema_invalid"):
        dm.build_matrix(
            arm_receipt_path=receipt_path, live_rows_path=rows_path, root=ROOT
        )


# ------------------------------------------------------- AST call-site census rows


def _reachability_rows(matrix: dict) -> dict[str, dict]:
    return {row["row_id"]: row for row in matrix["rows"] if "call_sites" in row}


def test_the_call_site_census_reproduces_r1s_zero_production_callers(receipt_and_matrix):
    """R1 asserted this in prose; here it is measured.

    'Selector V4 admission — no production caller; the only bridge
    (gtos_vnext_runtime.py) is itself uncalled.'  A one-hop census would count that
    bridge's own call and report a live caller, which is why the census is two-hop.
    """

    _, matrix = receipt_and_matrix
    row = _reachability_rows(matrix)["E1.SELECTOR_V4_CALL_SITES"]
    assert row["probe_validated"] is True
    assert row["call_sites"]["research"], "the replay callers vanished — probe is broken"
    assert row["call_sites"]["live_reachable"] == []
    # ...and the bridge call is still reported, as a dead one rather than omitted.
    dead = row["call_sites"]["live_inside_uncalled_functions"]
    assert any("gtos_vnext_runtime.py" in site for site in dead)
    assert row["direction"] == "REPLAY_ONLY"


def test_the_allocator_and_memory_guard_have_no_live_call_sites(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    rows = _reachability_rows(matrix)
    for row_id in ("E1.ALLOCATOR_CALL_SITES", "E1.REPLAY_MEMORY_GUARD_CALL_SITES"):
        row = rows[row_id]
        assert row["probe_validated"] is True, row_id
        assert row["call_sites"]["research"], row_id
        assert row["call_sites"]["live_reachable"] == [], row_id
        assert row["direction"] == "REPLAY_ONLY", row_id


def test_files_that_will_not_parse_are_reported_not_swallowed(receipt_and_matrix):
    """A probe that silently skips files reports a zero it has not earned.

    Twelve files in this tree carry UTF-8 BOMs that break ast.parse (F25).  The census
    must surface them so a reader can judge whether the census could have missed a
    call site.
    """

    _, matrix = receipt_and_matrix
    row = _reachability_rows(matrix)["E1.SELECTOR_V4_CALL_SITES"]
    assert isinstance(row["unparseable_files"], list)
    # Not asserting a count — that changes as files are fixed. Asserting the channel
    # exists and is populated from a real scan.
    assert all(name.endswith(".py") for name in row["unparseable_files"])


def test_a_census_that_finds_nothing_at_all_is_treated_as_a_broken_probe(tmp_path):
    """The fail-closed case: an empty result must not read as 'no divergence'."""

    empty_root = tmp_path / "empty"
    (empty_root / "src").mkdir(parents=True)
    rows = dm._derive_reachability_rows(root=empty_root)
    assert rows
    for row in rows:
        assert row["probe_validated"] is False
        assert row["direction"] == "UNKNOWN"
        assert row["quantification"]["status"] == "UNQUANTIFIED"
        assert row["transfer_risk"] == "BLOCKS_TRANSFER"


def test_the_census_states_what_it_measured(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    for row in _reachability_rows(matrix).values():
        assert "not full transitive reachability" in row["census_semantics"]


# ------------------------------------------------ Session E's W7 forensics manifest

W7_MANIFEST_PATH = (
    ROOT
    / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics"
    / "LIVE_TRADE_ROWS_MANIFEST.json"
)


def _synthetic_w7_manifest(tmp_path: Path) -> Path:
    path = tmp_path / "LIVE_TRADE_ROWS_MANIFEST.json"
    path.write_text(
        json.dumps(
            {
                "schema": "gtos.w7_live_forensics.manifest.v1",
                "n_rows_total": 300,
                "n_rows_w7": 175,
                "cross_broker_pairing": {
                    "risk_ratio_fn_over_ftmo": {"mean": 1.5015, "median": 1.3981, "n": 64},
                    "n_pairs_with_unequal_contract_size": 25,
                    "n_paired_signals": 64,
                    "n_ftmo_only": 33,
                    "n_redacted_account_only": 14,
                    "unpaired_ftmo_net": -398.85,
                    "unpaired_fn_net": -1377.72,
                },
                "live_books": {
                    "profile": "clean3_w7_ceiling_nom2p00",
                    "core8": ["a"] * 8,
                    "candidate_live": ["b"] * 9,
                    "market_expansion_live": ["c"] * 12,
                    "derisk_mode": "smooth",
                    "total_live_sleeves": 29,
                },
                "accounts": {
                    "ftmo": {"daily_reset_rule": "CE(S)T"},
                    "redacted_account": {"daily_reset_rule": "server_midnight"},
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_the_w7_manifest_reduces_to_quantified_live_only_rows(tmp_path):
    """E's row is one closed position; this matrix's row is one divergence dimension.

    So E's artifact is reduced, not merged, and the reduction must produce measured
    numbers rather than restating that live evidence exists.
    """

    receipt_path = _synthetic_receipt(tmp_path)
    matrix = dm.build_matrix(
        arm_receipt_path=receipt_path,
        w7_forensics_path=_synthetic_w7_manifest(tmp_path),
        root=ROOT,
    )
    live = {r["row_id"]: r for r in matrix["rows"] if r["family"] == "live_only"}
    assert "LIVE_ONLY.ROW_SET_NOT_SUPPLIED" not in live

    ratio = live["LIVE_ONLY.CROSS_ACCOUNT_RISK_RATIO"]
    assert ratio["quantification"]["status"] == "QUANTIFIED"
    assert ratio["quantification"]["value"] == 1.5015
    assert ratio["direction"] == "LIVE_ONLY"

    unpaired = live["LIVE_ONLY.UNPAIRED_SIGNALS"]
    assert unpaired["quantification"]["value"] == 47  # 33 + 14
    assert "111" in unpaired["live_behavior"]["value"]

    dm.verify_matrix(matrix, arm_receipt=json.loads(receipt_path.read_text()))


def test_a_w7_manifest_missing_expected_fields_yields_unknown_not_a_guess(tmp_path):
    receipt_path = _synthetic_receipt(tmp_path)
    manifest = tmp_path / "thin.json"
    manifest.write_text(
        json.dumps({"schema": "gtos.w7_live_forensics.manifest.v1"}), encoding="utf-8"
    )
    matrix = dm.build_matrix(
        arm_receipt_path=receipt_path, w7_forensics_path=manifest, root=ROOT
    )
    live = [r for r in matrix["rows"] if r["family"] == "live_only"]
    assert live
    assert all(r["direction"] == "UNKNOWN" for r in live)
    assert all(r["quantification"]["status"] == "UNQUANTIFIED" for r in live)
    assert matrix["transfer_verdict"] == dm.VERDICT_BLOCKED


def test_a_w7_manifest_with_an_unrecognised_schema_is_not_read(tmp_path):
    receipt_path = _synthetic_receipt(tmp_path)
    manifest = tmp_path / "wrong.json"
    manifest.write_text(
        json.dumps({"schema": "something.else.v9", "n_rows_w7": 175}), encoding="utf-8"
    )
    matrix = dm.build_matrix(
        arm_receipt_path=receipt_path, w7_forensics_path=manifest, root=ROOT
    )
    ids = {r["row_id"] for r in matrix["rows"]}
    assert "LIVE_ONLY.W7_MANIFEST_UNRECOGNISED" in ids
    assert "LIVE_ONLY.CROSS_ACCOUNT_RISK_RATIO" not in ids


def test_the_real_w7_manifest_reduces_once_session_e_merges(tmp_path):
    """Runs for real as soon as Session E's artifact lands on this branch."""

    if not W7_MANIFEST_PATH.is_file():
        pytest.skip("Session E's W7 forensics manifest is not on this branch yet")
    receipt_path = _synthetic_receipt(tmp_path)
    matrix = dm.build_matrix(
        arm_receipt_path=receipt_path, w7_forensics_path=W7_MANIFEST_PATH, root=ROOT
    )
    live = [r for r in matrix["rows"] if r["family"] == "live_only"]
    assert live and all(r["row_id"] != "LIVE_ONLY.ROW_SET_NOT_SUPPLIED" for r in live)
    dm.verify_matrix(matrix, arm_receipt=json.loads(receipt_path.read_text()))


# ------------------------------------------------------------- declared-row honesty


def test_declared_and_derived_rows_are_never_confusable(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    for row in matrix["rows"]:
        derivation = row["derivation"]
        if derivation["mode"] == "DECLARED":
            assert derivation["owner"], row["row_id"]
            assert derivation["declared_utc"], row["row_id"]
            assert derivation["justification"], row["row_id"]
        else:
            assert derivation["owner"] is None, row["row_id"]
            assert derivation["declared_utc"] is None, row["row_id"]


def test_a_declaration_whose_justifying_document_vanished_becomes_unknown(tmp_path):
    """A DECLARED row is only as good as the document behind it.

    Point the generator at a repo root where the audit documents do not exist; every
    declared row must degrade to UNKNOWN rather than keep asserting a fact whose source
    is gone.
    """

    # Build a skeleton root with the config/code the derived rules need, but none of
    # the audit markdown the declarations cite.
    fake_root = tmp_path / "fakerepo"
    fake_root.mkdir()
    rows = dm._declared_rows(root=fake_root)
    assert rows, "declared rows disappeared entirely"
    assert all(row["direction"] == "UNKNOWN" for row in rows)
    assert all(row["quantification"]["status"] == "UNQUANTIFIED" for row in rows)


def test_the_markdown_rendering_marks_declared_rows_visibly(receipt_and_matrix):
    _, matrix = receipt_and_matrix
    text = dm.render_markdown(matrix)
    assert "[DECLARED]" in text
    assert matrix["transfer_verdict"] in text
    assert matrix["matrix_root_sha256"] in text


# ------------------------------------------------------------------- sealed corpus


@pytest.mark.parametrize("arm_id", sorted(JANUARY_ARMS))
def test_the_matrix_generates_for_each_sealed_january_arm(arm_id):
    receipt_path = (
        SEALED_ROOT / JANUARY_ARMS[arm_id] / "B7_5_POST_ACCELERATION_ARM_RECEIPT.json"
    )
    if not receipt_path.is_file():
        pytest.skip("sealed January corpus not present in this checkout")
    matrix = dm.build_matrix(arm_receipt_path=receipt_path, root=ROOT)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    dm.verify_matrix(matrix, arm_receipt=receipt)
    assert matrix["arm_binding"]["arm_id"] == arm_id
    assert matrix["transfer_verdict"] == dm.VERDICT_BLOCKED
