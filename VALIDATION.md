# Validation Notes

This Mesa implementation preserves the original conceptual mechanisms:
environmental affordances, personal pro/non states, individual learning, social
learning through networks, mutation, movement, and cultural niche construction.
It intentionally excludes nudge, policy-intervention, and consumer-choice
extensions so validation focuses on the NetLogo v1.2.0 model.

Known implementation deviations from the NetLogo v1.2.0 model:

1. Movement is a discrete Moore-neighbour random walk on a toroidal grid. The
   NetLogo model uses continuous headings with `rt random 45`, `lt random 45`,
   and `fd 1`.
2. Behaviour attempts are guarded by `max_behavior_attempts` to prevent rare
   infinite loops. NetLogo loops until an agent behaves.
3. The Klemm-Eguiluz network generator is an approximation of the NetLogo
   procedure and has not been proven byte-for-byte equivalent.
4. Random number streams are Mesa/Python/NumPy streams, so exact trajectory
   identity with NetLogo should not be expected even with comparable seeds.
5. This port reports affordance share in the model data collector; the NetLogo
   BehaviorSpace experiments often report a pro-affordance patch count.

To compare against NetLogo outputs, place BehaviorSpace CSV files in
`original_outputs/` and run:

```bash
python scripts/validate_against_netlogo.py
```

The validation script reads matching parameter columns where present, runs Mesa
with comparable settings, and writes metric differences to `outputs/validation/`.

## EV extension: calibration and sensitivity workflow

The EV extension is validated as a separate scenario layer on top of the
affordance model. Scenario sweeps use:

```bash
python scripts/run_ev_experiments.py --scenarios no_policy subsidy --seeds 1 2 3 --steps 200
```

This writes `outputs/ev_experiment_curves.csv`,
`outputs/ev_experiment_summary.csv`, and `outputs/ev_adoption_curves.png`.

Empirical adoption targets can be supplied as a CSV with columns `step` and
`ev_adoption_share`:

```bash
python scripts/run_ev_experiments.py --scenarios subsidy --seeds 1 2 3 --targets targets.csv
```

The summary table then includes `target_rmse`, computed on overlapping steps.

One-at-a-time sensitivity sweeps vary one parameter at a time while holding the
other overrides fixed:

```bash
python scripts/run_ev_experiments.py --sweep adoption_threshold=0.25,0.30,0.34,0.40 --sweep subsidy=0,4000,8000,12000 --sweep-scenario colleague_baseline --seeds 1 2 3 --steps 200
```

Sensitivity mode writes `outputs/ev_sensitivity_summary.csv` plus one plot per
parameter, for example `outputs/ev_sensitivity_subsidy.png`.

Reproducibility is handled through explicit seeds, deterministic default EV
mechanisms, and same-seed regression tests in `tests/`. The optional stochastic
or feedback mechanisms are tested separately so the default baseline remains
stable.

Still open:

1. Calibration against real EV adoption data.
2. Charger reliability, charger types, and realistic geography.
3. Used-vehicle market representation.
