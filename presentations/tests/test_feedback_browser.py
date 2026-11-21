"""The audience's feedback at the end (#1717), end to end in headless Chromium: two phones of different widths on the follow
page of an ended Session rate the talk, one of them twice (its second answer replaces the first), and the speaker's drive
screen shows the count, the average to one decimal and the comments in arrival order in its audience sheet, with no device
id anywhere. The new controls (the phone's five ratings, comment and Send; the sheet's feedback part) are measured in
English and Portuguese at 340, 360, 390 and 412 px: each inside the screen, no text cut, no horizontal scroll, the
ratings at least 44 px, and no CSP violation. The server is a stand-in for the portal and the API (test_questions_browser's
Asking, with the Session ended and the two feedback routes, upserting by device as leagore does); every name and comment
is invented. Skips with no browser."""
import json

import pytest
from test_drive_browser import BASE, LANGS, WIDTHS, chromium, fits, opened
from test_follow_browser import CODE, LISTENER, frame
from test_questions_browser import FOLLOW, Asking, follower

RATE_MEASURE = """() => {
  const shown = (node) => node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden';
  const boxes = [...document.querySelectorAll('#rate, #rate-label, #rate textarea, #rate button, #rate-status, #rate-count')].filter(shown).map((node) => {
    const box = node.getBoundingClientRect();
    return { id: node.id || node.tagName, tag: node.tagName, left: box.left, right: box.right, bottom: box.bottom, height: box.height,
             cut: node.tagName !== 'TEXTAREA' && node.scrollWidth > node.clientWidth + 1 };
  });
  return { width: document.documentElement.clientWidth, height: window.innerHeight, scroll: document.documentElement.scrollWidth, boxes };
}"""
SENT = "() => /Thanks|Obrigad|updated|atualizada/.test(document.querySelector('#rate-status').textContent)"
SHEET = ".questions-sheet .sheet-title, .feedback-summary, .feedback-comment, .questions-sheet .sheet-actions button"


class Rating(Asking):
  """Asking with the Session ended, and the feedback the phones post, one answer per device in its first place."""

  def __init__(self, directory, engine=False):
    super().__init__(directory, engine=engine)
    self.ended = "2026-12-01T17:31:00Z"
    self.rated: dict[str, dict] = {}

  def answer(self, path):
    if path == f"{BASE}/feedback":
      with self.lock:
        rows = list(self.rated.values())
      count = len(rows)
      return self.json({"count": count, "average": round(sum(row["rating"] for row in rows) / count, 1) if count else None,
                        "comments": [{"text": row["comment"], "at": "2026-12-01T17:32:00Z"} for row in rows if row["comment"]]})
    return super().answer(path)

  def posted(self, path, body):
    if path == f"{FOLLOW}/feedback":
      with self.lock:
        created = body["device"] not in self.rated
        self.rated[body["device"]] = {"rating": body["rating"], "comment": body.get("comment", "").strip() or None}
      result = {"result": "created" if created else "configured", "at": "2026-12-01T17:32:00Z"}
      return 201 if created else 200, "application/json", json.dumps(result).encode(), False
    return super().posted(path, body)


def rate(page, rating, comment):
  page.click(f"#rate-{rating}")
  page.fill("#rate-text", comment)
  page.evaluate("document.querySelector('#rate-status').textContent = ''")
  page.click("#rate-send")
  page.wait_for_function(SENT, timeout=5000)


def phone_fits(page):
  found = page.evaluate(RATE_MEASURE)
  assert found["scroll"] <= found["width"], found
  assert found["boxes"], found
  for box in found["boxes"]:
    assert box["left"] >= 0 and box["right"] <= found["width"] + 0.5, (found["width"], box)
    assert box["bottom"] <= found["height"] + 0.5, (found["height"], box)
    assert not box["cut"], (found["width"], box)
    if box["tag"] == "BUTTON":
      assert box["height"] >= 44, box


@pytest.mark.parametrize("lang", LANGS)
def test_two_phones_rate_the_talk_one_twice_and_the_speaker_reads_the_result(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Rating(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      first, first_errors = follower(browser, playwright, lang, 360)
      second, second_errors = follower(browser, playwright, lang, 412)
      for page in (first, second):
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        page.locator("#rate").wait_for(state="visible", timeout=5000)
        assert page.locator("#ask").is_hidden()
      rate(first, 2, "  Too fast  ")
      rate(second, 5, "Great demo")
      rate(first, 4, "Better on reflection")
      assert first.evaluate("document.querySelector('#rate-4').getAttribute('aria-pressed')") == "true"
      assert len(stand.rated) == 2
      assert [row["rating"] for row in stand.rated.values()] == [4, 5]

      speaker = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
      speaker_errors = []
      speaker.on("pageerror", lambda error: speaker_errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      opened(speaker, stand, lang, 390)
      speaker.locator("[data-role=session]").first.click()
      speaker.locator("[data-role=questions]").click()
      summary = speaker.locator("[data-role=feedback-summary]")
      summary.wait_for(state="visible", timeout=7000)
      expected = "2 answers · average 4.5 of 5" if lang == "en" else "2 respostas · média 4,5 de 5"
      said = "document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('[data-role=feedback-summary]').textContent"
      speaker.wait_for_function(f"() => {said} === {json.dumps(expected)}", timeout=7000)
      assert speaker.locator("[data-role=feedback-comment]").all_text_contents() == ["Better on reflection", "Great demo"]
      content = speaker.content() + speaker.evaluate("document.querySelector('nereus-presentations-drive').shadowRoot.innerHTML")
      assert not any(device in content or device[:6] in content for device in stand.rated)
      assert first_errors == second_errors == speaker_errors == []
      assert first.evaluate("window.__csp") == second.evaluate("window.__csp") == speaker.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


@pytest.mark.parametrize("lang", LANGS)
def test_the_ratings_and_the_speaker_s_feedback_fit_every_phone(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  (tmp_path / "buttons").mkdir()
  (tmp_path / "engine").mkdir()
  stand = Rating(tmp_path / "buttons")
  staged = Rating(tmp_path / "engine", engine=True)
  long = "A comment long enough to wrap over the lines of a narrow phone, and then some more words " * 3
  for each in (stand, staged):
    each.rated["3f2a9c1e-7b4d-4e8a-9c2f-1a2b3c4d5e6f"] = {"rating": 4, "comment": long[:280]}
    each.rated["8d7c6b5a-4f3e-4d2c-8b1a-0f9e8d7c6b5a"] = {"rating": 5, "comment": "Short"}
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for width in WIDTHS:
        page, errors = follower(browser, playwright, lang, width)
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        page.locator("#rate").wait_for(state="visible", timeout=5000)
        page.click("#rate-3")
        page.fill("#rate-text", "x" * 300)
        page.click("#rate-send")
        phone_fits(page)
        assert errors == [] and page.evaluate("window.__csp") == []
        page.context.close()
        for screen in (stand, staged):
          speaker = browser.new_context(viewport={"width": width, "height": 844}).new_page()
          speaker.add_init_script(LISTENER)
          opened(speaker, screen, lang, width)
          speaker.locator("[data-role=session]").first.click()
          speaker.locator("[data-role=questions]").click()
          speaker.locator("[data-role=feedback-comment]").first.wait_for(state="visible", timeout=7000)
          fits(speaker, SHEET)
          assert speaker.evaluate("window.__csp") == []
          speaker.context.close()
      browser.close()
  finally:
    stand.close()
    staged.close()


@pytest.mark.parametrize("lang", LANGS)
def test_the_speaker_asks_the_room_to_rate_on_the_last_step_and_a_phone_rates_before_end(tmp_path, lang):
  """#1876: on the last step the speaker's Ask the room to rate opens the rating on the phones while the Session is live;
  a phone rates, and End is still there to press."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Rating(tmp_path)
  stand.ended = None
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      speaker = browser.new_context(viewport={"width": 360, "height": 800}).new_page()
      speaker_errors = []
      speaker.on("pageerror", lambda error: speaker_errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      opened(speaker, stand, lang, 360)
      speaker.locator("[data-role=session]").first.click()
      speaker.locator("[data-role=controls]").wait_for(timeout=5000)
      assert speaker.locator("[data-role=rate]").is_hidden()
      for _ in range(3):
        speaker.locator("[data-role=next]").click()
      rate_button = speaker.locator("[data-role=rate]")
      rate_button.wait_for(state="visible", timeout=2000)
      assert rate_button.inner_text().strip() == ("Ask the room to rate" if lang == "en" else "Pedir avaliação")
      rate_button.click()
      rate_button.wait_for(state="hidden", timeout=2000)
      assert "rating_open" in stand.turns and stand.ended is None
      assert speaker.locator("[data-role=end]").is_visible()

      page, errors = follower(browser, playwright, lang, 360)
      page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      page.locator("#rate").wait_for(state="visible", timeout=5000)
      rate(page, 5, "Had to leave early")
      assert [row["rating"] for row in stand.rated.values()] == [5]
      assert errors == speaker_errors == []
      assert page.evaluate("window.__csp") == speaker.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


@pytest.mark.parametrize("lang", LANGS)
def test_a_phone_puts_the_rating_away_once_sent_and_opens_it_again_to_change_it(tmp_path, lang):
  """#1907: once sent, Done folds the rating to one line of thanks, inside the screen and under the pace buttons' row
  (64 px); a tap on it opens the sheet again, and a second answer replaces the first. At 340 and 412 px."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Rating(tmp_path)
  done = {"en": "Done", "pt": "Pronto"}[lang]
  again = {"en": "Thanks for your rating", "pt": "Obrigado pela avaliação"}[lang]
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for width in (340, 412):
        page, errors = follower(browser, playwright, lang, width)
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        page.locator("#rate").wait_for(state="visible", timeout=5000)
        assert page.locator("#rate-done").is_hidden(), "nothing to put away before an answer"
        rate(page, 4, "")
        assert page.locator("#rate-done").text_content() == done
        phone_fits(page)
        page.click("#rate-done")
        page.locator("#rate-again").wait_for(state="visible", timeout=2000)
        assert page.locator("#rate-again").text_content().startswith(again)
        assert page.locator("#rate-text").is_hidden() and page.locator("#rate-send").is_hidden()
        assert page.evaluate("() => document.querySelector('#rate').getBoundingClientRect().height") <= 64
        phone_fits(page)
        page.click("#rate-again")
        page.locator("#rate-send").wait_for(state="visible", timeout=2000)
        assert page.locator("#rate-again").is_hidden()
        rate(page, 2, "")
        assert [row["rating"] for row in stand.rated.values()][-1] == 2
        assert errors == [] and page.evaluate("window.__csp") == []
        page.close()
      browser.close()
  finally:
    stand.close()


class Moving(Rating):
  """Rating whose stream the phones read again every 300 ms, so they see the speaker's steps, and with only the turns the
  speaker opened (no questions here: their box would take the bottom over the folded rating, #1907)."""

  def answer(self, path):
    if path == FOLLOW:
      return 200, "text/event-stream", b"retry: 300\n\n" + frame("state", self.state()), False
    return super().answer(path)


@pytest.mark.parametrize("lang", LANGS)
def test_the_rating_folds_when_the_speaker_moves_back_and_its_line_opens_it_again(tmp_path, lang):
  """#1912: the speaker asks the room to rate on the last step, then goes back a step; the phone's open rating folds to
  its one line (inside the screen, under 64 px), the slide shows again, and a tap on the line opens the rating while its
  turn lasts. At 340 and 412 px."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Moving(tmp_path)
  stand.ended = None
  later = {"en": "Rate the talk", "pt": "Avalie a palestra"}[lang]
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      speaker = browser.new_context(viewport={"width": 360, "height": 800}).new_page()
      speaker_errors = []
      speaker.on("pageerror", lambda error: speaker_errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      opened(speaker, stand, lang, 360)
      speaker.locator("[data-role=session]").first.click()
      speaker.locator("[data-role=controls]").wait_for(timeout=5000)
      for _ in range(3):
        speaker.locator("[data-role=next]").click()
      speaker.locator("[data-role=rate]").click()
      speaker.locator("[data-role=rate]").wait_for(state="hidden", timeout=2000)
      phones = [follower(browser, playwright, lang, width) for width in (340, 412)]
      for page, _ in phones:
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
        page.locator("#rate-send").wait_for(state="visible", timeout=5000)
      speaker.locator("[data-role=prev]").click()
      for page, errors in phones:
        page.locator("#rate-again").wait_for(state="visible", timeout=5000)
        assert page.locator("#rate-again").text_content().startswith(later)
        assert page.locator("#rate-text").is_hidden() and page.locator("#rate-send").is_hidden()
        assert page.evaluate("() => document.querySelector('#rate').getBoundingClientRect().height") <= 64
        phone_fits(page)
        page.click("#rate-again")
        page.locator("#rate-send").wait_for(state="visible", timeout=2000)
        rate(page, 4, "")
        assert errors == [] and page.evaluate("window.__csp") == []
      assert [row["rating"] for row in stand.rated.values()] == [4, 4]
      assert speaker_errors == [] and speaker.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()
