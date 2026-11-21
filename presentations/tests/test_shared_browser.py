"""The public link of a deck under the portal's exact policy, in headless Chromium (#1704): /d/<link> shows the deck as
the engine renders it, and the viewer moves through every step on their own (the engine's own mode, every control), with
zero CSP violations; an expired link and an unknown one say so. The server here stands in for the portal and the API: it
serves the portal's own shared.html, shared.js, follow.js, follow.css, deck.css and deck.js with portal.csp(), and the
scene's deck rendered with --split at /v1/presentations/links/<link>/deck. Skips when there is no browser."""
import http.server
import importlib.machinery
import importlib.util
import pathlib
import subprocess
import sys
import threading

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = HERE.parents[1]
LINK, EXPIRED, UNKNOWN = "9FK2PQ7XMZ4HR8TV3WKN6PQ2JD", "2345678923MN7XC4QR9TBV2WKH", "ZZZZZZZZZZZZZZZZZZZZZZZZZZ"
DECK = REPO / "test" / "scene-presentations-deck.yaml"


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


portal = load("portal", REPO / "controllers" / "nereus-portal" / "portal.py")
ro = load("render_outline_shared", HERE / "render-outline")


class Stand:
  """The portal's page and the deck of one link; EXPIRED answers 410 and any other link 404."""

  def __init__(self, directory):
    subprocess.run([sys.executable, str(HERE / "render-outline"), str(DECK), "--split", "--output", str(directory / "deck.html")],
                   check=True, capture_output=True)
    deck = (directory / "deck.html").read_bytes()
    self.steps = ro.deck_steps(deck.decode())
    names = ("shared.html", "shared.js", "follow.js", "follow.css", "deck.css", "deck.js")
    files = {f"/{name}": (portal.STATIC / name) for name in names}

    class Handler(http.server.BaseHTTPRequestHandler):
      def log_message(self, *args):
        pass

      def secure(self, code, kind, data):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        for key, value in portal.headers("https://auth.example.com").items():
          self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

      def do_GET(self):
        path = self.path.split("?")[0]
        if portal.SHARED.fullmatch(path):
          self.secure(200, "text/html; charset=utf-8", files["/shared.html"].read_bytes())
        elif path in files:
          self.secure(200, portal.content_type(files[path]), files[path].read_bytes())
        elif path == f"/v1/presentations/links/{LINK}/deck":
          self.secure(200, "text/html; charset=utf-8", deck)
        elif path == f"/v1/presentations/links/{EXPIRED}/deck":
          self.secure(410, "application/json", b'{"error": {"code": "Expired"}}')
        else:
          self.secure(404, "application/json", b'{"error": {"code": "NotFound"}}')

    self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.httpd.daemon_threads = True
    threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
    self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

  def close(self):
    self.httpd.shutdown()


LISTENER = """
window.__csp = [];
window.__step = null;
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.effectiveDirective + ' ' + e.blockedURI), true);
document.addEventListener('nereus-step', e => { window.__step = e.detail.step; }, true);
"""


def chromium(playwright):
  failures = []
  for channel in (None, "chrome"):
    try:
      return playwright.chromium.launch(channel=channel)
    except Exception as error:
      failures.append(str(error).splitlines()[0])
  pytest.skip("no headless browser: run `uvx playwright install chromium-headless-shell` or install Chrome\n" + "\n".join(failures))


def reached(page, step):
  """Presses PageDown until the engine reports the step: a press while a command types only ends that animation."""
  for _ in range(4):
    page.keyboard.press("PageDown")
    try:
      page.wait_for_function("n => window.__step === n", arg=step, timeout=1000)
      return
    except Exception:
      pass
  raise AssertionError(f"step {step} never reached: on {page.evaluate('window.__step')}, hash {page.evaluate('location.hash')}")


def test_a_phone_walks_every_step_of_a_shared_deck_on_its_own_with_no_csp_violation(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      options = {key: value for key, value in playwright.devices["iPhone 13"].items() if key != "default_browser_type"}
      page = browser.new_context(**options, locale="en-US").new_page()
      errors, outside = [], []
      page.on("pageerror", lambda error: errors.append(str(error)))
      page.on("request", lambda request: None if request.url.startswith(stand.url) else outside.append(request.url))
      page.add_init_script(LISTENER)
      page.goto(f"{stand.url}/d/{LINK}", wait_until="load")
      page.wait_for_function("document.documentElement.dataset.mode === 'view' && document.querySelector('.slide.on')", timeout=5000)
      assert page.locator("#status").text_content() == ""
      # The engine's own controls, the ones a follower does not have, are there.
      assert page.locator("#nextBtn").count() == 1
      for step in range(1, stand.steps):
        reached(page, step)
      assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "no horizontal scroll on a phone"
      assert page.evaluate("window.__csp") == []
      assert errors == [] and outside == []
      browser.close()
  finally:
    stand.close()


@pytest.mark.parametrize(("link", "words"), [
  (EXPIRED, "This link expired: ask the speaker for a new one."),
  (UNKNOWN, "This link opens no presentation."),
])
def test_an_expired_or_unknown_link_says_so(tmp_path, link, words):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      page = browser.new_context(locale="en-US").new_page()
      page.add_init_script(LISTENER)
      page.goto(f"{stand.url}/d/{link}", wait_until="load")
      page.wait_for_function("t => document.getElementById('status').textContent === t", arg=words, timeout=5000)
      assert page.evaluate("window.__csp") == [] and page.locator(".slide").count() == 0
      browser.close()
  finally:
    stand.close()
