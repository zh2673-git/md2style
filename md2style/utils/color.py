"""颜色工具：十六进制 <-> RGB 转换与校验（规范/存储辅助）。"""

import re
from ..core.errors import StyleValidationError

_HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def is_valid_hex(value: str) -> bool:
    return bool(_HEX_RE.match(value or ""))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    if not is_valid_hex(value):
        raise StyleValidationError(f"非法颜色值: {value!r}，应为 #RRGGBB")
    h = value.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(value: str) -> float:
    """相对亮度（WCAG），0=黑 1=白。用于判断背景深浅以选取代码高亮配色。"""
    r, g, b = hex_to_rgb(value)
    def _lin(c: int) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
