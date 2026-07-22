import pytest
import numpy as np
from pandas.testing import assert_frame_equal

from affordance_mesa.ev_agents import EVConsumerAgent
from affordance_mesa.ev_costs import adoption_probability, ev_tco, ice_tco
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


def test_home_pos_is_set_and_fixed_after_movement():
    params = EVParams(width=8, height=8, number_of_agents=10)
    model = EVAdoptionModel(params, seed=42)

    home_positions = [agent.home_pos for agent in model.agent_list]

    assert all(home_pos is not None for home_pos in home_positions)
    assert all(0 <= x < params.width and 0 <= y < params.height for x, y in home_positions)

    model.run_model(5)

    assert [agent.home_pos for agent in model.agent_list] == home_positions
    assert any(agent.pos != agent.home_pos for agent in model.agent_list)


def test_charging_score_uses_home_not_current_position():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=1,
        charger_expansion_rate=0.0,
        initial_charging_coverage=0.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    agent.home_charging_access = 0.0
    model.charging_access[:, :] = 0.0
    model.charging_access[agent.home_pos] = 1.0

    cell_other_than_home = (agent.home_pos[0], (agent.home_pos[1] + 1) % params.height)
    model.grid.move_agent(agent, cell_other_than_home)

    agent.consider_ev_adoption()

    assert agent.last_charging_score == pytest.approx(0.3)


def test_peer_share_uses_residential_neighbours():
    params = EVParams(width=8, height=8, number_of_agents=3, networks=False)
    model = EVAdoptionModel(params, seed=42)
    a, b, c = model.agent_list

    b.home_pos = ((a.home_pos[0] + 1) % params.width, a.home_pos[1])
    c.home_pos = ((a.home_pos[0] + 3) % params.width, (a.home_pos[1] + 3) % params.height)
    model._agents_by_home.clear()
    for agent in model.agent_list:
        model._agents_by_home.setdefault(agent.home_pos, []).append(agent)

    b.ev_adopted = True
    model.grid.move_agent(a, ((a.home_pos[0] + 4) % params.width, a.home_pos[1]))
    model.grid.move_agent(b, ((b.home_pos[0] + 4) % params.width, b.home_pos[1]))
    model.grid.move_agent(c, ((a.home_pos[0] + 1) % params.width, (a.home_pos[1] + 1) % params.height))

    assert a._peer_adoption_share() == pytest.approx(1.0)


def test_same_seed_reproduces_home_positions():
    params = EVParams(width=8, height=8, number_of_agents=12)
    first = EVAdoptionModel(params, seed=123)
    second = EVAdoptionModel(params, seed=123)

    assert [agent.home_pos for agent in first.agent_list] == [
        agent.home_pos for agent in second.agent_list
    ]


def test_extended_model_columns_present_and_in_range():
    params = EVParams(width=10, height=10, number_of_agents=25)
    model = EVAdoptionModel(params, seed=42)

    model.run_model(15)

    model_vars = model.datacollector.get_model_vars_dataframe()
    new_columns = [
        "mean_economic_score",
        "mean_charging_score",
        "mean_environmental_score",
        "mean_peer_adoption_share",
        "mean_range_anxiety_penalty",
        "mean_ev_tco",
        "mean_ice_tco",
        "mean_vehicle_age",
        "mean_income",
        "mean_home_charging_access",
    ]
    assert all(column in model_vars.columns for column in new_columns)

    last = model_vars.iloc[-1]
    assert 0 <= last.mean_environmental_score <= 1
    assert 0 <= last.mean_peer_adoption_share <= 1
    assert 0 <= last.mean_range_anxiety_penalty <= params.range_anxiety_weight
    assert last.mean_ev_tco >= 0
    assert last.mean_ice_tco >= 0
    assert last.mean_income >= 0
    assert last.mean_vehicle_age >= 0
    assert 0 <= last.mean_home_charging_access <= 1


def test_extended_agent_columns_present():
    params = EVParams(width=10, height=10, number_of_agents=25)
    model = EVAdoptionModel(params, seed=42)

    agent_vars = model.datacollector.get_agent_vars_dataframe()
    new_columns = [
        "last_economic_score",
        "last_charging_score",
        "last_environmental_score",
        "last_peer_adoption_share",
        "last_range_anxiety_penalty",
        "last_ev_tco",
        "last_ice_tco",
        "vehicle_age",
        "income",
        "home_charging_access",
        "has_evaluated_adoption",
    ]

    assert all(column in agent_vars.columns for column in new_columns)


def test_means_average_only_evaluated_agents():
    params = EVParams(width=8, height=8, number_of_agents=12)
    model = EVAdoptionModel(params, seed=42)
    agent0 = model.agent_list[0]

    assert model.mean_ev_tco == 0.0

    agent0.consider_ev_adoption()
    model._update_ev_metrics()

    assert model.mean_economic_score == pytest.approx(agent0.last_economic_score)
    assert model.mean_environmental_score == pytest.approx(agent0.last_environmental_score)


def test_means_match_manual_computation():
    params = EVParams(width=10, height=10, number_of_agents=25)
    model = EVAdoptionModel(params, seed=42)

    model.run_model(10)

    evaluated_agents = [
        agent for agent in model.agent_list if agent.has_evaluated_adoption
    ]
    assert evaluated_agents
    manual_mean_ev_tco = np.mean([agent.last_ev_tco for agent in evaluated_agents])
    manual_mean_income = np.mean([agent.income for agent in model.agent_list])
    last = model.datacollector.get_model_vars_dataframe().iloc[-1]

    assert model.mean_ev_tco == pytest.approx(manual_mean_ev_tco)
    assert model.mean_income == pytest.approx(manual_mean_income)
    assert last.mean_ev_tco == pytest.approx(manual_mean_ev_tco)
    assert last.mean_income == pytest.approx(manual_mean_income)


def test_default_rule_is_deterministic_and_draws_no_randomness():
    assert EVParams().adoption_rule == "deterministic"
    params = EVParams(width=5, height=5, number_of_agents=3)
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    state = model.random.getstate()

    agent._decide_adoption(0.9)
    agent._decide_adoption(0.0)

    assert model.random.getstate() == state
    assert agent.last_adoption_probability in (0.0, 1.0)


def test_deterministic_same_seed_dataframe_reproducible():
    params = EVParams(
        width=8,
        height=8,
        number_of_agents=15,
        adoption_rule="deterministic",
    )
    first = EVAdoptionModel(params, seed=11)
    second = EVAdoptionModel(params, seed=11)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_logistic_low_temperature_approximates_deterministic():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        adoption_rule="logistic",
        adoption_temperature=1e-9,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    threshold = model.params.adoption_threshold

    for _ in range(20):
        assert agent._decide_adoption(threshold + 0.1) is True
        assert agent._decide_adoption(threshold - 0.1) is False


def test_adoption_probability_monotonic_in_score():
    scores = np.linspace(-1, 2, 31)
    probabilities = [
        adoption_probability(score, 0.34, 0.05)
        for score in scores
    ]

    assert all(
        current <= next_value
        for current, next_value in zip(probabilities[:-1], probabilities[1:], strict=True)
    )
    assert adoption_probability(0.34, 0.34, 0.05) == pytest.approx(0.5)
    assert adoption_probability(1e6, 0.34, 0.05) == 1.0
    assert adoption_probability(-1e6, 0.34, 0.05) == 0.0
    assert adoption_probability(0.35, 0.34, 0.0) == 1.0
    assert adoption_probability(0.33, 0.34, 0.0) == 0.0


def test_logistic_same_seed_reproducible():
    params = EVParams(
        width=8,
        height=8,
        number_of_agents=20,
        adoption_rule="logistic",
    )
    first = EVAdoptionModel(params, seed=7)
    second = EVAdoptionModel(params, seed=7)

    first.run_model(20)
    second.run_model(20)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_unknown_adoption_rule_raises():
    params = EVParams(width=5, height=5, number_of_agents=3)
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    model.params.adoption_rule = "bogus"

    with pytest.raises(ValueError):
        agent._decide_adoption(0.5)


def test_initial_ev_share_defaults_to_zero_with_no_rng_cost():
    assert EVParams().initial_ev_share == 0.0
    assert EVParams().initial_ev_clustered is False

    params = EVParams(width=5, height=5, number_of_agents=5)
    model = EVAdoptionModel(params, seed=42)

    assert not any(agent.ev_adopted for agent in model.agent_list)

    state = model.random.getstate()
    model._assign_initial_adopters()

    assert model.random.getstate() == state


def test_initial_ev_share_sets_expected_count_at_row_zero():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        initial_ev_share=0.3,
    )
    model = EVAdoptionModel(params, seed=42)
    adopted_agents = [agent for agent in model.agent_list if agent.ev_adopted]
    first_row = model.datacollector.get_model_vars_dataframe().iloc[0]

    assert len(adopted_agents) == 6
    assert all(agent.vehicle_age == 0 for agent in adopted_agents)
    assert first_row.ev_adoption_share == pytest.approx(0.3)


def test_initial_ev_share_full_adoption_clamped():
    full_params = EVParams(
        width=5,
        height=5,
        number_of_agents=5,
        initial_ev_share=1.0,
    )
    out_of_range_params = EVParams(
        width=5,
        height=5,
        number_of_agents=5,
        initial_ev_share=5.0,
    )

    full_model = EVAdoptionModel(full_params, seed=42)
    out_of_range_model = EVAdoptionModel(out_of_range_params, seed=42)

    assert all(agent.ev_adopted for agent in full_model.agent_list)
    assert all(agent.ev_adopted for agent in out_of_range_model.agent_list)


def test_clustered_initial_adopters_are_spatially_close():
    params = EVParams(
        width=20,
        height=20,
        number_of_agents=40,
        initial_ev_share=0.25,
        initial_ev_clustered=True,
    )
    model = EVAdoptionModel(params, seed=42)
    adopter_positions = [
        agent.home_pos for agent in model.agent_list if agent.ev_adopted
    ]
    all_positions = [agent.home_pos for agent in model.agent_list]

    def mean_pairwise_distance(positions):
        distances = [
            model._torus_manhattan(a, b)
            for i, a in enumerate(positions)
            for b in positions[i + 1 :]
        ]
        return float(np.mean(distances))

    assert mean_pairwise_distance(adopter_positions) < mean_pairwise_distance(all_positions)


def test_initial_adopters_same_seed_reproducible():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        initial_ev_share=0.4,
    )
    first = EVAdoptionModel(params, seed=9)
    second = EVAdoptionModel(params, seed=9)

    first_adopted_homes = [
        agent.home_pos for agent in first.agent_list if agent.ev_adopted
    ]
    second_adopted_homes = [
        agent.home_pos for agent in second.agent_list if agent.ev_adopted
    ]

    assert first_adopted_homes == second_adopted_homes

    first.run_model(5)
    second.run_model(5)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_charger_expansion_mode_defaults_to_exogenous():
    assert EVParams().charger_expansion_mode == "exogenous"

    params = EVParams(
        width=8,
        height=8,
        number_of_agents=15,
        charger_expansion_mode="exogenous",
    )
    first = EVAdoptionModel(params, seed=11)
    second = EVAdoptionModel(params, seed=11)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_demand_mode_without_adopters_adds_no_chargers_and_no_rng():
    params = EVParams(
        width=8,
        height=8,
        number_of_agents=15,
        charger_expansion_mode="demand",
        initial_ev_share=0.0,
        initial_charging_coverage=0.0,
        charger_expansion_rate=5.0,
    )
    model = EVAdoptionModel(params, seed=42)
    state = model.random.getstate()

    model._expand_charging_infrastructure()

    assert len(model.chargers) == 0
    assert model.random.getstate() == state


def test_demand_mode_places_chargers_near_adopter_homes():
    params = EVParams(
        width=20,
        height=20,
        number_of_agents=30,
        charger_expansion_mode="demand",
        initial_ev_share=0.3,
        initial_ev_clustered=True,
        charger_expansion_rate=3.0,
        demand_expansion_gain=4.0,
    )
    model = EVAdoptionModel(params, seed=42)

    model.run_model(5)

    adopted_homes = [agent.home_pos for agent in model.agent_list if agent.ev_adopted]

    def within_demand_radius(charger, home):
        dx = abs(charger[0] - home[0])
        dx = min(dx, params.width - dx)
        dy = abs(charger[1] - home[1])
        dy = min(dy, params.height - dy)
        return max(dx, dy) <= params.demand_radius

    assert len(model.chargers) > 0
    assert all(
        any(within_demand_radius(charger, home) for home in adopted_homes)
        for charger in model.chargers
    )


def test_demand_mode_fallback_to_random_when_no_positive_weights():
    params = EVParams(
        width=8,
        height=8,
        number_of_agents=15,
        charger_expansion_mode="demand",
        initial_ev_share=0.0,
        initial_charging_coverage=0.0,
    )
    model = EVAdoptionModel(params, seed=42)

    model._add_demand_chargers(2)

    assert len(model.chargers) == 2


def test_unknown_charger_expansion_mode_raises():
    params = EVParams(width=5, height=5, number_of_agents=3)
    model = EVAdoptionModel(params, seed=42)
    model.params.charger_expansion_mode = "bogus"

    with pytest.raises(ValueError):
        model._expand_charging_infrastructure()


def test_social_diffusion_off_by_default_and_traits_static():
    assert EVParams().social_diffusion is False
    params = EVParams(width=8, height=8, number_of_agents=15)
    model = EVAdoptionModel(params, seed=42)
    traits = [
        (agent.range_anxiety, agent.environmental_concern)
        for agent in model.agent_list
    ]

    model.run_model(5)

    assert [
        (agent.range_anxiety, agent.environmental_concern)
        for agent in model.agent_list
    ] == traits


def test_social_diffusion_updates_perceptions_near_adopters():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        social_diffusion=True,
        initial_ev_share=0.5,
    )
    model = EVAdoptionModel(params, seed=42)
    candidates = [
        agent
        for agent in model.agent_list
        if not agent.ev_adopted
        and agent._peer_adoption_share() > 0
        and (
            agent.range_anxiety > params.range_anxiety_min
            or agent.environmental_concern < params.environmental_concern_max
        )
    ]
    assert candidates
    agent = candidates[0]
    range_anxiety = agent.range_anxiety
    environmental_concern = agent.environmental_concern

    model.run_model(3)

    assert (
        agent.range_anxiety < range_anxiety
        or agent.range_anxiety == params.range_anxiety_min
    )
    assert (
        agent.environmental_concern > environmental_concern
        or agent.environmental_concern == params.environmental_concern_max
    )


def test_social_diffusion_respects_bounds():
    params = EVParams(
        width=8,
        height=8,
        number_of_agents=12,
        social_diffusion=True,
        initial_ev_share=1.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    agent.range_anxiety = params.range_anxiety_min
    agent.environmental_concern = params.environmental_concern_max

    agent._diffuse_perceptions()

    assert agent.range_anxiety == params.range_anxiety_min
    assert agent.environmental_concern == params.environmental_concern_max


def test_social_diffusion_same_seed_reproducible():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        social_diffusion=True,
        initial_ev_share=0.3,
    )
    first = EVAdoptionModel(params, seed=5)
    second = EVAdoptionModel(params, seed=5)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_supply_and_learning_defaults_are_inactive():
    params = EVParams(width=8, height=8, number_of_agents=15)
    assert EVParams().ev_supply_per_step == float("inf")
    assert EVParams().ev_price_learning_rate == 0.0

    model = EVAdoptionModel(params, seed=42)
    assert model.effective_ev_price == params.ev_purchase_price

    first = EVAdoptionModel(params, seed=11)
    second = EVAdoptionModel(params, seed=11)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_supply_cap_limits_adoptions_per_step():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=30,
        ev_supply_per_step=1,
        subsidy=30000.0,
        adoption_threshold=0.0,
        income_budget_share=1.0,  # isolate the supply cap from the affordability gate
        vehicle_age_min=12,
        vehicle_age_max=12,
        stagger_initial_vehicle_age=False,
        replacement_interval_min=6,
        replacement_interval_max=6,
    )
    model = EVAdoptionModel(params, seed=42)

    model.run_model(5)

    counts = model.datacollector.get_model_vars_dataframe()["ev_adoption_count"]
    increases = counts.diff().iloc[1:]

    assert all(increase <= 1 for increase in increases)
    assert counts.iloc[-1] == 5
    assert model.datacollector.get_model_vars_dataframe().iloc[-1].ev_supply_blocked > 0


def test_supply_blocked_agents_adopt_later():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=30,
        ev_supply_per_step=1,
        subsidy=30000.0,
        adoption_threshold=0.0,
        income_budget_share=1.0,  # isolate the supply cap from the affordability gate
        vehicle_age_min=12,
        vehicle_age_max=12,
        stagger_initial_vehicle_age=False,
        replacement_interval_min=6,
        replacement_interval_max=6,
    )
    model = EVAdoptionModel(params, seed=42)

    model.run_model(12)

    counts = model.datacollector.get_model_vars_dataframe()["ev_adoption_count"]
    increases = counts.diff().iloc[1:]

    assert all(increase == 1 for increase in increases)


def test_price_learning_lowers_effective_price_with_floor():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        initial_ev_share=0.5,
        ev_price_learning_model="linear",
        ev_price_learning_rate=0.4,
    )
    model = EVAdoptionModel(params, seed=3)

    assert model.effective_ev_price == pytest.approx(
        params.ev_purchase_price * (1 - 0.4 * 0.5)
    )

    model.ev_adoption_share = 1.0
    model.params.ev_price_learning_rate = 0.9

    assert model._effective_ev_price() == pytest.approx(
        params.ev_purchase_price * params.ev_price_floor_share
    )


def test_supply_constrained_same_seed_reproducible():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=25,
        ev_supply_per_step=2,
        initial_ev_share=0.2,
    )
    first = EVAdoptionModel(params, seed=8)
    second = EVAdoptionModel(params, seed=8)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_infinite_capacity_aliases_raw_access():
    params = EVParams(width=8, height=8, number_of_agents=15)
    model = EVAdoptionModel(params, seed=42)

    assert model.effective_charging_access is model.charging_access
    assert model.mean_charger_congestion == 0.0

    model.run_model(5)

    assert model.effective_charging_access is model.charging_access

    first = EVAdoptionModel(params, seed=11)
    second = EVAdoptionModel(params, seed=11)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_finite_capacity_discounts_access_under_demand():
    params = EVParams(
        width=12,
        height=12,
        number_of_agents=30,
        initial_ev_share=0.5,
        initial_ev_clustered=True,
        initial_charging_coverage=0.01,
        charger_expansion_rate=0.0,
        charger_capacity=1.0,
        congestion_radius=2,
    )
    model = EVAdoptionModel(params, seed=42)

    assert model.effective_charging_access is not model.charging_access
    assert np.all(model.effective_charging_access <= model.charging_access + 1e-12)
    assert model.effective_charging_access.sum() < model.charging_access.sum()
    assert model.mean_charger_congestion > 0.0


def test_high_capacity_behaves_like_uncongested():
    params = EVParams(
        width=12,
        height=12,
        number_of_agents=30,
        initial_ev_share=0.5,
        initial_ev_clustered=True,
        initial_charging_coverage=1.0,
        charger_expansion_rate=0.0,
        charger_capacity=1000.0,
        congestion_radius=2,
    )
    model = EVAdoptionModel(params, seed=42)

    assert np.allclose(model.effective_charging_access, model.charging_access)


def test_agent_reads_effective_access():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=1,
        charger_capacity=5.0,
        initial_charging_coverage=0.0,
        charger_expansion_rate=0.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    agent.home_charging_access = 0.0
    model.charging_access[:, :] = 0.0
    model.effective_charging_access = np.zeros_like(model.charging_access)
    model.effective_charging_access[agent.home_pos] = 1.0

    agent.consider_ev_adoption()

    assert agent.last_charging_score == pytest.approx(0.3)


def test_congested_same_seed_reproducible():
    params = EVParams(
        width=12,
        height=12,
        number_of_agents=25,
        initial_ev_share=0.3,
        charger_capacity=2.0,
        initial_charging_coverage=0.02,
    )
    first = EVAdoptionModel(params, seed=6)
    second = EVAdoptionModel(params, seed=6)

    first.run_model(10)
    second.run_model(10)

    assert_frame_equal(
        first.datacollector.get_model_vars_dataframe(),
        second.datacollector.get_model_vars_dataframe(),
    )


def test_env_score_weight_default_matches_previous_blend():
    assert EVParams().env_score_pro_env_weight == 0.5
    params = EVParams(width=5, height=5, number_of_agents=3)
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]

    agent.consider_ev_adoption()

    assert agent.last_environmental_score == pytest.approx(
        0.5 * agent.environmental_concern + 0.5 * agent.pro_env
    )


def test_env_score_weight_zero_uses_concern_only():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        env_score_pro_env_weight=0.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]

    agent.consider_ev_adoption()

    assert agent.last_environmental_score == pytest.approx(agent.environmental_concern)


def test_env_score_weight_one_uses_pro_env_only():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        env_score_pro_env_weight=1.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]

    agent.consider_ev_adoption()

    assert agent.last_environmental_score == pytest.approx(agent.pro_env)


# --- Model-review fixes: range anxiety, budget gate, staggered age, ---
# --- price learning models, discounting, income/home-charging realism, ---
# --- and time-varying price schedules.                                ---


def test_range_anxiety_penalty_discounted_by_effective_access():
    params = EVParams(width=5, height=5, number_of_agents=3, range_anxiety_weight=0.5)
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    agent.range_anxiety = 0.8
    home_x, home_y = agent.home_pos

    model.effective_charging_access[home_x, home_y] = 1.0
    agent.consider_ev_adoption()
    assert agent.last_range_anxiety_penalty == pytest.approx(0.0)

    agent.has_evaluated_adoption = False
    model.effective_charging_access[home_x, home_y] = 0.0
    agent.consider_ev_adoption()
    assert agent.last_range_anxiety_penalty == pytest.approx(
        params.range_anxiety_weight * agent.range_anxiety
    )


def test_income_budget_gate_blocks_unaffordable_agents_even_if_score_passes():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        adoption_threshold=-1e6,  # score-based decision always passes
        income_budget_share=0.10,
        ev_purchase_price=100000.0,
        subsidy=0.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    agent.income = 100.0  # far too poor to afford even 10% of a cheap EV

    agent.consider_ev_adoption()

    assert agent.last_affordable is False
    assert agent.ev_adopted is False


def test_income_budget_gate_allows_affordable_agents():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        adoption_threshold=-1e6,
        income_budget_share=0.10,
        ev_purchase_price=10000.0,
        subsidy=10000.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]
    agent.income = 1_000_000.0  # trivially affordable

    agent.consider_ev_adoption()

    assert agent.last_affordable is True
    assert agent.ev_adopted is True


def test_price_sensitivity_and_peer_sensitivity_default_bounds():
    params = EVParams()
    assert params.price_sensitivity_min == 0.5
    assert params.price_sensitivity_max == 1.5
    assert params.peer_sensitivity_min == 0.5
    assert params.peer_sensitivity_max == 1.5


def test_economic_component_uses_price_sensitivity_directly_not_shifted():
    params = EVParams(width=5, height=5, number_of_agents=3)
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]

    agent.consider_ev_adoption()

    from affordance_mesa.ev_costs import economic_score

    expected = economic_score(agent.last_ev_tco, agent.last_ice_tco) * agent.price_sensitivity
    assert agent.last_economic_score == pytest.approx(expected)


def test_stagger_initial_vehicle_age_stays_below_replacement_interval():
    params = EVParams(width=10, height=10, number_of_agents=50)
    assert params.stagger_initial_vehicle_age is True
    model = EVAdoptionModel(params, seed=42)

    assert all(
        agent.vehicle_age < agent.replacement_interval for agent in model.agent_list
    )


def test_disabling_stagger_uses_independent_vehicle_age_bounds():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=10,
        stagger_initial_vehicle_age=False,
        vehicle_age_min=20,
        vehicle_age_max=20,
        replacement_interval_min=6,
        replacement_interval_max=6,
    )
    model = EVAdoptionModel(params, seed=42)

    assert all(agent.vehicle_age == 20 for agent in model.agent_list)


def test_discount_rate_reduces_tco_relative_to_zero_rate():
    kwargs = dict(
        annual_mileage=12000,
        maintenance_cost=300,
        years=8,
    )
    undiscounted = ev_tco(purchase_price=35000, electricity_price=0.25, kwh_per_km=0.18, **kwargs)
    discounted = ev_tco(
        purchase_price=35000, electricity_price=0.25, kwh_per_km=0.18, discount_rate=0.05, **kwargs
    )
    assert discounted < undiscounted

    ice_kwargs = dict(annual_mileage=12000, maintenance_cost=600, years=8)
    ice_undiscounted = ice_tco(purchase_price=25000, fuel_price=1.8, liters_per_km=0.07, **ice_kwargs)
    ice_discounted = ice_tco(
        purchase_price=25000, fuel_price=1.8, liters_per_km=0.07, discount_rate=0.05, **ice_kwargs
    )
    assert ice_discounted < ice_undiscounted


def test_discount_rate_zero_matches_flat_multiplication():
    total = ev_tco(
        purchase_price=35000,
        electricity_price=0.25,
        annual_mileage=12000,
        kwh_per_km=0.18,
        maintenance_cost=300,
        years=8,
        discount_rate=0.0,
    )
    expected = 35000 + (12000 * 0.18 * 0.25 + 300) * 8
    assert total == pytest.approx(expected)


def test_wright_law_price_declines_with_cumulative_adopters():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        ev_price_learning_model="wright",
        ev_wright_learning_rate=0.18,
        ev_wright_reference_adopters=1,
    )
    model = EVAdoptionModel(params, seed=42)

    model.ev_adoption_count = 1
    price_at_one = model._effective_ev_price()
    model.ev_adoption_count = 2
    price_at_two = model._effective_ev_price()

    assert price_at_two < price_at_one
    # One doubling should cut price by exactly the learning rate.
    assert price_at_two == pytest.approx(price_at_one * (1 - params.ev_wright_learning_rate))


def test_wright_law_price_floors_like_linear_model():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=20,
        ev_price_learning_model="wright",
        ev_wright_learning_rate=0.5,
        ev_wright_reference_adopters=1,
        ev_price_floor_share=0.5,
    )
    model = EVAdoptionModel(params, seed=42)
    model.ev_adoption_count = 10_000

    assert model._effective_ev_price() == pytest.approx(
        params.ev_purchase_price * params.ev_price_floor_share
    )


def test_unknown_price_learning_model_raises():
    params = EVParams(width=5, height=5, number_of_agents=3)
    model = EVAdoptionModel(params, seed=42)
    model.params.ev_price_learning_model = "bogus"

    with pytest.raises(ValueError):
        model._effective_ev_price()


def test_lognormal_income_is_positive_and_right_skewed():
    params = EVParams(
        width=10,
        height=10,
        number_of_agents=200,
        income_distribution="lognormal",
    )
    model = EVAdoptionModel(params, seed=42)

    incomes = np.array([agent.income for agent in model.agent_list])
    assert (incomes > 0).all()
    assert np.mean(incomes) == pytest.approx(params.income_mean, rel=0.25)
    # Right-skewed: mean should exceed the median.
    assert np.mean(incomes) > np.median(incomes)


def test_unknown_income_distribution_raises():
    params = EVParams(width=5, height=5, number_of_agents=1, income_distribution="bogus")

    with pytest.raises(ValueError):
        EVAdoptionModel(params, seed=42)


def test_home_charging_income_weight_zero_ignores_income_argument():
    params = EVParams(width=5, height=5, number_of_agents=3)
    assert params.home_charging_income_weight == 0.0
    model = EVAdoptionModel(params, seed=99)

    state = model.rng.bit_generator.state
    low = model._sample_home_charging_access(0.0)
    model.rng.bit_generator.state = state
    high = model._sample_home_charging_access(1_000_000.0)

    # Same underlying RNG draw regardless of income when the weight is zero.
    assert low == pytest.approx(high)


def test_home_charging_income_weight_one_matches_income_percentile():
    params = EVParams(width=5, height=5, number_of_agents=3, home_charging_income_weight=1.0)
    model = EVAdoptionModel(params, seed=42)

    low_income_access = model._sample_home_charging_access(params.income_mean - 5 * params.income_sd)
    high_income_access = model._sample_home_charging_access(params.income_mean + 5 * params.income_sd)

    assert low_income_access < 0.01
    assert high_income_access > 0.99


def test_fuel_price_schedule_overrides_scalar_and_holds_last_value():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        fuel_price=1.8,
        fuel_price_schedule=(1.0, 2.0, 3.0),
    )
    model = EVAdoptionModel(params, seed=42)

    assert model.current_fuel_price == pytest.approx(1.0)
    model.step()
    assert model.current_fuel_price == pytest.approx(2.0)
    model.step()
    assert model.current_fuel_price == pytest.approx(3.0)
    model.step()
    assert model.current_fuel_price == pytest.approx(3.0)  # holds last value once exhausted


def test_no_schedule_uses_flat_scalar_price():
    params = EVParams(width=5, height=5, number_of_agents=3, fuel_price=2.2)
    model = EVAdoptionModel(params, seed=42)

    assert model.current_fuel_price == pytest.approx(2.2)
    model.step()
    assert model.current_fuel_price == pytest.approx(2.2)


def test_subsidy_schedule_feeds_into_ev_cost():
    params = EVParams(
        width=5,
        height=5,
        number_of_agents=3,
        subsidy=0.0,
        subsidy_schedule=(5000.0,),
        ev_price_learning_rate=0.0,
    )
    model = EVAdoptionModel(params, seed=42)
    agent = model.agent_list[0]

    agent.consider_ev_adoption()

    assert model.current_subsidy == pytest.approx(5000.0)
    assert agent.last_ev_tco == pytest.approx(
        max(params.ev_purchase_price - 5000.0, 0.0)
        + (
            agent.annual_mileage * params.ev_kwh_per_km * params.electricity_price
            + params.ev_maintenance_cost
        )
        * params.tco_years
    )
