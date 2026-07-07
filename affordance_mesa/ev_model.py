"""EV adoption extension for the affordance-landscape Mesa model."""

from __future__ import annotations

import numpy as np
from mesa.datacollection import DataCollector

from .ev_agents import EVConsumerAgent
from .ev_params import EVParams
from .model import (
    AffordanceLandscapeModel,
    dominant_pro_share,
    global_clustering_coefficient,
    mean_non_env,
    mean_pro_env,
    non_behaviour_share,
    pro_affordance_share,
    pro_behaviour_share,
)


class EVAdoptionModel(AffordanceLandscapeModel):
    """Affordance landscape model with an added EV replacement decision."""

    def __init__(self, params: EVParams | None = None, seed: int | None = None):
        self.chargers: list[tuple[int, int]] = []
        self._charger_sites: set[tuple[int, int]] = set()
        self._agents_by_home: dict[tuple[int, int], list] = {}
        self.charging_access: np.ndarray
        self.ev_adoption_count = 0
        self.ev_adoption_share = 0.0
        self.mean_adoption_score = 0.0
        self.mean_charging_access = 0.0
        self.mean_tco_gap = 0.0

        super().__init__(params=params or EVParams(), seed=seed)

        self.ev_agents = self.agent_list
        self.charging_access = np.zeros((self.params.width, self.params.height), dtype=float)
        self._create_initial_chargers()
        self._update_charging_access()
        self._update_ev_metrics()
        self.datacollector = self._create_ev_datacollector()
        self.datacollector.collect(self)

    def _create_agents(self) -> None:
        for _ in range(self.params.number_of_agents):
            lower_bound, upper_bound = self._sample_bounds()
            agent = EVConsumerAgent(
                model=self,
                pro_env=float(self.rng.normal(self.params.initial_pro, 0.15)),
                non_env=float(self.rng.normal(self.params.initial_non, 0.15)),
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                income=self._sample_nonnegative_normal(
                    self.params.income_mean,
                    self.params.income_sd,
                ),
                annual_mileage=self._sample_nonnegative_normal(
                    self.params.annual_mileage_mean,
                    self.params.annual_mileage_sd,
                ),
                vehicle_age=self.random.randint(
                    self.params.vehicle_age_min,
                    self.params.vehicle_age_max,
                ),
                replacement_interval=self.random.randint(
                    self.params.replacement_interval_min,
                    self.params.replacement_interval_max,
                ),
                home_charging_access=self._sample_uniform(
                    self.params.home_charging_min,
                    self.params.home_charging_max,
                ),
                environmental_concern=self._sample_uniform(
                    self.params.environmental_concern_min,
                    self.params.environmental_concern_max,
                ),
                price_sensitivity=self._sample_uniform(
                    self.params.price_sensitivity_min,
                    self.params.price_sensitivity_max,
                ),
                range_anxiety=self._sample_uniform(
                    self.params.range_anxiety_min,
                    self.params.range_anxiety_max,
                ),
                peer_sensitivity=self._sample_uniform(
                    self.params.peer_sensitivity_min,
                    self.params.peer_sensitivity_max,
                ),
            )
            agent._clamp_states()
            x = self.random.randrange(self.params.width)
            y = self.random.randrange(self.params.height)
            self.grid.place_agent(agent, (x, y))
            agent.home_pos = (x, y)
            self._agents_by_home.setdefault((x, y), []).append(agent)
            self.agent_list.append(agent)

    def home_neighbours(self, agent: EVConsumerAgent) -> list[EVConsumerAgent]:
        """Residential neighbourhood used for EV peer effects.

        Deliberately not ``grid.get_neighbors``, which would count transient
        passers-by at their current positions.
        """

        positions = [agent.home_pos]
        positions.extend(self.moore_neighbour_positions(agent.home_pos))
        neighbours: list[EVConsumerAgent] = []
        for pos in positions:
            neighbours.extend(
                home_agent
                for home_agent in self._agents_by_home.get(pos, [])
                if home_agent is not agent
            )
        return neighbours

    def _sample_bounds(self) -> tuple[float, float]:
        lower = self._sample_uniform(0.0, 1.0, self.params.lower_bound_mean, self.params.lower_bound_sd)
        upper = self._sample_uniform(0.0, 1.0, self.params.upper_bound_mean, self.params.upper_bound_sd)
        if lower >= upper:
            lower, upper = min(lower, upper), max(lower, upper)
        if lower == upper:
            upper = min(lower + 0.01, 1.0)
            lower = min(lower, upper - 0.01)
        return lower, upper

    def _sample_uniform(
        self,
        minimum: float,
        maximum: float,
        mean: float | None = None,
        sd: float | None = None,
    ) -> float:
        if mean is not None and sd is not None:
            value = float(self.rng.normal(mean, sd))
        else:
            value = float(self.rng.uniform(minimum, maximum))
        return min(max(value, minimum), maximum)

    def _sample_nonnegative_normal(self, mean: float, sd: float) -> float:
        return max(float(self.rng.normal(mean, sd)), 0.0)

    def _create_initial_chargers(self) -> None:
        n_cells = self.params.width * self.params.height
        n_chargers = int(round(n_cells * self.params.initial_charging_coverage))
        self._add_random_chargers(n_chargers)

    def _create_ev_datacollector(self) -> DataCollector:
        return DataCollector(
            model_reporters={
                "pro_behaviour": "pro_behaviour",
                "non_behaviour": "non_behaviour",
                "pro_behaviour_share": pro_behaviour_share,
                "non_behaviour_share": non_behaviour_share,
                "mean_pro_env": mean_pro_env,
                "mean_non_env": mean_non_env,
                "pro_affordance_share": pro_affordance_share,
                "dominant_pro_share": dominant_pro_share,
                "global_clustering": global_clustering_coefficient,
                "ev_adoption_share": "ev_adoption_share",
                "mean_adoption_score": "mean_adoption_score",
                "mean_charging_access": "mean_charging_access",
                "mean_tco_gap": "mean_tco_gap",
                "charger_count": lambda model: len(model.chargers),
            },
            agent_reporters={
                "pro_env": "pro_env",
                "non_env": "non_env",
                "dominant_state": "dominant_state",
                "last_behaviour": "last_behaviour",
                "ev_adopted": "ev_adopted",
                "last_adoption_score": "last_adoption_score",
                "last_tco_gap": "last_tco_gap",
            },
        )

    def _expand_charging_infrastructure(self) -> None:
        rate = max(float(self.params.charger_expansion_rate), 0.0)
        n_new = int(rate)
        fractional = rate - n_new
        if self.random.random() < fractional:
            n_new += 1

        if n_new > 0:
            self._add_random_chargers(n_new)
            self._update_charging_access()

    def _add_random_chargers(self, n_chargers: int) -> None:
        if n_chargers <= 0:
            return

        n_cells = self.params.width * self.params.height
        available = n_cells - len(self._charger_sites)
        if available <= 0:
            return

        flat_candidates = [
            idx
            for idx in range(n_cells)
            if (idx // self.params.height, idx % self.params.height) not in self._charger_sites
        ]
        selected = self.rng.choice(
            flat_candidates,
            size=min(n_chargers, len(flat_candidates)),
            replace=False,
        )

        for flat_index in np.atleast_1d(selected):
            x = int(flat_index) // self.params.height
            y = int(flat_index) % self.params.height
            pos = (x, y)
            self._charger_sites.add(pos)
            self.chargers.append(pos)

    def _update_charging_access(self) -> None:
        if not self.chargers:
            self.charging_access.fill(0.0)
            self.mean_charging_access = 0.0
            return

        width = self.params.width
        height = self.params.height
        x_grid = np.arange(width)[:, None]
        y_grid = np.arange(height)[None, :]
        min_distance = np.full((width, height), np.inf)

        for charger_x, charger_y in self.chargers:
            dx = np.abs(x_grid - charger_x)
            dy = np.abs(y_grid - charger_y)
            dx = np.minimum(dx, width - dx)
            dy = np.minimum(dy, height - dy)
            min_distance = np.minimum(min_distance, dx + dy)

        decay = max(float(self.params.charger_access_decay), 1e-9)
        self.charging_access = 1.0 / (1.0 + min_distance / decay)
        self.mean_charging_access = float(np.mean(self.charging_access))

    def _update_ev_metrics(self) -> None:
        adopted = [agent.ev_adopted for agent in self.agent_list]
        scores = [agent.last_adoption_score for agent in self.agent_list]
        tco_gaps = [
            agent.last_tco_gap
            for agent in self.agent_list
            if agent.last_ev_tco and agent.last_ice_tco
        ]

        n_agents = len(self.agent_list)
        self.ev_adoption_count = sum(adopted)
        self.ev_adoption_share = self.ev_adoption_count / n_agents if n_agents else 0.0
        self.mean_adoption_score = float(np.mean(scores)) if scores else 0.0
        self.mean_charging_access = float(np.mean(self.charging_access))
        self.mean_tco_gap = float(np.mean(tco_gaps)) if tco_gaps else 0.0

    def step(self) -> None:
        self._expand_charging_infrastructure()

        self.pro_behaviour = 0
        self.non_behaviour = 0
        agents = list(self.agent_list)
        self.random.shuffle(agents)
        for agent in agents:
            agent.step()

        if self.params.mutate_on:
            self._mutate()

        self._update_ev_metrics()
        self.datacollector.collect(self)
        if self.steps >= self.params.max_steps:
            self.running = False
