"""
Q-Spark Studio — 服务启动与组装入口
"""
import asyncio
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

# 过滤高频的 /api/metrics 心跳日志，避免终端刷屏
class MetricsEndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/api/metrics" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(MetricsEndpointFilter())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from engine import engine, OUTPUTS_DIR, BASE_DIR
from api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    checker_task = asyncio.create_task(engine.idle_checker_loop())

    def _auto_open_browser():
        import urllib.request
        import webbrowser
        for _ in range(60):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen("http://127.0.0.1:40188/api/vram/status", timeout=1):
                    webbrowser.open("http://127.0.0.1:40188/")
                    break
            except Exception:
                pass

    if os.environ.get("NO_BROWSER") != "1":
        threading.Thread(target=_auto_open_browser, daemon=True).start()

    yield
    checker_task.cancel()
    engine.stop_server()


app = FastAPI(title="Q-Spark Studio", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源与图片输出挂载
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 挂载核心 API 路由
app.include_router(router)


@app.get("/")
async def serve_index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/app.ico")
async def serve_favicon():
    ico_path = BASE_DIR / "app.ico"
    if ico_path.exists():
        return FileResponse(ico_path)
    return ""


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("Q-Spark Studio 服务启动中...")
    print("Web 交互界面: http://127.0.0.1:40188")
    print("Agent API 地址: http://127.0.0.1:40188/v1/images/generations")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=40188)
