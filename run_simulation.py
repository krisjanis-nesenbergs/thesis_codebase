""" Run app_simulation """
#python3 run_simulation.py --config=3.3.3.3.3.3 --start=1 --count=2

from experiment import __main__

import argparse

parser = argparse.ArgumentParser(description='Experiment argument acquisition:')
parser.add_argument('--config', metavar='string', required=True,
                    help='The config in form 3.3.3.3.3.3')
parser.add_argument('--start', type = int, metavar='number', required=True,
                    help='From which experiment number to start? 0 = first line of the file')
parser.add_argument('--count', type=int, metavar='number', required=True,
                    help='how many experiments to run?')
args = parser.parse_args()
__main__.main(config=args.config, start=args.start, count=args.count)
