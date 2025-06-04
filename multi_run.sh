#!/bin/bash

# You can use top command and press 1 in order to see all processes
# On a 32 thread cpu this script should be run 5 times for best efficiency
# First server run should start with 1, second with 1700 and so on.
# Run with params 1, 101, 201, 301, 401, 501 etc. up to 1601 (the second parameter should allways be 100)
# top -p `pgrep -d "," python` -c

nohup python3 run_simulation.py --config=3.3.3.3.3.3 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=3.3.3.3.6 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=3.3.3.4.4 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=3.3.4.3.4 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=3.4.6.4 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=3.6.3.6 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=3.12.12 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=4.4.4.4 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=4.6.12 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=4.6.12.a --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=4.6.12.b --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=4.8.8 --start=$1 --count=$2 &
nohup python3 run_simulation.py --config=6.6.6 --start=$1 --count=$2 &

