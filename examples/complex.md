# md2style 综合效果评估文档

本文件用于全面验证渲染器在复杂内容下的表现，覆盖多级标题、嵌套列表、长代码、多表格、引用、分割线等元素。

## 一、设计理念

md2style 的本质是**用声明式样式表 + 参数白名单取代自由文本描述**，把"排好看点"这类不可执行意图转化为可复用的版式引擎。

> 引用：好的排版应当有清晰的层级节奏——标题与正文之间、段落与段落之间，都有恰当的呼吸感。

---

## 二、功能清单

### 2.1 转换能力

- 支持格式：Word（docx）、网页（html）、演示（pptx）
- 预定义风格：论文、公文、Claude、Mac
- 参数微调：H1 颜色、字号、正文字体、行距

### 2.2 逆向学习

1. 用户拖入 Word 模板 → 自动提取样式
2. 用户拖入 HTML 模板 → 提取 CSS 声明
3. 生成 YAML 立即可在下拉框选用

## 三、代码示例

下面是一段较长的 Python 代码，用于验证代码块在三种格式下的呈现：

```python
from dataclasses import dataclass
from typing import List


@dataclass
class StyleConfig:
    """样式配置：声明式、可序列化。"""
    headings: dict
    body: dict
    code: dict


class Engine:
    def __init__(self, presets: List[StyleConfig]):
        self.presets = {p.name: p for p in presets}

    def resolve(self, name: str, overrides: dict) -> StyleConfig:
        base = self.presets.get(name, StyleConfig.default())
        return base.merge(overrides)

    def validate(self, cfg: StyleConfig) -> None:
        for h, spec in cfg.headings.items():
            if not (8 <= spec.size <= 72):
                raise ValueError(f"{h} 字号越界: {spec.size}")
```

行内代码如 `StyleConfig.merge()` 也会被保留。

## 四、对比表格

| 维度 | 论文风格 | 公文风格 | Claude | Mac |
|------|---------|---------|--------|-----|
| 标题字体 | 黑体 | 方正小标宋 | Georgia 衬线 | SF 无衬线 |
| 正文字体 | 宋体 | 仿宋 | 系统无衬线 | SF 无衬线 |
| 标题对齐 | 左对齐 | 居中（红头） | 左对齐 | 左对齐 |
| 正文缩进 | 2 字符 | 2 字符 | 无 | 无 |
| 分割线 | 实线 | 实线 | 柔和灰 | 柔和灰 |

### 4.1 表格二（数值型）

| 指标 | 目标值 | 实测 | 达标 |
|------|-------|------|------|
| 单次转换耗时 | < 5s | 0.3s | 是 |
| 样式偏差 | 0 | 0 | 是 |
| 学习闭环 | 完整 | 完整 | 是 |

## 五、嵌套内容演示

> 外层引用：
>
> > 内层引用：支持多级引用嵌套，体现版式层次。
>
> 回到外层。

## 六、结尾说明

以上覆盖了常见 Markdown 语义节点。三种格式的渲染应分别体现各自风格的"原版观感"：
公文严肃规整、论文学术克制、Claude 优雅留白、Mac 现代圆润。
