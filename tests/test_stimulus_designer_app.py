import os

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 is not installed")
QtGui = pytest.importorskip("PyQt6.QtGui", reason="PyQt6 is not installed")
QtCore = pytest.importorskip("PyQt6.QtCore", reason="PyQt6 is not installed")

from scripts.stimuli.stimulus_designer_app import StimulusDesignerWindow  # noqa: E402


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
        assert window.project.grid_settings.first_ring_radius_cm == pytest.approx(1.0)
        assert window.project.grid_settings.ring_spacing_cm == pytest.approx(0.4)
        assert window.project.grid_settings.points_per_ring == 12
        assert window.project.grid_settings.movement_interval_ms == pytest.approx(70.0)
        assert window.grid_first_radius_spin.value() == pytest.approx(1.0)
        assert window.grid_spacing_spin.value() == pytest.approx(0.4)
        assert window.grid_points_spin.value() == 12
        assert window.project.grid_settings.movement_interval_ms == pytest.approx(70.0)
    finally:
        window.close()


def test_stimulus_designer_add_menu_hides_redundant_primitives(qt_app):
    window = StimulusDesignerWindow()
    try:
        kinds = [window.kind_combo.itemText(i) for i in range(window.kind_combo.count())]
        assert kinds == ["static_hold", "flicker", "rocking", "rocking_lr", "point_path", "whole_field_grating", "loom"]
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
        assert window.params_group.layout().rowCount() == 4
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
