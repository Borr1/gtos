#!/usr/bin/env python3
"""EURGBP × vss_fxcross_london Dig-style HOLD-span replay — 2026-09-20.

Tape: multiyear/EURGBP_M15_from_mt5.csv (host-local).
Signal: Dig-style vss_fxcross_london_proxy (affinity formula; causal ORB impulse).
Fill: Dig PRIMARY adapted — entry=signal close; structure stop=opp ORB; TP=1R;
      time_stop=32; stop-before-tp. Disclosure 3R same signal.
No XAU geometry port. Cost never kill. place=false. No NEWS invent.
TRAIN<=2021 impossible if tape starts >=2022 → HOLD-span label.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

TAPE = Path("/workspace/gtos/research/warroom_20260920/multiyear/EURGBP_M15_from_mt5.csv")
OUT_DIR = Path("/workspace/gtos/research/warroom_20260920")
MULTI = OUT_DIR / "multiyear"
BLOTTER_1R = MULTI / "blotter_HOLD_EURGBP_vss_fxcross_london_proxy_v0_1R.jsonl"
BLOTTER_3R = MULTI / "blotter_HOLD_EURGBP_vss_fxcross_london_proxy_dig3R.jsonl"
MD = OUT_DIR / "EURGBP_VSS_MULTIYEAR_20260920.md"
JS = OUT_DIR / "EURGBP_VSS_MULTIYEAR_20260920.json"

VSS_ORB_BARS = 6
TIME_STOP = 32
TRAIN_END = datetime(2021, 12, 31, 23, 59, 59)
HOLD_START = datetime(2022, 1, 1, 0, 0, 0)
WR_FLOOR = 0.40
ASOF_ICT = "2026-09-20 14:28 ICT"


def atr14(h, l, c, n=14):
    out = np.full(len(c), np.nan)
    tr = np.zeros(len(c))
    tr[0] = h[0] - l[0]
    for i in range(1, len(c)):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    for i in range(n - 1, len(c)):
        out[i] = float(np.mean(tr[i - n + 1 : i + 1]))
    return out


def load_tape(path: Path):
    times, o, h, l, c, v = [], [], [], [], [], []
    with path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            times.append(datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S"))
            o.append(float(row["open"]))
            h.append(float(row["high"]))
            l.append(float(row["low"]))
            c.append(float(row["close"]))
            v.append(float(row.get("volume") or 0))
    return (
        times,
        np.asarray(o),
        np.asarray(h),
        np.asarray(l),
        np.asarray(c),
        np.asarray(v),
    )


def sig_vss_fxcross_london_proxy(o, h, l, c, atr, hours):
    """Causal Dig-style proxy (same formula as affinity_scoreboard)."""
    n = len(c)
    sig = np.zeros(n, dtype=bool)
    side = np.zeros(n, dtype=np.int8)
    sp = np.full(n, np.nan)
    i = 20
    while i < n:
        if hours[i] != 7:
            i += 1
            continue
        orb_end = min(i + VSS_ORB_BARS, n)
        if orb_end - i < VSS_ORB_BARS:
            i += 1
            continue
        if hours[orb_end - 1] > 8:
            i += 1
            continue
        orb_hi = float(h[i:orb_end].max())
        orb_lo = float(l[i:orb_end].min())
        impulse = float(c[orb_end - 1] - o[i])
        if abs(impulse) < 1e-12:
            i = orb_end
            continue
        impulse_side = 1 if impulse > 0 else -1
        j = orb_end
        fired = False
        while j < n and hours[j] >= 7 and hours[j] < 21:
            if not fired and np.isfinite(atr[j]) and atr[j] > 0:
                if impulse_side > 0 and c[j] > orb_hi:
                    sig[j] = True
                    side[j] = 1
                    sp[j] = orb_lo
                    fired = True
                elif impulse_side < 0 and c[j] < orb_lo:
                    sig[j] = True
                    side[j] = -1
                    sp[j] = orb_hi
                    fired = True
            j += 1
        i = j if j > i else i + 1
    return sig, side, sp


def simulate(i, side_i, entry, stop, tp_mult, times, h, l, c, time_stop=TIME_STOP):
    if side_i > 0:
        risk = entry - stop
        if risk <= 0:
            return None
        target = entry + tp_mult * risk
        for j in range(i + 1, min(i + 1 + time_stop, len(times))):
            if l[j] <= stop:
                return {
                    "side": "LONG",
                    "exit_i": j,
                    "exit_px": stop,
                    "exit": "orig_stop",
                    "R": -1.0,
                    "target": target,
                }
            if h[j] >= target:
                return {
                    "side": "LONG",
                    "exit_i": j,
                    "exit_px": target,
                    "exit": "orig_tp",
                    "R": float(tp_mult),
                    "target": target,
                }
        j = min(i + time_stop, len(times) - 1)
        if j <= i:
            return None
        return {
            "side": "LONG",
            "exit_i": j,
            "exit_px": float(c[j]),
            "exit": "time_stop",
            "R": round((c[j] - entry) / risk, 4),
            "target": target,
        }
    else:
        risk = stop - entry
        if risk <= 0:
            return None
        target = entry - tp_mult * risk
        for j in range(i + 1, min(i + 1 + time_stop, len(times))):
            if h[j] >= stop:
                return {
                    "side": "SHORT",
                    "exit_i": j,
                    "exit_px": stop,
                    "exit": "orig_stop",
                    "R": -1.0,
                    "target": target,
                }
            if l[j] <= target:
                return {
                    "side": "SHORT",
                    "exit_i": j,
                    "exit_px": target,
                    "exit": "orig_tp",
                    "R": float(tp_mult),
                    "target": target,
                }
        j = min(i + time_stop, len(times) - 1)
        if j <= i:
            return None
        return {
            "side": "SHORT",
            "exit_i": j,
            "exit_px": float(c[j]),
            "exit": "time_stop",
            "R": round((entry - c[j]) / risk, 4),
            "target": target,
        }


def maxdd(rs):
    eq = peak = mdd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    return round(mdd, 4)


def summarize(trades):
    rs = [t["R"] for t in trades]
    n = len(rs)
    if n == 0:
        return {"n": 0, "sumR": 0.0, "avgR": 0.0, "win_rate": 0.0, "maxDD_R": 0.0}
    wins = sum(1 for r in rs if r > 0)
    return {
        "n": n,
        "sumR": round(sum(rs), 4),
        "avgR": round(sum(rs) / n, 4),
        "win_rate": round(wins / n, 4),
        "maxDD_R": maxdd(rs),
    }


def year_table(trades):
    by_y = defaultdict(list)
    for t in trades:
        by_y[t["year"]].append(t["R"])
    rows = []
    for y in sorted(by_y):
        rs = by_y[y]
        wins = sum(1 for r in rs if r > 0)
        rows.append(
            {
                "year": y,
                "n": len(rs),
                "WR": round(wins / len(rs), 4),
                "avgR": round(sum(rs) / len(rs), 4),
                "sumR": round(sum(rs), 4),
            }
        )
    return rows


def run_blotter(times, o, h, l, c, atr, hours, sig, side, sp, tp_mult, sleeve, source_tag):
    trades = []
    cooldown_until = -1
    for i in range(len(times)):
        if not sig[i] or i < cooldown_until:
            continue
        if times[i] < HOLD_START:
            continue  # only HOLD-span for this pack (no train bars anyway)
        entry = float(c[i])
        stop = float(sp[i])
        if not np.isfinite(stop):
            continue
        sim = simulate(i, int(side[i]), entry, stop, tp_mult, times, h, l, c)
        if sim is None:
            continue
        row = {
            "sleeve": sleeve,
            "symbol": "EURGBP",
            "side": sim["side"],
            "entry_time": times[i].strftime("%Y-%m-%d %H:%M:%S"),
            "entry_px": entry,
            "stop_px": stop,
            "target_px": sim["target"],
            "exit_time": times[sim["exit_i"]].strftime("%Y-%m-%d %H:%M:%S"),
            "exit_px": sim["exit_px"],
            "exit": sim["exit"],
            "R": sim["R"],
            "split": "hold",
            "fill_model": f"geometry_proxy_ohlc_touch_v0_{tp_mult}R_no_broker_fill",
            "bars_source": source_tag,
            "year": times[i].year,
        }
        trades.append(row)
        cooldown_until = sim["exit_i"] + 1  # no overlap
    return trades


def main():
    times, o, h, l, c, v = load_tape(TAPE)
    atr = atr14(h, l, c)
    hours = np.array([t.hour for t in times], dtype=int)
    years = np.array([t.year for t in times], dtype=int)

    n_train = sum(1 for t in times if t <= TRAIN_END)
    n_hold = sum(1 for t in times if t >= HOLD_START)
    train_possible = n_train > 0
    span_days = (times[-1] - times[0]).days
    span_years = round(span_days / 365.25, 2)
    ge_2y = span_days >= (365 * 2 - 30)

    sig, side, sp = sig_vss_fxcross_london_proxy(o, h, l, c, atr, hours)
    source_tag = "VPS_MT5_EURGBP_M15_from_mt5_HOLD_span"

    trades_1r = run_blotter(
        times, o, h, l, c, atr, hours, sig, side, sp, 1.0,
        "vss_fxcross_london_proxy_v0_1R", source_tag,
    )
    trades_3r = run_blotter(
        times, o, h, l, c, atr, hours, sig, side, sp, 3.0,
        "vss_fxcross_london_proxy_dig3R", source_tag,
    )

    s1 = summarize(trades_1r)
    s3 = summarize(trades_3r)
    y1 = year_table(trades_1r)
    y3 = year_table(trades_3r)
    exits_1 = dict(Counter(t["exit"] for t in trades_1r))
    exits_3 = dict(Counter(t["exit"] for t in trades_3r))
    sides_1 = dict(Counter(t["side"] for t in trades_1r))

    # Owner Dig gate on v0 1R HOLD window
    sumR_ok = s1["sumR"] > 0
    wr_ok = s1["win_rate"] >= WR_FLOOR
    gate_pass = bool(sumR_ok and wr_ok and s1["n"] > 0)
    pass_fail = "PASS" if gate_pass else "FAIL"

    # write blotters
    with BLOTTER_1R.open("w") as f:
        for t in trades_1r:
            f.write(json.dumps(t) + "\n")
    with BLOTTER_3R.open("w") as f:
        for t in trades_3r:
            f.write(json.dumps(t) + "\n")

    payload = {
        "schema": "gtos.chair.eurgbp_vss_multiyear.v2_hold_span",
        "ts_ict": ASOF_ICT,
        "pairing": {
            "instrument": "EURGBP",
            "sleeve": "vss_fxcross_london",
            "proxy": "vss_fxcross_london_proxy_v0_1R",
            "challenge_keep_ticket": 291816474,
            "challenge_keep_sumR": 1.87,
            "challenge_loser_ticket": 291087142,
            "challenge_loser_sumR": -1.20,
            "challenge_note": "KEEP win + loser twin mixed affinity; Dig multiyear is the expectancy test",
        },
        "status": "HOLD_SPAN_REPLAY" if ge_2y else "BLOCKED_THIN",
        "prior_status": "BLOCKED_THIN",
        "train_hold": {
            "plan_rule": "TRAIN<=2021-12-31 / HOLD>=2022-01-01",
            "train_possible": train_possible,
            "n_train_bars": n_train,
            "n_hold_bars": n_hold,
            "label": (
                "honest TRAIN/HOLD"
                if train_possible
                else "HOLD-span / no-pre-2022-train"
            ),
            "reason": (
                None
                if train_possible
                else f"tape starts {times[0].strftime('%Y-%m-%d')}; TRAIN<=2021 impossible"
            ),
        },
        "tape": {
            "path": str(TAPE),
            "source": "VPS MT5 C:\\MT5\\FTMO Challenge 0 copy_rates (year-merge; maxbars=100000)",
            "resolved_symbol": "EURGBP",
            "span": [
                times[0].strftime("%Y-%m-%d %H:%M:%S"),
                times[-1].strftime("%Y-%m-%d %H:%M:%S"),
            ],
            "n_bars": len(times),
            "span_days": span_days,
            "span_years_approx": span_years,
            "ge_2y": ge_2y,
            "prior_thin": "box historical_2026 ~112d — superseded by MT5 deep pull",
        },
        "fill_model": {
            "gate": "Dig PRIMARY adapted: geometry OHLC touch; structure stop=opp ORB extreme; TP=1R; time_stop=32; entry=signal close; stop-before-tp; NOT broker fills",
            "disclosure_dig_blotter_3R": "same signal with TP=3R — disclosure only, not gate",
            "not_ported": "XAU spring/expanding/three_fresh geometry",
        },
        "signal": {
            "formula": "vss_fxcross_london_proxy: London hour==7 ORB first 6 M15 bars; impulse=sign(close[orb_end]-open[orb_start]); fire later London/NY close beyond ORB extreme in impulse dir; stop=opp ORB; one fire/day",
            "sides": "BOTH (impulse-directed LONG/SHORT)",
        },
        "hold_window_ge_2022_v0_1R": s1,
        "hold_window_ge_2022_dig3R_disclosure": s3,
        "year_detail_v0_1R": y1,
        "year_detail_dig3R": y3,
        "exit_reasons_v0_1R": exits_1,
        "exit_reasons_dig3R": exits_3,
        "side_mix_v0_1R": sides_1,
        "owner_gate_v0_1R": {
            "sumR_gt_0": sumR_ok,
            "wr_floor": WR_FLOOR,
            "wr_ok": wr_ok,
            "pass_fail": pass_fail,
        },
        "gates": {
            "place": False,
            "ready_for_key_fx": False,
            "APPLY": "unset",
            "invent_geometry": False,
            "cost_kill": False,
            "NEWS_PROTOCOL": False,
        },
        "pass_fail": pass_fail,
        "monday_ready": False,
        "artifacts": {
            "md": str(MD),
            "json": str(JS),
            "blotter_1R": str(BLOTTER_1R),
            "blotter_3R": str(BLOTTER_3R),
            "tape": str(TAPE),
        },
    }
    def _native(o):
        import numpy as _np
        if isinstance(o, (_np.bool_,)):
            return bool(o)
        if isinstance(o, (_np.integer,)):
            return int(o)
        if isinstance(o, (_np.floating,)):
            return float(o)
        if isinstance(o, dict):
            return {k: _native(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_native(v) for v in o]
        return o
    JS.write_text(json.dumps(_native(payload), indent=2) + "\n", encoding="utf-8")

    # Markdown
    lines = []
    lines.append("# EURGBP × vss_fxcross_london — MULTIYEAR HOLD-span Dig replay — 2026-09-20")
    lines.append("")
    lines.append(
        f"**Status:** **{pass_fail}** ({payload['train_hold']['label']}) · **place=false** · **ready_for_key_fx=false** · APPLY unset  "
    )
    lines.append(f"**ts_ict:** {ASOF_ICT}  ")
    lines.append(
        "**Affinity:** Challenge KEEP **291816474** +1.87 vs loser **291087142** −1.20 · mixed twin; Dig multiyear is expectancy test"
    )
    lines.append("")
    lines.append("## Tape (REAL — prior BLOCKED thin superseded)")
    lines.append("")
    lines.append("| Role | Path | Span | n bars |")
    lines.append("|------|------|------|-------:|")
    lines.append(
        f"| **VPS MT5 (this run)** | `{TAPE}` | {times[0].date()} → {times[-1].date()} (~{span_years}y) | {len(times)} |"
    )
    lines.append(
        "| Prior thin (superseded) | box historical_2026 / fable ~weeks–months | 2026-only | ≤7761 |"
    )
    lines.append("")
    lines.append("## TRAIN / HOLD honesty")
    lines.append("")
    lines.append("| Question | Answer |")
    lines.append("|----------|--------|")
    lines.append(
        f"| TRAIN ≤2021 possible? | **{'YES' if train_possible else 'NO'}** — tape starts {times[0].date()} → **{payload['train_hold']['label']}** |"
    )
    lines.append(f"| HOLD ≥2022 bars | **{n_hold}** |")
    lines.append(f"| TRAIN bars ≤2021 | **{n_train}** |")
    lines.append(f"| Span gate ≥~2y | **{'PASS' if ge_2y else 'FAIL'}** ({span_years}y) |")
    lines.append("")
    lines.append("## Dig PRIMARY-style fill model (gate)")
    lines.append("")
    lines.append(
        "- Adapted from `multiyear/run_multiyear_positive_v0.py`: geometry OHLC touch · structure stop = opp ORB · **TP=1R** · **time_stop=32** · entry=signal close · stop-before-tp"
    )
    lines.append(
        "- Signal: Dig-style `vss_fxcross_london_proxy` (London ORB impulse + continuation break; both sides)"
    )
    lines.append("- **Do not** port XAU spring/expanding/three_fresh geometry")
    lines.append("- Cost never kill-gate · no NEWS invent · place=false")
    lines.append("")
    lines.append("## Owner gate (≥2022 HOLD window — v0 1R)")
    lines.append("")
    lines.append("| Gate | Result |")
    lines.append("|------|--------|")
    lines.append(
        f"| HOLD sumR > 0 | **{s1['sumR']}** → **{'PASS' if sumR_ok else 'FAIL'}** |"
    )
    lines.append(
        f"| WR (reported) | **{s1['win_rate']*100:.2f}%** (floor 40% → {'OK' if wr_ok else 'BELOW'}) |"
    )
    lines.append(
        f"| n / avgR / maxDD | {s1['n']} / {s1['avgR']} / {s1['maxDD_R']} |"
    )
    lines.append(f"| side mix | {sides_1} |")
    lines.append("| place | **false** |")
    lines.append("| ready_for_key_fx | **false** |")
    lines.append("")
    lines.append("### Year table (PRIMARY Dig · v0 1R)")
    lines.append("")
    lines.append("| year | n | WR | avgR | sumR |")
    lines.append("|-----:|--:|---:|-----:|-----:|")
    for r in y1:
        lines.append(
            f"| {r['year']} | {r['n']} | {r['WR']*100:.2f}% | {r['avgR']} | {r['sumR']} |"
        )
    lines.append("")
    lines.append(f"Exit reasons (1R): `{exits_1}`")
    lines.append("")
    lines.append("### Disclosure — Dig blotter 3R (same signal; not gate)")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|--------|------:|")
    lines.append(f"| sumR | {s3['sumR']} |")
    lines.append(f"| WR | {s3['win_rate']*100:.2f}% |")
    lines.append(f"| n | {s3['n']} |")
    lines.append("")
    lines.append(
        "3R year sumR: "
        + str([(r["year"], r["sumR"]) for r in y3])
    )
    lines.append("")
    lines.append("## Affinity note (Challenge twin)")
    lines.append("")
    lines.append(
        "- Twin autopsy: 291087142 FS **−1.20** vs 291816474 **+1.87** → mixed; REVIEW path (`CHALLENGE_KEEP_TWIN_FS_AUTOPSY_20260920`)"
    )
    lines.append(
        f"- Dig HOLD-span **{pass_fail}** (sumR={s1['sumR']}, n={s1['n']}, WR {s1['win_rate']*100:.2f}%) {'outweighs' if not gate_pass else 'supports'} single KEEP ticket for multiyear Dig edge claim"
    )
    lines.append(
        "- Do **not** hard-off EURGBP×vss from Dig alone without Chair affinity law review; place remains false"
    )
    lines.append("")
    lines.append("## Milestone")
    lines.append("")
    lines.append(f"- **PASS/FAIL (owner sumR gate on Dig v0 1R):** **{pass_fail}**")
    lines.append("- **Monday-ready:** **NO**")
    lines.append("- **WakeParent:** NO")
    lines.append("- **APPLY:** unset")
    lines.append(
        f"- Next unlock for full TRAIN/HOLD: EURGBP M15 spanning ≤2021 (broker terminal maxbars={100000} capped this pull at ~2022-09)"
    )
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("- `EURGBP_VSS_MULTIYEAR_20260920.{md,json}`")
    lines.append(f"- `{BLOTTER_1R.name}` / `{BLOTTER_3R.name}`")
    lines.append("- Tape: `multiyear/EURGBP_M15_from_mt5.csv`")
    lines.append("")

    MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "pass_fail": pass_fail,
        "span_years": span_years,
        "n_bars": len(times),
        "train_possible": train_possible,
        "hold_1R": s1,
        "hold_3R": s3,
        "exits_1R": exits_1,
        "sides": sides_1,
        "years_1R": y1,
    }, indent=2))


if __name__ == "__main__":
    main()
