from pandas.testing import assert_frame_equal

from affordance_mesa.ev_agents import EVConsumerAgent
from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams
from affordance_mesa.model import AffordanceLandscapeModel


def test_ev_model_extends_affordance_landscape_without_duplicate_agents():
    params = EVParams(width=10, height=10, number_of_agents=17)
    model = EVAdoptionModel(params, seed=42)

    assert isinstance(model, AffordanceLandscapeModel)
    assert len(model.agent_list) == params.number_of_agents
    assert model.ev_agents is model.agent_list
    assert model.affordances.shape == (params.width, params.height)
    assert model.charging_access.shape == (params.width, params.height)
    assert all(isinstance(agent, EVConsumerAgent) for agent in model.agent_list)


def test_model_runs_and_collects_one_row_per_step_with_original_and_ev_metrics():
    params = EVParams(width=10, height=10, number_of_agents=25)
    model = EVAdoptionModel(params, seed=42)

    model.run_model(10)

    assert 0.0 <= model.ev_adoption_share <= 1.0
    assert 0 <= model.pro_behaviour + model.non_behaviour <= params.number_of_agents

    model_vars = model.datacollector.get_model_vars_dataframe()
    assert len(model_vars) == 11
    assert "pro_behaviour_share" in model_vars.columns
    assert "mean_pro_env" in model_vars.columns
    assert "ev_adoption_share" in model_vars.columns
    assert "mean_tco_gap" in model_vars.columns
    assert "charger_count" in model_vars.columns


def test_ev_agent_step_calls_parent_affordance_behaviour():
    params = EVParams(width=5, height=5, number_of_agents=5)
    model = EVAdoptionModel(params, seed=7)
    agent = model.agent_list[0]
    called = {"value": False}

    def fake_behave():
        called["value"] = True
        agent.last_behaviour = "pro"

    agent.behave = fake_behave
    agent.vehicle_age = 0
    agent.replacement_interval = 99

    agent.step()

    assert called["value"] is True
    assert agent.last_behaviour == "pro"


def test_ev_adoption_is_gated_by_replacement_timing():
    params = EVParams(width=5, height=5, number_of_agents=5)
    model = EVAdoptionModel(params, seed=11)
    agent = model.agent_list[0]
    called = {"value": False}

    agent.behave = lambda: None
    agent.consider_ev_adoption = lambda: called.update(value=True)
    agent.vehicle_age = 0
    agent.replacement_interval = 2

    agent.step()
    assert called["value"] is False

    agent.step()
    assert called["value"] is True


def test_network_peer_effect_uses_model_network_neighbours():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        networks=True,
        network_type="random",
        network_param=1.0,
    )
    model = EVAdoptionModel(params, seed=10)
    agent = model.agent_list[0]
    model.agent_list[1].ev_adopted = True
    called = {"value": False}

    def fake_network_neighbours(agent_arg):
        called["value"] = True
        assert agent_arg is agent
        return [model.agent_list[1]]

    model.network_neighbours = fake_network_neighbours

    agent.consider_ev_adoption()

    assert called["value"] is True
    assert agent.last_peer_adoption_share == 1.0


def test_spatial_chargers_increase_access_without_uniform_fill():
    params = EVParams(
        width=7,
        height=7,
        number_of_agents=5,
        initial_charging_coverage=0.0,
        charger_expansion_rate=1.0,
    )
    model = EVAdoptionModel(params, seed=42)

    assert len(model.chargers) == 0
    assert model.mean_charging_access == 0.0

    model.step()

    assert len(model.chargers) == 1
    assert model.charging_access.max() == 1.0
    assert 0.0 < model.mean_charging_access < 1.0


def test_same_seed_reproduces_ev_attributes_and_outputs():
    params = EVParams(width=8, height=8, number_of_agents=12)
    first = EVAdoptionModel(params, seed=123)
    second = EVAdoptionModel(params, seed=123)

    first_attrs = [
        (
            agent.income,
            agent.annual_mileage,
            agent.vehicle_age,
            agent.replacement_interval,
            agent.home_charging_access,
        )
        for agent in first.agent_list
    ]
    second_attrs = [
        (
            agent.income,
            agent.annual_mileage,
            agent.vehicle_age,
            agent.replacement_interval,
            agent.home_charging_access,
        )
        for agent in second.agent_list
    ]
    assert first_attrs == second_attrs
    assert first.chargers == second.chargers

    first.run_model(5)
    second.run_model(5)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_subsidy_monotonicity_with_same_seed():
    params_low = EVParams(width=10, height=10, number_of_agents=40, subsidy=0)
    params_high = EVParams(width=10, height=10, number_of_agents=40, subsidy=5000)

    model_low = EVAdoptionModel(params_low, seed=42)
    model_high = EVAdoptionModel(params_high, seed=42)

    model_low.run_model(30)
    model_high.run_model(30)

    assert model_high.ev_adoption_share >= model_low.ev_adoption_share


def test_charging_access_monotonicity_with_same_seed():
    params_low = EVParams(
        width=10,
        height=10,
        number_of_agents=40,
        initial_charging_coverage=0.0,
        charger_expansion_rate=0.0,
    )
    params_high = EVParams(
        width=10,
        height=10,
        number_of_agents=40,
        initial_charging_coverage=0.0,
        charger_expansion_rate=1.0,
    )

    model_low = EVAdoptionModel(params_low, seed=42)
    model_high = EVAdoptionModel(params_high, seed=42)

    model_low.run_model(30)
    model_high.run_model(30)

    assert model_high.mean_charging_access >= model_low.mean_charging_access
    assert model_high.ev_adoption_share >= model_low.ev_adoption_share
