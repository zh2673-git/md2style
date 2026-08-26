"""HTML 声明式样式提取器（Learner 的 HTML 分支辅助）。

仅用标准库 html.parser，不引入外部依赖。
策略：
1. 解析 <h1>~<h6> 的 style 属性（内联）取字号/颜色/字体。
2. 解析 <style> 块中 :root / body / h1..h6 选择器的声明（含 CSS 变量 --accent 等）。

返回结构：
{
  "headings": {"h1": {"size":int,"color":str,"font":str}, ...},
  "body": {"font":,"size":,"line_height":,"color":},
  "extras": {"divider_color":, "accent_color":, "card_background":, ...}
}
"""

import re


# 字号单位换算（相对单位近似为 px）
_FONT_PX = 16
_UNIT_PX = {"px": 1.0, "pt": 1.333, "em": _FONT_PX, "rem": _FONT_PX}


def extract_html_style(html: str) -> dict:
    """入口：从 HTML 文本提取声明式样式。"""
    return _parse_declarations(html)


def _parse_declarations(html: str) -> dict:
    result = {
        "headings": {},
        "body": {},
        "extras": {},
    }

    # 1) 内联 style 在 <hN> / <body> 标签
    for level in range(1, 7):
        tag = f"h{level}"
        style = _inline_style_of_tag(html, tag)
        if style:
            parsed = _parse_style_text(style)
            result["headings"][tag] = parsed
    body_style = _inline_style_of_tag(html, "body")
    if body_style:
        result["body"].update(_parse_style_text(body_style))

    # 2) <style> 块里的选择器声明 + CSS 变量
    css_vars = {}
    for block in _style_blocks(html):
        css_vars.update(_extract_css_vars(block))
        for level in range(1, 7):
            decl = _selector_decl(block, f"h{level}")
            if decl:
                merged = result["headings"].get(f"h{level}", {})
                merged.update(_parse_style_text(decl))
                result["headings"][f"h{level}"] = merged
        body_decl = _selector_decl(block, "body")
        if body_decl:
            result["body"].update(_parse_style_text(body_decl))

    # 3) CSS 变量映射为 extras
    for var, val in css_vars.items():
        if var in ("--divider", "--divider-color", "--divider_color"):
            result["extras"]["divider_color"] = val
        elif var in ("--accent", "--accent-color", "--accent_color"):
            result["extras"]["accent_color"] = val
        elif var in ("--card-bg", "--card-background", "--card_background"):
            result["extras"]["card_background"] = val
        elif var in ("--card-radius", "--card_radius"):
            result["extras"]["card_radius"] = _to_int(val)

    return result


# ---- 解析工具 ----
def _inline_style_of_tag(html: str, tag: str):
    # 匹配 <tag ... style="...">
    m = re.search(rf"<{tag}\b[^>]*\bstyle\s*=\s*[\"']([^\"']*)[\"']", html, re.IGNORECASE)
    return m.group(1) if m else None


def _style_blocks(html: str):
    return re.findall(r"<style[^>]*>(.*?)</style>", html, re.IGNORECASE | re.DOTALL)


def _extract_css_vars(block: str) -> dict:
    out = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;{}]+);", block):
        out[m.group(1)] = m.group(2).strip()
    return out


def _selector_decl(block: str, selector: str) -> str:
    # 匹配 selector { ... } （非贪婪，跨行）
    m = re.search(rf"{re.escape(selector)}\s*\{{(.*?)\}}", block, re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else None


def _parse_style_text(text: str) -> dict:
    out = {}
    text = text or ""
    # font-size
    m = re.search(r"font-size\s*:\s*([\d.]+)(px|pt|em|rem)", text, re.IGNORECASE)
    if m:
        out["size"] = _to_int(float(m.group(1)) * _UNIT_PX[m.group(2).lower()])
    # color
    m = re.search(r"color\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgba?\([^)]*\))", text, re.IGNORECASE)
    if m:
        out["color"] = _normalize_color(m.group(1))
    # font-family
    m = re.search(r"font-family\s*:\s*([^;]+)", text, re.IGNORECASE)
    if m:
        out["font"] = m.group(1).split(",")[0].strip().strip("'\"")
    # line-height
    m = re.search(r"line-height\s*:\s*([\d.]+)", text, re.IGNORECASE)
    if m:
        out["line_height"] = float(m.group(1))
    return out


def _normalize_color(c: str) -> str:
    c = c.strip()
    if c.startswith("#"):
        if len(c) == 4:  # #abc -> #aabbcc
            return "#" + "".join(ch * 2 for ch in c[1:])
        return c[:7]
    if c.startswith("rgb"):
        nums = re.findall(r"[\d.]+", c)
        if len(nums) >= 3:
            return "#%02X%02X%02X" % (int(float(nums[0])), int(float(nums[1])), int(float(nums[2])))
    return c


def _to_int(v) -> int:
    try:
        return int(round(float(v)))
    except Exception:
        return v
