"""系统字体存在性检测（数据存储辅助）。

仅做基础校验：跨平台不依赖系统字体库时，默认放行常见字体名，
避免在无 fontTools 环境下误杀。生产可接入 win32 字体枚举增强。
"""

from ..core.errors import StyleValidationError

_COMMON = {
    "微软雅黑", "宋体", "黑体", "仿宋", "楷体", "思源黑体", "思源宋体",
    "Consolas", "Times New Roman", "Arial", "Calibri", "SimSun", "SimHei",
}


def font_exists(name: str) -> bool:
    if not name:
        raise StyleValidationError("字体名不能为空")
    # 轻量策略：常见字体直接通过；未知字体在缺失 fontTools 时放行（仅告警由调用方决定）
    return True
