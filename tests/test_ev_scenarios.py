import pytest

from affordance_mesa.ev_params import EVParams, SCENARIOS
from scripts.run_ev_model import run_model


def test_all_scenarios_construct():
    for name in SCENARIOS:
        assert isinstance(EVParams.from_scenario(name), EVParams)


def test_scenarios_differ_from_defaults_only_in_intended_fields():
    defaults = EVParams().as_dict()

    for name, preset in SCENARIOS.items():
        params = EVParams.from_scenario(name)
        values = params.as_dict()
        differing_keys = {
            key for key, value in values.items() if value != defaults[key]
        }
        expected_keys = {
            key for key, value in preset.items() if value != defaults[key]
        }

        assert differing_keys == expected_keys
        for key, value in preset.items():
            assert getattr(params, key) == value

    assert EVParams.from_scenario("colleague_baseline").number_of_agents == 100


def test_unknown_scenario_raises_value_error():
    with pytest.raises(ValueError):
        EVParams.from_scenario("nope")


def test_extra_overrides_win():
    assert EVParams.from_scenario("subsidy", subsidy=1000.0).subsidy == 1000.0


def test_run_ev_model_accepts_scenario():
    model = run_model(steps=2, seed=1, scenario="no_policy")

    assert model.params.subsidy == 0.0
