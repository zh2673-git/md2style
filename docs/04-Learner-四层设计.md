# Learner 递归四层详细设计（模块D，第1层·核心）

> 父本质锚定：md2style 本质是"用声明式样式表 + 参数白名单取代自由文本描述"。
> 本模块本质（逆向）：Learner 是"**从 Word 版式反推声明式 YAML 的提取器**"，与 Style Engine 构成双向闭环。
> **产品定位**：学习是 md2style 的一等公民与核心黏性——用户看到好模板，拖入即学、立即可用，无需懂 YAML。

## 数据规范（Specification）
- 输出结构：与 `StyleConfig` 同构（headings/h1..hN, body），保证 `learn` 产物可直接被 `resolve` 复用。
- 输入：`.docx` 路径 + 目标 `name`。

## 数据存储（Storage）
- 读：`template.docx`（python-docx `Document`）。
- 写：`styles/<name>.yaml`，首行注释 `# 自动学习自: <template.docx>`。
- 不修改内置预设（保护不变量 I）。

## 数据流转（Flow）
```
learn(docx_path, name):
  1. try: 精准模式 → 读标准样式 'Heading 1'/'Heading 2'/'Normal'
         提取 size/color/font → 映射 headings/body
  2. except 缺失标准样式: 启发式 learn_heuristic(docx_path)
  3. write_yaml(styles/<name>.yaml, config)
  4. print("✅ 已学习样式 <name>，可使用 --style <name> 调用")
```
- `learn_heuristic`：遍历所有段落，按 `font.size` + `bold` 聚类；字号最大且频次最少→H1，次大→H2，频次最多→body；主色取首个非黑颜色。
- **Web 一键学习闭环**：用户在界面拖入 Word → `handle_learn(form)` 调 `learn` → 生成 yaml 后界面下拉框**实时刷新**出现新风格，无需重启；learn 结果经 Orchestrator 落盘，与内置 `paper/official/claude/mac` 同等可选。
- 事务边界：解析与写文件为原子操作，失败回滚不生成半截 YAML。

## 数据接口（Interface）
```python
def learn(docx_path: str, name: str) -> str: ...        # 返回 yaml 路径
def learn_heuristic(docx_path: str) -> dict: ...          # 返回 StyleConfig 同构 dict
```
- 调用方：Orchestrator（learn 子命令）。
- 稳定性：签名受不变量 I 保护。

## 闭环验证（与 Style Engine 互通）
- 不变量：learn 输出 YAML 必须能被 `style_engine.resolve(name, {})` 完整加载且 `validate` 通过。
- 测试用例：`learn(sample.docx, temp) → resolve('temp', {}) → validate` 全绿。
