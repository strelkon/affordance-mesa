import json
from pathlib import Path


def test_ev_scenarios_notebook_is_valid_and_clean():
    notebook_path = Path("notebooks/ev_scenarios.ipynb")

    with notebook_path.open() as handle:
        notebook = json.load(handle)

    code_cells = [
        cell for cell in notebook["cells"] if cell["cell_type"] == "code"
    ]
    source = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"]
    )

    assert notebook["nbformat"] == 4
    assert code_cells
    assert all(cell["outputs"] == [] for cell in code_cells)
    assert all(cell["execution_count"] is None for cell in code_cells)
    assert "from_scenario" in source
