"""Mechanism families — one hypothesis over a symbol class, and the honest bill for it.

WHY A FAMILY IS A DIFFERENT HYPOTHESIS FROM ITS MEMBERS
--------------------------------------------------------
The estate's most common honest failure is significance: a real-looking per-symbol edge that
cannot pay a 69-look multiplicity bill on its own. `AA_ESTATE_WALK` produced 22 `BREADTH`
rows saying exactly that, each carrying the scoping multiple `(z_alpha / z_observed)**2`.

The Fundamental Law's answer is breadth, and it is a *statistical* answer, not a rhetorical
one. Pooling `k` members of equal information coefficient into one equal-weight
cross-sectional series scales the t-statistic by `sqrt(k)` — the mean stays put and the
standard error falls. So "does donchian-20 carry edge on the crypto class" is a strictly
more powerful question than "does donchian-20 carry edge on BTCUSD", and it is also a
*different* question, with its own answer and its own failure modes.

This module makes the pooled question askable through the same sealed gate, with three
disciplines that stop it being a laundering device:

1. **The family is defined by the SYMBOL CLASS, never by results.** `family_members` takes
   a mechanism and an asset class and returns every archive symbol in that class. A member
   may be dropped only for *data* (no bars, no priceable cost) and every drop is recorded
   in `FamilyGrid.dropped` with its reason. Dropping a loser and keeping a winner would make
   the pooled mean a selection statistic; the grid is built before any outcome is known.

2. **Pooling refuses to mix fidelity classes.** A first-of-day member pooled with per-bar
   members and stamped per-bar would launder the weaker stamp. `pool_family` raises.

3. **Every member-look is a look.** The member-level run and the family-level run are both
   hypotheses someone examined. `FamilyGrid.n_looks` is the number to hand
   `GateSpec.declared_family_size`, and every cell is written to the trial ledger by the
   caller. A family verdict that quotes only the number of *families* tested is quoting the
   cheaper of two bills it owes.

WHAT IS NOT HERE
----------------
Per-symbol allocation inside an admitted family. That is the diversifier door
(`walkforward.diversifier.certify_diversifier`, FOURTH_REVIEW §4.4) and it is wave-8 work.
An admitted family says "this mechanism has edge on this class"; it does not say how much
of the book each member should carry, and this module deliberately cannot answer that.
"""

from __future__ import annotations

import contextlib
import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Sequence

from src.research_infra.walkforward.fidelity import (
    EXPANSION_PREFIX,
    fidelity_for,
    register_surface_expansion,
)
from src.research_infra.walkforward.panel import TradeRecord

__all__ = [
    "ASSET_CLASS",
    "FamilyGrid",
    "FamilyMember",
    "MECHANISMS",
    "MechanismSpec",
    "expanded_surface",
    "fidelity_scope",
    "family_members",
    "member_name",
    "pool_family",
]

TF_NAME: dict[int, str] = {15: "M15", 16388: "H4", 16408: "D1"}


# ======================================================================================
# the mechanisms, detached from the symbols they were authored on
# ======================================================================================
@dataclass(frozen=True)
class MechanismSpec:
    """A generation rule, named independently of the symbol it happens to be wired to.

    `generate` is the PRODUCTION generator, obtained from the production factory. Nothing
    in this module re-derives a signal: `w_mx_pilot.py`'s header names re-implementation as
    "the failure mode that bit three agents this week" and that judgement stands.
    """

    #: Stable mechanism id. Part of every member name, so it is in the trial ledger.
    mechanism: str
    #: The authored sleeve whose rule this is. Fidelity transfers from it; it is also the
    #: parity reference — running the mechanism on the parent's own symbol must reproduce
    #: the parent's trades exactly.
    parent_sleeve: str
    #: Timeframe the rule was authored on. A member at any other timeframe is a VARIANT and
    #: says so in its row.
    authored_timeframe: int
    #: file:line establishing the rule and its structural fidelity class.
    source: str
    #: How the caller widens the production surface so `generate` will accept a new symbol.
    #: `None` means the rule accepts any symbol already.
    surface_widener: Callable[[Sequence[str]], Any] | None = None


def _mx_generator(mechanism: str) -> Callable[..., Any]:
    """A callable that runs one market-expansion D1 rule on whatever symbol it is given.

    The production `generate_for_tag` dispatches on a `(symbol, mechanism)` pair looked up
    from `TAG_TO_RULE`, so a rule cannot be pointed at a new symbol without an entry. The
    entry is installed by `expanded_surface`; this returns the production
    `generator_for(tag)` closure for it.
    """
    from src.components.ultimate_book.sleeves import market_expansion_d1 as _mx

    def _gen(member: str, symbol: str, bars, decision_day: str, **kw):
        if _mx.TAG_TO_RULE.get(member) != (symbol, mechanism):
            raise KeyError(
                f"{member!r} is not installed for ({symbol!r}, {mechanism!r}); wrap the call "
                f"in walkforward.family.expanded_surface(...)"
            )
        return _mx.generate_for_tag(member, symbol, bars, decision_day, **kw)

    return _gen


def _core_module(module_name: str):
    """The production sleeve module by name — imported, never fetched off a package attr."""
    import importlib

    return importlib.import_module(f"src.components.ultimate_book.sleeves.{module_name}")


def _core_generator(module_name: str) -> Callable[..., Any]:
    """A callable that runs one core-book H4 rule on whatever symbol it is given.

    `crypto.generate` and `energy_agri.generate` open with `if symbol not in ON_SURFACE`.
    That guard is the thing under test — the question is whether the RULE carries beyond the
    two symbols it was wired to — so `expanded_surface` widens the tuple for the duration of
    a sweep and restores it. The rule itself is untouched.
    """

    def _gen(member: str, symbol: str, bars, decision_day: str, **kw):
        mod = _core_module(module_name)
        if symbol not in mod.ON_SURFACE:
            raise KeyError(
                f"{symbol!r} is not on {module_name}.ON_SURFACE; wrap the call in "
                f"walkforward.family.expanded_surface(...)"
            )
        return mod.generate(symbol, bars, decision_day, **kw)

    return _gen


MECHANISMS: dict[str, MechanismSpec] = {
    "donchian_20_breakout": MechanismSpec(
        mechanism="d1_donchian_20_breakout",
        parent_sleeve="mx_btcusd_d1_donchian_20_breakout",
        authored_timeframe=16408,
        source="sleeves/market_expansion_d1.py:103-115 (_donchian_signal), :203-224",
    ),
    "volume_surge_reversal": MechanismSpec(
        mechanism="d1_volume_surge_reversal",
        parent_sleeve="mx_us30_cash_d1_volume_surge_reversal",
        authored_timeframe=16408,
        source="sleeves/market_expansion_d1.py:129-144 (_volume_surge_signal), :207-224",
    ),
    "atr_mean_reversion": MechanismSpec(
        mechanism="d1_atr_mean_reversion",
        parent_sleeve="mx_us500_cash_d1_atr_mean_reversion",
        authored_timeframe=16408,
        source="sleeves/market_expansion_d1.py:118-126 (_atr_mean_reversion_signal), :205-224",
    ),
    "crypto_h4_donchian_ac60": MechanismSpec(
        mechanism="h4_donchian_20_ac60_4r",
        parent_sleeve="crypto",
        authored_timeframe=16388,
        source="sleeves/crypto.py:31-66 — donchian-20 H4 + ac60>=0.15, sd=2*ATR, 4R",
    ),
    "energy_fvg_retest": MechanismSpec(
        mechanism="h4_fvg_retest_energy_gate",
        parent_sleeve="energy_agri",
        authored_timeframe=16388,
        source="sleeves/energy_agri.py:47-63 — metals FVG retest + energy state gate, 4R",
    ),
}

#: Which production module each core mechanism's surface lives on.
_CORE_MODULE: dict[str, str] = {
    "crypto_h4_donchian_ac60": "crypto",
    "energy_fvg_retest": "energy_agri",
}


# ======================================================================================
# the symbol classes — declared before any outcome is seen
# ======================================================================================
#: Canonical archive symbol -> asset class. This is the family partition and it is
#: PRE-SPECIFIED: a family is "mechanism x class", so which symbols are in a family is fixed
#: by what the instrument IS, never by what it earned. Classes follow the broker's own
#: instrument grouping (`BROKER_SYMBOL_SPEC_COMPARISON.json`) and the estate's existing
#: sleeve clusters (`sleeves/registry.py` cluster names).
ASSET_CLASS: dict[str, str] = {
    # crypto (9)
    "ADAUSD": "crypto", "AVAUSD": "crypto", "BTCUSD": "crypto", "DASHUSD": "crypto",
    "DOTUSD": "crypto", "ETHUSD": "crypto", "LTCUSD": "crypto", "XRPUSD": "crypto",
    "XTZUSD": "crypto",
    # equity index (6 unique instruments; GER40_cash and JP225_cash are the same broker
    # instrument re-exported under a second canonical name — see FamilyGrid.dropped)
    "GER40": "index", "JP225": "index", "NAS100": "index", "SPX500": "index",
    "UK100": "index", "US30_cash": "index",
    "GER40_cash": "index", "JP225_cash": "index",
    # metals (9)
    "XAGAUD": "metal", "XAGEUR": "metal", "XAGUSD": "metal", "XAUAUD": "metal",
    "XAUEUR": "metal", "XAUUSD": "metal", "XCUUSD": "metal", "XPDUSD": "metal",
    "XPTUSD": "metal",
    # energy (3)
    "NATGAS_cash": "energy", "UKOIL_cash": "energy", "USOIL_cash": "energy",
    # fx (14)
    "AUDJPY": "fx", "AUDUSD": "fx", "CADJPY": "fx", "CHFJPY": "fx", "EURGBP": "fx",
    "EURJPY": "fx", "EURUSD": "fx", "GBPJPY": "fx", "GBPUSD": "fx", "NZDJPY": "fx",
    "NZDUSD": "fx", "USDCAD": "fx", "USDCHF": "fx", "USDJPY": "fx",
}


# ======================================================================================
# members and grids
# ======================================================================================
def member_name(mechanism_key: str, symbol: str, timeframe: int) -> str:
    """`mxf_<mechanism>_<symbol>_<tf>` — the sleeve name a family member is judged under."""
    tf = TF_NAME.get(int(timeframe), str(timeframe))
    return f"{EXPANSION_PREFIX}{mechanism_key}_{symbol}_{tf}".lower()


@dataclass(frozen=True)
class FamilyMember:
    member: str
    mechanism_key: str
    #: The rule's own id inside `market_expansion_d1` / the core sleeve.
    mechanism: str
    parent_sleeve: str
    #: Canonical (archive/registry) symbol.
    symbol: str
    #: BROKER symbol — what `cost_r` and the bar series are keyed on.
    broker_symbol: str
    timeframe: int
    asset_class: str
    #: True when this member is the rule on the symbol AND timeframe it was authored for.
    is_authored_cell: bool
    #: True when the live FTMO profile carries an instrument config for the symbol. A member
    #: that clears the gate but is False here needs a profile entry before it could ever be
    #: armed — that is a wiring item, not a research one, and it is reported not hidden.
    profile_supported: bool

    @property
    def family(self) -> str:
        return f"fam_{self.mechanism_key}_{self.asset_class}_{TF_NAME.get(self.timeframe, self.timeframe)}".lower()


@dataclass
class FamilyGrid:
    """The pre-specified sweep: every (mechanism, symbol, timeframe) cell, and every drop."""

    members: list[FamilyMember] = field(default_factory=list)
    #: (cell_id, reason) for everything the grid could not include. NO SILENT CAPS.
    dropped: list[tuple[str, str]] = field(default_factory=list)

    @property
    def n_looks(self) -> int:
        """Member cells + distinct families. Both are hypotheses someone examined."""
        return len(self.members) + len(self.families())

    def families(self) -> dict[str, list[FamilyMember]]:
        out: dict[str, list[FamilyMember]] = {}
        for m in self.members:
            out.setdefault(m.family, []).append(m)
        return out

    def as_dict(self) -> dict[str, Any]:
        fams = self.families()
        return {
            "n_members": len(self.members),
            "n_families": len(fams),
            "n_looks": self.n_looks,
            "families": {
                f: {
                    "members": [m.member for m in ms],
                    "symbols": sorted(m.symbol for m in ms),
                    "mechanism": ms[0].mechanism,
                    "parent_sleeve": ms[0].parent_sleeve,
                    "asset_class": ms[0].asset_class,
                    "timeframe": TF_NAME.get(ms[0].timeframe, ms[0].timeframe),
                    "authored_timeframe": (
                        TF_NAME.get(MECHANISMS[ms[0].mechanism_key].authored_timeframe)),
                }
                for f, ms in sorted(fams.items())
            },
            "dropped": [{"cell": c, "reason": r} for c, r in self.dropped],
        }


def family_members(
    mechanism_keys: Sequence[str],
    timeframes: Sequence[int],
    *,
    symbols: Sequence[str],
    broker_symbol: Callable[[str], str],
    profile_supports: Callable[[str], bool] | None = None,
    classes: Sequence[str] | None = None,
) -> FamilyGrid:
    """Build the full cross. Complete by construction — no cell is chosen, all are taken.

    `symbols` is the archive's canonical symbol list. `classes`, when given, restricts to
    those asset classes; a symbol with no class entry is DROPPED with a reason rather than
    silently assigned one, because an unclassified symbol would land in a family whose
    membership nobody declared.
    """
    grid = FamilyGrid()
    want = set(classes) if classes else None
    for key in mechanism_keys:
        if key not in MECHANISMS:
            raise KeyError(f"unknown mechanism {key!r}; have {sorted(MECHANISMS)}")
        spec = MECHANISMS[key]
        for tf in timeframes:
            for sym in symbols:
                cell = f"{key}|{sym}|{TF_NAME.get(tf, tf)}"
                cls = ASSET_CLASS.get(sym)
                if cls is None:
                    grid.dropped.append((cell, "symbol has no declared asset class"))
                    continue
                if want is not None and cls not in want:
                    continue
                grid.members.append(FamilyMember(
                    member=member_name(key, sym, tf),
                    mechanism_key=key,
                    mechanism=spec.mechanism,
                    parent_sleeve=spec.parent_sleeve,
                    symbol=sym,
                    broker_symbol=broker_symbol(sym),
                    timeframe=int(tf),
                    asset_class=cls,
                    is_authored_cell=(int(tf) == spec.authored_timeframe),
                    profile_supported=(
                        bool(profile_supports(sym)) if profile_supports else True),
                ))
    return grid


# ======================================================================================
# widening the production surface, reversibly
# ======================================================================================
@contextlib.contextmanager
def expanded_surface(members: Iterable[FamilyMember]) -> Iterator[dict[str, Callable]]:
    """Install `members` on the production generators, yield their callables, restore.

    Yields `{member_name: generate(symbol, bars, decision_day, **kw)}`.

    Two production maps are widened and both are restored on exit, including on exception:

      * `market_expansion_d1.TAG_TO_RULE` gains one `(symbol, mechanism)` entry per
        market-expansion member. That map is the rule's own dispatch table — adding a pair
        to it is how the fourteen authored tags are themselves declared
        (`market_expansion_d1.py:30-45`), so a member added this way runs the identical code.
      * `crypto.ON_SURFACE` / `energy_agri.ON_SURFACE` gain the swept symbols. The surface
        guard is the thing under test; the rule below it is untouched.

    Fidelity records for the members are registered on entry and cleared on exit, so a
    member cannot outlive its sweep and be scored later under a stamp nobody re-derived.
    """
    from src.components.ultimate_book.sleeves import market_expansion_d1 as _mx
    from src.research_infra.walkforward import fidelity as _fid

    members = list(members)
    saved_tags = dict(_mx.TAG_TO_RULE)
    saved_surfaces: dict[str, tuple[str, ...]] = {}
    try:
        gens: dict[str, Callable] = {}
        for m in members:
            spec = MECHANISMS[m.mechanism_key]
            mod_name = _CORE_MODULE.get(m.mechanism_key)
            if mod_name is None:
                _mx.TAG_TO_RULE[m.member] = (m.symbol, spec.mechanism)
                inner = _mx_generator(spec.mechanism)
            else:
                mod = _core_module(mod_name)
                if mod_name not in saved_surfaces:
                    saved_surfaces[mod_name] = tuple(mod.ON_SURFACE)
                if m.symbol not in mod.ON_SURFACE:
                    mod.ON_SURFACE = tuple(mod.ON_SURFACE) + (m.symbol,)
                inner = _core_generator(mod_name)
            gens[m.member] = _bind(inner, m.member)
            _fid.register_surface_expansion(
                m.member, parent=m.parent_sleeve, symbol=m.symbol,
                timeframe=TF_NAME.get(m.timeframe, str(m.timeframe)),
                surface_note=(
                    "authored cell" if m.is_authored_cell
                    else f"TIMEFRAME VARIANT: rule authored on "
                         f"{TF_NAME.get(spec.authored_timeframe)}"),
            )
        yield gens
    finally:
        _mx.TAG_TO_RULE.clear()
        _mx.TAG_TO_RULE.update(saved_tags)
        for mod_name, surf in saved_surfaces.items():
            _core_module(mod_name).ON_SURFACE = surf
        _fid.clear_surface_expansions()


@contextlib.contextmanager
def fidelity_scope(members: Iterable[FamilyMember], *, pooled: bool = True) -> Iterator[None]:
    """Register the members' (and their families') fidelity records for a scoring run.

    `expanded_surface` is for GENERATING; this is for SCORING trades that were generated
    earlier. The gate refuses any sleeve with no fidelity record (`gate.py:432-455`), which
    is correct and is exactly why the records have to be present — and equally why they are
    removed again on exit, so nothing can be scored later under a stamp nobody re-derived.

    A pooled family inherits the same parent as its members: it is the same rule, and
    `pool_family` has already refused to build it out of mixed classes.
    """
    from src.research_infra.walkforward import fidelity as _fid

    members = list(members)
    try:
        for m in members:
            _fid.register_surface_expansion(
                m.member, parent=m.parent_sleeve, symbol=m.symbol,
                timeframe=TF_NAME.get(m.timeframe, str(m.timeframe)),
                surface_note=("authored cell" if m.is_authored_cell else "timeframe variant"))
        if pooled:
            for f, ms in sorted(_by_family(members).items()):
                _fid.register_surface_expansion(
                    f, parent=ms[0].parent_sleeve,
                    symbol=f"{len(ms)} {ms[0].asset_class} symbols "
                           f"({', '.join(sorted(m.symbol for m in ms))})",
                    timeframe=TF_NAME.get(ms[0].timeframe, str(ms[0].timeframe)),
                    surface_note="POOLED FAMILY — one hypothesis over the whole class")
        yield
    finally:
        _fid.clear_surface_expansions()


def _by_family(members: Sequence[FamilyMember]) -> dict[str, list[FamilyMember]]:
    out: dict[str, list[FamilyMember]] = {}
    for m in members:
        out.setdefault(m.family, []).append(m)
    return out


def _bind(inner: Callable[..., Any], member: str) -> Callable[..., Any]:
    def _gen(symbol: str, bars, decision_day: str, **kw):
        return inner(member, symbol, bars, decision_day, **kw)

    _gen.__name__ = f"generate_{member}"
    return _gen


# ======================================================================================
# pooling
# ======================================================================================
def pool_family(
    family: str,
    trades_by_member: dict[str, Sequence[TradeRecord]],
    members: Sequence[FamilyMember],
) -> list[TradeRecord]:
    """The family's trades as ONE sleeve: an equal-weight cross-section of its members.

    Relabelling is all that happens. The gate's own `build_daily_panel` then takes the
    day-mean across whatever members traded that day (`GateSpec.day_aggregation`), which is
    exactly the equal-weight cross-sectional portfolio the Fundamental Law's `sqrt(k)` refers
    to — so the breadth gain is produced by the sealed panel code, not by anything here.

    Refuses to pool members of different fidelity classes: a pooled series whose stamp came
    from its best-attested member would be laundering, and the pooled hypothesis is only as
    strong as its weakest generator.
    """
    classes = {fidelity_for(m.member).cls for m in members}
    if len(classes) > 1:
        raise ValueError(
            f"{family}: refusing to pool members of different fidelity classes "
            f"{sorted(c.value for c in classes)} — the pooled verdict would carry a stamp no "
            f"single member earned"
        )
    tfs = {m.timeframe for m in members}
    if len(tfs) > 1:
        raise ValueError(
            f"{family}: refusing to pool members on different timeframes {sorted(tfs)} — "
            f"the day panel would mix one observation per day with six"
        )
    out: list[TradeRecord] = []
    for m in members:
        for t in trades_by_member.get(m.member, ()):  # noqa: PERF401 - explicit relabel
            out.append(TradeRecord(
                sleeve=family,
                symbol=t.symbol,
                entry_utc=t.entry_utc,
                exit_utc=t.exit_utc,
                direction=t.direction,
                sl_distance_price=t.sl_distance_price,
                entry_price=t.entry_price,
                r_gross=t.r_gross,
                features={**t.features, "member": m.member, "asset_class": m.asset_class},
            ))
    out.sort(key=lambda t: (t.entry_utc, t.symbol))
    return out


def family_composition_by_fold(
    trades: Sequence[TradeRecord], folds: Sequence[tuple[dt.date, dt.date]]
) -> list[dict[str, Any]]:
    """Which members actually contributed inside each fold.

    A pooled family is NOT constant-composition when its members' histories start at
    different dates — `ADAUSD` begins 2024-10 and `EURUSD` in 2000 — so an early fold can be
    one symbol wearing the family's name. That is honest (it is what a real portfolio would
    have held) and it is also exactly the thing a reader must be able to see, so it is
    published per fold rather than averaged away.
    """
    out = []
    for lo, hi in folds:
        inside = [t for t in trades if lo <= t.entry_utc.date() <= hi]
        mem: dict[str, int] = {}
        for t in inside:
            k = str(t.features.get("member", t.symbol))
            mem[k] = mem.get(k, 0) + 1
        out.append({
            "oos_start": lo.isoformat(), "oos_end": hi.isoformat(),
            "n_trades": len(inside), "n_members_firing": len(mem),
            "trades_by_member": dict(sorted(mem.items(), key=lambda kv: -kv[1])),
        })
    return out
