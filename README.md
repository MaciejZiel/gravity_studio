<p align="center">
  <img src="screenshots/gravity-studio-20260321-000517-clean.png" alt="Gravity Studio Solar System screenshot" width="100%" />
</p>

<h1 align="center">Gravity Studio: Solar System</h1>

<p align="center">
  A fullscreen, astronomy-inspired Solar System visualization built with <code>Python</code> and <code>Pygame</code>.
</p>

<p align="center">
  Real planets. Cinematic focus views. Responsive fullscreen rendering. Portfolio-grade presentation.
</p>

## Overview

Gravity Studio is a premium-style desktop visualization of our Solar System designed for large displays.  
It blends a compressed but credible scale model with responsive camera choreography, real planet metadata, cinematic tours, a live time mode, and a textured focus renderer for close-up planet inspection.

This is not a toy orbit demo. The project is built to feel closer to a compact astronomy product: restrained UI, calmer motion, modern fullscreen composition, and a codebase organized for further expansion.

## Highlights

- Fullscreen-by-default desktop app with responsive layout and scaling
- Real Solar System dataset with the Sun plus all 8 planets in the correct order
- Scene presets for `System`, `Inner`, `Giants`, `Outer`, and planet `Focus` views
- Live `1:1` time mode, guided tours, presentation mode, date jumps, and time-speed controls
- Textured planet close-ups with rotating shaded spheres, seasonal lighting, Earth clouds, night lights, aurora cues, and Saturn rings
- Mission overlays, major moons, adaptive labels, sky-context strip, screenshots, local settings persistence, and ambient audio

## What It Includes

- Responsive fullscreen composition for large monitors and high-resolution displays
- Elliptical orbit projection with inclination cues and alternate distance scaling modes
- Clean overlay UI with HUD, focus badge, timeline, event chips, tour captions, and scene controls
- Major moons for Earth, Jupiter, and Saturn
- Mission trajectories for `Parker`, `JWST`, `Voyager 1`, `Cassini`, and `Apollo 11`
- Earth-sky context strip showing approximate ecliptic longitudes from Earth's point of view
- Scale story mode that relaxes the compressed model toward a harsher sense of real distance
- Runtime app icon, branded splash screen, and screenshot capture workflow

## Quick Start

### Requirements

- Python `3.10+`
- A desktop environment that can run `Pygame`

### Install and run

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

### Optional desktop build

```bash
source .venv/bin/activate
pip install pyinstaller
python scripts/build_desktop.py
```

## Core Experience

- Watch the Solar System in a curated compressed scale that stays readable in fullscreen
- Jump between curated scene presets depending on whether you want global context or a tighter view
- Click a planet to open a focus experience with a rotating textured sphere and contextual data
- Switch to `Live` mode to view the current planetary arrangement in real time
- Launch guided tours or presentation mode for a passive, polished showcase loop

## Controls

- `Left click`: select a planet
- `Left click` on a planet: jump into focus and show the rotating close-up preview
- `Left drag` on the focus sphere: rotate the selected planet manually
- `Mouse wheel`: zoom in or out
- `Q / W / E / G`: switch between `System`, `Inner`, `Outer`, and `Giants` scenes
- `F`: jump to focus view for the selected planet
- `T / Y`: start the `Grand Tour` or `Historic Dates` guided tour
- `D`: toggle looping presentation mode
- `1 / 2 / 3 / 4`: switch time speed presets
- `Timeline scrubber`: drag to set the simulation date
- `Quick date chips`: jump to current and curated astronomy events, including the next computed alignment
- `Live`: sync the Solar System to the current moment and run at `1:1` real time
- `Sound`: toggle the ambient soundscape
- `Pause` / `Resume`: stop or continue orbital motion
- `Orbits`: show or hide orbit lines
- `Labels`: show or hide planet labels
- `M`: show or hide mission trajectories
- `K`: show or hide the Earth-sky context strip
- `S`: toggle the scale story blend
- `Scale`: switch between compressed and expanded distance scaling
- `H`: hide or reveal the UI
- `P`: capture a screenshot into `screenshots/`
- `Clean Shot`: capture a HUD-free screenshot of the current frame
- `Reset`: restore the original system state

## Project layout

- `main.py`: simple desktop entry point
- `orbit_sim/app.py`: app orchestration and input flow
- `orbit_sim/solar_system.py`: Solar System dataset and planet metadata
- `orbit_sim/satellites.py`: major moon dataset
- `orbit_sim/missions.py`: mission trajectory presets
- `orbit_sim/tours.py`: cinematic tour definitions
- `orbit_sim/simulation.py`: orbital motion state
- `orbit_sim/camera.py`: responsive scene layout, zoom, and distance scaling
- `orbit_sim/rendering.py`: scene rendering
- `orbit_sim/planet_sphere.py`: focus close-up sphere rendering
- `orbit_sim/ui.py`: info panel, HUD, and controls
- `orbit_sim/background.py`: procedural star field
- `orbit_sim/audio.py`: adaptive ambient soundscape
- `orbit_sim/branding.py`: splash screen and runtime icon
- `orbit_sim/settings.py`: local settings persistence
