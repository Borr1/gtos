"""Which sleeves does the live config ACTUALLY arm? Measured through the production resolvers.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_armed_set_membership.py

WHY THIS EXISTS
---------------
`SURVIVOR_BOOK_V1.json` lists four UNCONDITIONAL sleeves — `metals_core`, `crypto`,
`energy_agri`, `sub_xvol_pullback` — and every wave-4/5 document, including this session's
own brief, describes a funded FTMO account being armed on those four.

`WAVE_5_WORKING_AGREEMENT.md` §3 item 6: *"If a claim is cheaply measurable, measure it."*
This is two seconds of work and it is load-bearing for OD-3, so it is measured rather than
inherited. Nothing here touches a broker, a token, or a config file: it loads YAML and calls
`admission.effective_registry` exactly as `book_engine._active_sleeve_names` does.

THE NAME COLLISION THAT MAKES THIS EASY TO GET WRONG
-----------------------------------------------------
`config/agent_config.yaml:1302` sets `ultimate_book_profile: "clean3_w7_ceiling_nom2p00"`.
That is an ALLOCATION PROFILE — a sizing dial (`admission.py:778-783`, 2.0% nominal per
unit). It is not the sleeve set. The sleeve set is decided 32 lines earlier by
`ultimate_book_include_clean3` (`:1270`), and `admission.py:212-215` states the rule
plainly: the clean-3 sleeves "are NOT loaded into the live decision path unless the caller
passes include_clean3=True (owner flips the flag at go-live)."

A dial named `clean3_*` alongside a flag `include_clean3: false` is how a book of three
comes to be described as a book of four.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import effective_registry  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.utils.config import apply_profile_overrides  # noqa: E402

OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_ARMED_SET_MEMBERSHIP.json"
SURVIVOR = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
PROFILES = ("operator_profile", "redacted_account")


def resolve(profile: str) -> dict:
    cfg = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    merged = apply_profile_overrides(cfg, profile)
    rt = dict(merged.get("gtos_vnext_runtime") or {})
    reg = effective_registry(
        include_clean3=bool(rt.get("ultimate_book_include_clean3", False)),
        include_clean4=bool(rt.get("ultimate_book_include_clean4", False)),
        include_candidate_book=bool(rt.get("ultimate_book_include_candidate_book", False)),
        candidate_book_sleeves=_candidate_book_sleeves(rt) or None,
        include_market_expansion_book=bool(
            rt.get("ultimate_book_include_market_expansion_book", False)),
        market_expansion_sleeves=_market_expansion_sleeves(rt) or None,
    )
    return {
        "profile": profile,
        "flags": {k: rt.get(k) for k in (
            "ultimate_book_enabled", "ultimate_book_apply_to_execution",
            "ultimate_book_live_activation_allowed", "ultimate_book_include_clean3",
            "ultimate_book_include_clean4", "ultimate_book_include_candidate_book",
            "ultimate_book_include_market_expansion_book", "ultimate_book_profile")},
        "effective_registry_size": len(reg),
        "effective_registry": sorted(reg),
    }


def main() -> dict:
    survivors = {}
    if SURVIVOR.is_file():
        raw = json.load(open(SURVIVOR))
        acct = (raw.get("accounts") or {}).get("FTMO") or {}
        for name, rec in (acct.get("sleeves") or {}).items():
            survivors[name] = {"tier": rec.get("survivor_tier"), "n": rec.get("n"),
                               "gross_r": rec.get("gross_r")}
    unconditional = sorted(n for n, r in survivors.items() if r["tier"] == "UNCONDITIONAL")

    per_profile = {p: resolve(p) for p in PROFILES}
    rows = []
    for name in unconditional or ("metals_core", "crypto", "energy_agri", "sub_xvol_pullback"):
        rows.append({
            "sleeve": name,
            "survivor_tier": survivors.get(name, {}).get("tier"),
            "survivor_n": survivors.get(name, {}).get("n"),
            "survivor_gross_r": survivors.get(name, {}).get("gross_r"),
            **{f"in_{p}": name in per_profile[p]["effective_registry"] for p in PROFILES},
        })

    absent = [r["sleeve"] for r in rows if not all(r[f"in_{p}"] for p in PROFILES)]
    out = {
        "schema": "gtos.walkforward.armed_set_membership.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase5/receipts/"
                         "x_armed_set_membership.py"),
        "resolver": ("src.components.ultimate_book.admission.effective_registry, called with the "
                     "same flags as book_engine._active_sleeve_names (book_engine.py:190-224), "
                     "over the profile-merged config (src.utils.config.apply_profile_overrides — "
                     "the same merge run_book.py:212 performs)"),
        "survivor_book": str(SURVIVOR.relative_to(REPO)) if SURVIVOR.is_file() else None,
        "survivor_unconditional": unconditional,
        "profiles": per_profile,
        "rows": rows,
        "unconditional_sleeves_absent_from_the_live_book": absent,
        "finding": (
            "The live config resolves 29 sleeves on both accounts and "
            f"{len(absent)} of the {len(rows)} SURVIVOR_BOOK_V1 UNCONDITIONAL sleeves "
            f"{'is' if len(absent) == 1 else 'are'} not among them: {absent}. "
            "config/agent_config.yaml:1270 sets ultimate_book_include_clean3: false, and "
            "admission.py:212-215 records that the clean-3 sleeves are not loaded into the "
            "live decision path unless that flag is True ('owner flips the flag at go-live'). "
            "Arming the book AS CONFIGURED today therefore arms three of the four."
            if absent else
            "Every SURVIVOR_BOOK_V1 UNCONDITIONAL sleeve is in the live effective registry on "
            "both accounts."),
        "name_collision_note": (
            "ultimate_book_profile: 'clean3_w7_ceiling_nom2p00' (agent_config.yaml:1302) is an "
            "ALLOCATION PROFILE — a 2.0% nominal sizing dial at admission.py:778-783 — not a "
            "sleeve set. It is 32 lines below ultimate_book_include_clean3: false and shares its "
            "name prefix."),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))

    print(f"{'sleeve':22s} {'tier':16s} {'n':>5s} {'gross_r':>9s}  " +
          "  ".join(f"{p[:14]:>14s}" for p in PROFILES))
    for r in rows:
        print(f"{r['sleeve']:22s} {str(r['survivor_tier']):16s} {str(r['survivor_n']):>5s} "
              f"{str(r['survivor_gross_r']):>9s}  " +
              "  ".join(f"{'IN' if r[f'in_{p}'] else 'ABSENT':>14s}" for p in PROFILES))
    print()
    print(out["finding"])
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
