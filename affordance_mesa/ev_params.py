from dataclasses import dataclass

@dataclass
class EVParams:
    """
    Parâmetros para o modelo EVAdoptionModel.
    Compatível com AffordanceModelParams.
    """

    # ---------------------------------------------------------
    # Parâmetros obrigatórios do modelo base
    # ---------------------------------------------------------
    number_of_agents: int = 100
    width: int = 201
    height: int = 201

    pro_amount: float = 0.5
    initial_pro: float = 0.5
    initial_non: float = 0.5

    asocial_learning: float = 0.00005
    social_learning: float = 0.00007

    networks: bool = False
    network_type: str = "KE"
    network_param: float = 5.0

    mu: float = 0.9

    niche_construction: bool = False
    construct_pro: float = 5.0
    construct_non: float = 5.0

    mutate_on: bool = False
    mutate_prob: float = 0.005
    mutate_rate: float = 0.05

    max_steps: int = 20440
    max_behavior_attempts: int = 1000

    # Estes quatro são OBRIGATÓRIOS no modelo base
    lower_bound_mean: float = 0.2
    lower_bound_sd: float = 0.05
    upper_bound_mean: float = 0.8
    upper_bound_sd: float = 0.05

    # ---------------------------------------------------------
    # Parâmetros EV — política / cenário
    # ---------------------------------------------------------
    subsidy: float = 8000.0
    fuel_price: float = 1.8
    electricity_price: float = 0.25
    charger_expansion_rate: int = 2
    adoption_threshold: float = 0.5

    # ---------------------------------------------------------
    # Pesos da regra de adoção
    # ---------------------------------------------------------
    economic_weight: float = 0.25
    charging_weight: float = 0.25
    environmental_weight: float = 0.25
    peer_weight: float = 0.15
    range_anxiety_weight: float = 0.10

    # ---------------------------------------------------------
    # Parâmetros de geração de atributos EV dos agentes
    # ---------------------------------------------------------
    income_mean: float = 30000.0
    income_sd: float = 8000.0

    annual_mileage_mean: float = 12000.0
    annual_mileage_sd: float = 2000.0

    vehicle_age_min: int = 1
    vehicle_age_max: int = 12

    replacement_interval_min: int = 6
    replacement_interval_max: int = 14

    home_charging_min: float = 0.0
    home_charging_max: float = 1.0

    environmental_concern_min: float = 0.0
    environmental_concern_max: float = 1.0

    price_sensitivity_min: float = 0.0
    price_sensitivity_max: float = 1.0

    range_anxiety_min: float = 0.0
    range_anxiety_max: float = 1.0

    peer_sensitivity_min: float = 0.0
    peer_sensitivity_max: float = 1.0
