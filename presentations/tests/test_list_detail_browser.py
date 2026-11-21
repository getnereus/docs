"""From 840 px the Sessions screen is a Material 3 list-detail layout (#1842), in headless Chromium inside the real portal
(index.html, app.js, app.css, its navigation rail, under the portal's exact policy), signed in through the stand-in of
oidc-client-ts, with leagore's real drive.js and drive.css on the Sessions of test_drive_browser.py. At 1280x800 the list
stays on the left beside the rail, a Session chosen there opens in the detail on the right (its row in secondary
container, the detail in surface container low with radius 24), and Next and End are pressed in the detail; a resize to
390 px shows the open Session alone, as on a phone, the portal's rail and bar aside, and back at 1280 the same Session
is still open and selected. The deck engine's Session opens in the detail too, the engine taking the space left. Every
control is measured inside the window and uncut in English and Portuguese at 1280x800 and 1024x768. Set DRIVE_SHOTS to a
folder to keep the screenshots (1280x800 and 1024x768, dark and light). Every name is invented. Skips with no browser."""
import re

import pytest
from test_drive_browser import LANGS, MEASURE, SESSION, Stand, chromium, shots
from test_follow_browser import LISTENER, portal
from test_portal_navigation_browser import OIDC

SCREENS = [
  {"reef": "presentations", "tab": "Sessions", "element": "nereus-presentations-drive", "module": "drive.js", "icon": "presentation"},
  {"reef": "presentations", "tab": "Decks", "element": "nereus-presentations-decks", "module": "decks.js", "icon": "folder"},
]
SIZES = ((1280, 800), (1024, 768))
WIDE = ".session, .chip, .stage-name, .subtitle, .share, .full, .bar .end, .stage-ended, .controls button, .pace, .part, .remaining, .upcoming, .progress, .pick, .elapsed, .total"
# The two panes' boxes, the selected row and the colors the detail and the row take from the portal's roles.
PANES = """() => {
  const root = document.querySelector('nereus-presentations-drive').shadowRoot;
  const box = (node) => (node && node.getClientRects().length ? node.getBoundingClientRect().toJSON() : null);
  const detail = root.querySelector('.detail');
  const selected = root.querySelector('.session[aria-current="true"]');
  return {
    list: box(root.querySelector('.list-pane')), detail: box(detail), rail: box(document.getElementById('tabs')),
    selected: selected ? selected.querySelector('.headline').textContent : null,
    selectedBg: selected ? getComputedStyle(selected).backgroundColor : null,
    detailBg: getComputedStyle(detail).backgroundColor, radius: getComputedStyle(detail).borderTopLeftRadius,
    back: box(root.querySelector('[data-role=back]')),
  };
}"""
# A role of the portal, as the page computes it (a hex color).
ROLE = "(name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()"


def rgb(value):
  """A #rrggbb as the browser writes a computed color."""
  assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), value
  return "rgb({}, {}, {})".format(*(int(value[n:n + 2], 16) for n in (1, 3, 5)))


class Portal(Stand):
  """test_drive_browser.py's stand of the Sessions, served inside the real portal: its pages, the sign-in stand-in, the
  screens' list and leagore's files under /reefs/presentations/ui/."""

  def __init__(self, directory, **options):
    super().__init__(directory, **options)
    self.files.update(portal.files())

  def answer(self, path):
    js = "text/javascript; charset=utf-8"
    if path == "/vendor/oidc-client-ts-3.5.0.min.js":
      return 200, js, OIDC.encode(), False
    if path == "/config.json":
      return self.json({"issuer": "https://auth.example.com/realms/nereus", "clientId": "nereus-portal", "publicUrl": "https://portal.example.com"})
    if path == "/v1/me":
      return self.json({"sub": "u1", "name": "Ana Example", "email": "ana@example.com"})
    if path == "/v1/screens":
      return self.json({"items": SCREENS})
    if path == "/sw.js":
      return 404, "text/plain", b"no worker on the stand\n", False
    if path.startswith("/reefs/presentations/ui/"):
      return super().answer("/" + path.rsplit("/", 1)[1])
    return super().answer(path)


def portal_page(playwright, browser, stand, lang, width, height, scheme="dark"):
  """The portal at a size, a scheme and a language, on the Sessions tab, its list drawn."""
  context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, reduced_motion="reduce",
                                locale="pt-BR" if lang == "pt" else "en-US")
  page = context.new_page()
  errors, outside = [], []
  page.add_init_script(LISTENER)
  page.on("pageerror", lambda error: errors.append(str(error)))
  page.on("request", lambda request: None if request.url.startswith((stand.url, "data:")) else outside.append(request.url))
  page.goto(stand.url + "/")
  page.locator("#tabs [data-tab]").nth(1).click()
  page.locator("[data-role=session]").first.wait_for(timeout=5000)
  return page, errors, outside


def measured(page, width):
  """Every control drawn inside the window, none cut, no horizontal scroll; the ones to press at least 48 px high."""
  found = page.evaluate(MEASURE, WIDE)
  assert found["scroll"] <= found["width"], found
  for box in found["boxes"]:
    assert box["left"] >= 0 and box["right"] <= width + 0.5, (width, box)
    assert not box["cut"], (width, box)
    if box["role"] in ("session", "share", "full", "prev", "next", "end"):
      assert box["height"] >= 48, box
  return found["boxes"]


def test_a_wide_screen_drives_a_session_from_the_detail_beside_the_list_and_a_resize_keeps_it(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Portal(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        for width, height in SIZES:
          stand.step, stand.ended, stand.posts = 0, None, []
          page, errors, outside = portal_page(playwright, browser, stand, lang, width, height)
          # Nothing chosen yet: the list beside the rail, the detail saying what to do, no back.
          panes = page.evaluate(PANES)
          assert panes["rail"] and panes["list"] and panes["detail"], panes
          assert panes["rail"]["right"] <= panes["list"]["left"] < panes["list"]["right"] <= panes["detail"]["left"], panes
          assert panes["selected"] is None and page.locator("[data-role=pick]").is_visible()
          measured(page, width)
          page.locator("[data-role=session]").first.click()
          page.locator("[data-role=controls]").wait_for(timeout=5000)
          panes = page.evaluate(PANES)
          assert panes["selected"] == SESSION and panes["back"] is None, panes
          assert panes["selectedBg"] == rgb(page.evaluate(ROLE, "--nereus-secondary-container")), panes
          assert panes["detailBg"] == rgb(page.evaluate(ROLE, "--nereus-surface-container-low")) and panes["radius"] == "24px", panes
          assert panes["detail"]["bottom"] <= height + 0.5, panes
          # The portal keeps its rail and its app bar beside the list (nereus-focus says no whole view from 840 px).
          assert page.locator("#tabs").is_visible() and page.locator("#app-bar").is_visible()
          boxes = measured(page, width)
          prev, nxt = (next(box for box in boxes if box["role"] == role) for role in ("prev", "next"))
          assert prev["height"] == nxt["height"] == 72 and nxt["width"] > prev["width"], (prev, nxt)
          # A step from the detail: the slide moves, the post reaches the API, and the row's chip turns Live.
          page.locator("[data-role=next]").click()
          page.locator("[data-role=progress]").filter(has_text="2").wait_for(timeout=2000)
          page.wait_for_function("() => document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('.session[aria-current=\"true\"] .chip.live')")
          assert stand.posts == [1], stand.posts
          if lang == "en" and shots():
            for scheme in ("dark", "light"):
              page.emulate_media(color_scheme=scheme)
              page.wait_for_timeout(300)
              page.screenshot(path=str(shots() / f"list-detail-{width}x{height}-{scheme}.png"))
            page.emulate_media(color_scheme="dark")
          # A resize to a phone: the open Session alone, the portal's rail and bar aside, Back on screen.
          page.set_viewport_size({"width": 390, "height": 844})
          page.locator("[data-role=back]").wait_for(timeout=2000)
          sync_api.expect(page.locator("#tabs")).to_be_hidden()
          assert page.locator("[data-role=sessions]").is_hidden()
          assert page.locator("[data-role=progress]").inner_text().startswith("Step 2" if lang == "en" else "Passo 2")
          # Back at the wide size: the same Session, still selected, on the same step.
          page.set_viewport_size({"width": width, "height": height})
          page.locator("[data-role=sessions]").wait_for(timeout=2000)
          sync_api.expect(page.locator("#tabs")).to_be_visible()
          assert page.evaluate(PANES)["selected"] == SESSION
          assert page.locator("[data-role=progress]").inner_text().startswith("Step 2" if lang == "en" else "Passo 2")
          for _ in range(2):
            page.locator("[data-role=next]").click()
          page.locator("[data-role=end]").wait_for(timeout=2000)
          measured(page, width)
          page.locator("[data-role=end]").click()
          page.locator("[data-role=status]").filter(has_text="Ended" if lang == "en" else "Encerrada").wait_for(timeout=2000)
          assert stand.posts == [1, 2, 3] and stand.ended
          assert page.evaluate("() => window.__csp") == [] and errors == [] and outside == []
          page.context.close()
      browser.close()
  finally:
    stand.close()


def test_a_wide_screen_hosts_the_deck_engine_in_the_detail(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Portal(tmp_path, engine=True)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        for width, height in SIZES:
          page, errors, outside = portal_page(playwright, browser, stand, lang, width, height)
          page.locator("[data-role=session]").first.click()
          page.frame_locator("iframe").locator("#joy").wait_for(state="attached", timeout=5000)
          panes = page.evaluate(PANES)
          frame = page.evaluate("() => document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('iframe').getBoundingClientRect().toJSON()")
          assert panes["detail"]["left"] <= frame["left"] and frame["right"] <= panes["detail"]["right"], (panes, frame)
          assert frame["bottom"] <= height and frame["height"] > (height - 64) * 0.6, frame
          measured(page, width)
          if lang == "en" and shots():
            for scheme in ("dark", "light"):
              page.emulate_media(color_scheme=scheme)
              page.wait_for_timeout(400)
              page.screenshot(path=str(shots() / f"list-detail-engine-{width}x{height}-{scheme}.png"))
          assert page.evaluate("() => window.__csp") == [] and errors == [] and outside == []
          page.context.close()
      browser.close()
  finally:
    stand.close()

