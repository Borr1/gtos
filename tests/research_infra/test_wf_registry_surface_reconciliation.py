"""Registry universe vs generator surface — pinned, so it cannot drift silently again.

`FOURTH_REVIEW.md` §3.1 reads `energy_agri`'s 4-symbol registry against its 2-symbol
generator as a per-sleeve **wiring defect** ("CORN/COTTON are sized-for but can never
fire"), and §3.2 reads `idxrev`'s 8-vs-5 the same way. Measured through the production
resolvers on 2026-07-29 (B604), both halves of that reading need amending:

  * It is **four** sleeves, not two — `sub_mid_dn_revert` and `sub_xvol_pullback` diverge
    identically, and the last of those is one of the three ARMED sleeves.
  * They are not **sized**-for. `SleeveSpec.symbols` has no consumer in any sizing or
    admission path: repo-wide, the core registry's `.symbols` is read only by
    `scripts/w7_live_forensics.py:127`, `scripts/w7_packet_forensics.py:161` and
    `walkforward/registry.build_symbol_allowlist`. Nothing in `admit_and_size` reads it.
  * All four divergences have the same cause and it is deliberate: the registry carries the
    AUTHORED universe and the generator carries the TRADEABLE one after the W7 tick-truth
    and spread-wall exclusions (`substrate.py:51` for the clean-3 pair, the sleeve
    docstrings for the other two).

So the defect is a naming collision — two different universes wearing one field name —
with one real consequence: `build_symbol_allowlist` hands the gate the WIDER universe, so
the gate's symbol-consistency check is loose (it cannot raise a false mismatch, and it
would not catch a generator that started firing on CORN either).

This test pins the exact divergence set with its reason. If a fifth sleeve diverges, or a
listed one stops, someone has changed a universe and must say which one they meant.
"""

from __future__ import annotations

import pytest
import yaml

from src.components.ultimate_book.admission import effective_registry
from src.components.ultimate_book.book_engine import (
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.sleeves.registry import active_specs

#: sleeve -> (registry-only symbols, why the generator excludes them)
KNOWN_DIVERGENCES = {
    "energy_agri": (
        ("CORN_c", "COTTON_c"),
        "live tick spread put CORN/COTTON over the 0.20R untradeable wall "
        "(sleeves/energy_agri.py:8-10)",
    ),
    "idxrev": (
        ("EU50_cash", "FRA40_cash", "US2000_cash"),
        "no bars and no measured spread for these three in the archive; the generator "
        "surface is the 5 indices that can be priced",
    ),
    "sub_mid_dn_revert": (
        ("HEATOIL_c", "NATGAS_cash"),
        "W7 tick-truth ENERGY_DROPPED_SYMBOLS, filtered at sleeves/substrate.py:51",
    ),
    "sub_xvol_pullback": (
        ("HEATOIL_c", "NATGAS_cash"),
        "W7 tick-truth ENERGY_DROPPED_SYMBOLS, filtered at sleeves/substrate.py:51",
    ),
}


def _surfaces():
    cfg = dict(yaml.safe_load(open("config/agent_config.yaml")).get("gtos_vnext_runtime") or {})
    cfg["ultimate_book_include_clean3"] = True
    specs = {
        s.tag: s
        for s in active_specs(
            None,
            include_candidate_book=True,
            candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
            include_market_expansion_book=True,
            market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
        )
    }
    reg = effective_registry(
        include_clean3=True, include_candidate_book=True, include_market_expansion_book=True
    )
    return reg, specs


def test_the_divergence_set_is_exactly_the_four_known_ones():
    reg, specs = _surfaces()
    found = {}
    for name, spec in sorted(reg.items()):
        gen = specs.get(name)
        if gen is None:
            continue
        only_reg = tuple(sorted(set(spec.symbols) - set(gen.on_surface)))
        only_gen = tuple(sorted(set(gen.on_surface) - set(spec.symbols)))
        # A generator firing on a symbol the registry does not carry would be the
        # dangerous direction, and there is none today.
        assert not only_gen, (
            f"{name}: generator fires on {only_gen} which the registry does not carry. "
            f"That direction is a real defect — the registry is what every forensic "
            f"report and the gate's allowlist read."
        )
        if only_reg:
            found[name] = only_reg
    assert found == {k: v[0] for k, v in KNOWN_DIVERGENCES.items()}, (
        f"registry-vs-generator surface set changed: {found!r}. Update "
        f"KNOWN_DIVERGENCES with the measured reason, or reconcile the universe."
    )


def test_registry_symbols_have_no_sizing_consumer():
    """The `sized-for` half of the §3.1 reading, tested rather than asserted.

    Sizing reads confidence and the intents' own symbols; it never reads the registry
    universe. If that ever changes, this test fails and the divergence above stops being
    documentation drift and becomes a real sizing defect.
    """
    import inspect

    from src.components.ultimate_book import admission as A

    src = inspect.getsource(A.admit_and_size)
    assert ".symbols" not in src, (
        "admit_and_size now reads a SleeveSpec universe. The four registry-vs-generator "
        "divergences pinned above would become live sizing errors; reconcile them first."
    )


@pytest.mark.parametrize("sleeve", sorted(KNOWN_DIVERGENCES))
def test_every_divergence_carries_a_measured_reason(sleeve):
    _syms, why = KNOWN_DIVERGENCES[sleeve]
    assert why and (".py:" in why or "archive" in why), (
        f"{sleeve}'s divergence has no file-cited reason; an unexplained universe "
        f"difference is the thing this file exists to prevent."
    )
