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
- Short label: Stimulus designer grating and loom primitives
- Slice goal: Add whole-field grating and loom primitives to the point-grid GUI while keeping dot trajectory exports compatible.
- Passes completed: Added generator rows for grating/loom visual channels, GUI primitive defaults and point placement, preview drawing, PsychoPy playback support, active-column timing extraction, and focused tests.
- What changed: `src/stimulus_designer.py` now defaults static periods to 10 s and emits `grating_*`/`loom_*` columns for the new primitives. `scripts/stimuli/stimulus_designer_app.py` adds the primitives, parameter fields, grid interactions, a rotated fish icon with eyes, and preview rendering. `scripts/stimuli/try_projection.py` draws gratings/looms and restricts dot detection to `dotN_*` columns. `src/stimuli_timeline.py` recognizes `*_active` visual onset columns.
- What remains broken: PsychoPy rendering still needs a manual projector smoke test in the real display environment.
- Remaining in-slice work: Confirm grating orientation and perceived motion direction on the stimulus display.
- Next likely breakpoint: PsychoPy `GratingStim` orientation conventions may need a sign/90-degree adjustment after visual inspection.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`; GUI tests skip where PyQt6 is unavailable.

- Date: 2026-04-28
- Short label: Stimulus designer point-grid primitive editor
- Slice goal: Make GUI primitive authoring point-grid based and remove redundant primitive choices from new GUI workflows.
- Passes completed: Added blank-stimulus defaults, selected-primitive grid clicks, dynamic per-primitive parameter fields, and empty-export validation.
- What changed: `src/stimulus_designer.py` now supports grid-point params for static hold, flicker, rocking, and rocking_lr, returns empty dataframes for blank stimuli, and rejects empty exports. `scripts/stimuli/stimulus_designer_app.py` hides arc/continuous_arc/waypoint_move from the add menu, stops auto-creating point_path on grid clicks, moves Interval/Mode into `Stimulus parameters`, and starts added stimuli without a default static hold.
- What remains broken: GUI tests still skip where PyQt6 is unavailable.
- Remaining in-slice work: Manual GUI smoke test in a PyQt6 environment to confirm parameter visibility and click placement feel right.
- Next likely breakpoint: Old saved projects can still contain legacy arc/continuous_arc/waypoint_move primitives; they remain supported by backend generation but do not have structured GUI parameter rows.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`; install/activate PyQt6 to exercise GUI tests instead of skip behavior.

- Date: 2026-04-28
- Short label: Stimulus designer point grid defaults
- Slice goal: Update the GUI's startup point-grid defaults for custom path design.
- Passes completed: Changed `GridSettings` defaults and added a focused owner-module test for the startup values.
- What changed: New projects now start with first ring radius 1.00 cm, ring spacing 0.40 cm, 12 points per ring, and 70 ms point-path interval.
- What remains broken: Nothing known.
- Remaining in-slice work: Manual GUI check in an environment with PyQt6 installed.
- Next likely breakpoint: Existing saved designer projects keep their serialized grid settings when loaded.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`; GUI tests skip when PyQt6 is unavailable.

- Date: 2026-04-28
- Short label: Stimulus designer zoom shortcut and window resize fixes
- Slice goal: Make Cmd/Ctrl zoom shortcuts reliable and keep the outer PyQt window sized to the scaled GUI content.
- Passes completed: Added active-window shortcut override handling and direct keypress fallback handling for Cmd/Ctrl plus, equals, minus, underscore, unicode minus, and zero; made all zoom changes resize the main window; capped resize targets to the current screen's available geometry; added GUI tests for keypress fallback, Cmd-minus shortcut override, and resize bounds.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now resizes after `set_zoom()`, registers explicit Ctrl and Meta shortcuts with application shortcut context, and recognizes zoom shortcuts even when native `QShortcut` sequence matching differs by platform, keyboard layout, or focused child widget. `tests/test_stimulus_designer_app.py` covers the new behavior when PyQt6 is installed.
- What remains broken: PyQt6 is not installed in the current execution environment, so GUI-specific tests may still skip here.
- Remaining in-slice work: Manual macOS smoke test in the PyQt6 environment to confirm native Cmd +, Cmd -, and Cmd 0 behavior with a visible window.
- Next likely breakpoint: Qt may report keyboard keys differently on non-US layouts, but both `+` and `=` are now accepted for zoom in.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`; install/activate PyQt6 to exercise GUI tests instead of skip behavior.

- Date: 2026-04-28
- Short label: Stimulus designer GUI scaling and layout fixes
- Slice goal: Make the PyQt stimulus designer usable on smaller screens with proportional app zoom, reliable macOS zoom shortcuts, hover help boxes, and non-compressed right-panel fields.
- Passes completed: Added whole-app scaling wrapper; added explicit zoom shortcuts; replaced bottom description label with native Qt tooltips; moved the right-side editor panel into a vertical scroll area; added optional PyQt GUI tests.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now wraps the fixed design-size UI in `ScaledWidgetView`, auto-fits at startup, supports `Ctrl/Cmd +`, `Ctrl/Cmd =`, `Ctrl/Cmd -`, and `Ctrl/Cmd 0`, uses `setToolTip()` for registered descriptions, and keeps Global / calibration plus Point grid group boxes at natural height inside a scrollable right panel. `tests/test_stimulus_designer_app.py` covers the GUI behavior when PyQt6 is installed and skips otherwise.
- What remains broken: PyQt6 is not installed in the current execution environment, so GUI-specific tests were not exercised here beyond import-skip behavior.
- Remaining in-slice work: Manual smoke test in an environment with PyQt6 on macOS to confirm native `Cmd +`/`Cmd =` shortcut behavior and tooltip placement.
- Next likely breakpoint: Qt shortcut sequence differences across keyboard layouts or platform-specific tooltip behavior inside the scaled `QGraphicsView`.
- Rerun implications: `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py` currently reports `10 passed, 1 skipped` in this environment; install/activate PyQt6 to exercise the GUI tests.
