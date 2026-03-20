# Gravity Studio

A premium-styled orbital simulation MVP built with Python and Pygame.

## Features

- Central star with layered glow and subtle pulse
- Multiple planets with distinct size, speed, orbit radius, and material treatment
- Elegant orbit rings and procedural background star field
- Click selection with a floating info card
- Smooth mouse-wheel zoom
- Pause/resume, reset, and add-planet controls
- Clean modular structure for simulation, rendering, and UI

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
- `Add Planet`: append a new stylized body to the system
- `Pause` / `Resume`: stop or continue orbital motion
- `Reset`: restore the original system state

## Project layout

- `main.py`: simple desktop entry point
- `orbit_sim/app.py`: app orchestration and input flow
- `orbit_sim/simulation.py`: orbital state and planet generation
- `orbit_sim/rendering.py`: scene rendering
- `orbit_sim/ui.py`: info panel, HUD, and controls
- `orbit_sim/background.py`: procedural star field
