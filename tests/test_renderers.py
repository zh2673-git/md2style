from pathlib import Path

import pytest

from md2style.engines import StyleEngine
from md2style.engines.md_parser import MdParser
from md2style.renderers import RendererDispatcher
from md2style.orchestrator import Orchestrator

SAMPLE = "# 标题一\n\n这是正文段落。\n\n```python\nprint('hi')\n```\n"


def _md(tmp_path) -> str:
    p = tmp_path / "in.md"
    p.write_text(SAMPLE, encoding="utf-8")
    return str(p)


def test_convert_docx(tmp_path):
    inp = _md(tmp_path)
    out = str(tmp_path / "o.docx")
    orch = Orchestrator(tmp_path.parent)
    # 用内置 styles 目录需指向项目根；此处验证渲染器可生成文件
    from md2style.engines import StyleEngine as SE
    se = SE(Path(__file__).resolve().parents[1] / "styles")
    ir = MdParser().to_ir(SAMPLE)
    final = se.resolve("paper", {})
    RendererDispatcher.by_suffix(out).render(ir, final, out)
    assert Path(out).exists()


def test_convert_html(tmp_path):
    inp = _md(tmp_path)
    out = str(tmp_path / "o.html")
    se = StyleEngine(Path(__file__).resolve().parents[1] / "styles")
    ir = MdParser().to_ir(SAMPLE)
    RendererDispatcher.by_suffix(out).render(ir, se.resolve("claude", {}), out)
    assert Path(out).exists()
    assert "h1" in Path(out).read_text(encoding="utf-8")


def test_whitelist_blocks_unknown():
    orch = Orchestrator(Path(__file__).resolve().parents[1])
    with pytest.raises(Exception):
        orch.run("convert", {"-i": "x", "-o": "y.docx", "--unknown-param": "1"})
