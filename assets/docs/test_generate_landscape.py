"""docs/assets/docs/generate-landscape draws landscape.svg, and the committed file is its output (#1490)."""
import importlib.machinery
import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).parent
loader = importlib.machinery.SourceFileLoader("generate_landscape", str(HERE / "generate-landscape"))
spec = importlib.util.spec_from_loader("generate_landscape", loader)
generate = importlib.util.module_from_spec(spec)
loader.exec_module(generate)


def test_the_committed_svg_is_the_generator_output():
  assert (HERE / "landscape.svg").read_text() == generate.draw(), "run docs/assets/docs/generate-landscape and commit landscape.svg"


def test_the_main_writes_the_output_file(tmp_path):
  output = tmp_path / "landscape.svg"
  generate.main(["--output", str(output)])
  assert output.read_text() == generate.draw()


def test_every_plane_and_capability_sits_under_planes():
  parts = re.findall(r'<g data-part="([\w.-]+)">', generate.draw())
  planes = [part for part in parts if part.split(".")[0].split("-")[0] in generate.PLANES]
  assert planes == [], f"outside planes.: {planes}"
  assert [p for p in parts if p.startswith("planes.") and p.endswith("-plane")] == [f"planes.{key}-plane" for key in generate.PLANES]
  assert sum(p.startswith("planes.") for p in parts) == len(generate.PLANES) + sum(len(caps) for caps in generate.CAPS.values())
  assert {"api", "clients.1", "clients.2", "clients.3", "clients.4"} <= set(parts)
