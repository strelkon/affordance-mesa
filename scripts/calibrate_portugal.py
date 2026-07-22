"""One-off calibration search: find EVParams overrides that best reproduce
the Portuguese EV fleet-share target series
(outputs/portugal_ev_stock_share_targets.csv, see
ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md for sourcing).

Not part of the automated test suite (no assertions, non-deterministic
random search) -- run manually to reproduce or refine the calibration:

    python scripts/calibrate_portugal.py             # full search from scratch
    python scripts/calibrate_portugal.py --from-known  # refine around KNOWN_GOOD

To validate the parameters currently baked into EVParams/SCENARIOS directly
(the recommended way to check "does the shipped calibration still fit"),
use the actual experiment runner instead of this script:

    python scripts/run_ev_experiments.py --scenarios portugal_2010_2024 \\
        --seeds 1 2 3 4 5 6 7 8 9 10 11 12 --steps 14 \\
        --targets outputs/portugal_ev_stock_share_targets.csv
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams

TARGETS_PATH = Path(__file__).resolve().parents[1] / "outputs" / "portugal_ev_stock_share_targets.csv"
STEPS = 14  # step 0 = 2010, step 14 = 2024
SCREEN_SEEDS = [1, 2, 3, 4]
FINAL_SEEDS = list(range(1, 13))
# NOTE: charger_expansion_rate is an absolute chargers-per-step rate, not
# scaled to number_of_agents, so a fit found at one agent count does not
# transfer to another without rescaling it. Screening and final validation
# intentionally use the same agent count (matching the "portugal_2010_2024"
# scenario in ev_params.py) to avoid that trap.
NUM_AGENTS_SCREEN = 4000
NUM_AGENTS_FINAL = 4000

# Zero for 2010-2014, then a linear ramp from EUR500 to EUR4,000 over
# 2015-2024, approximating the real 2015 incentive reintroduction and the
# documented ~EUR2,000-4,000 grant range (PORTUGAL_CALIBRATION_DATA.md). A
# smooth ramp (rather than a hard step) avoids an artificial batch-adoption
# jump the year the subsidy changes; the exact year-by-year historical
# amounts are not available at that resolution in the sourced data.
SUBSIDY_SCHEDULE = tuple([0.0] * 5 + list(np.linspace(500.0, 4000.0, 10)))

FIXED = dict(
    width=60,
    height=60,
    max_steps=STEPS,
    subsidy=0.0,
    subsidy_schedule=SUBSIDY_SCHEDULE,
    fuel_price=1.8,
    electricity_price=0.25,
    income_distribution="lognormal",
    ev_price_learning_model="wright",
    adoption_rule="deterministic",
    charger_expansion_mode="exogenous",
    initial_charging_coverage=0.0,
)

SEARCH_RANGES = dict(
    income_budget_share=(0.01, 0.14),
    income_mean=(6000.0, 20000.0),
    income_sd=(3000.0, 12000.0),
    ev_purchase_price=(30000.0, 45000.0),
    ice_purchase_price=(16000.0, 24000.0),
    ev_wright_learning_rate=(0.02, 0.30),
    charger_expansion_rate=(0.2, 5.0),
    adoption_threshold=(0.02, 0.5),
)
REFERENCE_ADOPTER_CHOICES = [10, 20, 40, 80, 150]


def build_params(number_of_agents: int, **overrides) -> EVParams:
    kwargs = {**FIXED, "number_of_agents": number_of_agents, **overrides}
    return EVParams(**kwargs)


def rmse(model_share: np.ndarray, target_share: np.ndarray) -> float:
    diffs = model_share - target_share
    return float(np.sqrt(np.mean(diffs**2)))


def evaluate(overrides: dict, seeds: list[int], number_of_agents: int) -> tuple[float, np.ndarray]:
    targets = pd.read_csv(TARGETS_PATH)
    params = build_params(number_of_agents, **overrides)

    curves = []
    for seed in seeds:
        model = EVAdoptionModel(params, seed=seed)
        model.run_model(STEPS)
        df = model.datacollector.get_model_vars_dataframe()
        curves.append(df["ev_adoption_share"].to_numpy())
    mean_curve = np.mean(curves, axis=0)

    merged = targets.merge(
        pd.DataFrame({"step": range(len(mean_curve)), "model_share": mean_curve}),
        on="step",
        how="inner",
    )
    return rmse(merged["model_share"].to_numpy(), merged["ev_adoption_share"].to_numpy()), mean_curve


def sample_overrides(rng: random.Random) -> dict:
    overrides = {key: rng.uniform(*bounds) for key, bounds in SEARCH_RANGES.items()}
    overrides["ev_wright_reference_adopters"] = rng.choice(REFERENCE_ADOPTER_CHOICES)
    return overrides


def random_search(n_trials: int, seed: int = 0):
    rng = random.Random(seed)
    best = None
    for i in range(n_trials):
        overrides = sample_overrides(rng)
        score, _ = evaluate(overrides, SCREEN_SEEDS, NUM_AGENTS_SCREEN)
        if best is None or score < best[0]:
            best = (score, overrides)
            print(f"trial {i + 1}/{n_trials}: new best RMSE={score:.5f}  {overrides}")
        elif (i + 1) % 25 == 0:
            print(f"trial {i + 1}/{n_trials}: best RMSE so far={best[0]:.5f}")
    return best


def refine(best_overrides: dict, n_trials: int, seed: int = 1):
    """Local random perturbation around the screening best."""
    rng = random.Random(seed)
    best = (evaluate(best_overrides, SCREEN_SEEDS, NUM_AGENTS_SCREEN)[0], dict(best_overrides))
    for i in range(n_trials):
        candidate = dict(best[1])
        for key, (lo, hi) in SEARCH_RANGES.items():
            span = (hi - lo) * 0.15
            candidate[key] = min(max(candidate[key] + rng.uniform(-span, span), lo), hi)
        if rng.random() < 0.3:
            candidate["ev_wright_reference_adopters"] = rng.choice(REFERENCE_ADOPTER_CHOICES)
        score, _ = evaluate(candidate, SCREEN_SEEDS, NUM_AGENTS_SCREEN)
        if score < best[0]:
            best = (score, candidate)
            print(f"refine {i + 1}/{n_trials}: new best RMSE={score:.5f}  {candidate}")
    return best


# Result of the search that produced the current EVParams defaults and the
# "portugal_2010_2024" scenario (rounded slightly for readability there).
# Passed via --from-known to skip straight to the refinement phase, e.g. to
# validate at a different seed count or after editing SEARCH_RANGES.
KNOWN_GOOD = dict(
    income_budget_share=0.10130976512894171,
    income_mean=9000.0,
    income_sd=9000.0,
    ev_purchase_price=39405.67943992926,
    ice_purchase_price=22894.302666143463,
    ev_wright_learning_rate=0.23120022828768463,
    charger_expansion_rate=1.0656955233174608,
    adoption_threshold=0.08611247166924725,
    ev_wright_reference_adopters=10,
)

if __name__ == "__main__":
    if "--from-known" in sys.argv:
        print("Refining from KNOWN_GOOD")
        best_score, best_overrides = refine(KNOWN_GOOD, n_trials=100)
    else:
        print("Phase 1: broad random search")
        best_score, best_overrides = random_search(n_trials=200)
        print("\nPhase 2: local refinement")
        best_score, best_overrides = refine(best_overrides, n_trials=100)

    print("\n=== Best found (screening seeds/agents) ===")
    print("RMSE:", best_score)
    print("Overrides:", best_overrides)

    print("\n=== Validating at full seed count / agent count ===")
    final_score, final_curve = evaluate(best_overrides, FINAL_SEEDS, NUM_AGENTS_FINAL)
    targets = pd.read_csv(TARGETS_PATH)
    print("Final RMSE:", final_score)
    print("Model curve:  ", np.round(final_curve, 5).tolist())
    print("Target curve: ", targets["ev_adoption_share"].tolist())
