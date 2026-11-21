"""The portal mode of the renderer (#1693): an HTML, a deck.css and a deck.js, so a deck fits the portal's CSP."""
import http.server
import importlib.machinery
import importlib.util
import pathlib
import re
import subprocess
import sys
import threading
from html.parser import HTMLParser

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = HERE.parents[1]


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


ro = load("render_outline", HERE / "render-outline")
portal = load("portal", REPO / "controllers" / "nereus-portal" / "portal.py")

DECKS = ("presentations-reef", "storytelling")


class Inline(HTMLParser):
  """Every piece of markup the policy `default-src 'self'` refuses: inline scripts, style blocks, style attributes,
  event-handler attributes."""

  def __init__(self):
    super().__init__()
    self.found = []

  def handle_starttag(self, tag, attrs):
    attrs = dict(attrs)
    if tag == "script" and "src" not in attrs and attrs.get("type") != "application/json":
      self.found.append("inline <script>")
    if tag == "style":
      self.found.append("<style> block")
    if "style" in attrs:
      self.found.append(f"style attribute on <{tag}>")
    self.found += [f"{name} handler on <{tag}>" for name in attrs if name.startswith("on")]


def inline_markup(page):
  parser = Inline()
  parser.feed(page)
  return parser.found


def render(tmp_path, name, *options):
  output = tmp_path / f"{name}.html"
  subprocess.run([sys.executable, str(HERE / "render-outline"), str(HERE / f"{name}.yaml"), "--output", str(output), *options],
                 check=True, capture_output=True, text=True)
  return output


def test_the_joystick_grips_are_placed_by_classes_not_style_attributes():
  page = ro.render_html(yaml.safe_load((HERE / "storytelling.yaml").read_text()), HERE)
  for corner in ("tl", "tr", "bl", "br"):
    assert f'<i class="grip {corner}"></i>' in page
    assert f".joy .grip.{corner}" in ro.CSS
  assert 'class="grip" style=' not in page


def test_the_self_contained_mode_stays_the_default(tmp_path):
  output = render(tmp_path, "storytelling")
  page = output.read_text()
  assert f"<style>{ro.CSS}</style>" in page
  assert f"<script>{ro.SCRIPT}</script>" in page
  assert sorted(path.name for path in tmp_path.iterdir()) == ["storytelling.html"]


@pytest.mark.parametrize("name", DECKS)
def test_the_portal_mode_writes_the_style_and_the_script_as_their_own_files(tmp_path, name):
  output = render(tmp_path, name, "--split")
  page = output.read_text()
  assert '<link rel="stylesheet" href="deck.css">' in page
  assert '<script src="deck.js"></script>' in page
  assert (tmp_path / "deck.css").read_text() == ro.CSS
  assert (tmp_path / "deck.js").read_text() == ro.SCRIPT
  assert inline_markup(page) == []


def test_the_self_contained_mode_is_what_the_portal_mode_refuses(tmp_path):
  assert sorted(set(inline_markup(render(tmp_path, "storytelling").read_text()))) == ["<style> block", "inline <script>"]


# ── The browser: the portal's exact policy, headless Chromium ──

def serve(directory, policy):
  class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, directory=str(directory), **kwargs)

    def end_headers(self):
      self.send_header("Content-Security-Policy", policy)
      super().end_headers()

    def log_message(self, *args):
      pass

  server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
  threading.Thread(target=server.serve_forever, daemon=True).start()
  return server


LISTENER = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.effectiveDirective + ' ' + e.blockedURI), true);
"""

# Walks every slide and step of both decks, both languages, the theme, the notes, the zoom and the joystick: what the
# script does at run time is checked too, not only what the parser meets.
DRIVE = """
async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const key = k => document.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true}));
  for (const k of ['l', 'l', 't', 'n', 'n', 'i', 'Escape', '+', '-']) { key(k); await wait(10); }
  for (const id of ['zoomIn', 'zoomOut', 'themeBtn', 'langBtn', 'langBtn', 'clearBtn', 'restartBtn', 'joyClear', 'notesBtn', 'nzIn', 'nzOut', 'npx'])
    document.getElementById(id).click();
  const joy = document.getElementById('joy');
  for (const t of ['pointerdown', 'pointermove', 'pointerup']) joy.dispatchEvent(new PointerEvent(t, {clientX: 100, clientY: 100, bubbles: true}));
  let walked = 0;
  for (const deck of ['main', 'refs']) {
    const slides = document.querySelectorAll(`[data-deck="${deck}"] > .slide`).length;
    for (let s = 0; s < slides; s++, walked++) {
      for (let i = 0; i < 40; i++) key('ArrowDown');
      await wait(5);
      key('ArrowRight');
    }
    key('d'); await wait(10);
  }
  return walked;
}
"""


def chromium(playwright):
  """Playwright's own Chromium when it was downloaded, else the Chrome of the host: nothing is installed for the test."""
  failures = []
  for channel in (None, "chrome"):
    try:
      return playwright.chromium.launch(channel=channel)
    except Exception as error:
      failures.append(str(error).splitlines()[0])
  pytest.fail("no headless browser: run `uvx playwright install chromium-headless-shell` or install Chrome\n" + "\n".join(failures))


def open_under_the_portal_policy(directory, name):
  """Loads the deck under the portal's exact policy, drives it, and returns the CSP violations and the page errors."""
  from playwright import sync_api
  server = serve(directory, portal.csp("https://auth.example.com"))
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      page = browser.new_page()
      errors = []
      page.on("pageerror", lambda error: errors.append(str(error)))
      page.add_init_script(LISTENER)
      page.goto(f"http://127.0.0.1:{server.server_address[1]}/{name}.html", wait_until="load")
      ran = page.evaluate("document.getElementById('num').textContent") != ""
      if ran:
        assert page.evaluate(DRIVE) > 0
      violations = page.evaluate("window.__csp")
      browser.close()
  finally:
    server.shutdown()
  return ran, violations, errors


@pytest.mark.parametrize("name", DECKS)
def test_a_deck_in_the_portal_mode_breaks_nothing_under_the_portal_policy(tmp_path, name):
  render(tmp_path, name, "--split")
  ran, violations, errors = open_under_the_portal_policy(tmp_path, name)
  assert ran  # the script ran
  assert (violations, errors) == ([], [])


def test_the_listener_sees_what_the_policy_refuses(tmp_path):
  """The control: the self-contained deck under the same policy must raise violations, or the test above proves nothing."""
  render(tmp_path, "storytelling")
  ran, violations, _ = open_under_the_portal_policy(tmp_path, "storytelling")
  assert not ran
  assert any(v.startswith("script-src") for v in violations)
  assert any(v.startswith("style-src") for v in violations)


def test_the_portal_serves_the_engine_s_own_style_and_script():
  """The follow page (#1760) loads deck.css and deck.js from the portal: they are the renderer's, byte for byte. After a change
  of the engine, render any deck with --split and copy both into controllers/nereus-portal/static/."""
  static = REPO / "controllers" / "nereus-portal" / "static"
  assert (static / ro.STYLE_FILE).read_text() == ro.CSS
  assert (static / ro.SCRIPT_FILE).read_text() == ro.SCRIPT
