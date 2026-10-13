export interface Command {
  label: string;
  /** Right-aligned secondary text: the kind of command, or its shortcut. */
  hint: string;
  run: () => void;
}

/** Rank a label against a query: lower is better, null means no match. */
export function score(label: string, query: string): number | null {
  const l = label.toLowerCase();
  const q = query.trim().toLowerCase();
  if (!q) return 0;
  if (l.startsWith(q)) return 0;
  const word = l.split(/[\s:-]+/).findIndex((w) => w.startsWith(q));
  if (word > 0) return 1;
  if (l.includes(q)) return 2;
  if (q.length < 3) return null;
  let i = 0;
  for (const ch of l) if (ch === q[i] && ++i === q.length) return 3;
  return null;
}

/** Accessible combobox (ARIA 1.2 list autocomplete) inside a modal dialog. */
export function createPalette(dialog: HTMLDialogElement, getCommands: () => Command[]): { open: () => void; close: () => void } {
  const input = dialog.querySelector<HTMLInputElement>("input")!;
  const list = dialog.querySelector<HTMLUListElement>("ul")!;
  let shown: Command[] = [];
  let active = 0;

  const setActive = (i: number) => {
    if (!shown.length) return;
    active = (i + shown.length) % shown.length;
    list.querySelectorAll("li").forEach((li, n) => li.setAttribute("aria-selected", String(n === active)));
    const li = list.children[active] as HTMLElement;
    input.setAttribute("aria-activedescendant", li.id);
    li.scrollIntoView({ block: "nearest" });
  };

  const render = () => {
    const q = input.value;
    shown = getCommands()
      .map((c, order) => ({ c, s: score(c.label, q), order }))
      .filter((x) => x.s !== null)
      .sort((a, b) => a.s! - b.s! || a.order - b.order)
      .map((x) => x.c);
    list.replaceChildren(
      ...shown.map((c, n) => {
        const li = document.createElement("li");
        li.id = `pal-opt-${n}`;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", "false");
        const name = document.createElement("span");
        name.textContent = c.label;
        const hint = document.createElement("span");
        hint.className = "hint";
        hint.textContent = c.hint;
        li.append(name, hint);
        li.addEventListener("pointermove", () => active !== n && setActive(n));
        li.addEventListener("click", () => choose(n));
        return li;
      }),
    );
    if (!shown.length) {
      const li = document.createElement("li");
      li.className = "none";
      li.textContent = "Nothing matches. Try a planet, moon, mission, tour or date.";
      list.appendChild(li);
      input.removeAttribute("aria-activedescendant");
    } else setActive(0);
  };

  const close = () => {
    if (dialog.open) dialog.close();
  };
  const choose = (n: number) => {
    const c = shown[n];
    if (!c) return;
    close();
    c.run();
  };

  input.addEventListener("input", render);
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") (e.preventDefault(), setActive(active + 1));
    else if (e.key === "ArrowUp") (e.preventDefault(), setActive(active - 1));
    else if (e.key === "Home" && e.ctrlKey) (e.preventDefault(), setActive(0));
    else if (e.key === "End" && e.ctrlKey) (e.preventDefault(), setActive(shown.length - 1));
    else if (e.key === "Enter") (e.preventDefault(), choose(active));
  });
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) close();
  });

  return {
    open: () => {
      if (dialog.open) return;
      input.value = "";
      render();
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
      input.focus();
    },
    close,
  };
}
