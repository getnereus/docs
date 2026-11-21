"""The import of a deck from the portal (#1705), in headless Chromium under the portal's exact policy: the Decks screen
(controllers/leagore/ui/decks.js) imports the storytelling deck of #190, with the references and the other deck it names,
from a folder picked on a computer and from a package picked on a phone. A broken copy shows the Nereid's reason and
keeps Create closed; the right one checks clean and is created. The server here stands in for the portal and the API:
it serves the screen with portal.headers(), packs a folder with the CLI's own deck_package.from_folder (what the API
does) and checks every package with leagore's own deck.check (what the Nereid does). Skips when there is no browser."""
import base64
import binascii
import http.server
import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import threading

import pytest

HERE = pathlib.Path(__file__).resolve().parent.parent
REPO = HERE.parents[1]
UI = REPO / "controllers" / "leagore" / "ui"
STORY = HERE / "storytelling.yaml"


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


portal = load("portal_import", REPO / "controllers" / "nereus-portal" / "portal.py")
deck_package = load("deck_package_import", REPO / "cli" / "src" / "nereus" / "deck_package.py")
leagore_deck = load("leagore_deck_import", REPO / "controllers" / "leagore" / "deck.py")

STAND = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Decks</title><script type="module" src="/stand.js"></script></head><body></body></html>
"""
# The portal's api (screens.js bound) without its token: get and post of /v1, JSON in and out.
SCRIPT = """import "./decks.js";
const send = (method, path, body) => fetch(path, body === undefined
  ? { method, headers: { Accept: "application/json" } }
  : { method, headers: { Accept: "application/json", "Content-Type": "application/json" }, body: JSON.stringify(body) });
const element = document.createElement("nereus-presentations-decks");
element.lang = "en";
element.api = { get: (path) => send("GET", path), post: (path, body) => send("POST", path, body), delete: (path) => send("DELETE", path) };
document.body.append(element);
"""


def broken(text: str) -> str:
  assert "  - name: thanks\n" in text
  return text.replace("  - name: thanks\n", "  - name: thanks\n    refs: [nowhere]\n", 1)


# The package's own layout (#1706): its root is docs/, since the deck draws a diagram from docs/assets, so the deck sits
# at presentations/storytelling.yaml in it.
PACKAGE = deck_package.build(STORY).manifest
DECK = PACKAGE["deck"]


def folder_of(root: pathlib.Path, deck_text: str) -> pathlib.Path:
  """A folder laid out as the package (deck_text as the deck, every file it names) and a file it does not name."""
  for each in PACKAGE["files"]:
    target = root / each["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE.parent / each["path"], target)
  (root / DECK).write_text(deck_text)
  (root / "notes.txt").write_text("not named by the deck\n")
  return root


class Stand:
  """The screen at /, and the API's POST and GET of /v1/presentations/presentations over the real packing and checks."""

  def __init__(self):  # noqa: C901 - the handler's routes, one stand
    self.created = {}
    self.posts = []
    files = {"/decks.js": UI / "decks.js", "/decks.css": UI / "decks.css"}
    stand = self

    class Handler(http.server.BaseHTTPRequestHandler):
      def log_message(self, *args):
        pass

      def secure(self, code, kind, data):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        for key, value in portal.headers("https://auth.example.com").items():
          self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

      def answer(self, code, body):
        self.secure(code, "application/json", json.dumps(body).encode())

      def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
          self.secure(200, "text/html; charset=utf-8", STAND.encode())
        elif path == "/stand.js":
          self.secure(200, "text/javascript; charset=utf-8", SCRIPT.encode())
        elif path in files:
          self.secure(200, portal.content_type(files[path]), files[path].read_bytes())
        elif path == "/v1/presentations/presentations":
          self.answer(200, {"items": [{"metadata": {"name": name}, "status": found} for name, found in sorted(stand.created.items())]})
        else:
          self.answer(404, {"error": {"code": "NotFound", "message": path}})

      def do_POST(self):
        path, _, query = self.path.partition("?")
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        stand.posts.append((query, body))
        if path != "/v1/presentations/presentations":
          return self.answer(404, {"error": {"code": "NotFound", "message": path}})
        try:
          tar = stand.packed(body)
        except (deck_package.PackageError, binascii.Error, KeyError) as error:
          return self.answer(400, {"error": {"code": "Invalid", "message": str(error)}})
        checked = leagore_deck.check(tar)
        name = f"presentations/presentations/{body['name']}"
        if checked["errors"]:
          return self.answer(400, {"error": {"code": "Invalid", "message": f"{name}: the deck engine refuses the deck", "errors": checked["errors"]}})
        if query == "dryRun=true":
          return self.answer(200, {"result": "dryRun", "steps": checked["steps"], "warnings": checked["warnings"]})
        revision = leagore_deck.digest(tar)
        stand.created[body["name"]] = {"revision": revision, "revisions": 1, "slides": checked["steps"]}
        return self.answer(200, {"result": "created", "revision": revision})

    self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.httpd.daemon_threads = True
    threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
    self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"

  @staticmethod
  def packed(body: dict) -> bytes:
    """The API's presentation_request, for the forms the screen sends: a package, a folder or a deck alone."""
    if "package" in body:
      return base64.b64decode(body["package"], validate=True)
    if "folder" in body:
      files = {name: base64.b64decode(data, validate=True) for name, data in body["folder"]["files"].items()}
      return deck_package.from_folder(files, body["folder"]["deck"]).tar
    return deck_package.from_text(body["deck"], body.get("source")).tar

  def close(self):
    self.httpd.shutdown()


# The steps the storytelling deck renders, as the Nereid counts them.
STEPS = leagore_deck.check(deck_package.build(STORY).tar)["steps"]

LISTENER = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.effectiveDirective + ' ' + e.blockedURI), true);
"""


def chromium(playwright):
  failures = []
  for channel in (None, "chrome"):
    try:
      return playwright.chromium.launch(channel=channel)
    except Exception as error:
      failures.append(str(error).splitlines()[0])
  pytest.skip("no headless browser: run `uvx playwright install chromium-headless-shell` or install Chrome\n" + "\n".join(failures))


@pytest.fixture
def opened():
  """A page of the Decks screen on the stand, and its checks at the end: no page error, no CSP violation, no request
  to another origin."""
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand()
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)

      def page_on(device=None):
        options = {key: value for key, value in playwright.devices[device].items() if key != "default_browser_type"} if device else {}
        page = browser.new_context(**options, locale="en-US").new_page()
        page.add_init_script(LISTENER)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: None if request.url.startswith(stand.url) else outside.append(request.url))
        page.goto(stand.url + "/")
        # The import is a bottom sheet behind the extended FAB (#1839).
        page.locator("[data-role=import]").click()
        page.locator("[data-role=file]").wait_for(state="attached")
        pages.append(page)
        return page

      errors, outside, pages = [], [], []
      yield stand, page_on, sync_api.expect
      for page in pages:
        assert page.evaluate("window.__csp") == []
      assert errors == [] and outside == []
      browser.close()
  finally:
    stand.close()


def test_a_computer_imports_the_storytelling_folder_a_broken_copy_refused_then_the_right_one_created(opened, tmp_path):
  stand, page_on, expect = opened
  page = page_on()
  text = STORY.read_text()
  wrong = folder_of(tmp_path / "wrong" / "talks", broken(text))
  page.locator("[data-role=segment-folder]").click()
  page.locator("[data-role=folder]").set_input_files(wrong)
  page.locator("[data-role=choose]").select_option(f"talks/{DECK}")
  expect(page.locator("[data-role=note]")).to_contain_text("file(s) of the folder go with the deck")
  page.locator("[data-role=check]").click()
  expect(page.locator("[data-role=reason]")).to_have_text(["thanks: refs unknown reference 'nowhere'"])
  expect(page.locator("[data-role=create]")).to_be_disabled()
  sent = stand.posts[-1][1]["folder"]["files"]
  assert "talks/notes.txt" not in sent and f"talks/{DECK}" in sent
  assert stand.created == {}

  right = folder_of(tmp_path / "right" / "talks", text)
  page.locator("[data-role=folder]").set_input_files(right)
  page.locator("[data-role=choose]").select_option(f"talks/{DECK}")
  expect(page.locator("[data-role=name]")).to_have_value("storytelling")
  page.locator("[data-role=check]").click()
  expect(page.locator("[data-role=result]")).to_contain_text(f"The deck renders: {STEPS} steps.")
  page.locator("[data-role=create]").click()
  expect(page.locator("[data-role=created]")).to_contain_text("storytelling created, revision sha256:")
  expect(page.locator("[data-role=deck-name]")).to_have_text(["storytelling"])
  assert stand.created["storytelling"]["revision"] == leagore_deck.digest(deck_package.from_folder(
    {f"talks/{path.relative_to(right).as_posix()}": path.read_bytes() for path in right.rglob("*") if path.is_file()}, f"talks/{DECK}").tar)


def test_a_phone_imports_the_storytelling_package_a_broken_one_refused_then_the_right_one_created(opened, tmp_path):
  stand, page_on, expect = opened
  page = page_on("iPhone 13")
  text = STORY.read_text()
  wrong = folder_of(tmp_path / "wrong", broken(text))
  (tmp_path / "storytelling.tar").write_bytes(deck_package.build(wrong / DECK).tar)
  page.locator("[data-role=file]").set_input_files(tmp_path / "storytelling.tar")
  page.locator("[data-role=check]").click()
  expect(page.locator("[data-role=reason]")).to_have_text(["thanks: refs unknown reference 'nowhere'"])
  expect(page.locator("[data-role=create]")).to_be_disabled()

  package = deck_package.build(STORY)
  (tmp_path / "right").mkdir()
  (tmp_path / "right" / "storytelling.tar").write_bytes(package.tar)
  page.locator("[data-role=file]").set_input_files(tmp_path / "right" / "storytelling.tar")
  page.locator("[data-role=check]").click()
  expect(page.locator("[data-role=result]")).to_contain_text(f"The deck renders: {STEPS} steps.")
  page.locator("[data-role=create]").click()
  expect(page.locator("[data-role=created]")).to_contain_text(f"storytelling created, revision {package.revision[:15]}")
  expect(page.locator("[data-role=sheet]")).not_to_be_visible()
  assert stand.created["storytelling"]["revision"] == package.revision
