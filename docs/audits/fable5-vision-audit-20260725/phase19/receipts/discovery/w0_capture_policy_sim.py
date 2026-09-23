"""w0-capture step 3: reproduce the engine's exit policy, then price its dials.

The January pool's every row carries ``dynamic_geometry_policy=momentum_exhaustion``.
``selected_execution_policy_spec_for_replay`` (v4_timewarp:60738-60765) builds
``momentum_exhaustion_policy(trigger_r=1.0, pullback_r=0.4, final_target_r=2.0)``
and ``simulate_policy`` (src/research/dynamic_execution_policy.py:335-535) gives
that policy TERMINAL AUTHORITY over the raw fixed 2R bracket.

The giveback branch (dynamic_execution_policy.py:503-535) is the exit that closes
a winner below target:

    best_mfe = max(best_mfe, obs.high_r)                    # :393
    ...
    if best_mfe >= trailing_trigger_r:                      # :506
        giveback_exit_r = best_mfe - giveback_close_r       # :508
        if obs.low_r <= giveback_exit_r:                    # :509
            return close(reason="giveback_close", exit_r=giveback_exit_r)

``best_mfe`` already contains THIS bar's high, so the exit is decided against the
same bar's low: an intrabar giveback.  This script reproduces it, then re-runs the
same paths with the dials moved, and with a bar-close-only (no look-ahead) variant.
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
LANE_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence"
    "/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
M1_DIR = LANE_ROOT / "sources/bars/bridge_ftmo_m1_202601"
MANIFEST = LANE_ROOT / "manifests/january_2026.json"
POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
HORIZON_MIN = 120


def epoch_us(w: dt.datetime) -> int:
    return int(w.timestamp() * 1_000_000)


def load_m1():
    manifest = json.loads(MANIFEST.read_text())
    want = {}
    for raw in manifest.get("bar_sources") or []:
        if raw.get("timeframe") == "M1" and raw.get("source_family") == "bridge_ftmo_m1_202601":
            want[str(raw.get("mapped_symbol") or raw.get("symbol"))] = int(raw.get("row_count") or 0)
    out = {}
    for sym, rows in sorted(want.items()):
        path = M1_DIR / f"{sym}_M1.csv"
        t, o, h, l, c = [], [], [], [], []
        with path.open("r", encoding="utf-8") as fh:
            rd = csv.reader(fh)
            next(rd)
            for r in rd:
                t.append(epoch_us(dt.datetime.fromisoformat(r[0])))
                o.append(float(r[1])); h.append(float(r[2])); l.append(float(r[3])); c.append(float(r[4]))
        assert len(t) == rows, (sym, len(t), rows)
        out[sym] = (np.asarray(t, np.int64), np.asarray(o), np.asarray(h), np.asarray(l), np.asarray(c))
    return out


def simulate(open_r, high_r, low_r, close_r, *, trigger, giveback, final_target,
             stop_r=-1.0, same_bar="conservative", lookahead=True):
    """Faithful re-implementation of the momentum_exhaustion branch of
    src/research/dynamic_execution_policy.py::simulate_policy.

    Returns (final_r, reason_code).  reason codes:
      1 stop_loss  2 final_target  3 giveback_close  4 stop_first_same_bar
      5 horizon_mark  6 no_bars
    """
    n = len(high_r)
    if n == 0:
        return None, 6
    best = -np.inf
    prev_best = -np.inf
    for i in range(n):
        prev_best = best
        best = high_r[i] if high_r[i] > best else best
        stop_hit = low_r[i] <= stop_r
        final_hit = final_target is not None and high_r[i] >= final_target
        if stop_hit and final_hit:
            if same_bar == "conservative":
                return stop_r, 4
            stop_hit = False
        if stop_hit:
            return stop_r, 1
        if final_hit:
            return float(final_target), 2
        if giveback is not None:
            ref = best if lookahead else prev_best
            if ref >= trigger:
                gx = ref - giveback
                if low_r[i] <= gx:
                    return float(gx), 3
    return float(max(-1.0, min(close_r[n - 1], final_target if final_target is not None else close_r[n - 1]))), 5


ARMS = [
    ("engine_momentum_exhaustion_trig1.0_give0.4", dict(trigger=1.0, giveback=0.4, final_target=2.0, lookahead=True)),
    ("no_giveback_pure_2R_bracket", dict(trigger=1.0, giveback=None, final_target=2.0, lookahead=True)),
    ("giveback_0.2", dict(trigger=1.0, giveback=0.2, final_target=2.0, lookahead=True)),
    ("giveback_0.6", dict(trigger=1.0, giveback=0.6, final_target=2.0, lookahead=True)),
    ("giveback_0.8", dict(trigger=1.0, giveback=0.8, final_target=2.0, lookahead=True)),
    ("giveback_1.0", dict(trigger=1.0, giveback=1.0, final_target=2.0, lookahead=True)),
    ("giveback_1.5", dict(trigger=1.0, giveback=1.5, final_target=2.0, lookahead=True)),
    ("trigger_1.5_give0.4", dict(trigger=1.5, giveback=0.4, final_target=2.0, lookahead=True)),
    ("trigger_1.8_give0.4", dict(trigger=1.8, giveback=0.4, final_target=2.0, lookahead=True)),
    ("engine_dials_NO_intrabar_lookahead", dict(trigger=1.0, giveback=0.4, final_target=2.0, lookahead=False)),
    ("giveback_0.4_target_3R", dict(trigger=1.0, giveback=0.4, final_target=3.0, lookahead=True)),
    ("no_giveback_target_3R", dict(trigger=1.0, giveback=None, final_target=3.0, lookahead=True)),
    ("no_giveback_target_1R", dict(trigger=1.0, giveback=None, final_target=1.0, lookahead=True)),
    ("no_giveback_target_1.5R", dict(trigger=1.0, giveback=None, final_target=1.5, lookahead=True)),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("W0_CAPTURE_POLICY_SIM_V1.json"))
    args = ap.parse_args()

    series = load_m1()
    rows = []
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            rows.append(r)
    n = len(rows)

    gross_rec = np.full(n, np.nan)
    fam = np.empty(n, dtype=object)
    cost = np.full(n, np.nan)
    arm_r = {name: np.full(n, np.nan) for name, _ in ARMS}
    arm_reason = {name: np.zeros(n, dtype=np.int8) for name, _ in ARMS}

    slices = []
    for i, r in enumerate(rows):
        fam[i] = r.get("origin_family")
        if r.get("cost_r") is not None:
            cost[i] = float(r["cost_r"])
        if r.get("opportunity_net_proxy_r") is not None and r.get("cost_r") is not None:
            gross_rec[i] = float(r["opportunity_net_proxy_r"]) + float(r["cost_r"])
        sym = r["symbol"]
        t, o, h, l, c = series[sym]
        entry = float(r["entry_price"]); stop = float(r["stop_loss"])
        side = str(r["side"]).upper()
        risk = abs(entry - stop)
        d = epoch_us(dt.datetime.fromisoformat(r["decision_time_utc"]))
        s = int(np.searchsorted(t, d, side="right"))
        e = int(np.searchsorted(t, d + HORIZON_MIN * 60_000_000, side="right"))
        if s >= e or risk <= 0:
            slices.append(None)
            continue
        if side == "LONG":
            hr = (h[s:e] - entry) / risk
            lr = (l[s:e] - entry) / risk
            orr = (o[s:e] - entry) / risk
            cr = (c[s:e] - entry) / risk
        else:
            hr = (entry - l[s:e]) / risk
            lr = (entry - h[s:e]) / risk
            orr = (entry - o[s:e]) / risk
            cr = (entry - c[s:e]) / risk
        slices.append((orr, hr, lr, cr))

    for name, kw in ARMS:
        out_r = arm_r[name]; out_x = arm_reason[name]
        for i, sl in enumerate(slices):
            if sl is None:
                out_x[i] = 6
                continue
            orr, hr, lr, cr = sl
            v, why = simulate(orr, hr, lr, cr, **kw)
            out_r[i] = np.nan if v is None else v
            out_x[i] = why

    ok = np.isfinite(gross_rec)
    engine = arm_r["engine_momentum_exhaustion_trig1.0_give0.4"]
    d = engine - gross_rec
    recon = {
        "n": int(ok.sum()),
        "match_within_0p02R": int((ok & (np.abs(d) <= 0.02)).sum()),
        "match_share": float((ok & (np.abs(d) <= 0.02)).sum() / ok.sum()),
        "match_within_0p10R": float((ok & (np.abs(d) <= 0.10)).sum() / ok.sum()),
        "mean_abs_diff_R": float(np.nanmean(np.abs(d[ok]))),
        "mean_signed_diff_R": float(np.nanmean(d[ok])),
        "sim_gross_mean_R": float(np.nanmean(engine[ok])),
        "recorded_gross_mean_R": float(np.nanmean(gross_rec[ok])),
    }

    reasons = {1: "stop_loss", 2: "final_target", 3: "giveback_close", 4: "stop_first_same_bar", 5: "horizon_mark", 6: "no_bars"}

    def summarize(vals, why, mask):
        v = vals[mask]
        w = why[mask]
        wins = v[v > 0]
        loss = v[v < 0]
        rc = collections.Counter(w.tolist())
        return {
            "n": int(mask.sum()),
            "gross_mean_R": float(np.nanmean(v)),
            "net_frozen_cost_R": float(np.nanmean(v - cost[mask])),
            "win_rate": float(np.mean(v > 0)),
            "mean_winner_R": float(wins.mean()) if len(wins) else None,
            "mean_loser_R": float(loss.mean()) if len(loss) else None,
            "payoff_ratio": float(abs(wins.mean() / loss.mean())) if len(wins) and len(loss) else None,
            "exit_reason_share": {reasons[k]: float(v2 / mask.sum()) for k, v2 in sorted(rc.items())},
        }

    fvg = ok & (fam == "current_fvg_fill")
    nb = ok & (fam != "current_breaker_re_entry")
    arms_out = []
    for name, kw in ARMS:
        arms_out.append(
            {
                "arm": name,
                "dials": {k: (None if v is None else v) for k, v in kw.items()},
                "all": summarize(arm_r[name], arm_reason[name], ok),
                "ex_current_breaker_re_entry": summarize(arm_r[name], arm_reason[name], nb),
                "current_fvg_fill": summarize(arm_r[name], arm_reason[name], fvg),
            }
        )

    # recorded book, for reference
    rec_summary = {
        "all": {
            "n": int(ok.sum()),
            "gross_mean_R": float(np.nanmean(gross_rec[ok])),
            "net_frozen_cost_R": float(np.nanmean(gross_rec[ok] - cost[ok])),
            "win_rate": float(np.mean(gross_rec[ok] > 0)),
            "mean_winner_R": float(gross_rec[ok][gross_rec[ok] > 0].mean()),
            "mean_loser_R": float(gross_rec[ok][gross_rec[ok] < 0].mean()),
        },
        "current_fvg_fill": {
            "n": int(fvg.sum()),
            "gross_mean_R": float(np.nanmean(gross_rec[fvg])),
        },
    }

    # per-family, engine arm vs no-giveback arm
    per_fam = []
    for f in sorted({str(x) for x in fam}):
        m = ok & (fam == f)
        if m.sum() == 0:
            continue
        eng = float(np.nanmean(arm_r["engine_momentum_exhaustion_trig1.0_give0.4"][m]))
        pure = float(np.nanmean(arm_r["no_giveback_pure_2R_bracket"][m]))
        per_fam.append(
            {
                "family": f,
                "n": int(m.sum()),
                "recorded_gross_mean_R": float(np.nanmean(gross_rec[m])),
                "sim_engine_gross_mean_R": eng,
                "sim_no_giveback_gross_mean_R": pure,
                "giveback_cost_R_per_trade": pure - eng,
                "giveback_exit_share": float(np.mean(arm_reason["engine_momentum_exhaustion_trig1.0_give0.4"][m] == 3)),
                "mean_cost_R": float(np.nanmean(cost[m])),
                "no_giveback_net_frozen_R": pure - float(np.nanmean(cost[m])),
            }
        )
    per_fam.sort(key=lambda r: -r["giveback_cost_R_per_trade"] * r["n"])

    res = {
        "schema": "gtos-w0-capture-policy-sim-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "broker_live_authority": False,
        "horizon_minutes": HORIZON_MIN,
        "source_citations": {
            "policy_selected_for_every_january_row": "pool field dynamic_geometry_policy == momentum_exhaustion (27658/27658)",
            "policy_spec_built_at": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:60738-60765",
            "policy_given_terminal_authority_at": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:62060-62078 (composition_mode selected_policy_only)",
            "giveback_branch": "src/research/dynamic_execution_policy.py:503-535",
            "best_mfe_includes_current_bar_high": "src/research/dynamic_execution_policy.py:393",
            "default_pullback_r": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:60739-60748 safe_float(..., 0.4)",
            "default_trigger_r": "src/research_infra/v4_timewarp_simulated_live_research_loop.py:60715 safe_float(target_destination.get('trigger_r'), 1.0)",
        },
        "reconciliation_sim_vs_sealed": recon,
        "recorded": rec_summary,
        "arms": arms_out,
        "per_family_giveback_cost": per_fam,
    }
    args.out.write_text(json.dumps(res, indent=1, sort_keys=True))

    print(json.dumps(recon, indent=1))
    print("\narm                                        n      gross    netFroz   win   winMean losMean  giveback%")
    for a in arms_out:
        s = a["all"]
        gs = s["exit_reason_share"].get("giveback_close", 0.0)
        print(
            f"{a['arm']:<42} {s['n']:>5} {s['gross_mean_R']:+.4f} {s['net_frozen_cost_R']:+.4f} "
            f"{s['win_rate']:.3f} {(s['mean_winner_R'] or 0):+.3f} {(s['mean_loser_R'] or 0):+.3f}  {gs:.3f}"
        )
    print("\nex-breaker:")
    for a in arms_out:
        s = a["ex_current_breaker_re_entry"]
        print(f"{a['arm']:<42} {s['n']:>5} gross={s['gross_mean_R']:+.4f} netFroz={s['net_frozen_cost_R']:+.4f} win={s['win_rate']:.3f}")
    print("\ncurrent_fvg_fill:")
    for a in arms_out:
        s = a["current_fvg_fill"]
        print(f"{a['arm']:<42} {s['n']:>5} gross={s['gross_mean_R']:+.4f} netFroz={s['net_frozen_cost_R']:+.4f} win={s['win_rate']:.3f}")
    print("\nper family giveback cost:")
    for r in per_fam:
        print(
            f"{r['family']:<32} n={r['n']:>5} rec={r['recorded_gross_mean_R']:+.4f} eng={r['sim_engine_gross_mean_R']:+.4f} "
            f"pure={r['sim_no_giveback_gross_mean_R']:+.4f} cost={r['giveback_cost_R_per_trade']:+.4f} "
            f"gbShare={r['giveback_exit_share']:.3f} pureNetFroz={r['no_giveback_net_frozen_R']:+.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
