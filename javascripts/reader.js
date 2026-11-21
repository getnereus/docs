// Reader mode for phones (docs/agent/docs.md, #1986): `data-reader="on"` on <html> hides the header, tabs, sidebars,
// footer and the AI button row (CSS in extra.css) and widens the article. `?reader=1|0` wins over the stored choice
// (localStorage["nereus.reader"]); Esc or the exit button (.doc-reader-exit) leaves.
(() => {
  const KEY = "nereus.reader";

  // query: "?reader=1" (or ""), stored: "on", "off" or null. Returns "on" or "off".
  function readerState(query, stored) {
    const asked = new URLSearchParams(query || "").get("reader");
    if (asked === "1") return "on";
    if (asked === "0") return "off";
    return stored === "on" ? "on" : "off";
  }

  const read = () => {
    try { return localStorage.getItem(KEY); } catch (error) { return null; }
  };
  const write = (state) => {
    try { localStorage.setItem(KEY, state); } catch (error) { /* private window: the choice lasts for this page only */ }
  };

  const api = { readerState };
  if (typeof window !== "undefined") window.nereusReader = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  const get = () => (root.dataset.reader === "on" ? "on" : "off");
  let exit = null;

  function set(state) {
    root.dataset.reader = state;
    write(state);
    if (exit) exit.hidden = state !== "on";
    // The URL's ?reader= would win on reload: drop it once the choice is made.
    const url = new URL(location.href);
    if (url.searchParams.has("reader")) {
      url.searchParams.delete("reader");
      history.replaceState(history.state, "", url);
    }
  }

  Object.assign(api, { get, set, toggle: () => set(get() === "on" ? "off" : "on") });

  // Early: the attribute is set before the body is built on, so the page does not flash its chrome.
  root.dataset.reader = readerState(location.search, read());
  write(root.dataset.reader);

  function build() {
    exit = document.createElement("button");
    exit.type = "button";
    exit.className = "doc-reader-exit";
    exit.textContent = "Exit reader";
    exit.setAttribute("aria-label", "Exit reader mode");
    exit.hidden = get() !== "on";
    exit.addEventListener("click", () => set("off"));
    document.body.appendChild(exit);
  }

  if (document.body) build();
  else document.addEventListener("DOMContentLoaded", build);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && get() === "on") set("off");
  });
})();
