"""The terminal's toolbar (#2361), in headless Chromium under the portal's policy: a terminal shows only ⋯; a tap opens
copy, A−/A+ and narrow/widen, labelled in the deck's language; the font and the width are one setting for every terminal
of the deck, kept on the device after a reload; an open toolbar fits a phone's terminal at its narrowest, and folds
back on Esc and on a tap outside. Skips with no browser. The release deck: its first slides are terminals."""
import pytest

from test_drive_browser import LANGS, chromium
from test_portal_mode import portal, serve
from test_steps import RECORD, render

DECK = "release"
FIRST = "apply-reef"
LABELS = {"en": ("Terminal options", "Larger font"), "pt": ("Opções do terminal", "Fonte maior")}
STATE = """() => {
  const terms = [...document.querySelectorAll('.term')];
  const on = document.querySelector('.slide.on .term');
  const tt = on.querySelector('.tt'), bar = on.querySelector('.bar');
  const box = node => node.getBoundingClientRect();
  const shown = [...tt.querySelectorAll('button')].filter(node => node.getClientRects().length > 0);
  return {
    sizes: [...new Set(terms.map(term => getComputedStyle(term).fontSize))],
    width: box(on).width, view: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth,
    open: tt.classList.contains('open'), shown: shown.map(node => node.dataset.act),
    inside: shown.every(node => box(node).left >= box(bar).left - 0.5 && box(node).right <= box(bar).right + 0.5),
  };
}"""


def opened(browser, server, lang, width):
  page = browser.new_page(viewport={"width": width, "height": 800})
  errors = []
  page.on("pageerror", lambda error: errors.append(str(error)))
  page.add_init_script(f"try {{ localStorage.setItem('deck.motion', 'off'); localStorage.setItem('deck.lang', '{lang}'); }} catch (e) {{}}" + RECORD)
  page.goto(f"http://127.0.0.1:{server.server_address[1]}/{DECK}.html#{FIRST}", wait_until="load")
  return page, errors


def tool(page, act):
  page.locator(f".slide.on .term .tt button[data-act='{act}']").click()


@pytest.mark.parametrize("lang", LANGS)
def test_the_toolbar_folds_behind_more_and_sets_every_terminal_of_the_deck(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  render(tmp_path, DECK)
  server = serve(tmp_path, portal.csp("https://auth.example.com"))
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      # A phone: folded, only ⋯; open, every button inside the bar at the narrowest terminal.
      page, errors = opened(browser, server, lang, 390)
      state = page.evaluate(STATE)
      assert not state["open"] and state["shown"] == ["more"]
      more = page.locator(".slide.on .term .tt .more")
      assert more.get_attribute("aria-label") == LABELS[lang][0]
      more.click()
      state = page.evaluate(STATE)
      assert state["open"] and state["shown"] == ["copy", "smaller", "larger", "narrow", "wide", "more"]
      assert page.locator(".slide.on .term .tt [data-act='larger']").get_attribute("aria-label") == LABELS[lang][1]
      before = state["sizes"]
      assert len(before) == 1, "every terminal starts at one size"
      tool(page, "larger")
      after = page.evaluate(STATE)["sizes"]
      assert len(after) == 1 and float(after[0][:-2]) > float(before[0][:-2]), "A+ grows every terminal of the deck"
      narrow = page.locator(".slide.on .term .tt [data-act='narrow']")
      for _ in range(20):
        if narrow.get_attribute("aria-disabled") == "true":
          break
        narrow.click()
      state = page.evaluate(STATE)
      assert state["inside"] and state["scroll"] <= state["view"], state
      assert narrow.get_attribute("aria-disabled") == "true", "the narrowest stops"
      page.keyboard.press("Escape")
      assert not page.evaluate(STATE)["open"], "Esc folds it"
      # The setting stays on the device: a reload opens every terminal with it.
      page.reload(wait_until="load")
      assert page.evaluate(STATE)["sizes"] == after
      assert errors == []
      page.close()

      # A computer: widen grows the terminal past the slide, never past the screen; a tap outside folds it.
      page, errors = opened(browser, server, lang, 1280)
      more = page.locator(".slide.on .term .tt .more")
      more.click()
      start = page.evaluate(STATE)["width"]
      tool(page, "wide")
      tool(page, "wide")
      state = page.evaluate(STATE)
      assert state["width"] > start and state["width"] <= state["view"] - 32 + 0.5 and state["scroll"] <= state["view"], state
      page.mouse.click(5, 400)
      assert not page.evaluate(STATE)["open"], "a tap outside folds it"
      assert errors == []
      page.close()
      browser.close()
  finally:
    server.shutdown()
