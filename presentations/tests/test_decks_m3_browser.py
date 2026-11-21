"""The Decks screen of Material 3 (#1839) inside the real portal, in headless Chromium under the portal's exact policy:
the portal's index.html, app.js and app.css, leagore's real decks.js and decks.css, signed in through the stand-in of
oidc-client-ts, on a stand-in API of Presentations. A two-line item per deck with its menu (download, delete after a
confirmation), and an extended FAB that opens the import's modal bottom sheet (File | Folder, the picked file's row, the
Name field, Check's banner, Cancel and Create), closed by Escape and the scrim. Every control is measured inside the
screen at 340, 360, 390 and 412 px in English and in Portuguese (docs/agent/decks.md, Screens on a phone). Set
NEREUS_SHOTS to a folder to keep the screenshots (the PR's). Skips when there is no browser."""
import http.server
import json
import os
import pathlib
import threading

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
UI = REPO / "controllers" / "leagore" / "ui"


def load(name, path):
  import importlib.machinery
  import importlib.util
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


navigation = load("portal_navigation_browser", HERE / "test_portal_navigation_browser.py")
portal = navigation.portal

ITEMS = [
  {"reef": "presentations", "tab": "Sessions", "element": "nereus-presentations-drive", "module": "drive.js", "icon": "presentation"},
  {"reef": "presentations", "tab": "Decks", "element": "nereus-presentations-decks", "module": "decks.js", "icon": "folder"},
]
DIGEST = "sha256:" + "4f1c9a0b7e2d".ljust(64, "0")
DECK = "outlineVersion: 1\nslides:\n  - name: opening\n"


class Stand:
  """The portal's files, leagore's Decks screen and a small API of Presentations that remembers what is created and
  deleted."""

  def __init__(self):  # noqa: C901 - one stand, its routes
    files = portal.files()
    decks = {
      "storytelling": {"metadata": {"name": "storytelling"}, "spec": {"description": "Tell the platform's story"}, "status": {"revision": DIGEST, "slides": 24}},
      "nereus-overview": {"metadata": {"name": "nereus-overview"}, "status": {"revision": DIGEST, "slides": 12}},
    }
    self.decks, self.calls = decks, []

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

      def json(self, code, body):
        self.secure(code, "application/json", json.dumps(body).encode())

      def do_GET(self):  # noqa: C901 - one stand, its routes
        path = self.path.split("?")[0]
        js = "text/javascript; charset=utf-8"
        if path == "/vendor/oidc-client-ts-3.5.0.min.js":
          self.secure(200, js, navigation.OIDC.encode())
        elif path == "/config.json":
          self.json(200, {"issuer": "https://auth.example.com/realms/nereus", "clientId": "nereus-portal", "publicUrl": "https://portal.example.com"})
        elif path == "/v1/me":
          self.json(200, {"sub": "u1", "name": "Ana Example", "email": "ana@example.com"})
        elif path == "/v1/screens":
          self.json(200, {"items": ITEMS})
        elif path == "/reefs/presentations/ui/drive.js":
          self.secure(200, js, (navigation.MODULE % ("nereus-presentations-drive", "Sessions")).encode())
        elif path in ("/reefs/presentations/ui/decks.js", "/reefs/presentations/ui/decks.css"):
          name = path.rsplit("/", 1)[1]
          self.secure(200, js if name.endswith(".js") else "text/css; charset=utf-8", (UI / name).read_bytes())
        elif path == "/v1/presentations/presentations":
          self.json(200, {"items": list(decks.values())})
        elif path.startswith("/v1/presentations/presentations/") and path.endswith("/deck"):
          self.secure(200, "text/html; charset=utf-8", b"<!doctype html><title>storytelling</title>")
        elif path == "/sw.js":
          self.secure(404, "text/plain", b"no worker on the stand\n")
        elif path in files:
          self.secure(200, portal.content_type(files[path]), files[path].read_bytes())
        else:
          self.json(404, {})

      def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        stand.calls.append(("POST", self.path, body))
        if self.path.endswith("?dryRun=true"):
          self.json(200, {"result": "dryRun", "steps": 14, "warnings": []})
          return
        decks[body["name"]] = {"metadata": {"name": body["name"]}, "status": {"revision": DIGEST, "slides": 14}}
        self.json(200, {"result": "created", "revision": DIGEST})

      def do_DELETE(self):
        stand.calls.append(("DELETE", self.path, None))
        decks.pop(self.path.rsplit("/", 1)[1], None)
        self.json(200, {"result": "deleted"})

    stand = self
    self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.url = f"http://127.0.0.1:{self.server.server_port}"
    threading.Thread(target=self.server.serve_forever, daemon=True).start()

  def close(self):
    self.server.shutdown()


@pytest.fixture
def decks_page():
  """Opens the portal's Decks tab at a size, a scheme and a language; at the end: no page error, no CSP violation, no
  request to another origin."""
  pytest.importorskip("playwright")
  from playwright import sync_api
  stands, checks = [], []
  with sync_api.sync_playwright() as playwright:
    browser = navigation.chromium(playwright)

    def opened(width=390, height=844, scheme="dark", locale="en-US"):
      stand = Stand()
      stands.append(stand)
      page = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, locale=locale, accept_downloads=True).new_page()
      errors, outside = [], []
      page.add_init_script(navigation.LISTENER)
      page.on("pageerror", lambda error: errors.append(str(error)))
      page.on("request", lambda request: None if request.url.startswith((stand.url, "blob:")) else outside.append(request.url))
      page.goto(stand.url + "/")
      page.locator("#tabs [data-tab]").nth(1).click()
      page.locator("#reef-tabs [role=tab]").nth(1).click()
      page.locator("[data-role=deck-name]").first.wait_for()
      checks.append((page, errors, outside))
      return stand, page

    yield opened, sync_api.expect
    for page, errors, outside in checks:
      assert page.evaluate("window.__csp") == []
      assert errors == [] and outside == []
    browser.close()
  for stand in stands:
    stand.close()


def shot(page, name):
  folder = os.environ.get("NEREUS_SHOTS")
  if folder:
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    page.wait_for_timeout(300)
    page.screenshot(path=str(pathlib.Path(folder) / f"{name}.png"))


def inside(page, selector, width):
  """Every match of the selector is drawn whole inside the screen's width, and its text is not cut."""
  for box in page.locator(selector).all():
    if not box.is_visible():
      continue
    edges = box.bounding_box()
    assert edges["x"] >= 0 and edges["x"] + edges["width"] <= width + 0.5, f"{selector} past the edge at {width}: {edges}"
    assert box.evaluate("node => node.scrollWidth <= node.clientWidth + 1"), f"{selector} cuts its text at {width}"


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_each_deck_is_a_two_line_item_and_the_fab_opens_the_import_sheet(decks_page, scheme):
  opened, expect = decks_page
  stand, page = opened(scheme=scheme)
  expect(page.locator("[data-role=deck-name]")).to_have_text(["storytelling", "nereus-overview"])
  rows = page.locator("li.deck")
  assert all(row.bounding_box()["height"] >= 72 for row in rows.all())
  more = page.locator("[data-role=more]").first
  assert more.get_attribute("aria-label") == "More options for storytelling"
  assert more.bounding_box()["width"] >= 48 and more.bounding_box()["height"] >= 48
  fab = page.locator("[data-role=import]")
  expect(fab).to_have_text("Import deck")
  # The FAB sits over the navigation bar, never on it.
  assert fab.bounding_box()["y"] + fab.bounding_box()["height"] <= page.locator("#tabs").bounding_box()["y"]
  shot(page, f"decks-390x844-{scheme}")

  fab.click()
  sheet = page.locator("[data-role=sheet]")
  expect(sheet).to_be_visible()
  expect(page.locator("[data-role=segment-file]")).to_have_attribute("aria-pressed", "true")
  page.locator("[data-role=file]").set_input_files(files=[{"name": "storytelling.yaml", "mimeType": "application/yaml", "buffer": DECK.encode()}])
  expect(page.locator("[data-role=name]")).to_have_value("storytelling")
  expect(page.locator("[data-role=create]")).to_be_disabled()
  page.locator("[data-role=check]").click()
  expect(page.locator("[data-role=result]")).to_contain_text("The deck renders: 14 steps.")
  expect(page.locator("[data-role=create]")).to_be_enabled()
  shot(page, f"decks-sheet-390x844-{scheme}")
  page.locator("[data-role=create]").click()
  expect(sheet).not_to_be_visible()
  expect(page.locator("[data-role=created]")).to_contain_text("storytelling created")
  assert [call[1] for call in stand.calls] == ["/v1/presentations/presentations?dryRun=true", "/v1/presentations/presentations"]


def test_the_sheet_closes_on_escape_and_on_the_scrim_and_keeps_the_focus_inside(decks_page):
  opened, expect = decks_page
  _, page = opened()
  page.locator("[data-role=import]").click()
  sheet = page.locator("[data-role=sheet]")
  expect(sheet).to_be_visible()
  for _ in range(8):
    page.keyboard.press("Tab")
    # The deepest focused element, through the shadow roots, is inside the sheet; or the body, the step where a modal
    # dialog lets the focus go to the browser's own controls, never to the page behind.
    assert page.evaluate("""() => {
      let node = document.activeElement;
      while (node && node.shadowRoot && node.shadowRoot.activeElement) { node = node.shadowRoot.activeElement; }
      return node === document.body || Boolean(node && node.closest('dialog[data-role=sheet]'));
    }""")
  page.keyboard.press("Escape")
  expect(sheet).not_to_be_visible()
  page.locator("[data-role=import]").click()
  expect(sheet).to_be_visible()
  page.mouse.click(195, 20)
  expect(sheet).not_to_be_visible()


def test_a_deck_s_menu_downloads_its_page_and_deletes_it_after_a_confirmation(decks_page):
  opened, expect = decks_page
  stand, page = opened()
  more = page.locator("[data-role=more]").first
  more.click()
  menu = page.locator("[data-role=menu]")
  expect(menu).to_be_visible()
  inside(page, "[data-role=menu]", 390)
  # Under its button, its right edge near the button's.
  assert menu.bounding_box()["y"] >= more.bounding_box()["y"] + more.bounding_box()["height"] - 9
  assert abs(menu.bounding_box()["x"] + menu.bounding_box()["width"] - more.bounding_box()["x"] - more.bounding_box()["width"]) <= 12
  expect(page.locator("[data-role=download]")).to_be_focused()
  page.keyboard.press("Escape")
  expect(menu).not_to_be_visible()
  expect(more).to_be_focused()
  more.click()
  page.mouse.click(195, 500)
  expect(menu).not_to_be_visible()
  more.click()
  with page.expect_download() as download:
    page.locator("[data-role=download]").click()
  assert download.value.suggested_filename == "storytelling.html"
  page.locator("[data-role=more]").first.click()
  page.locator("[data-role=delete]").click()
  expect(page.locator("[data-role=confirm-title]")).to_have_text("Delete storytelling?")
  page.locator("[data-role=confirm-delete]").click()
  expect(page.locator("[data-role=deleted]")).to_have_text("storytelling deleted.")
  expect(page.locator("[data-role=deck-name]")).to_have_text(["nereus-overview"])
  assert stand.calls[-1] == ("DELETE", "/v1/presentations/presentations/storytelling", None)


@pytest.mark.parametrize("width", [340, 360, 390, 412])
@pytest.mark.parametrize("locale", ["en-US", "pt-BR"])
def test_no_control_runs_past_the_screen_in_either_language(decks_page, width, locale):
  opened, expect = decks_page
  _, page = opened(width=width, locale=locale)
  inside(page, "[data-role=import]", width)
  inside(page, "li.deck", width)
  inside(page, "li.deck .text > span", width)
  page.locator("[data-role=import]").click()
  page.locator("[data-role=file]").set_input_files(files=[{"name": "storytelling.yaml", "mimeType": "application/yaml", "buffer": DECK.encode()}])
  page.locator("[data-role=check]").click()
  expect(page.locator("[data-role=create]")).to_be_enabled()
  for selector in ("[data-role=sheet] .segment", "[data-role=sheet] .pick:not([hidden])", "[data-role=name]", "[data-role=sheet] .actions button"):
    inside(page, selector, width)
  assert page.evaluate("document.scrollingElement.scrollWidth") <= width
