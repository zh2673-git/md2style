# md2style

统一工具：将 **Markdown** 一键转换为 **Word / HTML / PPT**，支持**从 Word/HTML 逆向学习样式**，并可在预设风格基础上**微调字体与间距**。

> 面向两类用户：普通用户用**本地 Web 界面**（无需命令行），自动化/LLM 用**CLI 子命令**（参数经白名单校验，杜绝幻觉扩散）。

---

## 特性

- **多格式输出**：`.docx` / `.html` / `.pptx`
- **预设风格**：
  - HTML / PPT：`claude`（金橙暖调）、`mac`（苹果蓝）
  - Word：公文（`official`）、论文（`paper`）
  - 从 Word/HTML **学习**所得的新风格（立即可用）
- **风格化细节**：
  - HTML：Hero 封面标题、卡片、引用块、代码块、内联强调/链接/图片、页脚
  - PPT：accent 强调标题条、圆角内容卡片（非白底纯字）
  - Word：公文/论文排版（标题分级、首行缩进、段间距）
- **在风格基础上微调**：可覆盖 H1–H6 字号/颜色、正文字体/字号/颜色/行距/段间距、代码块配色
- **逆向学习（Learner）**：拖入任意 Word/HTML 模板，自动提取样式生成 YAML 预设

---

## 安装

需要 Python 3.10+。

```bash
cd <项目根目录>

# 方式一：用 Poetry（推荐）
poetry install

# 方式二：用 pip 安装依赖
pip install python-docx python-pptx Jinja2 Pygments PyYAML markdown-it-py fastapi uvicorn
```

---

## 快速开始

### A. 普通用户：本地 Web 界面（推荐）

```bash
python -m md2style.interfaces.web
```

浏览器打开：<http://127.0.0.1:8080>

界面采用 **FastAPI + 原生 HTML/JS**，顶部三个 Tab 互不阻塞：

1. **转换**：上传 `.md` → 选格式（docx/html/pptx）→ 选样式 → “微调”区默认显示所选风格当前取值，可改后下载
   - 选 docx 时，样式下拉仅显示 `official` / `paper`（公文/论文）；`claude`/`mac` 仅用于 html/pptx
   - **微调为选择器而非手填**：颜色用色板（`<input type="color">`）、字体用下拉、字号/行距/段距用数字框；切换样式自动回填默认值，也可点“恢复所选风格默认”
2. **预览**：选样式 + 可选 H1 颜色/正文字体微调 → 生成临时 HTML 内联显示在页面（无需下载即可看效果）
3. **学习新样式**：上传 Word/HTML 模板，命名后即刻可在“样式”下拉中选择使用
4. **管理样式**（无需上传，直接操作 yaml）：在「学习样式」页的“管理已有样式”卡片里
   - **载入**任意 `.yaml` 查看/编辑、**保存修改**覆盖
   - **新建空白**：填名字即生成最小可编辑骨架，从零写起
   - **另存为新样式**：基于当前内容另存一份（不覆盖原文件）
   - **删除此样式**：删除选中样式（二次确认；内置 `claude`/`mac`/`official`/`paper` 也可删，谨慎操作）

> 想做一键启动，可运行根目录的 `start_web.py`（后台 detached 启动）。
> 接口文档：<http://127.0.0.1:8080/docs>

### B. 自动化 / CLI

```bash
# 转换为 Word（论文风格）
python -m md2style.cli convert -i examples/complex.md -o out.docx -s paper

# 转换为 HTML（claude 风格 + 微调）
python -m md2style.cli convert -i examples/complex.md -o out.html -s claude \
    --h1-size 40 --h2-color #C0392B --body-size 18 --para-spacing 1.4 \
    --code-bg #1E1E1E --code-color #D4D4D4

# 转换为 PPT（mac 风格）
python -m md2style.cli convert -i examples/complex.md -o out.pptx -s mac

# 生成临时 HTML 预览
python -m md2style.cli preview -i examples/complex.md -s claude

# 从模板学习样式
python -m md2style.cli learn -t my_template.docx -n my_company
```

---

## 微调参数一览（CLI）

在所选风格基础上覆盖，留空则用默认：

| 参数 | 说明 |
| --- | --- |
| `--h1-size` … `--h6-size` | H1–H6 字号 |
| `--h1-color` … `--h6-color` | H1–H6 颜色 `#RRGGBB` |
| `--h1-font` … `--h6-font` | H1–H6 字体 |
| `--body-font` | 正文字体 |
| `--body-size` | 正文字号 |
| `--body-color` | 正文颜色 |
| `--line-height` | 正文行距 |
| `--para-spacing` | 段落间距（em） |
| `--code-font` | 代码字体 |
| `--code-size` | 代码字号 |
| `--code-color` | 代码颜色 |
| `--code-bg` | 代码背景 |
| `--template` | docx 模板（dotx）名 |

> Web 界面中与上述一一对应：颜色字段为色板、字体字段为下拉、数字字段为数字框，默认显示当前风格取值。

---

## 项目结构

```
md2style/
├── cli.py                  # CLI 入口（argparse 子命令，参数经白名单校验）
├── orchestrator.py         # 子命令路由 + 参数白名单 + 流程编排
├── core/                   # 常量、IR 数据模型、错误类型
├── engines/
│   ├── md_parser.py        # Markdown -> IR（markdown-it）
│   ├── style_engine.py     # 三层优先级合并 + 校验（DEFAULT < YAML < CLI）
│   └── learner.py          # Word/HTML -> YAML 样式预设
├── renderers/              # 执行层：docx / html / pptx 渲染器
├── interfaces/
│   └── web/                # 本地 Web 界面（FastAPI + 原生 HTML/JS，三区 Tab）
└── utils/                  # 颜色/字体/日志工具
styles/                     # 预设样式 YAML（claude/mac/official/paper/learned_*）
examples/                   # 示例 md 与生成产物
tests/                      # 单元测试
```

---

## 样式优先级

`DEFAULT（硬编码兜底）` < `YAML（预设/学习所得）` < `CLI/Web 微调参数`

合并后经 `StyleEngine.validate` 校验（颜色/字号范围/字体存在性），非法参数直接报错，不会生成脏文件。

---

## 测试

```bash
pytest
```

---

## 设计原则

- **白名单机制**：CLI/Web 仅接受已知参数，未知参数一律拦截，杜绝 LLM 幻觉扩散到下游。
- **界面无业务规则**：Web/CLI 只做参数采集与展示，所有规则在 Orchestrator / Engines / Renderers。
- **可学习**：用户看到好模板即可“拖入即学”，沉淀为可复用的 YAML 预设。
