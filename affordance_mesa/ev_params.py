from dataclasses import dataclass

@dataclass
class EVParams:
    # --- Grid ---
    width: int = 20
    height: int = 20

    # ============================================================
    # === BASE MODEL PARAMETERS ===============
    # ============================================================

    # Initial states
    initial_pro: float = 0.5
    initial_non: float = 0.5

    # Learning
    asocial_learning: float = 0.05
    social_learning: float = 0.05

    # Mutation
    mutation_rate: float = 0.01

    # Attempts at behavior
    max_behavior_attempts: int = 10

    # Niche construction
    niche_construction: bool = False
    construct_pro: float = 0.1

    # Social Networks
    networks: bool = False
    network_type: str = "small_world"
    rewiring_prob: float = 0.1

    # Number of agents
    number_of_agents: int = 0   # vamos ignorar, porque criamos os nossos EV agents

    # Bounds 
    lower_bound: float = 0.2
    upper_bound: float = 0.8

    # ============================================================
    # === EV parameters  ==================================
    # ============================================================

    subsidy: float = 0.0
    fuel_price: float = 1.8
    electricity_price: float = 0.25
    charger_expansion_rate: float = 0.02
    adoption_threshold: float = 0.5

    economic_weight: float = 0.25
    charging_weight: float = 0.25
    environmental_weight: float = 0.25
    peer_weight: float = 0.15
    range_anxiety_weight: float = 0.10




