"""The deck outline's JSON Schema (#1700): every deck of the repository validates against it, and the schema and the
renderer's own validation agree on what they refuse, so an editor that reads `$schema` flags what the import would."""
import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
SCHEMAS = ROOT / "cli/src/nereus/schemas/presentations/outline"
SCHEMA = SCHEMAS / "1.json"


def load(name, path):
  loader = importlib.machinery.SourceFileLoader(name, str(path))
  module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
  loader.exec_module(module)
  return module


ro = load("render_outline_schema", HERE / "render-outline")
VALIDATORS = {version: jsonschema.Draft202012Validator(json.loads((SCHEMAS / f"{version}.json").read_text())) for version in (1, 2)}
validator = VALIDATORS[1]


def decks():
  for path in sorted(ROOT.glob("docs/**/*.yaml")):
    outline = yaml.safe_load(path.read_text())
    if isinstance(outline, dict) and "slides" in outline:
      yield path


MINIMAL = {
  "$schema": "https://getnereus.dev/schemas/presentations/outline/1.json",
  "outlineVersion": 1,
  "deck": {"name": "sample", "title": "A sample", "pt": {"title": "Um exemplo"}},
  "acts": [{"name": "one", "title": "One", "pt": {"title": "Um"}}],
  "slides": [{"name": "hello", "act": "one", "message": "A deck checked before the import",
              "pt": {"message": "Um deck verificado antes do import"}}],
}


def changed(change):
  outline = copy.deepcopy(MINIMAL)
  change(outline)
  return outline


BROKEN = {
  "an unknown top field": lambda o: o.update(theme="dark"),
  "an unknown slide field": lambda o: o["slides"][0].update(colour="red"),
  "a message with a full stop": lambda o: o["slides"][0].update(message="It ends here."),
  "an unknown status": lambda o: o["slides"][0].update(status="done", issue=1),
  "outlineVersion 3": lambda o: o.update(outlineVersion=3),
  "outlineVersion true": lambda o: o.update(outlineVersion=True),
  "a reference with no http url": lambda o: (o.update(references=[{"name": "r", "title": "R", "url": "ftp://example.com"}]),
                                             o["slides"][0].update(refs=["r"])),
  "a short option in a terminal": lambda o: o["slides"][0].update(terminal={"steps": [{"run": "nereus get", "options": ["-o yaml"]}]}),
  "a detail with no tip": lambda o: o["slides"][0].update(diagram="d.svg", details={"p": {"title": "T", "body": "B"}},
                                                          pt={"details": {"p": {"title": "T", "tip": "t", "body": "B"}}}),
}


def schema_errors(outline):
  """What the schema of the outline's own version refuses; a version no schema has falls to version 1's."""
  return [error.message for error in VALIDATORS.get(outline.get("outlineVersion"), validator).iter_errors(outline)]


@pytest.mark.parametrize("version", [1, 2])
def test_the_schema_is_a_valid_draft_2020_12_schema(version):
  jsonschema.Draft202012Validator.check_schema(json.loads((SCHEMAS / f"{version}.json").read_text()))


def test_version_2_is_version_1_with_a_slide_s_poll():
  one, two = (json.loads((SCHEMAS / f"{version}.json").read_text()) for version in (1, 2))
  assert two["required"] == ["outlineVersion", *one["required"]]
  assert set(two["$defs"]) - set(one["$defs"]) == {"poll"}
  assert set(two["$defs"]["slide"]["properties"]) - set(one["$defs"]["slide"]["properties"]) == {"poll"}
  for key in ("$id", "title", "required", "properties", "$defs"):
    one.pop(key), two.pop(key)
  assert one == two


@pytest.mark.parametrize("path", list(decks()), ids=lambda path: str(path.relative_to(ROOT)))
def test_every_deck_of_the_repository_validates_against_the_schema(path):
  assert schema_errors(yaml.safe_load(path.read_text())) == []


def test_the_storytelling_deck_names_the_schema_by_a_path_that_exists():
  outline = yaml.safe_load((HERE / "storytelling.yaml").read_text())
  assert (HERE / outline["$schema"]).resolve() == SCHEMA
  assert outline["outlineVersion"] == 1


def test_a_deck_with_schema_and_version_passes_both():
  assert schema_errors(MINIMAL) == []
  assert ro.validate(MINIMAL) == []


@pytest.mark.parametrize("what", list(BROKEN))
def test_the_schema_and_the_renderer_refuse_the_same_broken_deck(what):
  outline = changed(BROKEN[what])
  assert schema_errors(outline), f"the schema accepts {what}"
  assert ro.validate(outline), f"the renderer accepts {what}"


# A slide's poll (#1722), outlineVersion 2.
POLLS = {
  "choice": {"kind": "choice", "question": "Which part comes next?", "choices": ["Reefs", "Nereids", "Mandates"], "seconds": 20,
             "pt": {"question": "Qual parte vem agora?", "choices": ["Reefs", "Nereids", "Mandates"]}},
  "scale": {"kind": "scale", "question": "How well do you know Kubernetes?", "scale": {"min": 1, "max": 5},
            "pt": {"question": "Quanto você conhece de Kubernetes?"}},
  "text": {"kind": "text", "question": "One word for this talk?", "pt": {"question": "Uma palavra para esta palestra?"}},
}


def polled(poll, version=2):
  outline = changed(lambda o: o.update(outlineVersion=version))
  outline["$schema"] = f"https://getnereus.dev/schemas/presentations/outline/{version}.json"
  outline["slides"].append({"name": "ask", "act": "one", "poll": copy.deepcopy(poll)})
  return outline


@pytest.mark.parametrize("kind", list(POLLS))
def test_a_poll_of_each_kind_passes_both_on_version_2(kind):
  outline = polled(POLLS[kind])
  assert schema_errors(outline) == []
  assert ro.validate(outline) == []


def poll_changed(kind, change):
  poll = copy.deepcopy(POLLS[kind])
  change(poll)
  return polled(poll)


BROKEN_POLLS = {
  "a choice with no choices": lambda: poll_changed("choice", lambda p: (p.pop("choices"), p["pt"].pop("choices"))),
  "a choice with one choice": lambda: poll_changed("choice", lambda p: p.update(choices=["Only"])),
  "choices on a scale": lambda: poll_changed("scale", lambda p: p.update(choices=["A", "B"])),
  "a scale with no scale": lambda: poll_changed("scale", lambda p: p.pop("scale")),
  "a scale on a text": lambda: poll_changed("text", lambda p: p.update(scale={"min": 1, "max": 5})),
  "an unknown kind": lambda: poll_changed("text", lambda p: p.update(kind="rating")),
  "no question": lambda: poll_changed("text", lambda p: p.pop("question")),
  "seconds under 5": lambda: poll_changed("text", lambda p: p.update(seconds=3)),
  "seconds over 300": lambda: poll_changed("text", lambda p: p.update(seconds=600)),
  "an unknown poll field": lambda: poll_changed("text", lambda p: p.update(anonymous=True)),
  "a poll on version 1": lambda: polled(POLLS["scale"], 1),
  "a poll on a slide with no name": lambda: (outline := polled(POLLS["scale"]), outline["slides"][-1].pop("name"))[0],
}


@pytest.mark.parametrize("what", list(BROKEN_POLLS))
def test_the_schema_and_the_renderer_refuse_the_same_broken_poll(what):
  outline = BROKEN_POLLS[what]()
  assert schema_errors(outline), f"the schema accepts {what}"
  try:
    refused = ro.validate(outline)
  except KeyError:
    refused = True  # A slide with no name stops the renderer before any check.
  assert refused, f"the renderer accepts {what}"


# What a schema cannot compare, the renderer checks: the scale's ends, the Portuguese texts.
RENDERER_ONLY = {
  "a scale with min equal to max": (lambda p: p.update(scale={"min": 3, "max": 3}), "scale 3-3: min must be 0 or more and below max"),
  "a scale with min over max": (lambda p: p.update(scale={"min": 5, "max": 1}), "scale 5-1: min must be 0 or more and below max"),
  "a question with no pt": (lambda p: p.pop("pt"), "ask: poll: no pt.question"),
}


@pytest.mark.parametrize("what", list(RENDERER_ONLY))
def test_the_renderer_refuses_what_the_schema_cannot_compare(what):
  change, error = RENDERER_ONLY[what]
  outline = poll_changed("scale", change)
  assert any(error in each for each in ro.validate(outline)), ro.validate(outline)


def test_the_widest_scale_is_0_to_10():
  outline = poll_changed("scale", lambda p: p.update(scale={"min": 0, "max": 10}))
  assert schema_errors(outline) == [] and ro.validate(outline) == []


def test_the_renderer_refuses_pt_choices_of_another_length_and_a_poll_with_a_list():
  outline = poll_changed("choice", lambda p: p["pt"].update(choices=["Reefs", "Nereids"]))
  assert "ask: poll: pt.choices must have 3 items" in ro.validate(outline)
  outline = polled(POLLS["text"])
  outline["slides"][-1].update(screen=["one"], pt={"screen": ["um"]})
  assert "ask: a poll slide carries no screen" in ro.validate(outline)


def test_a_poll_on_version_1_is_told_to_raise_the_version():
  assert ro.validate(polled(POLLS["scale"], 1)) == ["ask: poll needs outlineVersion 2: raise outlineVersion to 2"]
