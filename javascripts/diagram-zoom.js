// A diagram of scripts/docs/diagrams opens full screen on a click (or Enter), and closes on a click or Esc (#1985).
// Delegated on the document, so it works across Material's instant navigation.
(function () {
  function close() {
    const open = document.querySelector("figure.diagram.zoomed");
    if (open) {
      open.classList.remove("zoomed");
      document.documentElement.classList.remove("diagram-zoomed");
    }
  }

  function toggle(figure) {
    if (figure.classList.contains("zoomed")) {
      close();
      return;
    }
    close();
    figure.classList.add("zoomed");
    document.documentElement.classList.add("diagram-zoomed");
  }

  function prepare() {
    for (const figure of document.querySelectorAll("figure.diagram:not([tabindex])")) {
      figure.setAttribute("tabindex", "0");
      figure.setAttribute("title", "Click to zoom; Esc to close");
    }
  }

  document.addEventListener("click", (event) => {
    const figure = event.target.closest("figure.diagram");
    if (figure) toggle(figure);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
    if (event.key === "Enter" && event.target.matches && event.target.matches("figure.diagram")) toggle(event.target);
  });
  if (window.document$) window.document$.subscribe(prepare);
  else document.addEventListener("DOMContentLoaded", prepare);
})();
