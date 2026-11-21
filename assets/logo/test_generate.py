"""docs/assets/logo/generate writes the login theme's honeycomb and favicon (#598)."""
import importlib.machinery
import importlib.util
from pathlib import Path

from PIL import Image

loader = importlib.machinery.SourceFileLoader("generate", str(Path(__file__).with_name("generate")))
spec = importlib.util.spec_from_loader("generate", loader)
generate = importlib.util.module_from_spec(spec)
loader.exec_module(generate)


def run(tmp_path: Path) -> tuple[Path, Path]:
  theme = tmp_path / "theme"
  generate.main(["--output-dir", str(tmp_path), "--theme-dir", str(theme)])
  return tmp_path, theme


def test_the_favicon_is_an_ico_of_16_32_and_48_px(tmp_path):
  output, theme = run(tmp_path)
  with Image.open(output / "favicon-honeycomb.ico") as ico:
    assert ico.format == "ICO"
    assert ico.info["sizes"] == {(16, 16), (32, 32), (48, 48)}
  assert (theme / "favicon.ico").read_bytes() == (output / "favicon-honeycomb.ico").read_bytes()


def test_the_favicon_keeps_its_transparency_and_is_not_a_dot(tmp_path):
  output, _ = run(tmp_path)
  with Image.open(output / "favicon-honeycomb.ico") as ico:
    ico.size = (16, 16)
    image = ico.convert("RGBA")
  alpha = image.getchannel("A")
  assert alpha.getextrema() == (0, 255)
  left, top, right, bottom = alpha.getbbox()
  assert right - left >= 14


def test_the_mark_has_no_background(tmp_path):
  output, theme = run(tmp_path)
  mark = (output / "honeycomb-mark.svg").read_text()
  assert "<rect" not in mark
  assert 'fill="#fff"' in mark
  assert 'viewBox="0 0 512 512"' not in mark
  assert (theme / "honeycomb.svg").read_text() == mark
