""" Configuration generator for the extended simulation run (2026)

Generates experiment configurations for the extended wire segment length study. Additive to the
original 2023 run - no original configuration or result file is modified.
"""

__author__ = "Krisjanis Nesenbergs"
__version__ = "1.0"
__contact__ = 'krisjanis.nesenbergs@edi.lv'
__copyright__ = "Copyright 2026, Krisjanis Nesenbergs"
__license__ = "GPL"
__status__ = "Production"

import os
import sys
sys.path.insert(0, os.getcwd())

import logging
logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("=[%(levelname)s @ %(filename)s (L=%(lineno)s) F=%(funcName)s() ]= %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

from clothing.clothes_list import ClothesList
from generator import ExperimentConfiguration
from generator import GeneratorConstants
from generator.adjusted_clothing_item import AdjustedClothingItem

import json
import os
import random

FINALISTS = ["3.3.3.3.3.3", "4.4.4.4", "3.6.3.6"]

NON_FINALISTS = ["3.12.12", "3.3.3.3.6", "3.3.3.4.4", "3.3.4.3.4", "3.4.6.4",
                 "4.6.12", "4.6.12.a", "4.6.12.b", "4.8.8", "6.6.6"]


def cross(wire_lengths, jumper_lengths):
    # Wire segment length varies slowest, matching the original generator nesting
    return [(a, j) for a in wire_lengths for j in jumper_lengths]


# Each tier defines the patterns, the (wire segment length, jumper length) pairs per pattern and
# the experiment ID base. Tiers 1 and 2 share base 900000 as originally generated, so the unique
# key across the whole study is the pair (tag, experiment ID), recorded in every result file.
TIERS = {
    "tier1": {
        # Wire segment lengths the infinite plane approximation predicts to be optimal
        "patterns": FINALISTS,
        "pairs": cross([125.0, 206.0, 249.0, 357.0, 412.0, 714.0], [80.0, 160.0]),
        "id_base": 900000,
        "seed": 20260913
    },
    "tier2": {
        # Regular sweep beyond the original 160 mm ceiling
        "patterns": FINALISTS,
        "pairs": cross([240.0, 320.0, 480.0, 640.0], [10.0, 20.0, 40.0, 80.0, 160.0]),
        "id_base": 900000,
        "seed": 20260913
    },
    "tier3": {
        # Short jumper rows, never tested outside the original grid, plus frontier brackets
        "patterns": FINALISTS,
        "pairs": [(50.0, 20.0), (60.0, 20.0), (90.0, 20.0), (100.0, 20.0),
                  (100.0, 40.0), (125.0, 40.0), (180.0, 40.0), (206.0, 40.0),
                  (180.0, 80.0), (224.0, 80.0),
                  (224.0, 160.0), (240.0, 160.0)],
        "id_base": 930000,
        "seed": 20260914
    },
    "tier4": {
        # Non-finalist patterns at wire segment lengths the original study skipped
        "patterns": NON_FINALISTS,
        "pairs": cross([100.0, 125.0, 206.0], [80.0, 160.0]),
        "id_base": 960000,
        "seed": 20260914
    },
    "tier5": {
        # Frontier bisection - two probes inside each known pass/fail bracket
        "patterns": FINALISTS,
        "pairs": {
            "3.3.3.3.3.3": [(84.0, 20.0), (88.0, 20.0), (167.0, 40.0), (173.0, 40.0),
                            (265.0, 80.0), (290.0, 80.0), (370.0, 160.0), (390.0, 160.0)],
            "4.4.4.4":     [(53.0, 20.0), (56.0, 20.0), (90.0, 40.0), (96.0, 40.0),
                            (168.0, 80.0), (174.0, 80.0), (243.0, 160.0), (246.0, 160.0)],
            "3.6.3.6":     [(52.0, 40.0), (60.0, 40.0), (95.0, 80.0), (110.0, 80.0),
                            (175.0, 160.0), (190.0, 160.0)]
        },
        "id_base": 980000,
        "seed": 20260915
    },
    "tier5b": {
        # Fine grid frontier brackets, deferred from tier5 because of their cost
        "patterns": FINALISTS,
        "pairs": {
            "3.3.3.3.3.3": [(46.0, 10.0), (54.0, 10.0)],
            "4.4.4.4":     [(24.0, 10.0), (28.0, 10.0)],
            "3.6.3.6":     [(13.0, 10.0), (16.0, 10.0), (28.0, 20.0), (33.0, 20.0)]
        },
        "id_base": 990000,
        "seed": 20260915
    },
    "tier6": {
        # Closes the gap between 160 and 206 mm wire segment length, where the q = 90 %
        # coverage frontier falls for both the 80 mm and 160 mm jumper lengths but no
        # configuration had been simulated to verify it
        "patterns": ["4.4.4.4"],
        "pairs": [(165.0, 80.0), (170.0, 80.0), (176.0, 80.0),
                  (170.0, 160.0), (180.0, 160.0), (190.0, 160.0), (198.0, 160.0)],
        "id_base": 995000,
        "seed": 20260915
    },
    "tier7": {
        # The non-finalist patterns received only the coarse tier 4 sweep, while the three
        # finalists were refined across tiers 3, 5 and 6. Comparing them on that basis would
        # understate what the non-finalists can achieve. Wire consumed per unit coverage at a
        # common cell separates the thirteen patterns into a group of five near the regular
        # tilings and the rest well behind; of those five, only 6.6.6 and 4.6.12.a exceed the
        # reachability requirement at that cell. This tier gives those two the same refinement
        # around their frontiers that the finalists received.
        "patterns": ["6.6.6", "4.6.12.a"],
        "pairs": {
            "6.6.6":    [(50.0, 20.0), (55.0, 20.0), (60.0, 20.0),
                         (50.0, 40.0), (55.0, 40.0), (60.0, 40.0),
                         (90.0, 80.0), (110.0, 80.0),
                         (135.0, 160.0), (145.0, 160.0)],
            "4.6.12.a": [(50.0, 20.0), (60.0, 20.0),
                         (50.0, 40.0), (60.0, 40.0),
                         (90.0, 80.0), (110.0, 80.0),
                         (115.0, 160.0), (130.0, 160.0)]
        },
        "id_base": 996000,
        "seed": 20260916
    }

}


def main(tier="tier1"):
    logger.critical("Generating configurations for ``%s``", tier)
    console_handler.setLevel(logging.INFO)

    DATA_FILE = "01_clothing_data_joined_L_parts"
    DATA_FOLDER = "./data/"
    OUTPUT_FOLDER = "./simulation_ext/"

    spec = TIERS[tier]
    random.seed(spec["seed"])   # The original run was unseeded, this one is reproducible

    _ClothesList = ClothesList(DATA_FOLDER + DATA_FILE).getClothesList()
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    experiment_no = 0
    counts = {}

    for config in spec["patterns"]:
        pairs = spec["pairs"][config] if isinstance(spec["pairs"], dict) else spec["pairs"]
        outfilename = OUTPUT_FOLDER + config + "_" + tier + "_config.json"
        written = 0
        with open(outfilename, "w") as outfile:
            for clothe_id, clothe_item in enumerate(_ClothesList):
                for size in GeneratorConstants.SIZES:
                    adjusted = AdjustedClothingItem(clothe_id, clothe_item, size=size)
                    for node_distance, joint_radius in pairs:
                        adjusted.regenerate_sink_and_seeds()
                        experiment_no = experiment_no + 1
                        cfg = ExperimentConfiguration(spec["id_base"] + experiment_no, adjusted,
                                                      config, node_distance, joint_radius)
                        outfile.write(cfg.serialize() + "\n")
                        written = written + 1
        counts[config] = written
        print("Wrote " + str(written) + " configurations: " + outfilename)

    manifest = {
        "tag": tier,
        "seed": spec["seed"],
        "id_base": spec["id_base"],
        "patterns": spec["patterns"],
        "pairs_mm": spec["pairs"] if isinstance(spec["pairs"], dict) else [list(p) for p in spec["pairs"]],
        "clothing_designs": len(_ClothesList),
        "sizes": list(GeneratorConstants.SIZES),
        "configurations_per_pattern": counts,
        "total_configurations": sum(counts.values())
    }
    with open(OUTPUT_FOLDER + "run_manifest_" + tier + ".json", "w") as outfile:
        json.dump(manifest, outfile, indent=4)

    print("END: " + tier + ", " + str(sum(counts.values())) + " configurations")


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Extended run configuration generation:')
    parser.add_argument('--tier', metavar='string', required=True,
                        help='Which tier to generate: ' + ", ".join(TIERS))
    args = parser.parse_args()
    main(tier=args.tier)
