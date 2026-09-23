"""ENERGY + AGRI SLEEVE (track: energy_agri). Commodity-continuation sleeves on
ENERGY (USOIL_cash, UKOIL_cash, NATGAS_cash, HEATOIL_c) and AGRI (CORN_c, COTTON_c)
using the metals carrier machinery:
  ENTRY : H4 FVG-retest continuation in HTF trend.
  GATE  : each decision if is a spot-exact Choice. Two sides of that condition.
          Unique highest probability wins. Empty, tie, and error do not restore
          the measured boolean.
  EXIT  : vol-tiered scale-out STATE_D.
  SIZE  : confidence-weighted.

DATA HONESTY: H4 is the source. No lookahead: features use closed bars index<=i.
"""
from __future__ import annotations
import sys, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs

ENERGY = ['USOIL_cash', 'UKOIL_cash', 'NATGAS_cash', 'HEATOIL_c']
AGRI   = ['CORN_c', 'COTTON_c']
FORWARD_VALIDATABLE = {'USOIL_cash', 'NATGAS_cash', 'CORN_c'}

def wins(r): return max(-1.3, min(5.0, r))

def trend_slope(B, i, lb=30):
    """normalized linear-regression slope of closes over trailing lb bars (closed bars only)."""
    if i < lb: return 0.0
    ys = [B[k].c for k in range(i-lb+1, i+1)]
    n = len(ys); xs = list(range(n))
    mx = (n-1)/2; my = sum(ys)/n
    num = sum((xs[k]-mx)*(ys[k]-my) for k in range(n))
    den = sum((xs[k]-mx)**2 for k in range(n))
    if den == 0: return 0.0
    slope = num/den
    a = atr14(B, i)
    return slope/a if a > 0 else 0.0

def build_candidates():
    """One row per FVG-retest signal across energy+agri, with state + STATE_D outcome."""
    rows = []
    for grp, syms in (('energy', ENERGY), ('agri', AGRI)):
        for s in syms:
            try: T, B = w1.load(s)
            except Exception: continue
            if len(B) < 200: continue
            atrs = [atr14(B, k) for k in range(len(B))]
            for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
                ac = cs.autocorr(B, i, 60)
                vr = cs.vol_ratio(atrs, i)
                slope = trend_slope(B, i, 30)
                tr = w1.htf_trend(B, i, 30)
                ex = cs.exit_state_d(B, i, d, sd, vr, c2)
                base2R = wins(simulate(B, i, d, stop_dist=sd, target_dist=2*sd, cost=c2))
                rows.append(dict(
                    sym=s, grp=grp, year=t.year, month=t.month, date=str(t)[:10], dir=d,
                    ac60=round(ac, 4) if ac is not None else None,
                    vr=round(vr, 3), slope=round(slope, 4), tr=tr,
                    aligned=int(tr == d),
                    R=round(ex['R'], 4), base2R=round(base2R, 4),
                    mfe=round(ex['mfe'], 3), bars1R=ex['bars1R'], reason=ex['reason'],
                    fwd_ok=int(s in FORWARD_VALIDATABLE),
                ))
    return rows

def pstat(rows, key='R'):
    if not rows: return (0, 0.0, 0.0)
    n = len(rows); m = sum(x[key] for x in rows)/n
    w = sum(1 for x in rows if x[key] > 0)/n*100
    return n, round(m, 4), round(w, 1)

def per_year(rows, key='R'):
    yr = collections.defaultdict(list)
    for r in rows: yr[r['year']].append(r)
    return {y: pstat(rs, key) for y, rs in sorted(yr.items())}

def energy_gate(r):
    """Measurement: vr>=2.0 OR |slope|<0.05. Not the decision."""
    return (r['vr'] >= 2.0) or (abs(r['slope']) < 0.05)

def agri_gate_high(r):
    """Measurement: ac60>=0.10. Not the decision."""
    return r['ac60'] is not None and r['ac60'] >= 0.10

def agri_gate_breadth(r):
    """Measurement: month not in Dec-Feb. Not the decision."""
    return r['month'] not in (12, 1, 2)

CONF = {
    'energy_supply_shock': 1.00,
    'energy_flat_breakout': 1.00,
    'agri_persistence': 0.50,
    'agri_seasonal': 0.25,
}
SYM_CONF = {s: (1.0 if s in FORWARD_VALIDATABLE else 0.5) for s in ENERGY + AGRI}


def _choice(spot, measured, true_name, false_name, condition, true_text, false_text, facts):
    from src.components.ultimate_book.sleeves.energy_agri import energy_side
    return energy_side(
        spot,
        bool(measured),
        true_name,
        false_name,
        f"Condition: {condition}. Which side of this condition is the decision?",
        true_text=true_text,
        false_text=false_text,
        facts=facts,
    )


def _facts(r):
    return {
        "sym": r.get("sym"),
        "grp": r.get("grp"),
        "date": r.get("date"),
        "vr": r.get("vr"),
        "slope": r.get("slope"),
        "ac60": r.get("ac60"),
        "month": r.get("month"),
    }


def final_sleeve(rows=None):
    """Tag trades only when the unique highest side of each decision if says so."""
    if rows is None: rows = build_candidates()
    out = []
    for r in rows:
        tags = []
        facts = _facts(r)
        is_energy = _choice(
            "ea_sleeve_grp_energy",
            r["grp"] == "energy",
            "energy",
            "not_energy",
            "r['grp'] == 'energy'",
            "This row is the energy book.",
            "This row is not the energy book.",
            facts,
        )
        if is_energy == "true":
            gate = _choice(
                "ea_sleeve_energy_gate",
                energy_gate(r),
                "gate_open",
                "gate_closed",
                "(r['vr'] >= 2.0) or (abs(r['slope']) < 0.05)",
                "This energy bar is inside the state gate.",
                "This energy bar is outside the state gate.",
                facts,
            )
            if gate == "true":
                shock = _choice(
                    "ea_sleeve_vr_ge_2",
                    r["vr"] >= 2.0,
                    "supply_shock",
                    "flat_breakout",
                    "r['vr'] >= 2.0",
                    "vr is at least 2.0. Tag supply shock.",
                    "vr is below 2.0. Tag flat breakout.",
                    facts,
                )
                if shock == "true":
                    tags.append(("energy_supply_shock", CONF["energy_supply_shock"]))
                elif shock == "false":
                    tags.append(("energy_flat_breakout", CONF["energy_flat_breakout"]))
        is_agri = _choice(
            "ea_sleeve_grp_agri",
            r["grp"] == "agri",
            "agri",
            "not_agri",
            "r['grp'] == 'agri'",
            "This row is the agri book.",
            "This row is not the agri book.",
            facts,
        )
        if is_agri == "true":
            high = _choice(
                "ea_sleeve_agri_persistence",
                agri_gate_high(r),
                "persistence",
                "not_persistence",
                "r['ac60'] is not None and r['ac60'] >= 0.10",
                "ac60 persistence holds. Tag agri persistence.",
                "ac60 persistence does not hold.",
                facts,
            )
            if high == "true":
                tags.append(("agri_persistence", CONF["agri_persistence"]))
            elif high == "false":
                season = _choice(
                    "ea_sleeve_agri_breadth",
                    agri_gate_breadth(r),
                    "in_season",
                    "winter",
                    "r['month'] not in (12, 1, 2)",
                    "Month is outside the winter dead-zone. Tag seasonal breadth.",
                    "Month is in the winter dead-zone.",
                    facts,
                )
                if season == "true":
                    tags.append(("agri_seasonal", CONF["agri_seasonal"]))
        drop = _choice(
            "ea_sleeve_not_tags",
            not tags,
            "drop",
            "keep",
            "not tags",
            "No tag. Drop this row.",
            "A tag is present. Keep this row.",
            facts,
        )
        if drop == "true" or drop is None or not tags:
            continue
        tag, base_conf = tags[0]
        conf = base_conf * SYM_CONF.get(r["sym"], 0.5)
        rr = dict(r); rr["tag"] = tag; rr["conf"] = round(conf, 3)
        out.append(rr)
    return out

def _byyear_str(rs):
    yr = collections.defaultdict(list)
    for r in rs: yr[r['year']].append(r)
    return ' '.join(f"{y}:{pstat(v)[1]:+.2f}(n{pstat(v)[0]})" for y, v in sorted(yr.items()))

def _bysym_str(rs):
    sy = collections.defaultdict(list)
    for r in rs: sy[r['sym']].append(r)
    return ' '.join(f"{s.split('_')[0]}:{pstat(v)[1]:+.2f}(n{pstat(v)[0]})" for s, v in sorted(sy.items()))

if __name__ == '__main__':
    rows = build_candidates()
    (HERE/'ENERGY_AGRI_CANDIDATES.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
    sleeve = final_sleeve(rows)
    (HERE/'ENERGY_AGRI_SLEEVE_TRADES.jsonl').write_text('\n'.join(json.dumps(r) for r in sleeve))
    print(f"built {len(rows)} candidates -> {len(sleeve)} gated sleeve trades\n")
    for tag in ('energy_supply_shock', 'energy_flat_breakout', 'agri_persistence', 'agri_seasonal'):
        rs = [r for r in sleeve if r['tag'] == tag]
        if not rs: continue
        n, m, w = pstat(rs)
        print(f"\n[{tag}]  n={n}  EV={m:+.3f}R  win={w:.0f}%  conf={CONF[tag]}")
        print(f"   per-year: {_byyear_str(rs)}")
        print(f"   per-sym : {_bysym_str(rs)}")
    en = [r for r in sleeve if r['grp'] == 'energy']
    ag = [r for r in sleeve if r['grp'] == 'agri']
    print(f"\n--- ENERGY combined: {pstat(en)} | {_byyear_str(en)}")
    print(f"--- AGRI combined  : {pstat(ag)} | {_byyear_str(ag)}")
    enf = [r for r in en if r['year'] >= 2025]; agf = [r for r in ag if r['year'] >= 2025]
    print(f"\nFORWARD 2025-26: energy {pstat(enf)} | agri {pstat(agf)}")
    def conf_ev(rs):
        if not rs: return 0.0
        return round(sum(r['R']*r['conf'] for r in rs)/sum(r['conf'] for r in rs), 4)
    print(f"FORWARD conf-weighted EV: energy {conf_ev(enf)}R | agri {conf_ev(agf)}R | all {conf_ev(enf+agf)}R")
    allf = enf + agf
    n, m, w = pstat(allf)
    print(f"FORWARD all energy+agri: n={n} EV={m:+.3f}R win={w:.0f}% conf-wtd={conf_ev(allf)}R")
