"""B9 step 1b — does the clamp touch LIVE admission, and by how much?

The chain, each link read at origin/main and cited in the report:

  execution_packets.py:451,:655   stamp `gtos_vnext_production_execution_path: True` on every
                                  ultimate_book order packet
  broker_net_cost_engine.py:155-172  is_vnext_broker_net_cost_required -> True given
                                  agent_config.yaml:612 enabled / :613 mode / :614 apply_to_execution
  execution.py:3158 open_trade -> :3407 _vnext_pretrade_cost_model -> :2022 build_pretrade_cost_packet
  broker_net_cost_engine.py:768-773  total_cost_r = spread_r + slippage_r + swap_cost_r + commission_r
                                  ...where swap_cost_r is CLAMPED at :465-468
  broker_net_cost_engine.py:990-994  total_cost_r - max_total_cost_r > tol -> refusal
                                  (agent_config.yaml:716 selected_cell_pretrade_max_total_cost_r: 0.15)
  execution.py:3438-3444          refusal -> `return None`, the order is not placed

So the clamp OVERSTATES `total_cost_r` on a favourable-carry candidate and can only make the
live gate MORE conservative -- it never admits a trade it should refuse. The remedy for a
conservative gate is different from the remedy for a mis-stated research number, so this file
sizes the conservative half.

The pre-trade horizon is capped at ONE day (`selected_cell_swap_cost_horizon_days_cap: 1.0`,
agent_config.yaml:737) and converted through `rollover_nights`, so the live overstatement is at
most one charged night (three on the triple-swap weekday).

Measured two ways:
  (a) per-night credit in R on every armed-sleeve trade, using each trade's own sl_distance;
  (b) the FLIP SET: candidate-cache rows for those symbol/sides whose modelled `cost_r` sits in
      (ceiling, ceiling + one-night credit] -- i.e. refused today, admitted un-clamped.

Writes B9_LIVE_GATE_V1.json.
"""
from __future__ import annotations

import collections
import gzip
import json
import pathlib
import pickle
import statistics
import sys

REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
sys.path.insert(0, str(REPO))

HERE = pathlib.Path(__file__).resolve().parent
CACHE = pathlib.Path("/private/tmp/w21-puzzle-cache")
EXPORT = pathlib.Path("/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api")
ESTATE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
MONTHS = ("feb", "apr", "may", "jun", "jul")
CEILING = 0.15          # agent_config.yaml:716 selected_cell_pretrade_max_total_cost_r
FUNNEL_CEILING = 0.20   # wave21_forward_shadow/feature_contract.py:27 MAX_COST_R
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")  # 2026-08-11; sub_mid_dn_revert disarmed 08-11


def swap_table(fname: str) -> dict:
    out = {}
    for line in (EXPORT / fname).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if "swap_long" not in r:
            continue
        rec = {"swap_long": r["swap_long"], "swap_short": r.get("swap_short"),
               "swap_mode": r.get("swap_mode"), "point": r.get("point")}
        n = str(r.get("name"))
        out[n] = rec
        out[n.replace(".", "_")] = rec
    return out


def one_night_price_credit(rec, direction, price):
    """Price units the broker PAYS for one night, or 0.0 when the side is adverse."""
    swap = rec.get("swap_long") if direction > 0 else rec.get("swap_short")
    mode = rec.get("swap_mode")
    if swap is None or mode is None or float(swap) < 0:
        return 0.0
    mode = int(float(mode))
    if mode == 1:
        return float(swap) * float(rec.get("point") or 0.0)
    if mode in (5, 6) and price:
        return float(price) * (float(swap) / 100.0) / 360.0
    return 0.0


def main() -> int:
    tab = swap_table("ftmo_symbols_get.jsonl")
    est = json.loads(gzip.open(ESTATE, "rt").read())

    # (a) one-night credit in R, per armed-sleeve trade, at that trade's own stop
    per_sleeve = {}
    for sleeve in ARMED + ("sub_mid_dn_revert",):
        vals = []
        for t in est["trades"].get(sleeve, []):
            rec = tab.get(t.get("symbol_canonical")) or tab.get(t.get("symbol"))
            sld = t.get("sl_distance_price")
            if not rec or not sld:
                continue
            c = one_night_price_credit(rec, int(t.get("direction", 0)), t.get("entry_price"))
            vals.append(c / float(sld))
        if not vals:
            continue
        pos = [v for v in vals if v > 0]
        per_sleeve[sleeve] = {
            "n_trades": len(vals),
            "n_favourable_side": len(pos),
            "pct_favourable_side": 100.0 * len(pos) / len(vals),
            "mean_one_night_credit_r": sum(vals) / len(vals),
            "median_one_night_credit_r_favourable_only": (statistics.median(pos) if pos else 0.0),
            "max_one_night_credit_r": max(vals),
            "pct_of_live_ceiling_at_max": 100.0 * max(vals) / CEILING,
            "armed_2026_08_11": sleeve in ARMED,
        }

    # (b) flip set on the candidate cache
    rows = []
    for m in MONTHS:
        rows += pickle.load(gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb"))
    # per-symbol median mid price, from the broker-truth artifact (only used for modes 5/6)
    btc = json.loads((REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json").read_text())
    px = {}
    for sym, r in btc["accounts"]["FTMO"]["instruments"].items():
        p = (r.get("spread_price") or {}).get("mid_price_median")
        if p:
            px[sym] = px[sym.replace(".", "_")] = p

    flip = collections.defaultdict(lambda: {"n_rows": 0, "n_above_ceiling": 0, "n_flip": 0,
                                            "mean_credit_r": 0.0, "credits": []})
    for r in rows:
        sym, side = r.get("symbol"), str(r.get("side", "")).upper()
        rec = tab.get(sym)
        if rec is None:
            continue
        d = 1 if side in ("LONG", "BUY") else -1
        c_price = one_night_price_credit(rec, d, px.get(sym))
        if c_price <= 0:
            continue
        rf = r.get("risk_fraction_of_entry")
        p = px.get(sym)
        try:
            rf = float(rf)
        except (TypeError, ValueError):
            continue
        if not rf or not p:
            continue
        credit_r = c_price / (rf * p)
        try:
            cost = float(r.get("cost_r"))
        except (TypeError, ValueError):
            continue
        if cost != cost:
            continue
        b = flip[f"{sym}|{side}"]
        b["n_rows"] += 1
        b["credits"].append(credit_r)
        if cost > CEILING:
            b["n_above_ceiling"] += 1
            if cost - credit_r <= CEILING:
                b["n_flip"] += 1
    for k, b in flip.items():
        b["mean_credit_r"] = sum(b["credits"]) / len(b["credits"]) if b["credits"] else 0.0
        b["pct_flip_of_above_ceiling"] = (
            100.0 * b["n_flip"] / b["n_above_ceiling"] if b["n_above_ceiling"] else 0.0
        )
        b["pct_flip_of_all_rows"] = 100.0 * b["n_flip"] / b["n_rows"] if b["n_rows"] else 0.0
        del b["credits"]

    tot_rows = sum(b["n_rows"] for b in flip.values())
    tot_above = sum(b["n_above_ceiling"] for b in flip.values())
    tot_flip = sum(b["n_flip"] for b in flip.values())

    out = {
        "verdict": (
            "THE CLAMP TOUCHES LIVE ADMISSION. It inflates `total_cost_r` on every "
            "favourable-carry candidate, and `total_cost_r > selected_cell_pretrade_max_total_cost_r` "
            "(0.15) is a hard refusal that returns None before the broker request "
            "(execution.py:3438-3444). The direction is CONSERVATIVE: it refuses trades it should "
            "admit; it never admits one it should refuse."
        ),
        "chain": {
            "packet_stamp": "src/components/ultimate_book/execution_packets.py:451,:655",
            "required": "src/components/broker_net_cost_engine.py:155-172",
            "config_enable": ["config/agent_config.yaml:612", ":613", ":614"],
            "call": "src/components/execution.py:3407 -> :2022",
            "total": "src/components/broker_net_cost_engine.py:768-773",
            "clamp": "src/components/broker_net_cost_engine.py:465-468",
            "gate": "src/components/broker_net_cost_engine.py:990-994",
            "ceiling": "config/agent_config.yaml:716 (0.15); by-sleeve override :727-729 (fx_jpy* 0.45 only)",
            "block": "src/components/execution.py:3438-3444 (`return None`)",
            "horizon_cap": "config/agent_config.yaml:737 selected_cell_swap_cost_horizon_days_cap: 1.0",
        },
        "live_ceiling_r": CEILING,
        "funnel_ceiling_r": FUNNEL_CEILING,
        "one_night_credit_by_sleeve": per_sleeve,
        "flip_set": {
            "basis": "632,934-row candidate cache (feb/apr/may/jun/jul 2026), FTMO swap table "
                     "2026-07-25, per-row risk_fraction_of_entry, symbol median mid price",
            "rows_on_a_favourable_carry_side": tot_rows,
            "rows_above_live_ceiling": tot_above,
            "rows_that_would_FLIP_to_admitted": tot_flip,
            "pct_of_above_ceiling": 100.0 * tot_flip / tot_above if tot_above else 0.0,
            "pct_of_all_favourable_rows": 100.0 * tot_flip / tot_rows if tot_rows else 0.0,
            "by_symbol_side": dict(flip),
        },
    }
    (HERE / "B9_LIVE_GATE_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    print("one-night credit in R at each trade's own stop (FTMO table 2026-07-25):")
    print(f"  {'sleeve':<22}{'n':>5}{'%fav side':>11}{'mean R':>10}{'median R (fav)':>16}{'max R':>9}{'max as % of 0.15':>18}")
    for s, v in per_sleeve.items():
        print(f"  {s:<22}{v['n_trades']:>5}{v['pct_favourable_side']:>10.1f}%{v['mean_one_night_credit_r']:>+10.5f}"
              f"{v['median_one_night_credit_r_favourable_only']:>+16.5f}{v['max_one_night_credit_r']:>+9.5f}"
              f"{v['pct_of_live_ceiling_at_max']:>17.1f}%{'  *ARMED*' if v['armed_2026_08_11'] else ''}")
    f = out["flip_set"]
    print(f"\nflip set: {f['rows_that_would_FLIP_to_admitted']} of {f['rows_above_live_ceiling']} rows above the "
          f"0.15 ceiling ({f['pct_of_above_ceiling']:.2f}%) would flip to admitted; "
          f"{f['pct_of_all_favourable_rows']:.3f}% of the {f['rows_on_a_favourable_carry_side']} favourable-side rows")
    for k, b in sorted(flip.items(), key=lambda kv: -kv[1]["n_flip"])[:12]:
        print(f"   {k:<22} rows {b['n_rows']:>6}  above ceiling {b['n_above_ceiling']:>6}  FLIP {b['n_flip']:>5}"
              f"  mean credit {b['mean_credit_r']:+.5f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
