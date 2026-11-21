"""The public follow page under the portal's exact policy, in headless Chromium (#1697, #1760): a phone and a projector show
the deck as the engine renders it and follow a scripted stream, each step within a second, with zero CSP violations. A−/A+
change one follower only and stay on its device; the keys that change the step do nothing there. The server here is a
stand-in for the portal and the API: it serves the portal's own follow.html, follow.js, follow.css, deck.css and deck.js
with portal.csp(), the scene's deck rendered with --split at /v1/presentations/follow/<code>/deck, and a scripted SSE at
/v1/presentations/follow/<code>. Skips when there is no browser."""
import http.server
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = HERE.parents[1]
CODE = "K7Q4"
DECK = REPO / "test" / "scene-presentations-deck.yaml"
WITHIN = 1000


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


portal = load("portal", REPO / "controllers" / "nereus-portal" / "portal.py")
ro = load("render_outline_follow", HERE / "render-outline")


class Stand:
  """The portal's page, the deck's page and a scripted stream of one Session."""

  def __init__(self, directory):
    self.clients: list[queue.Queue] = []
    self.lock = threading.Lock()
    self.sequence = 0
    self.opened = 0
    self.cookies: list[str] = []
    stand = self
    subprocess.run([sys.executable, str(HERE / "render-outline"), str(DECK), "--split", "--output", str(directory / "deck.html")],
                   check=True, capture_output=True)
    deck = (directory / "deck.html").read_bytes()
    self.steps = ro.deck_steps(deck.decode())
    names = ("follow.html", "follow.js", "follow.css", "deck.css", "deck.js", "follow-qr.js", "vendor/qrcode-generator-2.0.4.js")
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
        if path == f"/p/{CODE}":
          self.secure(200, "text/html; charset=utf-8", files["/follow.html"].read_bytes())
        elif path in files:
          self.secure(200, portal.content_type(files[path]), files[path].read_bytes())
        elif path == f"/v1/presentations/follow/{CODE}/deck":
          self.secure(200, "text/html; charset=utf-8", deck)
        elif path == f"/v1/presentations/follow/{CODE}":
          self.stream()
        else:
          self.secure(404, "text/plain", b"not found\n")

      def stream(self):
        mine: queue.Queue = queue.Queue()
        with stand.lock:
          stand.clients.append(mine)
          stand.opened += 1
          stand.cookies.append(self.headers.get("Cookie") or "")
          first = stand.state()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
          self.wfile.write(b"retry: 2000\n\n")
          self.wfile.write(frame("state", first))
          self.wfile.flush()
          while True:
            try:
              self.wfile.write(mine.get(timeout=5))
            except queue.Empty:
              self.wfile.write(b"event: hb\ndata: {}\n\n")
            self.wfile.flush()
        except OSError:
          pass

    self.step = 0
    # More of the state (the talk's clock, #1709), for a test that needs the questions' turn (#1715).
    self.extra: dict = {}
    self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.httpd.daemon_threads = True
    threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
    self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

  def state(self):
    return {"code": CODE, "step": self.step, "steps": self.steps, "sequence": self.sequence, "slide": {"title": "", "message": ""}, **self.extra}

  def go(self, step):
    with self.lock:
      self.step, self.sequence = step, self.sequence + 1
      data = frame("step", self.state())
      for client in self.clients:
        client.put(data)

  def close(self):
    self.httpd.shutdown()


def frame(kind, state):
  return f"event: {kind}\nid: {state['sequence']}\ndata: {json.dumps(state)}\n\n".encode()


# The CSP listener, and the engine's own report of the step on screen (nereus-step).
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


def shows(page, step):
  """Waits up to WITHIN ms for the engine of the page to be on a step, and returns how long it took."""
  started = time.monotonic()
  page.wait_for_function("n => window.__step === n", arg=step, timeout=WITHIN)
  return time.monotonic() - started


def open_pages(playwright, stand):
  browser = chromium(playwright)
  phone_options = {key: value for key, value in playwright.devices["iPhone 13"].items() if key != "default_browser_type"}
  phone_context = browser.new_context(**phone_options, locale="en-US")
  projector_context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
  pages, console, errors = {}, [], []
  for name, context, search in (("phone", phone_context, ""), ("projector", projector_context, "?projector")):
    page = context.new_page()
    page.on("console", lambda message, name=name: console.append((name, message.type, message.text)))
    page.on("pageerror", lambda error, name=name: errors.append((name, str(error))))
    page.add_init_script(LISTENER)
    page.goto(f"{stand.url}/p/{CODE}{search}", wait_until="load")
    pages[name] = page
  return browser, pages, console, errors


def test_a_phone_and_a_projector_follow_every_step_of_the_engine_within_a_second_with_no_csp_violation(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  shots = os.environ.get("NEREUS_SCREENSHOTS")
  try:
    with sync_api.sync_playwright() as playwright:
      browser, pages, console, errors = open_pages(playwright, stand)
      for name, page in pages.items():
        page.wait_for_function("document.documentElement.dataset.mode === 'follow' && document.querySelector('.slide.on')", timeout=5000)
        assert shows(page, 0) < WITHIN / 1000, name
      for step in range(1, stand.steps):
        stand.go(step)
        for name, page in pages.items():
          assert shows(page, step) < WITHIN / 1000, f"{name} step {step}"
      # A burst: only the last one is on the screen when it settles.
      for step in (0, 1, 2):
        stand.go(step)
      for page in pages.values():
        shows(page, 2)
      phone, projector = pages["phone"], pages["projector"]
      assert phone.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "no horizontal scroll on a phone"
      assert not phone.locator("#full").is_visible()
      assert projector.locator("#full").is_visible()
      # The engine's controls that change the step are hidden; A−/A+ stay.
      for page in pages.values():
        assert not page.locator("#joy").is_visible() and not page.locator("#nextBtn").is_visible()
        assert page.locator("#zoomIn").is_visible()
      if shots:
        pathlib.Path(shots).mkdir(parents=True, exist_ok=True)
        phone.screenshot(path=f"{shots}/follow-phone.png")
        projector.screenshot(path=f"{shots}/follow-projector.png")
      violations = {name: page.evaluate("window.__csp") for name, page in pages.items()}
      browser.close()
  finally:
    stand.close()
  policy = [item for item in console if "content security policy" in item[2].lower()]
  assert violations == {"phone": [], "projector": []}
  assert policy == [] and errors == []
  assert stand.opened == 2, "one stream per page, none reopened"


def test_a_plus_changes_one_follower_only_and_stays_on_its_device_and_its_keys_never_move_the_step(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser, pages, _, errors = open_pages(playwright, stand)
      phone, projector = pages["phone"], pages["projector"]
      for page in pages.values():
        page.wait_for_function("window.__step === 0", timeout=5000)
      size = "() => getComputedStyle(document.body).fontSize"
      before = {name: page.evaluate(size) for name, page in pages.items()}
      phone.locator("#zoomIn").click()
      phone.locator("#zoomIn").click()
      assert phone.evaluate(size) != before["phone"]
      assert projector.evaluate(size) == before["projector"]
      # The keys and the swipe of the speaker do nothing on a follower.
      for key in ("ArrowDown", "ArrowRight", "End", "Home", "r"):
        phone.keyboard.press(key)
      assert phone.evaluate("window.__step") == 0
      # The size stays on this device, through a reload.
      grown = phone.evaluate(size)
      phone.reload(wait_until="load")
      phone.wait_for_function("window.__step === 0", timeout=5000)
      assert phone.evaluate(size) == grown
      browser.close()
  finally:
    stand.close()
  assert errors == []


def test_the_watchdog_listener_sees_a_violation_the_policy_raises(tmp_path):
  """The control: an inline script under the same policy raises securitypolicyviolation, or the test above proves nothing."""
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      page = browser.new_page()
      page.add_init_script(LISTENER)
      page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      page.evaluate("() => { const s = document.createElement('script'); s.textContent = 'window.x = 1'; document.head.appendChild(s); }")
      page.wait_for_function("window.__csp.length > 0", timeout=2000)
      assert page.evaluate("window.__csp")[0].startswith("script-src")
      browser.close()
  finally:
    stand.close()


UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


def test_a_device_keeps_its_anonymous_id_across_visits_and_a_cleared_one_gets_a_new_one(tmp_path):
  """#1714: the first visit makes a random id and keeps it in localStorage; the stream gets it in a cookie, never in its
  URL; a returning visit sends the same; a device whose site data was cleared sends a new one."""
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phone = {key: value for key, value in playwright.devices["iPhone 13"].items() if key != "default_browser_type"}
      context = browser.new_context(**phone, locale="en-US")
      page = context.new_page()
      page.add_init_script(LISTENER)

      def visit():
        before = len(stand.cookies)
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        page.wait_for_function("() => window.__step !== null", timeout=WITHIN)
        deadline = time.monotonic() + 5
        while len(stand.cookies) == before and time.monotonic() < deadline:
          time.sleep(0.05)
        kept = page.evaluate("() => localStorage.getItem('nereus-device')")
        sent = stand.cookies[-1]
        return kept, sent

      first, sent = visit()
      assert UUID.fullmatch(first), first
      assert sent == f"nereus_device={first}"
      again, sent = visit()
      assert again == first and sent == f"nereus_device={first}"
      page.evaluate("() => localStorage.clear()")
      context.clear_cookies()
      cleared, sent = visit()
      assert UUID.fullmatch(cleared) and cleared != first
      assert sent == f"nereus_device={cleared}"
      browser.close()
  finally:
    stand.close()
