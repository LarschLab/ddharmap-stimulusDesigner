# Current State

Purpose: collect practical caveats for the stimulus-designer-only repo.

- The repository now focuses on stimulus design, trajectory CSV export, and PsychoPy playback.
- The main GUI is `scripts/stimuli/stimulus_designer_app.py`.
- Reusable project, primitive, geometry, and export logic lives in `src/stimulus_designer.py`.
- `scripts/stimuli` contains historical spelling variants such as `trayectory`; preserve existing paths/names unless a migration is explicitly requested.
- PsychoPy is optional for design/export work and required only for live fullscreen playback.
- GUI tests skip in environments without PyQt6.
- Generated stimulus output folders such as `stim_projects/` are not source-of-truth code.
