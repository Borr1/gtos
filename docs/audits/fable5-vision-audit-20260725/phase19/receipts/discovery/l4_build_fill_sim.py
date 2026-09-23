#!/usr/bin/env python3
"""l4 — build the per-candidate FILL SIMULATION substrate.

One heavy streaming pass. Emits l4_FILL_V1.jsonl.gz: one row per candidate carrying
everything needed to score the owner's passive-limit contract at ANY fill window,
so every downstream question is a cheap pass over a small file.

CONVENTIONS (audit these before using any number downstream)
  STRICT PASSIVE FILL: the order rests at entry_price. It fills at the first path bar
  where price trades at or through it (adv <= 0, w0_ws sign convention), at the LIMIT
  PRICE. Gap-throughs are credited at the limit (conservative: the real fill is better).
  A fill is only accepted if fill_bar <= W (the fill window in M1 bars); otherwise the
  order is CANCELLED and the trade does not exist.

  LIFE: the path is hard-capped at 120 M1 bars (2 h). A fill at bar k leaves 120-k bars.
  Unresolved trades are marked to market at the last bar close.

  BORN CLASS from the decision anchor (mkt_r_prev_close = close of the M1 bar ENDING at
  the decision instant, signed for the trade's own side, in R relative to entry):
     at_limit   mkt == 0            entry == the decision price (an at-market order)
     resting    mkt > 0             genuine passive limit, price must come back
     marketable -1 < mkt < 0        limit through the market: fills instantly, better price
     past_stop  mkt <= -1           the stop was ALREADY breached before the order was sent
"""
import gzip, json, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
OUT    = os.path.join(HERE, "l4_FILL_V1.jsonl.gz")

CARRY = ["symbol","side","origin_family","session_bucket","route_session","decision_timeframe",
         "is_first_emission","setup_dup_count","gross_r","cost_r","spread_r","commission_r",
         "swap_cost_r","expected_slippage_r","policy_target_r","execution_fill_probability",
         "fill_probability","fill_realism_class","scheduler_materialization_status",
         "limit_marketable_at_decision","risk_distance","entry_price","stop_loss",
         "final_blocker_class","bars_to_entry_touch","entry_touched","path_bars",
         "which_came_first","mfe_r","mae_r","r_at_path_end","plain_walk_r","outcome_band",
         "candidate_probability","candidate_ev_r","risk_per_trade_pct"]


def walk_from(fav, adv, cls, start, target_r, stop_r=-1.0, last=None):
    """First-touch walk beginning at 0-based bar `start`. Conservative same-bar tie -> stop."""
    n = len(fav) if last is None else min(len(fav), last)
    if start is None or start >= n:
        return None
    for i in range(start, n):
        if adv[i] <= stop_r + 1e-12:
            return {"r": stop_r, "reason": "stop", "bar": i + 1}
        if fav[i] >= target_r - 1e-12:
            return {"r": target_r, "reason": "target", "bar": i + 1}
    return {"r": cls[n - 1], "reason": "mark", "bar": n}


def main():
    rows = {}
    for r in w0_ws.iter_rows():
        rows[(r["candidate_id"], r["decision_time_utc"])] = r
    sys.stderr.write("ws loaded %d\n" % len(rows)); sys.stderr.flush()

    anch = {}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            a = json.loads(line)
            anch[(a["candidate_id"], a["decision_time_utc"])] = a
    sys.stderr.write("anchor loaded %d\n" % len(anch)); sys.stderr.flush()

    n_out = 0
    miss_anchor = 0
    with gzip.open(OUT, "wt", encoding="utf-8") as out:
        for rp in w0_ws.iter_rpaths():
            k = (rp["candidate_id"], rp["decision_time_utc"])
            r = rows.get(k)
            if r is None:
                continue
            fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
            n = len(fav)
            a = anch.get(k)
            if a is None:
                miss_anchor += 1
                mkt = None; anchor_exact = None
            else:
                mkt = a.get("mkt_r_prev_close"); anchor_exact = a.get("anchor_exact")

            if mkt is None:
                born = "unknown"
            elif mkt <= -1.0 + 1e-12:
                born = "past_stop"
            elif mkt < -1e-12:
                born = "marketable"
            elif mkt <= 1e-12:
                born = "at_limit"
            else:
                born = "resting"

            # ---- fill bar (strict passive): first bar with adv <= 0
            fb = next((i for i in range(n) if adv[i] <= 1e-12), None)

            tgt_flat = 2.0
            tgt_pol = float(r.get("policy_target_r") or 2.0)

            rec = {"candidate_id": rp["candidate_id"], "decision_time_utc": rp["decision_time_utc"],
                   "mkt_r_prev_close": mkt, "anchor_exact": anchor_exact, "born": born,
                   "n_bars": n, "fill_bar0": fb}
            for c in CARRY:
                rec[c] = r.get(c)

            # (a) FILL-BLIND ceiling: enter at entry_price at bar 1 regardless of whether
            #     price ever traded there.  This is the pool's own convention.
            wb = walk_from(fav, adv, cls, 0, tgt_flat)
            rec["blind_r"] = wb["r"]; rec["blind_reason"] = wb["reason"]; rec["blind_bar"] = wb["bar"]
            wbp = walk_from(fav, adv, cls, 0, tgt_pol)
            rec["blind_r_pol"] = wbp["r"]; rec["blind_reason_pol"] = wbp["reason"]

            # (b) OWNER CONTRACT: strict passive fill, then walk from the fill bar.
            if fb is None:
                rec["fill_r"] = None; rec["fill_reason"] = "no_fill"; rec["fill_exit_bar"] = None
                rec["fill_r_pol"] = None; rec["fill_life"] = 0
            else:
                wf = walk_from(fav, adv, cls, fb, tgt_flat)
                rec["fill_r"] = wf["r"]; rec["fill_reason"] = wf["reason"]; rec["fill_exit_bar"] = wf["bar"]
                wfp = walk_from(fav, adv, cls, fb, tgt_pol)
                rec["fill_r_pol"] = wfp["r"]
                rec["fill_life"] = n - fb

            # (c) CHASE / market entry at the decision price, same stop+target PRICE levels.
            #     Booked in declared-R units = level - mkt.  risk-normalised divides by (1+mkt).
            if mkt is not None and mkt > -1.0 + 1e-12:
                wc = walk_from(fav, adv, cls, 0, tgt_flat)
                rec["chase_r_samesize"] = wc["r"] - mkt
                rec["chase_r_risknorm"] = (wc["r"] - mkt) / (1.0 + mkt)
                rec["chase_reason"] = wc["reason"]
            else:
                rec["chase_r_samesize"] = None; rec["chase_r_risknorm"] = None
                rec["chase_reason"] = "already_past_stop"

            # (e) marketable true-price fill sensitivity: fill at the decision price instead of
            #     the limit, when the limit is through the market (mkt < 0).  Same levels.
            if mkt is not None and mkt < -1e-12 and fb is not None:
                rec["truefill_r_samesize"] = rec["fill_r"] - mkt if rec["fill_r"] is not None else None
            else:
                rec["truefill_r_samesize"] = rec["fill_r"]

            # ---- MFE/MAE measured only from the fill bar onward (adverse-selection inputs)
            if fb is not None:
                seg_f = fav[fb:]; seg_a = adv[fb:]
                rec["mfe_after_fill"] = max(seg_f) if seg_f else None
                rec["mae_after_fill"] = min(seg_a) if seg_a else None
                rec["r_end_after_fill"] = cls[n-1]
                # how far did price run AWAY (favourably) before coming back to fill?
                rec["mfe_before_fill"] = max(fav[:fb]) if fb > 0 else None
                rec["mae_before_fill"] = min(adv[:fb]) if fb > 0 else None
            else:
                rec["mfe_after_fill"] = None; rec["mae_after_fill"] = None
                rec["r_end_after_fill"] = None
                rec["mfe_before_fill"] = max(fav) if n else None
                rec["mae_before_fill"] = min(adv) if n else None

            out.write(json.dumps(rec) + "\n")
            n_out += 1
            if n_out % 5000 == 0:
                sys.stderr.write("  %d\n" % n_out); sys.stderr.flush()

    sys.stderr.write("DONE rows=%d missing_anchor=%d -> %s\n" % (n_out, miss_anchor, OUT))


if __name__ == "__main__":
    main()
