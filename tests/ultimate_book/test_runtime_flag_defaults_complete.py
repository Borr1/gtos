"""Session AU (B1556) — a runtime flag read without a documented default is a silent live outage.

THE DEFECT CLASS, MEASURED BY SESSION AR BEFORE IT WAS FILED

`bridge._bool(cfg, key)` is `config_bool_value(cfg.get(key, DEFAULT_CONFIG[key]), DEFAULT_CONFIG[key])`
(`bridge.py:224-225`). If `key` is absent from `DEFAULT_CONFIG`, that expression raises `KeyError` --
and it raises it INSIDE `evaluate_vnext_ultimate_book_admission`, which `book_engine.evaluate` catches
as `engine_exception` because the book must never break the live path. So the failure mode is not a
crash and not a traceback anybody sees. It is **an armed book that stands down every tick with a
perfectly healthy heartbeat**, on two funded accounts, until somebody reads the sized-unit count.

AR hit it on the first run of `--vol-level-tilt` and filed the fix as a repair row rather than
building it (`SESSION_AR_..._RESULT.md` §0, handoff item 4: *"One AST walk, no market data. It prevents
the most expensive class of defect here ... and makes it impossible rather than fixed once."*). This is
that AST walk.

WHY AST AND NOT A CALL

Calling `evaluate` with a stripped config would test one path through one function. The keys are read
across ~40 call sites in two modules and a future one will be added by a session that has never heard
of this test. So the test DISCOVERS the resolvers (any function that indexes its module's
`DEFAULT_CONFIG` by a parameter) and then checks every literal key handed to one. Adding a new
resolver, or a new key, is covered without touching this file.

SCOPE. Two modules index a `DEFAULT_CONFIG` by key and can therefore raise:
`ultimate_book/bridge.py` and `ultimate_book/convergence_advisory.py`. `replay_policy/sleeve_book.py`
reads the same defaults but through `.get(key, DEFAULT.get(key, False))`, which cannot raise -- and is
therefore *fail-open* rather than fail-closed, so it is asserted separately below rather than trusted.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import pathlib

import pytest

MODULES = (
    "src.components.ultimate_book.bridge",
    "src.components.ultimate_book.convergence_advisory",
)


def _tree(mod):
    return ast.parse(pathlib.Path(inspect.getsourcefile(mod)).read_text(encoding="utf-8"))


def _resolver_names(tree: ast.Module) -> set[str]:
    """Functions that index `DEFAULT_CONFIG` by one of their own parameters.

    That is the signature of the dangerous shape: the key is data, so the KeyError is reachable from a
    caller rather than visible at the subscript. A function that indexes it by a string LITERAL is
    checked directly instead (see `_literal_keys`).
    """
    found: set[str] = set()
    for fn in (n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
        params = {a.arg for a in list(fn.args.args) + list(fn.args.kwonlyargs)}
        for sub in ast.walk(fn):
            if (isinstance(sub, ast.Subscript)
                    and isinstance(sub.value, ast.Name) and sub.value.id == "DEFAULT_CONFIG"
                    and isinstance(sub.slice, ast.Name) and sub.slice.id in params):
                found.add(fn.name)
                break
    return found


def _literal_keys(tree: ast.Module, resolvers: set[str]) -> set[str]:
    """Every string literal that reaches a resolver, plus every literal `DEFAULT_CONFIG["..."]`."""
    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if fname in resolvers:
                for arg in list(node.args) + [k.value for k in node.keywords]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        keys.add(arg.value)
        elif (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name) and node.value.id == "DEFAULT_CONFIG"
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str)):
            keys.add(node.slice.value)
        elif (isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "get"
                and isinstance(getattr(node.func, "value", None), ast.Name)
                and node.func.value.id == "cfg"
                and len(node.args) == 2
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and isinstance(node.args[1], ast.Subscript)
                and getattr(node.args[1].value, "id", None) == "DEFAULT_CONFIG"):
            keys.add(node.args[0].value)
    return keys


@pytest.mark.parametrize("modname", MODULES)
def test_the_walk_finds_the_resolvers_it_is_meant_to_find(modname):
    """A discovery test that discovers nothing passes vacuously. Assert it found something."""
    mod = importlib.import_module(modname)
    resolvers = _resolver_names(_tree(mod))
    assert resolvers, f"{modname}: no DEFAULT_CONFIG resolver found — the walk has stopped working"
    if modname.endswith("bridge"):
        assert {"_bool", "_str", "_str_tuple"} <= resolvers


@pytest.mark.parametrize("modname", MODULES)
def test_every_runtime_key_read_has_a_documented_default(modname):
    """The property: no key can be read that `DEFAULT_CONFIG` does not answer for.

    A failure here is not a style complaint. It is the KeyError that stands an armed book down every
    tick while `authority_gates_ON=True`, the heartbeat is healthy and the log is clean.
    """
    mod = importlib.import_module(modname)
    tree = _tree(mod)
    keys = _literal_keys(tree, _resolver_names(tree))
    assert keys, f"{modname}: no literal keys found — the walk has stopped working"
    missing = sorted(k for k in keys if k not in mod.DEFAULT_CONFIG)
    assert not missing, (
        f"{modname}: {len(missing)} runtime key(s) are read but carry no DEFAULT_CONFIG entry: "
        f"{missing}. An absent key raises KeyError inside the admission bridge, which "
        f"book_engine.evaluate catches as `engine_exception` — the armed book then stands down "
        f"every tick with a healthy heartbeat. Add the default beside the others."
    )


def test_the_negative_case_is_actually_detected():
    """The test above must fail when the defect is present, or it proves nothing. Synthetic module,
    the exact shape of `bridge._bool` plus one key with no default."""
    src = (
        "DEFAULT_CONFIG = {'ultimate_book_documented': False}\n"
        "def _bool(cfg, key):\n"
        "    return bool(cfg.get(key, DEFAULT_CONFIG[key]))\n"
        "def evaluate(cfg):\n"
        "    return _bool(cfg, 'ultimate_book_documented'), _bool(cfg, 'ultimate_book_forgotten')\n"
    )
    tree = ast.parse(src)
    resolvers = _resolver_names(tree)
    assert resolvers == {"_bool"}
    keys = _literal_keys(tree, resolvers)
    assert keys == {"ultimate_book_documented", "ultimate_book_forgotten"}
    documented = {"ultimate_book_documented": False}
    assert sorted(k for k in keys if k not in documented) == ["ultimate_book_forgotten"]


def test_the_replay_policy_reader_is_fail_open_and_that_is_recorded():
    """`sleeve_book.py`'s dial reader is `cfg.get(key, DEFAULT.get(key, False))` — it cannot raise, so
    it cannot stand the book down; it silently answers False for an unknown key instead. That is the
    OPPOSITE failure (a research dial reading off when it was meant to be on) and it is fine in the
    replay lane, but it means the guarantee above does not extend there. Pinned so a future reader
    does not assume one rule covers both lanes."""
    from src.research_infra.replay_policy import sleeve_book
    src = inspect.getsource(sleeve_book)
    assert "_BRIDGE_DEFAULT_CONFIG.get(key, False)" in src
    #: and every dial key the replay policy declares IS in the bridge's defaults anyway, so the two
    #: lanes agree today even though only one of them is enforced by construction.
    from src.components.ultimate_book.bridge import DEFAULT_CONFIG, REQUIRED_DIAL_KEYS
    assert set(REQUIRED_DIAL_KEYS) <= set(DEFAULT_CONFIG)
    assert set(sleeve_book.SleeveBookPolicy.DIAL_KEYS) == set(REQUIRED_DIAL_KEYS), (
        "bridge.REQUIRED_DIAL_KEYS and SleeveBookPolicy.DIAL_KEYS are deliberately identical "
        "(bridge.py:154-158) so the live bridge and the replay policy cannot disagree about what a "
        "complete dial is"
    )
