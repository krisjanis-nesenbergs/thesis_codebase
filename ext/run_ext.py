""" Main entry point for the extended Clothing Data Experiment run (2026)

Runs the extended wire segment length simulation. The simulator itself is imported unmodified from
experiment/, so a diff against the original release shows only added files. Monte Carlo depth is
set at runtime rather than by editing GeneratorConstants, and every result file is stamped with a
_run_meta block recording which run produced it.
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

from experiment.experiment import Experiment
from generator import ExperimentConfiguration
from generator import GeneratorConstants

import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

sys.setrecursionlimit(8000)


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def main(config="3.6.3.6", tier="tier1", start=0, count=1, sinks=100, sensors=1000):
    logger.critical("Starting extended experiments with config ``%s`` (%s) starting with %d, for %d iterations",
                    config, tier, start, count)
    console_handler.setLevel(logging.INFO)

    DATA_FILE = "01_clothing_data_joined_L_parts"
    DATA_FOLDER = "./data/"
    EXPERIMENT_CONFIG_FILE = "./simulation_ext/" + config + "_" + tier + "_config.json"
    EXPERIMENT_RESULT_FOLDER = "./results_ext/" + tier + "/"

    # Monte Carlo depth is a module level constant in the original code, set here so the simulator
    # needs no modification. Recorded in _run_meta so any reduced run is self documenting.
    GeneratorConstants.SOURCE_POINTS = sinks
    GeneratorConstants.DESTINATION_POINTS = sensors

    from clothing.clothes_list import ClothesList
    _ClothesList = ClothesList(DATA_FOLDER + DATA_FILE).getClothesList()

    meta_common = {
        "run": "extended_2026",
        "tag": tier,
        "monte_carlo_sinks": sinks,
        "monte_carlo_sensors_per_sink": sensors,
        "monte_carlo_iterations": sinks * sensors,
        "git_commit": git_commit(),
        "python": sys.version.split()[0],
        "host": platform.node()
    }

    with open(EXPERIMENT_CONFIG_FILE) as infile:
        for line_index, line in enumerate(infile):
            if line_index < start:
                continue
            if line_index >= start + count:
                break

            rescfg = ExperimentConfiguration()
            rescfg.deserialize(line, _ClothesList)

            outfilename = EXPERIMENT_RESULT_FOLDER + config + "/" + str(rescfg.ID).zfill(7) + ".json"
            os.makedirs(os.path.dirname(outfilename), exist_ok=True)
            if os.path.exists(outfilename):   # Allows an interrupted run to be resumed
                continue

            pretxt = "[EXT][ID = " + str(rescfg.ID) + "][" + config + "][A=" + str(rescfg.node_distance) + "][J=" + str(rescfg.joint_radius) + "]"

            started = time.time()
            ex = Experiment()
            res = ex.execute_experiment(rescfg, False, pretxt=pretxt)

            meta = dict(meta_common)
            meta["experiment_id"] = rescfg.ID
            meta["pattern"] = rescfg.tessellation_algorithm
            meta["wire_segment_length_mm"] = rescfg.node_distance
            meta["jumper_length_mm"] = rescfg.joint_radius
            meta["clothing_id"] = rescfg.adjusted_clothe.clothing_id
            meta["sex"] = rescfg.adjusted_clothe.sex
            meta["size"] = rescfg.adjusted_clothe.size
            meta["runtime_seconds"] = round(time.time() - started, 1)
            meta["finished_utc"] = datetime.utcnow().isoformat() + "Z"
            res["_run_meta"] = meta

            # Written to a temporary name first so an interrupted run leaves no truncated file
            with open(outfilename + ".part", "w") as outfile:
                json.dump(res, outfile, indent=4)
            os.replace(outfilename + ".part", outfilename)

    print("END: ", config, tier)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Extended experiment argument acquisition:')
    parser.add_argument('--config', metavar='string', required=True,
                        help='The config in form 3.3.3.3.3.3')
    parser.add_argument('--tier', metavar='string', required=True,
                        help='Which tier to run, e.g. tier1')
    parser.add_argument('--start', type=int, metavar='number', required=True,
                        help='From which line of the config file to start? 0 = first line')
    parser.add_argument('--count', type=int, metavar='number', required=True,
                        help='how many experiments to run?')
    parser.add_argument('--sinks', type=int, metavar='number', default=100,
                        help='Monte Carlo sink placements per configuration (original run: 100)')
    parser.add_argument('--sensors', type=int, metavar='number', default=1000,
                        help='Monte Carlo sensor placements per sink (original run: 1000)')
    args = parser.parse_args()
    main(config=args.config, tier=args.tier, start=args.start, count=args.count,
         sinks=args.sinks, sensors=args.sensors)
