"""Behavioural tests for the Phase-2 differential harness.

The failure mode this harness exists to prevent is a comparator that reports
equivalence it has not established, so most of these tests are *discrimination*
tests: hand it something known-different and check it says so, at the right
field.  A test that only proved "identical inputs compare equal" would pass
against a comparator that always returns EQUIVALENT.

The synthetic fixtures run everywhere.  Two tests additionally exercise the real
sealed January arms and skip when that machine-local evidence is absent -- they
are marked and named so a skip is visible rather than silent.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research_infra import (
    replay_acceleration_task2_semantic_acceptance as task2,
)
from src.research_infra.replay_differential_harness import (
    CLASSIFICATION_ALLOWLISTED_CLOCK,
    CLASSIFICATION_ALLOWLISTED_HASH,
    CLASSIFICATION_UNKNOWN,
    VERDICT_DIFFER,
    VERDICT_EQUIVALENT,
    VERDICT_INCOMPLETE,
    ArmOutputs,
    DifferentialHarnessError,
    compare_arms,
)

PREFIX = "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_S0R0_SYNTHETIC"
HASH_A = "a" * 64
HASH_B = "b" * 64

SEALED_ARM_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/research/"
    "operations/final_moonshot_ultimate_system_denominator_to_deployment_"
    "execution_2026_06_20/attempt_5_typed_sparse"
)
SEALED_S0R0 = SEALED_ARM_ROOT / "PHASE_D_JANUARY_S0R0_R2_20260724T062502Z"
SEALED_S1R0 = SEALED_ARM_ROOT / "PHASE_D_JANUARY_S1R0_R1_20260724T103515Z"

requires_sealed_arms = pytest.mark.skipif(
    not (SEALED_S0R0.is_dir() and SEALED_S1R0.is_dir()),
    reason="machine-local sealed January arms are not present in this checkout",
)


def seal_order_row(row: dict) -> dict:
    """Recompute every declared runtime hash from its own preimage.

    ``task2._validate_runtime_hash_preimages`` (``task2:862-902``) runs on both
    rows before any comparison, so a fixture carrying a made-up hash is rejected
    outright -- correctly. An adversarial pass found the first version of these
    fixtures using ``"a"*64``, which is the hash of nothing, and asserting
    EQUIVALENT on it; that made the tests agree with a comparator that never
    checked a preimage. Sealing here is what makes them mean anything.
    """

    packet = row.get("broker_order_lifecycle_capture_v4_packet")
    if isinstance(packet, dict):
        material = {
            key: value
            for key, value in packet.items()
            if key not in {"generated_at_utc", "packet_hash_sha256"}
        }
        packet["packet_hash_sha256"] = task2.producer_sha256(material)
    risk = row.get("risk_authority")
    if isinstance(risk, dict):
        headroom = risk.get("prop_firm_headroom")
        if isinstance(headroom, dict):
            snapshot = headroom["simulated_headroom"]
            snapshot.pop("snapshot_hash_sha256", None)
            snapshot["snapshot_hash_sha256"] = task2.producer_sha256(dict(snapshot))
            # task2:887-890 requires the evaluation snapshot to be canonically
            # identical to the simulated one.
            headroom["prop_firm_headroom_v4_evaluation"] = {
                "captured_at_utc": headroom.get(
                    "prop_firm_headroom_v4_evaluation", {}
                ).get("captured_at_utc", "2026-01-02T07:15:02+00:00"),
                "snapshot": copy.deepcopy(snapshot),
            }
        material = copy.deepcopy(risk)
        material["packet_hash_sha256"] = ""
        risk["packet_hash_sha256"] = task2.producer_sha256(material)
        row["risk_authority_packet_hash_sha256"] = risk["packet_hash_sha256"]
    return row


def _order_row(index: int) -> dict:
    """One structurally plausible order row, small but with the real shapes."""

    key = f"broadorigin_{index:024x}@@2026-01-02T07:15:00+00:00"
    return seal_order_row(
        {
            "canonical_replay_candidate_instance_key": key,
            "candidate_id": f"broadorigin_{index:024x}",
            "candidate_instance_time_utc": "2026-01-02T07:15:00+00:00",
            "order_event_stage": "accepted_pending",
            "trading_day": "2026-01-02",
            "asof_utc": "2026-01-02T07:15:00+00:00",
            "symbol": "XAUUSD",
            "approved_risk_pct": 0.4,
            "candidate_ev_r": 1.25,
            "broker_order_lifecycle_capture_v4_packet": {
                "schema_version": "broker_order_lifecycle_capture_v4_packet_v1",
                "generated_at_utc": "2026-01-02T07:15:01+00:00",
                "pre_order_capture_contract": {
                    "execution_manager_packet_hash": HASH_A,
                },
            },
            "candidate_packet_sidecar_hash_sha256": HASH_A,
            "packet_sidecar_hash_sha256": HASH_A,
            "risk_authority": {
                "prop_firm_headroom": {
                    "simulated_headroom": {
                        "captured_at_utc": "2026-01-02T07:15:02+00:00",
                        "equity_floor_cash": 9000.0,
                    },
                },
            },
        }
    )


def _bucket_row(day: str) -> dict:
    """``bucket`` is one of ``task2.EXACT_ROLES`` -- no allowlist applies."""

    return {
        "trading_day": day,
        "chunk_id": f"synthetic:development:{day}:{day}",
        "chunk_start_day": day,
        "chunk_end_day": day,
        "simulated_orders": 3,
        "risk_authority_packet_hash_sha256": HASH_A,
    }


def _write_arm(root: Path, *, orders=None, buckets=None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if orders is not None:
        path = root / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in orders),
            encoding="utf-8",
        )
    if buckets is not None:
        path = root / f"{PREFIX}_{task2.ROLE_SUFFIXES['bucket']}"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in buckets),
            encoding="utf-8",
        )
    return root


@pytest.fixture
def arm_pair(tmp_path):
    """Two byte-identical synthetic arms; mutate the right one per test."""

    orders = [_order_row(i) for i in range(4)]
    buckets = [_bucket_row("2026-01-02"), _bucket_row("2026-01-03")]
    left = _write_arm(tmp_path / "left", orders=orders, buckets=buckets)
    right = _write_arm(
        tmp_path / "right",
        orders=copy.deepcopy(orders),
        buckets=copy.deepcopy(buckets),
    )
    return left, right


def _mutate_order(root: Path, index: int, mutate, *, reseal: bool = True) -> None:
    """Mutate one order row.

    ``reseal`` recomputes the runtime hashes afterwards, which is what a real
    engine would do. Pass ``reseal=False`` to produce a row whose declared hash
    contradicts its own preimage -- the defect class a rebuilt engine is most
    likely to introduce, and the one the harness must not wave through.
    """

    path = root / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    mutate(rows[index])
    if reseal:
        seal_order_row(rows[index])
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _fields(report, role):
    return {d["field_path"] for d in report["roles"][role]["differences"]}


def _classified(report, role, classification):
    return {
        d["field_path"]
        for d in report["roles"][role]["differences"]
        if d["classification"] == classification
    }


# --------------------------------------------------------------------------
# It does not cry wolf.
# --------------------------------------------------------------------------


def test_identical_arms_compare_equivalent(arm_pair):
    left, right = arm_pair
    report = compare_arms(left, right, roles=["order", "bucket"])
    assert report["verdict"] == VERDICT_EQUIVALENT
    assert report["totals"]["unknown_difference_count"] == 0
    assert report["roles"]["order"]["left_row_count"] == 4
    assert report["roles"]["bucket"]["status"] == VERDICT_EQUIVALENT


def test_an_allowlisted_clock_difference_does_not_break_equivalence(arm_pair):
    left, right = arm_pair
    _mutate_order(
        right,
        1,
        lambda row: row["broker_order_lifecycle_capture_v4_packet"].__setitem__(
            "generated_at_utc", "2026-01-02T08:30:00+00:00"
        ),
    )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_EQUIVALENT
    assert _classified(
        report, "order", CLASSIFICATION_ALLOWLISTED_CLOCK
    ) == {"broker_order_lifecycle_capture_v4_packet/generated_at_utc"}


def test_a_clock_change_may_cascade_into_hashes_and_stay_equivalent(arm_pair):
    """The genuinely benign case: an allowlisted clock moves, and the hashes
    computed over it legitimately move with it, both sides self-consistent."""

    left, right = arm_pair
    _mutate_order(
        right,
        2,
        lambda row: row["risk_authority"]["prop_firm_headroom"][
            "simulated_headroom"
        ].__setitem__("captured_at_utc", "2026-01-02T09:45:00+00:00"),
    )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_EQUIVALENT
    benign = _classified(report, "order", CLASSIFICATION_ALLOWLISTED_HASH)
    assert "risk_authority/packet_hash_sha256" in benign
    assert (
        "risk_authority/prop_firm_headroom/simulated_headroom/snapshot_hash_sha256"
        in benign
    )
    assert _classified(report, "order", CLASSIFICATION_ALLOWLISTED_CLOCK)


def test_a_hash_that_contradicts_its_own_preimage_is_unknown(arm_pair):
    """The defect a rebuilt engine is most likely to introduce.

    ``task2.compare_role_rows`` catches this via
    ``_validate_runtime_hash_preimages`` (``task2:951-952``). An earlier version
    of this harness classified the same row ``ALLOWLISTED_DERIVED_HASH_PROVEN``
    on a pattern-string match, reporting ``PREIMAGE`` for a hash that provably
    was not one. This test is the regression pin for that.
    """

    left, right = arm_pair
    _mutate_order(
        right,
        1,
        lambda row: row["risk_authority"].__setitem__(
            "packet_hash_sha256", HASH_B
        ),
        reseal=False,
    )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER
    reasons = {d["reason"] for d in report["roles"]["order"]["differences"]}
    assert any(r.startswith("row_preimage_invalid:right:") for r in reasons)
    assert report["roles"]["order"]["unknown_difference_count"] >= 1


def test_the_risk_authority_alias_shortcut_requires_the_packet_on_both_sides(tmp_path):
    """``task2:990-991`` only takes the alias shortcut when a Mapping is
    actually present at ``risk_authority`` on both sides."""

    from src.research_infra.replay_differential_harness import classify_difference

    bare_left = {"risk_authority_packet_hash_sha256": HASH_A}
    bare_right = {"risk_authority_packet_hash_sha256": HASH_B}
    classification, reason = classify_difference(
        "order",
        ("risk_authority_packet_hash_sha256",),
        HASH_A,
        HASH_B,
        left_row=bare_left,
        right_row=bare_right,
    )
    assert classification == CLASSIFICATION_UNKNOWN
    assert reason.startswith("derived_hash_closure_unproven:")


# --------------------------------------------------------------------------
# It finds what is actually there, at the right field.
# --------------------------------------------------------------------------


def test_a_single_economic_field_change_is_located_by_row_and_field(arm_pair):
    left, right = arm_pair
    _mutate_order(right, 2, lambda row: row.__setitem__("approved_risk_pct", 0.8))
    report = compare_arms(left, right, roles=["order"])

    assert report["verdict"] == VERDICT_DIFFER
    assert _fields(report, "order") == {"approved_risk_pct"}
    (difference,) = report["roles"]["order"]["differences"]
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"] == "no_allowlist_entry"
    assert difference["left_row_index"] == 2
    assert difference["right_row_index"] == 2
    assert report["roles"]["order"]["rows_with_differences"] == 1
    # The value itself is a digest unless disclosure was asked for.
    assert "left_value" not in difference
    assert report["economic_values_exposed"] is False


def test_a_nested_economic_field_change_reports_its_full_path(arm_pair):
    """The economic leaf is named, and the hashes it feeds move with it.

    Resealing makes the mutated row internally consistent, which is what a real
    engine would produce, so the snapshot and packet hashes legitimately change
    too. Those are allowlisted and proven; the economic leaf is not.
    """

    left, right = arm_pair
    _mutate_order(
        right,
        0,
        lambda row: row["risk_authority"]["prop_firm_headroom"][
            "simulated_headroom"
        ].__setitem__("equity_floor_cash", 1234.5),
    )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER

    leaf = "risk_authority/prop_firm_headroom/simulated_headroom/equity_floor_cash"
    (difference,) = _find(report, "order", leaf)
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"] == "no_allowlist_entry"

    # Every other reported path is a hash computed over that leaf.
    unknown = {
        d["field_path"]
        for d in report["roles"]["order"]["differences"]
        if d["classification"] == CLASSIFICATION_UNKNOWN
    }
    assert unknown == {
        leaf,
        "risk_authority/prop_firm_headroom/prop_firm_headroom_v4_evaluation"
        "/snapshot/equity_floor_cash",
    }


def test_expose_values_returns_both_sides_and_says_so(arm_pair):
    left, right = arm_pair
    _mutate_order(right, 1, lambda row: row.__setitem__("candidate_ev_r", 9.5))
    report = compare_arms(left, right, roles=["order"], expose_values=True)
    (difference,) = report["roles"]["order"]["differences"]
    assert difference["left_value"] == 1.25
    assert difference["right_value"] == 9.5
    assert report["economic_values_exposed"] is True


# --------------------------------------------------------------------------
# You cannot smuggle a real change through an allowlisted slot.
# --------------------------------------------------------------------------


def _find(report, role, field_path):
    return [
        d
        for d in report["roles"][role]["differences"]
        if d["field_path"] == field_path
    ]


def test_an_allowlisted_clock_slot_holding_a_non_timestamp_is_unknown(arm_pair):
    left, right = arm_pair
    _mutate_order(
        right,
        0,
        lambda row: row["broker_order_lifecycle_capture_v4_packet"].__setitem__(
            "generated_at_utc", 4321.0
        ),
    )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER
    (difference,) = _find(
        report, "order", "broker_order_lifecycle_capture_v4_packet/generated_at_utc"
    )
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"] == "volatile_timestamp_invalid"


def test_an_allowlisted_hash_slot_holding_a_non_hash_is_unknown(arm_pair):
    left, right = arm_pair
    _mutate_order(
        right,
        0,
        lambda row: row["risk_authority"].__setitem__(
            "packet_hash_sha256", {"net_r": 3.5}
        ),
        reseal=False,
    )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER
    (difference,) = _find(report, "order", "risk_authority/packet_hash_sha256")
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"] == "derived_hash_invalid"


def test_an_allowlisted_hash_without_a_proven_closure_is_unknown(arm_pair):
    """``candidate_packet_sidecar_hash_sha256`` is allowlisted but not
    self-proving, so it stays UNKNOWN until a proof class is supplied.

    Both sidecar aliases move together: ``task2:899-902`` rejects a row where
    they disagree, so changing one alone would test the preimage guard instead.
    """

    left, right = arm_pair

    def _both(row):
        row["candidate_packet_sidecar_hash_sha256"] = HASH_B
        row["packet_sidecar_hash_sha256"] = HASH_B

    _mutate_order(right, 0, _both)
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER
    (difference,) = _find(report, "order", "candidate_packet_sidecar_hash_sha256")
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"].startswith("derived_hash_closure_unproven:")

    proven = compare_arms(
        left,
        right,
        roles=["order"],
        derived_hash_proofs={
            "candidate_packet_sidecar_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL",
            "packet_sidecar_hash_sha256": "HISTORICAL_HASH_ONLY_NONCAUSAL",
        },
    )
    assert proven["verdict"] == VERDICT_EQUIVALENT
    # An EQUIVALENT that depended on a supplied proof map says so.
    assert proven["derived_hash_proofs_root_sha256"] is not None


def test_a_mapping_proof_class_is_resolved_rather_than_raising(arm_pair):
    """``task2:999-1012`` allows a proof value keyed by row identity. Testing
    such a value for set membership raises ``TypeError``; it must be resolved."""

    from src.research_infra.replay_differential_harness import classify_difference

    row = _order_row(0)
    identity = row["canonical_replay_candidate_instance_key"]
    classification, reason = classify_difference(
        "order",
        ("candidate_packet_sidecar_hash_sha256",),
        HASH_A,
        HASH_B,
        left_row=row,
        right_row=row,
        derived_hash_proofs={
            "candidate_packet_sidecar_hash_sha256": {identity: "IDENTITY_ALIAS"}
        },
    )
    assert classification == CLASSIFICATION_ALLOWLISTED_HASH
    assert reason.startswith("IDENTITY_ALIAS:")


def test_exact_roles_admit_no_normalization_at_all(arm_pair):
    """``bucket`` is an exact role.  A path that *is* allowlisted for ``order``
    must still be UNKNOWN here -- mirrors ``task2:958-959``."""

    left, right = arm_pair
    path = right / f"{PREFIX}_{task2.ROLE_SUFFIXES['bucket']}"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rows[0]["risk_authority_packet_hash_sha256"] = HASH_B
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report = compare_arms(left, right, roles=["bucket"])
    assert report["verdict"] == VERDICT_DIFFER
    (difference,) = report["roles"]["bucket"]["differences"]
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"] == "exact_role_admits_no_normalization"


# --------------------------------------------------------------------------
# Row-set differences.
# --------------------------------------------------------------------------


def test_positional_alignment_reports_a_row_count_mismatch(arm_pair):
    left, right = arm_pair
    path = right / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_order_row(99), sort_keys=True) + "\n")
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER
    assert report["roles"]["order"]["row_count_mismatch"] is True
    assert report["roles"]["order"]["left_row_count"] == 4
    assert report["roles"]["order"]["right_row_count"] == 5


def test_identity_alignment_names_the_unmatched_rows(arm_pair):
    left, right = arm_pair
    path = right / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_order_row(99), sort_keys=True) + "\n")
    report = compare_arms(left, right, roles=["order"], alignment="identity")
    assert report["verdict"] == VERDICT_DIFFER
    detail = report["roles"]["order"]
    assert detail["left_only_row_count"] == 0
    assert detail["right_only_row_count"] == 1
    assert detail["matched_row_count"] == 4
    assert detail["right_only_keys"][0].startswith("broadorigin_")


def test_identity_alignment_refuses_a_non_unique_key(arm_pair):
    left, right = arm_pair
    report = compare_arms(
        left,
        right,
        roles=["order"],
        alignment="identity",
        identity_keys={"order": ("symbol",)},
    )
    # All four rows share one symbol, so the declared key is not an identity.
    assert report["verdict"] == VERDICT_INCOMPLETE
    assert report["roles"]["order"]["status"] == "UNAVAILABLE"
    assert "identity_key_not_unique" in report["roles"]["order"]["reason"]


def test_identity_alignment_will_not_invent_a_key_for_an_undeclared_role(arm_pair):
    left, right = arm_pair
    report = compare_arms(left, right, roles=["bucket"], alignment="identity")
    assert report["verdict"] == VERDICT_INCOMPLETE
    assert report["roles"]["bucket"]["reason"] == "identity_key_undeclared"


# --------------------------------------------------------------------------
# It never claims equivalence it has not established.
# --------------------------------------------------------------------------


def test_an_unreadable_role_makes_the_run_incomplete_not_equivalent(arm_pair):
    left, right = arm_pair
    report = compare_arms(left, right, roles=["order", "trade"])
    assert report["roles"]["order"]["status"] == VERDICT_EQUIVALENT
    assert report["roles"]["trade"]["status"] == "UNAVAILABLE"
    # The readable role passed, and the run still refuses to say EQUIVALENT.
    assert report["verdict"] == VERDICT_INCOMPLETE


def test_comparing_zero_roles_is_incomplete_not_equivalent(arm_pair):
    left, right = arm_pair
    report = compare_arms(left, right, roles=["trade", "oracle"])
    assert report["roles_compared"] == []
    assert report["verdict"] == VERDICT_INCOMPLETE


def test_the_cli_exits_nonzero_unless_equivalence_was_established(arm_pair, capsys):
    from src.research_infra.replay_differential_harness import main

    left, right = arm_pair
    assert main(["--left", str(left), "--right", str(right), "--role", "order"]) == 0
    _mutate_order(right, 0, lambda row: row.__setitem__("approved_risk_pct", 0.9))
    assert main(["--left", str(left), "--right", str(right), "--role", "order"]) == 1
    # An INCOMPLETE run is also a non-zero exit -- it is not an equivalence claim.
    assert main(["--left", str(left), "--right", str(right), "--role", "trade"]) == 1


def test_default_role_selection_is_the_intersection_of_both_arms(arm_pair):
    left, right = arm_pair
    (right / f"{PREFIX}_{task2.ROLE_SUFFIXES['bucket']}").unlink()
    report = compare_arms(left, right)
    assert report["roles_requested"] == ["order"]
    assert report["verdict"] == VERDICT_EQUIVALENT


# --------------------------------------------------------------------------
# Arm resolution -- the H4 property.
# --------------------------------------------------------------------------


def test_an_arm_outside_this_worktree_is_readable(arm_pair):
    """The comparator must not inherit the sealed runner's path binding.

    ``tmp_path`` is outside the repo, so a harness that validated arm paths
    against its own root -- as ``task2._require_regular_no_symlink_components``
    does at ``task2:2293-2309`` -- would reject these fixtures outright.
    """

    left, _ = arm_pair
    assert Path("/private/tmp") in left.parents or "/tmp" in str(left) or True
    arm = ArmOutputs(left)
    assert arm.prefix == PREFIX
    assert arm.arm_id == "S0R0"
    assert arm.root.is_absolute()
    assert not str(arm.root).startswith(str(Path(__file__).resolve().parents[1]))


def test_an_ambiguous_arm_directory_is_refused(tmp_path):
    root = tmp_path / "ambiguous"
    root.mkdir()
    for prefix in ("PREFIX_ONE", "PREFIX_TWO"):
        (root / f"{prefix}_{task2.ROLE_SUFFIXES['order']}").write_text(
            "", encoding="utf-8"
        )
    with pytest.raises(DifferentialHarnessError, match="arm_ledger_prefix_ambiguous"):
        ArmOutputs(root)


def test_an_arm_directory_with_no_ledgers_is_refused(tmp_path):
    root = tmp_path / "empty"
    root.mkdir()
    with pytest.raises(DifferentialHarnessError, match="arm_ledger_prefix_absent"):
        ArmOutputs(root)


# --------------------------------------------------------------------------
# Regression pins from the adversarial pass. Each of these was a false green,
# a crash, or a misreported total before it was fixed.
# --------------------------------------------------------------------------


def test_zero_rows_on_both_sides_is_not_equivalence(arm_pair):
    """"Compared nothing" one level below the zero-roles guard."""

    left, right = arm_pair
    for root in (left, right):
        (root / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}").write_text(
            "", encoding="utf-8"
        )
    report = compare_arms(left, right, roles=["order"])
    assert report["roles"]["order"]["status"] == "UNAVAILABLE"
    assert report["roles"]["order"]["reason"] == "no_rows_compared"
    assert report["verdict"] == VERDICT_INCOMPLETE


def test_a_zero_byte_archive_role_is_a_demotion_marker_not_an_empty_ledger(arm_pair):
    """``task2:2397`` routes a zero-byte flat ledger for an archive role to the
    streaming-proof archive. Reading the empty file instead would call the
    largest surfaces equivalent without comparing a row."""

    left, right = arm_pair
    for root in (left, right):
        (root / f"{PREFIX}_{task2.ROLE_SUFFIXES['decision']}").write_text(
            "", encoding="utf-8"
        )
    assert ArmOutputs(left).storage_mode("decision") == "archive_stub"
    report = compare_arms(left, right, roles=["decision"])
    assert report["roles"]["decision"]["status"] == "UNAVAILABLE"
    assert "archive_stub" in report["roles"]["decision"]["reason"]
    assert report["verdict"] == VERDICT_INCOMPLETE


def test_counts_are_totals_and_unknowns_survive_truncation(arm_pair):
    """With a small cap, the benign differences must not crowd out the real one,
    and the reported counts must be totals rather than "however many fit"."""

    left, right = arm_pair
    # Every row gets a benign clock move; one also gets an economic change.
    for index in range(4):
        _mutate_order(
            right,
            index,
            lambda row: row["broker_order_lifecycle_capture_v4_packet"].__setitem__(
                "generated_at_utc", "2026-01-02T08:30:00+00:00"
            ),
        )
    _mutate_order(right, 3, lambda row: row.__setitem__("approved_risk_pct", 0.9))

    report = compare_arms(left, right, roles=["order"], max_differences_per_role=2)
    detail = report["roles"]["order"]
    assert report["verdict"] == VERDICT_DIFFER
    assert detail["differences_truncated"] is True
    assert detail["max_differences_per_role"] == 2
    assert report["limits"]["max_differences_per_role"] == 2
    # The economic change is retained despite the cap being filled by clocks.
    assert _find(report, "order", "approved_risk_pct")
    # Counts are totals, not the size of the retained list.
    assert detail["allowlisted_difference_count"] > len(detail["differences"])
    assert detail["unknown_difference_count"] == 1


def test_truncation_alone_blocks_equivalence(arm_pair):
    left, right = arm_pair
    _mutate_order(
        right,
        0,
        lambda row: row["broker_order_lifecycle_capture_v4_packet"].__setitem__(
            "generated_at_utc", "2026-01-02T08:30:00+00:00"
        ),
    )
    report = compare_arms(left, right, roles=["order"], max_differences_per_role=0)
    assert report["roles"]["order"]["unknown_difference_count"] == 0
    assert report["roles"]["order"]["differences_truncated"] is True
    assert report["verdict"] == VERDICT_DIFFER


def test_a_proven_difference_outranks_an_unreadable_role(arm_pair):
    """Saying "could not establish" when a difference HAS been established
    understates it; a gate reading only the verdict would be misled."""

    left, right = arm_pair
    _mutate_order(right, 0, lambda row: row.__setitem__("approved_risk_pct", 0.9))
    report = compare_arms(left, right, roles=["order", "trade"])
    assert report["roles"]["order"]["status"] == VERDICT_DIFFER
    assert report["roles"]["trade"]["status"] == "UNAVAILABLE"
    assert report["verdict"] == VERDICT_DIFFER


def test_two_nans_are_never_silently_equal(arm_pair):
    """Under the pre-``e5c7ce30a`` encoder ``b"NaN" == b"NaN"``, so two runs that
    both produced an undefined economic value compared equal."""

    left, right = arm_pair
    for root in (left, right):
        path = root / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
        rows[0]["candidate_ev_r"] = float("nan")
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_DIFFER
    (difference,) = _find(report, "order", "candidate_ev_r")
    assert difference["classification"] == CLASSIFICATION_UNKNOWN
    assert difference["reason"] == "non_finite_undefined_value"


def test_infinity_is_a_comparable_value_not_a_crash(arm_pair):
    """``scorecard`` carries ``Infinity`` as a "no ceiling" sentinel in 26 of the
    first 40 rows of every sealed arm. Refusing to canonicalise it produced no
    report at all."""

    left, right = arm_pair
    for root in (left, right):
        path = root / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line]
        rows[0]["configured_scalar_max_expected_cost_r"] = float("inf")
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
    report = compare_arms(left, right, roles=["order"])
    assert report["verdict"] == VERDICT_EQUIVALENT
    assert report["roles"]["order"]["non_finite_leaf_count"] == 2

    # …but +inf against a finite value is still a difference.
    path = right / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rows[0]["configured_scalar_max_expected_cost_r"] = 12.0
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    changed = compare_arms(left, right, roles=["order"])
    assert changed["verdict"] == VERDICT_DIFFER
    assert _find(changed, "order", "configured_scalar_max_expected_cost_r")


def test_identity_and_positional_agree_on_an_allowlisted_only_difference(arm_pair):
    """Deciding equivalence from row digests alone would make identity
    alignment unable to certify the case it exists for -- two real runs always
    differ in wall-clock."""

    left, right = arm_pair
    _mutate_order(
        right,
        1,
        lambda row: row["broker_order_lifecycle_capture_v4_packet"].__setitem__(
            "generated_at_utc", "2026-01-02T08:30:00+00:00"
        ),
    )
    positional = compare_arms(left, right, roles=["order"])
    identity = compare_arms(left, right, roles=["order"], alignment="identity")
    assert positional["verdict"] == VERDICT_EQUIVALENT
    assert identity["verdict"] == VERDICT_EQUIVALENT
    assert identity["roles"]["order"]["rows_changed_by_digest"] == 1


def test_identity_bounds_the_rows_it_materialises(arm_pair):
    """Pass two holds at most ``max_detailed_rows`` rows. Unbounded, the
    ``missed`` surface (154,299 rows, 7.6 GB logical) would exceed this machine."""

    left, right = arm_pair
    for index in range(4):
        _mutate_order(
            right, index, lambda row: row.__setitem__("approved_risk_pct", 0.9)
        )
    report = compare_arms(
        left, right, roles=["order"], alignment="identity", max_detailed_rows=1
    )
    detail = report["roles"]["order"]
    assert detail["rows_changed_by_digest"] == 4
    assert detail["rows_with_differences"] == 1
    assert detail["rows_changed_not_detailed"] == 3
    assert detail["max_detailed_rows"] == 1
    # Undetailed changed rows must block equivalence.
    assert report["verdict"] == VERDICT_DIFFER


def test_an_unexpected_exception_becomes_unavailable_not_a_dead_run(arm_pair):
    """A role must not be able to abandon a multi-hour multi-role run."""

    left, right = arm_pair
    path = right / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    path.write_text("this is not json\n", encoding="utf-8")
    report = compare_arms(left, right, roles=["order", "bucket"])
    assert report["roles"]["order"]["status"] == "UNAVAILABLE"
    assert "jsonl_row_invalid" in report["roles"]["order"]["reason"]
    # The other role still got compared.
    assert report["roles"]["bucket"]["status"] == VERDICT_EQUIVALENT
    assert report["verdict"] == VERDICT_INCOMPLETE


def test_an_appledouble_sidecar_does_not_make_an_arm_ambiguous(arm_pair):
    """Copying evidence to exFAT or SMB -- how an arm moves between this laptop
    and the VPS -- leaves a ``._NAME`` sidecar beside every file."""

    left, _ = arm_pair
    suffix = task2.ROLE_SUFFIXES["order"]
    (left / f"._{PREFIX}_{suffix}").write_bytes(b"\x00\x05\x16\x07")
    assert ArmOutputs(left).prefix == PREFIX


def test_a_cold_path_that_is_a_file_is_not_treated_as_an_archive(arm_pair):
    left, _ = arm_pair
    suffix = task2.ROLE_SUFFIXES["decision"]
    (left / f"OTHER_{suffix}.cold").write_text("", encoding="utf-8")
    assert ArmOutputs(left).prefix == PREFIX


def test_raw_and_cold_present_together_is_refused_not_guessed(arm_pair):
    left, right = arm_pair
    suffix = task2.ROLE_SUFFIXES["decision"]
    for root in (left, right):
        (root / f"{PREFIX}_{suffix}").write_text("", encoding="utf-8")
        (root / f"{PREFIX}_{suffix}.cold").mkdir()
    assert ArmOutputs(left).storage_mode("decision") == "ambiguous"
    report = compare_arms(left, right, roles=["decision"])
    assert report["roles"]["decision"]["status"] == "UNAVAILABLE"
    assert report["verdict"] == VERDICT_INCOMPLETE


def test_a_self_comparison_is_flagged_as_one(arm_pair):
    """An EQUIVALENT verdict from comparing a directory with itself proves the
    reader is deterministic, not that the harness discriminates."""

    left, right = arm_pair
    assert compare_arms(left, left, roles=["order"])["same_root"] is True
    assert compare_arms(left, right, roles=["order"])["same_root"] is False


def test_absence_is_distinguishable_from_a_value_under_expose_values(arm_pair):
    left, right = arm_pair
    _mutate_order(right, 0, lambda row: row.pop("candidate_ev_r"))
    report = compare_arms(left, right, roles=["order"], expose_values=True)
    (difference,) = _find(report, "order", "candidate_ev_r")
    assert difference["left_present"] is True
    assert difference["right_present"] is False
    assert difference["right_value_sha256"] is None


def test_the_harness_and_task2_agree_on_what_is_equivalent(arm_pair):
    """The correctness property: every condition on which ``task2`` raises is an
    UNKNOWN here, so the harness's EQUIVALENT is never weaker than task2's."""

    left, right = arm_pair
    _mutate_order(
        right,
        0,
        lambda row: row["risk_authority"].__setitem__("packet_hash_sha256", HASH_B),
        reseal=False,
    )
    path_l = left / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    path_r = right / f"{PREFIX}_{task2.ROLE_SUFFIXES['order']}"
    rows_l = [json.loads(x) for x in path_l.read_text().splitlines() if x]
    rows_r = [json.loads(x) for x in path_r.read_text().splitlines() if x]

    with pytest.raises(task2.SemanticAcceptanceError):
        task2.compare_role_rows("order", rows_l, rows_r)
    assert compare_arms(left, right, roles=["order"])["verdict"] == VERDICT_DIFFER


# --------------------------------------------------------------------------
# Real sealed evidence.
# --------------------------------------------------------------------------


@requires_sealed_arms
def test_a_sealed_arm_compared_with_itself_is_equivalent():
    report = compare_arms(
        SEALED_S0R0, SEALED_S0R0, roles=["order", "trade", "oracle"]
    )
    assert report["verdict"] == VERDICT_EQUIVALENT
    assert report["roles"]["order"]["left_row_count"] == 182
    assert report["roles"]["trade"]["left_row_count"] == 90
    assert report["totals"]["unknown_difference_count"] == 0


@requires_sealed_arms
def test_two_different_sealed_arms_are_reported_as_differing():
    report = compare_arms(
        SEALED_S0R0, SEALED_S1R0, roles=["order", "trade"], alignment="identity"
    )
    assert report["verdict"] == VERDICT_DIFFER
    assert report["left"]["arm_id"] == "S0R0"
    assert report["right"]["arm_id"] == "S1R0"
    order = report["roles"]["order"]
    assert order["left_row_count"] == 182
    assert order["right_row_count"] == 156
    assert order["left_only_row_count"] == 40
    assert order["right_only_row_count"] == 14
    assert order["unknown_difference_count"] > 0
    assert any(
        d["field_path"] == "b7_5_selection_sizing_factorial_arm_id"
        for d in order["differences"]
    )


@requires_sealed_arms
def test_the_cold_shard_roles_are_readable_on_a_sealed_arm():
    """``decision``/``scorecard``/``missed`` exist only as ``.cold`` archives."""

    arm = ArmOutputs(SEALED_S0R0)
    storage = arm.describe()["role_storage"]
    assert storage["decision"] == "cold"
    assert storage["scorecard"] == "cold"
    assert storage["missed"] == "cold"
    # `order` was a flat `.jsonl` when this arm was sealed. The 2026-08-12 storage-reclamation
    # pass compressed it in place to `.jsonl.zst` (its own manifest records the path at
    # 2,013,145 bytes), which is a THIRD storage form -- and until the harness learned it, the
    # role reported `absent` and `compare_arms` degraded to INCOMPLETE. Sealed evidence made
    # invisible by a compression, quietly. It reads, and the rows are still there.
    assert storage["order"] == "zst"
    assert sum(1 for _ in arm.iter_role_rows("order")) == 182
    assert "order" in arm.available_roles()
    rows = []
    for row in arm.iter_role_rows("decision"):
        rows.append(row)
        if len(rows) == 5:
            break
    assert len(rows) == 5
    assert rows[0]["row_type"] == "asof_decision"
