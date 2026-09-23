#!/usr/bin/env python3
"""T1 pool screens (Phase D) — R-CAPS cell table + R-GEOMETRY contract cells.

Population: the January diagnostic pool (27,658 rows, CJ_RECLOCKED_S0R0_POOL_V1)
joined 1:1 to the CK/CQ ordered-path sidecar (M1_CONSERVATIVE paths, no selection
feedback). Costs: truthed spread via spread_model (band=mid, v2_damped), frozen
commission/swap per row, flat 0.02 slippage; all price-anchored components rescale
by the cell's own risk distance. Walker: CQ semantics (running maxima, conservative
stop-first on ties, MTM clamp [-1, target] at the 120-min wall).

EVIDENCE CLASS: DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade.
No March, no live-forward.
"""
import gzip, json, math, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/fa2-integration-20260803")
from src.costs.spread_model import spread_price  # noqa: E402

ROOT = Path("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
POOL = ROOT / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
SIDECAR = ROOT / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
OUTDIR = ROOT / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/forensic/t1"
OUTDIR.mkdir(parents=True, exist_ok=True)

CAPS = [0.05, 0.10, 0.15, 0.20, 0.25, 0.35, 0.50, 0.75, 1.00, 1.50]
STOP_CELLS = [1.5, 2.0, 3.0]          # stop multiplier, target PRICE fixed
TARGET_CELLS = [1.5, 3.0, 5.0]        # target in base-d units, stop x1
SLIP_R = 0.02
TOL = 1e-9


def iter_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def main():
    # ---- pool index ----
    pool = {}
    refused = 0
    for r in iter_gz(POOL):
        k = (r["candidate_id"], r["decision_time_utc"])
        entry, stop = float(r["entry_price"]), float(r["stop_loss"])
        base_d = abs(entry - stop)
        if not math.isfinite(base_d) or base_d <= 0:
            continue
        if r.get("pretrade_cost_packet_status") == "REFUSED":
            refused += 1
        pool[k] = dict(
            entry=entry, base_d=base_d, side=r["side"], symbol=r["symbol"],
            fam=r["origin_family"], sess=r["route_session"],
            net=float(r["opportunity_net_proxy_r"]), cost=float(r["cost_r"]),
            comm=float(r.get("commission_r") or 0.0), swap=float(r.get("swap_cost_r") or 0.0),
            spread_frozen=float(r.get("spread_r") or 0.0),
            target_r=float(r.get("policy_target_r") or 2.0),
            refused=r.get("pretrade_cost_packet_status") == "REFUSED",
        )
    n_pool = len(pool)

    # ---- spread truth cache ----
    cache = {}
    def spread_true(symbol, iso):
        dt = datetime.fromisoformat(iso)
        key = (symbol, dt.strftime("%Y-%m-%dT%H"))
        if key not in cache:
            cache[key] = spread_price(symbol, "FTMO", dt, band="mid").spread_price
        return cache[key]

    # ---- accumulators ----
    capA = {c: dict(n=0, win=0, sum=0.0, ref_admit_frozen=0) for c in CAPS}
    pool_stats = dict(n=0, win_true=0, sum_true=0.0, sum_frozen=0.0, refused=0,
                      untradeable_true=0, untradeable_frozen=0)
    calib = dict(n=0, exact=0, close=0, far=0, max_abs=0.0, sum_diff=0.0,
                 far_examples=[])
    cells = {}
    for s in STOP_CELLS:
        cells[f"stop_x{s}"] = defaultdict(lambda: dict(n=0, win=0, sum=0.0, amb=0))
    for t in TARGET_CELLS:
        cells[f"target_{t}R"] = defaultdict(lambda: dict(n=0, win=0, sum=0.0, amb=0))
    cells["base"] = defaultdict(lambda: dict(n=0, win=0, sum=0.0, amb=0))
    joined = 0
    no_join = 0

    for row in iter_gz(SIDECAR):
        k = (row["candidate_id"], row["decision_time_utc"])
        p = pool.get(k)
        if p is None:
            no_join += 1
            continue
        joined += 1
        obs = row["ordered_path_observations"]
        if not obs:
            continue
        entry, base_d, side = p["entry"], p["base_d"], p["side"]
        # running favorable/adverse in base-d units + terminal
        run_fav = run_adv = 0.0
        fav_seq, adv_seq = [], []
        for b in obs:
            hi, lo = float(b["high"]), float(b["low"])
            if side == "LONG":
                f, a = (hi - entry) / base_d, (entry - lo) / base_d
            else:
                f, a = (entry - lo) / base_d, (hi - entry) / base_d
            run_fav = f if f > run_fav else run_fav
            run_adv = a if a > run_adv else run_adv
            fav_seq.append(run_fav)
            adv_seq.append(run_adv)
        last_close = float(obs[-1]["close"])
        term_d = (last_close - entry) / base_d if side == "LONG" else (entry - last_close) / base_d

        sp_true = spread_true(p["symbol"], row["decision_time_utc"])
        # frozen-unit truthed cost
        cost_true = p["comm"] + p["swap"] + SLIP_R + sp_true / base_d
        gross_frozen = p["net"] + p["cost"]
        net_true = gross_frozen - cost_true

        # pool stats + Screen A
        pool_stats["n"] += 1
        pool_stats["sum_frozen"] += p["net"]
        pool_stats["sum_true"] += net_true
        if net_true > 0:
            pool_stats["win_true"] += 1
        if p["refused"]:
            pool_stats["refused"] += 1
        # untradeable definition (B5): cost >= gross target potential? use cap grid only
        for c in CAPS:
            if cost_true <= c:
                capA[c]["n"] += 1
                capA[c]["sum"] += net_true
                if net_true > 0:
                    capA[c]["win"] += 1
            if p["cost"] <= c:
                capA[c]["ref_admit_frozen"] += 1

        # ---- cell walker ----
        def first_idx(seq, thr):
            for i, v in enumerate(seq):
                if v >= thr - TOL:
                    return i
            return None

        def outcome(stop_mult, target_d):
            ti = first_idx(fav_seq, target_d)
            si = first_idx(adv_seq, stop_mult)
            amb = ti is not None and si is not None and ti == si
            if si is not None and (ti is None or si <= ti):
                g = -1.0
            elif ti is not None:
                g = target_d / stop_mult
            else:
                g = max(-1.0, min(term_d / stop_mult, target_d / stop_mult))
            net = g - (p["comm"] + p["swap"] + SLIP_R) / stop_mult - sp_true / (stop_mult * base_d)
            return g, net, amb

        fam = p["fam"]
        g0, n0, a0 = outcome(1.0, p["target_r"])
        cb = cells["base"][fam]
        cb["n"] += 1; cb["sum"] += n0; cb["amb"] += a0
        if n0 > 0: cb["win"] += 1
        # calibration vs frozen walked gross
        d = abs(g0 - gross_frozen)
        calib["n"] += 1
        calib["sum_diff"] += g0 - gross_frozen
        calib["max_abs"] = max(calib["max_abs"], d)
        if d < 1e-6: calib["exact"] += 1
        elif d <= 0.05: calib["close"] += 1
        else:
            calib["far"] += 1
            if len(calib["far_examples"]) < 6:
                calib["far_examples"].append(
                    dict(key=k[0][-12:] + "@" + k[1][11:16], sym=p["symbol"],
                         mine=round(g0, 4), frozen=round(gross_frozen, 4)))
        for s in STOP_CELLS:
            g, n_, amb = outcome(s, p["target_r"])
            c = cells[f"stop_x{s}"][fam]
            c["n"] += 1; c["sum"] += n_; c["amb"] += amb
            if n_ > 0: c["win"] += 1
        for t in TARGET_CELLS:
            g, n_, amb = outcome(1.0, t)
            c = cells[f"target_{t}R"][fam]
            c["n"] += 1; c["sum"] += n_; c["amb"] += amb
            if n_ > 0: c["win"] += 1

    # ---- emit ----
    def cell_table(cd):
        total = dict(n=0, win=0, sum=0.0, amb=0)
        fams = {}
        for fam, v in sorted(cd.items()):
            total["n"] += v["n"]; total["win"] += v["win"]; total["sum"] += v["sum"]; total["amb"] += v["amb"]
            fams[fam] = dict(n=v["n"], win_rate=round(v["win"] / v["n"], 4) if v["n"] else None,
                             mean_net=round(v["sum"] / v["n"], 4) if v["n"] else None,
                             sum_net=round(v["sum"], 1), ambiguity=v["amb"])
        return dict(total=dict(n=total["n"],
                               win_rate=round(total["win"] / total["n"], 4) if total["n"] else None,
                               mean_net=round(total["sum"] / total["n"], 4) if total["n"] else None,
                               sum_net=round(total["sum"], 1), ambiguity=total["amb"]),
                    by_family=fams)

    out = dict(
        schema="gtos-fa-t1-screens-v1",
        evidence_class="DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade",
        population=dict(pool_rows=n_pool, sidecar_joined=joined, sidecar_unjoined=no_join,
                        pool_refused_frozen=refused),
        cost_model=dict(spread="spread_model band=mid v2_damped hour-aware (cached per symbol-hour)",
                        commission="frozen per-row commission_r (CJ gated repair)",
                        swap="frozen per-row swap_cost_r", slippage=f"flat {SLIP_R}",
                        rescale="all price-anchored components divide by cell risk (stop_mult x base_d)"),
        calibration_base_vs_frozen=dict(
            n=calib["n"], exact_1e6=calib["exact"], within_0p05=calib["close"], far=calib["far"],
            max_abs=round(calib["max_abs"], 4),
            mean_signed=round(calib["sum_diff"] / calib["n"], 5) if calib["n"] else None,
            far_examples=calib["far_examples"],
            note="base cell = plain barrier stop x1 / target policy_target_r / MTM clamp at wall; agreement level decides whether frozen proxies are plain-barrier or overlay"),
        pool=dict(n=pool_stats["n"],
                  mean_net_frozen=round(pool_stats["sum_frozen"] / pool_stats["n"], 4),
                  mean_net_true=round(pool_stats["sum_true"] / pool_stats["n"], 4),
                  win_rate_true=round(pool_stats["win_true"] / pool_stats["n"], 4),
                  refused_share_frozen=round(pool_stats["refused"] / pool_stats["n"], 4)),
        screen_A_caps={str(c): dict(admitted=v["n"],
                                    admit_share=round(v["n"] / pool_stats["n"], 4),
                                    winners=v["win"],
                                    mean_net_true=round(v["sum"] / v["n"], 4) if v["n"] else None,
                                    sum_net_true=round(v["sum"], 1),
                                    frozen_cost_admit=v["ref_admit_frozen"])
                       for c, v in capA.items()},
        screen_B_cells={name: cell_table(cd) for name, cd in cells.items()},
    )
    (OUTDIR / "T1_SCREENS_V1.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(dict(pool=out["population"], calibration=out["calibration_base_vs_frozen"],
                          pool_stats=out["pool"]), indent=1))
    print("\nScreen A caps:")
    for c, v in out["screen_A_caps"].items():
        print(f"  cap {c}: admit {v['admitted']} ({v['admit_share']:.1%}) mean_net_true {v['mean_net_true']} sum {v['sum_net_true']}")
    print("\nScreen B cells (totals):")
    for name, t in out["screen_B_cells"].items():
        tt = t["total"]
        print(f"  {name}: n {tt['n']} win {tt['win_rate']} mean_net {tt['mean_net']} sum {tt['sum_net']} amb {tt['ambiguity']}")


if __name__ == "__main__":
    main()
