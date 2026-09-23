from pathlib import Path
import ast

p = Path(r"host-local\redacted_host\repo\src\judgment\cycle.py")
text = p.read_text(encoding="utf-8")

import_block = '''
try:
    from .sleeve_select import (
        QUESTION_ID as SLEEVE_SELECT_QID,
        build_sleeve_select_menu,
        emit_sleeve_select_shadow_payload,
        sleeve_select_shadow_enabled,
    )
except Exception:  # noqa: BLE001
    SLEEVE_SELECT_QID = "JEV_SLEEVE_SELECT"  # type: ignore
    build_sleeve_select_menu = None  # type: ignore
    emit_sleeve_select_shadow_payload = None  # type: ignore
    sleeve_select_shadow_enabled = None  # type: ignore
'''

if "build_sleeve_select_menu" not in text:
    needle = "from .alive_menu import AliveMenu, assert_menu_fresh, rebuild_choice_criteria"
    if needle not in text:
        raise SystemExit("alive_menu import missing")
    text = text.replace(needle, needle + "\n" + import_block, 1)
    print("IMPORT_OK")
else:
    print("IMPORT_PRESENT")

hook = '''
    # JEV_SLEEVE_SELECT — SHADOW when fluid shadow on; APPLY=0 until hist-prove
    if build_sleeve_select_menu is not None and shadow_on:
        try:
            _ss_on = True
            if sleeve_select_shadow_enabled is not None:
                try:
                    _ss_on = bool(sleeve_select_shadow_enabled(environ=environ, fluid_shadow_on=True))
                except TypeError:
                    _ss_on = bool(sleeve_select_shadow_enabled(environ=environ))
            if _ss_on:
                _sym = "CHALLENGE"
                _state = dict(answers) if answers else {}
                if answers:
                    _sym = str(answers.get("symbol") or answers.get("instrument") or _sym)
                ss_menu = build_sleeve_select_menu(_sym, _state)
                sleeve_select_payload = emit_sleeve_select_shadow_payload(
                    ss_menu, state=_state, apply_flag=False
                )
                sleeve_select_payload["cycle_id"] = menu.cycle_id
                payload["jev_sleeve_select"] = sleeve_select_payload
                payload["shadow.jev.sleeve_select.question_id"] = SLEEVE_SELECT_QID
                payload["shadow.jev.sleeve_select.apply"] = False
                payload["shadow.jev.sleeve_select.place"] = False
                notes.append("jev_sleeve_select_shadow")
                notes.append("jev_sleeve_select_apply_0")
        except Exception as _ss_exc:  # noqa: BLE001
            notes.append(f"jev_sleeve_select_err:{type(_ss_exc).__name__}")
            payload["jev_sleeve_select"] = {
                "question_id": SLEEVE_SELECT_QID,
                "error": type(_ss_exc).__name__,
                "apply": False,
                "place": False,
                "fail_closed": True,
            }

'''

if "jev_sleeve_select_shadow" in text:
    print("HOOK_PRESENT")
else:
    marker = '        "close_state": None if close_state is None else dict(close_state),\n    }\n    _write_json(log_path, payload)'
    if marker not in text:
        raise SystemExit("payload close marker missing")
    repl = '        "close_state": None if close_state is None else dict(close_state),\n    }\n' + hook + '    _write_json(log_path, payload)'
    text = text.replace(marker, repl, 1)
    print("HOOK_INSERTED")

p.write_text(text, encoding="utf-8")
ast.parse(text)
print("AST_OK")
