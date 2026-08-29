"""CLI 入口：argparse 子命令绑定（数据接口层）。

人类与 LLM 共用的固定入口；参数经 Orchestrator 白名单校验。
"""

import argparse
import sys

from .orchestrator import Orchestrator
from .core.errors import ParamWhitelistError, Md2StyleError


def _add_tune_args(p: argparse.ArgumentParser) -> None:
    """给 convert / batch 挂上通用的样式与微调参数。"""
    p.add_argument("-s", default="", help="样式名（paper/official/claude/mac/已学习）")
    # 微调：标题字号/颜色（H1-H6）
    p.add_argument("--h1-size", type=int, help="H1 字号")
    p.add_argument("--h1-color", help="H1 颜色 #RRGGBB")
    p.add_argument("--h2-size", type=int, help="H2 字号")
    p.add_argument("--h2-color", help="H2 颜色")
    p.add_argument("--h3-size", type=int, help="H3 字号")
    p.add_argument("--h3-color", help="H3 颜色")
    p.add_argument("--h4-size", type=int, help="H4 字号")
    p.add_argument("--h4-color", help="H4 颜色")
    p.add_argument("--h5-size", type=int, help="H5 字号")
    p.add_argument("--h5-color", help="H5 颜色")
    p.add_argument("--h6-size", type=int, help="H6 字号")
    p.add_argument("--h6-color", help="H6 颜色")
    # 微调：正文
    p.add_argument("--body-font", help="正文字体")
    p.add_argument("--body-size", type=float, help="正文字号")
    p.add_argument("--body-color", help="正文颜色 #RRGGBB")
    p.add_argument("--line-height", type=float, help="正文行距")
    p.add_argument("--para-spacing", type=float, help="段落间距(em)")
    # 微调：代码块
    p.add_argument("--code-font", help="代码字体")
    p.add_argument("--code-size", type=float, help="代码字号")
    p.add_argument("--code-color", help="代码颜色 #RRGGBB")
    p.add_argument("--code-bg", help="代码背景 #RRGGBB")
    p.add_argument("--template", help="docx 模板 dotx 名")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="md2style",
        description="Markdown 多格式转换 + 样式逆向学习",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_convert = sub.add_parser("convert", help="转换 Markdown 为多格式")
    p_convert.add_argument("-i", required=True, help="输入 md 路径")
    p_convert.add_argument("-o", required=True, help="输出路径（后缀决定格式）")
    _add_tune_args(p_convert)

    p_batch = sub.add_parser("batch", help="批量转换目录下的 Markdown")
    p_batch.add_argument("-i", required=True, help="输入目录，或 glob 模式（如 docs/*.md）")
    p_batch.add_argument("-o", required=True, help="输出目录")
    p_batch.add_argument("-f", default="docx", help="输出格式 docx/html/pptx（默认 docx）")
    p_batch.add_argument("--flat", action="store_true", help="不保留子目录结构，全部平铺到输出目录")
    p_batch.add_argument("--no-recursive", action="store_false", dest="recursive",
                         help="只处理输入目录第一层，不递归子目录")
    _add_tune_args(p_batch)

    p_learn = sub.add_parser("learn", help="从 Word 学习样式")
    p_learn.add_argument("-t", required=True, help="模板 docx 路径")
    p_learn.add_argument("-n", required=True, help="学习后的样式名")

    p_preview = sub.add_parser("preview", help="生成临时 HTML 预览")
    p_preview.add_argument("-i", required=True, help="输入 md 路径")
    p_preview.add_argument("-s", default="", help="样式名")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    args = {k: v for k, v in vars(ns).items() if k != "subcommand" and v is not None}

    orch = Orchestrator()
    try:
        result = orch.run(ns.subcommand, args)
        print(f"✅ 成功: {result}")
        return 0
    except ParamWhitelistError as e:
        print(f"❌ 参数错误（白名单拦截）: {e}", file=sys.stderr)
        return 2
    except Md2StyleError as e:
        print(f"❌ 处理失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
