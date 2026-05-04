"""Solara dashboard for the Affordance Landscape Mesa model."""

from __future__ import annotations

import asyncio
from typing import Iterable

import matplotlib.colors as mcolors
import numpy as np
import solara
from matplotlib.figure import Figure

from affordance_mesa.model import AffordanceLandscapeModel, AffordanceModelParams

PLAY_INTERVAL_SECONDS = 0.08
MAX_LINKS_DRAWN = 1500
SKY_COLOR = "#28a9e0"
VIOLET_COLOR = "#7b4cc2"
RED_COLOR = "#d64b3c"
INK_COLOR = "#171717"
LINK_COLOR = "#2b8a90"

APP_STYLE = """
.aff-root {
  min-height: 100vh;
  background: #f4f5f0;
  color: #171717;
  padding: 12px;
  box-sizing: border-box;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  letter-spacing: 0;
}
.aff-grid {
  display: grid;
  grid-template-columns: minmax(230px, 280px) minmax(420px, 620px) minmax(420px, 1fr);
  gap: 12px;
  align-items: start;
}
.aff-panel {
  background: #ffffff;
  border: 1px solid #cfd5cd;
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 1px 2px rgba(23, 23, 23, 0.06);
}
.aff-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.aff-control-block {
  border: 1px solid #d7ddd5;
  border-radius: 8px;
  padding: 8px;
  background: #fbfcfa;
}
.aff-section-title {
  font-size: 13px;
  font-weight: 700;
  margin: 2px 0 6px 0;
  color: #38443d;
}
.aff-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 8px 0;
}
.aff-button-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}
.aff-button-row .v-btn {
  min-width: 0 !important;
  text-transform: none !important;
}
.aff-world {
  min-height: 460px;
}
.aff-plot-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.aff-monitor-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.aff-monitor {
  border: 1px solid #d7ddd5;
  border-radius: 8px;
  padding: 8px;
  background: #fbfcfa;
}
.aff-monitor-label {
  font-size: 12px;
  color: #5c675f;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.aff-monitor-value {
  font-size: 22px;
  font-weight: 700;
  line-height: 1.15;
  color: #171717;
}
.aff-panel .v-card__text {
  padding: 0 !important;
}
@media (max-width: 1340px) {
  .aff-grid {
    grid-template-columns: 280px minmax(420px, 1fr);
  }
  .aff-right {
    grid-column: 1 / -1;
  }
}
@media (max-width: 760px) {
  .aff-grid,
  .aff-plot-grid,
  .aff-monitor-grid {
    grid-template-columns: 1fr;
  }
  .aff-button-row {
    grid-template-columns: 1fr;
  }
}
"""


def _params_from_controls(
    *,
    number_of_agents: int,
    width: int,
    height: int,
    pro_amount: float,
    initial_pro: float,
    initial_non: float,
    networks: bool,
    network_type: str,
    network_param: float,
    mu: float,
    asocial_learning: float,
    social_learning: float,
    niche_construction: bool,
    construct_pro: float,
    construct_non: float,
    mutate_on: bool,
    max_steps: int,
) -> AffordanceModelParams:
    return AffordanceModelParams(
        number_of_agents=number_of_agents,
        width=width,
        height=height,
        pro_amount=pro_amount,
        initial_pro=initial_pro,
        initial_non=initial_non,
        networks=networks,
        network_type=network_type,
        network_param=network_param,
        mu=mu,
        asocial_learning=asocial_learning,
        social_learning=social_learning,
        niche_construction=niche_construction,
        construct_pro=construct_pro,
        construct_non=construct_non,
        mutate_on=mutate_on,
        max_steps=max_steps,
    )


def _plot_dataframe(model: AffordanceLandscapeModel):
    return model.datacollector.get_model_vars_dataframe().reset_index(names="step")


def _agent_positions(model: AffordanceLandscapeModel) -> tuple[np.ndarray, np.ndarray]:
    positions = [agent.pos for agent in model.agent_list if agent.pos is not None]
    if not positions:
        return np.array([], dtype=float), np.array([], dtype=float)
    x, y = zip(*positions, strict=True)
    return np.asarray(x, dtype=float), np.asarray(y, dtype=float)


def _agent_colors(model: AffordanceLandscapeModel) -> list[str]:
    colors = []
    for agent in model.agent_list:
        if agent.dominant_state == "pro":
            colors.append(INK_COLOR)
        elif agent.dominant_state == "non":
            colors.append(RED_COLOR)
        else:
            colors.append("#f1f1ec")
    return colors


def _network_edges(model: AffordanceLandscapeModel) -> Iterable[tuple[tuple[int, int], tuple[int, int]]]:
    if model.graph is None or model.graph.number_of_edges() == 0:
        return []
    edges = []
    for edge_number, (node_a, node_b) in enumerate(model.graph.edges()):
        if edge_number >= MAX_LINKS_DRAWN:
            break
        agent_a = model._agent_by_graph_node[node_a]
        agent_b = model._agent_by_graph_node[node_b]
        if agent_a.pos is not None and agent_b.pos is not None:
            edges.append((agent_a.pos, agent_b.pos))
    return edges


@solara.component
def WorldPlot(model: AffordanceLandscapeModel, render_key: int):
    fig = Figure(figsize=(6.4, 6.4), facecolor="#ffffff")
    ax = fig.subplots()
    cmap = mcolors.ListedColormap([SKY_COLOR, VIOLET_COLOR])

    ax.imshow(
        model.affordances.T,
        origin="lower",
        cmap=cmap,
        interpolation="nearest",
        vmin=0,
        vmax=1,
    )

    for (x_a, y_a), (x_b, y_b) in _network_edges(model):
        dx = x_b - x_a
        dy = y_b - y_a
        if abs(dx) > model.params.width / 2:
            dx -= int(np.sign(dx) * model.params.width)
        if abs(dy) > model.params.height / 2:
            dy -= int(np.sign(dy) * model.params.height)
        ax.plot(
            [x_a, x_a + dx],
            [y_a, y_a + dy],
            color=LINK_COLOR,
            alpha=0.35,
            linewidth=0.4,
            zorder=1,
        )

    x, y = _agent_positions(model)
    if len(x) > 0:
        ax.scatter(
            x,
            y,
            c=_agent_colors(model),
            s=18,
            alpha=0.95,
            linewidths=0.2,
            edgecolors="#ffffff",
            zorder=3,
        )

    ax.set_xlim(-0.5, model.params.width - 0.5)
    ax.set_ylim(-0.5, model.params.height - 0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_edgecolor("#171717")
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
    solara.FigureMatplotlib(fig, dependencies=[render_key], format="png")


@solara.component
def TimeseriesPlot(
    model: AffordanceLandscapeModel,
    render_key: int,
    title: str,
    series: list[tuple[str, str, str]],
    y_limits: tuple[float, float] | None = None,
):
    fig = Figure(figsize=(5.2, 2.8), facecolor="#ffffff")
    ax = fig.subplots()
    df = _plot_dataframe(model)

    for column, color, label in series:
        if column in df.columns:
            ax.plot(df["step"], df[column], color=color, linewidth=1.5, label=label)

    ax.set_title(title, fontsize=10, pad=8)
    ax.set_xlim(0, max(1, int(model.params.max_steps)))
    if y_limits is not None:
        ax.set_ylim(y_limits)
    ax.grid(color="#e7e9e2", linewidth=0.7)
    ax.legend(loc="best", fontsize=8, frameon=False)
    ax.tick_params(axis="both", labelsize=8)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.14, top=0.84)
    solara.FigureMatplotlib(fig, dependencies=[render_key], format="png")


@solara.component
def DegreeHistogram(model: AffordanceLandscapeModel, render_key: int):
    fig = Figure(figsize=(5.2, 2.8), facecolor="#ffffff")
    ax = fig.subplots()
    degrees = [degree for _, degree in model.graph.degree()] if model.graph is not None else []
    if degrees:
        bins = np.arange(0, max(degrees) + 2)
        ax.hist(degrees, bins=bins, color="#f1f1ec", edgecolor=INK_COLOR, linewidth=0.8)
    else:
        ax.text(0.5, 0.5, "No links", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Network degree", fontsize=10, pad=8)
    ax.grid(color="#e7e9e2", linewidth=0.7)
    ax.tick_params(axis="both", labelsize=8)
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.14, top=0.84)
    solara.FigureMatplotlib(fig, dependencies=[render_key], format="png")


@solara.component
def Monitor(label: str, value: str):
    with solara.Div(classes=["aff-monitor"]):
        solara.Text(label, classes=["aff-monitor-label"])
        solara.Text(value, classes=["aff-monitor-value"])


@solara.component
def ControlSection(title: str):
    with solara.Div(classes=["aff-section-title"]):
        solara.Text(title)


@solara.component
def Page():
    solara.Style(APP_STYLE)

    number_of_agents = solara.use_reactive(100)
    width = solara.use_reactive(101)
    height = solara.use_reactive(101)
    max_steps = solara.use_reactive(1000)
    seed = solara.use_reactive(74)
    pro_amount = solara.use_reactive(0.5)
    initial_pro = solara.use_reactive(0.5)
    initial_non = solara.use_reactive(0.5)
    networks = solara.use_reactive(False)
    network_type = solara.use_reactive("KE")
    network_param = solara.use_reactive(5.0)
    mu = solara.use_reactive(0.9)
    asocial_learning = solara.use_reactive(5.0e-5)
    social_learning = solara.use_reactive(7.0e-5)
    niche_construction = solara.use_reactive(False)
    construct_pro = solara.use_reactive(5.0)
    construct_non = solara.use_reactive(5.0)
    mutate_on = solara.use_reactive(False)

    initial_model = solara.use_memo(
        lambda: AffordanceLandscapeModel(
            AffordanceModelParams(
                number_of_agents=100,
                width=101,
                height=101,
                max_steps=1000,
            ),
            seed=74,
        ),
        dependencies=[],
    )
    model = solara.use_reactive(initial_model)
    running = solara.use_reactive(False)
    render_key = solara.use_reactive(0)

    def build_params() -> AffordanceModelParams:
        return _params_from_controls(
            number_of_agents=int(number_of_agents.value),
            width=int(width.value),
            height=int(height.value),
            pro_amount=float(pro_amount.value),
            initial_pro=float(initial_pro.value),
            initial_non=float(initial_non.value),
            networks=bool(networks.value),
            network_type=str(network_type.value),
            network_param=float(network_param.value),
            mu=float(mu.value),
            asocial_learning=float(asocial_learning.value),
            social_learning=float(social_learning.value),
            niche_construction=bool(niche_construction.value),
            construct_pro=float(construct_pro.value),
            construct_non=float(construct_non.value),
            mutate_on=bool(mutate_on.value),
            max_steps=int(max_steps.value),
        )

    def setup_model() -> None:
        running.set(False)
        model.set(AffordanceLandscapeModel(build_params(), seed=int(seed.value)))
        render_key.set(render_key.value + 1)

    def step_once() -> None:
        if not model.value.running:
            return
        model.value.step()
        render_key.set(render_key.value + 1)

    def toggle_running() -> None:
        if running.value:
            running.set(False)
        else:
            if not model.value.running:
                setup_model()
            running.set(True)

    async def run_loop():
        if not running.value:
            return
        while running.value and model.value.running:
            model.value.step()
            render_key.set(render_key.value + 1)
            await asyncio.sleep(PLAY_INTERVAL_SECONDS)
        if running.value:
            running.set(False)

    solara.lab.use_task(
        run_loop,
        dependencies=[running.value, id(model.value)],
        prefer_threaded=False,
    )

    current = model.value
    pro_affordances = int(current.affordances.sum())
    df = _plot_dataframe(current)
    final = df.iloc[-1]

    with solara.Div(classes=["aff-root"]):
        with solara.Div(classes=["aff-grid"]):
            with solara.Div(classes=["aff-panel", "aff-controls"]):
                solara.Text("Affordance Landscape", classes=["aff-title"])
                with solara.Div(classes=["aff-button-row"]):
                    solara.Button(
                        "Setup",
                        icon_name="mdi-refresh",
                        on_click=setup_model,
                        disabled=running.value,
                        color="green",
                        style={"color": "white"},
                    )
                    solara.Button(
                        "Step",
                        icon_name="mdi-skip-next",
                        on_click=step_once,
                        disabled=running.value or not current.running,
                        color="green",
                        outlined=True,
                    )
                    solara.Button(
                        "Stop" if running.value else "Run",
                        icon_name="mdi-stop" if running.value else "mdi-play",
                        on_click=toggle_running,
                        color="green",
                        style={"color": "white"},
                    )

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("Run")
                    solara.SliderInt("Agents", value=number_of_agents, min=20, max=600, step=10)
                    solara.SliderInt("Width", value=width, min=31, max=201, step=10)
                    solara.SliderInt("Height", value=height, min=31, max=201, step=10)
                    solara.SliderInt("Max steps", value=max_steps, min=50, max=5000, step=50)
                    solara.InputInt("Seed", value=seed, dense=True)

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("Core")
                    solara.SliderFloat("Pro affordances", value=pro_amount, min=0.0, max=1.0, step=0.01)
                    solara.SliderFloat("Initial pro", value=initial_pro, min=0.0, max=1.0, step=0.01)
                    solara.SliderFloat("Initial non", value=initial_non, min=0.0, max=1.0, step=0.01)
                    solara.Switch(label="Networks", value=networks, color="green")
                    solara.Select(
                        "Network type",
                        value=network_type,
                        values=["KE", "random", "small-world", "preferential"],
                        dense=True,
                    )
                    solara.SliderFloat("Network param", value=network_param, min=1.0, max=20.0, step=0.5)
                    solara.SliderFloat("Mu", value=mu, min=0.0, max=1.0, step=0.01)
                    solara.InputFloat("Asocial learning", value=asocial_learning, dense=True)
                    solara.InputFloat("Social learning", value=social_learning, dense=True)
                    solara.Switch(label="Niche construction", value=niche_construction, color="green")
                    solara.SliderFloat("Construct pro", value=construct_pro, min=0.0, max=20.0, step=0.5)
                    solara.SliderFloat("Construct non", value=construct_non, min=0.0, max=20.0, step=0.5)
                    solara.Switch(label="Mutation", value=mutate_on, color="green")

            with solara.Div(classes=["aff-panel", "aff-world"]):
                WorldPlot(current, render_key.value)

            with solara.Div(classes=["aff-right"]):
                with solara.Div(classes=["aff-monitor-grid"]):
                    Monitor("Step", f"{current.steps}")
                    Monitor("Pro", f"{int(final['pro_behaviour'])}")
                    Monitor("Non", f"{int(final['non_behaviour'])}")
                    Monitor("Aff.", f"{pro_affordances:,}")

                with solara.Div(classes=["aff-plot-grid"], style={"marginTop": "10px"}):
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "Behaviour share",
                            [
                                ("pro_behaviour_share", INK_COLOR, "pro"),
                                ("non_behaviour_share", RED_COLOR, "non"),
                            ],
                            y_limits=(0, 1),
                        )
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "Mean personal states",
                            [
                                ("mean_pro_env", INK_COLOR, "pro"),
                                ("mean_non_env", RED_COLOR, "non"),
                            ],
                            y_limits=(0, 1),
                        )
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "Landscape and dominance",
                            [
                                ("pro_affordance_share", VIOLET_COLOR, "aff."),
                                ("dominant_pro_share", LINK_COLOR, "dom."),
                            ],
                            y_limits=(0, 1),
                        )
                    with solara.Div(classes=["aff-panel"]):
                        DegreeHistogram(current, render_key.value)


page = Page
