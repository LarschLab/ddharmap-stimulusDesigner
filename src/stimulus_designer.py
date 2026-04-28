import json
import math
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_VERSION = 1


@dataclass
class Calibration:
    screen_width_px: int = 1920
    screen_height_px: int = 1080
    screen_width_mm: float = 590.0
    screen_height_mm: float = 330.0

    @property
    def mm_per_px_x(self) -> float:
        return self.screen_width_mm / float(self.screen_width_px)

    @property
    def mm_per_px_y(self) -> float:
        return self.screen_height_mm / float(self.screen_height_px)

    def cm_to_px(self, x_cm: float, y_cm: float) -> tuple[float, float]:
        x_px = (x_cm * 10.0) / self.mm_per_px_x
        y_px = (y_cm * 10.0) / self.mm_per_px_y
        return x_px, y_px

    def px_to_mm(self, x_px: float, y_px: float) -> tuple[float, float]:
        return x_px * self.mm_per_px_x, y_px * self.mm_per_px_y


@dataclass
class GlobalStimulusParams:
    radius_cm: float = 1.8
    speed_cm_sec: float = 0.497
    framerate: float = 60.0
    update_interval_ms: float = 600.0
    static_period_sec: float = 8.0
    dot_size_cm: float = 0.2
    rotation_angle_deg: float = 45.0
    flicker_interval_sec: float = 0.3
    pause_before_sec: float = 12.5
    pause_after_sec: float = 12.5
    repetitions: int = 1


@dataclass
class GridSettings:
    ring_count: int = 3
    first_ring_radius_cm: float = 1.0
    ring_spacing_cm: float = 0.4
    points_per_ring: int = 12
    movement_interval_ms: float = 70.0
    movement_mode: str = "bout"


@dataclass
class Primitive:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class StimulusSpec:
    key: str = "Stimulus_1"
    name: str = "Stimulus 1"
    n_dots: int = 1
    primitives: list[Primitive] = field(default_factory=list)


@dataclass
class StimulusProject:
    name: str = "stimulus_project"
    calibration: Calibration = field(default_factory=Calibration)
    global_params: GlobalStimulusParams = field(default_factory=GlobalStimulusParams)
    grid_settings: GridSettings = field(default_factory=GridSettings)
    stimuli: list[StimulusSpec] = field(default_factory=list)


def default_project() -> StimulusProject:
    return StimulusProject(
        stimuli=[
            StimulusSpec(
                key="LeB",
                name="left bout",
                n_dots=1,
                primitives=[],
            )
        ]
    )


def project_to_dict(project: StimulusProject) -> dict[str, Any]:
    data = asdict(project)
    data["version"] = PROJECT_VERSION
    return data


def project_from_dict(data: dict[str, Any]) -> StimulusProject:
    calibration = Calibration(**data.get("calibration", {}))
    global_params = GlobalStimulusParams(**data.get("global_params", {}))
    grid_settings = GridSettings(**data.get("grid_settings", {}))
    stimuli = []
    for stim_data in data.get("stimuli", []):
        primitives = [
            Primitive(kind=p["kind"], params=p.get("params", {}))
            for p in stim_data.get("primitives", [])
        ]
        stimuli.append(
            StimulusSpec(
                key=stim_data.get("key", "Stimulus"),
                name=stim_data.get("name", stim_data.get("key", "Stimulus")),
                n_dots=int(stim_data.get("n_dots", 1)),
                primitives=primitives,
            )
        )
    return StimulusProject(
        name=data.get("name", "stimulus_project"),
        calibration=calibration,
        global_params=global_params,
        grid_settings=grid_settings,
        stimuli=stimuli,
    )


def save_project(project: StimulusProject, path: str | Path) -> None:
    Path(path).write_text(json.dumps(project_to_dict(project), indent=2))


def load_project(path: str | Path) -> StimulusProject:
    return project_from_dict(json.loads(Path(path).read_text()))


def import_legacy_config(path: str | Path) -> StimulusProject:
    config = json.loads(Path(path).read_text())
    project = StimulusProject(name=Path(path).stem)
    saved_ranges: dict[str, list[float]] = {}
    for key, params in config.items():
        n_dots = int(params.get("n_dots", 1))
        stim_type = params.get("type", "trajectory")
        primitives: list[Primitive] = []
        if stim_type == "flicker":
            based_on = params["based_on"]
            angle_range = saved_ranges.get(based_on, [-30.0, -160.0])
            primitives.append(
                Primitive(
                    "flicker",
                    {
                        "angle_range": angle_range,
                        "angle_index": int(params.get("angle_index", 0)),
                        "duration_sec": None,
                    },
                )
            )
        else:
            angle_range = list(params.get("angle_ranges", [[-30.0, -160.0]])[0])
            saved_ranges[key] = angle_range
            if params.get("rocking_lr", False):
                primitives.append(
                    Primitive(
                        "rocking_lr",
                        {
                            "left_angle_range": params.get("left_angle_range", [-30.0, -163.0]),
                            "right_angle_range": params.get("right_angle_range", [30.0, 163.0]),
                            "rocking_lr_indices": params.get("rocking_lr_indices", [11, 13]),
                            "flickering": bool(params.get("flickering", False)),
                        },
                    )
                )
            elif params.get("rocking", False):
                primitives.append(
                    Primitive(
                        "rocking",
                        {
                            "angle_range": angle_range,
                            "rocking_idx_pair": params.get("rocking_idx_pair", [11, 13]),
                            "flickering": bool(params.get("flickering", False)),
                        },
                    )
                )
            else:
                primitives.append(
                    Primitive(
                        "arc",
                        {
                            "angle_range": angle_range,
                            "continuous": bool(params.get("continuous", False)),
                            "flickering": bool(params.get("flickering", False)),
                        },
                    )
                )
        project.stimuli.append(
            StimulusSpec(
                key=key,
                name=params.get("name", key),
                n_dots=n_dots,
                primitives=primitives,
            )
        )
    return project


def _rotated_position(radius_cm: float, angle_deg: float, rotation_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    theta = math.radians(rotation_deg)
    x = radius_cm * math.sin(angle)
    y = radius_cm * math.cos(angle)
    return (
        round(x * math.cos(theta) - y * math.sin(theta), 3),
        round(x * math.sin(theta) + y * math.cos(theta), 3),
    )


def grid_point_to_position(radius_cm: float, angle_deg: float, params: GlobalStimulusParams | None = None) -> tuple[float, float]:
    params = params or GlobalStimulusParams()
    return _rotated_position(radius_cm, angle_deg, params.rotation_angle_deg)


def make_grid_point(ring_index: int, point_index: int, grid: GridSettings, params: GlobalStimulusParams | None = None) -> dict[str, float | int]:
    ring_index = max(0, int(ring_index))
    point_index = int(point_index) % max(1, int(grid.points_per_ring))
    radius_cm = float(grid.first_ring_radius_cm) + ring_index * float(grid.ring_spacing_cm)
    angle_deg = -180.0 + (360.0 * point_index / max(1, int(grid.points_per_ring)))
    x_cm, y_cm = grid_point_to_position(radius_cm, angle_deg, params)
    return {
        "ring_index": ring_index,
        "point_index": point_index,
        "points_per_ring": max(1, int(grid.points_per_ring)),
        "radius_cm": round(radius_cm, 3),
        "angle_deg": round(angle_deg, 3),
        "x_cm": x_cm,
        "y_cm": y_cm,
    }


def _arc_samples(angle_range: list[float], params: GlobalStimulusParams, continuous: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    start_angle, end_angle = np.deg2rad(angle_range)
    omega = params.speed_cm_sec / params.radius_cm
    arc_length = params.radius_cm * abs(end_angle - start_angle)
    total_time = round(arc_length / params.speed_cm_sec, 4)
    step = 1.0 / params.framerate if continuous else params.update_interval_ms / 1000.0
    sample_times = np.round(np.arange(0.0, total_time + step, step), 4)
    sign = np.sign(end_angle - start_angle) if end_angle != start_angle else 1.0
    angles = start_angle + sign * omega * sample_times
    x = np.round(params.radius_cm * np.sin(angles), 3)
    y = np.round(params.radius_cm * np.cos(angles), 3)
    theta = np.deg2rad(params.rotation_angle_deg)
    xr = np.round(x * np.cos(theta) - y * np.sin(theta), 3)
    yr = np.round(x * np.sin(theta) + y * np.cos(theta), 3)
    return xr, yr, np.rad2deg(angles), total_time


def _apply_flicker(radius_values: list[float], start_frame: int, params: GlobalStimulusParams) -> None:
    interval_frames = max(1, int(round(params.flicker_interval_sec * params.framerate)))
    on = True
    for start in range(start_frame, len(radius_values), interval_frames):
        end = min(start + interval_frames, len(radius_values))
        radius_values[start:end] = [params.dot_size_cm if on else 0.0] * (end - start)
        on = not on


def _append_rows(rows: list[dict[str, float]], x: float, y: float, radius: float, frames: int) -> None:
    for _ in range(max(0, int(frames))):
        rows.append({"x": float(x), "y": float(y), "radius": float(radius)})


def _point_xy(point: dict[str, Any], params: GlobalStimulusParams) -> tuple[float, float]:
    if "radius_cm" in point and "angle_deg" in point:
        return grid_point_to_position(float(point["radius_cm"]), float(point["angle_deg"]), params)
    return float(point.get("x_cm", 0.0)), float(point.get("y_cm", 0.0))


def _primitive_point_xy(primitive_params: dict[str, Any], params: GlobalStimulusParams) -> tuple[float, float] | None:
    point = primitive_params.get("point")
    if isinstance(point, dict):
        return _point_xy(point, params)
    return None


def _point_path_rows(path_params: dict[str, Any], params: GlobalStimulusParams) -> list[dict[str, float]]:
    points = list(path_params.get("points", []))
    if not points:
        return []
    mode = str(path_params.get("mode", "bout")).lower()
    interval_ms = float(path_params.get("movement_interval_ms", params.update_interval_ms))
    frames = max(1, int(round((interval_ms / 1000.0) * params.framerate)))
    rows: list[dict[str, float]] = []
    xy_points = [_point_xy(point, params) for point in points]
    if mode == "continuous" and len(xy_points) > 1:
        for (x0, y0), (x1, y1) in zip(xy_points[:-1], xy_points[1:]):
            for frame in range(frames):
                frac = (frame + 1) / frames
                x = x0 + (x1 - x0) * frac
                y = y0 + (y1 - y0) * frac
                _append_rows(rows, x, y, params.dot_size_cm, 1)
    else:
        for x, y in xy_points:
            _append_rows(rows, x, y, params.dot_size_cm, frames)
    return rows


def _point_rocking_rows(rocking_params: dict[str, Any], params: GlobalStimulusParams) -> list[dict[str, float]]:
    points = list(rocking_params.get("points", []))
    if len(points) < 2:
        return []
    x1, y1 = _point_xy(points[0], params)
    x2, y2 = _point_xy(points[1], params)
    duration = float(rocking_params.get("duration_sec", 1.0))
    interval_ms = float(rocking_params.get("movement_interval_ms", params.update_interval_ms))
    total_frames = max(1, int(round(duration * params.framerate)))
    frames_per_update = max(1, int(round((interval_ms / 1000.0) * params.framerate)))
    rows: list[dict[str, float]] = []
    filled = 0
    toggle = False
    while filled < total_frames:
        block = min(frames_per_update, total_frames - filled)
        toggle = not toggle
        x, y = (x1, y1) if toggle else (x2, y2)
        _append_rows(rows, x, y, params.dot_size_cm, block)
        filled += block
    if rocking_params.get("flickering", False):
        radii = [row["radius"] for row in rows]
        _apply_flicker(radii, 0, params)
        for row, radius in zip(rows, radii):
            row["radius"] = radius
    return rows


def _generate_dot_rows(spec: StimulusSpec, dot_index: int, params: GlobalStimulusParams) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    current_x, current_y = _rotated_position(params.radius_cm, -30.0, params.rotation_angle_deg)

    for primitive in spec.primitives:
        kind = primitive.kind
        p = primitive.params
        if kind == "static_hold":
            point_xy = _primitive_point_xy(p, params)
            if point_xy is not None:
                current_x, current_y = point_xy
            elif "angle_deg" in p:
                current_x, current_y = _rotated_position(params.radius_cm, float(p["angle_deg"]), params.rotation_angle_deg)
            frames = round(float(p.get("duration_sec", params.static_period_sec)) * params.framerate)
            _append_rows(rows, current_x, current_y, params.dot_size_cm, frames)

        elif kind in {"arc", "continuous_arc"}:
            angle_range = list(p.get("angle_range", [-30.0, -160.0]))
            continuous = bool(p.get("continuous", kind == "continuous_arc"))
            if not rows:
                x0, y0 = _rotated_position(params.radius_cm, angle_range[0], params.rotation_angle_deg)
                _append_rows(rows, x0, y0, params.dot_size_cm, round(params.static_period_sec * params.framerate))
            flicker_start = len(rows)
            xr, yr, _, total_time = _arc_samples(angle_range, params, continuous)
            n_frames = int(round(params.framerate * total_time))
            frame_times = np.round(np.arange(0.0, total_time + (1.0 / params.framerate), 1.0 / params.framerate), 4)
            sample_times = np.round(np.linspace(0.0, total_time, len(xr)), 4) if continuous else np.round(np.arange(0.0, total_time + params.update_interval_ms / 1000.0, params.update_interval_ms / 1000.0), 4)
            for frame in range(n_frames):
                t = frame_times[frame]
                if t in sample_times:
                    idx = int(np.where(sample_times == t)[0][0])
                    current_x = float(xr[min(idx + 1, len(xr) - 1)])
                    current_y = float(yr[min(idx + 1, len(yr) - 1)])
                _append_rows(rows, current_x, current_y, params.dot_size_cm, 1)
            if p.get("flickering", False):
                radii = [row["radius"] for row in rows]
                _apply_flicker(radii, flicker_start, params)
                for row, radius in zip(rows, radii):
                    row["radius"] = radius

        elif kind == "flicker":
            point_xy = _primitive_point_xy(p, params)
            total_time = 0.0
            if point_xy is not None:
                current_x, current_y = point_xy
            else:
                angle_range = list(p.get("angle_range", [-30.0, -160.0]))
                xr, yr, _, total_time = _arc_samples(angle_range, params, False)
                idx = max(0, min(len(xr) - 1, int(p.get("angle_index", 0))))
                current_x = float(xr[idx])
                current_y = float(yr[idx])
            duration = p.get("duration_sec")
            if duration is None:
                duration = total_time + params.flicker_interval_sec
            _append_rows(rows, current_x, current_y, params.dot_size_cm, round(params.static_period_sec * params.framerate))
            start = len(rows)
            _append_rows(rows, current_x, current_y, params.dot_size_cm, round(float(duration) * params.framerate))
            radii = [row["radius"] for row in rows]
            flicker_params = params
            if "flicker_interval_sec" in p:
                flicker_params = GlobalStimulusParams(**{**asdict(params), "flicker_interval_sec": float(p["flicker_interval_sec"])})
            _apply_flicker(radii, start, flicker_params)
            for row, radius in zip(rows, radii):
                row["radius"] = radius

        elif kind == "rocking":
            point_rows = _point_rocking_rows(p, params)
            if point_rows:
                rows.extend(point_rows)
            else:
                angle_range = list(p.get("angle_range", [-30.0, -163.0]))
                i1, i2 = p.get("rocking_idx_pair", [11, 13])
                rows.extend(_rocking_rows(params, angle_range, int(i1), int(i2), bool(p.get("flickering", False))))
            if rows:
                current_x = rows[-1]["x"]
                current_y = rows[-1]["y"]

        elif kind == "rocking_lr":
            point_rows = _point_rocking_rows(p, params)
            if point_rows:
                rows.extend(point_rows)
            else:
                left_range = list(p.get("left_angle_range", [-30.0, -163.0]))
                right_range = list(p.get("right_angle_range", [30.0, 163.0]))
                i_left, i_right = p.get("rocking_lr_indices", [11, 13])
                rows.extend(_rocking_lr_rows(params, left_range, right_range, int(i_left), int(i_right), bool(p.get("flickering", False))))
            if rows:
                current_x = rows[-1]["x"]
                current_y = rows[-1]["y"]

        elif kind == "waypoint_move":
            target_x = float(p.get("x_cm", current_x))
            target_y = float(p.get("y_cm", current_y))
            duration = float(p.get("duration_sec", 1.0))
            frames = max(1, int(round(duration * params.framerate)))
            for i in range(frames):
                frac = (i + 1) / frames
                x = current_x + (target_x - current_x) * frac
                y = current_y + (target_y - current_y) * frac
                _append_rows(rows, x, y, params.dot_size_cm, 1)
            current_x, current_y = target_x, target_y

        elif kind == "point_path":
            point_rows = _point_path_rows(p, params)
            rows.extend(point_rows)
            if point_rows:
                current_x = point_rows[-1]["x"]
                current_y = point_rows[-1]["y"]

        else:
            raise ValueError(f"Unknown primitive kind: {kind}")

    return rows


def _sample_xy(angle_range: list[float], index_1b: int, params: GlobalStimulusParams) -> tuple[float, float, float]:
    xr, yr, _, total_time = _arc_samples(angle_range, params, False)
    idx = max(0, min(len(xr) - 1, int(index_1b) - 1))
    return float(xr[idx]), float(yr[idx]), float(total_time)


def _rocking_rows(params: GlobalStimulusParams, angle_range: list[float], i1: int, i2: int, flickering: bool) -> list[dict[str, float]]:
    x1, y1, total_time = _sample_xy(angle_range, i1, params)
    x2, y2, _ = _sample_xy(angle_range, i2, params)
    rows: list[dict[str, float]] = []
    _append_rows(rows, x2, y2, params.dot_size_cm, round(params.static_period_sec * params.framerate))
    _append_rocking_motion(rows, x1, y1, x2, y2, total_time, params)
    if flickering:
        radii = [row["radius"] for row in rows]
        _apply_flicker(radii, round(params.static_period_sec * params.framerate), params)
        for row, radius in zip(rows, radii):
            row["radius"] = radius
    return rows


def _rocking_lr_rows(params: GlobalStimulusParams, left_range: list[float], right_range: list[float], i_left: int, i_right: int, flickering: bool) -> list[dict[str, float]]:
    x_left, y_left, t_left = _sample_xy(left_range, i_left, params)
    x_right, y_right, t_right = _sample_xy(right_range, i_right, params)
    rows: list[dict[str, float]] = []
    _append_rows(rows, x_right, y_right, params.dot_size_cm, round(params.static_period_sec * params.framerate))
    _append_rocking_motion(rows, x_left, y_left, x_right, y_right, min(t_left, t_right), params)
    if flickering:
        radii = [row["radius"] for row in rows]
        _apply_flicker(radii, round(params.static_period_sec * params.framerate), params)
        for row, radius in zip(rows, radii):
            row["radius"] = radius
    return rows


def _append_rocking_motion(rows: list[dict[str, float]], x1: float, y1: float, x2: float, y2: float, duration: float, params: GlobalStimulusParams) -> None:
    total_frames = int(round(duration * params.framerate))
    frames_per_update = max(1, int(round((params.update_interval_ms / 1000.0) * params.framerate)))
    filled = 0
    toggle = False
    while filled < total_frames:
        block = min(frames_per_update, total_frames - filled)
        toggle = not toggle
        x, y = (x1, y1) if toggle else (x2, y2)
        _append_rows(rows, x, y, params.dot_size_cm, block)
        filled += block


def generate_stimulus_dataframe(spec: StimulusSpec, params: GlobalStimulusParams | None = None) -> pd.DataFrame:
    params = params or GlobalStimulusParams()
    per_dot = [_generate_dot_rows(spec, i, params) for i in range(spec.n_dots)]
    dot_count = max(1, int(spec.n_dots))
    if not per_dot or not any(per_dot):
        return pd.DataFrame(
            {
                column: pd.Series(dtype=float)
                for dot_index in range(dot_count)
                for column in (f"dot{dot_index}_x", f"dot{dot_index}_y", f"dot{dot_index}_radius")
            }
        )
    max_len = max(len(rows) for rows in per_dot)
    data: dict[str, list[float]] = {}
    for dot_index, rows in enumerate(per_dot):
        if len(rows) < max_len:
            rows = rows + [rows[-1]] * (max_len - len(rows))
        data[f"dot{dot_index}_x"] = [row["x"] for row in rows]
        data[f"dot{dot_index}_y"] = [row["y"] for row in rows]
        data[f"dot{dot_index}_radius"] = [row["radius"] for row in rows]
    return pd.DataFrame(data)


def export_project(project: StimulusProject, output_dir: str | Path) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    params_dir = output_path / "parameters"
    params_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    metadata: list[dict[str, Any]] = []
    total_time_sec = 0.0
    for spec in project.stimuli:
        df = generate_stimulus_dataframe(spec, project.global_params)
        if df.empty:
            raise ValueError(f"Stimulus {spec.key} has no primitives to export.")
        csv_path = output_path / f"{spec.key}_trajectory.csv"
        df.to_csv(csv_path, index=False)
        written.append(csv_path)
        duration = len(df) / float(project.global_params.framerate)
        total_time_sec += duration + project.global_params.pause_before_sec + project.global_params.pause_after_sec
        metadata.append(
            {
                "stimulus_key": spec.key,
                "name": spec.name,
                "n_dots": spec.n_dots,
                "total_frames": len(df),
                "total_sec": duration,
                **asdict(project.global_params),
            }
        )

    pd.DataFrame(metadata).to_csv(params_dir / "experiment_parameters.csv", index=False)
    pd.DataFrame(
        [{"total_experiment_duration_sec": total_time_sec * int(project.global_params.repetitions)}]
    ).to_csv(params_dir / "total_time_sec.csv", index=False)
    save_project(project, params_dir / "stimulus_designer_project.json")
    return written


def mirror_stimulus_in_place(spec: StimulusSpec, params: GlobalStimulusParams | None = None) -> None:
    params = params or GlobalStimulusParams()
    for primitive in spec.primitives:
        p = primitive.params
        for key in ("angle_deg",):
            if key in p:
                p[key] = -float(p[key])
        for key in ("angle_range", "left_angle_range", "right_angle_range"):
            if key in p:
                p[key] = [-float(angle) for angle in p[key]]
        if primitive.kind == "rocking_lr":
            left = p.get("left_angle_range")
            right = p.get("right_angle_range")
            p["left_angle_range"] = right
            p["right_angle_range"] = left
        if primitive.kind == "waypoint_move" and "x_cm" in p:
            p["x_cm"] = -float(p["x_cm"])
        if primitive.kind == "point_path":
            mirrored_points = []
            for point in p.get("points", []):
                mirrored = dict(point)
                if "angle_deg" in mirrored:
                    mirrored["angle_deg"] = -float(mirrored["angle_deg"])
                    if "points_per_ring" in mirrored:
                        points_per_ring = max(1, int(mirrored["points_per_ring"]))
                        mirrored["point_index"] = int(round(((float(mirrored["angle_deg"]) + 180.0) / 360.0) * points_per_ring)) % points_per_ring
                if "radius_cm" in mirrored and "angle_deg" in mirrored:
                    x_cm, y_cm = grid_point_to_position(float(mirrored["radius_cm"]), float(mirrored["angle_deg"]), params)
                    mirrored["x_cm"] = x_cm
                    mirrored["y_cm"] = y_cm
                elif "x_cm" in mirrored:
                    mirrored["x_cm"] = -float(mirrored["x_cm"])
                mirrored_points.append(mirrored)
            p["points"] = mirrored_points


def launch_psychopy_projection(stimuli_dir: str | Path, script_path: str | Path | None = None) -> subprocess.Popen:
    script = Path(script_path) if script_path else Path(__file__).resolve().parents[1] / "scripts" / "stimuli" / "try_projection.py"
    return subprocess.Popen([sys.executable, str(script), "--stimuli-path", str(stimuli_dir)])
