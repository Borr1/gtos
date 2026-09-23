"""Sleeve -> broker-symbol universe, resolved through the production path only.

`GateSpec.sleeve_symbol_allowlist` makes a sleeve's NAME falsifiable: the fidelity register
keys on the name alone, so relabelling a 30%-live-recall first-of-day sleeve as a per-bar
one walks straight past the fidelity gate. An adversarial refuter did exactly that. Checking
the trades' symbols against what the sleeve is actually registered to trade catches it.

This module is deliberately the only place in the package that touches config, because it
is the only place that needs to cross the canonical -> broker boundary. It crosses it with
`symbol_map.build_broker_symbol_resolver`, never by hand — the failure mode being avoided is
recorded in `WAVE_5_WORKING_AGREEMENT.md` section 3: an agent probed `mt5.symbol_info` on
canonical names, bypassed the resolver, and reported `energy_agri` at 0/2 and
`sub_xvol_pullback` at 6/18 when both are at full surface. Those wrong numbers nearly killed
two sleeves of a funded book.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

__all__ = ["build_symbol_allowlist", "live_registry"]

REPO = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO / "config/agent_config.yaml"
DEFAULT_PROFILE = REPO / "config/profiles/operator_profile.yaml"


def _load(config_path: Path | str | None, profile_path: Path | str | None) -> tuple[dict, dict]:
    import yaml  # lazy: the rest of the package needs no yaml

    base = yaml.safe_load(open(config_path or DEFAULT_CONFIG)) or {}
    prof = yaml.safe_load(open(profile_path or DEFAULT_PROFILE)) or {}
    return base, prof


def live_registry(
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    """The effective sleeve registry, resolved exactly as the live bridge assembles it.

    Calls `admission.effective_registry` with the flags `book_engine` reads, including the
    market-expansion POLICY resolution — the step whose omission produced 20 sleeves
    instead of 29 in an earlier session. Returns `{name: SleeveSpec}`.
    """
    from src.components.ultimate_book.admission import effective_registry
    from src.components.ultimate_book.book_engine import (
        _candidate_book_sleeves,
        _market_expansion_sleeves,
    )

    base, _ = _load(config_path, None)
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    return effective_registry(
        include_clean3=bool(cfg.get("ultimate_book_include_clean3", False)),
        include_clean4=bool(cfg.get("ultimate_book_include_clean4", False)),
        include_candidate_book=bool(cfg.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
        include_market_expansion_book=bool(
            cfg.get("ultimate_book_include_market_expansion_book", False)
        ),
        market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
    )


def build_symbol_allowlist(
    config_path: Path | str | None = None,
    profile_path: Path | str | None = None,
) -> dict[str, tuple[str, ...]]:
    """`{sleeve: (broker_symbol, ...)}` for every sleeve the live config resolves.

    Hand the result to `GateSpec(sleeve_symbol_allowlist=...)`. Sleeves absent from the map
    are not checked — the gate records that the check was skipped rather than passing it
    silently.
    """
    _, prof = _load(config_path, profile_path)
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver

    resolve = build_broker_symbol_resolver(prof)
    out: dict[str, tuple[str, ...]] = {}
    for name, spec in live_registry(config_path).items():
        symbols = tuple(getattr(spec, "symbols", ()) or ())
        out[name] = tuple(sorted({resolve(s) for s in symbols}))
    return out
