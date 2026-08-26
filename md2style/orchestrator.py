"""Orchestrator：子命令路由 + 参数白名单校验 + 流程编排（数据流转编排层）。

白名单机制：仅接受已知参数，未知参数抛 ParamWhitelistError，杜绝 LLM 幻觉扩散。
所有业务规则在 engines/renderers，本层只做编排。
"""

from pathlib import Path

from .engines import StyleEngine
from .engines.md_parser import MdParser
from .engines.learner import Learner
from .renderers import RendererDispatcher
from .core.errors import ParamWhitelistError, Md2StyleError
from .utils.logger import get_logger

logger = get_logger("orchestrator")

# 参数白名单（与 CLI / Web 表单字段严格一致，使用 argparse 的 dest 名）
WHITELIST = {
    "convert": {
        "i", "o", "s", "template",
        # 微调：H1-H6 字号/颜色/字体
        "h1_size", "h1_color", "h1_font", "h2_size", "h2_color", "h2_font",
        "h3_size", "h3_color", "h3_font", "h4_size", "h4_color", "h4_font",
        "h5_size", "h5_color", "h5_font", "h6_size", "h6_color", "h6_font",
        # 微调：正文
        "body_font", "body_size", "body_color", "line_height", "para_spacing",
        # 微调：代码块
        "code_font", "code_size", "code_color", "code_bg",
    },
    "learn": {"t", "n"},
    "preview": {"i", "s", "h1_color", "body_font"},
}


class Orchestrator:
    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self.style_engine = StyleEngine(self.base_dir / "styles")
        self.parser = MdParser()
        self.learner = Learner(self.base_dir / "styles")

    # ---- 入口 ----
    def run(self, subcommand: str, args: dict) -> str:
        self._check_whitelist(subcommand, args)
        if subcommand == "convert":
            return self._convert(args)
        if subcommand == "learn":
            return self._learn(args)
        if subcommand == "preview":
            return self._preview(args)
        raise ParamWhitelistError(f"未知子命令: {subcommand}")

    # ---- 白名单 ----
    def _check_whitelist(self, subcommand: str, args: dict) -> None:
        allowed = WHITELIST.get(subcommand)
        if allowed is None:
            raise ParamWhitelistError(f"未知子命令: {subcommand}")
        for key in args:
            if key not in allowed:
                raise ParamWhitelistError(
                    f"参数 {key} 不在白名单。可用: {sorted(allowed)}"
                )

    # ---- 子命令实现 ----
    def _convert(self, args: dict) -> str:
        input_path = args["i"]
        output_path = args["o"]
        style_name = args.get("s", "")
        overrides = self._build_overrides(args)

        md_text = Path(input_path).read_text(encoding="utf-8")
        final_style = self.style_engine.resolve(style_name, overrides)
        if "template" in args:
            final_style["_template"] = args["template"]

        ir = self.parser.to_ir(md_text)
        renderer = RendererDispatcher.by_suffix(output_path)
        renderer.render(ir, final_style, output_path)
        logger.info("转换完成: %s -> %s", input_path, output_path)
        return output_path

    def _learn(self, args: dict) -> str:
        template = args["t"]
        name = args["n"]
        return self.learner.learn(template, name)

    def _preview(self, args: dict) -> str:
        input_path = args["i"]
        output_path = str(Path(args["i"]).with_suffix(".preview.html"))
        args["o"] = output_path
        return self._convert(args)

    def _build_overrides(self, args: dict) -> dict:
        ov: dict = {}
        for lv in range(1, 7):
            if f"h{lv}_size" in args:
                _set_nested(ov, f"headings.h{lv}.size", args[f"h{lv}_size"])
            if f"h{lv}_color" in args:
                _set_nested(ov, f"headings.h{lv}.color", args[f"h{lv}_color"])
            if f"h{lv}_font" in args:
                _set_nested(ov, f"headings.h{lv}.font", args[f"h{lv}_font"])
        if "body_font" in args:
            _set_nested(ov, "body.font", args["body_font"])
        if "body_size" in args:
            _set_nested(ov, "body.size", args["body_size"])
        if "body_color" in args:
            _set_nested(ov, "body.color", args["body_color"])
        if "line_height" in args:
            _set_nested(ov, "body.line_height", args["line_height"])
        if "para_spacing" in args:
            _set_nested(ov, "body.para_spacing", args["para_spacing"])
        if "code_font" in args:
            _set_nested(ov, "code.font", args["code_font"])
        if "code_size" in args:
            _set_nested(ov, "code.size", args["code_size"])
        if "code_color" in args:
            _set_nested(ov, "code.color", args["code_color"])
        if "code_bg" in args:
            _set_nested(ov, "code.background", args["code_bg"])
        return ov


def _set_nested(d: dict, path: str, value):
    keys = path.split(".")
    cur = d
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value
