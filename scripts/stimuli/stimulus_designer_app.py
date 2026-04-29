from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except ImportError as exc:
    raise SystemExit(
        "PyQt6 is required for the stimulus designer GUI. "
        "Activate the social_filters Conda environment or install PyQt6."
    ) from exc

from src.stimulus_designer import (
    Calibration,
    GlobalStimulusParams,
    Primitive,
    StimulusProject,
    StimulusSpec,
    default_project,
    export_project,
    generate_stimulus_dataframe,
    import_legacy_config,
    launch_psychopy_projection,
    load_project,
    make_grid_point,
    mirror_stimulus_in_place,
    primitive_duration_summary,
    project_to_dict,
    save_project,
)


class PreviewCanvas(QtWidgets.QWidget):
    frame_changed = QtCore.pyqtSignal(int)
    grid_point_clicked = QtCore.pyqtSignal(int, int)
    MIN_PREVIEW_ZOOM = 1.0
    MAX_PREVIEW_ZOOM = 8.0
    PREVIEW_ZOOM_STEP = 1.15

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 520)
        self.project = default_project()
        self.stimulus = self.project.stimuli[0]
        self.frame_index = 0
        self.df = generate_stimulus_dataframe(self.stimulus, self.project.global_params)
        self.hovered_grid_point: tuple[int, int] | None = None
        self.preview_zoom = 1.0
        self.view_center_cm = QtCore.QPointF(0.0, 0.0)
        self.is_panning = False
        self._last_pan_pos: QtCore.QPointF | None = None
        self.setMouseTracking(True)

    def set_stimulus(self, project: StimulusProject, stimulus: StimulusSpec) -> None:
        self.project = project
        self.stimulus = stimulus
        self.df = generate_stimulus_dataframe(stimulus, project.global_params)
        self.frame_index = min(self.frame_index, max(0, len(self.df) - 1))
        self.update()

    def set_frame(self, frame_index: int) -> None:
        self.frame_index = max(0, min(frame_index, max(0, len(self.df) - 1)))
        self.update()

    def _screen_size_cm(self) -> tuple[float, float]:
        return (
            max(0.1, self.project.calibration.screen_width_mm / 10.0),
            max(0.1, self.project.calibration.screen_height_mm / 10.0),
        )

    def _base_scale(self) -> float:
        screen_width_cm, screen_height_cm = self._screen_size_cm()
        margin = 0.9
        return min(
            self.width() / (screen_width_cm + margin),
            self.height() / (screen_height_cm + margin),
        )

    def _scale(self) -> float:
        return self._base_scale() * self.preview_zoom

    def _to_widget(self, x_cm: float, y_cm: float) -> QtCore.QPointF:
        scale = self._scale()
        return QtCore.QPointF(
            self.width() / 2.0 + (x_cm - self.view_center_cm.x()) * scale,
            self.height() / 2.0 - (y_cm - self.view_center_cm.y()) * scale,
        )

    def _widget_to_cm(self, position: QtCore.QPointF) -> QtCore.QPointF:
        scale = self._scale()
        return QtCore.QPointF(
            self.view_center_cm.x() + (position.x() - self.width() / 2.0) / scale,
            self.view_center_cm.y() - (position.y() - self.height() / 2.0) / scale,
        )

    def _screen_rect(self) -> QtCore.QRectF:
        screen_width_cm, screen_height_cm = self._screen_size_cm()
        top_left = self._to_widget(-screen_width_cm / 2.0, screen_height_cm / 2.0)
        bottom_right = self._to_widget(screen_width_cm / 2.0, -screen_height_cm / 2.0)
        return QtCore.QRectF(top_left, bottom_right).normalized()

    def _clamp_preview_zoom(self, zoom: float) -> float:
        return max(self.MIN_PREVIEW_ZOOM, min(self.MAX_PREVIEW_ZOOM, zoom))

    def _clamp_view_center(self, center: QtCore.QPointF | None = None) -> QtCore.QPointF:
        center = center or self.view_center_cm
        screen_width_cm, screen_height_cm = self._screen_size_cm()
        scale = self._scale()
        viewport_width_cm = self.width() / scale
        viewport_height_cm = self.height() / scale

        def clamp_axis(value: float, screen_cm: float, viewport_cm: float) -> float:
            if viewport_cm >= screen_cm:
                return 0.0
            limit = (screen_cm - viewport_cm) / 2.0
            return max(-limit, min(limit, value))

        return QtCore.QPointF(
            clamp_axis(center.x(), screen_width_cm, viewport_width_cm),
            clamp_axis(center.y(), screen_height_cm, viewport_height_cm),
        )

    def _set_preview_zoom(self, zoom: float, anchor: QtCore.QPointF | None = None) -> None:
        anchor = anchor or QtCore.QPointF(self.width() / 2.0, self.height() / 2.0)
        before_cm = self._widget_to_cm(anchor)
        self.preview_zoom = self._clamp_preview_zoom(zoom)
        if self.preview_zoom == self.MIN_PREVIEW_ZOOM:
            self.view_center_cm = QtCore.QPointF(0.0, 0.0)
        else:
            scale = self._scale()
            self.view_center_cm = self._clamp_view_center(
                QtCore.QPointF(
                    before_cm.x() - (anchor.x() - self.width() / 2.0) / scale,
                    before_cm.y() + (anchor.y() - self.height() / 2.0) / scale,
                )
            )
        self.update()

    def _pan_by_pixels(self, delta_px: QtCore.QPointF) -> None:
        scale = self._scale()
        self.view_center_cm = self._clamp_view_center(
            QtCore.QPointF(
                self.view_center_cm.x() - delta_px.x() / scale,
                self.view_center_cm.y() + delta_px.y() / scale,
            )
        )
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        steps = delta / 120.0
        self._set_preview_zoom(self.preview_zoom * (self.PREVIEW_ZOOM_STEP ** steps), event.position())
        event.accept()

    def resizeEvent(self, event):
        self.view_center_cm = self._clamp_view_center()
        super().resizeEvent(event)

    def _angle_endpoint(self, angle_deg: float, radius_cm: float) -> QtCore.QPointF:
        theta = math.radians(self.project.global_params.rotation_angle_deg)
        angle = math.radians(angle_deg)
        x = radius_cm * math.sin(angle)
        y = radius_cm * math.cos(angle)
        xr = x * math.cos(theta) - y * math.sin(theta)
        yr = x * math.sin(theta) + y * math.cos(theta)
        return self._to_widget(xr, yr)

    def _visual_field_polygon(self, start_deg: float, end_deg: float, steps: int = 32) -> QtGui.QPolygonF:
        screen_width_cm, screen_height_cm = self._screen_size_cm()
        radius_cm = math.hypot(screen_width_cm, screen_height_cm)
        center = self._to_widget(0.0, 0.0)
        points = [center]
        if end_deg < start_deg:
            end_deg += 360.0
        for index in range(steps + 1):
            angle = start_deg + (end_deg - start_deg) * index / steps
            if angle > 180.0:
                angle -= 360.0
            points.append(self._angle_endpoint(angle, radius_cm))
        return QtGui.QPolygonF(points)

    def _selected_grid_points(self) -> list[tuple[int, int]]:
        selected: list[tuple[int, int]] = []
        for primitive in self.stimulus.primitives:
            if primitive.kind in {"static_hold", "flicker", "loom"}:
                points = [primitive.params.get("point")]
            elif primitive.kind in {"rocking", "rocking_lr", "point_path", "whole_field_grating", "linear"}:
                points = primitive.params.get("points", [])
            else:
                continue
            for point in points:
                if not isinstance(point, dict):
                    continue
                if "ring_index" in point and "point_index" in point:
                    selected.append((int(point["ring_index"]), int(point["point_index"])))
        return selected

    def _grid_point_positions(self) -> list[tuple[int, int, QtCore.QPointF]]:
        grid = self.project.grid_settings
        positions = []
        for ring_index in range(max(0, int(grid.ring_count))):
            for point_index in range(max(1, int(grid.points_per_ring))):
                point = make_grid_point(ring_index, point_index, grid, self.project.global_params)
                positions.append((ring_index, point_index, self._to_widget(float(point["x_cm"]), float(point["y_cm"]))))
        return positions

    def _nearest_grid_point(self, position: QtCore.QPointF) -> tuple[int, int] | None:
        closest: tuple[int, int] | None = None
        closest_dist = 10.0
        for ring_index, point_index, point_pos in self._grid_point_positions():
            dist = ((point_pos.x() - position.x()) ** 2 + (point_pos.y() - position.y()) ** 2) ** 0.5
            if dist <= closest_dist:
                closest = (ring_index, point_index)
                closest_dist = dist
        return closest

    def mouseMoveEvent(self, event):
        if self.is_panning and self._last_pan_pos is not None:
            pos = event.position()
            self._pan_by_pixels(pos - self._last_pan_pos)
            self._last_pan_pos = pos
            event.accept()
            return
        point = self._nearest_grid_point(event.position())
        if point != self.hovered_grid_point:
            self.hovered_grid_point = point
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hovered_grid_point = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.is_panning = True
            self._last_pan_pos = event.position()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            point = self._nearest_grid_point(event.position())
            if point is not None:
                self.grid_point_clicked.emit(point[0], point[1])
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton and self.is_panning:
            self.is_panning = False
            self._last_pan_pos = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#f7f7f4"))

        center = self._to_widget(0.0, 0.0)
        scale = self._scale()
        screen_rect = self._screen_rect()

        outer_brush = QtGui.QColor("#ecece6")
        painter.fillRect(self.rect(), outer_brush)
        painter.fillRect(screen_rect, QtGui.QColor("#f7f7f4"))
        painter.save()
        painter.setClipRect(screen_rect)
        self._draw_visual_field_guides(painter)

        grid_pen = QtGui.QPen(QtGui.QColor("#d6d6d0"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        screen_width_cm, screen_height_cm = self._screen_size_cm()
        x_min = -screen_width_cm / 2.0
        x_max = screen_width_cm / 2.0
        y_min = -screen_height_cm / 2.0
        y_max = screen_height_cm / 2.0
        for i in range(math.floor(x_min * 2), math.ceil(x_max * 2) + 1):
            cm = i * 0.5
            p1 = self._to_widget(cm, y_min)
            p2 = self._to_widget(cm, y_max)
            painter.drawLine(p1, p2)
        for i in range(math.floor(y_min * 2), math.ceil(y_max * 2) + 1):
            cm = i * 0.5
            p3 = self._to_widget(x_min, cm)
            p4 = self._to_widget(x_max, cm)
            painter.drawLine(p3, p4)

        axis_pen = QtGui.QPen(QtGui.QColor("#8a8a84"))
        axis_pen.setWidth(2)
        painter.setPen(axis_pen)
        painter.drawLine(QtCore.QPointF(screen_rect.left(), center.y()), QtCore.QPointF(screen_rect.right(), center.y()))
        painter.drawLine(QtCore.QPointF(center.x(), screen_rect.top()), QtCore.QPointF(center.x(), screen_rect.bottom()))

        row = None
        if not self.df.empty:
            row = self.df.iloc[self.frame_index]
            self._draw_grating_preview(painter, row)

        fish_pen = QtGui.QPen(QtGui.QColor("#1b1b1b"))
        fish_pen.setWidth(2)
        painter.setPen(fish_pen)
        painter.setBrush(QtGui.QColor("#d9efe7"))
        self._draw_fish_icon(painter, center)

        selected_points = self._selected_grid_points()
        selected_lookup = set(selected_points)
        grid = self.project.grid_settings
        ring_pen = QtGui.QPen(QtGui.QColor("#b9c3bd"))
        ring_pen.setWidth(1)
        painter.setPen(ring_pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        for ring_index in range(max(0, int(grid.ring_count))):
            radius_cm = float(grid.first_ring_radius_cm) + ring_index * float(grid.ring_spacing_cm)
            painter.drawEllipse(center, radius_cm * scale, radius_cm * scale)
        for ring_index, point_index, pos in self._grid_point_positions():
            is_hovered = self.hovered_grid_point == (ring_index, point_index)
            is_selected = (ring_index, point_index) in selected_lookup
            if is_selected:
                order = selected_points.index((ring_index, point_index))
                if order == 0:
                    color = QtGui.QColor("#1b8f5a")
                elif order == len(selected_points) - 1:
                    color = QtGui.QColor("#c94f3d")
                else:
                    color = QtGui.QColor("#2f6fbb")
                color.setAlphaF(0.4)
            elif is_hovered:
                color = QtGui.QColor("#d7a31f")
            else:
                color = QtGui.QColor("#ffffff")
            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor("#4c4c48")))
            radius_px = 5 if is_hovered or is_selected else 3
            painter.drawEllipse(pos, radius_px, radius_px)

        painter.setPen(QtGui.QPen(QtGui.QColor("#303030")))
        if self.df.empty:
            painter.drawText(12, 22, "No frames")
        else:
            path_pen = QtGui.QPen(QtGui.QColor("#3f7f99"))
            path_pen.setWidth(2)
            painter.setPen(path_pen)
            for dot in self._dot_names():
                points = [
                    self._to_widget(float(frame_row[f"{dot}_x"]), float(frame_row[f"{dot}_y"]))
                    for _, frame_row in self.df.iloc[:: max(1, len(self.df) // 250)].iterrows()
                ]
                for a, b in zip(points[:-1], points[1:]):
                    painter.drawLine(a, b)

            self._draw_loom_preview(painter, row, scale)

            dot_color = self._stimulus_dot_color()
            painter.setBrush(dot_color)
            painter.setPen(QtGui.QPen(dot_color))
            for dot in self._dot_names():
                radius = float(row.get(f"{dot}_radius", self.project.global_params.dot_size_cm))
                if radius <= 0:
                    continue
                pos = self._to_widget(float(row[f"{dot}_x"]), float(row[f"{dot}_y"]))
                painter.drawEllipse(pos, max(2.0, radius * scale), max(2.0, radius * scale))

            painter.setPen(QtGui.QPen(QtGui.QColor("#303030")))
            painter.drawText(12, 22, f"Frame {self.frame_index + 1}/{len(self.df)}")
        painter.drawText(12, 42, "Fish center: 0 mm, 0 mm")
        painter.restore()
        boundary_pen = QtGui.QPen(QtGui.QColor("#303030"))
        boundary_pen.setWidth(2)
        painter.setPen(boundary_pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawRect(screen_rect)

    def _draw_visual_field_guides(self, painter: QtGui.QPainter) -> None:
        binocular = QtGui.QColor("#6abf8a")
        binocular.setAlpha(48)
        blind = QtGui.QColor("#d07777")
        blind.setAlpha(48)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(binocular)
        painter.drawPolygon(self._visual_field_polygon(-30.0, 30.0))
        painter.setBrush(blind)
        painter.drawPolygon(self._visual_field_polygon(160.0, 200.0))

        guide_pen = QtGui.QPen(QtGui.QColor("#6b6b64"))
        guide_pen.setWidth(1)
        guide_pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        painter.setPen(guide_pen)
        screen_width_cm, screen_height_cm = self._screen_size_cm()
        radius_cm = math.hypot(screen_width_cm, screen_height_cm)
        center = self._to_widget(0.0, 0.0)
        for angle in (-30.0, 30.0, -160.0, 160.0):
            painter.drawLine(center, self._angle_endpoint(angle, radius_cm))

    def _dot_names(self) -> list[str]:
        return sorted({col.rsplit("_", 1)[0] for col in self.df.columns if col.startswith("dot") and col.endswith("_x")})

    def _stimulus_dot_color(self) -> QtGui.QColor:
        color = QtGui.QColor("#111111")
        color.setAlphaF(0.4)
        return color

    def _draw_fish_icon(self, painter: QtGui.QPainter, center: QtCore.QPointF) -> None:
        painter.save()
        painter.translate(center)
        painter.rotate(-45)
        painter.drawEllipse(QtCore.QPointF(0, 0), 12, 26)
        tail = QtGui.QPolygonF(
            [
                QtCore.QPointF(0, 28),
                QtCore.QPointF(-10, 42),
                QtCore.QPointF(10, 42),
            ]
        )
        painter.drawPolygon(tail)
        painter.setBrush(QtGui.QColor("#1b1b1b"))
        painter.drawEllipse(QtCore.QPointF(-5, -18), 2.2, 2.2)
        painter.drawEllipse(QtCore.QPointF(5, -18), 2.2, 2.2)
        painter.restore()

    def _draw_grating_preview(self, painter: QtGui.QPainter, row) -> None:
        if float(row.get("grating_active", 0.0)) <= 0:
            return
        direction = float(row.get("grating_direction_deg", 0.0))
        thickness_cm = max(0.05, float(row.get("grating_bar_thickness_cm", 0.5)))
        phase_cm = float(row.get("grating_phase_cm", 0.0))
        scale = self._scale()
        spacing_px = thickness_cm * scale * 2.0
        black_width_px = max(1.0, thickness_cm * scale)
        angle = -direction
        painter.save()
        painter.setClipRect(self._screen_rect())
        painter.translate(self.width() / 2.0, self.height() / 2.0)
        painter.rotate(angle)
        painter.fillRect(
            QtCore.QRectF(-self.width(), -self.height(), self.width() * 2.0, self.height() * 2.0),
            QtGui.QColor("#ffffff"),
        )
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor("#111111"))
        offset = (phase_cm * scale) % spacing_px
        start = -self.width() - self.height() - spacing_px
        end = self.width() + self.height() + spacing_px
        pos = start + offset
        while pos < end:
            painter.drawRect(QtCore.QRectF(pos, -end, black_width_px, end * 2.0))
            pos += spacing_px
        painter.restore()

        points = self._selected_grating_points()
        if len(points) >= 2:
            p0 = self._to_widget(float(points[0]["x_cm"]), float(points[0]["y_cm"]))
            p1 = self._to_widget(float(points[1]["x_cm"]), float(points[1]["y_cm"]))
            arrow_pen = QtGui.QPen(QtGui.QColor("#c94f3d"))
            arrow_pen.setWidth(3)
            painter.setPen(arrow_pen)
            painter.drawLine(p0, p1)

    def _selected_grating_points(self) -> list[dict]:
        for primitive in self.stimulus.primitives:
            if primitive.kind == "whole_field_grating":
                return [point for point in primitive.params.get("points", []) if isinstance(point, dict)]
        return []

    def _draw_loom_preview(self, painter: QtGui.QPainter, row, scale: float) -> None:
        if float(row.get("loom_active", 0.0)) <= 0:
            return
        radius = float(row.get("loom_radius", 0.0))
        if radius <= 0:
            return
        pos = self._to_widget(float(row.get("loom_x", 0.0)), float(row.get("loom_y", 0.0)))
        painter.setBrush(QtGui.QColor("#111111"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#111111")))
        painter.drawEllipse(pos, radius * scale, radius * scale)


class ScaledWidgetView(QtWidgets.QGraphicsView):
    def __init__(self, content: QtWidgets.QWidget, design_size: QtCore.QSize, parent=None):
        super().__init__(parent)
        self._design_size = design_size
        self._zoom = 1.0
        self._scene = QtWidgets.QGraphicsScene(self)
        self._proxy = self._scene.addWidget(content)
        self._proxy.setPos(0, 0)
        self.setScene(self._scene)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setMinimumSize(1, 1)
        self._scene.setSceneRect(QtCore.QRectF(QtCore.QPointF(0, 0), QtCore.QSizeF(design_size)))

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_zoom(self, zoom: float) -> None:
        self._zoom = zoom
        self.resetTransform()
        self.scale(zoom, zoom)


class StimulusDesignerWindow(QtWidgets.QMainWindow):
    DESIGN_SIZE = QtCore.QSize(1280, 760)
    MIN_ZOOM = 0.55
    MAX_ZOOM = 1.50
    ZOOM_STEP = 0.10

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stimulus Designer")
        self.project = default_project()
        self.current_output_dir: Path | None = None
        self.zoom_factor = 1.0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._advance_frame)
        self._build_ui()
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._install_zoom_shortcuts()
        self._refresh_all()
        self._apply_startup_zoom()

    def _register_description(self, widget: QtCore.QObject, description: str) -> None:
        widget.setProperty("description_text", description)
        if isinstance(widget, QtWidgets.QWidget):
            widget.setToolTip(description)

    def _build_ui(self):
        central = QtWidgets.QWidget()
        central.setFixedSize(self.DESIGN_SIZE)
        layout = QtWidgets.QHBoxLayout(central)
        self.scaled_view = ScaledWidgetView(central, self.DESIGN_SIZE, self)
        self.setCentralWidget(self.scaled_view)

        left = QtWidgets.QVBoxLayout()
        self.stimulus_list = QtWidgets.QListWidget()
        self.stimulus_list.currentRowChanged.connect(self._on_stimulus_selected)
        left.addWidget(QtWidgets.QLabel("Stimuli"))
        left.addWidget(self.stimulus_list)

        add_btn = QtWidgets.QPushButton("Add")
        add_btn.clicked.connect(self._add_stimulus)
        dup_btn = QtWidgets.QPushButton("Duplicate")
        dup_btn.clicked.connect(self._duplicate_stimulus)
        del_btn = QtWidgets.QPushButton("Delete")
        del_btn.clicked.connect(self._delete_stimulus)
        mirror_btn = QtWidgets.QPushButton("Mirror")
        mirror_btn.clicked.connect(self._mirror_stimulus)
        for btn, description in [
            (add_btn, "Add a new stimulus to the project."),
            (dup_btn, "Duplicate the selected stimulus, including its primitives."),
            (del_btn, "Delete the selected stimulus. At least one stimulus remains."),
            (mirror_btn, "Mirror the selected stimulus in place to the opposite side of the fish."),
        ]:
            self._register_description(btn, description)
        left_buttons = QtWidgets.QHBoxLayout()
        left_buttons.addWidget(add_btn)
        left_buttons.addWidget(dup_btn)
        left_buttons.addWidget(del_btn)
        left_buttons.addWidget(mirror_btn)
        left.addLayout(left_buttons)
        layout.addLayout(left, 1)

        middle = QtWidgets.QVBoxLayout()
        self.canvas = PreviewCanvas()
        self.canvas.grid_point_clicked.connect(self._toggle_grid_point)
        self._register_description(
            self.canvas,
            "Click grid points to build a custom path. Hover highlights the target point; clicking an existing path point removes it. Scroll to zoom around the cursor; right-drag to pan while zoomed.",
        )
        middle.addWidget(self.canvas, 1)
        self.frame_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.frame_slider.valueChanged.connect(self.canvas.set_frame)
        middle.addWidget(self.frame_slider)
        preview_buttons = QtWidgets.QHBoxLayout()
        play_btn = QtWidgets.QPushButton("Play")
        play_btn.clicked.connect(lambda: self.timer.start(max(1, int(1000 / self.project.global_params.framerate))))
        pause_btn = QtWidgets.QPushButton("Pause")
        pause_btn.clicked.connect(self.timer.stop)
        self._register_description(play_btn, "Play the generated preview for the selected stimulus.")
        self._register_description(pause_btn, "Pause the preview playback.")
        preview_buttons.addWidget(play_btn)
        preview_buttons.addWidget(pause_btn)
        middle.addLayout(preview_buttons)
        layout.addLayout(middle, 3)

        self.right_scroll = QtWidgets.QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.right_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_panel = QtWidgets.QWidget()
        self.right_scroll.setWidget(self.right_panel)
        right = QtWidgets.QVBoxLayout(self.right_panel)
        form = QtWidgets.QFormLayout()
        self.key_edit = QtWidgets.QLineEdit()
        self.key_edit.editingFinished.connect(self._apply_fields)
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.editingFinished.connect(self._apply_fields)
        self.n_dots_spin = QtWidgets.QSpinBox()
        self.n_dots_spin.setRange(1, 8)
        self.n_dots_spin.valueChanged.connect(self._apply_fields)
        self._register_description(self.key_edit, "Trajectory CSVs use this key as the stimulus file prefix.")
        self._register_description(self.name_edit, "Human-readable stimulus name saved in project metadata.")
        self._register_description(self.n_dots_spin, "Number of dot columns generated for this stimulus.")
        form.addRow("Key", self.key_edit)
        form.addRow("Name", self.name_edit)
        form.addRow("Dots", self.n_dots_spin)
        right.addLayout(form)

        self.timeline_label = QtWidgets.QLabel("Timeline primitives")
        self.primitive_list = QtWidgets.QListWidget()
        self.primitive_list.currentRowChanged.connect(self._load_primitive_editor)
        right.addWidget(self.timeline_label)
        right.addWidget(self.primitive_list)
        primitive_buttons = QtWidgets.QHBoxLayout()
        self.kind_combo = QtWidgets.QComboBox()
        self.kind_combo.addItems(["static_hold", "flicker", "rocking", "rocking_lr", "point_path", "linear", "whole_field_grating", "loom"])
        add_prim_btn = QtWidgets.QPushButton("Add")
        add_prim_btn.clicked.connect(self._add_primitive)
        del_prim_btn = QtWidgets.QPushButton("Delete")
        del_prim_btn.clicked.connect(self._delete_primitive)
        self._register_description(self.kind_combo, "Choose the primitive type to add to the selected stimulus.")
        self._register_description(add_prim_btn, "Append a timeline primitive to the selected stimulus.")
        self._register_description(del_prim_btn, "Delete the selected timeline primitive.")
        primitive_buttons.addWidget(self.kind_combo)
        primitive_buttons.addWidget(add_prim_btn)
        primitive_buttons.addWidget(del_prim_btn)
        right.addLayout(primitive_buttons)

        self.primitive_json = QtWidgets.QPlainTextEdit()
        self.primitive_json.setMaximumHeight(160)
        apply_primitive_btn = QtWidgets.QPushButton("Apply Primitive JSON")
        apply_primitive_btn.clicked.connect(self._apply_primitive_json)
        self._register_description(self.primitive_json, "Edit the selected primitive as JSON when precise values are needed.")
        self._register_description(apply_primitive_btn, "Apply the primitive JSON editor contents to the selected primitive.")
        right.addWidget(self.primitive_json)
        right.addWidget(apply_primitive_btn)

        self.stimulus_params_group = QtWidgets.QGroupBox("Stimulus parameters")
        stimulus_params_form = QtWidgets.QFormLayout(self.stimulus_params_group)
        self.duration_spin = QtWidgets.QDoubleSpinBox()
        self.duration_spin.setRange(0.001, 10000)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setDecimals(3)
        self.primitive_interval_spin = QtWidgets.QDoubleSpinBox()
        self.primitive_interval_spin.setRange(1, 10000)
        self.primitive_interval_spin.setSuffix(" ms")
        self.primitive_interval_spin.setDecimals(1)
        self.primitive_mode_combo = QtWidgets.QComboBox()
        self.primitive_mode_combo.addItems(["bout", "continuous"])
        self.flicker_interval_spin = QtWidgets.QDoubleSpinBox()
        self.flicker_interval_spin.setRange(0.001, 1000)
        self.flicker_interval_spin.setSuffix(" s")
        self.flicker_interval_spin.setDecimals(3)
        self.flickering_check = QtWidgets.QCheckBox()
        self.bar_thickness_spin = QtWidgets.QDoubleSpinBox()
        self.bar_thickness_spin.setRange(0.01, 100)
        self.bar_thickness_spin.setSuffix(" cm")
        self.bar_thickness_spin.setDecimals(3)
        self.speed_spin = QtWidgets.QDoubleSpinBox()
        self.speed_spin.setRange(0.001, 1000)
        self.speed_spin.setSuffix(" cm/s")
        self.speed_spin.setDecimals(3)
        self.growth_speed_spin = QtWidgets.QDoubleSpinBox()
        self.growth_speed_spin.setRange(0.001, 1000)
        self.growth_speed_spin.setSuffix(" cm/s")
        self.growth_speed_spin.setDecimals(3)
        self.max_radius_spin = QtWidgets.QDoubleSpinBox()
        self.max_radius_spin.setRange(0.001, 1000)
        self.max_radius_spin.setSuffix(" cm")
        self.max_radius_spin.setDecimals(3)
        self.step_distance_spin = QtWidgets.QDoubleSpinBox()
        self.step_distance_spin.setRange(0.001, 1000)
        self.step_distance_spin.setSuffix(" cm")
        self.step_distance_spin.setDecimals(3)
        self._stimulus_param_rows = []
        for label_text, widget in [
            ("Duration", self.duration_spin),
            ("Interval", self.primitive_interval_spin),
            ("Mode", self.primitive_mode_combo),
            ("Flicker interval", self.flicker_interval_spin),
            ("Flickering", self.flickering_check),
            ("Bar thickness", self.bar_thickness_spin),
            ("Speed", self.speed_spin),
            ("Growth speed", self.growth_speed_spin),
            ("Max radius", self.max_radius_spin),
            ("Step distance", self.step_distance_spin),
        ]:
            label = QtWidgets.QLabel(label_text)
            stimulus_params_form.addRow(label, widget)
            self._stimulus_param_rows.append((label_text, label, widget))
        for widget in [
            self.duration_spin,
            self.primitive_interval_spin,
            self.flicker_interval_spin,
            self.bar_thickness_spin,
            self.speed_spin,
            self.growth_speed_spin,
            self.max_radius_spin,
            self.step_distance_spin,
        ]:
            widget.valueChanged.connect(self._apply_stimulus_parameter_fields)
        self.primitive_mode_combo.currentTextChanged.connect(self._apply_stimulus_parameter_fields)
        self.flickering_check.stateChanged.connect(self._apply_stimulus_parameter_fields)
        self._register_description(self.duration_spin, "Duration for the selected primitive.")
        self._register_description(self.primitive_interval_spin, "Time between point changes for the selected primitive.")
        self._register_description(self.primitive_mode_combo, "Bout jumps point-to-point; continuous interpolates between points.")
        self._register_description(self.flicker_interval_spin, "Flicker on/off interval for the selected primitive.")
        self._register_description(self.flickering_check, "Apply flickering while the selected primitive is active.")
        self._register_description(self.bar_thickness_spin, "Black and white bar thickness for whole-field gratings.")
        self._register_description(self.speed_spin, "Whole-field grating motion speed.")
        self._register_description(self.growth_speed_spin, "Loom radius growth speed.")
        self._register_description(self.max_radius_spin, "Maximum loom radius; the loom holds here until duration ends.")
        self._register_description(self.step_distance_spin, "Distance moved along the linear path at each interval.")
        self.stimulus_params_group.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        right.addWidget(self.stimulus_params_group)

        self.params_group = QtWidgets.QGroupBox("Global / calibration")
        params_form = QtWidgets.QFormLayout(self.params_group)
        self.framerate_spin = QtWidgets.QDoubleSpinBox()
        self.framerate_spin.setRange(1, 240)
        self.framerate_spin.setValue(60)
        self.radius_spin = QtWidgets.QDoubleSpinBox()
        self.radius_spin.setRange(0.1, 20)
        self.radius_spin.setValue(1.8)
        self.calibration_summary_label = QtWidgets.QLabel()
        self.calibration_summary_label.setWordWrap(True)
        self.calibration_summary_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        for widget in [self.framerate_spin, self.radius_spin]:
            widget.valueChanged.connect(self._apply_global_fields)
        self._register_description(self.framerate_spin, "Preview and export framerate in frames per second.")
        self._register_description(self.radius_spin, "Default arc radius used by angle-based primitives.")
        self._register_description(self.calibration_summary_label, "Read-only screen calibration used for preview and export metadata.")
        params_form.addRow("Framerate", self.framerate_spin)
        params_form.addRow("Arc radius cm", self.radius_spin)
        params_form.addRow("Screen", self.calibration_summary_label)
        self.params_group.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        self.params_group.setMinimumHeight(self.params_group.sizeHint().height())
        right.addWidget(self.params_group)

        self.grid_group = QtWidgets.QGroupBox("Point grid")
        grid_form = QtWidgets.QFormLayout(self.grid_group)
        self.grid_rings_spin = QtWidgets.QSpinBox()
        self.grid_rings_spin.setRange(1, 12)
        self.grid_first_radius_spin = QtWidgets.QDoubleSpinBox()
        self.grid_first_radius_spin.setRange(0.1, 20)
        self.grid_first_radius_spin.setSingleStep(0.1)
        self.grid_spacing_spin = QtWidgets.QDoubleSpinBox()
        self.grid_spacing_spin.setRange(0.1, 20)
        self.grid_spacing_spin.setSingleStep(0.1)
        self.grid_points_spin = QtWidgets.QSpinBox()
        self.grid_points_spin.setRange(4, 96)
        for widget in [
            self.grid_rings_spin,
            self.grid_first_radius_spin,
            self.grid_spacing_spin,
            self.grid_points_spin,
        ]:
            widget.valueChanged.connect(self._apply_grid_fields)
        self._register_description(self.grid_rings_spin, "Number of concentric placement rings around the fish.")
        self._register_description(self.grid_first_radius_spin, "Distance from fish center to the first placement ring in centimeters.")
        self._register_description(self.grid_spacing_spin, "Distance between neighboring placement rings in centimeters.")
        self._register_description(self.grid_points_spin, "Number of clickable positions on each ring.")
        grid_form.addRow("Rings", self.grid_rings_spin)
        grid_form.addRow("First ring cm", self.grid_first_radius_spin)
        grid_form.addRow("Ring spacing cm", self.grid_spacing_spin)
        grid_form.addRow("Points / ring", self.grid_points_spin)
        self.grid_group.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        self.grid_group.setMinimumHeight(self.grid_group.sizeHint().height())
        right.addWidget(self.grid_group)

        file_buttons = QtWidgets.QGridLayout()
        actions = [
            ("Open Project", self._open_project),
            ("Save Project", self._save_project),
            ("Import Legacy JSON", self._import_legacy),
            ("Export CSVs", self._export_csvs),
            ("Launch PsychoPy", self._launch_psychopy),
        ]
        for i, (label, callback) in enumerate(actions):
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(callback)
            descriptions = {
                "Open Project": "Load a saved stimulus designer project JSON.",
                "Save Project": "Save the editable project JSON.",
                "Import Legacy JSON": "Import an older stimulus JSON into the designer model.",
                "Export CSVs": "Write canonical trajectory CSVs and parameter metadata.",
                "Launch PsychoPy": "Start PsychoPy playback for an exported stimulus folder.",
            }
            self._register_description(btn, descriptions[label])
            file_buttons.addWidget(btn, i // 2, i % 2)
        right.addLayout(file_buttons)
        layout.addWidget(self.right_scroll, 2)

    def _install_zoom_shortcuts(self) -> None:
        shortcuts = [
            (QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.ZoomIn), self.zoom_in),
            (QtGui.QKeySequence("Ctrl++"), self.zoom_in),
            (QtGui.QKeySequence("Ctrl+="), self.zoom_in),
            (QtGui.QKeySequence("Meta++"), self.zoom_in),
            (QtGui.QKeySequence("Meta+="), self.zoom_in),
            (QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.ZoomOut), self.zoom_out),
            (QtGui.QKeySequence("Ctrl+-"), self.zoom_out),
            (QtGui.QKeySequence("Meta+-"), self.zoom_out),
            (QtGui.QKeySequence("Ctrl+_"), self.zoom_out),
            (QtGui.QKeySequence("Meta+_"), self.zoom_out),
            (QtGui.QKeySequence("Ctrl+0"), self.reset_zoom),
            (QtGui.QKeySequence("Meta+0"), self.reset_zoom),
        ]
        self.zoom_shortcuts = []
        for sequence, callback in shortcuts:
            shortcut = QtGui.QShortcut(sequence, self)
            shortcut.setContext(QtCore.Qt.ShortcutContext.ApplicationShortcut)
            shortcut.activated.connect(callback)
            self.zoom_shortcuts.append(shortcut)

    def eventFilter(self, watched, event):
        if (
            event.type() == QtCore.QEvent.Type.ShortcutOverride
            and self.isActiveWindow()
            and self._is_zoom_key_event(event)
        ):
            event.accept()
            return False
        if (
            event.type() == QtCore.QEvent.Type.KeyPress
            and self.isActiveWindow()
            and self._handle_zoom_key_event(event)
        ):
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if self._handle_zoom_key_event(event):
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def _handle_zoom_key_event(self, event) -> bool:
        action = self._zoom_action_for_key_event(event)
        if action == "in":
            self.zoom_in()
        elif action == "out":
            self.zoom_out()
        elif action == "reset":
            self.reset_zoom()
        else:
            return False
        event.accept()
        return True

    def _is_zoom_key_event(self, event) -> bool:
        return self._zoom_action_for_key_event(event) is not None

    def _zoom_action_for_key_event(self, event) -> str | None:
        modifiers = event.modifiers()
        is_zoom_modifier = bool(
            modifiers
            & (
                QtCore.Qt.KeyboardModifier.ControlModifier
                | QtCore.Qt.KeyboardModifier.MetaModifier
            )
        )
        if not is_zoom_modifier:
            return None
        key = event.key()
        text = event.text()
        if key in (QtCore.Qt.Key.Key_Plus, QtCore.Qt.Key.Key_Equal) or text in ("+", "="):
            return "in"
        if key in (QtCore.Qt.Key.Key_Minus, QtCore.Qt.Key.Key_Underscore) or text in ("-", "_", "−"):
            return "out"
        if key == QtCore.Qt.Key.Key_0 or text == "0":
            return "reset"
        return None

    def _apply_startup_zoom(self) -> None:
        screen = QtWidgets.QApplication.primaryScreen()
        if screen is None:
            self.set_zoom(1.0)
            return

        available = screen.availableGeometry()
        width_zoom = available.width() / float(self.DESIGN_SIZE.width())
        height_zoom = available.height() / float(self.DESIGN_SIZE.height())
        zoom = min(1.0, width_zoom, height_zoom)
        self.set_zoom(zoom)

    def _clamp_zoom(self, zoom: float) -> float:
        return max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))

    def set_zoom(self, zoom: float) -> None:
        self.zoom_factor = self._clamp_zoom(zoom)
        self.scaled_view.set_zoom(self.zoom_factor)
        self.resize_to_scaled_content()

    def zoom_in(self) -> None:
        self.set_zoom(self.zoom_factor + self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self.set_zoom(self.zoom_factor - self.ZOOM_STEP)

    def reset_zoom(self) -> None:
        self.set_zoom(1.0)

    def resize_to_scaled_content(self) -> None:
        self.resize(self._scaled_window_size())

    def _scaled_window_size(self) -> QtCore.QSize:
        scaled_width = int(self.DESIGN_SIZE.width() * self.zoom_factor)
        scaled_height = int(self.DESIGN_SIZE.height() * self.zoom_factor)
        available = self._available_screen_geometry()
        if available is None:
            return QtCore.QSize(scaled_width, scaled_height)
        return QtCore.QSize(
            min(scaled_width, available.width()),
            min(scaled_height, available.height()),
        )

    def _available_screen_geometry(self) -> QtCore.QRect | None:
        screen = self.screen() or QtWidgets.QApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry()

    def _current_stimulus(self) -> StimulusSpec | None:
        row = self.stimulus_list.currentRow()
        if row < 0 or row >= len(self.project.stimuli):
            return None
        return self.project.stimuli[row]

    def _refresh_all(self):
        current = max(0, self.stimulus_list.currentRow())
        self.stimulus_list.clear()
        for stim in self.project.stimuli:
            self.stimulus_list.addItem(stim.key)
        if self.project.stimuli:
            self.stimulus_list.setCurrentRow(min(current, len(self.project.stimuli) - 1))
        self._refresh_fields()
        self._refresh_preview()

    def _refresh_fields(self):
        stim = self._current_stimulus()
        if not stim:
            return
        blockers = [
            QtCore.QSignalBlocker(widget)
            for widget in [
                self.key_edit,
                self.name_edit,
                self.n_dots_spin,
                self.primitive_list,
                self.framerate_spin,
                self.radius_spin,
                self.grid_rings_spin,
                self.grid_first_radius_spin,
                self.grid_spacing_spin,
                self.grid_points_spin,
                self.duration_spin,
                self.primitive_interval_spin,
                self.primitive_mode_combo,
                self.flicker_interval_spin,
                self.flickering_check,
                self.bar_thickness_spin,
                self.speed_spin,
                self.growth_speed_spin,
                self.max_radius_spin,
                self.step_distance_spin,
            ]
        ]
        self.key_edit.setText(stim.key)
        self.name_edit.setText(stim.name)
        self.n_dots_spin.setValue(stim.n_dots)
        self._refresh_timeline_rows()
        if stim.primitives:
            self.primitive_list.setCurrentRow(0)
        self.framerate_spin.setValue(self.project.global_params.framerate)
        self.radius_spin.setValue(self.project.global_params.radius_cm)
        self.calibration_summary_label.setText(self._calibration_summary_text())
        grid = self.project.grid_settings
        self.grid_rings_spin.setValue(grid.ring_count)
        self.grid_first_radius_spin.setValue(grid.first_ring_radius_cm)
        self.grid_spacing_spin.setValue(grid.ring_spacing_cm)
        self.grid_points_spin.setValue(grid.points_per_ring)
        self._load_stimulus_parameter_fields()
        del blockers

    def _refresh_timeline_rows(self) -> None:
        stim = self._current_stimulus()
        if not stim:
            self.timeline_label.setText("Timeline primitives (0.000 s total)")
            self.primitive_list.clear()
            return
        current_row = self.primitive_list.currentRow()
        blocker = QtCore.QSignalBlocker(self.primitive_list)
        self.primitive_list.clear()
        summaries = primitive_duration_summary(stim, self.project.global_params)
        total_sec = summaries[-1]["cumulative_sec"] if summaries else 0.0
        self.timeline_label.setText(f"Timeline primitives ({total_sec:.3f} s total)")
        for primitive, summary in zip(stim.primitives, summaries):
            self.primitive_list.addItem(
                f"{primitive.kind} | {summary['duration_sec']:.3f} s | end {summary['cumulative_sec']:.3f} s"
            )
        del blocker
        if stim.primitives:
            self.primitive_list.setCurrentRow(max(0, min(current_row, len(stim.primitives) - 1)))

    def _refresh_preview(self):
        stim = self._current_stimulus()
        if not stim:
            return
        self.canvas.set_stimulus(self.project, stim)
        self.frame_slider.setRange(0, max(0, len(self.canvas.df) - 1))
        self.frame_slider.setValue(min(self.frame_slider.value(), max(0, len(self.canvas.df) - 1)))

    def _on_stimulus_selected(self, row: int):
        self._refresh_fields()
        self._refresh_preview()

    def _apply_fields(self):
        stim = self._current_stimulus()
        if not stim:
            return
        stim.key = self.key_edit.text().strip() or "Stimulus"
        stim.name = self.name_edit.text().strip() or stim.key
        stim.n_dots = self.n_dots_spin.value()
        self._refresh_all()

    def _apply_global_fields(self):
        self.project.global_params.framerate = self.framerate_spin.value()
        self.project.global_params.radius_cm = self.radius_spin.value()
        self._refresh_timeline_rows()
        self._refresh_preview()

    def _calibration_summary_text(self) -> str:
        calibration = self.project.calibration
        width_cm = calibration.screen_width_mm / 10.0
        height_cm = calibration.screen_height_mm / 10.0
        return (
            f"{calibration.screen_width_px} x {calibration.screen_height_px} px; "
            f"{width_cm:.1f} x {height_cm:.1f} cm; "
            f"{calibration.mm_per_px_x:.5f} x {calibration.mm_per_px_y:.5f} mm/px"
        )

    def _apply_grid_fields(self):
        self.project.grid_settings.ring_count = self.grid_rings_spin.value()
        self.project.grid_settings.first_ring_radius_cm = self.grid_first_radius_spin.value()
        self.project.grid_settings.ring_spacing_cm = self.grid_spacing_spin.value()
        self.project.grid_settings.points_per_ring = self.grid_points_spin.value()
        self._refresh_preview()

    def _add_stimulus(self):
        idx = len(self.project.stimuli) + 1
        self.project.stimuli.append(StimulusSpec(key=f"Stimulus_{idx}", name=f"Stimulus {idx}", primitives=[]))
        self._refresh_all()
        self.stimulus_list.setCurrentRow(len(self.project.stimuli) - 1)

    def _duplicate_stimulus(self):
        stim = self._current_stimulus()
        if not stim:
            return
        data = json.loads(json.dumps(project_to_dict(StimulusProject(stimuli=[stim]))["stimuli"][0]))
        dup = StimulusSpec(
            key=f"{data['key']}_copy",
            name=f"{data['name']} copy",
            n_dots=data["n_dots"],
            primitives=[Primitive(p["kind"], p.get("params", {})) for p in data["primitives"]],
        )
        self.project.stimuli.append(dup)
        self._refresh_all()
        self.stimulus_list.setCurrentRow(len(self.project.stimuli) - 1)

    def _delete_stimulus(self):
        row = self.stimulus_list.currentRow()
        if len(self.project.stimuli) <= 1 or row < 0:
            return
        del self.project.stimuli[row]
        self._refresh_all()

    def _mirror_stimulus(self):
        stim = self._current_stimulus()
        if not stim:
            return
        mirror_stimulus_in_place(stim, self.project.global_params)
        self._refresh_fields()
        self._refresh_preview()

    def _default_primitive_params(self, kind: str) -> dict:
        defaults = {
            "static_hold": {"duration_sec": 10.0},
            "flicker": {"duration_sec": 3.0, "flicker_interval_sec": self.project.global_params.flicker_interval_sec},
            "rocking": {"points": [], "duration_sec": 1.0, "movement_interval_ms": self.project.grid_settings.movement_interval_ms, "flickering": False},
            "rocking_lr": {"points": [], "duration_sec": 1.0, "movement_interval_ms": self.project.grid_settings.movement_interval_ms, "flickering": False},
            "point_path": {
                "points": [],
                "movement_interval_ms": self.project.grid_settings.movement_interval_ms,
                "mode": self.project.grid_settings.movement_mode,
            },
            "linear": {
                "points": [],
                "movement_interval_ms": self.project.grid_settings.movement_interval_ms,
                "mode": self.project.grid_settings.movement_mode,
                "step_distance_cm": 0.2,
            },
            "whole_field_grating": {
                "points": [],
                "duration_sec": 10.0,
                "bar_thickness_cm": 0.5,
                "speed_cm_sec": 1.0,
            },
            "loom": {
                "duration_sec": 3.0,
                "growth_speed_cm_sec": 1.0,
                "max_radius_cm": 3.0,
            },
        }
        return defaults[kind]

    def _add_primitive(self):
        stim = self._current_stimulus()
        if not stim:
            return
        kind = self.kind_combo.currentText()
        stim.primitives.append(Primitive(kind, self._default_primitive_params(kind)))
        self._refresh_fields()
        self.primitive_list.setCurrentRow(len(stim.primitives) - 1)
        self._refresh_preview()

    def _selected_primitive(self) -> Primitive | None:
        stim = self._current_stimulus()
        if not stim:
            return None
        row = self.primitive_list.currentRow()
        if row < 0 or row >= len(stim.primitives):
            return None
        return stim.primitives[row]

    def _toggle_grid_point(self, ring_index: int, point_index: int):
        primitive = self._selected_primitive()
        if primitive is None:
            return
        point = make_grid_point(ring_index, point_index, self.project.grid_settings, self.project.global_params)
        if primitive.kind in {"static_hold", "flicker", "loom"}:
            primitive.params["point"] = point
        elif primitive.kind in {"rocking", "rocking_lr"}:
            primitive.params["points"] = self._toggle_limited_point_list(primitive.params.get("points", []), point, limit=2)
        elif primitive.kind in {"whole_field_grating", "linear"}:
            primitive.params["points"] = self._toggle_limited_point_list(primitive.params.get("points", []), point, limit=2)
        elif primitive.kind == "point_path":
            primitive.params["points"] = self._toggle_limited_point_list(primitive.params.get("points", []), point, limit=None)
            primitive.params["movement_interval_ms"] = primitive.params.get("movement_interval_ms", self.project.grid_settings.movement_interval_ms)
            primitive.params["mode"] = primitive.params.get("mode", self.project.grid_settings.movement_mode)
        else:
            return
        self._load_primitive_editor(self.primitive_list.currentRow())
        self._refresh_timeline_rows()
        self._refresh_preview()

    def _toggle_limited_point_list(self, points, point: dict, limit: int | None) -> list[dict]:
        current = [existing for existing in points if isinstance(existing, dict)]
        keep = []
        removed = False
        for existing in current:
            if (
                int(existing.get("ring_index", -1)) == int(point["ring_index"])
                and int(existing.get("point_index", -1)) == int(point["point_index"])
            ):
                removed = True
            else:
                keep.append(existing)
        if removed:
            return keep
        if limit is not None and len(keep) >= limit:
            keep[-1] = point
            return keep
        keep.append(point)
        return keep

    def _delete_primitive(self):
        stim = self._current_stimulus()
        row = self.primitive_list.currentRow()
        if not stim or row < 0:
            return
        del stim.primitives[row]
        self._refresh_fields()
        self._refresh_preview()

    def _load_primitive_editor(self, row: int):
        stim = self._current_stimulus()
        if not stim or row < 0 or row >= len(stim.primitives):
            self.primitive_json.clear()
            self._load_stimulus_parameter_fields()
            return
        primitive = stim.primitives[row]
        self.primitive_json.setPlainText(json.dumps({"kind": primitive.kind, "params": primitive.params}, indent=2))
        self._load_stimulus_parameter_fields()

    def _load_stimulus_parameter_fields(self) -> None:
        primitive = self._selected_primitive()
        relevant = set()
        if primitive is None:
            self.stimulus_params_group.setVisible(False)
        else:
            self.stimulus_params_group.setVisible(True)
            if primitive.kind == "static_hold":
                relevant = {"Duration"}
            elif primitive.kind == "flicker":
                relevant = {"Duration", "Flicker interval"}
            elif primitive.kind in {"rocking", "rocking_lr"}:
                relevant = {"Duration", "Interval", "Flickering"}
            elif primitive.kind == "point_path":
                relevant = {"Interval", "Mode"}
            elif primitive.kind == "linear":
                relevant = {"Interval", "Mode", "Step distance"}
            elif primitive.kind == "whole_field_grating":
                relevant = {"Duration", "Bar thickness", "Speed"}
            elif primitive.kind == "loom":
                relevant = {"Duration", "Growth speed", "Max radius"}
        for label_text, label, widget in self._stimulus_param_rows:
            visible = label_text in relevant
            label.setVisible(visible)
            widget.setVisible(visible)
        if primitive is None:
            return
        blockers = [
            QtCore.QSignalBlocker(widget)
            for _, _, widget in self._stimulus_param_rows
        ]
        self.duration_spin.setValue(float(primitive.params.get("duration_sec", 1.0)))
        self.primitive_interval_spin.setValue(float(primitive.params.get("movement_interval_ms", self.project.grid_settings.movement_interval_ms)))
        self.primitive_mode_combo.setCurrentText(str(primitive.params.get("mode", self.project.grid_settings.movement_mode)))
        self.flicker_interval_spin.setValue(float(primitive.params.get("flicker_interval_sec", self.project.global_params.flicker_interval_sec)))
        self.flickering_check.setChecked(bool(primitive.params.get("flickering", False)))
        self.bar_thickness_spin.setValue(float(primitive.params.get("bar_thickness_cm", 0.5)))
        self.speed_spin.setValue(float(primitive.params.get("speed_cm_sec", self.project.global_params.speed_cm_sec)))
        self.growth_speed_spin.setValue(float(primitive.params.get("growth_speed_cm_sec", 1.0)))
        self.max_radius_spin.setValue(float(primitive.params.get("max_radius_cm", 3.0)))
        self.step_distance_spin.setValue(float(primitive.params.get("step_distance_cm", 0.2)))
        del blockers

    def _apply_stimulus_parameter_fields(self):
        primitive = self._selected_primitive()
        if primitive is None:
            return
        if primitive.kind in {"static_hold", "flicker", "rocking", "rocking_lr", "whole_field_grating", "loom"}:
            primitive.params["duration_sec"] = self.duration_spin.value()
        if primitive.kind in {"rocking", "rocking_lr", "point_path", "linear"}:
            primitive.params["movement_interval_ms"] = self.primitive_interval_spin.value()
        if primitive.kind in {"point_path", "linear"}:
            primitive.params["mode"] = self.primitive_mode_combo.currentText()
        if primitive.kind == "flicker":
            primitive.params["flicker_interval_sec"] = self.flicker_interval_spin.value()
        if primitive.kind in {"rocking", "rocking_lr"}:
            primitive.params["flickering"] = self.flickering_check.isChecked()
        if primitive.kind == "whole_field_grating":
            primitive.params["bar_thickness_cm"] = self.bar_thickness_spin.value()
            primitive.params["speed_cm_sec"] = self.speed_spin.value()
        if primitive.kind == "loom":
            primitive.params["growth_speed_cm_sec"] = self.growth_speed_spin.value()
            primitive.params["max_radius_cm"] = self.max_radius_spin.value()
        if primitive.kind == "linear":
            primitive.params["step_distance_cm"] = self.step_distance_spin.value()
        self._load_primitive_editor(self.primitive_list.currentRow())
        self._refresh_timeline_rows()
        self._refresh_preview()

    def _apply_primitive_json(self):
        stim = self._current_stimulus()
        row = self.primitive_list.currentRow()
        if not stim or row < 0:
            return
        try:
            data = json.loads(self.primitive_json.toPlainText())
            stim.primitives[row] = Primitive(data["kind"], data.get("params", {}))
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Invalid primitive JSON", str(exc))
            return
        self._refresh_fields()
        self.primitive_list.setCurrentRow(row)
        self._refresh_preview()

    def _advance_frame(self):
        value = self.frame_slider.value() + 1
        if value > self.frame_slider.maximum():
            value = 0
        self.frame_slider.setValue(value)

    def _open_project(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open project", "", "JSON (*.json)")
        if path:
            self.project = load_project(path)
            self._refresh_all()

    def _save_project(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save project", "stimulus_designer_project.json", "JSON (*.json)")
        if path:
            save_project(self.project, path)

    def _import_legacy(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import legacy stimulus JSON", "", "JSON (*.json)")
        if path:
            self.project = import_legacy_config(path)
            self._refresh_all()

    def _export_csvs(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Export trajectory CSVs")
        if path:
            try:
                written = export_project(self.project, path)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(self, "Export failed", str(exc))
                return
            self.current_output_dir = Path(path)
            QtWidgets.QMessageBox.information(self, "Export complete", f"Wrote {len(written)} trajectory CSV files.")

    def _launch_psychopy(self):
        if self.current_output_dir is None:
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose generated stimulus folder")
            if not path:
                return
            self.current_output_dir = Path(path)
        launch_psychopy_projection(self.current_output_dir)


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    window = StimulusDesignerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
