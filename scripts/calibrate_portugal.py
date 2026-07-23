"""Calibration search: find EVParams overrides that best reproduce the
Portuguese EV fleet-share target series
(outputs/portugal_ev_stock_share_targets.csv, see
ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md for sourcing).

Design (second round, 2026-07-23):

- ``income_mean``/``income_sd`` are PINNED to empirical values (Eurostat
  EU-SILC, see INCOME ANCHOR below) and excluded from the search;
  ``income_budget_share`` absorbs the equivalence-scale/affordability
  slack instead, resolving the joint-identifiability problem of the first
  round (where the search drove income to unrealistic values).
- The objective is LOG-space RMSE on the FIT WINDOW ONLY (steps 0-10 =
  2010-2020). Log-RMSE weights the early exponential phase properly,
  where raw RMSE is dominated by the late, large-value years.
- Steps 11-14 (2021-2024) are a HOLD-OUT never seen by the search;
  out-of-sample RMSE (raw and log) is reported at the end.

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
FIT_STEPS = 10  # fit window: steps 0..10 (2010-2020); 11..14 (2021-2024) held out
SCREEN_SEEDS = [1, 2, 3, 4]
FINAL_SEEDS = list(range(1, 13))
# NOTE: charger_expansion_rate is an absolute chargers-per-step rate, not
# scaled to number_of_agents, so a fit found at one agent count does not
# transfer to another without rescaling it. Screening and final validation
# intentionally use the same agent count (matching the "portugal_2010_2024"
# scenario in ev_params.py) to avoid that trap.
NUM_AGENTS = 4000
# Share granularity is 1/NUM_AGENTS; floor log-space values at half an agent
# so integer-agent noise in the near-zero early years does not dominate.
LOG_FLOOR = 0.5 / NUM_AGENTS

# INCOME ANCHOR (empirical, not searched): Eurostat EU-SILC mean equivalised
# net disposable income for Portugal (ilc_di03, EUR), 2010-2024 average
# EUR 11,565 (range 9,856-14,951); mean/median ratio ~1.20 implies lognormal
# sigma ~0.60, independently cross-checked by the Gini coefficient
# (ilc_di12, ~32-34 over the period -> sigma ~0.60). mean 11,600 with
# sd 7,600 reproduces sigma ~0.60 and median ~EUR 9,700 (empirical ~9,656).
# Equivalised income is per adult-equivalent, not per household; the
# household equivalence-scale factor is absorbed by income_budget_share,
# which is the parameter fitted instead of income.
INCOME_MEAN = 11600.0
INCOME_SD = 7600.0

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
    number_of_agents=NUM_AGENTS,
    max_steps=STEPS,
    subsidy=0.0,
    subsidy_schedule=SUBSIDY_SCHEDULE,
    fuel_price=1.8,
    electricity_price=0.25,
    income_mean=INCOME_MEAN,
    income_sd=INCOME_SD,
    income_distribution="lognormal",
    # 2010 stock was ~950 BEVs / 5.8M fleet = 0.00016 -> 1 agent of 4000.
    initial_ev_share=0.00016,
    ev_price_learning_model="wright",
    adoption_rule="deterministic",
    charger_expansion_mode="exogenous",
    initial_charging_coverage=0.0,
)

SEARCH_RANGES = dict(
    income_budget_share=(0.02, 0.40),
    ev_purchase_price=(30000.0, 45000.0),
    ice_purchase_price=(16000.0, 24000.0),
    ev_wright_learning_rate=(0.02, 0.30),
    charger_expansion_rate=(0.2, 5.0),
    adoption_threshold=(0.02, 0.5),
)
REFERENCE_ADOPTER_CHOICES = [1, 5, 10, 20, 40, 80]


def build_params(**overrides) -> EVParams:
    return EVParams(**{**FIXED, **overrides})


def rmse(model_share: np.ndarray, target_share: np.ndarray) -> float:
    return float(np.sqrt(np.mean((model_share - target_share) ** 2)))


def log_rmse(model_share: np.ndarray, target_share: np.ndarray) -> float:
    log_model = np.log(np.maximum(model_share, LOG_FLOOR))
    log_target = np.log(np.maximum(target_share, LOG_FLOOR))
    return float(np.sqrt(np.mean((log_model - log_target) ** 2)))


def run_mean_curve(overrides: dict, seeds: list[int]) -> np.ndarray:
    params = build_params(**overrides)
    curves = []
    for seed in seeds:
        model = EVAdoptionModel(params, seed=seed)
        model.run_model(STEPS)
        df = model.datacollector.get_model_vars_dataframe()
        curves.append(df["ev_adoption_share"].to_numpy())
    return np.mean(curves, axis=0)


def evaluate(overrides: dict, seeds: list[int]) -> dict:
    """Return fit-window and hold-out scores plus the mean curve."""

    targets = pd.read_csv(TARGETS_PATH)["ev_adoption_share"].to_numpy()
    curve = run_mean_curve(overrides, seeds)

    fit_slice = slice(0, FIT_STEPS + 1)
    holdout_slice = slice(FIT_STEPS + 1, STEPS + 1)
    return {
        "fit_log_rmse": log_rmse(curve[fit_slice], targets[fit_slice]),
        "fit_rmse": rmse(curve[fit_slice], targets[fit_slice]),
        "holdout_log_rmse": log_rmse(curve[holdout_slice], targets[holdout_slice]),
        "holdout_rmse": rmse(curve[holdout_slice], targets[holdout_slice]),
        "curve": curve,
    }


def objective(overrides: dict, seeds: list[int]) -> float:
    """Search objective: log-RMSE on the fit window ONLY (hold-out untouched)."""

    return evaluate(overrides, seeds)["fit_log_rmse"]


def sample_overrides(rng: random.Random) -> dict:
    overrides = {key: rng.uniform(*bounds) for key, bounds in SEARCH_RANGES.items()}
    overrides["ev_wright_reference_adopters"] = rng.choice(REFERENCE_ADOPTER_CHOICES)
    return overrides


def budget_share_sweep(base_overrides: dict, seeds: list[int]) -> tuple[float, dict]:
    """Phase A: 1-D sweep of income_budget_share with all else held fixed.

    This is the direct answer to "income re-anchored, budget share refitted":
    interpretable, and a strong starting point for the local refinement.
    """

    best = None
    for share in np.linspace(*SEARCH_RANGES["income_budget_share"], 20):
        candidate = {**base_overrides, "income_budget_share": float(share)}
        score = objective(candidate, seeds)
        marker = ""
        if best is None or score < best[0]:
            best = (score, candidate)
            marker = "  <- best"
        print(f"budget_share={share:.3f}: fit log-RMSE={score:.4f}{marker}")
    return best


def random_search(n_trials: int, seeds: list[int], seed: int = 0):
    rng = random.Random(seed)
    best = None
    for i in range(n_trials):
        overrides = sample_overrides(rng)
        score = objective(overrides, seeds)
        if best is None or score < best[0]:
            best = (score, overrides)
            print(f"trial {i + 1}/{n_trials}: new best fit log-RMSE={score:.4f}  {overrides}")
        elif (i + 1) % 25 == 0:
            print(f"trial {i + 1}/{n_trials}: best fit log-RMSE so far={best[0]:.4f}")
    return best


def refine(best_overrides: dict, n_trials: int, seeds: list[int], seed: int = 1):
    """Local random perturbation around the current best."""

    rng = random.Random(seed)
    best = (objective(best_overrides, seeds), dict(best_overrides))
    for i in range(n_trials):
        candidate = dict(best[1])
        for key, (lo, hi) in SEARCH_RANGES.items():
            span = (hi - lo) * 0.15
            candidate[key] = min(max(candidate[key] + rng.uniform(-span, span), lo), hi)
        if rng.random() < 0.3:
            candidate["ev_wright_reference_adopters"] = rng.choice(REFERENCE_ADOPTER_CHOICES)
        score = objective(candidate, seeds)
        if score < best[0]:
            best = (score, candidate)
            print(f"refine {i + 1}/{n_trials}: new best fit log-RMSE={score:.4f}  {candidate}")
    return best


# Non-income parameters shipped by the first calibration round; Phase A
# starts from these and refits income_budget_share under the new income
# anchor before Phase B refines everything (except income) jointly.
ROUND1_BASE = dict(
    ev_purchase_price=39500.0,
    ice_purchase_price=23000.0,
    ev_wright_learning_rate=0.23,
    ev_wright_reference_adopters=10,
    charger_expansion_rate=1.1,
    adoption_threshold=0.085,
)

# Round-2 result now shipped as the EVParams defaults / "portugal_2010_2024"
# scenario. Validated at 12 seeds: fit-window (2010-2020) log-RMSE ~0.36
# (raw ~0.0006), hold-out (2021-2024) log-RMSE ~0.29 (raw ~0.006).
# Passed via --from-known to skip straight to the refinement phase.
KNOWN_GOOD = dict(
    ev_purchase_price=44000.0,
    ice_purchase_price=23200.0,
    ev_wright_learning_rate=0.18,
    ev_wright_reference_adopters=5,
    charger_expansion_rate=1.86,
    adoption_threshold=0.02,
    income_budget_share=0.108,
)

if __name__ == "__main__":
    if "--from-known" in sys.argv:
        print("Refining from KNOWN_GOOD")
        best_score, best_overrides = refine(KNOWN_GOOD, n_trials=100, seeds=SCREEN_SEEDS)
    else:
        print("Phase A: 1-D income_budget_share sweep (income pinned to Eurostat anchor)")
        best_score, best_overrides = budget_share_sweep(ROUND1_BASE, SCREEN_SEEDS)
        print("\nPhase B: local refinement of all searchable parameters")
        best_score, best_overrides = refine(best_overrides, n_trials=120, seeds=SCREEN_SEEDS)

    print("\n=== Best found (screening seeds) ===")
    print("Fit log-RMSE:", best_score)
    print("Overrides:", best_overrides)

    print("\n=== Validating at full seed count (12 seeds) ===")
    result = evaluate(best_overrides, FINAL_SEEDS)
    targets = pd.read_csv(TARGETS_PATH)
    print(f"Fit window (2010-2020):  log-RMSE={result['fit_log_rmse']:.4f}  raw RMSE={result['fit_rmse']:.5f}")
    print(f"Hold-out  (2021-2024):  log-RMSE={result['holdout_log_rmse']:.4f}  raw RMSE={result['holdout_rmse']:.5f}")
    print("Model curve:  ", np.round(result["curve"], 5).tolist())
    print("Target curve: ", targets["ev_adoption_share"].tolist())
