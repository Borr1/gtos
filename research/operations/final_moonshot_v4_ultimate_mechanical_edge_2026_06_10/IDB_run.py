"""IDB driver — produce the intraday-breadth result JSON + ledger (track: IDB).

Reports, for every probed family, TRAIN(2025-H2)/FWD(2026-H1) per-half, per-symbol both-halves,
per-direction, trades/yr, and the combined frequency lift vs the validated book. Emits both the
VALIDATED additions (FVG-retest H1 crypto + metals) and the LEARNINGS (raw breakout intraday
falsified; energy intraday falsified) — nothing killed, everything sized by confidence.
"""
import sys, json, statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parents[2]))
import IDB_intraday_breadth as idb

def half(t): return 'TRAIN' if t.year==2025 else 'FWD'
def st(rows):
    if not rows: return dict(n=0,ev=0.0,win=0.0)
    return dict(n=len(rows), ev=round(sum(r['R'] for r in rows)/len(rows),4),
                win=round(sum(1 for r in rows if r['R']>0)/len(rows)*100,1))
def spl(rows):
    return st([r for r in rows if half(r['t'])=='TRAIN']), st([r for r in rows if half(r['t'])=='FWD'])

def scorecard(name, rows, ps, kind):
    tr,fw=spl(rows)
    persym={}
    both=0
    for s,r in ps.items():
        if not r: continue
        a,b=spl(r); persym[s]=dict(train=a,fwd=b,
                                   both_pos=bool(a['ev']>0 and b['ev']>0))
        if a['ev']>0 and b['ev']>0: both+=1
    dirs={}
    for d,lab in ((1,'long'),(-1,'short')):
        rr=[x for x in rows if x['dir']==d]; a,b=spl(rr); dirs[lab]=dict(train=a,fwd=b)
    Rs=[r['R'] for r in rows]
    return dict(name=name, kind=kind, train=tr, fwd=fw,
                trades_yr=idb.per_yr(len(rows)),
                both_halves_carriers=both, n_carriers=len([1 for r in ps.values() if r]),
                per_symbol=persym, per_direction=dirs,
                tail=dict(mean=round(sum(Rs)/len(Rs),4) if Rs else 0,
                          median=round(statistics.median(Rs),4) if Rs else 0,
                          mx=round(max(Rs),3) if Rs else 0, mn=round(min(Rs),3) if Rs else 0,
                          std=round(statistics.pstdev(Rs),3) if Rs else 0))

out={"families":[], "ledger_rows":0}
ledger=[]

# ---- VALIDATED: FVG-retest continuation on H1 ----
fv_crypto_010, ps = idb.build_fvg('crypto', idb.CRYPTO, 'H1', ac_thr=0.10, tgt_R=2.0)
out["families"].append(scorecard("VALID_crypto_H1_FVG_ac0.10_t2", fv_crypto_010, ps, "VALIDATED_breadth"))
for r in fv_crypto_010: ledger.append({**{k:(str(v) if k=='t' else v) for k,v in r.items()}, "sleeve":"crypto_intraday_fvg", "tf":"H1", "conf":0.40})

fv_crypto_015, ps = idb.build_fvg('crypto', idb.CRYPTO, 'H1', ac_thr=0.15, tgt_R=2.0)
out["families"].append(scorecard("VALID_crypto_H1_FVG_ac0.15_t2", fv_crypto_015, ps, "VALIDATED_breadth_hi"))

fv_metals_none, ps = idb.build_fvg('metals', idb.METALS, 'H1', ac_thr=None, tgt_R=2.0)
out["families"].append(scorecard("VALID_metals_H1_FVG_acNone_t2", fv_metals_none, ps, "VALIDATED_breadth"))
for r in fv_metals_none: ledger.append({**{k:(str(v) if k=='t' else v) for k,v in r.items()}, "sleeve":"metals_intraday_fvg", "tf":"H1", "conf":0.30})

fv_metals_010, ps = idb.build_fvg('metals', idb.METALS, 'H1', ac_thr=0.10, tgt_R=2.0)
out["families"].append(scorecard("VALID_metals_H1_FVG_ac0.10_t2", fv_metals_010, ps, "VALIDATED_breadth_hi"))

# ---- LEARNING: raw breakout intraday (falsified as quality) ----
bk_crypto_h1, ps = idb.build('crypto', idb.CRYPTO, 'H1', lb=20, ac_thr=0.20, sd_mult=2.0, tgt_R=4.0, maxbars=320)
out["families"].append(scorecard("LEARN_crypto_H1_breakout_ac0.20_t4", bk_crypto_h1, ps, "LEARNING_fragile"))
bk_crypto_m15, ps = idb.build('crypto', idb.CRYPTO, 'M15', lb=20, ac_thr=0.15, sd_mult=2.0, tgt_R=4.0, maxbars=1280)
out["families"].append(scorecard("LEARN_crypto_M15_breakout_ac0.15_t4", bk_crypto_m15, ps, "LEARNING_falsified"))

# ---- LEARNING: energy intraday (falsified both ways) ----
bk_energy_h1, ps = idb.build('energy', idb.ENERGY, 'H1', lb=20, ac_thr=0.15, sd_mult=2.0, tgt_R=4.0, maxbars=320)
out["families"].append(scorecard("LEARN_energy_H1_breakout_ac0.15_t4", bk_energy_h1, ps, "LEARNING_train_only"))
bk_energy_m15, ps = idb.build('energy', idb.ENERGY, 'M15', lb=40, ac_thr=0.15, sd_mult=2.0, tgt_R=4.0, maxbars=1280)
out["families"].append(scorecard("LEARN_energy_M15_breakout_ac0.15_t4", bk_energy_m15, ps, "LEARNING_fwd_only"))

# ---- combined VALIDATED intraday frequency lift ----
val_cryp = idb.per_yr(len(fv_crypto_010))
val_met  = idb.per_yr(len(fv_metals_none))
out["combined_validated"] = dict(
    crypto_intraday_fvg_trades_yr=val_cryp,
    metals_intraday_fvg_trades_yr=val_met,
    total_new_trades_yr=round(val_cryp+val_met,1),
    note="ADDITIVE: these are NEW intraday entries (H1 FVG-retest), not a re-timing of H4 signals (=TW cascade).")

(HERE/'IDB_INTRADAY_BREADTH_RESULT.json').write_text(json.dumps(out, indent=1))
(HERE/'IDB_INTRADAY_TRADE_LEDGER.jsonl').write_text('\n'.join(json.dumps(r) for r in ledger))
out["ledger_rows"]=len(ledger)

# console summary
print("=== INTRADAY BREADTH — validated additions (TRAIN 2025H2 / FWD 2026H1) ===")
for f in out["families"]:
    tag="VALID" if f["kind"].startswith("VALID") else "learn"
    print(f"[{tag}] {f['name']:38} TRAIN {f['train']['ev']:+.3f}(n{f['train']['n']}) FWD {f['fwd']['ev']:+.3f}(n{f['fwd']['n']}) "
          f"win{f['fwd']['win']:.0f}% {f['trades_yr']}/yr both{f['both_halves_carriers']}/{f['n_carriers']}")
print(f"\nCOMBINED NEW validated intraday frequency: +{out['combined_validated']['total_new_trades_yr']}/yr "
      f"(crypto {val_cryp} + metals {val_met})")
print(f"wrote IDB_INTRADAY_BREADTH_RESULT.json + IDB_INTRADAY_TRADE_LEDGER.jsonl ({len(ledger)} rows)")
