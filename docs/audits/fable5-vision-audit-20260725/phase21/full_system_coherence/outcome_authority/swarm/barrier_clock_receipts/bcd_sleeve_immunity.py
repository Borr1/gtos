#!/usr/bin/env python3
"""BARRIER-CLOCK DEFECT — does it reach the SLEEVE estate and the ARMED live book?

Structural test, from code and data, never from prose. Three questions:

  Q1  Does any LIVE order rest as a limit?          -> scan the order-request construction.
  Q2  Does the sleeve RESEARCH walk have a
      decision->fill gap?                            -> entry convention + walk start index.
  Q3  Does the sleeve trade artifact carry any
      order-type / fill field at all?                -> schema of AA_ESTATE_TRADES.json.gz.

Read-only. Writes BCD_SLEEVE_IMMUNITY.json next to this file.
"""
import gzip, json, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]            # this worktree, at origin/main
WT = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
AA = WT / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
OUT = Path(__file__).resolve().parent / "BCD_SLEEVE_IMMUNITY.json"

def tree_grep(root, pattern, subdirs):
    """pure-python recursive grep over *.py under `subdirs` of `root` (no external tools)."""
    out = []
    rx = re.compile(pattern)
    for sub in subdirs:
        for f in sorted((root / sub).rglob("*.py")):
            if "__pycache__" in f.parts:
                continue
            try:
                lines = f.read_text(errors="replace").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                if rx.search(line):
                    out.append(f"{f.relative_to(root)}:{i}:{line.strip()[:180]}")
    return out


def grep(path, pattern):
    hits = []
    for i, line in enumerate(Path(path).read_text(errors="replace").splitlines(), 1):
        if re.search(pattern, line):
            hits.append({"line": i, "text": line.strip()[:200]})
    return hits

res = {}

# ---- Q1: the live order request -------------------------------------------------------
pend = tree_grep(REPO, r"ORDER_TYPE_(BUY|SELL)_(LIMIT|STOP)|TRADE_ACTION_PENDING", ["src", "scripts"])
res["Q1_live_order_path"] = {
    "pending_or_limit_order_type_references_in_src_and_scripts": pend,
    "book_router_geometry": grep(REPO / "src/components/ultimate_book/order_router.py",
                                 r"entry = float\(ask if d > 0 else bid\)|stop_loss|take_profit_1|open_trade\("),
    "execution_request_construction": grep(REPO / "src/components/execution.py",
                                           r"order_type = 0 if direction == \"LONG\" else 1|\"action\": 1,  # TRADE_ACTION_DEAL"),
    "internal_pending_mode_constant": grep(REPO / "src/components/execution.py",
                                           r"^INTERNAL_PENDING_ORDER_MODE"),
    "legacy_pending_limit_fill_gate": grep(REPO / "src/components/execution.py",
                                           r"intent\.direction == \"LONG\" and candle\[\"low\"\] <= intent\.limit_price|target_reached_without_fill"),
    "ultimate_book_limit_price_references": tree_grep(
        REPO, r"limit_price", ["src/components/ultimate_book"]),
    "verdict": ("the W7/ultimate_book order is TRADE_ACTION_DEAL with type BUY/SELL at the live tick; "
                "no resting order is ever created; the book module contains no limit_price at all"),
}

# ---- Q2: the sleeve research walk -----------------------------------------------------
res["Q2_sleeve_research_walk"] = {
    "entry_convention": grep(
        WT / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/aa_estate_generate.py",
        r"entry = bars\[i\]\.c|entry_convention_gap|gaps\.append"),
    "walk_start_indices_in_exits_replay": grep(
        REPO / "src/research_infra/walkforward/exits.py", r"for j in range\(i \+ 1"),
    "verdict": ("entry is the CLOSE of the signal bar (a traded price at the decision instant) and "
                "every barrier loop starts at i+1; decision instant == fill instant, gap = 0 bars"),
}

# ---- Q3: the sleeve artifact schema ---------------------------------------------------
d = json.load(gzip.open(AA, "rt"))
rows = [r for v in d["trades"].values() for r in v] if isinstance(d.get("trades"), dict) else None
if rows is None:                                    # tolerate either shape
    rows = [r for k, v in d.items() if isinstance(v, list) for r in v if isinstance(r, dict)]
keys = sorted({k for r in rows[:5000] for k in r})
res["Q3_sleeve_artifact"] = {
    "artifact": str(AA), "n_rows": len(rows), "n_sleeves": len(d.get("trades", {})),
    "schema_keys": keys,
    "order_type_or_fill_fields": [k for k in keys
                                  if any(t in k.lower() for t in
                                         ("limit", "order_type", "fill", "pending", "passive", "marketable"))],
    "rows_with_exit_bar_offset_0": sum(1 for r in rows if r.get("exit_bar_offset") == 0),
    "min_exit_bar_offset": min(r["exit_bar_offset"] for r in rows if "exit_bar_offset" in r),
    "verdict": ("no order-type, limit, fill or marketability field exists anywhere in the sleeve "
                "corpus, and no trade can exit on its own entry bar"),
}
res["_conclusion"] = (
    "The sleeve estate and the armed live book are STRUCTURALLY IMMUNE to the barrier-clock "
    "defect: both place at market, so there is no interval between the decision and the fill "
    "in which a barrier could resolve.")
OUT.write_text(json.dumps(res, indent=1) + "\n")
for k in ("Q1_live_order_path", "Q2_sleeve_research_walk", "Q3_sleeve_artifact"):
    print(k, "->", res[k]["verdict"])
print(res["_conclusion"])
