import pytest
from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams


# ------------------------------------------------------------
# 1. O modelo corre 10 steps sem erros
# ------------------------------------------------------------
def test_model_runs_10_steps():
    params = EVParams(width=10, height=10)
    model = EVAdoptionModel(params, seed=42)

    for _ in range(10):
        model.step()

    assert model.ev_adoption_share >= 0  # modelo correu


# ------------------------------------------------------------
# 2. A adoção fica sempre entre 0 e 1
# ------------------------------------------------------------
def test_adoption_share_bounds():
    params = EVParams(width=10, height=10)
    model = EVAdoptionModel(params, seed=42)

    for _ in range(20):
        model.step()
        assert 0.0 <= model.ev_adoption_share <= 1.0


# ------------------------------------------------------------
# 3. Maior subsídio não reduz adoção (mesmo seed)
# ------------------------------------------------------------
def test_subsidy_monotonicity():
    params_low = EVParams(width=10, height=10, subsidy=0)
    params_high = EVParams(width=10, height=10, subsidy=5000)

    model_low = EVAdoptionModel(params_low, seed=42)
    model_high = EVAdoptionModel(params_high, seed=42)

    for _ in range(30):
        model_low.step()
        model_high.step()

    assert model_high.ev_adoption_share >= model_low.ev_adoption_share


# ------------------------------------------------------------
# 4. Maior charging access não reduz adoção (mesmo seed)
# ------------------------------------------------------------
def test_charging_access_monotonicity():
    params_low = EVParams(width=10, height=10, charger_expansion_rate=0.0)
    params_high = EVParams(width=10, height=10, charger_expansion_rate=0.05)

    model_low = EVAdoptionModel(params_low, seed=42)
    model_high = EVAdoptionModel(params_high, seed=42)

    for _ in range(30):
        model_low.step()
        model_high.step()

    assert model_high.ev_adoption_share >= model_low.ev_adoption_share
