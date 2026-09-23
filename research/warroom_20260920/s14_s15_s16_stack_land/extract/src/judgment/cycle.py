"""One Challenge fluid-gate cycle: ALIVE_MENU → CONF_GATE → DONE_OUTSIDE (+ S14/S15).

Shadow by default. APPLY writes a LABEL draft only when Chair enables the
flag *and* a legal prove receipt exists. Jev never places.

S14 ``REGIME_GATE_SHADOW`` and S15 ``COST_OF_ERROR`` compose on this same
admit sidecar — not a parallel place path. Outcomes are labels only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .alive_menu import AliveMenu, assert_menu_fresh, rebuild_choice_criteria
from .challenge import CHALLENGE_LOGIN, account_surface, assert_challenge_payout_writer
from .conf_gate import (
    ConfGateLog,
    CostOfErrorLog,
    extract_confidence,
    extract_ticket,
    log_conf_gate,
    log_cost_of_error,
    merge_conf_gate_s15,
    tape_authority_facts,
)
from .done_outside import VerifyResult, completion_truth, verify_side_effect
from .flags import (
    ApplyDecision,
    ProveReceipt,
    apply_authorized,
    apply_enabled,
    load_prove_receipt,
    shadow_enabled,
)
from .inventory import LiveInventory, collect_live_inventory
from .regime_compose import RegimeComposeResult
from .regime_gate import evaluate_s14
from .regime_system_one import S14_QUESTION_IDS, RegimeAnswerCache
from .veto import assert_answers_have_no_place_path, refuse_invented_news_protocol

SCHEMA = "jev_fluid_gate_v1"
NAMESPACE = "gtos.astra.jev_trial.fluid_gate.v1"

FANOUT_QUESTION_IDS = (
    "next_gate",
    "urgency",
    "evidence_enough",
    "corr_hold",
    "sleeve_fit",
)

S14_FANOUT_QUESTION_IDS = FANOUT_QUESTION_IDS + S14_QUESTION_IDS

REQUIRED_LOG_KEYS = (
    "schema",
    "mode",
    "shadow_log_only",
    "never_place",
    "never_remint",
    "never_flatten",
    "account_surface",
    "alive_menu",
    "conf_gate",
    "cost_of_error",
    "s15_tape_authority",
    "broker_effect",
)

REQUIRED_LOG_CONSTS = {
    "schema": SCHEMA,
    "mode": "shadow_log_only",
    "shadow_log_only": True,
    "never_place": True,
    "never_remint": True,
    "never_flatten": True,
    "broker_effect": False,
}


@dataclass
class CycleResult:
    """Outcome of one fluid-gate cycle. ``broker_effect`` is always False."""

    cycle_id: str
    inventory: LiveInventory
    menu: AliveMenu
    conf_gate: ConfGateLog
    cost_of_error: CostOfErrorLog | None
    apply: ApplyDecision
    log_path: Path | None
    apply_path: Path | None
    verify: VerifyResult
    completion: str
    skipped: bool = False
    skip_reason: str | None = None
    notes: list[str] = field(default_factory=list)
    regime: RegimeComposeResult | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "cycle_id": self.cycle_id,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "inventory_fingerprint": self.inventory.fingerprint,
            "menu": self.menu.as_dict(),
            "conf_gate": self.conf_gate.as_dict(),
            "cost_of_error": None if self.cost_of_error is None else self.cost_of_error.as_dict(),
            "apply": self.apply.as_dict(),
            "log_path": str(self.log_path) if self.log_path else None,
            "apply_path": str(self.apply_path) if self.apply_path else None,
            "verify": self.verify.as_dict(),
            "completion": self.completion,
            "broker_effect": False,
            "notes": list(self.notes),
            "regime": None if self.regime is None else self.regime.as_dict(),
        }


def default_log_dir(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    override = os.environ.get("GTOS_JEV_FLUID_GATES_LOG_DIR", "").strip()
    if override:
        return Path(override)
    return root / "judgment" / "live" / "jev_sidecar"


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_fluid_gate_cycle(
    *,
    login: str = CHALLENGE_LOGIN,
    inventory: LiveInventory | None = None,
    answers: Mapping[str, object] | None = None,
    stake: str = "sleeve_admit",
    confidence_key: str = "next_gate",
    log_dir: Path | str | None = None,
    prove_dir: Path | str | None = None,
    prove_site_id: str | None = None,
    prior_menu: AliveMenu | None = None,
    jev_done_choice: str | None = None,
    invented_files: tuple[str, ...] = (),
    shadow: bool | None = None,
    apply_flag: bool | None = None,
    force: bool = False,
    environ: Mapping[str, str] | None = None,
    gold_state: Mapping[str, Any] | None = None,
    harvest: Mapping[str, Any] | None = None,
    s14_answers: Mapping[str, Any] | None = None,
    s14_cache: RegimeAnswerCache | None = None,
    s14_research_thresholds: bool = False,
    s14_confidence_threshold: float | None = None,
    s14_half_size_threshold: float | None = None,
    s14_g4_applies: bool = False,
    s15_ticket: str | int | None = None,
    s15_subclass: str | None = None,
    s15_gate_id: str | None = None,
) -> CycleResult:
    """Run one shadow cycle. ``force=True`` is for tests / explicit CLI invoke.

    Production Chair enable is ``GTOS_JEV_FLUID_GATES_SHADOW=1``. APPLY stays
    off unless that flag *and* ``GTOS_JEV_FLUID_GATES_APPLY=1`` *and* a prove
    receipt all pass — and even then only a LABEL draft is written.
    """

    assert_challenge_payout_writer(login)
    refuse_invented_news_protocol(invented_files)
    assert_answers_have_no_place_path(dict(answers) if answers else None)
    assert_answers_have_no_place_path(dict(s14_answers) if s14_answers else None)

    shadow_on = shadow if shadow is not None else shadow_enabled(environ=environ, force=force)
    apply_on = apply_flag if apply_flag is not None else apply_enabled(environ=environ)

    live = inventory if inventory is not None else collect_live_inventory()
    menu = rebuild_choice_criteria(live, prior_menu=prior_menu)
    # Freshness is always vs the menu we are about to log — never a reused map.
    assert_menu_fresh(menu, live)

    regime: RegimeComposeResult | None = None
    s14_jev_state: dict[str, object] | None = None
    merged_answers: dict[str, object] = dict(answers) if answers else {}
    notes_s14: list[str] = []
    if gold_state is not None:
        bucket_state, s14_call, regime = evaluate_s14(
            gold_state,
            harvest,
            injected_answers=s14_answers,
            cache=s14_cache,
            confidence_threshold=s14_confidence_threshold,
            half_size_threshold=s14_half_size_threshold,
            research_thresholds=s14_research_thresholds,
            g4_applies=s14_g4_applies,
        )
        s14_jev_state = dict(bucket_state.jev_state)
        if s14_call.raw:
            merged_answers.update(s14_call.raw)
        assert_answers_have_no_place_path(merged_answers)
        notes_s14 = [
            "chair_compose_s14_regime_gate_shadow",
            "s14_same_admit_sidecar_not_parallel",
        ]

    if regime is not None and regime.answers is not None and regime.answers.regime_max_p is not None:
        conf_value, conf_source = regime.answers.regime_max_p, "s14_regime_max_p"
    else:
        conf_value, conf_source = extract_confidence(merged_answers or answers, key=confidence_key)
    conf = log_conf_gate(conf_value, stake=stake, source=conf_source)
    ticket = extract_ticket(gold_state, explicit=s15_ticket)
    cost = log_cost_of_error(
        conf_value,
        stake=stake,
        ticket=ticket,
        subclass=s15_subclass,
        gate_id=s15_gate_id,
        gold_state=gold_state,
        regime=regime,
    )
    receipt: ProveReceipt | None = None
    if prove_site_id:
        receipt = load_prove_receipt(prove_site_id, prove_dir=prove_dir)
    decision = apply_authorized(
        stake=stake,
        apply_flag=apply_on,
        receipt=receipt,
        band=conf.band,
        required_band=conf.required_band,
    )

    notes = [
        "chair_enforce_alive_menu",
        "chair_enforce_conf_gate",
        "chair_enforce_done_outside",
        "chair_enforce_s15_cost_of_error",
        "s15_tape_authority_baked",
        "s15_false_abstain_0",
        "s15_review_291087142_keep_not_hard_off",
        "s15_review_293128383_keep_offhours_not_hard_off",
        "s15_place_infinity_veto",
        "fanout_questions_logged_not_chained",
        *notes_s14,
    ]
    if not shadow_on and not force:
        notes.append("shadow_flag_off")
        empty = VerifyResult(False, "shadow_flag_off")
        return CycleResult(
            cycle_id=menu.cycle_id,
            inventory=live,
            menu=menu,
            conf_gate=conf,
            cost_of_error=cost,
            apply=decision,
            log_path=None,
            apply_path=None,
            verify=empty,
            completion=completion_truth(jev_choice=jev_done_choice, verify=empty),
            skipped=True,
            skip_reason="shadow_flag_off",
            notes=notes,
            regime=regime,
        )

    root = Path(log_dir) if log_dir is not None else default_log_dir()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = root / "admit" / day / f"{menu.cycle_id}.json"
    payload = {
        "schema": SCHEMA,
        "mode": "shadow_log_only",
        "shadow_log_only": True,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "never_move_sl": True,
        "never_write_chair_inbox": True,
        "namespace": NAMESPACE,
        "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account_surface": account_surface(),
        "inventory": {
            "sleeves": list(live.sleeves),
            "workers": list(live.workers),
            "handlers": list(live.handlers),
            "blocked_sleeves": list(live.blocked_sleeves),
            "fingerprint": live.fingerprint,
            "collected_at_utc": live.collected_at_utc,
            "source": live.source,
            "notes": list(live.notes),
        },
        "alive_menu": menu.as_dict(),
        "fanout_book": {
            "label": "FANOUT_BOOK",
            "questions": list(S14_FANOUT_QUESTION_IDS if regime is not None else FANOUT_QUESTION_IDS),
            "note": "independent questions over one state; code consumes branches; "
            "toxic_remint is close-only and is not asked LIVE. S14 regime questions "
            "share this call when gold_state is present.",
        },
        "answers_injected": bool(answers) or bool(s14_answers),
        "answers": dict(merged_answers),
        "conf_gate": merge_conf_gate_s15(conf, cost),
        "cost_of_error": cost.as_dict(),
        "s15_tape_authority": tape_authority_facts(),
        "apply": decision.as_dict(),
        "prove_site_id": prove_site_id,
        "prove_receipt": None
        if receipt is None
        else {
            "site_id": receipt.site_id,
            "wire_class": receipt.wire_class,
            "proven": receipt.proven,
            "owner_word": receipt.owner_word,
        },
        "broker_effect": False,
        "jev_done_choice_advisory": jev_done_choice,
        "disposition": "log_only" if not decision.apply else "label_draft",
        "steal": "S14" if regime is not None else None,
        "steal_s15": "S15",
        "regime": None if regime is None else regime.as_dict(),
        "s14_jev_state": s14_jev_state,
    }
    _write_json(log_path, payload)

    apply_path: Path | None = None
    if decision.apply:
        apply_path = root / "apply" / day / f"{menu.cycle_id}.json"
        _write_json(
            apply_path,
            {
                "schema": SCHEMA,
                "kind": "label_draft",
                "never_place": True,
                "broker_effect": False,
                "cycle_id": menu.cycle_id,
                "account_surface": account_surface(),
                "conf_gate": conf.as_dict(),
                "apply": decision.as_dict(),
                "chair_verb": "LABEL",
            },
        )
        notes.append("apply_label_draft_written")

    verify = verify_side_effect(
        "shadow_log",
        path=log_path,
        required_keys=REQUIRED_LOG_KEYS,
        required_consts=REQUIRED_LOG_CONSTS,
    )
    if decision.apply and apply_path is not None:
        apply_verify = verify_side_effect(
            "label_draft",
            path=apply_path,
            required_keys=("kind", "never_place", "broker_effect", "chair_verb"),
            required_consts={
                "kind": "label_draft",
                "never_place": True,
                "broker_effect": False,
                "chair_verb": "LABEL",
            },
        )
        if not apply_verify.ok:
            verify = apply_verify
    done = completion_truth(jev_choice=jev_done_choice, verify=verify)
    return CycleResult(
        cycle_id=menu.cycle_id,
        inventory=live,
        menu=menu,
        conf_gate=conf,
        cost_of_error=cost,
        apply=decision,
        log_path=log_path,
        apply_path=apply_path,
        verify=verify,
        completion=done,
        notes=notes,
        regime=regime,
    )
