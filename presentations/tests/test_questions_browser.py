"""The audience's question (#1716), end to end in headless Chromium: a phone on the follow page, at the questions' turn,
sends a question from its text box (the questions opened by the speaker, with most of the talk's time left, #1876), and the speaker's drive screen shows it in its Questions sheet, with the device's
six-character label only. The new controls (the phone's box, the speaker's Questions action and its sheet) are measured
in English and Portuguese at 340, 360, 390 and 412 px: each inside the screen, no text cut, no horizontal scroll, and no
CSP violation. The server is a stand-in for the portal and the API (test_drive_browser.Stand with the follow page, a
stream in the questions' phase and the two questions routes); every name and question is invented. Skips with no
browser."""
import datetime
import json

import pytest
from test_drive_browser import BASE, LANGS, WIDTHS, Stand, chromium, fits, opened
from test_follow_browser import CODE, LISTENER, frame, portal

FOLLOW = f"/v1/presentations/follow/{CODE}"
ASKED = "Will the demo work offline?"
PHONE_MEASURE = """() => {
  const shown = (node) => node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden';
  const boxes = [...document.querySelectorAll('#ask, #ask label, #ask textarea, #ask button, #ask-status, #ask-count')].filter(shown).map((node) => {
    const box = node.getBoundingClientRect();
    return { id: node.id || node.tagName, left: box.left, right: box.right, bottom: box.bottom, height: box.height,
             cut: node.tagName !== 'TEXTAREA' && node.scrollWidth > node.clientWidth + 1 };
  });
  return { width: document.documentElement.clientWidth, height: window.innerHeight, scroll: document.documentElement.scrollWidth, boxes };
}"""


class Asking(Stand):
  """The drive's stand, plus the follow page whose stream has the questions open (#1876), and the questions the phones post."""

  def __init__(self, directory, engine=False):
    super().__init__(directory, engine=engine)
    self.asked: list[dict] = []
    self.devices: list[str] = []

  def answer(self, path):
    if path == f"/p/{CODE}":
      return 200, "text/html; charset=utf-8", (portal.STATIC / "follow.html").read_bytes(), False
    if path == f"{FOLLOW}/deck":
      return 200, "text/html; charset=utf-8", self.deck, False
    if path == FOLLOW:
      # One state and the stream closes; the page keeps it, and its retry is long enough not to matter here. The talk has
      # most of its hour left and the speaker opened the questions a minute ago (#1876): the clock opens nothing.
      now = datetime.datetime.now(datetime.timezone.utc)
      state = {**self.state(), "talk": 3600, "questions": 600, "started": (now - datetime.timedelta(minutes=2)).isoformat(),
               "questions_open": (now - datetime.timedelta(minutes=1)).isoformat(), "now": now.isoformat()}
      return 200, "text/event-stream", b"retry: 60000\n\n" + frame("state", state), False
    if path == f"{BASE}/questions":
      with self.lock:
        return self.json({"questions": list(self.asked)})
    return super().answer(path)

  def posted(self, path, body):
    if path == f"{FOLLOW}/questions":
      with self.lock:
        self.devices.append(body["device"])
        self.asked.append({"device": body["device"][:6], "text": body["text"].strip(), "at": "2026-12-01T17:31:00Z"})
      return 201, "application/json", json.dumps({"result": "created", "at": "2026-12-01T17:31:00Z"}).encode(), False
    return super().posted(path, body)


def follower(browser, playwright, lang, width):
  device = {key: value for key, value in playwright.devices["iPhone 13"].items() if key != "default_browser_type"}
  device["viewport"] = {"width": width, "height": 844}
  page = browser.new_context(**device, locale="pt-BR" if lang == "pt" else "en-US").new_page()
  errors = []
  page.on("pageerror", lambda error: errors.append(str(error)))
  page.add_init_script(LISTENER)
  if lang == "pt":
    # The deck opens in English (#1906: the page's words follow it): a Portuguese reader has picked PT on its switch before.
    page.add_init_script("localStorage.setItem('deck.lang', 'pt')")
  return page, errors


def phone_fits(page):
  found = page.evaluate(PHONE_MEASURE)
  assert found["scroll"] <= found["width"], found
  assert found["boxes"], found
  for box in found["boxes"]:
    assert box["left"] >= 0 and box["right"] <= found["width"] + 0.5, (found["width"], box)
    assert box["bottom"] <= found["height"] + 0.5, (found["height"], box)
    assert not box["cut"], (found["width"], box)
    if box["id"] == "BUTTON":
      assert box["height"] >= 44, box


SPEAKER = ".questions-action, .badge, .share, .full, .back, .stage-name"
SHEET = ".questions-sheet .sheet-title, .question-device, .question-text, .questions-sheet .sheet-actions button"


@pytest.mark.parametrize("lang", LANGS)
def test_a_question_sent_from_a_phone_shows_on_the_speaker_s_screen(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Asking(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phone, phone_errors = follower(browser, playwright, lang, 390)
      phone.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      phone.locator("#ask").wait_for(state="visible", timeout=5000)
      phone.fill("#ask-text", f"  {ASKED}  ")
      phone.click("#ask-send")
      phone.wait_for_function("() => document.querySelector('#ask-text').value === ''", timeout=5000)
      assert [each["text"] for each in stand.asked] == [ASKED]

      speaker = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
      speaker_errors = []
      speaker.on("pageerror", lambda error: speaker_errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      opened(speaker, stand, lang, 390)
      speaker.locator("[data-role=session]").first.click()
      action = speaker.locator("[data-role=questions]")
      action.wait_for(state="visible", timeout=5000)
      speaker.locator("[data-role=questions-count]").filter(has_text="1").wait_for(timeout=7000)
      action.click()
      shown = speaker.locator("[data-role=question-text]")
      shown.wait_for(state="visible", timeout=5000)
      assert shown.all_text_contents() == [ASKED]
      label = speaker.locator("[data-role=question-device]").all_text_contents()
      assert label == [f"#{stand.devices[0][:6]}"]
      assert stand.devices[0] not in speaker.content()
      assert phone_errors == speaker_errors == []
      assert phone.evaluate("window.__csp") == speaker.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


@pytest.mark.parametrize("lang", LANGS)
def test_the_question_box_and_the_speaker_s_questions_fit_every_phone(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  (tmp_path / "buttons").mkdir()
  (tmp_path / "engine").mkdir()
  stand = Asking(tmp_path / "buttons")
  staged = Asking(tmp_path / "engine", engine=True)
  stand.asked.append({"device": "3f2a9c", "text": "A question long enough to wrap over the lines of a narrow phone " * 3,
                      "at": "2026-12-01T17:31:00Z"})
  staged.asked.extend(stand.asked)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for width in WIDTHS:
        phone, errors = follower(browser, playwright, lang, width)
        phone.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        phone.locator("#ask").wait_for(state="visible", timeout=5000)
        phone.fill("#ask-text", "x" * 300)
        phone_fits(phone)
        assert errors == [] and phone.evaluate("window.__csp") == []
        phone.context.close()
        for screen in (stand, staged):
          page = browser.new_context(viewport={"width": width, "height": 844}).new_page()
          page.add_init_script(LISTENER)
          opened(page, screen, lang, width)
          page.locator("[data-role=session]").first.click()
          page.locator("[data-role=questions-count]").filter(has_text="1").wait_for(timeout=7000)
          fits(page, SPEAKER)
          page.locator("[data-role=questions]").click()
          page.locator("[data-role=question-text]").wait_for(state="visible", timeout=5000)
          fits(page, SHEET)
          assert page.evaluate("window.__csp") == []
          page.context.close()
      browser.close()
  finally:
    stand.close()
    staged.close()
