"""Parameter set for the EV extension of the affordance model."""

from __future__ import annotations

from dataclasses import dataclass

from .model import AffordanceModelParams


@dataclass
class EVParams(AffordanceModelParams):
    """Affordance model parameters plus EV-specific policy and cost inputs."""

    width: int = 201
    height: int = 201
    max_steps: int = 20440

    lower_bound_mean: float = 0.2
    lower_bound_sd: float = 0.05
    upper_bound_mean: float = 0.8
    upper_bound_sd: float = 0.05

    initial_charging_coverage: float = 0.0
    # Calibrated against Portugal's 2010-2024 BEV fleet-share series (see
    # ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md and
    # scripts/calibrate_portugal.py); RMSE ~0.003 against the target curve at
    # the "portugal_2010_2024" scenario's scale (see note below -- the fit is
    # scale-dependent since charger rollout is not agent-count-scaled).
    charger_expansion_rate: float = 1.1
    charger_expansion_mode: str = "exogenous"
    demand_expansion_gain: float = 4.0
    demand_radius: int = 2
    charger_access_decay: float = 1.0
    charger_capacity: float = float("inf")
    congestion_radius: int = 3

    subsidy: float = 8000.0
    fuel_price: float = 1.8
    electricity_price: float = 0.25
    # Optional per-step override sequences for policy/price paths (e.g. a
    # historical or scenario time series). None keeps the flat scalar above;
    # once a sequence is exhausted its last value holds.
    subsidy_schedule: tuple | None = None
    fuel_price_schedule: tuple | None = None
    electricity_price_schedule: tuple | None = None
    ev_supply_per_step: float = float("inf")
    ev_price_learning_rate: float = 0.0
    ev_price_floor_share: float = 0.5
    # "linear" (backward-compatible proxy) or "wright" (Wright's-law
    # experience curve keyed on cumulative adopters). Calibrated to "wright"
    # against the Portugal target (see calibrate_portugal.py); pass
    # ev_price_learning_model="linear" to recover the old flat-price behaviour.
    ev_price_learning_model: str = "wright"
    ev_wright_learning_rate: float = 0.23
    ev_wright_reference_adopters: int = 10
    # Average annual TCO cannot exceed this share of income (paper's "10% of
    # income" affordability rule), enforced as a hard adoption gate. The
    # Portugal calibration search converged close to the original 0.10 guess.
    income_budget_share: float = 0.10
    discount_rate: float = 0.0

    # Calibrated against Portugal's 2010-2024 BEV fleet-share series (see
    # ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md and
    # scripts/calibrate_portugal.py) rather than picked ad hoc.
    ev_purchase_price: float = 39500.0
    ice_purchase_price: float = 23000.0
    ev_kwh_per_km: float = 0.18
    ice_liters_per_km: float = 0.07
    ev_maintenance_cost: float = 300.0
    ice_maintenance_cost: float = 600.0
    tco_years: int = 8

    initial_ev_share: float = 0.0
    initial_ev_clustered: bool = False
    # Calibrated against the Portugal target curve (see
    # scripts/calibrate_portugal.py); markedly lower than an uncalibrated
    # guess since the income-budget gate above already screens out most
    # low-income agents before the score-based threshold is even checked.
    adoption_threshold: float = 0.085
    adoption_rule: str = "deterministic"
    adoption_temperature: float = 0.05
    economic_weight: float = 0.25
    charging_weight: float = 0.25
    environmental_weight: float = 0.25
    # Weight of dynamic pro_env in the EV environmental score; 1 - weight is environmental_concern.
    # 0.0 = EV preference only, 1.0 = affordance state only.
    env_score_pro_env_weight: float = 0.5
    peer_weight: float = 0.15
    range_anxiety_weight: float = 0.10

    # Effective purchasing-power parameters fitted to the Portugal adoption
    # curve (scripts/calibrate_portugal.py) -- NOT an empirical Portuguese
    # income distribution (mean household disposable income there is roughly
    # EUR 20k+). The adoption curve only constrains the product of income
    # scale and income_budget_share against annual EV cost, so these are
    # jointly identified with income_budget_share; to use empirical incomes,
    # pin income_mean/sd to Eurostat/INE data and refit income_budget_share.
    income_mean: float = 9000.0
    income_sd: float = 9000.0
    # "normal" (backward-compatible truncated normal) or "lognormal"
    # (right-skewed, matching the empirical income distribution; matched to
    # the same mean/sd). Calibrated to "lognormal".
    income_distribution: str = "lognormal"
    annual_mileage_mean: float = 12000.0
    annual_mileage_sd: float = 2000.0
    vehicle_age_min: int = 1
    vehicle_age_max: int = 12
    # When True (default), initial vehicle_age is drawn in
    # [0, replacement_interval - 1] instead of from vehicle_age_min/max,
    # avoiding a synchronized replacement burst at step 1. Set False to use
    # vehicle_age_min/max directly (e.g. to force immediate evaluation in
    # tests/scenarios).
    stagger_initial_vehicle_age: bool = True
    replacement_interval_min: int = 6
    replacement_interval_max: int = 14
    home_charging_min: float = 0.0
    home_charging_max: float = 1.0
    # Blends home_charging_access toward an income-based percentile (garage
    # ownership correlates with income); 0.0 keeps it fully independent.
    home_charging_income_weight: float = 0.0
    environmental_concern_min: float = 0.0
    environmental_concern_max: float = 1.0
    # Rescaled to [0.5, 1.5] so the score can use the trait directly instead
    # of the old "(0.5 + trait)" expression; identical distribution.
    price_sensitivity_min: float = 0.5
    price_sensitivity_max: float = 1.5
    range_anxiety_min: float = 0.0
    range_anxiety_max: float = 1.0
    peer_sensitivity_min: float = 0.5
    peer_sensitivity_max: float = 1.5
    social_diffusion: bool = False
    peer_range_anxiety_relief: float = 0.02
    peer_concern_gain: float = 0.01

    @classmethod
    def from_scenario(cls, name, **overrides):
        if name not in SCENARIOS:
            raise ValueError(f"Unknown scenario {name!r}; valid: {sorted(SCENARIOS)}")
        return cls(**{**SCENARIOS[name], **overrides})


# Zero for 2010-2014, then a linear ramp from EUR500 to EUR4,000 over
# 2015-2024, approximating the real 2015 EV-incentive reintroduction and the
# documented ~EUR2,000-4,000 grant range (PORTUGAL_CALIBRATION_DATA.md). A
# smooth ramp avoids an artificial batch-adoption jump the year the subsidy
# changes; exact year-by-year historical amounts are not available at that
# resolution in the sourced data.
_PORTUGAL_SUBSIDY_SCHEDULE = (
    0.0, 0.0, 0.0, 0.0, 0.0,
    500.0, 888.9, 1277.8, 1666.7, 2055.6,
    2444.4, 2833.3, 3222.2, 3611.1, 4000.0,
)

# Provisional proposals relative to the defaults; users can tune every value.
SCENARIOS: dict[str, dict] = {
    "colleague_baseline": {"number_of_agents": 100},
    "no_policy": {
        "subsidy": 0.0,
        "charger_expansion_rate": 0.0,
        "initial_charging_coverage": 0.0,
    },
    "subsidy": {"subsidy": 12000.0},
    "fuel_price": {"fuel_price": 2.6},
    "charging_expansion": {
        "charger_expansion_rate": 6.0,
        "initial_charging_coverage": 0.02,
    },
    # Reproduces the Portugal 2010-2024 BEV fleet-share calibration
    # (RMSE ~0.003 against outputs/portugal_ev_stock_share_targets.csv over
    # 12 seeds at this scenario's number_of_agents; see
    # ev_adoption_models/PORTUGAL_CALIBRATION_DATA.md and
    # scripts/calibrate_portugal.py). step 0 = 2010, step 14 = 2024.
    # NOTE: charger_expansion_rate is an absolute chargers-per-step rate, not
    # scaled to number_of_agents, so the fit is tied to number_of_agents=4000
    # on this width x height grid -- changing either without rescaling
    # charger_expansion_rate will shift the charging-access/range-anxiety
    # balance and degrade the fit.
    "portugal_2010_2024": {
        "width": 60,
        "height": 60,
        "number_of_agents": 4000,
        "max_steps": 14,
        "subsidy_schedule": _PORTUGAL_SUBSIDY_SCHEDULE,
    },
}
