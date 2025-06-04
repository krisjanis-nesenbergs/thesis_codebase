""" Main entry point for Clothing Data Experiment console application

The goal of this application is to take parameters for simulation and run specific simulation configs headless
"""

__author__ = "Krisjanis Nesenbergs"
__version__ = "1.0"
__contact__ = 'krisjanis.nesenbergs@edi.lv'
__copyright__ = "Copyright 2017, Krisjanis Nesenbergs"
__license__ = "GPL"
__status__ = "Producton" #Finished "Prototype", "Development" for this

import logging
logger = logging.getLogger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("=[%(levelname)s @ %(filename)s (L=%(lineno)s) F=%(funcName)s() ]= %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)    

from .experiment import Experiment
from generator import ExperimentConfiguration
from generator import GeneratorConstants

import json
import os
import sys

sys.setrecursionlimit(8000)

#import sys #For parameter processing

def main(config = "3.3.3.3.3.3", start = 0, count = 2):
    logger.critical("Starting experiments with config ``%s`` starting with %d, for %d iterations", config, start, count)
    console_handler.setLevel(logging.INFO)

    #Some simulation constants:
    DATA_FILE = "01_clothing_data_joined_L_parts"
    DATA_FOLDER = "./data/" # if running from experiment folder, then path is ../data, but running from top level with python3 -m experiment --config=a --start=1 --count=2 it is ./data

    from clothing.clothes_list import ClothesList
    #import sys, os
    #sys.path.insert(1, os.path.join(sys.path[0], '..'))
    _ClothesList = ClothesList(DATA_FOLDER + DATA_FILE).getClothesList() # List of ClothingItem

    #print(_ClothesList)
    EXPERIMENT_CONFIG_FILE = "./simulation/"+config+"_config.json"
    EXPERIMENT_RESULT_FOLDER = "./results/"

    #import pprint 
    #pp = pprint.PrettyPrinter(indent=4, depth=None, sort_dicts = False)

    CFG = {
        "3.3.3.3.3.3": 0,
        "3.3.3.3.6": 3400,
        "3.3.3.4.4": 6800,
        "3.3.4.3.4": 10200,
        "3.4.6.4": 13600,
        "3.6.3.6": 17000,
        "3.12.12": 20400,
        "4.4.4.4": 23800,
        "4.6.12": 27200,
        "4.8.8": 30600,
        "6.6.6": 34000,
        "4.6.12.a": 37400,
        "4.6.12.b": 40800
    }

    start=start+CFG[config]

    #GeneratorConstants.SOURCE_POINTS = 2 #TODO REMOVE LATER

    



    #precision_decimals = 6
    #precision_constant = 1*10**(-precision_decimals)
    with open(EXPERIMENT_CONFIG_FILE) as infile:
        iii=0
        for line in infile:
            if True:
                rescfg = ExperimentConfiguration()
                rescfg.deserialize(line, _ClothesList)

                if(rescfg.ID<start):
                    continue
                if(rescfg.ID>=start+count):
                    break
                outfilename = EXPERIMENT_RESULT_FOLDER+config+"/"+str(rescfg.ID).zfill(5)+".json"
                os.makedirs(os.path.dirname(outfilename), exist_ok=True)
                ex = Experiment()
                res = ex.execute_experiment(rescfg, False, pretxt = "[ID = "+str(rescfg.ID)+"]["+config+"]")

                with open(outfilename,"w") as outfile:
                    json.dump(res , outfile, indent=4)
            iii=iii+1

            #if iii==6:
            #    break

    print("END: ", config)



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Experiment argument acquisition:')
    parser.add_argument('--config', metavar='string', required=True,
                        help='The config in form 3.3.3.3.3.3')
    parser.add_argument('--start', type = int, metavar='number', required=True,
                        help='From which experiment number to start? 0 = first line of the file')
    parser.add_argument('--count', type=int, metavar='number', required=True,
                        help='how many experiments to run?')
    args = parser.parse_args()
    main(config=args.config, start=args.start, count=args.count)

    #main()