/** Guided tours, same steps as orbit_sim/tours.py. */

export type SceneMode = "full_system" | "inner_worlds" | "outer_worlds" | "gas_giants" | "focus";

export interface TourStep {
  key: string;
  title: string;
  caption: string;
  scene: SceneMode;
  duration: number; // seconds
  focusBody?: string;
  jump?: JumpAction;
  scaleStory?: boolean;
}

export type JumpAction = "apollo" | "voyager" | "equinox" | "solstice" | "now" | "eclipse" | "webb";

export interface Tour {
  id: string;
  label: string;
  description: string;
  steps: TourStep[];
}

export const TOURS: Tour[] = [
  {
    id: "grand",
    label: "Grand Tour",
    description: "A pass from the rocky inner worlds out to the edge of the giant planets.",
    steps: [
      { key: "opening", title: "Solar System", caption: "The full architecture of the planetary system in one frame.", scene: "full_system", duration: 5 },
      { key: "inner", title: "Inner Worlds", caption: "Mercury through Mars reveal how tightly packed the rocky planets are.", scene: "inner_worlds", duration: 6 },
      { key: "earth", title: "Earth System", caption: "A close-up of Earth, the Moon and near-Earth exploration paths.", scene: "focus", duration: 6, focusBody: "Earth" },
      { key: "jupiter", title: "Gas Giant Scale", caption: "Jupiter dominates the outer system with its Galilean satellites.", scene: "focus", duration: 6, focusBody: "Jupiter" },
      { key: "saturn", title: "Rings in Motion", caption: "Saturn's ring plane and Titan bring the scene into cinematic territory.", scene: "focus", duration: 7, focusBody: "Saturn" },
      { key: "outer", title: "Outer Reach", caption: "Uranus and Neptune sit in immense stretches of empty space.", scene: "outer_worlds", duration: 6 },
      { key: "story", title: "Scale Story", caption: "This pass relaxes the compressed view toward a harsher sense of real distance.", scene: "full_system", duration: 7, scaleStory: true },
    ],
  },
  {
    id: "history",
    label: "Historic Dates",
    description: "Jumps through moments that changed how humanity sees the Solar System.",
    steps: [
      { key: "apollo", title: "Apollo 11", caption: "Humanity's first crewed lunar landing happened inside the Earth-Moon system.", scene: "focus", duration: 6, focusBody: "Earth", jump: "apollo" },
      { key: "voyager", title: "Voyager Era", caption: "Voyager 1 began the mission that redefined the outer planets.", scene: "gas_giants", duration: 6, jump: "voyager" },
      { key: "equinox", title: "Equinox Geometry", caption: "At equinox the solar lighting across Earth is especially legible.", scene: "inner_worlds", duration: 5, jump: "equinox" },
      { key: "solstice", title: "Solstice Tilt", caption: "Seasonal lighting shifts become obvious in planetary close-ups.", scene: "inner_worlds", duration: 5, jump: "solstice" },
      { key: "now", title: "Now", caption: "Return to the current live arrangement of the planets.", scene: "full_system", duration: 5, jump: "now" },
    ],
  },
];

export interface Bookmark {
  id: JumpAction;
  label: string;
  note: string;
  /** Resolves to a UTC instant; `ref` is the current simulated time. */
  at: (ref: number) => number;
}

export const BOOKMARKS: Bookmark[] = [
  { id: "now", label: "Now", note: "The live arrangement at this moment.", at: () => Date.now() },
  { id: "apollo", label: "Apollo 11 landing", note: "Apollo 11 lands in the Sea of Tranquility.", at: () => Date.UTC(1969, 6, 20, 20, 17) },
  { id: "voyager", label: "Voyager 1 launch", note: "Voyager 1 begins its outward grand tour.", at: () => Date.UTC(1977, 8, 5, 12, 56) },
  { id: "webb", label: "JWST at L2", note: "James Webb settles near the Earth-Sun L2 point.", at: () => Date.UTC(2022, 0, 24, 19, 0) },
  { id: "eclipse", label: "Eclipse 2024", note: "The 2024 total solar eclipse over North America.", at: () => Date.UTC(2024, 3, 8, 18, 18) },
  { id: "equinox", label: "Equinox", note: "March equinox of the displayed year: day and night are equal everywhere.", at: (ref) => Date.UTC(new Date(ref).getUTCFullYear(), 2, 20, 12) },
  { id: "solstice", label: "June solstice", note: "Earth's axial tilt is at a seasonal extreme.", at: (ref) => Date.UTC(new Date(ref).getUTCFullYear(), 5, 21, 12) },
];
