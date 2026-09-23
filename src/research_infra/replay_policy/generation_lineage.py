"""Which *code generation* a replay is imitating — the missing axis in K1-b.

The problem this exists to make measurable
------------------------------------------
`phase3/K1_GATE_RECEIPT.md` compares the generation port's intents against the
intents the live FTMO book recorded over 2026-06-18..07-24, and reports 19 %
live-recall on seven "first-of-day" sleeves against 96 % on the per-bar ones.
It attributes the gap to path dependence: a first-of-day rule latches on the
session's first qualifying bar, so one differing bar diverges the whole day.

**That comparison ran two different programs against each other.** The live book
runs the VPS lineage (`redacted_host`, byte-identical to the 2026-07-25 read-only
export). Mainline carries the F7/B29 clock repair, which the VPS has never been
given: `_server_clock.py` does not exist in that tree at all.

**Ten** sleeve files differ between the two, in two distinct ways:

* **Nine** — `asian_fade`, `asia_pdl_fade`, `orb_crypto_london`,
  `metal_session_reversion`, `liq_asia_up_low_metal`, `vss_fxcross_london_up_low`,
  `ny_crypto_momentum`, `kz_london_crypto_low`, `ny_index_momentum` — differ by
  **exactly** the `_hour`/`_day`/`_hm` helper and nothing else. Mainline routes
  them through `_server_clock` (FTMO server wall clock = `America/New_York + 7h`);
  the deployed lineage compares raw **UTC** hours against constants that are
  server hours. In the K1-b window that is a flat **+3 h** shift of every session
  window, so a replay of mainline against a live record made by the deployed
  lineage compares a London window that opens at 05:00 UTC against one that opened
  at 08:00 UTC. Eight of the nine are in the deployed candidate allowlist
  (`config/agent_config.yaml:1274-1283`); `ny_index_momentum` is not.
* **One** — `fx_jpy` — differs in its own `_to_server_local`, which used the
  **EU** (EET/EEST last-Sunday) DST calendar where mainline uses the measured
  **US** one. That is inert in the K1-b window (both read +3 all summer) and
  1 h wrong for ~28 days a year. It is registered here anyway, because
  `metals.py:157` imports `_to_server_local` from it **at call time** — so the
  ARMED `metals_core`/`metals_softband` A8 `session_hour` feature runs on
  whichever calendar `fx_jpy` carries, and a replay of a window that crosses a
  divergence seam (the sealed March window 2026-03-08..03-28 is almost entirely
  inside one) would otherwise silently run mainline's clock for them.
  Registered after a refuter found the omission.

The seven K1 calls "first-of-day" are the nine minus the two K1 did not compare:
`ny_index_momentum` (zero rows in either namespace) and
`vss_fxcross_london_up_low` (55 FTMO rows, **all** of them `unit_skipped /
future_decision_bar_time` — generation-side refusals, never candidates).

What this module does
---------------------
It makes the lineage an explicit, declared input to a replay instead of an
accident of which checkout you are standing in. `deployed_lineage()` installs
the pre-B29 helpers into the nine sleeve modules for the duration of a block and
restores them exactly on exit, so the same port, the same bars and the same
driver can be run under either lineage and the difference attributed.

It is a **measurement instrument, not a repair**. Nothing here changes live
behaviour: it is inert unless a caller enters the context manager, it lives in
`research_infra`, and the direction of the repair (mainline is correct, the
deployed tree is not) is not in question — see `CLOCK_TRUTH_IMPACT_NOTE.md` and
`_server_clock.py`'s own docstring. Reproducing a defect is how you prove the
port does not have one.

Fail-closed
-----------
Activation asserts, behaviourally, that each target currently carries the
**mainline** helper (a summer UTC 05:00 stamp must read as server hour 8) and
that the swap actually took (it must then read as 5). A module that has already
been patched, or whose helper has been renamed, raises rather than silently
measuring nothing — that is the failure mode this whole finding is about.
"""

from __future__ import annotations

import calendar
import contextlib
import importlib
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator, Mapping, Optional

SCHEMA = "gtos.phase5.replay_policy.generation_lineage.v1"

#: The lineage the live FTMO/redacted_account books were running for the whole K1-b
#: window. Verified two ways: `git show redacted_host:<path>` and the read-only
#: export `vps-export-20260725/extracted/20_src/...` and
#: `.../13_packet_repo/src/...` are byte-identical for all nine sleeves.
DEPLOYED = "vps_redacted_host"
#: This checkout, i.e. post-B29 with the F7 clock repair.
MAINLINE = "mainline"

_SLEEVE_PKG = "src.components.ultimate_book.sleeves"


# ---------------------------------------------------------------------------
# the pre-B29 helpers, transcribed verbatim from redacted_host
# ---------------------------------------------------------------------------
def pre_b29_hour(t):
    """`_hour` as the deployed lineage implements it: the **UTC** hour."""
    if t is None:
        return None
    if hasattr(t, "hour"):
        return t.hour
    s = str(t)
    return int(s[11:13]) if len(s) >= 13 else None


def pre_b1200_utc_hour(t):
    """`substrate._utc_hour` exactly as it stood at redacted_host, before B1200.

    Transcribed separately from `pre_b29_hour` rather than reused, for the reason
    `pre_b29_hour_vss` records: the deployed bodies differ off the happy path and a shim that
    behaves differently there is not the same program. This one normalises a tz-aware stamp with
    `astimezone(utc)` (so a non-UTC tz-aware input still yields the UTC hour) and does **not**
    parse strings at all — `.hour` on a string raises, where `pre_b29_hour` would slice it.
    """
    if t is None:
        return None
    tz = getattr(t, "tzinfo", None)
    if tz is not None:
        return t.astimezone(timezone.utc).hour
    return t.hour


def pre_b29_day(t):
    """`_day` as the deployed lineage implements it: the **UTC** calendar date."""
    if t is None:
        return None
    if hasattr(t, "date"):
        return t.date().isoformat()
    return str(t)[:10]


def pre_b29_hour_minute(t):
    """`_hm` as the deployed lineage implements it: the **UTC** (hour, minute)."""
    if t is None:
        return None, None
    if hasattr(t, "hour"):
        return t.hour, t.minute
    s = str(t)
    return (int(s[11:13]), int(s[14:16])) if len(s) >= 16 else (None, None)


def pre_b29_hour_vss(t):
    """`vss_fxcross_london_up_low._hour`, which is the one of the nine that guarded its
    string parse. Identical to `pre_b29_hour` for the tz-aware datetimes `bar_provider`
    actually supplies; transcribed separately because the deployed behaviour on a malformed
    string is *fail closed*, not *raise*, and a shim that crashes where the original
    returned None is not the same program. Found by a refuter."""
    if t is None:
        return None
    if hasattr(t, "hour"):
        return t.hour
    s = str(t)
    if len(s) < 13:
        return None
    try:
        return int(s[11:13])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# the pre-F7 EU DST calendar, transcribed verbatim from redacted_host's fx_jpy.py
# ---------------------------------------------------------------------------
def _eu_last_sunday_0100_utc(year: int, month: int) -> datetime:
    """UTC instant of the EU DST switch in `month` (01:00 UTC on its last Sunday)."""
    last_day = calendar.monthrange(year, month)[1]
    d = datetime(year, month, last_day, 1, 0, tzinfo=timezone.utc)
    return d - timedelta(days=(d.weekday() - 6) % 7)


def pre_f7_to_server_local(bar_time) -> Optional[datetime]:
    """`fx_jpy._to_server_local` as the deployed lineage implements it: the **EU**
    EET/EEST calendar (+3 between the last Sundays of March and October, else +2)."""
    if not isinstance(bar_time, datetime):
        return None
    u = bar_time if bar_time.tzinfo is not None else bar_time.replace(tzinfo=timezone.utc)
    u = u.astimezone(timezone.utc)
    start = _eu_last_sunday_0100_utc(u.year, 3)
    end = _eu_last_sunday_0100_utc(u.year, 10)
    hours = 3 if start <= u < end else 2
    return (u + timedelta(hours=hours)).replace(tzinfo=None)


#: module -> {attribute: deployed-lineage implementation}.
#: Every sleeve module whose redacted_host <-> HEAD diff carries a clock change.
#: `test_replay_policy_generation_lineage.py` asserts this set equals
#: `clock_dependent_sleeves()`, so a further sleeve cannot join the clock repair
#: without this register being updated. The first version of this register was
#: keyed on `_server_clock` importers alone and therefore MISSED `fx_jpy` — which
#: is the entry that reaches an armed sleeve. Do not narrow the invariant again.
DEPLOYED_HELPERS: Mapping[str, Mapping[str, Any]] = {
    "asian_fade": {"_hour": pre_b29_hour, "_day": pre_b29_day},
    "asia_pdl_fade": {"_hour": pre_b29_hour, "_day": pre_b29_day},
    "orb_crypto_london": {"_hour": pre_b29_hour, "_day": pre_b29_day},
    "metal_session_reversion": {"_hour": pre_b29_hour, "_day": pre_b29_day},
    "liq_asia_up_low_metal": {"_hour": pre_b29_hour, "_day": pre_b29_day},
    "vss_fxcross_london_up_low": {"_hour": pre_b29_hour_vss},
    "ny_crypto_momentum": {"_hm": pre_b29_hour_minute},
    "kz_london_crypto_low": {"_hm": pre_b29_hour_minute},
    "ny_index_momentum": {"_hm": pre_b29_hour_minute},
    # reaches fx_jpy, fx_jpy_ny AND (via metals.py:157's call-time import)
    # metals_core / metals_softband.
    "fx_jpy": {"_to_server_local": pre_f7_to_server_local},
    # registry-orphan at both lineages, but its FILE exists at redacted_host with the raw-UTC
    # `_hour` (byte-identical in shape to `pre_b29_hour`); Session AK's B950 repair moved it
    # to `_server_clock` at HEAD. Registered at the wave-8 train merge, when the coverage
    # guard demanded it.
    "structural_retest": {"_hour": pre_b29_hour},
    # `sub_mid_dn_revert`'s `session=ny` cell condition. The FILE exists at redacted_host carrying the
    # raw-UTC `_utc_hour`; Session AM's B1200 repair renamed it `_session_hour` and routed it
    # through `_server_clock`, which makes this module a clock owner. Registered here rather than in
    # NO_DEPLOYED_LINEAGE because the deployed behaviour EXISTS and is reproducible.
    "substrate": {"_session_hour": pre_b1200_utc_hour},
}

#: Clock-owning sleeves with NO deployed lineage: they postdate redacted_host entirely, so there is
#: no pre-repair behaviour to transcribe and nothing for a live-lineage replay to reproduce — a
#: replay of the deployed lineage must generate NOTHING for these. Added at the wave-8 train
#: merge, for `session_leadlag`, which Session AK shipped born on the repaired clock —
#: `structural_retest`, whose FILE predates the lineage cutoff, sits in DEPLOYED_HELPERS with
#: its raw-UTC `_hour` transcribed instead. The coverage test asserts
#: `DEPLOYED_HELPERS | NO_DEPLOYED_LINEAGE == clock_dependent_sleeves()` with the two disjoint,
#: so a new clock-owning sleeve still cannot appear without being classified — it just has two
#: honest classifications now instead of one.
NO_DEPLOYED_LINEAGE: frozenset = frozenset({"session_leadlag"})

#: Behavioural activation guards, per helper shape. Both probes are summer
#: instants inside the K1-b window, where server = NY+7 = UTC+3.
#:
#:   `_hour`/`_hm`  05:00 UTC -> server hour 8 (mainline) vs UTC hour 5 (deployed)
#:   `_day`         22:00 UTC -> server day 07-09 (mainline) vs UTC day 07-08
#:                  (deployed) — the 05:00 probe cannot separate them, because
#:                  a +3 h shift does not cross midnight there.
#:
#: These are behavioural probes, not source-string matches: a helper that has
#: been renamed or re-implemented is caught by what it returns.
_PROBE_HOUR = datetime(2026, 7, 8, 5, 0, tzinfo=timezone.utc)
_PROBE_DAY = datetime(2026, 7, 8, 22, 0, tzinfo=timezone.utc)
#: `_to_server_local` differs only on a DST seam, so its probe MUST sit inside
#: one. 2026-03-10 is after the US switch (Mar 8) and before the EU one (Mar 29):
#: mainline +3, the deployed EU calendar +2. A summer probe would pass under both
#: and certify nothing.
_PROBE_SEAM = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)

#: attribute -> (probe, mainline expectation, deployed expectation)
_GUARDS: Mapping[str, tuple[datetime, Any, Any]] = {
    "_hour": (_PROBE_HOUR, 8, 5),
    "_hm": (_PROBE_HOUR, (8, 0), (5, 0)),
    "_day": (_PROBE_DAY, "2026-07-09", "2026-07-08"),
    "_to_server_local": (_PROBE_SEAM,
                         datetime(2026, 3, 10, 15, 0),
                         datetime(2026, 3, 10, 14, 0)),
    # `substrate._session_hour`, B1200. Same probe and same expectations as `_hour`: the mainline
    # reads server 8 and the deployed lineage reads UTC 5 at 05:00 UTC in summer.
    "_session_hour": (_PROBE_HOUR, 8, 5),
}


class LineageError(RuntimeError):
    """A lineage could not be installed, and refuses to measure under a guess."""


#: Set while a lineage is installed. Re-entry — nested, or from another thread —
#: is refused on this alone, not on a probe. An earlier revision took a public
#: ``verify=False`` that disabled the probes, and a refuter measured that this
#: made nested and cross-thread entry succeed **silently**: a caller could then
#: measure under a lineage it had not established. Probes cannot cover that case
#: anyway, because the second entry's post-swap probe reads the value the FIRST
#: entry installed and passes.
_ACTIVE: list[str] = []


@contextlib.contextmanager
def deployed_lineage() -> Iterator[dict]:
    """Run a block with the registered sleeves on the **deployed** clock.

    Yields a description of what was swapped, for the receipt. Both behavioural
    probes are mandatory and there is no way to switch them off.
    """

    if _ACTIVE:
        raise LineageError(
            f"lineage {_ACTIVE[-1]!r} is already installed; nesting or entering from a "
            f"second thread would measure under a lineage this caller did not establish")
    _ACTIVE.append(DEPLOYED)
    installed: list[tuple[Any, str, Any]] = []
    report: dict[str, Any] = {
        "schema": SCHEMA, "lineage": DEPLOYED, "modules": {},
        "probes": {a: g[0].isoformat() for a, g in _GUARDS.items()},
    }
    try:
        for name, attrs in DEPLOYED_HELPERS.items():
            mod = importlib.import_module(f"{_SLEEVE_PKG}.{name}")
            for attr, impl in attrs.items():
                current = getattr(mod, attr, None)
                if current is None:
                    raise LineageError(
                        f"{name}.{attr} does not exist; the lineage register is stale")
                guard = _GUARDS.get(attr)
                if guard is None:
                    raise LineageError(
                        f"{name}.{attr} has no behavioural guard; add one to _GUARDS rather "
                        f"than swapping an attribute nothing can check")
                probe, want_main, want_deployed = guard
                before = current(probe)
                if before != want_main:
                    raise LineageError(
                        f"{name}.{attr} is not the mainline helper: probe read {before!r}, "
                        f"expected {want_main!r}. Already patched, or the clock repair "
                        f"has moved.")
                setattr(mod, attr, impl)
                installed.append((mod, attr, current))
                after = getattr(mod, attr)(probe)
                if after != want_deployed:
                    raise LineageError(
                        f"{name}.{attr} swap did not take: probe read {after!r}, expected "
                        f"{want_deployed!r}")
                report["modules"].setdefault(name, []).append(attr)
        yield report
    finally:
        for mod, attr, original in reversed(installed):
            setattr(mod, attr, original)
        if _ACTIVE:
            _ACTIVE.pop()


@contextlib.contextmanager
def lineage(name: str) -> Iterator[dict]:
    """`deployed_lineage()` for `DEPLOYED`; a no-op for `MAINLINE`."""
    if name == MAINLINE:
        yield {"schema": SCHEMA, "lineage": MAINLINE, "modules": {}}
        return
    if name != DEPLOYED:
        raise LineageError(f"unknown lineage {name!r}; expected {MAINLINE!r} or {DEPLOYED!r}")
    with deployed_lineage() as report:
        yield report


#: Every way a sleeve module can acquire a broker-clock conversion. Keying the
#: invariant on `_server_clock` alone is what let `fx_jpy` — the only clock owner
#: an ARMED sleeve reaches — escape the register in the first revision.
_CLOCK_MARKERS = ("_server_clock import", "broker_clock import", "import broker_clock")

#: Modules that CONSUME another sleeve's clock helper instead of owning one, and
#: the owner that covers them. `metals.py:157` imports `_to_server_local` from
#: `fx_jpy` inside the function body, so swapping the owner's attribute reaches
#: it at call time; it needs no register entry of its own.
CLOCK_CONSUMERS: Mapping[str, str] = {"metals": "fx_jpy"}


def clock_dependent_sleeves() -> set[str]:
    """Sleeve modules that own a broker-clock conversion.

    Read from source rather than declared, so the register cannot drift away
    from the package.
    """

    import pathlib

    here = pathlib.Path(__file__).resolve()
    root = here.parents[2]  # .../src
    pkg = root / "components" / "ultimate_book" / "sleeves"
    out: set[str] = set()
    for path in sorted(pkg.glob("*.py")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in _CLOCK_MARKERS):
            out.add(path.stem)
    return out


def clock_consuming_sleeves() -> dict[str, str]:
    """`{module: owner}` for sleeves that import a clock helper from another sleeve.

    Derived from source, so a new consumer shows up as a register gap rather than
    as a silently unswapped sleeve.
    """

    import pathlib
    import re

    here = pathlib.Path(__file__).resolve()
    pkg = here.parents[2] / "components" / "ultimate_book" / "sleeves"
    out: dict[str, str] = {}
    pattern = re.compile(r"from \.(\w+) import [^\n]*_to_server_local")
    for path in sorted(pkg.glob("*.py")):
        if path.name.startswith("_"):
            continue
        hit = pattern.search(path.read_text(encoding="utf-8"))
        if hit and hit.group(1) != path.stem:
            out[path.stem] = hit.group(1)
    return out
