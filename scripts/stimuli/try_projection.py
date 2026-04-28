import argparse
import time
from pathlib import Path

import pandas as pd


DEFAULT_STIMULI_PATH = Path(r"\\nasdcsr.unil.ch\RECHERCHE\FAC\FBM\CIG\jlarsch\default\D2c\Alejandro\2p\Exp_6_mapping_positions_retina")


def _dot_names_from_columns(columns):
    names = []
    for column in columns:
        if not column.endswith("_x"):
            continue
        name = column.rsplit("_", 1)[0]
        if name.startswith("dot") and name[3:].isdigit():
            names.append(name)
    return sorted(set(names))


def run_projection(
    stimuli_path,
    screen_index=0,
    physical_width_cm=59.0,
    viewing_distance_cm=20.0,
    pause_between_sec=1.0,
):
    from psychopy import core, event, monitors, visual
    import pyglet

    stimuli_path = Path(stimuli_path)
    stimulus_files = sorted(stimuli_path.glob("*_trajectory.csv"))
    if not stimulus_files:
        raise FileNotFoundError(f"No *_trajectory.csv files found in {stimuli_path}")

    display = pyglet.canvas.get_display()
    screens = display.get_screens()
    resolution = (screens[screen_index].width, screens[screen_index].height)
    print(f"Screen {screen_index} resolution: {resolution}")

    monitor = monitors.Monitor(name="auto_monitor")
    monitor.setWidth(physical_width_cm)
    monitor.setDistance(viewing_distance_cm)
    monitor.setSizePix(resolution)
    monitor.save()

    win = visual.Window(
        size=resolution,
        units="cm",
        monitor=monitor,
        fullscr=True,
        screen=screen_index,
        color="red",
    )
    timing_log = []

    for csv_file in stimulus_files:
        print(f"Playing: {csv_file.name}")
        df = pd.read_csv(csv_file)
        stim_start = time.time()
        print(stim_start)
        dot_names = _dot_names_from_columns(df.columns)
        dots = {}
        for dot_name in dot_names:
            dots[dot_name] = visual.Circle(
                win=win,
                radius=1,
                fillColor="black",
                lineColor="black",
                units="cm",
            )
        grating = None
        if "grating_active" in df.columns:
            grating = visual.GratingStim(
                win=win,
                tex="sqr",
                mask=None,
                units="cm",
                size=(physical_width_cm * 3.0, physical_width_cm * 3.0),
                interpolate=False,
                contrast=1.0,
            )
        loom = None
        if "loom_active" in df.columns:
            loom = visual.Circle(
                win=win,
                radius=1,
                fillColor="black",
                lineColor="black",
                units="cm",
            )

        for _, row in df.iterrows():
            if grating is not None and row.get("grating_active", 0) > 0:
                thickness = max(0.001, float(row.get("grating_bar_thickness_cm", 0.5)))
                cycle_width = thickness * 2.0
                grating.pos = (float(row.get("grating_x", 0.0)), float(row.get("grating_y", 0.0)))
                grating.ori = float(row.get("grating_direction_deg", 0.0)) + 90.0
                grating.sf = 1.0 / cycle_width
                grating.phase = (float(row.get("grating_phase_cm", 0.0)) / cycle_width, 0.0)
                grating.draw()
            for dot_name, dot in dots.items():
                x, y = row[f"{dot_name}_x"], row[f"{dot_name}_y"]
                radius = row.get(f"{dot_name}_radius", 0.4)
                if radius > 0:
                    dot.pos = (x, y)
                    dot.radius = radius
                    dot.draw()
            if loom is not None and row.get("loom_active", 0) > 0:
                radius = float(row.get("loom_radius", 0.0))
                if radius > 0:
                    loom.pos = (float(row.get("loom_x", 0.0)), float(row.get("loom_y", 0.0)))
                    loom.radius = radius
                    loom.draw()
            win.flip()

            if "escape" in event.getKeys():
                win.close()
                core.quit()

        stim_end = time.time()
        print(stim_end)
        timing_log.append(
            {
                "stimulus_file": csv_file.name,
                "start_time_unix": stim_start,
                "end_time_unix": stim_end,
                "duration_sec": round(stim_end - stim_start, 3),
            }
        )

        core.wait(pause_between_sec)

    win.close()
    core.quit()

    timing_df = pd.DataFrame(timing_log)
    timing_df.to_csv(stimuli_path / "stimulus_timing_log.csv", index=False)
    print("Timing log saved.")


def _parse_args():
    parser = argparse.ArgumentParser(description="Play generated stimulus trajectory CSV files with PsychoPy.")
    parser.add_argument("--stimuli-path", type=Path, default=DEFAULT_STIMULI_PATH)
    parser.add_argument("--screen-index", type=int, default=0)
    parser.add_argument("--physical-width-cm", type=float, default=59.0)
    parser.add_argument("--viewing-distance-cm", type=float, default=20.0)
    parser.add_argument("--pause-between-sec", type=float, default=1.0)
    return parser.parse_args()


def main():
    args = _parse_args()
    run_projection(
        stimuli_path=args.stimuli_path,
        screen_index=args.screen_index,
        physical_width_cm=args.physical_width_cm,
        viewing_distance_cm=args.viewing_distance_cm,
        pause_between_sec=args.pause_between_sec,
    )


if __name__ == "__main__":
    main()
