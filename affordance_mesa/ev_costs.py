"""
Pure cost functions for EV and ICE vehicles.
These functions do NOT depend on Mesa, agents, or the model.
They are simple mathematical utilities.
"""

import math


def _annuity_factor(years, discount_rate):
    """Present-value factor for a `years`-long stream of unit annual costs.

    Degenerates to ``years`` when ``discount_rate == 0``, so undiscounted
    callers get exactly the old flat-multiplication behaviour.
    """
    if discount_rate == 0:
        return float(years)
    return sum(1.0 / (1.0 + discount_rate) ** k for k in range(1, years + 1))


def ev_tco(purchase_price, electricity_price, annual_mileage, kwh_per_km, maintenance_cost, years, discount_rate=0.0):
    """
    Total Cost of Ownership for an EV over N years.
    """
    annual_cost = annual_mileage * kwh_per_km * electricity_price + maintenance_cost
    total = purchase_price + annual_cost * _annuity_factor(years, discount_rate)
    return total


def ice_tco(purchase_price, fuel_price, annual_mileage, liters_per_km, maintenance_cost, years, discount_rate=0.0):
    """
    Total Cost of Ownership for an ICE vehicle over N years.
    """
    annual_cost = annual_mileage * liters_per_km * fuel_price + maintenance_cost
    total = purchase_price + annual_cost * _annuity_factor(years, discount_rate)
    return total


def economic_score(ev_tco_value, ice_tco_value):
    """
    Positive score means EV is economically attractive.
    Normalized difference between ICE and EV TCO.
    """
    if ice_tco_value == 0:
        return 0.0

    score = (ice_tco_value - ev_tco_value) / ice_tco_value
    return score


def adoption_probability(score, threshold, temperature):
    """Logistic probability of adoption; temperature <= 0 degenerates to a step function."""
    if temperature <= 0:
        return 1.0 if score >= threshold else 0.0

    z = (score - threshold) / temperature
    z = max(min(z, 60.0), -60.0)
    if z == 60.0:
        return 1.0
    if z == -60.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-z))



