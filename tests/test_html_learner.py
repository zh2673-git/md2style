from pathlib import Path

from md2style.engines.learner import Learner
from md2style.engines import StyleEngine


HTML = """<!DOCTYPE html>
<html><head><style>
:root {
  --accent: #0A84FF;
  --divider: #E5E7EB;
}
body { font-family: -apple-system, sans-serif; font-size: 16px; color: #1D1D1F; line-height: 1.6; }
h1 { font-size: 32px; color: #1D1D1F; font-family: -apple-system, sans-serif; }
h2 { font-size: 26px; color: #1D1D1F; }
</style></head>
<body><h1>标题</h1><h2>副标题</h2><p>正文</p></body></html>"""


def test_learn_html_and_reuse(tmp_path):
    tpl = tmp_path / "tpl.html"
    tpl.write_text(HTML, encoding="utf-8")

    styles_dir = tmp_path / "styles"
    styles_dir.mkdir()
    yaml_path = Learner(styles_dir).learn(str(tpl), "my_html")

    se = StyleEngine(styles_dir)
    final = se.resolve("my_html", {})
    assert final["headings"]["h1"]["size"] == 32
    assert final["headings"]["h1"]["font"].startswith("-apple-system")
    assert final["accent_color"] == "#0A84FF"   # CSS 变量被提取
    assert final["divider_color"] == "#E5E7EB"
