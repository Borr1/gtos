"""Session BD (B2073-B2085) -- OD-P1: emit-on-change, and the state contract that decides it.

WHAT WAS FILED. Session P, OD-P1: emit-on-change for `position_managed` *"drops 76.05 % of the
stream ... my recommendation: yes, with a 15-minute heartbeat"*, and **irreversible for the window
in which it runs** -- packets not emitted are not recoverable.

WHAT THE MEASUREMENT CHANGED. Over the same 99,112-packet export the SAME stream compresses by
anything from 0.94 % to 96.72 % depending only on which fields count as state:

    none (every field is state)                 0.94 % of position_managed   0.74 % of stream
    top-level `*_checked_at_utc` excluded       40.14 %                     31.87 %
    RECURSIVE `*_checked_at_utc` excluded       96.72 %                     76.79 %

So P's 76.05 % is reproducible (line 3, within 0.7 pp) and P's contract was never written down.
The obvious implementation is line 2 -- **a top-level exclusion list under-delivers by 2.4x while
looking deployed** -- because `policy_clock_diagnostic` embeds its own `checked_at_utc` one level
down, on 59.7 % of rows at 100 % churn. That single nested key IS the gap between the two lines.

AND THE RECOMMENDED CONFIGURATION IS NOT THE HEADLINE. 76.05 %/76.79 % is the NO-heartbeat figure.
With the 15-minute heartbeat P recommends in the same paragraph, the measured drop is
**73.70 % of the stream** -- the heartbeat costs 3,068 packets, 2.35 pp. Quote the configuration
you are shipping, not the one you measured.

DEPLOYMENT. The code default remains OFF, while the live config explicitly enables the measured
15-minute-heartbeat contract after guard-valid replay against the current host ledger.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book.packet_emit_on_change import (
    STATE_CONTRACT_ID,
    PositionManagedEmitFilter,
    filter_packets,
    state_digest,
    strip_observation_instants,
)
from src.components.ultimate_book.runtime_learning_packet import (
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)

T0 = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)


def _packet(*, bars=10, at=T0, ticket="abc", event="position_managed", action="monitoring"):
    stamp = at.isoformat()
    return {
        "event_type": event,
        "created_at_utc": stamp,
        "outcome": {
            "ticket_hash_sha256": ticket,
            "sleeve": "crypto",
            "symbol": "BTCUSD",
            "action": action,
            "policy_clock_bars_until_due": bars,
            "management_checked_at_utc": stamp,
            "last_management_checked_at_utc": stamp,
            "policy_clock_checked_at_utc": stamp,
            "policy_clock_diagnostic": {"status": "ok", "checked_at_utc": stamp},
        },
    }


# --------------------------------------------------------------------------------------------
# 1. The state contract -- recursion is the load-bearing word
# --------------------------------------------------------------------------------------------


def test_a_nested_observation_instant_is_stripped():
    """The 2.4x. A top-level-only strip leaves `policy_clock_diagnostic.checked_at_utc` in state."""
    a = _packet(at=T0)["outcome"]
    b = _packet(at=T0 + timedelta(seconds=60))["outcome"]
    assert a["policy_clock_diagnostic"] != b["policy_clock_diagnostic"]
    assert state_digest(a) == state_digest(b), "the nested instant is still counted as state"


def test_a_toplevel_only_strip_would_not_collapse_these():
    """The counterfactual, run. This is what the obvious implementation does."""
    def toplevel_only(outcome):
        return {k: v for k, v in sorted(outcome.items())
                if k != "checked_at_utc" and not k.endswith("_checked_at_utc")}

    a, b = _packet(at=T0)["outcome"], _packet(at=T0 + timedelta(seconds=60))["outcome"]
    assert toplevel_only(a) != toplevel_only(b), "top-level strip leaves them distinct -> emits both"
    assert state_digest(a) == state_digest(b), "the recursive strip collapses them -> emits one"


def test_only_checked_at_keys_are_stripped():
    value = {
        "checked_at_utc": "x",
        "policy_clock_checked_at_utc": "x",
        "nested": {"management_checked_at_utc": "x", "bars": 3},
        "created_at_utc": "x",
        "asof_utc": "x",
        "decision_bar_iso": "x",
        "bars": 7,
    }
    out = strip_observation_instants(value)
    assert "checked_at_utc" not in out and "policy_clock_checked_at_utc" not in out
    assert "management_checked_at_utc" not in out["nested"]
    # These are NOT observation instants -- `asof_utc` and `decision_bar_iso` are decision facts.
    assert out["created_at_utc"] == "x"
    assert out["asof_utc"] == "x"
    assert out["decision_bar_iso"] == "x"
    assert out["bars"] == 7 and out["nested"]["bars"] == 3


def test_the_bar_clock_advancing_is_a_change():
    """4.86 % churn on `policy_clock_bars_until_due` is the real signal. It must survive."""
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    assert f.decide(_packet(bars=10, at=T0))[0] is True
    assert f.decide(_packet(bars=10, at=T0 + timedelta(seconds=60)))[0] is False
    assert f.decide(_packet(bars=9, at=T0 + timedelta(seconds=120)))[0] is True


# --------------------------------------------------------------------------------------------
# 2. Nothing but `position_managed` is ever suppressed
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("event", [
    "position_closed", "breach_flatten", "position_adopted", "position_management_error",
    "position_out_of_universe", "unit_admitted", "unit_placed", "unit_skipped", "unit_shadow",
    "cycle_no_candidates", "cycle_no_decision",
])
def test_no_other_event_type_is_ever_suppressed(event):
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    for i in range(5):
        emit, _ = f.decide(_packet(event=event, at=T0 + timedelta(seconds=60 * i)))
        assert emit is True, f"{event} was suppressed"
    assert f.suppressed_total == 0


def test_a_close_is_emitted_even_after_identical_management_ticks():
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    f.decide(_packet(at=T0))
    assert f.decide(_packet(at=T0 + timedelta(seconds=60)))[0] is False
    closed = _packet(at=T0 + timedelta(seconds=120), event="position_closed")
    assert f.decide(closed)[0] is True


# --------------------------------------------------------------------------------------------
# 3. What is lost is COUNTABLE
# --------------------------------------------------------------------------------------------


def test_the_run_length_survives_the_compression():
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    f.decide(_packet(bars=10, at=T0))
    for i in range(1, 4):
        assert f.decide(_packet(bars=10, at=T0 + timedelta(seconds=60 * i)))[0] is False
    emit, ann = f.decide(_packet(bars=9, at=T0 + timedelta(seconds=240)))
    assert emit is True
    assert ann["emit_on_change_suppressed_before"] == 3
    assert ann["emit_on_change_unchanged_seconds"] == pytest.approx(240.0)
    assert ann["emit_on_change_state_contract"] == STATE_CONTRACT_ID


def test_the_annotations_land_on_the_emitted_packet():
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    kept, suppressed = filter_packets([_packet(at=T0)], f)
    assert suppressed == 0
    assert kept[0]["outcome"]["emit_on_change_status"] == "emitted_state_changed"

    batch = [_packet(at=T0 + timedelta(seconds=60)), _packet(at=T0 + timedelta(seconds=120))]
    kept, suppressed = filter_packets(batch, f)
    assert kept == [] and suppressed == 2

    kept, suppressed = filter_packets([_packet(bars=9, at=T0 + timedelta(seconds=180))], f)
    assert suppressed == 0
    assert kept[0]["outcome"]["emit_on_change_suppressed_before"] == 2


def test_annotations_rehash_a_guard_valid_runtime_packet():
    packet = build_runtime_learning_packet(
        namespace="operator_profile",
        event_type="position_managed",
        ts=T0.isoformat(),
        outcome={
            "ticket_hash_sha256": "a" * 64,
            "sleeve": "crypto",
            "symbol": "BTCUSD",
            "action": "monitoring",
        },
        source="test",
    )
    before = packet["packet_hash_sha256"]

    kept, suppressed = filter_packets(
        [packet],
        PositionManagedEmitFilter(heartbeat_seconds=900),
        now=T0,
    )

    assert suppressed == 0
    assert kept[0]["packet_hash_sha256"] != before
    assert kept[0]["outcome"]["emit_on_change_status"] == "emitted_state_changed"
    assert validate_runtime_learning_packet(kept[0]) == (True, [])


def test_the_heartbeat_fires_and_is_labelled():
    f = PositionManagedEmitFilter(heartbeat_seconds=900)
    f.decide(_packet(at=T0))
    assert f.decide(_packet(at=T0 + timedelta(seconds=300)))[0] is False
    emit, ann = f.decide(_packet(at=T0 + timedelta(seconds=900)))
    assert emit is True
    assert ann["emit_on_change_status"] == "emitted_heartbeat"
    assert f.heartbeat_total == 1


def test_heartbeat_zero_disables_the_heartbeat_rather_than_firing_every_tick():
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    f.decide(_packet(at=T0))
    for i in range(1, 100):
        assert f.decide(_packet(at=T0 + timedelta(seconds=60 * i)))[0] is False
    assert f.heartbeat_total == 0


# --------------------------------------------------------------------------------------------
# 4. Fail OPEN -- a filter fault must never stop the evidence stream
# --------------------------------------------------------------------------------------------


def test_an_unidentifiable_position_is_emitted():
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    blind = {"event_type": "position_managed", "outcome": {"action": "monitoring"}}
    for _ in range(3):
        emit, ann = f.decide(blind)
        assert emit is True
        assert ann["emit_on_change_status"] == "emitted_unidentifiable_position"


def test_an_unserialisable_outcome_is_emitted_not_dropped():
    class Exploding:
        def __repr__(self):
            raise RuntimeError("boom")

    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    packet = _packet(at=T0)
    packet["outcome"]["landmine"] = Exploding()
    emit, _ = f.decide(packet)
    assert emit is True


def test_a_filter_that_raises_does_not_drop_the_batch():
    class Broken(PositionManagedEmitFilter):
        def decide(self, packet, *, now=None):
            raise RuntimeError("boom")

    kept, suppressed = filter_packets([_packet(at=T0), _packet(at=T0)], Broken())
    assert len(kept) == 2 and suppressed == 0


def test_no_filter_is_the_identity_function():
    """Default-off must cost nothing and reach no branch."""
    packets = [_packet(at=T0), _packet(at=T0)]
    kept, suppressed = filter_packets(packets, None)
    assert kept == packets and suppressed == 0
    assert "emit_on_change_status" not in packets[0]["outcome"]


# --------------------------------------------------------------------------------------------
# 5. Bounded state
# --------------------------------------------------------------------------------------------


def test_positions_are_evicted_so_the_state_dict_cannot_grow_without_bound():
    f = PositionManagedEmitFilter(heartbeat_seconds=0, state_ttl_seconds=3600)
    for i in range(50):
        f.decide(_packet(ticket=f"t{i}", at=T0))
    assert f.status()["tracked_positions"] == 50
    f.decide(_packet(ticket="fresh", at=T0 + timedelta(seconds=7200)))
    assert f.status()["tracked_positions"] == 1


def test_two_positions_do_not_share_state():
    f = PositionManagedEmitFilter(heartbeat_seconds=0)
    assert f.decide(_packet(ticket="a", at=T0))[0] is True
    assert f.decide(_packet(ticket="b", at=T0))[0] is True
    assert f.decide(_packet(ticket="a", at=T0 + timedelta(seconds=60)))[0] is False
    assert f.decide(_packet(ticket="b", at=T0 + timedelta(seconds=60)))[0] is False


# --------------------------------------------------------------------------------------------
# 6. Default OFF, in the book
# --------------------------------------------------------------------------------------------


def test_the_book_builds_no_filter_by_default():
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    owner = UltimateBookOwner.__new__(UltimateBookOwner)
    rt: dict = {}
    assert not rt.get("ultimate_book_runtime_learning_packet_emit_on_change", False)
    # The constructor branch is guarded by exactly that key; an unset key means None.
    assert getattr(owner, "_runtime_learning_emit_filter", None) is None


def test_book_owner_survives_the_filter_module_being_absent():
    """A carry that copies `book_owner.py` WITHOUT this new file must not kill the live book.

    `book_owner.py` is on the host; `packet_emit_on_change.py` is not. A module-top import of a
    file that has not landed raises ImportError at module load, propagates out of `run_book.py`
    startup, and stops BOTH funded accounts. AZ measured 9 of 16 partial carry states unsafe with
    four of them module-load deaths -- against a probe that could not have seen this one, because
    the file did not exist when it ran.

    Loaded here with the import genuinely blocked, not by asserting the try/except exists.
    """
    import importlib
    import sys

    blocked = "src.components.ultimate_book.packet_emit_on_change"
    saved = {k: sys.modules.get(k) for k in (blocked, "src.components.ultimate_book.book_owner")}

    class _Blocker:
        def find_module(self, name, path=None):
            return self if name == blocked else None

        def find_spec(self, name, path=None, target=None):
            if name == blocked:
                raise ImportError("simulated: this file was not carried")
            return None

    sys.modules.pop(blocked, None)
    sys.modules.pop("src.components.ultimate_book.book_owner", None)
    sys.meta_path.insert(0, _Blocker())
    try:
        bo = importlib.import_module("src.components.ultimate_book.book_owner")
        assert bo.EMIT_ON_CHANGE_AVAILABLE is False
        # ...and the fallback is the identity function, so packets still flow.
        packets = [{"event_type": "position_managed", "outcome": {"a": 1}}]
        kept, suppressed = bo.filter_emit_on_change_packets(packets, None)
        assert kept == packets and suppressed == 0
    finally:
        sys.meta_path.pop(0)
        for k, v in saved.items():
            if v is not None:
                sys.modules[k] = v
            else:
                sys.modules.pop(k, None)
        importlib.import_module("src.components.ultimate_book.book_owner")


def test_a_corrupt_filter_module_degrades_the_same_way_as_an_absent_one():
    """A half-finished transfer leaves the file PRESENT AND BROKEN -- SyntaxError, not ImportError.

    `except ImportError` would not catch it and the book would die anyway, which is why the guard
    is `except Exception`. Same reasoning as `packet_economics.py:58-66`.
    """
    import ast
    import inspect
    import pathlib

    from src.components.ultimate_book import book_owner as bo

    tree = ast.parse(pathlib.Path(inspect.getsourcefile(bo)).read_text(encoding="utf-8"))
    guards = [
        h for node in ast.walk(tree) if isinstance(node, ast.Try)
        for h in node.handlers
        if any(isinstance(n, ast.ImportFrom) and (n.module or "").endswith("packet_emit_on_change")
               for n in ast.walk(node))
    ]
    assert guards, "the emit-on-change import is not guarded at all"
    for h in guards:
        assert isinstance(h.type, ast.Name) and h.type.id == "Exception", (
            "the guard is narrower than Exception; a corrupt module raises SyntaxError and would "
            "kill the live book on both accounts"
        )


def test_live_config_enables_the_measured_fifteen_minute_contract():
    import pathlib
    import yaml

    root = pathlib.Path(__file__).resolve().parents[2]
    config = yaml.safe_load((root / "config" / "agent_config.yaml").read_text(encoding="utf-8"))
    rt = config["gtos_vnext_runtime"]
    assert rt["ultimate_book_runtime_learning_packet_emit_on_change"] is True
    assert rt["ultimate_book_runtime_learning_packet_emit_heartbeat_seconds"] == 900
