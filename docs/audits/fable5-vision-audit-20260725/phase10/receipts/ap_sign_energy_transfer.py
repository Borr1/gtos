"""Write `BROKER_TRUE_COSTS_V1_2.json` = V1_1 + the two signed energy commission blocks.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ap_sign_energy_transfer.py

WHY A NEW FILE RATHER THAN AN EDIT
----------------------------------
Same discipline OD-AI-4 option C asks for on the survivor book, for the same reason: every
published AF, AA, AH, AK and AL number is computed against V1_1's bytes, and a cost artifact
that changes under them turns "it reproduces" into "it used to". V1_1 is left alone; V1_2 is
a sibling, and the run that spends the transfer states which one it read.

WHAT IS ASSERTED, NOT ASSUMED
-----------------------------
The generator refuses to write unless **exactly** the named records differ from the base, at
**exactly** the `commission` key. That is the control that makes "only the pricing moved"
a measurement rather than an intention -- the same shape as OD-AI-4's `book_days` control.
It also refuses if a target record's commission is not currently `unknown`, so re-running it
against an artifact where the gap has since been closed by a real deal row cannot silently
overwrite a MEASURED number with a transfer.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.costs.model import PEER_TRANSFER, cost_r, load_broker_true_costs  # noqa: E402

HERE = Path(__file__).resolve().parent
SIGNED = HERE / "ENERGY_CLASS_PEER_TRANSFER_V1.json"
BASE = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
OUT_DIR = REPO / "research/operations/broker_truth_layer_2026_07_30"
OUT = OUT_DIR / "BROKER_TRUE_COSTS_V1_2.json"
ACCOUNT = "FTMO"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> dict:
    sig = json.loads(SIGNED.read_text())
    base = json.loads(BASE.read_text())
    out = copy.deepcopy(base)

    ins = out["accounts"][ACCOUNT]["instruments"]
    changed = []
    for sym, block in sorted(sig["instruments"].items()):
        rec = ins.get(sym)
        if rec is None:
            raise SystemExit(f"{sym} is not in {BASE.name} accounts.{ACCOUNT}.instruments")
        cur = rec["commission"].get("kind")
        if cur != "unknown":
            raise SystemExit(
                f"refusing to sign over {sym}: its commission kind is {cur!r}, not 'unknown'. "
                "A transfer may only fill a gap. If a deal row has since priced it, that "
                "measurement supersedes this signature and this script has nothing to do."
            )
        rec["commission"] = copy.deepcopy(block)
        changed.append(sym)

    # ---- the control: exactly these records, exactly this key -----------------------
    diffs = []
    for acct in sorted(set(base["accounts"]) | set(out["accounts"])):
        b = base["accounts"][acct]["instruments"]
        o = out["accounts"][acct]["instruments"]
        if set(b) != set(o):
            raise SystemExit(f"{acct}: instrument SET changed -- a transfer adds no symbol")
        for s in sorted(b):
            if b[s] == o[s]:
                continue
            keys = sorted(k for k in set(b[s]) | set(o[s]) if b[s].get(k) != o[s].get(k))
            diffs.append((acct, s, keys))
    expected = [(ACCOUNT, s, ["commission"]) for s in changed]
    if diffs != expected:
        raise SystemExit(f"unexpected diff surface:\n  got      {diffs}\n  expected {expected}")

    out["version"] = "1.2.0"
    out["derived_from"] = {
        "base": str(BASE.relative_to(REPO)),
        "base_sha256": _sha(BASE),
        "signature": str(SIGNED.relative_to(REPO)),
        "signature_sha256": _sha(SIGNED),
        "records_changed": sorted(changed),
        "keys_changed": ["accounts.FTMO.instruments.<symbol>.commission"],
        "records_unchanged_verified": True,
        "control": ("every other instrument record on both accounts compares equal to the "
                    "base dict, and the instrument sets are identical -- asserted by "
                    "ap_sign_energy_transfer.py before this file is written, not after."),
        "what_this_does_not_do": ("it does not re-derive anything. No deal row, tick file or "
                                 "symbol spec was read; the only new information is the "
                                 "signature."),
        "decision": "OD-AI-8",
        "authorized_by": sig["authorized_by"],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))

    # ---- and it must price -----------------------------------------------------------
    costs = load_broker_true_costs(OUT)
    report = {}
    for sym in changed:
        try:
            b = cost_r(sym, ACCOUNT, 24.0, sl_distance_price=0.10, entry_price=3.16,
                       side="LONG", spread_band="mid", costs=costs)
            report[sym] = {"priced": True, "commission_r": round(b.commission_r.value, 6),
                           "commission_coverage": str(b.commission_r.coverage),
                           "total_r": round(b.total_r.value, 6),
                           "total_coverage": str(b.total_r.coverage),
                           "kind": b.detail["commission"]["kind"]}
        except Exception as e:  # noqa: BLE001 - the report IS the finding
            report[sym] = {"priced": False, "refusal": f"{type(e).__name__}: {e}"}
        assert report[sym].get("commission_coverage") != "MEASURED"
    print(f"wrote {OUT.relative_to(REPO)}  sha256 {_sha(OUT)[:12]}")
    print(f"changed records: {changed}")
    for s, r in report.items():
        print(f"  {s:14s} {json.dumps(r)}")
    print("NOTE: a `priced: false` row here is a finding, not a failure -- HEATOIL.c has no "
          "spread source at all, so its signature is inert until bars exist.")
    return {"out": str(OUT), "report": report}


if __name__ == "__main__":
    main()
