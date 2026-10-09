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

| Action | Input |
| --- | --- |
| Select a planet | `Left click` |
| Rotate the focus sphere | `Left drag` on the focused planet |
| Zoom | `Mouse wheel` |
| System scenes | `Q / W / E / G` |
| Focus selected planet | `F` |
| Start guided tours | `T / Y` |
| Toggle presentation mode | `D` |
| Time speed presets | `1 / 2 / 3 / 4` |
| Scrub simulation date | `Timeline slider` |
| Jump to curated dates | `Quick date chips` |
| Toggle `Live` real-time mode | `Live` |
| Toggle sound | `Sound` |
| Pause or resume | `Pause / Resume` |
| Toggle orbit lines | `Orbits` or `O` |
| Toggle labels | `Labels` or `L` |
| Toggle mission trajectories | `M` |
| Toggle sky context strip | `K` |
| Toggle scale story | `S` |
| Toggle distance scaling mode | `Scale` |
| Hide or reveal the UI | `H` |
| Capture a screenshot | `P` |
| Capture a HUD-free shot | `Clean Shot` |
| Reset the viewer state | `Reset` |

## Repository Layout

| Path | Purpose |
| --- | --- |
| `main.py` | Desktop entry point |
| `orbit_sim/app.py` | App orchestration, state flow, and input handling |
| `orbit_sim/solar_system.py` | Solar System dataset and planet metadata |
| `orbit_sim/satellites.py` | Major moon dataset |
| `orbit_sim/missions.py` | Mission trajectory presets |
| `orbit_sim/tours.py` | Guided tour definitions |
| `orbit_sim/simulation.py` | Orbital state and time progression |
| `orbit_sim/camera.py` | Responsive layout, zoom, scene presets, and distance scaling |
| `orbit_sim/rendering.py` | Main scene renderer and focus-view composition |
| `orbit_sim/planet_sphere.py` | Textured close-up sphere renderer |
| `orbit_sim/ui.py` | HUD, info panels, strips, and overlay controls |
| `orbit_sim/background.py` | Procedural star field and space backdrop |
| `orbit_sim/audio.py` | Adaptive ambient soundscape |
| `orbit_sim/branding.py` | Splash screen and runtime branding |
| `orbit_sim/settings.py` | Local settings persistence |
| `assets/planets/` | Planet maps, ring masks, and auxiliary texture assets |
| `screenshots/` | Runtime screenshots captured from the app |

## Technical Notes

- The visualization uses a deliberately compressed scale model so the full Solar System remains readable in fullscreen
- Planet close-ups use textured rotating spheres rather than flat 2D portraits
- The app includes a substantial performance pass around starfield caching, label caching, focus overlays, mission geometry, and sphere rendering hot paths
- Settings such as UI visibility, scale mode, and overlay toggles persist locally between runs

## Project Priorities

- Keep the visualization readable in fullscreen without collapsing into a literal but unusable scale model
- Make the app feel calm, modern, and astronomy-inspired rather than playful or demo-like
- Preserve a modular structure so rendering, simulation, camera, UI, and assets can evolve independently
- Ship something that works well both as a portfolio piece and as a clean base for future expansion

## License

The source code is released under the MIT License, see [LICENSE](LICENSE).

Planet textures in `assets/planets/` come from [Solar System Scope](https://www.solarsystemscope.com/textures/) via Wikimedia Commons and are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); they are not covered by the MIT License.
