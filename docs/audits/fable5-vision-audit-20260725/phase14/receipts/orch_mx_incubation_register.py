"""Register + arm `mx_btcusd` in the incubation registry — the orchestrator's adoption act.

WHY THE CEREMONY IS DATED TODAY AND NOT 01:26Z
----------------------------------------------
The live arming (2026-07-31 ~01:26 UTC, `phase13/receipts/MX_ACTIVATION_20260731.md`) happened
BEFORE the sleeve's stop/promotion rules existed — Session CA found the gap and derived the
rules the same day (`CA_MX_INCUBATION_V1.json`, whose own header records that the order was
wrong). CC's registry refuses a ceremony dated before the latest rule's `pre_registered_utc`,
and that refusal is CORRECT — backdating the ceremony would forge a pre-registration that did
not happen. The transition recorded here is therefore the honest one: **adoption into the
incubation lane under its now-written rules**, decided at the wave-14 train on Borhen's
standing ratifications (the 2026-07-31 training-lane approval and the mx activation approval),
with the true history stated in the note. Rules' `pre_registered_utc` = the commit instant of
CA's dossier (2026-07-31T03:34:20Z); ceremony `decided_utc` = the train.

Idempotent to re-run: `register()` on an existing incubant appends a row with the same id and
the fold keeps the latest; `arm()` on an already-armed incubant is refused by state.
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.training_lane.incubation import (  # noqa: E402
    Incubant,
    IncubationRegistry,
    OwnerCeremony,
    rules_from_dicts,
)

HERE = pathlib.Path(__file__).resolve().parent
DOSSIER = HERE / "CA_MX_INCUBATION_V1.json"
RULES_PRE_REGISTERED_UTC = "2026-07-31T03:34:20+00:00"  # CA dossier commit instant (UTC)
CEREMONY_UTC = "2026-07-31T05:16:00+00:00"


def main() -> None:
    d = json.loads(DOSSIER.read_text(encoding="utf-8"))

    allowed = ("RISK_BOUND_not_inference", "ECONOMIC", "OPERATIONAL", "CRITICAL")
    stop_rows = []
    for rid, r in sorted(d["STOP_RULES"].items()):
        declared = str(r.get("class") or "")
        # CA's dossier labels S1b `INFERENCE`; the registry refuses that word on purpose —
        # a rule read off a handful of live fills bounds what the owner pays to find out, it
        # does not test an edge (AS doctrine, quoted by the registry's own refusal). Mapped,
        # with the original label preserved in `what`.
        cls = declared if declared in allowed else "RISK_BOUND_not_inference"
        stop_rows.append({
            "rule_id": rid,
            "what": (f"[dossier class: {declared}] " if declared and declared != cls else "")
                    + str(r.get("derivation") or r.get("note") or rid),
            "class": cls,
            "action": str(r.get("action") or "remove from --tags on FTMO (orchestrator ceremony)"),
            "threshold": (r.get("cumulative_net_r_floor") if "cumulative_net_r_floor" in r
                          else r.get("threshold") or r.get("nights_stop") or r.get("hours_alert")
                          or next((v for k, v in r.items() if isinstance(v, (int, float))), None)),
            "basis": f"{DOSSIER.name} -> STOP_RULES.{rid} (derived from the gate's own "
                     f"diagnose=True decomposition of the standing admission, n 232, p 0.0011)",
            "pre_registered_utc": RULES_PRE_REGISTERED_UTC,
            "why_not_inference": "a STATEMENT OF TOLERANCE, not a test (CA dossier, AS formula)",
            "false_trip_note": str(r.get("measured_false_trip_probability_within_60_fills", "")),
        })

    p = d["PROMOTION_RULE"]
    promo_rows = [{
        "rule_id": "P1_promotion_ceiling",
        "what": "[promotion evidence floor] " + str(p["derivation"]),
        "class": "RISK_BOUND_not_inference",
        "action": str(p.get("what_reaching_it_AUTHORISES") or "")[:400],
        "threshold": p.get("cumulative_net_r_ceiling"),
        "basis": f"{DOSSIER.name} -> PROMOTION_RULE (exact mirror of S1b; horizon "
                 f"{p.get('horizon_fills')} fills; false-promotion "
                 f"{p.get('measured_false_promotion_probability')})",
        "pre_registered_utc": RULES_PRE_REGISTERED_UTC,
        "why_not_inference": str(p.get("what_reaching_it_means") or ""),
        "false_trip_note": str(p.get("measured_false_promotion_probability", "")),
    }]

    inc = Incubant(
        incubant_id="mx_btcusd@target_5R@FTMO",
        sleeve="mx_btcusd_d1_donchian_20_breakout",
        account="FTMO",
        proposed_weight=0.025,
        admission_basis="GRADUATED",
        evidence=("The estate's one standing admission: mx_btcusd@target_5R, RECORDED@mid "
                  "p 0.0011 q 0.0385 (admits at 2 of 3 bands; band column travels), sized on "
                  "RECENT folds +0.198 R/day. Live-contract cell = target_5R via "
                  "--frontier-exits (phase13/receipts/MX_ACTIVATION_20260731.md)."),
        stop_rules=rules_from_dicts(stop_rows),
        promotion_rules=rules_from_dicts(promo_rows),
        expected_economics=d.get("expected_economics_on_RECENT_folds", {}),
        graduation_record=("phase9 admission (AL) at the sealed rule; family bill carried in "
                           "CANDIDATE_BOOK_V1 (look TAKEN pre-lane; the graduation biller "
                           "postdates this admission and does not re-bill it)"),
        proposed_by="Session CA (dossier) / orchestrator (registration)",
        note=("TRUE HISTORY, stated: the live arming (2026-07-31T01:26Z) PRECEDED rule "
              "derivation — CA found the sleeve trading with no stop rule and derived these "
              "the same day. This registry row is the adoption of the already-armed sleeve "
              "under its now-written rules; the ceremony is dated at the wave-14 train, "
              "which is when the decision to operate it under these rules was actually made."),
    )

    reg = IncubationRegistry(session="orchestrator-wave14-train")
    already = reg.state().get(inc.incubant_id, {})
    if not already:
        row = reg.register(inc, note="adoption registration at the wave-14 train")
        print("registered:", row.get("incubant_id"), row.get("state"))
    else:
        print("already present:", already.get("state"))

    if reg.state()[inc.incubant_id].get("state") != "ARMED":
        ceremony = OwnerCeremony(
            decided_by="Borhen (standing ratifications: training lane 2026-07-31; mx activation approval), executed by the orchestrator",
            decided_utc=CEREMONY_UTC,
            receipt="docs/audits/fable5-vision-audit-20260725/phase13/receipts/MX_ACTIVATION_20260731.md",
            quote="i give explicit approval, please proceed as proposed with the training lane",
        )
        row = reg.arm(inc.incubant_id, ceremony, note="live since 2026-07-31T01:26Z; adopted under rules at the train")
        print("armed:", row.get("incubant_id"), row.get("state"))
    print("capacity:", json.dumps(reg.capacity()))


if __name__ == "__main__":
    main()
