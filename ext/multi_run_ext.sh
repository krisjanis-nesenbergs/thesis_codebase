#!/bin/bash

# Parallel launcher for the extended run. Unlike multi_run.sh the patterns are not fixed, since
# tiers cover different pattern sets, so they are discovered from the config filenames.
# The second parameter is the TOTAL number of processes, divided evenly across the patterns found.
#
# Run with params: tier1 30 100 1000
# Workers skip configurations that already have a result file, so this is safe to re-run.
# Progress: find ./results_ext/tier1 -name "*.json" | wc -l
# Stop all:  pkill -f "ext/run_ext.py"

TIER=$1
TOTAL=${2:-30}
SINKS=${3:-100}
SENSORS=${4:-1000}

PATTERNS=()
for f in ./simulation_ext/*_"${TIER}"_config.json; do
    [ -e "$f" ] || continue
    b="${f##*/}"
    PATTERNS+=("${b%_${TIER}_config.json}")
done

if [ ${#PATTERNS[@]} -eq 0 ]; then
    echo "No config files for tier ${TIER} - run gen_ext_configs.py first"
    exit 1
fi

PER=$(( TOTAL / ${#PATTERNS[@]} ))
[ $PER -lt 1 ] && PER=1
LOGDIR="./results_ext/${TIER}/logs"
mkdir -p "$LOGDIR"

echo "Tier ${TIER}: ${#PATTERNS[@]} patterns, ${PER} workers each, Monte Carlo ${SINKS}x${SENSORS}"

for PATTERN in "${PATTERNS[@]}"; do
    LINES=$(wc -l < "./simulation_ext/${PATTERN}_${TIER}_config.json")
    BLOCK=$(( (LINES + PER - 1) / PER ))
    for ((w=0; w<PER; w++)); do
        START=$(( w * BLOCK ))
        [ $START -ge $LINES ] && break
        nohup python3 ext/run_ext.py --config=$PATTERN --tier=$TIER --start=$START --count=$BLOCK --sinks=$SINKS --sensors=$SENSORS > "${LOGDIR}/${PATTERN}_${w}.log" 2>&1 &
    done
done

wait
echo "END: ${TIER}"
