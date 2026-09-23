#!/usr/bin/env python3
"""Lane FE verification: independent recompute of the January condition scan
from the RAW CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz pool, implementing
CONDITIONS_PROTOCOL.json from scratch (not reading Sol's CELL_MAP_JAN).
Streams line-by-line; peak memory well under 1.5 GB."""
import gzip, json, hashlib, datetime
from collections import defaultdict

JAN = '/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz'

TRAIN_DATES = {"2026-01-02","2026-01-05","2026-01-06","2026-01-07","2026-01-08","2026-01-09",
               "2026-01-12","2026-01-13","2026-01-14","2026-01-15","2026-01-16","2026-01-19","2026-01-20"}
HOLDOUT_DATES = {"2026-01-21","2026-01-22","2026-01-23","2026-01-26","2026-01-27","2026-01-28",
                 "2026-01-29","2026-01-30"}

SYMBOL_CLASS = {}
for cls, syms in {
    "crypto": ["BTCUSD","ETHUSD"],
    "energy": ["UKOIL_cash","USOIL_cash"],
    "fx": ["AUDJPY","AUDUSD","CHFJPY","EURGBP","EURJPY","EURUSD","GBPJPY","GBPUSD","NZDUSD","USDCAD","USDCHF","USDJPY"],
    "index": ["GER40","JP225","NAS100","SPX500","UK100","US30_cash"],
    "metal": ["XAGUSD","XAUUSD"],
}.items():
    for s in syms: SYMBOL_CLASS[s] = cls

DOW = {0:"MON",1:"TUE",2:"WED",3:"THU",4:"FRI",5:"SAT",6:"SUN"}
AXIS_PRECEDENCE = ["family_direction_session","family_hour","family","direction","session",
                   "utc_hour","symbol_class","kill_zone","route_session","day_of_week"]

# accumulators: cell_id -> split -> [n, gross_sum, net_sum, cost_sum, set(days)]
stats = defaultdict(lambda: {"TRAIN":[0,0.0,0.0,0.0,set()], "HOLDOUT":[0,0.0,0.0,0.0,set()]})
train_members = defaultdict(list)   # cell_id -> list of composite identity strings (TRAIN only)
identities = set()
n_rows = 0; dup = 0
dates_seen = defaultdict(int)
unmapped_symbols = defaultdict(int)
undeclared = defaultdict(int)
side_direction_disagree = 0

with gzip.open(JAN, 'rt') as f:
    for line in f:
        row = json.loads(line)
        n_rows += 1
        ident = (row["candidate_id"], row["decision_time_utc"], row["symbol"], row["direction"])
        ident_s = "|".join(ident)
        if ident_s in identities: dup += 1
        identities.add(ident_s)
        side = row.get("side")
        if side is not None and str(side).upper() != str(row["direction"]).upper():
            side_direction_disagree += 1
        dt = datetime.datetime.fromisoformat(row["decision_time_utc"])
        day = dt.date().isoformat()
        dates_seen[day] += 1
        if day in TRAIN_DATES: split = "TRAIN"
        elif day in HOLDOUT_DATES: split = "HOLDOUT"
        else: split = None; undeclared[("date",day)] += 1
        net = float(row["opportunity_net_proxy_r"])
        cost = float(row["cost_r"])
        gross = net + cost
        fam = row["origin_family"]; dirn = row["direction"]; sess = row["session_bucket"]
        hour = row["utc_hour_bucket"]; kz = row["kill_zone"]; rs = row["route_session"]
        sym = row["symbol"]
        symcls = SYMBOL_CLASS.get(sym)
        if symcls is None: unmapped_symbols[sym] += 1
        dow = DOW[dt.weekday()]
        cells = [
            f"family_direction_session|family={fam}|direction={dirn}|session={sess}",
            f"family|family={fam}",
            f"direction|direction={dirn}",
            f"session|session={sess}",
            f"utc_hour|utc_hour={hour}",
            f"symbol_class|symbol_class={symcls}",
            f"family_hour|family={fam}|utc_hour={hour}",
            f"kill_zone|kill_zone={kz}",
            f"route_session|route_session={rs}",
            f"day_of_week|day_of_week={dow}",
        ]
        if split is None: continue
        for cid in cells:
            s = stats[cid][split]
            s[0] += 1; s[1] += gross; s[2] += net; s[3] += cost; s[4].add(day)
            if split == "TRAIN":
                train_members[cid].append(ident_s)

print(f"rows={n_rows} unique_identities={len(identities)} duplicates={dup} side_dir_disagree={side_direction_disagree}")
train_rows = sum(v for d,v in dates_seen.items() if d in TRAIN_DATES)
holdout_rows = sum(v for d,v in dates_seen.items() if d in HOLDOUT_DATES)
print(f"train_rows={train_rows} holdout_rows={holdout_rows} distinct_dates={len(dates_seen)}")
print(f"dates sorted: {sorted(dates_seen)}")
print(f"unmapped_symbols={dict(unmapped_symbols)} undeclared={dict(undeclared)}")

# eligibility: TRAIN n >= 200
eligible = [cid for cid in stats if stats[cid]["TRAIN"][0] >= 200]
print(f"observed cells (any split, n>0): {len(stats)}")
print(f"eligible cells (TRAIN n>=200) before alias collapse: {len(eligible)}")

# alias collapse: identical sorted TRAIN membership
memb_hash = {}
for cid in eligible:
    h = hashlib.sha256("\n".join(sorted(train_members[cid])).encode()).hexdigest()
    memb_hash[cid] = h
groups = defaultdict(list)
for cid in eligible: groups[memb_hash[cid]].append(cid)
canonical = []
alias_map = {}
axis_rank = {a:i for i,a in enumerate(AXIS_PRECEDENCE)}
for h, members in groups.items():
    members_sorted = sorted(members, key=lambda c: (axis_rank[c.split("|")[0]], c))
    canon = members_sorted[0]
    canonical.append(canon)
    for m in members_sorted[1:]: alias_map[m] = canon
print(f"canonical inferential cells after alias collapse: {len(canonical)}")

def mean(cid, split, idx):
    s = stats[cid][split]
    return s[idx]/s[0] if s[0] else None

# counts among canonical cells
tg = [c for c in canonical if mean(c,"TRAIN",1) > 0]
tn = [c for c in canonical if mean(c,"TRAIN",2) > 0]
pg = [c for c in tg if stats[c]["HOLDOUT"][0] > 0 and mean(c,"HOLDOUT",1) > 0]
pn = [c for c in tn if stats[c]["HOLDOUT"][0] > 0 and mean(c,"HOLDOUT",2) > 0]
print(f"TRAIN gross-positive canonical cells: {len(tg)}")
for c in sorted(tg, key=lambda c: -mean(c,"TRAIN",1)):
    print(f"   {c}  TRAIN n={stats[c]['TRAIN'][0]} gross={mean(c,'TRAIN',1):+.6f} net={mean(c,'TRAIN',2):+.6f} "
          f"HOLDOUT n={stats[c]['HOLDOUT'][0]} gross={mean(c,'HOLDOUT',1) if stats[c]['HOLDOUT'][0] else float('nan'):+.6f}")
print(f"TRAIN net-positive canonical cells: {len(tn)} {tn}")
print(f"persistent gross-positive (TRAIN>0 & HOLDOUT>0): {len(pg)}")
for c in pg: print(f"   {c}")
print(f"persistent net-positive: {len(pn)} {pn}")

# frontier: TRAIN n>=200, HOLDOUT n>=100, gross>0 both
frontier = [c for c in canonical if stats[c]["TRAIN"][0]>=200 and stats[c]["HOLDOUT"][0]>=100
            and mean(c,"TRAIN",1)>0 and mean(c,"HOLDOUT",1)>0]
print(f"frontier cells (TRAIN>=200, HOLDOUT>=100, gross>0 both): {len(frontier)}")
for c in frontier:
    print(f"   {c}")
    print(f"     TRAIN  gross={mean(c,'TRAIN',1):+.6f} net={mean(c,'TRAIN',2):+.6f} n={stats[c]['TRAIN'][0]}")
    print(f"     HOLD   gross={mean(c,'HOLDOUT',1):+.6f} net={mean(c,'HOLDOUT',2):+.6f} n={stats[c]['HOLDOUT'][0]}")
    ntot = stats[c]['TRAIN'][0]+stats[c]['HOLDOUT'][0]
    ctot = stats[c]['TRAIN'][3]+stats[c]['HOLDOUT'][3]
    print(f"     JAN cost_mean={ctot/ntot:.6f} (TRAIN cost_mean={mean(c,'TRAIN',3):.6f})")

# top-3 by TRAIN gross among canonical
rank_gross = sorted(canonical, key=lambda c: (-mean(c,"TRAIN",1), c))
rank_net   = sorted(canonical, key=lambda c: (-mean(c,"TRAIN",2), c))
print("MY top-5 TRAIN gross ranking:")
for c in rank_gross[:5]:
    print(f"   {c}: gross={mean(c,'TRAIN',1):+.6f} net={mean(c,'TRAIN',2):+.6f} n={stats[c]['TRAIN'][0]}")
print("MY top-5 TRAIN net ranking:")
for c in rank_net[:5]:
    print(f"   {c}: gross={mean(c,'TRAIN',1):+.6f} net={mean(c,'TRAIN',2):+.6f} n={stats[c]['TRAIN'][0]}")

# persist full recompute for the receipt
out = {
  "rows": n_rows, "unique_identities": len(identities), "duplicates": dup,
  "train_rows": train_rows, "holdout_rows": holdout_rows,
  "observed_cells_nonzero": len(stats),
  "eligible_before_alias_collapse": len(eligible),
  "canonical_cells": len(canonical),
  "alias_groups_gt1": sum(1 for g in groups.values() if len(g)>1),
  "aliases_collapsed": len(eligible)-len(canonical),
  "train_gross_positive": sorted(tg), "train_net_positive": sorted(tn),
  "persistent_gross_positive": sorted(pg), "persistent_net_positive": sorted(pn),
  "frontier": {c: {"TRAIN": {"n":stats[c]['TRAIN'][0], "gross_mean":mean(c,'TRAIN',1), "net_mean":mean(c,'TRAIN',2), "cost_mean":mean(c,'TRAIN',3)},
                   "HOLDOUT":{"n":stats[c]['HOLDOUT'][0], "gross_mean":mean(c,'HOLDOUT',1), "net_mean":mean(c,'HOLDOUT',2), "cost_mean":mean(c,'HOLDOUT',3)}}
               for c in frontier},
  "rank_gross_top5": [{ "cell":c, "gross_mean":mean(c,'TRAIN',1), "net_mean":mean(c,'TRAIN',2), "n":stats[c]['TRAIN'][0]} for c in rank_gross[:5]],
  "rank_net_top5":   [{ "cell":c, "gross_mean":mean(c,'TRAIN',1), "net_mean":mean(c,'TRAIN',2), "n":stats[c]['TRAIN'][0]} for c in rank_net[:5]],
  "rank_gross_top20": [c for c in rank_gross[:20]],
  "rank_net_top20": [c for c in rank_net[:20]],
}
json.dump(out, open("jan_recompute.json","w"), indent=1)
print("WROTE jan_recompute.json")
