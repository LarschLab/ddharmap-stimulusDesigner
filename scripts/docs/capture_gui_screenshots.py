from __future__ import annotations

import os
import sys
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from PyQt6 import QtCore, QtWidgets
except ImportError as exc:
    raise SystemExit(
        "PyQt6 is required to capture GUI screenshots. "
        "Run this inside the documented Conda environment."
    ) from exc

from scripts.stimuli.stimulus_designer_app import StimulusDesignerWindow


OUTPUT_DIR = REPO_ROOT / "docs" / "images"


def _save_widget(widget: QtWidgets.QWidget, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pixmap = widget.grab()
    path = OUTPUT_DIR / name
    if not pixmap.save(str(path)):
        raise RuntimeError(f"Could not save screenshot: {path}")
    print(f"saved {path.relative_to(REPO_ROOT)}")


def _prepare_sample_window() -> StimulusDesignerWindow:
    QtCore.QSettings(
        StimulusDesignerWindow.SETTINGS_ORG,
        StimulusDesignerWindow.SETTINGS_APP,
    ).clear()
    window = StimulusDesignerWindow()
    window.set_zoom(1.0)
    window.resize_to_scaled_content()
    window.show()
    QtWidgets.QApplication.processEvents()

    window.kind_combo.setCurrentText("static_hold")
    window._add_primitive()
    window._toggle_grid_point(0, 1)

    window.kind_combo.setCurrentText("bezier_arc")
    window._add_primitive()
    window._toggle_grid_point(0, 2)
    window._toggle_grid_point(0, 4)
    window._toggle_grid_point(1, 3)

    window.frame_slider.setValue(0)
    QtWidgets.QApplication.processEvents()
    return window


def main() -> int:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    window = _prepare_sample_window()
    try:
        _save_widget(window, "gui-main-window.png")
        _save_widget(window.stimulus_list, "gui-add-stimulus.png")
        _save_widget(window.right_panel, "gui-primitive-editor.png")
        _save_widget(window.canvas, "gui-preview-guides.png")
        _save_widget(window.file_actions_widget, "gui-export-launch.png")
    finally:
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
