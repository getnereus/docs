"""The Share bottom sheet (#1841), in headless Chromium on a phone: the Drive screen's QR action opens one modal sheet with
Audience | Projector, the link's QR code, its full address (wrapped, never cut), a help line, the switch Show on the
projector (#1859), Copy link and Done. The test
switches the segment and sees the address, the QR code and the help change; copies through the Clipboard API (the
permission granted) and sees the snackbar; copies again with no Clipboard API and finds the address selected; keeps the
focus inside while tabbing; closes with Escape and with a click on the scrim. Every control of the sheet is measured in
English and Portuguese at 340, 360, 390 and 412 px (docs/agent/decks.md, "Screens on a phone"), with no CSP violation.
With DRIVE_SHOTS set to a folder, it saves the sheet at 390x844 in both themes. The stand is test_drive_browser.py's;
every name is invented. Skips with no browser."""
import pytest
from test_drive_browser import LANGS, WIDTHS, Stand, chromium, fits, opened, phone, pressable, shots
from test_follow_browser import CODE

SHEET = ".sheet-title, .segment, .qr, .share-url, .share-help, .switch-row, .switch-label, .switch-help, .snackbar, .sheet-actions button"
WORDS = {
  "en": {"title": "Share this Session", "follow": "Audience", "projector": "Projector", "copy": "Copy link", "done": "Done", "copied": "Link copied",
         "selected": "Link selected: copy it from here", "follow_help": "Scan to follow", "projector_help": "Open it on the room screen",
         "show_qr": "Show on the projector"},
  "pt": {"title": "Compartilhar esta Sessão", "follow": "Plateia", "projector": "Projetor", "copy": "Copiar link", "done": "Concluir", "copied": "Link copiado",
         "selected": "Link selecionado: copie daqui", "follow_help": "Escaneie para acompanhar", "projector_help": "Abra na tela da sala",
         "show_qr": "Mostrar no projetor"},
}
# Where the focus is: inside the sheet, on the page outside it, or nowhere on the page (the browser's own interface).
FOCUS = """() => {
  const root = document.querySelector('nereus-presentations-drive').shadowRoot;
  const sheet = root.querySelector('dialog');
  if (document.activeElement === document.body || document.activeElement === null) { return 'none'; }
  const inside = root.activeElement && sheet.contains(root.activeElement);
  return inside ? (root.activeElement.dataset.role || 'sheet') : 'outside:' + (root.activeElement ? root.activeElement.dataset.role : document.activeElement.tagName);
}"""
OPEN = "() => document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('dialog').open"
SELECTED = "() => document.getSelection().toString()"
BOX = "() => { const box = document.querySelector('nereus-presentations-drive').shadowRoot.querySelector('dialog').getBoundingClientRect(); return [box.top, box.bottom, innerHeight]; }"


def sheet_opened(page, lang, width, stand, scheme="dark"):
  opened(page, stand, lang, width, scheme=scheme)
  page.locator("[data-role=session]").first.click()
  page.locator("[data-role=share]").click()
  page.locator("[data-role=share-sheet]").wait_for(timeout=3000)
  assert page.evaluate(OPEN)


def test_the_share_sheet_switches_copies_keeps_the_focus_closes_and_fits_every_phone(tmp_path):
  pytest.importorskip("playwright")
  from playwright import sync_api
  stand = Stand(tmp_path)
  try:
    with sync_api.sync_playwright() as playwright:
      browser = chromium(playwright)
      for lang in LANGS:
        words = WORDS[lang]
        page, errors = phone(playwright, browser, lang, permissions=["clipboard-read", "clipboard-write"])
        follow, projector = f"{stand.url}/p/{CODE}", f"{stand.url}/p/{CODE}?projector"
        for width in WIDTHS:
          sheet_opened(page, lang, width, stand)
          assert page.locator("[data-role=share-title]").inner_text() == words["title"]
          labels = [page.locator(f"[data-role={role}]").inner_text() for role in ("segment-follow", "segment-projector", "copy", "done")]
          assert labels == [words["follow"], words["projector"], words["copy"], words["done"]], labels
          assert page.locator("[data-role=share-projector] .switch-label").inner_text() == words["show_qr"]
          url = page.locator("[data-role=share-url]")
          image = page.locator("[data-role=qr-image]")
          assert url.inner_text() == follow and url.get_attribute("href") == follow
          assert page.locator("[data-role=segment-follow]").get_attribute("aria-pressed") == "true"
          assert page.locator("[data-role=share-help]").inner_text().startswith(words["follow_help"])
          code = image.get_attribute("src")
          # The QR code drew: a square image as wide as it is tall.
          assert image.evaluate("(node) => node.complete && node.naturalWidth > 0 && node.width === node.height && node.width >= 160")
          boxes = fits(page, SHEET)
          pressable(boxes)
          top, bottom, height = page.evaluate(BOX)
          assert top >= 0 and bottom <= height + 0.5, (top, bottom, height)
          # Projector switches the address, the QR code and the help line.
          page.locator("[data-role=segment-projector]").click()
          assert page.locator("[data-role=segment-projector]").get_attribute("aria-pressed") == "true"
          assert page.locator("[data-role=segment-follow]").get_attribute("aria-pressed") == "false"
          assert url.inner_text() == projector and url.get_attribute("href") == projector
          assert image.get_attribute("src") != code
          assert page.locator("[data-role=share-help]").inner_text().startswith(words["projector_help"])
          # Copy link: the Clipboard API, and the snackbar confirms it; the sheet still fits with the snackbar shown.
          page.locator("[data-role=copy]").click()
          page.locator("[data-role=snackbar]").filter(has_text=words["copied"]).wait_for(timeout=2000)
          assert page.evaluate("() => navigator.clipboard.readText()") == projector
          fits(page, SHEET)
          top, bottom, height = page.evaluate(BOX)
          assert top >= 0 and bottom <= height + 0.5, (top, bottom, height)
          # The focus stays inside the sheet: a Tab never lands on the screen under it.
          visited = set()
          for _ in range(10):
            page.keyboard.press("Tab")
            where = page.evaluate(FOCUS)
            assert not where.startswith("outside"), where
            visited.add(where)
          assert {"segment-follow", "segment-projector", "share-url", "share-projector", "share-thermometer", "copy", "done"} <= visited, visited
          # Escape closes it, and the focus goes back to Share.
          page.keyboard.press("Escape")
          assert not page.evaluate(OPEN)
          assert page.evaluate("() => document.querySelector('nereus-presentations-drive').shadowRoot.activeElement?.dataset.role") == "share"
          # It opens again on Audience; a tap on the scrim, above the sheet, closes it.
          page.locator("[data-role=share]").click()
          assert url.inner_text() == follow
          page.mouse.click(width / 2, 12)
          assert not page.evaluate(OPEN)
        # With no Clipboard API, Copy link selects the address and says so.
        sheet_opened(page, lang, 390, stand)
        page.evaluate("() => Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })")
        page.locator("[data-role=copy]").click()
        page.locator("[data-role=snackbar]").filter(has_text=words["selected"]).wait_for(timeout=2000)
        assert page.evaluate(SELECTED) == follow
        assert page.evaluate("() => window.__csp") == [] and errors == []
        page.context.close()
      if shots():
        for scheme in ("dark", "light"):
          page, _ = phone(playwright, browser, "en", permissions=["clipboard-read", "clipboard-write"])
          sheet_opened(page, "en", 390, stand, scheme=scheme)
          page.wait_for_timeout(300)
          page.screenshot(path=str(shots() / f"share-390x844-{scheme}.png"))
          page.context.close()
      browser.close()
  finally:
    stand.close()
