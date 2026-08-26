# md2style 效果演示

这是一个用于展示多格式转换效果的测试文档，覆盖了常见 Markdown 元素。

## 1. 标题层级

### 三级标题

#### 四级标题

正文段落示例：md2style 将同一份 Markdown 转换为 Word / HTML / PPT，样式由预定义 YAML 或用户学习所得控制。

## 2. 强调与引用

> 引用块：好的工具应当让人和 LLM 都能稳定复用版式，而不是每次重新描述"排好看点"。

行内 **加粗**、*斜体* 与 `行内代码` 也都会被保留为语义节点。

## 3. 列表

- 预定义风格：论文 / 公文 / Claude / Mac
- 逆向学习：拖入模板即学
- 双入口：CLI 与本地 Web

1. 第一步：写 Markdown
2. 第二步：选风格
3. 第三步：导出

## 4. 代码块

```python
def convert(md: str, style: str) -> str:
    """把 Markdown 按指定风格转换。"""
    ir = parser.to_ir(md)
    return renderer.render(ir, engine.resolve(style))
```

## 5. 表格

| 格式 | 预定义风格 | 学习支持 |
|------|-----------|---------|
| Word | 论文 / 公文 | ✅ |
| HTML | Claude / Mac | ✅ |
| PPT | 复用 HTML | — |

---

> 以上为分割线后的收尾说明。
