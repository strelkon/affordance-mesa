"""Mesa port of the NetLogo Affordance Landscape model."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import networkx as nx
import numpy as np
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

from .agents import ConsumerAgent
from .networks import create_social_network


@dataclass
class AffordanceModelParams:
    """Parameters mirroring the NetLogo interface where possible."""

    number_of_agents: int = 100
    width: int = 201
    height: int = 201
    pro_amount: float = 0.5
    initial_pro: float = 0.5
    initial_non: float = 0.5
    asocial_learning: float = 0.00005
    social_learning: float = 0.00007
    networks: bool = False
    network_type: str = "KE"
    network_param: float = 5.0
    mu: float = 0.9
    niche_construction: bool = False
    construct_pro: float = 5.0
    construct_non: float = 5.0
    mutate_on: bool = False
    mutate_prob: float = 0.005
    mutate_rate: float = 0.05
    max_steps: int = 20440
    max_behavior_attempts: int = 1000

    def as_dict(self) -> dict:
        return asdict(self)


class AffordanceLandscapeModel(Model):
    """Affordance landscape model implemented in Mesa 3.x.

    This is a computational translation of the NetLogo model. It keeps the
    abstract original logic as closely as Mesa's discrete-grid implementation
    allows.
    """

    def __init__(self, params: AffordanceModelParams | None = None, seed: int | None = None):
        super().__init__(rng=seed)
        self.params = params or AffordanceModelParams()
        self.seed = seed
        self.grid = MultiGrid(self.params.width, self.params.height, torus=True)
        self.affordances = np.zeros((self.params.width, self.params.height), dtype=np.int8)
        self.agent_list: list[ConsumerAgent] = []
        self.graph: nx.Graph | None = None
        self._agent_by_graph_node: dict[int, ConsumerAgent] = {}
        self._graph_node_by_agent_id: dict[int, int] = {}
        self.pro_behaviour = 0
        self.non_behaviour = 0
        self.running = True

        self._create_affordances()
        self._create_agents()
        if self.params.networks:
            self._create_network()

        self.datacollector = DataCollector(
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
            },
            agent_reporters={
                "pro_env": "pro_env",
                "non_env": "non_env",
                "dominant_state": "dominant_state",
                "last_behaviour": "last_behaviour",
            },
        )
        self.datacollector.collect(self)

    def _create_affordances(self) -> None:
        n_cells = self.params.width * self.params.height
        n_pro = int(round(n_cells * self.params.pro_amount))
        flat = self.affordances.ravel()
        flat[:] = 0
        if n_pro > 0:
            indices = self.rng.choice(n_cells, size=n_pro, replace=False)
            flat[indices] = 1

    def _create_agents(self) -> None:
        for _ in range(self.params.number_of_agents):
            agent = ConsumerAgent(
                model=self,
                pro_env=float(self.rng.normal(self.params.initial_pro, 0.15)),
                non_env=float(self.rng.normal(self.params.initial_non, 0.15)),
                lower_bound=float(self.rng.normal(0.2, 0.05)),
                upper_bound=float(self.rng.normal(0.8, 0.05)),
            )
            agent._clamp_states()
            x = self.random.randrange(self.params.width)
            y = self.random.randrange(self.params.height)
            self.grid.place_agent(agent, (x, y))
            self.agent_list.append(agent)

    def _create_network(self) -> None:
        self.graph = create_social_network(
            n_agents=self.params.number_of_agents,
            network_type=self.params.network_type,
            network_param=self.params.network_param,
            mu=self.params.mu,
            seed=self.seed,
        )
        self._agent_by_graph_node = {i: agent for i, agent in enumerate(self.agent_list)}
        self._graph_node_by_agent_id = {
            agent.unique_id: i for i, agent in enumerate(self.agent_list)
        }

    def step(self) -> None:
        self.pro_behaviour = 0
        self.non_behaviour = 0

        # Mesa 3's AgentSet supports shuffle_do, but an explicit list preserves
        # compatibility with older inspection/debug workflows.
        agents = list(self.agent_list)
        self.random.shuffle(agents)
        for agent in agents:
            agent.step()

        if self.params.mutate_on:
            self._mutate()

        self.datacollector.collect(self)
        if self.steps >= self.params.max_steps:
            self.running = False

    def run_model(self, n_steps: int | None = None) -> None:
        limit = self.params.max_steps if n_steps is None else n_steps
        for _ in range(limit):
            if not self.running:
                break
            self.step()

    def _mutate(self) -> None:
        # Same directional possibilities as the original NetLogo code.
        if self.random.random() < self.params.mutate_prob:
            for agent in self.agent_list:
                agent.pro_env += self.params.mutate_rate
                agent._clamp_states()
        if self.random.random() < self.params.mutate_prob:
            for agent in self.agent_list:
                agent.non_env -= self.params.mutate_rate
                agent._clamp_states()
        if self.random.random() < self.params.mutate_prob:
            for agent in self.agent_list:
                agent.non_env += self.params.mutate_rate
                agent._clamp_states()
        if self.random.random() < self.params.mutate_prob:
            for agent in self.agent_list:
                agent.pro_env -= self.params.mutate_rate
                agent._clamp_states()

    def network_neighbours(self, agent: ConsumerAgent) -> Iterable[ConsumerAgent]:
        if self.graph is None:
            return []
        node = self._graph_node_by_agent_id.get(agent.unique_id)
        if node is None:
            return []
        return [self._agent_by_graph_node[n] for n in self.graph.neighbors(node)]

    def moore_neighbour_positions(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = pos
        positions: list[tuple[int, int]] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                positions.append(((x + dx) % self.params.width, (y + dy) % self.params.height))
        return positions

    def random_neighbour_position(self, pos: tuple[int, int]) -> tuple[int, int]:
        return self.random.choice(self.moore_neighbour_positions(pos))

    def parameters(self) -> dict:
        return self.params.as_dict()


def pro_behaviour_share(model: AffordanceLandscapeModel) -> float:
    return model.pro_behaviour / model.params.number_of_agents


def non_behaviour_share(model: AffordanceLandscapeModel) -> float:
    return model.non_behaviour / model.params.number_of_agents


def mean_pro_env(model: AffordanceLandscapeModel) -> float:
    return float(np.mean([agent.pro_env for agent in model.agent_list]))


def mean_non_env(model: AffordanceLandscapeModel) -> float:
    return float(np.mean([agent.non_env for agent in model.agent_list]))


def pro_affordance_share(model: AffordanceLandscapeModel) -> float:
    return float(np.mean(model.affordances))


def dominant_pro_share(model: AffordanceLandscapeModel) -> float:
    return sum(agent.dominant_state == "pro" for agent in model.agent_list) / model.params.number_of_agents


def global_clustering_coefficient(model: AffordanceLandscapeModel) -> float:
    if model.graph is None or model.graph.number_of_nodes() == 0:
        return 0.0
    return float(nx.transitivity(model.graph))
