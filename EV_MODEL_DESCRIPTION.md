# EV Adoption Extension — Model Description

## 1. Purpose

The extension adds household electric-vehicle adoption on top of the
affordance-landscape model of pro-environmental behaviour. Adoption emerges
from total cost of ownership, charging access, environmental attitudes, peer
visibility, and range anxiety, under policy levers (subsidy, fuel price,
charging roll-out) and optional market feedbacks (demand-driven
infrastructure, congestion, supply limits, price learning, social diffusion).

## 2. Entities and state variables

### Space

A toroidal `width x height` Mesa `MultiGrid` shared with the base model. Three
grid-shaped layers matter for the EV extension:

- `affordances` — the base model's pro/non opportunity cells (unchanged).
- `charging_access` — for every cell, `1 / (1 + d / charger_access_decay)`,
  where `d` is the torus Manhattan distance to the nearest charger site.
- `effective_charging_access` — `charging_access` discounted by congestion
  (Section 5.4). With the default infinite `charger_capacity` this is the
  same array object as `charging_access`.

Charger sites are point locations (`model.chargers`); a cell holds at most one
site.

### Agents (`EVConsumerAgent`, subclass of `ConsumerAgent`)

Two positions with distinct meanings:

- `pos` — the moving position in the abstract affordance landscape. Movement
  belongs to the inherited behaviour loop and is *not* residential relocation.
- `home_pos` — the fixed residential location assigned at placement. All EV
  mechanics (charging access reads, spatial peer effects, charger demand)
  use `home_pos`.

Inherited dynamic states: `pro_env`, `non_env` (bounded by per-agent
`lower_bound`/`upper_bound`, updated by affordance learning).

EV attributes sampled at initialization: `income` (normal or lognormal,
`income_distribution`), `annual_mileage` (non-negative normal),
`vehicle_age`, `replacement_interval` (uniform integers — see the staggering
note below), `home_charging_access`, `environmental_concern`, `range_anxiety`
in [0, 1], and `price_sensitivity`, `peer_sensitivity` in **[0.5, 1.5]** (so
the adoption score can multiply by the trait directly rather than the old
`0.5 + trait` expression; the distribution is unchanged, only the
parameterization is simpler). `environmental_concern` and `range_anxiety` are
fixed unless `social_diffusion` is enabled (Section 5.5).

`vehicle_age` is sampled in `[0, replacement_interval - 1]` by default
(`stagger_initial_vehicle_age=True`), so the initial population does not
start with a synchronized replacement burst at step 1. Set
`stagger_initial_vehicle_age=False` to sample `vehicle_age` independently
from `vehicle_age_min`/`vehicle_age_max` instead (useful to force immediate
evaluation in tests/scenarios).

`home_charging_access` optionally correlates with `income`
(`home_charging_income_weight`, default 0.0 = fully independent uniform, as
before): the sampled value is blended toward a logistic percentile of income
around `income_mean`/`income_sd`, reflecting that home-charging access
(private garage/driveway) is not independent of income in practice.

Adoption state: `ev_adopted` (one-shot; adopting resets `vehicle_age` to 0).

Decision telemetry (recorded on every evaluation): `last_adoption_score`,
`last_economic_score`, `last_charging_score`, `last_environmental_score`,
`last_peer_adoption_share`, `last_range_anxiety_penalty`, `last_ev_tco`,
`last_ice_tco`, `last_tco_gap`, `last_adoption_probability`,
`last_affordable` (result of the income-budget gate, Section 5.2), and
`has_evaluated_adoption`.

### Model-level EV state

`chargers` / `_charger_sites`, `effective_ev_price` (learning-curve price,
Section 5.6), per-step market counters (`ev_purchases_this_step`,
`ev_supply_blocked_this_step`), and the `mean_*` diagnostics of Section 7.

## 3. Interpretation: affordance states versus EV traits

The model carries two environmental layers. `pro_env` is the *general*
pro-environmental affordance state (dynamic through asocial/social affordance
learning). `environmental_concern` is the *EV-specific* preference trait. The
EV environmental score blends them with `env_score_pro_env_weight` `w`:

```
environmental_score = (1 - w) * environmental_concern + w * pro_env
```

`w = 0.0` reads the score as a pure EV preference, `w = 1.0` as a pure
affordance state, and the default `w = 0.5` keeps the equal blend.

## 4. Process overview and scheduling

Each model step, in order:

1. Reset the per-step market counters and set `effective_ev_price` from the
   previous step's adoption share.
2. Expand charging infrastructure (`exogenous` or `demand` mode) and update
   `charging_access` if chargers were added.
3. Update `effective_charging_access` (congestion discount; no-op alias when
   capacity is infinite).
4. Agents step in random order. Each agent: runs the inherited affordance
   behaviour loop (move / act / learn); ages its vehicle by one step;
   optionally diffuses perceptions from peer exposure; and, if
   `vehicle_age >= replacement_interval` and not yet adopted, evaluates EV
   adoption (Section 5.1–5.2).
5. Optional base-model mutation; EV metrics update; DataCollector collects.

Row 0 of the DataCollector is collected at construction and already reflects
initial adopters, initial chargers, and the initial effective price.

## 5. Submodels

### 5.1 Adoption score

Evaluated only at replacement time (and re-evaluated every step thereafter
until adoption). With parameters `p`, agent traits, and `effective_access =
effective_charging_access[home_pos]`:

```
ev_tco   = (effective_ev_price - subsidy)+  +  annuity(years, discount_rate) * (mileage * kwh_per_km * electricity_price + ev_maintenance)
ice_tco  = ice_purchase_price               +  annuity(years, discount_rate) * (mileage * l_per_km   * fuel_price       + ice_maintenance)
# annuity(years, 0) == years, so discount_rate = 0.0 (default) reproduces the old flat-multiplication TCO exactly.

tco_score            = (ice_tco - ev_tco) / ice_tco
economic_component   = tco_score * price_sensitivity   # price_sensitivity ~ U(0.5, 1.5)

charging_score        = 0.7 * home_charging_access + 0.3 * effective_access
environmental_score   = (1 - w) * environmental_concern + w * pro_env
peer_share             = share of ev_adopted among peers (Section 5.3)
range_anxiety_penalty  = range_anxiety * (1 - effective_access)  # good charging access discounts the penalty

adoption_score = economic_weight      * economic_component
               + charging_weight      * charging_score
               + environmental_weight * environmental_score
               + peer_weight          * peer_share * peer_sensitivity   # peer_sensitivity ~ U(0.5, 1.5)
               - range_anxiety_weight * range_anxiety_penalty
```

`subsidy`, `fuel_price`, and `electricity_price` are each read from the
model's per-step resolved value (`current_subsidy`, `current_fuel_price`,
`current_electricity_price`; Section 5.6), which equals the flat scalar
parameter unless a `*_schedule` sequence is supplied.

There is no separate "affordability" score term (the previous
`0.1 * min(income/ev_tco, 1)` addition was dropped — with defaults it was
almost constant across agents and added little heterogeneity); the income
constraint is instead enforced as a hard gate, Section 5.2.

### 5.2 Decision rule and market gate

- `adoption_rule = "deterministic"` (default): decide adopt iff
  `adoption_score >= adoption_threshold`. Draws no random numbers.
- `adoption_rule = "logistic"`: decide adopt with probability
  `1 / (1 + exp(-(score - threshold) / adoption_temperature))`
  (`temperature <= 0` degenerates to the step function).

**Income-budget gate.** Independently of the score-based decision, an agent
may adopt only if the average annual cost of EV ownership does not exceed
`income_budget_share` (default 0.10) of its income:
`(ev_tco / tco_years) <= income_budget_share * income`. This implements the
"agents cannot spend more than 10% of income on an EV" affordability rule as
an actual constraint rather than a soft score contribution. The result is
recorded in `last_affordable` regardless of outcome, for telemetry.

A score-positive **and** affordable decision must then pass the market:
`request_ev_purchase()` grants at most `ev_supply_per_step` purchases per
step. Blocked agents remain past their replacement interval and retry on
later steps, so delivery delays emerge from the queue without an explicit
waiting list.

### 5.3 Peer exposure

With `networks` enabled, peers are the agent's social-network neighbours.
Otherwise peers are *residential* neighbours: agents whose `home_pos` lies in
the Moore-1 torus neighbourhood of the agent's `home_pos` (via a static
home-position index, not current grid positions).

### 5.4 Charging infrastructure

- **Access**: nearest-charger torus Manhattan distance mapped through
  `1 / (1 + d / charger_access_decay)`.
- **Expansion** (`charger_expansion_mode`):
  - `"exogenous"` (default): expected `charger_expansion_rate` new random
    sites per step (stochastic fractional rounding).
  - `"demand"`: expected sites per step =
    `charger_expansion_rate * demand_expansion_gain * ev_adoption_share`;
    placement is weighted sampling over free cells by
    `local adopter homes within demand_radius × (1 - charging_access)`,
    falling back to uniform placement when no demand exists. This closes the
    adoption → infrastructure feedback loop.
- **Congestion** (finite `charger_capacity`): within `congestion_radius`
  (Chebyshev, torus), local charger supply `sites × capacity` is compared to
  local adopter-home demand; where demand exceeds supply, perceived access is
  scaled by `supply / demand` (0 where demand exists but no local capacity).
  This is a balancing loop that counteracts the demand-expansion loop.

### 5.5 Social diffusion of perceptions

With `social_diffusion` enabled, each step every agent's peer adoption share
`s` deterministically shifts perceptions:
`range_anxiety -= peer_range_anxiety_relief * s` and
`environmental_concern += peer_concern_gain * s`, clamped to their trait
bounds. This is the only mechanism that makes these two traits dynamic.

### 5.6 Price learning and baseline market state

`effective_ev_price` is floored at `ev_purchase_price * ev_price_floor_share`
and computed by one of two interchangeable models
(`ev_price_learning_model`):

- `"linear"` (default): `ev_purchase_price * (1 - ev_price_learning_rate *
  ev_adoption_share)` — a linear-in-adoption-share proxy; the rate-0 default
  keeps the list price exactly.
- `"wright"`: Wright's-law experience curve keyed on cumulative adopters,
  `ev_purchase_price * (ev_adoption_count / ev_wright_reference_adopters) **
  -b`, with `b = -log2(1 - ev_wright_learning_rate)`. `ev_wright_learning_rate`
  is the fractional cost decline per doubling of cumulative adopters (a
  commonly cited range for Li-ion battery packs is 0.06–0.09; anchoring to
  the wider EV-cost literature may justify a different value).
  `ev_wright_reference_adopters` (default 1) is `N_0`, the adopter count at
  which price equals the list price.

`initial_ev_share` seeds a baseline adopted population at t = 0
(`initial_ev_clustered` clusters it around a random seed household by torus
home distance), giving row 0 an observed market state for calibration.

**Time-varying prices.** `subsidy`, `fuel_price`, and `electricity_price` can
each be overridden with a `*_schedule` sequence (`subsidy_schedule`,
`fuel_price_schedule`, `electricity_price_schedule`), indexed by step number;
once the sequence is exhausted its last value holds for all remaining steps.
`None` (default) keeps the flat scalar parameter. The model resolves these
once per step into `current_subsidy`, `current_fuel_price`,
`current_electricity_price`, which is what agents actually read — this
supports replaying a real policy/price history (e.g. a national subsidy
programme's year-to-year budget swings) instead of a single constant value.

## 6. Parameters (`EVParams`, defaults)

All mechanism switches default to **off/neutral**, so the baseline model is
unchanged by their presence (seeded runs are byte-identical).

| Group | Parameter (default) |
|---|---|
| Run/grid | `width` (201), `height` (201), `max_steps` (20440), `number_of_agents` (100, inherited) |
| Affordance bounds | `lower_bound_mean` (0.2), `lower_bound_sd` (0.05), `upper_bound_mean` (0.8), `upper_bound_sd` (0.05) |
| Charging | `initial_charging_coverage` (0.0), `charger_expansion_rate` (2.0), `charger_expansion_mode` ("exogenous"), `demand_expansion_gain` (4.0), `demand_radius` (2), `charger_access_decay` (1.0), `charger_capacity` (inf), `congestion_radius` (3) |
| Policy/prices | `subsidy` (8000), `fuel_price` (1.8), `electricity_price` (0.25), `subsidy_schedule`/`fuel_price_schedule`/`electricity_price_schedule` (None) |
| Market/supply | `ev_supply_per_step` (inf), `ev_price_learning_model` ("wright", calibrated¹), `ev_price_learning_rate` (0.0, only used if `ev_price_learning_model="linear"`), `ev_price_floor_share` (0.5), `ev_wright_learning_rate` (0.23, calibrated¹), `ev_wright_reference_adopters` (10, calibrated¹) |
| Cost model | `ev_purchase_price` (39500, calibrated¹), `ice_purchase_price` (23000, calibrated¹), `ev_kwh_per_km` (0.18), `ice_liters_per_km` (0.07), `ev_maintenance_cost` (300), `ice_maintenance_cost` (600), `tco_years` (8), `discount_rate` (0.0) |
| Affordability | `income_budget_share` (0.10, calibrated¹) — hard gate, Section 5.2 |
| Initial market | `initial_ev_share` (0.0), `initial_ev_clustered` (False) |
| Decision | `adoption_threshold` (0.085, calibrated¹), `adoption_rule` ("deterministic"), `adoption_temperature` (0.05), weights: economic 0.25 / charging 0.25 / environmental 0.25 / peer 0.15 / range anxiety 0.10, `env_score_pro_env_weight` (0.5) |
| Agent distributions | `income_mean/sd` (9000/9000, calibrated¹), `income_distribution` ("lognormal", calibrated¹), `annual_mileage_mean/sd` (12000/2000), `vehicle_age_min/max` (1/12), `stagger_initial_vehicle_age` (True), `replacement_interval_min/max` (6/14), `home_charging_income_weight` (0.0), trait ranges: `home_charging`/`environmental_concern`/`range_anxiety` (0.0/1.0), `price_sensitivity`/`peer_sensitivity` (0.5/1.5) |
| Social diffusion | `social_diffusion` (False), `peer_range_anxiety_relief` (0.02), `peer_concern_gain` (0.01) |
| Grid/run | `charger_expansion_rate` (1.1, calibrated¹) |

¹ Calibrated against Portugal's 2010–2024 BEV fleet-share series via
`scripts/calibrate_portugal.py` (see `VALIDATION.md` §"Portugal calibration"
and `ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md`), replacing earlier
ad hoc guesses (US-scale income, `ev_price_learning_model="linear"`,
`adoption_threshold=0.34`, `charger_expansion_rate=2.0`,
`ev_purchase_price=35000`, `ice_purchase_price=25000`). The fit
(RMSE ≈ 0.003) is tied to the `"portugal_2010_2024"` scenario's
`number_of_agents=4000` on its 60×60 grid — see the scale-dependency note
below.

Scenario presets live in `SCENARIOS` (`colleague_baseline`, `no_policy`,
`subsidy`, `fuel_price`, `charging_expansion`, `portugal_2010_2024`) and are
constructed with `EVParams.from_scenario(name, **overrides)`; preset values
are provisional and user-tunable except `portugal_2010_2024`, which
reproduces a specific calibration fit (Section 10). Presets do not touch the
mechanism switches.

## 7. Outputs

Model reporters (per step) beyond the base model's nine: `ev_adoption_count`,
`ev_adoption_share`, `charger_count`, `effective_ev_price`,
`current_fuel_price`, `current_electricity_price`, `current_subsidy`,
`ev_supply_blocked`, and means — `mean_adoption_score`, `mean_tco_gap`,
`mean_economic_score`, `mean_charging_score`, `mean_environmental_score`,
`mean_peer_adoption_share`, `mean_range_anxiety_penalty`, `mean_ev_tco`,
`mean_ice_tco` (averaged **only over agents that have evaluated adoption at
least once**; 0.0 before the first evaluation), plus all-agent means
`mean_vehicle_age`, `mean_income`, `mean_home_charging_access`,
`mean_range_anxiety`, `mean_environmental_concern`, and grid means
`mean_charging_access`, `mean_effective_charging_access`,
`mean_charger_congestion`.

Agent reporters: the base four plus `ev_adopted`, `vehicle_age`, `income`,
`home_charging_access`, `range_anxiety`, `environmental_concern`,
`has_evaluated_adoption`, and every `last_*` telemetry value including
`last_adoption_probability` and `last_affordable`.

## 8. Reproducibility

All stochasticity flows through the model-seeded RNGs (`model.random`,
`model.rng`). Every optional mechanism draws zero random numbers while
disabled, so enabling none reproduces earlier seeded results byte-for-byte;
the test suite pins this with same-seed dataframe-equality and
RNG-state-invariance tests (`tests/test_ev_model.py` and companions, 88 tests).

## 9. Workflows

- Single run: `python scripts/run_ev_model.py --scenario no_policy --steps 50 --seed 42`
- Scenario × seed sweeps and empirical-target RMSE:
  `python scripts/run_ev_experiments.py --scenarios no_policy subsidy --seeds 1 2 3 --targets targets.csv`
- One-at-a-time sensitivity:
  `python scripts/run_ev_experiments.py --sweep subsidy=0,4000,8000,12000 --sweep-scenario colleague_baseline`
- Notebook: `notebooks/ev_scenarios.ipynb` (same presets, fixed seeds).
- Dashboard: `solara run affordance_mesa/solara_app.py` (scenario selector and
  a Mechanisms block for the optional switches).

## 10. Known limitations

- Defaults are calibrated against one real target (Portugal's 2010–2024 BEV
  fleet-share series; `VALIDATION.md` §"Portugal calibration"), not
  cross-validated against a second market or a held-out period. The fit
  overshoots in the middle of the period (a one-shot-replacement-cycle
  "backlog burst" artifact) and is scale-dependent on `number_of_agents` via
  `charger_expansion_rate`; see the scenario-table footnote above. Other
  presets (`no_policy`, `subsidy`, `fuel_price`, `charging_expansion`,
  `colleague_baseline`) remain uncalibrated illustrative scenarios.
- The income-budget gate (`income_budget_share`) uses `ev_tco / tco_years` as
  a proxy for "annual cost of ownership"; it is not a real amortized-loan
  calculation and does not model financing terms.
- Chargers have capacity but no reliability, type mix (AC/DC), or realistic
  geography; the grid is an abstract torus.
- No used-vehicle market or explicit model-availability constraints beyond
  the per-step supply cap.
- Adoption is one-shot; there is no disadoption or vehicle-to-vehicle
  replacement choice set.
- The Wright's-law price model treats `ev_adoption_count` (agents in this
  model) as a proxy for cumulative EV production/adopters; it is not tied to
  any external production-volume series.
