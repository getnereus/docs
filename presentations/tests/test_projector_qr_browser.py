"""The projector's QR code (#1715), in headless Chromium under the portal's exact policy: on the title slide and at the turn
to the questions, the projector's view (`?projector`) shows the QR code of the follow link and the short code in large type;
the test reads the QR code from a screenshot of the projector's screen (zxing-cpp, a test-only dependency of `make
deck-test`) and opens the follow page with the address it holds. A phone's view never shows it. Checked in English and
Portuguese at 1920x1080 and 1280x720: the QR code is at least min(35vh, 30vw), the card stays inside the screen and covers
no text of the slide (its column moves left while the card shows). On demand (#1859): the speaker's switch Show on the
projector, in the drive screen's Share sheet, shows the card on a middle slide, then takes it away. The stands are
test_follow_browser.py's and test_drive_browser.py's, the drive one passing the posted `sharing` to the follow stream as
leagore and the API do; every name is invented. Skips with no browser."""
import datetime
import io
import os
import pathlib

import pytest
import test_drive_browser
from test_follow_browser import CODE, LISTENER, Stand, chromium

WORDS = {"en-US": "Follow on your phone", "pt-BR": "Acompanhe pelo celular"}
SCREENS = ({"width": 1920, "height": 1080}, {"width": 1280, "height": 720})
SHARE = "#share"
# The card's box against every box of text on the slide on screen: none may cross it.
CROSSED = """() => {
  const card = document.querySelector('#share').getBoundingClientRect();
  const texts = [...document.querySelectorAll('.slide.on h1, .slide.on h2, .slide.on h3, .slide.on p, .slide.on li')]
    .map((node) => node.getBoundingClientRect()).filter((box) => box.width > 0 && box.height > 0);
  return texts.filter((box) => box.left < card.right && box.right > card.left && box.top < card.bottom && box.bottom > card.top).length;
}"""
# The QR code is at least min(35vh, 30vw): scanned from the back of a room.
LARGE = """() => { const box = document.querySelector('#share-qr').getBoundingClientRect();
  return box.height >= Math.min(0.35 * innerHeight, 0.30 * innerWidth) - 1; }"""
INSIDE = """() => { const box = document.querySelector('#share').getBoundingClientRect();
  return box.left >= 0 && box.top >= 0 && box.right <= innerWidth && box.bottom <= innerHeight; }"""


def decoded(png: bytes) -> list[str]:
  import zxingcpp
  from PIL import Image
  return [found.text for found in zxingcpp.read_barcodes(Image.open(io.BytesIO(png)))]


def page_of(browser, stand, locale, viewport, search, errors):
  context = browser.new_context(viewport=viewport, locale=locale)
  page = context.new_page()
  page.on("pageerror", lambda error: errors.append(str(error)))
  page.add_init_script(LISTENER)
  page.goto(f"{stand.url}/p/{CODE}{search}", wait_until="load")
  page.wait_for_function("() => window.__step !== null", timeout=5000)
  return page


def test_the_projector_shows_the_follow_qr_on_the_title_slide_and_a_scan_opens_the_follow_page(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  shots = os.environ.get("NEREUS_SCREENSHOTS")
  errors: list[str] = []
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for locale, words in WORDS.items():
        for viewport in SCREENS:
          stand.go(0)
          projector = page_of(browser, stand, locale, viewport, "?projector", errors)
          projector.locator(SHARE).wait_for(state="visible", timeout=3000)
          assert projector.locator("#share-code").inner_text() == CODE
          assert projector.locator("#share-text").inner_text() == words
          assert projector.evaluate(INSIDE), (locale, viewport)
          assert projector.evaluate(LARGE), (locale, viewport)
          assert projector.evaluate(CROSSED) == 0, (locale, viewport)
          # Read from the projector's screen, as a phone in the room does.
          found = decoded(projector.screenshot())
          assert found == [f"{stand.url}/p/{CODE}"], found
          if shots:
            pathlib.Path(shots).mkdir(parents=True, exist_ok=True)
            projector.screenshot(path=f"{shots}/projector-qr-{locale}-{viewport['width']}.png")
          # The scan opens the follow page: a phone's view, on the same step, with no QR code of its own.
          phone = page_of(browser, stand, locale, {"width": 390, "height": 844}, "", errors)
          phone.goto(found[0], wait_until="load")
          phone.wait_for_function("() => document.documentElement.dataset.mode === 'follow' && window.__step === 0", timeout=5000)
          assert not phone.locator(SHARE).is_visible()
          # The first step takes the card away from the wall.
          stand.go(1)
          projector.wait_for_function("() => window.__step === 1", timeout=3000)
          projector.locator(SHARE).wait_for(state="hidden", timeout=3000)
          assert projector.evaluate("window.__csp") == [] and phone.evaluate("window.__csp") == []
          projector.context.close()
          phone.context.close()
      browser.close()
  finally:
    stand.close()
  assert errors == []


def test_the_projector_shows_the_follow_qr_again_at_the_turn_to_the_questions(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  now = datetime.datetime.now(datetime.timezone.utc)
  # A talk with most of its hour left whose questions the speaker opened a minute ago (#1876): the questions' turn.
  stand.extra = {"talk": 3600, "questions": 600, "started": (now - datetime.timedelta(seconds=120)).isoformat(),
                 "questions_open": (now - datetime.timedelta(seconds=60)).isoformat(), "now": now.isoformat()}
  stand.go(2)
  errors: list[str] = []
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      projector = page_of(browser, stand, "en-US", SCREENS[0], "?projector", errors)
      phone = page_of(browser, stand, "en-US", {"width": 390, "height": 844}, "", errors)
      for page in (projector, phone):
        page.wait_for_function("() => window.__step === 2 && document.body.classList.contains('questions')", timeout=5000)
      projector.locator(SHARE).wait_for(state="visible", timeout=3000)
      assert decoded(projector.screenshot()) == [f"{stand.url}/p/{CODE}"]
      assert projector.evaluate(INSIDE) and projector.evaluate(LARGE) and projector.evaluate(CROSSED) == 0
      shots = os.environ.get("NEREUS_SCREENSHOTS")
      if shots:
        pathlib.Path(shots).mkdir(parents=True, exist_ok=True)
        projector.screenshot(path=f"{shots}/projector-qr-questions-en-US-1920.png")
      assert not phone.locator(SHARE).is_visible()
      browser.close()
  finally:
    stand.close()
  assert errors == []


class Driving(test_drive_browser.Stand):
  """The drive screen's stand, whose posted `sharing` reaches the follow stand's stream, as leagore's state reaches the
  followers through the API (#1859)."""

  def __init__(self, directory, follow):
    super().__init__(directory)
    self.follow = follow
    self.sharing = False

  def posted(self, path, body):
    if path != f"{test_drive_browser.BASE}/sharing":
      return super().posted(path, body)
    with self.lock:
      self.sharing = body["on"]
    self.follow.extra["sharing"] = body["on"]
    self.follow.go(self.follow.step)
    return self.json({**self.state(), "sharing": self.sharing})


def test_the_speaker_shows_the_follow_qr_on_the_projector_on_demand_from_the_drive_screen(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  (tmp_path / "follow").mkdir()
  (tmp_path / "drive").mkdir()
  follow = Stand(tmp_path / "follow")
  drive = Driving(tmp_path / "drive", follow)
  follow.go(2)
  errors: list[str] = []
  shots = os.environ.get("NEREUS_SCREENSHOTS")
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      projector = page_of(browser, follow, "pt-BR", SCREENS[0], "?projector", errors)
      projector.wait_for_function("() => window.__step === 2", timeout=5000)
      assert not projector.locator(SHARE).is_visible()
      speaker, speaker_errors = test_drive_browser.phone(playwright, browser, "pt")
      test_drive_browser.opened(speaker, drive, "pt", 340)
      speaker.locator("[data-role=session]").first.click()
      speaker.locator("[data-role=share]").click()
      toggle = speaker.locator("[data-role=share-projector]")
      assert toggle.get_attribute("aria-checked") == "false"
      test_drive_browser.fits(speaker, ".switch-row, .switch-label, .switch-help, .sheet-actions button")
      toggle.click()
      projector.locator(SHARE).wait_for(state="visible", timeout=3000)
      assert speaker.locator("[data-role=share-projector]").get_attribute("aria-checked") == "true"
      assert projector.evaluate("window.__step") == 2
      assert decoded(projector.screenshot()) == [f"{follow.url}/p/{CODE}"]
      assert projector.evaluate(INSIDE) and projector.evaluate(LARGE) and projector.evaluate(CROSSED) == 0
      if shots:
        pathlib.Path(shots).mkdir(parents=True, exist_ok=True)
        speaker.wait_for_timeout(300)
        speaker.screenshot(path=f"{shots}/drive-share-projector-pt-340.png")
        projector.screenshot(path=f"{shots}/projector-qr-on-demand-pt-BR-1920.png")
      toggle.click()
      projector.locator(SHARE).wait_for(state="hidden", timeout=3000)
      assert toggle.get_attribute("aria-checked") == "false"
      assert projector.evaluate("window.__csp") == [] and speaker.evaluate("window.__csp") == []
      assert speaker_errors == []
      browser.close()
  finally:
    drive.close()
    follow.close()
  assert errors == []
