"""Coverage classes and the typed measure that carries one.

The design rule this file enforces, from `SESSION_J_BROKER_TRUTH.md`:

    A number without a coverage class is not a number this layer emits.
    Make that structural -- schema, not convention.

So `Measure` is the only way a number leaves `src.costs`, and it cannot be built
without a coverage class and a provenance string. A `TRANSFERRED` measure additionally
cannot be built without naming what it was transferred from. These are constructor
errors, not lint rules.

Why it matters here specifically. `GATE_G1B_RECEIPT.md` §5.2a measured commission at
**0.0000 R on the six index CFDs**, 0.0054 R on XAUUSD and **0.1948 R on USDJPY**. A
re-cost that silently modelled the unmeasured instruments as zero would reproduce F38
with better manners -- the zero would look identical to the six genuinely-measured
zeros. The coverage class is what keeps those two zeros distinguishable.

Bands
-----
`SESSION_J` requires x0.5 / x1 / x2 sensitivity bands on anything not `[MEASURED]`.
They are derived in `__post_init__` rather than passed in, so a caller cannot forget
them and cannot narrow them. A `MEASURED` value has a degenerate band (value, value).

Sign convention: **costs are positive**. This matches the live engine, where
`spread_r`, `expected_slippage_r` and `swap_cost_r` are all positive drags summed into
`total_cost_r` (`broker_net_cost_engine.py:577-583`).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

__all__ = [
    "Coverage",
    "Measure",
    "weakest",
]

# Sensitivity multipliers applied to anything not MEASURED.
BAND_LOW_MULT = 0.5
BAND_HIGH_MULT = 2.0


class Coverage(enum.Enum):
    """How well-grounded a number is. Ordered weakest-last by `strength`."""

    MEASURED = "MEASURED"
    """Observed on this account, this instrument."""

    TRANSFERRED = "TRANSFERRED"
    """Inferred from a comparable instrument; the band is wider and says from what."""

    MODELLED = "MODELLED"
    """No observation; a stated assumption with an owner and a date."""

    @property
    def strength(self) -> int:
        return _STRENGTH[self]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


_STRENGTH = {Coverage.MEASURED: 0, Coverage.TRANSFERRED: 1, Coverage.MODELLED: 2}


def weakest(*coverages: Coverage) -> Coverage:
    """The coverage a derived number inherits: the weakest of its inputs.

    A total built from a measured spread and a modelled commission is modelled. This is
    the "class travels into every result computed from it" rule, in one function.
    """
    if not coverages:
        raise ValueError("weakest() needs at least one coverage class")
    return max(coverages, key=lambda c: c.strength)


@dataclass(frozen=True)
class Measure:
    """A number that cannot exist without a coverage class and a provenance.

    Parameters
    ----------
    value:
        The quantity. Costs are positive.
    coverage:
        `Coverage.MEASURED` / `TRANSFERRED` / `MODELLED`.
    provenance:
        Where the number came from, specific enough to re-derive: a `file:line`, an
        artifact path, or a named measurement with its n. Required and non-empty.
    unit:
        Free-text unit, e.g. ``"R"``, ``"USD/lot"``, ``"price"``, ``"bp_of_notional"``.
    n:
        Observation count behind a measurement, when there is one.
    transferred_from:
        Required when `coverage is Coverage.TRANSFERRED`: what the value was taken from.
    owner, asof:
        Required when `coverage is Coverage.MODELLED`: whose assumption, and when.
        `SESSION_J`: "a stated assumption with an owner and a date".
    """

    value: float
    coverage: Coverage
    provenance: str
    unit: str = "R"
    n: int | None = None
    transferred_from: str | None = None
    owner: str | None = None
    asof: str | None = None
    band_mult: tuple[float, float] | None = None
    band_provenance: str | None = None
    band_low: float = field(init=False)
    band_high: float = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, Coverage):
            raise TypeError(
                f"coverage must be a Coverage, got {type(self.coverage).__name__}. "
                "A number without a coverage class is not a number this layer emits."
            )
        if not self.provenance or not self.provenance.strip():
            raise ValueError(
                "provenance is required and must be non-empty: name the file:line, "
                "artifact, or measurement this value came from."
            )
        if self.coverage is Coverage.TRANSFERRED and not self.transferred_from:
            raise ValueError(
                "a TRANSFERRED measure must name transferred_from -- 'the band is wider "
                "and says from what'."
            )
        if self.coverage is Coverage.MODELLED and not (self.owner and self.asof):
            raise ValueError(
                "a MODELLED measure must carry owner and asof -- "
                "'a stated assumption with an owner and a date'."
            )
        if self.band_mult is not None:
            if self.coverage is Coverage.MEASURED:
                raise ValueError(
                    "a MEASURED measure has a degenerate band; band_mult is meaningless"
                )
            if not self.band_provenance:
                raise ValueError(
                    "narrowing the default x0.5/x2 band requires band_provenance -- the "
                    "measurement that justifies the tighter band."
                )
        low, high = self._band()
        object.__setattr__(self, "band_low", low)
        object.__setattr__(self, "band_high", high)

    def _band(self) -> tuple[float, float]:
        """x0.5 / x1 / x2 by default on anything not MEASURED.

        The default is deliberately wide and cannot be forgotten. It *can* be replaced by
        an evidence-backed band via `band_mult` + `band_provenance` -- measured here, the
        same-class commission transfer is accurate to <0.7% (redacted_account metals 0.52%,
        crypto 0.017%, FX 0.000%), so x0.5/x2 would overstate that uncertainty by two
        orders of magnitude. Narrowing requires the measurement; widening never does.
        """
        if self.coverage is Coverage.MEASURED:
            return (self.value, self.value)
        lo_mult, hi_mult = self.band_mult or (BAND_LOW_MULT, BAND_HIGH_MULT)
        lo = self.value * lo_mult
        hi = self.value * hi_mult
        return (min(lo, hi), max(lo, hi))

    @property
    def is_measured(self) -> bool:
        return self.coverage is Coverage.MEASURED

    def scaled(self, factor: float, *, provenance: str) -> "Measure":
        """Rescale, preserving coverage and widening nothing.

        Used for unit conversions (USD/lot -> R). The coverage class of a converted
        number is the coverage of the number, not of the conversion; callers that
        introduce an assumption in the conversion must downgrade explicitly with
        `downgraded_to`.
        """
        return Measure(
            value=self.value * factor,
            coverage=self.coverage,
            provenance=provenance,
            unit=self.unit,
            n=self.n,
            transferred_from=self.transferred_from,
            owner=self.owner,
            asof=self.asof,
        )

    def downgraded_to(
        self,
        coverage: Coverage,
        *,
        provenance: str,
        transferred_from: str | None = None,
        owner: str | None = None,
        asof: str | None = None,
    ) -> "Measure":
        """Return the same value at a weaker coverage class. Refuses to strengthen."""
        if coverage.strength < self.coverage.strength:
            raise ValueError(
                f"refusing to strengthen coverage {self.coverage} -> {coverage}; "
                "coverage only ever degrades as assumptions are added."
            )
        return Measure(
            value=self.value,
            coverage=coverage,
            provenance=provenance,
            unit=self.unit,
            n=self.n,
            transferred_from=transferred_from or self.transferred_from,
            owner=owner or self.owner,
            asof=asof or self.asof,
        )

    def as_dict(self) -> dict:
        out = {
            "value": self.value,
            "coverage": self.coverage.value,
            "provenance": self.provenance,
            "unit": self.unit,
            "band_low": self.band_low,
            "band_high": self.band_high,
        }
        for key in ("n", "transferred_from", "owner", "asof"):
            val = getattr(self, key)
            if val is not None:
                out[key] = val
        return out
