"""Html Renderer：CSS 变量注入的自包含页面生成器（数据接口执行层，第2层）。

基于 Jinja2；输出内嵌 CSS 的单一 HTML，渲染时将 final_style 注入 <style>。
代码块经 Pygments 高亮。支持 claude / mac 风格的卡片、阴影、圆角、分割线、引用块等观感。
"""

from pathlib import Path

from jinja2 import Template
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from .base import RendererBase, RendererDispatcher
from ..core.ir import IRNode, NodeType
from ..utils.color import relative_luminance


_HTML_TPL = Template(
    """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<style>
{{ pygments_css }}
:root {
  --h1-size: {{ s.headings.h1.size }}px; --h1-color: {{ s.headings.h1.color }}; --h1-font: {{ s.headings.h1.font }};
  --h2-size: {{ s.headings.h2.size }}px; --h2-color: {{ s.headings.h2.color }}; --h2-font: {{ s.headings.h2.font }};
  --h3-size: {{ s.headings.h3.size }}px; --h3-color: {{ s.headings.h3.color }}; --h3-font: {{ s.headings.h3.font }};
  --h4-size: {{ s.headings.h4.size }}px; --h4-color: {{ s.headings.h4.color }}; --h4-font: {{ s.headings.h4.font }};
  --h5-size: {{ s.headings.h5.size }}px; --h5-color: {{ s.headings.h5.color }}; --h5-font: {{ s.headings.h5.font }};
  --h6-size: {{ s.headings.h6.size }}px; --h6-color: {{ s.headings.h6.color }}; --h6-font: {{ s.headings.h6.font }};
  --body-size: {{ s.body.size }}px; --body-color: {{ s.body.color }}; --body-font: {{ s.body.font }};
  --line-height: {{ s.body.line_height }};
  --para-spacing: {{ s.body.get('para_spacing', 1.0) }}em;
  --code-bg: {{ s.code.background }}; --code-color: {{ s.code.color }};
  --divider: {{ s.get('divider_color', '#E5E7EB') }};
  --card-bg: {{ s.get('card_background', '#F5F5F7') }};
  --card-radius: {{ s.get('card_radius', 12) }}px;
  --accent: {{ s.get('accent_color', '#888') }};
}
* { box-sizing: border-box; }
body {
  font-family: var(--body-font); font-size: var(--body-size); color: var(--body-color);
  line-height: var(--line-height); max-width: 720px; margin: 56px auto; padding: 0 24px;
  -webkit-font-smoothing: antialiased;
}
.hero { font-size: calc(var(--h1-size) * 1.4); text-align: center; margin: 1.2em 0 0.8em; position: relative; padding-bottom: 0.4em; }
.hero::after { content: ""; display: block; width: 64px; height: 3px; border-radius: 2px; background: var(--accent); margin: 0.5em auto 0; }
h1 { font-size: var(--h1-size); color: var(--h1-color); font-family: var(--h1-font); font-weight: 700; letter-spacing: -0.01em; line-height: 1.25; margin: 2em 0 0.6em; }
h2 { font-size: var(--h2-size); color: var(--h2-color); font-family: var(--h2-font); font-weight: 700; line-height: 1.3; margin: 1.8em 0 0.5em; padding-bottom: 0.3em; border-bottom: 1px solid var(--divider); }
h3 { font-size: var(--h3-size); color: var(--h3-color); font-family: var(--h3-font); font-weight: 600; margin: 1.5em 0 0.4em; }
h4 { font-size: var(--h4-size); color: var(--h4-color); font-family: var(--h4-font); font-weight: 600; margin: 1.3em 0 0.4em; }
h5, h6 { font-weight: 600; margin: 1.2em 0 0.3em; }
p { margin: var(--para-spacing) 0; }
strong { font-weight: 700; color: var(--h1-color); }
em { font-style: italic; }
a { color: var(--accent); text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--accent) 40%, transparent); }
a:hover { border-bottom-color: var(--accent); }
ul, ol { margin: 1em 0; padding-left: 1.5em; }
li { margin: 0.4em 0; }
li::marker { color: var(--accent); }
hr { border: none; border-top: 1px solid var(--divider); margin: 2.5em 0; }
blockquote {
  border-left: 3px solid var(--accent); margin: 1.4em 0; padding: 0.6em 1.1em;
  background: color-mix(in srgb, var(--accent) 7%, transparent); border-radius: var(--card-radius);
  color: var(--body-color);
}
blockquote p { margin: 0.3em 0; }
code { font-family: {{ s.code.font }}, monospace; font-size: 0.88em; background: var(--code-bg); color: var(--code-color); padding: 0.15em 0.4em; border-radius: 5px; }
pre {
  background: var(--code-bg); border-radius: var(--card-radius); margin: 1.4em 0; overflow: auto;
  border: 1px solid var(--divider); box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
pre code { background: none; color: inherit; padding: 0; border-radius: 0; display: block; padding: 16px 18px; font-size: 0.85em; line-height: 1.6; }
.code-label { display: block; font-size: 0.72em; color: #888; padding: 8px 16px; border-bottom: 1px solid var(--divider); letter-spacing: 0.04em; text-transform: uppercase; background: color-mix(in srgb, var(--code-bg) 80%, #000 0%); }
.card { background: var(--card-bg); border-radius: var(--card-radius); padding: 18px 22px; margin: 1.4em 0; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
img { max-width: 100%; border-radius: var(--card-radius); margin: 1.4em 0; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.footer { margin-top: 4em; padding-top: 1.5em; border-top: 1px solid var(--divider); font-size: 0.85em; color: #888; text-align: center; }
table { border-collapse: collapse; width: 100%; margin: 1.6em 0; font-size: 0.95em; border-radius: var(--card-radius); overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
table thead { background: var(--card-bg); }
table th, table td { border: 1px solid var(--divider); padding: 10px 14px; text-align: left; }
table th { font-weight: 600; }
</style>
</head>
<body>
{{ body_html }}
</body>
</html>"""
)


class HtmlRenderer(RendererBase):
    def render(self, ir, final_style: dict, output_path: str) -> None:
        parts = []
        i = 0
        n = len(ir)
        seen_h1 = False
        while i < n:
            node = ir[i]
            if node.type in (NodeType.LIST,):
                # 连续 list 节点归并为同一列表
                items = []
                ordered = node.ordered
                while i < n and ir[i].type == NodeType.LIST and ir[i].ordered == ordered:
                    items.append(ir[i].text)
                    i += 1
                tag = "ol" if ordered else "ul"
                parts.append(f"<{tag}>" + "".join(f"<li>{_render_inline(t)}</li>" for t in items) + f"</{tag}>")
                continue
            # 首个 h1 渲染为 hero 封面
            if node.type == NodeType.HEADING and node.level == 1 and not seen_h1:
                seen_h1 = True
                parts.append(f'<h1 class="hero">{_render_inline(node.text)}</h1>')
                continue
            parts.append(self._render_node(node, final_style))
            i += 1
        footer = '<div class="footer">由 md2style 生成 · 样式可经 Web 界面微调</div>'
        body_html = "\n".join(parts) + "\n" + footer
        # 代码块配色随背景明暗自适应，避免“黑底白字太淡”
        code_bg = final_style.get("code", {}).get("background", "#F5F5F5")
        pyg_css = _pygments_css(code_bg)
        html = _HTML_TPL.render(
            title="md2style", s=final_style, body_html=body_html, pygments_css=pyg_css
        )
        Path(output_path).write_text(html, encoding="utf-8")

    def _render_node(self, node: IRNode, s: dict) -> str:
        font = node.meta.get("font")
        style_attr = f' style="font-family:{_esc(font)}"' if font else ""
        if node.type == NodeType.HEADING:
            return f"<h{node.level}{style_attr}>{_render_runs(node)}</h{node.level}>"
        if node.type == NodeType.PARAGRAPH:
            return f"<p{style_attr}>{_render_runs(node)}</p>"
        if node.type == NodeType.CODE:
            lexer = _safe_lexer(node.lang)
            code_bg = s.get("code", {}).get("background", "#F5F5F5")
            style_name = "monokai" if relative_luminance(code_bg) < 0.4 else "default"
            code = highlight(node.text.rstrip("\n"), lexer, HtmlFormatter(nowrap=True, style=style_name))
            label = node.lang or "text"
            return f'<pre><span class="code-label">{_esc(label)}</span><code>{code}</code></pre>'
        if node.type == NodeType.QUOTE:
            inner = "".join(f"<p>{_render_runs_line(line)}</p>" for line in node.text.split("\n") if line)
            return f"<blockquote>{inner}</blockquote>"
        if node.type == NodeType.HR:
            return "<hr>"
        if node.type == NodeType.TABLE:
            return _render_table(node)
        return ""


def _safe_lexer(lang: str):
    try:
        return get_lexer_by_name(lang or "text")
    except ClassNotFound:
        return get_lexer_by_name("text")


def _pygments_css(bg: str) -> str:
    """根据代码背景明暗返回对应的 Pygments 配色 CSS。"""
    dark = relative_luminance(bg) < 0.4
    style_name = "monokai" if dark else "default"
    fmt = HtmlFormatter(style=style_name)
    return fmt.get_style_defs(".highlight")


def _esc(t: str) -> str:
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_inline(text: str) -> str:
    """轻量 inline 渲染：保留粗体/斜体/行内代码/链接/图片语义（先转义再还原标签）。"""
    import re as _re
    s = _esc(text)
    # 行内代码 `code`
    s = _re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
    # 图片 ![alt](src)
    s = _re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}">', s)
    # 链接 [text](url)
    s = _re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    # 粗体 **text**
    s = _re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    # 斜体 *text*
    s = _re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s


def _render_runs(node) -> str:
    """优先使用结构化 runs 渲染（准确）；无 runs 时回退正则。"""
    runs = getattr(node, "runs", None)
    if not runs:
        return _render_inline(node.text)
    out = []
    for r in runs:
        if r.link:
            out.append(f'<a href="{_esc(r.link)}">{_esc(r.text)}</a>')
        elif r.code:
            out.append(f"<code>{_esc(r.text)}</code>")
        else:
            t = _esc(r.text)
            if r.bold:
                t = f"<strong>{t}</strong>"
            if r.italic:
                t = f"<em>{t}</em>"
            out.append(t)
    return "".join(out)


def _render_runs_line(line: str) -> str:
    """QUOTE 行是纯文本（带 > 前缀），用正则回退。"""
    return _render_inline(line)


def _render_cell(runs) -> str:
    """渲染表格单元格：优先结构化 runs（保留加粗/斜体/代码/链接），\n 转 <br>。"""
    if not runs:
        return ""
    out = _render_runs_from_runs(runs)
    return out.replace("\n", "<br>\n")


def _render_runs_from_runs(runs) -> str:
    out = []
    for r in runs:
        if r.text == "\n":
            out.append("\n")
            continue
        if r.link:
            out.append(f'<a href="{_esc(r.link)}">{_esc(r.text)}</a>')
        elif r.code:
            out.append(f"<code>{_esc(r.text)}</code>")
        else:
            t = _esc(r.text)
            if r.bold:
                t = f"<strong>{t}</strong>"
            if r.italic:
                t = f"<em>{t}</em>"
            out.append(t)
    return "".join(out)


def _render_table(node: IRNode) -> str:
    rows = node.rows
    if not rows:
        return ""
    head = "".join(f"<th>{_render_cell(c)}</th>" for c in rows[0])
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{_render_cell(c)}</td>" for c in r) + "</tr>" for r in rows[1:]
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body_rows}</tbody></table>"


RendererDispatcher.register(".html", HtmlRenderer)
