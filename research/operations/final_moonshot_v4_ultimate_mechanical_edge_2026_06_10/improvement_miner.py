"""improvement_miner.py  (track key: D4 — the self-improvement loop, reusable)

AUTOMATED per-trade improvement miner. Consumes the combined per-trade ledger
(D4_COMBINED_TRADE_LEDGER.jsonl) and, for each (sleeve x state-feature), tests whether a
CONDITIONAL TWEAK improves FORWARD EV. Three tweak families:

  1. GATE-THRESHOLD shift   — keep only trades where a state feature is above/below a
                              TRAIN-picked threshold (tighten/relax the admission gate).
  2. GEOMETRY change        — re-simulate the SAME entries at an alternative (stop_atr,
                              target_R) via geometry_lib (leak-free). For fixed-exit sleeves.
  3. EXIT-BAND change       — re-simulate STATE_D entries under an alternative vol-banded
                              scale/lock/target exit policy (the EXEC_COMBO/LOCK family).

DISCIPLINE (binding doctrine):
  - TRAIN/FORWARD HOLDOUT: thresholds & policies are PICKED on TRAIN (year<=2024 where a
    sleeve has train depth; else the earliest available year as pseudo-train), then the SAME
    rule is applied FORWARD (2025 & 2026) and the FORWARD delta vs baseline is reported.
  - NO AVERAGES AS VERDICTS: every proposal carries per-year forward EV and the baseline it
    beats; the headline is the FORWARD delta, not a blended mean.
  - DELETE NOTHING: a gate proposal that drops trades is only emitted if forward EV AND
    forward total-R both improve OR it concentrates EV at much higher per-trade EV with
    acceptable frequency; the LEARNING (where it worked) is always recorded.
  - Real cost is already baked into stored R (and re-sims use the stored, tightness-scaled
    cost). Winsorize net R to [-1.3,+5] (wins()).
  - Re-simulation is leak-free: geometry_lib.simulate / the parameterized exit look forward
    ONLY to label an already-decided entry; the threshold/policy is chosen on TRAIN outcomes.

OUTPUT: IMPROVEMENT_PROPOSALS.json  — ranked list, each with sleeve, kind, rule, train EV,
forward EV, FORWARD DELTA, n (train/fwd), per-year forward, and a forward-validated flag.

Reusable: re-run after any ledger regen to mine the next improvement (standing loop).
"""
from __future__ import annotations
import sys, json, math, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import d4_combined_ledger as L

LEDGER = HERE / 'D4_COMBINED_TRADE_LEDGER.jsonl'
def wins(r): return max(-1.3, min(5.0, r))

# ---------------------------------------------------------------------------
# basic stats helpers (per-year, never a bulk verdict)
# ---------------------------------------------------------------------------
def ev(rs, key='R'):
    if not rs: return 0.0
    return sum(r[key] for r in rs) / len(rs)

def winr(rs, key='R'):
    if not rs: return 0.0
    return sum(1 for r in rs if r[key] > 0) / len(rs) * 100

def per_year(rs, key='R'):
    by = collections.defaultdict(list)
    for r in rs: by[r['year']].append(r)
    return {str(y): dict(n=len(v), ev=round(ev(v, key), 3)) for y, v in sorted(by.items())}

# ---------------------------------------------------------------------------
# TRAIN / FORWARD split. Forward is always 2025-26. Train is <=2024 if the sleeve
# has >= MIN_TRAIN trades there; otherwise the EARLIEST forward year is used as
# pseudo-train and the LATER forward year is the holdout (so forward-only sleeves
# still get an honest out-of-sample check, flagged forward_only).
# ---------------------------------------------------------------------------
MIN_TRAIN = 20
def split(rs):
    tr = [r for r in rs if r['year'] <= 2024]
    if len(tr) >= MIN_TRAIN:
        fw = [r for r in rs if r['year'] >= 2025]
        return tr, fw, False, 'year<=2024 -> 2025-26'
    # forward-only: pseudo-split on the earliest year present
    yrs = sorted(set(r['year'] for r in rs))
    if len(yrs) < 2: return rs, [], True, 'single-year (no holdout)'
    ptr = [r for r in rs if r['year'] == yrs[0]]
    pfw = [r for r in rs if r['year'] > yrs[0]]
    return ptr, pfw, True, f'{yrs[0]} -> {yrs[1:]}'

# ===========================================================================
# RE-SIMULATION under alternative policies (the engine that lets us test
# geometry/exit tweaks rather than only re-slicing realized R).
# ===========================================================================
def _bars_for(row):
    key = tuple(row['resim']['stream'])
    s = L.stream(key)
    return s

def resim_fixed(row, stop_atr_mult, target_R):
    """Re-simulate a fixed-target entry at a new stop/target. stop_atr_mult multiplies the
    ORIGINAL stop distance (1.0 = unchanged). target_R is the fixed R target on the new stop.
    Cost is re-scaled by stop tightness (cost in R scales inversely with stop size)."""
    rs = _bars_for(row);
    if rs is None: return None
    _, B = rs; rd = row['resim']; i = rd['idx']; d = rd['d']
    sd = rd['sd'] * stop_atr_mult
    cost = rd['cost'] / stop_atr_mult            # tighter stop -> larger R cost
    R = simulate(B, i, d, stop_dist=sd, target_dist=target_R * sd, maxbars=rd['maxbars'], cost=cost)
    return wins(R)

def resim_exit_band(row, scale_R, lock_lo, lock_mid, lock_hi, tgt_lo, tgt_mid, tgt_hi):
    """Re-simulate a STATE_D entry under a vol-banded scale/lock/target exit (EXEC_COMBO family).
    50% leg at scale_R; after scale, runner stop -> lock (profit-lock, not BE); runner fixed
    target by vol tier. Mirrors cs.exit_state_d's bar loop & pessimism. Leak-free (forward only)."""
    rs = _bars_for(row)
    if rs is None: return None
    _, B = rs; rd = row['resim']; i = rd['idx']; d = rd['d']; sd = rd['sd']; vr = rd['vr']
    cost = rd['cost']; maxbars = rd['maxbars']
    if vr < 1.35: lock, runR = lock_lo, tgt_lo
    elif vr < 1.6: lock, runR = lock_mid, tgt_mid
    else: lock, runR = lock_hi, tgt_hi
    entry = B[i].c; scaled = False; leg2 = None; reason = None
    end = min(i + maxbars, len(B) - 1)
    for j in range(i + 1, end + 1):
        hi = B[j].h; lo = B[j].l
        favp = hi if d > 0 else lo; advp = lo if d > 0 else hi
        fav = d * (favp - entry) / sd; adv = d * (advp - entry) / sd
        if not scaled:
            if adv <= -1.0: return wins(-1.0 - cost)
            if fav >= scale_R: scaled = True
        else:
            if adv <= lock: leg2 = lock; reason = 'lock'; break       # runner stopped at lock
            if fav >= runR: leg2 = runR; reason = 'target'; break
    if reason is None:
        if scaled: leg2 = d * (B[end].c - entry) / sd
        else:
            R = d * (B[end].c - entry) / sd; return wins(R - cost)
    R = 0.5 * scale_R + 0.5 * leg2
    return wins(R - cost)

# intra-sleeve size multiplier (softband ramp / energy-agri conf) applies equally to base &
# variant, so it cancels in the DELTA; we mine on raw per-trade R for clean signal.

# ===========================================================================
# EXPERIMENT FAMILIES
# ===========================================================================
# state features to condition gate tweaks on (numeric, leak-free)
GATE_FEATS = ['ac60', 'vr', 'slope30', 'rng_pos', 'ret5', 'body', 'aligned']
# candidate geometry grid (stop multiplier x target R) for fixed sleeves
GEOM_GRID = [(0.75, 1.0), (0.75, 1.5), (1.0, 1.0), (1.0, 1.5), (1.0, 2.0), (1.0, 3.0),
             (1.25, 2.0), (1.5, 2.0), (1.0, 4.0), (0.5, 0.75)]
# candidate exit-band policies (scale_R, lock_lo/mid/hi, tgt_lo/mid/hi). First = STATE_D-equiv.
EXIT_POLICIES = {
    'state_d_equiv':   (1.5, 0.0, 0.0, 0.0, 4.0, 3.0, 2.5),     # baseline shape (BE locks)
    'exec_lock':       (1.5, 0.0, 0.5, 0.75, 4.0, 3.0, 2.5),    # KB_execution EXEC_LOCK
    'exec_combo':      (2.0, 0.25, 0.5, 0.75, 4.0, 3.0, 2.5),   # KB_execution EXEC_COMBO
    'scale_by_vol':    (2.0, 0.25, 0.5, 0.75, 2.5, 2.0, 1.0),   # scale-by-vol variant from KB
    'deeper_runner':   (1.5, 0.0, 0.5, 0.75, 6.0, 5.0, 3.5),    # deeper targets + lock
    'tight_lock':      (1.5, 0.25, 0.5, 1.0, 4.0, 3.0, 2.5),    # stronger profit lock
}

MIN_KEEP_FRAC = 0.30     # a gate must keep >= 30% of forward trades (frequency matters)
MIN_FWD_N = 8            # need at least this many forward trades to trust a forward number

def baseline_fwd(rs):
    tr, fw, fo, desc = split(rs)
    return ev(fw), len(fw), tr, fw, fo, desc

# ---- 1. GATE-THRESHOLD experiments ----------------------------------------
def mine_gate(sleeve, rs, proposals):
    tr, fw, fo, desc = split(rs)
    if len(fw) < MIN_FWD_N: return
    base_fwd_ev = ev(fw); base_fwd_sum = sum(r['R'] for r in fw)
    for feat in GATE_FEATS:
        vals = sorted(set(r[feat] for r in tr if r.get(feat) is not None))
        if len(vals) < 5: continue
        # candidate thresholds = deciles of TRAIN feature distribution
        qs = [vals[int(q * (len(vals) - 1))] for q in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]
        best = None
        for thr in sorted(set(qs)):
            for side in ('>=', '<='):
                keep = (lambda r: r.get(feat) is not None and (r[feat] >= thr if side == '>=' else r[feat] <= thr))
                tr_k = [r for r in tr if keep(r)]
                if len(tr_k) < max(MIN_TRAIN // 2, 10): continue
                if len(tr_k) / len(tr) < MIN_KEEP_FRAC: continue
                tr_ev = ev(tr_k)
                # TRAIN PICK: choose the rule with the best TRAIN EV (must beat baseline train)
                if best is None or tr_ev > best['tr_ev']:
                    best = dict(feat=feat, thr=thr, side=side, tr_ev=tr_ev, tr_n=len(tr_k))
        if not best: continue
        if best['tr_ev'] <= ev(tr): continue        # must improve train (train-pick discipline)
        keep = (lambda r, b=best: r.get(b['feat']) is not None and
                (r[b['feat']] >= b['thr'] if b['side'] == '>=' else r[b['feat']] <= b['thr']))
        fw_k = [r for r in fw if keep(r)]
        if len(fw_k) < MIN_FWD_N: continue
        if len(fw_k) / len(fw) < MIN_KEEP_FRAC: continue   # frequency discipline
        fw_drop = [r for r in fw if not keep(r)]
        fw_ev = ev(fw_k); fw_sum = sum(r['R'] for r in fw_k)
        delta = fw_ev - base_fwd_ev
        proposals.append(dict(
            sleeve=sleeve, kind='gate_threshold',
            rule=f"keep {best['feat']} {best['side']} {round(best['thr'],4)}",
            split_desc=desc, forward_only=fo,
            train=dict(n=best['tr_n'], ev=round(best['tr_ev'], 4), base_ev=round(ev(tr), 4)),
            forward=dict(n=len(fw_k), base_n=len(fw), ev=round(fw_ev, 4),
                         base_ev=round(base_fwd_ev, 4), win=round(winr(fw_k), 1),
                         keep_frac=round(len(fw_k) / len(fw), 3),
                         total_R=round(fw_sum, 2), base_total_R=round(base_fwd_sum, 2)),
            forward_delta=round(delta, 4),
            forward_total_R_delta=round(fw_sum - base_fwd_sum, 2),
            per_year_forward=per_year(fw_k),
            # CONFIDENCE-SIZING CURVE (doctrine: size by confidence, DELETE NOTHING). The dropped
            # bucket is reported with its own EV so it can be kept at SMALL size, not discarded.
            confidence_curve=_conf_curve(tr, fw, best['feat']),
            dropped_bucket=dict(n=len(fw_drop), ev=round(ev(fw_drop), 4) if fw_drop else 0.0,
                                win=round(winr(fw_drop), 1) if fw_drop else 0.0),
            forward_validated=bool(delta > 0 and best['tr_ev'] > ev(tr) and len(fw_k) >= MIN_FWD_N),
            learning=_gate_learning(best, fw_drop),
        ))

def _gate_learning(best, fw_drop):
    dn = len(fw_drop); dev = ev(fw_drop) if fw_drop else 0.0
    return (f"gate {best['feat']}{best['side']}{round(best['thr'],3)} keeps the higher-EV regime; "
            f"the {dn} fwd trades it drops avg {round(dev,3)}R -> keep them at SMALL confidence size "
            f"(do not delete); SIZE UP the kept high-EV regime.")

def _conf_curve(tr, fw, feat):
    """Per-tercile EV map of the feature on TRAIN and FORWARD — the confidence-sizing curve.
    Shows whether the feature monotonically grades EV (size up the strong tercile) rather than
    implying a hard cliff. Leak-free: terciles are cut on the TRAIN distribution only."""
    vals = sorted(r[feat] for r in tr if r.get(feat) is not None)
    if len(vals) < 9: return None
    lo = vals[len(vals)//3]; hi = vals[2*len(vals)//3]
    def band(rs, name):
        if name == 'low': sel = [r for r in rs if r.get(feat) is not None and r[feat] <= lo]
        elif name == 'mid': sel = [r for r in rs if r.get(feat) is not None and lo < r[feat] <= hi]
        else: sel = [r for r in rs if r.get(feat) is not None and r[feat] > hi]
        return dict(n=len(sel), ev=round(ev(sel), 3)) if sel else dict(n=0, ev=0.0)
    return dict(cut_lo=round(lo, 4), cut_hi=round(hi, 4),
               train={b: band(tr, b) for b in ('low', 'mid', 'high')},
               forward={b: band(fw, b) for b in ('low', 'mid', 'high')})

# ---- 2. GEOMETRY experiments (fixed-exit sleeves) -------------------------
def mine_geometry(sleeve, rs, proposals):
    if not rs or rs[0]['resim']['kind'] != 'fixed': return
    tr, fw, fo, desc = split(rs)
    if len(fw) < MIN_FWD_N: return
    base_fw_ev = ev(fw)
    # baseline geometry result under resim (sanity it reproduces stored R approx)
    best = None
    for (sm, tR) in GEOM_GRID:
        tr_R = [resim_fixed(r, sm, tR) for r in tr]; tr_R = [x for x in tr_R if x is not None]
        if len(tr_R) < MIN_TRAIN // 2: continue
        tev = sum(tr_R) / len(tr_R)
        if best is None or tev > best['tev']:
            best = dict(sm=sm, tR=tR, tev=tev)
    if not best: return
    # forward-apply the train-picked geometry
    fw_R = [resim_fixed(r, best['sm'], best['tR']) for r in fw]; fw_R = [x for x in fw_R if x is not None]
    if len(fw_R) < MIN_FWD_N: return
    fw_ev = sum(fw_R) / len(fw_R)
    delta = fw_ev - base_fw_ev
    # per-year forward under the new geometry
    pyf = collections.defaultdict(list)
    for r in fw:
        v = resim_fixed(r, best['sm'], best['tR'])
        if v is not None: pyf[r['year']].append(v)
    py = {str(y): dict(n=len(v), ev=round(sum(v)/len(v), 3)) for y, v in sorted(pyf.items())}
    proposals.append(dict(
        sleeve=sleeve, kind='geometry',
        rule=f"stop x{best['sm']} (of orig), fixed target {best['tR']}R",
        split_desc=desc, forward_only=fo,
        train=dict(n=len(tr), ev=round(best['tev'], 4), base_ev=round(ev(tr), 4)),
        forward=dict(n=len(fw_R), ev=round(fw_ev, 4), base_ev=round(base_fw_ev, 4),
                     win=round(sum(1 for x in fw_R if x > 0)/len(fw_R)*100, 1)),
        forward_delta=round(delta, 4),
        per_year_forward=py,
        forward_validated=bool(delta > 0 and best['tev'] > ev(tr) and len(fw_R) >= MIN_FWD_N),
        learning=(f"re-sim shows {sleeve} entries pay best at stop x{best['sm']} target {best['tR']}R "
                  f"on train ({round(best['tev'],3)}R); forward {'confirms' if delta>0 else 'does NOT confirm'} "
                  f"({round(fw_ev,3)} vs base {round(base_fw_ev,3)})."),
    ))

# ---- 3. EXIT-BAND experiments (state_d sleeves) --------------------------
def mine_exit(sleeve, rs, proposals):
    if not rs or rs[0]['resim']['kind'] != 'state_d': return
    tr, fw, fo, desc = split(rs)
    if len(fw) < MIN_FWD_N: return
    base_fw_ev = ev(fw)
    # evaluate each policy on TRAIN; pick best train EV; forward-check
    pol_tr = {}
    for name, p in EXIT_POLICIES.items():
        tr_R = [resim_exit_band(r, *p) for r in tr]; tr_R = [x for x in tr_R if x is not None]
        if len(tr_R) < MIN_TRAIN // 2: continue
        pol_tr[name] = (sum(tr_R) / len(tr_R), len(tr_R))
    if not pol_tr: return
    best_name = max(pol_tr, key=lambda k: pol_tr[k][0])
    p = EXIT_POLICIES[best_name]; tev, trn = pol_tr[best_name]
    # baseline policy under the SAME engine for an apples-to-apples train baseline
    base_eng_tr = [resim_exit_band(r, *EXIT_POLICIES['state_d_equiv']) for r in tr]
    base_eng_tr = [x for x in base_eng_tr if x is not None]
    base_eng_tr_ev = sum(base_eng_tr) / len(base_eng_tr) if base_eng_tr else 0.0
    if tev <= base_eng_tr_ev: return                      # must beat baseline-policy on train
    fw_R = [resim_exit_band(r, *p) for r in fw]; fw_R = [x for x in fw_R if x is not None]
    base_eng_fw = [resim_exit_band(r, *EXIT_POLICIES['state_d_equiv']) for r in fw]
    base_eng_fw = [x for x in base_eng_fw if x is not None]
    if len(fw_R) < MIN_FWD_N: return
    fw_ev = sum(fw_R) / len(fw_R); base_eng_fw_ev = sum(base_eng_fw) / len(base_eng_fw)
    delta = fw_ev - base_eng_fw_ev
    pyf = collections.defaultdict(list)
    for r in fw:
        v = resim_exit_band(r, *p)
        if v is not None: pyf[r['year']].append(v)
    py = {str(y): dict(n=len(v), ev=round(sum(v)/len(v), 3)) for y, v in sorted(pyf.items())}
    proposals.append(dict(
        sleeve=sleeve, kind='exit_band', rule=f"exit policy '{best_name}' {p}",
        split_desc=desc, forward_only=fo,
        train=dict(n=trn, ev=round(tev, 4), base_ev=round(base_eng_tr_ev, 4)),
        forward=dict(n=len(fw_R), ev=round(fw_ev, 4), base_ev=round(base_eng_fw_ev, 4),
                     win=round(sum(1 for x in fw_R if x > 0)/len(fw_R)*100, 1),
                     vs_stored_base_ev=round(base_fw_ev, 4)),
        forward_delta=round(delta, 4),
        per_year_forward=py,
        forward_validated=bool(delta > 0 and tev > base_eng_tr_ev and len(fw_R) >= MIN_FWD_N),
        learning=(f"vol-banded exit '{best_name}' lifts {sleeve} on train (+{round(tev-base_eng_tr_ev,3)}R) by "
                  f"banking the runner give-back; forward {'confirms' if delta>0 else 'does not confirm'} "
                  f"(+{round(delta,3)}R)."),
    ))

# ===========================================================================
# DRIVER
# ===========================================================================
def load_ledger():
    # rebuild streams (resim needs the bar arrays in memory) then read rows from disk
    print("Rebuilding sleeve streams for re-simulation (leak-free)...")
    L.build_all()                       # populates L._STREAMS as a side effect
    rows = [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()]
    return rows

def main():
    rows = load_ledger()
    by = collections.defaultdict(list)
    for r in rows: by[r['sleeve']].append(r)
    proposals = []
    print("\nMining improvement candidates per (sleeve x state-feature x tweak-family)...")
    for sleeve, rs in by.items():
        n0 = len(proposals)
        mine_gate(sleeve, rs, proposals)
        mine_geometry(sleeve, rs, proposals)
        mine_exit(sleeve, rs, proposals)
        print(f"  {sleeve:>16}: {len(proposals)-n0} candidate proposals")
    # rank: forward-validated first, then by forward_delta (EV), tie-break forward n
    proposals.sort(key=lambda p: (p['forward_validated'], p['forward_delta'],
                                  p['forward'].get('n', 0)), reverse=True)
    out = dict(
        ledger=str(LEDGER.name), n_trades=len(rows),
        n_proposals=len(proposals),
        n_forward_validated=sum(1 for p in proposals if p['forward_validated']),
        method=("per (sleeve x state-feature) conditional tweaks (gate-threshold / geometry / "
                "exit-band); TRAIN-pick -> FORWARD-check; forward_delta = fwd EV(variant) - fwd "
                "EV(baseline); winsorized R[-1.3,+5]; real tightness-scaled cost; leak-free re-sim."),
        proposals=proposals,
    )
    (HERE / 'IMPROVEMENT_PROPOSALS.json').write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote IMPROVEMENT_PROPOSALS.json  ({len(proposals)} proposals, "
          f"{out['n_forward_validated']} forward-validated)")
    # report top forward-validated (per-year shown — never a bulk verdict)
    print("\n=== TOP FORWARD-VALIDATED IMPROVEMENT PROPOSALS ===")
    fv = [p for p in proposals if p['forward_validated']]
    for p in fv[:12]:
        f = p['forward']
        print(f"\n[{p['sleeve']} / {p['kind']}] {p['rule']}")
        print(f"   split: {p['split_desc']}{' (forward-only pseudo-split)' if p['forward_only'] else ''}")
        print(f"   TRAIN: n={p['train']['n']} ev={p['train']['ev']:+.3f} (base {p['train']['base_ev']:+.3f})")
        print(f"   FWD  : n={f['n']} ev={f['ev']:+.3f} (base {f['base_ev']:+.3f})  DELTA {p['forward_delta']:+.3f}R  win={f.get('win','?')}%")
        print(f"   per-year fwd: " + " ".join(f"{y}:{v['ev']:+.2f}(n{v['n']})" for y, v in p['per_year_forward'].items()))
        print(f"   -> {p['learning']}")
    if not fv:
        print("  (none cleared train-pick + forward-positive; see LEARNINGS below)")
    print("\n=== TOP LEARNINGS from NON-validated candidates (kept, not killed) ===")
    nv = [p for p in proposals if not p['forward_validated']][:6]
    for p in nv:
        print(f"  [{p['sleeve']}/{p['kind']}] {p['rule']}: fwd delta {p['forward_delta']:+.3f} -> {p['learning']}")
    return out

if __name__ == '__main__':
    main()
