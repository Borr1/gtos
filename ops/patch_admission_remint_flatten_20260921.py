from pathlib import Path

p = Path(r"host-local\redacted_host\repo\src\components\ultimate_book\admission.py")
text = p.read_text(encoding="utf-8")
old = """        # OWNER UNLOCK 2026-09-21: Jev place Choice (GTOS_JEV_PLACE_APPLY=1)
        try:
            from src.judgment.place_choice import evaluate_place_choice
            _plc = evaluate_place_choice(it)
            if _plc.get(\"refuse_place\") and _plc.get(\"action\") in {\"STAND\", \"DELAY\"}:
                _refuse(it, \"jev_place_choice_\" + str(_plc.get(\"action\", \"STAND\")).lower())
                continue
        except Exception:
            pass
"""
new = """        # OWNER UNLOCK 2026-09-21: Jev place Choice (GTOS_JEV_PLACE_APPLY=1)
        # Dig 20260921: REMINT/FLATTEN refuse fresh place + stamp jev_writer_compose
        try:
            from src.judgment.place_choice import evaluate_place_choice
            _plc = evaluate_place_choice(it)
            _compose = _plc.get(\"writer_compose\") if isinstance(_plc, dict) else None
            if not isinstance(_compose, dict):
                try:
                    from src.judgment.writer_compose_place import compose_writer_intent
                    _compose = compose_writer_intent(_plc if isinstance(_plc, dict) else {})
                except Exception:
                    _compose = {
                        \"action\": (_plc or {}).get(\"action\") if isinstance(_plc, dict) else \"DELAY\",
                        \"allow_fresh_place\": False,
                        \"remint_signal\": False,
                        \"flatten_candidate\": False,
                        \"refuse_admit\": True,
                        \"reason\": \"jev_place_compose_import_fail\",
                    }
            _act = str((_compose or {}).get(\"action\") or (_plc or {}).get(\"action\") or \"\").upper()
            _det = getattr(it, \"details\", None)
            if not isinstance(_det, dict):
                try:
                    it.details = {}
                    _det = it.details
                except Exception:
                    _det = None
            if isinstance(_det, dict) and isinstance(_compose, dict):
                _det[\"jev_writer_compose\"] = dict(_compose)
                _det[\"jev_place_action\"] = _act
            if _act in {\"STAND\", \"DELAY\"}:
                _refuse(it, \"jev_place_choice_\" + _act.lower())
                continue
            if isinstance(_plc, dict) and _plc.get(\"refuse_place\") and _act not in {\"PLACE\", \"REMINT\", \"FLATTEN_CANDIDATE\", \"SKIP_APPLY_OFF\", \"SKIP_NOT_CHALLENGE\"}:
                _refuse(it, \"jev_place_choice_\" + str(_plc.get(\"action\", \"stand\")).lower())
                continue
            if _act == \"REMINT\":
                if isinstance(_det, dict):
                    _det[\"jev_remint_signal\"] = True
                _refuse(it, \"jev_place_choice_remint\")
                continue
            if _act == \"FLATTEN_CANDIDATE\":
                if isinstance(_det, dict):
                    _det[\"jev_flatten_candidate\"] = True
                _refuse(it, \"jev_place_choice_flatten_candidate\")
                continue
            # PLACE / SKIP_* fall through
        except Exception:
            pass
"""
if old not in text:
    # try already patched?
    if "jev_place_choice_remint" in text and "Dig 20260921" in text:
        print("ALREADY_PATCHED")
        raise SystemExit(0)
    raise SystemExit("OLD_BLOCK_NOT_FOUND")
bak = p.with_suffix(".py.bak_remint_flatten_20260921")
if not bak.exists():
    bak.write_text(text, encoding="utf-8")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("PATCHED", p)
print("BACKUP", bak)
