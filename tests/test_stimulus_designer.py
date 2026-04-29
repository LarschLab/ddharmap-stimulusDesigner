import json
from pathlib import Path

import pandas as pd
import pytest

from src.stimulus_designer import (
    Calibration,
    GlobalStimulusParams,
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
    primitive_duration_summary,
    project_from_dict,
)
from src.stimuli_timeline import get_motion_timing_simple
from scripts.stimuli.try_projection import _dot_names_from_columns


def test_calibration_converts_px_and_cm():
    calibration = Calibration(screen_width_px=1000, screen_height_px=500, screen_width_mm=500, screen_height_mm=250)
    assert calibration.px_to_mm(10, 20) == (5.0, 10.0)
    assert calibration.cm_to_px(1.0, 2.0) == (20.0, 40.0)


def test_calibration_defaults_match_projector_setup():
    calibration = Calibration()
    assert calibration.screen_width_px == 1280
    assert calibration.screen_height_px == 800
    assert calibration.screen_width_mm == pytest.approx(152.0)
    assert calibration.screen_height_mm == pytest.approx(95.0)
    assert calibration.mm_per_px_x == pytest.approx(calibration.mm_per_px_y)


def test_arc_generation_uses_canonical_columns():
    spec = StimulusSpec(
        key="Arc",
        primitives=[
            Primitive("static_hold", {"duration_sec": 1.0, "angle_deg": -30.0}),
            Primitive("arc", {"angle_range": [-30.0, -160.0], "continuous": False}),
        ],
    )
    df = generate_stimulus_dataframe(spec)
    assert list(df.columns) == ["dot0_x", "dot0_y", "dot0_radius"]
    assert len(df) > 0
    assert df["dot0_radius"].max() > 0


def test_default_project_starts_with_blank_stimulus():
    project = default_project()
    assert len(project.stimuli) == 1
    assert project.stimuli[0].primitives == []
    df = generate_stimulus_dataframe(project.stimuli[0], project.global_params)
    assert list(df.columns) == ["dot0_x", "dot0_y", "dot0_radius"]
    assert df.empty


def test_flicker_generation_toggles_radius():
    spec = StimulusSpec(
        key="Flick",
        primitives=[Primitive("flicker", {"angle_range": [-30, -160], "angle_index": 2, "duration_sec": 1.0})],
    )
    df = generate_stimulus_dataframe(spec)
    assert 0.0 in set(df["dot0_radius"])


def test_static_hold_uses_grid_point_position():
    grid = GridSettings(points_per_ring=4)
    point = make_grid_point(0, 1, grid)
    spec = StimulusSpec(
        key="Hold",
        primitives=[Primitive("static_hold", {"point": point, "duration_sec": 0.5})],
    )
    df = generate_stimulus_dataframe(spec)
    assert len(df) == 30
    assert df.iloc[0]["dot0_x"] == point["x_cm"]
    assert df.iloc[0]["dot0_y"] == point["y_cm"]


def test_flicker_uses_grid_point_position_and_primitive_interval():
    grid = GridSettings(points_per_ring=4)
    point = make_grid_point(0, 1, grid)
    spec = StimulusSpec(
        key="FlickPoint",
        primitives=[Primitive("flicker", {"point": point, "duration_sec": 0.2, "flicker_interval_sec": 0.05})],
    )
    df = generate_stimulus_dataframe(spec)
    assert df.iloc[0]["dot0_x"] == point["x_cm"]
    assert 0.0 in set(df["dot0_radius"])


def test_rocking_uses_two_grid_points_and_duration():
    grid = GridSettings(points_per_ring=4)
    p1 = make_grid_point(0, 0, grid)
    p2 = make_grid_point(0, 1, grid)
    spec = StimulusSpec(
        key="Rock",
        primitives=[
            Primitive(
                "rocking",
                {"points": [p1, p2], "duration_sec": 0.5, "movement_interval_ms": 100},
            )
        ],
    )
    df = generate_stimulus_dataframe(spec)
    assert len(df) == 30
    assert set(df["dot0_x"]) == {p1["x_cm"], p2["x_cm"]}


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


def test_grid_settings_defaults_match_gui_startup_values():
    grid = GridSettings()
    assert grid.first_ring_radius_cm == 2.0
    assert grid.ring_spacing_cm == 0.4
    assert grid.points_per_ring == 12
    assert grid.movement_interval_ms == 700.0


def test_static_period_default_is_ten_seconds():
    assert GlobalStimulusParams().static_period_sec == 10.0


def test_whole_field_grating_generates_visual_columns():
    grid = GridSettings(points_per_ring=4)
    p1 = make_grid_point(0, 0, grid)
    p2 = make_grid_point(0, 1, grid)
    spec = StimulusSpec(
        key="Grating",
        primitives=[
            Primitive(
                "whole_field_grating",
                {
                    "points": [p1, p2],
                    "duration_sec": 0.5,
                    "bar_thickness_cm": 0.25,
                    "speed_cm_sec": 2.0,
                },
            )
        ],
    )
    df = generate_stimulus_dataframe(spec)
    assert len(df) == 30
    assert {"dot0_x", "dot0_y", "dot0_radius", "grating_active", "grating_phase_cm"}.issubset(df.columns)
    assert set(df["dot0_radius"]) == {0.0}
    assert set(df["grating_active"]) == {1.0}
    assert df["grating_bar_thickness_cm"].iloc[0] == pytest.approx(0.25)
    assert df["grating_speed_cm_sec"].iloc[0] == pytest.approx(2.0)
    assert df["grating_phase_cm"].iloc[-1] > df["grating_phase_cm"].iloc[0]


def test_linear_bout_steps_until_endpoint_is_exceeded():
    params = GlobalStimulusParams(framerate=10)
    spec = StimulusSpec(
        key="Linear",
        primitives=[
            Primitive(
                "linear",
                {
                    "points": [
                        {"x_cm": 0.0, "y_cm": 0.0},
                        {"x_cm": 0.5, "y_cm": 0.0},
                    ],
                    "movement_interval_ms": 100,
                    "mode": "bout",
                    "step_distance_cm": 0.2,
                },
            )
        ],
    )
    df = generate_stimulus_dataframe(spec, params)
    assert len(df) == 4
    assert list(df["dot0_x"]) == pytest.approx([0.0, 0.2, 0.4, 0.6])
    assert df["dot0_y"].tolist() == [0.0, 0.0, 0.0, 0.0]


def test_linear_continuous_interpolates_between_step_positions():
    params = GlobalStimulusParams(framerate=10)
    spec = StimulusSpec(
        key="Linear",
        primitives=[
            Primitive(
                "linear",
                {
                    "points": [
                        {"x_cm": 0.0, "y_cm": 0.0},
                        {"x_cm": 0.3, "y_cm": 0.0},
                    ],
                    "movement_interval_ms": 200,
                    "mode": "continuous",
                    "step_distance_cm": 0.2,
                },
            )
        ],
    )
    df = generate_stimulus_dataframe(spec, params)
    assert len(df) == 6
    assert df.iloc[0]["dot0_x"] == pytest.approx(0.0)
    assert df.iloc[-1]["dot0_x"] == pytest.approx(0.4)
    assert df["dot0_x"].nunique() > 3


def test_primitive_duration_summary_reports_cumulative_times():
    spec = StimulusSpec(
        key="Durations",
        primitives=[
            Primitive("static_hold", {"duration_sec": 1.0}),
            Primitive(
                "linear",
                {
                    "points": [{"x_cm": 0.0, "y_cm": 0.0}, {"x_cm": 0.3, "y_cm": 0.0}],
                    "movement_interval_ms": 100,
                    "mode": "bout",
                    "step_distance_cm": 0.2,
                },
            ),
        ],
    )
    summaries = primitive_duration_summary(spec, GlobalStimulusParams(framerate=10))
    assert summaries[0] == {"duration_sec": 1.0, "cumulative_sec": 1.0}
    assert summaries[1]["duration_sec"] == pytest.approx(0.3)
    assert summaries[1]["cumulative_sec"] == pytest.approx(1.3)


def test_whole_field_grating_needs_direction_points():
    spec = StimulusSpec(
        key="Grating",
        primitives=[Primitive("whole_field_grating", {"points": [], "duration_sec": 0.5})],
    )
    df = generate_stimulus_dataframe(spec)
    assert df.empty


def test_loom_grows_clamps_and_holds_until_duration():
    params = GlobalStimulusParams(framerate=10)
    spec = StimulusSpec(
        key="Loom",
        primitives=[
            Primitive(
                "loom",
                {
                    "duration_sec": 1.0,
                    "growth_speed_cm_sec": 2.0,
                    "max_radius_cm": 1.0,
                },
            )
        ],
    )
    df = generate_stimulus_dataframe(spec, params)
    assert len(df) == 10
    assert set(df["loom_active"]) == {1.0}
    assert df["loom_radius"].iloc[0] == pytest.approx(0.0)
    assert df["loom_radius"].max() == pytest.approx(1.0)
    assert df["loom_radius"].iloc[-1] == pytest.approx(1.0)


def test_motion_timing_uses_visual_active_columns(tmp_path):
    path = tmp_path / "Grating_trajectory.csv"
    pd.DataFrame(
        {
            "dot0_x": [0.0, 0.0, 0.0],
            "dot0_y": [0.0, 0.0, 0.0],
            "dot0_radius": [0.0, 0.0, 0.0],
            "grating_active": [0.0, 1.0, 1.0],
        }
    ).to_csv(path, index=False)
    timing = get_motion_timing_simple(path, framerate=10)
    assert timing["motion_start_frame"] == 1


def test_projection_dot_names_ignore_visual_columns():
    names = _dot_names_from_columns(
        ["dot0_x", "dot0_y", "dot1_x", "grating_x", "loom_x", "grating_active"]
    )
    assert names == ["dot0", "dot1"]


def test_mirror_stimulus_negates_angles_and_point_path_positions():
    grid = GridSettings(points_per_ring=8)
    point = make_grid_point(0, 1, grid)
    spec = StimulusSpec(
        key="Mirror",
        primitives=[
            Primitive("static_hold", {"angle_deg": -30.0}),
            Primitive("arc", {"angle_range": [-30.0, -160.0]}),
            Primitive("point_path", {"points": [point], "movement_interval_ms": 600, "mode": "bout"}),
            Primitive("linear", {"points": [point, make_grid_point(0, 2, grid)], "movement_interval_ms": 600, "mode": "bout"}),
        ],
    )
    mirror_stimulus_in_place(spec)
    assert spec.primitives[0].params["angle_deg"] == 30.0
    assert spec.primitives[1].params["angle_range"] == [30.0, 160.0]
    mirrored_point = spec.primitives[2].params["points"][0]
    assert mirrored_point["angle_deg"] == -point["angle_deg"]
    assert mirrored_point["point_index"] != point["point_index"]
    assert mirrored_point["x_cm"] != point["x_cm"]
    mirrored_linear_point = spec.primitives[3].params["points"][0]
    assert mirrored_linear_point["angle_deg"] == -point["angle_deg"]


def test_mirror_stimulus_mirrors_all_timeline_primitive_points_in_order():
    grid = GridSettings(points_per_ring=8)
    p1 = make_grid_point(0, 1, grid)
    p2 = make_grid_point(0, 2, grid)
    p3 = make_grid_point(0, 3, grid)
    spec = StimulusSpec(
        key="Mirror_All",
        primitives=[
            Primitive("static_hold", {"point": p1, "duration_sec": 1.0}),
            Primitive("flicker", {"point": p2, "duration_sec": 1.0}),
            Primitive("rocking", {"points": [p1, p2], "duration_sec": 1.0}),
            Primitive("rocking_lr", {"points": [p2, p3], "duration_sec": 1.0}),
            Primitive("point_path", {"points": [p1, p2, p3], "movement_interval_ms": 600, "mode": "bout"}),
            Primitive("linear", {"points": [p1, p3], "movement_interval_ms": 600, "mode": "bout"}),
            Primitive("whole_field_grating", {"points": [p1, p2], "duration_sec": 1.0}),
            Primitive("loom", {"point": p3, "duration_sec": 1.0}),
            Primitive("waypoint_move", {"x_cm": 1.25, "y_cm": -0.5, "duration_sec": 1.0}),
        ],
    )
    original_kinds = [primitive.kind for primitive in spec.primitives]

    mirror_stimulus_in_place(spec)

    assert [primitive.kind for primitive in spec.primitives] == original_kinds
    assert spec.primitives[0].params["point"]["angle_deg"] == -p1["angle_deg"]
    assert spec.primitives[1].params["point"]["angle_deg"] == -p2["angle_deg"]
    assert [point["angle_deg"] for point in spec.primitives[2].params["points"]] == [-p1["angle_deg"], -p2["angle_deg"]]
    assert [point["angle_deg"] for point in spec.primitives[3].params["points"]] == [-p2["angle_deg"], -p3["angle_deg"]]
    assert [point["angle_deg"] for point in spec.primitives[4].params["points"]] == [-p1["angle_deg"], -p2["angle_deg"], -p3["angle_deg"]]
    assert [point["angle_deg"] for point in spec.primitives[5].params["points"]] == [-p1["angle_deg"], -p3["angle_deg"]]
    assert [point["angle_deg"] for point in spec.primitives[6].params["points"]] == [-p1["angle_deg"], -p2["angle_deg"]]
    assert spec.primitives[7].params["point"]["angle_deg"] == -p3["angle_deg"]
    assert spec.primitives[8].params["x_cm"] == pytest.approx(-1.25)


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
    project = StimulusProject(
        stimuli=[
            StimulusSpec(
                key="LeB",
                name="left bout",
                primitives=[Primitive("static_hold", {"duration_sec": 1.0, "angle_deg": -30.0})],
            )
        ]
    )
    written = export_project(project, tmp_path)
    assert written == [tmp_path / "LeB_trajectory.csv"]
    assert (tmp_path / "parameters" / "experiment_parameters.csv").exists()
    assert (tmp_path / "parameters" / "total_time_sec.csv").exists()
    assert (tmp_path / "parameters" / "stimulus_designer_project.json").exists()
    df = pd.read_csv(written[0])
    assert {"dot0_x", "dot0_y", "dot0_radius"}.issubset(df.columns)


def test_export_project_rejects_empty_stimuli(tmp_path):
    project = default_project()
    with pytest.raises(ValueError, match="has no primitives"):
        export_project(project, tmp_path)


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
