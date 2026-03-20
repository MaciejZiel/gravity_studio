# Gravity Studio: Solar System

A fullscreen, astronomy-inspired Solar System visualization built with Python and Pygame.

## Features

- Fullscreen launch with responsive scaling for large displays
- Real Solar System dataset with the Sun and all 8 planets in correct order
- Compressed but realistic-inspired orbit scaling for readability
- Minimal orbit lines, restrained solar glow, and subdued planet rendering
- Saturn ring rendering with separate front and back layers
- Planet labels, zoom, pause/resume, orbit toggle, label toggle, and scale mode toggle
- Selected planet info card with radius, distance, orbital period, and a short fact
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
- `Mouse wheel`: zoom in or out
- `Pause` / `Resume`: stop or continue orbital motion
- `Orbits`: show or hide orbit lines
- `Labels`: show or hide planet labels
- `Scale`: switch between compressed and expanded distance scaling
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
