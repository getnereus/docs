"""The portal's navigation of Material 3 (#1838), in headless Chromium under the portal's exact policy: the real
index.html, app.js, app.css, screens.js and icons.js, signed in through a stand-in of oidc-client-ts, with the reefs'
screens of a stand-in GET /v1/screens. "Me" and one destination per reef; a reef with several screens shows them as
primary tabs; a navigation bar at the bottom on a phone, a rail at the side from 600 px, a modal drawer above five
destinations; a screen's nereus-focus hides it all. Set NEREUS_SHOTS to a folder to keep the screenshots (the PR's).
Skips when there is no browser."""
import http.server
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import threading

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = HERE.parents[1]


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


portal = load("portal_navigation", REPO / "controllers" / "nereus-portal" / "portal.py")

# oidc-client-ts stood in: a user signed in, never expired; nothing is redirected.
OIDC = """window.oidc = {
  UserManager: class {
    constructor() { this.events = { addUserLoaded() {}, addAccessTokenExpiring() {} }; }
    getUser() { return Promise.resolve({ access_token: "token", refresh_token: "refresh", id_token: "id", expired: false }); }
  },
  WebStorageStateStore: class {},
  InMemoryWebStorage: class {},
};
"""

# A reef's screen: its element names itself and holds a button that asks for the whole view (nereus-focus, #1761).
MODULE = """customElements.define("%s", class extends HTMLElement {
  connectedCallback() {
    const name = document.createElement("p");
    name.textContent = "%s";
    const focus = document.createElement("button");
    focus.type = "button";
    focus.className = "focus";
    focus.textContent = "Open one";
    focus.addEventListener("click", () => this.dispatchEvent(new CustomEvent("nereus-focus", { detail: { focused: true } })));
    this.replaceChildren(name, focus);
  }
});
"""

PRESENTATIONS = [
  {"reef": "presentations", "tab": "Sessions", "element": "nereus-presentations-drive", "module": "drive.js", "icon": "presentation"},
  {"reef": "presentations", "tab": "Decks", "element": "nereus-presentations-decks", "module": "decks.js", "icon": "folder"},
]
TIDE = {"reef": "ideas", "tab": "Tide", "element": "nereus-tide", "module": "tide.js", "icon": "waves"}
USAGE = {"reef": "usage", "tab": "Usage", "element": "nereus-usage", "module": "usage.js", "icon": "gauge"}
MORE = [{"reef": f"extra-{n}", "tab": f"Extra {n}", "element": f"nereus-extra-{n}", "module": "x.js", "icon": "nowhere"} for n in range(3)]

LISTENER = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.effectiveDirective + ' ' + e.blockedURI), true);
"""


class Stand:
  def __init__(self, items):
    files = portal.files()
    by_module = {f"/reefs/{item['reef']}/ui/{item['module']}": item for item in items}

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
        js = "text/javascript; charset=utf-8"
        if path == "/vendor/oidc-client-ts-3.5.0.min.js":
          self.secure(200, js, OIDC.encode())
        elif path == "/config.json":
          body = {"issuer": "https://auth.example.com/realms/nereus", "clientId": "nereus-portal", "publicUrl": "https://portal.example.com"}
          self.secure(200, "application/json", json.dumps(body).encode())
        elif path == "/v1/me":
          self.secure(200, "application/json", json.dumps({"sub": "u1", "name": "Ana Example", "email": "ana@example.com"}).encode())
        elif path == "/v1/screens":
          self.secure(200, "application/json", json.dumps({"items": items}).encode())
        elif path in by_module:
          item = by_module[path]
          self.secure(200, js, (MODULE % (item["element"], item["tab"])).encode())
        elif path == "/sw.js":
          self.secure(404, "text/plain", b"no worker on the stand\n")
        elif path in files:
          self.secure(200, portal.content_type(files[path]), files[path].read_bytes())
        else:
          self.secure(404, "application/json", b"{}")

    self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.url = f"http://127.0.0.1:{self.server.server_port}"
    threading.Thread(target=self.server.serve_forever, daemon=True).start()

  def close(self):
    self.server.shutdown()


def chromium(playwright):
  failures = []
  for channel in (None, "chrome"):
    try:
      return playwright.chromium.launch(channel=channel)
    except Exception as error:
      failures.append(str(error).splitlines()[0])
  pytest.skip("no headless browser: run `uvx playwright install chromium-headless-shell` or install Chrome\n" + "\n".join(failures))


@pytest.fixture
def portal_page():
  """Opens the portal on a stand with the given screens, at a size, a scheme and a language; at the end: no page error,
  no CSP violation, no request to another origin."""
  pytest.importorskip("playwright")
  from playwright import sync_api
  stands, checks = [], []
  with sync_api.sync_playwright() as playwright:
    browser = chromium(playwright)

    def opened(items, width=390, height=844, scheme="dark", locale="en-US"):
      stand = Stand(items)
      stands.append(stand)
      page = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, locale=locale).new_page()
      errors, outside = [], []
      page.add_init_script(LISTENER)
      page.on("pageerror", lambda error: errors.append(str(error)))
      page.on("request", lambda request: None if request.url.startswith(stand.url) else outside.append(request.url))
      page.goto(stand.url + "/")
      page.locator("#tabs:not([hidden])").wait_for()
      page.wait_for_function(f"document.querySelectorAll('#tabs [data-tab]').length > {1 if items else 0}")
      checks.append((page, errors, outside))
      return page

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


def settled(page, wanted, timeout_ms=3000):
  """Waits for the navigation's box to reach where it goes (the drawer's slide is a transition), polling from Python:
  the portal's CSP refuses wait_for_function's string, an eval."""
  box = None
  for _ in range(timeout_ms // 50):
    box = page.locator("#tabs").bounding_box()
    if box and wanted(box):
      return
    page.wait_for_timeout(50)
  raise AssertionError(f"#tabs never settled: {box}")


def labels(page):
  return page.locator("#tabs [data-tab] .label").all_text_contents()


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_a_phone_has_a_bar_at_the_bottom_one_destination_per_reef_and_its_screens_as_tabs(portal_page, scheme):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE], scheme=scheme)
  assert labels(page) == ["Me", "Presentations", "Tide", "Usage"]
  bar = page.locator("#tabs").bounding_box()
  assert bar["y"] + bar["height"] == pytest.approx(844, abs=1) and bar["width"] == pytest.approx(390, abs=1)
  for button in page.locator("#tabs [data-tab]").all():
    box = button.bounding_box()
    assert box["width"] >= 48 and box["height"] >= 48
  shot(page, f"nav-phone-me-{scheme}")

  page.locator('#tabs [data-tab="presentations"]').click()
  expect(page.locator('#tabs [data-tab="presentations"]')).to_have_attribute("aria-current", "page")
  expect(page.locator("#reef-tabs")).to_be_visible()
  expect(page.locator("#reef-tabs [role=tab]:visible")).to_have_text(["Sessions", "Decks"])
  expect(page.locator("#reef-tabs [aria-selected=true]")).to_have_text("Sessions")
  expect(page.locator("nereus-presentations-drive")).to_be_visible()
  shot(page, f"nav-phone-presentations-{scheme}")

  page.locator("#reef-tabs [role=tab]", has_text="Decks").click()
  expect(page.locator("nereus-presentations-decks")).to_be_visible()
  expect(page.locator("nereus-presentations-drive")).to_be_hidden()

  # Back on the reef, its last screen opens again; a reef of one screen shows no tabs.
  page.locator('#tabs [data-tab="ideas"]').click()
  expect(page.locator("#reef-tabs")).to_be_hidden()
  expect(page.locator("nereus-tide")).to_be_visible()
  page.locator('#tabs [data-tab="presentations"]').click()
  expect(page.locator("nereus-presentations-decks")).to_be_visible()


def test_a_screen_that_asks_for_the_whole_view_hides_the_bar_and_the_tabs(portal_page):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS])
  page.locator('#tabs [data-tab="presentations"]').click()
  page.locator("nereus-presentations-drive .focus").click()
  expect(page.locator("#tabs")).to_be_hidden()
  expect(page.locator("#reef-tabs")).to_be_hidden()


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_a_wide_screen_has_a_rail_at_the_side(portal_page, scheme):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE], width=1280, height=800, scheme=scheme)
  rail = page.locator("#tabs").bounding_box()
  assert rail["x"] == 0 and rail["y"] == 0 and rail["width"] == pytest.approx(96, abs=1) and rail["height"] == pytest.approx(800, abs=1)
  page.locator('#tabs [data-tab="presentations"]').click()
  expect(page.locator("#reef-tabs [aria-selected=true]")).to_have_text("Sessions")
  shot(page, f"nav-wide-presentations-{scheme}")


def test_more_than_five_destinations_go_to_a_modal_drawer(portal_page):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE, *MORE])
  assert page.evaluate("document.body.dataset.nav") == "drawer"
  assert len(labels(page)) == 7
  expect(page.locator("#menu")).to_be_visible()
  # The drawer slides out once the page knows it has more than five destinations: wait for the slide's end, never read
  # its box mid-transition.
  settled(page, lambda box: box["x"] + box["width"] <= 0)
  page.locator("#menu").click()
  expect(page.locator("#tabs")).to_have_attribute("data-open", "")
  settled(page, lambda box: box["x"] == 0)
  shot(page, "nav-phone-drawer-dark")
  page.keyboard.press("Escape")
  expect(page.locator("#scrim")).to_be_hidden()
  page.locator("#menu").click()
  page.locator('#tabs [data-tab="extra-1"]').click()
  expect(page.locator("#scrim")).to_be_hidden()
  expect(page.locator("nereus-extra-1")).to_be_visible()


def test_the_reef_s_name_follows_the_language(portal_page):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE], locale="pt-BR")
  assert labels(page) == ["Eu", "Apresentações", "Tide"]
  page.locator('[data-language="en"]').click()
  assert labels(page) == ["Me", "Presentations", "Tide"]
  expect(page.locator("#tabs")).to_have_attribute("aria-label", "Main")


@pytest.mark.parametrize("width,height", [(390, 844), (1280, 800)])
@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_a_reef_s_screen_fills_the_portal_under_a_top_app_bar_with_no_card(portal_page, width, height, scheme):
  """#1846: the app bar names the destination; the screen has no card around it and fills the width beside the rail
  or above the bar; the mark steps aside."""
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE], width=width, height=height, scheme=scheme)
  expect(page.locator("#app-bar")).to_be_visible()
  expect(page.locator("#app-title")).to_have_text("Me")
  expect(page.locator(".mark")).to_be_hidden()
  page.locator('#tabs [data-tab="presentations"]').click()
  expect(page.locator("#app-title")).to_have_text("Presentations")
  card = page.locator("main.card")
  assert card.evaluate("e => getComputedStyle(e).borderTopWidth") == "0px"
  assert card.evaluate("e => getComputedStyle(e).backgroundColor") == "rgba(0, 0, 0, 0)"
  box = page.locator("nereus-presentations-drive").bounding_box()
  start = 112 if width >= 600 else 16
  assert box["x"] == pytest.approx(start, abs=1) and box["x"] + box["width"] == pytest.approx(width - 16, abs=1)
  bar = page.locator("#app-bar").bounding_box()
  assert bar["y"] == 0 and bar["height"] == pytest.approx(64, abs=1)
  shot(page, f"app-bar-{'wide' if width >= 600 else 'phone'}-presentations-{scheme}")
  page.locator('#tabs [data-tab="ideas"]').click()
  expect(page.locator("#app-title")).to_have_text("Tide")


def test_the_app_bar_follows_the_language_and_steps_aside_on_focus(portal_page):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS], locale="pt-BR")
  expect(page.locator("#app-title")).to_have_text("Eu")
  page.locator('#tabs [data-tab="presentations"]').click()
  expect(page.locator("#app-title")).to_have_text("Apresentações")
  expect(page.locator("#reef-tabs [role=tab]:visible")).to_have_text(["Sessões", "Decks"])
  page.locator('[data-language="en"]').click()
  expect(page.locator("#app-title")).to_have_text("Presentations")
  expect(page.locator("#reef-tabs [role=tab]:visible")).to_have_text(["Sessions", "Decks"])
  page.locator("nereus-presentations-drive .focus").click()
  expect(page.locator("#app-bar")).to_be_hidden()



@pytest.mark.parametrize("width", [340, 360, 390, 412])
@pytest.mark.parametrize("locale", ["pt-BR", "en-US"])
def test_no_label_is_cut_on_a_phone_in_either_language(portal_page, width, locale):
  """docs/agent/decks.md, Screens on a phone: every row of controls measured in both languages at 340 to 412 px: no
  label of the bar, the app bar or the primary tabs cut, nothing past the screen's edge, no horizontal scroll."""
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE], width=width, locale=locale)
  page.locator('#tabs [data-tab="presentations"]').click()
  found = page.evaluate("""() => ({
    scroll: document.documentElement.scrollWidth > innerWidth,
    cut: [...document.querySelectorAll('#tabs .label, #app-title, #reef-tabs [role=tab]:not([hidden])')]
      .filter((e) => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > innerWidth)
      .map((e) => e.textContent),
  })""")
  assert found == {"scroll": False, "cut": []}
