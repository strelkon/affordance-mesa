# Affordance Landscape model — Mesa reimplementation

This repository is a Mesa/Python reimplementation of the NetLogo model:

> Kaaronen, R. O. & Strelkovskii, N. (2019). *Cultural Evolution of Sustainable Behaviours: Landscape of Affordances Model*, Version 1.2.0. CoMSES Computational Model Library. DOI: 10.25937/z8x6-2v73.

The original model is an abstract ABM of pro-environmental behaviour patterns. Collective behaviour emerges from interactions among:

1. the landscape of environmental affordances;
2. individual learning and habituation;
3. social learning and network structure;
4. personal states such as habits and attitudes; and
5. cultural niche construction.

The original affordance-landscape implementation remains available as the
computational core. EV adoption code is provided as a separate extension layer:
it adds vehicle replacement, total-cost-of-ownership, charging access, and peer
adoption mechanisms while preserving the original affordance behaviour loop.
The EV extension is not part of the original NetLogo model.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

Mesa also recommends installing the latest stable release with:

```bash
pip install -U mesa
```

## Run one simulation

```bash
python scripts/run_model.py --steps 1000 --seed 74 --out outputs/baseline.csv
```

Enable the original model's optional network and niche-construction switches
with:

```bash
python scripts/run_model.py --steps 1000 --seed 74 --networks --niche-construction
```

## Run a small parameter sweep

```bash
python scripts/run_experiments.py
```

## Run the EV adoption extension

The EV extension lives in `affordance_mesa/ev_model.py`,
`affordance_mesa/ev_agents.py`, `affordance_mesa/ev_params.py`, and
`affordance_mesa/ev_costs.py`.

```bash
python scripts/run_ev_model.py
```

The EV model subclasses `AffordanceLandscapeModel`. Each `EVConsumerAgent`
first performs the original affordance behaviour, then considers EV adoption
when its vehicle reaches replacement age.

Key EV outputs collected by the Mesa `DataCollector` include:

- `ev_adoption_share`
- `mean_adoption_score`
- `mean_charging_access`
- `mean_tco_gap`
- `charger_count`

`charger_expansion_rate` is interpreted as the expected number of new charger
sites per step. For example, `0.5` means roughly one new charger every two
steps; `1.0` means one new charger per step. Charging access is spatial:
charger sites are placed on the grid, and access decays with distance.

## Run the EV model from Jupyter

If the notebook is opened outside the repository folder, first point it at this
checkout:

```python
%cd /Users/strelkon/Library/CloudStorage/OneDrive-IIASA/YSSP/26_Jorge
```

Then run:

```python
from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams

params = EVParams(
    width=201,
    height=201,
    number_of_agents=100,
    subsidy=8000,
    initial_charging_coverage=0.0,
    charger_expansion_rate=2.0,
    adoption_threshold=0.34,
)

model = EVAdoptionModel(params, seed=42)
model.run_model(50)

results = model.datacollector.get_model_vars_dataframe()
results.tail()
```

Alternatively, install the repository in editable mode from a notebook:

```python
%pip install -e /Users/strelkon/Library/CloudStorage/OneDrive-IIASA/YSSP/26_Jorge
```

## Launch the EV Solara dashboard

```bash
solara run affordance_mesa/solara_app.py --port 8765
```

The dashboard runs the EV adoption extension. It exposes EV policy controls,
charging infrastructure controls, selected affordance-core controls, and plots
EV adoption, charging access, TCO gap, and original affordance behaviour shares.

## EV scenarios and experiments

EV scenario presets are defined in `affordance_mesa.ev_params.SCENARIOS` and
constructed with `EVParams.from_scenario(...)`. The current preset names are
`colleague_baseline`, `no_policy`, `subsidy`, `fuel_price`, and
`charging_expansion`.

Run one preset from the command line:

```bash
python scripts/run_ev_model.py --scenario no_policy --steps 50 --seed 42
```

Run scenario and seed sweeps, optionally comparing against empirical targets:

```bash
python scripts/run_ev_experiments.py --scenarios no_policy subsidy --seeds 1 2 3 --targets targets.csv --set number_of_agents=100
```

The experiment runner writes `outputs/ev_experiment_curves.csv`,
`outputs/ev_experiment_summary.csv`, and `outputs/ev_adoption_curves.png`.
The notebook `notebooks/ev_scenarios.ipynb` provides the same preset workflow
for reproducible exploratory runs.

Optional mechanism switches include `adoption_rule`/`adoption_temperature`,
`initial_ev_share`/`initial_ev_clustered`, `charger_expansion_mode=demand`,
`social_diffusion`, `ev_supply_per_step`, and `ev_price_learning_rate`; all are
off by default, so baseline runs are unchanged.

## Main files

- `affordance_mesa/model.py` — Mesa model class, parameters, affordance landscape, data collection.
- `affordance_mesa/agents.py` — consumer agent behaviour, learning, niche construction, movement.
- `affordance_mesa/networks.py` — random, small-world, preferential, and KE-style social networks.
- `affordance_mesa/ev_model.py` — optional EV adoption model extending the affordance model.
- `affordance_mesa/ev_agents.py` — EV-capable consumer agents.
- `affordance_mesa/ev_params.py` — EV extension parameters.
- `affordance_mesa/ev_costs.py` — pure EV/ICE total-cost-of-ownership helpers.
- `affordance_mesa/solara_app.py` — browser dashboard for stepping and plotting the EV extension.
- `scripts/run_model.py` — command-line runner for one simulation.
- `scripts/run_ev_model.py` — command-line runner for the EV adoption extension.
- `scripts/run_experiments.py` — simple BehaviorSpace-style parameter sweep.
- `CODEX_TASK.md` — prompt for continuing the implementation with Codex.

## Mapping from NetLogo to Mesa

| NetLogo concept | Mesa/Python implementation |
|---|---|
| `turtles-own [pro-env non-env behaved? lower-bound upper-bound]` | `ConsumerAgent.pro_env`, `non_env`, `behaved`, `lower_bound`, `upper_bound` |
| `patches-own [affordance]` | `model.affordances`, a NumPy array |
| `pro-behavior`, `non-behavior` globals | `model.pro_behaviour`, `model.non_behaviour` |
| `create-aff` | `AffordanceLandscapeModel._create_affordances()` |
| `create-network` | `create_social_network()` with NetworkX |
| `behave` | `ConsumerAgent.behave()` |
| `niche-construction` | local conversion of neighbouring affordance cells |
| NetLogo plots/monitors | Mesa `DataCollector` model and agent reporters |

## Known deviations from NetLogo

1. **Movement**: NetLogo uses continuous heading (`rt random 45`, `lt random 45`, `fd 1`). This Mesa port uses a discrete Moore-neighbour random walk on a toroidal grid.
2. **Infinite behaviour loop guard**: NetLogo loops until the agent behaves. This port uses `max_behavior_attempts` to avoid rare infinite loops.
3. **KE network**: The KE network generator is a transparent approximation of the NetLogo implementation, not a formally verified byte-for-byte port.
4. **Visualization**: The Solara dashboard is a Mesa/Python browser view and is not a NetLogo interface clone.
5. **Validation**: The port has not yet been numerically calibrated against the original NetLogo BehaviorSpace output.
6. **EV extension**: EV adoption mechanisms are an added scenario layer and are not present in the original NetLogo model.

## Tests

Run the test suite with:

```bash
python -m pytest -q
```

The tests cover the original affordance model, network generation, validation
script plumbing, and the EV extension integration points.

## License note

This is a derivative reimplementation of a published model. The original CoMSES page lists CC-BY-NC-4.0, while the NetLogo Info tab mentions CC BY-NC-SA 3.0. Before public release, reconcile the licence and preserve attribution to the original authors and source.
