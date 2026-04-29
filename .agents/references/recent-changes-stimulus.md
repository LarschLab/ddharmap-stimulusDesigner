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

## 2026-04-29

- Date: 2026-04-29
- Short label: Stimulus designer 2 cm first ring default
- Slice goal: Start new GUI projects with the first placement ring 2 cm from the fish.
- Passes completed: Updated the `GridSettings` default and matching backend/GUI startup tests.
- What changed: New stimulus designer projects now use first ring radius 2.00 cm; existing saved projects keep their serialized grid setting.
- What remains broken: Nothing known.
- Remaining in-slice work: None.
- Next likely breakpoint: Existing saved projects may still open with older 1.00 cm first-ring values until edited.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`.

- Date: 2026-04-29
- Short label: Stimulus designer avoidance fill and petri dish guide
- Slice goal: Emphasize the near-fish avoidance area and show the 10 cm dish boundary in the calibrated preview.
- Passes completed: Filled the 18 mm avoidance circle with translucent red, added a fish-centered 10 cm diameter petri dish guide, and updated GUI tests.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now draws preview-only avoidance and petri dish guides without changing trajectory exports or projection playback.
- What remains broken: Manual visual confirmation is still useful because the 10 cm dish slightly exceeds the current 9.5 cm calibrated screen height.
- Remaining in-slice work: Confirm the red fill opacity is strong enough without obscuring grid/stimulus details.
- Next likely breakpoint: If the exact dish center differs from fish origin in a real setup, the guide may need an offset setting.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`.

- Date: 2026-04-29
- Short label: Stimulus designer full timeline mirror and avoidance guide
- Slice goal: Mirror all selected-stimulus timeline primitives consistently and show a fish-centered near-field avoidance cue.
- Passes completed: Consolidated point mirroring across primitive params, refreshed GUI state after mirror, added an 18 mm preview-only avoidance circle, and added focused backend/GUI tests.
- What changed: `src/stimulus_designer.py` now mirrors any primitive `point`/`points` payload while preserving timeline order. `scripts/stimuli/stimulus_designer_app.py` draws an 18 mm radius guide around the fish and refreshes timeline/editor/preview state after mirror.
- What remains broken: GUI tests still skip where PyQt6 is unavailable; manual visual confirmation of the circle styling is still useful.
- Remaining in-slice work: Confirm the 18 mm guide reads clearly on the actual workstation display.
- Next likely breakpoint: The guide radius may need to become configurable once the exact behavioral distance is known.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`.

## 2026-04-28

- Date: 2026-04-28
- Short label: Stimulus designer right-drag preview pan
- Slice goal: Let users navigate a zoomed preview field without changing stimulus coordinates or left-click point selection.
- Passes completed: Added right-button pan state, pan clamping through the existing calibrated screen bounds, cursor feedback, tooltip text, and focused GUI tests.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now supports right-click drag panning in `PreviewCanvas`; left click remains point selection and full-screen zoom remains centered.
- What remains broken: PyQt GUI tests still skip where PyQt6 is unavailable; manual GUI check is needed for drag feel and cursor behavior.
- Remaining in-slice work: Confirm right-drag pan feels natural with the actual mouse/trackpad setup.
- Next likely breakpoint: Drag direction may need inversion if users expect map-style panning instead of viewport-center panning.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q` in an environment with PyQt6 to exercise GUI tests.

- Date: 2026-04-28
- Short label: Stimulus designer preview transform and live durations
- Slice goal: Keep zoomed preview guide geometry aligned, make actual stimulus dots translucent, and update primitive duration rows immediately after parameter edits.
- Passes completed: Switched fish/ring/field guide origins to the transformed fish origin, changed preview stimulus dot color to 40% alpha, added live timeline row refresh, and added focused GUI tests.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now keeps fish, concentric rings, binocular field, blind spot, grid, and stimulus preview in one zoomed coordinate system. Timeline duration/end rows refresh after primitive parameter edits, grid point changes, and global timing changes.
- What remains broken: PyQt GUI tests still skip where PyQt6 is unavailable; manual visual check is needed for the zoomed preview alignment.
- Remaining in-slice work: Confirm in the GUI that fish/field overlays remain visually locked to grid points while wheel zooming.
- Next likely breakpoint: If selected grid dots still feel visually heavy on top of the intended start point, reduce their radius rather than their opacity.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q` in an environment with PyQt6 to exercise the GUI tests.

- Date: 2026-04-28
- Short label: Stimulus designer calibration summary and preview zoom
- Slice goal: Make screen calibration read-only in the GUI and support precise point selection by zooming the preview around the cursor.
- Passes completed: Removed editable screen dimension fields, added a calibration summary label, added cursor-centered preview-only wheel zoom with full-screen minimum zoom, and covered the behavior with focused GUI tests.
- What changed: `scripts/stimuli/stimulus_designer_app.py` now shows calibrated screen dimensions and pixel scale as read-only text, while `PreviewCanvas` maintains its own zoom/view center independent of whole-app keyboard zoom.
- What remains broken: Manual PyQt visual check still needed for mouse-wheel feel on the real GUI.
- Remaining in-slice work: Confirm cursor-centered wheel zoom is comfortable for selecting dense grid points on the actual display/workstation.
- Next likely breakpoint: Trackpad wheel deltas may feel too sensitive or too slow; adjust `PREVIEW_ZOOM_STEP` if manual use suggests it.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`.

- Date: 2026-04-28
- Short label: Stimulus designer calibrated screen preview
- Slice goal: Match the GUI defaults to the measured projector calibration and show the full stimulus screen with fish-relative visual field guides.
- Passes completed: Updated calibration defaults, exposed height calibration fields, fit preview scaling to the calibrated physical screen rectangle, clipped visual previews to the screen, and added binocular/blind-spot overlays.
- What changed: `src/stimulus_designer.py` now defaults to 1280 x 800 px projected over 15.2 x 9.5 cm. `scripts/stimuli/stimulus_designer_app.py` now shows width and height calibration controls, draws the full calibrated screen extent, and overlays fish-relative ±30 degree binocular and ±160 degree blind-spot guides.
- What remains broken: Projection playback itself is unchanged; field guides are GUI-only and need a manual visual check in the PyQt GUI.
- Remaining in-slice work: Manually confirm screen boundary and guide orientation against the real projection/fish-facing convention.
- Next likely breakpoint: If the measured projected height differs from the inferred 9.5 cm, update the default height and saved project calibration.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`.

- Date: 2026-04-28
- Short label: Stimulus designer linear primitive and GUI duration updates
- Slice goal: Add linear point-grid motion, update grating/bout defaults, and make timeline/preview behavior clearer.
- Passes completed: Added backend linear trajectory rows, GUI primitive controls, timeline duration summaries, grating-under-fish preview layering, translucent selected grid points, and focused tests.
- What changed: `src/stimulus_designer.py` now defaults bout intervals to 700 ms, supports `linear` primitives with step-distance overshoot semantics, mirrors linear points, and exposes primitive duration summary helpers. `scripts/stimuli/stimulus_designer_app.py` adds the linear primitive, 10 s / 1 cm/s grating defaults, per-primitive and cumulative timeline durations, translucent selected grid dots, and grating preview drawing beneath the fish icon.
- What remains broken: GUI-specific tests still skip where PyQt6 is unavailable.
- Remaining in-slice work: Manual GUI smoke test in a PyQt6 environment to confirm the timeline label, linear point selection, and grating layering visually.
- Next likely breakpoint: Saved projects with serialized 70 ms intervals keep that value until edited; new primitives use 700 ms.
- Rerun implications: Run `python -m pytest tests/test_stimulus_designer.py tests/test_stimulus_designer_app.py -q`; run a manual PyQt6 GUI check for visual layering.

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
