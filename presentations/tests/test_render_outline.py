import copy
import importlib.machinery
import importlib.util
import pathlib
import html
import re

import pytest
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
loader = importlib.machinery.SourceFileLoader("render_outline", str(HERE / "render-outline"))
ro = importlib.util.module_from_spec(importlib.util.spec_from_loader("render_outline", loader))
loader.exec_module(ro)

# The decks of the repository: these, the CLI reference, one deck per reef, and the walkthroughs that link to it (#477).
OUTLINES = (sorted(HERE.glob("*.yaml")) + sorted((HERE / "idp").glob("*.yaml"))
            + sorted((HERE.parent / "specs" / "cli").rglob("*.yaml"))
            + sorted((HERE.parent / "walkthrough" / "decks").glob("*.yaml")))

SVG = '<svg><g data-part="plane"><rect/></g><g data-part="p.1"><rect/></g><g data-part="p.2"><rect/></g></svg>'


def outline():
  return copy.deepcopy({
    "deck": {"name": "t", "title": "T", "subtitle": "S", "pt": {"title": "T", "subtitle": "S pt"}},
    "acts": [{"name": "opening", "title": "Opening", "pt": {"title": "Abertura"}},
             {"name": "model", "title": "Model", "question": "Which words?", "pt": {"title": "Modelo", "question": "Que palavras?"}},
             {"name": "quiet", "title": "Quiet", "question": "Why?", "opening": False, "pt": {"title": "Calmo", "question": "Por quê?"}}],
    "references": [{"name": "brooks", "title": "The Mythical Man-Month", "url": "https://example.com/brooks", "author": "Brooks",
                    "year": 1975, "about": "A book", "pt": {"about": "Um livro"}}],
    "slides": [
      {"name": "title", "act": "opening", "cover": True, "message": "m", "notes": "n", "pt": {"message": "m", "notes": "n"}},
      {"name": "kinds", "act": "model", "topic": "Words", "message": "Three kinds", "heading": "h",
       "screen": ["**{reef:Reef}:** a capability", "**Nereid:** looks after it", "Mandate"], "refs": ["brooks"],
       "notes": "**First.** Second.\n\nSource: references/agile.md",
       "pt": {"topic": "Palavras", "message": "Três kinds", "heading": "h", "screen": ["**{reef:Reef}:** uma capacidade", "**Nereid:** cuida", "Mandate"],
              "notes": "**Primeiro.** Segundo."}},
      {"name": "run", "act": "quiet", "message": "One command", "dependsOn": ["kinds"],
       "terminal": {"steps": [
         {"comment": "Apply the reef", "run": "nereus reef apply environment",
          "output": "✓ reef/environment created\n\nNext steps:\n\n  nereus nereid apply <nereid> --reef environment"},
         {"run": "nereus nereid apply vcluster", "options": ["--reef environment", "--image example.com/vcluster:0.1.0"]},
       ]},
       "notes": "n", "pt": {"message": "Um comando", "notes": "n"}},
    ]})


def errors(changed):
  return ro.validate(changed)


# ── Validation ──────────────────────────────────────────

@pytest.mark.parametrize("source", OUTLINES, ids=lambda path: path.stem)
def test_the_committed_outlines_are_valid(source):
  assert ro.validate(yaml.safe_load(source.read_text()), source.parent) == []


def test_a_valid_outline_has_no_errors():
  assert errors(outline()) == []


def test_unknown_fields_are_refused():
  changed = outline()
  changed["slides"][0]["animation"] = "none"
  changed["parts"] = []
  assert errors(changed) == ["outline: unknown field 'parts'", "title: unknown field 'animation'"]


@pytest.mark.parametrize(("where", "field"), [(("slides", 1), "topic"), (("slides", 1), "notes"), (("acts", 1), "question"), (("references", 0), "about")])
def test_every_text_has_its_portuguese_version(where, field):
  changed = outline()
  del changed[where[0]][where[1]]["pt"][field]
  assert len(errors(changed)) == 1 and f"no pt.{field}" in errors(changed)[0]


def test_the_portuguese_screen_has_as_many_items():
  changed = outline()
  changed["slides"][1]["pt"]["screen"].pop()
  assert errors(changed) == ["kinds: pt.screen must have 3 items"]


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_a_message_never_ends_with_a_full_stop(lang):
  changed = outline()
  slide = changed["slides"][1] if lang == "en" else changed["slides"][1]["pt"]
  slide["message"] += "."
  assert errors(changed) == [f"kinds: the message ends with a full stop: '{slide['message']}'"]
  slide["message"] = slide["message"][:-1] + "?"
  assert errors(changed) == []


def test_depends_on_must_point_back():
  changed = outline()
  changed["slides"][1]["dependsOn"] = ["run"]
  changed["slides"][2]["dependsOn"] = ["gone"]
  assert errors(changed) == ["kinds: dependsOn 'run', which comes later", "run: dependsOn unknown slide 'gone'"]


@pytest.mark.parametrize(("step", "error"), [
  ({"run": "nereus reef apply environment --dry-run"}, "options go in `options`"),
  ({"run": "nereus reef apply environment", "options": ["-y"]}, "'-y' is not a long option"),
  ({"run": "nereus reef apply environment", "output": "done\nNext steps:\n\n  nereus reef list"}, "'Next steps:' needs a blank line before and after"),
  ({"run": "nereus reef apply environment", "output": "done\n\nNext steps:\n  nereus reef list"}, "'Next steps:' needs a blank line before and after"),
  ({"comment": "nothing to run"}, "no run"),
])
def test_terminals_follow_the_format_of_today(step, error):
  changed = outline()
  changed["slides"][2]["terminal"]["steps"] = [step]
  assert len(errors(changed)) == 1 and error in errors(changed)[0]


def test_references_are_cited_and_have_a_url():
  changed = outline()
  changed["slides"][1]["refs"] = ["gone"]
  changed["references"].append({"name": "brooks", "title": "", "url": "ftp://example.com"})
  assert errors(changed) == [
    "reference 'brooks': defined twice", "reference 'brooks': no title", "reference 'brooks': url must be http(s)",
    "kinds: refs unknown reference 'gone'", "reference 'brooks': no slide cites it", "reference 'brooks': no slide cites it"]


def test_diagram_parts_must_be_in_the_svg(tmp_path):
  (tmp_path / "d.svg").write_text(SVG)
  changed = outline()
  changed["slides"][1].update(diagram="d.svg", show=["plane", "p"], reveal=["q"])
  assert ro.validate(changed, tmp_path) == ["kinds: part 'q' is not in d.svg"]
  del changed["slides"][1]["diagram"]
  assert "kinds: show/dim/reveal without diagram" in ro.validate(changed, tmp_path)


def test_a_diagram_that_names_none_of_its_parts_is_refused(tmp_path):
  """Every part the slide does not name is hidden: with none named, the slide would show an empty frame (#1706)."""
  (tmp_path / "d.svg").write_text(SVG)
  changed = outline()
  changed["slides"][1].update(diagram="d.svg")
  assert ro.validate(changed, tmp_path) == ["kinds: d.svg shows none of its parts: name them in show, dim or reveal"]


def test_a_moved_code_file_breaks_the_deck(tmp_path):
  changed = outline()
  changed["slides"][1]["code"] = {"file": "gone.yaml"}
  assert ro.validate(changed, tmp_path) == ["kinds: code file 'gone.yaml' not found"]


# ── A code frame or a terminal per language (#1457) ─────

def per_language(tmp_path):
  (tmp_path / "hypothesis.md").write_text("We believe that\n")
  (tmp_path / "hipotese.md").write_text("Acreditamos que\n")
  changed = outline()
  changed["slides"][1]["code"] = {"file": "hypothesis.md"}
  changed["slides"][1]["pt"]["code"] = {"file": "hipotese.md"}
  changed["slides"][2]["pt"]["terminal"] = {"steps": [{"comment": "Aplique o reef", "run": "nereus reef apply environment",
                                                       "output": "{dim:reef/environment} criado"}]}
  return changed


def test_a_slide_may_have_its_own_code_frame_and_terminal_in_portuguese(tmp_path):
  changed = per_language(tmp_path)
  assert ro.validate(changed, tmp_path) == []
  page = ro.render_html(changed, tmp_path)
  kinds = page.split("id='kinds-2'")[1].split(">", 1)[1].split("</section>")[0]
  assert re.search(r"<div lang='en'><div class='code'>.*hypothesis\.md.*We believe that.*</div><div lang='pt'><div class='code'>.*hipotese\.md.*Acreditamos que", kinds)
  run = page.split("id='run'")[1].split(">", 1)[1].split("</section>")[0]
  assert "<div lang='en'><div class='term'" in run and "<div lang='pt'><div class='term'" in run
  assert "Apply the reef" in run and "Aplique o reef" in run


def test_a_slide_without_a_portuguese_frame_shares_one_for_both_languages(page):
  run = page.split("id='run'")[1].split(">", 1)[1].split("</section>")[0]
  assert run.count("<div class='term'") == 1 and "<div lang='en'><div class='term'" not in run


def test_a_portuguese_frame_is_checked_like_the_english_one(tmp_path):
  changed = per_language(tmp_path)
  changed["slides"][1]["pt"]["code"] = {"file": "gone.md"}
  changed["slides"][2]["pt"]["terminal"] = {"steps": []}
  del changed["slides"][2]["terminal"]
  assert ro.validate(changed, tmp_path) == ["kinds: code file 'gone.md' not found", "run: pt.terminal without terminal",
                                            "run: pt.terminal: terminal with no steps"]


def test_a_slide_may_have_its_own_diagram_in_portuguese_with_the_same_parts(tmp_path):
  (tmp_path / "d.svg").write_text(SVG.replace("<rect/>", "<text>plane</text>", 1))
  (tmp_path / "d-pt.svg").write_text(SVG.replace("<rect/>", "<text>plano</text>", 1).replace('"p.2"', '"q.2"'))
  changed = outline()
  changed["slides"][1].update(diagram="d.svg", show=["plane", "p"])
  changed["slides"][1]["pt"]["diagram"] = "d-pt.svg"
  assert ro.validate(changed, tmp_path) == []
  diagram = ro.render_html(changed, tmp_path).split("id='kinds-2'")[1].split(">", 1)[1].split("</section>")[0]
  assert re.search(r"<div lang='en'><div class='diagram'.*plane.*</div><div lang='pt'><div class='diagram'.*plano", diagram)
  changed["slides"][1]["show"] = ["plane", "p.2"]
  assert ro.validate(changed, tmp_path) == ["kinds: part 'p.2' is not in d-pt.svg"]


def test_the_terminal_steps_only_through_the_language_on_screen():
  assert "for (const t of $$('.term', s).filter(inLang)) if (termStep(t))" in ro.SCRIPT
  assert "for (const d of $$('.diagram', s).filter(inLang)) if (revealPart(d))" in ro.SCRIPT


# ── The terminal ────────────────────────────────────────

def text(markup):
  return re.sub(r"<[^>]+>", "", markup).replace("&lt;", "<").replace("&gt;", ">")


def test_a_command_puts_one_long_option_per_line_two_spaces_from_nereus():
  lines = re.findall(r"<span class='ln'>(.*?)</span>(?=<span class='ln'>|$)", ro.command_lines("nereus nereid apply vcluster", ["--reef environment", "--image example.com/v:1"]))
  assert [text(line) for line in lines] == ["$ nereus nereid apply vcluster \\", "    --reef environment \\", "    --image example.com/v:1"]


def test_a_command_with_no_options_has_no_continuation():
  assert text(ro.command_lines("nereus status", [])) == "$ nereus status"


def test_concepts_keep_their_colour_in_the_terminal():
  markup = ro.command_lines("nereus nereid apply vcluster", ["--reef environment", "--image example.com/v:1"])
  assert "<span class='cx-nereid'>nereid</span>" in markup and "<span class='cx-nereid'>vcluster</span>" in markup
  assert "<span class='cx-reef'>environment</span>" in markup
  assert "<span class='t-val'>example.com/v:1</span>" in markup
  assert "<span class='t-grp'>release</span>" in ro.command_lines("nereus release repo list", [])


def test_output_lines_are_coloured_by_what_they_say():
  assert "t-ok" in ro.output_line("✓ reef/environment created")
  assert "t-bad" in ro.output_line("✗ reef environment does not exist.")
  assert "t-label" in ro.output_line("Next steps:")
  assert ro.output_line("") == "<span class='ln wrap'> </span>"


def test_an_output_line_colours_concepts_marks_and_dimmed_runs_inline():
  # The comparator's table (#1455): Nereid names purple, ✓ green, ✗ red, a lone ~ amber, the target column dimmed.
  line = ro.output_line("p95 latency  {dim:< 300ms}  {nereid:keycloak} ✓  {nereid:auth0} ✗  ~")
  assert line == ("<span class='ln wrap'>p95 latency  <span class='t-c'>&lt; 300ms</span>  <span class='cx-nereid'>keycloak</span> "
                  "<span class='t-ok'>✓</span>  <span class='cx-nereid'>auth0</span> <span class='t-bad'>✗</span>  "
                  "<span class='t-val'>~</span></span>")


def test_a_tilde_in_a_path_stays_plain_and_a_whole_line_keeps_its_colour():
  assert ro.output_line("saved to ~/example/deck.html") == "<span class='ln wrap'>saved to ~/example/deck.html</span>"
  assert ro.output_line("✓ {reef:reef}/environment created ✓") == (
    "<span class='ln wrap'><span class='t-ok'>✓ <span class='cx-reef'>reef</span>/environment created ✓</span></span>")


def test_dim_markup_lives_only_in_a_terminal_output():
  changed = outline()
  changed["slides"][1]["message"] = "Three {dim:kinds}"
  assert "kinds: {dim:...} is only for a terminal's output" in errors(changed)
  changed = outline()
  changed["slides"][2]["terminal"]["steps"][0]["output"] = "{dim:scope:} login"
  assert not errors(changed)


def test_the_copy_button_carries_the_output_as_shown_never_its_markup():
  changed = outline()["slides"][2]["terminal"]
  changed["steps"][0]["output"] = "{dim:scope} {nereid:auth0} ✓"
  copy = html.unescape(re.search(r"data-copy='([^']*)'", ro.render_terminal(changed)).group(1))
  assert "\nscope auth0 ✓\n" in copy and "{" not in copy


def test_a_stepwise_output_is_revealed_one_line_per_step():
  # The comparator's table (#1456): each step shows one more line; a blank line goes with the line after it.
  changed = outline()["slides"][2]["terminal"]
  changed["steps"][0]["stepwise"] = True
  markup = ro.render_terminal(changed)
  assert markup.count("<span class='grp out' data-stepwise='1'>") == 1 and markup.count("<span class='grp out'>") == 0
  assert "case 'lines': t._u++; outputLine(t); return true;" in ro.SCRIPT
  assert "if (g.dataset.stepwise) { t._phase = 'lines';" in ro.SCRIPT
  assert "if (l.textContent.trim()) break;" in ro.SCRIPT
  assert "if (t._lines.slice(t._k).every(l => !l.textContent.trim())) {" in ro.SCRIPT


def test_stepwise_is_a_boolean_on_a_step_with_output():
  changed = outline()
  changed["slides"][2]["terminal"]["steps"][1]["stepwise"] = True
  assert "run: terminal step 2: stepwise with no output" in errors(changed)
  changed = outline()
  changed["slides"][2]["terminal"]["steps"][0]["stepwise"] = "yes"
  assert "run: terminal step 1: stepwise is true or false" in errors(changed)


def test_commands_are_typed_and_outputs_shown_with_a_blank_line_between():
  markup = ro.render_terminal(outline()["slides"][2]["terminal"])
  groups = re.findall(r"<span class='grp (cmd|out)'>", markup)
  assert groups == ["cmd", "out", "cmd"]
  first_output = markup.split("<span class='grp out'>")[1].split("<span class='grp cmd'>")[0]
  assert first_output.endswith("<span class='ln wrap'> </span></span>")
  assert "<span class='t-c'># Apply the reef</span>" in markup
  assert "<div class='bar'><span class='dots'><i></i><i></i><i></i></span><span class='cwd'>~/example</span><span class='tt'>" in markup



def test_every_terminal_has_a_folded_toolbar_whose_copy_takes_the_whole_terminal():
  markup = ro.render_terminal(outline()["slides"][2]["terminal"])
  bar = re.search(r"<div class='bar'>(.*?)</div>", markup, re.S).group(1)
  tools = re.search(r"<span class='tt'>(.*)</span>$", bar, re.S).group(1)
  acts = re.findall(r"data-act='(\w+)'", tools)
  assert acts == ["copy", "smaller", "larger", "narrow", "wide", "more"]
  assert "<button type='button' class='more' data-act='more' data-w='termMore' aria-expanded='false'" in tools
  copy = html.unescape(re.search(r"data-act='copy'[^>]*data-copy='([^']*)'", tools).group(1))
  steps = outline()["slides"][2]["terminal"]["steps"]
  assert copy == ro.terminal_text(steps)
  assert copy.startswith("# Apply the reef\n$ nereus reef apply environment\n")
  assert "$ nereus nereid apply vcluster \\\n    --reef environment \\\n    --image example.com/vcluster:0.1.0" in copy
  assert "class='cp'" not in markup
  assert all(word in ro.WORDS[lang] for word in ro.TERM_TOOLS_WORDS for lang in ro.LANGS)


def test_the_whole_terminal_text_has_comments_prompts_options_and_output_a_blank_line_between_steps():
  steps = [{"comment": "First", "run": "nereus core reefs list", "output": "NAME  \ncore\n"},
           {"run": "nereus environment environments create demo", "options": ["--mandate vcluster"]}]
  assert ro.terminal_text(steps) == ("# First\n$ nereus core reefs list\nNAME\ncore\n\n"
                                     "$ nereus environment environments create demo \\\n    --mandate vcluster")


# ── Slides ──────────────────────────────────────────────

@pytest.fixture
def page():
  return ro.render_html(outline(), HERE)


def slide(page, name):
  return re.search(rf"<section class='slide[^']*' id='{name}'[^>]*>(.*?)</section>", page, re.S).group(1)


def test_every_slide_has_both_languages(page):
  sections = re.findall(r"<section class='slide[^']*' id='[^']+'[^>]*>(.*?)</section>", page, re.S)
  assert sections and all("<div lang='en'>" in body and "<div lang='pt'>" in body for body in sections)


def test_the_cover_shows_the_title_then_reveals_the_subtitle(page):
  assert "<section class='slide cover' id='title' data-units='1'>" in page
  cover = slide(page, "title")
  assert "<h1>T</h1><p class='st sub'>S</p>" in cover and "<p class='st sub'>S pt</p>" in cover


def test_a_subtitle_appears_after_the_title_as_its_own_step(page):
  assert "<h2>Three kinds</h2><p class='lead st'>h</p>" in slide(page, "kinds")


def test_animations_none_shows_the_subtitle_at_once():
  changed = outline()
  changed["slides"][1]["animations"] = "none"
  assert "<p class='lead'>h</p>" in slide(ro.render_html(changed, HERE), "kinds")


def test_a_subtitle_stays_at_full_colour_when_the_next_step_comes():
  assert ".lead.st.on" in ro.CSS


def test_an_act_with_a_question_opens_with_it_unless_opening_is_false(page):
  assert "<div class='kicker'>Model</div><h2>Which words?</h2>" in slide(page, "act-model")
  assert "id='act-quiet'" not in page


def test_a_list_that_fits_stays_on_one_slide(page):
  assert "id='kinds-2'" not in page and slide(page, "kinds").count("<li class='st'>") == 6
  assert "Model · Words · 1/2" not in page


def test_a_list_that_does_not_fit_continues_on_the_next_slide_with_the_same_message():
  changed = outline()
  long_items = [f"**Item {n}:** " + "a long line that wraps on a phone " * 4 for n in range(8)]
  changed["slides"][1]["screen"] = long_items
  changed["slides"][1]["pt"]["screen"] = long_items
  page = ro.render_html(changed, HERE)
  first, second = slide(page, "kinds"), slide(page, "kinds-2")
  assert "Model · Words · 1/" in first and "Modelo · Palavras · 2/" in second
  assert "<h2>Three kinds</h2>" in second


def test_a_slide_with_a_terminal_keeps_at_most_two_items():
  parts = ro.slide_parts({"message": "m", "screen": ["a", "b", "c"], "terminal": {"steps": []}})
  assert [(start, end) for _, _, start, end in parts] == [(0, 2), (2, 4)]


# ── A diagram measured by its viewBox (#1458) ───────────

def test_a_diagram_keeps_the_items_that_fit_under_it_on_a_phone(tmp_path):
  (tmp_path / "wide.svg").write_text('<svg viewBox="0 0 800 200"><g data-part="a"/></svg>')
  slide = {"name": "loop", "message": "m", "diagram": "wide.svg", "screen": ["**raw:** files", "**order:** a work order", "**agent:** claims it",
                                                                      "**PR:** reviewable code", "**handoff:** the next session"]}
  assert [(start, end) for _, _, start, end in ro.slide_parts(slide, tmp_path)] == [(0, 5)]


def test_a_tall_diagram_sends_the_items_that_do_not_fit_to_the_next_part(tmp_path):
  (tmp_path / "tall.svg").write_text('<svg viewBox="0 0 400 300"><g data-part="a"/></svg>')
  slide = {"name": "loop", "message": "m", "diagram": "tall.svg", "screen": ["a", "b", "c", "d", "e"]}
  parts = ro.slide_parts(slide, tmp_path)
  # The diagram is drawn on the last part only: the items before it fill the screen, the last part keeps room for it.
  assert [(start, end) for _, _, start, end in parts] == [(0, 2), (2, 5)]
  assert "loop-2" in ro.slide_names({"slides": [{**slide, "act": "a"}]}, tmp_path)


def test_a_diagram_without_a_viewbox_keeps_at_most_two_items(tmp_path):
  (tmp_path / "d.svg").write_text(SVG)
  parts = ro.slide_parts({"message": "m", "diagram": "d.svg", "screen": ["a", "b", "c"]}, tmp_path)
  assert [(start, end) for _, _, start, end in parts] == [(0, 2), (2, 4)]


# ── The roles of the work, one colour each (#1458) ──────

@pytest.mark.parametrize("role", ["order", "pr", "agent", "raw", "human", "handoff"])
def test_a_role_takes_its_colour_on_a_slide_and_in_both_themes(role):
  assert ro.inline(f"**{{{role}:it}}**") == f"<b><span class='cx-{role}'>it</span></b>"
  assert f".cx-{role} {{ color: var(--cx-{role}); }}" in ro.CSS and f"--cx-{role}: " in ro.CSS


def test_screen_items_are_a_plain_list_with_bold_labels_revealed_in_turn(page):
  first = slide(page, "kinds")
  assert "<div class='kicker'>Model · Words</div><h2>Three kinds</h2><p class='lead st'>h</p><ul class='steps plain'>" in first
  assert "<li class='st'><b><span class='cx-reef'>Reef</span>:</b> a capability</li>" in first


def test_animations_none_shows_every_item_at_once():
  changed = outline()
  changed["slides"][1]["animations"] = "none"
  first = slide(ro.render_html(changed, HERE), "kinds")
  assert "<li class='st'>" not in first and "<li><b><span class='cx-reef'>Reef</span>:</b> a capability</li>" in first


def test_the_source_sits_at_the_bottom_in_each_language():
  changed = outline()
  changed["slides"][1]["source"] = "Brooks, 1975"
  first = slide(ro.render_html(changed, HERE), "kinds")
  assert "<p class='src'>Source: Brooks, 1975</p>" in first and "<p class='src'>Fonte: Brooks, 1975</p>" in first


# ── The accent ──────────────────────────────────────────

def test_the_accent_puts_words_of_the_message_in_amber():
  changed = outline()
  changed["slides"][1].update(accent="kinds")
  changed["slides"][1]["pt"]["accent"] = "kinds"
  changed["deck"]["accent"] = "S"
  changed["deck"]["pt"]["accent"] = "pt"
  assert errors(changed) == []
  page = ro.render_html(changed, HERE)
  assert "<h2>Three <em>kinds</em></h2>" in slide(page, "kinds") and "<h2>Três <em>kinds</em></h2>" in slide(page, "kinds")
  assert "<p class='st sub'><em>S</em></p>" in slide(page, "title") and "<p class='st sub'>S <em>pt</em></p>" in slide(page, "title")


def test_the_accent_is_checked():
  changed = outline()
  changed["slides"][1]["accent"] = "kinds"
  assert errors(changed) == ["kinds: no pt.accent"]
  changed["slides"][1]["pt"]["accent"] = "four"
  assert errors(changed) == ["kinds: pt.accent 'four' is not in the message"]
  changed["slides"][1].update(message="Three {reef:kinds}", accent="kinds")
  changed["slides"][1]["pt"]["accent"] = "kinds"
  assert errors(changed) == ["kinds: accent 'kinds' cuts through the markup of the message"]
  changed["slides"][0].update(accent="m")
  changed["slides"][0]["pt"]["accent"] = "m"
  assert "title: a cover shows the deck's title and subtitle: its accent goes in deck.accent" in errors(changed)
  changed = outline()
  changed["deck"]["accent"] = "Z"
  changed["deck"]["pt"]["accent"] = "Z"
  assert errors(changed) == ["deck: accent 'Z' is not in the subtitle", "deck: pt.accent 'Z' is not in the subtitle"]


def test_notes_are_rendered_per_language_with_links_to_the_sources(page):
  notes = re.search(r"<template data-notes='en'>(.*?)</template>", slide(page, "kinds"), re.S).group(1)
  assert notes.startswith("<p><strong>First.</strong> Second.</p>")
  assert "<a href='references/agile.md' target='_blank'>references/agile.md</a>" in notes
  assert "<a href='#ref-brooks' data-go='ref-brooks'>The Mythical Man-Month</a>" in notes
  assert "<strong>Primeiro.</strong>" in slide(page, "kinds")


def test_a_url_in_inline_code_stays_code_and_is_never_a_link():
  notes = ro.linkify("sends it to `http://triton.example.svc:8080`, and `cloudflared` runs; see https://example.com/docs.", HERE, HERE)
  assert notes == ("<p>sends it to <code>http://triton.example.svc:8080</code>, and <code>cloudflared</code> runs; "
                   "see <a href='https://example.com/docs' target='_blank'>https://example.com/docs</a>.</p>")


def test_the_references_are_a_deck_of_their_own(page):
  main, refs = page.split('<div data-deck="main">')[1].split('<div data-deck="refs">')
  assert "id='kinds'" in main and "id='references'" not in main
  assert "id='references'" in refs and "id='ref-brooks'" in refs
  assert 'id="refsBtn"' in page


def test_each_reference_gets_a_slide_with_its_qr_code_and_link(page):
  ref = slide(page, "ref-brooks")
  assert "<button type='button' class='qb' data-u='https://example.com/brooks' aria-label='QR code'><svg" in ref
  assert "<a href='https://example.com/brooks' target='_blank' rel='noopener'>https://example.com/brooks</a>" in ref
  assert "<p class='lead'>Brooks · 1975</p>" in ref and "<li><b>Sobre:</b> Um livro</li>" in ref
  listing = slide(page, "references")
  assert "data-go='ref-brooks'" in listing and "class='qb' data-u='https://example.com/brooks' aria-label='QR code'></button>" in listing


def test_the_qr_code_opens_in_an_overlay_with_a_clickable_link(page):
  assert '<div class="qv" id="qv" role="dialog"' in page and '<a class="qu" id="qvu" target="_blank" rel="noopener"></a>' in page
  assert "function openQR(u)" in ro.SCRIPT and "a.href = u;" in ro.SCRIPT
  assert "if (e.target === e.currentTarget) closeQR();" in ro.SCRIPT


def test_a_part_details_are_checked_and_rendered_in_both_languages(tmp_path):
  (tmp_path / "d.svg").write_text(SVG)
  detail = {"title": "T", "tip": "It's a tip", "body": "B"}
  changed = outline()
  changed["slides"][1].update(diagram="d.svg", show=["plane", "p"], details={"p.1": detail, "q": detail})
  changed["slides"][1]["pt"]["details"] = {"p.1": {"title": "T"}}
  errors = ro.validate(changed, tmp_path)
  assert "kinds: details of 'q', which is not in d.svg" in errors
  assert "kinds: details of 'q' in one language only" in errors
  assert "kinds: details of 'p.1' (pt) with no tip" in errors
  slide = {"diagram": "d.svg", "show": ["plane", "p"], "details": {"p.1": detail}, "pt": {"details": {"p.1": detail}}}
  markup = ro.render_diagram(slide, tmp_path)
  assert "data-detail='p.1' data-lang='en' data-tip='It&#x27;s a tip'" in markup
  assert "data-detail='p.1' data-lang='pt'" in markup


def test_a_diagram_hides_what_it_reveals_later(tmp_path):
  (tmp_path / "d.svg").write_text(SVG)
  markup = ro.render_diagram({"diagram": "d.svg", "show": ["plane"], "dim": [], "reveal": ["p"]}, tmp_path)
  assert '<g data-part="plane">' in markup and '<g data-part="p.1">' in markup
  assert "data-reveal='[&quot;p&quot;]'" in markup
  markup = ro.render_diagram({"diagram": "d.svg", "show": ["plane"], "dim": ["p"]}, tmp_path)
  assert '<g data-part="p.1" class="part-dim">' in markup


# ── The page ────────────────────────────────────────────

def test_the_page_is_self_contained(page):
  assert not re.search(r"<(script|link|img)[^>]+(src|href)=", page)
  assert "@import" not in page and "url(" not in ro.CSS


def test_colours_are_tokens_with_both_themes_and_the_toggle():
  assert ':root:not([data-theme="dark"])' in ro.CSS and ':root[data-theme="light"]' in ro.CSS
  for concept, colour in ro.CONCEPTS.items():
    assert f"--cx-{concept}: {colour};" in ro.CSS


def test_storage_is_only_a_convenience():
  assert ro.SCRIPT.count("localStorage") == 2
  assert "try { return localStorage.getItem(k); } catch (e) { return null; }" in ro.SCRIPT


def test_the_keys_of_the_deck():
  for key in ("'ArrowDown', 'Enter', ' ', 'PageDown'", "k === 'ArrowUp'", "'ArrowLeft', 'PageUp'", "k === 'ArrowRight'", "k === 'Home'",
              "k === 'n'", "k === 'l'", "k === 'r'", "k === 'c'", "k === 'd'", "k === '+'", "k === '-'", "k === 'Escape'"):
    assert key in ro.SCRIPT


def test_back_at_the_start_of_a_slide_goes_to_the_previous_one():
  assert "if (atStart(s)) { go(-1); return; }" in ro.SCRIPT


def test_the_bar_the_navigation_pad_and_the_toggles(page):
  for button in ("homeBtn", "prevBtn", "zoomOut", "zoomIn", "notesBtn", "refsBtn", "nextBtn", "joyUp", "joyDown", "joyLeft", "joyRight",
                 "langBtn", "themeBtn"):
    assert f'id="{button}"' in page and f"on('#{button}'" in ro.SCRIPT
  assert '<button type="button" class="pill" id="langBtn" title="PT/EN (L)"><span data-l="en">EN</span>|<span data-l="pt">PT</span></button>' in page
  assert 'html[data-lang="pt"] #langBtn [data-l="pt"]' in ro.CSS


def test_the_theme_button_swaps_what_is_on_screen_without_storage():
  assert "setTheme(shown() === 'dark' ? 'light' : 'dark')" in ro.SCRIPT


def test_the_previous_step_dims_and_a_click_outside_closes_the_notes():
  assert ".st.on:not(.cur) { opacity: .42; }" in ro.CSS
  assert "!np.contains(e.target) && !e.target.closest('#notesBtn, #qv')) toggleNotes(false)" in ro.SCRIPT


def test_reduced_motion_turns_off_the_animations():
  assert "@media (prefers-reduced-motion: reduce) { .caret, .key, .ln.fresh, .term .tt.open > button { animation: none; } .st, .joy, nav.bar button { transition: none; } }" in ro.CSS


# ── The committed decks match their outlines (#340) ─────

@pytest.mark.parametrize("source", OUTLINES, ids=lambda path: path.stem)
def test_the_committed_deck_matches_a_fresh_render(source):
  # A deck cites files by line number: a change to a cited file, without `render-outline`, leaves a stale slide.
  outline = yaml.safe_load(source.read_text())
  assert ro.render_html(outline, source.parent) == source.with_suffix(".html").read_text(), (
    f"{source.with_suffix('.html').name} is stale: run render-outline {source.name} and check its code slides")


# ── The slide index, opened from the counter (#1450) ────

def deck_ids(page, deck):
  main, refs = page.split('<div data-deck="main">')[1].split('<div data-deck="refs">')
  return re.findall(r"<section class='slide[^']*' id='([^']+)'[^>]*>", main if deck == "main" else refs.split("</main>")[0])


def index_of(page, deck):
  return re.search(rf"<ol data-ix='{deck}'[^>]*>(.*?)</ol>", page, re.S).group(1)


def test_the_counter_is_the_control_of_the_index(page):
  assert ('<button type="button" class="pill" id="num" aria-haspopup="dialog" aria-controls="ix" aria-expanded="false"'
          ' title="Index (I)"></button>') in page
  assert '<div class="ix" id="ix" role="dialog" aria-label="Index">' in page and 'id="ixx" aria-label="Close"' in page
  assert "on('#num', () => { if (!follow) toggleIndex(); })" in ro.SCRIPT and "on('#ixx', () => toggleIndex(false))" in ro.SCRIPT
  assert "k === 'i' || k === 'I'" in ro.SCRIPT
  # Esc closes the QR code, else the index, else the notes; a click outside closes it; a swipe never starts on it.
  assert "!ix.contains(e.target) && !e.target.closest('#num, #qv')) toggleIndex(false)" in ro.SCRIPT
  assert ".joy, nav, .np, .ix, .qv, pre" in ro.SCRIPT
  assert ro.WORDS["en"]["index"] == "Index" and ro.WORDS["pt"]["index"] == "Índice"


def test_the_index_lists_every_slide_of_each_deck_in_order(page):
  for deck in ("main", "refs"):
    entries = index_of(page, deck)
    ids = deck_ids(page, deck)
    assert ids and re.findall(r"<a href='#[^']+' data-go='([^']+)'>", entries) == ids
    assert re.findall(r"<span class='ixn'>(\d+)</span>", entries) == [str(n) for n in range(1, len(ids) + 1)]


def test_an_index_entry_has_its_number_label_and_message_in_both_languages(page):
  entries = index_of(page, "main")
  assert ("<li><a href='#kinds' data-go='kinds'><span class='ixn'>3</span><span class='ixt'>"
          "<span lang='en'><small>Model · Words</small>Three kinds</span>"
          "<span lang='pt'><small>Modelo · Palavras</small>Três kinds</span></span></a></li>") in entries
  assert "<span lang='en'><small>Opening</small>T</span>" in entries
  assert all("<span lang='en'>" in li and "<span lang='pt'>" in li for li in re.findall(r"<li>(.*?)</li>", entries))


def test_the_index_puts_each_act_title_above_its_slides(page):
  entries = index_of(page, "main")
  heading = "<li class='ixa'><span lang='en'>{}</span><span lang='pt'>{}</span></li>"
  assert entries.index(heading.format("Opening", "Abertura")) < entries.index("data-go='title'")
  assert entries.index(heading.format("Model", "Modelo")) < entries.index("data-go='act-model'")
  assert entries.index(heading.format("Quiet", "Calmo")) < entries.index("data-go='run'")
  assert "class='ixa'" not in index_of(page, "refs")


def test_the_index_keeps_the_accent_and_the_concept_colours():
  changed = outline()
  changed["slides"][1].update(message="Three {reef:kinds}", accent="Three")
  changed["slides"][1]["pt"].update(message="Três {reef:kinds}", accent="Três")
  entries = index_of(ro.render_html(changed, HERE), "main")
  assert "<em>Three</em> <span class='cx-reef'>kinds</span>" in entries


def test_an_entry_goes_to_its_slide_at_its_start_and_closes_the_index():
  assert "toggleNotes(false); toggleIndex(false); goTo(a.dataset.go);" in ro.SCRIPT
  assert "function goTo(id)" in ro.SCRIPT and "restart();" in ro.SCRIPT.split("function goTo(id)")[1].split("}")[2]


def test_a_slide_name_resolves_in_the_deck_on_screen_first():
  # An outline may name a slide `references`, as the reference deck's listing is: its index entry stays in its deck.
  assert "for (const k of [deck, ...Object.keys(decks).filter(k => k !== deck)])" in ro.SCRIPT


def test_the_index_marks_the_current_slide_and_opens_scrolled_to_it():
  assert "a.setAttribute('aria-current', 'true')" in ro.SCRIPT and "scrollIntoView({ block: 'center' })" in ro.SCRIPT
  assert ".ix a[aria-current]" in ro.CSS and ".ix a { display: flex;" in ro.CSS and "min-height: 44px" in ro.CSS.split(".ix a {")[1]
  assert 'html[data-lang="en"] .ix [lang="pt"], html[data-lang="pt"] .ix [lang="en"] { display: none; }' in ro.CSS


@pytest.mark.parametrize("source", OUTLINES, ids=lambda path: path.stem)
def test_every_committed_deck_lists_each_slide_in_its_index(source):
  page = ro.render_html(yaml.safe_load(source.read_text()), source.parent)
  for deck in ("main", "refs"):
    assert re.findall(r"data-go='([^']+)'><span class='ixn'>", index_of(page, deck)) == deck_ids(page, deck)


# ── A command's status in the CLI specs (#477) ──────────

def test_a_planned_command_shows_its_issue_after_the_label():
  changed = outline()
  changed["slides"][2].update(status="planned", issue=475)
  assert errors(changed) == []
  html = ro.render_html(changed, HERE)
  assert "<span class='tag planned'>planned #475</span>" in html
  assert "<span class='tag planned'>planejado #475</span>" in html


@pytest.mark.parametrize("fields, error", [
  ({"status": "done"}, "run: status must be one of built, planned, idea: 'done'"),
  ({"status": "planned"}, "run: a planned command names the issue that builds it"),
  ({"status": "idea", "issue": "475"}, "run: issue must be an issue number: '475'"),
  ({"issue": 475}, "run: issue without status"),
])
def test_a_status_is_checked(fields, error):
  changed = outline()
  changed["slides"][2].update(fields)
  assert errors(changed) == [error]


# ── Links between decks (#477) ──────────────────────────

def test_a_link_on_a_slide_is_rendered():
  assert ro.inline("[`nereus reef apply edge`](reefs/edge.html#apply-reef)") == (
    "<a href='reefs/edge.html#apply-reef'><code class='mono'>nereus reef apply edge</code></a>")


def linked(tmp_path, href):
  (tmp_path / "edge.yaml").write_text(yaml.safe_dump(outline()))
  changed = outline()
  changed["slides"][1]["screen"][2] = f"[Apply it]({href})"
  changed["slides"][1]["pt"]["screen"][2] = f"[Aplique]({href})"
  return ro.validate(changed, tmp_path)


def test_a_link_to_a_slide_of_another_deck_is_checked(tmp_path):
  assert linked(tmp_path, "edge.html#run") == []
  assert linked(tmp_path, "edge.html#act-model") == []
  assert linked(tmp_path, "edge.html#gone") == ["kinds: link to a missing slide 'edge.html#gone'"]
  assert linked(tmp_path, "other.html#run") == ["kinds: link to a missing file 'other.html#run'"]


def plain_message(text):
  return re.sub(r"<[^>]+>", "", ro.inline(text))


@pytest.mark.parametrize("name", ["nereus", "how-we-work", "storytelling"])
def test_a_title_has_at_most_sixty_characters(name):
  outline = yaml.safe_load((HERE / f"{name}.yaml").read_text())
  long_titles = [slide["name"] for slide in outline["slides"]
                 for version in (slide, slide.get("pt") or {})
                 if len(plain_message(version.get("message") or "")) > 60]
  assert long_titles == []


@pytest.mark.parametrize("name", ["nereus", "how-we-work", "storytelling"])
def test_a_title_with_two_parts_splits_into_a_title_and_a_subtitle(name):
  outline = yaml.safe_load((HERE / f"{name}.yaml").read_text())
  two_parts = [slide["name"] for slide in outline["slides"]
               for version in (slide, slide.get("pt") or {})
               if re.search(r"[;:]", plain_message(version.get("message") or "")) and not version.get("subtitle")]
  assert two_parts == []


def test_a_sub_item_is_indented_and_revealed_on_its_own():
  html_list = ro.plain_list(["**Parent:**", "- child", "- **other**"])
  assert "<li class='st'><b>Parent:</b></li><li class='st sub'>child</li><li class='st sub'><b>other</b></li>" in html_list
  assert "<li class='sub'>child</li>" in ro.plain_list(["- child"], steps=False)


@pytest.mark.parametrize("name", ["nereus", "how-we-work", "storytelling"])
def test_reef_nereid_and_mandate_are_capitalized_and_colored_on_a_slide(name):
  outline = yaml.safe_load((HERE / f"{name}.yaml").read_text())
  bare = []
  for slide in outline["slides"]:
    for version in (slide, slide.get("pt") or {}):
      texts = [version.get(field) or "" for field in ("message", "subtitle", "heading")] + list(version.get("screen") or [])
      for text in texts:
        without_markup = re.sub(r"`[^`]*`|\]\([^)]*\)|\{\w+:[^}]*\}", "", text)
        if re.search(r"\b(reefs?|nereids?|mandates?)\b", without_markup, re.I):
          bare.append(f"{slide['name']}: {text}")
  assert bare == []


def test_a_message_over_sixty_characters_is_a_warning_in_either_language_never_an_error():
  outline = {"slides": [
    {"name": "short", "message": "x" * 60, "pt": {"message": "y" * 60}},
    {"name": "long", "message": "x" * 61, "pt": {"message": "y" * 75}},
  ]}
  assert ro.fit_warnings(outline) == [
    "long: the message has 61 characters, at most 60 fit the screen",
    "long: the pt.message has 75 characters, at most 60 fit the screen",
  ]


# A slide's poll (#1722): the question and its options, still, with the data attributes a live session's screens read.
def polled():
  deck = outline()
  deck["outlineVersion"] = 2
  deck["slides"] += [
    {"name": "level", "act": "model", "poll": {"kind": "scale", "question": "How well do you know **Kubernetes**?", "scale": {"min": 1, "max": 5},
                                               "pt": {"question": "Quanto você conhece de **Kubernetes**?"}}},
    {"name": "next", "act": "model", "message": "Pick the next part", "pt": {"message": "Escolha a próxima parte"},
     "poll": {"kind": "choice", "question": "Which part comes next?", "choices": ["Reefs", "Nereids", "Mandates"], "seconds": 20,
              "pt": {"question": "Qual parte vem agora?", "choices": ["Os reefs", "Os Nereids", "Os Mandates"]}}},
    {"name": "word", "act": "model", "poll": {"kind": "text", "question": "One word?", "seconds": 45, "pt": {"question": "Uma palavra?"}}},
  ]
  assert ro.validate(deck) == []
  return deck


def poll_of(page, name):
  return page.split(f"<section class='slide' id='{name}'", 1)[1].split("</section>", 1)[0]


def test_a_poll_carries_its_name_kind_and_time_for_the_live_screens():
  page = ro.render_html(polled(), HERE)
  assert "<div class='poll' data-poll='level' data-kind='scale' data-seconds='30' data-min='1' data-max='5'>" in poll_of(page, "level")
  assert "<div class='poll' data-poll='next' data-kind='choice' data-seconds='20' data-choices='3'>" in poll_of(page, "next")
  assert "<div class='poll' data-poll='word' data-kind='text' data-seconds='45'>" in poll_of(page, "word")
  for name in ("level", "next", "word"):
    assert "<div class='pl' data-poll-live hidden><output data-poll-clock></output><output data-poll-count></output></div>" in poll_of(page, name)


def test_a_poll_shows_its_question_and_options_in_both_languages():
  page = ro.render_html(polled(), HERE)
  level, choice, word = (poll_of(page, name) for name in ("level", "next", "word"))
  assert "<p class='pq'>How well do you know <b>Kubernetes</b>?</p>" in level and "<p class='pq'>Quanto você conhece de <b>Kubernetes</b>?</p>" in level
  assert [int(value) for value in re.findall(r"<li data-option='(\d+)'><b>\1</b>", level)] == [1, 2, 3, 4, 5] * 2
  assert re.findall(r"<li data-option='\d'><b>(\w)</b><span>([^<]+)</span>", choice) == [
    ("A", "Reefs"), ("B", "Nereids"), ("C", "Mandates"), ("A", "Os reefs"), ("B", "Os Nereids"), ("C", "Os Mandates")]
  assert "20 s to answer" in choice and "20 s para responder" in choice
  assert "<p class='po text'>An answer in a few words, from each phone</p>" in word
  assert "<p class='po text'>Uma resposta em poucas palavras, de cada celular</p>" in word


def test_a_poll_slide_with_no_message_has_its_question_as_its_title_and_no_steps():
  deck = polled()
  page = ro.render_html(deck, HERE)
  assert "<h2>" not in poll_of(page, "level").split("<div class='poll'")[0]
  assert "<h2>Pick the next part</h2>" in poll_of(page, "next")
  assert all(f"<section class='slide' id='{name}' data-units='0'>" in page for name in ("level", "next", "word"))
  assert " style=" not in page.split("<body", 1)[1] and " on" + "click=" not in page
