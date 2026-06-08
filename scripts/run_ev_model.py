"""Run the EVAdoptionModel for a chosen number of steps."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams


def run_model(steps: int = 50, seed: int = 42) -> EVAdoptionModel:
    params = EVParams(
        width=20,
        height=20,
        number_of_agents=100,
        subsidy=3000,
        fuel_price=1.8,
        electricity_price=0.25,
        initial_charging_coverage=0.05,
        charger_expansion_rate=0.5,
        adoption_threshold=0.5,
    )

    model = EVAdoptionModel(params, seed=seed)
    model.run_model(steps)

    print(f"Ran EV model for {steps} steps.")
    print("Final outcomes:")
    print(f"  EV adoption share: {model.ev_adoption_share:.3f}")
    print(f"  Mean adoption score: {model.mean_adoption_score:.3f}")
    print(f"  Mean charging access: {model.mean_charging_access:.3f}")
    print(f"  Charger sites: {len(model.chargers)}")
    print(f"  Mean TCO gap (ICE - EV): {model.mean_tco_gap:.2f}")

    return model


if __name__ == "__main__":
    run_model()
