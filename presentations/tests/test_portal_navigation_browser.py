"""The portal's navigation of Material 3 (#1838), in headless Chromium under the portal's exact policy: the real
index.html, app.js, app.css, screens.js and icons.js, signed in through a stand-in of oidc-client-ts, with the reefs'
screens of a stand-in GET /v1/screens. The home screen (#740, the instance's status from a stand-in GET /v1/status) and
one destination per reef; a reef with several screens shows them as
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

# GET /v1/status as the API answers it (#739): the core, a reef that needs attention, one that waits, the good ones.
def row(reef, nereid, status="Ready", reason=None, version="1.0.0", created="2026-11-20T00:00:00Z"):
  return {"reef": reef, "nereid": nereid, "version": version, "status": status, "reason": reason, "createdAt": created}


CORE_ROW = row("core", "built-in", version="0.1.0")
INSTALLATION = {"name": "nereus", "alias": "nereus-local", "url": "https://nereus.example.com"}
STATUS = {
  "installation": INSTALLATION,
  "registry": None,
  "items": [
    CORE_ROW,
    row("presentations", "leagore"),
    row("release", "flux", "NotReady", "the HelmRelease podinfo failed: install retries exhausted"),
    row("secrets", "openbao"),
    row("tenancy", "-", "Waiting", version="-"),
    row("usage", "reference-usage"),
  ],
}
EMPTY = {"installation": INSTALLATION, "registry": None, "items": [CORE_ROW]}
GOOD = {"installation": INSTALLATION, "registry": None, "items": [CORE_ROW, row("secrets", "openbao"), row("usage", "reference-usage")]}
DOWN = (503, {"error": {"code": 503, "message": "cannot read the cluster from the Kubernetes API"}})

LISTENER = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.effectiveDirective + ' ' + e.blockedURI), true);
"""


ANA = {"sub": "u1", "name": "Ana Example", "email": "ana@example.com", "identityProvider": "google", "groups": ["nereus-admins", "nereus-users"]}
BRUNO = {"sub": "u2", "name": "Bruno Example", "email": "bruno@example.com", "groups": ["nereus-users"]}


class Stand:
  def __init__(self, items, status=None, person=None):
    files = portal.files()
    stand = self
    answers = [status or (200, STATUS)]
    self.answers = answers
    self.asked = []
    by_module = {f"/reefs/{item['reef']}/ui/{item['module']}": item for item in items}

    class Handler(http.server.BaseHTTPRequestHandler):
      def log_message(self, *args):
        pass

      def asked_status(self):
        stand.asked.append("status")

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
          self.secure(200, "application/json", json.dumps(person or ANA).encode())
        elif path == "/v1/status":
          code, body = answers[0]
          self.asked_status()
          self.secure(code, "application/json", json.dumps(body).encode())
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

    def opened(items, width=390, height=844, scheme="dark", locale="en-US", status=None, touch=False, clock=False, person=None, script=None):
      stand = Stand(items, status, person)
      stands.append(stand)
      context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, locale=locale, has_touch=touch)
      page = context.new_page()
      page.stand = stand
      if clock:
        page.clock.install()
      errors, outside = [], []
      page.add_init_script(LISTENER)
      if script:
        page.add_init_script(script)
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


def open_sheet(page):
  """Opens the account sheet and waits for its entrance to end, so its box is where it stays."""
  page.locator("#avatar").click()
  page.locator("#account").wait_for()
  for _ in range(60):
    if page.evaluate("document.getElementById('account').getAnimations().every((a) => a.playState === 'finished')"):
      return
    page.wait_for_timeout(50)
  raise AssertionError("the sheet's entrance never ended")


def choose_language(page, wanted):
  """Signed in, the language switch is in the account sheet (#2024): open it, choose, close it."""
  page.locator("#avatar").click()
  page.locator(f'#account [data-language="{wanted}"]').click()
  page.keyboard.press("Escape")


def labels(page):
  return page.locator("#tabs [data-tab] .label").all_text_contents()


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_a_phone_has_a_bar_at_the_bottom_one_destination_per_reef_and_its_screens_as_tabs(portal_page, scheme):
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE], scheme=scheme)
  assert labels(page) == ["Status", "Presentations", "Tide", "Usage"]
  bar = page.locator("#tabs").bounding_box()
  assert bar["y"] + bar["height"] == pytest.approx(844, abs=1) and bar["width"] == pytest.approx(390, abs=1)
  for button in page.locator("#tabs [data-tab]").all():
    box = button.bounding_box()
    assert box["width"] >= 48 and box["height"] >= 48
  shot(page, f"nav-phone-status-{scheme}")

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
  assert labels(page) == ["Status", "Apresentações", "Tide"]
  choose_language(page, "en")
  assert labels(page) == ["Status", "Presentations", "Tide"]
  expect(page.locator("#tabs")).to_have_attribute("aria-label", "Main")


@pytest.mark.parametrize("width,height", [(390, 844), (1280, 800)])
@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_a_reef_s_screen_fills_the_portal_under_a_top_app_bar_with_no_card(portal_page, width, height, scheme):
  """#1846: the app bar names the destination; the screen has no card around it and fills the width beside the rail
  or above the bar; the mark steps aside."""
  opened, expect = portal_page
  page = opened([*PRESENTATIONS, TIDE, USAGE], width=width, height=height, scheme=scheme)
  expect(page.locator("#app-bar")).to_be_visible()
  expect(page.locator("#app-title")).to_have_text("Nereus")
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
  expect(page.locator("#app-title")).to_have_text("Nereus")
  page.locator('#tabs [data-tab="presentations"]').click()
  expect(page.locator("#app-title")).to_have_text("Apresentações")
  expect(page.locator("#reef-tabs [role=tab]:visible")).to_have_text(["Sessões", "Decks"])
  choose_language(page, "en")
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


# The home screen (#740, Material 3): the instance's status after signing in.
def rgb(hex_colour):
  value = hex_colour.lstrip("#")
  return "rgb({}, {}, {})".format(*(int(value[i:i + 2], 16) for i in (0, 2, 4)))


SUCCESS = {"dark": rgb("#5cc27e"), "light": rgb("#1f7a3a")}
WARNING = {"dark": rgb("#e09a3a"), "light": rgb("#b06a0f")}


def home(page):
  page.locator("#status-rows:not([hidden]), #status-empty:not([hidden]), #status-error:not([hidden])").wait_for()
  return page


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_the_home_screen_shows_the_worst_state_and_the_rows_that_need_attention_first(portal_page, scheme):
  opened, expect = portal_page
  page = home(opened([*PRESENTATIONS, USAGE], scheme=scheme))
  expect(page.locator('#tabs [data-tab="status"]')).to_have_attribute("aria-current", "page")
  expect(page.locator("#app-title")).to_have_text("Nereus")
  expect(page.locator("#app-subtitle")).to_have_text("nereus-local · portal.example.com")
  expect(page.locator("#avatar")).to_have_text("AE")
  expect(page.locator("#summary-title")).to_have_text("1 reef needs attention")
  expect(page.locator("#summary-counts")).to_have_text("5 reefs · 4 Nereids")
  expect(page.locator("#summary-checked")).to_contain_text("checked at")
  expect(page.locator("#attention .headline")).to_have_text(["release", "tenancy"])
  expect(page.locator("#attention .supporting").first).to_have_text("flux · the HelmRelease podinfo failed: install retries exhausted")
  expect(page.locator("#attention .chip")).to_have_text(["NotReady", "Waiting"])
  assert page.locator("#attention .chip").first.evaluate("e => getComputedStyle(e).color") == WARNING[scheme]
  # On a phone the good rows fold while some need attention.
  expect(page.locator("#good-title")).to_have_text("All good · 4")
  expect(page.locator("#good")).to_be_hidden()
  shot(page, f"home-phone-attention-{scheme}")
  page.locator("#see-all").click()
  expect(page.locator("#good .headline")).to_have_text(["core", "presentations", "secrets", "usage"])
  assert page.locator("#good .chip").first.evaluate("e => getComputedStyle(e).color") == SUCCESS[scheme]
  # The same rows as nereus status, one per reef and Nereid pair.
  assert page.locator("#status .row").count() == len(STATUS["items"])
  for button in page.locator("#status .row-head, #refresh, #avatar, #see-all:visible").all():
    box = button.bounding_box()
    assert box["height"] >= 40 and box["width"] >= 40


def test_a_row_opens_its_detail_in_place(portal_page):
  opened, expect = portal_page
  page = home(opened([]))
  head = page.locator("#attention .row-head").first
  detail = page.locator("#attention .row-detail").first
  expect(detail).to_be_hidden()
  head.click()
  expect(head).to_have_attribute("aria-expanded", "true")
  expect(detail).to_be_visible()
  expect(detail.locator("dt")).to_have_text(["Nereid", "Version", "Reason", "Age"])
  expect(detail.locator("dd")).to_have_text(["flux", "1.0.0", "the HelmRelease podinfo failed: install retries exhausted", re_age()])
  shot(page, "home-phone-detail-dark")
  head.click()
  expect(detail).to_be_hidden()


def re_age():
  import re
  return re.compile(r"^\d+[smhd]$")


def test_all_good_shows_every_row_and_no_attention_group(portal_page):
  opened, expect = portal_page
  page = home(opened([], status=(200, GOOD)))
  expect(page.locator("#summary-title")).to_have_text("All good")
  expect(page.locator("#attention-title")).to_be_hidden()
  expect(page.locator("#see-all")).to_be_hidden()
  expect(page.locator("#good .headline")).to_have_text(["core", "secrets", "usage"])
  assert page.locator("#summary-icon svg").evaluate("e => getComputedStyle(e).fill") == SUCCESS["dark"]


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_an_instance_with_only_the_core_invites_to_install_the_first_reef(portal_page, scheme):
  opened, expect = portal_page
  page = home(opened([], status=(200, EMPTY), scheme=scheme))
  expect(page.locator("#summary-title")).to_have_text("Instance ready")
  expect(page.locator("#summary-counts")).to_have_text("only the core · no reef")
  expect(page.locator("#status-rows")).to_be_hidden()
  expect(page.locator("#status-empty h2")).to_have_text("Install your first reef")
  expect(page.locator("#status-empty code")).to_have_text("$ nereus reef apply <reef>")
  expect(page.locator("#copy")).to_have_attribute("aria-label", "Copy the command")
  expect(page.locator("#see-reefs")).to_have_attribute("href", "https://docs.getnereus.dev/reference/reefs-and-nereids/")
  shot(page, f"home-phone-empty-{scheme}")


def test_the_copy_button_copies_the_command(portal_page):
  opened, expect = portal_page
  page = home(opened([], status=(200, EMPTY)))
  page.context.grant_permissions(["clipboard-read", "clipboard-write"])
  page.locator("#copy").click()
  expect(page.locator("#copy")).to_have_attribute("aria-label", "Copied")
  assert page.evaluate("navigator.clipboard.readText()") == "nereus reef apply <reef>"


def test_the_api_s_error_shows_with_a_retry(portal_page):
  opened, expect = portal_page
  page = home(opened([], status=DOWN))
  expect(page.locator("#summary-title")).to_have_text("The status did not load")
  expect(page.locator("#status-reason")).to_have_text("cannot read the cluster from the Kubernetes API")
  expect(page.locator("#status-rows")).to_be_hidden()
  shot(page, "home-phone-error-dark")
  page.stand.answers[0] = (200, STATUS)
  page.locator("#status-retry").click()
  expect(page.locator("#status-error")).to_be_hidden()
  expect(page.locator("#attention .headline")).to_have_text(["release", "tenancy"])


def test_the_home_screen_follows_the_language(portal_page):
  opened, expect = portal_page
  page = home(opened([], locale="pt-BR"))
  expect(page.locator("#summary-title")).to_have_text("1 reef precisa de atenção")
  expect(page.locator("#attention-title")).to_have_text("Precisa de atenção")
  expect(page.locator("#see-all")).to_have_text("Ver todos os 4")
  choose_language(page, "en")
  expect(page.locator("#summary-title")).to_have_text("1 reef needs attention")
  expect(page.locator("#see-all")).to_have_text("See all 4")


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_a_wide_screen_shows_count_chips_and_the_rows_in_two_columns(portal_page, scheme):
  opened, expect = portal_page
  page = home(opened([*PRESENTATIONS, USAGE], width=1280, height=800, scheme=scheme))
  expect(page.locator("#summary-counts")).to_be_hidden()
  expect(page.locator("#count-chips .chip")).to_have_text(["4 ready", "1 waiting", "1 need attention"])
  expect(page.locator("#see-all")).to_be_hidden()
  expect(page.locator("#good")).to_be_visible()
  first, second = (page.locator("#good .row").nth(n).bounding_box() for n in (0, 1))
  assert first["y"] == pytest.approx(second["y"], abs=1) and second["x"] > first["x"] + first["width"]
  shot(page, f"home-wide-{scheme}")


def test_a_pull_from_the_top_reloads_the_status_and_the_browser_s_own_pull_is_off(portal_page):
  opened, expect = portal_page
  page = home(opened([], touch=True))
  assert page.evaluate("getComputedStyle(document.documentElement).overscrollBehaviorY") == "contain"
  asked = len(page.stand.asked)
  cdp = page.context.new_cdp_session(page)
  cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 195, "y": 200}]})
  for y in range(220, 420, 20):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 195, "y": y}]})
  expect(page.locator("#pull")).to_have_attribute("data-ready", "")
  cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
  expect(page.locator("#pull")).not_to_have_attribute("data-pulling", "")
  for _ in range(40):
    if len(page.stand.asked) > asked:
      break
    page.wait_for_timeout(50)
  assert len(page.stand.asked) == asked + 1
  # A short pull does not reload.
  cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 195, "y": 200}]})
  cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 195, "y": 260}]})
  cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
  page.wait_for_timeout(300)
  assert len(page.stand.asked) == asked + 1


def test_the_status_reloads_every_30_seconds_while_visible(portal_page):
  opened, expect = portal_page
  page = home(opened([], clock=True))
  asked = len(page.stand.asked)
  page.clock.run_for(31000)
  for _ in range(40):
    if len(page.stand.asked) > asked:
      break
    page.wait_for_timeout(50)
  assert len(page.stand.asked) == asked + 1


@pytest.mark.parametrize("width", [340, 390])
@pytest.mark.parametrize("locale", ["pt-BR", "en-US"])
def test_nothing_on_the_home_screen_passes_the_phone_s_edge(portal_page, width, locale):
  opened, expect = portal_page
  page = home(opened([*PRESENTATIONS, USAGE], width=width, locale=locale))
  page.locator("#see-all").click()
  found = page.evaluate("""() => ({
    scroll: document.documentElement.scrollWidth > innerWidth,
    out: [...document.querySelectorAll('#status *, #app-bar *')].filter((e) => e.getBoundingClientRect().right > innerWidth + 0.5)
      .map((e) => e.id || e.className || e.tagName),
  })""")
  assert found == {"scroll": False, "out": []}


# The account sheet (#2024, Material 3): the avatar opens it; a bottom sheet on a phone, a side sheet from 600 px.
@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_on_a_phone_the_avatar_opens_a_bottom_sheet_with_the_account(portal_page, scheme):
  opened, expect = portal_page
  page = home(opened([*PRESENTATIONS], scheme=scheme))
  expect(page.locator(".lang")).to_be_hidden()
  expect(page.locator("#avatar-face")).to_have_text("AE")
  face = page.locator("#avatar-face").bounding_box()
  target = page.locator("#avatar").bounding_box()
  assert face["width"] == pytest.approx(32, abs=1) and target["width"] >= 48 and target["height"] >= 48
  open_sheet(page)
  sheet = page.locator("#account")
  expect(sheet).to_be_visible()
  expect(page.locator("#sheet-scrim")).to_be_visible()
  expect(page.locator("#avatar")).to_have_attribute("aria-expanded", "true")
  box = sheet.bounding_box()
  assert box["x"] == 0 and box["width"] == pytest.approx(390, abs=1) and box["y"] + box["height"] == pytest.approx(844, abs=1)
  expect(page.locator(".sheet-handle")).to_be_visible()
  expect(page.locator("#sheet-close")).to_be_hidden()
  expect(page.locator("#account-name")).to_have_text("Ana Example")
  expect(page.locator("#account-email")).to_have_text("ana@example.com")
  expect(page.locator("#role-chip")).to_have_text("Platform administrator")
  expect(page.locator("#account-groups .chip")).to_have_text(["nereus-admins", "nereus-users"])
  expect(page.locator("#via-provider")).to_have_text("Google")
  expect(page.locator("#via-host")).to_have_text("auth.example.com")
  expect(page.locator("#instance-name")).to_have_text("nereus-local")
  # #2045: the API's host, not the portal's, and the line that signs the CLI in.
  expect(page.locator("#instance-host")).to_have_text("nereus.example.com")
  expect(page.locator("#instance-terminal dt")).to_have_text("In the terminal")
  expect(page.locator("#instance-terminal code")).to_have_text("$ nereus login https://nereus.example.com")
  expect(page.locator('#account [data-action="signout"]')).to_be_visible()
  # The status screen stays where it was, behind the scrim.
  expect(page.locator("#status")).to_be_visible()
  shot(page, f"account-phone-{scheme}")
  page.keyboard.press("Escape")
  expect(sheet).to_be_hidden()
  expect(page.locator("#sheet-scrim")).to_be_hidden()
  expect(page.locator("#avatar")).to_be_focused()
  page.locator("#avatar").click()
  page.locator("#sheet-scrim").click(position={"x": 195, "y": 20})
  expect(sheet).to_be_hidden()



def test_the_sheet_s_copy_button_copies_the_nereus_login_line(portal_page):
  """#2045: a person signed in on the portal signs the CLI in with the line the sheet copies."""
  opened, expect = portal_page
  page = home(opened([]))
  page.context.grant_permissions(["clipboard-read", "clipboard-write"])
  open_sheet(page)
  expect(page.locator("#copy-login")).to_have_attribute("aria-label", "Copy the login command")
  page.locator("#copy-login").click()
  expect(page.locator("#copy-login")).to_have_attribute("aria-label", "Copied")
  assert page.evaluate("navigator.clipboard.readText()") == "nereus login https://nereus.example.com"


def test_an_instance_with_no_address_hides_its_host_and_the_terminal_block(portal_page):
  """#2045: no Gateway, only port-forward: the Installation has no url, so the sheet names the instance only."""
  opened, expect = portal_page
  bare = {**STATUS, "installation": {"name": "nereus", "alias": "nereus-local", "url": None}}
  page = home(opened([], locale="pt-BR", status=(200, bare)))
  open_sheet(page)
  expect(page.locator("#instance-name")).to_have_text("nereus-local")
  expect(page.locator("#instance-host")).to_be_hidden()
  expect(page.locator("#instance-terminal")).to_be_hidden()


def test_the_terminal_block_speaks_portuguese(portal_page):
  opened, expect = portal_page
  page = home(opened([], locale="pt-BR"))
  open_sheet(page)
  expect(page.locator("#instance-terminal dt")).to_have_text("No terminal")
  expect(page.locator("#copy-login")).to_have_attribute("aria-label", "Copiar o comando de login")

@pytest.mark.parametrize("width", [700, 1280])
@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_from_600_px_the_avatar_opens_a_440_px_side_sheet_with_a_close_button(portal_page, width, scheme):
  opened, expect = portal_page
  page = home(opened([*PRESENTATIONS], width=width, height=800, scheme=scheme))
  open_sheet(page)
  box = page.locator("#account").bounding_box()
  assert box["width"] == pytest.approx(440, abs=1) and box["x"] + box["width"] == pytest.approx(width, abs=1)
  assert box["y"] == 0 and box["height"] == pytest.approx(800, abs=1)
  expect(page.locator(".sheet-handle")).to_be_hidden()
  expect(page.locator("#sheet-close")).to_be_focused()
  expect(page.locator("#sheet-close")).to_have_attribute("aria-label", "Close")
  shot(page, f"account-wide-{width}-{scheme}")
  page.locator("#sheet-close").click()
  expect(page.locator("#account")).to_be_hidden()


def test_without_nereus_admins_there_is_no_role_and_the_login_names_the_instance_s_issuer(portal_page):
  opened, expect = portal_page
  page = home(opened([], person=BRUNO))
  page.locator("#avatar").click()
  expect(page.locator("#role-row")).to_be_hidden()
  expect(page.locator("#account-groups .chip")).to_have_text(["nereus-users"])
  expect(page.locator("#via-provider")).to_have_text("The instance's login")


def test_the_language_switch_lives_in_the_sheet(portal_page):
  opened, expect = portal_page
  page = home(opened([*PRESENTATIONS], locale="pt-BR"))
  page.locator("#avatar").click()
  expect(page.locator('#account [data-language="pt-BR"]')).to_have_attribute("aria-pressed", "true")
  expect(page.locator("#role-chip")).to_have_text("Administrador da plataforma")
  expect(page.locator('#account [data-action="signout"]')).to_have_text("Sair")
  page.locator('#account [data-language="en"]').click()
  expect(page.locator("#account")).to_be_visible()
  expect(page.locator("#role-chip")).to_have_text("Platform administrator")
  expect(page.locator('#account [data-action="signout"]')).to_have_text("Sign out")
  expect(page.locator("#summary-title")).to_have_text("1 reef needs attention")


def test_the_focus_stays_in_the_sheet_while_it_is_open(portal_page):
  opened, expect = portal_page
  page = home(opened([], width=1280, height=800))
  page.locator("#avatar").click()
  expect(page.locator("#sheet-close")).to_be_focused()
  for _ in range(6):
    page.keyboard.press("Tab")
    assert page.evaluate("document.getElementById('account').contains(document.activeElement)")
  page.keyboard.press("Shift+Tab")
  assert page.evaluate("document.getElementById('account').contains(document.activeElement)")


def test_a_drag_down_closes_the_bottom_sheet_and_a_short_one_puts_it_back(portal_page):
  opened, expect = portal_page
  page = home(opened([], touch=True))
  open_sheet(page)
  cdp = page.context.new_cdp_session(page)

  def drag(to):
    top = page.locator("#account").bounding_box()["y"]
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 195, "y": top + 10}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 195, "y": top + to}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

  drag(40)
  expect(page.locator("#account")).to_be_visible()
  drag(200)
  expect(page.locator("#account")).to_be_hidden()


@pytest.mark.parametrize("width", [340, 390])
@pytest.mark.parametrize("locale", ["pt-BR", "en-US"])
def test_nothing_in_the_bottom_sheet_passes_the_phone_s_edge(portal_page, width, locale):
  opened, expect = portal_page
  page = home(opened([], width=width, locale=locale))
  open_sheet(page)
  found = page.evaluate("""() => [...document.querySelectorAll('#account *')]
    .filter((e) => e.offsetParent !== null && e.getBoundingClientRect().right > innerWidth + 0.5)
    .map((e) => e.id || e.className || e.tagName)""")
  assert found == []


# Each Nereid's signals (#744): GET /v1/status's rows with a Nereid carry signals (null without the metrics reef); the
# home shows them in a list or a grid, under filter chips, the view kept in the browser.
def wave(base, points=60):
  return [round(base * (1 + 0.5 * ((n * 7) % 11) / 11), 4) for n in range(points)]


def signals(rate, errors, p95):
  return {"rate": rate, "errorRatio": errors, "p95Seconds": p95, "saturation": 0.05, "stuckSeconds": 0.0, "series": {"rate": wave(rate or 0.01)}}


SIGNALLED = {
  "installation": INSTALLATION,
  "registry": None,
  "items": [
    CORE_ROW,
    {**row("presentations", "leagore"), "signals": signals(0.08, 0.0, 0.12)},
    {**row("release", "flux", "NotReady", "the HelmRelease podinfo failed: install retries exhausted"), "signals": signals(0.31, 0.12, 0.84)},
    {**row("secrets", "openbao"), "signals": signals(1.5, None, 1.25)},
    row("tenancy", "-", "Waiting", version="-"),
    {**row("usage", "reference-usage"), "signals": signals(None, 0.0, None)},
  ],
}
ERROR = {"dark": rgb("#f2b8b5"), "light": rgb("#b3261e")}
BLOCKED = "Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked', 'SecurityError'); } });"


def to_grid(page, expect):
  page.locator('#status-rows [data-view="grid"]').click()
  expect(page.locator("#status-grid")).to_be_visible()


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_the_list_shows_each_nereid_s_red_line_and_sparkline(portal_page, scheme):
  opened, expect = portal_page
  page = home(opened([], scheme=scheme, status=(200, SIGNALLED)))
  expect(page.locator('#status-rows [data-filter="all"]')).to_have_attribute("aria-pressed", "true")
  expect(page.locator('#status-rows [data-view="list"]')).to_have_attribute("aria-pressed", "true")
  expect(page.locator("#status-list")).to_be_visible()
  expect(page.locator("#status-grid")).to_be_hidden()
  expect(page.locator("#no-metrics")).to_be_hidden()
  release = page.locator("#attention .row").first
  expect(release.locator(".red-line span")).to_have_text(["0.31/s", "12% err", "p95 840ms"])
  assert release.locator(".red-errors").evaluate("e => getComputedStyle(e).color") == ERROR[scheme]
  assert release.locator(".spark-line").evaluate("e => getComputedStyle(e).stroke") == WARNING[scheme]
  # The Nereid-less row keeps its state and shows no numbers.
  tenancy = page.locator("#attention .row").nth(1)
  expect(tenancy.locator(".chip")).to_have_text("Waiting")
  expect(tenancy.locator(".red-line, .spark")).to_have_count(0)
  shot(page, f"signals-list-phone-{scheme}")
  page.locator("#see-all").click()
  good = page.locator("#good .row")
  expect(good.nth(0).locator(".red-line")).to_have_count(0)
  expect(good.nth(1).locator(".red-line span")).to_have_text(["4.8/min", "0% err", "p95 120ms"])
  assert good.nth(1).locator(".red-errors").evaluate("e => getComputedStyle(e).color") != ERROR[scheme]
  assert good.nth(1).locator(".spark-line").evaluate("e => getComputedStyle(e).stroke") == SUCCESS[scheme]
  # A failed query nulls only its field: a dash, never 0.
  expect(good.nth(2).locator(".red-line span")).to_have_text(["1.50/s", "– err", "p95 1.3s"])
  expect(good.nth(3).locator(".red-line span")).to_have_text(["–", "0% err", "p95 –"])


@pytest.mark.parametrize("scheme", ["dark", "light"])
def test_the_grid_shows_two_columns_of_cards_attention_first_and_the_choice_is_kept(portal_page, scheme):
  opened, expect = portal_page
  page = home(opened([], scheme=scheme, status=(200, SIGNALLED)))
  to_grid(page, expect)
  expect(page.locator('#status-rows [data-view="grid"]')).to_have_attribute("aria-pressed", "true")
  expect(page.locator("#status-list")).to_be_hidden()
  cards = page.locator("#status-grid .signal-card")
  expect(cards.locator(".card-reef")).to_have_text(["release", "tenancy", "core", "presentations", "secrets", "usage"])
  first, second, third = (cards.nth(n).bounding_box() for n in (0, 1, 2))
  assert first["y"] == pytest.approx(second["y"], abs=1) and second["x"] > first["x"] + first["width"]
  assert third["y"] > first["y"] + first["height"] - 1
  assert cards.nth(0).evaluate("e => getComputedStyle(e).borderTopColor") == WARNING[scheme]
  assert cards.nth(2).evaluate("e => getComputedStyle(e).borderTopColor") == "rgba(0, 0, 0, 0)"
  expect(cards.nth(0).locator(".card-nereid")).to_have_text("flux")
  expect(cards.nth(0).locator(".card-state")).to_have_text("NotReady")
  expect(cards.nth(0).locator(".card-rate")).to_have_text("0.31/s")
  expect(cards.nth(0).locator(".red-errors")).to_have_text("12%")
  assert cards.nth(0).locator(".red-errors").evaluate("e => getComputedStyle(e).color") == ERROR[scheme]
  expect(cards.nth(0).locator(".spark")).to_have_count(1)
  expect(cards.nth(1).locator(".card-numbers, .spark")).to_have_count(0)
  expect(cards.nth(3).locator(".card-rate")).to_have_text("4.8/min")
  shot(page, f"signals-grid-phone-{scheme}")
  page.reload()
  home(page)
  expect(page.locator("#status-grid")).to_be_visible()
  page.locator('#status-rows [data-view="list"]').click()
  page.reload()
  home(page)
  expect(page.locator("#status-list")).to_be_visible()


def test_the_chips_filter_both_views(portal_page):
  opened, expect = portal_page
  page = home(opened([], status=(200, SIGNALLED)))
  page.locator('#status-rows [data-filter="attention"]').click()
  expect(page.locator('#status-rows [data-filter="attention"]')).to_have_attribute("aria-pressed", "true")
  expect(page.locator('#status-rows [data-filter="all"]')).to_have_attribute("aria-pressed", "false")
  expect(page.locator("#attention .headline")).to_have_text(["release", "tenancy"])
  expect(page.locator("#good-title")).to_be_hidden()
  expect(page.locator("#see-all")).to_be_hidden()
  to_grid(page, expect)
  expect(page.locator("#status-grid .card-reef")).to_have_text(["release", "tenancy"])
  page.locator('#status-rows [data-filter="ready"]').click()
  expect(page.locator("#status-grid .card-reef")).to_have_text(["core", "presentations", "secrets", "usage"])
  page.locator('#status-rows [data-view="list"]').click()
  expect(page.locator("#attention-title")).to_be_hidden()
  expect(page.locator("#good .headline")).to_have_text(["core", "presentations", "secrets", "usage"])
  expect(page.locator("#good")).to_be_visible()
  expect(page.locator("#filter-empty")).to_be_hidden()


def test_without_the_metrics_reef_the_rows_keep_today_s_form_and_one_line_says_so(portal_page):
  opened, expect = portal_page
  page = home(opened([], locale="pt-BR"))
  expect(page.locator("#no-metrics")).to_have_text("sem métricas: instale o reef de métricas")
  expect(page.locator("#status .red-line, #status .spark")).to_have_count(0)
  expect(page.locator("#status-rows [data-filter]")).to_have_text(["Todos", "Atenção", "Prontos"])
  expect(page.locator('#status-rows [data-view="grid"]')).to_have_attribute("aria-label", "Grade")
  choose_language(page, "en")
  expect(page.locator("#no-metrics")).to_have_text("no metrics: install the metrics reef")
  to_grid(page, expect)
  expect(page.locator("#status-grid .card-numbers, #status-grid .spark")).to_have_count(0)


def test_blocked_storage_opens_the_list_and_the_toggle_still_works(portal_page):
  opened, expect = portal_page
  page = home(opened([], status=(200, SIGNALLED), script=BLOCKED))
  expect(page.locator("#status-list")).to_be_visible()
  to_grid(page, expect)
  page.reload()
  home(page)
  expect(page.locator("#status-list")).to_be_visible()


@pytest.mark.parametrize("width", [340, 360, 390, 412])
@pytest.mark.parametrize("locale", ["pt-BR", "en-US"])
def test_neither_view_nor_the_chips_pass_the_phone_s_edge(portal_page, width, locale):
  """docs/agent/decks.md, Screens on a phone: the chips and the toggle on one row, both views, measured in both
  languages at 340 to 412 px: nothing past the screen's edge, no horizontal scroll, no label cut."""
  opened, expect = portal_page
  page = home(opened([], width=width, locale=locale, status=(200, SIGNALLED)))
  page.locator("#see-all").click()
  measure = """() => ({
    scroll: document.documentElement.scrollWidth > innerWidth,
    out: [...document.querySelectorAll('#status *')].filter((e) => e.getBoundingClientRect().right > innerWidth + 0.5)
      .map((e) => e.id || e.getAttribute('class') || e.tagName),
    cut: [...document.querySelectorAll('.filter-chip, .card-rate, .red-line')]
      .filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.textContent),
    rows: new Set([...document.querySelectorAll('.toolbar > *')].map((e) => { const r = e.getBoundingClientRect(); return Math.round(r.top + r.height / 2); })).size,
  })"""
  assert page.evaluate(measure) == {"scroll": False, "out": [], "cut": [], "rows": 1}
  to_grid(page, expect)
  assert page.evaluate(measure) == {"scroll": False, "out": [], "cut": [], "rows": 1}
  if width == 390 and locale == "en-US":
    shot(page, "signals-list-then-grid-390-en")

