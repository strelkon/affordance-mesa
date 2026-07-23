"""Generate all figures (and the numbers JSON) for paper draft v13.

Everything runs on the calibrated ``portugal_2010_2024`` scenario scale
(4,000 agents, 60x60 grid, steps 0-14 = 2010-2024), replacing the v12
figures that were produced with pre-calibration defaults at 100-agent
scale. All figures aggregate multiple seeds and show dispersion.

Outputs to outputs/v13_figures/:
    fig_calibration.png   model vs Portugal target, fit/hold-out split
    fig_scenarios.png     2024 share under policy counterfactuals (bars +- sd)
    fig_sens_fuel.png     fuel-price sweep (mean +- sd)
    fig_sens_charger.png  charger-expansion-rate sweep (mean +- sd)
    fig_sens_subsidy.png  subsidy-ramp-scale sweep (mean +- sd)
    fig_surface.png       fuel price x charger rate surface (seed mean)
    v13_numbers.json      all aggregates used in the paper text

Run:  python scripts/make_v13_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams, _PORTUGAL_SUBSIDY_SCHEDULE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "v13_figures"
TARGETS = pd.read_csv(ROOT / "outputs" / "portugal_ev_stock_share_targets.csv")

STEPS = 14
SEEDS_MAIN = list(range(1, 13))
SEEDS_SWEEP = list(range(1, 9))
SEEDS_SURFACE = list(range(1, 5))
YEARS = np.arange(2010, 2025)


def run_curves(seeds, **overrides) -> np.ndarray:
    """Return (n_seeds, STEPS+1) adoption-share curves for the Portugal scenario."""

    params = EVParams.from_scenario("portugal_2010_2024", **overrides)
    curves = []
    for seed in seeds:
        model = EVAdoptionModel(params, seed=seed)
        model.run_model(STEPS)
        curves.append(
            model.datacollector.get_model_vars_dataframe()["ev_adoption_share"].to_numpy()
        )
    return np.array(curves)


def scaled_schedule(factor: float) -> tuple:
    return tuple(value * factor for value in _PORTUGAL_SUBSIDY_SCHEDULE)


def fig_calibration(numbers: dict) -> None:
    curves = run_curves(SEEDS_MAIN)
    mean, sd = curves.mean(axis=0), curves.std(axis=0)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(YEARS, TARGETS["ev_adoption_share"], "ko--", label="Observed (UVE/ACAP)")
    ax.plot(YEARS, mean, "C0-", label="Model mean (12 seeds)")
    ax.fill_between(YEARS, mean - sd, mean + sd, color="C0", alpha=0.25, label="±1 sd")
    ax.axvline(2020.5, color="grey", linestyle=":", linewidth=1)
    ax.text(2015, ax.get_ylim()[1] * 0.92, "fit window", ha="center", fontsize=9, color="grey")
    ax.text(2022.6, ax.get_ylim()[1] * 0.92, "hold-out", ha="center", fontsize=9, color="grey")
    ax.set_xlabel("Year")
    ax.set_ylabel("BEV fleet share")
    ax.set_title("Portugal BEV fleet share: model vs observed")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "fig_calibration.png", dpi=150)
    plt.close(fig)

    numbers["calibration"] = {
        "model_mean_curve": mean.round(5).tolist(),
        "model_sd_curve": sd.round(5).tolist(),
        "target_curve": TARGETS["ev_adoption_share"].tolist(),
        "model_2024_mean": float(mean[-1]),
        "model_2024_sd": float(sd[-1]),
        "target_2024": float(TARGETS["ev_adoption_share"].iloc[-1]),
    }


def fig_scenarios(numbers: dict) -> None:
    scenarios = {
        "calibrated\nbaseline": {},
        "no subsidy": {"subsidy_schedule": None, "subsidy": 0.0},
        "double subsidy\nramp": {"subsidy_schedule": scaled_schedule(2.0)},
        "double charger\nrollout": {"charger_expansion_rate": 3.72},
        "high fuel price\n(2.6 EUR/l)": {"fuel_price": 2.6},
    }
    labels, means, sds = [], [], []
    for label, overrides in scenarios.items():
        curves = run_curves(SEEDS_MAIN, **overrides)
        labels.append(label)
        means.append(curves[:, -1].mean())
        sds.append(curves[:, -1].std())

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=sds, capsize=4, color="C0")
    ax.set_xticks(x, labels, fontsize=9)
    ax.set_ylabel("BEV fleet share in 2024")
    ax.set_title("2024 adoption under policy counterfactuals (12 seeds, ±1 sd)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_scenarios.png", dpi=150)
    plt.close(fig)

    numbers["scenarios"] = {
        label.replace("\n", " "): {"mean": float(m), "sd": float(s)}
        for label, m, s in zip(labels, means, sds, strict=True)
    }


def sweep(values, override_key, transform=None):
    means, sds = [], []
    for value in values:
        overrides = transform(value) if transform else {override_key: value}
        curves = run_curves(SEEDS_SWEEP, **overrides)
        means.append(curves[:, -1].mean())
        sds.append(curves[:, -1].std())
    return np.array(means), np.array(sds)


def line_figure(x, means, sds, xlabel, title, path):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.errorbar(x, means, yerr=sds, marker="o", capsize=3)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("BEV fleet share in 2024")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def fig_sens_fuel(numbers: dict) -> None:
    values = [1.4, 1.8, 2.2, 2.6, 3.0]
    means, sds = sweep(values, "fuel_price")
    line_figure(values, means, sds, "Fuel price (EUR/l)",
                "Sensitivity: 2024 adoption vs fuel price (8 seeds, ±1 sd)",
                OUT / "fig_sens_fuel.png")
    numbers["fuel_sweep"] = {"values": values, "means": means.round(5).tolist(), "sds": sds.round(5).tolist()}


def fig_sens_charger(numbers: dict) -> None:
    values = [0.0, 1.0, 1.86, 3.0, 4.5, 6.0]
    means, sds = sweep(values, "charger_expansion_rate")
    line_figure(values, means, sds, "Charger expansion rate (chargers/step)",
                "Sensitivity: 2024 adoption vs charger rollout (8 seeds, ±1 sd)",
                OUT / "fig_sens_charger.png")
    numbers["charger_sweep"] = {"values": values, "means": means.round(5).tolist(), "sds": sds.round(5).tolist()}


def fig_sens_subsidy(numbers: dict) -> None:
    factors = [0.0, 0.5, 1.0, 1.5, 2.0]
    peak = [4000.0 * f for f in factors]
    means, sds = sweep(factors, None, transform=lambda f: {"subsidy_schedule": scaled_schedule(f)})
    line_figure(peak, means, sds, "Peak subsidy reached by 2024 (EUR; ramp scaled)",
                "Sensitivity: 2024 adoption vs subsidy-ramp scale (8 seeds, ±1 sd)",
                OUT / "fig_sens_subsidy.png")
    numbers["subsidy_sweep"] = {"peak_eur": peak, "means": means.round(5).tolist(), "sds": sds.round(5).tolist()}


def fig_surface(numbers: dict) -> None:
    fuel_values = [1.4, 1.8, 2.2, 2.6, 3.0]
    charger_values = [0.0, 1.0, 1.86, 3.0, 4.5]
    grid = np.zeros((len(fuel_values), len(charger_values)))
    for i, fuel in enumerate(fuel_values):
        for j, rate in enumerate(charger_values):
            curves = run_curves(SEEDS_SURFACE, fuel_price=fuel, charger_expansion_rate=rate)
            grid[i, j] = curves[:, -1].mean()

    fig = plt.figure(figsize=(7.5, 5.5))
    ax = fig.add_subplot(111, projection="3d")
    fuel_mesh, charger_mesh = np.meshgrid(charger_values, fuel_values)
    surface = ax.plot_surface(charger_mesh, fuel_mesh, grid, cmap="viridis", edgecolor="k", linewidth=0.3)
    ax.set_ylabel("Charger expansion rate")
    ax.set_xlabel("Fuel price (EUR/l)")
    ax.set_zlabel("BEV fleet share in 2024")
    ax.set_title("2024 adoption: fuel price x charger rollout (4-seed means)")
    fig.colorbar(surface, shrink=0.6, label="BEV fleet share in 2024")
    fig.tight_layout()
    fig.savefig(OUT / "fig_surface.png", dpi=150)
    plt.close(fig)

    numbers["surface"] = {
        "fuel_values": fuel_values,
        "charger_values": charger_values,
        "grid": grid.round(5).tolist(),
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    numbers: dict = {}
    for step_name, fn in [
        ("calibration", fig_calibration),
        ("scenarios", fig_scenarios),
        ("fuel sweep", fig_sens_fuel),
        ("charger sweep", fig_sens_charger),
        ("subsidy sweep", fig_sens_subsidy),
        ("surface", fig_surface),
    ]:
        print(f"Running {step_name}...")
        fn(numbers)
    (OUT / "v13_numbers.json").write_text(json.dumps(numbers, indent=2))
    print(f"Wrote figures + v13_numbers.json to {OUT}")
