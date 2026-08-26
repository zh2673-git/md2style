"""渲染器抽象基类（数据接口执行层）。

所有格式渲染器继承此类，统一签名 render(ir, final_style, output_path)。
新增格式（pdf/latex）仅需继承本类，不动其它模块。
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..core.ir import IR


class RendererBase(ABC):
    @abstractmethod
    def render(self, ir: IR, final_style: dict, output_path: str) -> None:
        """将 IR 按 final_style 写入 output_path。"""
        raise NotImplementedError


class RendererDispatcher:
    """按输出后缀分发渲染器（数据接口执行层调度）。"""

    _registry: dict[str, type[RendererBase]] = {}

    @classmethod
    def register(cls, suffix: str, renderer: type[RendererBase]) -> None:
        cls._registry[suffix.lower()] = renderer

    @classmethod
    def by_suffix(cls, output_path: str) -> RendererBase:
        suffix = Path(output_path).suffix.lower()
        if suffix not in cls._registry:
            raise ValueError(f"不支持的输出格式: {suffix}（可选: {sorted(cls._registry)}）")
        return cls._registry[suffix]()
