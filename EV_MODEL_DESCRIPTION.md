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

EV attributes sampled at initialization: `income`, `annual_mileage`
(non-negative normals), `vehicle_age`, `replacement_interval` (uniform
integers), and five traits in [0, 1]: `home_charging_access`,
`environmental_concern`, `price_sensitivity`, `range_anxiety`,
`peer_sensitivity`. `environmental_concern` and `range_anxiety` are fixed
unless `social_diffusion` is enabled (Section 5.5).

Adoption state: `ev_adopted` (one-shot; adopting resets `vehicle_age` to 0).

Decision telemetry (recorded on every evaluation): `last_adoption_score`,
`last_economic_score`, `last_charging_score`, `last_environmental_score`,
`last_peer_adoption_share`, `last_range_anxiety_penalty`, `last_ev_tco`,
`last_ice_tco`, `last_tco_gap`, `last_adoption_probability`, and
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
until adoption). With parameters `p` and agent traits:

```
ev_tco   = (effective_ev_price - subsidy)+  +  mileage * kwh_per_km * electricity_price * years  +  ev_maintenance * years
ice_tco  = ice_purchase_price               +  mileage * l_per_km   * fuel_price       * years  +  ice_maintenance * years

tco_score            = (ice_tco - ev_tco) / ice_tco
affordability        = min(income / ev_tco, 1)
economic_component   = tco_score * (0.5 + price_sensitivity) + 0.1 * affordability

charging_score       = 0.7 * home_charging_access + 0.3 * effective_charging_access[home_pos]
environmental_score  = (1 - w) * environmental_concern + w * pro_env
peer_share           = share of ev_adopted among peers (Section 5.3)

adoption_score = economic_weight      * economic_component
               + charging_weight      * charging_score
               + environmental_weight * environmental_score
               + peer_weight          * peer_share * (0.5 + peer_sensitivity)
               - range_anxiety_weight * range_anxiety
```

### 5.2 Decision rule and market gate

- `adoption_rule = "deterministic"` (default): adopt iff
  `adoption_score >= adoption_threshold`. Draws no random numbers.
- `adoption_rule = "logistic"`: adopt with probability
  `1 / (1 + exp(-(score - threshold) / adoption_temperature))`
  (`temperature <= 0` degenerates to the step function).

A positive decision must then pass the market: `request_ev_purchase()` grants
at most `ev_supply_per_step` purchases per step. Blocked agents remain past
their replacement interval and retry on later steps, so delivery delays
emerge from the queue without an explicit waiting list.

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

- `effective_ev_price = max(ev_purchase_price * (1 - ev_price_learning_rate *
  ev_adoption_share), ev_purchase_price * ev_price_floor_share)` — a linear
  learning-curve proxy; the rate 0 default keeps the list price exactly.
- `initial_ev_share` seeds a baseline adopted population at t = 0
  (`initial_ev_clustered` clusters it around a random seed household by torus
  home distance), giving row 0 an observed market state for calibration.

## 6. Parameters (`EVParams`, defaults)

All mechanism switches default to **off/neutral**, so the baseline model is
unchanged by their presence (seeded runs are byte-identical).

| Group | Parameter (default) |
|---|---|
| Run/grid | `width` (201), `height` (201), `max_steps` (20440), `number_of_agents` (100, inherited) |
| Affordance bounds | `lower_bound_mean` (0.2), `lower_bound_sd` (0.05), `upper_bound_mean` (0.8), `upper_bound_sd` (0.05) |
| Charging | `initial_charging_coverage` (0.0), `charger_expansion_rate` (2.0), `charger_expansion_mode` ("exogenous"), `demand_expansion_gain` (4.0), `demand_radius` (2), `charger_access_decay` (1.0), `charger_capacity` (inf), `congestion_radius` (3) |
| Policy/prices | `subsidy` (8000), `fuel_price` (1.8), `electricity_price` (0.25) |
| Market/supply | `ev_supply_per_step` (inf), `ev_price_learning_rate` (0.0), `ev_price_floor_share` (0.5) |
| Cost model | `ev_purchase_price` (35000), `ice_purchase_price` (25000), `ev_kwh_per_km` (0.18), `ice_liters_per_km` (0.07), `ev_maintenance_cost` (300), `ice_maintenance_cost` (600), `tco_years` (8) |
| Initial market | `initial_ev_share` (0.0), `initial_ev_clustered` (False) |
| Decision | `adoption_threshold` (0.34), `adoption_rule` ("deterministic"), `adoption_temperature` (0.05), weights: economic 0.25 / charging 0.25 / environmental 0.25 / peer 0.15 / range anxiety 0.10, `env_score_pro_env_weight` (0.5) |
| Agent distributions | `income_mean/sd` (30000/8000), `annual_mileage_mean/sd` (12000/2000), `vehicle_age_min/max` (1/12), `replacement_interval_min/max` (6/14), five trait `*_min/_max` ranges (0.0/1.0) |
| Social diffusion | `social_diffusion` (False), `peer_range_anxiety_relief` (0.02), `peer_concern_gain` (0.01) |

Scenario presets live in `SCENARIOS` (`colleague_baseline`, `no_policy`,
`subsidy`, `fuel_price`, `charging_expansion`) and are constructed with
`EVParams.from_scenario(name, **overrides)`; preset values are provisional
and user-tunable. Presets do not touch the mechanism switches.

## 7. Outputs

Model reporters (per step) beyond the base model's nine: `ev_adoption_count`,
`ev_adoption_share`, `charger_count`, `effective_ev_price`,
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
`last_adoption_probability`.

## 8. Reproducibility

All stochasticity flows through the model-seeded RNGs (`model.random`,
`model.rng`). Every optional mechanism draws zero random numbers while
disabled, so enabling none reproduces earlier seeded results byte-for-byte;
the test suite pins this with same-seed dataframe-equality and
RNG-state-invariance tests (`tests/test_ev_model.py` and companions, 69 tests).

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

- Preset and mechanism parameter values are provisional; no calibration
  against real EV adoption data has been performed yet (the `--targets` hook
  exists for it).
- Chargers have capacity but no reliability, type mix (AC/DC), or realistic
  geography; the grid is an abstract torus.
- No used-vehicle market or explicit model-availability constraints beyond
  the per-step supply cap.
- Adoption is one-shot; there is no disadoption or vehicle-to-vehicle
  replacement choice set.
