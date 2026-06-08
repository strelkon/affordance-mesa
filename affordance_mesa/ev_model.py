import numpy as np
from mesa.datacollection import DataCollector
from affordance_mesa.model import AffordanceLandscapeModel
from .ev_agents import EVConsumerAgent

from .ev_costs import ev_tco, ice_tco, economic_score

class EVAdoptionModel(AffordanceLandscapeModel):

    def __init__(self, params, seed=None):
        super().__init__(params=params, seed=seed)

        width = self.params.width
        height = self.params.height

        # 1. Criar agentes EV
        self.ev_agents = []
        self._create_ev_agents()

        self.chargers = []


        # 2. Camada de charging access
        self.charging_access = np.zeros((width, height), dtype=float)

        # 3. Parâmetros EV
        self.subsidy = params.subsidy
        self.fuel_price = params.fuel_price
        self.electricity_price = params.electricity_price
        self.charger_expansion_rate = params.charger_expansion_rate
        self.adoption_threshold = params.adoption_threshold

        # 4. Métricas EV
        self.ev_adoption_count = 0
        self.ev_adoption_share = 0.0
        self.mean_adoption_score = 0.0
        self.mean_charging_access = 0.0
        self.mean_tco_gap = 0.0

        # 5. DataCollector (Mesa 3.5.1)
        self.datacollector = DataCollector(
            model_reporters={
                "EV_Adoption_Rate": lambda m: m.ev_adoption_share,
                "Mean_Adoption_Score": lambda m: m.mean_adoption_score,
                "Mean_Charging_Access": lambda m: m.mean_charging_access,
                "Mean_TCO_Gap": lambda m: m.mean_tco_gap,
            },
            agent_reporters={}
        )


    def _create_ev_agents(self):
        rng = self.random
        np_rng = np.random.default_rng()

        for _ in range(self.params.number_of_agents):

            agent = EVConsumerAgent(
                model=self,

                # Atributos do modelo base
                pro_env=float(np_rng.normal(self.params.initial_pro, 0.15)),
                non_env=float(np_rng.normal(self.params.initial_non, 0.15)),
                lower_bound=float(np_rng.normal(self.params.lower_bound_mean, self.params.lower_bound_sd)),
                upper_bound=float(np_rng.normal(self.params.upper_bound_mean, self.params.upper_bound_sd)),

                # Atributos EV
                income=float(np_rng.normal(self.params.income_mean, self.params.income_sd)),
                annual_mileage=float(np_rng.normal(self.params.annual_mileage_mean, self.params.annual_mileage_sd)),
                vehicle_age=int(rng.randint(self.params.vehicle_age_min, self.params.vehicle_age_max)),
                replacement_interval=int(rng.randint(self.params.replacement_interval_min, self.params.replacement_interval_max)),
                home_charging_access=float(np_rng.uniform(self.params.home_charging_min, self.params.home_charging_max)),
                environmental_concern=float(np_rng.uniform(self.params.environmental_concern_min, self.params.environmental_concern_max)),
                price_sensitivity=float(np_rng.uniform(self.params.price_sensitivity_min, self.params.price_sensitivity_max)),
                range_anxiety=float(np_rng.uniform(self.params.range_anxiety_min, self.params.range_anxiety_max)),
                peer_sensitivity=float(np_rng.uniform(self.params.peer_sensitivity_min, self.params.peer_sensitivity_max)),
            )

            # Colocar agente na grelha
            x = rng.randrange(self.params.width)
            y = rng.randrange(self.params.height)
            self.grid.place_agent(agent, (x, y))

            self.ev_agents.append(agent)
            self.agent_list.append(agent)   



    def step(self):
    # 1. Expandir carregadores
        self._expand_chargers()

    # 2. Atualizar charging access ANTES dos agentes agirem
        self._update_charging_access()

    # 3. Agora sim, deixar os agentes agir
        super().step()

    # 4. Atualizar métricas
        self._update_ev_metrics()

    # 5. Recolher dados
        self.datacollector.collect(self)

    
    def _expand_chargers(self):
        rng = self.random

    # Interpretar charger_expansion_rate como probabilidade
        if rng.random() < self.params.charger_expansion_rate:
            x = rng.randrange(self.params.width)
            y = rng.randrange(self.params.height)
            self.chargers.append((x, y))

    def _update_charging_access(self):
        width = self.params.width
        height = self.params.height

    # Reset da matriz
        self.charging_access = np.zeros((width, height), dtype=float)

        if len(self.chargers) == 0:
            self.mean_charging_access = 0.0
            return

    # Para cada célula da grelha
        for x in range(width):
            for y in range(height):
            # Distância ao carregador mais próximo
                dist = min(
                    abs(cx - x) + abs(cy - y)
                    for (cx, cy) in self.chargers
                )

            # Converter distância em score (quanto mais perto, melhor)
                access = 1.0 / (1.0 + dist)
                self.charging_access[x, y] = access

    # Média global
        self.mean_charging_access = float(np.mean(self.charging_access))

    


    def _update_ev_metrics(self):
        adopted = [a.ev_adopted for a in self.ev_agents]
        scores = [a.last_adoption_score for a in self.ev_agents]
        tco_gaps = [a.last_tco_gap for a in self.ev_agents]

        self.ev_adoption_count = sum(adopted)
        self.ev_adoption_share = float(np.mean(adopted))
        self.mean_adoption_score = float(np.mean(scores))
        self.mean_charging_access = float(np.mean(self.charging_access))
        self.mean_tco_gap = float(np.mean(tco_gaps))
