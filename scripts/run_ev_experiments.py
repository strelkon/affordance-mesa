"""Calibration & sensitivity workflow for EV scenario sweeps.

Batch scenario sweeps, comparison against empirical adoption targets, exported
tables and plots turn the prototype into an analysable model.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams, SCENARIOS


CURVE_COLUMNS = [
    "ev_adoption_share",
    "ev_adoption_count",
    "mean_adoption_score",
    "mean_charging_access",
    "effective_ev_price",
    "charger_count",
]


def _coerce_value(value: str):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_overrides(settings: list[str] | None) -> dict:
    overrides = {}
    for setting in settings or []:
        key, separator, value = setting.partition("=")
        if not separator:
            raise ValueError(f"Override must be KEY=VALUE, got {setting!r}")
        overrides[key] = _coerce_value(value)
    return overrides


def run_single(
    scenario: str,
    seed: int,
    steps: int,
    overrides: dict | None = None,
) -> pd.DataFrame:
    params = EVParams.from_scenario(scenario, **(overrides or {}))
    model = EVAdoptionModel(params, seed=seed)
    model.run_model(steps)

    df = model.datacollector.get_model_vars_dataframe()
    curves = df[CURVE_COLUMNS].copy()
    curves["scenario"] = scenario
    curves["seed"] = seed
    curves["step"] = df.index
    return curves


def _score_targets(curves: pd.DataFrame, targets_path: str | Path) -> pd.DataFrame:
    targets = pd.read_csv(targets_path)
    mean_curves = (
        curves.groupby(["scenario", "step"], as_index=False)["ev_adoption_share"]
        .mean()
        .rename(columns={"ev_adoption_share": "model_ev_adoption_share"})
    )
    rows = []
    for scenario, scenario_curve in mean_curves.groupby("scenario"):
        merged = scenario_curve.merge(
            targets[["step", "ev_adoption_share"]],
            on="step",
            how="inner",
        )
        if merged.empty:
            rmse = float("nan")
        else:
            errors = merged["model_ev_adoption_share"] - merged["ev_adoption_share"]
            rmse = float((errors.pow(2).mean()) ** 0.5)
        rows.append({"scenario": scenario, "target_rmse": rmse})
    return pd.DataFrame(rows)


def _plot_curves(
    curves: pd.DataFrame,
    plot_path: Path,
    targets_path: str | Path | None = None,
) -> None:
    mean_curves = curves.groupby(["scenario", "step"], as_index=False)[
        "ev_adoption_share"
    ].mean()

    fig, ax = plt.subplots(figsize=(8, 5))
    for scenario, scenario_curve in mean_curves.groupby("scenario"):
        ax.plot(
            scenario_curve["step"],
            scenario_curve["ev_adoption_share"],
            label=scenario,
        )

    if targets_path is not None:
        targets = pd.read_csv(targets_path)
        ax.plot(
            targets["step"],
            targets["ev_adoption_share"],
            color="black",
            linestyle="--",
            label="target",
        )

    ax.set_xlabel("Step")
    ax.set_ylabel("EV adoption share")
    ax.set_title("EV adoption curves by scenario")
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)


def run_experiments(
    scenarios,
    seeds,
    steps,
    output_dir,
    overrides=None,
    targets_path=None,
) -> pd.DataFrame:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = [
        run_single(scenario, seed, steps, overrides=overrides)
        for scenario in scenarios
        for seed in seeds
    ]
    curves = pd.concat(frames, ignore_index=True)

    curves_path = output_dir / "ev_experiment_curves.csv"
    summary_path = output_dir / "ev_experiment_summary.csv"
    plot_path = output_dir / "ev_adoption_curves.png"

    curves.to_csv(curves_path, index=False)

    final_step = curves["step"].max()
    final = curves[curves["step"] == final_step]
    summary = (
        final.groupby("scenario", as_index=False)
        .agg(
            final_ev_share_mean=("ev_adoption_share", "mean"),
            final_ev_share_std=("ev_adoption_share", "std"),
            final_charger_count_mean=("charger_count", "mean"),
            mean_adoption_score_mean=("mean_adoption_score", "mean"),
        )
    )
    summary["final_ev_share_std"] = summary["final_ev_share_std"].fillna(0.0)

    if targets_path is not None:
        target_scores = _score_targets(curves, targets_path)
        summary = summary.merge(target_scores, on="scenario", how="left")

    summary.to_csv(summary_path, index=False)
    _plot_curves(curves, plot_path, targets_path=targets_path)

    print(f"Wrote {curves_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {plot_path}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=sorted(SCENARIOS),
        default=sorted(SCENARIOS),
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--targets")
    parser.add_argument("--set", action="append", default=[])
    args = parser.parse_args()

    run_experiments(
        args.scenarios,
        args.seeds,
        args.steps,
        args.output_dir,
        overrides=parse_overrides(args.set),
        targets_path=args.targets,
    )


if __name__ == "__main__":
    main()
