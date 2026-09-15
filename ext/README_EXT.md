# Extended simulation run (2026)

An additive second stage to the simulation study published in [1]. Nothing in the original run is
modified: the code in `experiment/`, `generator/`, `tessellator/` and `clothing/` is used unchanged,
and `simulation/`, `results/` and `results/integrated_results.csv` are untouched.

## Why

In the initial run the wire segment length `A` was drawn from `{20, 40, 80, 160}` mm. For three of
the five jumper lengths the best configuration was found at `A = 160` mm, the upper edge of that
set, so it was established as the best of those tested rather than as optimal. This run extends the
range to 714 mm, adds the intermediate values the original grid skipped, and locates the boundary at
which each pattern stops meeting the reachability requirement.

## Layout

| | initial run (2023) | extended run (2026) |
|---|---|---|
| configurations | `simulation/` | `simulation_ext/` |
| results | `results/` | `results_ext/<tier>/` |
| aggregated csv | `results/integrated_results.csv` | `results_ext/integrated_results_ext.csv` |
| experiment IDs | 1 – 44200 | 900001 upward |
| filename width | 5 digits | 7 digits |

Every extended result file carries a `_run_meta` block recording the run, the tier, the Monte Carlo
depth actually used, the git commit and the runtime, so a single result file identifies its own
provenance without reference to its directory. Tiers 1 and 2 share an ID base, so the unique key
across the study is the pair (tier, experiment ID).

The two aggregated tables share a column schema and concatenate directly:

```python
a = pd.read_csv("results/integrated_results.csv")
b = pd.read_csv("results_ext/integrated_results_ext.csv")
a["CFG_run"], a["CFG_tag"], a["CFG_mc"] = "initial_2023", "", 100000
df = pd.concat([a, b], ignore_index=True)
```

## Tiers

Eight batches, 41988 configurations, all at the original Monte Carlo depth of 100 sinks x 1000 sensors.

| tier | patterns | wire segment lengths | jumper lengths | configurations |
|---|---|---|---|---|
| tier1 | 3 finalists | 125–714 mm | 80, 160 | 6120 |
| tier2 | 3 finalists | 240–640 mm | 10–160 | 10200 |
| tier3 | 3 finalists | 50–240 mm, paired | 20–160 | 6120 |
| tier4 | 10 non-finalists | 100, 125, 206 mm | 80, 160 | 10200 |
| tier5 | 3 finalists | frontier bisection | 20–160 | 3740 |
| tier5b | 3 finalists | frontier bisection, fine | 10, 20 | 1358 |
| tier6 | 4.4.4.4 only | 165–198 mm | 80, 160 | 1190 |
| tier7 | 6.6.6, 4.6.12.a | 50-145 mm| 20-160 | 3060 |

* Tier5b actually had 1360 configurations but two of them could not be calculated due to small number limits in simulation 

Exact pairs per tier are in `TIERS` in `gen_ext_configs.py` and in
`simulation_ext/run_manifest_<tier>.json`.

## Running

Requires Python 3.10 with `shapely < 2`. Shapely 2 removed iteration over multi-part geometries,
which silently breaks boundary clipping in `tessellator.py` rather than raising.

```bash
python3 -m venv venv_ext && source venv_ext/bin/activate
pip install "shapely>=1.7,<2.0" "numpy<2.0" matplotlib pandas

python3 ext/gen_ext_configs.py --tier=tier1
bash ext/multi_run_ext.sh tier1 30 100 1000
python3 ext/aggregate_ext.py
```

`multi_run_ext.sh` takes the total number of worker processes and divides it across the patterns
present in that tier. Workers skip configurations that already have a result file, so an
interrupted run is resumed by repeating the same command.

## Known behaviour

`Experiment.execute_experiment` retries a configuration with regenerated seeds if the tessellation
produces an inconsistent node count. Coarse grids on small garment parts trigger this more often
than fine grids did; no retries occurred in any tier of this run. A retry mutates the sink and seeds
for that configuration, so a retried configuration no longer matches the seeds stored in its config
file. This is inherited behaviour, not introduced here.

`_get_useful_grid_statistics` reports the shortest path and least jumper path useful-jumper columns
in crossed order. No published result uses those columns, but anything computed from them needs the
correction.

## Notes

Configuration generation is seeded and the seed is recorded in each manifest. The original run was
unseeded, so this extension is reproducible in a way the original is not; the difference is
deliberate and recorded.

The code in this directory was written with the assistance of Claude (Anthropic). The simulation
code it calls, the clothing dataset and the results are the author's own.

[1] K. Nesenbergs, "Choosing the Wiring Pattern for Universal Interconnect Fabric in Body Sensor
Network Clothing", IEEE BSN 2026.
