"""The Sessions list and the Drive screen follow Material 3 (#1840), in headless Chromium on a phone: the presentations reef's
drive screen (leagore/ui/drive.js) under the portal's theme (app.css, the --nereus-* roles). The list shows two-line items
with a status chip; a Session opens either in the deck engine (the stage: the top app bar with Share, #1841, and
Presentation over the framed engine, #1712) or, with no page for the engine, in the buttons' screen (the clock card, the slide card, Previous and Next,
End in Next's place on the last step). Every row of controls is measured in English and Portuguese at 340, 360, 390 and
412 px: each control inside the screen, no text cut, no horizontal scroll, and no CSP violation (docs/agent/decks.md,
"Screens on a phone"). With DRIVE_SHOTS set to a folder, it saves the screens at 390x844 in both themes. The server is a
stand-in for the portal and the API, as in test_present_browser.py; every name is invented. Skips with no browser."""
import http.server
import json
import os
import pathlib
import subprocess
import sys
import threading

import pytest
from test_follow_browser import CODE, DECK, HERE, LISTENER, REPO, chromium, portal, ro

LEAGORE_UI = REPO / "controllers" / "leagore" / "ui"
SESSION = "platform-day"
BASE = f"/v1/presentations/sessions/{SESSION}"
WIDTHS = (340, 360, 390, 412)
LANGS = ("en", "pt")
HOST_HTML = b"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Host</title><link rel="stylesheet" href="/app.css"><link rel="stylesheet" href="/host.css">
<script type="module" src="/host.js"></script></head><body></body></html>
"""
# The portal's frame around a screen, in short: 8px around a focused one (app.css), 16px around the list's card.
HOST_CSS = b"""body { display: block; padding: 16px; }
body:has(nereus-presentations-drive[data-focused="true"]) { padding: 8px; }
"""
HOST_JS = b"""import "/drive.js";
const api = {
  get: (path) => fetch(path, { cache: "no-store" }),
  post: (path, body) => fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
};
window.__focus = [];
const element = document.createElement("nereus-presentations-drive");
element.addEventListener("nereus-focus", (event) => {
  window.__focus.push(event.detail.focused);
  element.setAttribute("data-focused", String(event.detail.focused));
});
element.lang = new URLSearchParams(location.search).get("lang") || "en";
element.api = api;
document.body.append(element);
"""
SLIDES = [
  {"name": "opening", "title": "Why platforms", "message": "The problem we start from"},
  {"name": "map", "title": "The map of the talk", "message": "Three parts, one story"},
  {"name": "demo", "title": "A live demo", "message": "From a deck to a Session"},
  {"name": "close", "title": "Thanks", "message": "Questions at example.com"},
]
ITEMS = [
  {"metadata": {"name": SESSION}, "spec": {"presentation": "storytelling", "talk": "30m"}, "status": {"code": CODE, "step": 2, "slides": 4}},
  {"metadata": {"name": "dry-run"}, "spec": {"presentation": "storytelling", "talk": "30m", "rehearsal": True}, "status": {"step": 0, "slides": 4}},
  {"metadata": {"name": "meetup-week"}, "spec": {"presentation": "release", "talk": "1h"},
   "status": {"code": "M3QR", "step": 9, "slides": 10, "ended": "2026-11-17T20:00:00Z"}},
]


class Stand:
  """The portal's files, the host page, and one Session that takes the steps and the end it is posted. With `engine`, the
  Session has its page for the deck engine; without, the screen keeps its buttons."""

  def __init__(self, directory, engine=False, step=0):
    self.posts: list[int] = []
    self.step = step
    self.ended = None
    # The room's turns the speaker opened (#1876): {"questions_open": ..., "rating_open": ...}.
    self.turns: dict[str, str] = {}
    self.lock = threading.Lock()
    stand = self
    subprocess.run([sys.executable, str(HERE / "render-outline"), str(DECK), "--split", "--output", str(directory / "deck.html")],
                   check=True, capture_output=True)
    deck = (directory / "deck.html").read_bytes()
    self.slides = [{"name": f"s{n}", "title": f"Slide {n + 1}", "message": ""} for n in range(ro.deck_steps(deck.decode()))] if engine else SLIDES
    files = {f"/{name}": portal.STATIC / name for name in ("app.css", "present.html", "present.js", "follow.js", "follow.css", "deck.css", "deck.js")}
    files.update({f"/{path.name}": path for path in LEAGORE_UI.iterdir()})
    pages = {"/host.html": ("text/html; charset=utf-8", HOST_HTML), "/host.js": ("text/javascript; charset=utf-8", HOST_JS),
             "/host.css": ("text/css; charset=utf-8", HOST_CSS)}

    self.files, self.pages, self.deck, self.engine = files, pages, deck, engine

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

      def do_GET(self):
        self.secure(*stand.answer(self.path.split("?")[0]))

      def do_POST(self):
        self.secure(*stand.posted(self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"{}")))

    self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.httpd.daemon_threads = True
    threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
    self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

  def answer(self, path):
    """A GET's (status, type, body, framed)."""
    if path in self.files:
      return 200, portal.content_type(self.files[path]), self.files[path].read_bytes(), path in portal.FRAMED
    if path in self.pages:
      return (200, *self.pages[path], False)
    if path == "/v1/presentations/sessions":
      return self.json({"items": ITEMS})
    if path == BASE:
      return self.json({"object": {"metadata": {"name": SESSION}, "spec": {"presentation": "storytelling", "talk": "30m"}}, "state": self.state(),
                        "follow": f"/p/{CODE}", "followers": 3, "live": True, "slides": self.slides})
    if path == f"{BASE}/deck" and self.engine:
      return 200, "text/html; charset=utf-8", self.deck, False
    return 404, "text/plain", b"not found\n", False

  def posted(self, path, body):
    """A POST's answer: the step or the end, taken."""
    with self.lock:
      if path == f"{BASE}/end":
        self.ended = "2026-12-01T17:31:00Z"
      elif path == f"{BASE}/step":
        self.posts.append(body["step"])
        self.step = body["step"]
      elif path == f"{BASE}/open" and body.get("part") in ("questions", "rating"):
        self.turns.setdefault(f"{body['part']}_open", "2026-12-01T17:30:00Z")
      else:
        return 404, "text/plain", b"not found\n", False
    return self.json(self.state())

  @staticmethod
  def json(body):
    return 200, "application/json", json.dumps(body).encode(), False

  def state(self):
    found = {"code": CODE, "session": SESSION, "presentation": "storytelling", "step": self.step, "steps": len(self.slides),
             "sequence": len(self.posts), "slide": self.slides[self.step], **self.turns}
    return {**found, "ended": self.ended} if self.ended else found

  def close(self):
    self.httpd.shutdown()


# Every shown control of the screen: its box, whether its text is cut, and the page's scroll width.
MEASURE = """(selector) => {
  const root = document.querySelector('nereus-presentations-drive').shadowRoot;
  const shown = (node) => node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden';
  const boxes = [...root.querySelectorAll(selector)].filter(shown).map((node) => {
    const box = node.getBoundingClientRect();
    return { role: node.dataset.role || node.className, left: box.left, right: box.right, width: box.width, height: box.height,
             cut: node.scrollWidth > node.clientWidth + 1, text: node.textContent };
  });
  return { width: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth, boxes };
}"""
ROWS = ".session, .chip, .back, .stage-name, .subtitle, .share, .full, .bar .end, .bar .rate, .stage-ended, .controls button, .pace, .part, .remaining, .upcoming, .progress"


def fits(page, selector=ROWS):
  """Each control inside the screen, none cut, and no horizontal scroll; the controls to press at least 48px high."""
  found = page.evaluate(MEASURE, selector)
  assert found["scroll"] <= found["width"], found
  for box in found["boxes"]:
    assert box["left"] >= 0 and box["right"] <= found["width"] + 0.5, (found["width"], box)
    assert not box["cut"], (found["width"], box)
  return found["boxes"]


def pressable(boxes):
  for box in boxes:
    if box["role"] in ("session", "back", "share", "full", "prev", "next", "segment-follow", "segment-projector", "share-projector", "share-thermometer", "copy", "done"):
      assert box["height"] >= 48, box


def opened(page, stand, lang, width, height=844, scheme="dark"):
  page.set_viewport_size({"width": width, "height": height})
  page.emulate_media(color_scheme=scheme)
  page.goto(f"{stand.url}/host.html?lang={lang}", wait_until="load")
  page.locator("[data-role=session]").first.wait_for(timeout=5000)


def phone(playwright, browser, lang, **context):
  device = {key: value for key, value in playwright.devices["Pixel 7"].items() if key != "default_browser_type"}
  page = browser.new_context(**device, locale="pt-BR" if lang == "pt" else "en-US", **context).new_page()
  errors = []
  page.on("pageerror", lambda error: errors.append(str(error)))
  page.add_init_script(LISTENER)
  return page, errors


def shots():
  folder = os.environ.get("DRIVE_SHOTS")
  return pathlib.Path(folder) if folder else None


def test_the_sessions_list_is_two_line_items_with_a_status_chip_that_fit_every_phone(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        page, errors = phone(playwright, browser, lang)
        for width in WIDTHS:
          opened(page, stand, lang, width)
          boxes = fits(page)
          pressable(boxes)
          rows = [box for box in boxes if box["role"] == "session"]
          assert len(rows) == 3 and all(box["height"] >= 72 for box in rows)
          chips = [box["text"] for box in boxes if box["role"] == "session-status"]
          assert chips == (["Live", "Ready", "Ended"] if lang == "en" else ["Ao vivo", "Pronta", "Encerrada"])
        metas = page.locator("[data-role=session-meta]").all_inner_texts()
        assert metas[1].startswith("Rehearsal" if lang == "en" else "Ensaio") and CODE in metas[0]
        assert page.evaluate("() => window.__csp") == [] and errors == []
        page.context.close()
      if shots():
        for scheme in ("dark", "light"):
          page, _ = phone(playwright, browser, "en")
          opened(page, stand, "en", 390, scheme=scheme)
          page.screenshot(path=str(shots() / f"sessions-390x844-{scheme}.png"))
          page.context.close()
      browser.close()
  finally:
    stand.close()


def test_the_buttons_screen_walks_to_the_last_step_where_end_takes_next_s_place(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        page, errors = phone(playwright, browser, lang)
        for width in WIDTHS:
          stand.step, stand.ended, stand.posts, stand.turns = 0, None, [], {}
          opened(page, stand, lang, width)
          page.locator("[data-role=session]").first.click()
          page.locator("[data-role=controls]").wait_for(timeout=5000)
          assert page.evaluate("() => window.__focus") == [False, True]
          boxes = fits(page)
          pressable(boxes)
          prev, nxt = (next(box for box in boxes if box["role"] == role) for role in ("prev", "next"))
          assert prev["height"] == nxt["height"] == 96 and 1.8 < nxt["width"] / prev["width"] < 2.2, (prev, nxt)
          assert page.locator("[data-role=upcoming]").inner_text() == ("Next: The map of the talk" if lang == "en" else "A seguir: The map of the talk")
          for _ in range(3):
            page.locator("[data-role=next]").click()
          page.locator("[data-role=end]").wait_for(timeout=2000)
          assert page.locator("[data-role=next]").is_hidden()
          assert page.locator("[data-role=progress]").inner_text() == ("Step 4 of 4" if lang == "en" else "Passo 4 de 4")
          boxes = fits(page)
          end = next(box for box in boxes if box["role"] == "end")
          assert end["height"] == 96 and 1.8 < end["width"] / prev["width"] < 2.2
          # Ask the room to rate (#1876): over Previous and End, the whole row, before End is pressed.
          rate = next(box for box in boxes if box["role"] == "rate")
          assert rate["height"] == 56 and rate["width"] > end["width"], (rate, end)
          if width == 390 and lang == "en" and shots():
            for scheme in ("dark", "light"):
              page.emulate_media(color_scheme=scheme)
              page.wait_for_timeout(400)
              page.screenshot(path=str(shots() / f"drive-buttons-last-390x844-{scheme}.png"))
            page.emulate_media(color_scheme="dark")
          page.locator("[data-role=end]").click()
          page.locator("[data-role=status]").filter(has_text="Ended" if lang == "en" else "Encerrada").wait_for(timeout=2000)
          assert stand.posts == [1, 2, 3] and stand.ended
          page.locator("[data-role=back]").click()
          page.locator("[data-role=sessions]").wait_for(timeout=2000)
        assert page.evaluate("() => window.__csp") == [] and errors == []
        page.context.close()
      if shots():
        for scheme in ("dark", "light"):
          stand.step, stand.ended = 1, None
          page, _ = phone(playwright, browser, "en")
          opened(page, stand, "en", 390, scheme=scheme)
          page.locator("[data-role=session]").first.click()
          page.locator("[data-role=controls]").wait_for(timeout=5000)
          page.screenshot(path=str(shots() / f"drive-buttons-390x844-{scheme}.png"))
          page.context.close()
      browser.close()
  finally:
    stand.close()


def test_the_stage_keeps_the_engine_under_an_app_bar_that_fits_every_phone(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  probe = Stand(tmp_path, engine=True)
  last = len(probe.slides) - 1
  probe.close()
  stand = Stand(tmp_path, engine=True, step=last)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        page, errors = phone(playwright, browser, lang)
        for width in WIDTHS:
          opened(page, stand, lang, width)
          page.locator("[data-role=session]").first.click()
          page.frame_locator("iframe").locator("#joy").wait_for(timeout=5000)
          # On the last step End sits in the app bar (#1712), with the way back, the name and its presentation.
          page.locator("[data-role=end]").wait_for(timeout=2000)
          boxes = fits(page)
          pressable(boxes)
          roles = [box["role"] for box in boxes]
          for role in ("back", "session-name", "subtitle", "share", "full", "end"):
            assert role in roles, (width, lang, roles)
          frame = page.evaluate("() => document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('iframe').getBoundingClientRect().height")
          assert frame > 844 * 0.6, frame
        assert page.evaluate("() => window.__csp") == [] and errors == []
        page.context.close()
      if shots():
        for scheme in ("dark", "light"):
          page, _ = phone(playwright, browser, "en")
          opened(page, stand, "en", 390, scheme=scheme)
          page.locator("[data-role=session]").first.click()
          page.frame_locator("iframe").locator("#joy").wait_for(timeout=5000)
          page.mouse.move(195, 20)
          page.wait_for_timeout(500)
          page.screenshot(path=str(shots() / f"drive-stage-390x844-{scheme}.png"))
          page.set_viewport_size({"width": 1280, "height": 800})
          page.wait_for_timeout(300)
          page.screenshot(path=str(shots() / f"drive-stage-1280x800-{scheme}.png"))
          page.context.close()
      browser.close()
  finally:
    stand.close()
