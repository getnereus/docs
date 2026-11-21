"""The room's pace thermometer in full screen (#1922), in headless Chromium: the engine's bottom bar shows the host's counts
(`nereus-pace`, "▲ 1  ▼ 2": up too fast, down too slow, 0 and 0 included) after the clock and the pace's mark, its sentence
as the label, on one line with the clock on a phone of 340 to 412 px in both languages, the questions' longer clock
included, every control inside the screen and the buttons' row where it was; off, it hides. Under the portal's policy;
skips with no browser. The storytelling deck: presentations-reef has a slide named `pace`, whose id the bar's mark shares."""
import pytest

from test_drive_browser import LANGS, chromium
from test_follow_browser import LISTENER
from test_portal_mode import portal, serve
from test_steps import GOTO, RECORD, render

WIDTHS = (340, 412)
LABEL = {"en": "12 too fast, 10 too slow", "pt": "12 muito rápido, 10 muito lento"}
# The clock as the host sends it (drive.js): the talk's short time, and the questions' one, the longest the bar gets.
CLOCKS = {"en": ("12:34 / 30:00", "Questions 01:00 / 10:00"), "pt": ("12:34 / 30:00", "Perguntas 01:00 / 10:00")}
ROW = """() => {
  const width = document.documentElement.clientWidth;
  const box = (node) => { const r = node.getBoundingClientRect(); return { id: node.id || node.className, left: r.left, right: r.right, top: r.top, bottom: r.bottom }; };
  const shown = [...document.querySelectorAll('nav.bar > *, #clock > *')].filter((node) => node.getClientRects().length > 0);
  const gauge = document.getElementById('gauge');
  return { width, scroll: document.documentElement.scrollWidth, boxes: shown.map(box), clock: box(document.getElementById('clock')),
           buttons: [...document.querySelectorAll('nav.bar > button')].filter((node) => node.getClientRects().length > 0).map(box),
           cut: gauge.scrollWidth > gauge.clientWidth + 0.5 };
}"""


def clock(page, short, gauge=None):
  page.evaluate("""([short, gauge]) => {
    document.dispatchEvent(new CustomEvent('nereus-clock', {detail: {text: short + ' · 17:26 left · 3 to go', over: false, short, pace: {text: '+1:20', kind: 'behind'}}}));
    if (gauge) document.dispatchEvent(new CustomEvent('nereus-pace', {detail: gauge}));
  }""", [short, gauge])


@pytest.mark.parametrize("lang", LANGS)
def test_the_gauge_sits_on_the_clock_s_row_on_one_line_at_phone_widths_and_hides_when_off(tmp_path, lang):
  sync_api = pytest.importorskip("playwright.sync_api")
  total = render(tmp_path, "storytelling", mode="drive")
  server = serve(tmp_path, portal.csp("https://auth.example.com"))
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for width in WIDTHS:
        page = browser.new_page(viewport={"width": width, "height": 760})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.add_init_script(f"try {{ localStorage.setItem('deck.motion', 'off'); localStorage.setItem('deck.lang', '{lang}'); }} catch (e) {{}}" + RECORD + LISTENER)
        page.goto(f"http://127.0.0.1:{server.server_address[1]}/storytelling.html", wait_until="load")
        # The last step, End and the room's turn on offer: the fullest the bar gets.
        assert page.evaluate(GOTO, total - 1) == total - 1
        page.evaluate("""() => {
          document.dispatchEvent(new CustomEvent('nereus-ending', {detail: {show: true, label: 'End'}}));
          document.dispatchEvent(new CustomEvent('nereus-turn', {detail: {show: true, label: 'Rate', part: 'rating'}}));
        }""")
        gauge = page.locator("#gauge")
        for short in CLOCKS[lang]:
          clock(page, short, {"show": False, "slow": 0, "fast": 0, "text": "", "label": ""})
          assert gauge.is_hidden(), "no gauge until the host shows one"
          before = page.evaluate(ROW)["buttons"]
          clock(page, short, {"show": True, "slow": 10, "fast": 12, "text": "▲ 12  ▼ 10", "label": LABEL[lang]})
          assert gauge.is_visible()
          assert [gauge.text_content(), gauge.get_attribute("aria-label"), gauge.get_attribute("title")] == ["▲ 12  ▼ 10", LABEL[lang], LABEL[lang]]
          row = page.evaluate(ROW)
          assert not row["cut"], (width, short, "the gauge is cut short")
          assert row["scroll"] <= row["width"], row
          for box in row["boxes"]:
            assert box["left"] >= -0.5 and box["right"] <= row["width"] + 0.5, (width, short, box)
          # One line: the clock's row is one line high, and the buttons stay where they were.
          parts = [box for box in row["boxes"] if box["id"] in ("clockTime", "pace", "gauge")]
          assert len(parts) == 3 and max(box["top"] for box in parts) < min(box["bottom"] for box in parts), (width, short, parts)
          assert row["clock"]["bottom"] - row["clock"]["top"] < 30, (width, short, row["clock"])
          assert row["buttons"] == before, (width, short, "the gauge moved the buttons")
        # Live with no tap yet: 0 and 0 show; off, it hides.
        clock(page, CLOCKS[lang][0], {"show": True, "slow": 0, "fast": 0, "text": "▲ 0  ▼ 0", "label": "0"})
        assert gauge.is_visible() and gauge.text_content() == "▲ 0  ▼ 0"
        clock(page, CLOCKS[lang][0], {"show": False, "slow": 0, "fast": 0, "text": "▲ 0  ▼ 0", "label": "0"})
        assert gauge.is_hidden() and page.locator("#clockTime").is_visible()
        assert errors == [] and page.evaluate("window.__csp") == []
        page.close()
      browser.close()
  finally:
    server.shutdown()
