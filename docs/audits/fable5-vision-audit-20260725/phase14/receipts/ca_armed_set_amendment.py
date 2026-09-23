#!/usr/bin/env python3
"""Session CA (B2145-B2147) — S6's book-composition statement, brought to the armed truth.

    python3 .../phase14/receipts/ca_armed_set_amendment.py --check     # report, change nothing
    python3 .../phase14/receipts/ca_armed_set_amendment.py --apply

WHAT IS WRONG, AND WHY IT IS THE MOST URGENT THING ON CA'S PAGE
----------------------------------------------------------------
`FIVE_SLEEVE_STOP_CONDITIONS_V1.json` was pre-registered on 2026-07-30, when both accounts
ran the same five sleeves. Two ceremonies later they do not:

    FTMO        crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert,
                mx_btcusd_d1_donchian_20_breakout   (the last on --frontier-exits, target_5R)
    redacted_account  crypto, energy_agri, sub_xvol_pullback, sub_mid_dn_revert

The artifact still declares ONE flat list containing `fx_jpy` — pulled 2026-07-30 ~14:57Z —
and not `mx_btcusd`. So `book_sleeve_telemetry.py`'s S6 check, whose own text is *"read this
first; nothing below matters if it is wrong"*, would fire **CRITICAL on both accounts** the
first time anyone runs it against a correct host read, for the wrong reason. A CRITICAL that
is always wrong is worse than no check: it trains its reader to skip it.

WHAT THIS AMENDS, AND WHAT IT REFUSES TO TOUCH
-----------------------------------------------
`armed_tags` and `S6.expected_tags` are statements of CURRENT FACT about what is armed — the
artifact's own header calls `armed_tags` "the armed set, in the order `--tags` carries it on
both hosts". They change at every ceremony by design. Every other field in `conditions` is a
pre-registered THRESHOLD, and a threshold amended after the fact is not pre-registered at
all. So this file:

  * rewrites `armed_tags` (the union across accounts) and `S6.expected_tags` (per account);
  * records the prior values verbatim under `amendments`, so nothing is lost;
  * PROVES it touched nothing else, by hashing every other condition block before and after
    and refusing to write if any hash moves.

The per-account form is new; `book_sleeve_telemetry.expected_tags_for` accepts both shapes and
reports UNCHECKED — never CLEAN — for an account a mapping omits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
COND = (REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
        / "FIVE_SLEEVE_STOP_CONDITIONS_V1.json")

MX = "mx_btcusd_d1_donchian_20_breakout"
CORE4 = ["crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert"]
NOW = {"FTMO": CORE4 + [MX], "redacted_account": list(CORE4)}
PROVENANCE = {
    "FTMO": ("phase13/receipts/MX_ACTIVATION_20260731.md (host d6c9c4b19, 2026-07-31 ~01:26Z) "
             "on top of phase8/receipts/FXJPY_PULL_20260730.md (host 7017c6745, ~14:57Z). "
             "mx_btcusd runs on --frontier-exits (target_5R); the frontier is FTMO-only."),
    "redacted_account": ("phase8/receipts/FN_ARMING_20260730.md + FIVE_SLEEVE_EXPANSION_20260730.md, "
                   "then the fx_jpy pull. Four sleeves, no frontier; the mx ceremony left this "
                   "account untouched."),
}


def _hash_others(doc: dict) -> dict:
    return {k: hashlib.sha256(
        json.dumps(v, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
        for k, v in doc["conditions"].items() if k != "S6_book_composition"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = json.loads(COND.read_text())
    before = _hash_others(doc)
    prior_armed = list(doc.get("armed_tags") or [])
    prior_expected = doc["conditions"]["S6_book_composition"]["expected_tags"]

    union = sorted(set(NOW["FTMO"]) | set(NOW["redacted_account"]))
    stale_now_armed = sorted(set(prior_armed) - set(union))
    missing_from_prior = sorted(set(union) - set(prior_armed))
    print(f"prior expected_tags: {prior_expected}")
    print(f"  armed today  FTMO       : {NOW['FTMO']}")
    print(f"  armed today  redacted_account : {NOW['redacted_account']}")
    print(f"  in the artifact but NOT armed anywhere: {stale_now_armed}")
    print(f"  armed but NOT in the artifact         : {missing_from_prior}")
    if not a.apply:
        print("\n--check only; nothing written. Re-run with --apply.")
        return 0

    doc["armed_tags"] = union
    doc["conditions"]["S6_book_composition"]["expected_tags"] = dict(NOW)
    doc["conditions"]["S6_book_composition"]["expected_tags_provenance"] = PROVENANCE
    doc["conditions"]["S6_book_composition"]["what"] = (
        "the workers' --tags do not equal the armed set FOR THAT ACCOUNT, on either account")
    doc["conditions"]["S6_book_composition"]["per_account_form"] = (
        "expected_tags is a mapping account -> tags because the two accounts no longer run "
        "the same book: FTMO carries mx_btcusd on --frontier-exits and redacted_account does not. "
        "book_sleeve_telemetry.expected_tags_for accepts a flat list too (every artifact "
        "before 2026-07-31) and reports UNCHECKED, never CLEAN, for an account a mapping "
        "omits.")
    doc.setdefault("amendments", []).append({
        "at": "2026-07-31", "by": "Session CA (wave 14), blocks B2145-B2147",
        "fields": ["armed_tags", "conditions.S6_book_composition.expected_tags"],
        "prior_armed_tags": prior_armed,
        "prior_expected_tags": prior_expected,
        "why": ("statements of CURRENT FACT about what is armed, stale in BOTH directions "
                "after two ceremonies: fx_jpy was pulled 2026-07-30 ~14:57Z and mx_btcusd was "
                "armed on FTMO 2026-07-31 ~01:26Z. Left as they were, S6 — the condition "
                "whose own text says 'read this first; nothing below matters if it is wrong' "
                "— fires CRITICAL on BOTH accounts against a correct host read."),
        "what_was_NOT_touched": ("every pre-registered THRESHOLD. Each non-S6 condition block "
                                 "is hashed before and after and this file refuses to write "
                                 "if any hash moves."),
        "threshold_hashes_unchanged": True,
    })
    after = _hash_others(doc)
    moved = sorted(k for k in before if before[k] != after.get(k))
    if moved or set(before) != set(after):
        raise SystemExit(f"REFUSING TO WRITE: condition blocks moved: {moved or 'set changed'}")
    COND.write_text(json.dumps(doc, indent=1, sort_keys=False, default=str) + "\n")
    print(f"\nwrote {COND.relative_to(REPO)}")
    print(f"  {len(before)} pre-registered condition blocks hashed before and after: UNCHANGED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
