# Style Engine 递归四层详细设计（模块A，第1层·核心）

> 父本质锚定：md2style 本质是"用声明式样式表 + 参数白名单取代自由文本描述"。
> 本模块本质：在统一映射引擎约束下，Style Engine 是"**三层优先级合并 + 合法性校验的样式裁决器**"。

## 数据规范（Specification）
- `StyleConfig` 结构（dict）：
  ```yaml
  headings:
    h1: {size: 22, color: "#1A3C5E", font: "思源黑体"}
    h2: {size: 18, color: "#2E5C8A", font: "思源黑体"}
    ...
  body:
    font: "思源黑体"
    size: 10.5
    line_height: 1.5
  ```
- 优先级常量：`PRIORITY = [DEFAULT, YAML, CLI]`（索引递增，后者覆盖前者）。
- 边界常量（`core/constants.py`）：`MIN_SIZE=8, MAX_SIZE=72`。

## 数据存储（Storage）
- 源：`styles/{name}.yaml`（只读加载，PyYAML）。
- 兜底：`core/constants.py` 内 `DEFAULT_STYLE` 硬编码字典。
- 运行期：合并结果仅存内存，不回写预设（保护不变量 I）。

## 数据流转（Flow）
```
resolve(style_name, cli_overrides):
  1. base = DEFAULT_STYLE                        # 优先级1
  2. if yaml exists: base = deep_merge(base, load_yaml(name))   # 优先级2
  3. final = deep_merge(base, cli_overrides)     # 优先级3
  4. validate(final)                             # 合法性裁决
  5. return final
```
- `validate`：遍历 headings/body → `is_valid_hex(color)`、`MIN_SIZE<=size<=MAX_SIZE`、`font_exists(font)`；任一失败抛 `StyleValidationError`。
- 事务边界：合并为纯函数，无副作用，可并发调用。

## 数据接口（Interface）
```python
def resolve(style_name: str, cli_overrides: dict) -> dict: ...
def validate(style_dict: dict) -> None: ...   # 抛 StyleValidationError
```
- 调用方：Orchestrator（convert/preview 流程第2步）。
- 稳定性：签名受不变量 I 保护，不可随意改。

## 递归子模块（如需）
- 暂不拆分子模块；当样式维度扩展到"段落级/字符级/表格级"细分时，可下钻第2层 `style_layers/`。
