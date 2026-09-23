"""The single source of truth for "which sleeves are armed".

Why this module exists
----------------------
Three wave-20 artifacts each hard-coded the armed set as a four-tuple from memory
(``r1_estate_rewalk.py``'s ``ARMED`` tuple, ``R2_RESULT_V1.json -> live_isolation``,
``tests/test_broad_origin_emission_repairs.py``) and **all three were wrong the same
way**: they omitted ``sub_mid_dn_revert``, which is armed on both accounts, and
included ``mx_btcusd_d1_donchian_20_breakout``, which the owner disarmed on
2026-08-05. The omission was the expensive half -- ``sub_mid_dn_revert`` is the
armed sleeve that lane r1's quote-side repair moves most in proportion (-59.6 % of
its published gross) and it never entered r1's fold or p-value receipts.

Nothing in the estate could have caught that, because there was nowhere to look it
up. There is now:

* ``config/live_armed_set.json`` is the **declaration** -- the owner-decision side,
  with the receipt for every arming and disarming.
* ``scripts/run_book_supervisor.ps1`` is the **mechanism** -- the file that actually
  supplies ``run_book.py --tags``. There is no ``confidence_floor`` key anywhere in
  the tree and no floor can express the armed set (``admission.py:218-219``:
  ``sub_xvol_pullback`` is 0.45 while the killed ``metals_softband`` is 0.50), so
  ``--tags`` *is* the arming mechanism.
* :func:`reconcile` compares them and :mod:`tests.safety.test_armed_set_single_source`
  fails the build when they disagree.

Read :func:`armed_sleeves` for the answer; read :func:`reconcile` before believing it.

Modelling notes that are safety properties, not conveniences
------------------------------------------------------------
``--tags ""`` is **fail-open**: ``run_book.py:383`` reads
``tuple(...) if args.tags else None``, so an empty string is falsy and the book runs
every BUILT sleeve. An empty tag list is therefore *unbounded*, never *empty*, and
this module represents it as ``tags=None`` so that a caller cannot mistake a
fail-open launcher for a zero-sleeve one.

``--tags`` can only ever **subset**: ``book_engine.py:452-453`` intersects it with the
include-flag registry, so it can never add back a sleeve the config removed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

__all__ = [
    "AccountArming",
    "ArmedSetDisagreement",
    "LAUNCHER_PATH",
    "MANIFEST_PATH",
    "armed_sleeves",
    "declared_arming",
    "launcher_arming",
    "parse_launcher",
    "reconcile",
]

_REPO_ROOT = Path(__file__).resolve().parents[2]

#: The mechanism: the file that supplies ``run_book.py --tags`` on the host.
LAUNCHER_PATH = _REPO_ROOT / "scripts" / "run_book_supervisor.ps1"

#: The declaration: the owner-decision side, with a receipt per change.
MANIFEST_PATH = _REPO_ROOT / "config" / "live_armed_set.json"

#: ``tags`` sentinel meaning "the launcher passed nothing, so the book runs every
#: BUILT sleeve". Distinct from an empty tuple, which cannot occur.
UNBOUNDED = None


#: The two kinds of decision surface a launcher row can be.
#:
#: ``production`` is the armed book: the production risk dial, broker identity
#: ``MAGIC_NUMBER``, and every sleeve in it is an owner arming decision at full size.
#: ``experiment`` is a minimal-size surface -- ``run_book.py --f5-minimal-size-usd``, a
#: fixed dollar risk per trade, its own broker identity and its own namespace. The two are
#: modelled separately because *"which sleeves are armed"* means the first one: every
#: consumer of :func:`armed_sleeves` is asking about money at the production dial, and
#: silently folding a 32-sleeve $10 surface into that union would answer a different
#: question with the same words -- which is precisely the class of error this module exists
#: to prevent.
SURFACE_PRODUCTION = "production"
SURFACE_EXPERIMENT = "experiment"


@dataclass(frozen=True)
class AccountArming:
    """What one live worker is launched with."""

    namespace: str
    profile: str
    #: ``None`` means UNBOUNDED -- the ``--tags`` fail-open. Never an empty tuple.
    tags: tuple[str, ...] | None
    frontier_exits: tuple[str, ...] = ()
    spread_geometry_floor: tuple[str, ...] = ()
    #: ``production`` or ``experiment``; see :data:`SURFACE_PRODUCTION`.
    surface: str = SURFACE_PRODUCTION
    #: The fixed dollar risk per trade, for an experiment surface. ``None`` on production.
    minimal_size_usd: str | None = None

    @property
    def is_fail_open(self) -> bool:
        """True when this worker would run every BUILT sleeve (``run_book.py:383``)."""

        return self.tags is None

    @property
    def is_experiment(self) -> bool:
        """True when this worker places at a fixed minimal size rather than the dial."""

        return self.surface == SURFACE_EXPERIMENT

    @property
    def armed(self) -> frozenset[str]:
        """The sleeves this worker can generate. Empty frozenset when fail-open --
        callers must check :attr:`is_fail_open` rather than reading emptiness as
        "nothing armed"."""

        return frozenset(self.tags or ())


@dataclass(frozen=True)
class ArmedSetDisagreement:
    """One way the mechanism and the declaration fail to agree."""

    kind: str
    namespace: str
    detail: str
    severity: str = "CRITICAL"

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return f"[{self.severity}] {self.kind} on {self.namespace}: {self.detail}"


_ROW_RE = re.compile(r"@\{\s*ns\s*=\s*\"(?P<ns>[^\"]+)\"(?P<body>.*?)\}", re.DOTALL)


def _row_field(body: str, key: str) -> str | None:
    """Read one ``key="value"`` out of a PowerShell hashtable row body.

    ``$null`` and an absent key both return ``None``; an explicit empty string
    returns ``""`` so that the fail-open case stays distinguishable from an absent
    argument (they behave identically at ``run_book.py:383``, but only one of them
    is a typo).
    """

    m = re.search(rf"(?:^|;)\s*{re.escape(key)}\s*=\s*(\"(?P<q>[^\"]*)\"|\$null)", body)
    if m is None:
        return None
    return m.group("q")


def _split_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def parse_launcher(text: str) -> dict[str, AccountArming]:
    """Parse the ``$books`` array out of the supervisor launcher.

    This reads the launcher's *argument list*, which is configuration, not an
    implementation -- so it is not the "grep the source for a substring" antipattern
    the engineering rules forbid. If the owner arms a sixth sleeve the parse changes
    and every consumer notices.
    """

    out: dict[str, AccountArming] = {}
    for m in _ROW_RE.finditer(text):
        ns = m.group("ns")
        body = m.group("body")
        raw_tags = _row_field(body, "tags")
        tags = _split_csv(raw_tags)
        # The surface is derived from the MECHANISM, not from a label: a row that supplies
        # `--f5-minimal-size-usd` IS a minimal-size surface whatever anyone wrote next to it.
        # `reconcile` then checks the declaration agrees, so mislabelling either side is a
        # build failure rather than a silent reclassification of real money.
        f5_size = _row_field(body, "f5Size")
        out[ns] = AccountArming(
            namespace=ns,
            profile=_row_field(body, "profile") or "",
            tags=tags if tags else UNBOUNDED,
            frontier_exits=_split_csv(_row_field(body, "frontier")),
            spread_geometry_floor=_split_csv(
                _row_field(body, "spreadFloor") or _row_field(body, "floor")
            ),
            surface=SURFACE_EXPERIMENT if f5_size else SURFACE_PRODUCTION,
            minimal_size_usd=f5_size,
        )
    return out


def launcher_arming(path: Path | str | None = None) -> dict[str, AccountArming]:
    """The mechanism side: what the committed launcher actually arms."""

    p = Path(path) if path is not None else LAUNCHER_PATH
    return parse_launcher(p.read_text(encoding="utf-8"))


def declared_arming(path: Path | str | None = None) -> dict[str, AccountArming]:
    """The declaration side: what ``config/live_armed_set.json`` says is armed."""

    p = Path(path) if path is not None else MANIFEST_PATH
    doc = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, AccountArming] = {}
    for ns, row in doc["accounts"].items():
        sleeves = tuple(row.get("armed_sleeves") or ())
        out[ns] = AccountArming(
            namespace=ns,
            profile=row.get("profile", ""),
            tags=sleeves if sleeves else UNBOUNDED,
            frontier_exits=tuple(row.get("frontier_exits") or ()),
            spread_geometry_floor=tuple(row.get("spread_geometry_floor") or ()),
            surface=str(row.get("surface") or SURFACE_PRODUCTION),
            minimal_size_usd=(str(row["minimal_size_usd"])
                              if row.get("minimal_size_usd") is not None else None),
        )
    return out


def manifest(path: Path | str | None = None) -> dict:
    """The raw declaration document, including its decision log."""

    p = Path(path) if path is not None else MANIFEST_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def armed_sleeves(account: str | None = None, *,
                  surface: str | None = SURFACE_PRODUCTION) -> frozenset[str]:
    """The armed sleeve names -- for one account, or the union across accounts.

    This is the function every research artifact, dossier and test should call
    instead of writing a tuple of names down. It reads the *declaration*, which is
    the owner-decision side; :func:`reconcile` is what guarantees the mechanism
    agrees with it, and the test suite runs that on every commit.

    The union defaults to :data:`SURFACE_PRODUCTION` -- **the armed book at the production
    dial**, which is what every caller of this function has ever meant by "armed". A
    minimal-size experiment surface runs a much wider sleeve list at a fixed few dollars a
    trade on its own broker identity, and folding it into this union would answer a
    different question with the same words. Pass ``surface=SURFACE_EXPERIMENT`` for that
    one, or ``surface=None`` for every worker the launcher starts.

    Naming a specific ``account`` returns that account's set regardless of surface: a
    namespace is unambiguous, so no default can mislead.
    """

    decl = declared_arming()
    if account is not None:
        return decl[account].armed
    out: set[str] = set()
    for row in decl.values():
        if surface is not None and row.surface != surface:
            continue
        out |= row.armed
    return frozenset(out)


def production_arming(
    rows: dict[str, AccountArming] | None = None,
) -> dict[str, AccountArming]:
    """Only the workers that trade at the production dial -- the armed book.

    Use this wherever the question is "what is trading real money at full size": the
    disarmed-sleeve guard, the survivor screens, the learning-lane re-rate, and every
    published economic figure.
    """

    src = rows if rows is not None else declared_arming()
    return {ns: row for ns, row in src.items() if row.surface == SURFACE_PRODUCTION}


def experiment_arming(
    rows: dict[str, AccountArming] | None = None,
) -> dict[str, AccountArming]:
    """Only the minimal-size experiment workers."""

    src = rows if rows is not None else declared_arming()
    return {ns: row for ns, row in src.items() if row.surface == SURFACE_EXPERIMENT}


def reconcile(
    launcher: dict[str, AccountArming] | None = None,
    declared: dict[str, AccountArming] | None = None,
) -> list[ArmedSetDisagreement]:
    """Every way the launcher and the declaration disagree. Empty list == consistent."""

    lau = launcher if launcher is not None else launcher_arming()
    dec = declared if declared is not None else declared_arming()
    problems: list[ArmedSetDisagreement] = []

    for ns in sorted(set(lau) | set(dec)):
        if ns not in lau:
            problems.append(ArmedSetDisagreement(
                "declared_account_absent_from_launcher", ns,
                "the manifest declares this account but the launcher starts no worker for it"))
            continue
        if ns not in dec:
            problems.append(ArmedSetDisagreement(
                "launcher_account_undeclared", ns,
                "the launcher starts a worker for an account the manifest does not declare"))
            continue
        L, D = lau[ns], dec[ns]
        if L.is_fail_open:
            problems.append(ArmedSetDisagreement(
                "launcher_tags_fail_open", ns,
                "the launcher passes no --tags (or an empty one), so this book runs EVERY "
                "BUILT sleeve -- run_book.py:383 treats an empty string as 'all'"))
            continue
        if D.is_fail_open:
            problems.append(ArmedSetDisagreement(
                "declaration_is_unbounded", ns,
                "the manifest declares no sleeves for this account"))
            continue
        if L.surface != D.surface:
            # The launcher's surface is derived from whether the row passes
            # `--f5-minimal-size-usd`, so this fires when the mechanism and the declaration
            # disagree about what KIND of surface an account is. Both directions are
            # dangerous and one is dangerous on real money: a production row that quietly
            # gained a minimal-size flag would place 1/200th lots while every published
            # figure, every survivor screen and every learning-lane recommendation still
            # priced it at the dial.
            problems.append(ArmedSetDisagreement(
                "surface_mismatch", ns,
                f"launcher runs this as a {L.surface} surface "
                f"(minimal_size_usd={L.minimal_size_usd!r}); the manifest declares "
                f"{D.surface}"))
        if L.armed != D.armed:
            extra = sorted(L.armed - D.armed)
            missing = sorted(D.armed - L.armed)
            problems.append(ArmedSetDisagreement(
                "armed_set_mismatch", ns,
                f"launcher arms {sorted(L.armed)}; manifest declares {sorted(D.armed)}"
                + (f"; launcher arms undeclared {extra}" if extra else "")
                + (f"; launcher omits declared {missing}" if missing else "")))
        if set(L.frontier_exits) != set(D.frontier_exits):
            problems.append(ArmedSetDisagreement(
                "frontier_exits_mismatch", ns,
                f"launcher --frontier-exits {sorted(L.frontier_exits)}; "
                f"manifest declares {sorted(D.frontier_exits)}"))
        if set(L.spread_geometry_floor) != set(D.spread_geometry_floor):
            problems.append(ArmedSetDisagreement(
                "spread_geometry_floor_mismatch", ns,
                f"launcher --spread-geometry-floor {sorted(L.spread_geometry_floor)}; "
                f"manifest declares {sorted(D.spread_geometry_floor)}",
                severity="HIGH"))
        stray = set(L.frontier_exits) - L.armed
        if stray:
            problems.append(ArmedSetDisagreement(
                "frontier_exit_for_unarmed_sleeve", ns,
                f"--frontier-exits names {sorted(stray)}, which is not in this worker's --tags"))

    return problems


def assert_consistent() -> None:
    """Raise if the launcher and the declaration disagree. Cheap enough to call
    from any research entrypoint that is about to publish an armed-money number."""

    problems = reconcile()
    if problems:
        raise AssertionError(
            "armed-set declaration and launcher disagree:\n  "
            + "\n  ".join(str(p) for p in problems))
