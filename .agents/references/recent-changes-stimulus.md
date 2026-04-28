# Recent Changes: Stimulus Workflow

Append meaningful handoffs using this template.

## Template

- Date:
- Short label:
- Slice goal:
- Passes completed:
- What changed:
- What remains broken:
- Remaining in-slice work:
- Next likely breakpoint:
- Rerun implications:

## 2026-04-28

- Date: 2026-04-28
- Short label: Stimulus designer GUI scaling and layout fixes
- Slice goal: Make the PyQt stimulus designer usable on smaller screens with proportional app zoom, reliable macOS zoom shortcuts, hover help boxes, and non-compressed right-panel fields.
- Passes completed: Added whole-app scaling wrapper; added explicit zoom shortcuts; replaced bottom description label with native Qt tooltips; moved the right-side editor panel into a vertical scroll area; added optional PyQt GUI tests.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now wraps the fixed design-size UI in `ScaledWidgetView`, auto-fits at startup, supports `Ctrl/Cmd +`, `Ctrl/Cmd =`, `Ctrl/Cmd -`, and `Ctrl/Cmd 0`, uses `setToolTip()` for registered descriptions, and keeps Global / calibration plus Point grid group boxes at natural height inside a scrollable right panel. `tests/test_stimulus_designer_app.py` covers the GUI behavior when PyQt6 is installed and skips otherwise.
- What remains broken: PyQt6 is not installed in the current execution environment, so GUI-specific tests were not exercised here beyond import-skip behavior.
- Remaining in-slice work: Manual smoke test in an environment with PyQt6 on macOS to confirm native `Cmd +`/`Cmd =` shortcut behavior and tooltip placement.
- Next likely breakpoint: Qt shortcut sequence differences across keyboard layouts or platform-specific tooltip behavior inside the scaled `QGraphicsView`.
- Rerun implications: `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py` currently reports `10 passed, 1 skipped` in this environment; install/activate PyQt6 to exercise the GUI tests.
