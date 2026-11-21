"""A New session FAB creates a Session from the portal (#1843), in headless Chromium inside the real portal (index.html,
app.js, app.css, its navigation bar and rail, under the portal's exact policy), signed in through the stand-in of
oidc-client-ts, with leagore's real drive.js and drive.css on the Sessions of test_drive_browser.py. The extended FAB sits
over the navigation bar on a phone and at the head of the list from 840 px; it opens a modal bottom sheet (the
presentation from the Decks, the Session's name, the talk time, Rehearsal as a switch) whose Create posts what the CLI
posts, and the new Session shows in the list (opened beside it, selected, at 1280x800). A refusal shows its line inside
the sheet; Escape and the scrim close it, and the focus stays inside. Every control is measured inside the window and
uncut in English and Portuguese at 340, 360, 390 and 412 px and at 1280x800. Set DRIVE_SHOTS to a folder to keep the
screenshots (the list with the FAB and the sheet, 390x844, dark and light). Every name is invented. Skips with no
browser."""
import json

import pytest
from test_drive_browser import ITEMS, LANGS, MEASURE, WIDTHS, chromium, shots
from test_list_detail_browser import Portal, portal_page

SESSIONS = "/v1/presentations/sessions"
DECKS = ["storytelling", "release"]
CONTROLS = ".fab, .sheet-title, .input, .field-label, .field-help, .switch-row, .sheet-actions button, .sheet-error, .session, .chip"
PRESSED = ("new-session", "new-session-presentation", "new-session-name", "new-session-talk", "new-session-rehearsal", "new-session-cancel", "new-session-create", "session")
# The deepest focused element, through the shadow roots, is inside the sheet; or the body, the step where a modal dialog
# lets the focus go to the browser's own controls, never to the page behind.
FOCUS_INSIDE = """() => {
  let node = document.activeElement;
  while (node && node.shadowRoot && node.shadowRoot.activeElement) { node = node.shadowRoot.activeElement; }
  return node === document.body || Boolean(node && node.closest('dialog[data-role=new-session-sheet]'));
}"""
BOX = """(role) => {
  const node = document.querySelector('nereus-presentations-drive').shadowRoot.querySelector(`[data-role=${role}]`);
  return node && node.getClientRects().length ? node.getBoundingClientRect().toJSON() : null;
}"""


class Stand(Portal):
  """The portal's stand of the Sessions, with the Decks' Presentations and the Session posts: a new name joins the list,
  a name already listed is refused as the API refuses it (409 AlreadyExists)."""

  def __init__(self, directory, **options):
    super().__init__(directory, **options)
    self.reset()

  def reset(self):
    self.items, self.created = [dict(item) for item in ITEMS], []

  def answer(self, path):
    if path == SESSIONS:
      return self.json({"items": self.items})
    if path == "/v1/presentations/presentations":
      return self.json({"items": [{"metadata": {"name": name}, "spec": {}, "status": {"slides": 4}} for name in DECKS]})
    created = {body["name"]: body for body in self.created}
    name = path.rsplit("/", 1)[1]
    if path == f"{SESSIONS}/{name}" and name in created:
      spec = {"presentation": created[name]["presentation"], "talk": created[name]["talk"]}
      return self.json({"object": {"metadata": {"name": name}, "spec": spec}, "state": self.state(), "follow": "/p/K7Q4", "followers": 0, "live": True, "slides": self.slides})
    return super().answer(path)

  def posted(self, path, body):
    if path != SESSIONS:
      return super().posted(path, body)
    with self.lock:
      if any(item["metadata"]["name"] == body.get("name") for item in self.items):
        refused = {"error": {"code": "AlreadyExists", "message": f"presentations/sessions/{body['name']} already exists", "errors": ["choose another name"]}}
        return 409, "application/json", json.dumps(refused).encode(), False
      self.created.append(body)
      spec = {"presentation": body["presentation"], "talk": body["talk"], **({"rehearsal": True} if body.get("rehearsal") else {})}
      self.items.append({"metadata": {"name": body["name"]}, "spec": spec, "status": {"step": 0, "slides": 4}})
    return self.json({"result": "created", "object": self.items[-1], "state": self.state(), "follow": None if body.get("rehearsal") else "/p/K7Q4"})


def measured(page, width):
  """Every shown control inside the window, none cut, no horizontal scroll; the ones to press at least 48 px high."""
  found = page.evaluate(MEASURE, CONTROLS)
  assert found["scroll"] <= found["width"], found
  for box in found["boxes"]:
    assert box["left"] >= 0 and box["right"] <= width + 0.5, (width, box)
    assert not box["cut"], (width, box)
    if box["role"] in PRESSED:
      assert box["height"] >= 48, box
  return found["boxes"]


def sheet_opened(page):
  page.locator("[data-role=new-session]").click()
  page.locator("[data-role=new-session-create]").wait_for(timeout=5000)


def test_the_fab_and_the_sheet_fit_every_phone_in_both_languages(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        for width in WIDTHS:
          page, errors, outside = portal_page(playwright, browser, stand, lang, width, 844)
          fab = page.evaluate(BOX, "new-session")
          bar = page.locator("#tabs").bounding_box()
          # Over the navigation bar, never on it, at the right edge.
          assert fab and fab["bottom"] <= bar["y"] and fab["height"] == 56 and width - fab["right"] == 16, (fab, bar)
          assert page.locator("[data-role=new-session]").inner_text() == ("New session" if lang == "en" else "Nova sessão")
          measured(page, width)
          sheet_opened(page)
          boxes = measured(page, width)
          roles = {box["role"] for box in boxes}
          assert {"new-session-presentation", "new-session-name", "new-session-talk", "new-session-rehearsal", "new-session-cancel", "new-session-create"} <= roles, roles
          if lang == "en" and width == 390 and shots():
            page.keyboard.press("Escape")
            for scheme in ("dark", "light"):
              page.emulate_media(color_scheme=scheme)
              # Escape gives the focus back to the FAB, with its ring: the list's picture is taken without it.
              page.evaluate("() => document.querySelector('nereus-presentations-drive').shadowRoot.activeElement?.blur()")
              page.wait_for_timeout(300)
              page.screenshot(path=str(shots() / f"new-session-list-390x844-{scheme}.png"))
              sheet_opened(page)
              page.wait_for_timeout(300)
              page.screenshot(path=str(shots() / f"new-session-sheet-390x844-{scheme}.png"))
              page.keyboard.press("Escape")
          assert page.evaluate("() => window.__csp") == [] and errors == [] and outside == []
          page.context.close()
      browser.close()
  finally:
    stand.close()


def test_a_session_created_from_the_sheet_shows_in_the_list_and_a_refusal_stays_in_the_sheet(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        stand.reset()
        page, errors, outside = portal_page(playwright, browser, stand, lang, 390, 844)
        sheet = page.locator("[data-role=new-session-sheet]")
        # Escape and the scrim close the sheet; Tab never leaves it.
        sheet_opened(page)
        for _ in range(10):
          page.keyboard.press("Tab")
          assert page.evaluate(FOCUS_INSIDE)
        page.keyboard.press("Escape")
        sync_api.expect(sheet).not_to_be_visible()
        sheet_opened(page)
        page.mouse.click(195, 20)
        sync_api.expect(sheet).not_to_be_visible()
        # A rehearsal of release, 90 minutes: the name follows the presentation, the switch turns on, Create posts it.
        sheet_opened(page)
        assert page.locator("[data-role=new-session-name]").input_value() == "storytelling-1"
        page.locator("[data-role=new-session-presentation]").select_option("release")
        assert page.locator("[data-role=new-session-name]").input_value() == "release-1"
        page.locator("[data-role=new-session-talk]").select_option("90")
        switch = page.locator("[data-role=new-session-rehearsal]")
        switch.click()
        sync_api.expect(switch).to_have_attribute("aria-checked", "true")
        page.locator("[data-role=new-session-create]").click()
        sync_api.expect(sheet).not_to_be_visible()
        page.locator("[data-role=session-title]", has_text="release-1").wait_for(timeout=5000)
        assert stand.created == [{"name": "release-1", "presentation": "release", "talk": "1h30m", "rehearsal": True}], stand.created
        # A name already listed: the API's refusal and its reason inside the sheet, which stays open.
        sheet_opened(page)
        page.locator("[data-role=new-session-name]").fill("platform-day")
        page.locator("[data-role=new-session-create]").click()
        page.locator("[data-role=new-session-error-line]", has_text="already exists").wait_for(timeout=5000)
        sync_api.expect(page.locator("[data-role=reason]")).to_have_text("choose another name")
        sync_api.expect(sheet).to_be_visible()
        measured(page, 390)
        page.keyboard.press("Escape")
        # The screen stays: the list, not the portal's error view.
        sync_api.expect(page.locator("[data-role=sessions]")).to_be_visible()
        assert len(stand.created) == 1
        assert page.evaluate("() => window.__csp") == [] and errors == [] and outside == []
        page.context.close()
      browser.close()
  finally:
    stand.close()


def test_on_a_wide_screen_the_fab_heads_the_list_and_the_new_session_opens_beside_it(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        stand.reset()
        page, errors, outside = portal_page(playwright, browser, stand, lang, 1280, 800)
        fab, rows, detail = (page.evaluate(BOX, role) for role in ("new-session", "sessions", "detail"))
        # At the head of the list, never over the detail.
        assert fab["bottom"] <= rows["top"] + 0.5 and fab["right"] <= detail["left"], (fab, rows, detail)
        measured(page, 1280)
        sheet_opened(page)
        measured(page, 1280)
        page.locator("[data-role=new-session-create]").click()
        sync_api.expect(page.locator("[data-role=new-session-sheet]")).not_to_be_visible()
        page.locator("[data-role=controls]").wait_for(timeout=5000)
        selected = page.locator("[data-role=session][aria-current=true] [data-role=session-title]")
        sync_api.expect(selected).to_have_text("storytelling-1")
        sync_api.expect(page.locator("[data-role=session-name]")).to_have_text("storytelling-1")
        assert stand.created == [{"name": "storytelling-1", "presentation": "storytelling", "talk": "30m"}], stand.created
        assert page.evaluate("() => window.__csp") == [] and errors == [] and outside == []
        page.context.close()
      browser.close()
  finally:
    stand.close()
