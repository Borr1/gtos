"""A position that cannot be closed. (B333)

`_normalize_volume` computed `math.floor((lots - volume_min) / volume_step)` on a raw
binary quotient. With `volume_min == volume_step == 0.01`, `(0.03 - 0.01) / 0.01` is
`1.9999999999999998`, so **0.03 normalized to 0.02** — and
`_close_request_execution_geometry` (execution.py:2418) refuses any close whose
normalized volume differs from the requested one by more than 1e-9.

Why that is a strand rather than a rounding nit:

* **nine** close producers route through that check — full close, TP1, TP2, final
  target, time stop, and flatten (`execution.py:8005, 8162, 8215, 8331, 8405, 8482,
  8547, 8602, 8729`);
* the live book **always** takes the verified-geometry branch, because
  `ultimate_book/execution_packets.py:318-319` sets the two selected-cell risk fields
  `_trade_requires_verified_broker_geometry` keys on;
* each producer returns **before** `safe_place_order`, so nothing reaches the
  activation-token layer — every chaos drill in this session was looking one layer too
  low;
* and there is no recovery. `book_owner.py` records `{action}_close_failed` and retries
  on the next tick, recomputing the identical volume, refused identically, forever.

Measured before the fix: **33 of 300** two-decimal lot sizes affected at (0.01, 0.01),
**100 of 291** at a 0.10 minimum, and **44 of 327 real broker close deals** in
`vps-export-20260725` — **8 of 78** of the engine-initiated ones.

The two properties the fix must hold are asserted separately, because they pull in
opposite directions: every valid volume must round-trip (or the strand remains), and no
volume may ever be rounded UP (or the engine closes, or opens, more than it intended).
"""

from __future__ import annotations

import json
import math
import pathlib
from types import SimpleNamespace

import pytest

from src.components.execution import ExecutionEngine

REPO = pathlib.Path(__file__).resolve().parents[1]
VPS_DEALS = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")

# The geometries the two funded accounts actually present, plus the awkward ones.
GEOMETRIES = [
    (0.01, 0.01, 100.0),
    (0.10, 0.01, 100.0),
    (0.01, 0.001, 100.0),
    (0.10, 0.10, 500.0),
    (1.0, 1.0, 1000.0),
]


def _norm(lots, volume_min, volume_step, volume_max):
    info = SimpleNamespace(volume_min=volume_min, volume_step=volume_step,
                           volume_max=volume_max)
    return ExecutionEngine._normalize_volume(
        None, lots, info, require_broker_geometry=True)


def _aligned(lots, volume_min, volume_step):
    """Is `lots` an exact multiple of the step above the minimum? Decided in integer
    arithmetic so the test cannot inherit the bug it is testing."""

    if lots < volume_min:
        return False
    scale = 10 ** 9
    return round((round(lots * scale) - round(volume_min * scale))) % round(
        volume_step * scale) == 0


@pytest.mark.parametrize("volume_min,volume_step,volume_max", GEOMETRIES)
def test_every_broker_valid_volume_round_trips(volume_min, volume_step, volume_max):
    """THE test. A volume the broker would accept must normalize to itself, or the
    engine cannot close a position holding it."""

    refused = []
    for i in range(1, 3001):
        lots = round(i / 100.0, 2)
        if not _aligned(lots, volume_min, volume_step) or lots > volume_max:
            continue
        got = _norm(lots, volume_min, volume_step, volume_max)
        if got is None or abs(got - lots) > 1e-9:
            refused.append((lots, got))
    assert not refused, (
        f"{len(refused)} broker-valid volumes do not round-trip at "
        f"(min={volume_min}, step={volume_step}); first 10: {refused[:10]}. "
        "Each is a position the engine cannot close.")


@pytest.mark.parametrize("volume_min,volume_step,volume_max", GEOMETRIES)
def test_normalization_never_rounds_up(volume_min, volume_step, volume_max):
    """The property the epsilon must not break. Rounding UP would make a close request
    exceed the position — which `deal_reduces_existing_position` refuses at the
    activation layer — and would make an ENTRY larger than the sizing decided."""

    for i in range(1, 3001):
        lots = round(i / 100.0, 2)
        if lots < volume_min:
            continue
        got = _norm(lots, volume_min, volume_step, volume_max)
        if got is None:
            continue
        assert got <= lots + 1e-12, f"{lots} normalized UP to {got}"


@pytest.mark.parametrize("volume_min,volume_step,volume_max", GEOMETRIES)
def test_a_misaligned_volume_still_rounds_down_to_a_valid_step(
        volume_min, volume_step, volume_max):
    """The epsilon must absorb float error, not step error."""

    for i in range(1, 2000):
        lots = volume_min + i * volume_step / 3.0      # deliberately off-step
        if lots > volume_max:
            break
        got = _norm(lots, volume_min, volume_step, volume_max)
        if got is None:
            continue
        assert got <= lots + 1e-12
        assert _aligned(round(got, 9), volume_min, volume_step), (
            f"{lots} normalized to {got}, which is not on the broker's step grid")


def test_normalization_is_idempotent():
    """A position placed at a normalized volume must be closable at that volume.

    Before the fix, 14 reachable outputs were themselves refused — so an entry the
    engine itself sized and placed could not afterwards be closed by it.
    """

    volume_min = volume_step = 0.01
    outputs = {_norm(round(i / 100.0, 2), volume_min, volume_step, 100.0)
               for i in range(1, 3001)}
    for value in sorted(v for v in outputs if v is not None):
        again = _norm(value, volume_min, volume_step, 100.0)
        assert abs(again - value) <= 1e-9, (
            f"{value} is a reachable placed volume that normalizes to {again} — "
            "the engine can open it and can never close it")


def test_the_specific_volumes_that_were_stranded():
    """Regression pins, from the pre-fix measurement."""

    for lots in (0.03, 0.06, 0.15, 0.18, 0.21, 0.24, 0.29, 0.30, 0.35, 0.41, 0.47,
                 0.48, 0.59, 0.94, 1.13, 1.61, 1.88):
        assert abs(_norm(lots, 0.01, 0.01, 100.0) - lots) <= 1e-9, (
            f"{lots} still does not round-trip")


def test_below_minimum_is_still_refused():
    """The fix must not smuggle a sub-minimum volume past the guard."""

    assert _norm(0.005, 0.01, 0.01, 100.0) is None
    assert _norm(0.05, 0.10, 0.01, 100.0) is None


def test_volume_max_still_caps():
    assert _norm(500.0, 0.01, 0.01, 2.0) == pytest.approx(2.0)


def test_the_legacy_branch_is_untouched():
    """`require_broker_geometry=False` is a different code path with its own contract."""

    assert ExecutionEngine._normalize_volume(
        None, 0.037, None, require_broker_geometry=False) == pytest.approx(0.03)
    assert ExecutionEngine._normalize_volume(
        None, 0.001, None, require_broker_geometry=False) == pytest.approx(0.01)


@pytest.mark.skipif(not VPS_DEALS.is_dir(), reason="VPS export not on this machine")
def test_no_real_broker_close_deal_would_now_be_refused():
    """The measurement that made this a defect rather than a curiosity.

    44 of 327 real close deals on the two funded accounts carried a volume the engine
    would have refused. After the fix it must be zero — against the broker's own
    recorded volumes and the broker's own recorded specs.
    """

    refused = []
    checked = 0
    for account in ("ftmo", "redacted_account"):
        deals_path = VPS_DEALS / f"{account}_history_deals_get.jsonl"
        specs_path = VPS_DEALS / f"{account}_symbol_specs_traded.json"
        if not (deals_path.is_file() and specs_path.is_file()):
            continue
        specs = json.loads(specs_path.read_text())
        for line in deals_path.read_text().splitlines():
            if not line.strip():
                continue
            deal = json.loads(line)
            if deal.get("entry") != 1:            # DEAL_ENTRY_OUT
                continue
            spec = specs.get(deal.get("symbol")) or {}
            volume = deal.get("volume")
            vmin, vstep, vmax = (spec.get("volume_min"), spec.get("volume_step"),
                                 spec.get("volume_max"))
            if not (volume and vmin and vstep and vmax):
                continue
            checked += 1
            got = _norm(float(volume), float(vmin), float(vstep), float(vmax))
            if got is None or abs(got - float(volume)) > 1e-9:
                refused.append((account, deal.get("symbol"), volume, got))
    assert checked > 100, f"only {checked} deals checked; the export shape has changed"
    assert not refused, (
        f"{len(refused)} of {checked} REAL broker close deals would still be refused: "
        f"{refused[:10]}")


def test_the_close_geometry_gate_still_refuses_a_genuinely_bad_volume():
    """The fix must not turn the alignment check into a no-op — it exists to stop the
    engine sending a volume the broker will reject."""

    lots = 0.037                                   # not on a 0.01 grid
    got = _norm(lots, 0.01, 0.01, 100.0)
    assert abs(got - lots) > 1e-9, "an off-grid volume must still fail the equality gate"
    assert got == pytest.approx(0.03)
