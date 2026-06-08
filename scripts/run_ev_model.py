"""
Run the EVAdoptionModel for a chosen number of steps.
This script works both in Jupyter (%run) and from the terminal.
"""

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams


def run_model(steps=50, seed=42):
    # 1. Define EV model parameters
    params = EVParams()
    params.width = 20
    params.height = 20
    params.number_of_agents = 200
    params.subsidy = 3000
    params.fuel_price = 1.8
    params.electricity_price = 0.25
    params.charger_expansion_rate = 0.5
    params.adoption_threshold = 0.0

    # 2. Create model
    model = EVAdoptionModel(params=params, seed=seed)

    # 3. Run model
    for _ in range(steps):
        model.step()

    # 4. Print final results
    print(f"Ran EV model for {steps} steps.")
    print("Final outcomes:")
    print(f"  EV adoption share: {model.ev_adoption_share:.3f}")
    print(f"  Mean adoption score: {model.mean_adoption_score:.3f}")
    print(f"  Mean charging access: {model.mean_charging_access:.3f}")
    print(f"  Mean TCO gap (ICE - EV): {model.mean_tco_gap:.2f}")

    return model

if __name__ == "__main__":
    model = run_model()










