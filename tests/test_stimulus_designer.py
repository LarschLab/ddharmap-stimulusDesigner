import json
from pathlib import Path

import pandas as pd

from src.stimulus_designer import (
    Calibration,
    GridSettings,
    Primitive,
    StimulusProject,
    StimulusSpec,
    default_project,
    export_project,
    generate_stimulus_dataframe,
    import_legacy_config,
    launch_psychopy_projection,
    make_grid_point,
    mirror_stimulus_in_place,
    project_from_dict,
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


def test_point_path_bout_holds_each_clicked_point():
    grid = GridSettings(points_per_ring=4, movement_interval_ms=500)
    points = [make_grid_point(0, 0, grid), make_grid_point(0, 1, grid)]
    spec = StimulusSpec(
        key="Path",
        primitives=[Primitive("point_path", {"points": points, "movement_interval_ms": 500, "mode": "bout"})],
    )
    df = generate_stimulus_dataframe(spec)
    assert len(df) == 60
    assert df.iloc[0]["dot0_x"] == points[0]["x_cm"]
    assert df.iloc[29]["dot0_x"] == points[0]["x_cm"]
    assert df.iloc[30]["dot0_x"] == points[1]["x_cm"]


def test_point_path_continuous_interpolates_between_clicked_points():
    grid = GridSettings(points_per_ring=4, movement_interval_ms=500)
    points = [make_grid_point(0, 0, grid), make_grid_point(0, 1, grid)]
    spec = StimulusSpec(
        key="Path",
        primitives=[Primitive("point_path", {"points": points, "movement_interval_ms": 500, "mode": "continuous"})],
    )
    df = generate_stimulus_dataframe(spec)
    assert len(df) == 30
    assert df.iloc[-1]["dot0_x"] == points[1]["x_cm"]
    assert df["dot0_x"].nunique() > 1


def test_mirror_stimulus_negates_angles_and_point_path_positions():
    grid = GridSettings(points_per_ring=8)
    point = make_grid_point(0, 1, grid)
    spec = StimulusSpec(
        key="Mirror",
        primitives=[
            Primitive("static_hold", {"angle_deg": -30.0}),
            Primitive("arc", {"angle_range": [-30.0, -160.0]}),
            Primitive("point_path", {"points": [point], "movement_interval_ms": 600, "mode": "bout"}),
        ],
    )
    mirror_stimulus_in_place(spec)
    assert spec.primitives[0].params["angle_deg"] == 30.0
    assert spec.primitives[1].params["angle_range"] == [30.0, 160.0]
    mirrored_point = spec.primitives[2].params["points"][0]
    assert mirrored_point["angle_deg"] == -point["angle_deg"]
    assert mirrored_point["point_index"] != point["point_index"]
    assert mirrored_point["x_cm"] != point["x_cm"]


def test_project_from_dict_loads_legacy_without_grid_settings():
    project = project_from_dict(
        {
            "stimuli": [
                {
                    "key": "Legacy",
                    "name": "Legacy",
                    "n_dots": 1,
                    "primitives": [{"kind": "static_hold", "params": {"duration_sec": 1.0}}],
                }
            ]
        }
    )
    assert project.grid_settings.ring_count == 3
    assert project.grid_settings.movement_mode == "bout"


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
