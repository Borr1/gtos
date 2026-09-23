#!/usr/bin/env python3
"""Slim ship-callable cross-asset direction resolver.

Peer panel in, +1 / −1 / 0 out. Importable on F5: no tensor, scipy, or core.py.
Does not import research-substrate. Fat research blob stays where it is.

    from xasset_direction import direction_resolver
    d = direction_resolver(setup_name, fire_bar, peer_panel)  # +1 / -1 / 0
    if d == 0:
        return None  # still timing

Prefer peer_panel={'aligned_move': float}. Packet-style {peer: atr_move} is a
scale-proxy. q4 → +1, q0 → −1, mid → 0, unready / only_ready=True → 0.

The nine MDE80-ready names ship geometry.py best_both_halves, not this side.
Coin-flip / up>=0.5 is refused for these nine.

Live generate() choice (WEEKEND-XA-SLEEVES): fire on the measured
geometry side. Resolver never flips it. Missing panel or resolver 0 is
a SIZE annotation (fire) because unconditioned geometry already
selected a side. If the resolver is available and disagrees, skip
(timing-only). Not armed.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

# Official discovery cuts (named peers + LOO class). Same digitize as research.
# q = 0 if x < cuts[0]; q = 4 if x >= cuts[3].
CUTS: tuple[float, float, float, float] = (
    -0.7046618461608887,
    -0.18597553670406342,
    0.2207496464252472,
    0.7553930282592773,
)
NQ = 5

# Nine that beat holdout MDE80 (BUILD-XASSET.md). The three that failed are absent.
READY_NAMES: frozenset[str] = frozenset((
    "wave_two_standing_bar_already_large",
    "already_huge_same_way_wave_two",
    "huge_bar_closed_on_20bar_extreme",
    "isolated_huge_bar_then_opposite",
    "already_huge_and_prior_huge_same_way",
    "climax_first_touch_20low_springs",
    "second_rth_bar_after_open_drive",
    "already_wide_bar_same_extreme",
    "second_leg_after_first_expansion",
))

# Existing DISPLACEMENT_BUILT tags. Do not invent new xa_* names.
TAG_TO_SETUP: dict[str, str] = {
    "xa_wave_two_standing": "wave_two_standing_bar_already_large",
    "xa_huge_same_way": "already_huge_same_way_wave_two",
    "xa_huge_20_extreme": "huge_bar_closed_on_20bar_extreme",
    "xa_isolated_opposite": "isolated_huge_bar_then_opposite",
    "xa_prior_huge": "already_huge_and_prior_huge_same_way",
    "xa_climax_spring": "climax_first_touch_20low_springs",
    "xa_second_rth": "second_rth_bar_after_open_drive",
    "xa_wide_extreme": "already_wide_bar_same_extreme",
    "xa_second_leg": "second_leg_after_first_expansion",
}

_SKIP_KEYS = frozenset((
    "aligned_move", "cx", "bodies", "own_body", "peer_bodies",
    "betas", "kbars", "aux_bars", "aux_times", "moves",
))


def canon_name(setup_name: str) -> str:
    return TAG_TO_SETUP.get(setup_name, setup_name)


def _finite(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return x


def _digitize(x: float, cuts: tuple[float, ...] = CUTS) -> int:
    """np.digitize(x, cuts) with right=False. No numpy."""
    q = 0
    for c in cuts:
        if x >= c:
            q += 1
        else:
            break
    return q


def _aligned_from_peer_panel(peer_panel: Mapping[str, Any] | None) -> float | None:
    if peer_panel is None:
        return None
    if "aligned_move" in peer_panel:
        return _finite(peer_panel["aligned_move"])
    if "cx" in peer_panel:
        return _finite(peer_panel["cx"])
    moves = peer_panel.get("moves")
    if moves is None and peer_panel and all(
        k not in _SKIP_KEYS and _finite(v) is not None
        for k, v in peer_panel.items()
    ):
        moves = dict(peer_panel)
    if not isinstance(moves, Mapping) or not moves:
        return None
    betas = peer_panel.get("betas") or {}
    parts: list[float] = []
    for name, mv in moves.items():
        if name in _SKIP_KEYS:
            continue
        x = _finite(mv)
        if x is None:
            continue
        b = _finite(betas.get(name, 1.0))
        if b is None:
            b = 1.0
        parts.append((-1.0 if b < 0 else 1.0) * x)
    if not parts:
        return None
    return sum(parts) / len(parts)


def direction_resolver(
    setup_name: str,
    fire_bar: Mapping[str, Any] | None,
    peer_panel: Mapping[str, Any] | None,
    *,
    only_ready: bool = False,
) -> int:
    """Return +1 / −1 / 0 for one fire.

    fire_bar is accepted for call-shape parity (symbol / index unused here).
    peer_panel: prefer {aligned_move: float}. Packet {peer: atr_move} is a
    scale-proxy. 0 = mid, unknown, or setup not in the nine when only_ready.
    """
    del fire_bar  # call-shape parity with the research callable
    if only_ready and canon_name(setup_name) not in READY_NAMES:
        return 0
    cx = _aligned_from_peer_panel(peer_panel)
    if cx is None:
        return 0
    q = _digitize(cx)
    if q <= 0:
        return -1
    if q >= NQ - 1:
        return 1
    return 0


def stay_timing(
    setup_name: str,
    fire_bar: Mapping[str, Any] | None,
    peer_panel: Mapping[str, Any] | None,
    *,
    only_ready: bool = False,
) -> bool:
    """Stub-path hook. True → generate() returns None (still timing).

    Missing panel does not suppress. When a panel is supplied, resolver 0
    stays timing. Live keepers use skip_on_resolver_disagree instead.
    """
    if peer_panel is None:
        return False
    return direction_resolver(
        setup_name, fire_bar, peer_panel, only_ready=only_ready,
    ) == 0


def skip_on_resolver_disagree(
    setup_name: str,
    fire_bar: Mapping[str, Any] | None,
    peer_panel: Mapping[str, Any] | None,
    geometry_side: int,
    *,
    only_ready: bool = False,
) -> bool:
    """True → live generate() returns None (timing-only skip).

    Geometry already selected a side. Resolver is never a side flip.
    Missing panel or resolver 0 → fire (SIZE annotation). Resolver
    available and disagrees with geometry_side → skip. Not armed.
    """
    if peer_panel is None:
        return False
    d = direction_resolver(
        setup_name, fire_bar, peer_panel, only_ready=only_ready,
    )
    if d == 0:
        return False
    return int(d) != int(geometry_side)


def resolver_for_ship(setup_name: str, *, only_ready: bool = True):
    """Closure: direction_resolver(fire_bar, peer_panel) -> int."""

    def _call(fire_bar, peer_panel=None):
        return direction_resolver(
            setup_name, fire_bar, peer_panel, only_ready=only_ready,
        )

    _call.setup_name = setup_name
    return _call


def smoke() -> dict[str, int]:
    """Same cases as BUILD-XASSET.md: q4→+1, q0→−1, mid→0, unready only_ready→0."""
    name = "wave_two_standing_bar_already_large"
    fire = {"symbol": "EURUSD"}
    return {
        "q4": direction_resolver(name, fire, {"aligned_move": 1.0}),
        "q0": direction_resolver(name, fire, {"aligned_move": -1.0}),
        "mid": direction_resolver(name, fire, {"aligned_move": 0.0}),
        "unready_only_ready": direction_resolver(
            "one_bar_consumes_20bar_box",
            fire,
            {"aligned_move": 1.0},
            only_ready=True,
        ),
    }


if __name__ == "__main__":
    got = smoke()
    print("SMOKE", got)
    assert got["q4"] == 1, got
    assert got["q0"] == -1, got
    assert got["mid"] == 0, got
    assert got["unready_only_ready"] == 0, got
    print("SMOKE_OK")
