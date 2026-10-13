import "./style.css";
import { Vector3 } from "three";
import { MISSIONS } from "./data/missions";
import { BOOKMARKS, TOURS, type Tour, type TourStep } from "./data/tours";
import { MOONS, PLANETS } from "./data/bodies";
import { moonsOf } from "./astro/layout";
import { TIMELINE_END_MS, TIMELINE_START_MS } from "./astro/time";
import { Clock, SPEEDS, dateInputValue, formatUtc } from "./clock";
import { SolarScene } from "./render/scene";
import { TourRunner } from "./tour";
import { describe } from "./ui/info";
import { createPalette, type Command } from "./ui/palette";

const $ = <T extends HTMLElement>(id: string): T => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el as T;
};

function webglAvailable(): boolean {
  if (new URLSearchParams(location.search).has("nowebgl")) return false;
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function openDialog(dlg: HTMLDialogElement): void {
  if (dlg.open) return;
  if (typeof dlg.showModal === "function") dlg.showModal();
  else dlg.setAttribute("open", "");
}

function setupDialogs(): void {
  $("credits-from-help").addEventListener("click", () => {
    $<HTMLDialogElement>("help").close();
    $("credits-open").click();
  });
  for (const [button, id] of [["credits-open", "credits"], ["help-open", "help"]] as const) {
    const dlg = $<HTMLDialogElement>(id);
    $(button).addEventListener("click", () => openDialog(dlg));
    dlg.addEventListener("click", (e) => {
      if (e.target === dlg) dlg.close();
    });
  }
}

function showNoWebgl(): void {
  document.body.classList.add("no-gl");
  $("nowebgl").hidden = false;
  $("view").hidden = true;
}

declare global {
  interface Window {
    __gravity?: { frames: () => number; focus: () => string; ms: () => number; live: () => boolean; mode: () => string };
  }
}

function start(): void {
  setupDialogs();
  if (!webglAvailable()) return showNoWebgl();

  const canvas = $<HTMLCanvasElement>("view");
  let scene: SolarScene;
  try {
    scene = new SolarScene({ canvas, labels: $("labels"), onPick: (id) => focusBody(id) });
  } catch (err) {
    console.error(err);
    return showNoWebgl();
  }

  const clock = new Clock();
  let userTrue = false;

  // ---- dock layout ----
  const dock = $("dock");
  const phone = window.matchMedia("(max-width: 720px)");
  const syncDock = () => {
    document.documentElement.style.setProperty("--dock-h", `${dock.offsetHeight}px`);
    // On phones the info card and body strip also sit over the lower part of the view.
    const vh = window.innerHeight;
    let covered = vh - dock.getBoundingClientRect().top;
    if (phone.matches) {
      for (const id of ["info"]) {
        const el = $(id);
        if (el.offsetParent !== null) covered = Math.max(covered, vh - el.getBoundingClientRect().top);
      }
    }
    scene.setInsets($("topbar").offsetHeight, Math.round(covered));
  };
  new ResizeObserver(syncDock).observe(dock);
  new ResizeObserver(syncDock).observe($("info"));
  window.addEventListener("resize", syncDock);
  syncDock();

  // ---- bodies list ----
  const nav = $("bodies");
  const focusBody = (id: string) => {
    scene.focus(id);
    renderBodies();
    renderInfo();
  };
  const chip = (id: string, label: string, color: string, cls = "", key = "") => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `chip ${cls}`.trim();
    b.dataset.id = id;
    b.setAttribute("aria-pressed", String(scene.getFocus() === id));
    const num = document.createElement("span");
    num.className = "key";
    num.setAttribute("aria-hidden", "true");
    num.textContent = key;
    const dot = document.createElement("span");
    dot.className = "dot";
    dot.style.background = color;
    b.append(num, dot, document.createTextNode(label));
    if (key) b.setAttribute("aria-keyshortcuts", key);
    b.addEventListener("click", () => focusBody(id));
    return b;
  };
  function renderBodies(): void {
    const f = scene.getFocus();
    const moon = MOONS.find((m) => m.name === f);
    const showMoonsOf = moon ? moon.parent : PLANETS.some((p) => p.name === f) ? f : null;
    nav.replaceChildren(chip("Sun", "Sun", "#ffcf70", "", "S"));
    PLANETS.forEach((p, i) => {
      nav.appendChild(chip(p.name, p.name, p.accent, "", String(i + 1)));
      if (p.name === showMoonsOf) for (const m of moonsOf(p.name)) nav.appendChild(chip(m.name, m.name, m.accent, "moon"));
    });
    nav.querySelector<HTMLElement>('[aria-pressed="true"]')?.scrollIntoView({ block: "nearest", inline: "center" });
  }

  // ---- info ----
  const infoName = $("info-name");
  const infoKind = $("info-kind");
  const infoFact = $("info-fact");
  const infoStats = $("info-stats");
  const infoMore = $("info-more");
  const KEY_FACTS = 3;
  let infoKey = "";
  infoMore.addEventListener("click", () => {
    const open = infoMore.getAttribute("aria-expanded") !== "true";
    infoMore.setAttribute("aria-expanded", String(open));
    infoMore.textContent = open ? "Less" : "More";
    $("info").classList.toggle("expanded", open);
    syncDock();
  });
  function renderInfo(): void {
    const f = scene.getFocus();
    const view = describe(f, clock.ms);
    infoName.textContent = view.name;
    infoKind.textContent = view.kind;
    infoFact.textContent = view.fact;
    const key = f + view.stats.map((s) => s[0]).join();
    if (key !== infoKey) {
      infoKey = key;
      infoStats.replaceChildren(
        ...view.stats.flatMap(([k], i) => {
          const dt = document.createElement("dt");
          dt.textContent = k;
          const dd = document.createElement("dd");
          if (i >= KEY_FACTS) dt.className = dd.className = "extra";
          return [dt, dd];
        }),
      );
    }
    const dds = infoStats.querySelectorAll("dd");
    view.stats.forEach(([, v], i) => {
      if (dds[i] && dds[i]!.textContent !== v) dds[i]!.textContent = v;
    });
  }

  // ---- time controls ----
  const speeds = $("speeds");
  SPEEDS.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = s.label;
    b.dataset.index = String(i);
    b.addEventListener("click", () => {
      clock.setSpeed(i);
      syncTime(true);
    });
    speeds.appendChild(b);
  });
  const jumpTo = (id: string) => {
    const b = BOOKMARKS.find((x) => x.id === id);
    if (!b) return;
    if (id === "now") clock.goLive();
    else {
      clock.setTime(b.at(clock.ms));
      clock.playing = false;
    }
    syncTime(true);
  };
  $("live").addEventListener("click", () => {
    clock.goLive();
    syncTime(true);
  });
  $("play").addEventListener("click", () => {
    clock.togglePlay();
    syncTime(true);
  });
  $("reverse").addEventListener("click", () => {
    clock.toggleReverse();
    syncTime(true);
  });
  const slider = $<HTMLInputElement>("timeline");
  let scrubbing = false;
  slider.addEventListener("input", () => {
    scrubbing = true;
    clock.setTime(TIMELINE_START_MS + (Number(slider.value) / 10000) * (TIMELINE_END_MS - TIMELINE_START_MS));
    clock.playing = false;
    syncTime(false);
  });
  slider.addEventListener("change", () => {
    scrubbing = false;
  });
  const dateInput = $<HTMLInputElement>("date");
  dateInput.addEventListener("change", () => {
    const t = Date.parse(`${dateInput.value}T00:00:00Z`);
    if (!Number.isNaN(t)) {
      clock.setTime(t);
      clock.playing = false;
      syncTime(true);
    }
  });

  const clockEl = $("clock");
  const modeEl = $("clock-mode");
  const playBtn = $("play");
  const playIcon = $("play-icon");
  const PAUSE = "M7 5h4v14H7zM13 5h4v14h-4z";
  const PLAY = "M8 5v14l11-7z";
  function syncTime(full: boolean): void {
    clockEl.textContent = `${formatUtc(clock.ms)} UTC`;
    const state = clock.live ? "Live" : !clock.playing ? "Paused" : `${clock.reverse ? "Reverse " : ""}${SPEEDS[clock.speedIndex]!.label}`;
    if (modeEl.textContent !== state) modeEl.textContent = state;
    modeEl.classList.toggle("live", clock.live);
    if (full) {
      $("live").setAttribute("aria-pressed", String(clock.live));
      $("reverse").setAttribute("aria-pressed", String(clock.reverse && !clock.live));
      const showPlay = !clock.playing && !clock.live;
      playBtn.setAttribute("aria-label", showPlay ? "Play" : "Pause");
      playIcon.firstElementChild!.setAttribute("d", showPlay ? PLAY : PAUSE);
      speeds.querySelectorAll("button").forEach((b, i) => b.setAttribute("aria-pressed", String(i === clock.speedIndex && clock.playing)));
      if (document.activeElement !== dateInput) dateInput.value = dateInputValue(clock.ms);
    }
    if (!scrubbing) slider.value = String(Math.round(clock.fraction * 10000));
  }

  // ---- view settings (reached from the command palette) ----
  const view = { orbits: true, labels: true, missions: true };
  const zoomIn = () => scene.zoomBy(0.6);
  const zoomOut = () => scene.zoomBy(1.6);
  const overview = () => {
    if (tours.active) tours.stop();
    scene.focus("Sun", { direction: new Vector3(0, 0.55, 0.83) });
    renderBodies();
    renderInfo();
  };
  const setTrue = (v: boolean) => {
    userTrue = v;
    scene.setDistanceMode(v ? "true" : "compressed");
  };

  // ---- missions ----
  const goMission = (m: (typeof MISSIONS)[number]) => {
    clock.setTime(m.launchMs + (m.endMs - m.launchMs) * 0.4);
    clock.playing = false;
    syncTime(true);
    scene.setTime(clock.ms);
    if (m.frame === "earth_local") focusBody("Earth");
    else focusBody(`mission:${m.name}`);
  };

  // ---- tours ----
  const tourbar = $("tourbar");
  const applyStep = (step: TourStep) => {
    if (step.jump) {
      const bm = BOOKMARKS.find((b) => b.id === step.jump)!;
      if (step.jump === "now") clock.goLive();
      else {
        clock.setTime(bm.at(clock.ms));
        clock.setSpeed(0);
        clock.playing = true;
      }
      syncTime(true);
      scene.setTime(clock.ms);
    }
    scene.setDistanceMode(step.scaleStory ? "true" : userTrue ? "true" : "compressed");
    if (step.focusBody) scene.focus(step.focusBody);
    else scene.focus("Sun", { distance: scene.sceneModeDistance(step.scene), direction: new Vector3(0, step.scene === "full_system" ? 0.55 : 0.4, 0.83) });
    renderBodies();
    renderInfo();
  };
  const tours = new TourRunner({
    enter: (step, tour: Tour, index) => {
      document.body.classList.add("touring");
      tourbar.hidden = false;
      $("tour-title").textContent = `${tour.label}, ${index + 1} of ${tour.steps.length}: ${step.title}`;
      $("tour-caption").textContent = step.caption;
      applyStep(step);
    },
    exit: () => {
      document.body.classList.remove("touring");
      tourbar.hidden = true;
      scene.setDistanceMode(userTrue ? "true" : "compressed");
    },
  });
  $("tour-stop").addEventListener("click", () => tours.stop());
  $("tour-next").addEventListener("click", () => tours.next());
  $("tour-prev").addEventListener("click", () => tours.prev());

  // ---- command palette ----
  const onOff = (v: boolean) => (v ? "on, turn off" : "off, turn on");
  const palette = createPalette($<HTMLDialogElement>("palette"), () => {
    const cmds: Command[] = [{ label: "Sun", hint: "S", run: () => focusBody("Sun") }];
    PLANETS.forEach((p, i) => {
      cmds.push({ label: p.name, hint: String(i + 1), run: () => focusBody(p.name) });
    });
    for (const m of MOONS) cmds.push({ label: m.name, hint: `Moon of ${m.parent}`, run: () => focusBody(m.name) });
    for (const m of MISSIONS) cmds.push({ label: m.name, hint: "Mission", run: () => goMission(m) });
    for (const t of TOURS) cmds.push({ label: `Tour: ${t.label}`, hint: t.description, run: () => tours.start(t) });
    for (const b of BOOKMARKS) cmds.push({ label: b.label, hint: "Date", run: () => jumpTo(b.id) });
    cmds.push(
      { label: "Overview", hint: "0", run: overview },
      { label: "Zoom in", hint: "+", run: zoomIn },
      { label: "Zoom out", hint: "-", run: zoomOut },
      { label: clock.playing ? "Pause time" : "Resume time", hint: "Space", run: () => (clock.togglePlay(), syncTime(true)) },
      { label: `Orbits: ${onOff(view.orbits)}`, hint: "View", run: () => scene.setVisibility({ orbits: (view.orbits = !view.orbits) }) },
      { label: `Labels: ${onOff(view.labels)}`, hint: "View", run: () => scene.setVisibility({ labels: (view.labels = !view.labels) }) },
      { label: `Mission paths: ${onOff(view.missions)}`, hint: "View", run: () => scene.setVisibility({ missions: (view.missions = !view.missions) }) },
      { label: `True distances: ${onOff(userTrue)}`, hint: "View", run: () => setTrue(!userTrue) },
      { label: "Keyboard help", hint: "?", run: () => $("help-open").click() },
    );
    return cmds;
  });
  $("palette-open").addEventListener("click", () => palette.open());

  // ---- keyboard ----
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      palette.open();
      return;
    }
    const tag = (e.target as HTMLElement).tagName;
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA" || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === "/") {
      e.preventDefault();
      palette.open();
    } else if (e.key === "?") $("help-open").click();
    else if (e.key === "+" || e.key === "=") zoomIn();
    else if (e.key === "-" || e.key === "_") zoomOut();
    else if (e.key === "0") overview();
    else if (e.key >= "1" && e.key <= "8") focusBody(PLANETS[Number(e.key) - 1]!.name);
    else if (e.key === "s" || e.key === "S") focusBody("Sun");
    else if (e.key === "l" || e.key === "L") {
      clock.goLive();
      syncTime(true);
    } else if (e.key === " " && tag !== "BUTTON") {
      e.preventDefault();
      clock.togglePlay();
      syncTime(true);
    } else if (e.key === "Escape" && tours.active) tours.stop();
  });

  // ---- loop ----
  window.addEventListener("resize", () => scene.resize());
  new ResizeObserver(() => scene.resize()).observe(canvas);
  let last = performance.now();
  let infoTimer = 0;
  const loop = (now: number) => {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    clock.tick(dt);
    tours.update(dt);
    scene.setTime(clock.ms);
    scene.update(dt);
    syncTime(false);
    if (tours.active) $("tour-bar").style.width = `${(tours.progress * 100).toFixed(1)}%`;
    infoTimer += dt;
    if (infoTimer > 0.25) {
      infoTimer = 0;
      renderInfo();
      syncTime(true);
    }
    requestAnimationFrame(loop);
  };

  renderBodies();
  renderInfo();
  syncTime(true);
  requestAnimationFrame(loop);
  window.__gravity = {
    frames: () => scene.frames,
    focus: () => scene.getFocus(),
    ms: () => clock.ms,
    live: () => clock.live,
    mode: () => scene.getDistanceMode(),
  };
  document.body.dataset.ready = "true";
}

start();
