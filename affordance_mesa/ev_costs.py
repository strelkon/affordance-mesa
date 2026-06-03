"""
Pure cost functions for EV and ICE vehicles.
These functions do NOT depend on Mesa, agents, or the model.
They are simple mathematical utilities.
"""

def ev_tco(purchase_price, electricity_price, annual_mileage, kwh_per_km, maintenance_cost, years):
    """
    Total Cost of Ownership for an EV over N years.
    """
    energy_cost = annual_mileage * kwh_per_km * electricity_price * years
    total = purchase_price + energy_cost + maintenance_cost * years
    return total


def ice_tco(purchase_price, fuel_price, annual_mileage, liters_per_km, maintenance_cost, years):
    """
    Total Cost of Ownership for an ICE vehicle over N years.
    """
    fuel_cost = annual_mileage * liters_per_km * fuel_price * years
    total = purchase_price + fuel_cost + maintenance_cost * years
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





