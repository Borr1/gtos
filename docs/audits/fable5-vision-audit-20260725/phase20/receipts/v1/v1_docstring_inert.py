"""Prove the v1 edits to the two production modules are docstring-only, by AST.

Strip every docstring from both the HEAD-of-lane version and the v1 version and compare the
dumped ASTs. Equal => no executable statement changed => the edit cannot move a number.
"""
import ast, subprocess, sys

TARGETS = ["src/research_infra/walkforward/quote_side.py",
           "src/components/broad_origin_emission_contract.py",
           "tests/test_broad_origin_emission_repairs.py"]
BASE = "5f72e6772"

def strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
               and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree

for p in TARGETS:
    old = subprocess.run(["git", "show", f"{BASE}:{p}"], capture_output=True, text=True).stdout
    new = open(p).read()
    a = ast.dump(strip_docstrings(ast.parse(old)))
    b = ast.dump(strip_docstrings(ast.parse(new)))
    print(f"{p:55s} docstring-stripped AST identical: {a == b}")
