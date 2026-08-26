"""Web Interface：FastAPI 本地 Web 服务（原生 HTML/JS 前端，三区 Tab）。

界面层仅采集参数 + 展示结果，业务规则全在 Orchestrator。
特点：
- docx 格式仅支持 公文(official)/论文(paper) 及学习所得（claude/mac 仅用于 html/ppt）
- 提供丰富的「微调」字段：H1-H6 字号/颜色、正文大小/颜色/行距/间距、代码配色
"""

from .app import create_app, app

__all__ = ["create_app", "app"]
