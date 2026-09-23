"""Shared loader for the scripts/f5_harvest modules (scripts/ is not a package)."""
import importlib.util
import os
import sys

import pytest

_SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "f5_harvest")


def load_script(name):
    path = os.path.abspath(os.path.join(_SCRIPTS, name + ".py"))
    spec = importlib.util.spec_from_file_location("f5_harvest_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def builder():
    return load_script("build_f5_outcome_ledger")


@pytest.fixture(scope="session")
def summarizer():
    return load_script("summarize_f5_daily")


@pytest.fixture(scope="session")
def tripwires():
    return load_script("f5_tripwires")
