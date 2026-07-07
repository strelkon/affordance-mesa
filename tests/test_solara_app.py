from affordance_mesa.ev_params import EVParams
from affordance_mesa.solara_app import Page, _params_from_controls


def test_solara_page_is_importable():
    assert Page is not None


def test_solara_controls_build_ev_params():
    params = _params_from_controls(
        number_of_agents=100,
        width=201,
        height=201,
        max_steps=1000,
        pro_amount=0.5,
        initial_pro=0.5,
        initial_non=0.5,
        networks=False,
        network_type="KE",
        network_param=5.0,
        mu=0.9,
        subsidy=8000.0,
        fuel_price=1.8,
        electricity_price=0.25,
        initial_charging_coverage=0.0,
        charger_expansion_rate=2.0,
        charger_access_decay=1.0,
        adoption_threshold=0.34,
        economic_weight=0.25,
        charging_weight=0.25,
        environmental_weight=0.25,
        peer_weight=0.15,
        range_anxiety_weight=0.10,
        income_mean=30000.0,
        annual_mileage_mean=12000.0,
    )

    assert isinstance(params, EVParams)
    assert params.subsidy == 8000.0
    assert params.adoption_threshold == 0.34


def test_scenarios_importable_from_solara_app():
    from affordance_mesa import solara_app

    assert "subsidy" in solara_app.SCENARIOS
