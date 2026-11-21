"""The steps of a deck (#1760): the renderer counts them from the outline (`data-units`), the engine walks them in headless
Chromium, and the two agree. A step forward with no motion is exactly one step; `nereus-goto` reaches any step, the next one
animated; a follower (`data-mode="follow"`) ignores the keys that change the step and keeps its own size and language."""
import importlib.machinery
import importlib.util
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_portal_mode import chromium, portal, serve  # noqa: E402


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


ro = load("render_outline_steps", HERE / "render-outline")

# Every deck of the directory: lists, terminals (`stepwise` ones too) and diagrams that reveal parts.
DECKS = sorted(path.stem for path in HERE.glob("*.yaml"))


def render(tmp_path, name, follow=False, mode=None):
  subprocess.run([sys.executable, str(HERE / "render-outline"), str(HERE / f"{name}.yaml"), "--split",
                  "--output", str(tmp_path / f"{name}.html")], check=True, capture_output=True)
  page = tmp_path / f"{name}.html"
  mode = "follow" if follow else mode
  if mode:
    page.write_text(page.read_text().replace("<html ", f'<html data-mode="{mode}" ', 1))
  return ro.deck_steps(page.read_text())


def test_a_terminal_command_is_two_units_and_a_stepwise_output_one_more_per_filled_line():
  terminal = {"steps": [{"run": "a", "output": "one\n\ntwo\nthree\n", "stepwise": True}, {"run": "b"}, {"run": "c", "output": "x\ny"}]}
  assert ro.terminal_units(terminal) == (2 + 2) + 2 + 2


def test_an_item_counts_once_whatever_its_other_classes():
  assert ro.item_units("<p class='lead st'>a</p><li class='st sub'>b</li><li class='sub'>c</li><li class='step'>d</li>") == 2


RECORD = """
window.__steps = [];
document.addEventListener('nereus-step', e => window.__steps.push(e.detail), true);
"""

# No motion: every ArrowDown is one step, reported once, until the last step of the main deck.
WALK = """
async total => {
  const key = k => document.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true}));
  const seen = [];
  for (let i = 1; i < total + 5; i++) {
    const before = window.__steps.length;
    key('ArrowDown');
    seen.push(window.__steps.length - before === 1 ? window.__steps[window.__steps.length - 1].step : null);
  }
  return {seen, steps: window.__steps[0].steps};
}
"""

GOTO = """
n => { document.dispatchEvent(new CustomEvent('nereus-goto', {detail: {step: n}})); return window.__steps.at(-1).step; }
"""


def open_page(tmp_path, name, motion):
  from playwright import sync_api
  server = serve(tmp_path, portal.csp("https://auth.example.com"))
  playwright = sync_api.sync_playwright().start()
  browser = chromium(playwright)
  page = browser.new_page(viewport={"width": 390, "height": 760})
  errors = []
  page.on("pageerror", lambda error: errors.append(str(error)))
  page.add_init_script(f"try {{ localStorage.setItem('deck.motion', '{motion}'); }} catch (e) {{}}" + RECORD)
  page.goto(f"http://127.0.0.1:{server.server_address[1]}/{name}.html", wait_until="load")

  def close():
    browser.close()
    playwright.stop()
    server.shutdown()
  return page, errors, close


@pytest.mark.parametrize("name", DECKS)
def test_the_engine_walks_exactly_the_steps_the_renderer_counts(tmp_path, name):
  total = render(tmp_path, name)
  page, errors, close = open_page(tmp_path, name, "off")
  try:
    walked = page.evaluate(WALK, total)
    # Past the last step a press moves nothing: no event.
    assert walked["seen"] == list(range(1, total)) + [None] * 5
    assert walked["steps"] == total
    for n in (total - 1, 0, total // 2, total // 2 + 1, 3, 2):
      assert page.evaluate(GOTO, n) == n
    assert errors == []
  finally:
    close()


def test_the_next_step_animates_and_a_jump_does_not(tmp_path):
  total = render(tmp_path, "presentations-reef")
  page, errors, close = open_page(tmp_path, "presentations-reef", "on")
  try:
    # The first slide with a terminal: its first unit types the first command.
    first = page.evaluate("""() => {
      const slides = [...document.querySelectorAll('[data-deck="main"] > .slide')];
      let base = 0;
      for (const s of slides) { if (s.querySelector('.term')) return base + s.querySelectorAll('div[lang="en"] .st').length; base += Number(s.dataset.units) + 1; }
      return -1;
    }""")
    assert 0 < first < total
    page.evaluate(GOTO, first)
    assert page.evaluate("document.querySelector('.slide.on .term')._phase") == "idle"
    page.evaluate(GOTO, first + 1)
    assert page.evaluate("document.querySelector('.slide.on .term')._phase") == "typing"
    # The run arrives while it still types: the typing ends at once, then the command runs.
    page.evaluate(GOTO, first + 2)
    assert page.evaluate("document.querySelector('.slide.on .term')._u") == 2
    # A jump back reaches its step at once, typing nothing.
    page.evaluate(GOTO, first + 1)
    assert page.evaluate("document.querySelector('.slide.on .term')._phase") == "typed"
    assert errors == []
  finally:
    close()


def test_a_follower_keeps_its_step_its_size_and_its_language_but_never_moves_on_its_own(tmp_path):
  total = render(tmp_path, "presentations-reef", follow=True)
  page, errors, close = open_page(tmp_path, "presentations-reef", "off")
  try:
    key = "k => document.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true}))"
    for k in ("ArrowDown", "ArrowRight", "Home", "r", "i", "n"):
      page.evaluate(key, k)
    assert page.evaluate("document.querySelector('.slide.on').id") == page.evaluate("document.querySelector('[data-deck=main] > .slide').id")
    assert page.evaluate("window.__steps.at(-1).step") == 0
    n = total // 2
    assert page.evaluate(GOTO, n) == n
    page.evaluate(key, "+")
    assert page.evaluate("document.documentElement.style.getPropertyValue('--fs')") != ""
    # The language changes on this screen only, and the step stays.
    page.evaluate(key, "l")
    assert page.evaluate("document.documentElement.dataset.lang") == "pt"
    assert page.evaluate(GOTO, n + 1) == n + 1
    hidden = page.evaluate("['joy', 'prevBtn', 'nextBtn', 'notesBtn', 'restartBtn'].map(id => getComputedStyle(document.getElementById(id)).display)")
    assert hidden == ["none"] * 5
    assert page.evaluate("getComputedStyle(document.getElementById('zoomIn')).display") != "none"
    assert errors == []
  finally:
    close()


def test_the_speaker_s_hosted_deck_keeps_every_control_never_writes_the_address_and_shows_the_clock(tmp_path):
  """data-mode="drive" (#1761, the Sessions tab): the page that hosts it sets the step, so it starts on the first one and
  never writes the hash or this browser's slide; the keys move it and report each step; the clock goes in the bottom bar."""
  total = render(tmp_path, "presentations-reef", mode="drive")
  page, errors, close = open_page(tmp_path, "presentations-reef", "off")
  try:
    assert page.evaluate("location.hash") == ""
    assert page.evaluate("window.__steps.at(-1).step") == 0
    page.evaluate("k => document.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true}))", "ArrowDown")
    assert page.evaluate("window.__steps.at(-1).step") == 1
    assert page.evaluate(GOTO, total // 2) == total // 2
    assert page.evaluate("location.hash") == ""
    assert page.evaluate("Object.keys(localStorage).filter(k => k.endsWith('.slide'))") == []
    shown = "['notesBtn', 'restartBtn', 'num'].map(id => getComputedStyle(document.getElementById(id)).display)"
    assert "none" not in page.evaluate(shown)
    assert page.evaluate("document.getElementById('clock').hidden")
    page.evaluate("() => document.dispatchEvent(new CustomEvent('nereus-clock', {detail: {text: '31:00 / 30:00', over: true}}))")
    assert page.evaluate("[document.getElementById('clock').textContent, document.getElementById('clock').hidden, document.getElementById('clock').className]") == ["31:00 / 30:00", False, "clock over"]
    # #1712: the bottom bar shows the short time and the pace's mark; the whole line is the clock's title.
    detail = "{text: '05:02 / 30:00 · 24:58 left · +0:40 behind', over: false, short: '05:02 / 30:00', pace: {text: '+0:40', kind: 'behind'}}"
    page.evaluate(f"() => document.dispatchEvent(new CustomEvent('nereus-clock', {{detail: {detail}}}))")
    clock = "(() => { const c = document.getElementById('clock'), p = document.getElementById('pace'); return [c.parentElement.tagName, document.getElementById('clockTime').textContent, c.title, p.textContent, p.className, p.hidden]; })()"
    assert page.evaluate(clock) == ["NAV", "05:02 / 30:00", "05:02 / 30:00 · 24:58 left · +0:40 behind", "+0:40", "pace behind", False]
    # #1712: in full screen the host offers End on the last step, in its own language; a press goes back to the host.
    assert page.evaluate("document.getElementById('endBtn').hidden")
    page.evaluate("() => { window.__ends = 0; document.addEventListener('nereus-end', () => window.__ends++); document.dispatchEvent(new CustomEvent('nereus-ending', {detail: {show: true, label: 'Encerrar'}})); }")
    assert page.evaluate("[document.getElementById('endBtn').hidden, document.getElementById('endBtn').textContent, document.getElementById('endBtn').getAttribute('aria-label')]") == [False, "✓", "Encerrar"]
    # End takes Next's place: on the last step Next does nothing.
    assert page.evaluate("getComputedStyle(document.getElementById('nextBtn')).display") == "none"
    page.click("#endBtn")
    assert page.evaluate("window.__ends") == 1
    page.evaluate("() => document.dispatchEvent(new CustomEvent('nereus-ending', {detail: {show: false}}))")
    assert page.evaluate("document.getElementById('endBtn').hidden")
    assert errors == []
  finally:
    close()


def test_the_steps_flag_prints_the_count_and_writes_nothing(tmp_path):
  """--steps (#1760): test/scene-presentations counts the presses of its deck with it."""
  import shutil
  import subprocess
  import sys
  outline = tmp_path / "scene.yaml"
  shutil.copy(HERE.parents[1] / "test" / "scene-presentations-deck.yaml", outline)
  found = subprocess.run([sys.executable, str(HERE / "render-outline"), str(outline), "--steps"], check=True, capture_output=True, text=True)
  assert found.stdout.strip() == "9"
  assert sorted(path.name for path in tmp_path.iterdir()) == ["scene.yaml"]
