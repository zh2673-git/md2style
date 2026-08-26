"""错误码与自定义异常（数据规范层）。"""

class Md2StyleError(Exception):
    """所有 md2style 异常的基类。"""


class StyleValidationError(Md2StyleError):
    """样式校验失败（颜色/字号/字体非法）。"""


class ParamWhitelistError(Md2StyleError):
    """参数不在白名单内（LLM/用户传了未知参数）。"""
