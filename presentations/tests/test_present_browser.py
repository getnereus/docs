"""The speaker presents with the deck engine (#1761), in headless Chromium on a phone: the presentations reef's drive screen
(leagore/ui/drive.js) opens a Session in the portal's /present.html, framed from the same origin, and every move of the
engine (its pad, its index) is posted as the Session's step, the screen moving before the answer. The notes are on the
speaker's screen, the talk's time in the engine's top bar, and nothing breaks the portal's policy. The server here is a
stand-in for the portal and the API: the portal's own files with portal.headers() (framed for /present.html only), a host
page that mounts the drive screen as the portal's app does (with an api over fetch), and the Session's routes. Skips when
there is no browser."""
import http.server
import json
import pathlib
import subprocess
import sys
import threading

import pytest
from test_follow_browser import CODE, DECK, HERE, LISTENER, REPO, chromium, portal, ro

LEAGORE_UI = REPO / "controllers" / "leagore" / "ui"
SESSION = "scene-talk"
BASE = f"/v1/presentations/sessions/{SESSION}"
# The portal's app, in short: the drive screen with an api over fetch (screens.js gives a bound one, with the token).
HOST_HTML = b"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Host</title><script type="module" src="/host.js"></script></head><body></body></html>
"""
HOST_JS = b"""import "/drive.js";
const api = {
  get: (path) => fetch(path, { cache: "no-store" }),
  post: (path, body) => fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
};
const element = document.createElement("nereus-presentations-drive");
element.lang = "en";
element.api = api;
document.body.append(element);
"""


class Stand:
  """The portal's files, the host page, and one Session that takes the steps it is posted."""

  def __init__(self, directory):
    self.posts: list[int] = []
    self.step = 0
    self.lock = threading.Lock()
    stand = self
    subprocess.run([sys.executable, str(HERE / "render-outline"), str(DECK), "--split", "--output", str(directory / "deck.html")],
                   check=True, capture_output=True)
    deck = (directory / "deck.html").read_bytes()
    self.steps = ro.deck_steps(deck.decode())
    files = {f"/{name}": portal.STATIC / name for name in ("present.html", "present.js", "follow.js", "follow.css", "deck.css", "deck.js")}
    # Every file of leagore's ui/, as the portal forwards the files its contract lists (drive.js imports the QR encoder).
    files.update({f"/{path.name}": path for path in LEAGORE_UI.iterdir()})
    pages = {"/host.html": ("text/html; charset=utf-8", HOST_HTML), "/host.js": ("text/javascript; charset=utf-8", HOST_JS)}

    class Handler(http.server.BaseHTTPRequestHandler):
      def log_message(self, *args):
        pass

      def secure(self, code, kind, data, framed=False):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        for key, value in portal.headers("https://auth.example.com", framed).items():
          self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

      def json(self, body):
        self.secure(200, "application/json", json.dumps(body).encode())

      def do_GET(self):
        path = self.path.split("?")[0]
        if path in files:
          self.secure(200, portal.content_type(files[path]), files[path].read_bytes(), framed=path in portal.FRAMED)
        elif path in pages:
          self.secure(200, *pages[path])
        elif path == "/v1/presentations/sessions":
          self.json({"items": [{"metadata": {"name": SESSION}, "spec": {"presentation": "scene", "talk": "30m"}, "status": {"code": CODE}}]})
        elif path == BASE:
          self.json({"object": {"metadata": {"name": SESSION}, "spec": {"talk": "30m"}}, "state": stand.state(), "follow": f"/p/{CODE}",
                     "slides": [{"title": "", "message": ""}] * stand.steps})
        elif path == f"{BASE}/deck":
          self.secure(200, "text/html; charset=utf-8", deck)
        else:
          self.secure(404, "text/plain", b"not found\n")

      def do_POST(self):
        if self.path != f"{BASE}/step":
          self.secure(404, "text/plain", b"not found\n")
          return
        step = json.loads(self.rfile.read(int(self.headers["Content-Length"])))["step"]
        with stand.lock:
          stand.posts.append(step)
          stand.step = step
        self.json(stand.state())

    self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.httpd.daemon_threads = True
    threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
    self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

  def state(self):
    return {"code": CODE, "session": SESSION, "step": self.step, "steps": self.steps, "sequence": len(self.posts), "slide": {"title": "", "message": ""}}

  def close(self):
    self.httpd.shutdown()


def test_the_speaker_drives_the_session_with_the_engine_s_pad_and_index_on_a_phone(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  stand.step = 1
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phone = {key: value for key, value in playwright.devices["iPhone 13"].items() if key != "default_browser_type"}
      page = browser.new_context(**phone, locale="en-US").new_page()
      errors = []
      page.on("pageerror", lambda error: errors.append(str(error)))
      page.add_init_script(LISTENER)
      page.goto(f"{stand.url}/host.html", wait_until="load")
      page.locator("[data-role=session]").click()
      page.wait_for_function("() => document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('iframe')", timeout=5000)
      deck = page.frame_locator("iframe")
      deck.locator("#joy").wait_for(timeout=5000)
      frame = next(each for each in page.frames if each.url.endswith("/present.html"))
      # The engine starts on the Session's step, in its drive mode, with every control.
      # A frame keeps the window of its first, blank document: the listener goes on the deck's own document, once it is there.
      frame.wait_for_function("() => document.documentElement.dataset.mode === 'drive' && document.querySelector('.slide.on')", timeout=5000)
      frame.wait_for_timeout(300)
      frame.evaluate("() => {" + LISTENER + "}")
      assert deck.locator("#joy").is_visible() and deck.locator("#notesBtn").is_visible()
      assert stand.posts == []
      # The pad: each step is posted, the screen first.
      for expected in range(2, 5):
        deck.locator("#joyDown").click()
        frame.wait_for_function("n => window.__step === n", arg=expected, timeout=1000)
      frame.wait_for_timeout(300)
      # The first press went from the Session's step (1) to 2: the engine had started where the Session was.
      assert stand.posts[0] == 2 and stand.posts[-1] == 4 and stand.posts == sorted(set(stand.posts))
      # The index: a jump to the first slide is one step, posted.
      deck.locator("#num").click()
      deck.locator("#ix a[data-go]").first.click()
      frame.wait_for_function("() => window.__step === 0", timeout=1000)
      frame.wait_for_timeout(300)
      assert stand.posts[-1] == 0
      # The notes are on the speaker's screen; the talk's time is in the engine's bottom bar.
      deck.locator("#notesBtn").click()
      assert "Only the speaker reads this note" in deck.locator("#np").inner_text()
      # #1709: the time spent of the talk's, the time left and the steps to go.
      frame.wait_for_function("() => /^\\d\\d:\\d\\d \\/ 30:00 · \\d\\d:\\d\\d left · \\d+ to go$/.test(document.getElementById('clock').title)", timeout=3000)
      violations = page.evaluate("() => window.__csp") + frame.evaluate("() => window.__csp")
      browser.close()
  finally:
    stand.close()
  assert violations == [] and errors == []


def test_a_page_of_another_origin_cannot_frame_the_portal_but_present_html(tmp_path):
  """The control: the app's other pages refuse any frame, so only /present.html runs inside the drive screen."""
  stand = Stand(tmp_path)
  try:
    import urllib.request
    framed = urllib.request.urlopen(f"{stand.url}/present.html").headers
    other = urllib.request.urlopen(f"{stand.url}/host.html").headers
  finally:
    stand.close()
  assert framed["X-Frame-Options"] == "SAMEORIGIN" and "frame-ancestors 'self'" in framed["Content-Security-Policy"]
  assert other["X-Frame-Options"] == "DENY" and "frame-ancestors 'none'" in other["Content-Security-Policy"]
