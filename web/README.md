# Gravity Studio for the browser

A Solar System viewer that runs in the browser, built with Vite, TypeScript and Three.js. Planet positions come from real orbital elements, not from a simulation, so any date between 1960 and 2165 gives the same answer every time.

## Features

- Eight textured planets, the Sun, and six moons (Moon, Io, Europa, Ganymede, Callisto, Titan).
- Elliptical orbits drawn from the orbital elements; Earth has a day-night shader with city lights and clouds.
- Focus and zoom on any body from the list, with the keyboard (1-8, S, +, -, 0) or by dragging and scrolling.
- Time controls: live 1:1 clock, pause, reverse, speeds from 1 min/s to 1000 d/s, a timeline for 1960-2165, a date field and bookmarked moments.
- Mission paths for Parker Solar Probe, JWST, Voyager 1, Cassini and Apollo 11, and guided tours.
- Works down to 400 px wide; a message is shown when WebGL is not available.

## Accuracy

Positions use the approximate Keplerian elements and rates of Standish and Williams from JPL, solved with Newton iteration on Kepler's equation. Table 1 (valid 1800-2050) is used up to 2050 and Table 2a (valid over a longer span, lower accuracy) from 2050 to 2165; the switch moves positions by less than 0.2 degrees. Moons other than the Moon use circular orbits with arbitrary starting phases, and mission paths are schematic. Sizes are enlarged and distances compressed in the default view; "True distances" switches to linear au.

Tests in `tests/` check Earth at J2000, the 2024 perihelion, aphelion and equinox against reference values, the Kepler solver, the clock, the tours and the layout mapping.

## Run

```
cd web
npm ci
npm run dev        # development server
npm test           # vitest
npm run build      # type check and static build into web/dist
npm run test:e2e   # Playwright smoke tests (needs: npx playwright install chromium)
```

`web/dist` is a static site with relative paths and can be served from any directory.

## Credits

Planet textures are from Solar System Scope (https://www.solarsystemscope.com/textures/), CC BY 4.0, unmodified 2k maps copied from `assets/planets/`. The Sun and moon surfaces are generated procedurally. Orbital elements are from the JPL Solar System Dynamics group. See `3rdparty_licenses.md` in the repository root.
