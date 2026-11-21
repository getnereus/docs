// Text size (owner, 2026-11-20): A− and A+ in the button row and beside "Exit reader" scale the article's text,
// one step at a time, from 85% to 160%. The choice lasts across pages (localStorage["nereus.font"]) and is applied
// before the body is built, as --doc-font-scale on <html> (CSS in extra.css), so the page does not jump.
(function () {
  const KEY = "nereus.font";
  const STEPS = [0.85, 1, 1.15, 1.3, 1.45, 1.6];

  // stored: a step index as text, or null; delta: -1, 0 or +1. Returns the new index, within STEPS.
  function fontStep(stored, delta) {
    const index = Number.parseInt(stored, 10);
    const current = Number.isInteger(index) && index >= 0 && index < STEPS.length ? index : STEPS.indexOf(1);
    return Math.min(STEPS.length - 1, Math.max(0, current + delta));
  }

  const api = { fontStep, STEPS };
  if (typeof window !== "undefined") window.nereusFont = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document === "undefined") return;

  function read() {
    try { return localStorage.getItem(KEY); } catch (error) { return null; }
  }
  function write(index) {
    try { localStorage.setItem(KEY, String(index)); } catch (error) { /* private window: this page only */ }
  }

  const root = document.documentElement;
  let index = fontStep(read(), 0);

  function apply() {
    root.style.setProperty("--doc-font-scale", String(STEPS[index]));
    document.querySelectorAll(".doc-font-smaller").forEach((node) => { node.disabled = index === 0; });
    document.querySelectorAll(".doc-font-larger").forEach((node) => { node.disabled = index === STEPS.length - 1; });
  }

  function change(delta) {
    index = fontStep(String(index), delta);
    write(index);
    apply();
  }

  // The two buttons, for the row (ai.js) and for reader mode.
  function buttons() {
    const make = (label, name, delta, className) => {
      const node = document.createElement("button");
      node.type = "button";
      node.className = className;
      node.textContent = label;
      node.setAttribute("aria-label", name);
      node.title = name;
      node.addEventListener("click", () => change(delta));
      return node;
    };
    const nodes = [make("A−", "Smaller text", -1, "doc-font-smaller"), make("A+", "Larger text", 1, "doc-font-larger")];
    nodes[0].disabled = index === 0;
    nodes[1].disabled = index === STEPS.length - 1;
    return nodes;
  }

  Object.assign(api, { buttons, smaller: () => change(-1), larger: () => change(1) });
  apply();

  // Reader mode hides the row: a second pair sits beside "Exit reader" (shown only in reader mode, by CSS).
  function build() {
    const group = document.createElement("div");
    group.className = "doc-reader-font";
    group.append(...buttons());
    document.body.appendChild(group);
  }

  if (document.body) build();
  else document.addEventListener("DOMContentLoaded", build);
})();
