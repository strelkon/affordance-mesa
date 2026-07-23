"""EV-enabled agents built as a subclass of the affordance ConsumerAgent.

Interpretation: the model carries two environmental layers. ``pro_env`` is the
general pro-environmental affordance state inherited from ``ConsumerAgent``; it
is dynamic through asocial/social affordance learning and bounded by the
agent's lower and upper bounds. ``environmental_concern`` is an EV-specific
preference trait, fixed at initialization unless social diffusion is enabled.
The EV environmental score blends the two with
``env_score_pro_env_weight``. Grid movement belongs to the abstract affordance
landscape, while EV adoption is tied to the residential ``home_pos``.
"""

from __future__ import annotations

from .agents import ConsumerAgent
from .ev_costs import adoption_probability, economic_score, ev_tco, ice_tco


class EVConsumerAgent(ConsumerAgent):
    """Consumer agent with an additional vehicle replacement decision.

    ``pos`` represents movement through the abstract affordance landscape
    inherited from ``ConsumerAgent``. ``home_pos`` is the fixed residential
    location used for EV charging access and spatial peer exposure.
    """

    def __init__(
        self,
        model,
        pro_env: float,
        non_env: float,
        lower_bound: float,
        upper_bound: float,
        *,
        income: float,
        annual_mileage: float,
        vehicle_age: int,
        replacement_interval: int,
        home_charging_access: float,
        environmental_concern: float,
        price_sensitivity: float,
        range_anxiety: float,
        peer_sensitivity: float,
    ) -> None:
        super().__init__(
            model=model,
            pro_env=pro_env,
            non_env=non_env,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

        self.income = income
        self.annual_mileage = annual_mileage
        self.vehicle_age = vehicle_age
        self.replacement_interval = replacement_interval
        self.home_charging_access = home_charging_access
        self.environmental_concern = environmental_concern
        self.price_sensitivity = price_sensitivity
        self.range_anxiety = range_anxiety
        self.peer_sensitivity = peer_sensitivity
        self.ev_adopted = False
        self.home_pos: tuple[int, int] | None = None

        self.last_adoption_score = 0.0
        self.last_charging_score = 0.0
        self.last_economic_score = 0.0
        self.last_environmental_score = 0.0
        self.last_adoption_probability = 0.0
        self.last_peer_adoption_share = 0.0
        self.last_range_anxiety_penalty = 0.0
        self.last_tco_gap = 0.0
        self.last_ev_tco = 0.0
        self.last_ice_tco = 0.0
        self.has_evaluated_adoption = False
        self.last_affordable = True

    def step(self) -> None:
        """Run original affordance behaviour, then the EV decision layer."""

        super().step()
        self.vehicle_age += 1

        if self.model.params.social_diffusion:
            self._diffuse_perceptions()

        if self.vehicle_age >= self.replacement_interval and not self.ev_adopted:
            self.consider_ev_adoption()

    def consider_ev_adoption(self) -> None:
        p = self.model.params
        home_x, home_y = self.home_pos

        subsidy = self.model.current_subsidy
        ev_cost = ev_tco(
            purchase_price=max(self.model.effective_ev_price - subsidy, 0.0),
            electricity_price=self.model.current_electricity_price,
            annual_mileage=self.annual_mileage,
            kwh_per_km=p.ev_kwh_per_km,
            maintenance_cost=p.ev_maintenance_cost,
            years=p.tco_years,
            discount_rate=p.discount_rate,
        )
        ice_cost = ice_tco(
            purchase_price=p.ice_purchase_price,
            fuel_price=self.model.current_fuel_price,
            annual_mileage=self.annual_mileage,
            liters_per_km=p.ice_liters_per_km,
            maintenance_cost=p.ice_maintenance_cost,
            years=p.tco_years,
            discount_rate=p.discount_rate,
        )

        tco_gap = ice_cost - ev_cost
        tco_score = economic_score(ev_cost, ice_cost)
        economic_component = tco_score * self.price_sensitivity

        effective_access = float(self.model.effective_charging_access[home_x, home_y])
        charging_score = 0.7 * self.home_charging_access + 0.3 * effective_access
        w = p.env_score_pro_env_weight
        environmental_score = (1.0 - w) * self.environmental_concern + w * self.pro_env
        peer_adoption_share = self._peer_adoption_share()
        # Range anxiety is a psychological barrier that good charging access
        # alleviates; agents with high effective access at home discount it.
        range_anxiety_penalty = self.range_anxiety * (1.0 - effective_access)

        adoption_score = (
            p.economic_weight * economic_component
            + p.charging_weight * charging_score
            + p.environmental_weight * environmental_score
            + p.peer_weight * peer_adoption_share * self.peer_sensitivity
            - p.range_anxiety_weight * range_anxiety_penalty
        )

        # Hard affordability gate: average annual cost of ownership cannot
        # exceed income_budget_share of income, regardless of score.
        annual_ev_cost = ev_cost / p.tco_years
        affordable = annual_ev_cost <= p.income_budget_share * self.income

        self.last_ev_tco = ev_cost
        self.last_ice_tco = ice_cost
        self.last_tco_gap = tco_gap
        self.last_economic_score = economic_component
        self.last_charging_score = charging_score
        self.last_environmental_score = environmental_score
        self.last_peer_adoption_share = peer_adoption_share
        self.last_range_anxiety_penalty = p.range_anxiety_weight * range_anxiety_penalty
        self.last_adoption_score = adoption_score
        self.last_affordable = affordable
        self.has_evaluated_adoption = True

        decided_to_adopt = self._decide_adoption(adoption_score)
        if decided_to_adopt and affordable and self.model.request_ev_purchase():
            self.ev_adopted = True
            self.vehicle_age = 0

    def _decide_adoption(self, score):
        p = self.model.params
        rule = p.adoption_rule

        if rule == "deterministic":
            decision = score >= p.adoption_threshold
            self.last_adoption_probability = 1.0 if decision else 0.0
            return decision
        if rule == "logistic":
            prob = adoption_probability(
                score,
                p.adoption_threshold,
                p.adoption_temperature,
            )
            self.last_adoption_probability = prob
            return self.random.random() < prob
        raise ValueError(f"Unknown adoption_rule {rule!r}")

    def _diffuse_perceptions(self) -> None:
        """Visible EV adoption among peers updates perceived EV salience.

        Residential or network peer exposure reduces perceived range anxiety
        and raises environmental salience; this is social learning acting on
        perceptions, not just on the adoption-score peer term.
        """

        p = self.model.params
        share = self._peer_adoption_share()
        if share <= 0.0:
            return

        self.range_anxiety = max(
            self.range_anxiety - p.peer_range_anxiety_relief * share,
            p.range_anxiety_min,
        )
        self.environmental_concern = min(
            self.environmental_concern + p.peer_concern_gain * share,
            p.environmental_concern_max,
        )

    def _peer_adoption_share(self) -> float:
        if self.model.params.networks:
            neighbours = list(self.model.network_neighbours(self))
        else:
            neighbours = self.model.home_neighbours(self)

        if not neighbours:
            return 0.0
        return sum(bool(getattr(agent, "ev_adopted", False)) for agent in neighbours) / len(
            neighbours
        )
