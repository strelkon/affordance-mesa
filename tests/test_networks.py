from affordance_mesa.networks import create_social_network


def test_network_generators_have_expected_nodes():
    for network_type in ["random", "small-world", "preferential", "KE"]:
        g = create_social_network(50, network_type, 5, seed=1)
        assert g.number_of_nodes() == 50
