# Affordance Landscape model — Mesa reimplementation

This repository is a Mesa/Python reimplementation of the NetLogo model:

> Kaaronen, R. O. & Strelkovskii, N. (2019). *Cultural Evolution of Sustainable Behaviours: Landscape of Affordances Model*, Version 1.2.0. CoMSES Computational Model Library. DOI: 10.25937/z8x6-2v73.

The original model is an abstract ABM of pro-environmental behaviour patterns. Collective behaviour emerges from interactions among:

1. the landscape of environmental affordances;
2. individual learning and habituation;
3. social learning and network structure;
4. personal states such as habits and attitudes; and
5. cultural niche construction.

This port keeps the original model logic only. It does not include nudge,
policy-intervention, or consumer-choice extensions beyond the NetLogo v1.2.0
mechanisms.

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

## Launch the Solara dashboard

```bash
solara run affordance_mesa/solara_app.py --port 8765
```

## Main files

- `affordance_mesa/model.py` — Mesa model class, parameters, affordance landscape, data collection.
- `affordance_mesa/agents.py` — consumer agent behaviour, learning, niche construction, movement.
- `affordance_mesa/networks.py` — random, small-world, preferential, and KE-style social networks.
- `affordance_mesa/solara_app.py` — browser dashboard for stepping and plotting the model.
- `scripts/run_model.py` — command-line runner for one simulation.
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

## License note

This is a derivative reimplementation of a published model. The original CoMSES page lists CC-BY-NC-4.0, while the NetLogo Info tab mentions CC BY-NC-SA 3.0. Before public release, reconcile the licence and preserve attribution to the original authors and source.
