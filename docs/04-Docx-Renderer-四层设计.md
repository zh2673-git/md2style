# Docx Renderer 递归四层详细设计（模块C1，第2层·核心）

> 父本质锚定：Renderers 本质是"把 IR 节点按 final_style 精准写入目标格式的映射执行器族"。
> 本模块本质：在映射约束下，Docx Renderer 是"**段落/字符级样式注入器**"。

## 数据规范（Specification）
- 输入契约：`ir: list[IRNode]`（来自 MD Parser）、`final_style: dict`（来自 Style Engine）。
- 依赖 `final_style['headings']['hN']`、`final_style['body']`。
- 模板：`templates/word/base.dotx`（空白母版）、`company.dotx`（带 Logo）。

## 数据存储（Storage）
- 读：`templates/word/*.dotx`（母版）、`final_style`（内存）。
- 写：输出 `.docx` 文件（python-docx `Document`）。
- 无数据库；长文档采用流式逐段写入避免内存溢出。

## 数据流转（Flow）
```
render(ir, final_style, output_path):
  1. doc = load_template(option.template)         # base / company
  2. for node in ir:
       if node.type == heading:
           p = doc.add_heading(node.text, level=node.level)
           apply_style(p, final_style['headings'][f'h{node.level}'])
       elif node.type == paragraph:
           p = doc.add_paragraph(node.text)
           apply_body_style(p, final_style['body'])
       elif node.type == code:
           p = doc.add_paragraph(node.text, style='CodeBlock')
           apply_monospace(p)
       elif node.type == table:
           build_table(doc, node, final_style)
  3. doc.save(output_path)
```
- `apply_style`：设置 `font.size / font.color.rgb / font.name`（段落级 + 字符级）。
- 事务边界：单个 `render` 调用内完成，失败即抛异常不落盘。

## 数据接口（Interface）
```python
class DocxRenderer(RendererBase):
    def render(self, ir: list[IRNode], final_style: dict, output_path: str) -> None: ...
# 通过 RendererDispatcher.by_suffix('.docx') 被 Orchestrator 调用
```
- 稳定性：实现 `RendererBase` 抽象签名，受不变量 I 保护。

## 父模块依赖
- 依赖：`core/ir.py`（IRNode）、`engines/style_engine`（final_style 结构）、`utils/color.py`。
- 不反向依赖：Domain 层不直接 import 具体渲染实现（依赖倒置）。
