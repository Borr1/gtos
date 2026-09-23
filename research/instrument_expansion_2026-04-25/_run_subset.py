"""Test runner — analyzes a single instrument to validate pipeline."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

# Rename the analysis module to a Python-importable name in-memory.
import importlib.util

spec = importlib.util.spec_from_file_location(
    "decay_analysis_mod",
    Path(__file__).parent / "02_decay_analysis.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["decay_analysis_mod"] = mod
spec.loader.exec_module(mod)

# Override INSTRUMENTS for sanity test
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--symbols", nargs="+", default=None)
args = parser.parse_args()
if args.symbols:
    mod.INSTRUMENTS = args.symbols

mod.main()
