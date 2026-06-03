import numpy as np
from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from .ev_agents import EVConsumerAgent

class EVAdoptionModel(Model):

    def __init__(self, params, seed=None):
        super().__init__(seed=seed)

        self.params = params

        # 1) Create a grid (without affordances)
        self.grid = MultiGrid(params.width, params.height, torus=False)

        # 2) Second layer: access to chargers
        self.charging_access = np.zeros((params.width, params.height), dtype=float)

        # 3) List of EV agents
        self.agent_list = []
        self._create_ev_agents()

        # 4) EV Metrics
        self.ev_adoption_count = 0
        self.ev_adoption_share = 0.0
        self.mean_adoption_score = 0.0
        self.mean_charging_access = 0.0

        # 5) DataCollector EV (Clean)
        self.datacollector = DataCollector(
            model_reporters={
                "ev_adoption_share": lambda m: m.ev_adoption_share,
                "mean_adoption_score": lambda m: m.mean_adoption_score,
                "mean_charging_access": lambda m: m.mean_charging_access,
            }
        )


    def _create_ev_agents(self):
        for x in range(self.params.width):
            for y in range(self.params.height):

                pro_env = self.random.normalvariate(0.5, 0.15)
                non_env = self.random.normalvariate(0.5, 0.15)
                bound = self.random.normalvariate(0.5, 0.1)

                agent = EVConsumerAgent(
                    self,
                    (x, y),
                    pro_env,
                    non_env,
                    bound
                )

                self.grid.place_agent(agent, (x, y))
                self.agent_list.append(agent)

    
    def _expand_charging_infrastructure(self):
        rate = self.params.charger_expansion_rate
        self.charging_access += rate
        np.clip(self.charging_access, 0, 1, out=self.charging_access)

    
    def _update_ev_metrics(self):
        adopted = [a.ev_adopted for a in self.agent_list]
        scores = [a.last_adoption_score for a in self.agent_list]

        self.ev_adoption_count = sum(adopted)
        self.ev_adoption_share = self.ev_adoption_count / len(self.agent_list)
        self.mean_adoption_score = float(np.mean(scores))
        self.mean_charging_access = float(np.mean(self.charging_access))

    # ---TCO average gap  ---
        tco_gaps = []
        for a in self.agent_list:
            if hasattr(a, "last_ev_tco") and hasattr(a, "last_ice_tco"):
                tco_gaps.append(a.last_ice_tco - a.last_ev_tco)

        self.mean_tco_gap = float(np.mean(tco_gaps)) if tco_gaps else 0.0


    def step(self):
        self._expand_charging_infrastructure()

        for agent in self.agent_list:
            agent.step()

        self._update_ev_metrics()

        self.datacollector.collect(self)
