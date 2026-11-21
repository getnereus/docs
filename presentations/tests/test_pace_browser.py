"""The room's pace thermometer (#1723), end to end in headless Chromium.

The speaker turns the Pace thermometer on from the drive screen's Share sheet; three phones of 340, 390 and 412 px show
Too slow and Too fast and tap (one slow, two fast); each phone marks only its own button, and the drive screen's gauge
counts the taps. A minute later, on the stand-in's clock and the phones' (Playwright's fake clock), the taps fade: the
gauge goes back to zero and no phone keeps its mark. With the switch off, the follow page shows no buttons and the
gauge goes. Both languages; the buttons and the gauge fit each phone with no horizontal scroll and no CSP violation.

The server is a stand-in for the portal and the API (test_drive_browser's Stand, with the follow page and a stream sent
again every 300 ms, and the thermometer's routes counting each device's latest tap for a minute, as leagore does);
every name is invented. Skips with no browser."""
import datetime
import json

import pytest
from test_drive_browser import BASE, LANGS, Stand, chromium, fits, opened
from test_follow_browser import CODE, LISTENER, frame, portal
from test_questions_browser import FOLLOW, follower

PACE = 60
WORDS = {"en": ("Too slow", "Too fast"), "pt": ("Muito lento", "Muito rápido")}
PHONES = (340, 390, 412)
# The pace buttons on a phone: each inside the screen, at least 44 px high, its text never cut, and no sideways scroll.
PHONE_MEASURE = """() => {
  const boxes = [...document.querySelectorAll('#thermometer, #thermometer button')].filter((node) => node.getClientRects().length > 0).map((node) => {
    const box = node.getBoundingClientRect();
    return { id: node.id, left: box.left, right: box.right, bottom: box.bottom, height: box.height, cut: node.scrollWidth > node.clientWidth + 1 };
  });
  return { width: document.documentElement.clientWidth, height: window.innerHeight, scroll: document.documentElement.scrollWidth, boxes };
}"""
GAUGE = ".gauge-panel, .gauge-side, .gauge-label, .gauge-count, .controls button"
SHADOW = "document.querySelector('nereus-presentations-drive').shadowRoot"


class Pacing(Stand):
  """The drive's stand with the follow page, the thermometer's switch and the phones' taps: one per device, counting for a
  minute on the stand's clock, which a test moves forward with `shift`."""

  def __init__(self, directory):
    super().__init__(directory)
    self.thermometer = False
    self.taps: dict[str, tuple[str, datetime.datetime]] = {}
    self.shift = 0.0

  def now(self):
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=self.shift)

  def gauge(self):
    since = self.now() - datetime.timedelta(seconds=PACE)
    with self.lock:
      counted = [vote for vote, at in self.taps.values() if at > since]
    return {"slow": counted.count("slow"), "fast": counted.count("fast")}

  def state(self):
    return {**super().state(), "thermometer": self.thermometer}

  def answer(self, path):
    if path == f"/p/{CODE}":
      return 200, "text/html; charset=utf-8", (portal.STATIC / "follow.html").read_bytes(), False
    if path == f"{FOLLOW}/deck":
      return 200, "text/html; charset=utf-8", self.deck, False
    if path == FOLLOW:
      # The followers' state: whether the buttons show, never the counts; sent again every 300 ms.
      state = {**self.state(), "now": self.now().isoformat().replace("+00:00", "Z")}
      return 200, "text/event-stream", b"retry: 300\n\n" + frame("state", state), False
    if path == f"{BASE}/thermometer":
      return self.json({"on": self.thermometer, **self.gauge()})
    if path == BASE:
      status, kind, body, framed = super().answer(path)
      found = json.loads(body)
      found["state"]["gauge"] = self.gauge() if self.thermometer else None
      return status, kind, json.dumps(found).encode(), framed
    return super().answer(path)

  def posted(self, path, body):
    if path == f"{BASE}/thermometer":
      self.thermometer = body["on"] is True
      return self.json(self.state())
    if path == f"{FOLLOW}/pace":
      if not self.thermometer:
        return 409, "application/json", b'{"error": {"code": "Refused", "message": "the thermometer is off"}}', False
      at = self.now()
      with self.lock:
        self.taps[body["device"]] = (body["vote"], at)
      stamp = lambda moment: moment.isoformat().replace("+00:00", "Z")  # noqa: E731
      return self.json({"result": "configured", "vote": body["vote"], "at": stamp(at), "fades": stamp(at + datetime.timedelta(seconds=PACE))})
    return super().posted(path, body)


def counts(speaker):
  return speaker.evaluate(f"() => [...{SHADOW}.querySelectorAll('.gauge-count')].map((node) => node.textContent).join('/')")


def switch(speaker):
  """The Share sheet's Pace thermometer switch, pressed, then the sheet closed: its aria-checked after the press."""
  speaker.locator("[data-role=share]").click()
  toggle = speaker.locator("[data-role=share-thermometer]")
  toggle.click()
  checked = toggle.get_attribute("aria-checked")
  speaker.locator("[data-role=done]").click()
  return checked


def tapped(page, vote):
  """One phone taps `vote`: only that button is marked, and the buttons fit the phone."""
  page.click(f"#thermometer-{vote}")
  page.wait_for_function(f"() => document.querySelector('#thermometer-{vote}').classList.contains('chosen')", timeout=5000)
  assert page.locator("#thermometer .chosen").count() == 1, "each phone marks only its own tap"
  assert page.get_attribute(f"#thermometer-{vote}", "aria-pressed") == "true"
  found = page.evaluate(PHONE_MEASURE)
  assert found["scroll"] <= found["width"] and len(found["boxes"]) == 3, found
  for box in found["boxes"]:
    assert box["left"] >= 0 and box["right"] <= found["width"] + 0.5 and box["bottom"] <= found["height"] + 0.5, (found["width"], box)
    assert not box["cut"] and box["height"] >= 44, (found["width"], box)


@pytest.mark.parametrize("lang", LANGS)
def test_three_phones_tap_the_speaker_sees_the_gauge_and_a_minute_later_the_taps_fade(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Pacing(tmp_path)
  slow, fast = WORDS[lang]
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phones = [follower(browser, playwright, lang, width) for width in PHONES]
      for page, _ in phones:
        page.clock.install()
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        page.wait_for_function(f"() => document.querySelector('#thermometer-slow').textContent === {json.dumps(slow)}", timeout=5000)
      speaker = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
      speaker_errors = []
      speaker.on("pageerror", lambda error: speaker_errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      opened(speaker, stand, lang, 390)
      speaker.locator("[data-role=session]").first.click()
      speaker.locator("[data-role=share]").wait_for(state="visible", timeout=5000)
      assert speaker.locator("[data-role=gauge]").is_hidden(), "no gauge while off"
      for page, _ in phones:
        assert page.locator("#thermometer").is_hidden(), "no buttons while off"

      assert switch(speaker) == "true" and stand.thermometer
      speaker.locator("[data-role=gauge]").wait_for(state="visible", timeout=5000)
      for page, _ in phones:
        page.locator("#thermometer").wait_for(state="visible", timeout=5000)
        assert page.locator("#thermometer button").all_text_contents() == [slow, fast]
      for (page, _), vote in zip(phones, ("slow", "fast", "fast")):
        tapped(page, vote)
      speaker.wait_for_function(f"() => [...{SHADOW}.querySelectorAll('.gauge-count')].map((node) => node.textContent).join('/') === '1/2'", timeout=5000)
      label = speaker.locator("[data-role=gauge]").get_attribute("aria-label")
      assert label == ("Pace: 1 too slow, 2 too fast" if lang == "en" else "Ritmo: 1 muito lento, 2 muito rápido"), label
      assert speaker.locator(".gauge-label").all_text_contents() == [slow, fast]
      for width in PHONES:
        speaker.set_viewport_size({"width": width, "height": 844})
        assert len(fits(speaker, GAUGE)) >= 5

      # A minute later, on the stand's clock and the phones': every tap fades.
      stand.shift += PACE + 1
      for page, _ in phones:
        page.clock.fast_forward((PACE + 1) * 1000)
      speaker.wait_for_function(f"() => [...{SHADOW}.querySelectorAll('.gauge-count')].map((node) => node.textContent).join('/') === '0/0'", timeout=5000)
      for page, _ in phones:
        page.wait_for_function("() => document.querySelectorAll('#thermometer .chosen').length === 0", timeout=5000)
        assert page.locator("#thermometer").is_visible()

      assert switch(speaker) == "false" and not stand.thermometer
      for page, _ in phones:
        page.locator("#thermometer").wait_for(state="hidden", timeout=5000)
      assert speaker.locator("[data-role=gauge]").is_hidden()
      assert counts(speaker) == "0/0"

      assert [errors for _, errors in phones] == [[], [], []] and speaker_errors == []
      for page in [page for page, _ in phones] + [speaker]:
        assert page.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


def test_the_projector_never_shows_the_pace_buttons(tmp_path):
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Pacing(tmp_path)
  stand.thermometer = True
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phone, _ = follower(browser, playwright, "en", 390)
      phone.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      phone.locator("#thermometer").wait_for(state="visible", timeout=5000)
      projector = browser.new_context(viewport={"width": 1280, "height": 720}).new_page()
      projector.add_init_script(LISTENER)
      projector.goto(f"{stand.url}/p/{CODE}?projector", wait_until="load")
      projector.wait_for_function("() => document.body.classList.contains('projector')", timeout=5000)
      projector.wait_for_timeout(1000)
      assert projector.locator("#thermometer").is_hidden()
      assert projector.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


def test_the_pace_buttons_follow_the_deck_language_switch_both_ways(tmp_path):
  """#1906: a pt-BR phone that reads the deck in PT sees the buttons in Portuguese; EN on the deck's switch turns them to
  English at once, and PT turns them back."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Pacing(tmp_path)
  stand.thermometer = True
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phone, errors = follower(browser, playwright, "pt", 390)
      phone.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      phone.locator("#thermometer").wait_for(state="visible", timeout=5000)
      reads = "() => [document.querySelector('#thermometer-slow').textContent, document.querySelector('#thermometer-fast').textContent]"
      assert phone.evaluate(reads) == list(WORDS["pt"])
      for lang in ("en", "pt"):
        phone.locator("#langBtn").click()
        phone.wait_for_function(f"() => document.documentElement.dataset.lang === '{lang}'", timeout=5000)
        assert phone.evaluate(reads) == list(WORDS[lang]), lang
        assert phone.get_attribute("#thermometer", "aria-label") == ("Pace" if lang == "en" else "Ritmo")
      assert errors == [] and phone.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


def test_the_pace_buttons_step_aside_while_a_sheet_is_open(tmp_path):
  """#1907: the question box opens at the bottom, where the pace buttons sit: the buttons hide while it is open, and come
  back when the questions close; never both on screen."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Pacing(tmp_path)
  stand.thermometer = True
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phone, errors = follower(browser, playwright, "en", 340)
      phone.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      phone.locator("#thermometer").wait_for(state="visible", timeout=5000)
      stand.turns["questions_open"] = stand.now().isoformat().replace("+00:00", "Z")
      phone.locator("#ask").wait_for(state="visible", timeout=5000)
      assert phone.locator("#thermometer").is_hidden(), "the question box is open"
      del stand.turns["questions_open"]
      phone.locator("#thermometer").wait_for(state="visible", timeout=5000)
      assert phone.locator("#ask").is_hidden()
      assert errors == [] and phone.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()
