"""渲染器包：导入即注册各格式到 RendererDispatcher。"""

from .base import RendererBase, RendererDispatcher
from .docx_renderer import DocxRenderer
from .html_renderer import HtmlRenderer
from .ppt_renderer import PptRenderer

# 触发注册
_ = (DocxRenderer, HtmlRenderer, PptRenderer)

__all__ = ["RendererBase", "RendererDispatcher", "DocxRenderer", "HtmlRenderer", "PptRenderer"]
