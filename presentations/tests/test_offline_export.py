"""The offline export (#1703), the whole chain, in headless Chromium: the CLI packs the storytelling deck (#190) as it does
for `nereus presentations presentation create`, leagore checks and renders the package as it does for a revision, and its
offline page, the one `get --output html` writes, opens from file:// with the network off. Every step of the deck shows,
every slide with its diagrams drawn, no request leaves the file and no script fails. Skips when there is no browser."""
import importlib.machinery
import importlib.util
import re
import sys

import pytest
from test_follow_browser import HERE, REPO, chromium

sys.path.insert(0, str(REPO / "cli" / "src"))
from nereus import deck_package  # noqa: E402


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


leagore = load("leagore_deck_offline", REPO / "controllers" / "leagore" / "deck.py")
ro = load("render_outline_offline", HERE / "render-outline")
# The scene's offline check (#1706): which diagrams of the slide on screen are drawn.
offline = load("scene_presentations_offline", REPO / "test" / "scene-presentations-offline")
SOURCE = HERE / "storytelling.yaml"


def test_the_exported_storytelling_deck_opens_offline_with_every_slide_and_diagram(tmp_path):
  playwright = pytest.importorskip("playwright.sync_api")
  page_html = leagore.parse(deck_package.build(SOURCE).tar).offline
  steps = ro.deck_steps(page_html)
  main = page_html.split('<div data-deck="refs">', 1)[0]
  slides = re.findall(r"<section class='slide[^']*' id='([^']*)'", main)
  assert steps > len(slides) > 10
  target = tmp_path / "storytelling.html"
  target.write_text(page_html)
  with playwright.sync_playwright() as driver:
    browser = chromium(driver)
    try:
      context = browser.new_context()
      context.set_offline(True)
      left = []
      context.route("**/*", lambda route: route.continue_() if route.request.url.startswith("file://") else (left.append(route.request.url), route.abort()))
      page = context.new_page()
      errors = []
      page.on("pageerror", lambda error: errors.append(str(error)))
      page.goto(target.as_uri(), wait_until="load")
      page.wait_for_function("() => document.querySelector('.slide.on')", timeout=5000)
      shown, drawn = [], {}
      for step in range(steps):
        if step:
          page.keyboard.press("PageDown")
        page.wait_for_timeout(20)
        slide = page.evaluate("() => document.querySelector('.slide.on').id")
        if not shown or shown[-1] != slide:
          shown.append(slide)
        now = page.evaluate(offline.DRAWN)
        drawn[slide] = [a or b for a, b in zip(drawn[slide], now)] if slide in drawn else now
      assert shown == slides
      assert [slide for slide, each in drawn.items() if not all(each)] == []
      assert "this-platform" in drawn and drawn["this-platform"] == [True]
      assert left == [] and errors == []
    finally:
      browser.close()
