import json
from pathlib import Path

import pandas as pd

from src.stimulus_designer import (
    Calibration,
    Primitive,
    StimulusProject,
    StimulusSpec,
    default_project,
    export_project,
    generate_stimulus_dataframe,
    import_legacy_config,
    launch_psychopy_projection,
)


def test_calibration_converts_px_and_cm():
    calibration = Calibration(screen_width_px=1000, screen_height_px=500, screen_width_mm=500, screen_height_mm=250)
    assert calibration.px_to_mm(10, 20) == (5.0, 10.0)
    assert calibration.cm_to_px(1.0, 2.0) == (20.0, 40.0)


def test_arc_generation_uses_canonical_columns():
    project = default_project()
    df = generate_stimulus_dataframe(project.stimuli[0], project.global_params)
    assert list(df.columns) == ["dot0_x", "dot0_y", "dot0_radius"]
    assert len(df) > 0
    assert df["dot0_radius"].max() == project.global_params.dot_size_cm


def test_flicker_generation_toggles_radius():
    spec = StimulusSpec(
        key="Flick",
        primitives=[Primitive("flicker", {"angle_range": [-30, -160], "angle_index": 2, "duration_sec": 1.0})],
    )
    df = generate_stimulus_dataframe(spec)
    assert 0.0 in set(df["dot0_radius"])


def test_export_project_writes_contract_files(tmp_path):
    project = default_project()
    written = export_project(project, tmp_path)
    assert written == [tmp_path / "LeB_trajectory.csv"]
    assert (tmp_path / "parameters" / "experiment_parameters.csv").exists()
    assert (tmp_path / "parameters" / "total_time_sec.csv").exists()
    assert (tmp_path / "parameters" / "stimulus_designer_project.json").exists()
    df = pd.read_csv(written[0])
    assert {"dot0_x", "dot0_y", "dot0_radius"}.issubset(df.columns)


def test_import_legacy_config_maps_known_shapes(tmp_path):
    config_path = tmp_path / "legacy.json"
    config_path.write_text(
        json.dumps(
            {
                "LeB": {
                    "name": "left_bout",
                    "type": "trajectory",
                    "angle_ranges": [[-30, -160]],
                    "n_dots": 1,
                    "flickering": True,
                },
                "Flick_L": {
                    "name": "flicker_left",
                    "type": "flicker",
                    "based_on": "LeB",
                    "angle_index": 10,
                    "n_dots": 1,
                },
            }
        )
    )
    project = import_legacy_config(config_path)
    assert [stim.key for stim in project.stimuli] == ["LeB", "Flick_L"]
    assert project.stimuli[0].primitives[0].kind == "arc"
    assert project.stimuli[1].primitives[0].kind == "flicker"


def test_launch_psychopy_command_is_parameterized(monkeypatch, tmp_path):
    calls = []

    class DummyProcess:
        pass

    def fake_popen(cmd):
        calls.append(cmd)
        return DummyProcess()

    monkeypatch.setattr("src.stimulus_designer.subprocess.Popen", fake_popen)
    process = launch_psychopy_projection(tmp_path, script_path=Path("scripts/stimuli/try_projection.py"))
    assert isinstance(process, DummyProcess)
    assert "--stimuli-path" in calls[0]
    assert str(tmp_path) in calls[0]
