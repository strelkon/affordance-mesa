"""Compare Mesa runs with NetLogo BehaviorSpace CSVs.

Place original NetLogo CSV exports in ``original_outputs/`` and run:

    python scripts/validate_against_netlogo.py

The script reads parameter settings from each CSV, runs the Mesa model with
matching settings where possible, and writes comparison summaries to
``outputs/validation/``.
"""

from __future__ import annotations

import argparse
import csv
import html
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

from affordance_mesa import AffordanceLandscapeModel, AffordanceModelParams


PARAMETER_COLUMNS = {
    "number-of-agents": "number_of_agents",
    "pro-amount": "pro_amount",
    "initial-pro": "initial_pro",
    "initial-non": "initial_non",
    "asocial-learning": "asocial_learning",
    "social-learning": "social_learning",
    "networks": "networks",
    "network-type": "network_type",
    "network-param": "network_param",
    "mu": "mu",
    "niche-construction": "niche_construction",
    "construct-pro": "construct_pro",
    "construct-non": "construct_non",
    "mutate-on?": "mutate_on",
}

METRIC_COLUMNS = {
    "pro-behavior": "pro_behaviour",
    "non-behavior": "non_behaviour",
    "mean [pro-env] of turtles": "mean_pro_env",
    "mean [non-env] of turtles": "mean_non_env",
    "global-clustering-coefficient": "global_clustering",
}

PATCH_COUNT_COLUMNS = {
    "count patches with [pcolor = violet]",
    "count patches with [affordance = 1]",
}

RUN_COLUMNS = ("[run number]", "run number", "run", "run_number")
STEP_COLUMNS = ("[step]", "step", "ticks", "tick")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-dir", type=Path, default=Path("original_outputs"))
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/validation"))
    parser.add_argument("--max-runs", type=int, default=20)
    parser.add_argument("--default-steps", type=int, default=1000)
    parser.add_argument("--base-seed", type=int, default=74)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_paths = sorted(args.original_dir.glob("*.csv"))
    if not csv_paths:
        print(f"No NetLogo CSVs found in {args.original_dir}. Nothing to validate.")
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for csv_path in csv_paths:
        netlogo = read_behaviorspace_csv(csv_path)
        comparison = compare_csv(
            netlogo=netlogo,
            max_runs=args.max_runs,
            default_steps=args.default_steps,
            base_seed=args.base_seed,
        )
        out_path = args.out_dir / f"{csv_path.stem}_comparison.csv"
        comparison.to_csv(out_path, index=False)
        print(f"Wrote {out_path}")


def read_behaviorspace_csv(path: Path) -> pd.DataFrame:
    header_row = find_header_row(path)
    df = pd.read_csv(path, header=header_row)
    df.columns = [str(column).strip() for column in df.columns]
    return df.dropna(how="all")


def find_header_row(path: Path) -> int:
    with path.open(newline="") as handle:
        for line_number, row in enumerate(csv.reader(handle)):
            normalized = {cell.strip() for cell in row}
            if normalized.intersection(RUN_COLUMNS) or normalized.intersection(STEP_COLUMNS):
                return line_number
            if "pro-behavior" in normalized or "mean [pro-env] of turtles" in normalized:
                return line_number
    return 0


def compare_csv(
    netlogo: pd.DataFrame,
    max_runs: int,
    default_steps: int,
    base_seed: int,
) -> pd.DataFrame:
    run_column = first_existing_column(netlogo, RUN_COLUMNS)
    step_column = first_existing_column(netlogo, STEP_COLUMNS)
    scenario_columns = [
        column for column in PARAMETER_COLUMNS if column in netlogo.columns
    ]
    group_columns = ([run_column] if run_column else []) + scenario_columns

    if group_columns:
        grouped = list(netlogo.groupby(group_columns, dropna=False, sort=False))
    else:
        grouped = [(None, netlogo)]

    rows: list[dict[str, Any]] = []
    for run_index, (_key, group) in enumerate(grouped[:max_runs]):
        final_netlogo = last_row_by_step(group, step_column)
        steps = steps_from_row(final_netlogo, step_column, default_steps)
        params = params_from_row(final_netlogo, default_steps=max(steps, 1))
        seed = seed_from_row(final_netlogo, run_index=run_index, base_seed=base_seed)

        model = AffordanceLandscapeModel(params=params, seed=seed)
        model.run_model(steps)
        mesa = model.datacollector.get_model_vars_dataframe()
        final_mesa = mesa.iloc[-1]

        rows.extend(metric_rows(final_netlogo, final_mesa, model, run_index, steps, seed))

    return pd.DataFrame(rows)


def first_existing_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    return next((column for column in candidates if column in df.columns), None)


def last_row_by_step(group: pd.DataFrame, step_column: str | None) -> pd.Series:
    if step_column is None:
        return group.iloc[-1]
    numeric_steps = pd.to_numeric(group[step_column], errors="coerce")
    if numeric_steps.notna().any():
        return group.loc[numeric_steps.idxmax()]
    return group.iloc[-1]


def steps_from_row(row: pd.Series, step_column: str | None, default_steps: int) -> int:
    if step_column is None:
        return default_steps
    steps = pd.to_numeric(row[step_column], errors="coerce")
    if pd.isna(steps):
        return default_steps
    return max(0, int(steps))


def params_from_row(row: pd.Series, default_steps: int) -> AffordanceModelParams:
    params = AffordanceModelParams(max_steps=default_steps)
    updates: dict[str, Any] = {}
    for netlogo_name, mesa_name in PARAMETER_COLUMNS.items():
        if netlogo_name in row.index and pd.notna(row[netlogo_name]):
            updates[mesa_name] = convert_value(row[netlogo_name])
    return replace(params, **updates)


def seed_from_row(row: pd.Series, run_index: int, base_seed: int) -> int | None:
    if is_false(row.get("random-seed?")):
        return base_seed + run_index
    if "rseed" in row.index and pd.notna(row["rseed"]):
        return int(float(row["rseed"]))
    return base_seed + run_index


def metric_rows(
    netlogo_row: pd.Series,
    mesa_row: pd.Series,
    model: AffordanceLandscapeModel,
    run_index: int,
    steps: int,
    seed: int | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for netlogo_metric, mesa_metric in METRIC_COLUMNS.items():
        if netlogo_metric not in netlogo_row.index or mesa_metric not in mesa_row.index:
            continue
        rows.append(
            comparison_row(
                run_index=run_index,
                steps=steps,
                seed=seed,
                metric=netlogo_metric,
                netlogo_value=netlogo_row[netlogo_metric],
                mesa_value=mesa_row[mesa_metric],
            )
        )

    for patch_column in PATCH_COUNT_COLUMNS.intersection(netlogo_row.index):
        mesa_patch_count = float(model.affordances.sum())
        rows.append(
            comparison_row(
                run_index=run_index,
                steps=steps,
                seed=seed,
                metric=patch_column,
                netlogo_value=netlogo_row[patch_column],
                mesa_value=mesa_patch_count,
            )
        )

    return rows


def comparison_row(
    run_index: int,
    steps: int,
    seed: int | None,
    metric: str,
    netlogo_value: Any,
    mesa_value: Any,
) -> dict[str, Any]:
    netlogo_float = float(netlogo_value)
    mesa_float = float(mesa_value)
    return {
        "run_index": run_index,
        "steps": steps,
        "mesa_seed": seed,
        "metric": metric,
        "netlogo": netlogo_float,
        "mesa": mesa_float,
        "difference": mesa_float - netlogo_float,
        "absolute_difference": abs(mesa_float - netlogo_float),
    }


def convert_value(value: Any) -> Any:
    if isinstance(value, str):
        stripped = html.unescape(value).strip().strip('"')
        lowered = stripped.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            number = float(stripped)
        except ValueError:
            return stripped
    else:
        number = float(value)

    if number.is_integer():
        return int(number)
    return number


def is_false(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    return isinstance(value, str) and value.strip().lower() == "false"


if __name__ == "__main__":
    main()
