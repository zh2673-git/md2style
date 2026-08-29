"""FastAPI 后端：md2style 本地 Web 服务（原生 HTML/JS 前端，三区 Tab 互不阻塞）。

业务规则全在 Orchestrator，本层只做：参数收集 -> 调 Orchestrator -> 返回文件/内容。
参数键名严格使用白名单 dest 名（下划线，无 --），规避旧 PyWebIO 版的 bug。
"""

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles

from ...orchestrator import Orchestrator
from ...core.errors import ParamWhitelistError, Md2StyleError
from ...utils.fonts import _COMMON
from ...utils.logger import get_logger

logger = get_logger("web")

BASE_DIR = Path(__file__).resolve().parents[3]
STATIC_DIR = Path(__file__).resolve().parent / "static"
EXAMPLES_DIR = BASE_DIR / "examples"
WEB_ONLY_STYLES = {"claude", "mac"}  # 仅适用于 html/pptx，docx 不可用

SUFFIX = {"docx": ".docx", "html": ".html", "pptx": ".pptx"}

# 字体下拉选项：常见字体 + 中文衬线/无衬线补充
FONT_OPTIONS = sorted(_COMMON | {
    "Georgia", "PingFang SC", "Microsoft YaHei", "SimSun", "SimHei", "KaiTi", "FangSong",
})


def _available_styles() -> list:
    styles_dir = BASE_DIR / "styles"
    return sorted(p.stem for p in styles_dir.glob("*.yaml"))


def _style_options(fmt: str) -> list:
    opts = _available_styles()
    if fmt == "docx":
        opts = [s for s in opts if s not in WEB_ONLY_STYLES]
    return opts or ["paper"]


def _unique_name(name: str, used: dict) -> str:
    """批量打包时避免同名文件互相覆盖：a.docx, a_1.docx, a_2.docx ..."""
    if name not in used:
        used[name] = 1
        return name
    stem, suffix = Path(name).stem, Path(name).suffix
    used[name] += 1
    return f"{stem}_{used[name] - 1}{suffix}"


def create_app() -> FastAPI:
    app = FastAPI(title="md2style Web")

    @app.get("/api/styles")
    def api_styles(fmt: str = "docx"):
        """返回某格式可用的样式列表。"""
        return {"styles": _style_options(fmt), "all": _available_styles()}

    @app.get("/api/fonts")
    def api_fonts():
        """字体下拉选项。"""
        return {"fonts": FONT_OPTIONS}

    @app.get("/api/style/{name}")
    def api_style_detail(name: str):
        """返回某风格的当前微调默认值（扁平化，供前端回填）。"""
        try:
            s = Orchestrator(BASE_DIR).style_engine.resolve(name)
        except Exception as e:
            raise HTTPException(400, f"无法读取样式 {name}: {e}")
        h = s.get("headings", {})
        body = s.get("body", {})
        code = s.get("code", {})
        out = {"fonts": FONT_OPTIONS}
        for lv in range(1, 7):
            hc = h.get(f"h{lv}", {})
            out[f"h{lv}_size"] = hc.get("size")
            out[f"h{lv}_color"] = hc.get("color")
        out["body_font"] = body.get("font")
        out["body_size"] = body.get("size")
        out["body_color"] = body.get("color")
        out["line_height"] = body.get("line_height")
        out["para_spacing"] = body.get("para_spacing", 1.0)
        out["code_font"] = code.get("font")
        out["code_size"] = code.get("size")
        out["code_color"] = code.get("color")
        out["code_bg"] = code.get("background")
        return out

    @app.post("/api/convert")
    async def api_convert(request: Request, md_file: List[UploadFile] = File(...)):
        """转换：支持 1 个或多个 .md。单文件直接下载，多文件打包为 zip。"""
        form = await request.form()
        fmt = form.get("fmt", "")
        style = form.get("style", "")
        if fmt not in SUFFIX:
            raise HTTPException(400, f"不支持的格式: {fmt}")
        # docx 不允许 claude/mac
        if fmt == "docx" and style in WEB_ONLY_STYLES:
            style = "paper"

        # 从 form 收集微调字段（仅非空），键名即白名单 dest 名
        NUM_KEYS = {"body_size", "line_height", "para_spacing", "code_size",
                    "h1_size", "h2_size", "h3_size", "h4_size", "h5_size", "h6_size"}
        tune = {}
        for k, v in form.items():
            if k in ("md_file", "fmt", "style"):
                continue
            v = str(v).strip()
            if not v:
                continue
            tune[k] = float(v) if k in NUM_KEYS else v

        uploads = [u for u in md_file if u.filename]
        if not uploads:
            raise HTTPException(400, "请先上传至少一个 Markdown 文件")

        # 单文件：沿用既有行为（产物落在 examples 目录）
        if len(uploads) == 1:
            up = uploads[0]
            in_path = EXAMPLES_DIR / "_upload_tmp.md"
            in_path.write_bytes(await up.read())
            out_path = EXAMPLES_DIR / f"_out{SUFFIX[fmt]}"
            args = {"i": str(in_path), "o": str(out_path), "s": style, **tune}
            try:
                result = Orchestrator(BASE_DIR).run("convert", args)
            except (ParamWhitelistError, Md2StyleError) as e:
                raise HTTPException(400, f"转换失败: {e}")
            return FileResponse(result, filename=out_path.name,
                                media_type="application/octet-stream")

        # 多文件：临时目录逐个转换，打包 zip 后返回（响应结束自动清理）
        tmp_dir = Path(tempfile.mkdtemp(prefix="md2style_batch_"))
        try:
            produced: list[Path] = []
            used: dict[str, int] = {}
            for idx, up in enumerate(uploads):
                raw_name = Path(up.filename or f"doc{idx}.md").name  # 防路径穿越
                stem = Path(raw_name).stem or f"doc{idx}"
                in_path = tmp_dir / f"in_{idx}_{raw_name}"
                in_path.write_bytes(await up.read())
                out_name = _unique_name(stem + SUFFIX[fmt], used)
                out_path = tmp_dir / out_name
                args = {"i": str(in_path), "o": str(out_path), "s": style, **tune}
                try:
                    Orchestrator(BASE_DIR).run("convert", args)
                except (ParamWhitelistError, Md2StyleError) as e:
                    raise HTTPException(400, f"{raw_name} 转换失败: {e}")
                produced.append(out_path)

            zip_path = tmp_dir / "md2style_batch.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in produced:
                    zf.write(p, p.name)
            # 先把字节读入内存，再删除临时目录，避免流式响应与后台清理的竞态
            data = zip_path.read_bytes()
        except HTTPException:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            raise
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return Response(
            content=data,
            media_type="application/zip",
            headers={"Content-Disposition":
                     f'attachment; filename="md2style_batch_{len(produced)}files.zip"'},
        )

    @app.post("/api/preview")
    async def api_preview(
        md_file: UploadFile = File(...),
        style: str = Form(""),
        h1_color: str = Form(""),
        body_font: str = Form(""),
    ):
        md_bytes = await md_file.read()
        in_path = EXAMPLES_DIR / "_upload_tmp.md"
        in_path.write_bytes(md_bytes)
        args = {"i": str(in_path), "s": style}
        if h1_color.strip():
            args["h1_color"] = h1_color.strip()
        if body_font.strip():
            args["body_font"] = body_font.strip()
        try:
            out_html = Orchestrator(BASE_DIR).run("preview", args)
        except (ParamWhitelistError, Md2StyleError) as e:
            raise HTTPException(400, f"预览失败: {e}")
        html = Path(out_html).read_text(encoding="utf-8")
        return HTMLResponse(html)

    @app.post("/api/learn")
    async def api_learn(
        template_file: UploadFile = File(...),
        name: str = Form(...),
    ):
        ext = Path(template_file.filename or "").suffix.lower()
        if ext not in (".docx", ".html", ".htm"):
            raise HTTPException(400, "仅支持 .docx / .html / .htm 模板")
        data = await template_file.read()
        tmp = EXAMPLES_DIR / f"_learn_tmp{ext}"
        tmp.write_bytes(data)
        try:
            yaml_path = Orchestrator(BASE_DIR).run("learn", {"t": str(tmp), "n": name})
        except (ParamWhitelistError, Md2StyleError) as e:
            raise HTTPException(400, f"学习失败: {e}")
        return JSONResponse({"yaml": str(yaml_path),
                             "msg": f"已学习样式 {name}，现在可在转换/预览的样式下拉中选择。"})

    @app.get("/api/style_yaml/{name}")
    def api_get_style_yaml(name: str):
        """读取某风格的 yaml 源文件内容（供前端查看/编辑）。"""
        p = BASE_DIR / "styles" / f"{name}.yaml"
        if not p.exists():
            raise HTTPException(404, f"样式不存在: {name}")
        return {"name": name, "content": p.read_text(encoding="utf-8")}

    @app.post("/api/style_yaml/{name}")
    async def api_save_style_yaml(name: str, request: Request):
        """保存（覆盖）某风格的 yaml 内容；写前用 StyleEngine.resolve 校验合法性。"""
        p = BASE_DIR / "styles" / f"{name}.yaml"
        if not p.exists():
            raise HTTPException(404, f"样式不存在: {name}")
        body = await request.body()
        content = body.decode("utf-8")
        try:
            import yaml as _yaml
            parsed = _yaml.safe_load(content)
            if not isinstance(parsed, dict):
                raise ValueError("顶层必须为映射（mapping）")
        except Exception as e:
            raise HTTPException(400, f"YAML 解析失败，未保存: {e}")
        # 先写回，再用 StyleEngine 验证可被正确加载；失败则回滚，保证磁盘上 yaml 一定合法
        backup = p.read_text(encoding="utf-8")
        p.write_text(content, encoding="utf-8")
        try:
            Orchestrator(BASE_DIR).style_engine.resolve(name)
        except Exception as e:
            p.write_text(backup, encoding="utf-8")
            raise HTTPException(400, f"YAML 不合法（已回滚）: {e}")
        return {"ok": True, "msg": f"样式 {name} 已保存，立即可在转换/预览中使用。"}

    @app.post("/api/style_yaml_new/{name}")
    async def api_new_style_yaml(name: str, request: Request):
        """另存为新样式：仅当 styles/<name>.yaml 不存在时写入，避免覆盖已有样式。"""
        p = BASE_DIR / "styles" / f"{name}.yaml"
        if p.exists():
            raise HTTPException(409, f"样式 {name} 已存在，请用『保存修改』覆盖，或换一个新名字。")
        body = await request.body()
        content = body.decode("utf-8")
        try:
            import yaml as _yaml
            parsed = _yaml.safe_load(content)
            if not isinstance(parsed, dict):
                raise ValueError("顶层必须为映射（mapping）")
        except Exception as e:
            raise HTTPException(400, f"YAML 解析失败，未保存: {e}")
        p.write_text(content, encoding="utf-8")
        try:
            Orchestrator(BASE_DIR).style_engine.resolve(name)
        except Exception as e:
            p.unlink(missing_ok=True)
            raise HTTPException(400, f"YAML 不合法（已删除）: {e}")
        return {"ok": True, "msg": f"已创建新样式 {name}，立即可在转换/预览中使用。"}

    @app.post("/api/style_yaml_blank/{name}")
    async def api_blank_style_yaml(name: str):
        """新建一个空白（最小）样式文件，供在界面里从零开始填写。"""
        p = BASE_DIR / "styles" / f"{name}.yaml"
        if p.exists():
            raise HTTPException(409, f"样式 {name} 已存在，请换一个新名字或直接编辑它。")
        blank = (
            f"# 自定义样式 {name}\n"
            "headings:\n"
            "  h1: { size: 20, color: \"#000000\", font: \"黑体\", align: \"left\" }\n"
            "  h2: { size: 17, color: \"#000000\", font: \"黑体\", align: \"left\" }\n"
            "  h3: { size: 15, color: \"#000000\", font: \"黑体\", align: \"left\" }\n"
            "  h4: { size: 13, color: \"#000000\", font: \"黑体\", align: \"left\" }\n"
            "  h5: { size: 12, color: \"#000000\", font: \"黑体\", align: \"left\" }\n"
            "  h6: { size: 12, color: \"#000000\", font: \"黑体\", align: \"left\" }\n"
            "body:\n"
            "  font: \"宋体\"\n  size: 12\n  color: \"#000000\"\n"
            "  line_height: 1.5\n  para_spacing: 0.5\n"
            "code:\n"
            "  font: \"Consolas\"\n  size: 11\n  color: \"#c7254e\"\n  background: \"#f6f8fa\"\n"
        )
        p.write_text(blank, encoding="utf-8")
        try:
            Orchestrator(BASE_DIR).style_engine.resolve(name)
        except Exception as e:
            p.unlink(missing_ok=True)
            raise HTTPException(400, f"模板不合法（已删除）: {e}")
        return {"ok": True, "msg": f"已新建空白样式 {name}，可在文本框中编辑后保存。"}

    @app.delete("/api/style_yaml/{name}")
    def api_delete_style_yaml(name: str):
        """删除一个样式文件。内置预设也会被删除（前端会二次确认）。"""
        p = BASE_DIR / "styles" / f"{name}.yaml"
        if not p.exists():
            raise HTTPException(404, f"样式不存在: {name}")
        p.unlink()
        return {"ok": True, "msg": f"已删除样式 {name}。"}

    # 静态首页
    @app.get("/", response_class=HTMLResponse)
    def index():
        return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    # 挂载静态资源（如前端有额外 css/js）
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()
