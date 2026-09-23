"""Behavioural pins for the March 2026 one-shot authorization.

These tests exist because the module they cover deliberately opens the estate's
strongest fuse. Every one of them asserts BEHAVIOUR (what `authorize_window`
does), never source text, so they pass only against an implementation that
actually refuses.

The default-off tests duplicate coverage that already exists in
`test_training_lane_protocol.py` and `test_trainer_partitions.py` on purpose:
those files pin the surface map and registry, this one pins that adding an
arming path did not quietly weaken them.
"""

from __future__ import annotations

import hashlib

import pytest

from src.research_infra import trainer_partitions
from src.research_infra.train_engine import guard
from src.research_infra.train_engine import march_one_shot as M

MARCH = ("2026-03-01", "2026-03-31")
JANUARY = ("2026-01-01", "2026-01-31")
LIVE_FORWARD = ("2026-07-29", "2026-07-31")


@pytest.fixture
def prereg_digest() -> str:
    path = M.REPO_ROOT / M.MARCH_PREREG_REPO_RELPATH
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def armed(monkeypatch, prereg_digest):
    monkeypatch.setenv(M.ENV_PREREG_SHA256, prereg_digest)
    return M.current()


@pytest.fixture
def unarmed(monkeypatch):
    monkeypatch.delenv(M.ENV_PREREG_SHA256, raising=False)


# -- default-off ------------------------------------------------------------------


def test_unarmed_returns_none(unarmed):
    assert M.current() is None


@pytest.mark.parametrize(
    "purpose",
    [guard.PURPOSE_LANE_ITERATION, guard.PURPOSE_TRAINING, guard.PURPOSE_REPRODUCTION],
)
def test_unarmed_march_is_refused_on_every_purpose(unarmed, purpose):
    with pytest.raises(guard.WindowRefused) as excinfo:
        guard.authorize_window(start=MARCH[0], end=MARCH[1], purpose=purpose)
    assert "blackout" in str(excinfo.value)


def test_unarmed_single_march_day_is_refused(unarmed):
    """A one-day window is not a loophole; the blackout is per-day."""

    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start="2026-03-17", end="2026-03-17", purpose=guard.PURPOSE_LANE_ITERATION
        )


def test_unarmed_window_straddling_march_is_refused(unarmed):
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(
            start="2026-02-25", end="2026-03-03", purpose=guard.PURPOSE_LANE_ITERATION
        )


# -- arming authenticates ---------------------------------------------------------


def test_wrong_digest_raises_rather_than_silently_unarming(monkeypatch):
    """The failure mode that would be worst is a quiet no-arm."""

    monkeypatch.setenv(M.ENV_PREREG_SHA256, "0" * 64)
    with pytest.raises(M.MarchOneShotRefused) as excinfo:
        M.current()
    assert "digest_mismatch" in str(excinfo.value)


def test_wrong_digest_propagates_through_the_guard(monkeypatch):
    monkeypatch.setenv(M.ENV_PREREG_SHA256, "deadbeef")
    with pytest.raises(M.MarchOneShotRefused):
        guard.authorize_window(
            start=MARCH[0], end=MARCH[1], purpose=guard.PURPOSE_LANE_ITERATION
        )


def test_armed_authorization_names_its_own_protocol(armed, prereg_digest):
    assert armed is not None
    assert armed.prereg_sha256 == prereg_digest
    assert armed.span == trainer_partitions.RESERVED_UNREAD_MARCH_2026
    assert armed.as_dict()["authorized_purpose"] == "LANE_ITERATION"


# -- armed: exactly one door opens ------------------------------------------------


def test_armed_lane_iteration_on_march_is_authorized(armed):
    auth = guard.authorize_window(
        start=MARCH[0], end=MARCH[1], purpose=guard.PURPOSE_LANE_ITERATION
    )
    assert len(auth.days) == 31
    assert auth.dominant_surface == "VAL"
    assert auth.may_emit_iteration_evidence is True


@pytest.mark.parametrize(
    "purpose", [guard.PURPOSE_TRAINING, guard.PURPOSE_REPRODUCTION]
)
def test_armed_march_still_refused_for_every_other_purpose(armed, purpose):
    with pytest.raises(guard.WindowRefused):
        guard.authorize_window(start=MARCH[0], end=MARCH[1], purpose=purpose)


def test_armed_march_is_never_trainable(armed):
    """The one-shot buys iteration, never fitting."""

    auth = guard.authorize_window(
        start=MARCH[0], end=MARCH[1], purpose=guard.PURPOSE_LANE_ITERATION
    )
    assert auth.trainable_checked is False
    assert auth.may_emit_training_evidence is False
    assert set(auth.roles.values()) == {"RESERVED_UNREAD"}
    assert "RESERVED_UNREAD" not in trainer_partitions.TRAINABLE_ROLES


def test_armed_does_not_open_the_live_forward_stream(armed):
    with pytest.raises(guard.WindowRefused) as excinfo:
        guard.authorize_window(
            start=LIVE_FORWARD[0],
            end=LIVE_FORWARD[1],
            purpose=guard.PURPOSE_LANE_ITERATION,
        )
    assert "TEST" in str(excinfo.value)


def test_armed_leaves_january_bit_for_bit_alone(armed):
    """January must resolve against the UNRENAMED default map even while armed."""

    auth = guard.authorize_window(
        start=JANUARY[0], end=JANUARY[1], purpose=guard.PURPOSE_LANE_ITERATION
    )
    assert auth.surface_map_id == trainer_partitions.DEFAULT_SURFACE_MAP.map_id
    assert "march_one_shot" not in auth.surface_map_id
    assert "march_one_shot" not in auth.registry_id


def test_armed_march_receipt_names_the_one_shot_without_extra_disclosure(armed):
    auth = guard.authorize_window(
        start=MARCH[0], end=MARCH[1], purpose=guard.PURPOSE_LANE_ITERATION
    )
    assert "march_one_shot:MARCH_PREREG_V1" in auth.surface_map_id
    assert "march_one_shot:MARCH_PREREG_V1" in auth.registry_id


# -- the span guard ---------------------------------------------------------------


def test_authorized_objects_refuse_a_wider_blackout(armed):
    """If a successor protects a second month, the one-shot must not unlock it."""

    widened = trainer_partitions.DEFAULT_SURFACE_MAP.__class__(
        map_id="widened",
        authored_utc="2026-08-05",
        bands=trainer_partitions.DEFAULT_SURFACE_MAP.bands,
        gaps=trainer_partitions.DEFAULT_SURFACE_MAP.gaps,
        blackout=(("2026-03-01", "2026-03-31"), ("2026-09-01", "2026-09-30")),
    )
    with pytest.raises(M.MarchOneShotRefused) as excinfo:
        M.authorized_surfaces(armed, base=widened)
    assert "span_mismatch" in str(excinfo.value)


def test_authorized_surface_map_clears_only_march(armed):
    surfaces = M.authorized_surfaces(armed)
    assert surfaces.blackout == ()
    # Every band the default map declared is still there, unmoved.
    assert {(b.band_id, b.start, b.end, b.surface) for b in surfaces.bands} == {
        (b.band_id, b.start, b.end, b.surface)
        for b in trainer_partitions.DEFAULT_SURFACE_MAP.bands
    }
    assert surfaces.surface_for_day("2026-03-15").surface == "VAL"
    assert surfaces.surface_for_day("2026-07-30").iterable is False


def test_authorized_registry_keeps_march_unfittable(armed):
    registry = M.authorized_registry(armed)
    assert registry.reserved_blackout == ()
    disposition = registry.disposition_for_day("2026-03-15")
    assert disposition.role == "RESERVED_UNREAD"
    assert disposition.trainable is False


def test_the_default_objects_are_not_mutated_by_arming(armed):
    """`dataclasses.replace` must copy, not edit the module singletons."""

    M.authorized_surfaces(armed)
    M.authorized_registry(armed)
    assert trainer_partitions.DEFAULT_SURFACE_MAP.blackout == (
        trainer_partitions.RESERVED_UNREAD_MARCH_2026,
    )
    assert trainer_partitions.DEFAULT_REGISTRY.reserved_blackout == (
        trainer_partitions.RESERVED_UNREAD_MARCH_2026,
    )
