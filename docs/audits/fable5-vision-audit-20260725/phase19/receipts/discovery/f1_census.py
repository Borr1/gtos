import json, glob, os, gzip
FA2="/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725"
ROOT="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725"
BRK="/Users/borr/GTOSActive/worktrees/wave19-breaker-folds-20260801/docs/audits/fable5-vision-audit-20260725"
WIN={
 "2026-01": dict(receipt=f"{ROOT}/phase16/receipts/CJ_RECLOCKED_ARM_S0R0_V7.json",
                 lane=f"{ROOT}/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl",
                 pool=f"{ROOT}/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"),
 "2026-02": dict(lane=f"{ROOT}/phase18/receipts/CP_FEBRUARY_TRUE_UTC_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl",
                 pool=f"{ROOT}/phase18/receipts/pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"),
 "2026-03": dict(lane=f"{FA2}/phase19/receipts/march/arm_receipts/FA2_M_R0_LANE/LANE_TRADE_TABLE.jsonl",
                 receipt=f"{FA2}/phase19/receipts/march/arm_receipts/FA2_M_R0_RECEIPT.json"),
 "2026-04": dict(lane=f"{FA2}/phase19/receipts/CS_APRIL_S0R0_V2_LANE/LANE_TRADE_TABLE.jsonl",
                 pool=f"{FA2}/phase19/receipts/pools/CS_APRIL_S0R0_POOL_V1.jsonl.gz"),
 "2026-05": dict(lane=f"{FA2}/phase19/receipts/CS_MAY_S0R0_V1_LANE/LANE_TRADE_TABLE.jsonl",
                 pool=f"{FA2}/phase19/receipts/pools/CS_MAY_S0R0_POOL_V1.jsonl.gz"),
 "2025-10": dict(lane=f"{FA2}/phase19/receipts/pools/arm_receipts/LP_OCT_2025_S0R0_LANE/LANE_TRADE_TABLE.jsonl",
                 receipt=f"{FA2}/phase19/receipts/pools/arm_receipts/LP_OCT_2025_S0R0_RECEIPT.json",
                 pool=f"{FA2}/phase19/receipts/pools/LP_october_2025_S0R0_POOL_V1.jsonl.gz"),
 "2025-11": dict(lane=f"{FA2}/phase19/receipts/pools/arm_receipts/LP_NOV_2025_S0R0_LANE/LANE_TRADE_TABLE.jsonl",
                 receipt=f"{FA2}/phase19/receipts/pools/arm_receipts/LP_NOV_2025_S0R0_RECEIPT.json",
                 pool=f"{FA2}/phase19/receipts/pools/LP_november_2025_S0R0_POOL_V1.jsonl.gz"),
 "2025-12": dict(lane=f"{FA2}/phase19/receipts/pools/arm_receipts/LP_DEC_2025_S0R0_LANE/LANE_TRADE_TABLE.jsonl",
                 receipt=f"{FA2}/phase19/receipts/pools/arm_receipts/LP_DEC_2025_S0R0_RECEIPT.json",
                 pool=f"{FA2}/phase19/receipts/pools/LP_december_2025_S0R0_POOL_V1.jsonl.gz"),
}
out={}
for w,p in sorted(WIN.items()):
    rec={}
    lane=p.get("lane")
    if lane and os.path.isfile(lane):
        rows=[json.loads(l) for l in open(lane)]
        hdr=[r for r in rows if r.get("row_kind")=="header"]
        rec["lane_counts"]=hdr[0]["counts"] if hdr else None
        rec["lane_trades"]=sum(1 for r in rows if r.get("row_kind")=="trade")
        rec["lane_path"]=lane
    r=p.get("receipt")
    if r and os.path.isfile(r):
        d=json.load(open(r))
        rec["receipt_counts"]=d.get("receipt_counts")
        rec["window"]=d.get("lane_input_authority",{}).get("window")
    pl=p.get("pool")
    if pl and os.path.isfile(pl):
        n=0
        with gzip.open(pl,'rt') as fh:
            for _ in fh: n+=1
        rec["pool_rows"]=n; rec["pool_path"]=pl
    out[w]=rec
print(json.dumps(out,indent=1))
json.dump(out,open('/tmp/f1/census.json','w'),indent=1)
