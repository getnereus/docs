// Terminal look for command blocks (reused from the wasp-idp docs): a `$` prompt on each command, options
// and their values in their own colors, and ✓/✗ lines of the output in green/red.
// The prompt is a CSS pseudo-element, so the copy button still copies the commands only.
(() => {
  // Options that take no value: the word after them is an argument, not their value.
  const FLAGS = new Set(["--yes", "--dry-run", "--force", "--generate-file", "--create-cluster",
    "--use-current-context", "--editable", "--keep-cluster", "--all-namespaces", "--help"]);
  const OPERATORS = new Set(["|", "||", "&&", ";", ">", ">>", "<", "\\", "--"]);
  // Reserved words of the shell, where a command would stand (`for`, `do`, `done`, `if`, `then` ...).
  const KEYWORDS = new Set(["for", "while", "until", "do", "done", "if", "then", "elif", "else", "fi", "case", "esac"]);
  // Verbs of the platform and kubectl commands: the word before one is the noun, the first argument
  // after it is the object; both are shown in bold.
  const VERBS = new Set(["install", "uninstall", "list", "add", "get", "delete", "create", "describe", "import"]);

  const escape = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const span = (kind, text) => `<span class="t-${kind}">${escape(text)}</span>`;

  // Words and the spaces between them, keeping quoted strings whole.
  function words(line) {
    return line.match(/\s+|'[^']*'|"[^"]*"|[^\s'"]+(?:'[^']*'|"[^"]*")?[^\s'"]*/g) || [];
  }

  function shell(text) {
    let continued = false;
    // Open `do`/`then` blocks of a loop or an if: their lines and the closing `done`/`fi` belong to the
    // command that opened them, so they get no prompt of their own.
    let depth = 0;
    // Delimiter of an open here-document: its lines are input to the command, not commands.
    let heredoc = null;
    return text.replace(/\n$/, "").split("\n").map((line) => {
      if (heredoc !== null) {
        if (line === heredoc) heredoc = null;
        return '<span class="t-heredoc"></span>' + escape(line);
      }
      const opened = line.match(/<<-?\s*['"]?(\w+)['"]?/);
      if (opened) heredoc = opened[1];
      if (!line.trim()) {
        continued = false;
        return "";
      }
      if (/^\s*#/.test(line)) return span("comment", line);
      const closes = /^\s*(done|fi)\b/.test(line);
      if (closes && depth > 0) depth -= 1;
      // A line inside a block still opens with a command (colored), only without the prompt.
      const fresh = !continued;
      const start = fresh && depth === 0 && !closes;
      continued = /\\\s*$/.test(line);
      if (/\b(do|then)\s*$/.test(line)) depth += 1;
      let first = fresh;
      let expectValue = false;
      const parts = words(line);
      // The `in` of `for <name> in`: the word after the loop variable.
      let loopVariable = false;
      // Noun and object of the command: the word before the verb and the first argument after it.
      const bold = new Set();
      if (start) {
        const plain = parts.map((word, index) => [word, index]).filter(([word]) => !/^\s+$/.test(word));
        const verb = plain.findIndex(([word], position) => position > 0 && VERBS.has(word));
        if (verb > 0) {
          if (verb > 1) bold.add(plain[verb - 1][1]);
          const object = plain.slice(verb + 1).find(([word]) => !word.startsWith("-") && !OPERATORS.has(word));
          if (object) bold.add(object[1]);
        }
      }
      const html = parts.map((word, index) => {
        if (/^\s+$/.test(word)) return word;
        if (OPERATORS.has(word)) {
          expectValue = false;
          if (word === "|" || word === "&&" || word === "||" || word === ";") first = true;
          return span("op", word);
        }
        if (first) {
          // After `do`/`then` a command can follow on the same line (`do echo`), so it stays first.
          if (KEYWORDS.has(word)) {
            first = word !== "for" && word !== "case";
            loopVariable = word === "for";
            return span("kw", word);
          }
          first = false;
          return span("cmd", word);
        }
        if (loopVariable) {
          loopVariable = false;
          return span("arg", word);
        }
        if (word === "in" && parts.slice(0, index).some((w) => w === "for" || w === "case")) return span("kw", word);
        if (word === "do" || word === "then") return span("kw", word);
        if (word.startsWith("-")) {
          expectValue = word.startsWith("--") && !FLAGS.has(word) && !word.includes("=");
          return span("opt", word);
        }
        if (expectValue) {
          expectValue = false;
          return span("val", word);
        }
        if (bold.has(index)) return span("key", word);
        if (/^['"$]/.test(word)) return span("val", word);
        return span("arg", word);
      }).join("");
      return (start ? '<span class="t-prompt"></span>' : '<span class="t-indent"></span>') + html;
    }).join("\n") + "\n";
  }

  function output(text) {
    return text.replace(/\n$/, "").split("\n").map((line) => {
      const head = line.trimStart();
      if (head.startsWith("✓")) return span("ok", line);
      if (head.startsWith("✗")) return span("err", line);
      if (head.startsWith("→")) return span("info", line);
      return escape(line);
    }).join("\n") + "\n";
  }

  function paint() {
    document.querySelectorAll(".highlight.language-bash pre > code:not([data-terminal])").forEach((code) => {
      code.innerHTML = shell(code.textContent);
      code.dataset.terminal = "";
    });
    document.querySelectorAll(".highlight.output pre > code:not([data-terminal])").forEach((code) => {
      code.innerHTML = output(code.textContent);
      code.dataset.terminal = "";
    });
  }

  if (typeof document$ !== "undefined") document$.subscribe(paint);
  else document.addEventListener("DOMContentLoaded", paint);
})();
