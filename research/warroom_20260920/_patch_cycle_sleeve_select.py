from pathlib import Path
import ast

p = Path(r"host-local\redacted_host\repo\src\judgment\cycle.py")
# When run on box this path won't exist — runner is VPS. Script is copied to VPS.
text = p.read_text(encoding="utf-8")

import_block = '''
try:
    from .sleeve_select import (
        QUESTION_ID as SLEEVE_SELECT_QID,
        append_warroom_shadow_jsonl,
        build_sleeve_select_menu,
        emit_sleeve_select_shadow_payload,
        sleeve_select_apply_enabled,
        sleeve_select_shadow_enabled,
    )
except Exception:  # noqa: BLE001
    SLEEVE_SELECT_QID = "JEV_SLEEVE_SELECT"  # type: ignore
    append_warroom_shadow_jsonl = None  # type: ignore
    build_sleeve_select_menu = None  # type: ignore
    emit_sleeve_select_shadow_payload = None  # type: ignore
    sleeve_select_apply_enabled = None  # type: ignore
    sleeve_select_shadow_enabled = None  # type: ignore
'''

if "build_sleeve_select_menu" not in text:
    needle = "from .alive_menu import"
    idx = text.find(needle)
    if idx < 0:
        raise SystemExit("no alive_menu import")
    end = text.find("\n", idx) + 1
    if "(" in text[idx:end]:
        end = text.find(")\n", idx) + 2
    text = text[:end] + import_block + text[end:]
    print("IMPORT_INSERTED")
else:
    print("IMPORT_OK")

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
                sleeve_select_payload["cycle_id"] = getattr(menu, "cycle_id", None)
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
    print("HOOK_ALREADY")
else:
    marker = '"alive_menu": menu.as_dict()'
    pos = text.find(marker)
    if pos < 0:
        marker = "'alive_menu': menu.as_dict()"
        pos = text.find(marker)
    if pos >= 0:
        line_end = text.find("\n", pos)
        text = text[: line_end + 1] + hook + text[line_end + 1 :]
        print("HOOK_AFTER_ALIVE_MENU")
    else:
        rpos = text.rfind("\n    return ")
        if rpos < 0:
            raise SystemExit("no insert point")
        text = text[:rpos] + "\n" + hook + text[rpos:]
        print("HOOK_BEFORE_RETURN")
    p.write_text(text, encoding="utf-8")
    print("WROTE")

ast.parse(p.read_text(encoding="utf-8"))
print("AST_OK")
