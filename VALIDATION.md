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
`outputs/portugal_ev_stock_share_targets.csv` (Portuguese BEV fleet share,
2010–2024; see `ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md` for sourcing
and caveats) is a ready-made `--targets` file — note it is a **stock/fleet**
share, not the sales/registration share usually quoted in press coverage, so
compare it against `ev_adoption_share`, not a new-registrations metric.

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

1. Charger reliability, charger types, and realistic geography.
2. Used-vehicle market representation.
3. Re-running the published sensitivity sweeps (subsidy, fuel price, charger
   expansion) with multiple seeds and confidence bands — the current draft
   figures are single-seed runs and some of the reported non-monotonicities
   may be seed noise rather than genuine threshold effects.

## Portugal calibration (2026-07-22)

`EVParams` defaults (`income_mean`, `income_sd`, `income_distribution`,
`ev_purchase_price`, `ice_purchase_price`, `ev_price_learning_model`,
`ev_wright_learning_rate`, `ev_wright_reference_adopters`,
`charger_expansion_rate`, `adoption_threshold`) were recalibrated by a random
+ local-refinement search (`scripts/calibrate_portugal.py`) against the
Portugal BEV fleet-share target (`outputs/portugal_ev_stock_share_targets.csv`,
2010–2024). The `"portugal_2010_2024"` scenario (`EVParams.from_scenario`)
additionally applies the calibrated `subsidy_schedule` and the grid/agent
scale the search was run at:

```bash
python scripts/run_ev_experiments.py --scenarios portugal_2010_2024 --seeds 1 2 3 4 5 6 7 8 9 10 11 12 --steps 14 --targets outputs/portugal_ev_stock_share_targets.csv
```

RMSE ≈ 0.003 (12-seed mean) against target values spanning 0.02%–3.3%. The
model curve tracks the target's near-zero early years and its final-year
level closely, but rises faster than the target through the middle of the
period (a "backlog-then-burst" artifact: agents whose vehicle came up for
replacement early but couldn't yet afford an EV keep re-evaluating every
subsequent step, so a wave of them clears the affordability bar together as
the subsidy ramp and Wright's-law price decline improve conditions, rather
than diffusing as smoothly as the real market did). This is a documented,
understood limitation of the one-shot-per-replacement-cycle mechanism, not a
bug — treat the fit as "right order of magnitude and right endpoints,
smoother in reality than in the model," not an exact reproduction.

**Important scale-dependency**: `charger_expansion_rate` is an absolute
chargers-per-step rate, not scaled to `number_of_agents`, so the fit is tied
to the `"portugal_2010_2024"` scenario's `number_of_agents=4000` on its
60×60 grid. Running the same parameters at a different population size (as
an ad hoc validation during calibration did, at 8,000 agents) changes the
charger-to-population ratio and materially worsens the fit (RMSE ≈ 0.012 at
8,000 agents vs ≈ 0.003 at 4,000) — this is expected, not a discrepancy to
chase, but it means the calibration should not be assumed to hold at an
arbitrary agent count without rescaling infrastructure parameters.

Two existing tests (`test_supply_cap_limits_adoptions_per_step`,
`test_supply_blocked_agents_adopt_later`) explicitly set
`income_budget_share=1.0` to disable the new affordability gate, since they
test the market supply-cap queue in isolation and predate this calibration.

## Model-review fixes (2026-07-22)

Following a review of the model against its own paper description
(`Eva_JorgeNike_versao11.pdf`) and a SOTA literature benchmark
(`ev_adoption_models/SOTA_BENCHMARK_REPORT.md`), the following were
implemented (see `EV_MODEL_DESCRIPTION.md` for full formulas):

- **Fixed**: range-anxiety penalty now discounts by effective charging access
  (`range_anxiety * (1 - effective_access)`), matching the paper's own
  formula — previously it was a constant penalty regardless of access.
- **Fixed**: the paper's "agents cannot spend more than 10% of income on an
  EV" claim is now a real hard gate (`income_budget_share`), replacing an
  additive affordability term that contributed almost no heterogeneity.
- **Simplified**: `price_sensitivity`/`peer_sensitivity` are now sampled
  directly in `[0.5, 1.5]` instead of `0.5 + U(0,1)` — identical
  distribution, simpler equations.
- **Fixed**: initial `vehicle_age` is staggered below each agent's own
  `replacement_interval` by default, removing a synchronized-evaluation
  artifact at step 1 (opt out with `stagger_initial_vehicle_age=False`).
- **Added** (all opt-in, default-preserving): Wright's-law price-learning
  model as an alternative to the linear proxy; discounted TCO
  (`discount_rate`); lognormal income option; income-correlated home-charging
  access; per-step subsidy/fuel-price/electricity-price schedules.

88 tests pass (`pytest`), up from 69 before this round.
