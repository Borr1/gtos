#!/usr/bin/env python3
"""Lane FE verification, part 2: recompute the frozen February transfer from the
RAW CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz pool. February is read as FIXED ATTRIBUTION
ONLY under owner_mandate_20260801 — no selection, no retuning, frozen cells only.
Also recomputes the gross-identity reconciliation and the union top-k tables."""
import gzip, json, datetime
from collections import defaultdict

FEB = '/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz'
SENS_EXCLUDE = {"GER40","UKOIL_cash","USOIL_cash"}

sol = json.load(open('/Users/borr/GTOSActive/worktrees/wave19-sol-conditions-20260801/research/operations/wave19_sol_repair_2026_08_01/conditions/FROZEN_JAN_SELECTIONS.json'))
rank_g = sol['rankings']['gross']   # verified == my raw-reconstructed ranking
rank_n = sol['rankings']['net']
frozen = sorted(set(rank_g) | set(rank_n))
assert len(frozen) == 26

def parse_cell(cid):
    axis, *parts = cid.split('|')
    lv = dict(p.split('=',1) for p in parts)
    return axis, lv

CELLS = [(cid,)+parse_cell(cid) for cid in frozen]

SYMBOL_CLASS = {}
for cls, syms in {
    "crypto": ["BTCUSD","ETHUSD"], "energy": ["UKOIL_cash","USOIL_cash"],
    "fx": ["AUDJPY","AUDUSD","CHFJPY","EURGBP","EURJPY","EURUSD","GBPJPY","GBPUSD","NZDUSD","USDCAD","USDCHF","USDJPY"],
    "index": ["GER40","JP225","NAS100","SPX500","UK100","US30_cash"], "metal": ["XAGUSD","XAUUSD"],
}.items():
    for s in syms: SYMBOL_CLASS[s] = cls

def row_matches(axis, lv, row, symcls):
    if axis == "family_direction_session":
        return row["origin_family"]==lv["family"] and row["direction"]==lv["direction"] and row["session_bucket"]==lv["session"]
    if axis == "family_hour":
        return row["origin_family"]==lv["family"] and row["utc_hour_bucket"]==lv["utc_hour"]
    if axis == "family": return row["origin_family"]==lv["family"]
    if axis == "session": return row["session_bucket"]==lv["session"]
    if axis == "utc_hour": return row["utc_hour_bucket"]==lv["utc_hour"]
    if axis == "symbol_class": return symcls==lv["symbol_class"]
    if axis == "kill_zone": return row["kill_zone"]==lv["kill_zone"]
    if axis == "route_session": return row["route_session"]==lv["route_session"]
    if axis == "direction": return row["direction"]==lv["direction"]
    raise ValueError(axis)

# per-cell accumulators: cid -> {"primary":[n,g,net,cost,days], "sens":[...]}
acc = {cid: {"primary":[0,0.0,0.0,0.0,set()], "sens":[0,0.0,0.0,0.0,set()]} for cid in frozen}
# union accumulators keyed (basis,k): identity-deduped
unions = {}
for basis, rank in (("gross",rank_g),("net",rank_n)):
    for k in (5,10,20):
        unions[(basis,k)] = {"cells":[ (cid,)+parse_cell(cid) for cid in rank[:k] ],
                             "primary":[0,0.0,0.0,0.0], "sens":[0,0.0,0.0,0.0]}

n_rows=0; identities=set(); dup=0
gid_gt_1e9=0; gid_gt_5e9=0; gid_max=0.0; gid_has_field=0
feb_dates=set()
for_march_guard = 0

with gzip.open(FEB,'rt') as f:
    for line in f:
        row=json.loads(line)
        n_rows+=1
        ident="|".join((row["candidate_id"],row["decision_time_utc"],row["symbol"],row["direction"]))
        if ident in identities: dup+=1
        identities.add(ident)
        dt=datetime.datetime.fromisoformat(row["decision_time_utc"])
        day=dt.date().isoformat()
        feb_dates.add(day)
        if not day.startswith("2026-02"): for_march_guard+=1
        net=float(row["opportunity_net_proxy_r"]); cost=float(row["cost_r"]); gross=net+cost
        og=row.get("opportunity_gross_r")
        if og is not None:
            gid_has_field+=1
            dv=abs(float(og)-gross)
            if dv>1e-9: gid_gt_1e9+=1
            if dv>5e-9: gid_gt_5e9+=1
            if dv>gid_max: gid_max=dv
        symcls=SYMBOL_CLASS.get(row["symbol"])
        in_sens = row["symbol"] not in SENS_EXCLUDE
        for cid, axis, lv in CELLS:
            if row_matches(axis,lv,row,symcls):
                a=acc[cid]["primary"]; a[0]+=1; a[1]+=gross; a[2]+=net; a[3]+=cost; a[4].add(day)
                if in_sens:
                    a=acc[cid]["sens"]; a[0]+=1; a[1]+=gross; a[2]+=net; a[3]+=cost; a[4].add(day)
        for (basis,k),u in unions.items():
            hit=any(row_matches(axis,lv,row,symcls) for _,axis,lv in u["cells"])
            if hit:
                u["primary"][0]+=1; u["primary"][1]+=gross; u["primary"][2]+=net; u["primary"][3]+=cost
                if in_sens:
                    u["sens"][0]+=1; u["sens"][1]+=gross; u["sens"][2]+=net; u["sens"][3]+=cost

print(f"feb rows={n_rows} unique_identities={len(identities)} dup={dup} non-feb-dated rows={for_march_guard}")
print(f"feb distinct dates={len(feb_dates)} range {min(feb_dates)}..{max(feb_dates)}")
print(f"gross-identity: rows with |opportunity_gross_r-(net+cost)|>1e-9: {gid_gt_1e9}; >5e-9: {gid_gt_5e9}; max={gid_max:.11e}; rows with field={gid_has_field}")
print()
gp=[]; npos=[]
percell={}
for cid in frozen:
    a=acc[cid]["primary"]; s=acc[cid]["sens"]
    gm=a[1]/a[0] if a[0] else None; nm=a[2]/a[0] if a[0] else None
    sgm=s[1]/s[0] if s[0] else None; snm=s[2]/s[0] if s[0] else None
    percell[cid]={"n":a[0],"gross_mean":gm,"net_mean":nm,"day_count":len(a[4]),
                  "sens_n":s[0],"sens_gross_mean":sgm,"sens_net_mean":snm}
    if gm is not None and gm>0: gp.append(cid)
    if nm is not None and nm>0: npos.append(cid)
print(f"MY Feb per-cell: gross-positive={len(gp)} net-positive={len(npos)}")
for cid in gp: print(f"   GROSS+ {cid}: n={percell[cid]['n']} gross={percell[cid]['gross_mean']:+.6f} net={percell[cid]['net_mean']:+.6f}")
print()
uout={}
for (basis,k),u in sorted(unions.items()):
    p=u["primary"]; s=u["sens"]
    uout[f"{basis}_top{k}"]={"n":p[0],"gross_mean":p[1]/p[0],"net_mean":p[2]/p[0],
                            "sens_n":s[0],"sens_net_mean":s[2]/s[0]}
    print(f"MY union {basis} top-{k}: n={p[0]:5d} gross={p[1]/p[0]:+.6f} net={p[2]/p[0]:+.6f} sens_net={s[2]/s[0]:+.6f}")

json.dump({"rows":n_rows,"unique_identities":len(identities),"dup":dup,
           "gross_identity":{"gt_1e9":gid_gt_1e9,"gt_5e9":gid_gt_5e9,"max":gid_max,"rows_with_field":gid_has_field},
           "per_cell":percell,"gross_positive":sorted(gp),"net_positive":sorted(npos),
           "unions":uout}, open("feb_recompute.json","w"), indent=1)
print("WROTE feb_recompute.json")
