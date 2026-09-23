"""The exit-repair frontier: re-simulate every exit variant over AA's stored intents, re-gate.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_exit_sweep.py
    AD_ONLY=mx_btcusd_d1_donchian_20_breakout python3 .../ad_exit_sweep.py   # one sleeve

WHAT THIS IS
------------
`SESSION_AA_ESTATE_WALK_RESULT.md` §2.2 measured, per sleeve, how much of its own excursion
the exit keeps. `metals_core` — live, conf 1.0 — reaches +1.76 R mean MFE and keeps 0.114 of
it; `kz_london_crypto_low` reaches 3.40 R and gives back all of it. This sweeps exits that
keep more, per sleeve, and publishes the frontier with both trail bounds.

WHY IT DOES NOT REGENERATE
--------------------------
AA's `AA_ESTATE_TRADES.json.gz` carries every walked trade with the INTENT that produced it
(`decision_bar_iso`, `direction`, `sl_distance_price`, `entry_price`, `target_dist`,
`timeframe`), and `decision_bar_iso` is the exact index into the archive series the trade was
labelled on. So re-simulating a different exit is a replay from the stored intent, not a
regeneration: minutes, against AA's 10,736 s.

THE STOP-WIDTH CELLS ARE A REGENERATION, AND THIS IS WHY THEY DO NOT NEED THE GENERATOR
---------------------------------------------------------------------------------------
The working agreement says stop-width cells must be REGENERATED rather than rescaled,
because a wider stop changes R geometry. That is right, and it is satisfied here without
re-running generation, for a reason that had to be checked per sleeve rather than assumed:
**for the five COST_GEOMETRY sleeves the entry signal does not read the stop distance**, so a
`k`x stop changes the geometry of the same candidate set and nothing else.

    metals_core       `fvg_signal` returns (direction, sd) from structure + STOP_BUF*ATR
                      floored at ATR_STOP_FLOOR*ATR (`sleeves/metals.py:63-91`); the
                      admission gates are `ac60` and `vol_ratio`, neither reads sd.
    fx_jpy/_ny        sd = 1.0*ATR14(iw), td = 2.5*ATR14(iw) (`sleeves/fx_jpy.py:203`);
                      the NY gates are an impulse and a trend sign, neither reads sd.
    vss_fxcross       sd = STOP_ATR*atr_i, td = TGT_ATR*atr_i
                      (`sleeves/vss_fxcross_london_up_low.py:171-181`); the only sd test is
                      `sd <= 0`, which scaling by k>0 preserves.
    metal_session_reversion  sd = STOP_K*ATR, target_dist None, trail in stop units
                      (`sleeves/metal_session_reversion.py:115`).
    mx_* donchian / volume_surge   sd = risk, td = TARGET_R*risk
                      (`sleeves/market_expansion_d1.py:218-225`).

**The one exception, and it is excluded rather than swept:** `mx_us100_cash_d1_atr_mean_reversion`
and `mx_us500_...` call `_atr_mean_reversion_signal(bars, signal_idx, risk)` —
`market_expansion_d1.py:211` — so for those two the stop distance is an INPUT to the entry
signal and a stop-width cell changes which trades exist. Rescaling them here would be the
error the agreement warns about, so their stop-width cells are not run and the reason is
published in the artifact.

THE TWO TARGET CONVENTIONS, SWEPT SEPARATELY BECAUSE THE SLEEVES DISAGREE
-------------------------------------------------------------------------
`metals_core` and the `mx_*` family set `target_dist = R * stop_dist`, so their native
wider-stop behaviour scales the target with the stop and holds target-R fixed. `fx_jpy`,
`fx_jpy_ny` and `vss_fxcross` set `target_dist = M * ATR` INDEPENDENTLY of the stop, so
their native behaviour holds the target's PRICE distance fixed and lets target-R shrink as
1/k. Both are run for every sleeve and labelled `target_scales` / `target_fixed`, with the
native one marked — because AA's frontier algebra `net(k) = (gross - c_var)/k - c_fixed`
assumes the scaling reading, and under the fixed-price reading gross-in-R behaves differently.

THE TRAIL RULE (B613) IS LAW HERE
---------------------------------
Every trail cell is run twice, at `trail_lag_extremes` False (production `simulate`
semantics: a trail can arm and fill inside one bar at `high - gap`) and True (the running
extreme comes only from strictly earlier bars). Both bounds are published for every cell.
95.8 % of `asian_fade`'s apparent trail gain was intrabar sequencing; no cell here is
reported at the production bound alone.

MULTIPLICITY IS AA'S FAMILY, SO THE A/B IS A CLEAN A/B
-------------------------------------------------------
Each variant is gated with the FULL 32-sleeve family, the target sleeve's records swapped and
every other sleeve left at its as-walked labelling, `declared_family_size=69` exactly as AA
set it. Gating one sleeve alone would change its BH rank and make the q-value incomparable
to the baseline it is being measured against. The full-family gate costs 1.2 s, so there was
no reason to approximate it.

Every variant is appended to the shared trial ledger. The count deflates everyone's
admission statistics, including this session's — that is the design.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import math
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import effective_registry, winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.costs.model import _mt5_dow  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.registry import build_symbol_allowlist  # noqa: E402
from src.utils.broker_clock import (  # noqa: E402
    broker_naive_to_utc,
    resolve_rule,
    utc_to_broker_naive,
)

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
UNITS = HERE / "AD_TIMESTOP_UNITS_V1.json"
#: A supplementary run writes beside the main artifact rather than over it, so a targeted
#: re-run of two sleeves cannot destroy a 24-sleeve sweep. `ad_frontier_analysis.py` merges
#: any `EXIT_FRONTIER_V1*.json` it finds, later files winning per sleeve.
OUT = HERE / f"EXIT_FRONTIER_V1{os.environ.get('AD_OUT_SUFFIX', '')}.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
MAXBARS = 80
DECLARED_FAMILY = 69          # AA's: 32 judged + 12 W looks + 25 X looks

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}

#: Sleeves whose entry signal READS the stop distance, so a stop-width cell is not a
#: geometry change but a different candidate set. Excluded from stop-width sweeps.
STOP_DEPENDENT_SIGNAL = {
    "mx_us100_cash_d1_atr_mean_reversion": "market_expansion_d1.py:211 "
                                           "_atr_mean_reversion_signal(bars, idx, risk)",
    "mx_us500_cash_d1_atr_mean_reversion": "market_expansion_d1.py:211 "
                                           "_atr_mean_reversion_signal(bars, idx, risk)",
}

#: How each sleeve's generator sets `target_dist`, read at source. Decides which stop-width
#: target convention is NATIVE (the other is still swept, and labelled).
TARGET_CONVENTION = {
    "metals_core": ("scales_with_stop", "sleeves/metals.py:204 target_dist=_runner_R(vr)*sd"),
    "metals_softband": ("scales_with_stop", "sleeves/metals.py:218"),
    "metals_ob_micro": ("scales_with_stop", "sleeves/metals_ob_micro.py:133-134"),
    "crypto": ("scales_with_stop", "sleeves/crypto.py:66 target_dist=TARGET_R*sd"),
    "energy_agri": ("scales_with_stop", "sleeves/energy_agri.py:63 target_dist=4.0*sd"),
    "idxrev": ("scales_with_stop", "sleeves/index_jpy.py:57 target_dist=IDX_TGT_R*sd"),
    "vol_compression": ("scales_with_stop", "sleeves/vol_compression.py:58"),
    "sub_mid_dn_revert": ("scales_with_stop", "sleeves/substrate.py:114 td=target_R*sd"),
    "sub_xvol_pullback": ("scales_with_stop", "sleeves/substrate.py:114 td=target_R*sd"),
    "fx_jpy": ("fixed_price", "sleeves/fx_jpy.py:203 target_dist=_TGT_M*a (ATR, not stop)"),
    "fx_jpy_ny": ("fixed_price", "sleeves/fx_jpy.py:203 target_dist=_TGT_M*a (ATR, not stop)"),
    "vss_fxcross_london_up_low": ("fixed_price",
                                  "sleeves/vss_fxcross_london_up_low.py:181 TGT_ATR*atr_i"),
    "metal_session_reversion": ("no_target",
                                "sleeves/metal_session_reversion.py:116 target_dist=None"),
    "kz_london_crypto_low": ("no_target", "sleeves/kz_london_crypto_low.py:102"),
    "ny_crypto_momentum": ("no_target", "sleeves/ny_crypto_momentum.py:111"),
}
for _s in (
    "mx_avausd_d1_donchian_20_breakout", "mx_btcusd_d1_donchian_20_breakout",
    "mx_cadjpy_d1_volume_surge_reversal", "mx_ethusd_d1_donchian_20_breakout",
    "mx_ger40_cash_d1_volume_surge_reversal", "mx_jp225_cash_d1_volume_surge_reversal",
    "mx_nzdjpy_d1_donchian_20_breakout", "mx_us30_cash_d1_volume_surge_reversal",
    "mx_us100_cash_d1_atr_mean_reversion", "mx_us500_cash_d1_atr_mean_reversion",
):
    TARGET_CONVENTION[_s] = ("scales_with_stop",
                             "sleeves/market_expansion_d1.py:225 target_dist=TARGET_R*risk")


# =====================================================================================
# variants


@dataclass(frozen=True)
class Variant:
    name: str
    family: str
    time_stop_bars: int | None = None
    trail_arm_r: float | None = None
    trail_gap_r: float | None = None
    trail_lag_extremes: bool = False
    stop_mult: float = 1.0
    #: "native" | "scales_with_stop" | "fixed_price" | "fixed_r" | "no_target"
    target_mode: str = "native"
    target_r: float | None = None
    flat_hour: int | None = None
    #: None | "every_rollover" | "triple_swap_only"
    flat_rule: str | None = None
    partial_at_r: float | None = None
    partial_frac: float = 0.5
    be_stop_after_partial: bool = True
    note: str = ""

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()
             if v not in (None, False, "") and not (k in ("stop_mult",) and v == 1.0)
             and not (k == "partial_frac" and self.partial_at_r is None)
             and not (k == "be_stop_after_partial" and self.partial_at_r is None)}
        d["name"], d["family"] = self.name, self.family
        return d


AS_WALKED = Variant(name="as_walked", family="baseline",
                    note="AA's labelling, reproduced. The A/B base for every cell below.")


# =====================================================================================
# substrate


def load_bars() -> tuple[dict, dict, callable]:
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files: dict[tuple[str, int], str] = {}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is None:
            continue
        files[(res(sym), tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    series: dict[tuple[str, int], tuple[list, list]] = {}
    index: dict[tuple[str, int], dict] = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        series[key] = ([Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                        for r in rows],
                       [dt.datetime.fromisoformat(r["time"]) for r in rows])
        index[key] = {ts: i for i, ts in enumerate(series[key][1])}
    return series, index, res


def zero_carry_costs(path: Path):
    """The same cost artifact with every swap rate zeroed — AA's counterfactual, verbatim.

    Copied from `phase6/receipts/aa_estate_walk.py:105-134` rather than imported, because
    that file is a receipt script and importing across receipts couples two sessions'
    artifacts. It is a COUNTERFACTUAL: nobody trades at zero swap. Its only job here is to
    bound what a carry repair could possibly be worth.
    """
    from src.costs.model import BrokerTrueCosts

    doc = json.loads(path.read_text())
    for acct in doc.get("accounts", {}).values():
        for rec in (acct.get("instruments") or {}).values():
            sw = rec.get("swap") or {}
            sw["swap_long"] = 0.0
            sw["swap_short"] = 0.0
            spec = rec.get("spec") or {}
            spec["swap_long"] = 0.0
            spec["swap_short"] = 0.0
            rec["swap"], rec["spec"] = sw, spec
    doc["version"] = f"{doc.get('version')}+zero_carry_counterfactual"
    return BrokerTrueCosts(doc, source=path)


def swap3_weekday(costs, symbol: str, account: str) -> int | None:
    try:
        rec = costs.doc["accounts"][account]["instruments"][symbol]
    except Exception:
        return None
    return (rec.get("spec") or {}).get("swap_rollover3days")


def next_rollover_utc(entry_utc: dt.datetime, rule, only_weekday: int | None,
                      horizon_days: int = 90) -> dt.datetime | None:
    """First broker midnight strictly after `entry_utc`, optionally only on one weekday.

    `only_weekday` is MT5 numbering (Sunday=0), matching `swap_rollover3days` and
    `costs.model._mt5_dow`. Saturday and Sunday midnights are skipped because
    `rollover_nights` does not charge them.
    """
    local = utc_to_broker_naive(entry_utc, rule)
    day = (local + dt.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    for _ in range(horizon_days):
        dow = _mt5_dow(day)
        if dow not in (0, 6) and (only_weekday is None or dow == int(only_weekday)):
            return broker_naive_to_utc(day, rule)
        day += dt.timedelta(days=1)
    return None


def resimulate(rows: list[dict], variant: Variant, series: dict, index: dict,
               costs, account: str, rule) -> tuple[list[dict], dict]:
    """AA's rows re-labelled under `variant`. Returns (rows, telemetry)."""
    out: list[dict] = []
    tel = collections.Counter()
    for r in rows:
        tf = int(r["timeframe"])
        key = (r["symbol"], tf)
        if key not in index:
            tel["skip_no_series"] += 1
            continue
        i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            tel["skip_bar_not_found"] += 1
            continue
        bars, times = series[key]
        if i + 2 >= len(bars):
            tel["skip_no_room"] += 1
            continue

        stop = float(r["sl_distance_price"]) * variant.stop_mult
        native_target = r.get("target_dist")
        mode = variant.target_mode
        if mode == "native":
            target = native_target
        elif mode == "scales_with_stop":
            target = (native_target * variant.stop_mult) if native_target else None
        elif mode == "fixed_price":
            target = native_target
        elif mode == "fixed_r":
            target = (variant.target_r * stop) if variant.target_r else None
        elif mode == "no_target":
            target = None
        else:
            raise ValueError(f"unknown target_mode {mode!r}")

        pol = ExitPolicy(
            target_dist=target,
            trail_arm=(variant.trail_arm_r * stop) if variant.trail_arm_r else None,
            trail_gap=(variant.trail_gap_r * stop) if variant.trail_gap_r else None,
            maxbars=MAXBARS,
            time_stop_bars=variant.time_stop_bars,
            flat_before_rollover_local_hour=variant.flat_hour,
            partial_at_r=variant.partial_at_r,
            partial_frac=variant.partial_frac,
            be_stop_after_partial=variant.be_stop_after_partial,
            trail_lag_extremes=variant.trail_lag_extremes,
            label=variant.name,
        )
        flat_utc = None
        if variant.flat_rule:
            entry_utc = times[i] + dt.timedelta(minutes=TF_MINUTES[tf])
            wd = (swap3_weekday(costs, r["symbol"], account)
                  if variant.flat_rule == "triple_swap_only" else None)
            if variant.flat_rule == "triple_swap_only" and wd is None:
                tel["skip_no_swap3_weekday"] += 1
            else:
                flat_utc = next_rollover_utc(entry_utc, rule, wd)

        pr = replay(bars, i, int(r["direction"]), stop_dist=stop, policy=pol,
                    times=times, server=SERVER, bar_minutes=TF_MINUTES[tf],
                    flat_before_utc=flat_utc)
        xi = pr.exit_index
        ivl = dt.timedelta(minutes=TF_MINUTES[tf])
        tel[f"exit_{pr.exit_reason}"] += 1
        out.append({
            **r,
            "entry_utc": (times[i] + ivl).isoformat(),
            "exit_utc": (times[xi] + ivl).isoformat(),
            "sl_distance_price": stop,
            "target_dist": target,
            "r_gross": float(winsorize_R(pr.r_gross)),
            "exit_policy": variant.name,
            "exit_reason": pr.exit_reason,
            "mfe_r": round(pr.mfe_r, 6),
            "mae_r": round(pr.mae_r, 6),
            "bars_to_mfe": int(pr.bars_to_mfe),
            "exit_bar_offset": int(xi - i),
            "hold_hours": round((xi - i) * TF_MINUTES[tf] / 60.0, 4),
        })
    return out, dict(tel)


def to_records(rows: list[dict]) -> list[TradeRecord]:
    return [TradeRecord(
        sleeve=r["sleeve"], symbol=r["symbol"],
        entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
        exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
        direction=int(r["direction"]),
        sl_distance_price=float(r["sl_distance_price"]),
        entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
        features={"decision_day": r["decision_day"], "timeframe": r["timeframe"],
                  "hold_hours": r["hold_hours"],
                  "symbol_canonical": r.get("symbol_canonical"),
                  "decision_bar_iso": r.get("decision_bar_iso"),
                  "mfe_r": r.get("mfe_r"), "mae_r": r.get("mae_r"),
                  "bars_to_mfe": r.get("bars_to_mfe"),
                  "exit_reason": r.get("exit_reason"),
                  "exit_policy": r.get("exit_policy"),
                  "r_gross_plain": r.get("r_gross_plain")},
    ) for r in rows]


def allowlist() -> dict:
    al = build_symbol_allowlist()
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    for name, spec in effective_registry(include_clean3=True).items():
        al.setdefault(name, tuple(sorted({resolve(s) for s in (spec.symbols or ())})))
    return al


# =====================================================================================
# reporting one gated variant


def summarize(sv, tel: dict, n_in: int) -> dict:
    diag = sv.diagnostics or {}
    cd = diag.get("cost_decomposition") or {}
    hold = diag.get("holding") or {}
    exc = diag.get("excursion") or {}
    nights = cd.get("swap_nights") or {}
    terms = cd.get("terms") or {}
    return {
        "verdict": sv.verdict.value,
        "n_trades": sv.n_trades,
        "n_resimulated": n_in,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "lifetime_mean_r_per_trade": sv.gates.get("lifetime", {}).get(
            "mean_r_net_per_trade_all_folds"),
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "gates": {g: bool(v.get("pass")) for g, v in sorted(sv.gates.items())},
        "failing_gates": [g for g in ("expectancy", "lifetime", "stability", "robustness",
                                      "significance")
                          if not sv.gates.get(g, {}).get("pass")],
        "oos_positive_fold_frac": sv.gates.get("stability", {}).get("oos_positive_fold_frac"),
        "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
        "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
        "coverage_frac": sv.gates.get("cost_coverage", {}).get("coverage_frac"),
        "mean_gross_r": cd.get("mean_gross_r"),
        "mean_cost_r": cd.get("mean_cost_r"),
        "cost_pct_of_abs_gross": cd.get("cost_pct_of_abs_gross"),
        "largest_cost_term": cd.get("largest_term"),
        "cost_terms_mean_r": {k: (v or {}).get("mean_r") for k, v in sorted(terms.items())},
        "swap_share_of_cost": (terms.get("swap_r") or {}).get("share_of_cost"),
        "swap_nights_mean": nights.get("mean"),
        "swap_nights_median": nights.get("median"),
        "frac_trades_zero_nights": nights.get("frac_zero"),
        "median_hold_hours": hold.get("median_hours"),
        "p90_hold_hours": hold.get("p90_hours"),
        "frac_hold_over_24h": hold.get("frac_over_24h"),
        "mean_mfe_r": exc.get("mean_mfe_r"),
        "mean_mae_r": exc.get("mean_mae_r"),
        "capture_ratio_pooled": exc.get("capture_ratio_pooled"),
        "exit_reasons": {k[5:]: v for k, v in sorted(tel.items()) if k.startswith("exit_")},
        "resim_skips": {k: v for k, v in sorted(tel.items()) if k.startswith("skip_")},
        "primary_prescription": diag.get("primary_prescription"),
    }


# =====================================================================================
# the sweep plan


def plan_for(sleeve: str, tf: int, units: dict) -> list[Variant]:
    """The variant grid for one sleeve. Structured surfaces, never single cells."""
    vs: list[Variant] = [AS_WALKED]
    conv = (TARGET_CONVENTION.get(sleeve) or ("scales_with_stop", "assumed"))[0]
    c = (units.get("sleeve_contracts") or {}).get(sleeve) or {}
    live_ts = c.get("time_stop_in_own_bars")

    # ---- 1. the time-stop surface, on the sleeve's OWN grid ---------------------------
    if tf == TF_D1:
        grid = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30, 40, 60]
    elif tf == TF_H4:
        grid = [2, 3, 4, 6, 8, 12, 16, 20, 30, 40, 60]
    else:
        grid = [2, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64]
    for n in grid:
        if n >= MAXBARS:
            continue
        vs.append(Variant(name=f"time_stop_{n}", family="time_stop", time_stop_bars=n))
    if live_ts:
        n = max(1, int(round(live_ts)))
        if n < MAXBARS and f"time_stop_{n}" not in {v.name for v in vs}:
            vs.append(Variant(name=f"time_stop_{n}", family="time_stop", time_stop_bars=n,
                              note="the LIVE contract, converted (B750)"))

    # ---- 2. the scheduled flats -------------------------------------------------------
    #  hour rule at 0 == "flat before the broker midnight after entry" (B751 semantics)
    for h in (0, 22):
        vs.append(Variant(name=f"prerollover_flat_h{h}", family="prerollover",
                          flat_hour=h))
    vs.append(Variant(name="flat_before_every_rollover", family="swap_aware",
                      flat_rule="every_rollover",
                      note="§5.3 swap-aware exit at threshold 0: no night ever charged"))
    vs.append(Variant(name="flat_before_triple_swap", family="swap_aware",
                      flat_rule="triple_swap_only",
                      note="§5.3 pre-weekend flat: skip only the 3x rollover"))

    # ---- 3. the stop-width surface ----------------------------------------------------
    if sleeve not in STOP_DEPENDENT_SIGNAL:
        for k in (1.25, 1.5, 2.0, 2.5, 3.0):
            for mode in ("scales_with_stop", "fixed_price"):
                if conv == "no_target" and mode == "fixed_price":
                    continue          # no target to hold fixed
                vs.append(Variant(
                    name=f"stop_{k:g}x_{'tgtscale' if mode == 'scales_with_stop' else 'tgtfix'}",
                    family="stop_width", stop_mult=k, target_mode=mode,
                    note=("NATIVE convention" if mode == conv else "counterfactual convention")))

    # ---- 4. the trail surface, BOTH bounds, always ------------------------------------
    #  The sleeve's OWN live arm/gap is added to the grid when it has one, because for the
    #  two `trailing_runner` sleeves the plain `as_walked` baseline is NOT their production
    #  contract — AA labelled them under the trail and this sweep's baseline is plain, so
    #  without these cells the surface would not contain the thing being repaired.
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    live_arm = prof.get("trigger_r") if prof.get("policy") == "trailing_runner" else None
    live_gap = prof.get("trail_gap_r") if prof.get("policy") == "trailing_runner" else None
    arms = sorted({0.5, 1.0, 2.0} | ({float(live_arm)} if live_arm else set()))
    gaps = sorted({0.5, 1.0} | ({float(live_gap)} if live_gap else set()))
    for arm in arms:
        for gap in gaps:
            for lag in (False, True):
                is_live = (live_arm is not None and abs(arm - float(live_arm)) < 1e-9
                           and abs(gap - float(live_gap)) < 1e-9)
                vs.append(Variant(
                    name=f"trail_a{arm:g}_g{gap:g}_{'honest' if lag else 'prod'}",
                    family="trail", trail_arm_r=arm, trail_gap_r=gap,
                    trail_lag_extremes=lag,
                    note=("the LIVE contract (execution_packets.py:57,61)" if is_live else "")))

    # ---- 5. the target surface. The ridge runs high on trend sleeves, so the grid goes
    #         to 8R: the first mx_btcusd run peaked at the grid's own edge (3R), which is
    #         a grid artefact and not a result.
    tgrid = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0)
    if conv != "no_target":
        for tr in tgrid:
            vs.append(Variant(name=f"target_{tr:g}R", family="target",
                              target_mode="fixed_r", target_r=tr))
        vs.append(Variant(name="target_none", family="target", target_mode="no_target"))
    else:
        for tr in tgrid:
            vs.append(Variant(name=f"target_{tr:g}R", family="target",
                              target_mode="fixed_r", target_r=tr,
                              note="the sleeve is natively targetless; this ADDS one"))

    # ---- 6. the partial_be_runner surface (B752) --------------------------------------
    #  For the four sleeves this is the LIVE contract, the `live_contract` cell is the one
    #  the armed book actually runs and AA never simulated. For the others it is a
    #  candidate exit like any other, because "scale out and protect" is the classic
    #  answer to a high-MFE / low-capture sleeve and that is this lane's whole subject.
    live_trigger = prof_trigger(sleeve)
    for trig in (0.5, 1.0, 1.5, 2.0, 3.0):
        vs.append(Variant(name=f"partial_{trig:g}R_be", family="partial",
                          partial_at_r=trig,
                          note=("the LIVE contract (execution_packets.py:44-51)"
                                if live_trigger is not None
                                and abs(trig - live_trigger) < 1e-9 else "")))
        vs.append(Variant(name=f"partial_{trig:g}R_nobe", family="partial",
                          partial_at_r=trig, be_stop_after_partial=False,
                          note="scale out, keep the original stop — isolates the BE move"))
    if live_trigger is not None and live_trigger not in (0.5, 1.0, 1.5, 2.0, 3.0):
        vs.append(Variant(name=f"partial_{live_trigger:g}R_be", family="partial",
                          partial_at_r=live_trigger,
                          note="the LIVE contract (execution_packets.py:44-51)"))
    return vs


def prof_trigger(sleeve: str) -> float | None:
    """The sleeve's LIVE `partial_be_runner` trigger R, or None if that is not its policy."""
    prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
    if prof.get("policy") != "partial_be_runner":
        return None
    t = prof.get("trigger_r")
    return float(t) if t is not None else None


#: The work list, in the prompt's value order. Everything else in AA's 32 is left at its
#: as-walked labelling inside every gate call, which is what makes each row an A/B.
WORK_LIST = [
    "mx_btcusd_d1_donchian_20_breakout",            # item 2 — the carry exit
    "metals_core",                                  # item 3 — 0.59x, live conf 1.0
    "vss_fxcross_london_up_low",                    # item 3 — 0.74x
    "fx_jpy",                                       # item 3 — 1.89x
    "fx_jpy_ny",                                    # items 3+4 — 1.99x + the flat rule
    "metal_session_reversion",                       # item 3 — 2.09x, trail sleeve
    "sub_mid_dn_revert",                            # item 5 — the nearest miss
    "metals_softband",                              # item 5
    "kz_london_crypto_low",                         # item 6 — MFE 3.40, capture -0.037
    "ny_crypto_momentum",                           # item 6 — MFE 2.39, capture 0.004
    "crypto",                                       # item 6 — live; measurement only
    "vol_compression",                              # item 6
    "energy_agri",                                  # item 6 — live
    "mx_us100_cash_d1_atr_mean_reversion",          # item 6 — EXIT_REPAIR row
    "mx_us500_cash_d1_atr_mean_reversion",          # item 6 — EXIT_REPAIR row
    "metals_ob_micro",                              # AA EXIT_REPAIR row
    "idxrev",                                       # AA INVERSE_TEST — the null check
]
#: The rest of the mx_* D1 family. B750 measured that the live time stop truncates 72-90 %
#: of their trades, so the time-stop question is the whole family's, not one sleeve's.
MX_FAMILY = [
    "mx_avausd_d1_donchian_20_breakout", "mx_cadjpy_d1_volume_surge_reversal",
    "mx_ethusd_d1_donchian_20_breakout", "mx_ger40_cash_d1_volume_surge_reversal",
    "mx_jp225_cash_d1_volume_surge_reversal", "mx_nzdjpy_d1_donchian_20_breakout",
    "mx_us30_cash_d1_volume_surge_reversal",
]


def main() -> dict:
    only = [s for s in (os.environ.get("AD_ONLY") or "").split(",") if s]
    t_start = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AD")
    raw = json.load(gzip.open(AA_IN, "rt"))
    units = json.loads(UNITS.read_text())
    tf_of = {s: {"M15": TF_M15, "H4": TF_H4, "D1": TF_D1}[v]
             for s, v in raw["timeframe_by_sleeve"].items()}
    costs = load_broker_true_costs(COSTS)
    costs_zero = zero_carry_costs(COSTS)
    rule = resolve_rule(SERVER)
    series, index, _res = load_bars()
    print(f"loaded {len(series)} bar series in {time.time()-t_start:.0f}s")

    al = allowlist()
    base_spec = OPTIONS["B_balanced"]
    spec = base_spec.with_(spec_id=f"{base_spec.spec_id}_ad_exit_frontier",
                           sleeve_symbol_allowlist=al,
                           declared_family_size=DECLARED_FAMILY)
    baseline_rows = {s: list(rows) for s, rows in raw["trades"].items()}

    # ---- the baseline, and the parity check against AA --------------------------------
    base_res = run_gate({s: to_records(r) for s, r in baseline_rows.items()},
                        spec, costs=costs, diagnose=True, server=SERVER)
    aa_walk = json.loads((REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
                          / "AA_ESTATE_WALK.json").read_text())
    aa_rows = {r["sleeve"]: r for r in aa_walk["runs"]["B_balanced|v1_1"]["rows"]}
    parity = {"n_compared": 0, "identical": 0, "moved": {}}
    for s, sv in base_res.verdicts.items():
        a = aa_rows.get(s)
        if not a:
            continue
        parity["n_compared"] += 1
        same = (a["verdict"] == sv.verdict.value
                and (a["pooled_oos_mean_r"] is None) == (sv.pooled_oos_mean_r is None)
                and (a["pooled_oos_mean_r"] is None
                     or abs(a["pooled_oos_mean_r"] - sv.pooled_oos_mean_r) < 1e-12))
        if same:
            parity["identical"] += 1
        else:
            parity["moved"][s] = {"aa_verdict": a["verdict"], "here": sv.verdict.value,
                                  "aa_pooled": a["pooled_oos_mean_r"],
                                  "here_pooled": sv.pooled_oos_mean_r}
    print(f"baseline parity vs AA B_balanced|v1_1: {parity['identical']}/"
          f"{parity['n_compared']} identical; moved: {sorted(parity['moved'])}")

    # ---- the sweep ---------------------------------------------------------------------
    sleeves = only or (WORK_LIST + MX_FAMILY)
    results: dict[str, dict] = {}
    n_cells = 0
    for sleeve in sleeves:
        rows = baseline_rows.get(sleeve) or []
        if not rows:
            results[sleeve] = {"available": False, "reason": "no generated trades in AA's walk"}
            print(f"\n### {sleeve}: no trades, skipped")
            continue
        tf = tf_of[sleeve]
        prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
        conv, conv_cite = TARGET_CONVENTION.get(sleeve, ("scales_with_stop", "assumed"))
        plan = plan_for(sleeve, tf, units)
        print(f"\n### {sleeve} [{TF_NAME[tf]}] n={len(rows)} — {len(plan)} cells "
              f"(native target convention: {conv})", flush=True)
        cells: dict[str, dict] = {}
        t0 = time.time()
        for v in plan:
            new_rows, tel = resimulate(rows, v, series, index, costs, spec.account, rule)
            if not new_rows:
                cells[v.name] = {"variant": v.as_dict(), "available": False,
                                 "reason": "no trade survived re-simulation",
                                 "resim_skips": tel}
                continue
            recs = {s: to_records(r if s != sleeve else new_rows)
                    for s, r in baseline_rows.items()}
            res = run_gate(recs, spec, costs=costs, diagnose=True, server=SERVER)
            cells[v.name] = {"variant": v.as_dict(),
                             **summarize(res.verdicts[sleeve], tel, len(new_rows))}
            n_cells += 1
            ledger.record(
                mechanism="exit_repair_sweep", sleeve=sleeve, variant=v.as_dict(),
                window="full_archive", spec_sha256=spec.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(
                             res.verdicts[sleeve].verdict.value, "evaluated"),
                metric=res.verdicts[sleeve].pooled_oos_mean_r,
                metric_name="pooled_oos_mean_r",
                note=f"AD exit frontier, {v.family} cell {v.name}",
            )
        # ---- ONE post-hoc composite, stamped as one --------------------------------------
        #  The argmax cell of each family, stacked. This is a 4-dimensional pick from a
        #  swept surface and it is labelled that way everywhere it appears: it is what
        #  wave 8's composition would START from, never a result. Its ledger row carries
        #  the same weight as every other cell, which is the point of the ledger.
        def _argmax(fam: str):
            got = [(c["pooled_oos_mean_r"], n) for n, c in cells.items()
                   if c.get("pooled_oos_mean_r") is not None
                   and (c.get("variant") or {}).get("family") == fam]
            return max(got)[1] if got else None

        picks = {f: _argmax(f) for f in ("stop_width", "target", "time_stop", "partial")}
        by_name = {v.name: v for v in plan}
        sw = by_name.get(picks["stop_width"] or "")
        tg = by_name.get(picks["target"] or "")
        ts = by_name.get(picks["time_stop"] or "")
        pa = by_name.get(picks["partial"] or "")
        comp = Variant(
            name="POST_HOC_COMPOSITE", family="composite",
            stop_mult=(sw.stop_mult if sw else 1.0),
            target_mode=("fixed_r" if tg else (sw.target_mode if sw else "native")),
            target_r=(tg.target_r if tg else None),
            time_stop_bars=(ts.time_stop_bars if ts else None),
            partial_at_r=(pa.partial_at_r if pa else None),
            be_stop_after_partial=(pa.be_stop_after_partial if pa else True),
            note=("argmax of each family stacked: "
                  + ", ".join(f"{k}={v}" for k, v in picks.items() if v)
                  + ". A 4-D pick from a swept surface — the START of a composition, "
                    "never a result."),
        )
        c_rows, c_tel = resimulate(rows, comp, series, index, costs, spec.account, rule)
        if c_rows:
            cr = run_gate({s: to_records(r if s != sleeve else c_rows)
                           for s, r in baseline_rows.items()},
                          spec, costs=costs, diagnose=True, server=SERVER)
            cells[comp.name] = {"variant": comp.as_dict(),
                                **summarize(cr.verdicts[sleeve], c_tel, len(c_rows))}
            n_cells += 1
            ledger.record(
                mechanism="exit_repair_sweep", sleeve=sleeve, variant=comp.as_dict(),
                window="full_archive", spec_sha256=spec.seal(),
                outcome={"ADMIT": "admitted", "REJECT": "rejected",
                         "NOT_EVALUABLE": "not_evaluable"}.get(
                             cr.verdicts[sleeve].verdict.value, "evaluated"),
                metric=cr.verdicts[sleeve].pooled_oos_mean_r,
                metric_name="pooled_oos_mean_r",
                note="AD exit frontier, POST-HOC composite of family argmaxes",
            )

        # ---- the carry CEILING: AA's counterfactual, so every carry cell can be read
        #      against the best any carry repair could possibly do -----------------------
        zc_rows, zc_tel = resimulate(rows, AS_WALKED, series, index, costs, spec.account, rule)
        zc = run_gate({s: to_records(r if s != sleeve else zc_rows)
                       for s, r in baseline_rows.items()},
                      spec, costs=costs_zero, diagnose=True, server=SERVER)
        ceiling = summarize(zc.verdicts[sleeve], zc_tel, len(zc_rows))
        ledger.record(
            mechanism="exit_repair_sweep", sleeve=sleeve,
            variant={**AS_WALKED.as_dict(), "counterfactual": "zero_carry"},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(
                         zc.verdicts[sleeve].verdict.value, "evaluated"),
            metric=zc.verdicts[sleeve].pooled_oos_mean_r,
            metric_name="pooled_oos_mean_r",
            note="AD exit frontier, zero-carry CEILING (counterfactual, not a proposal)",
        )
        n_cells += 1

        # ---- the winning cell at all three spread bands (Session AG's own instruction) --
        scored = [(c["pooled_oos_mean_r"], n) for n, c in cells.items()
                  if c.get("pooled_oos_mean_r") is not None]
        bands: dict = {}
        best_name = max(scored)[1] if scored else None
        # The composite is not in `plan` (it is built from the plan's own argmaxes), and it
        # is frequently the best cell — which is exactly why the band check must be able to
        # find it. Looking only in `plan` raised StopIteration on the third sleeve.
        all_variants = {v.name: v for v in plan}
        all_variants[comp.name] = comp
        if best_name:
            bv = all_variants[best_name]
            b_rows, b_tel = resimulate(rows, bv, series, index, costs, spec.account, rule)
            for band in ("low", "mid", "high"):
                bspec = spec.with_(spec_id=f"{spec.spec_id}_band_{band}", spread_band=band)
                br = run_gate({s: to_records(r if s != sleeve else b_rows)
                               for s, r in baseline_rows.items()},
                              bspec, costs=costs, diagnose=True, server=SERVER)
                bands[band] = summarize(br.verdicts[sleeve], b_tel, len(b_rows))
                n_cells += 1
                ledger.record(
                    mechanism="exit_repair_sweep", sleeve=sleeve,
                    variant={**bv.as_dict(), "spread_band": band},
                    window="full_archive", spec_sha256=bspec.seal(),
                    outcome={"ADMIT": "admitted", "REJECT": "rejected",
                             "NOT_EVALUABLE": "not_evaluable"}.get(
                                 br.verdicts[sleeve].verdict.value, "evaluated"),
                    metric=br.verdicts[sleeve].pooled_oos_mean_r,
                    metric_name="pooled_oos_mean_r",
                    note=f"AD exit frontier, best cell {best_name} at spread_band={band}",
                )

        base = cells.get("as_walked") or {}
        bp = base.get("pooled_oos_mean_r")
        print(f"{'cell':34s} {'verdict':13s} {'R/day':>9s} {'dR/day':>9s} {'gross/t':>8s} "
              f"{'cost%':>6s} {'nights':>7s} {'hold_h':>8s} {'capt':>6s} {'q':>7s}")
        for name, c in cells.items():
            if not c.get("verdict"):
                print(f"{name:34s} {'-':13s} {c.get('reason','')}")
                continue
            f = lambda x, p=5, w=9: (f"{'-':>{w}s}" if x is None else f"{x:{w}.{p}f}")  # noqa: E731
            d = (None if bp is None or c["pooled_oos_mean_r"] is None
                 else c["pooled_oos_mean_r"] - bp)
            print(f"{name:34s} {c['verdict']:13s} {f(c['pooled_oos_mean_r'])} {f(d)} "
                  f"{f(c['mean_gross_r'],4,8)} {f(c['cost_pct_of_abs_gross'],1,6)} "
                  f"{f(c['swap_nights_mean'],3,7)} {f(c['median_hold_hours'],2,8)} "
                  f"{f(c['capture_ratio_pooled'],3,6)} {f(c['q_value'],4,7)}")
        print(f"{'CEILING zero-carry':34s} {ceiling['verdict']:13s} "
              f"{ceiling['pooled_oos_mean_r']} q={ceiling['q_value']}  "
              f"<- the best ANY carry repair could reach")
        if bands:
            for b, v in bands.items():
                print(f"{'  band ' + b + ' (' + best_name + ')':34s} {v['verdict']:13s} "
                      f"{v['pooled_oos_mean_r']} q={v['q_value']} cov={v['coverage_frac']}")

        results[sleeve] = {
            "available": True,
            "timeframe": TF_NAME[tf],
            "n_trades_as_walked": len(rows),
            "live_exit_contract": dict(prof),
            "zero_carry_ceiling": {
                "what": ("the as-walked labelling gated with every swap rate forced to zero "
                         "— AA's counterfactual. No exit repair can beat it, because no exit "
                         "repair can charge less than nothing for carry. A carry cell that "
                         "does not close the gap to this row is not failing to be clever; "
                         "the gap is the most carry could ever have been worth."),
                **ceiling,
            },
            "best_cell_at_spread_bands": {
                "cell": best_name,
                "why": ("Session AG measured that the 37-day cost snapshot's era bias has NO "
                        "single sign (EURUSD 2000-2003 at 50x, XAUUSD 2020-2024 at 0.18x), so "
                        "a cell that only wins at the flat snapshot has not been shown to win"),
                "bands": bands,
            },
            "live_time_stop_in_own_bars": (units.get("sleeve_contracts") or {}).get(
                sleeve, {}).get("time_stop_in_own_bars"),
            "native_target_convention": {"convention": conv, "source": conv_cite},
            "stop_width_swept": sleeve not in STOP_DEPENDENT_SIGNAL,
            "stop_width_excluded_because": STOP_DEPENDENT_SIGNAL.get(sleeve),
            "seconds": round(time.time() - t0, 1),
            "cells": cells,
        }
        print(f"  {len(plan)} cells in {time.time()-t0:.0f}s", flush=True)

    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    out = {
        "schema": "gtos.walkforward.exit_frontier.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AD",
        "blocks": "B752-B7xx",
        "source_trades": str(AA_IN.relative_to(REPO)),
        "source_generated_by": raw.get("generated_by"),
        "timestop_units": str(UNITS.relative_to(REPO)),
        "cost_artifact": str(COSTS.relative_to(REPO)),
        "gate": {"option": "B_balanced", "spec_id": spec.spec_id,
                 "spec_sha256": spec.seal(), "account": spec.account,
                 "declared_family_size": DECLARED_FAMILY,
                 "note": ("every cell is gated with the FULL 32-sleeve family, the target "
                          "sleeve's records swapped and every other sleeve left at its "
                          "as-walked labelling, so each row is a clean A/B and the BH rank "
                          "is comparable to the baseline")},
        "baseline_parity_vs_aa": parity,
        "maxbars": MAXBARS,
        "method": {
            "resimulation": ("AA's stored intents (decision_bar_iso indexes the archive "
                             "series exactly) re-labelled through walkforward.exits.replay, "
                             "which is fuzz-verified identical to primitives.simulate_detail"),
            "stop_width": ("a k-x stop is applied as sl_distance_price*k with the target "
                           "under BOTH conventions; legitimate without re-running the "
                           "generator because for these sleeves the entry signal does not "
                           "read the stop distance (per-sleeve citations in the module "
                           "docstring). The two ATR-mean-reversion sleeves DO read it and "
                           "are excluded from stop-width cells."),
            "trail": ("every trail cell run at trail_lag_extremes False (production) and "
                      "True (intrabar-honest); both bounds published, neither called the "
                      "answer (B613)"),
            "scheduled_flats": ("prerollover_flat_h0 is the corrected close-based rule "
                                "(B751); flat_before_every_rollover and "
                                "flat_before_triple_swap use the new flat_before_utc "
                                "primitive with the rollover instant priced from the cost "
                                "artifact's swap_rollover3days"),
        },
        "cost_look_ahead": {
            "measured_window": ["2026-06-18", "2026-07-24"],
            "applied_to": "every trade in the panel regardless of era",
            "direction": ("no single sign — Session AG measured EURUSD 2000-2003 at 50x the "
                          "snapshot and XAUUSD 2020-2024 at 0.18x. Winning cells are re-run "
                          "at spread_band high/mid/low in the band check below."),
        },
        "trial_ledger": nt,
        "n_cells_gated": n_cells,
        "seconds_total": round(time.time() - t_start, 1),
        "sleeves": results,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({n_cells} cells, "
          f"{time.time()-t_start:.0f}s)")
    print(f"trial ledger: {nt['n_prospective_look_events']} look events; "
          f"n_trials {nt['n_trials']} (basis {nt['basis']})")
    return out


if __name__ == "__main__":
    main()
