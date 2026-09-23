#!/usr/bin/env python3
"""w0-workingset v2 — the fast substrate for all fourteen wave-19 discovery lanes.

ONE streaming pass over the 34 MB ordered-path sidecar. Never holds it in memory.

Emits THREE artifacts:
  w0_WORKING_SET.jsonl.gz       scalar row per candidate: every pool field verbatim +
                                precomputed path geometry in R units.  ~8 MB, ~5 s to load.
  w0_R_PATHS.jsonl.gz           bar-level R arrays per candidate (fav/adv/close/offset),
                                so any exit-policy question is a local simulation and
                                NOBODY has to re-stream the raw sidecar.
  w0_WORKING_SET_BUILD_V2.json  coverage + validation receipt.

SIGN CONVENTION (also in w0_WORKING_SET_README.md)
  d = risk_distance = abs(entry_price - stop_loss)          (price units, > 0)
  Signed R is always for the trade's OWN side, so +1R is always a gain:
      LONG :  fav(bar) = (high - entry)/d      adv(bar) = (low  - entry)/d
      SHORT:  fav(bar) = (entry - low )/d      adv(bar) = (entry - high)/d
  fav >= adv always.  mfe_r = max fav over path; mae_r = min adv over path (normally <= 0).
  Stop level is exactly -1.0 R by construction; target is policy_target_r (2.0 for the pool).

TIE RULE  if target and stop are first touched on the SAME bar -> which_came_first='stop'
          (conservative; M1 bars, no intrabar ordering available).

INDEXING  every bars_to_* is 1-BASED: 1 = the first bar of the path (the bar AFTER the
          decision bar). None = never touched inside the path.
"""
from __future__ import annotations

import gzip
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
POOL = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz")
SIDE = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz")
OUT = os.path.join(DISC, "w0_WORKING_SET.jsonl.gz")
OUT_PATHS = os.path.join(DISC, "w0_R_PATHS.jsonl.gz")
RECEIPT = os.path.join(DISC, "w0_WORKING_SET_BUILD_V2.json")

TOL = 1e-12
BAND_TOL = 1e-3          # the tolerance the ESTABLISHED band table uses (verified below)
STOP_R = -1.0

FAV_LADDER = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0]
ADV_LADDER = [-0.25, -0.5, -0.75, -1.0]
MARK_BARS = [5, 15, 30, 60, 120]


def iter_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def parse_iso(s):
    return datetime.fromisoformat(s)


def band_of(g, tgt):
    """The ESTABLISHED outcome bands, with the 1e-3 edge tolerance."""
    if g >= tgt - BAND_TOL:
        return "ge_target"
    if g >= 1.0 - BAND_TOL:
        return "b_1_to_target"
    if g >= 0.5:
        return "b_05_to_1"
    if g >= 0.1:
        return "b_01_to_05"
    if g > 0:
        return "scratch_0_to_01"
    if g > STOP_R + BAND_TOL:
        return "partial_loss"
    return "full_stop"


def main():
    # ------------------------------------------------------------------ pool
    pool = {}
    dup_pool = 0
    bad_d = 0
    null_econ = 0
    for r in iter_gz(POOL):
        k = (r["candidate_id"], r["decision_time_utc"])
        if k in pool:
            dup_pool += 1
        e, s = r.get("entry_price"), r.get("stop_loss")
        if e is None or s is None or not math.isfinite(float(e)) or not math.isfinite(float(s)) or abs(float(e) - float(s)) <= 0:
            bad_d += 1
        if r.get("opportunity_net_proxy_r") is None or r.get("cost_r") is None:
            null_econ += 1
        pool[k] = r
    n_pool = len(pool)

    # ---- PSEUDO-REPLICATION: candidate_id is NOT a primary key ---------------
    # 21,880 distinct candidate_id across 27,658 rows; 967 ids repeat, one up to 140
    # times.  A repeat is the SAME setup (same entry_price) re-emitted at successive
    # M15 decision times while it stays valid, each emission walked as a whole trade.
    # 91.9 % of current_fvg_fill is repeat rows.  Every lane must be able to collapse
    # this in one line, so the rank/count ship as columns.
    by_cid = defaultdict(list)
    for (cid, dt) in pool:
        by_cid[cid].append(dt)
    dup_rank = {}
    for cid, dts in by_cid.items():
        for i, dt in enumerate(sorted(dts)):
            dup_rank[(cid, dt)] = (i + 1, len(dts))

    # ------------------------------------------------------- stream sidecar
    seen = set()
    dup_side = n_side = no_pool = no_obs = unusable_d = 0
    side_mismatch = symbol_mismatch = tp_geom_mismatch = 0
    written = 0
    bars_hist = Counter()
    first_cross = Counter()
    bands = Counter()
    fam = defaultdict(lambda: dict(n=0, win=0, wsum=0.0, lsum=0.0, l=0, gsum=0.0,
                                   pw=0.0, fh=0.0, cost=0.0))
    blocker = Counter()

    v_n = 0
    v_gross_sum = v_cost_sum = 0.0
    v_win = v_loss = 0
    v_win_sum = v_loss_sum = 0.0
    v_mfe_ge_target = 0
    v_stop_then_reverse_1r = 0
    v_mfe_after_stop_none = 0
    v_plain_sum = v_fh_sum = 0.0
    v_no_entry_touch = 0
    fh_cross = Counter()

    with gzip.open(OUT, "wt", encoding="utf-8") as out, gzip.open(OUT_PATHS, "wt", encoding="utf-8") as outp:
        for row in iter_gz(SIDE):
            n_side += 1
            k = (row["candidate_id"], row["decision_time_utc"])
            if k in seen:
                dup_side += 1
                continue
            seen.add(k)
            p = pool.get(k)
            if p is None:
                no_pool += 1
                continue
            obs = row.get("ordered_path_observations") or []
            if not obs:
                no_obs += 1
                continue
            entry = float(p["entry_price"])
            stop = float(p["stop_loss"])
            d = abs(entry - stop)
            if not math.isfinite(d) or d <= 0:
                unusable_d += 1
                continue
            side = p["side"]
            if row.get("side") and row["side"] != side:
                side_mismatch += 1
            if row.get("symbol") and row["symbol"] != p.get("symbol"):
                symbol_mismatch += 1
            tgt = float(p.get("policy_target_r") or 2.0)
            is_long = side == "LONG"

            tp1 = p.get("take_profit_1")
            if tp1 is not None:
                implied = ((float(tp1) - entry) / d) if is_long else ((entry - float(tp1)) / d)
                if abs(implied - tgt) > 1e-4:
                    tp_geom_mismatch += 1

            t0 = parse_iso(p["decision_time_utc"])

            favs, advs, clss, offs = [], [], [], []
            mfe, mae = -1e18, 1e18
            i_mfe = i_mae = i_tgt = i_stop = i_entry = None
            fav_hit = {}
            adv_hit = {}
            for i, b in enumerate(obs):
                hi, lo, cl = b["high"], b["low"], b["close"]
                if is_long:
                    fav = (hi - entry) / d
                    adv = (lo - entry) / d
                    cr = (cl - entry) / d
                else:
                    fav = (entry - lo) / d
                    adv = (entry - hi) / d
                    cr = (entry - cl) / d
                # Round ONCE, here, and use the rounded values for EVERY decision below.
                # The emitted w0_R_PATHS arrays are these same rounded values, so
                # w0_ws.walk() reproduces every emitted column bit-for-bit. Internal
                # consistency beats 1e-4 R of precision: without this, lanes using walk()
                # and lanes using the columns disagree on ~2,500 rows and cannot reconcile.
                fav = round(fav, 4)
                adv = round(adv, 4)
                cr = round(cr, 4)
                favs.append(fav)
                advs.append(adv)
                clss.append(cr)
                try:
                    offs.append(int(round((parse_iso(b["time_utc"]) - t0).total_seconds() / 60.0)))
                except Exception:
                    offs.append(None)
                if fav > mfe:
                    mfe, i_mfe = fav, i
                if adv < mae:
                    mae, i_mae = adv, i
                if i_tgt is None and fav >= tgt - TOL:
                    i_tgt = i
                if i_stop is None and adv <= STOP_R + TOL:
                    i_stop = i
                if i_entry is None and adv <= 0.0 + TOL:
                    i_entry = i   # price traded at/through entry_price -> a resting limit fills
                for L in FAV_LADDER:
                    if L not in fav_hit and fav >= L - TOL:
                        fav_hit[L] = i + 1
                for L in ADV_LADDER:
                    if L not in adv_hit and adv <= L + TOL:
                        adv_hit[L] = i + 1

            if i_stop is not None and (i_tgt is None or i_stop <= i_tgt):
                which = "stop"
            elif i_tgt is not None:
                which = "target"
            else:
                which = "neither"
            first_cross[which] += 1

            # --- excursions conditioned on the first-touch events -------------
            mfe_after_stop = None          # best R reached STRICTLY AFTER the stop bar
            bars_to_mfe_after_stop = None
            if i_stop is not None and i_stop + 1 < len(obs):
                m, mi = -1e18, None
                for j in range(i_stop + 1, len(obs)):
                    if favs[j] > m:
                        m, mi = favs[j], j
                mfe_after_stop = round(m, 6)
                bars_to_mfe_after_stop = mi + 1
            elif i_stop is not None:
                v_mfe_after_stop_none += 1

            mae_before_target = None       # worst R up to AND INCLUDING the target bar
            if i_tgt is not None:
                m = 1e18
                for j in range(0, i_tgt + 1):
                    if advs[j] < m:
                        m = advs[j]
                mae_before_target = round(m, 6)

            mfe_before_stop = None         # best R up to AND INCLUDING the stop bar
            if i_stop is not None:
                m = -1e18
                for j in range(0, i_stop + 1):
                    if favs[j] > m:
                        m = favs[j]
                mfe_before_stop = round(m, 6)

            r_end = clss[-1]
            marks = {}
            for kb in MARK_BARS:
                marks["r_at_bar_%d" % kb] = clss[kb - 1] if len(clss) >= kb else None
                marks["mfe_r_by_bar_%d" % kb] = round(max(favs[:kb]), 6) if favs else None
                marks["mae_r_by_bar_%d" % kb] = round(min(advs[:kb]), 6) if advs else None

            # --- the plain 2R/-1R first-touch baseline, and its fill-honest twin -----
            # plain_walk_r: what a dumb "target at policy_target_r, stop at -1R, else mark
            # to market at the last bar" contract would have booked on this same path.
            if which == "target":
                plain = tgt
            elif which == "stop":
                plain = STOP_R
            else:
                plain = clss[-1]
            # fill-honest: a resting limit at entry_price only fills once price trades there.
            # Excursion is only creditable from the fill bar onward.
            fh_which, fh_r = "no_fill", 0.0
            if i_entry is not None:
                fi = i_entry
                jt = js = None
                for j in range(fi, len(obs)):
                    if jt is None and favs[j] >= tgt - TOL:
                        jt = j
                    if js is None and advs[j] <= STOP_R + TOL:
                        js = j
                    if jt is not None or js is not None:
                        break
                if js is not None and (jt is None or js <= jt):
                    fh_which, fh_r = "stop", STOP_R
                elif jt is not None:
                    fh_which, fh_r = "target", tgt
                else:
                    fh_which, fh_r = "neither", clss[-1]

            fb, lb = obs[0]["time_utc"], obs[-1]["time_utc"]
            try:
                pm = (parse_iso(lb) - parse_iso(fb)).total_seconds() / 60.0
            except Exception:
                pm = None

            gross = round(float(p["opportunity_net_proxy_r"]) + float(p["cost_r"]), 9)

            rec = dict(p)  # every pool field verbatim
            rec.update(
                risk_distance=d,
                gross_r=gross,
                outcome_band=band_of(gross, tgt),
                mfe_r=round(mfe, 6),
                mae_r=round(mae, 6),
                bars_to_mfe=(i_mfe + 1) if i_mfe is not None else None,
                bars_to_mae=(i_mae + 1) if i_mae is not None else None,
                bars_to_target=(i_tgt + 1) if i_tgt is not None else None,
                bars_to_stop=(i_stop + 1) if i_stop is not None else None,
                which_came_first=which,
                setup_dup_rank=dup_rank[k][0],
                setup_dup_count=dup_rank[k][1],
                is_first_emission=dup_rank[k][0] == 1,
                bars_to_entry_touch=(i_entry + 1) if i_entry is not None else None,
                entry_touched=i_entry is not None,
                entry_touch_before_target=(None if i_tgt is None else
                                           (i_entry is not None and i_entry < i_tgt)),
                entry_touch_same_bar_as_target=(None if i_tgt is None else
                                                (i_entry is not None and i_entry == i_tgt)),
                plain_walk_r=round(plain, 6),
                fill_honest_which_came_first=fh_which,
                fill_honest_walk_r=round(fh_r, 6),
                r_at_path_end=r_end,
                path_bars=len(obs),
                path_minutes=pm,
                first_bar_utc=fb,
                last_bar_utc=lb,
                mfe_r_after_stop=mfe_after_stop,
                bars_to_mfe_after_stop=bars_to_mfe_after_stop,
                mae_r_before_target=mae_before_target,
                mfe_r_before_stop=mfe_before_stop,
                bars_to_fav=[fav_hit.get(L) for L in FAV_LADDER],
                bars_to_adv=[adv_hit.get(L) for L in ADV_LADDER],
                path_horizon_end_utc=row.get("horizon_end_utc"),
                path_source_timeframe=row.get("source_timeframe"),
                path_source_path=row.get("source_path"),
                path_arm_id=row.get("arm_id"),
                **marks,
            )
            out.write(json.dumps(rec, separators=(",", ":")) + "\n")
            outp.write(json.dumps(
                {"candidate_id": p["candidate_id"], "decision_time_utc": p["decision_time_utc"],
                 "symbol": p.get("symbol"), "side": side, "risk_distance": d,
                 "policy_target_r": tgt, "off": offs, "fav": favs, "adv": advs, "cls": clss},
                separators=(",", ":")) + "\n")
            written += 1
            bars_hist[len(obs)] += 1

            # ---- validation, recomputed FROM the emitted record --------------
            v_n += 1
            v_gross_sum += gross
            v_cost_sum += float(p["cost_r"])
            if gross > 0:
                v_win += 1
                v_win_sum += gross
            else:
                v_loss += 1
                v_loss_sum += gross
            bands[rec["outcome_band"]] += 1
            if mfe >= tgt - TOL:
                v_mfe_ge_target += 1
            if mfe_after_stop is not None and mfe_after_stop >= 1.0:
                v_stop_then_reverse_1r += 1
            f = fam[p.get("origin_family")]
            f["n"] += 1
            f["gsum"] += gross
            f["pw"] += plain
            f["fh"] += fh_r
            f["cost"] += float(p["cost_r"])
            if gross > 0:
                f["win"] += 1
                f["wsum"] += gross
            else:
                f["l"] += 1
                f["lsum"] += gross
            blocker[p.get("final_blocker_class")] += 1
            v_plain_sum += plain
            v_fh_sum += fh_r
            fh_cross[fh_which] += 1
            if i_entry is None:
                v_no_entry_touch += 1

    fam_tbl = {}
    for name, f in sorted(fam.items(), key=lambda kv: -(kv[1]["gsum"] / max(kv[1]["n"], 1))):
        wm = f["wsum"] / f["win"] if f["win"] else None
        lm = f["lsum"] / f["l"] if f["l"] else None
        fam_tbl[name] = dict(
            n=f["n"], win_rate=round(f["win"] / f["n"], 4),
            gross_mean=round(f["gsum"] / f["n"], 4),
            plain_walk_mean=round(f["pw"] / f["n"], 4),
            fill_honest_mean=round(f["fh"] / f["n"], 4),
            frozen_cost_mean=round(f["cost"] / f["n"], 4),
            plain_minus_pool=round((f["pw"] - f["gsum"]) / f["n"], 4),
            plain_net_frozen=round((f["pw"] - f["cost"]) / f["n"], 4),
            winner_mean=round(wm, 4) if wm is not None else None,
            loser_mean=round(lm, 4) if lm is not None else None,
            payoff=round(abs(wm / lm), 3) if (wm and lm) else None,
        )

    v = {
        "n": v_n,
        "gross_mean": round(v_gross_sum / v_n, 6),
        "frozen_cost_mean": round(v_cost_sum / v_n, 6),
        "gross_win_rate": round(v_win / v_n, 6),
        "winner_mean_r": round(v_win_sum / v_win, 6),
        "loser_mean_r": round(v_loss_sum / v_loss, 6),
        "payoff_ratio": round(abs((v_win_sum / v_win) / (v_loss_sum / v_loss)), 6),
        "outcome_bands": {k: dict(n=c, share=round(c / v_n, 5)) for k, c in bands.items()},
        "path_which_came_first": {k: dict(n=c, share=round(c / v_n, 5)) for k, c in first_cross.items()},
        "share_mfe_ge_policy_target": round(v_mfe_ge_target / v_n, 6),
        "stopped_then_mfe_ge_1R_after": v_stop_then_reverse_1r,
        "plain_walk_mean_r": round(v_plain_sum / v_n, 6),
        "fill_honest_walk_mean_r": round(v_fh_sum / v_n, 6),
        "plain_minus_pool_gross_r": round((v_plain_sum - v_gross_sum) / v_n, 6),
        "plain_walk_net_frozen_cost_r": round((v_plain_sum - v_cost_sum) / v_n, 6),
        "pool_net_frozen_cost_r": round((v_gross_sum - v_cost_sum) / v_n, 6),
        "fill_honest_which_came_first": {k: dict(n=c, share=round(c / v_n, 5)) for k, c in fh_cross.items()},
        "entry_price_never_touched_in_path": v_no_entry_touch,
    }
    expected = {
        "gross_win_rate": 0.347, "winner_mean_r": 1.044, "loser_mean_r": -0.888,
        "gross_mean": -0.2175, "frozen_cost_mean": 0.663,
        "band_ge_target": 0.111, "band_1_to_target": 0.042, "band_05_to_1": 0.076,
        "band_01_to_05": 0.094, "band_scratch": 0.024, "band_partial_loss": 0.109,
        "band_full_stop": 0.544,
    }
    got = {
        "gross_win_rate": v["gross_win_rate"], "winner_mean_r": v["winner_mean_r"],
        "loser_mean_r": v["loser_mean_r"], "gross_mean": v["gross_mean"],
        "frozen_cost_mean": v["frozen_cost_mean"],
        "band_ge_target": v["outcome_bands"].get("ge_target", {}).get("share"),
        "band_1_to_target": v["outcome_bands"].get("b_1_to_target", {}).get("share"),
        "band_05_to_1": v["outcome_bands"].get("b_05_to_1", {}).get("share"),
        "band_01_to_05": v["outcome_bands"].get("b_01_to_05", {}).get("share"),
        "band_scratch": v["outcome_bands"].get("scratch_0_to_01", {}).get("share"),
        "band_partial_loss": v["outcome_bands"].get("partial_loss", {}).get("share"),
        "band_full_stop": v["outcome_bands"].get("full_stop", {}).get("share"),
    }
    checks = {k: dict(expected=expected[k], got=got[k],
                      abs_err=round(abs(got[k] - expected[k]), 5),
                      pass_=abs(got[k] - expected[k]) <= 0.0015) for k in expected}
    fam_expected_n = {
        "regime_transition_break": 297, "liquidity_sweep_reclaim": 4475,
        "session_open_range_break": 987, "volatility_compression_expansion": 605,
        "displacement_continuation": 4469, "current_ob_retest": 1340,
        "cross_asset_lead_lag": 2083, "current_fvg_fill": 7146,
        "structural_distance_extreme": 1993, "current_breaker_re_entry": 4263,
    }
    fam_check = {k: dict(expected_n=n_, got_n=fam_tbl.get(k, {}).get("n"),
                         pass_=fam_tbl.get(k, {}).get("n") == n_)
                 for k, n_ in fam_expected_n.items()}
    blk_expected = {
        "cost_authority": 20448, "other": 2684, "package_authority": 2668,
        "scheduler_selection": 689, "execution_fillability": 449,
        "selector_materialization": 369, "marketable_guard": 156,
        "fill_realism": 148, "daily_lockout": 47,
    }
    blk_check = {k: dict(expected_n=n_, got_n=blocker.get(k), pass_=blocker.get(k) == n_)
                 for k, n_ in blk_expected.items()}

    all_pass = (all(c["pass_"] for c in checks.values())
                and all(c["pass_"] for c in fam_check.values())
                and all(c["pass_"] for c in blk_check.values()))

    out_rec = {
        "schema": "gtos.wave19.w0.workingset.build.v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"pool": POOL, "sidecar": SIDE},
        "outputs": {"working_set": OUT, "r_paths": OUT_PATHS},
        "coverage": {
            "pool_rows": n_pool, "pool_duplicate_keys": dup_pool,
            "pool_rows_with_nonpositive_risk_distance": bad_d,
            "pool_rows_with_null_economics": null_econ,
            "sidecar_rows": n_side, "sidecar_duplicate_keys": dup_side,
            "sidecar_rows_with_no_pool_match": no_pool,
            "sidecar_rows_with_empty_observations": no_obs,
            "sidecar_rows_dropped_unusable_risk_distance": unusable_d,
            "written": written,
            "pool_rows_without_a_path": n_pool - len(seen & set(pool.keys())),
            "side_field_mismatch_pool_vs_sidecar": side_mismatch,
            "symbol_field_mismatch_pool_vs_sidecar": symbol_mismatch,
            "take_profit_1_vs_policy_target_r_mismatch": tp_geom_mismatch,
            "stop_touched_on_last_bar_no_after_window": v_mfe_after_stop_none,
            "distinct_candidate_id": len(by_cid),
            "candidate_ids_repeating": sum(1 for x in by_cid.values() if len(x) > 1),
            "rows_on_a_repeated_candidate_id": sum(len(x) for x in by_cid.values() if len(x) > 1),
            "max_repeats_for_one_candidate_id": max(len(x) for x in by_cid.values()),
            "PRIMARY_KEY": "(candidate_id, decision_time_utc)  -- candidate_id ALONE IS NOT UNIQUE",
        },
        "validation_recomputed_from_output": v,
        "validation_vs_established": checks,
        "validation_family_counts": fam_check,
        "validation_blocker_counts": blk_check,
        "ALL_VALIDATIONS_PASS": all_pass,
        "family_gross_table": fam_tbl,
        "blocker_counts": dict(blocker),
        "path_bars_histogram_top": dict(bars_hist.most_common(12)),
        "ladders": {"fav_ladder_r": FAV_LADDER, "adv_ladder_r": ADV_LADDER, "mark_bars": MARK_BARS},
        "band_edge_tolerance": BAND_TOL,
    }
    with open(RECEIPT, "w") as fh:
        json.dump(out_rec, fh, indent=1)
    print("WRITTEN", written, "ALL_PASS", all_pass)
    for k, c in checks.items():
        print("CHK %-20s exp=%-8s got=%-8s %s" % (k, c["expected"], c["got"], "OK" if c["pass_"] else "FAIL"))
    print("FAMCHK", sum(1 for c in fam_check.values() if c["pass_"]), "/", len(fam_check))
    print("BLKCHK", sum(1 for c in blk_check.values() if c["pass_"]), "/", len(blk_check))


if __name__ == "__main__":
    main()
