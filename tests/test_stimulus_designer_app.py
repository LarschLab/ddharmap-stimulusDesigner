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
        assert window.canvas.df.empty is False
        assert window.stimulus_list.count() == len(window.project.stimuli)
        assert window.scaled_view.minimumWidth() == 1
        assert window.scaled_view.minimumHeight() == 1
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
        assert window.interval_spin.toolTip()
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
        assert window.grid_group.layout().rowCount() == 6
        assert window.params_group.minimumHeight() >= window.params_group.sizeHint().height()
        assert window.grid_group.minimumHeight() >= window.grid_group.sizeHint().height()
    finally:
        window.close()
