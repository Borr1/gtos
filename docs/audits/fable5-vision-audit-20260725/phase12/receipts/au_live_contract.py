"""Session AU — the live exit contract as a replayable variant, and the `maxbars` census.

WHY THIS EXISTS, AND WHAT IT CORRECTS

AQ built the three-contract machinery (`PUBLISHED` / `LIVE_TRUE` / `REPAIRED`) and its `LIVE_TRUE`
arm is *"the same plus a time stop"* -- `AD.Variant(family="time_stop", time_stop_bars=ts,
target_mode="native")`. `Variant`'s defaults are `trail_arm_r=None, trail_gap_r=None,
partial_at_r=None`, so for a sleeve whose LIVE policy is `trailing_runner` or `partial_be_runner`
that arm silently deletes the sleeve's trail or scale-out. Three of AQ's ten Side-B sleeves are in
that class, including the two largest rows in the table:

    asian_fade                trailing_runner  trigger 0.5 / gap 0.5   AQ error +0.8832 R/day
    metal_session_reversion   trailing_runner  trigger 0.6 / gap 0.5   AQ error +0.3050
    energy_agri  (side B by policy, not in AQ's ten)  partial_be_runner  trigger 2.0 / ratio 0.5

`asian_fade`'s truncation fraction in that arm is **0.0** -- the time stop never fired -- so its
entire +0.8832 is the contract change, not the horizon. AQ named the mechanism (*"the damage is not
the time stop cutting trades short, it is the trailing runner contract interacting with it"*) and
routed measuring it to this session. This module is the instrument: it translates a sleeve's WHOLE
live exit profile into a replayable variant, so `LIVE_TRUE` means the live contract rather than a
time stop bolted to a plain exit.

THE CONTROL THAT MAKES THE TRANSLATION TRUSTWORTHY

`AA_ESTATE_TRADES.json.gz` records, per sleeve, what AA itself applied
(`exit_contracts[sleeve]["applied_here"]`, e.g. `"trail+stop+target+maxbars"`, and
`time_stop_bars_applied: false` for every sleeve). So the same translator, fed AA's *applied* contract
instead of the live one, must reproduce AA's own labelling trade by trade. `variant_for_applied` +
`published_identity_control` do exactly that. A translator that reproduces the walk it did not write
can be believed about the contract nobody has walked.

THE MAXBARS SHARE, WHICH IS NOW MANDATORY (wave-12 agreement §4)

AR measured that AL's published frontier winner carries **20.6 %** of its trades exiting on the
harness ceiling rather than on the contract, and that no exit sweep in this estate had ever reported
the share. `maxbars_share` reads it straight off `AD.resimulate`'s telemetry, which already counts it.
Every cell every AU driver publishes carries it.

BOUNDARY. Offline and pure: bars, cost artifacts and AA's stored intents. Imports no broker module.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
    resolve_exit_profile,
)

UNITS = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AD_TIMESTOP_UNITS_V1.json"
MAXBARS = AD.MAXBARS                       # 80
#: Calendar M15 bars per bar of each decision grid. See AQ §1 on why a SPEC must convert with the
#: calendar ratio and a MEASUREMENT should use the per-symbol printed ratio where it has one.
M15_PER_BAR_CALENDAR = {"M15": 1, "H4": 16, "D1": 96}
#: MT5 timeframe constants as AA stores them in `timeframe`.
TF_GRID = {15: "M15", 16388: "H4", 16408: "D1"}


# =====================================================================================
# the live profile -> a replayable variant
# =====================================================================================

def live_profile(sleeve: str, *, frontier_exits=()) -> dict:
    """The exit profile `run_book.py` resolves for `sleeve`, under a frontier selection."""
    return resolve_exit_profile(sleeve, frontier_exits=frontier_exits)


def own_bars(sleeve: str, m15_bars, *, grid: str, printed_ratio: float | None = None,
             cap_at_maxbars: bool = True) -> int | None:
    """`m15_bars` printed M15 bars expressed in the sleeve's OWN bars, as `exits.replay` counts them.

    `printed_ratio` is the MEASURED per-symbol printed-bar ratio when one is available (92 on a
    session index, 84 on UKOIL, 96 on a 24/7 symbol); the calendar ratio otherwise. Capped at
    `maxbars` because a policy cannot outlive the harness ceiling -- an uncapped value would make the
    time stop unreachable and read as "no time stop", which is the wrong way round.
    """
    if not m15_bars:
        return None
    ratio = float(printed_ratio or M15_PER_BAR_CALENDAR[grid])
    n = int(round(float(m15_bars) / ratio))
    n = max(1, n)
    return min(MAXBARS, n) if cap_at_maxbars else n


def variant_for_profile(sleeve: str, prof: dict, *, grid: str, name: str,
                        printed_ratio: float | None = None,
                        apply_time_stop: bool = True,
                        trail_lag_extremes: bool = False,
                        time_stop_own_bars: int | None = None) -> AD.Variant:
    """The whole live exit profile as an `AD.Variant`: trail AND scale-out AND target AND time stop.

    The mapping, read off `execution_packets.build_book_trade_params` rather than inferred:

      policy `trailing_runner`   -> trail arms at `trigger_r`, gives back `trail_gap_r`
      policy `partial_be_runner` -> `partial_frac` off at `trigger_r`, stop to breakeven after
      policy `time_stop`         -> neither; the target and the time stop are the whole contract

      broker TP: `broker_take_profit_mode == "none"` (or `final_target_r` None on such a sleeve)
                 -> no target at all. `final_from_intent` -> the intent's OWN target/stop ratio,
                 which is what `build_book_trade_params` computes at `:256`, so `target_mode`
                 stays `native`. Otherwise a fixed `final_target_r` R.

    `trail_lag_extremes` is exposed because B613 makes both bounds mandatory for any trail cell:
    False reproduces production `simulate` (a trail may arm and fill inside one bar), True forbids it.
    """
    policy = str(prof.get("policy") or DEFAULT_EXIT_PROFILE["policy"])
    no_tp = str(prof.get("broker_take_profit_mode", "final_target")).strip().lower() == "none"
    raw_ftr = prof.get("final_target_r", DEFAULT_EXIT_PROFILE["final_target_r"])

    if no_tp and raw_ftr in (None, ""):
        target_mode, target_r = "no_target", None
    elif prof.get("final_from_intent"):
        # the broker TP tracks the intent's own target/stop ratio -> the walked target, unchanged
        target_mode, target_r = "native", None
    elif raw_ftr in (None, ""):
        target_mode, target_r = "no_target", None
    else:
        target_mode, target_r = "fixed_r", float(raw_ftr)

    trail_arm = trail_gap = None
    partial_at = None
    partial_frac = 0.5
    if policy == "trailing_runner":
        trail_arm = float(prof.get("trigger_r") or 0.0) or None
        trail_gap = float(prof.get("trail_gap_r") or 0.0) or None
        if (trail_arm is None) != (trail_gap is None):
            raise ValueError(f"{sleeve}: trailing_runner needs both trigger_r and trail_gap_r, "
                             f"got {prof.get('trigger_r')!r}/{prof.get('trail_gap_r')!r}")
    elif policy == "partial_be_runner":
        partial_at = float(prof.get("trigger_r") or 0.0) or None
        pr = prof.get("partial_close_ratio")
        if pr is not None:
            partial_frac = float(pr)
        if partial_at is None:
            raise ValueError(f"{sleeve}: partial_be_runner needs trigger_r")
    elif policy != "time_stop":
        raise ValueError(
            f"{sleeve}: no replay translation for live policy {policy!r}. Refusing rather than "
            f"falling back to a plain exit -- an unrecognised policy silently replayed as "
            f"stop+target+maxbars is exactly the substitution this module exists to stop.")

    ts = None
    if apply_time_stop:
        ts = (time_stop_own_bars if time_stop_own_bars is not None
              else own_bars(sleeve, prof.get("time_stop_bars"), grid=grid,
                            printed_ratio=printed_ratio))

    return AD.Variant(
        name=name, family="live_contract",
        time_stop_bars=ts,
        trail_arm_r=trail_arm, trail_gap_r=trail_gap, trail_lag_extremes=trail_lag_extremes,
        target_mode=target_mode, target_r=target_r,
        partial_at_r=partial_at, partial_frac=partial_frac, be_stop_after_partial=True,
        note=f"the LIVE contract of {sleeve}: policy={policy}, "
             f"target={target_mode}{f'({target_r:g}R)' if target_r else ''}, "
             f"time_stop={ts} own bars",
    )


#: What AA's own metadata says it applied, mapped to the pieces of a variant. AA records this per
#: sleeve in `exit_contracts[sleeve]["applied_here"]`, so the published contract is READ and not
#: reconstructed from the sleeve's policy name.
_APPLIED_PIECES = {"trail", "stop", "target", "maxbars", "partial"}


def variant_for_applied(sleeve: str, prof: dict, applied_here: str, *, grid: str,
                        name: str = "published", trail_lag_extremes: bool = False) -> AD.Variant:
    """The contract AA actually applied, as a variant. `applied_here` is AA's own string.

    Every sleeve in AA's walk carries `time_stop_bars_applied: false`, so the published contract never
    has a time stop; what varies is whether the trail or the scale-out was applied.
    """
    pieces = {p.strip() for p in str(applied_here).split("+") if p.strip()}
    unknown = pieces - _APPLIED_PIECES
    if unknown:
        raise ValueError(f"{sleeve}: unrecognised applied_here piece(s) {sorted(unknown)} in "
                         f"{applied_here!r}; refusing to guess what AA applied")
    sub = dict(prof)
    if "trail" not in pieces:
        sub.pop("trail_gap_r", None)
        if str(sub.get("policy")) == "trailing_runner":
            sub["policy"] = "time_stop"
    if "partial" not in pieces and str(sub.get("policy")) == "partial_be_runner":
        sub["policy"] = "time_stop"
    if "target" not in pieces:
        sub["broker_take_profit_mode"] = "none"
        sub["final_target_r"] = None
        sub.pop("final_from_intent", None)
    v = variant_for_profile(sleeve, sub, grid=grid, name=name, apply_time_stop=False,
                            trail_lag_extremes=trail_lag_extremes)
    return AD.Variant(**{**v.__dict__, "family": "published",
                         "note": f"AA's own applied contract: {applied_here}"})


# =====================================================================================
# telemetry
# =====================================================================================

def maxbars_share(tel: dict) -> dict:
    """The share of a cell's trades that exited on the HARNESS CEILING rather than on the contract.

    Mandatory on every cell from wave 12 (agreement §4), because AR measured **20.6 %** on AL's own
    published winner and **31.8 %** at its grid edge, and no exit sweep had ever reported it. A cell
    with a high share is not measuring its geometry; it is measuring `maxbars`.
    """
    exits = {k[len("exit_"):]: v for k, v in (tel or {}).items() if k.startswith("exit_")}
    n = sum(exits.values())
    mb = int(exits.get("maxbars", 0))
    ts = int(exits.get("time_stop", 0))
    return {
        "n_exited": n,
        "exit_reasons": exits,
        "maxbars_share": (mb / n) if n else None,
        "time_stop_share": (ts / n) if n else None,
        "horizon_share": ((mb + ts) / n) if n else None,
    }


def published_identity_control(rows_published: list, rows_aa: list) -> dict:
    """`variant_for_applied` must reproduce AA's stored labelling trade by trade, or the translator
    is not trustworthy about the contract nobody has walked. Keyed on the trade, not on the mean."""
    def key(r):
        return (r["symbol"], r["decision_bar_iso"], int(r["direction"]))

    a = {key(r): r for r in rows_aa}
    b = {key(r): r for r in rows_published}
    shared = sorted(set(a) & set(b))
    mism = [k for k in shared
            if abs(float(a[k]["r_gross"]) - float(b[k]["r_gross"])) > 1e-9
            or int(a[k]["exit_bar_offset"]) != int(b[k]["exit_bar_offset"])]
    return {
        "n_aa": len(a), "n_replayed": len(b), "n_shared": len(shared),
        "n_mismatched": len(mism),
        "identical": (len(mism) == 0 and len(shared) == len(a) == len(b)),
        "examples": mism[:5],
    }


def grid_of(rows: list) -> str:
    tfs = {int(r["timeframe"]) for r in rows}
    if len(tfs) != 1:
        raise ValueError(f"rows span several grids: {sorted(tfs)}")
    tf = tfs.pop()
    try:
        return TF_GRID[tf]
    except KeyError:
        raise ValueError(f"unknown MT5 timeframe constant {tf}") from None


def printed_ratio_of(sleeve: str, units_doc: dict) -> float | None:
    """The MEASURED printed-M15-bars-per-own-bar ratio AD computed, when it has one for this sleeve.

    AD stores it trade-weighted per sleeve in `sleeve_contracts[sleeve]`
    (`m15_per_own_bar_trade_weighted`), which is the per-SYMBOL printed ratio averaged over the
    sleeve's own trades -- 96 on a 24/7 symbol, ~92 on a session index, ~84 on UKOIL. That is the
    right ratio for a MEASUREMENT; the calendar ratio is the right one for a SPEC (AQ §1).
    """
    row = ((units_doc.get("sleeve_contracts") or {}).get(sleeve) or {})
    v = row.get("m15_per_own_bar_trade_weighted")
    return float(v) if v else None


def ad_units_row(sleeve: str, units_doc: dict) -> dict:
    return dict((units_doc.get("sleeve_contracts") or {}).get(sleeve) or {})


__all__ = [
    "AD", "MAXBARS", "M15_PER_BAR_CALENDAR", "SLEEVE_EXIT_PROFILES", "TF_GRID", "UNITS",
    "ad_units_row", "grid_of", "live_profile", "maxbars_share", "own_bars", "printed_ratio_of",
    "published_identity_control", "variant_for_applied", "variant_for_profile",
]
