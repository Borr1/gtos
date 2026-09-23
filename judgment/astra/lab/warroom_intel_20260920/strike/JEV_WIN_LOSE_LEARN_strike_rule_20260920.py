# JEV_WIN_LOSE_LEARN strike_when_right stub — shadow only, apply=false
# Replay: feed scenario state dicts twice; Choice/Score must match.

def strike_when_right_choice(state: dict) -> dict:
    """Deterministic STRIKE_WHEN_RIGHT Choice stub.
    1) trap (FS & !KEEP) OR (year_le0 & full_state_dark) → A_STAND_DOWN
    2) KEEP residual FS → E_KEEP_CAP; else many null voters → C_SIZE_TRIM
    3) else → D_FULL
    Score base by Choice minus 5 per PENDING among alive/regime/conf/session_fit.
    """
    miss = state.get("miss")
    keep = state.get("keep_signature")
    year_le0 = state.get("year_le0_geometry_proxy")
    full_dark = state.get("full_state_dark")
    voters = [state.get("alive"), state.get("regime_tag"), state.get("conf_band"),
              state.get("session_fit"), state.get("Choice_prior")]
    n_incomplete = sum(1 for v in voters if v is None or v in ("PENDING", "PENDING_SHADOW"))
    keep_residual_fs = (keep is True and miss == "false_structure")
    year_proxy_win = state.get("year_proxy_valid_win") is True
    trap_nonkeep = (miss == "false_structure" and keep is False)
    trap_year = bool(year_le0 and full_dark)
    if trap_nonkeep or trap_year:
        choice, reason = "A_STAND_DOWN", "trap_signal"
    elif keep_residual_fs or (n_incomplete >= 3 and not year_proxy_win):
        if keep_residual_fs:
            choice, reason = "E_KEEP_CAP", "keep_residual_fs_review_not_hard_off"
        else:
            choice, reason = "C_SIZE_TRIM", "incomplete_state"
    else:
        choice, reason = "D_FULL", "no_trap_state_sufficient_or_valid_win"
    score_base = {"A_STAND_DOWN": 10, "B_SIZE_HALF": 30, "C_SIZE_TRIM": 45, "D_FULL": 80, "E_KEEP_CAP": 70}[choice]
    pending_pen = 5 * sum(1 for v in voters[:4] if v in (None, "PENDING", "PENDING_SHADOW"))
    return {"Choice": choice, "Score": max(0, score_base - pending_pen), "reason": reason, "apply": False, "place": False}
