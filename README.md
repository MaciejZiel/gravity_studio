# Gravity Studio: Solar System

A fullscreen, astronomy-inspired Solar System visualization built with Python and Pygame.

## Features

- Fullscreen launch with responsive scaling for large displays
- Real Solar System dataset with the Sun and all 8 planets in correct order
- Compressed but realistic-inspired orbit scaling for readability, with alternate scale mode
- Scene presets for `System`, `Inner`, `Outer`, and planet `Focus` views
- Textured planet focus close-up with a spinning shaded sphere built from full-surface planet maps
- Timeline scrubber with simulation date and `1x / 10x / 100x / 1000x` time controls
- Live local clock overlay plus per-focus timestamp readout with hour, minute, and second precision
- One-click `Live` mode that syncs planet positions to the current time and runs in real time
- Minimal orbit lines, cinematic focus vignette, and restrained solar rendering
- Richer planet treatment with surface cues, atmospheres, and Saturn ring shadowing
- Adaptive planet labels that respond to scene and zoom level
- Selected planet info card with radius, distance, orbital period, fact, and Earth comparison
- Screenshot capture and hide-UI presentation mode
- Modular separation between data, simulation, camera, rendering, background, and UI

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

You can also run it as a module:

```bash
python -m orbit_sim
```

## Controls

- `Left click`: select a planet
- `Left click` on a planet: jump into focus and show the rotating close-up preview
- `Left drag` on the focus sphere: rotate the selected planet manually
- `Mouse wheel`: zoom in or out
- `Q / W / E`: switch between `System`, `Inner`, and `Outer` scenes
- `F`: jump to focus view for the selected planet
- `1 / 2 / 3 / 4`: switch time speed presets
- `Timeline scrubber`: drag to set the simulation date
- `Live`: sync the Solar System to the current moment and run at `1:1` real time
- `Pause` / `Resume`: stop or continue orbital motion
- `Orbits`: show or hide orbit lines
- `Labels`: show or hide planet labels
- `Scale`: switch between compressed and expanded distance scaling
- `H`: hide or reveal the UI
- `P`: capture a screenshot into `screenshots/`
- `Reset`: restore the original system state

## Project layout

- `main.py`: simple desktop entry point
- `orbit_sim/app.py`: app orchestration and input flow
- `orbit_sim/solar_system.py`: Solar System dataset and planet metadata
- `orbit_sim/simulation.py`: orbital motion state
- `orbit_sim/camera.py`: responsive scene layout, zoom, and distance scaling
- `orbit_sim/rendering.py`: scene rendering
- `orbit_sim/ui.py`: info panel, HUD, and controls
- `orbit_sim/background.py`: procedural star field
