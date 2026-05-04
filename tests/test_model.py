from affordance_mesa import AffordanceLandscapeModel, AffordanceModelParams


def test_model_runs_and_collects_consistent_state():
    params = AffordanceModelParams(
        number_of_agents=25,
        width=25,
        height=25,
        max_steps=10,
    )

    model = AffordanceLandscapeModel(params=params, seed=74)
    model.run_model(10)

    assert len(model.agent_list) == params.number_of_agents

    model_vars = model.datacollector.get_model_vars_dataframe()
    assert not model_vars.empty

    behaviour_counts = model_vars["pro_behaviour"] + model_vars["non_behaviour"]
    assert (behaviour_counts <= params.number_of_agents).all()

    for agent in model.agent_list:
        assert agent.lower_bound <= agent.pro_env <= agent.upper_bound
        assert agent.lower_bound <= agent.non_env <= agent.upper_bound
