# Web Interface 递归四层详细设计（模块G，第0级接口·普通用户入口）

> 父本质锚定：md2style 本质是"用声明式样式表 + 参数白名单取代自由文本描述"。
> 本模块本质：在统一映射约束下，Web Interface 是"**用浏览器表单采集参数、复用同一引擎的可视化入口**"（纯 Python 本地服务，不打包 exe 二进制）。

## 数据规范（Specification）
- 表单字段与 CLI 参数一一对应：
  - `input`：Markdown 文件上传（等价 `-i`）
  - `output`：输出路径/格式选择（等价 `-o`，后缀决定 docx/html/pptx）
  - `style`：下拉（**动态加载** `styles/` 目录：内置 论文/公文/claude/mac + 用户学习所得，等价 `-s`）
  - `h1_color`：色板（等价 `--h1-color`）
  - `h1_size`：滑块 8~72（等价 `--h1-size`）
  - `body_font` / `line_height`：等价对应 CLI 微调项
- **学习区（一级功能）**：独立卡片"学习新样式"——拖入 Word 模板 → 填命名 → 提交；成功后 `style` 下拉**即时刷新**出现该风格。
- 返回契约：下载链接（convert/preview）或 yaml 名称（learn）。

## 数据存储（Storage）
- 仅临时持有上传文件（写入系统临时目录，请求结束即清理）。
- 不直接读写 `styles/`；learn 结果经 Orchestrator 落盘。
- 无数据库、无会话持久化（本地单用户）。

## 数据流转（Flow）
```
start(host, port):
  serve_form()                      # 渲染表单
handle_convert(form):
  args = form_to_args(form)         # 表单 -> dict
  Orchestrator.run(namespace(args)) # 复用同一编排，白名单校验照常生效
  return download_link(output_path)
handle_learn(form):   # 调 learn 子命令；成功后将新风格名回写界面下拉（无需重启）
handle_preview(form): # 同上，调 preview 子命令
```
- 事务边界：单次请求内完成；异常由 Orchestrator 抛错，界面层转为友好提示，不崩溃进程。
- 复用性：与 CLI 共用 `Orchestrator.run`，业务规则零重复（满足"界面层不含业务规则"约束）。

## 数据接口（Interface）
```python
def start(host: str = "127.0.0.1", port: int = 8080) -> None: ...
def handle_convert(form: dict) -> str: ...
def handle_learn(form: dict) -> str: ...
def handle_preview(form: dict) -> str: ...
```
- 调用方：浏览器（人类用户）；LLM 仍走 CLI / HTTP 直接调 Orchestrator。
- 稳定性：纯 Python 运行（用户机器 `python -m md2style.interfaces.web`），规避 exe 打包不稳定根因；签名受不变量 I 保护。

## 依赖关系
- 依赖：`orchestrator`（唯一业务入口）、`core/errors`（异常展示）。
- 不依赖：engines/renderers 具体实现（经 Orchestrator 隔离）。
- 约束：界面层不含业务规则，仅参数采集 + 结果展示（依赖铁律：interface 层不越界）。
