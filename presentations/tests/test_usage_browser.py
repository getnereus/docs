"""The Usage tab's layout on a phone (spec 0015, #2326; the corridor and the week's table of 2026-11-27), in headless
Chromium: <nereus-usage> over a fake api, at the narrowest width and in both languages. The node tests check its
figures; these check what only a browser can: the chart, the week's table and today's strip stay inside the card, each
day's column sits under its stretch of the chart, the whole card fits a phone's screen, and a long day-off reason never
pushes anything out of the card; the segmented button Week | Days (#2377) switches both."""
import http.server
import json
import pathlib
import threading

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
UI = REPO / "controllers" / "reference" / "ui"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/app.css"></head><body style="margin:0">
<script type="module">
import "/ui/usage.js";
const element = document.createElement("nereus-usage");
element.api = { get: async (path) => { const answer = await fetch("/answer" + path.split("?")[0]); return { ok: answer.ok, status: answer.status, json: () => answer.json() }; } };
element.lang = new URLSearchParams(location.search).get("lang") || "en";
document.body.append(element);
</script></body></html>"""


def week(today_off=None):
  """A mid-week reading: a day gone, a dated day off, an estimate, today, the plan to the reset with the weekend off."""
  return {
    "name": "weekly", "account": "aaa111", "used": 57.4, "resetsAt": "2026-11-30T04:00:00Z", "readAt": "2026-11-26T22:06:00Z",
    "timeZone": "America/Sao_Paulo", "ready": True, "reset": False, "forecast": 86.0, "pace": "steady", "todayGoal": 64,
    "todayOff": today_off,
    "days": [
      {"date": "2026-11-23", "start": "2026-11-23T04:00:00Z", "kind": "gone", "share": 18, "total": 18, "estimate": False, "ideal": 16, "adjusted": 16, "allowance": 16, "spent": 18},
      {"date": "2026-11-24", "start": "2026-11-24T03:00:00Z", "kind": "gone", "share": 0, "total": 18, "estimate": False, "off": "Doente", "ideal": 16, "adjusted": 18, "allowance": 0, "spent": 0},
      {"date": "2026-11-25", "start": "2026-11-25T03:00:00Z", "kind": "gone", "share": 20, "total": 38, "estimate": True, "ideal": 33, "adjusted": 36, "allowance": 18, "spent": 20},
      {"date": "2026-11-26", "start": "2026-11-26T03:00:00Z", "kind": "today", "share": 20, "total": 58, "estimate": False, "ideal": 48, "adjusted": 54, "allowance": 26, "spent": 20, "projected": 61,
       **({"off": today_off} if today_off else {})},
      {"date": "2026-11-27", "start": "2026-11-27T03:00:00Z", "kind": "plan", "share": 28, "total": 86, "estimate": False, "ideal": 66, "adjusted": 78, "allowance": 14, "spent": 17, "projected": 78},
      {"date": "2026-11-28", "start": "2026-11-28T03:00:00Z", "kind": "plan", "share": 7, "total": 93, "estimate": False, "ideal": 83, "adjusted": 89, "allowance": 11, "spent": 4, "projected": 82},
      {"date": "2026-11-29", "start": "2026-11-29T03:00:00Z", "kind": "plan", "share": 7, "total": 100, "estimate": False, "ideal": 100, "adjusted": 100, "allowance": 11, "spent": 4, "projected": 86},
    ],
  }


def serve(window):
  answers = {"/v1/usage/windows/weekly": window, "/v1/usage/dayoffs": {"items": []}, "/v1/usage/workweek": {"off": [], "worked": []}}

  class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
      pass

    def send(self, kind, body):
      self.send_response(200)
      self.send_header("Content-Type", kind)
      self.end_headers()
      self.wfile.write(body)

    def do_GET(self):
      path = self.path.split("?")[0]
      if path == "/":
        self.send("text/html", PAGE.encode())
      elif path == "/app.css":
        self.send("text/css", (REPO / "controllers" / "nereus-portal" / "static" / "app.css").read_bytes())
      elif path.startswith("/ui/") and (UI / path[4:]).is_file():
        self.send("text/javascript" if path.endswith(".js") else "text/css", (UI / path[4:]).read_bytes())
      elif path.startswith("/answer"):
        self.send("application/json", json.dumps(answers[path[len("/answer"):]]).encode())
      else:
        self.send_error(404)

  server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
  threading.Thread(target=server.serve_forever, daemon=True).start()
  return server


@pytest.fixture
def usage_page():
  """Opens the tab over a fake api at a width, a scheme and a language; returns the page, its shadow root at hand."""
  pytest.importorskip("playwright")
  from playwright import sync_api
  servers = []
  with sync_api.sync_playwright() as playwright:
    browser = None
    for channel in (None, "chrome"):
      try:
        browser = playwright.chromium.launch(channel=channel)
        break
      except Exception:
        continue
    if browser is None:
      pytest.skip("no headless browser: run `uvx playwright install chromium-headless-shell` or install Chrome")

    def opened(window, width=340, lang="pt-BR", scheme="dark", timezone_id=None, view=None):
      server = serve(window)
      servers.append(server)
      page = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme, timezone_id=timezone_id).new_page()
      page.goto(f"http://127.0.0.1:{server.server_port}/?lang={lang}")
      page.wait_for_function("document.querySelector('nereus-usage')?.shadowRoot?.querySelector('.hero .corridor svg')")
      if view:
        page.evaluate(f"document.querySelector('nereus-usage').shadowRoot.querySelector('[data-view={view}]').click()")
        page.wait_for_function(f"document.querySelector('nereus-usage')?.shadowRoot?.querySelector('.hero .corridor.{view} svg')")
      return page

    yield opened
    browser.close()
  for server in servers:
    server.shutdown()


BOXES = """() => {
  const root = document.querySelector('nereus-usage').shadowRoot;
  const box = (node) => { const r = node.getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width }; };
  return {
    hero: box(root.querySelector('.hero')),
    chart: box(root.querySelector('.corridor svg')),
    week: box(root.querySelector('.week')),
    days: [...root.querySelectorAll('.week thead th')].map(box),
    today: box(root.querySelector('.today')),
    views: box(root.querySelector('.views')),
    texts: [...root.querySelectorAll('.today b, .today span, .facts dd, .week td, .week th')].map(box),
  };
}"""


@pytest.mark.parametrize("view", [None, "days"])
@pytest.mark.parametrize("lang", ["pt-BR", "en"])
def test_the_chart_the_week_and_today_stay_inside_the_card_each_day_under_its_stretch_of_time(usage_page, lang, view):
  """Both views of #2377, Week (the default) and Days (a bar per day), in both languages."""
  page = usage_page(week(), lang=lang, view=view)
  boxes = page.evaluate(BOXES)
  hero = boxes["hero"]
  for name in ("chart", "week", "today", "views"):
    assert hero["left"] <= boxes[name]["left"] and boxes[name]["right"] <= hero["right"] + 0.5, (name, boxes)
  assert all(each["right"] <= hero["right"] + 0.5 for each in boxes["texts"]), boxes
  assert page.evaluate("document.documentElement.scrollWidth") <= 340
  # the chart's time axis starts after its 52 px label margin, as the table's first day does, and both end together;
  # the window is 7 days, so each day's column is a seventh of the axis
  axis = (boxes["chart"]["left"] + 52, boxes["chart"]["right"])
  assert abs(boxes["days"][0]["left"] - axis[0]) <= 1.5 and abs(boxes["days"][-1]["right"] - axis[1]) <= 1.5, boxes
  assert all(abs(each["width"] - (axis[1] - axis[0]) / 7) <= 1.5 for each in boxes["days"]), boxes
  # the whole card fits a phone's screen of 780 px with the portal's title and its bottom bar; the segmented button
  # Week | Days (#2377) adds its 40 px row, measured at the narrowest width, where the share's word wraps
  assert hero["bottom"] - hero["top"] <= 600, hero


def test_a_long_day_off_reason_stays_inside_the_card(usage_page):
  page = usage_page(week(today_off="Consulta médica e exames de rotina anual"), lang="pt-BR")
  boxes = page.evaluate(BOXES)
  assert boxes["hero"]["right"] <= 340 - 12 + 0.5, boxes["hero"]  # the card keeps the page's 12 px margin
  assert all(each["right"] <= boxes["hero"]["right"] for each in boxes["texts"]), boxes
  assert page.evaluate("document.documentElement.scrollWidth") <= 340


def resets_and_notice(page):
  return page.evaluate("""() => {
    const root = document.querySelector('nereus-usage').shadowRoot;
    return { label: root.querySelector('.hero .label').textContent, notice: root.querySelector('.hero .zone')?.textContent ?? null };
  }""")


def test_a_window_with_no_zone_shows_the_times_in_the_browsers_zone_and_says_the_days_are_cut_in_utc(usage_page):
  window = {key: value for key, value in week().items() if key != "timeZone"}
  shown = resets_and_notice(usage_page(window, lang="en", timezone_id="America/Sao_Paulo"))
  assert "Mon 01:00" in shown["label"], shown
  assert shown["notice"] == "Days cut in UTC · set the installation's time zone", shown


def test_a_window_with_a_zone_shows_the_same_times_and_no_notice(usage_page):
  shown = resets_and_notice(usage_page(week(), lang="en", timezone_id="America/Sao_Paulo"))
  assert "Mon 01:00" in shown["label"], shown
  assert shown["notice"] is None, shown
