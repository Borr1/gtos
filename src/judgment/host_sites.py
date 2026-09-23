"""Host site piece. Each site stays nested.

One ask: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
The choice, the host line, the github line, the file length, the tilt,
the piece loop, and whether the site exists are the Noul, Choice, or
Score that came back. Prior outcomes are attached on that ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset and does not restore a constant. A floor and a baseline are not a
question. This module does not send.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.host_sites.v1"
REPO_ROOT = Path(__file__).resolve().parents[2]

SITE_ORDER = (
    "UB-AUTH-010",
    "UB-PLC-017",
    "F5-JEV-004",
    "SEL-V4-002",
    "APLU-OBS-001",
)
FILE_LINE_SITES = frozenset({"UB-AUTH-010", "UB-PLC-017", "SEL-V4-002", "APLU-OBS-001"})
TILT_SITES = frozenset({"F5-JEV-004"})
SHADOW_SITES = frozenset({"APLU-OBS-001"})
WIRED_SITES = frozenset({"APLU-OBS-001"})

_IDENTITY = (
    "host_tree",
    "path",
    "host_symbol",
    "github_symbol",
    "alias_wires",
    "same_site_as",
    "note_path",
)
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_SKIP_PARTS = ("floor", "baseline")
_SKIP_WALK = {"prior_outcomes", "account", "books", "questions", "answers"}

# Names of the sites. The choice, the lines, and the tilt are not in here.
HOST_SITES: dict[str, dict[str, Any]] = {
    "UB-AUTH-010": {
        "host_tree": "redacted_host/repo dirty f5-live",
        "path": "src/components/ultimate_book/bridge.py",
        "host_symbol": "admit_and_size(",
        "github_symbol": "admit_and_size(",
    },
    "UB-PLC-017": {
        "host_tree": "redacted_host/repo dirty f5-live",
        "path": "src/components/ultimate_book/book_owner.py",
        "host_symbol": "def _spread_cost_screen",
        "github_symbol": "def _spread_cost_screen",
        "alias_wires": ("F5-JEV-004",),
    },
    "F5-JEV-004": {
        "host_tree": "redacted_host/repo dirty f5-live",
        "path": "src/components/ultimate_book/book_owner.py",
        "host_symbol": "def _spread_cost_screen",
        "github_symbol": "def _spread_cost_screen",
        "same_site_as": "UB-PLC-017",
    },
    "SEL-V4-002": {
        "host_tree": "redacted_host/repo dirty f5-live",
        "path": "src/components/selector_v4.py",
        "host_symbol": "confluence = _evaluate_confluence",
        "github_symbol": "confluence = _evaluate_confluence",
    },
    "APLU-OBS-001": {
        "host_tree": "redacted_host/repo dirty f5-live",
        "path": "src/components/ultimate_book/book_owner.py",
        "host_symbol": "def _spread_cost_screen",
        "github_symbol": "cost_skip = self._spread_cost_screen",
        "same_site_as": "UB-PLC-017",
        "note_path": "judgment/astra/lab/wires/HOST_APLU_OBS_LAND.md",
    },
}

SITE_CHOICES: dict[str, dict[str, str]] = {
    "UB-AUTH-010": {
        "hook_after_decide": (
            "Hook this site after the final decide. The env gate stays in front of the import."
        ),
        "leave_site": "Leave this site as it is.",
    },
    "UB-PLC-017": {
        "hook_after_cost": (
            "Hook this site after the cost screen call. The cost result stays as the screen left it."
        ),
        "leave_site": "Leave this site as it is.",
    },
    "F5-JEV-004": {
        "size_tilt": "The size on this site is the returned tilt. This is not a new refuse.",
        "leave_orig": "Leave the size on this site as it is.",
    },
    "SEL-V4-002": {
        "research_only": "This site stays research. The selector file is not imported.",
        "leave_site": "Leave this site as it is.",
    },
    "APLU-OBS-001": {
        "shadow_observe": (
            "Shadow this site after the cost screen call. The cost result stays as the screen left it."
        ),
        "leave_site": "Leave this site as it is.",
    },
}

XAU_CHOICES: dict[str, str] = {
    "apply_tilt": "The flow alignment size tilt is the returned parameter.",
    "leave_orig": "Leave this size as it is.",
}


def _skip_key(key: str) -> bool:
    low = key.lower()
    return any(part in low for part in _SKIP_PARTS)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _scrub(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return None
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value)
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _skip_key(name):
                continue
            out[name] = _scrub(item, depth + 1)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        return [_scrub(item, depth + 1) for item in value]
    return None


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    probs = _probs(block)
    kept = {name: probs[name] for name in order if name in probs}
    local = _unique(probs, order)
    picked: str | None = None
    helper_ran = False
    try:
        from .jev_questions import unique_highest

        helper_ran = True
        agreed = unique_highest(probs or None, order)
        if agreed in order:
            picked = str(agreed)
    except Exception:
        helper_ran = False
    if not helper_ran:
        return local, kept
    if picked is None or local is None or picked != local:
        return None, kept
    return picked, kept


def _score_of(block: Any) -> float | None:
    """The Score that came back. It is not snapped to a level and not a constant."""

    if not isinstance(block, dict):
        return None
    probs = _probs(block)
    if probs and _unique(probs, tuple(probs)) is None:
        return None
    number = None
    try:
        from .jev_questions import returned_number

        number = _number(returned_number(block))
    except Exception:
        number = None
    if number is not None:
        return number
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _number(raw)


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. Missing stays missing."""

    if not isinstance(block, dict):
        return None
    raw = block.get("noul")
    if raw is None and "Noul" in block:
        raw = block.get("Noul")
    if raw is True or raw is False:
        return raw
    number = _number(raw)
    if number is not None:
        return number
    picked = _unique(_probs(block), ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if receipt_error not in (None, ""):
        return str(receipt_error)
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _identity(spec: Mapping[str, Any]) -> dict[str, Any]:
    return {key: spec[key] for key in _IDENTITY if key in spec}


def _line_of(path: Path, needle: str) -> int | None:
    """Where the symbol sits in this tree. A fact on the ask, not the decision."""

    if not needle or not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for index, line in enumerate(lines, 1):
        if needle in line:
            return index
    return None


def _tree_facts() -> dict[str, Any]:
    facts: dict[str, Any] = {}
    for gate_id, spec in HOST_SITES.items():
        path = REPO_ROOT / str(spec.get("path") or "")
        facts[gate_id] = {
            "path": spec.get("path"),
            "path_exists": path.is_file(),
            "symbol_at": _line_of(path, str(spec.get("github_symbol") or "")),
        }
    return facts


def _levels(state: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _skip_key(key):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                name = str(child_key)
                if name.lower() in _SKIP_WALK:
                    continue
                walk(name, child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            return
        number = _number(value)
        if number is not None:
            found.append(number)

    for key, value in dict(state or {}).items():
        if str(key).lower() in _SKIP_WALK:
            continue
        walk(str(key), value)
    ordered = sorted(set(found))
    return [format(number, ".10g") for number in ordered]


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    if _skip_key(qid):
        return {}
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {str(key): str(text) for key, text in criteria.items()}
    return {qid: body}


def _score_question(qid: str, instructions: str, levels: list[str]) -> dict[str, Any]:
    if _skip_key(qid):
        return {}
    criteria = list(levels) if levels else list(_BETWEEN)
    body: dict[str, Any] = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "score"
    body["instructions"] = instructions
    body["criteria"] = criteria
    return {qid: body}


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    if _skip_key(qid):
        return {}
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes, on this state.",
                "false": "No, on this state.",
            },
        }
    }


def _questions(levels: list[str]) -> dict[str, Any]:
    """One piece. Each site keeps its own questions."""

    pack: dict[str, Any] = {}
    for gate_id in SITE_ORDER:
        pack.update(_choice_question(
            gate_id,
            (
                f"Host site {gate_id}. Pick one option. "
                "The option you return is the decision. "
                "An empty answer or a tie is not a decision. "
                "Do not send."
            ),
            SITE_CHOICES[gate_id],
        ))
        pack.update(_noul_question(
            f"{gate_id}__exists",
            (
                f"Does host site {gate_id} exist on this state? "
                "The noul you return is that existence. "
                "An empty noul leaves it unset. Do not send."
            ),
        ))
        pack.update(_noul_question(
            f"{gate_id}__bound",
            (
                f"Is host site {gate_id} bound on this state? "
                "The noul you return is that bound. "
                "An empty noul leaves it unset. Do not send."
            ),
        ))
        pack.update(_score_question(
            f"{gate_id}__host_line",
            (
                f"The score you return is the host line for {gate_id}. "
                "It may sit between the levels on this state. "
                "An empty score leaves the host line unset. Do not send."
            ),
            levels,
        ))
        pack.update(_score_question(
            f"{gate_id}__github_line",
            (
                f"The score you return is the github line for {gate_id}. "
                "It may sit between the levels on this state. "
                "An empty score leaves the github line unset. Do not send."
            ),
            levels,
        ))
        if gate_id in FILE_LINE_SITES:
            pack.update(_score_question(
                f"{gate_id}__file_lines",
                (
                    f"The score you return is the file length for {gate_id}. "
                    "It may sit between the levels on this state. "
                    "An empty score leaves the file length unset. Do not send."
                ),
                levels,
            ))
        if gate_id in TILT_SITES:
            pack.update(_score_question(
                f"{gate_id}__tilt",
                (
                    f"The score you return is the size tilt for {gate_id}. "
                    "It may sit between the levels on this state. "
                    "An empty score leaves the tilt unset. Do not send."
                ),
                levels,
            ))
        if gate_id in SHADOW_SITES:
            pack.update(_noul_question(
                f"{gate_id}__shadow",
                (
                    f"Is host site {gate_id} shadow on this state? "
                    "The noul you return is that. "
                    "An empty noul leaves it unset. Do not send."
                ),
            ))
        if gate_id in WIRED_SITES:
            pack.update(_noul_question(
                f"{gate_id}__wired",
                (
                    f"Is host site {gate_id} wired on this state? "
                    "The noul you return is that. "
                    "An empty noul leaves it unset. Do not send."
                ),
            ))
    pack.update(_choice_question(
        "xau_tilt",
        (
            "Flow alignment size tilt. Pick one option. "
            "The option you return is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not send."
        ),
        XAU_CHOICES,
    ))
    pack.update(_score_question(
        "xau_tilt__parameter",
        (
            "The score you return is the flow alignment size tilt. "
            "It may sit between the levels on this state. "
            "An empty score leaves the tilt unset. Do not send."
        ),
        levels,
    ))
    pack.update(_score_question(
        "host_piece_loop",
        (
            "The score you return is how many host sites are in this one piece. "
            "It may sit between the levels on this state. "
            "An empty score leaves the piece bound unset. Do not send."
        ),
        levels,
    ))
    return {qid: body for qid, body in pack.items() if not _skip_key(str(qid))}


def _read_site(
    answers: Mapping[str, Any],
    gate_id: str,
    receipt_error: Any,
) -> tuple[dict[str, Any], list[tuple[str, Any, str | None]]]:
    order = tuple(SITE_CHOICES[gate_id])
    choice_block = answers.get(gate_id)
    exists_block = answers.get(f"{gate_id}__exists")
    bound_block = answers.get(f"{gate_id}__bound")
    host_block = answers.get(f"{gate_id}__host_line")
    github_block = answers.get(f"{gate_id}__github_line")
    choice, probs = _choice_of(choice_block, order)
    exists = _noul_of(exists_block)
    bound = _noul_of(bound_block)
    host_line = _score_of(host_block)
    github_line = _score_of(github_block)
    file_lines = None
    file_block = None
    tilt = None
    tilt_block = None
    shadow = None
    shadow_block = None
    wired = None
    wired_block = None
    if gate_id in FILE_LINE_SITES:
        file_block = answers.get(f"{gate_id}__file_lines")
        file_lines = _score_of(file_block)
    if gate_id in TILT_SITES:
        tilt_block = answers.get(f"{gate_id}__tilt")
        tilt = _score_of(tilt_block)
    if gate_id in SHADOW_SITES:
        shadow_block = answers.get(f"{gate_id}__shadow")
        shadow = _noul_of(shadow_block)
    if gate_id in WIRED_SITES:
        wired_block = answers.get(f"{gate_id}__wired")
        wired = _noul_of(wired_block)
    fields: list[tuple[str, Any, Any, tuple[str, ...]]] = [
        (gate_id, choice_block, choice, order),
        (f"{gate_id}__exists", exists_block, exists, ("true", "false")),
        (f"{gate_id}__bound", bound_block, bound, ("true", "false")),
        (f"{gate_id}__host_line", host_block, host_line, ()),
        (f"{gate_id}__github_line", github_block, github_line, ()),
    ]
    if gate_id in FILE_LINE_SITES:
        fields.append((f"{gate_id}__file_lines", file_block, file_lines, ()))
    if gate_id in TILT_SITES:
        fields.append((f"{gate_id}__tilt", tilt_block, tilt, ()))
    if gate_id in SHADOW_SITES:
        fields.append((f"{gate_id}__shadow", shadow_block, shadow, ("true", "false")))
    if gate_id in WIRED_SITES:
        fields.append((f"{gate_id}__wired", wired_block, wired, ("true", "false")))
    remember: list[tuple[str, Any, str | None]] = []
    reasons: list[str] = []
    for key, block, value, field_order in fields:
        reason = _miss(block, value, field_order, receipt_error)
        remember.append((key, value, reason))
        if reason:
            reasons.append(reason)
    spec = HOST_SITES[gate_id]
    path = REPO_ROOT / str(spec.get("path") or "")
    row = _identity(spec)
    row.update({
        "gate_id": gate_id,
        "choice": choice,
        "probabilities": probs,
        "component_exists": exists,
        "bound": bound,
        "host_line": host_line,
        "github_line": github_line,
        "file_lines": file_lines,
        "tilt": tilt,
        "shadow_only": shadow,
        "wired": wired,
        "github_path_exists": path.is_file(),
        "error": reasons[0] if reasons else None,
    })
    return row, remember


def _read_xau(
    answers: Mapping[str, Any],
    receipt_error: Any,
) -> tuple[dict[str, Any], list[tuple[str, Any, str | None]]]:
    order = tuple(XAU_CHOICES)
    choice_block = answers.get("xau_tilt")
    tilt_block = answers.get("xau_tilt__parameter")
    choice, probs = _choice_of(choice_block, order)
    tilt = _score_of(tilt_block)
    fields = (
        ("xau_tilt", choice_block, choice, order),
        ("xau_tilt__parameter", tilt_block, tilt, ()),
    )
    remember: list[tuple[str, Any, str | None]] = []
    reasons: list[str] = []
    for key, block, value, field_order in fields:
        reason = _miss(block, value, field_order, receipt_error)
        remember.append((key, value, reason))
        if reason:
            reasons.append(reason)
    return {
        "choice": choice,
        "probabilities": probs,
        "parameter": tilt,
        "error": reasons[0] if reasons else None,
    }, remember


def _land_order(sites: Mapping[str, Any], bound: Any) -> list[dict[str, Any]] | None:
    """Sites in order, out to the returned piece bound. A missing bound stays missing."""

    number = _number(bound)
    if number is None:
        return None
    ordered: list[dict[str, Any]] = []
    for gate_id in SITE_ORDER:
        if len(ordered) >= number:
            break
        site = sites.get(gate_id)
        ordered.append(dict(site) if isinstance(site, Mapping) else {"gate_id": gate_id})
    return ordered


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = []
    if loaded is None:
        loaded = []
    payload["prior_outcomes"] = loaded
    try:
        call = evaluate_fn
        if call is None:
            from .jev_client import evaluate

            call = evaluate
        receipt = call(payload, questions=dict(questions), merge_sleeve=False, model=MODEL)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return payload, {}, type(exc).__name__
    if not isinstance(receipt, dict):
        return payload, {}, "evaluate_not_a_dict"
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        error = receipt.get("error") or receipt.get("skipped") or "empty"
    elif receipt.get("ok") is False:
        error = receipt.get("error") or receipt.get("skipped") or "post_failed"
    if error in (None, ""):
        return payload, answers, None
    return payload, answers, str(error)


def evaluate_host_piece(
    state: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One ask. Site objects stay nested. A miss stays unset."""

    posted = _scrub(dict(state or {}))
    if not isinstance(posted, dict):
        posted = {}
    posted["model"] = MODEL
    posted["tree"] = _scrub(_tree_facts())
    questions = _questions(_levels(posted))
    payload, answers, error = _post(posted, questions, evaluate_fn)
    sites: dict[str, Any] = {}
    remember: list[tuple[str, Any, str | None]] = []
    for gate_id in SITE_ORDER:
        row, pairs = _read_site(answers, gate_id, error)
        sites[gate_id] = row
        remember.extend(pairs)
    apply_xau, xau_pairs = _read_xau(answers, error)
    remember.extend(xau_pairs)
    piece_block = answers.get("host_piece_loop")
    piece_loop = _score_of(piece_block)
    piece_reason = _miss(piece_block, piece_loop, (), error)
    remember.append(("host_piece_loop", piece_loop, piece_reason))
    _remember(payload, remember)
    model = MODEL
    return {
        "schema": SCHEMA,
        "model": model,
        "never_place": True,
        "broker_effect": False,
        "do_not_wholesale_copy_book_owner": True,
        "piece_loop": piece_loop,
        "land_order": _land_order(sites, piece_loop),
        "sites": sites,
        "apply": {
            "f5_xau_flow_alignment_size_tilt": apply_xau,
            "F5-JEV-004": {
                "choice": sites["F5-JEV-004"].get("choice"),
                "tilt": sites["F5-JEV-004"].get("tilt"),
            },
        },
        "error": error if piece_loop is None and error else None,
    }


def github_live_sites(
    state: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Each site's lines are the scores on this ask. A miss does not scan one back in."""

    return evaluate_host_piece(state, evaluate_fn=evaluate_fn)["sites"]


def vps_land_plan(
    state: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """The land piece. Nested sites. The returns decide. This does not send."""

    return evaluate_host_piece(state, evaluate_fn=evaluate_fn)


def _install_skip_choices() -> None:
    try:
        from .skip_choices import install

        install()
    except Exception:
        return


_install_skip_choices()
