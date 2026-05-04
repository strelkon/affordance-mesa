"""Small BehaviorSpace-style parameter sweep for the Mesa port."""

from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd

from affordance_mesa import AffordanceLandscapeModel, AffordanceModelParams


def run_sweep(out: Path = Path("outputs/experiment_summary.csv")) -> None:
    rows = []
    seeds = [1, 2, 3, 4, 5]
    pro_amounts = [0.25, 0.5, 0.75]
    social_learning_values = [0.00003, 0.00007, 0.00012]

    for seed, pro_amount, social_learning in itertools.product(
        seeds, pro_amounts, social_learning_values
    ):
        params = AffordanceModelParams(
            pro_amount=pro_amount,
            social_learning=social_learning,
            max_steps=500,
        )
        model = AffordanceLandscapeModel(params=params, seed=seed)
        model.run_model(500)
        df = model.datacollector.get_model_vars_dataframe()
        last = df.iloc[-1].to_dict()
        rows.append(
            {
                "seed": seed,
                "pro_amount": pro_amount,
                "social_learning": social_learning,
                **last,
            }
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    run_sweep()
