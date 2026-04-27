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
    project_to_dict,
    save_project,
)


class PreviewCanvas(QtWidgets.QWidget):
    frame_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(560, 520)
        self.project = default_project()
        self.stimulus = self.project.stimuli[0]
        self.frame_index = 0
        self.df = generate_stimulus_dataframe(self.stimulus, self.project.global_params)
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


class StimulusDesignerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stimulus Designer")
        self.project = default_project()
        self.current_output_dir: Path | None = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._advance_frame)
        self._build_ui()
        self._refresh_all()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(central)
        self.setCentralWidget(central)

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
        left_buttons = QtWidgets.QHBoxLayout()
        left_buttons.addWidget(add_btn)
        left_buttons.addWidget(dup_btn)
        left_buttons.addWidget(del_btn)
        left.addLayout(left_buttons)
        layout.addLayout(left, 1)

        middle = QtWidgets.QVBoxLayout()
        self.canvas = PreviewCanvas()
        middle.addWidget(self.canvas, 1)
        self.frame_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.frame_slider.valueChanged.connect(self.canvas.set_frame)
        middle.addWidget(self.frame_slider)
        preview_buttons = QtWidgets.QHBoxLayout()
        play_btn = QtWidgets.QPushButton("Play")
        play_btn.clicked.connect(lambda: self.timer.start(max(1, int(1000 / self.project.global_params.framerate))))
        pause_btn = QtWidgets.QPushButton("Pause")
        pause_btn.clicked.connect(self.timer.stop)
        preview_buttons.addWidget(play_btn)
        preview_buttons.addWidget(pause_btn)
        middle.addLayout(preview_buttons)
        layout.addLayout(middle, 3)

        right = QtWidgets.QVBoxLayout()
        form = QtWidgets.QFormLayout()
        self.key_edit = QtWidgets.QLineEdit()
        self.key_edit.editingFinished.connect(self._apply_fields)
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.editingFinished.connect(self._apply_fields)
        self.n_dots_spin = QtWidgets.QSpinBox()
        self.n_dots_spin.setRange(1, 8)
        self.n_dots_spin.valueChanged.connect(self._apply_fields)
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
        self.kind_combo.addItems(["static_hold", "arc", "continuous_arc", "flicker", "rocking", "rocking_lr", "waypoint_move"])
        add_prim_btn = QtWidgets.QPushButton("Add")
        add_prim_btn.clicked.connect(self._add_primitive)
        del_prim_btn = QtWidgets.QPushButton("Delete")
        del_prim_btn.clicked.connect(self._delete_primitive)
        primitive_buttons.addWidget(self.kind_combo)
        primitive_buttons.addWidget(add_prim_btn)
        primitive_buttons.addWidget(del_prim_btn)
        right.addLayout(primitive_buttons)

        self.primitive_json = QtWidgets.QPlainTextEdit()
        self.primitive_json.setMaximumHeight(160)
        apply_primitive_btn = QtWidgets.QPushButton("Apply Primitive JSON")
        apply_primitive_btn.clicked.connect(self._apply_primitive_json)
        right.addWidget(self.primitive_json)
        right.addWidget(apply_primitive_btn)

        params_group = QtWidgets.QGroupBox("Global / calibration")
        params_form = QtWidgets.QFormLayout(params_group)
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
        params_form.addRow("Framerate", self.framerate_spin)
        params_form.addRow("Arc radius cm", self.radius_spin)
        params_form.addRow("Screen width mm", self.mm_width_spin)
        params_form.addRow("Screen width px", self.px_width_spin)
        right.addWidget(params_group)

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
            file_buttons.addWidget(btn, i // 2, i % 2)
        right.addLayout(file_buttons)
        layout.addLayout(right, 2)

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

    def _default_primitive_params(self, kind: str) -> dict:
        defaults = {
            "static_hold": {"duration_sec": 1.0, "angle_deg": -30.0},
            "arc": {"angle_range": [-30.0, -160.0], "continuous": False, "flickering": False},
            "continuous_arc": {"angle_range": [-30.0, -160.0], "flickering": False},
            "flicker": {"angle_range": [-30.0, -160.0], "angle_index": 10, "duration_sec": 3.0},
            "rocking": {"angle_range": [-30.0, -163.0], "rocking_idx_pair": [11, 13], "flickering": False},
            "rocking_lr": {"left_angle_range": [-30.0, -163.0], "right_angle_range": [30.0, 163.0], "rocking_lr_indices": [11, 13], "flickering": False},
            "waypoint_move": {"x_cm": 0.0, "y_cm": 1.0, "duration_sec": 1.0},
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
    window.resize(1280, 760)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
