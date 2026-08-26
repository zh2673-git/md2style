"""全局常量与默认样式兜底（数据规范层）。

DEFAULT_STYLE 为三层优先级合并的最底层（DEFAULT < YAML < CLI）。
"""

from typing import Any

MIN_SIZE = 8
MAX_SIZE = 72

# 兜底默认样式：缺失 YAML 字段时启用
DEFAULT_STYLE: dict[str, Any] = {
    "headings": {
        "h1": {"size": 22, "color": "#1A1A1A", "font": "微软雅黑"},
        "h2": {"size": 18, "color": "#1A1A1A", "font": "微软雅黑"},
        "h3": {"size": 15, "color": "#1A1A1A", "font": "微软雅黑"},
        "h4": {"size": 13, "color": "#1A1A1A", "font": "微软雅黑"},
        "h5": {"size": 12, "color": "#1A1A1A", "font": "微软雅黑"},
        "h6": {"size": 11, "color": "#1A1A1A", "font": "微软雅黑"},
    },
    "body": {
        "font": "微软雅黑",
        "size": 10.5,
        "line_height": 1.5,
        "color": "#1A1A1A",
    },
    "code": {
        "font": "Consolas",
        "size": 10,
        "color": "#333333",
        "background": "#F5F5F5",
    },
}
