from dataclasses import dataclass

@dataclass
class AffordanceModelParams:
    width: int = 20
    height: int = 20
    network_type: str = "small_world"
    rewiring_prob: float = 0.1
