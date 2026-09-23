"""Barrier-conditional execution slippage, measured, replacing a flat constant.

WHAT WAS WRONG
--------------
``config/agent_config.yaml:740`` carries ``selected_cell_default_expected_slippage_r: 0.02``
and the engine charges it to every trade, unconditionally.  Slippage is not a per-trade
constant; it is a property of *how the order reached the market*, and the estate resolves
its trades against three structurally different exits:

* **TARGET** is a limit.  A limit fills at its price or better, never worse.  Measured on
  3,435 target crossings against the tick archive, ``frac_adverse`` is **0.0000** -- not
  "small", zero -- and the tape overshoots the level in the trade's favour by 0.0397 R,
  which the engine correctly declines to book.  The flat constant charges these trades a
  slippage they cannot incur.
* **STOP** is a market order triggered in motion, and it is the expensive one:
  **0.03932 R** conditional on a stop for the MARKET arm (n=9,543, 99.5 % adverse),
  **0.04547 R** for the LIMIT arm (n=11,100, 100 % adverse).
* **TIME_STOP** is a market order at a scheduled instant, and it is nearly free:
  **0.00141 R** (MARKET, n=5,482), **0.01211 R** (LIMIT, n=3,786).

Charging one number across those three is a cross-subsidy from trades that reach target to
trades that stop out.  Measured over the sealed five-month census it moves individual
strategy families by **-$13.34 to +$88.92 per trade** at $2,000/R while barely moving the
pooled average -- which is exactly why a pooled check kept passing and the constant survived.

THE ENTRY LEG IS DELIBERATELY ZERO HERE
---------------------------------------
Entry slippage is real (0.00663 R MARKET / 0.02322 R LIMIT), but it is **already inside the
fill price** and must not be deducted a second time.  RECON measured its correlation with
modelled-vs-true spread error at **+0.753** and adjudicated it a spread-model quantity;
``spread_r`` is booked into the fill-anchored gross and never deducted again
(``src/costs/lifecycle.py`` marks it
``included_in_fill_anchored_gross_no_additional_deduction``).  Adding an entry leg here
would double-charge it.  ``entry_leg_r`` therefore returns 0.0 with that provenance
attached, rather than being silently absent.

UNITS
-----
Values are **R conditional on the barrier**, transferable because the measurement population
IS the sealed labeller's own resolved rows ("sealed labeller MARKET resolved rows, orig arm,
all 5 sealed months") and its per-symbol stop distances sit within 0.8-1.2x of the census's
own.  R does **not** transfer across stop geometries in general -- the live book's median
stop is 3.384x the January pool's -- so a caller working at a different geometry must
re-denominate through price.  ``price_domain_leg`` exposes the price-unit form for that.

PROVENANCE
----------
MARKET arm: ``RECON_SLIPPAGE_TRUTH_V1.json`` (18,978 rows, tick archive 2026-06-18..07-24).
LIMIT arm:  ``B1_LIMIT_ARM_MEASURED_V1.json`` (19,088 rows, same window).
Both are tick-measured against ``/Users/borr/GTOSActive/vps-ticks-20260726/``, broker->UTC via
``new_york_plus_7``, cluster-bootstrapped on ``trading_day``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = [
    "BarrierSlippageError",
    "BarrierSlippageModel",
    "SlippageLeg",
    "load_barrier_slippage_model",
]

REPO = Path(__file__).resolve().parents[2]
_SWARM = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "outcome_authority/swarm2"
)
DEFAULT_MARKET_ARTIFACT = (
    _SWARM / "recon_slippage_receipts/RECON_SLIPPAGE_TRUTH_V1.json"
)
DEFAULT_LIMIT_ARTIFACT = (
    _SWARM / "breakthrough/b1_limit_export/B1_LIMIT_ARM_MEASURED_V1.json"
)

#: Exits that reach the market as a *limit*.  A limit cannot fill adversely.
LIMIT_EXITS = frozenset({"TARGET"})
#: Exits that reach the market as a *market order* and therefore can slip.
MARKET_EXITS = frozenset({"STOP", "TRAIL", "TIME_STOP", "MAXBARS", "ROLLOVER_FLAT"})
#: Exits whose measured cost follows the scheduled-exit population rather than the stop one.
_TIME_STOP_LIKE = frozenset({"TIME_STOP", "MAXBARS", "ROLLOVER_FLAT"})
_STOP_LIKE = frozenset({"STOP", "TRAIL"})


class BarrierSlippageError(RuntimeError):
    """No measured sample can decide this leg, and no unmeasured number will be invented."""


@dataclass(frozen=True)
class SlippageLeg:
    """One charged leg, with everything needed to argue about it later."""

    value_r: float
    barrier: str
    arm: str
    symbol: str | None
    coverage: str          # MEASURED | TRANSFERRED | STRUCTURAL_ZERO
    n: int
    provenance: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "value_r": self.value_r,
            "barrier": self.barrier,
            "arm": self.arm,
            "symbol": self.symbol,
            "coverage": self.coverage,
            "n": self.n,
            "provenance": self.provenance,
        }


class BarrierSlippageModel:
    """Expected adverse execution slippage, conditioned on how the trade actually ended."""

    def __init__(self, market_doc: dict, limit_doc: dict) -> None:
        if market_doc.get("schema") != "recon_slippage_adjudication_v1":
            raise BarrierSlippageError(
                f"unsupported MARKET slippage schema {market_doc.get('schema')!r}"
            )
        self._market_doc = market_doc
        self._limit_doc = limit_doc
        self.window = market_doc.get("window")

        self._stop_by_symbol = {
            "MARKET": market_doc.get("stop_leg_by_symbol") or {},
            "LIMIT": limit_doc.get("LIMIT_stop_by_symbol") or {},
        }
        mm = market_doc
        lm = limit_doc.get("LIMIT_measured") or {}
        self._stop_pool = {
            "MARKET": _mean(mm.get("exit_STOP")),
            "LIMIT": _mean(lm.get("STOP")),
        }
        self._time_stop_pool = {
            "MARKET": _mean(mm.get("exit_TIME_STOP")),
            "LIMIT": _mean(lm.get("TIME_STOP")),
        }
        for arm in ("MARKET", "LIMIT"):
            if self._stop_pool[arm] is None or self._time_stop_pool[arm] is None:
                raise BarrierSlippageError(f"{arm} arm is missing a pooled exit leg")

    # -- the entry leg, and why it is zero ---------------------------------------------------
    def entry_leg_r(self, *, arm: str = "MARKET") -> SlippageLeg:
        """Always 0.0.  Entry slippage is inside the fill price; see the module docstring."""
        return SlippageLeg(
            value_r=0.0,
            barrier="ENTRY",
            arm=_norm_arm(arm),
            symbol=None,
            coverage="STRUCTURAL_ZERO",
            n=0,
            provenance=(
                "entry slippage correlates +0.753 with modelled-vs-true spread error and is "
                "already booked inside the fill-anchored gross via spread_r; deducting it "
                "here would double-charge it (RECON_SLIPPAGE_ADJUDICATION_V1 S2.2)"
            ),
        )

    # -- the exit leg, which is where the money is -------------------------------------------
    def exit_leg_r(self, *, exit_kind: str, order_type: str, symbol: str | None = None) -> SlippageLeg:
        barrier = _norm_barrier(exit_kind)
        arm = _norm_arm(order_type)

        if barrier in LIMIT_EXITS:
            n = _n(self._market_doc.get("exit_TARGET"))
            return SlippageLeg(
                value_r=0.0,
                barrier=barrier,
                arm=arm,
                symbol=symbol,
                coverage="MEASURED",
                n=n,
                provenance=(
                    f"limit exit: 0 of {n} measured target crossings filled adversely "
                    "(frac_adverse 0.0); the tape overshoots the level in the trade's favour "
                    "and the engine books the level exactly"
                ),
            )

        if barrier in _TIME_STOP_LIKE:
            return SlippageLeg(
                value_r=float(self._time_stop_pool[arm]),
                barrier=barrier,
                arm=arm,
                symbol=symbol,
                coverage="TRANSFERRED",
                n=_n(
                    (self._market_doc if arm == "MARKET" else self._limit_doc.get("LIMIT_measured", {}))
                    .get("exit_TIME_STOP" if arm == "MARKET" else "TIME_STOP")
                ),
                provenance=f"pooled {arm} scheduled-exit leg; no per-symbol time-stop sample exists",
            )

        if barrier in _STOP_LIKE:
            table = self._stop_by_symbol[arm]
            rec = table.get(symbol) if symbol else None
            if rec is not None and rec.get("n"):
                return SlippageLeg(
                    value_r=float(rec["mean"]),
                    barrier=barrier,
                    arm=arm,
                    symbol=symbol,
                    coverage="MEASURED",
                    n=int(rec["n"]),
                    provenance=f"per-symbol {arm} stop-conditional leg, tick-measured",
                )
            return SlippageLeg(
                value_r=float(self._stop_pool[arm]),
                barrier=barrier,
                arm=arm,
                symbol=symbol,
                coverage="TRANSFERRED",
                n=_n(
                    self._market_doc.get("exit_STOP")
                    if arm == "MARKET"
                    else (self._limit_doc.get("LIMIT_measured") or {}).get("STOP")
                ),
                provenance=(
                    f"pooled {arm} stop-conditional leg; no per-symbol sample for {symbol!r}"
                ),
            )

        raise BarrierSlippageError(
            f"no measured slippage leg for exit kind {exit_kind!r}; refusing to invent one"
        )

    def expected_slippage_r(
        self, *, exit_kind: str, order_type: str, symbol: str | None = None
    ) -> float:
        """Total charged slippage for one round trip: exit leg only, entry is inside gross."""
        return (
            self.entry_leg_r(arm=order_type).value_r
            + self.exit_leg_r(exit_kind=exit_kind, order_type=order_type, symbol=symbol).value_r
        )

    def price_domain_leg(
        self, *, exit_kind: str, order_type: str, symbol: str, stop_distance_price: float
    ) -> float:
        """The same leg in price units, for callers at a different stop geometry.

        R does not transfer across stop geometries.  Multiply back by the caller's own stop
        distance rather than reusing an R figure measured at someone else's.
        """
        if not stop_distance_price or stop_distance_price <= 0:
            raise BarrierSlippageError("stop_distance_price must be positive")
        leg = self.exit_leg_r(exit_kind=exit_kind, order_type=order_type, symbol=symbol)
        return leg.value_r * float(stop_distance_price)


def _mean(node: Any) -> float | None:
    if not isinstance(node, dict):
        return None
    if "at_crossing_tick" in node:
        node = node["at_crossing_tick"]
    value = node.get("mean")
    return float(value) if isinstance(value, (int, float)) else None


def _n(node: Any) -> int:
    if not isinstance(node, dict):
        return 0
    if "at_crossing_tick" in node:
        node = node["at_crossing_tick"]
    return int(node.get("n") or 0)


def _norm_arm(order_type: str) -> str:
    arm = str(order_type or "").strip().upper()
    if arm in ("MARKET", "LIMIT"):
        return arm
    raise BarrierSlippageError(f"unknown order arm {order_type!r}; expected MARKET or LIMIT")


def _norm_barrier(exit_kind: str) -> str:
    return str(exit_kind or "").strip().upper()


@lru_cache(maxsize=4)
def load_barrier_slippage_model(
    market_artifact: str | None = None, limit_artifact: str | None = None
) -> BarrierSlippageModel:
    mp = Path(market_artifact) if market_artifact else DEFAULT_MARKET_ARTIFACT
    lp = Path(limit_artifact) if limit_artifact else DEFAULT_LIMIT_ARTIFACT
    for p in (mp, lp):
        if not p.is_file():
            raise BarrierSlippageError(f"slippage artifact missing: {p}")
    return BarrierSlippageModel(
        json.loads(mp.read_text(encoding="utf-8")),
        json.loads(lp.read_text(encoding="utf-8")),
    )
