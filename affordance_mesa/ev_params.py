"""Parameter set for the EV extension of the affordance model."""

from __future__ import annotations

from dataclasses import dataclass

from .model import AffordanceModelParams


@dataclass
class EVParams(AffordanceModelParams):
    """Affordance model parameters plus EV-specific policy and cost inputs."""

    width: int = 20
    height: int = 20
    max_steps: int = 1000

    lower_bound_mean: float = 0.2
    lower_bound_sd: float = 0.05
    upper_bound_mean: float = 0.8
    upper_bound_sd: float = 0.05

    initial_charging_coverage: float = 0.05
    charger_expansion_rate: float = 0.2
    charger_access_decay: float = 2.0

    subsidy: float = 0.0
    fuel_price: float = 1.8
    electricity_price: float = 0.25

    ev_purchase_price: float = 35000.0
    ice_purchase_price: float = 25000.0
    ev_kwh_per_km: float = 0.18
    ice_liters_per_km: float = 0.07
    ev_maintenance_cost: float = 300.0
    ice_maintenance_cost: float = 600.0
    tco_years: int = 8

    adoption_threshold: float = 0.5
    economic_weight: float = 0.25
    charging_weight: float = 0.25
    environmental_weight: float = 0.25
    peer_weight: float = 0.15
    range_anxiety_weight: float = 0.10

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
