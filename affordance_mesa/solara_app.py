"""Solara dashboard for the EV affordance-landscape extension."""

from __future__ import annotations

import asyncio
from typing import Iterable

import matplotlib.colors as mcolors
import numpy as np
import solara
from matplotlib.figure import Figure

from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams, SCENARIOS

PLAY_INTERVAL_SECONDS = 0.08
MAX_LINKS_DRAWN = 1500

BACKGROUND_COLOR = "#f4f5f0"
PANEL_BORDER = "#cfd5cd"
INK_COLOR = "#171717"
RED_COLOR = "#d64b3c"
GREEN_COLOR = "#2f855a"
BLUE_COLOR = "#2b8a90"
VIOLET_COLOR = "#7b4cc2"
AMBER_COLOR = "#d08a1d"
LIGHT_COLOR = "#fbfcfa"

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
  grid-template-columns: minmax(260px, 310px) minmax(430px, 620px) minmax(430px, 1fr);
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
  grid-template-columns: repeat(5, minmax(0, 1fr));
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
  font-size: 21px;
  font-weight: 700;
  line-height: 1.15;
  color: #171717;
}
.aff-panel .v-card__text {
  padding: 0 !important;
}
@media (max-width: 1360px) {
  .aff-grid {
    grid-template-columns: 310px minmax(430px, 1fr);
  }
  .aff-right {
    grid-column: 1 / -1;
  }
}
@media (max-width: 780px) {
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


DEFAULT_PARAMS = EVParams()


def _params_from_controls(
    *,
    number_of_agents: int,
    width: int,
    height: int,
    max_steps: int,
    pro_amount: float,
    initial_pro: float,
    initial_non: float,
    networks: bool,
    network_type: str,
    network_param: float,
    mu: float,
    subsidy: float,
    fuel_price: float,
    electricity_price: float,
    initial_charging_coverage: float,
    charger_expansion_rate: float,
    charger_access_decay: float,
    adoption_threshold: float,
    economic_weight: float,
    charging_weight: float,
    environmental_weight: float,
    peer_weight: float,
    range_anxiety_weight: float,
    income_mean: float,
    annual_mileage_mean: float,
) -> EVParams:
    return EVParams(
        number_of_agents=number_of_agents,
        width=width,
        height=height,
        max_steps=max_steps,
        pro_amount=pro_amount,
        initial_pro=initial_pro,
        initial_non=initial_non,
        networks=networks,
        network_type=network_type,
        network_param=network_param,
        mu=mu,
        subsidy=subsidy,
        fuel_price=fuel_price,
        electricity_price=electricity_price,
        initial_charging_coverage=initial_charging_coverage,
        charger_expansion_rate=charger_expansion_rate,
        charger_access_decay=charger_access_decay,
        adoption_threshold=adoption_threshold,
        economic_weight=economic_weight,
        charging_weight=charging_weight,
        environmental_weight=environmental_weight,
        peer_weight=peer_weight,
        range_anxiety_weight=range_anxiety_weight,
        income_mean=income_mean,
        annual_mileage_mean=annual_mileage_mean,
    )


def _plot_dataframe(model: EVAdoptionModel):
    return model.datacollector.get_model_vars_dataframe().reset_index(names="step")


def _agent_positions(model: EVAdoptionModel) -> tuple[np.ndarray, np.ndarray]:
    positions = [agent.pos for agent in model.agent_list if agent.pos is not None]
    if not positions:
        return np.array([], dtype=float), np.array([], dtype=float)
    x, y = zip(*positions, strict=True)
    return np.asarray(x, dtype=float), np.asarray(y, dtype=float)


def _agent_colors(model: EVAdoptionModel) -> list[str]:
    colors = []
    for agent in model.agent_list:
        if agent.ev_adopted:
            colors.append(GREEN_COLOR)
        elif agent.dominant_state == "pro":
            colors.append(INK_COLOR)
        elif agent.dominant_state == "non":
            colors.append(RED_COLOR)
        else:
            colors.append("#f1f1ec")
    return colors


def _network_edges(model: EVAdoptionModel) -> Iterable[tuple[tuple[int, int], tuple[int, int]]]:
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
def WorldPlot(model: EVAdoptionModel, render_key: int):
    fig = Figure(figsize=(6.4, 6.4), facecolor="#ffffff")
    ax = fig.subplots()

    charger_cmap = mcolors.LinearSegmentedColormap.from_list(
        "charging_access",
        ["#f6f8f2", "#d8ead7", "#85bd8f", "#2f855a"],
    )
    affordance_cmap = mcolors.ListedColormap(["#00000000", "#7b4cc2"])

    ax.imshow(
        model.charging_access.T,
        origin="lower",
        cmap=charger_cmap,
        interpolation="nearest",
        vmin=0,
        vmax=1,
    )
    ax.imshow(
        np.where(model.affordances == 1, 1.0, np.nan).T,
        origin="lower",
        cmap=affordance_cmap,
        interpolation="nearest",
        alpha=0.18,
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
            color=BLUE_COLOR,
            alpha=0.3,
            linewidth=0.4,
            zorder=1,
        )

    if model.chargers:
        charger_x, charger_y = zip(*model.chargers, strict=True)
        ax.scatter(
            charger_x,
            charger_y,
            marker="s",
            s=30,
            color=AMBER_COLOR,
            edgecolors="#ffffff",
            linewidths=0.4,
            alpha=0.95,
            zorder=2,
            label="chargers",
        )

    x, y = _agent_positions(model)
    if len(x) > 0:
        ax.scatter(
            x,
            y,
            c=_agent_colors(model),
            s=20,
            alpha=0.95,
            linewidths=0.2,
            edgecolors="#ffffff",
            zorder=3,
        )

    ax.set_title("Charging access, chargers, and agents", fontsize=10, pad=8)
    ax.set_xlim(-0.5, model.params.width - 0.5)
    ax.set_ylim(-0.5, model.params.height - 0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_edgecolor(INK_COLOR)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.95)
    solara.FigureMatplotlib(fig, dependencies=[render_key], format="png")


@solara.component
def TimeseriesPlot(
    model: EVAdoptionModel,
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
    ax.set_xlim(0, max(1, int(df["step"].max())))
    if y_limits is not None:
        ax.set_ylim(y_limits)
    ax.grid(color="#e7e9e2", linewidth=0.7)
    ax.legend(loc="best", fontsize=8, frameon=False)
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

    number_of_agents = solara.use_reactive(DEFAULT_PARAMS.number_of_agents)
    width = solara.use_reactive(DEFAULT_PARAMS.width)
    height = solara.use_reactive(DEFAULT_PARAMS.height)
    max_steps = solara.use_reactive(1000)
    seed = solara.use_reactive(42)
    scenario = solara.use_reactive("custom")

    pro_amount = solara.use_reactive(DEFAULT_PARAMS.pro_amount)
    initial_pro = solara.use_reactive(DEFAULT_PARAMS.initial_pro)
    initial_non = solara.use_reactive(DEFAULT_PARAMS.initial_non)
    networks = solara.use_reactive(DEFAULT_PARAMS.networks)
    network_type = solara.use_reactive(DEFAULT_PARAMS.network_type)
    network_param = solara.use_reactive(DEFAULT_PARAMS.network_param)
    mu = solara.use_reactive(DEFAULT_PARAMS.mu)

    subsidy = solara.use_reactive(DEFAULT_PARAMS.subsidy)
    fuel_price = solara.use_reactive(DEFAULT_PARAMS.fuel_price)
    electricity_price = solara.use_reactive(DEFAULT_PARAMS.electricity_price)
    initial_charging_coverage = solara.use_reactive(DEFAULT_PARAMS.initial_charging_coverage)
    charger_expansion_rate = solara.use_reactive(DEFAULT_PARAMS.charger_expansion_rate)
    charger_access_decay = solara.use_reactive(DEFAULT_PARAMS.charger_access_decay)
    adoption_threshold = solara.use_reactive(DEFAULT_PARAMS.adoption_threshold)

    economic_weight = solara.use_reactive(DEFAULT_PARAMS.economic_weight)
    charging_weight = solara.use_reactive(DEFAULT_PARAMS.charging_weight)
    environmental_weight = solara.use_reactive(DEFAULT_PARAMS.environmental_weight)
    peer_weight = solara.use_reactive(DEFAULT_PARAMS.peer_weight)
    range_anxiety_weight = solara.use_reactive(DEFAULT_PARAMS.range_anxiety_weight)
    income_mean = solara.use_reactive(DEFAULT_PARAMS.income_mean)
    annual_mileage_mean = solara.use_reactive(DEFAULT_PARAMS.annual_mileage_mean)

    initial_model = solara.use_memo(
        lambda: EVAdoptionModel(
            EVParams(max_steps=1000),
            seed=42,
        ),
        dependencies=[],
    )
    model = solara.use_reactive(initial_model)
    running = solara.use_reactive(False)
    render_key = solara.use_reactive(0)

    def build_params() -> EVParams:
        return _params_from_controls(
            number_of_agents=int(number_of_agents.value),
            width=int(width.value),
            height=int(height.value),
            max_steps=int(max_steps.value),
            pro_amount=float(pro_amount.value),
            initial_pro=float(initial_pro.value),
            initial_non=float(initial_non.value),
            networks=bool(networks.value),
            network_type=str(network_type.value),
            network_param=float(network_param.value),
            mu=float(mu.value),
            subsidy=float(subsidy.value),
            fuel_price=float(fuel_price.value),
            electricity_price=float(electricity_price.value),
            initial_charging_coverage=float(initial_charging_coverage.value),
            charger_expansion_rate=float(charger_expansion_rate.value),
            charger_access_decay=float(charger_access_decay.value),
            adoption_threshold=float(adoption_threshold.value),
            economic_weight=float(economic_weight.value),
            charging_weight=float(charging_weight.value),
            environmental_weight=float(environmental_weight.value),
            peer_weight=float(peer_weight.value),
            range_anxiety_weight=float(range_anxiety_weight.value),
            income_mean=float(income_mean.value),
            annual_mileage_mean=float(annual_mileage_mean.value),
        )

    def setup_model() -> None:
        running.set(False)
        model.set(EVAdoptionModel(build_params(), seed=int(seed.value)))
        render_key.set(render_key.value + 1)

    def apply_scenario() -> None:
        if scenario.value != "custom":
            p = EVParams.from_scenario(scenario.value)
            number_of_agents.set(p.number_of_agents)
            subsidy.set(p.subsidy)
            fuel_price.set(p.fuel_price)
            electricity_price.set(p.electricity_price)
            initial_charging_coverage.set(p.initial_charging_coverage)
            charger_expansion_rate.set(p.charger_expansion_rate)
            setup_model()

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
    df = _plot_dataframe(current)
    final = df.iloc[-1]

    with solara.Div(classes=["aff-root"]):
        with solara.Div(classes=["aff-grid"]):
            with solara.Div(classes=["aff-panel", "aff-controls"]):
                solara.Text("EV Affordance Model", classes=["aff-title"])
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
                    ControlSection("Scenario")
                    solara.Select(
                        "Scenario",
                        value=scenario,
                        values=["custom"] + sorted(SCENARIOS),
                        dense=True,
                    )
                    solara.Button("Apply scenario", on_click=apply_scenario)

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("Run")
                    solara.SliderInt("Agents", value=number_of_agents, min=20, max=600, step=10)
                    solara.SliderInt("Width", value=width, min=31, max=201, step=10)
                    solara.SliderInt("Height", value=height, min=31, max=201, step=10)
                    solara.SliderInt("Max steps", value=max_steps, min=50, max=25000, step=50)
                    solara.InputInt("Seed", value=seed, dense=True)

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("EV policy")
                    solara.SliderFloat("Subsidy", value=subsidy, min=0.0, max=20000.0, step=500.0)
                    solara.SliderFloat("Fuel price", value=fuel_price, min=0.5, max=4.0, step=0.1)
                    solara.SliderFloat("Electricity price", value=electricity_price, min=0.05, max=1.0, step=0.05)
                    solara.SliderFloat("Adoption threshold", value=adoption_threshold, min=0.0, max=0.8, step=0.01)

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("Charging")
                    solara.SliderFloat(
                        "Initial coverage",
                        value=initial_charging_coverage,
                        min=0.0,
                        max=0.2,
                        step=0.01,
                    )
                    solara.SliderFloat("New chargers / step", value=charger_expansion_rate, min=0.0, max=5.0, step=0.1)
                    solara.SliderFloat("Access decay", value=charger_access_decay, min=0.5, max=10.0, step=0.5)

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("Consumers")
                    solara.SliderFloat("Income mean", value=income_mean, min=10000.0, max=80000.0, step=1000.0)
                    solara.SliderFloat("Annual mileage mean", value=annual_mileage_mean, min=2000.0, max=30000.0, step=1000.0)
                    solara.SliderFloat("Economic weight", value=economic_weight, min=0.0, max=1.0, step=0.01)
                    solara.SliderFloat("Charging weight", value=charging_weight, min=0.0, max=1.0, step=0.01)
                    solara.SliderFloat("Environmental weight", value=environmental_weight, min=0.0, max=1.0, step=0.01)
                    solara.SliderFloat("Peer weight", value=peer_weight, min=0.0, max=1.0, step=0.01)
                    solara.SliderFloat("Range anxiety weight", value=range_anxiety_weight, min=0.0, max=1.0, step=0.01)

                with solara.Div(classes=["aff-control-block"]):
                    ControlSection("Affordance core")
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

            with solara.Div(classes=["aff-panel", "aff-world"]):
                WorldPlot(current, render_key.value)

            with solara.Div(classes=["aff-right"]):
                with solara.Div(classes=["aff-monitor-grid"]):
                    Monitor("Step", f"{current.steps}")
                    Monitor("EV share", f"{current.ev_adoption_share:.3f}")
                    Monitor("Score", f"{current.mean_adoption_score:.3f}")
                    Monitor("Access", f"{current.mean_charging_access:.3f}")
                    Monitor("Chargers", f"{len(current.chargers):,}")

                with solara.Div(classes=["aff-plot-grid"], style={"marginTop": "10px"}):
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "EV adoption and score",
                            [
                                ("ev_adoption_share", GREEN_COLOR, "adoption"),
                                ("mean_adoption_score", INK_COLOR, "score"),
                            ],
                            y_limits=(0, 1),
                        )
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "Charging infrastructure",
                            [
                                ("mean_charging_access", BLUE_COLOR, "access"),
                                ("charger_count", AMBER_COLOR, "chargers"),
                            ],
                        )
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "TCO gap",
                            [("mean_tco_gap", GREEN_COLOR, "ICE - EV")],
                        )
                    with solara.Div(classes=["aff-panel"]):
                        TimeseriesPlot(
                            current,
                            render_key.value,
                            "Affordance behaviour",
                            [
                                ("pro_behaviour_share", INK_COLOR, "pro"),
                                ("non_behaviour_share", RED_COLOR, "non"),
                            ],
                            y_limits=(0, 1),
                        )


page = Page
