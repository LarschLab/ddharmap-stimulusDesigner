# Stimulus Stage Map

Purpose: preserve stimulus-generation and projection semantics.

Use this file when changing trajectory generators, stimulus configs, projection playback, or generated CSV contracts.

## End-to-end stages

1. JSON config: package/trajectory JSON files under `scripts/stimuli/` define stimulus names and parameters.
2. Trajectory generation: generator scripts create per-stimulus `*_trajectory.csv` files with position/radius columns and parameter metadata.
3. Metadata/duration output: scripts write `parameters/experiment_parameters.csv` and duration summaries when supported.
4. Projection playback: `try_projection.py` loads `*_trajectory.csv`, opens PsychoPy fullscreen playback, draws dots frame by frame, and writes `stimulus_timing_log.csv`.
5. Calcium consumption: `src/stimuli_timeline.py` later reads generated trajectory CSVs to infer timing for alignment.

## Concept ownership

- Geometry, angle ranges, speed, static period, flicker/rocking semantics: generator scripts and JSON configs.
- Display hardware, screen, monitor, frame playback, escape handling, timing log: `try_projection.py`.
- Downstream movement timing interpretation: `src/stimuli_timeline.py`.

## Navigation notes

Do not patch calcium notebooks to compensate for malformed trajectory CSVs. Fix trajectory generation when columns or frame counts are wrong.
