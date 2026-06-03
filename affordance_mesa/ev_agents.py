from .agents import ConsumerAgent
from .ev_costs import ev_tco, ice_tco, economic_score

class EVConsumerAgent(ConsumerAgent):
    """
    EV agent that extends the original ConsumerAgent.
    """

    def __init__(self, model, pos, pro_env, non_env, bound):
        super().__init__(model, pos, pro_env, non_env, bound)

        # EV-specific attributes
        self.income = self.random.lognormvariate(10, 0.5)
        self.annual_mileage = self.random.randint(5000, 25000)
        self.vehicle_age = self.random.randint(0, 15)
        self.replacement_interval = self.random.randint(5, 15)
        self.home_charging_access = self.random.choice([0, 1])
        self.environmental_concern = self.random.uniform(0, 1)
        self.price_sensitivity = self.random.uniform(0, 1)
        self.range_anxiety = self.random.uniform(0, 1)
        self.peer_sensitivity = self.random.uniform(0, 1)
        self.ev_adopted = False
        self.last_adoption_score = 0.0

    # ---------------------------------------------------------
    # STEP (clean, without calling super().step())
    # ---------------------------------------------------------
    def step(self):
        self.vehicle_age += 1

        if self.vehicle_age >= self.replacement_interval and not self.ev_adopted:
            self.consider_ev_adoption()

    # ---------------------------------------------------------
    # FINAL COMPLETE VERSION OF consider_ev_adoption()
    # ---------------------------------------------------------
    def consider_ev_adoption(self):
        p = self.model.params
        x, y = self.pos

        # ============================================================
        # 1) TCO — Total Cost of Ownership (EV vs ICE)
        # ============================================================

        ev_cost = ev_tco(
            purchase_price=35000 - p.subsidy,
            electricity_price=p.electricity_price,
            annual_mileage=self.annual_mileage,
            kwh_per_km=0.18,
            maintenance_cost=300,
            years=8
        )

        ice_cost = ice_tco(
            purchase_price=25000,
            fuel_price=p.fuel_price,
            annual_mileage=self.annual_mileage,
            liters_per_km=0.07,
            maintenance_cost=600,
            years=8
        )

        self.last_ev_tco = ev_cost
        self.last_ice_tco = ice_cost
        
        econ_score = economic_score(ev_cost, ice_cost)

        # ============================================================
        # 2) Charging access score
        # ============================================================

        charging_score = (
            0.7 * self.home_charging_access +
            0.3 * self.model.charging_access[x][y]
        )

        # ============================================================
        # 3) Environmental concern
        # ============================================================

        environmental_score = self.environmental_concern

        # ============================================================
        # 4) Peer effects (espacial, Moore neighborhood)
        # ============================================================

        neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)

        if len(neighbors) > 0:
            peer_adoption_share = sum(1 for n in neighbors if n.ev_adopted) / len(neighbors)
        else:
            peer_adoption_share = 0.0


        # ============================================================
        # 5) Range anxiety (negative effect)
        # ============================================================

        range_penalty = self.range_anxiety

        # ============================================================
        # 6) Combining everything into an adoption score.
        # ============================================================

        adoption_score = (
            p.economic_weight * econ_score +
            p.charging_weight * charging_score +
            p.environmental_weight * environmental_score +
            p.peer_weight * peer_adoption_share -
            p.range_anxiety_weight * range_penalty
        )

        self.last_adoption_score = adoption_score

        # ============================================================
        # 7) Deterministic decision
        # ============================================================

        if adoption_score >= p.adoption_threshold:
            self.ev_adopted = True
