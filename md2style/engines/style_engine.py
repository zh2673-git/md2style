"""Style Engine：三层优先级合并 + 合法性校验的样式裁决器（数据流转规则层）。

优先级：DEFAULT(硬编码) < YAML(预设) < CLI(覆盖参数)。合并后经 validate 才生效。
"""

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from ..core.constants import DEFAULT_STYLE, MIN_SIZE, MAX_SIZE
from ..core.errors import StyleValidationError
from ..utils.color import is_valid_hex
from ..utils.fonts import font_exists
from ..utils.logger import get_logger

logger = get_logger("style_engine")


class StyleEngine:
    def __init__(self, styles_dir: str | Path = "styles"):
        self.styles_dir = Path(styles_dir)

    # ---- 公共接口 ----
    def resolve(self, style_name: str, cli_overrides: dict | None = None) -> dict:
        """返回合并校验后的 final_style。"""
        base = deepcopy(DEFAULT_STYLE)                     # 优先级 1
        if style_name:
            yaml_style = self._load_yaml(style_name)       # 优先级 2
            if yaml_style:
                base = _deep_merge(base, yaml_style)
        if cli_overrides:
            base = _deep_merge(base, cli_overrides)        # 优先级 3
        self.validate(base)
        return base

    def validate(self, style_dict: dict) -> None:
        """校验颜色/字号/字体合法性；失败抛 StyleValidationError。"""
        headings = style_dict.get("headings", {})
        for h, cfg in headings.items():
            self._check_heading(h, cfg)
        body = style_dict.get("body", {})
        self._check_body(body)
        code = style_dict.get("code", {})
        if "color" in code and not is_valid_hex(code["color"]):
            raise StyleValidationError(f"code.color 非法: {code['color']}")
        if "background" in code and not is_valid_hex(code["background"]):
            raise StyleValidationError(f"code.background 非法: {code['background']}")

    # ---- 内部 ----
    def _load_yaml(self, style_name: str) -> dict:
        path = self._resolve_path(style_name)
        if not path.exists():
            logger.warning("样式预设不存在: %s，回退到 DEFAULT", path)
            return {}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _resolve_path(self, style_name: str) -> Path:
        # 接受 "name" 或 "name.yaml"
        if style_name.endswith(".yaml"):
            fname = style_name
        else:
            fname = f"{style_name}.yaml"
        return self.styles_dir / fname

    def _check_heading(self, h: str, cfg: dict) -> None:
        if "color" in cfg and not is_valid_hex(cfg["color"]):
            raise StyleValidationError(f"{h}.color 非法: {cfg['color']}")
        if "size" in cfg:
            if not (MIN_SIZE <= cfg["size"] <= MAX_SIZE):
                raise StyleValidationError(f"{h}.size 超出范围 {MIN_SIZE}~{MAX_SIZE}: {cfg['size']}")
        if "font" in cfg:
            font_exists(cfg["font"])

    def _check_body(self, body: dict) -> None:
        if "color" in body and not is_valid_hex(body["color"]):
            raise StyleValidationError(f"body.color 非法: {body['color']}")
        if "size" in body:
            if not (MIN_SIZE <= body["size"] <= MAX_SIZE):
                raise StyleValidationError(f"body.size 超出范围: {body['size']}")
        if "line_height" in body and body["line_height"] <= 0:
            raise StyleValidationError(f"body.line_height 必须 > 0: {body['line_height']}")
        if "font" in body:
            font_exists(body["font"])


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并；override 覆盖 base（列表/标量直接替换）。"""
    result = deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result
