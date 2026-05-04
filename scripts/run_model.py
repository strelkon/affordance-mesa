"""Run one Affordance Landscape Mesa simulation and export results."""

from __future__ import annotations

import argparse
from pathlib import Path

from affordance_mesa import AffordanceLandscapeModel, AffordanceModelParams


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = AffordanceModelParams()
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=74)
    parser.add_argument("--agents", type=int, default=100)
    parser.add_argument("--pro-amount", type=float, default=0.5)
    parser.add_argument("--network-type", default="KE", choices=["random", "small-world", "preferential", "KE"])
    parser.add_argument("--network-param", type=float, default=5.0)
    parser.add_argument("--networks", action=argparse.BooleanOptionalAction, default=defaults.networks)
    parser.add_argument("--no-network", action="store_false", dest="networks", help=argparse.SUPPRESS)
    parser.add_argument(
        "--niche-construction",
        action=argparse.BooleanOptionalAction,
        default=defaults.niche_construction,
    )
    parser.add_argument("--out", type=Path, default=Path("outputs/model_timeseries.csv"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = AffordanceModelParams(
        number_of_agents=args.agents,
        pro_amount=args.pro_amount,
        network_type=args.network_type,
        network_param=args.network_param,
        networks=args.networks,
        niche_construction=args.niche_construction,
        max_steps=args.steps,
    )
    model = AffordanceLandscapeModel(params=params, seed=args.seed)
    model.run_model(args.steps)
    df = model.datacollector.get_model_vars_dataframe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index_label="step")
    print(f"Wrote {args.out}")
    print(df.tail(1).to_string())


if __name__ == "__main__":
    main()
