"""MD Parser：Markdown -> 与版式无关的统一语义 IR（数据流转规则层）。

使用 markdown-it-py 生成 token 流，转换为 IRNode 列表，剥离所有原样式。
保留：标题层级、列表嵌套、代码块语言、表格对齐。
行内语义（**加粗** / *斜体* / `代码` / [链接](url)）解析为结构化 runs。
"""

from markdown_it import MarkdownIt
import re

from ..core.ir import IRNode, NodeType, IR, InlineRun

_BR_RE = re.compile(r"^<br\s*/?>$", re.IGNORECASE)


def re_match_br(s: str) -> bool:
    return bool(_BR_RE.match((s or "").strip()))


class MdParser:
    def __init__(self):
        self._md = MarkdownIt("commonmark").enable("table").enable("html_block").enable("html_inline")

    def to_ir(self, md_text: str) -> IR:
        tokens = self._md.parse(md_text)
        ir: IR = []
        i = 0
        n = len(tokens)
        while i < n:
            tok = tokens[i]
            nxt = tokens[i + 1] if i + 1 < n else None

            if tok.type == "heading_open":
                level = int(tok.tag[1])
                text, children, meta = self._strip_font_meta(nxt)
                runs = self._parse_inline(children) if children else []
                node = IRNode(type=NodeType.HEADING, text=text, runs=runs, level=level)
                if meta:
                    node.meta = meta
                ir.append(node)
                i += 2  # 跳过 inline + close

            elif tok.type == "paragraph_open":
                text, children, meta = self._strip_font_meta(nxt)
                runs = self._parse_inline(children) if children else []
                node = IRNode(type=NodeType.PARAGRAPH, text=text, runs=runs)
                if meta:
                    node.meta = meta
                ir.append(node)
                i += 2

            elif tok.type == "bullet_list_open" or tok.type == "ordered_list_open":
                ordered = tok.type == "ordered_list_open"
                level = int(tok.attrs.get("start", 0)) if ordered else 0
                # 收集到下一个 list_close 之间的列表项
                items, i = self._collect_list(tokens, i, n)
                for item in items:
                    ir.append(IRNode(type=NodeType.LIST, text=item["text"], runs=item["runs"],
                                     ordered=ordered, level=level))

            elif tok.type == "fence":
                lang = tok.info.strip()
                ir.append(IRNode(type=NodeType.CODE, text=tok.content, lang=lang))
                i += 1

            elif tok.type == "blockquote_open":
                # 收集到 blockquote_close 之间的所有 inline 文本（含嵌套，用层级前缀体现）
                texts = []
                runs_acc = None
                j = i + 1
                depth = 1
                cur_level = 1
                while j < n:
                    t = tokens[j]
                    if t.type == "blockquote_open":
                        depth += 1
                        cur_level = depth
                    elif t.type == "blockquote_close":
                        depth -= 1
                        if depth == 0:
                            break
                        cur_level = depth
                    elif t.type == "inline":
                        prefix = "> " * (cur_level - 1)
                        line_runs = [InlineRun(text=prefix)] + self._parse_inline(t.children)
                        if runs_acc is None:
                            runs_acc = []
                        runs_acc.extend(line_runs)
                        runs_acc.append(InlineRun(text="\n"))
                        texts.append(prefix + t.content)
                    j += 1
                node = IRNode(type=NodeType.QUOTE, text="\n".join(texts))
                if runs_acc:
                    node.runs = runs_acc
                ir.append(node)
                i = j + 1

            elif tok.type == "hr":
                ir.append(IRNode(type=NodeType.HR))
                i += 1

            elif tok.type == "html_block":
                # 裸 HTML 块（如 <a id="1"></a> 锚点、<div> 等）：原样保留
                ir.append(IRNode(type=NodeType.RAW_HTML, text=tok.content))
                i += 1

            elif tok.type == "table_open":
                rows, align, i = self._collect_table(tokens, i, n)
                ir.append(IRNode(type=NodeType.TABLE, rows=rows, align=align))

            else:
                i += 1
        return ir

    @staticmethod
    def _strip_font_meta(tok):
        """从 inline token 提取 `!{font:XXX}` 前缀作为 meta，返回 (text, children, meta)。"""
        import re
        meta = {}
        if not tok or not getattr(tok, "children", None):
            return (tok.content if tok else "", None, meta)
        content = tok.content or ""
        m = re.match(r"^!\{font:([^}]+)\}\s*", content)
        if m:
            meta["font"] = m.group(1).strip()
            # 从 children 第一个 text token 剥离前缀
            prefix_len = len(m.group(0))
            for c in tok.children:
                if c.type == "text":
                    c.content = c.content[prefix_len:]
                    break
            content = content[prefix_len:]
        return (content, tok.children, meta)

    def _parse_inline(self, children, bold=False, italic=False):
        if not children:
            return []
        runs = []
        i = 0
        n = len(children)
        while i < n:
            tok = children[i]
            if tok.type == "text":
                # 兜底：commonmark 对中文 **加粗** 可能未解析，这里再用正则细化
                runs.extend(self._split_emphasis(tok.content, bold, italic))
            elif tok.type == "code_inline":
                runs.append(InlineRun(text=tok.content, code=True))
            elif tok.type == "image":
                alt = tok.attrs.get("alt", "")
                url = tok.attrs.get("src", "")
                runs.append(InlineRun(text=f"[图片: {alt}]", link=url))
            elif tok.type == "strong_open":
                j = i + 1
                sub = []
                while j < n and children[j].type != "strong_close":
                    sub.append(children[j])
                    j += 1
                runs.extend(self._parse_children(sub, bold=True, italic=italic))
                i = j
            elif tok.type == "em_open":
                j = i + 1
                sub = []
                while j < n and children[j].type != "em_close":
                    sub.append(children[j])
                    j += 1
                runs.extend(self._parse_children(sub, bold=bold, italic=True))
                i = j
            elif tok.type == "softbreak":
                runs.append(InlineRun(text="\n"))
            elif tok.type == "hardbreak":
                runs.append(InlineRun(text="\n"))
            elif tok.type == "html_inline":
                # <br> 等内联 HTML：换行标签转 \n，其余原样保留（不转义）
                if re_match_br(tok.content):
                    runs.append(InlineRun(text="\n"))
                else:
                    runs.append(InlineRun(text=tok.content, raw=True))
            elif tok.type == "link_open":
                url = tok.attrs.get("href", "")
                j = i + 1
                sub = []
                while j < n and children[j].type != "link_close":
                    sub.append(children[j])
                    j += 1
                for r in self._parse_children(sub, bold, italic):
                    r.link = url
                    runs.append(r)
                i = j
            i += 1
        return runs

    def _parse_children(self, children, bold, italic):
        """递归配对 strong/em/link，继承当前加粗/斜体状态。"""
        return self._parse_inline(children, bold=bold, italic=italic)

    @staticmethod
    def _split_emphasis(text: str, bold=False, italic=False):
        """正则兜底：拆分 **加粗** / *斜体* / `代码`（仅当 markdown-it 未解析时）。
        bold/italic 继承外层状态。"""
        import re
        if not text:
            return []
        out = []
        pattern = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")
        pos = 0
        matched = False
        for m in pattern.finditer(text):
            matched = True
            if m.start() > pos:
                out.append(InlineRun(text=text[pos:m.start()], bold=bold, italic=italic))
            seg = m.group(1)
            if seg.startswith("**") and seg.endswith("**"):
                out.append(InlineRun(text=seg[2:-2], bold=True, italic=italic))
            elif seg.startswith("`") and seg.endswith("`"):
                out.append(InlineRun(text=seg[1:-1], code=True))
            else:  # *...*
                out.append(InlineRun(text=seg[1:-1], bold=bold, italic=True))
            pos = m.end()
        if not matched:
            return [InlineRun(text=text, bold=bold, italic=italic)]
        if pos < len(text):
            out.append(InlineRun(text=text[pos:], bold=bold, italic=italic))
        return out

    def _collect_list(self, tokens, start, n):
        items = []
        i = start + 1
        depth = 1
        while i < n:
            t = tokens[i]
            if t.type in ("bullet_list_open", "ordered_list_open"):
                depth += 1
            elif t.type in ("bullet_list_close", "ordered_list_close"):
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            elif t.type == "inline" and depth == 1:
                items.append({"text": t.content, "runs": self._parse_inline(t.children)})
            i += 1
        # 简化：仅取顶层项文本与 runs
        return items, i

    def _collect_table(self, tokens, start, n):
        rows = []
        align = []
        i = start + 1
        header_done = False
        while i < n:
            t = tokens[i]
            if t.type == "table_close":
                i += 1
                break
            if t.type == "inline":
                # 复用段落的内联解析，保留 **加粗** / *斜体* / `代码` / <br> 换行
                cells = [self._parse_inline(t.children) for c in t.content.split("|")]
                if not header_done:
                    align = self._parse_align(tokens, i)
                    rows.append(cells)
                    header_done = True
                else:
                    rows.append(cells)
            i += 1
        return rows, align, i

    def _parse_align(self, tokens, inline_idx):
        # 在 thead 之后的分隔行决定对齐
        for j in range(inline_idx, min(inline_idx + 4, len(tokens))):
            if tokens[j].type == "inline":
                parts = tokens[j].content.split("|")
                return ["left" if p.strip().startswith(":") and p.strip().endswith(":")
                        else "right" if p.strip().endswith(":")
                        else "center" if p.strip().startswith(":")
                        else "left" for p in parts]
        return []
