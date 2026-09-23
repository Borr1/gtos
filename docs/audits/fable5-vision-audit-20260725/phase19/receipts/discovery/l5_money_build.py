"""l5 lane step 1 -- re-denominate every January candidate's cost in PRICE units and USD.

Inputs (all read-only):
  w0_WORKING_SET.jsonl.gz                     27,658 candidates, pool fields + path geometry
  w0cap2_DECISION_ANCHOR_V1.jsonl.gz          born-state anchor (no look-ahead)
  BROKER_TRUE_COSTS_V1_1.json                 FTMO measured spread / commission / slippage / specs
  config/profiles/operator_profile.yaml  canonical -> mt5 symbol map

Identity being tested (broker_net_cost_engine.py:557-560 for commission,
_tick_packet:300-304 for spread):
    spread_r     = spread_price / sl_distance
    commission_r = usd_per_lot / (sl_distance * usd_per_price_unit_per_lot)
So with fixed-fractional sizing  lots = risk_usd / (sl_distance * upu):
    cost_usd = cost_r * risk_usd     EXACTLY, with no contract-spec term.
We compute lots/notional anyway, because the notional-denominated gate needs them.
"""
import gzip, json, os, sys, math
import yaml

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
WS = os.path.join(DISC, "w0_WORKING_SET.jsonl.gz")
ANCHOR = os.path.join(DISC, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
BTC = os.path.join(ROOT, "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json")
PROF = os.path.join(ROOT, "config/profiles/operator_profile.yaml")
OUT = os.path.join(DISC, "l5_MONEY_TABLE.jsonl.gz")
OUTSUM = os.path.join(DISC, "l5_MONEY_BUILD_V1.json")

BALANCE = 100000.0  # config/profiles/operator_profile.yaml:82 prop_safe_selector_initial_balance

prof = yaml.safe_load(open(PROF))
symmap = {}
for k, blk in (prof.get("instruments") or {}).items():
    m = (blk or {}).get("market") or {}
    if m.get("mt5_symbol"):
        symmap[k] = m["mt5_symbol"]

truth = json.load(open(BTC))
INS = truth["accounts"]["FTMO"]["instruments"]

def rec_for(sym):
    b = symmap.get(sym, sym)
    if b in INS:
        return b, INS[b]
    if sym in INS:
        return sym, INS[sym]
    return None, None

# born state from the no-look-ahead anchor
born = {}
with gzip.open(ANCHOR, "rt") as f:
    for line in f:
        a = json.loads(line)
        key = (a["candidate_id"], a["decision_time_utc"])
        side = (a.get("side") or "").upper()
        hi, lo = a.get("mkt_r_high"), a.get("mkt_r_low")
        op = a.get("mkt_r_open")
        # mkt_r_* are signed R relative to entry in the trade's favour-direction convention
        # produced by w0cap2_decision_anchor.py; classify with the same rule the capture lane used
        born[key] = a

def commission_usd_per_lot(rec, entry_price):
    c = rec["commission"]
    kind = c.get("kind")
    if kind == "zero":
        return 0.0, "zero"
    if kind == "per_lot":
        return float(c["value"]), "per_lot"
    if kind == "notional_bp":
        cs = rec["spec"].get("trade_contract_size")
        px = entry_price or (rec.get("spread_price") or {}).get("mid_price_median")
        if not cs or not px:
            return None, "notional_bp_missing"
        return float(c["value"]) / 1e4 * float(cs) * float(px), "notional_bp"
    return None, str(kind)

SESSMAP = {"ny": "ny", "london": "london", "tokyo": "asia", "asia": "asia"}

def true_spread_price(rec, session_bucket, stat="p50"):
    sp = rec.get("spread_price") or {}
    bys = sp.get("by_session") or {}
    s = SESSMAP.get(session_bucket)
    if s and s in bys and stat in bys[s]:
        return float(bys[s][stat]), "by_session:" + s
    pc = sp.get("percentiles") or {}
    if stat in pc:
        return float(pc[stat]), "pooled"
    return None, "missing"

n = 0
missing_sym = {}
w = gzip.open(OUT, "wt")
agg = {}
for line in gzip.open(WS, "rt"):
    r = json.loads(line)
    n += 1
    sym = r["symbol"]
    bsym, rec = rec_for(sym)
    if rec is None:
        missing_sym[sym] = missing_sym.get(sym, 0) + 1
        continue
    upu = float(rec["usd_per_price_unit_per_lot"])
    cs = float(rec["spec"]["trade_contract_size"])
    rd = float(r["risk_distance"])
    ep = float(r["entry_price"])
    rp = float(r["risk_per_trade_pct"])
    risk_usd = BALANCE * rp / 100.0
    lots = risk_usd / (rd * upu) if rd > 0 else None
    notional = lots * cs * ep if lots else None

    cost_r = r.get("cost_r")
    spread_r = r.get("spread_r")
    comm_r = r.get("commission_r")
    slip_r = r.get("expected_slippage_r")
    swap_r = r.get("swap_cost_r")

    frozen_spread_price = (spread_r * rd) if spread_r is not None else None
    tsp, tsp_src = true_spread_price(rec, r.get("session_bucket"))
    true_spread_r = (tsp / rd) if (tsp is not None and rd > 0) else None

    cusd, ckind = commission_usd_per_lot(rec, ep)
    comm_usd_true = (cusd * lots) if (cusd is not None and lots) else None
    comm_r_true = (comm_usd_true / risk_usd) if comm_usd_true is not None else None

    slip_true_r = float((rec.get("slippage") or {}).get("value_r")) if (rec.get("slippage") or {}).get("value_r") is not None else None

    def usd(x):
        return None if x is None else x * risk_usd

    total_usd = usd(cost_r)
    true_total_r = None
    if true_spread_r is not None and comm_r_true is not None:
        true_total_r = true_spread_r + comm_r_true + (slip_true_r or 0.0) + (swap_r or 0.0)

    out = {
        "candidate_id": r["candidate_id"],
        "decision_time_utc": r["decision_time_utc"],
        "symbol": sym, "broker_symbol": bsym,
        "instrument_class": rec.get("instrument_class"),
        "origin_family": r.get("origin_family"),
        "session_bucket": r.get("session_bucket"),
        "side": r.get("side"),
        "risk_per_trade_pct": rp, "risk_usd": risk_usd,
        "risk_distance": rd, "entry_price": ep,
        "usd_per_price_unit_per_lot": upu, "contract_size": cs,
        "lots": lots, "notional_usd": notional,
        "risk_pct_of_notional": (risk_usd / notional * 100.0) if notional else None,
        # frozen (what the gate used)
        "cost_r": cost_r, "spread_r": spread_r, "commission_r": comm_r,
        "expected_slippage_r": slip_r, "swap_cost_r": swap_r,
        "frozen_spread_price": frozen_spread_price,
        "cost_usd": total_usd,
        "spread_usd": usd(spread_r), "commission_usd": usd(comm_r),
        "slippage_usd": usd(slip_r), "swap_usd": usd(swap_r),
        "cost_bp_of_notional": (total_usd / notional * 1e4) if (total_usd is not None and notional) else None,
        "spread_bp_of_notional": (usd(spread_r) / notional * 1e4) if (spread_r is not None and notional) else None,
        # broker-true
        "true_spread_price": tsp, "true_spread_src": tsp_src,
        "true_spread_r": true_spread_r,
        "true_spread_usd": (true_spread_r * risk_usd) if true_spread_r is not None else None,
        "spread_overcharge_x": (frozen_spread_price / tsp) if (frozen_spread_price and tsp) else None,
        "commission_kind": ckind, "commission_usd_per_lot": cusd,
        "commission_usd_true": comm_usd_true, "commission_r_true": comm_r_true,
        "slippage_true_r": slip_true_r,
        "true_total_cost_r": true_total_r,
        "true_total_cost_usd": (true_total_r * risk_usd) if true_total_r is not None else None,
        # outcome + provenance
        "gross_r": r.get("gross_r"),
        "which_came_first": r.get("which_came_first"),
        "mfe_r": r.get("mfe_r"), "mae_r": r.get("mae_r"),
        "final_blocker_class": r.get("final_blocker_class"),
        "is_first_emission": r.get("is_first_emission"),
        "setup_dup_count": r.get("setup_dup_count"),
        "bars_to_entry_touch": r.get("bars_to_entry_touch"),
        "fill_honest_walk_r": r.get("fill_honest_walk_r"),
        "plain_walk_r": r.get("plain_walk_r"),
    }
    w.write(json.dumps(out) + "\n")
w.close()

summary = {"rows_in": n, "missing_symbols": missing_sym, "balance_usd": BALANCE,
           "symbol_map_used": {k: symmap.get(k, k) for k in sorted(set(symmap))},
           "out": OUT}
json.dump(summary, open(OUTSUM, "w"), indent=1)
print("rows", n, "missing", missing_sym)
