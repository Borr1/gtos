#!/usr/bin/env python3
"""A2-verify lane FC — stage 2: independent replay of the 40-cell overlay family.

Re-implements the frozen OVERLAY_PROTOCOL.json semantics from scratch (no FC
code imported) and replays all 40 cells over:
  - January executed book (57 trades; TRAIN = frozen first 13 ordered trading
    days, HOLDOUT = last 8, split read from the upstream CQ pool manifest);
  - February executed book (58 trades) — ATTRIBUTION ONLY under
    owner_mandate_20260801; no fitting, no ranking authority.

Claim targets (FC's receipts are the CLAIMS; raw tick/M1/trade data the EVIDENCE):
  FC1: V17_GB_T050_G010 TRAIN +0.197 total net R -> HOLDOUT -1.920 -> Feb -0.381,
       TRAIN improvement q(BH-40) = 0.4861; 0/40 pass the frozen persistence gate.

Where the protocol prose is ambiguous, the frozen analyzer interpretation
governs (documented in the receipt): exits fill AT the floor/stop/target level;
paths start strictly after the recorded fill; M1 evaluates both extrema
orderings and keeps the lower (net_r, exit_reason) result; TOL = 1e-9.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SCRATCH = Path(
    "/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave19-broad-forensic-20260801/"
    "90d4ce63-5eb8-4f7a-bb2a-3c9361ea36ce/scratchpad"
)
IN_DIR = SCRATCH / "fc_verify"
RECEIPT_DIR = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase19/receipts/forensic/a2_verify"
)

FA_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
    "research/operations/wave19_broad_forensic_2026_08_01"
)
PROTOCOL = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-sol-exit-20260801/research/operations/"
    "wave19_sol_repair_2026_08_01/exit/OVERLAY_PROTOCOL.json"
)
CQ_MANIFEST = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-path-pools-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json"
)

US_PER_MIN = 60_000_000
TOL = 1e-9
ALLOWED = {"2026-01", "2026-02"}


def parse_us(text: str) -> int:
    t = str(text).strip()
    if t[:7] not in ALLOWED:
        raise SystemExit(f"month_boundary_violation:{t[:7]}")
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    d = dt.datetime.fromisoformat(t)
    return int(round(d.astimezone(dt.timezone.utc).timestamp() * 1_000_000))


# ---------------------------------------------------------------- spec table
def build_specs() -> list[dict]:
    proto = json.loads(PROTOCOL.read_text())
    fam = proto["family"]
    assert fam["declared_family_size"] == 40
    variants = fam["variants"]
    assert len(variants) == 40
    specs = []
    for cell in variants:
        kind = cell["kind"]
        s = {
            "id": cell["id"], "kind": kind, "trigger": None, "gap": None,
            "fraction": 0.0, "be": False, "time_box": None,
            "hard_stop": -1.0, "hard_target": 2.0,
        }
        if kind == "identity":
            s["trigger"], s["gap"] = 1.0, 0.4
        elif kind == "break_even":
            s["trigger"], s["be"] = float(cell["trigger_r"]), True
        elif kind == "partial_harvest":
            s["trigger"], s["fraction"] = float(cell["trigger_r"]), float(cell["fraction"])
        elif kind == "tighter_giveback":
            s["trigger"], s["gap"] = float(cell["trigger_r"]), float(cell["giveback_gap_r"])
        elif kind == "time_box":
            s["time_box"] = int(cell["minutes"])
        elif kind == "partial_then_break_even":
            s["trigger"], s["fraction"], s["be"] = (
                float(cell["trigger_r"]), float(cell["fraction"]), True)
        else:
            raise SystemExit(f"unknown kind {kind}")
        specs.append(s)
    assert len({s["id"] for s in specs}) == 40
    return specs


# ---------------------------------------------------------------- replay core
def first_idx(mask: np.ndarray, offset: int = 0):
    nz = np.flatnonzero(mask)
    return None if not len(nz) else int(nz[0]) + offset


def replay_one(spec: dict, values: np.ndarray, times: np.ndarray,
               eligible: np.ndarray, decision_us: int, cost_r: float):
    n = len(values)
    assert n > 0
    stop_i = first_idx(values <= spec["hard_stop"] + TOL)
    targ_i = first_idx(values >= spec["hard_target"] - TOL)
    dl_i = None
    if spec["time_box"] is not None:
        deadline = decision_us + spec["time_box"] * US_PER_MIN
        dl_i = first_idx(eligible & (times >= deadline))
    trig_i = (first_idx(values >= spec["trigger"] - TOL)
              if spec["trigger"] is not None else None)

    floor_i = None
    floor_r = spec["hard_stop"]
    floor_reason = "protective_floor"
    if trig_i is not None and spec["be"]:
        start = trig_i + 1
        if start < n:
            floor_i = first_idx(values[start:] <= TOL, offset=start)
            floor_r = 0.0
            floor_reason = "break_even_floor"
    if trig_i is not None and spec["gap"] is not None:
        start = trig_i + 1
        if start < n:
            prior_mfe = np.maximum.accumulate(values[trig_i:-1])
            floors = np.maximum(spec["hard_stop"], prior_mfe - spec["gap"])
            rel = first_idx(values[start:] <= floors + TOL)
            if rel is not None:
                floor_i = start + rel
                floor_r = float(floors[rel])
                floor_reason = "giveback_floor"

    cands = [(n - 1, 4, "horizon_terminal_mark", float(values[-1]))]
    if stop_i is not None:
        cands.append((stop_i, 0, "hard_stop", spec["hard_stop"]))
    if floor_i is not None:
        cands.append((floor_i, 1, floor_reason, floor_r))
    if dl_i is not None:
        cands.append((dl_i, 2, "time_box", float(values[dl_i])))
    if targ_i is not None:
        cands.append((targ_i, 3, "hard_target", spec["hard_target"]))
    exit_i, _, reason, exit_r = min(cands, key=lambda c: (c[0], c[1]))

    touched = trig_i is not None and (
        trig_i < exit_i or (trig_i == exit_i and reason == "hard_target"))
    partial = 0.0
    remaining = 1.0
    if touched and spec["fraction"]:
        partial = spec["fraction"] * float(spec["trigger"])
        remaining -= spec["fraction"]
    gross = partial + remaining * float(exit_r)
    return {"gross": gross, "net": gross - cost_r, "reason": reason,
            "exit_i": exit_i, "touched": touched}


def signed(prices: np.ndarray, entry: float, dist: float, side: str) -> np.ndarray:
    return (prices - entry) / dist if side == "LONG" else (entry - prices) / dist


def replay_trade(spec: dict, trade: dict, path: dict):
    """path: {'mode','values'|('o','h','l','c'),'times'} in signed-R space."""
    if path["mode"] == "ORDERED_TICK":
        return replay_one(spec, path["values"], path["times"],
                          np.ones(len(path["values"]), bool),
                          trade["_decision_us"], trade["cost_r"]) | {
            "mode": "ORDERED_TICK", "ambiguous": False}
    # M1 conservative: two orderings, keep lower (net, reason)
    o, h, l, c, t = path["o"], path["h"], path["l"], path["c"], path["times"]
    rep_t = np.repeat(t, 4)
    elig = np.zeros(len(rep_t), bool)
    elig[3::4] = True
    hi_first = np.column_stack((o, h, l, c)).reshape(-1)
    lo_first = np.column_stack((o, l, h, c)).reshape(-1)
    r1 = replay_one(spec, hi_first, rep_t, elig, trade["_decision_us"], trade["cost_r"])
    r2 = replay_one(spec, lo_first, rep_t, elig, trade["_decision_us"], trade["cost_r"])
    sel = min((r1, r2), key=lambda r: (r["net"], r["reason"]))
    ambiguous = (r1["reason"] != r2["reason"]) or (abs(r1["gross"] - r2["gross"]) > TOL)
    return sel | {"mode": "M1_CONSERVATIVE", "ambiguous": ambiguous}


# ---------------------------------------------------------------- statistics
def sign_flip_p(vals: np.ndarray) -> dict:
    nz = vals[np.abs(vals) > 1e-12]
    if not len(nz):
        return {"p": 1.0, "k": 0, "perms": 1, "obs": float(np.mean(vals)) if len(vals) else 0.0}
    assert len(nz) <= 20
    sums = np.zeros(1)
    for v in nz:
        sums = np.concatenate((sums + v, sums - v))
    obs = float(np.mean(nz))
    p = float(np.mean(sums / len(nz) >= obs - 1e-12))
    return {"p": p, "k": int(len(nz)), "perms": int(len(sums)), "obs": obs}


def bh_q(ps: list[float]) -> list[float]:
    m = len(ps)
    order = sorted(range(m), key=lambda i: (ps[i], i))
    q = [1.0] * m
    running = 1.0
    for pos in range(m - 1, -1, -1):
        i = order[pos]
        running = min(running, min(1.0, ps[i] * m / (pos + 1)))
        q[i] = running
    return q


# ---------------------------------------------------------------- data load
def load_trades(path: Path, month: str, expected: int) -> list[dict]:
    payload = json.loads(path.read_text())
    trades = payload["trades"]
    assert len(trades) == expected
    for t in trades:
        side = str(t.get("side") or t.get("direction")).upper()
        t["_side"] = side
        t["_decision_us"] = parse_us(t["decision_time_utc"])
        t["_entry_us"] = parse_us(t["entry_time_utc"])
        t["_horizon_us"] = t["_decision_us"] + 120 * US_PER_MIN
        t["_day"] = t["decision_time_utc"][:10]
        assert t["_day"][:7] == month
        entry, stop = float(t["entry_price"]), float(t["stop_loss"])
        dist = abs(entry - stop)
        assert dist > 0 and float(t["cost_r"]) >= 0
        t["_dist"] = dist
    return trades


def build_paths(trades: list[dict], month: str) -> None:
    tick_cache, m1_cache = {}, {}
    for t in trades:
        sym = t["symbol"]
        tick_file = IN_DIR / f"tick_{month}_{sym}.npz"
        m1_file = IN_DIR / f"m1_{month}_{sym}.npz"
        entry, dist, side = float(t["entry_price"]), t["_dist"], t["_side"]
        if tick_file.exists():
            if sym not in tick_cache:
                tick_cache[sym] = np.load(tick_file)
            z = tick_cache[sym]
            s = int(np.searchsorted(z["times"], t["_entry_us"], side="right"))
            e = int(np.searchsorted(z["times"], t["_horizon_us"], side="right"))
            if s < e:
                quote = z["bid"][s:e] if side == "LONG" else z["ask"][s:e]
                t["_path"] = {
                    "mode": "ORDERED_TICK",
                    "values": signed(quote, entry, dist, side),
                    "times": z["times"][s:e],
                }
                continue
        assert m1_file.exists(), f"no path source for {sym} {month}"
        if sym not in m1_cache:
            m1_cache[sym] = np.load(m1_file)
        z = m1_cache[sym]
        s = int(np.searchsorted(z["times"], t["_entry_us"], side="right"))
        e = int(np.searchsorted(z["times"], t["_horizon_us"], side="right"))
        assert s < e, f"M1 path gap {sym} {t['candidate_id']}"
        sh = signed(z["high"][s:e], entry, dist, side)
        sl = signed(z["low"][s:e], entry, dist, side)
        t["_path"] = {
            "mode": "M1_CONSERVATIVE",
            "o": signed(z["open"][s:e], entry, dist, side),
            "h": np.maximum(sh, sl),
            "l": np.minimum(sh, sl),
            "c": signed(z["close"][s:e], entry, dist, side),
            "times": z["times"][s:e],
        }


def daily_sum(net: np.ndarray, days: list[str], dates: list[str]) -> np.ndarray:
    out = np.zeros(len(dates))
    idx = {d: i for i, d in enumerate(dates)}
    for v, d in zip(net, days):
        if d in idx:
            out[idx[d]] += v
    return out


def main() -> int:
    specs = build_specs()
    vids = [s["id"] for s in specs]
    v17 = vids.index("V17_GB_T050_G010")
    v00 = vids.index("V00_IDENTITY_CURRENT")

    cq = json.loads(CQ_MANIFEST.read_text())
    train_dates = list(cq["base_pool"]["train_dates"])
    holdout_dates = list(cq["base_pool"]["holdout_dates"])
    assert len(train_dates) == 13 and len(holdout_dates) == 8

    jan = load_trades(FA_ROOT / "trades_jan/TRADES_JAN_TABLE.json", "2026-01", 57)
    feb = load_trades(FA_ROOT / "trades_feb/TRADES_FEB_TABLE.json", "2026-02", 58)
    build_paths(jan, "2026-01")
    build_paths(feb, "2026-02")

    print("[stage2] paths built:",
          Counter(t["_path"]["mode"] for t in jan),
          Counter(t["_path"]["mode"] for t in feb), flush=True)

    # replay all 40 specs over both months
    results = {}
    for label, trades in (("jan", jan), ("feb", feb)):
        net = np.zeros((len(trades), 40))
        gross = np.zeros((len(trades), 40))
        modes = []
        for r, t in enumerate(trades):
            for k, spec in enumerate(specs):
                res = replay_trade(spec, t, t["_path"])
                net[r, k] = res["net"]
                gross[r, k] = res["gross"]
            modes.append(t["_path"]["mode"])
        results[label] = {"net": net, "gross": gross, "modes": modes,
                          "days": [t["_day"] for t in trades]}

    # identity reproduction vs source net_r (validation anchor)
    idrep = {}
    for label, trades in (("jan", jan), ("feb", feb)):
        rows = []
        for r, t in enumerate(trades):
            src = t.get("net_r")
            if isinstance(src, (int, float)):
                rows.append((t["_path"]["mode"], abs(results[label]["net"][r, v00] - src)))
        tick = [d for m, d in rows if m == "ORDERED_TICK"]
        m1 = [d for m, d in rows if m == "M1_CONSERVATIVE"]
        idrep[label] = {
            "tick_comparable": len(tick),
            "tick_within_1e6": int(sum(d <= 1e-6 for d in tick)),
            "tick_max_abs_delta": max(tick) if tick else None,
            "m1_comparable": len(m1),
            "m1_within_1e6": int(sum(d <= 1e-6 for d in m1)),
            "m1_max_abs_delta": max(m1) if m1 else None,
        }
    print("[stage2] identity reproduction:", json.dumps(idrep), flush=True)

    # books
    jd = results["jan"]["days"]
    train_mask = np.isin(jd, train_dates)
    hold_mask = np.isin(jd, holdout_dates)
    assert int(train_mask.sum()) + int(hold_mask.sum()) == 57

    jan_net = results["jan"]["net"]
    feb_net = results["feb"]["net"]

    book = {}
    for k, vid in enumerate(vids):
        book[vid] = {
            "train_total_net": float(jan_net[train_mask, k].sum()),
            "holdout_total_net": float(jan_net[hold_mask, k].sum()),
            "feb_total_net": float(feb_net[:, k].sum()),
            "train_improvement": float((jan_net[train_mask, k] - jan_net[train_mask, v00]).sum()),
            "holdout_improvement": float((jan_net[hold_mask, k] - jan_net[hold_mask, v00]).sum()),
            "feb_improvement": float((feb_net[:, k] - feb_net[:, v00]).sum()),
        }

    # TRAIN improvement q values across the 40-cell family
    ps = []
    for k, vid in enumerate(vids):
        dn = daily_sum(jan_net[train_mask, k], list(np.asarray(jd)[train_mask]), train_dates)
        di = daily_sum(jan_net[train_mask, v00], list(np.asarray(jd)[train_mask]), train_dates)
        test = sign_flip_p(dn - di)
        ps.append(test["p"])
        book[vid]["train_improvement_p"] = test["p"]
        book[vid]["train_improvement_nonzero_days"] = test["k"]
        book[vid]["train_improvement_daily_mean"] = test["obs"]
    qs = bh_q(ps)
    for k, vid in enumerate(vids):
        book[vid]["train_improvement_q_bh40"] = qs[k]

    # ranking (frozen rule): desc TRAIN total, desc TRAIN improvement, asc id
    ranked = sorted(
        (v for v in vids if v != "V00_IDENTITY_CURRENT"),
        key=lambda v: (-book[v]["train_total_net"], -book[v]["train_improvement"], v))
    top3 = ranked[:3]

    # persistence-gate arithmetic on my recomputed numbers
    gate = {}
    for vid in top3:
        b = book[vid]
        gate[vid] = {
            "train_pass": b["train_total_net"] > 0 and b["train_improvement"] > 0
                          and b["train_improvement_q_bh40"] <= 0.10,
            "holdout_pass": b["holdout_total_net"] > 0 and b["holdout_improvement"] > 0,
            "february_pass": b["feb_total_net"] > 0 and b["feb_improvement"] > 0,
        }
        gate[vid]["all"] = all(gate[vid].values())

    positivity = {
        "train_positive": [v for v in vids if v != "V00_IDENTITY_CURRENT" and book[v]["train_total_net"] > 0],
        "holdout_positive": [v for v in vids if v != "V00_IDENTITY_CURRENT" and book[v]["holdout_total_net"] > 0],
        "feb_positive": [v for v in vids if v != "V00_IDENTITY_CURRENT" and book[v]["feb_total_net"] > 0],
        "all_three_positive": [
            v for v in vids if v != "V00_IDENTITY_CURRENT"
            and book[v]["train_total_net"] > 0
            and book[v]["holdout_total_net"] > 0
            and book[v]["feb_total_net"] > 0
        ],
    }

    out = {
        "authority_note": (
            "February figures are ATTRIBUTION-ONLY under owner_mandate_20260801; "
            "no fitting, ranking, or implementation authority. No March 2026 or "
            "live-forward outcome was read."),
        "train_dates": train_dates,
        "holdout_dates": holdout_dates,
        "train_rows": int(train_mask.sum()),
        "holdout_rows": int(hold_mask.sum()),
        "feb_rows": len(feb),
        "identity_reproduction": idrep,
        "top3_by_frozen_rule": top3,
        "gate_arithmetic_top3": gate,
        "positivity": positivity,
        "book": book,
        "per_trade_v00_v17_jan": [
            {"key": [t["candidate_id"], t["decision_time_utc"], t["symbol"], t["_side"]],
             "day": t["_day"], "mode": t["_path"]["mode"], "source_net_r": t.get("net_r"),
             "v00_net": float(jan_net[r, v00]), "v17_net": float(jan_net[r, v17])}
            for r, t in enumerate(jan)
        ],
        "per_trade_v00_v17_feb": [
            {"key": [t["candidate_id"], t["decision_time_utc"], t["symbol"], t["_side"]],
             "day": t["_day"], "mode": t["_path"]["mode"], "source_net_r": t.get("net_r"),
             "v00_net": float(feb_net[r, v00]), "v17_net": float(feb_net[r, v17])}
            for r, t in enumerate(feb)
        ],
    }
    (RECEIPT_DIR / "FC_RECOMPUTE_DETAIL.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({
        "V17_train_total_net": book["V17_GB_T050_G010"]["train_total_net"],
        "V17_holdout_total_net": book["V17_GB_T050_G010"]["holdout_total_net"],
        "V17_feb_total_net": book["V17_GB_T050_G010"]["feb_total_net"],
        "V17_train_improvement": book["V17_GB_T050_G010"]["train_improvement"],
        "V17_train_improvement_p": book["V17_GB_T050_G010"]["train_improvement_p"],
        "V17_train_improvement_q": book["V17_GB_T050_G010"]["train_improvement_q_bh40"],
        "top3": top3,
        "gates": gate,
        "n_all_three_positive": len(positivity["all_three_positive"]),
    }, indent=1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
