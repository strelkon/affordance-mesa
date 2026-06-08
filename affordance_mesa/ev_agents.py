from .agents import ConsumerAgent
import numpy as np

from .ev_costs import ev_tco, ice_tco, economic_score

class EVConsumerAgent(ConsumerAgent):
    """
    Extensão do ConsumerAgent para incluir atributos e decisão de adoção EV.
    """

    def __init__(
        self,
        model,
        pro_env,
        non_env,
        lower_bound,
        upper_bound,
        *,
        income,
        annual_mileage,
        vehicle_age,
        replacement_interval,
        home_charging_access,
        environmental_concern,
        price_sensitivity,
        range_anxiety,
        peer_sensitivity,
    ):
        super().__init__(
            model=model,
            pro_env=pro_env,
            non_env=non_env,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

        # --- Atributos EV ---
        self.income = income
        self.annual_mileage = annual_mileage
        self.vehicle_age = vehicle_age
        self.replacement_interval = replacement_interval
        self.home_charging_access = home_charging_access
        self.environmental_concern = environmental_concern
        self.price_sensitivity = price_sensitivity
        self.range_anxiety = range_anxiety
        self.peer_sensitivity = peer_sensitivity

        # --- Estado EV ---
        self.ev_adopted = False
        self.last_adoption_score = 0.0
        self.last_tco_gap = 0.0
        self.last_ev_tco = 0.0
        self.last_ice_tco = 0.0

    # ---------------------------------------------------------
    # STEP DO AGENTE
    # ---------------------------------------------------------
    def step(self):
        self.consider_ev_adoption()

    # ---------------------------------------------------------
    # REGRA DE ADOÇÃO EV
    # ---------------------------------------------------------
    def consider_ev_adoption(self):
        m = self.model
        p = m.params

        # ---------------------------------------------------------
        # 1. TCO ICE
        # ---------------------------------------------------------
        fuel_cost = self.annual_mileage / 15.0 * p.fuel_price
        maintenance_ice = 600.0
        depreciation_ice = 1500.0
        ice_tco = fuel_cost + maintenance_ice + depreciation_ice

        # ---------------------------------------------------------
        # 2. TCO EV
        # ---------------------------------------------------------
        electricity_cost = self.annual_mileage / 6.0 * p.electricity_price
        maintenance_ev = 300.0
        depreciation_ev = 1800.0 - p.subsidy
        ev_tco = electricity_cost + maintenance_ev + depreciation_ev

        # ---------------------------------------------------------
        # 3. TCO gap
        # ---------------------------------------------------------
        tco_gap = ice_tco - ev_tco
        self.last_ice_tco = ice_tco
        self.last_ev_tco = ev_tco
        self.last_tco_gap = tco_gap

        # Score económico normalizado
        economic_score = 1 / (1 + np.exp(-tco_gap / 2000))

        # ---------------------------------------------------------
        # 4. Charging score
        # ---------------------------------------------------------
        x, y = self.pos
        charging_score = m.charging_access[x, y]
        charging_score = charging_score / (1 + charging_score)

        # ---------------------------------------------------------
        # 5. Environmental concern
        # ---------------------------------------------------------
        environmental_score = self.environmental_concern

        # ---------------------------------------------------------
        # 6. Peer adoption share
        # ---------------------------------------------------------
        neighbours = m.network_neighbours(self)
        if neighbours:
            peer_adoption_share = sum(a.ev_adopted for a in neighbours) / len(neighbours)
        else:
            peer_adoption_share = 0.0

        # ---------------------------------------------------------
        # 7. Range anxiety
        # ---------------------------------------------------------
        range_anxiety = self.range_anxiety

        # ---------------------------------------------------------
        # 8. Weighted adoption score
        # ---------------------------------------------------------
        adoption_score = (
            p.economic_weight * economic_score
            + p.charging_weight * charging_score
            + p.environmental_weight * environmental_score
            + p.peer_weight * peer_adoption_share
            - p.range_anxiety_weight * range_anxiety
        )

        self.last_adoption_score = adoption_score

        # ---------------------------------------------------------
        # 9. Decisão determinística
        # ---------------------------------------------------------
        if adoption_score >= p.adoption_threshold:
            self.ev_adopted = True

