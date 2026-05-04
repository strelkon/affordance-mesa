"""Network generation utilities for the Mesa affordance model."""

from __future__ import annotations

import random
from collections.abc import Sequence

import networkx as nx


def create_social_network(
    n_agents: int,
    network_type: str,
    network_param: float,
    mu: float = 0.9,
    seed: int | None = None,
) -> nx.Graph:
    """Create a graph corresponding to the original NetLogo choices.

    Parameters
    ----------
    n_agents:
        Number of consumer agents.
    network_type:
        One of ``random``, ``small-world``, ``preferential``, or ``KE``.
    network_param:
        NetLogo's network-param slider. It is interpreted as average degree for
        the random graph, neighbourhood size for Watts-Strogatz, and minimum
        degree / initial active set for preferential and KE networks.
    mu:
        Rewiring/activation parameter for the Klemm-Eguíluz-style generator.
    seed:
        Random seed for reproducibility.
    """

    rng = random.Random(seed)
    kind = network_type.lower()

    if n_agents <= 0:
        return nx.Graph()

    if kind == "random":
        # NetLogo repeats (network_param * count turtles) / 2 link additions.
        m_edges = max(0, int(round((network_param * n_agents) / 2)))
        return nx.gnm_random_graph(n_agents, m_edges, seed=seed)

    if kind == "small-world":
        # NetLogo nw:generate-watts-strogatz num-nodes neighborhood-size 0.1.
        k = _valid_even_k(int(round(network_param)), n_agents)
        return nx.watts_strogatz_graph(n_agents, k, 0.1, seed=seed)

    if kind == "preferential":
        # NetLogo preferential attachment: min degree = network-param.
        m = max(1, min(int(round(network_param)), max(1, n_agents - 1)))
        return nx.barabasi_albert_graph(n_agents, m, seed=seed)

    if kind == "ke":
        return klemm_eguiluz_graph(n_agents, int(round(network_param)), mu, rng)

    raise ValueError(
        f"Unknown network_type={network_type!r}. Use random, small-world, preferential, or KE."
    )


def _valid_even_k(k: int, n: int) -> int:
    """Return a valid even degree for NetworkX Watts-Strogatz."""
    if n <= 2:
        return 1
    k = max(2, min(k, n - 1))
    if k % 2 == 1:
        k -= 1
    return max(2, k)


def klemm_eguiluz_graph(n_agents: int, m0: int, mu: float, rng: random.Random) -> nx.Graph:
    """Approximate the Klemm-Eguíluz scale-free/high-clustering algorithm.

    The original NetLogo procedure adapts Fernando Sancho Caparrini's complex
    networks implementation. This is a transparent Python approximation that
    keeps the key mechanism: a small active set, full initial connectivity,
    new nodes connecting to active nodes or preferentially to inactive nodes,
    and deactivation inversely related to degree.
    """

    m0 = max(2, min(m0, n_agents))
    g = nx.complete_graph(m0)
    active: list[int] = list(range(m0))
    inactive: list[int] = []

    for new_node in range(m0, n_agents):
        g.add_node(new_node)
        for ac in list(active):
            if rng.random() < mu or not inactive:
                g.add_edge(new_node, ac)
            else:
                target = _weighted_choice_by_degree(g, inactive, rng)
                g.add_edge(new_node, target)

        active.append(new_node)
        # Deactivate one active node with probability proportional to 1 / degree.
        weights = [1.0 / max(1, g.degree(node)) for node in active]
        deactivated = _weighted_choice(active, weights, rng)
        active.remove(deactivated)
        inactive.append(deactivated)

    return g


def _weighted_choice_by_degree(g: nx.Graph, nodes: Sequence[int], rng: random.Random) -> int:
    weights = [max(1, g.degree(node)) for node in nodes]
    return _weighted_choice(nodes, weights, rng)


def _weighted_choice(nodes: Sequence[int], weights: Sequence[float], rng: random.Random) -> int:
    total = sum(weights)
    if total <= 0:
        return rng.choice(list(nodes))
    cutoff = rng.random() * total
    cumulative = 0.0
    for node, weight in zip(nodes, weights, strict=True):
        cumulative += weight
        if cumulative >= cutoff:
            return node
    return nodes[-1]
