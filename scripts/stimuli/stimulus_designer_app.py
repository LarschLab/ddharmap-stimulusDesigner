from __future__ import annotations

import json
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
    project_to_dict,
    save_project,
)


class PreviewCanvas(QtWidgets.QWidget):
    frame_changed = QtCore.pyqtSignal(int)
    grid_point_clicked = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 520)
        self.project = default_project()
        self.stimulus = self.project.stimuli[0]
        self.frame_index = 0
        self.df = generate_stimulus_dataframe(self.stimulus, self.project.global_params)
        self.hovered_grid_point: tuple[int, int] | None = None
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

    def _scale(self) -> float:
        return min(self.width(), self.height()) / 6.0

    def _to_widget(self, x_cm: float, y_cm: float) -> QtCore.QPointF:
        scale = self._scale()
        return QtCore.QPointF(self.width() / 2.0 + x_cm * scale, self.height() / 2.0 - y_cm * scale)

    def _selected_grid_points(self) -> list[tuple[int, int]]:
        selected: list[tuple[int, int]] = []
        for primitive in self.stimulus.primitives:
            if primitive.kind != "point_path":
                continue
            for point in primitive.params.get("points", []):
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
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            point = self._nearest_grid_point(event.position())
            if point is not None:
                self.grid_point_clicked.emit(point[0], point[1])
                return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#f7f7f4"))

        center = QtCore.QPointF(self.width() / 2.0, self.height() / 2.0)
        scale = self._scale()

        grid_pen = QtGui.QPen(QtGui.QColor("#d6d6d0"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for cm in [x * 0.5 for x in range(-6, 7)]:
            p1 = self._to_widget(cm, -3)
            p2 = self._to_widget(cm, 3)
            painter.drawLine(p1, p2)
            p3 = self._to_widget(-3, cm)
            p4 = self._to_widget(3, cm)
            painter.drawLine(p3, p4)

        axis_pen = QtGui.QPen(QtGui.QColor("#8a8a84"))
        axis_pen.setWidth(2)
        painter.setPen(axis_pen)
        painter.drawLine(QtCore.QPointF(0, center.y()), QtCore.QPointF(self.width(), center.y()))
        painter.drawLine(QtCore.QPointF(center.x(), 0), QtCore.QPointF(center.x(), self.height()))

        fish_pen = QtGui.QPen(QtGui.QColor("#1b1b1b"))
        fish_pen.setWidth(2)
        painter.setPen(fish_pen)
        painter.setBrush(QtGui.QColor("#d9efe7"))
        painter.drawEllipse(center, 12, 26)
        painter.drawLine(center + QtCore.QPointF(0, -34), center + QtCore.QPointF(0, 34))

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
            elif is_hovered:
                color = QtGui.QColor("#d7a31f")
            else:
                color = QtGui.QColor("#ffffff")
            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor("#4c4c48")))
            radius_px = 5 if is_hovered or is_selected else 3
            painter.drawEllipse(pos, radius_px, radius_px)

        if self.df.empty:
            return

        path_pen = QtGui.QPen(QtGui.QColor("#3f7f99"))
        path_pen.setWidth(2)
        painter.setPen(path_pen)
        for dot in self._dot_names():
            points = [
                self._to_widget(float(row[f"{dot}_x"]), float(row[f"{dot}_y"]))
                for _, row in self.df.iloc[:: max(1, len(self.df) // 250)].iterrows()
            ]
            for a, b in zip(points[:-1], points[1:]):
                painter.drawLine(a, b)

        row = self.df.iloc[self.frame_index]
        painter.setBrush(QtGui.QColor("#111111"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#111111")))
        for dot in self._dot_names():
            radius = float(row.get(f"{dot}_radius", self.project.global_params.dot_size_cm))
            if radius <= 0:
                continue
            pos = self._to_widget(float(row[f"{dot}_x"]), float(row[f"{dot}_y"]))
            painter.drawEllipse(pos, max(2.0, radius * scale), max(2.0, radius * scale))

        painter.setPen(QtGui.QPen(QtGui.QColor("#303030")))
        painter.drawText(12, 22, f"Frame {self.frame_index + 1}/{len(self.df)}")
        painter.drawText(12, 42, "Fish center: 0 mm, 0 mm")

    def _dot_names(self) -> list[str]:
        return sorted({col.rsplit("_", 1)[0] for col in self.df.columns if col.endswith("_x")})


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
            "Click grid points to build a custom path. Hover highlights the target point; clicking an existing path point removes it.",
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

        self.primitive_list = QtWidgets.QListWidget()
        self.primitive_list.currentRowChanged.connect(self._load_primitive_editor)
        right.addWidget(QtWidgets.QLabel("Timeline primitives"))
        right.addWidget(self.primitive_list)
        primitive_buttons = QtWidgets.QHBoxLayout()
        self.kind_combo = QtWidgets.QComboBox()
        self.kind_combo.addItems(["static_hold", "arc", "continuous_arc", "flicker", "rocking", "rocking_lr", "waypoint_move", "point_path"])
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

        self.params_group = QtWidgets.QGroupBox("Global / calibration")
        params_form = QtWidgets.QFormLayout(self.params_group)
        self.framerate_spin = QtWidgets.QDoubleSpinBox()
        self.framerate_spin.setRange(1, 240)
        self.framerate_spin.setValue(60)
        self.radius_spin = QtWidgets.QDoubleSpinBox()
        self.radius_spin.setRange(0.1, 20)
        self.radius_spin.setValue(1.8)
        self.mm_width_spin = QtWidgets.QDoubleSpinBox()
        self.mm_width_spin.setRange(1, 10000)
        self.mm_width_spin.setValue(590)
        self.px_width_spin = QtWidgets.QSpinBox()
        self.px_width_spin.setRange(1, 10000)
        self.px_width_spin.setValue(1920)
        for widget in [self.framerate_spin, self.radius_spin, self.mm_width_spin, self.px_width_spin]:
            widget.valueChanged.connect(self._apply_global_fields)
        self._register_description(self.framerate_spin, "Preview and export framerate in frames per second.")
        self._register_description(self.radius_spin, "Default arc radius used by angle-based primitives.")
        self._register_description(self.mm_width_spin, "Physical screen width used for calibration metadata.")
        self._register_description(self.px_width_spin, "Screen width in pixels used for calibration metadata.")
        params_form.addRow("Framerate", self.framerate_spin)
        params_form.addRow("Arc radius cm", self.radius_spin)
        params_form.addRow("Screen width mm", self.mm_width_spin)
        params_form.addRow("Screen width px", self.px_width_spin)
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
        self.interval_spin = QtWidgets.QDoubleSpinBox()
        self.interval_spin.setRange(1, 10000)
        self.interval_spin.setSuffix(" ms")
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["bout", "continuous"])
        for widget in [
            self.grid_rings_spin,
            self.grid_first_radius_spin,
            self.grid_spacing_spin,
            self.grid_points_spin,
            self.interval_spin,
            self.mode_combo,
        ]:
            if isinstance(widget, QtWidgets.QComboBox):
                widget.currentTextChanged.connect(self._apply_grid_fields)
            else:
                widget.valueChanged.connect(self._apply_grid_fields)
        self._register_description(self.grid_rings_spin, "Number of concentric placement rings around the fish.")
        self._register_description(self.grid_first_radius_spin, "Distance from fish center to the first placement ring in centimeters.")
        self._register_description(self.grid_spacing_spin, "Distance between neighboring placement rings in centimeters.")
        self._register_description(self.grid_points_spin, "Number of clickable positions on each ring.")
        self._register_description(self.interval_spin, "Time between point changes for clicked point paths.")
        self._register_description(self.mode_combo, "Bout jumps point-to-point; continuous interpolates between points.")
        grid_form.addRow("Rings", self.grid_rings_spin)
        grid_form.addRow("First ring cm", self.grid_first_radius_spin)
        grid_form.addRow("Ring spacing cm", self.grid_spacing_spin)
        grid_form.addRow("Points / ring", self.grid_points_spin)
        grid_form.addRow("Interval", self.interval_spin)
        grid_form.addRow("Mode", self.mode_combo)
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
                self.mm_width_spin,
                self.px_width_spin,
                self.grid_rings_spin,
                self.grid_first_radius_spin,
                self.grid_spacing_spin,
                self.grid_points_spin,
                self.interval_spin,
                self.mode_combo,
            ]
        ]
        self.key_edit.setText(stim.key)
        self.name_edit.setText(stim.name)
        self.n_dots_spin.setValue(stim.n_dots)
        self.primitive_list.clear()
        for primitive in stim.primitives:
            self.primitive_list.addItem(primitive.kind)
        if stim.primitives:
            self.primitive_list.setCurrentRow(0)
        self.framerate_spin.setValue(self.project.global_params.framerate)
        self.radius_spin.setValue(self.project.global_params.radius_cm)
        self.mm_width_spin.setValue(self.project.calibration.screen_width_mm)
        self.px_width_spin.setValue(self.project.calibration.screen_width_px)
        grid = self.project.grid_settings
        self.grid_rings_spin.setValue(grid.ring_count)
        self.grid_first_radius_spin.setValue(grid.first_ring_radius_cm)
        self.grid_spacing_spin.setValue(grid.ring_spacing_cm)
        self.grid_points_spin.setValue(grid.points_per_ring)
        self.interval_spin.setValue(grid.movement_interval_ms)
        self.mode_combo.setCurrentText(grid.movement_mode)
        del blockers

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
        self.project.calibration.screen_width_mm = self.mm_width_spin.value()
        self.project.calibration.screen_width_px = self.px_width_spin.value()
        self._refresh_preview()

    def _apply_grid_fields(self):
        self.project.grid_settings.ring_count = self.grid_rings_spin.value()
        self.project.grid_settings.first_ring_radius_cm = self.grid_first_radius_spin.value()
        self.project.grid_settings.ring_spacing_cm = self.grid_spacing_spin.value()
        self.project.grid_settings.points_per_ring = self.grid_points_spin.value()
        self.project.grid_settings.movement_interval_ms = self.interval_spin.value()
        self.project.grid_settings.movement_mode = self.mode_combo.currentText()
        primitive = self._current_point_path_primitive(create=False)
        if primitive is not None:
            primitive.params["movement_interval_ms"] = self.project.grid_settings.movement_interval_ms
            primitive.params["mode"] = self.project.grid_settings.movement_mode
        self._refresh_preview()

    def _add_stimulus(self):
        idx = len(self.project.stimuli) + 1
        self.project.stimuli.append(StimulusSpec(key=f"Stimulus_{idx}", name=f"Stimulus {idx}", primitives=[Primitive("static_hold", {"duration_sec": 1.0})]))
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
            "static_hold": {"duration_sec": 1.0, "angle_deg": -30.0},
            "arc": {"angle_range": [-30.0, -160.0], "continuous": False, "flickering": False},
            "continuous_arc": {"angle_range": [-30.0, -160.0], "flickering": False},
            "flicker": {"angle_range": [-30.0, -160.0], "angle_index": 10, "duration_sec": 3.0},
            "rocking": {"angle_range": [-30.0, -163.0], "rocking_idx_pair": [11, 13], "flickering": False},
            "rocking_lr": {"left_angle_range": [-30.0, -163.0], "right_angle_range": [30.0, 163.0], "rocking_lr_indices": [11, 13], "flickering": False},
            "waypoint_move": {"x_cm": 0.0, "y_cm": 1.0, "duration_sec": 1.0},
            "point_path": {
                "points": [],
                "movement_interval_ms": self.project.grid_settings.movement_interval_ms,
                "mode": self.project.grid_settings.movement_mode,
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

    def _current_point_path_primitive(self, create: bool) -> Primitive | None:
        stim = self._current_stimulus()
        if not stim:
            return None
        row = self.primitive_list.currentRow()
        if row >= 0 and row < len(stim.primitives) and stim.primitives[row].kind == "point_path":
            return stim.primitives[row]
        for primitive in reversed(stim.primitives):
            if primitive.kind == "point_path":
                return primitive
        if not create:
            return None
        primitive = Primitive("point_path", self._default_primitive_params("point_path"))
        stim.primitives.append(primitive)
        self._refresh_fields()
        self.primitive_list.setCurrentRow(len(stim.primitives) - 1)
        return primitive

    def _toggle_grid_point(self, ring_index: int, point_index: int):
        primitive = self._current_point_path_primitive(create=True)
        if primitive is None:
            return
        points = list(primitive.params.get("points", []))
        keep = []
        removed = False
        for point in points:
            if int(point.get("ring_index", -1)) == ring_index and int(point.get("point_index", -1)) == point_index:
                removed = True
            else:
                keep.append(point)
        if removed:
            primitive.params["points"] = keep
        else:
            keep.append(make_grid_point(ring_index, point_index, self.project.grid_settings, self.project.global_params))
            primitive.params["points"] = keep
        primitive.params["movement_interval_ms"] = self.project.grid_settings.movement_interval_ms
        primitive.params["mode"] = self.project.grid_settings.movement_mode
        self._load_primitive_editor(self.primitive_list.currentRow())
        self._refresh_preview()

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
            return
        primitive = stim.primitives[row]
        self.primitive_json.setPlainText(json.dumps({"kind": primitive.kind, "params": primitive.params}, indent=2))

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
            written = export_project(self.project, path)
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
