"""Write per-trade ledgers for the deployable transfer winners (cascade fills + exits)."""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import TW_mtf_cascade_transfer as C

# Crypto: cascade + native target4 exit (deployable winner)
ce = C.crypto_sleeve()
rows, leaks, _ = C.run_cascade(ce, 'target4')
assert leaks == 0
(HERE/'TW_CRYPTO_CASCADE_LEDGER.jsonl').write_text(
    '\n'.join(json.dumps(dict(sym=r['sym'], year=r['year'], date=r['date'], vr=round(r['vr'],3),
                              src=r['src'], base_R=round(r['base_R'],4), casc_R=round(r['casc_R'],4)))
             for r in rows))

# Energy: cascade + STATE_D (Pareto winner) AND cascade+COMBO (max-EV) — write both R columns
ee = C.energy_sleeve()
rsd, l1, _ = C.run_cascade(ee, 'state_d')
rcm, l2, _ = C.run_cascade(ee, 'combo')
rlk, l3, _ = C.run_cascade(ee, 'lock')
assert l1 == 0 and l2 == 0 and l3 == 0
out = []
for a, b, c in zip(rsd, rcm, rlk):
    out.append(dict(sym=a['sym'], year=a['year'], date=a['date'], vr=round(a['vr'],3), src=a['src'],
                    base_state_d_h4=round(a['base_R'],4),
                    casc_state_d=round(a['casc_R'],4),
                    casc_combo=round(b['casc_R'],4),
                    casc_lock=round(c['casc_R'],4)))
(HERE/'TW_ENERGY_CASCADE_LEDGER.jsonl').write_text('\n'.join(json.dumps(r) for r in out))
print(f"wrote crypto ledger ({len(rows)} rows), energy ledger ({len(out)} rows). leaks=0")
