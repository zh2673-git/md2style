"""IR（中间表示）：Markdown 解析后与版式无关的语义节点定义。

数据规范层（core/），不依赖任何其他层。所有渲染器共享此结构。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    HR = "hr"


@dataclass
class InlineRun:
    """行内片段：还原 **加粗** / *斜体* / `代码` / [链接](url) 语义。"""
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str = ""            # 链接地址，空表示非链接


@dataclass
class IRNode:
    type: NodeType
    text: str = ""
    runs: list = field(default_factory=list)  # InlineRun 列表（结构化行内）
    level: int = 0            # heading 层级 / list 嵌套层级
    lang: str = ""            # code 块语言标识
    ordered: bool = False     # list 是否有序
    align: list = field(default_factory=list)  # table 列对齐
    rows: list = field(default_factory=list)   # table 数据
    meta: dict = field(default_factory=dict)   # 其它元数据


IR = list[IRNode]
