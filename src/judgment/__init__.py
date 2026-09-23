"""Judgment package.

A missing spine export stays empty. The module object stays the module.
This import does not stop place_apply.
"""

try:
    from . import nineteen as nineteen
except Exception:  # noqa: BLE001 — sibling imports, including place_apply, must survive
    nineteen = None


def _pulled(name: str):
    module = nineteen
    if module is None:
        return None
    return getattr(module, name, None)


DENOMINATOR = _pulled("DENOMINATOR")
OTHER = _pulled("OTHER")
ROLES = _pulled("ROLES")
SEED_ROLES = _pulled("SEED_ROLES")
checksum = _pulled("checksum")
digit_fold = _pulled("digit_fold")
digit_sum = _pulled("digit_sum")
divides = _pulled("divides")
fold = _pulled("fold")
length = _pulled("length")
letter_count = _pulled("letter_count")
letter_total = _pulled("letter_total")
product = _pulled("product")
product_denominator = _pulled("product_denominator")
product_other = _pulled("product_other")
quantity = _pulled("quantity")
quantity_questions = _pulled("quantity_questions")
quantity_state = _pulled("quantity_state")
residue = _pulled("residue")
score = _pulled("score")
seed_mix = _pulled("seed_mix")
shares_denominator = _pulled("shares_denominator")
total = _pulled("total")
write_import_stamp = _pulled("write_import_stamp")
