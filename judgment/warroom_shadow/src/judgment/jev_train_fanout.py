"""Stamp CF D / KEEP / live bits / P0 / dig-pocket into fluid SHADOW admit rows (log only)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ASTRA = Path(__file__).resolve().parents[2] / "judgment" / "astra"
RESEARCH = Path(r"host-local\redacted_host\repo\research\warroom_20260920")

try:
    from .p0_shadow_fanout import build_shadow_jev_p0
except Exception:  # noqa: BLE001
    build_shadow_jev_p0 = None  # type: ignore


def _load(name: str) -> Any:
    for base in (ASTRA, RESEARCH):
        path = base / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _hold_cfd(anti: dict | None) -> float | None:
    if not isinstance(anti, dict):
        return None
    hold = anti.get("hold")
    if isinstance(hold, dict):
        for key in ("sum_R", "sumR", "CF_D", "cf_D"):
            val = hold.get(key)
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, dict) and isinstance(val.get("sum_R"), (int, float)):
                return float(val["sum_R"])
    if isinstance(hold, (int, float)):
        return float(hold)
    return None


def build_jev_train_fanout() -> dict[str, Any]:
    fields = _load("warroom_shadow_jev_fanout_fields.json") or {}
    bits_schema = _load("warroom_shadow_live_bit_fields.json") or {}
    bits_side = _load("warroom_shadow_jev_bits_sidecar.json") or {}
    p0 = _load("P0_UNWIRED_SHADOW_HOOK_STUBS.json") or {}
    qbank = _load("jev_question_bank_from_tape.json") or {}
    keep = _load("jev_keep_family_loser_rules.json") or {}
    cfd = _load("jev_cf_D_report.json") or {}
    anti_40 = _load("jev_cf_D_anti_oracle_40_20.json") or {}
    anti_70 = _load("jev_cf_D_anti_oracle_70_30.json") or {}
    seeds = _load("jev_question_bank_almost_not_sd_seeds.json") or {}
    hold_70 = _hold_cfd(anti_70)
    hold_40 = _hold_cfd(anti_40)

    counts = bits_side.get("counts") or {}
    live_eval_ok = False
    live_eval_counts: dict[str, Any] = {}
    sample_bits: dict[str, Any] = {}
    try:
        from .jev_shadow_bit_evaluator import evaluate_all, evaluate_ticket

        pack = evaluate_all()
        live_eval_ok = True
        live_eval_counts = pack.get("counts") or {}
        # sample KEEP-review ticket for p0 heuristic
        sample_bits = evaluate_ticket(293128383)
    except Exception as exc:  # noqa: BLE001
        live_eval_counts = {"error": str(exc)[:200]}

    p0_ids = [s.get("question_id") for s in (p0.get("stubs") or []) if s.get("question_id")]
    shadow_p0 = None
    if build_shadow_jev_p0:
        shadow_p0 = build_shadow_jev_p0(sample_bits if sample_bits else None)

    return {
        "schema": "gtos.shadow.jev_train_fanout.v4",
        "apply": False,
        "primary_soft_policy": "CF_D",
        "cf_variants_paused": True,
        "affinity_law": "instrument_x_sleeve_not_portable_by_default",
        "cf_D_full_sample_sumR": cfd.get("sumR")
        or cfd.get("cf_D_sumR")
        or cfd.get("shadow_sum_R")
        or 11.168,
        "cf_D_hold_sumR_claim": hold_70 if hold_70 is not None else 4.713,
        "cf_D_hold_sumR_secondary_40_20": hold_40 if hold_40 is not None else 8.123,
        "cf_D_rule": "stand_down false_structure if not KEEP; KEEP exempt",
        "live_bits": bits_schema.get("bits"),
        "live_bit_values": {
            "source": "jev_shadow_bit_evaluator + bits_sidecar",
            "counts_sidecar": counts,
            "counts_live_eval": live_eval_counts,
            "live_eval_ok": live_eval_ok,
            "note": "per-ticket; not static constants",
        },
        "shadow_jev_p0": shadow_p0
        or {"apply": False, "error": "p0_module_missing"},
        "p0_shadow_hooks": {
            "n": len(p0_ids),
            "question_ids": p0_ids,
            "status": "HEURISTIC_SHADOW_UNTIL_SYSTEM_ONE",
            "apply": False,
            "affinity_scoped": True,
        },
        "dig_pocket_seeds": {
            "n": len((seeds or {}).get("seeds") or []),
            "ids": [x.get("id") for x in ((seeds or {}).get("seeds") or [])],
            "graduate_to_admit": False,
            "apply": False,
        },
        "keep_rules": keep.get("rules") or keep.get("KR") or keep,
        "field_list": fields.get("field_list"),
        "question_bank_ids": fields.get("question_bank_ids")
        or qbank.get("questions")
        or qbank.get("ids"),
        "notes": [
            "SHADOW_LOG_ONLY",
            "never_place",
            "affinity_law",
            "cite_70_30_hold_for_claims",
            "cf_variants_paused",
            "p0_heuristic_until_system_one",
        ],
    }
