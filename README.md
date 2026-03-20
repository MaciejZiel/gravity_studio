# Gravity Studio: Solar System

A fullscreen, astronomy-inspired Solar System visualization built with Python and Pygame.

## Features

- Fullscreen launch with responsive scaling for large displays
- Real Solar System dataset with the Sun and all 8 planets in correct order
- Elliptical orbit projection with inclination cues, live ephemeris syncing, and alternate distance scaling
- Scene presets for `System`, `Inner`, `Giants`, `Outer`, and planet `Focus` views
- Textured planet focus close-up with a spinning shaded sphere built from full-surface planet maps
- Close-up shading upgrades with axial tilt, seasonal lighting, Earth clouds, night lights, aurora cues, atmospheric terminator haze, and denser Saturn rings
- Major moons for Earth, Jupiter, and Saturn rendered as contextual satellites in scene and focus views
- Mission trajectory layer for `Parker`, `JWST`, `Voyager 1`, `Cassini`, and `Apollo 11`
- Timeline scrubber with simulation date, quick date jumps, and `1x / 10x / 100x / 1000x` time controls
- Astronomy event chips with `Now`, `Next Alignment`, `Equinox`, `Solstice`, `Eclipse Season`, `Apollo 11`, `Voyager 1`, and `JWST`
- Earth-sky context strip showing approximate ecliptic longitudes of the planets from Earth's point of view
- Guided cinematic tours plus a looping presentation mode for passive fullscreen playback
- Scale story mode that relaxes the compressed visualization toward a harsher sense of true distance
- Live local clock overlay plus per-focus timestamp readout with hour, minute, and second precision
- One-click `Live` mode that syncs planet positions to the current time and runs in real time
- Layered starfield parallax, branded fullscreen splash, runtime app icon, and adaptive ambient soundscape
- Adaptive planet labels that avoid overlap in denser views
- Contextual focus overlays, clean screenshot capture, and locally persisted viewer settings
- Modular separation between data, simulation, camera, rendering, background, audio, and UI

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

Optional desktop build:

```bash
source .venv/bin/activate
pip install pyinstaller
python scripts/build_desktop.py
```

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
