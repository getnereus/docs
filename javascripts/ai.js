// AI affordances (docs/agent/docs.md, #1986): a row of buttons before the article (Copy page, Copy prompt, View as
// Markdown, Open in Claude, Reader) and a Copy prompt beside the copy button of each bash block. The prompts come from
// ai.json (scripts/docs/prompts.yaml); this file holds no wording of its own.
(() => {
  const script = document.querySelector('script[src*="javascripts/ai.js"]');
  if (!script) return;
  // The site root: the script lives at <root>/javascripts/ai.js.
  const root = new URL("../", script.src);
  let loaded = null;

  const load = () => {
    loaded = loaded || fetch(new URL("ai.json", root)).then((response) => response.json());
    return loaded;
  };

  const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, name) => (name in values ? values[name] : ""));

  async function copy(text, button) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      const area = document.createElement("textarea");
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    const label = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => { button.textContent = label; }, 1500);
  }

  function button(label, onclick) {
    const node = document.createElement("button");
    node.type = "button";
    node.className = "doc-ai-button";
    node.textContent = label;
    node.addEventListener("click", onclick);
    return node;
  }

  function anchor(label, href) {
    const node = document.createElement("a");
    node.className = "doc-ai-button";
    node.textContent = label;
    node.href = href;
    return node;
  }

  // The page's key in ai.json: its path below the site root ("" for the home page).
  function key() {
    let path = location.pathname.slice(root.pathname.length).replace(/index\.html$/, "");
    if (path && !path.endsWith("/") && !path.endsWith(".html")) path += "/";
    return path;
  }

  const heading = (node) => {
    const copyNode = node.cloneNode(true);
    copyNode.querySelectorAll(".headerlink").forEach((link) => link.remove());
    return copyNode.textContent.trim();
  };

  function exampleButtons(article, data, page) {
    let section = "";
    article.querySelectorAll("h2, div.language-bash").forEach((node) => {
      if (node.tagName === "H2") {
        section = heading(node);
        return;
      }
      if (node.dataset.docAi) return;
      node.dataset.docAi = "on";
      const next = node.nextElementSibling;
      const output = next && next.classList.contains("output") ? next.querySelector("pre").textContent.trim() : "";
      const command = node.querySelector("pre").textContent.trim();
      const example = button("Ask AI", () => {
        const prompt = fill(data.prompts.example, { title: page.title, section, command, output });
        copy(prompt, example);
      });
      example.classList.add("doc-ai-example");
      example.title = "Copy a prompt that asks an AI about this example";
      // Below the example, after its output when it has one, so the command and what it prints stay together.
      (next && next.classList.contains("output") ? next : node).insertAdjacentElement("afterend", example);
    });
  }

  function row(data, page) {
    const md = new URL(page.md, root).href;
    const absolute = data.site_url ? data.site_url + page.md : md;
    const prompt = () => fill(data.prompts.page, { url: absolute, title: page.title, goal: page.goal });
    const row = document.createElement("div");
    row.className = "doc-ai-row";
    const copyPage = button("Copy page", async () => copy(await (await fetch(md)).text(), copyPage));
    const copyPrompt = button("Copy prompt", () => copy(prompt(), copyPrompt));
    row.append(copyPage, copyPrompt, anchor("View as Markdown", md));
    if (data.site_url) row.append(anchor("Open in Claude", "https://claude.ai/new?q=" + encodeURIComponent(prompt())));
    row.append(button("Reader", () => window.nereusReader && window.nereusReader.toggle()));
    if (window.nereusFont && window.nereusFont.buttons) row.append(...window.nereusFont.buttons());
    return row;
  }

  async function render() {
    document.querySelectorAll(".doc-ai-row").forEach((node) => node.remove());
    const article = document.querySelector("article");
    if (!article) return;
    let data;
    try { data = await load(); } catch (error) { return; }
    const page = data.pages[key()];
    if (!page) return;
    // Home is the way in, not a page to copy or read: no row there.
    if (key() !== "") article.parentElement.insertBefore(row(data, page), article);
    exampleButtons(article, data, page);
  }

  if (typeof document$ !== "undefined") document$.subscribe(render);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render);
  else render();
})();
