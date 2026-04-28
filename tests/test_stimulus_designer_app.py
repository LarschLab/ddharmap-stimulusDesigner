import os

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

QtWidgets = pytest.importorskip("PyQt6.QtWidgets", reason="PyQt6 is not installed")
QtGui = pytest.importorskip("PyQt6.QtGui", reason="PyQt6 is not installed")

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
        assert "Ctrl+-" in sequences
        assert "Ctrl+0" in sequences
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
