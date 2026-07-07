"""Run the EVAdoptionModel for a chosen number of steps."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams, SCENARIOS


def run_model(
    steps: int = 50,
    seed: int = 42,
    scenario: str = "colleague_baseline",
) -> EVAdoptionModel:
    params = EVParams.from_scenario(scenario)

    model = EVAdoptionModel(params, seed=seed)
    model.run_model(steps)

    print(f"Ran EV model scenario {scenario!r} for {steps} steps.")
    print("Final outcomes:")
    print(f"  EV adoption share: {model.ev_adoption_share:.3f}")
    print(f"  Mean adoption score: {model.mean_adoption_score:.3f}")
    print(f"  Mean charging access: {model.mean_charging_access:.3f}")
    print(f"  Charger sites: {len(model.chargers)}")
    print(f"  Mean TCO gap (ICE - EV): {model.mean_tco_gap:.2f}")

    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS),
        default="colleague_baseline",
    )
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run_model(steps=args.steps, seed=args.seed, scenario=args.scenario)


if __name__ == "__main__":
    main()
