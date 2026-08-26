"""允许 `python -m md2style.interfaces.web` 直接启动 Web 界面（FastAPI + uvicorn）。"""
import uvicorn

from . import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
