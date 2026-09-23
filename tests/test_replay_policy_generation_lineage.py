"""Behavioural tests for the replay generation-lineage instrument (Session Y, B480+).

These are deliberately behavioural, not source-string assertions: the whole
finding they support is that a source that *looks* right can be running a
different program than the record it is compared against.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book.sleeves import asian_fade, kz_london_crypto_low
from src.research_infra.replay_policy import generation_lineage as GL

UTC = timezone.utc
# 2026-07-08 is inside the K1-b live window; FTMO server = America/New_York + 7h
# = UTC+3 there, and the EU and US DST calendars agree, so +3 is not in dispute.
SUMMER = datetime(2026, 7, 8, 5, 0, tzinfo=UTC)


def test_mainline_reads_server_hour_and_deployed_reads_utc_hour():
    assert asian_fade._hour(SUMMER) == 8            # server-local, post-B29
    with GL.deployed_lineage():
        assert asian_fade._hour(SUMMER) == 5        # raw UTC, the deployed tree
    assert asian_fade._hour(SUMMER) == 8            # restored


def test_day_boundary_differs_by_three_hours():
    late = datetime(2026, 7, 8, 22, 0, tzinfo=UTC)
    assert asian_fade._day(late) == "2026-07-09"    # server day rolls at 21:00 UTC
    with GL.deployed_lineage():
        assert asian_fade._day(late) == "2026-07-08"
    assert asian_fade._day(late) == "2026-07-09"


def test_helpers_are_restored_by_identity_even_on_error():
    before = {name: {a: getattr(_mod(name), a) for a in attrs}
              for name, attrs in GL.DEPLOYED_HELPERS.items()}
    with pytest.raises(RuntimeError):
        with GL.deployed_lineage():
            raise RuntimeError("boom")
    for name, attrs in before.items():
        for attr, fn in attrs.items():
            assert getattr(_mod(name), attr) is fn


def _mod(name):
    import importlib
    return importlib.import_module(f"src.components.ultimate_book.sleeves.{name}")


def test_activating_twice_fails_closed():
    with GL.deployed_lineage():
        with pytest.raises(GL.LineageError):
            with GL.deployed_lineage():
                pass


def test_reentry_is_refused_on_an_active_marker_not_on_a_probe():
    """An earlier revision took a public `verify=False` that disabled both probes, and
    a refuter measured that this let a nested caller in **silently** — the second
    entry's post-swap probe reads what the FIRST entry installed, so it passes. The
    refusal now rests on an explicit active marker, and there is no way to switch the
    probes off at all."""
    assert not hasattr(GL.deployed_lineage, "verify")
    with GL.deployed_lineage():
        assert GL._ACTIVE == [GL.DEPLOYED]
        with pytest.raises(GL.LineageError, match="already installed"):
            with GL.deployed_lineage():
                pass
    assert GL._ACTIVE == []
    assert asian_fade._hour(SUMMER) == 8


def test_a_failed_entry_does_not_disarm_the_outer_marker():
    with GL.deployed_lineage():
        for _ in range(3):
            with pytest.raises(GL.LineageError):
                with GL.deployed_lineage():
                    pass
        assert GL._ACTIVE == [GL.DEPLOYED]
        assert asian_fade._hour(SUMMER) == 5
    assert GL._ACTIVE == []


def test_entry_from_another_thread_is_refused_while_one_is_held():
    import threading
    seen = []

    def worker():
        try:
            with GL.deployed_lineage():
                seen.append("entered")
        except GL.LineageError:
            seen.append("refused")

    with GL.deployed_lineage():
        t = threading.Thread(target=worker)
        t.start()
        t.join(10)
    assert seen == ["refused"]


def test_register_covers_every_clock_owning_sleeve():
    """A further clock sleeve must not silently escape the register.

    The first revision keyed this on `_server_clock` importers alone, which let
    `fx_jpy` — the only clock owner an ARMED sleeve reaches, via
    `metals.py:157` — escape. Do not narrow it again.

    AMENDED at the wave-8 train merge: a clock-owning sleeve now has two honest
    classifications — DEPLOYED_HELPERS (its clock MOVED between redacted_host and HEAD)
    or NO_DEPLOYED_LINEAGE (it postdates the deployed lineage entirely, so a
    live-lineage replay generates nothing for it). The union must still be exact
    and the two disjoint, so nothing escapes.
    """
    assert set(GL.DEPLOYED_HELPERS) | set(GL.NO_DEPLOYED_LINEAGE) == GL.clock_dependent_sleeves()
    assert not set(GL.DEPLOYED_HELPERS) & set(GL.NO_DEPLOYED_LINEAGE)


def test_every_clock_consumer_is_covered_by_a_registered_owner():
    """`metals.py` owns no clock; it calls `fx_jpy`'s at call time, so the owner's
    register entry reaches it. A new consumer of an UNregistered owner fails here."""
    consumers = GL.clock_consuming_sleeves()
    assert consumers == dict(GL.CLOCK_CONSUMERS)
    for consumer, owner in consumers.items():
        assert owner in GL.DEPLOYED_HELPERS, f"{consumer} consumes unregistered {owner}"


def test_fx_jpy_swap_reaches_the_armed_metals_feature():
    """`metals._a8_features` computes `session_hour` through `fx_jpy._to_server_local`
    with a FUNCTION-LOCAL import, so swapping the owner's attribute must reach it.

    The probe sits on a DST seam: 2026-03-10 is after the US switch (Mar 8) and
    before the EU one (Mar 29), which is the only kind of instant where the two
    calendars disagree.
    """
    from src.components.ultimate_book.sleeves import metals

    seam = datetime(2026, 3, 10, 21, 0, tzinfo=UTC)          # server 00:00 (US) / 23:00 (EU)
    bars = [_bar(i) for i in range(60)]
    atrs = [1.0] * 60

    main = metals._a8_features(bars, atrs, 59, 1.0, seam)["session_hour"]
    with GL.deployed_lineage():
        dep = metals._a8_features(bars, atrs, 59, 1.0, seam)["session_hour"]
    assert main == 0 and dep == 23
    # ...and that flips the A8 ASIAN confluence condition (0 <= session_hour <= 6).
    from src.components.ultimate_book.metals_confluence_gate import metals_confluence
    kw = dict(htf_slope_norm=1.0, mom_20_atr=1.0, fvg_freshness_bars=99.0,
              atr_ratio=1.0, enabled=True)
    assert metals_confluence(session_hour=main, **kw).passed
    assert not metals_confluence(session_hour=dep, **kw).passed


def _bar(i: int):
    from src.components.ultimate_book.primitives import Bar
    return Bar(100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i)


def test_summer_probe_alone_would_not_have_certified_the_fx_jpy_swap():
    """Why `_to_server_local`'s guard must sit on a seam: in the K1-b window the
    two calendars agree, so a summer probe passes under both and certifies nothing."""
    from src.components.ultimate_book.sleeves import fx_jpy

    assert fx_jpy._to_server_local(SUMMER) == GL.pre_f7_to_server_local(SUMMER)
    seam = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
    assert fx_jpy._to_server_local(seam) != GL.pre_f7_to_server_local(seam)


def test_mainline_lineage_is_a_no_op():
    with GL.lineage(GL.MAINLINE) as report:
        assert report["lineage"] == GL.MAINLINE
        assert asian_fade._hour(SUMMER) == 8


def test_unknown_lineage_refuses():
    with pytest.raises(GL.LineageError):
        with GL.lineage("whatever"):
            pass


def test_fixed_decision_bar_sleeve_is_eligible_three_hours_apart():
    """The discriminating case, as behaviour.

    `kz_london_crypto_low` fires only when the decision bar's (hour, minute)
    equals its constants — there is no latch and no path dependence. Under the
    two lineages the eligible UTC instant differs by exactly the server offset,
    so such a sleeve disagrees with the live record on EVERY day rather than
    occasionally: live-recall 0 %, which is what K1 measured for it.
    """
    day = datetime(2026, 7, 8, 0, 0, tzinfo=UTC)
    grid = [day + timedelta(minutes=15 * k) for k in range(96)]
    want = (kz_london_crypto_low.DECISION_HOUR, kz_london_crypto_low.DECISION_MIN)

    mainline = [t for t in grid if kz_london_crypto_low._hm(t) == want]
    with GL.deployed_lineage():
        deployed = [t for t in grid if kz_london_crypto_low._hm(t) == want]

    assert len(mainline) == 1 and len(deployed) == 1
    # mainline resolves the constant as a SERVER hour (12:00 server = 09:00 UTC);
    # the deployed tree compares it to the UTC hour, so it fires 3 h later.
    assert mainline[0] == datetime(2026, 7, 8, 9, 0, tzinfo=UTC)
    assert deployed[0] - mainline[0] == timedelta(hours=3)
    assert not set(mainline) & set(deployed)


def test_deployed_lineage_claim_is_pinned_to_the_live_commit():
    """The lineage claim itself: every registered sleeve is on a repaired clock at
    HEAD and on none at redacted_host, and the register is exactly the set that moved."""
    try:
        subprocess.run(["git", "cat-file", "-e", "redacted_host^{commit}"],
                       check=True, capture_output=True)
    except Exception:
        pytest.skip("live-lineage commit redacted_host not present in this clone")

    def show(rev, path):
        return subprocess.run(["git", "show", f"{rev}:{path}"],
                              check=True, capture_output=True, text=True).stdout

    for name in GL.DEPLOYED_HELPERS:
        path = f"src/components/ultimate_book/sleeves/{name}.py"
        live, head = show("redacted_host", path), show("HEAD", path)
        assert not any(m in live for m in GL._CLOCK_MARKERS), \
            f"{name}: live lineage already carries a repaired clock?"
        assert any(m in head for m in GL._CLOCK_MARKERS), \
            f"{name}: HEAD is not on the repaired clock"
        assert live != head, f"{name}: registered but identical across the lineages"
    # The NO_DEPLOYED_LINEAGE half is pinned with the inverse claim: the file must NOT
    # exist at the live commit (nothing to transcribe, nothing to replay) and must own a
    # clock at HEAD. A sleeve that DOES exist there belongs in DEPLOYED_HELPERS instead.
    for name in GL.NO_DEPLOYED_LINEAGE:
        path = f"src/components/ultimate_book/sleeves/{name}.py"
        probe = subprocess.run(["git", "cat-file", "-e", f"redacted_host:{path}"],
                               capture_output=True)
        assert probe.returncode != 0, \
            f"{name}: exists at redacted_host — it has a deployed lineage and belongs in DEPLOYED_HELPERS"
        assert any(m in show("HEAD", path) for m in GL._CLOCK_MARKERS), \
            f"{name}: classified as clock-owning but HEAD carries no clock marker"

    # ...and nothing that moved is missing from the register.
    changed = subprocess.run(
        ["git", "diff", "--name-only", "redacted_host", "HEAD",
         "--", "src/components/ultimate_book/sleeves/"],
        check=True, capture_output=True, text=True).stdout.split()
    moved = {p.rsplit("/", 1)[-1][:-3] for p in changed if p.endswith(".py")}
    moved -= {"_server_clock"}                       # added by the repair, not a sleeve
    # Every diverged CLOCK-OWNING sleeve module is classified: either its clock MOVED
    # (DEPLOYED_HELPERS, with the deployed behaviour transcribed) or it POSTDATES the deployed
    # lineage entirely (NO_DEPLOYED_LINEAGE, nothing to transcribe). Wave-8 train merge.
    #
    # "Clock-owning at EITHER lineage", not just at HEAD: a sleeve that carried a clock at
    # redacted_host and lost it since still needs a classification, and `clock_dependent_sleeves()`
    # only reads HEAD.
    #
    # This compared `moved` to the register directly, i.e. it required a lineage classification
    # for ANY edit anywhere under `sleeves/`. That is not the register's invariant -- the module
    # states it as `DEPLOYED_HELPERS | NO_DEPLOYED_LINEAGE == clock_dependent_sleeves()`, which
    # `test_the_register_covers_every_clock_owner` asserts and which passes. Five modules have
    # since diverged for reasons that have nothing to do with a clock (`ce3be027a` centralised
    # the legacy stop-floor expression across `_stop_floor`/`metals`/`metals_ob_micro`,
    # `eeb73b090` struck the STAGE13 founding numbers in `candidate_registry`, `f2fdd99de`
    # prepared ETHUSD in `crypto`) and none of them owns a clock at either lineage. The guard
    # was reporting ordinary sleeve maintenance as an unclassified lineage divergence.
    clock_owning = set(GL.clock_dependent_sleeves())
    for name in sorted(moved - clock_owning):
        blob = subprocess.run(
            ["git", "show", f"redacted_host:src/components/ultimate_book/sleeves/{name}.py"],
            capture_output=True, text=True)
        if blob.returncode == 0 and any(m in blob.stdout for m in GL._CLOCK_MARKERS):
            clock_owning.add(name)
    assert moved & clock_owning == set(GL.DEPLOYED_HELPERS) | set(GL.NO_DEPLOYED_LINEAGE)
