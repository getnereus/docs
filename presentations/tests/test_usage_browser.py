"""The Usage tab's layout on a phone (spec 0015, #2326), in headless Chromium: <nereus-usage> over a fake api, at the
narrowest width and in both languages. The node tests check its figures; these check what only a browser can: the
week's ruler stays inside the card with the forecast's tick where the segments reach it, and a long day-off reason
never pushes the facts out of the card."""
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
      {"date": "2026-11-23", "kind": "gone", "share": 18, "total": 18, "estimate": False},
      {"date": "2026-11-24", "kind": "gone", "share": 0, "total": 18, "estimate": False, "off": "Doente"},
      {"date": "2026-11-25", "kind": "gone", "share": 20, "total": 38, "estimate": True},
      {"date": "2026-11-26", "kind": "today", "share": 20, "total": 58, "estimate": False, **({"off": today_off} if today_off else {})},
      {"date": "2026-11-27", "kind": "plan", "share": 28, "total": 86, "estimate": False},
      {"date": "2026-11-28", "kind": "plan", "share": 7, "total": 93, "estimate": False},
      {"date": "2026-11-29", "kind": "plan", "share": 7, "total": 100, "estimate": False},
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

    def opened(window, width=340, lang="pt-BR", scheme="dark"):
      server = serve(window)
      servers.append(server)
      page = browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme).new_page()
      page.goto(f"http://127.0.0.1:{server.server_port}/?lang={lang}")
      page.wait_for_function("document.querySelector('nereus-usage')?.shadowRoot?.querySelector('.hero .ruler')")
      return page

    yield opened
    browser.close()
  for server in servers:
    server.shutdown()


BOXES = """() => {
  const root = document.querySelector('nereus-usage').shadowRoot;
  const box = (node) => { const r = node.getBoundingClientRect(); return { left: r.left, right: r.right, width: r.width }; };
  return {
    hero: box(root.querySelector('.hero')),
    ruler: box(root.querySelector('.ruler')),
    segments: [...root.querySelectorAll('.ruler .rseg')].map(box),
    tick: box(root.querySelector('.ruler .tick')),
    facts: [...root.querySelectorAll('.facts dd')].map(box),
  };
}"""


@pytest.mark.parametrize("lang", ["pt-BR", "en"])
def test_the_ruler_stays_inside_the_card_and_its_tick_where_the_segments_reach_the_forecast(usage_page, lang):
  boxes = usage_page(week(), lang=lang).evaluate(BOXES)
  ruler = boxes["ruler"]
  assert all(ruler["left"] - 0.5 <= each["left"] and each["right"] <= ruler["right"] + 0.5 for each in boxes["segments"]), boxes
  assert ruler["right"] <= boxes["hero"]["right"]
  # the plan reaches 86 at the end of Friday's segment, the fourth drawn (Tuesday off used nothing: no segment)
  friday = boxes["segments"][3]
  tick = boxes["tick"]["left"] + boxes["tick"]["width"] / 2
  assert abs(tick - friday["right"]) <= 3, (tick, friday)


def test_a_long_day_off_reason_stays_inside_the_card(usage_page):
  page = usage_page(week(today_off="Consulta médica e exames de rotina anual"), lang="pt-BR")
  boxes = page.evaluate(BOXES)
  assert boxes["hero"]["right"] <= 340 - 16 + 0.5, boxes["hero"]  # the card keeps the page's 16 px margin
  assert all(each["right"] <= boxes["hero"]["right"] - 8 for each in boxes["facts"]), boxes
  assert page.evaluate("document.documentElement.scrollWidth") <= 340
