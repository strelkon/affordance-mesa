import pytest
from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams


def make_params(**overrides):
    """Cria um objeto EVParams com defaults e overrides."""
    p = EVParams()
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def run_model(steps, **param_overrides):
    params = make_params(**param_overrides)
    model = EVAdoptionModel(params=params, seed=123)
    for _ in range(steps):
        model.step()
    return model


def test_model_runs_10_steps():
    model = run_model(10, subsidy=5000, charger_expansion_rate=1)
    assert True


def test_adoption_share_between_0_and_1():
    model = run_model(10, subsidy=5000, charger_expansion_rate=1)
    assert 0.0 <= model.ev_adoption_share <= 1.0


def test_higher_subsidy_does_not_reduce_adoption():
    low = run_model(10, subsidy=3000)
    high = run_model(10, subsidy=8000)
    assert high.ev_adoption_share >= low.ev_adoption_share


def test_higher_charging_access_does_not_reduce_adoption():
    low = run_model(10, charger_expansion_rate=1)
    high = run_model(10, charger_expansion_rate=3)
    assert high.ev_adoption_share >= low.ev_adoption_share
