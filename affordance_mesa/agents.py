"""Agents for the Mesa affordance-landscape reimplementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from mesa import Agent

if TYPE_CHECKING:  # pragma: no cover
    from .model import AffordanceLandscapeModel


@dataclass(frozen=True)
class BehaviourEvent:
    """One realized behaviour during a model tick."""

    agent_id: int
    behaviour: str  # "pro" or "non"
    x: int
    y: int


class ConsumerAgent(Agent):
    """A consumer with competing pro- and non-environmental personal states.

    This follows the original NetLogo model closely: agents repeatedly move over
    an affordance landscape until they realize either a pro-environmental or a
    non-environmental behaviour. The behaviour updates their personal states,
    may reconstruct neighbouring affordances, and can transmit social learning
    to network neighbours.
    """

    def __init__(
        self,
        model: "AffordanceLandscapeModel",
        pro_env: float,
        non_env: float,
        lower_bound: float,
        upper_bound: float,
    ) -> None:
        super().__init__(model)
        self.pro_env = pro_env
        self.non_env = non_env
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.behaved = False
        self.last_behaviour: str | None = None

    @property
    def dominant_state(self) -> str:
        if self.pro_env > self.non_env:
            return "pro"
        if self.non_env > self.pro_env:
            return "non"
        return "tie"

    def step(self) -> None:
        self.behaved = False
        self.last_behaviour = None
        self.behave()

    def behave(self) -> None:
        """Attempt to perform one behaviour, moving until successful.

        NetLogo uses an unbounded `while [behaved? = false]` loop. This port uses
        `max_behavior_attempts` as a guard against pathological infinite loops
        when both personal-state probabilities are extremely low.
        """

        for _ in range(self.model.params.max_behavior_attempts):
            x, y = self.pos
            affordance = self.model.affordances[x, y]

            if affordance == 1 and self.model.random.random() < self.pro_env:
                self._perform_pro_behaviour(x, y)
                return

            if affordance == 0 and self.model.random.random() < self.non_env:
                self._perform_non_behaviour(x, y)
                return

            self.move()

        # If no behaviour occurs, keep NetLogo-like state bounds and continue.
        self._clamp_states()

    def _perform_pro_behaviour(self, x: int, y: int) -> None:
        p = self.model.params
        self.pro_env += p.asocial_learning
        self.non_env -= p.asocial_learning
        self.model.pro_behaviour += 1
        self.behaved = True
        self.last_behaviour = "pro"

        if p.niche_construction:
            if self.model.random.random() < (p.construct_pro / p.number_of_agents):
                nx, ny = self.model.random_neighbour_position((x, y))
                self.model.affordances[nx, ny] = 1

        if p.networks:
            for neighbour in self.model.network_neighbours(self):
                neighbour.pro_env += p.social_learning
                neighbour.non_env -= p.social_learning
                neighbour._clamp_states()

        self._clamp_states()

    def _perform_non_behaviour(self, x: int, y: int) -> None:
        p = self.model.params
        self.non_env += p.asocial_learning
        self.pro_env -= p.asocial_learning
        self.model.non_behaviour += 1
        self.behaved = True
        self.last_behaviour = "non"

        if p.niche_construction:
            if self.model.random.random() < (p.construct_non / p.number_of_agents):
                nx, ny = self.model.random_neighbour_position((x, y))
                self.model.affordances[nx, ny] = 0

        if p.networks:
            for neighbour in self.model.network_neighbours(self):
                neighbour.non_env += p.social_learning
                neighbour.pro_env -= p.social_learning
                neighbour._clamp_states()

        self._clamp_states()

    def _clamp_states(self) -> None:
        self.pro_env = min(max(self.pro_env, self.lower_bound), self.upper_bound)
        self.non_env = min(max(self.non_env, self.lower_bound), self.upper_bound)

    def move(self) -> None:
        """Discrete approximation of NetLogo's wiggle + fd 1 movement."""
        candidates = self.model.moore_neighbour_positions(self.pos)
        new_pos = self.model.random.choice(candidates)
        self.model.grid.move_agent(self, new_pos)
