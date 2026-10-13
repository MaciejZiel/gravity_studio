import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { MOONS, PLANETS, SUN, type MoonData, type PlanetData } from "../data/bodies";
import { MISSIONS, type MissionData } from "../data/missions";
import type { SceneMode } from "../data/tours";
import { orbitOutline } from "../astro/ephemeris";
import {
  SUN_VISUAL_RADIUS,
  type DistanceMode,
  moonOffset,
  moonOrbitPoint,
  planetScenePosition,
  spinAngle,
  toScene,
  visualRadius,
} from "../astro/layout";
import { atmosphereMaterial, earthMaterial } from "./earth";
import { SURFACES, renderGlow, renderSurface, rng } from "./procedural";

export type FocusId = string; // "Sun", planet, moon, or "mission:<name>"

interface PlanetNode {
  data: PlanetData;
  radius: number;
  group: THREE.Group; // positioned at the planet
  mesh: THREE.Mesh;
  orbit: THREE.Line;
  label: HTMLElement;
}

interface MoonNode {
  data: MoonData;
  radius: number;
  parent: PlanetNode;
  mesh: THREE.Mesh;
  ring: THREE.Line;
  label: HTMLElement;
}

interface MissionNode {
  data: MissionData;
  line: THREE.Line;
  curve: THREE.CatmullRomCurve3 | null;
  marker: THREE.Mesh;
  label: HTMLElement;
  /** Earth-local paths live in this group, which follows Earth. */
  holder: THREE.Object3D;
  position: THREE.Vector3;
  visible: boolean;
}

export interface SceneOptions {
  canvas: HTMLCanvasElement;
  labels: HTMLElement;
  onPick?: (id: FocusId) => void;
}

const BASE = import.meta.env.BASE_URL;
const TEXT_DIM = "#c9d3e0";

export class SolarScene {
  readonly renderer: THREE.WebGLRenderer;
  readonly camera: THREE.PerspectiveCamera;
  readonly controls: OrbitControls;
  private readonly scene = new THREE.Scene();
  private readonly planets: PlanetNode[] = [];
  private readonly moons: MoonNode[] = [];
  private readonly missions: MissionNode[] = [];
  private sun!: THREE.Mesh;
  private sunLabel!: HTMLElement;
  private readonly labelsRoot: HTMLElement;
  private mode: DistanceMode = "compressed";
  private ms = Date.now();
  private orbitsBuiltFor = NaN;
  private showOrbits = true;
  private showLabels = true;
  private showMissions = true;

  private focusId: FocusId = "Sun";
  private focusPos = new THREE.Vector3();
  private focusRadius = SUN_VISUAL_RADIUS;
  private goalDistance: number | null = null;
  private goalDir: THREE.Vector3 | null = null;
  private transitioning = false;
  private readonly tmp = new THREE.Vector3();
  frames = 0;

  constructor(private readonly opts: SceneOptions) {
    this.labelsRoot = opts.labels;
    this.renderer = new THREE.WebGLRenderer({ canvas: opts.canvas, antialias: true, powerPreference: "high-performance" });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setClearColor(0x03050a, 1);
    this.camera = new THREE.PerspectiveCamera(45, 1, 0.01, 4000);
    this.camera.position.set(0, 7, 11);
    this.controls = new OrbitControls(this.camera, opts.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = false;
    this.controls.rotateSpeed = 0.7;
    this.controls.zoomSpeed = 0.9;
    this.controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_ROTATE };
    this.controls.addEventListener("start", () => {
      this.goalDir = null;
      this.goalDistance = null;
    });

    this.buildLights();
    this.buildStars();
    this.buildSun();
    this.buildPlanets();
    this.buildMoons();
    this.buildMissions();
    this.setTime(this.ms);
    this.focus("Sun", { distance: this.overviewDistance(), direction: new THREE.Vector3(0, 0.55, 0.83), instant: true });
    this.bindPicking();
    this.resize();
  }

  // ---- construction ----

  private texture(name: string): THREE.Texture {
    const tex = new THREE.TextureLoader().load(`${BASE}textures/${name}`);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = Math.min(8, this.renderer.capabilities.getMaxAnisotropy());
    return tex;
  }

  private canvasTexture(c: HTMLCanvasElement): THREE.CanvasTexture {
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    return t;
  }

  private makeLabel(text: string, cls = ""): HTMLElement {
    const el = document.createElement("div");
    el.className = `body-label ${cls}`.trim();
    el.textContent = text;
    el.style.color = TEXT_DIM;
    this.labelsRoot.appendChild(el);
    return el;
  }

  private buildLights(): void {
    const sunLight = new THREE.PointLight(0xffffff, 4.6, 0, 0);
    this.scene.add(sunLight);
    this.scene.add(new THREE.AmbientLight(0x8fa0c0, 0.22));
  }

  private buildStars(): void {
    const rand = rng(7);
    const n = 3500;
    const pos = new Float32Array(n * 3);
    const col = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const z = rand() * 2 - 1;
      const t = rand() * Math.PI * 2;
      const s = Math.sqrt(1 - z * z);
      const R = 1800;
      pos.set([R * s * Math.cos(t), R * z, R * s * Math.sin(t)], i * 3);
      const b = 0.35 + Math.pow(rand(), 3) * 0.65;
      const warm = rand();
      col.set([b * (0.85 + 0.15 * warm), b * 0.92, b * (1 - 0.2 * warm)], i * 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    const m = new THREE.PointsMaterial({ size: 1.6, sizeAttenuation: false, vertexColors: true, depthWrite: false, fog: false });
    const stars = new THREE.Points(g, m);
    stars.frustumCulled = false;
    this.scene.add(stars);
  }

  private buildSun(): void {
    const tex = this.canvasTexture(renderSurface(SURFACES.Sun!, 512, 256));
    this.sun = new THREE.Mesh(
      new THREE.SphereGeometry(1, 64, 32),
      new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }),
    );
    this.sun.scale.setScalar(SUN_VISUAL_RADIUS);
    this.scene.add(this.sun);
    const glow = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: this.canvasTexture(renderGlow()), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }),
    );
    this.sun.add(glow);
    glow.scale.setScalar(7);
    this.sunLabel = this.makeLabel(SUN.name);
  }

  private buildPlanets(): void {
    const sphere = new THREE.SphereGeometry(1, 96, 48);
    for (const data of PLANETS) {
      const radius = visualRadius(data.radiusKm);
      const group = new THREE.Group();
      const tilt = new THREE.Group();
      tilt.rotation.x = -(data.axialTiltDeg * Math.PI) / 180;
      group.add(tilt);

      let material: THREE.Material;
      if (data.name === "Earth") {
        material = earthMaterial(this.texture("earth.jpg"), this.texture("earth_night.jpg"));
      } else {
        material = new THREE.MeshStandardMaterial({ map: this.texture(data.texture!), roughness: 1, metalness: 0 });
      }
      const mesh = new THREE.Mesh(sphere, material);
      mesh.scale.setScalar(radius);
      tilt.add(mesh);

      if (data.name === "Earth") {
        const clouds = new THREE.Mesh(
          sphere,
          new THREE.MeshStandardMaterial({ color: 0xffffff, alphaMap: this.texture("earth_clouds.jpg"), transparent: true, opacity: 0.85, depthWrite: false, roughness: 1 }),
        );
        clouds.scale.setScalar(radius * 1.012);
        clouds.name = "clouds";
        tilt.add(clouds);
        const atmo = new THREE.Mesh(sphere, atmosphereMaterial(new THREE.Color(0x5f9cff)));
        atmo.scale.setScalar(radius * 1.07);
        group.add(atmo);
      }
      if (data.rings) tilt.add(this.buildRings(radius));

      const orbit = new THREE.Line(
        new THREE.BufferGeometry(),
        new THREE.LineBasicMaterial({ color: new THREE.Color(data.accent), transparent: true, opacity: 0.38 }),
      );
      orbit.frustumCulled = false;
      this.scene.add(orbit);
      this.scene.add(group);
      this.planets.push({ data, radius, group, mesh, orbit, label: this.makeLabel(data.name) });
    }
  }

  private buildRings(radius: number): THREE.Mesh {
    const inner = radius * 1.24;
    const outer = radius * 2.27;
    const geo = new THREE.RingGeometry(inner, outer, 128, 1);
    const pos = geo.attributes.position!;
    const uv = geo.attributes.uv!;
    for (let i = 0; i < pos.count; i++) {
      const r = Math.hypot(pos.getX(i), pos.getY(i));
      uv.setXY(i, (r - inner) / (outer - inner), 0.5);
    }
    const mat = new THREE.MeshStandardMaterial({
      map: this.texture("saturn_ring_alpha.png"),
      transparent: true,
      side: THREE.DoubleSide,
      roughness: 1,
      depthWrite: false,
    });
    const ring = new THREE.Mesh(geo, mat);
    ring.rotation.x = -Math.PI / 2;
    return ring;
  }

  private buildMoons(): void {
    const sphere = new THREE.SphereGeometry(1, 40, 20);
    const radiusOf = (n: string) => PLANETS.find((p) => p.name === n)!.radiusKm;
    for (const data of MOONS) {
      const parent = this.planets.find((p) => p.data.name === data.parent)!;
      const spec = SURFACES[data.name]!;
      const tex = this.canvasTexture(renderSurface(spec, 512, 256));
      const mesh = new THREE.Mesh(sphere, new THREE.MeshStandardMaterial({ map: tex, roughness: 1, metalness: 0 }));
      const radius = Math.max(visualRadius(data.radiusKm), 0.006);
      mesh.scale.setScalar(radius);
      parent.group.add(mesh);

      const pts: THREE.Vector3[] = [];
      for (let i = 0; i <= 96; i++) pts.push(new THREE.Vector3(...moonOrbitPoint(data, radiusOf(data.parent), (i / 96) * Math.PI * 2)));
      const ring = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(pts),
        new THREE.LineBasicMaterial({ color: new THREE.Color(data.accent), transparent: true, opacity: 0.3 }),
      );
      parent.group.add(ring);
      this.moons.push({ data, radius, parent, mesh, ring, label: this.makeLabel(data.name, "moon") });
    }
  }

  private buildMissions(): void {
    const sphere = new THREE.SphereGeometry(1, 12, 8);
    for (const data of MISSIONS) {
      const line = new THREE.Line(
        new THREE.BufferGeometry(),
        new THREE.LineDashedMaterial({ color: new THREE.Color(data.color), dashSize: 0.06, gapSize: 0.04, transparent: true, opacity: 0.75 }),
      );
      line.frustumCulled = false;
      const marker = new THREE.Mesh(sphere, new THREE.MeshBasicMaterial({ color: new THREE.Color(data.color) }));
      const holder = new THREE.Group();
      holder.add(line);
      this.scene.add(holder);
      this.scene.add(marker);
      this.missions.push({ data, line, curve: null, marker, label: this.makeLabel(data.label, "mission"), holder, position: new THREE.Vector3(), visible: false });
    }
    this.rebuildMissions();
  }

  private rebuildMissions(): void {
    const earth = this.planets.find((p) => p.data.name === "Earth")!;
    for (const m of this.missions) {
      let pts: THREE.Vector3[];
      if (m.data.frame === "heliocentric") {
        pts = m.data.path.map(([x, y]) => new THREE.Vector3(...toScene({ x, y, z: 0 }, this.mode)));
      } else {
        const scale = earth.radius * 5.8;
        pts = m.data.path.map(([x, y]) => new THREE.Vector3(x * scale * 3, 0, -y * scale * 3));
      }
      m.curve = new THREE.CatmullRomCurve3(pts, false, "centripetal");
      const sampled = m.curve.getSpacedPoints(160);
      m.line.geometry.dispose();
      m.line.geometry = new THREE.BufferGeometry().setFromPoints(sampled);
      m.line.computeLineDistances();
      const mat = m.line.material as THREE.LineDashedMaterial;
      const len = m.curve.getLength();
      mat.dashSize = Math.max(0.01, len / 90);
      mat.gapSize = mat.dashSize * 0.7;
    }
  }

  private rebuildOrbits(): void {
    for (const p of this.planets) {
      const pts = orbitOutline(p.data.name, this.ms, 360).map((v) => new THREE.Vector3(...toScene(v, this.mode)));
      p.orbit.geometry.dispose();
      p.orbit.geometry = new THREE.BufferGeometry().setFromPoints(pts);
    }
    this.orbitsBuiltFor = this.ms;
  }

  // ---- state setters ----

  setTime(ms: number): void {
    this.ms = ms;
    if (!(Math.abs(ms - this.orbitsBuiltFor) < 20 * 365.25 * 86_400_000)) this.rebuildOrbits();
    for (const p of this.planets) {
      const [x, y, z] = planetScenePosition(p.data.name, ms, this.mode);
      p.group.position.set(x, y, z);
      const sunDir: [number, number] = [-x / Math.hypot(x, z), -z / Math.hypot(x, z)];
      p.mesh.rotation.y = spinAngle(p.data.name, p.data.rotationHours, ms, sunDir);
      const clouds = p.group.getObjectByName("clouds");
      if (clouds) clouds.rotation.y = p.mesh.rotation.y * 1.0 + ((ms / 86_400_000) % 1000) * 0.0008;
    }
    for (const m of this.moons) {
      const [x, y, z] = moonOffset(m.data, PLANETS.find((p) => p.name === m.data.parent)!.radiusKm, ms);
      m.mesh.position.set(x, y, z);
    }
    this.sun.rotation.y = (ms / 86_400_000) * 0.1;
    this.updateMissionMarkers();
  }

  private updateMissionMarkers(): void {
    const earth = this.planets.find((p) => p.data.name === "Earth")!;
    for (const m of this.missions) {
      if (!m.curve) continue;
      const total = m.data.endMs - m.data.launchMs;
      const progress = Math.min(1, Math.max(0, (this.ms - m.data.launchMs) / total));
      const started = this.ms >= m.data.launchMs;
      const p = m.curve.getPointAt(progress);
      if (m.data.frame === "earth_local") {
        m.holder.position.copy(earth.group.position);
        m.marker.position.copy(p).add(earth.group.position);
        m.position.copy(m.marker.position);
        m.visible = this.showMissions && this.focusId === "Earth";
      } else {
        m.marker.position.copy(p);
        m.position.copy(p);
        m.visible = this.showMissions && (this.focusId !== "Earth" || m.data.name === "JWST") && started;
      }
      m.line.visible = this.showMissions && (m.data.frame === "heliocentric" ? true : this.focusId === "Earth");
    }
  }

  setDistanceMode(mode: DistanceMode): void {
    if (mode === this.mode) return;
    this.mode = mode;
    this.rebuildOrbits();
    this.rebuildMissions();
    this.setTime(this.ms);
    if (this.focusId === "Sun" && this.goalDistance === null) this.goalDistance = this.overviewDistance();
  }

  getDistanceMode(): DistanceMode {
    return this.mode;
  }

  setVisibility(v: { orbits?: boolean; labels?: boolean; missions?: boolean }): void {
    if (v.orbits !== undefined) this.showOrbits = v.orbits;
    if (v.labels !== undefined) this.showLabels = v.labels;
    if (v.missions !== undefined) this.showMissions = v.missions;
    for (const p of this.planets) p.orbit.visible = this.showOrbits;
    for (const m of this.moons) m.ring.visible = this.showOrbits;
    this.updateMissionMarkers();
  }

  // ---- focus ----

  private overviewDistance(): number {
    return this.mode === "compressed" ? 13 : 75;
  }

  sceneModeDistance(scene: SceneMode): number {
    const compressed = this.mode === "compressed";
    switch (scene) {
      case "inner_worlds": return compressed ? 3.4 : 5;
      case "gas_giants": return compressed ? 9 : 30;
      case "outer_worlds": return compressed ? 12 : 62;
      default: return this.overviewDistance();
    }
  }

  getFocus(): FocusId {
    return this.focusId;
  }

  private resolve(id: FocusId): { pos: THREE.Vector3; radius: number } | null {
    if (id === "Sun") return { pos: new THREE.Vector3(), radius: SUN_VISUAL_RADIUS };
    const p = this.planets.find((n) => n.data.name === id);
    if (p) return { pos: p.group.position.clone(), radius: p.radius };
    const m = this.moons.find((n) => n.data.name === id);
    if (m) return { pos: m.mesh.getWorldPosition(new THREE.Vector3()), radius: m.radius };
    const ms = this.missions.find((n) => `mission:${n.data.name}` === id);
    if (ms) return { pos: ms.position.clone(), radius: 0.05 };
    return null;
  }

  focus(id: FocusId, o: { distance?: number; direction?: THREE.Vector3; instant?: boolean } = {}): void {
    const r = this.resolve(id);
    if (!r) return;
    this.focusId = id;
    this.focusRadius = r.radius;
    const isBody = id !== "Sun" && !id.startsWith("mission:");
    const distance = o.distance ?? (id === "Sun" ? this.overviewDistance() : id.startsWith("mission:") ? this.missionDistance() : Math.max(r.radius * 6, 0.12));
    let dir = o.direction;
    if (!dir) {
      if (isBody) {
        // Look at the sunlit side from slightly above the ecliptic.
        const toSun = r.pos.clone().multiplyScalar(-1);
        if (toSun.lengthSq() < 1e-9) toSun.set(0, 0, 1);
        toSun.normalize();
        const side = new THREE.Vector3().crossVectors(toSun, new THREE.Vector3(0, 1, 0)).normalize();
        dir = toSun.multiplyScalar(0.85).add(new THREE.Vector3(0, 0.38, 0)).add(side.multiplyScalar(0.3)).normalize();
      } else {
        dir = this.camera.position.clone().sub(this.controls.target).normalize();
      }
    }
    this.goalDir = dir.clone().normalize();
    this.goalDistance = distance;
    this.transitioning = !o.instant;
    this.controls.minDistance = Math.max(r.radius * 1.35, 0.004);
    this.controls.maxDistance = this.mode === "compressed" ? 160 : 400;
    if (o.instant) {
      this.controls.target.copy(r.pos);
      this.camera.position.copy(r.pos).addScaledVector(this.goalDir, distance);
      this.goalDir = null;
      this.goalDistance = null;
    }
    this.updateMissionMarkers();
  }

  private missionDistance(): number {
    return this.mode === "compressed" ? 2.2 : 6;
  }

  zoomBy(factor: number): void {
    const offset = this.camera.position.clone().sub(this.controls.target);
    const d = THREE.MathUtils.clamp(offset.length() * factor, this.controls.minDistance, this.controls.maxDistance);
    this.goalDir = offset.normalize();
    this.goalDistance = d;
    this.transitioning = true;
  }

  // ---- picking ----

  private bindPicking(): void {
    const c = this.opts.canvas;
    let down: { x: number; y: number; t: number } | null = null;
    c.addEventListener("pointerdown", (e) => {
      down = { x: e.clientX, y: e.clientY, t: performance.now() };
    });
    c.addEventListener("pointerup", (e) => {
      if (!down) return;
      const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
      const quick = performance.now() - down.t < 500;
      down = null;
      if (moved > 6 || !quick) return;
      const id = this.pick(e.clientX, e.clientY);
      if (id && this.opts.onPick) this.opts.onPick(id);
    });
  }

  private pick(cx: number, cy: number): FocusId | null {
    const rect = this.opts.canvas.getBoundingClientRect();
    let best: FocusId | null = null;
    let bestD = 28;
    const test = (id: FocusId, world: THREE.Vector3) => {
      const p = this.tmp.copy(world).project(this.camera);
      if (p.z > 1) return;
      const sx = rect.left + ((p.x + 1) / 2) * rect.width;
      const sy = rect.top + ((1 - p.y) / 2) * rect.height;
      const d = Math.hypot(sx - cx, sy - cy);
      if (d < bestD) {
        bestD = d;
        best = id;
      }
    };
    test("Sun", new THREE.Vector3());
    for (const p of this.planets) test(p.data.name, p.group.position);
    for (const m of this.moons) {
      if (this.moonVisible(m)) test(m.data.name, m.mesh.getWorldPosition(new THREE.Vector3()));
    }
    return best;
  }

  // ---- frame ----

  resize(): void {
    const c = this.opts.canvas;
    const w = Math.max(1, c.clientWidth);
    const h = Math.max(1, c.clientHeight);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    // Keep the horizontal field of view usable on narrow portrait screens.
    this.camera.fov = w / h < 0.8 ? 58 : 45;
    this.camera.updateProjectionMatrix();
  }

  private moonVisible(m: MoonNode): boolean {
    const camDist = this.camera.position.distanceTo(m.parent.group.position);
    return camDist < m.parent.radius * 90 || this.focusId === m.parent.data.name || this.focusId === m.data.name;
  }

  update(dt: number): void {
    const r = this.resolve(this.focusId);
    if (r) {
      this.focusPos.copy(r.pos);
      const k = this.transitioning ? 1 - Math.exp(-dt * 5) : 1;
      const delta = r.pos.clone().sub(this.controls.target);
      const move = delta.clone().multiplyScalar(k);
      this.controls.target.add(move);
      this.camera.position.add(move);
      if (this.goalDistance !== null || this.goalDir !== null) {
        const off = this.camera.position.clone().sub(this.controls.target);
        let d = off.length();
        const dir = off.normalize();
        const kk = 1 - Math.exp(-dt * 4.5);
        if (this.goalDir) {
          dir.lerp(this.goalDir, kk).normalize();
          if (dir.distanceTo(this.goalDir) < 0.004) this.goalDir = null;
        }
        if (this.goalDistance !== null) {
          d += (this.goalDistance - d) * kk;
          if (Math.abs(d / this.goalDistance - 1) < 0.004) {
            d = this.goalDistance;
            this.goalDistance = null;
          }
        }
        this.camera.position.copy(this.controls.target).addScaledVector(dir, d);
      }
      if (this.transitioning && delta.length() < Math.max(1e-4, r.radius * 0.02) && this.goalDistance === null && this.goalDir === null) this.transitioning = false;
    }
    this.controls.update();
    const dist = this.camera.position.distanceTo(this.controls.target);
    this.camera.near = Math.max(0.0008, Math.min(0.5, dist * 0.02, this.focusRadius * 0.4));
    this.camera.far = 4000;
    this.camera.updateProjectionMatrix();

    const scale = dist * 0.0075;
    for (const m of this.missions) {
      m.marker.scale.setScalar(Math.max(scale, 0.004));
      m.marker.visible = m.visible;
    }
    for (const m of this.moons) {
      const vis = this.moonVisible(m);
      m.mesh.visible = vis;
      m.ring.visible = this.showOrbits && vis;
    }
    this.renderer.render(this.scene, this.camera);
    this.frames++;
    this.updateLabels();
  }

  private updateLabels(): void {
    const rect = this.opts.canvas.getBoundingClientRect();
    const place = (el: HTMLElement, world: THREE.Vector3, show: boolean, offsetPx: number) => {
      if (!show || !this.showLabels) {
        el.style.display = "none";
        return;
      }
      const p = this.tmp.copy(world).project(this.camera);
      if (p.z > 1 || Math.abs(p.x) > 1.05 || Math.abs(p.y) > 1.05) {
        el.style.display = "none";
        return;
      }
      el.style.display = "block";
      const x = ((p.x + 1) / 2) * rect.width;
      const y = ((1 - p.y) / 2) * rect.height;
      el.style.transform = `translate(${x + offsetPx}px, ${y}px) translateY(-50%)`;
    };
    place(this.sunLabel, new THREE.Vector3(), true, 14);
    for (const p of this.planets) {
      // Labels sit to the right of the body by about its on-screen radius plus a gap.
      const px = this.screenRadius(p.radius, p.group.position);
      place(p.label, p.group.position, true, Math.min(px, 400) + 8);
    }
    for (const m of this.moons) {
      const show = this.focusId === m.data.name || this.focusId === m.parent.data.name || this.camera.position.distanceTo(m.parent.group.position) < m.parent.radius * 14;
      const world = m.mesh.getWorldPosition(new THREE.Vector3());
      place(m.label, world, show && m.mesh.visible, this.screenRadius(m.radius, world) + 6);
    }
    for (const ms of this.missions) place(ms.label, ms.position, ms.visible, 10);
  }

  private screenRadius(radius: number, world: THREE.Vector3): number {
    const dCam = this.camera.position.distanceTo(world);
    const h = this.opts.canvas.clientHeight;
    return (radius / (Math.tan((this.camera.fov * Math.PI) / 360) * dCam)) * (h / 2);
  }

  dispose(): void {
    this.renderer.dispose();
  }
}
