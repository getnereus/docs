"""Question slides (#1722) and the room's turn in full screen (#1882), end to end in headless Chromium.

A poll: the speaker's drive screen opens a slide's poll (never by itself), two phones of 340 and 412 px answer it on the
slide itself (one changes its answer, which replaces the first). Its seconds close nothing (#1917): past them the phones
and the projector say Open, the drive screen counts the time over, and only the speaker's Close question shows the
projector, the phones and the drive screen each option's bar and votes; Reopen question takes answers again. The poll's
reference is the shortest the engine takes (5 s). The phones' screens never scroll sideways, and no page breaks the
portal's policy.

A scale poll's result on the drive screen with the engine (#1918): each value and, apart, its votes, and the live line on
one line, at 340 and 412 px in both languages.

The turn: the engine's bottom bar shows the host's offer (Ask the room to rate, Pedir avaliação) next to End on a phone
of 340 to 412 px, every control inside the screen, and a press or the key O tells the host.

The server is a stand-in for the portal and the API (test_questions_browser's Asking, its stream sent again every few
hundred milliseconds, with the poll's routes keeping one answer per device as leagore does); every name is invented.
Skips with no browser."""
import datetime
import json
import re
import subprocess
import sys

import pytest
import yaml
from test_drive_browser import BASE, LANGS, WIDTHS, chromium, fits, opened
from test_follow_browser import CODE, DECK, HERE, LISTENER, ro
from test_questions_browser import FOLLOW, Asking, follower
from test_steps import GOTO, RECORD, render
from test_portal_mode import portal, serve

SECONDS = 5
CHOICES = {"en": ["Reefs", "Nereids", "Mandates"], "pt": ["Os reefs", "Os Nereids", "Os Mandates"]}
POLL = {"name": "pick", "act": "scene", "message": "Pick the next part", "pt": {"message": "Escolha a próxima parte"},
        "poll": {"kind": "choice", "question": "Which part comes next?", "choices": CHOICES["en"], "seconds": SECONDS,
                 "pt": {"question": "Qual parte vem agora?", "choices": CHOICES["pt"]}}}


def now():
  return datetime.datetime.now(datetime.timezone.utc)


def stamp(moment):
  return moment.isoformat().replace("+00:00", "Z")


class Polling(Asking):
  """Asking with a deck whose last slide but one asks the room (POLL), the Session on that slide, its stream sent again
  every 300 ms, and the poll's routes as leagore keeps them (#1917): the speaker's open (again once closed), close and
  list, the phones' answers while it is open."""

  def __init__(self, directory, engine=False, slide=POLL):
    super().__init__(directory, engine=engine)
    outline = yaml.safe_load(DECK.read_text())
    outline["outlineVersion"] = 2
    outline["slides"].insert(-1, slide)
    self.definition = slide["poll"]
    source = directory / "polled.yaml"
    source.write_text(yaml.safe_dump(outline, allow_unicode=True))
    subprocess.run([sys.executable, str(HERE / "render-outline"), str(source), "--split", "--output", str(directory / "polled.html")],
                   check=True, capture_output=True)
    self.deck = (directory / "polled.html").read_bytes()
    main = self.deck.decode().split('<div data-deck="refs">', 1)[0]
    names = [name for name, units in re.findall(r"<section class='slide[^']*' id='([^']*)' data-units='(\d+)'", main) for _ in range(int(units) + 1)]
    assert len(names) == ro.deck_steps(self.deck.decode())
    self.slides = [{"name": name, "title": name, "message": ""} for name in names]
    self.step = names.index("pick")
    self.opened = None
    self.closed = None
    self.answers: dict[str, int] = {}

  def poll(self):
    """The state's poll, as leagore gives it: the count, then the result once the speaker closed it."""
    if self.opened is None:
      return None
    closes = self.opened + datetime.timedelta(seconds=self.definition["seconds"])
    kind = self.definition["kind"]
    with self.lock:
      if kind == "scale":
        low, high = self.definition["scale"]["min"], self.definition["scale"]["max"]
        votes = list(self.answers.values())
        counts = [votes.count(n) for n in range(low, high + 1)]
        result = {"counts": counts, "average": sum(votes) / len(votes) if votes else None}
      else:
        result = {"counts": [list(self.answers.values()).count(n) for n in range(len(CHOICES["en"]))]}
      answers = len(self.answers)
    closed = self.closed
    return {"name": "pick", "kind": kind, "opened": stamp(self.opened), "closes": stamp(closes),
            "closed": stamp(closed) if closed else None, "answers": answers, "result": result if closed else None}

  def state(self):
    found = super().state()
    poll = self.poll()
    return {**found, "poll": poll} if poll else found

  def answer(self, path):
    if path == FOLLOW:
      state = {**self.state(), "now": stamp(now())}
      return 200, "text/event-stream", b"retry: 300\n\n" + f"event: state\ndata: {json.dumps(state)}\n\n".encode(), False
    if path == f"{BASE}/polls":
      given = self.definition
      scale = given.get("scale") or {}
      definition = {"question": given["question"], "seconds": given["seconds"], "pt": given["pt"], "choices": given.get("choices"),
                    "min": scale.get("min"), "max": scale.get("max"), "texts": None}
      unopened = {"name": "pick", "kind": given["kind"], "opened": None, "closes": None, "closed": None, "answers": 0, "result": None}
      return self.json({"polls": [{**(self.poll() or unopened), **definition}]})
    return super().answer(path)

  def posted(self, path, body):
    if path == f"{BASE}/polls/pick/open":
      if self.opened is not None and self.closed is None:
        return 409, "application/json", b'{"error": {"code": "Refused", "message": "the poll is open"}}', False
      self.opened, self.closed = now(), None
      return self.json(self.state())
    if path == f"{BASE}/polls/pick/close":
      if self.opened is None or self.closed is not None:
        return 409, "application/json", b'{"error": {"code": "Refused", "message": "the poll is not open"}}', False
      self.closed = now()
      return self.json(self.state())
    if path == f"{FOLLOW}/polls/pick/answers":
      if self.opened is None or self.closed is not None:
        return 409, "application/json", b'{"error": {"code": "Refused", "message": "the poll is closed"}}', False
      with self.lock:
        created = body["device"] not in self.answers
        self.answers[body["device"]] = body["answer"]
      return (201 if created else 200), "application/json", json.dumps({"created": created, "at": stamp(now())}).encode(), False
    return super().posted(path, body)


# The poll's places on a page: the visible options' votes, the clock and the count.
DRAWN = """() => {
  const poll = document.querySelector('.poll[data-poll="pick"]');
  const shown = (node) => node.getClientRects().length > 0;
  return { votes: [...poll.querySelectorAll('li[data-option]')].filter(shown).map((li) => li.querySelector('[data-poll-votes]').textContent),
           clock: poll.querySelector('[data-poll-clock]').textContent, count: poll.querySelector('[data-poll-count]').textContent,
           bars: [...poll.querySelectorAll('li[data-option]')].filter(shown).map((li) => {
             const bar = li.querySelector('[data-poll-bar]');
             return [bar.dataset.w, Math.round(100 * bar.getBoundingClientRect().width / li.getBoundingClientRect().width)];
           }) };
}"""
FITS = """() => {
  const width = document.documentElement.clientWidth;
  const shown = (node) => node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden';
  const out = [...document.querySelectorAll('.poll li[data-option], .poll [data-poll-live], #poll, #poll-status')].filter(shown)
    .map((node) => node.getBoundingClientRect()).filter((box) => box.left < -0.5 || box.right > width + 0.5);
  return { width, scroll: document.documentElement.scrollWidth, out: out.length };
}"""


def tap(page, option):
  page.locator(f'.poll[data-poll="pick"].poll-answering li[data-option="{option}"]:visible').click()
  page.wait_for_function("() => /sent|enviada/i.test(document.querySelector('#poll-status').textContent)", timeout=5000)
  page.evaluate("document.querySelector('#poll-status').textContent = ''")


@pytest.mark.parametrize("lang", LANGS)
def test_two_phones_answer_a_poll_the_speaker_opened_and_the_projector_shows_the_result(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Polling(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      phones = [follower(browser, playwright, lang, width) for width in (340, 412)]
      projector = browser.new_context(viewport={"width": 1280, "height": 720}, locale="pt-BR" if lang == "pt" else "en-US").new_page()
      projector.add_init_script(LISTENER)
      if lang == "pt":
        # The deck opens in English, and the poll's words follow it (#1906): the projector was switched to PT before.
        projector.add_init_script("localStorage.setItem('deck.lang', 'pt')")
      for page, _ in phones:
        page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      projector.goto(f"{stand.url}/p/{CODE}?projector", wait_until="load")
      for page in [page for page, _ in phones] + [projector]:
        page.locator('.poll[data-poll="pick"]').first.wait_for(state="visible", timeout=7000)
      # Nothing opens by itself: the slide shows the question, no phone can answer.
      assert phones[0][0].locator(".poll.poll-answering").count() == 0

      speaker = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
      speaker_errors = []
      speaker.on("pageerror", lambda error: speaker_errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      opened(speaker, stand, lang, 390)
      speaker.locator("[data-role=session]").first.click()
      open_poll = speaker.locator("[data-role=open-poll]")
      open_poll.wait_for(state="visible", timeout=7000)
      assert open_poll.text_content() == ("Open question" if lang == "en" else "Abrir pergunta")
      open_poll.click()
      speaker.locator("[data-role=poll]").wait_for(state="visible", timeout=5000)
      assert open_poll.is_hidden(), "an open poll opens no more"

      for page, _ in phones:
        page.locator('.poll[data-poll="pick"].poll-answering').first.wait_for(timeout=5000)
      tap(phones[0][0], 0)
      tap(phones[1][0], 1)
      tap(phones[0][0], 2)
      assert sorted(stand.answers.values()) == [1, 2], "the second tap replaced the first"
      for page, _ in phones:
        found = page.evaluate(FITS)
        assert found["scroll"] <= found["width"] and found["out"] == 0, found

      # Past its seconds it stays open (#1917): the room reads Open, never a negative clock; the speaker the time over.
      still = "Open" if lang == "en" else "Aberta"
      head = "document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('[data-role=poll-head]')"
      speaker.wait_for_function(f"() => {head}.textContent.startsWith('+00:0') && {head}.classList.contains('over')", timeout=SECONDS * 1000 + 5000)
      for page in [page for page, _ in phones] + [projector]:
        page.wait_for_function(f"() => document.querySelector('.poll[data-poll=\"pick\"] [data-poll-clock]').textContent === {json.dumps(still)}", timeout=5000)
        assert page.evaluate(DRAWN)["votes"] == ["", "", ""]
      assert phones[0][0].locator('.poll[data-poll="pick"].poll-answering').count() >= 1, "past its seconds the phones still answer"
      close_poll = speaker.locator("[data-role=close-poll]")
      assert close_poll.text_content() == ("Close question" if lang == "en" else "Fechar pergunta")
      close_poll.click()

      closed = "Closed" if lang == "en" else "Encerrada"
      count = "2 answers" if lang == "en" else "2 respostas"
      for page in [page for page, _ in phones] + [projector]:
        page.wait_for_function("() => document.querySelector('.poll[data-poll=\"pick\"] [data-poll-votes]').textContent !== ''", timeout=5000)
        drawn = page.evaluate(DRAWN)
        assert drawn["votes"] == ["0", "1", "1"], drawn
        assert [w for w, _ in drawn["bars"]] == ["0", "100", "100"], drawn
        assert [abs(share - int(w)) <= 2 for w, share in drawn["bars"]] == [True] * 3, drawn
        assert drawn["clock"] == closed and drawn["count"] == count, drawn
        assert page.locator(".poll.poll-answering").count() == 0
      speaker.wait_for_function(f"() => {head}.textContent.startsWith({json.dumps(closed)})", timeout=5000)
      speaker.locator("[data-role=poll-option]").first.wait_for(timeout=5000)
      rows = speaker.locator("[data-role=poll-option]").all_text_contents()
      assert rows == [f"{chr(65 + n)} {choice}{votes}" for n, (choice, votes) in enumerate(zip(CHOICES[lang], "011"))], rows
      assert open_poll.is_hidden(), "Open question is for a poll never opened"
      reopen = speaker.locator("[data-role=reopen-poll]")
      assert reopen.text_content() == ("Reopen question" if lang == "en" else "Reabrir pergunta")
      for width in (340, 412):
        speaker.set_viewport_size({"width": width, "height": 844})
        assert len(fits(speaker, ".poll-panel, .poll-head, .poll-option, .poll-label, .poll-votes, .close-poll, .controls button")) >= 5

      # Reopen question (#1917): the phones answer again, the answers already in stay, and the next close counts them.
      reopen.click()
      phones[1][0].locator('.poll[data-poll="pick"].poll-answering').first.wait_for(timeout=5000)
      tap(phones[1][0], 2)
      assert sorted(stand.answers.values()) == [2, 2], "the device's answer changed, the other stayed"
      speaker.locator("[data-role=close-poll]").click()
      projector.wait_for_function("() => document.querySelector('.poll[data-poll=\"pick\"] [data-poll-votes]').textContent !== ''", timeout=5000)
      assert projector.evaluate(DRAWN)["votes"] == ["0", "0", "2"]

      assert [errors for _, errors in phones] == [[], []] and speaker_errors == []
      for page in [page for page, _ in phones] + [projector, speaker]:
        assert page.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


class TextPolling(Polling):
  """Polling with the poll a text one for a minute (#1907): long enough to leave its slide and come back while it is open."""

  def poll(self):
    if self.opened is None:
      return None
    closes = self.opened + datetime.timedelta(seconds=60)
    return {"name": "pick", "kind": "text", "opened": stamp(self.opened), "closes": stamp(closes), "closed": None, "answers": len(self.answers), "result": None}


# A scale poll (#1918): five values, each answered by some of the room, the speaker's drive screen with the engine.
SCALE = {"name": "pick", "act": "scene", "message": "Rate it", "pt": {"message": "Avalie"},
         "poll": {"kind": "scale", "question": "How sure are you?", "scale": {"min": 1, "max": 5}, "seconds": SECONDS,
                  "pt": {"question": "Quanta certeza você tem?"}}}
# The scale's places in the engine's frame: each value's box and its votes', and the live line's outputs.
SCALED = """() => {
  const poll = [...document.querySelectorAll('.poll[data-poll="pick"]')].find((node) => node.getClientRects().length > 0);
  const box = (node) => { const found = node.getBoundingClientRect(); return { left: found.left, right: found.right, top: found.top, bottom: found.bottom }; };
  const options = [...poll.querySelectorAll('li[data-option]')].filter((li) => li.getClientRects().length > 0).map((li) => ({ value: box(li.querySelector('b')), votes: box(li.querySelector('[data-poll-votes]')),
    text: li.querySelector('[data-poll-votes]').textContent, li: box(li) }));
  const live = poll.querySelector('[data-poll-live]');
  const outs = [...live.querySelectorAll('output')].map((node) => ({ ...box(node), text: node.textContent, lines: Math.round(node.getBoundingClientRect().height / parseFloat(getComputedStyle(node).lineHeight || '20')) }));
  return { options, outs, width: document.documentElement.clientWidth };
}"""


@pytest.mark.parametrize("lang", LANGS)
def test_a_scale_poll_s_result_on_the_drive_screen_shows_each_value_apart_from_its_votes_on_one_line(tmp_path, lang):
  """#1918: in the engine's frame of the drive screen, a closed scale poll shows each value and, apart (under it), its
  votes, never glued as one number ("41"), and the live line (Closed, the count, the average) on one line, at 340 and
  412 px, in both languages."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = Polling(tmp_path, engine=True, slide=SCALE)
  stand.opened = now() - datetime.timedelta(seconds=20)
  stand.closed = now()
  stand.answers = {"a": 4, "b": 4, "c": 5, "d": 1}
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      speaker = browser.new_context(viewport={"width": 412, "height": 844}).new_page()
      errors = []
      speaker.on("pageerror", lambda error: errors.append(str(error)))
      speaker.add_init_script(LISTENER)
      if lang == "pt":
        speaker.add_init_script("localStorage.setItem('deck.lang', 'pt')")
      for width in (340, 412):
        opened(speaker, stand, lang, width)
        speaker.locator("[data-role=session]").first.click()
        frame = speaker.frame_locator("iframe")
        frame.locator('.slide.on .poll[data-poll="pick"] [data-poll-votes]:not(:empty):visible').first.wait_for(timeout=10000)
        engine = next(each for each in speaker.frames if each.url.endswith("present.html") or "present.html" in each.url)
        found = engine.evaluate(SCALED)
        assert [each["text"] for each in found["options"]] == ["1", "0", "0", "2", "1"], found
        for each in found["options"]:
          value, votes, li = each["value"], each["votes"], each["li"]
          assert votes["top"] >= value["bottom"] - 0.5, ("the votes sit under the value, apart", width, each)
          assert li["left"] - 0.5 <= votes["left"] and votes["right"] <= li["right"] + 0.5, (width, each)
        tops = {round(out["top"]) for out in found["outs"]}
        assert len(tops) == 1 and all(out["lines"] == 1 for out in found["outs"]), ("the live line on one line", width, found["outs"])
        closed = "Closed" if lang == "en" else "Encerrada"
        assert found["outs"][0]["text"] == closed and ("4 answers" if lang == "en" else "4 respostas") in found["outs"][1]["text"], found["outs"]
        assert all(out["right"] <= found["width"] + 0.5 for out in found["outs"]), found
        assert len(fits(speaker, ".poll-panel, .poll-head, .poll-option, .poll-label, .poll-votes, .close-poll")) >= 3
      assert errors == [] and speaker.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


@pytest.mark.parametrize("lang", LANGS)
def test_an_open_text_poll_s_box_goes_with_its_slide_and_comes_back_with_it(tmp_path, lang):
  """#1907: a phone answers an open text poll, the speaker moves on: the box goes at once, though the poll is still open;
  back on its slide, the box is there again. The answer sent still counts."""
  sync_api = pytest.importorskip("playwright.sync_api")
  stand = TextPolling(tmp_path)
  stand.opened = now()
  polled = stand.step
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      page, errors = follower(browser, playwright, lang, 340)
      page.goto(f"{stand.url}/p/{CODE}", wait_until="load")
      page.locator("#poll-text").wait_for(state="visible", timeout=7000)
      page.fill("#poll-text", "fast and safe")
      page.click("#poll-send")
      page.wait_for_function("() => /sent|enviada/i.test(document.querySelector('#poll-status').textContent)", timeout=5000)
      stand.step = polled + 1
      page.locator("#poll").wait_for(state="hidden", timeout=5000)
      stand.step = polled
      page.locator("#poll").wait_for(state="visible", timeout=5000)
      assert list(stand.answers.values()) == ["fast and safe"]
      assert errors == [] and page.evaluate("window.__csp") == []
      browser.close()
  finally:
    stand.close()


TURN = {"en": "Ask the room to rate", "pt": "Pedir avaliação"}
BAR = """() => {
  const width = document.documentElement.clientWidth;
  const shown = [...document.querySelectorAll('nav.bar > *')].filter((node) => node.getClientRects().length > 0);
  const boxes = shown.map((node) => { const box = node.getBoundingClientRect(); return { id: node.id || node.className, left: box.left, right: box.right, height: box.height }; });
  return { width, scroll: document.documentElement.scrollWidth, boxes };
}"""


@pytest.mark.parametrize("lang", LANGS)
def test_the_room_s_turn_sits_next_to_end_on_a_phone_and_its_press_or_the_key_o_tells_the_host(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  total = render(tmp_path, "presentations-reef", mode="drive")
  server = serve(tmp_path, portal.csp("https://auth.example.com"))
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for width in WIDTHS:
        page = browser.new_page(viewport={"width": width, "height": 760})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.add_init_script("try { localStorage.setItem('deck.motion', 'off'); } catch (e) {}" + RECORD + LISTENER)
        page.goto(f"http://127.0.0.1:{server.server_address[1]}/presentations-reef.html", wait_until="load")
        assert page.evaluate(GOTO, total - 1) == total - 1
        assert page.locator("#turnBtn").is_hidden()
        page.evaluate("""label => {
          window.__turns = [];
          document.addEventListener('nereus-turn-press', (e) => window.__turns.push(e.detail.part));
          document.dispatchEvent(new CustomEvent('nereus-ending', {detail: {show: true, label: 'End'}}));
          document.dispatchEvent(new CustomEvent('nereus-turn', {detail: {show: true, label, part: 'rating'}}));
        }""", TURN[lang])
        button = page.locator("#turnBtn")
        assert button.is_visible() and page.locator("#endBtn").is_visible()
        assert [button.text_content(), button.get_attribute("aria-label")] == ["★", TURN[lang]]
        bar = page.evaluate(BAR)
        assert bar["scroll"] <= bar["width"], bar
        for box in bar["boxes"]:
          assert box["left"] >= -0.5 and box["right"] <= bar["width"] + 0.5, (width, box)
        button.click()
        page.keyboard.press("o")
        assert page.evaluate("window.__turns") == ["rating", "rating"]
        page.evaluate("() => document.dispatchEvent(new CustomEvent('nereus-turn', {detail: {show: false, label: '', part: 'rating'}}))")
        assert button.is_hidden()
        page.keyboard.press("o")
        assert page.evaluate("window.__turns") == ["rating", "rating"], "no key O with nothing on offer"
        assert errors == [] and page.evaluate("window.__csp") == []
        page.close()
      browser.close()
  finally:
    server.shutdown()
