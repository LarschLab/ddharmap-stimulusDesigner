import os

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 is not installed")
QtGui = pytest.importorskip("PyQt6.QtGui", reason="PyQt6 is not installed")
QtCore = pytest.importorskip("PyQt6.QtCore", reason="PyQt6 is not installed")

from scripts.stimuli.stimulus_designer_app import PreviewCanvas, StimulusDesignerWindow  # noqa: E402


@pytest.fixture
def qt_app():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_stimulus_designer_zoom_controls_are_clamped(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.set_zoom(1.0)
        assert window.zoom_factor == pytest.approx(1.0)
        assert window.scaled_view.zoom == pytest.approx(1.0)

        window.zoom_out()
        assert window.zoom_factor == pytest.approx(0.9)
        window.zoom_in()
        assert window.zoom_factor == pytest.approx(1.0)

        window.set_zoom(99.0)
        assert window.zoom_factor == pytest.approx(window.MAX_ZOOM)
        window.set_zoom(0.0)
        assert window.zoom_factor == pytest.approx(window.MIN_ZOOM)

        window.reset_zoom()
        assert window.zoom_factor == pytest.approx(1.0)
    finally:
        window.close()


def test_stimulus_designer_scaled_view_keeps_content_usable(qt_app):
    window = StimulusDesignerWindow()
    try:
        assert window.scaled_view.scene() is not None
        assert window.canvas.df.empty
        assert window.stimulus_list.count() == len(window.project.stimuli)
        assert window.scaled_view.minimumWidth() == 1
        assert window.scaled_view.minimumHeight() == 1
    finally:
        window.close()


def test_stimulus_designer_gui_starts_with_grid_defaults(qt_app):
    window = StimulusDesignerWindow()
    try:
        assert window.project.grid_settings.first_ring_radius_cm == pytest.approx(2.0)
        assert window.project.grid_settings.ring_spacing_cm == pytest.approx(0.4)
        assert window.project.grid_settings.points_per_ring == 12
        assert window.project.grid_settings.movement_interval_ms == pytest.approx(700.0)
        assert window.grid_first_radius_spin.value() == pytest.approx(2.0)
        assert window.grid_spacing_spin.value() == pytest.approx(0.4)
        assert window.grid_points_spin.value() == 12
        assert window.project.grid_settings.movement_interval_ms == pytest.approx(700.0)
    finally:
        window.close()


def test_stimulus_designer_gui_starts_with_projector_calibration(qt_app):
    window = StimulusDesignerWindow()
    try:
        assert window.project.calibration.screen_width_px == 1280
        assert window.project.calibration.screen_height_px == 800
        assert window.project.calibration.screen_width_mm == pytest.approx(152.0)
        assert window.project.calibration.screen_height_mm == pytest.approx(95.0)
        assert not hasattr(window, "px_width_spin")
        assert not hasattr(window, "px_height_spin")
        assert not hasattr(window, "mm_width_spin")
        assert not hasattr(window, "mm_height_spin")
        assert "1280 x 800 px" in window.calibration_summary_label.text()
        assert "15.2 x 9.5 cm" in window.calibration_summary_label.text()
        assert "0.11875 x 0.11875 mm/px" in window.calibration_summary_label.text()
    finally:
        window.close()


def test_stimulus_designer_add_menu_hides_redundant_primitives(qt_app):
    window = StimulusDesignerWindow()
    try:
        kinds = [window.kind_combo.itemText(i) for i in range(window.kind_combo.count())]
        assert kinds == ["static_hold", "flicker", "rocking", "rocking_lr", "point_path", "linear", "whole_field_grating", "loom"]
        assert "arc" not in kinds
        assert "continuous_arc" not in kinds
        assert "waypoint_move" not in kinds
    finally:
        window.close()


def test_stimulus_designer_add_stimulus_starts_blank(qt_app):
    window = StimulusDesignerWindow()
    try:
        window._add_stimulus()
        stim = window.project.stimuli[-1]
        assert stim.primitives == []
    finally:
        window.close()


def test_stimulus_designer_grid_click_without_selected_primitive_does_not_create_path(qt_app):
    window = StimulusDesignerWindow()
    try:
        stim = window.project.stimuli[0]
        assert stim.primitives == []

        window._toggle_grid_point(0, 0)

        assert stim.primitives == []
    finally:
        window.close()


def test_stimulus_designer_grid_click_places_static_hold(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("static_hold")
        window._add_primitive()

        window._toggle_grid_point(0, 1)

        primitive = window.project.stimuli[0].primitives[0]
        assert primitive.kind == "static_hold"
        assert primitive.params["point"]["ring_index"] == 0
        assert primitive.params["point"]["point_index"] == 1
        assert primitive.params["duration_sec"] == pytest.approx(10.0)
    finally:
        window.close()


def test_stimulus_designer_grid_click_sets_grating_arrow(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("whole_field_grating")
        window._add_primitive()

        window._toggle_grid_point(0, 1)
        window._toggle_grid_point(0, 2)

        primitive = window.project.stimuli[0].primitives[0]
        points = primitive.params["points"]
        assert primitive.kind == "whole_field_grating"
        assert [(p["ring_index"], p["point_index"]) for p in points] == [(0, 1), (0, 2)]
    finally:
        window.close()


def test_stimulus_designer_grid_click_sets_loom_center(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("loom")
        window._add_primitive()

        window._toggle_grid_point(0, 3)

        primitive = window.project.stimuli[0].primitives[0]
        assert primitive.kind == "loom"
        assert primitive.params["point"]["ring_index"] == 0
        assert primitive.params["point"]["point_index"] == 3
    finally:
        window.close()


def test_stimulus_designer_grid_click_toggles_selected_point_path(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("point_path")
        window._add_primitive()

        window._toggle_grid_point(0, 1)
        window._toggle_grid_point(0, 2)
        window._toggle_grid_point(0, 1)

        points = window.project.stimuli[0].primitives[0].params["points"]
        assert [(p["ring_index"], p["point_index"]) for p in points] == [(0, 2)]
    finally:
        window.close()


def test_stimulus_designer_grid_click_sets_linear_start_and_end(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("linear")
        window._add_primitive()

        window._toggle_grid_point(0, 1)
        window._toggle_grid_point(0, 2)

        primitive = window.project.stimuli[0].primitives[0]
        points = primitive.params["points"]
        assert primitive.kind == "linear"
        assert [(p["ring_index"], p["point_index"]) for p in points] == [(0, 1), (0, 2)]
        assert primitive.params["movement_interval_ms"] == pytest.approx(700.0)
        assert primitive.params["mode"] == "bout"
        assert primitive.params["step_distance_cm"] == pytest.approx(0.2)
    finally:
        window.close()


def test_stimulus_designer_zoom_shortcuts_include_explicit_keys(qt_app):
    window = StimulusDesignerWindow()
    try:
        sequences = {
            shortcut.key().toString(QtGui.QKeySequence.SequenceFormat.PortableText)
            for shortcut in window.zoom_shortcuts
        }
        assert "Ctrl++" in sequences
        assert "Ctrl+=" in sequences
        assert "Meta++" in sequences
        assert "Meta+=" in sequences
        assert "Ctrl+-" in sequences
        assert "Meta+-" in sequences
        assert "Ctrl+_" in sequences
        assert "Meta+_" in sequences
        assert "Ctrl+0" in sequences
        assert "Meta+0" in sequences
    finally:
        window.close()


@pytest.mark.parametrize(
    ("key", "text", "modifier", "expected_zoom"),
    [
        (QtCore.Qt.Key.Key_Plus, "+", QtCore.Qt.KeyboardModifier.MetaModifier, 1.1),
        (QtCore.Qt.Key.Key_Equal, "=", QtCore.Qt.KeyboardModifier.ControlModifier, 1.1),
        (QtCore.Qt.Key.Key_Minus, "-", QtCore.Qt.KeyboardModifier.MetaModifier, 0.9),
        (QtCore.Qt.Key.Key_Underscore, "_", QtCore.Qt.KeyboardModifier.MetaModifier, 0.9),
        (QtCore.Qt.Key.Key_Minus, "−", QtCore.Qt.KeyboardModifier.MetaModifier, 0.9),
        (QtCore.Qt.Key.Key_0, "0", QtCore.Qt.KeyboardModifier.ControlModifier, 1.0),
    ],
)
def test_stimulus_designer_keypress_zoom_fallbacks(qt_app, key, text, modifier, expected_zoom):
    window = StimulusDesignerWindow()
    try:
        window.set_zoom(1.0)
        if key == QtCore.Qt.Key.Key_0:
            window.set_zoom(0.8)
        event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, key, modifier, text)

        window.keyPressEvent(event)

        assert event.isAccepted()
        assert window.zoom_factor == pytest.approx(expected_zoom)
    finally:
        window.close()


def test_stimulus_designer_shortcut_override_allows_cmd_minus_keypress(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.set_zoom(1.0)
        override = QtGui.QKeyEvent(
            QtCore.QEvent.Type.ShortcutOverride,
            QtCore.Qt.Key.Key_Minus,
            QtCore.Qt.KeyboardModifier.MetaModifier,
            "-",
        )
        keypress = QtGui.QKeyEvent(
            QtCore.QEvent.Type.KeyPress,
            QtCore.Qt.Key.Key_Minus,
            QtCore.Qt.KeyboardModifier.MetaModifier,
            "-",
        )

        assert window.eventFilter(window, override) is False
        assert override.isAccepted()
        assert window._handle_zoom_key_event(keypress)

        assert window.zoom_factor == pytest.approx(0.9)
    finally:
        window.close()


def test_stimulus_designer_zoom_resizes_window(qt_app, monkeypatch):
    window = StimulusDesignerWindow()
    try:
        target_size = QtCore.QSize(640, 380)
        monkeypatch.setattr(window, "_scaled_window_size", lambda: target_size)

        window.set_zoom(1.2)

        assert window.size() == target_size
    finally:
        window.close()


def test_stimulus_designer_scaled_window_size_is_capped_to_screen(qt_app, monkeypatch):
    window = StimulusDesignerWindow()
    try:
        monkeypatch.setattr(
            window,
            "_available_screen_geometry",
            lambda: QtCore.QRect(0, 0, 800, 600),
        )
        window.zoom_factor = 1.0

        assert window._scaled_window_size() == QtCore.QSize(800, 600)
    finally:
        window.close()


def test_stimulus_designer_uses_tooltips_instead_of_bottom_description(qt_app):
    window = StimulusDesignerWindow()
    try:
        assert window.key_edit.toolTip()
        assert window.canvas.toolTip()
        assert window.primitive_interval_spin.toolTip()
        assert not hasattr(window, "description_label")
        assert not hasattr(window, "description_timer")
    finally:
        window.close()


def test_stimulus_designer_right_panel_scrolls_and_groups_keep_rows(qt_app):
    window = StimulusDesignerWindow()
    try:
        assert isinstance(window.right_scroll, QtWidgets.QScrollArea)
        assert window.right_scroll.widget() is window.right_panel
        assert window.params_group.layout().rowCount() == 3
        assert window.grid_group.layout().rowCount() == 4
        assert window.params_group.minimumHeight() >= window.params_group.sizeHint().height()
        assert window.grid_group.minimumHeight() >= window.grid_group.sizeHint().height()
    finally:
        window.close()


def test_stimulus_designer_parameter_fields_follow_selected_primitive(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("static_hold")
        window._add_primitive()
        assert not window.duration_spin.isHidden()
        assert window.primitive_interval_spin.isHidden()
        assert window.primitive_mode_combo.isHidden()

        window.kind_combo.setCurrentText("point_path")
        window._add_primitive()
        assert window.duration_spin.isHidden()
        assert not window.primitive_interval_spin.isHidden()
        assert not window.primitive_mode_combo.isHidden()

        window.kind_combo.setCurrentText("linear")
        window._add_primitive()
        assert window.duration_spin.isHidden()
        assert not window.primitive_interval_spin.isHidden()
        assert not window.primitive_mode_combo.isHidden()
        assert not window.step_distance_spin.isHidden()

        window.kind_combo.setCurrentText("whole_field_grating")
        window._add_primitive()
        assert not window.duration_spin.isHidden()
        assert not window.bar_thickness_spin.isHidden()
        assert not window.speed_spin.isHidden()
        assert window.primitive_interval_spin.isHidden()

        window.kind_combo.setCurrentText("loom")
        window._add_primitive()
        assert not window.duration_spin.isHidden()
        assert not window.growth_speed_spin.isHidden()
        assert not window.max_radius_spin.isHidden()
        assert window.flicker_interval_spin.isHidden()
    finally:
        window.close()


def test_stimulus_designer_grating_defaults_match_requested_values(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("whole_field_grating")
        window._add_primitive()

        primitive = window.project.stimuli[0].primitives[0]
        assert primitive.params["duration_sec"] == pytest.approx(10.0)
        assert primitive.params["speed_cm_sec"] == pytest.approx(1.0)
    finally:
        window.close()


def test_stimulus_designer_timeline_rows_include_durations(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("static_hold")
        window._add_primitive()

        assert "total" in window.timeline_label.text()
        assert "static_hold" in window.primitive_list.item(0).text()
        assert "10.000 s" in window.primitive_list.item(0).text()
        assert "end 10.000 s" in window.primitive_list.item(0).text()
    finally:
        window.close()


def test_stimulus_designer_timeline_duration_updates_when_parameter_changes(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("static_hold")
        window._add_primitive()

        window.duration_spin.setValue(2.0)

        assert "2.000 s" in window.primitive_list.item(0).text()
        assert "end 2.000 s" in window.primitive_list.item(0).text()
        assert "2.000 s total" in window.timeline_label.text()
    finally:
        window.close()


def test_stimulus_designer_timeline_duration_updates_for_interval_changes(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("point_path")
        window._add_primitive()
        window._toggle_grid_point(0, 1)
        window._toggle_grid_point(0, 2)

        window.primitive_interval_spin.setValue(100.0)

        assert "0.200 s" in window.primitive_list.item(0).text()
        assert "0.200 s total" in window.timeline_label.text()
    finally:
        window.close()


def test_stimulus_designer_mirror_refreshes_point_primitive_editor_and_preview(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.kind_combo.setCurrentText("static_hold")
        window._add_primitive()
        window._toggle_grid_point(0, 1)
        before = window.project.stimuli[0].primitives[0].params["point"]["angle_deg"]

        window._mirror_stimulus()

        primitive = window.project.stimuli[0].primitives[0]
        assert primitive.params["point"]["angle_deg"] == pytest.approx(-before)
        assert str(-before) in window.primitive_json.toPlainText()
        assert "static_hold" in window.primitive_list.item(0).text()
        assert window.canvas.stimulus is window.project.stimuli[0]
    finally:
        window.close()


def test_stimulus_designer_calibration_summary_updates_from_project(qt_app):
    window = StimulusDesignerWindow()
    try:
        window.project.calibration.screen_width_px = 1000
        window.project.calibration.screen_height_px = 500
        window.project.calibration.screen_width_mm = 100.0
        window.project.calibration.screen_height_mm = 50.0
        window._refresh_fields()

        assert "1000 x 500 px" in window.calibration_summary_label.text()
        assert "10.0 x 5.0 cm" in window.calibration_summary_label.text()
        assert "0.10000 x 0.10000 mm/px" in window.calibration_summary_label.text()
    finally:
        window.close()


def test_preview_canvas_screen_rect_uses_calibrated_extent(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    canvas.project.calibration.screen_width_mm = 152.0
    canvas.project.calibration.screen_height_mm = 95.0

    rect = canvas._screen_rect()
    scale = canvas._scale()

    assert rect.width() / scale == pytest.approx(15.2)
    assert rect.height() / scale == pytest.approx(9.5)
    assert rect.left() > 0
    assert rect.right() < canvas.width()


def test_preview_canvas_visual_field_guides_use_requested_angles(qt_app, monkeypatch):
    canvas = PreviewCanvas()
    calls = []

    def fake_polygon(start_deg, end_deg, steps=32):
        calls.append((start_deg, end_deg))
        return QtGui.QPolygonF()

    monkeypatch.setattr(canvas, "_visual_field_polygon", fake_polygon)
    image = QtGui.QImage(100, 100, QtGui.QImage.Format.Format_ARGB32)
    painter = QtGui.QPainter(image)
    try:
        canvas._draw_visual_field_guides(painter)
    finally:
        painter.end()

    assert calls == [(-30.0, 30.0), (160.0, 200.0)]


def test_preview_canvas_visual_field_origin_tracks_fish_origin_after_zoom(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    canvas._set_preview_zoom(2.0, QtCore.QPointF(330.0, 230.0))

    polygon = canvas._visual_field_polygon(-30.0, 30.0)

    assert polygon[0] == canvas._to_widget(0.0, 0.0)
    assert polygon[0] != QtCore.QPointF(canvas.width() / 2.0, canvas.height() / 2.0)


def test_preview_canvas_stimulus_dot_color_is_translucent(qt_app):
    canvas = PreviewCanvas()

    assert canvas._stimulus_dot_color().alphaF() == pytest.approx(0.4)


def test_preview_canvas_avoidance_circle_uses_18_mm_radius(qt_app):
    canvas = PreviewCanvas()
    calls = []

    class FakePainter:
        def __init__(self):
            self.pen = None
            self.brush = None

        def setPen(self, pen):
            self.pen = pen

        def setBrush(self, brush):
            self.brush = brush

        def drawEllipse(self, center, radius_x, radius_y):
            calls.append((center, radius_x, radius_y, self.pen.color(), self.brush.color()))

    center = QtCore.QPointF(10.0, 20.0)
    canvas._draw_avoidance_circle(FakePainter(), center, scale=30.0)

    assert canvas.AVOIDANCE_RADIUS_CM == pytest.approx(1.8)
    assert calls[0][:3] == (center, pytest.approx(54.0), pytest.approx(54.0))
    assert calls[0][3] == QtGui.QColor("#b51f1f")
    assert calls[0][4].red() > calls[0][4].green()
    assert 0 < calls[0][4].alpha() < 255


def test_preview_canvas_petri_dish_uses_10_cm_diameter(qt_app):
    canvas = PreviewCanvas()
    calls = []

    class FakePainter:
        def __init__(self):
            self.brush = None

        def setPen(self, pen):
            pass

        def setBrush(self, brush):
            self.brush = brush

        def drawEllipse(self, center, radius_x, radius_y):
            calls.append((center, radius_x, radius_y, self.brush))

    center = QtCore.QPointF(10.0, 20.0)
    canvas._draw_petri_dish(FakePainter(), center, scale=30.0)

    assert canvas.PETRI_DISH_RADIUS_CM == pytest.approx(5.0)
    assert calls == [(center, pytest.approx(150.0), pytest.approx(150.0), QtCore.Qt.BrushStyle.NoBrush)]


def test_preview_canvas_zoom_clamps_to_full_screen(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)

    canvas._set_preview_zoom(0.1, QtCore.QPointF(200.0, 180.0))

    assert canvas.preview_zoom == pytest.approx(1.0)
    assert canvas.view_center_cm.x() == pytest.approx(0.0)
    assert canvas.view_center_cm.y() == pytest.approx(0.0)


def test_preview_canvas_zoom_preserves_cursor_coordinate(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    anchor = QtCore.QPointF(330.0, 230.0)
    before = canvas._widget_to_cm(anchor)

    canvas._set_preview_zoom(2.0, anchor)
    after = canvas._widget_to_cm(anchor)

    assert canvas.preview_zoom == pytest.approx(2.0)
    assert after.x() == pytest.approx(before.x())
    assert after.y() == pytest.approx(before.y())


def test_preview_canvas_grid_hit_testing_works_after_zoom(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    canvas._set_preview_zoom(2.0, QtCore.QPointF(canvas.width() / 2.0, canvas.height() / 2.0))

    ring_index, point_index, position = canvas._grid_point_positions()[0]

    assert canvas._nearest_grid_point(position) == (ring_index, point_index)


def test_preview_canvas_right_drag_pan_changes_view_center_when_zoomed(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    canvas._set_preview_zoom(2.0, QtCore.QPointF(canvas.width() / 2.0, canvas.height() / 2.0))

    canvas._pan_by_pixels(QtCore.QPointF(40.0, -20.0))

    assert canvas.view_center_cm.x() < 0.0
    assert canvas.view_center_cm.y() < 0.0


def test_preview_canvas_pan_is_clamped_to_screen_bounds(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    canvas._set_preview_zoom(8.0, QtCore.QPointF(canvas.width() / 2.0, canvas.height() / 2.0))

    canvas._pan_by_pixels(QtCore.QPointF(-100000.0, 100000.0))

    screen_width_cm, screen_height_cm = canvas._screen_size_cm()
    viewport_width_cm = canvas.width() / canvas._scale()
    viewport_height_cm = canvas.height() / canvas._scale()
    assert canvas.view_center_cm.x() == pytest.approx((screen_width_cm - viewport_width_cm) / 2.0)
    assert canvas.view_center_cm.y() == pytest.approx((screen_height_cm - viewport_height_cm) / 2.0)


def test_preview_canvas_pan_at_full_screen_zoom_stays_centered(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)

    canvas._pan_by_pixels(QtCore.QPointF(100.0, -100.0))

    assert canvas.preview_zoom == pytest.approx(1.0)
    assert canvas.view_center_cm.x() == pytest.approx(0.0)
    assert canvas.view_center_cm.y() == pytest.approx(0.0)


def test_preview_canvas_right_mouse_press_starts_pan_without_selecting(qt_app):
    canvas = PreviewCanvas()
    canvas.resize(560, 520)
    emitted = []
    canvas.grid_point_clicked.connect(lambda ring, point: emitted.append((ring, point)))
    event = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonPress,
        QtCore.QPointF(canvas.width() / 2.0, canvas.height() / 2.0),
        QtCore.Qt.MouseButton.RightButton,
        QtCore.Qt.MouseButton.RightButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
    )

    canvas.mousePressEvent(event)

    assert canvas.is_panning
    assert event.isAccepted()
    assert emitted == []
