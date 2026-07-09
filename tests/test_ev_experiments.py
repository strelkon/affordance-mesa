import pandas as pd
import pytest

from scripts.run_ev_experiments import (
    parse_overrides,
    parse_sweep,
    run_experiments,
    run_sensitivity,
    run_single,
)


FAST_OVERRIDES = {
    "width": 10,
    "height": 10,
    "number_of_agents": 10,
    "max_steps": 50,
}


def test_run_single_returns_expected_columns():
    df = run_single("no_policy", seed=1, steps=3, overrides=FAST_OVERRIDES)

    assert len(df) == 4
    assert {"scenario", "seed", "step", "ev_adoption_share"} <= set(df.columns)
    assert (df["scenario"] == "no_policy").all()


def test_run_experiments_writes_outputs(tmp_path):
    summary = run_experiments(
        ["no_policy", "subsidy"],
        seeds=[1, 2],
        steps=3,
        output_dir=tmp_path,
        overrides=FAST_OVERRIDES,
    )

    assert (tmp_path / "ev_experiment_curves.csv").exists()
    assert (tmp_path / "ev_experiment_summary.csv").exists()
    assert (tmp_path / "ev_adoption_curves.png").exists()
    assert len(summary) == 2
    assert "final_ev_share_mean" in summary.columns


def test_run_experiments_scores_against_targets(tmp_path):
    targets_path = tmp_path / "targets.csv"
    pd.DataFrame(
        {
            "step": [0, 1, 2, 3],
            "ev_adoption_share": [0.0, 0.05, 0.1, 0.15],
        }
    ).to_csv(targets_path, index=False)

    summary = run_experiments(
        ["subsidy"],
        seeds=[1],
        steps=3,
        output_dir=tmp_path,
        overrides=FAST_OVERRIDES,
        targets_path=targets_path,
    )

    assert "target_rmse" in summary.columns
    assert summary["target_rmse"].notna().all()


def test_cli_set_override_parsing():
    assert parse_overrides(
        ["number_of_agents=10", "subsidy=9000.5", "networks=true"]
    ) == {"number_of_agents": 10, "subsidy": 9000.5, "networks": True}


def test_parse_sweep_parses_values_and_rejects_bad_input():
    assert parse_sweep("subsidy=0,4000,8000") == ("subsidy", [0, 4000, 8000])
    assert parse_sweep("adoption_rule=deterministic,logistic") == (
        "adoption_rule",
        ["deterministic", "logistic"],
    )

    with pytest.raises(ValueError):
        parse_sweep("subsidy")
    with pytest.raises(ValueError):
        parse_sweep("subsidy=8000")


def test_run_sensitivity_writes_summary_and_plots(tmp_path):
    summary = run_sensitivity(
        {"subsidy": [0.0, 12000.0], "adoption_threshold": [0.3, 0.4]},
        scenario="colleague_baseline",
        seeds=[1],
        steps=3,
        output_dir=tmp_path,
        overrides=FAST_OVERRIDES,
    )

    assert (tmp_path / "ev_sensitivity_summary.csv").exists()
    assert (tmp_path / "ev_sensitivity_subsidy.png").exists()
    assert (tmp_path / "ev_sensitivity_adoption_threshold.png").exists()
    assert len(summary) == 4
    assert {"param", "value", "final_ev_share_mean"} <= set(summary.columns)


def test_sensitivity_subsidy_monotonic_on_final_share(tmp_path):
    summary = run_sensitivity(
        {"subsidy": [0.0, 30000.0]},
        scenario="no_policy",
        seeds=[1],
        steps=10,
        output_dir=tmp_path,
        overrides=FAST_OVERRIDES,
    )
    pivot = summary.set_index("value")["final_ev_share_mean"]

    assert pivot.loc[30000.0] >= pivot.loc[0.0]
