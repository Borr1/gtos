"""CONF_GATE consume-after-prove helpers — Dig Land D draft.

HIGH trust blocked when option-order sensitivity is material and
STATE_EVIDENCE_SUFFICIENCY fails. Dig merges; Dig Land D never broker-sends.
"""

from __future__ import annotations

from typing import Mapping


def high_trust_blocked_by_order_sensitivity(
    *,
    flip_rate: float | None,
    max_swing_pts: float | None,
    state_evidence_sufficiency_pass: bool,
    flip_threshold: float = 0.0,
    swing_threshold: float = 3.0,
) -> bool:
    """Chair WORD: block HIGH when flip>0 or swing>=3 without sufficiency pass."""
    flip = float(flip_rate or 0.0)
    swing = float(max_swing_pts or 0.0)
    material = flip > flip_threshold or swing >= swing_threshold
    if not material:
        return False
    return not bool(state_evidence_sufficiency_pass)


def conf_band_after_prove(
    vendor_band: str,
    *,
    flip_rate: float | None = None,
    max_swing_pts: float | None = None,
    state_evidence_sufficiency_pass: bool = True,
    vendor_determinism_challenge_true: bool = False,
) -> str:
    """Downgrade HIGH→LOW when order-sensitive without sufficiency, or vendor det. false."""
    band = str(vendor_band or "LOW").upper()
    if high_trust_blocked_by_order_sensitivity(
        flip_rate=flip_rate,
        max_swing_pts=max_swing_pts,
        state_evidence_sufficiency_pass=state_evidence_sufficiency_pass,
    ):
        return "LOW"
    if band == "HIGH" and not vendor_determinism_challenge_true:
        # vendor HIGH not Challenge-true until calibration — stay MED for auto paths
        return "MED"
    return band


def receipt_has_required_hashes(receipt: Mapping[str, object] | None) -> bool:
    if not receipt:
        return False
    need = ("menu_hash", "option_order_hash", "state_hash", "model_id", "run_id")
    return all(str(receipt.get(k) or "").strip() for k in need)
