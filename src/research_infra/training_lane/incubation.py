"""CC-4 — the incubation registry: ≤5 concurrent sleeves, ≤0.05-class weight, rules first.

`TRAINING_LANE_RATIFICATION.md` section 4, made machine-checked:

    at most 5 concurrent incubant sleeves
    each at <= 0.05-class confidence weight
    each carrying PRE-REGISTERED stop AND promotion rules, written before arming
    arming / pulling / promoting is an OWNER CEREMONY every time

WHY EACH OF THOSE IS ENFORCED AT A DIFFERENT MOMENT
----------------------------------------------------
They are not the same kind of constraint and pretending they are is how a registry becomes a
form nobody fills in honestly.

  weight and rules   are properties of ONE record, so they are enforced at `register()`. A
                     proposal that cannot state how it will be stopped is not a proposal.
  capacity (<= 5)    is a property of the SET, and "concurrent" means armed. Enforced at
                     `arm()`. Filing six dossiers is research; arming six is the thing the
                     ratification bounds. `capacity()` reports the headroom at any time so a
                     session filing a dossier knows what it is queueing behind.
  the ceremony       is a property of the TRANSITION. `arm()`, `pull()` and `promote()` each
                     refuse without an `OwnerCeremony` carrying who decided, when, and the
                     receipt path. The orchestrator executes; Borhen decides. A registry that
                     could arm itself would be the second line of defence this estate keeps
                     discovering it does not have.

THE STOP RULE IS THE PRICE, NOT A PREDICTION
---------------------------------------------
Session AS's five-sleeve stop conditions carry the honest framing and it is adopted here as a
required field: a stop rule is a `RISK_BOUND_not_inference`. Twelve fills cannot establish an
edge, and a rule that trips says the owner has paid what he pre-registered — it says nothing
about the sleeve. `PreRegisteredRule.class_` must be one of a closed vocabulary for exactly
that reason: a rule filed as `inference` is claiming a power it does not have.

WHAT AN INCUBANT IS NOT REQUIRED TO BE
---------------------------------------
Admitted. Section 4 frames incubation as sitting "between admission and full weight", but the
estate's own record has two intakes and only one is an admission: `mx_btcusd` graduated
(p 0.0011, two of three bands), while the five-sleeve expansion was armed on **explicit owner
risk acceptance, on the record**, and neither added sleeve passed an admission standard. CA's
revival candidates will be the same shape. So `admission_basis` is a closed two-value field —
`GRADUATED` (and then it must cite a graduation record) or `OWNER_RISK_ACCEPTED` (and then it
must cite the owner's decision). Anything else is refused. The distinction is recorded rather
than blurred, because a page that reads "incubating" over both is the page that lets a
risk-accepted sleeve be quoted later as an admitted one.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from .append_only import append_row, read_rows

__all__ = [
    "DEFAULT_INCUBATION_REGISTRY",
    "INCUBATION_SCHEMA",
    "MAX_CONCURRENT_INCUBANTS",
    "MAX_INCUBANT_WEIGHT",
    "ADMISSION_BASES",
    "RULE_CLASSES",
    "STATES",
    "Incubant",
    "IncubationRefusal",
    "IncubationRegistry",
    "OwnerCeremony",
    "PreRegisteredRule",
    "rules_from_dicts",
]

INCUBATION_SCHEMA = "gtos.training_lane.incubation_row.v1"

REPO = Path(__file__).resolve().parents[3]
DEFAULT_INCUBATION_REGISTRY = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
    / "TRAINING_LANE_INCUBATION_REGISTRY.jsonl"
)

#: Ratification section 4. Both are ceilings, not targets.
MAX_CONCURRENT_INCUBANTS = 5
MAX_INCUBANT_WEIGHT = 0.05
#: Float slack for a weight read out of YAML/JSON. 1e-9 admits 0.05 and refuses 0.0500001.
_WEIGHT_EPS = 1e-9

#: How an incubant got here. Two intakes, kept distinct — see the module docstring.
ADMISSION_BASES = ("GRADUATED", "OWNER_RISK_ACCEPTED")

#: What a pre-registered rule claims about itself. `inference` is absent on purpose: a stop or
#: promotion rule evaluated on a handful of live fills is a statement of tolerance, not a test.
RULE_CLASSES = ("RISK_BOUND_not_inference", "ECONOMIC", "OPERATIONAL", "CRITICAL")

STATES = ("PROPOSED", "ARMED", "PROMOTED", "STOPPED")
#: The only transitions the registry will record. Everything else is refused, including
#: PROPOSED -> PROMOTED (a sleeve cannot be promoted out of a lane it never entered).
_TRANSITIONS = {
    ("PROPOSED", "ARMED"),
    ("PROPOSED", "STOPPED"),
    ("ARMED", "PROMOTED"),
    ("ARMED", "STOPPED"),
}


class IncubationRefusal(RuntimeError):
    """A registration or a transition was refused. `reason` is the machine-readable code."""

    def __init__(self, reason: str, message: str, *, detail: Any = None) -> None:
        super().__init__(f"{reason}: {message}")
        self.reason = reason
        self.detail = detail


def _instant(value: Any, what: str) -> dt.datetime:
    """ISO-8601 -> an aware datetime. A naive timestamp is read as UTC.

    Timestamps in this module are compared as instants and never as strings, because ISO-8601
    offsets are not lexicographically ordered: `"2026-07-31T00:00:00Z"` sorts ABOVE
    `"2026-07-31T00:00:00+00:00"` (`'Z' > '+'`) while denoting the same moment.
    """
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise IncubationRefusal(
            "timestamp_unparseable",
            f"{what}: {value!r} is not an ISO-8601 timestamp, so 'pre-registered' cannot be "
            f"checked against it.",
            detail=value,
        ) from None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


@dataclass(frozen=True)
class PreRegisteredRule:
    """One stop or promotion rule, written BEFORE arming. The AS dossier shape, machine-checked.

    `basis` must name the artifact the threshold came from. A threshold with no basis is a
    number someone liked, and it is the field most likely to be left blank — so it is required
    rather than optional, and the refusal says why.
    """

    rule_id: str
    what: str
    class_: str
    action: str
    threshold: Any
    basis: str
    pre_registered_utc: str
    why_not_inference: str = ""
    false_trip_note: str = ""

    def __post_init__(self) -> None:
        missing = [k for k in ("rule_id", "what", "class_", "action", "basis",
                               "pre_registered_utc") if not getattr(self, k)]
        if self.threshold is None:
            missing.append("threshold")
        if missing:
            raise IncubationRefusal(
                "rule_incomplete",
                f"pre-registered rule {self.rule_id or '<unnamed>'} is missing {missing}. "
                f"`basis` must name the artifact the threshold came from — a threshold with no "
                f"basis is a number somebody liked, and it is the field a rushed dossier drops "
                f"first.",
                detail=missing,
            )
        if self.class_ not in RULE_CLASSES:
            raise IncubationRefusal(
                "rule_class_unknown",
                f"rule {self.rule_id!r} declares class {self.class_!r}; expected one of "
                f"{RULE_CLASSES}. Note that `inference` is deliberately absent: a rule "
                f"evaluated on a handful of live fills bounds what the owner pays to find out, "
                f"it does not test an edge (AS, FIVE_SLEEVE_STOP_CONDITIONS_V1.json).",
                detail=self.class_,
            )
        try:
            dt.datetime.fromisoformat(str(self.pre_registered_utc).replace("Z", "+00:00"))
        except ValueError:
            raise IncubationRefusal(
                "rule_timestamp_unparseable",
                f"rule {self.rule_id!r}: pre_registered_utc {self.pre_registered_utc!r} is not "
                f"an ISO timestamp. It is the field that makes 'pre-registered' checkable "
                f"against the arming time.",
                detail=self.pre_registered_utc,
            ) from None

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "what": self.what,
            "class": self.class_,
            "action": self.action,
            "threshold": self.threshold,
            "basis": self.basis,
            "pre_registered_utc": self.pre_registered_utc,
            "why_not_inference": self.why_not_inference,
            "false_trip_note": self.false_trip_note,
        }


@dataclass(frozen=True)
class OwnerCeremony:
    """Who decided, when, and where the receipt is. Required for every state transition."""

    decided_by: str
    decided_utc: str
    receipt: str
    quote: str = ""

    def __post_init__(self) -> None:
        missing = [k for k in ("decided_by", "decided_utc", "receipt") if not getattr(self, k)]
        if missing:
            raise IncubationRefusal(
                "ceremony_incomplete",
                f"owner ceremony is missing {missing}. Arming, pulling and promoting are "
                f"owner ceremonies every time — the orchestrator executes, Borhen decides "
                f"(ratification section 4). A transition with no receipt is a transition "
                f"nobody can audit.",
                detail=missing,
            )

    def as_dict(self) -> dict:
        return {
            "decided_by": self.decided_by,
            "decided_utc": self.decided_utc,
            "receipt": self.receipt,
            "quote": self.quote,
        }


@dataclass(frozen=True)
class Incubant:
    """One candidate sleeve in the incubation lane."""

    incubant_id: str
    sleeve: str
    account: str
    proposed_weight: float
    admission_basis: str
    evidence: str
    stop_rules: tuple[PreRegisteredRule, ...]
    promotion_rules: tuple[PreRegisteredRule, ...]
    expected_economics: dict = field(default_factory=dict)
    graduation_record: str = ""
    owner_risk_acceptance: str = ""
    proposed_by: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        missing = [k for k in ("incubant_id", "sleeve", "account", "evidence") if not getattr(self, k)]
        if missing:
            raise IncubationRefusal(
                "incubant_incomplete", f"incubant is missing {missing}", detail=missing
            )
        if not isinstance(self.proposed_weight, (int, float)) or self.proposed_weight <= 0:
            raise IncubationRefusal(
                "weight_invalid",
                f"{self.incubant_id}: proposed_weight {self.proposed_weight!r} must be a "
                f"positive number.",
                detail=self.proposed_weight,
            )
        if float(self.proposed_weight) > MAX_INCUBANT_WEIGHT + _WEIGHT_EPS:
            raise IncubationRefusal(
                "weight_above_incubation_ceiling",
                f"{self.incubant_id}: proposed_weight {self.proposed_weight} exceeds the "
                f"0.05-class ceiling ({MAX_INCUBANT_WEIGHT}) the ratification sets for every "
                f"incubant. For scale: the estate's one graduated admission, mx_btcusd, is "
                f"armed at registry confidence 0.025 — economically small by design, because "
                f"the forward record is the point.",
                detail=self.proposed_weight,
            )
        if self.admission_basis not in ADMISSION_BASES:
            raise IncubationRefusal(
                "admission_basis_unknown",
                f"{self.incubant_id}: admission_basis {self.admission_basis!r}; expected one of "
                f"{ADMISSION_BASES}. GRADUATED means it cleared the frozen sealed gate and must "
                f"cite its graduation record; OWNER_RISK_ACCEPTED means it did not and must "
                f"cite the owner's decision. Blurring the two is how a risk-accepted sleeve "
                f"gets quoted later as an admitted one.",
                detail=self.admission_basis,
            )
        if self.admission_basis == "GRADUATED" and not self.graduation_record:
            raise IncubationRefusal(
                "graduation_record_missing",
                f"{self.incubant_id}: admission_basis GRADUATED with no `graduation_record`. "
                f"Cite the record `training_lane.graduation.graduate()` emitted — that is the "
                f"artifact carrying the family bill this admission was corrected against.",
            )
        if self.admission_basis == "OWNER_RISK_ACCEPTED" and not self.owner_risk_acceptance:
            raise IncubationRefusal(
                "owner_risk_acceptance_missing",
                f"{self.incubant_id}: admission_basis OWNER_RISK_ACCEPTED with no "
                f"`owner_risk_acceptance`. Name the decision and its receipt — the five-sleeve "
                f"expansion is the precedent and it is on the record precisely because neither "
                f"added sleeve passed an admission standard.",
            )
        if not self.stop_rules:
            raise IncubationRefusal(
                "stop_rule_missing",
                f"{self.incubant_id}: no pre-registered STOP rule. The live stream is this "
                f"sleeve's test set, and a test set with no stopping rule written before the "
                f"first fill is a test set that gets read until it says something. Refused.",
            )
        if not self.promotion_rules:
            raise IncubationRefusal(
                "promotion_rule_missing",
                f"{self.incubant_id}: no pre-registered PROMOTION rule. Both directions must be "
                f"written before arming, not just the downside — an incubant with no way out of "
                f"the lane stays at 0.05 weight forever regardless of what it earns, and the "
                f"decision to promote then gets made on whatever the record happens to look "
                f"like on the day someone asks.",
            )
        ids = [r.rule_id for r in (*self.stop_rules, *self.promotion_rules)]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise IncubationRefusal(
                "duplicate_rule_id",
                f"{self.incubant_id}: repeated rule_id(s) {dupes}. Rule ids are how a trip is "
                f"reported; two rules sharing one make the report ambiguous.",
                detail=dupes,
            )

    def as_dict(self) -> dict:
        return {
            "incubant_id": self.incubant_id,
            "sleeve": self.sleeve,
            "account": self.account,
            "proposed_weight": float(self.proposed_weight),
            "admission_basis": self.admission_basis,
            "evidence": self.evidence,
            "graduation_record": self.graduation_record,
            "owner_risk_acceptance": self.owner_risk_acceptance,
            "expected_economics": self.expected_economics,
            "stop_rules": [r.as_dict() for r in self.stop_rules],
            "promotion_rules": [r.as_dict() for r in self.promotion_rules],
            "proposed_by": self.proposed_by,
            "note": self.note,
        }


class IncubationRegistry:
    """Append-only incubation lane. State is the fold of its rows, never a mutable field.

    Append-only because the interesting question a year from now is not "which sleeves are
    incubating" but "which were armed, on whose decision, and what stopped them" — and a
    registry that overwrites cannot answer it. `active()` folds the rows; `rows()` keeps the
    history.
    """

    def __init__(
        self,
        path: str | Path = DEFAULT_INCUBATION_REGISTRY,
        *,
        session: str = "",
        now_utc: str = "",
    ) -> None:
        self.path = Path(path)
        self.session = session
        self._now = now_utc

    def _timestamp(self) -> str:
        return self._now or dt.datetime.now(tz=dt.timezone.utc).isoformat()

    # -- reading ---------------------------------------------------------------------------
    def rows(self) -> list[dict]:
        return read_rows(self.path)

    def state(self) -> dict[str, dict]:
        """incubant_id -> its latest row. The fold."""
        out: dict[str, dict] = {}
        for r in self.rows():
            if "_unparseable" in r or not r.get("incubant_id"):
                continue
            out[str(r["incubant_id"])] = r
        return out

    def armed(self) -> list[dict]:
        return [r for r in self.state().values() if r.get("state") == "ARMED"]

    def capacity(self) -> dict:
        n = len(self.armed())
        return {
            "max_concurrent": MAX_CONCURRENT_INCUBANTS,
            "armed": n,
            "headroom": max(0, MAX_CONCURRENT_INCUBANTS - n),
            "armed_ids": sorted(r["incubant_id"] for r in self.armed()),
            "max_weight": MAX_INCUBANT_WEIGHT,
            "total_armed_weight": round(sum(float(r.get("proposed_weight") or 0.0)
                                            for r in self.armed()), 6),
        }

    # -- writing ---------------------------------------------------------------------------
    def register(self, incubant: Incubant, *, note: str = "") -> dict:
        """File a PROPOSED incubant. Refuses on weight, rules, and admission basis.

        Does NOT consume capacity — filing dossiers is research, arming is the thing the
        ratification bounds. The returned row carries the headroom so a session filing a
        proposal can see what it is queueing behind.
        """
        if incubant.incubant_id in self.state():
            raise IncubationRefusal(
                "already_registered",
                f"{incubant.incubant_id!r} is already in the registry with state "
                f"{self.state()[incubant.incubant_id].get('state')!r}. Use arm/pull/promote to "
                f"move it; re-registering would reset a history that is the point of the file.",
            )
        row = {
            "schema": INCUBATION_SCHEMA,
            "row_kind": "incubation_state",
            "ts": self._timestamp(),
            "session": self.session,
            "state": "PROPOSED",
            "transition": "register",
            "capacity_at_write": self.capacity(),
            "note": note,
            **incubant.as_dict(),
        }
        append_row(self.path, row)
        return row

    def _transition(self, incubant_id: str, to_state: str, ceremony: OwnerCeremony, *,
                    note: str = "", extra: dict | None = None) -> dict:
        cur = self.state().get(incubant_id)
        if cur is None:
            raise IncubationRefusal(
                "unknown_incubant",
                f"{incubant_id!r} is not registered. Register it (with its pre-registered stop "
                f"AND promotion rules) before any transition.",
            )
        frm = str(cur.get("state"))
        if (frm, to_state) not in _TRANSITIONS:
            raise IncubationRefusal(
                "illegal_transition",
                f"{incubant_id!r}: {frm} -> {to_state} is not a recorded transition; legal ones "
                f"are {sorted(_TRANSITIONS)}. In particular a sleeve cannot be PROMOTED out of "
                f"a lane it never entered.",
                detail=(frm, to_state),
            )
        if to_state == "ARMED":
            cap = self.capacity()
            if cap["headroom"] < 1:
                raise IncubationRefusal(
                    "incubation_capacity_full",
                    f"{cap['armed']} incubants are already armed and the ratified ceiling is "
                    f"{MAX_CONCURRENT_INCUBANTS} ({cap['armed_ids']}). Pull or promote one "
                    f"first — both are owner ceremonies.",
                    detail=cap,
                )
            rules = (cur.get("stop_rules") or []) + (cur.get("promotion_rules") or [])
            if not rules:
                raise IncubationRefusal(
                    "rules_missing_on_record",
                    f"{incubant_id!r} carries no rules at all. `register()` refuses that, so this "
                    f"row was hand-written into the registry. Re-register it through the API.",
                )
            # Compared as PARSED instants, never as strings. ISO-8601 offsets are not
            # lexicographically ordered — "…T00:00:00Z" sorts ABOVE "…T00:00:00+00:00" because
            # 'Z' > '+', so a string compare would let a rule written after the arming pass
            # whenever the two happened to use different (equally valid) offset spellings.
            armed_at = _instant(ceremony.decided_utc, f"{incubant_id} arming ceremony")
            # Compared against the LATEST rule, not the earliest. "Pre-registered" is a claim
            # about EVERY rule, so the binding one is the last one written: an earliest-rule
            # check passes an incubant whose stop rule predates the ceremony while its promotion
            # rule was added afterwards — which is precisely the rule you would add once you
            # could see the fills. My first version made that mistake and
            # `test_pre_registration_compares_instants_not_strings` caught it.
            #
            # `key=` and not a sort of (instant, dict) tuples: two rules pre-registered at the
            # same instant would make Python fall through to comparing the dicts and raise
            # TypeError.
            dated = sorted(
                ((_instant(r.get("pre_registered_utc"),
                           f"{incubant_id} rule {r.get('rule_id')!r}"), r) for r in rules),
                key=lambda pair: pair[0],
            )
            latest_at, latest_rule = dated[-1]
            if armed_at < latest_at:
                raise IncubationRefusal(
                    "rules_not_pre_registered",
                    f"{incubant_id!r}: the arming ceremony is dated {ceremony.decided_utc}, "
                    f"BEFORE rule {latest_rule.get('rule_id')!r}'s pre_registered_utc "
                    f"{latest_rule.get('pre_registered_utc')}. 'Pre-registered' means EVERY rule "
                    f"was written before arming; a rule written afterwards is a rule chosen once "
                    f"the fills were visible.",
                    detail={"armed_at": ceremony.decided_utc,
                            "latest_rule": latest_rule.get("rule_id"),
                            "latest_rule_utc": latest_rule.get("pre_registered_utc")},
                )
        row = dict(cur)
        row.update({
            "ts": self._timestamp(),
            "session": self.session,
            "state": to_state,
            "transition": f"{frm}->{to_state}",
            "owner_ceremony": ceremony.as_dict(),
            "capacity_at_write": self.capacity(),
            "note": note,
        })
        row.pop("_unparseable", None)
        if extra:
            row.update(extra)
        append_row(self.path, row)
        return row

    def arm(self, incubant_id: str, ceremony: OwnerCeremony, *, note: str = "") -> dict:
        """PROPOSED -> ARMED. Refuses over capacity and refuses rules written after the fact.

        This records a decision the owner has already made; it places no order and touches no
        host. The actual arming is the orchestrator's ceremony on the VPS.
        """
        return self._transition(incubant_id, "ARMED", ceremony, note=note)

    def pull(self, incubant_id: str, ceremony: OwnerCeremony, *, tripped_rule: str = "",
             note: str = "") -> dict:
        """-> STOPPED. `tripped_rule` names the pre-registered rule that fired, if one did."""
        return self._transition(incubant_id, "STOPPED", ceremony, note=note,
                                extra={"tripped_rule": tripped_rule})

    def amend_rules(self, incubant_id: str, ceremony: OwnerCeremony, *,
                    live_record: dict,
                    stop_rules: Sequence[PreRegisteredRule] | None = None,
                    promotion_rules: Sequence[PreRegisteredRule] | None = None,
                    supersedes: Sequence[str] = (),
                    reason: str = "", note: str = "") -> dict:
        """Replace an incubant's pre-registered rules WITHOUT a state transition.

        THE HAZARD THIS EXISTS TO CONTAIN, STATED BEFORE THE FEATURE
        ------------------------------------------------------------
        Everything else in this module is built so a rule cannot be written after the fills are
        visible: `_transition` refuses an arming whose LATEST rule postdates the ceremony, and
        that check is the reason `pre_registered_utc` is required. An amendment path is a hole
        in exactly that wall — it lets a session rewrite a promotion threshold once it can see
        how the sleeve is doing, which is the failure pre-registration exists to prevent.

        So the path is not closed (a rule that is measurably MIS-DERIVED has to be fixable, and
        OD-HISTORICAL-FIRST §1 obliges the estate to restate any rule whose binding clock is a
        live fill count) — it is made EXPENSIVE AND VISIBLE:

          * `live_record` is REQUIRED and is written into the row. It must carry `fills` and
            `cumulative_net_r`. An amendment made at zero live fills is a clean amendment: there
            is no record it could have been fitted to. One made at 40 fills is not, and the row
            says which it is in a field nobody has to compute — `amended_on_a_virgin_record`.
          * both directions must be supplied together. Amending only the promotion side is the
            exact shape of a rule loosened to fit, so a complete replacement set is required
            (`register()` demands both for the same reason).
          * an OwnerCeremony is required, as for every transition.
          * `reason` must be non-empty and `supersedes` must name the rule_ids being replaced,
            so the diff is in the file rather than in a diff of the file.
          * PROMOTED and STOPPED incubants are refused: the lane is over and its rules are
            history.

        It records `state` unchanged — an amendment is not a transition, and `state()` folding
        to the latest row keeps working because the row carries the same state it found.
        """
        cur = self.state().get(incubant_id)
        if cur is None:
            raise IncubationRefusal(
                "unknown_incubant",
                f"{incubant_id!r} is not registered; there are no rules to amend.")
        frm = str(cur.get("state"))
        if frm not in ("PROPOSED", "ARMED"):
            raise IncubationRefusal(
                "amendment_after_the_lane",
                f"{incubant_id!r} is {frm}. Its rules are history: a promoted or stopped "
                f"incubant's thresholds are the record of why it moved, and rewriting them "
                f"rewrites that.",
                detail=frm)
        if not stop_rules or not promotion_rules:
            raise IncubationRefusal(
                "amendment_one_sided",
                f"{incubant_id!r}: an amendment must supply BOTH stop and promotion rules. "
                f"Replacing only one side is the shape of a threshold loosened to fit — and "
                f"the estate's own restatement (OD-HISTORICAL-FIRST) changes the promotion "
                f"side, which is precisely the side a reader will suspect.")
        if not reason:
            raise IncubationRefusal(
                "amendment_reason_missing",
                f"{incubant_id!r}: an amendment needs a `reason`. 'Because the old rule was "
                f"wrong' is a claim that has to be written down where the next reader finds it.")
        if not isinstance(live_record, dict) or "fills" not in live_record \
                or "cumulative_net_r" not in live_record:
            raise IncubationRefusal(
                "amendment_live_record_missing",
                f"{incubant_id!r}: `live_record` must carry `fills` and `cumulative_net_r`. It "
                f"is what tells the next reader whether this amendment COULD have been fitted "
                f"to the live stream. Refusing to record it is refusing the only check there "
                f"is.",
                detail=live_record)
        fills = live_record.get("fills")
        virgin = isinstance(fills, (int, float)) and float(fills) == 0.0
        row = {
            "schema": INCUBATION_SCHEMA,
            "row_kind": "incubation_rule_amendment",
            "ts": self._timestamp(),
            "session": self.session,
            "state": frm,                    # unchanged: an amendment is not a transition
            # The arrow convention every other row uses, so `transition` stays
            # greppable; `row_kind` is what distinguishes an amendment from a move.
            "transition": f"{frm}->{frm} (amend_rules)",
            "incubant_id": incubant_id,
            "sleeve": cur.get("sleeve"),
            "account": cur.get("account"),
            "admission_basis": cur.get("admission_basis"),
            "proposed_weight": cur.get("proposed_weight"),
            "owner_ceremony": ceremony.as_dict(),
            "supersedes_rule_ids": list(supersedes),
            "amendment_reason": reason,
            "live_record_at_amendment": dict(live_record),
            "amended_on_a_virgin_record": virgin,
            "amendment_integrity_note": (
                "ZERO live fills at the amendment: there is no live record this could have been "
                "fitted to, which is the only clean moment to restate a promotion rule."
                if virgin else
                "NON-ZERO live fills at the amendment. This rule COULD have been fitted to the "
                "live stream. Read it with that in mind; the registry does not refuse it, it "
                "refuses to let it be invisible."),
            "stop_rules": [r.as_dict() for r in stop_rules],
            "promotion_rules": [r.as_dict() for r in promotion_rules],
            "capacity_at_write": self.capacity(),
            "note": note,
        }
        for k in ("evidence", "expected_economics", "graduation_record", "owner_risk_acceptance",
                  "proposed_by"):
            if k in cur:
                row[k] = cur[k]
        append_row(self.path, row)
        return row

    def promote(self, incubant_id: str, ceremony: OwnerCeremony, *, met_rule: str = "",
                to_weight: float | None = None, note: str = "") -> dict:
        """ARMED -> PROMOTED. `met_rule` names the promotion rule that was satisfied.

        The new weight is recorded, not enforced: weights above the incubation ceiling are the
        owner's allocation decision and this registry has no authority over them. What it does
        enforce is that leaving the lane is a ceremony with a receipt.
        """
        return self._transition(
            incubant_id, "PROMOTED", ceremony, note=note,
            extra={"met_rule": met_rule,
                   "promoted_to_weight": (float(to_weight) if to_weight is not None else None)},
        )

    # -- reporting -------------------------------------------------------------------------
    def summary(self) -> dict:
        st = self.state()
        by_state: dict[str, list[str]] = {}
        for k, r in sorted(st.items()):
            by_state.setdefault(str(r.get("state")), []).append(k)
        return {
            "schema": "gtos.training_lane.incubation_summary.v1",
            "path": str(self.path),
            "n_incubants": len(st),
            "by_state": {k: sorted(v) for k, v in sorted(by_state.items())},
            "capacity": self.capacity(),
            "by_admission_basis": {
                b: sorted(k for k, r in st.items() if r.get("admission_basis") == b)
                for b in ADMISSION_BASES
            },
            "note": (
                "GRADUATED and OWNER_RISK_ACCEPTED are both legitimate intakes and are NOT the "
                "same claim. Any page reporting incubants must keep them apart."
            ),
        }


def rules_from_dicts(rows: Sequence[dict]) -> tuple[PreRegisteredRule, ...]:
    """Build rules from JSON-shaped dicts (the AS dossier shape uses `class`, not `class_`)."""
    return tuple(
        PreRegisteredRule(
            rule_id=str(r.get("rule_id") or r.get("id") or ""),
            what=str(r.get("what") or ""),
            class_=str(r.get("class") or r.get("class_") or ""),
            action=str(r.get("action") or ""),
            threshold=r.get("threshold"),
            basis=str(r.get("basis") or ""),
            pre_registered_utc=str(r.get("pre_registered_utc") or ""),
            why_not_inference=str(r.get("why_not_inference") or ""),
            false_trip_note=str(r.get("false_trip_note") or ""),
        )
        for r in rows
    )
