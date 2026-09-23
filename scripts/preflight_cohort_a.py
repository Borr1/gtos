import json
import sys

sys.path.insert(0, r"host-local\redacted_host\repo")
from src.components.ultimate_book.sleeves.registry import DISPLACEMENT_BUILT, active_specs
from src.components.ultimate_book.admission import DISPLACEMENT_REGISTRY
from src.components.ultimate_book.execution_packets import SLEEVE_EXIT_PROFILES

none_names = [s.tag for s in active_specs(None)]
dsp_none = [n for n in none_names if n.startswith("dsp_")]
tags = (
    "asia_pdl_fade,asian_fade,crypto,dsp_climax_flush_to_96low_then_snap,"
    "dsp_expanding_up_staircase,dsp_london_two_up_into_20high_reverses,energy_agri,idxrev"
).split(",")
armed = [s.tag for s in active_specs(tags)]
clusters = {k: v.cluster for k, v in DISPLACEMENT_BUILT.items()}
print(json.dumps({
    "dsp_on_empty_tags": dsp_none,
    "armed_dsp": [n for n in armed if n.startswith("dsp_")],
    "clusters": clusters,
    "literal_displacement": any(c == "displacement" for c in clusters.values()),
    "adm_clusters": {k: v.asset_class for k, v in DISPLACEMENT_REGISTRY.items()},
    "exits": {k: SLEEVE_EXIT_PROFILES.get(k) for k in DISPLACEMENT_BUILT},
}))
