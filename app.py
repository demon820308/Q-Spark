import asyncio
import base64
import math
import os
import random
import re
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

# 确保 Windows 控制台字符编码安全
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import gradio as gr
import httpx
import psutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

# ==============================================================================
# 1. 基础路径与全局配置
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
BIN_DIR = BASE_DIR / "bin"
CONFIG_FILE = BASE_DIR / "config.json"

def to_rel_or_abs(p: Path | str) -> str:
    """如果路径在工程根目录下，返回相对路径；否则返回原始路径"""
    try:
        resolved = Path(p).resolve()
        return str(resolved.relative_to(BASE_DIR))
    except (ValueError, RuntimeError):
        return str(p)

def load_config() -> dict:
    default_cfg = {
        "models_dir": "models",
        "outputs_dir": "outputs",
        "api_diff_model": "Qwen-Image-2.1-Turbo-AD-Q4_K.gguf",
        "api_te_model": "Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf",
        "api_vae_model": "qwen_image_2.1_vae_bf16.safetensors",
        "api_steps": 8,
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_cfg.update(loaded)
        except Exception:
            pass
    return default_cfg

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Warning] 写入 config.json 失败: {e}")

APP_CONFIG = load_config()

_raw_models = APP_CONFIG.get("models_dir", "models")
MODELS_DIR = Path(_raw_models) if Path(_raw_models).is_absolute() else (BASE_DIR / _raw_models).resolve()

_raw_outputs = APP_CONFIG.get("outputs_dir", "outputs")
OUTPUTS_DIR = Path(_raw_outputs) if Path(_raw_outputs).is_absolute() else (BASE_DIR / _raw_outputs).resolve()
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def get_api_model_status_text() -> str:
    saved_m = APP_CONFIG.get("api_diff_model")
    saved_s = APP_CONFIG.get("api_steps")
    if saved_m:
        step_str = f"{saved_s} 步" if saved_s else "自动匹配"
        return f"📌 **当前外部 API 默认生效模型**：`{saved_m}`（{step_str}）"
    return "📌 **当前外部 API 默认生效模型**：跟随首选模型（可点击下方按钮保存指定）"

SD_CLI_EXE = BIN_DIR / "sd-cli.exe"
SD_SERVER_EXE = BIN_DIR / "sd-server.exe"

# Turbo 专属优化参数
TURBO_SIGMAS = "1.0,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0.0"

def get_viggle_6step_sigmas(width: int, height: int) -> str:
    """根据图像分辨率动态计算 Viggle 6-Step 专属 Sigmas 调度表 (等同于 ComfyUI ViggleTurboSigmas 节点)"""
    tokens = (width // 16) * (height // 16)
    mu = 0.5 + (0.9 - 0.5) * (tokens - 256) / (8192 - 256)
    nodes = [1.0, 0.9375, 0.875, 0.75, 0.5, 0.25]
    sigmas = [math.exp(mu) / (math.exp(mu) + (1.0 / t - 1.0)) for t in nodes] + [0.0]
    return ",".join(f"{s:.6f}" for s in sigmas)

DEFAULT_STEPS = 8
DEFAULT_CFG = 1.0
DEFAULT_SAMPLER = "euler"

# ==============================================================================
# 2. 动态扫描可用模型与硬件监测指标
# ==============================================================================
def get_sub_dir(root: Path, names: list[str]) -> Path:
    for name in names:
        p = root / name
        if p.exists() and p.is_dir():
            return p
    return root / names[0]

def resolve_model_file(subfolder_names: list[str], filename: str) -> Path:
    """在模型根目录下查找指定子目录中的具体模型文件"""
    global MODELS_DIR
    for folder in subfolder_names:
        candidate = MODELS_DIR / folder / filename
        if candidate.exists():
            return candidate
    return MODELS_DIR / subfolder_names[0] / filename

def scan_models(base_path: Optional[Path | str] = None):
    global MODELS_DIR
    root = Path(base_path) if base_path else MODELS_DIR
    diff_dir = get_sub_dir(root, ["diffusion_models", "diffusion"])
    te_dir = get_sub_dir(root, ["text_encoders", "text_encoder"])
    vae_dir = root / "vae"

    valid_exts = {".gguf", ".safetensors"}

    diff_models = [
        f.name for f in diff_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts
    ] if diff_dir.exists() else []

    te_models = [
        f.name for f in te_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts and not f.name.startswith("mmproj")
    ] if te_dir.exists() else []

    vae_models = [
        f.name for f in vae_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts
    ] if vae_dir.exists() else []

    # 优先将 Qwen 相关的模型置顶排在前列，避免被其它模型（如 minimax/ace）占位
    def sort_qwen(items: list[str]) -> list[str]:
        qwen_items = [x for x in items if "qwen" in x.lower()]
        other_items = [x for x in items if "qwen" not in x.lower()]
        return qwen_items + other_items

    diff_models = sort_qwen(diff_models)
    te_models = sort_qwen(te_models)
    vae_models = sort_qwen(vae_models)

    return (
        diff_models or ["Qwen-Image-2.1-Turbo-AD-Q4_K.gguf"],
        te_models or ["Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf"],
        vae_models or ["qwen_image_2.1_vae_bf16.safetensors"],
    )

def get_system_metrics_html() -> str:
    """实时采集 GPU 显存、物理内存与 CPU 占用率，并渲染为暗色进度条"""
    # 1. CPU
    try:
        cpu_pct = psutil.cpu_percent(interval=None)
    except Exception:
        cpu_pct = 0.0

    # 2. RAM 内存
    try:
        mem = psutil.virtual_memory()
        ram_u = mem.used / (1024**3)
        ram_t = mem.total / (1024**3)
        ram_pct = mem.percent
    except Exception:
        ram_u, ram_t, ram_pct = 0.0, 16.0, 0.0

    # 3. GPU 显存 (通过 nvidia-smi 毫秒级极速采集)
    vram_u, vram_t, vram_pct = 0.0, 10.0, 0.0
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,nounits,noheader"],
            text=True,
            timeout=0.6,
        ).strip()
        parts = [float(x.strip()) for x in out.split(",")]
        vram_u = parts[0] / 1024.0
        vram_t = parts[1] / 1024.0
        vram_pct = (vram_u / vram_t) * 100 if vram_t > 0 else 0.0
    except Exception:
        pass

    def get_bar_class(pct: float) -> str:
        if pct >= 88:
            return "bar-danger"
        if pct >= 75:
            return "bar-warn"
        return "bar-normal"

    v_cls = get_bar_class(vram_pct)
    r_cls = get_bar_class(ram_pct)
    c_cls = get_bar_class(cpu_pct)

    return f"""
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-row">
                <span class="metric-name">🎮 GPU 显存 (VRAM)</span>
                <span class="metric-val">{vram_u:.2f} / {vram_t:.1f} GB ({vram_pct:.0f}%)</span>
            </div>
            <div class="metric-progress-bg">
                <div class="metric-progress-bar {v_cls}" style="width: {min(100, vram_pct):.1f}%;"></div>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-row">
                <span class="metric-name">💾 物理内存 (RAM)</span>
                <span class="metric-val">{ram_u:.1f} / {ram_t:.1f} GB ({ram_pct:.0f}%)</span>
            </div>
            <div class="metric-progress-bg">
                <div class="metric-progress-bar {r_cls}" style="width: {min(100, ram_pct):.1f}%;"></div>
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-row">
                <span class="metric-name">⚡ 处理器占用 (CPU)</span>
                <span class="metric-val">{cpu_pct:.0f}%</span>
            </div>
            <div class="metric-progress-bg">
                <div class="metric-progress-bar {c_cls}" style="width: {min(100, cpu_pct):.1f}%;"></div>
            </div>
        </div>
    </div>
    """

# ==============================================================================
# 3. 显存策略与推理引擎调度器 (Inference Engine)
# ==============================================================================
class InferenceEngine:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.mode = "on_demand"
        self.idle_timeout = 300
        self.last_active = time.time()
        self.server_process: Optional[subprocess.Popen] = None
        self.server_port = 40189
        self.current_model_config = {}

    def get_status_text(self):
        is_running = self.server_process is not None and self.server_process.poll() is None
        if self.mode == "on_demand":
            return "即用即走（按需模式，闲置 0MB 显存）"
        if is_running:
            idle_left = max(0, int(self.idle_timeout - (time.time() - self.last_active)))
            if self.mode == "auto_unload":
                return f"常驻运行中（智能休眠，剩余 {idle_left}s 无请求释放）"
            return "常驻运行中（显存常驻模式）"
        return "休眠中（显存已释放，等待下次请求唤醒）"

    def stop_server(self):
        """强制终止后台常驻服务，物理级回收所有显存"""
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            self.server_process = None
            return "已成功终止常驻进程，显存已清空归零。"
        return "当前无后台常驻进程，显存处于空闲状态。"

    async def _stream_sd_cli(self, cmd, cwd) -> AsyncGenerator[dict, None]:
        """异步生成器：实时流式输出控制台日志 + 产出结构化进度事件"""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        error_lines = []
        current_pct = 0.05
        current_desc = "正在初始化推理环境..."

        yield {"pct": current_pct, "desc": current_desc, "log": ">>> 正在启动推理子进程...\n"}

        while True:
            line_bytes = await proc.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8", errors="replace")

            # 1. 实时写到终端控制台
            sys.stdout.write(line)
            sys.stdout.flush()

            error_lines.append(line)
            if len(error_lines) > 40:
                error_lines.pop(0)

            # 2. 解析进度
            m = re.search(r'\|\s*(\d+)/(\d+)', line)
            if m:
                cur, tot = int(m.group(1)), int(m.group(2))
                if tot == 397:
                    current_pct = 0.05 + 0.20 * (cur / tot)
                    current_desc = f"加载文本编码器模型 ({cur}/397)..."
                elif tot == 265:
                    current_pct = 0.25 + 0.10 * (cur / tot)
                    current_desc = f"加载 DiT 降噪模型 ({cur}/265)..."
                elif tot == 128:
                    current_pct = 0.90 + 0.09 * (cur / tot)
                    current_desc = f"VAE 高清解码渲染中 ({cur}/128)..."
                else:
                    current_pct = 0.40 + 0.50 * (cur / tot)
                    current_desc = f"采样去噪进行中 ({cur}/{tot} 步)..."
            elif "get_learned_condition completed" in line:
                current_pct = 0.35
                current_desc = "提示词编码完成，开始去噪采样..."
            elif "sampling completed" in line:
                current_pct = 0.90
                current_desc = "去噪完成，正在进行 VAE 解码..."
            elif "generate_image completed" in line:
                current_pct = 1.0
                current_desc = "图像生成完成！"

            yield {"pct": current_pct, "desc": current_desc, "log": line}

        ret = await proc.wait()
        if ret != 0:
            err_msg = "".join(error_lines[-15:])
            raise RuntimeError(f"sd-cli 执行失败 (代码 {ret}):\n{err_msg}")

    async def ensure_server(
        self,
        diff_model: str,
        te_model: str,
        vae_model: str,
        steps: Optional[int] = None,
        width: int = 1024,
        height: int = 1024,
    ):
        target_steps = int(steps) if (steps is not None and int(steps) > 0) else (6 if "6step" in (diff_model or "").lower() else DEFAULT_STEPS)

        target_config = {
            "diff": diff_model,
            "te": te_model,
            "vae": vae_model,
            "steps": target_steps,
        }

        if self.server_process and self.server_process.poll() is None:
            if self.current_model_config == target_config:
                return True
            self.stop_server()

        diff_path = resolve_model_file(["diffusion_models", "diffusion"], diff_model)
        te_path = resolve_model_file(["text_encoders", "text_encoder"], te_model)
        vae_path = resolve_model_file(["vae"], vae_model)

        cmd = [
            str(SD_SERVER_EXE),
            "--diffusion-model", to_rel_or_abs(diff_path),
            "--llm", to_rel_or_abs(te_path),
            "--vae", to_rel_or_abs(vae_path),
            "--listen-ip", "127.0.0.1",
            "--listen-port", str(self.server_port),
            "--steps", str(target_steps),
            "--cfg-scale", str(DEFAULT_CFG),
            "--sampling-method", DEFAULT_SAMPLER,
            "-s", "-1",
            "--diffusion-fa",
        ]
        if target_steps == 6:
            cmd.extend(["--sigmas", get_viggle_6step_sigmas(width, height)])
        elif target_steps == 8:
            cmd.extend(["--sigmas", TURBO_SIGMAS])

        self.server_process = subprocess.Popen(cmd, cwd=str(BASE_DIR))
        self.current_model_config = target_config

        for _ in range(90):
            await asyncio.sleep(1)
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    resp = await client.get(f"http://127.0.0.1:{self.server_port}/v1/models")
                    if resp.status_code == 200:
                        return True
            except Exception:
                pass
            if self.server_process.poll() is not None:
                raise RuntimeError("sd-server 进程意外退出，请检查显存。")
        raise TimeoutError("等待 sd-server 启动超时。")

    async def generate_image_stream(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        seed: int = -1,
        diff_model: str = "",
        te_model: str = "",
        vae_model: str = "",
    ) -> AsyncGenerator[dict, None]:
        async with self.lock:
            self.last_active = time.time()
            if seed == -1:
                seed = random.randint(1, 2**31 - 1)

            diff_list, te_list, vae_list = scan_models()
            diff_model = diff_model or APP_CONFIG.get("api_diff_model") or diff_list[0]
            te_model = te_model or APP_CONFIG.get("api_te_model") or te_list[0]
            vae_model = vae_model or APP_CONFIG.get("api_vae_model") or vae_list[0]

            if steps is None or int(steps) <= 0:
                steps = 6 if "6step" in (diff_model or "").lower() else (APP_CONFIG.get("api_steps") or DEFAULT_STEPS)
            steps = int(steps)

            out_filename = f"img_{int(time.time())}_{seed}.png"
            out_filepath = OUTPUTS_DIR / out_filename

            diff_path = resolve_model_file(["diffusion_models", "diffusion"], diff_model)
            te_path = resolve_model_file(["text_encoders", "text_encoder"], te_model)
            vae_path = resolve_model_file(["vae"], vae_model)

            cmd = [
                str(SD_CLI_EXE),
                "--diffusion-model", to_rel_or_abs(diff_path),
                "--llm", to_rel_or_abs(te_path),
                "--vae", to_rel_or_abs(vae_path),
                "-p", prompt,
                "--steps", str(steps),
                "--cfg-scale", str(DEFAULT_CFG),
                "--sampling-method", DEFAULT_SAMPLER,
                "-W", str(width),
                "-H", str(height),
                "-s", str(seed),
                "--diffusion-fa",
                "-o", to_rel_or_abs(out_filepath),
            ]
            if steps == 6:
                cmd.extend(["--sigmas", get_viggle_6step_sigmas(width, height)])
            elif steps == 8:
                cmd.extend(["--sigmas", TURBO_SIGMAS])

            # 策略 A：按需冷启动模式 (流式输出 + 实时进度)
            if self.mode == "on_demand":
                async for event in self._stream_sd_cli(cmd, cwd=BASE_DIR):
                    yield event
                yield {"pct": 1.0, "desc": "完成！", "log": "", "out_path": str(out_filepath), "diff_model": diff_model}
                return

            # 策略 B & C：常驻或自动休眠模式
            try:
                yield {"pct": 0.15, "desc": "准备常驻推理服务...", "log": ">>> 正在连接常驻模型服务...\n"}
                await self.ensure_server(diff_model, te_model, vae_model, steps=steps, width=width, height=height)
                yield {"pct": 0.45, "desc": "服务已就绪，正在进行 GPU 高速去噪...", "log": ">>> 开始发送生图任务...\n"}
                async with httpx.AsyncClient(timeout=300.0) as client:
                    resp = await client.post(
                        f"http://127.0.0.1:{self.server_port}/v1/images/generations",
                        json={
                            "prompt": prompt,
                            "size": f"{width}x{height}",
                            "seed": seed,
                            "response_format": "b64_json",
                        },
                    )
                    if resp.status_code != 200:
                        raise RuntimeError(f"sd-server 返回错误: {resp.text}")
                    data = resp.json()
                    b64_str = data["data"][0]["b64_json"]
                    img_bytes = base64.b64decode(b64_str)
                    with open(out_filepath, "wb") as f:
                        f.write(img_bytes)
                    yield {"pct": 1.0, "desc": "生成完成！", "log": ">>> 图像已成功保存。\n", "out_path": str(out_filepath), "diff_model": diff_model}
                    return
            except Exception as e:
                print(f"\n[Warning] 常驻模式异常，正在降级回退至 sd-cli 流式执行: {e}\n")
                self.stop_server()
                async for event in self._stream_sd_cli(cmd, cwd=BASE_DIR):
                    yield event
                yield {"pct": 1.0, "desc": "完成！", "log": "", "out_path": str(out_filepath), "diff_model": diff_model}

    async def idle_checker_loop(self):
        while True:
            await asyncio.sleep(10)
            if self.mode == "auto_unload" and self.server_process:
                if time.time() - self.last_active > self.idle_timeout:
                    self.stop_server()

engine = InferenceEngine()

# ==============================================================================
# 4. FastAPI 服务生命周期与 OpenAI 兼容 API
# ==============================================================================
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

app = FastAPI(title="Qwen-Image-Turbo SD.cpp Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

class OpenAIGenRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    prompt: str
    size: Optional[str] = "1024x1024"
    n: Optional[int] = 1
    response_format: Optional[str] = "url"
    steps: Optional[int] = DEFAULT_STEPS

class OpenAIChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: Optional[str] = "qwen-image-2.1-turbo"
    messages: list[dict]
    stream: Optional[bool] = False

@app.get("/api/vram/status")
async def get_vram_status():
    return {"status": engine.get_status_text(), "mode": engine.mode}

@app.post("/api/vram/flush")
async def flush_vram_api():
    msg = engine.stop_server()
    return {"message": msg}

@app.get("/v1/models")
@app.get("/models")
async def openai_get_models():
    """返回符合 OpenAI 规范的模型列表，供 Agent 客户端（如 Cherry Studio）一键自动导入模型"""
    model_ids = ["qwen-image-2.1-turbo", "dall-e-3"]
    return {
        "object": "list",
        "data": [
            {
                "id": m_id,
                "object": "model",
                "created": 1700000000,
                "owned_by": "local",
                "permission": [],
                "root": m_id,
                "parent": None,
            }
            for m_id in model_ids
        ],
    }

ASPECT_RATIO_PRESETS = {
    "1:1": (1024, 1024),
    "3:4": (768, 1024),
    "4:3": (1024, 768),
    "9:16": (768, 1360),
    "16:9": (1360, 768),
    "2:3": (832, 1248),
    "3:2": (1248, 832),
    "21:9": (1536, 640),
}

def _extract_from_text(text: Optional[str]) -> Optional[tuple[int, int]]:
    """从文本中提取尺寸或比例：支持 --ar 16:9、1792x1024、1024*1792、16:9、1:1 等"""
    if not text:
        return None
    s = text.strip()

    # 1. 优先提取显式 --ar X:Y 语法 (如 --ar 16:9, -ar 9:16, --ar 16/9, --ar 16：9)
    m_ar = re.search(r'--?ar\s+(\d+[:/：]\d+)', s, re.IGNORECASE)
    if m_ar:
        r = m_ar.group(1).replace("/", ":").replace("：", ":")
        if r in ASPECT_RATIO_PRESETS:
            return ASPECT_RATIO_PRESETS[r]

    # 2. 提取显式分辨率: 1792x1024, 1024*1792, 1024x1024, 1024*1024, 1792*1024 等
    m_dim = re.search(r'(?<!\d)(\d{3,4})\s*[\*xX×]\s*(\d{3,4})(?!\d)', s)
    if m_dim:
        try:
            w = int(m_dim.group(1))
            h = int(m_dim.group(2))
            w = max(256, min(2048, round(w / 16) * 16))
            h = max(256, min(2048, round(h / 16) * 16))
            return w, h
        except Exception:
            pass

    # 3. 提取独立比例预设: 1:1, 16:9, 9:16, 4:3, 3:4, 2:3, 3:2, 21:9 等
    for m_ratio in re.finditer(r'(?<!\d)(\d{1,2})\s*[:/：]\s*(\d{1,2})(?!\d)', s):
        ratio_key = f"{m_ratio.group(1)}:{m_ratio.group(2)}"
        if ratio_key in ASPECT_RATIO_PRESETS:
            return ASPECT_RATIO_PRESETS[ratio_key]

    return None

def resolve_dimensions(size_str: Optional[str] = None, prompt_str: str = "") -> tuple[int, int]:
    """智能解析尺寸与比例：支持分辨率 (1792x1024 / 1024*1792)、比例 (16:9, 9:16, 1:1, 4:3, 3:4) 以及 --ar 16:9"""
    # 1. 优先提取 prompt 中显式指定的比例/分辨率 (用户本次输入的具体意图)
    dim_from_prompt = _extract_from_text(prompt_str)
    if dim_from_prompt:
        return dim_from_prompt

    # 2. 若 prompt 未指定，则提取 size 参数中的尺寸或比例
    if size_str:
        dim_from_size = _extract_from_text(size_str)
        if dim_from_size:
            return dim_from_size

    # 3. 兜底默认 1024x1024
    return 1024, 1024

@app.post("/v1/images/generations")
@app.post("/images/generations")
async def openai_images_generations(req: OpenAIGenRequest):
    w, h = resolve_dimensions(req.size, req.prompt)

    start_t = time.time()
    out_path = None
    actual_diff_model = APP_CONFIG.get("api_diff_model", "")
    try:
        async for event in engine.generate_image_stream(
            prompt=req.prompt, width=w, height=h, steps=req.steps
        ):
            if "out_path" in event:
                out_path = event["out_path"]
            if "diff_model" in event:
                actual_diff_model = event["diff_model"]
        if not out_path:
            raise RuntimeError("生图流程未产出有效图片路径。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = os.path.basename(out_path)
    url_link = f"http://127.0.0.1:40188/outputs/{filename}"

    with open(out_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")

    return {
        "created": int(start_t),
        "data": [
            {
                "url": url_link,
                "b64_json": b64_data,
                "revised_prompt": f"Model: {actual_diff_model}",
            }
        ],
    }

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def openai_chat_completions(req: OpenAIChatRequest):
    """兼容对话补全协议 (openai-completions)，允许在 Agent 对话框内直接出图"""
    prompt = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                prompt = content.strip()
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        prompt = part.get("text", "").strip()
            if prompt:
                break

    if not prompt:
        prompt = "a beautiful landscape"

    w, h = resolve_dimensions(prompt_str=prompt)
    steps = None
    m_steps = re.search(r'--?steps?\s+(\d+)', prompt, re.IGNORECASE)
    if m_steps:
        try:
            steps = int(m_steps.group(1))
        except Exception:
            pass

    created_t = int(time.time())
    chat_id = f"chatcmpl-{created_t}-{random.randint(1000, 9999)}"
    model_name = req.model or "qwen-image-2.1-turbo"

    if req.stream:
        async def chat_stream_generator():
            out_path = None
            last_reported_desc = ""
            actual_diff_model = APP_CONFIG.get("api_diff_model", "")
            start_t = time.time()
            try:
                # 1. 发送助手角色与思考块开头（Cherry Studio 等客户端会自动折叠并展示思考状态卡片）
                step_hint = f" | 步数: {steps}" if steps else ""
                init_chunks = [
                    {"role": "assistant"},
                    {"content": "<think>\n"},
                    {"content": f"> 🚀 硬件平台: 本地 NVIDIA GPU | 生图规格: {w}x{h}{step_hint}\n"},
                ]
                for c in init_chunks:
                    chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "created": created_t,
                        "model": model_name,
                        "choices": [{"index": 0, "delta": c, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"

                # 2. 监听流式推理事件，实时向 Agent 对话框推送阶段进度
                async for event in engine.generate_image_stream(prompt=prompt, width=w, height=h, steps=steps):
                    desc = event.get("desc", "")
                    if desc and desc != last_reported_desc:
                        # 过滤过于琐碎的模型层数加载细节，保持思考流精炼
                        if "397" in desc or "265" in desc:
                            if not last_reported_desc.startswith("正在加载模型"):
                                desc_line = "> ⚙️ 正在载入多模态模型权重...\n"
                                last_reported_desc = "正在加载模型"
                            else:
                                continue
                        else:
                            last_reported_desc = desc
                            desc_line = f"> ⏳ {desc}\n"

                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "created": created_t,
                            "model": model_name,
                            "choices": [{"index": 0, "delta": {"content": desc_line}, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                    if "out_path" in event:
                        out_path = event["out_path"]
                    if "diff_model" in event:
                        actual_diff_model = event["diff_model"]

                cost = time.time() - start_t
                # 3. 闭合思考标签
                close_think_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_t,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": f"> ✨ 推理生成完成，耗时 {cost:.1f}s\n</think>\n\n"}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(close_think_chunk)}\n\n"

                # 4. 推送最终高清图像 Markdown（附带当前实际调用的主模型名称）
                if out_path:
                    filename = os.path.basename(out_path)
                    url_link = f"http://127.0.0.1:40188/outputs/{filename}"
                    model_display = f" ｜ 🧩 当前主模型: `{actual_diff_model}`" if actual_diff_model else ""
                    content_str = f"![image]({url_link})\n\n[🔍 点击查看高清原图]({url_link}){model_display}"
                else:
                    content_str = "❌ 图像生成未产出有效文件。"

                content_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_t,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": content_str}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(content_chunk)}\n\n"

            except Exception as e:
                err_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created_t,
                    "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": f"\n</think>\n\n❌ 生成出错: {str(e)}"}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(err_chunk)}\n\n"

            stop_chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": created_t,
                "model": model_name,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(stop_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(chat_stream_generator(), media_type="text/event-stream")

    out_path = None
    actual_diff_model = APP_CONFIG.get("api_diff_model", "")
    try:
        async for event in engine.generate_image_stream(prompt=prompt, width=w, height=h, steps=steps):
            if "out_path" in event:
                out_path = event["out_path"]
            if "diff_model" in event:
                actual_diff_model = event["diff_model"]
        if not out_path:
            raise RuntimeError("生图流程未产出有效图片路径。")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    filename = os.path.basename(out_path)
    url_link = f"http://127.0.0.1:40188/outputs/{filename}"
    model_display = f" ｜ 🧩 当前主模型: `{actual_diff_model}`" if actual_diff_model else ""
    reply_content = f"![image]({url_link})\n\n[🔍 点击查看高清原图]({url_link}){model_display}"

    return {
        "id": chat_id,
        "object": "chat.completion",
        "created": created_t,
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt),
            "completion_tokens": len(reply_content),
            "total_tokens": len(prompt) + len(reply_content),
        },
    }

# ==============================================================================
# 5. 全局暗黑系风格设计 (Dark Theme) + 硬件监测 + 网页实时进度条
# ==============================================================================
CLAUDE_DARK_CSS = """
/* 全局暗色调设计规范 (Claude Dark System) */
:root, html, body {
    background-color: #121110 !important;
    color: #edeae2 !important;
    color-scheme: dark !important;
}

.gradio-container {
    background-color: #121110 !important;
    color: #edeae2 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif !important;
}

/* 顶部标题栏 */
.dark-header {
    border-bottom: 1px solid #292623;
    padding-bottom: 12px;
    margin-bottom: 16px;
}
.dark-title {
    font-family: 'Copernicus', 'Georgia', serif !important;
    font-size: 2.1rem !important;
    font-weight: 400 !important;
    letter-spacing: -0.5px !important;
    color: #faf8f5 !important;
}
.dark-subtitle {
    color: #9c978f;
    font-size: 0.90rem;
    margin-top: 4px;
}

/* 硬件监控指标进度条面板 */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 18px;
}
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
}
.metric-card {
    background-color: #1a1816;
    border: 1px solid #2e2a25;
    border-radius: 10px;
    padding: 10px 14px;
}
.metric-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.84rem;
    margin-bottom: 6px;
    color: #d1ccc2;
}
.metric-val {
    font-weight: 600;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    color: #faf8f5;
}
.metric-progress-bg {
    background-color: #26231f;
    border-radius: 5px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}
.metric-progress-bar {
    height: 100%;
    transition: width 0.4s ease;
}
.bar-normal {
    background: linear-gradient(90deg, #cc785c, #e0967d);
}
.bar-warn {
    background: linear-gradient(90deg, #d4a017, #e8a55a) !important;
}
.bar-danger {
    background: linear-gradient(90deg, #c64545, #e06c6c) !important;
}

/* 卡片容器 */
.dark-card {
    background-color: #1c1a17 !important;
    border: 1px solid #2e2a25 !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

/* 输入框、下拉菜单、单选框暗黑化 */
input, textarea, select, .gr-input, .gr-box, .gr-check-radio {
    background-color: #161513 !important;
    color: #faf8f5 !important;
    border-color: #332f2a !important;
}

/* 珊瑚色主按钮 */
.btn-coral {
    background-color: #cc785c !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
    padding: 10px 20px !important;
    transition: background-color 0.2s ease !important;
}
.btn-coral:hover {
    background-color: #dd8a6e !important;
}

.btn-flush {
    border: 1px solid #c64545 !important;
    color: #e06c6c !important;
    background: transparent !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}
.btn-flush:hover {
    background-color: rgba(198, 69, 69, 0.15) !important;
}

/* 实时终端日志框 */
.dark-terminal-card {
    background-color: #141311 !important;
    border: 1px solid #292623 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    color: #c9c4b7 !important;
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
    font-size: 0.82rem !important;
}

/* 进度条与状态遮罩定制：彻底屏蔽日志框与信息框的 loading 遮罩，日志框恢复纯净滚动 */
#live-logs-box .generating,
#live-logs-box .loading,
#live-logs-box .progress-level-inner,
#live-logs-box .progress-text,
#live-logs-box .meta-text,
#live-logs-box .wrap.minimal,
#gen-info .generating,
#gen-info .loading,
#gen-info .progress-level-inner {
    display: none !important;
    opacity: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* Gradio 画布原生进度条暗色主题美化 */
.progress-level-inner, .progress-bar {
    background: linear-gradient(90deg, #cc785c, #e0967d) !important;
}

/* 快捷预设卡片平铺网格：一行 5 个卡片药丸布局 */
.preset-radio-grid {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin-bottom: 12px !important;
}
.preset-radio-grid > .wrap,
.preset-radio-grid fieldset {
    display: grid !important;
    grid-template-columns: repeat(5, 1fr) !important;
    gap: 6px !important;
    border: none !important;
    padding: 0 !important;
}
@media (max-width: 900px) {
    .preset-radio-grid > .wrap,
    .preset-radio-grid fieldset {
        grid-template-columns: repeat(2, 1fr) !important;
    }
}
.preset-radio-grid label {
    background-color: #161513 !important;
    border: 1px solid #2e2a25 !important;
    border-radius: 8px !important;
    padding: 8px 4px !important;
    cursor: pointer !important;
    font-size: 0.78rem !important;
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
    color: #edeae2 !important;
    transition: all 0.2s ease !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}
.preset-radio-grid label:hover {
    border-color: #cc785c !important;
    background-color: #211e1a !important;
}
.preset-radio-grid label.selected,
.preset-radio-grid input[type="radio"]:checked + span {
    border-color: #cc785c !important;
    color: #cc785c !important;
}
.preset-radio-grid label:has(input:checked) {
    border-color: #cc785c !important;
    background-color: rgba(204, 120, 92, 0.15) !important;
}

/* 实时终端日志框自动锁定最新行 */
#live-logs-box textarea {
    overflow-anchor: auto !important;
    scroll-behavior: smooth !important;
}
"""

diff_choices, te_choices, vae_choices = scan_models()
default_diff = APP_CONFIG.get("api_diff_model")
if not default_diff or default_diff not in diff_choices:
    default_diff = diff_choices[0] if diff_choices else None

default_te = APP_CONFIG.get("api_te_model")
if not default_te or default_te not in te_choices:
    default_te = te_choices[0] if te_choices else None

default_vae = APP_CONFIG.get("api_vae_model")
if not default_vae or default_vae not in vae_choices:
    default_vae = vae_choices[0] if vae_choices else None

default_steps = APP_CONFIG.get("api_steps")
if not default_steps:
    default_steps = 6 if default_diff and "6step" in default_diff.lower() else 8

with gr.Blocks(title="Q-Spark Studio") as demo:
    gr.HTML(f"<style>{CLAUDE_DARK_CSS}</style>")

    # 顶部品牌条
    with gr.Row(elem_classes=["dark-header"]):
        with gr.Column(scale=8):
            gr.Markdown(
                """
                <div class="dark-title">Q-Spark Studio</div>
                <div class="dark-subtitle">生图控制台· stable-diffusion.cpp 引擎  · 支持 Agent API</div>
                """
            )
        with gr.Column(scale=4):
            vram_badge = gr.Markdown(value=f"**显存状态**：{engine.get_status_text()}")
            flush_btn = gr.Button("⚡ 立即清空显存 (Flush VRAM)", elem_classes=["btn-flush"])

    # 硬件监控进度条面板 (VRAM / RAM / CPU)
    metrics_display = gr.HTML(value=get_system_metrics_html())
    metrics_timer = gr.Timer(value=2.5)
    metrics_timer.tick(fn=get_system_metrics_html, outputs=[metrics_display])

    # 主工作区
    with gr.Row():
        with gr.Column(scale=5, elem_classes=["dark-card"]):
            prompt_input = gr.Textbox(
                label="提示词 (Prompt)",
                placeholder="输入希望生成的画面描述（支持中英文，已去除所有审查限制）...",
                lines=5,
            )

            # 常用分辨率与画幅比例预设
            RESOLUTION_PRESETS = {
                "1:1 (1024x1024)": (1024, 1024),
                "3:4 (768x1024)": (768, 1024),
                "3:4 (864x1152)": (864, 1152),
                "9:16 (768x1360)": (768, 1360),
                "2:3 (832x1248)": (832, 1248),
                "4:3 (1024x768)": (1024, 768),
                "16:9 (1360x768)": (1360, 768),
                "3:2 (1248x832)": (1248, 832),
                "21:9 (1536x640)": (1536, 640),
                "1:1 (512x512)": (512, 512),
            }

            preset_res = gr.Radio(
                choices=list(RESOLUTION_PRESETS.keys()),
                value="1:1 (1024x1024)",
                label="画幅比例快捷预设（直接点击切换）",
                elem_classes=["preset-radio-grid"],
            )

            with gr.Accordion("⚙️ 模型与显存策略高级设置", open=False):
                with gr.Row():
                    models_dir_input = gr.Textbox(
                        value=to_rel_or_abs(MODELS_DIR),
                        label="📁 模型库根目录路径 (支持直接指向 ComfyUI 的 models 目录)",
                        lines=1,
                        scale=8,
                    )
                    rescan_btn = gr.Button("🔄 重新扫描模型", scale=2, elem_classes=["btn-flush"])

                with gr.Accordion("📖 模型下载说明文档", open=False):
                    gr.Markdown(
                        r"""
### 📁 存放目录层级规范
请将下载好的模型文件放置到模型根目录（或 ComfyUI 的 `models` 目录）对应的子文件夹中：
- **`diffusion_models/`** ：降噪主模型（DiT / UNet 权重，如 `.safetensors` 或 `.gguf`）
- **`text_encoders/`**（或 `clip/`）：文本编码器（LLM / CLIP 权重）
- **`vae/`** ：变分自编码器（VAE 解码器权重）

---

### 🌟 事例一：Qwen-Image-2.1-Turbo GGUF 极速免审核套装（图示配置 / 显存极致优化）
*专为 8~10G 显存优化，加载快、显存占用极低（仅需 4~6GB），支持 8 步快速出图且解除提示词审查。*

| 组件 | 文件名 | 存放子目录 | 下载页面 / 镜像直链 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-Turbo-AD-Q4_K.gguf` | `diffusion_models/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) \| [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-GGUF) |
| **文本编码器** | `Qwen-Image-2.1-Turbo-Abliterated-Uncensored-AD-Q4_K.gguf` | `text_encoders/` | [HF官方](https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) \| [国内镜像](https://hf-mirror.com/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | [HF官方](https://huggingface.co/Qwen/Qwen-Image-2.1) \| [国内镜像](https://hf-mirror.com/Qwen/Qwen-Image-2.1) |

---

### 🚀 事例二：Qwen-Image-2.1-Turbo 6步动态加速版（INT8 Safetensors）
*搭配 Viggle 动态调度算法，只需 6 步即可极速生成高质量图像。*

| 组件 | 文件名 | 存放子目录 | 下载页面 / 镜像直链 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `Qwen-Image-2.1-viggle-turbo-v0.3-6step-int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [国内镜像](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **文本编码器** | `qwen3vl_8b_int8_convrot.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/city96/Qwen-Image-2.1-Turbo-gguf) \| [国内镜像](https://hf-mirror.com/city96/Qwen-Image-2.1-Turbo-gguf) |
| **变分自编码器** | `qwen_image_2.1_vae_bf16.safetensors` | `vae/` | 同上 |

---

### 🎨 事例三：Z-Image Turbo 体系（阿里最新轻量开源模型）
*全新架构单流 Diffusion Transformer，推荐步数 8~9 步，采样器 `euler`，调度器 `simple`。*

| 组件 | 文件名 | 存放子目录 | 下载页面 / 镜像直链 |
| :--- | :--- | :--- | :--- |
| **降噪主模型** | `z_image_turbo_int8_convrot.safetensors` | `diffusion_models/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |
| **文本编码器** | `qwen_3_4b_fixed.safetensors` 或 `qwen_3_4b.safetensors` | `text_encoders/` | [HF官方](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) <br> *(⚠️ 注意：请勿使用带 NVFP4 2D分块量化的实验版)* |
| **变分自编码器** | `ae.safetensors` | `vae/` | [HF官方(Flux VAE)](https://huggingface.co/Comfy-Org/z_image_turbo) \| [国内镜像](https://hf-mirror.com/Comfy-Org/z_image_turbo) |

---
> 💡 **提示**：下载放置完成后，点击上方的 **「🔄 重新扫描模型」** 按钮，新模型即可立刻出现在下方下拉选择框中。
"""
                    )

                diff_select = gr.Dropdown(choices=diff_choices, value=default_diff, label="降噪主模型 (diffusion_models)")
                te_select = gr.Dropdown(choices=te_choices, value=default_te, label="文本编码器 (text_encoders)")
                vae_select = gr.Dropdown(choices=vae_choices, value=default_vae, label="变分自编码器 (vae)")

                policy_radio = gr.Radio(
                    choices=[
                        ("即用即走 (On-Demand 冷启动 / 推荐10G显存)", "on_demand"),
                        ("智能休眠 (5分钟闲置自动释放)", "auto_unload"),
                        ("显存常驻 (Always-On 秒级出图)", "always_on"),
                    ],
                    value="on_demand",
                    label="显存管理策略",
                )
                with gr.Row():
                    steps_input = gr.Number(
                        value=default_steps,
                        label="采样步数 (Steps, 6步/8步自动匹配)",
                        minimum=1,
                        maximum=50,
                        step=1,
                        precision=0,
                        scale=1,
                    )
                    seed_input = gr.Number(
                        value=-1,
                        label="随机种子 (-1 为随机)",
                        precision=0,
                        scale=1,
                    )

                save_api_btn = gr.Button("💾 保存为 API / Agent 默认调用模型 (Save for Agent)", elem_classes=["btn-flush"])
                api_model_info = gr.Markdown(value=get_api_model_status_text())

            generate_btn = gr.Button("开始生成图像 (Generate)", elem_classes=["btn-coral"])

        with gr.Column(scale=5):
            output_image = gr.Image(label="生成结果", type="filepath", elem_id="output-canvas")
            gen_info = gr.Markdown(value="准备就绪。", elem_id="gen-info")

    # 网页内嵌实时终端日志与外部 Agent 指南
    with gr.Row():
        with gr.Column(scale=6, elem_classes=["dark-terminal-card"]):
            gr.Markdown("#### 📟 网页实时执行进度日志 (Live Logs)")
            live_logs_box = gr.Textbox(
                value="等待生成指令...\n",
                lines=8,
                max_lines=12,
                label="",
                interactive=False,
                autoscroll=True,
                elem_id="live-logs-box",
            )

        with gr.Column(scale=6, elem_classes=["dark-terminal-card"]):
            gr.Markdown(
                """
                #### 🔌 外部 Agent 接入指南
                本服务对外暴露标准的 **OpenAI DALL-E 生图接口**：
                * **Base URL**: `http://127.0.0.1:40188/v1`
                * **API Key**: 任意填写（如 `sk-local`）
                * **模型名称 (Model)**: `qwen-image-2.1-turbo` 或 `dall-e-3`
                * **cURL 快速测试**:
                ```bash
                curl -X POST http://127.0.0.1:40188/v1/images/generations \\
                  -H "Content-Type: application/json" \\
                  -d '{"prompt": "a cyberpunk street, neon, 8k", "size": "1024x1024"}'
                ```
                """
            )

    # 交互事件绑定
    ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

    async def on_generate(prompt, preset_val, steps, seed, policy, diff_m, te_m, vae_m, progress=gr.Progress(track_tqdm=True)):
        if not prompt or not prompt.strip():
            yield None, "提示词不能为空！", "错误：提示词为空\n"
            return

        engine.mode = policy
        w, h = RESOLUTION_PRESETS.get(preset_val, (1024, 1024))
        start_t = time.time()
        accumulated_lines = [">>> 任务开始..."]
        accumulated_logs = ">>> 任务开始...\n"

        yield None, "正在启动生成任务...", accumulated_logs

        final_path = None
        try:
            async for ev in engine.generate_image_stream(
                prompt=prompt.strip(),
                width=w,
                height=h,
                steps=int(steps) if steps else DEFAULT_STEPS,
                seed=int(seed),
                diff_model=diff_m,
                te_model=te_m,
                vae_model=vae_m,
            ):
                pct = ev.get("pct", 0.0)
                desc = ev.get("desc", "处理中...")
                log_chunk = ev.get("log", "")

                if log_chunk:
                    cleaned = ANSI_REGEX.sub("", log_chunk)
                    raw_lines = cleaned.replace("\r\n", "\n").replace("\r", "\n").split("\n")
                    for raw_l in raw_lines:
                        l = raw_l.strip()
                        if not l:
                            continue
                        # 如果是进度行，且上一行也是进度行，则就地替换，避免刷屏产生海量滚动条
                        is_prog = ("|" in l and ("/" in l or "%" in l)) or l.startswith("[")
                        if is_prog and accumulated_lines and ("|" in accumulated_lines[-1] and ("/" in accumulated_lines[-1] or "%" in accumulated_lines[-1])):
                            accumulated_lines[-1] = l
                        else:
                            accumulated_lines.append(l)

                    accumulated_lines = accumulated_lines[-25:]
                    accumulated_logs = "\n".join(accumulated_lines) + "\n"

                progress(pct, desc=desc)

                if "out_path" in ev:
                    final_path = ev["out_path"]

                yield (
                    None,
                    f"正在执行: {desc}",
                    accumulated_logs,
                )

            cost = time.time() - start_t
            info_text = f"✨ **生成成功**！耗时: `{cost:.2f}s` | 分辨率: `{w}x{h}` | 存放目录: `{to_rel_or_abs(OUTPUTS_DIR)}/`"
            yield (
                final_path,
                info_text,
                accumulated_logs + f">>> 任务完成，总耗时 {cost:.2f}s\n",
            )
        except Exception as e:
            err_msg = f"❌ **生成失败**: {str(e)}"
            yield (
                None,
                err_msg,
                accumulated_logs + f"\n[ERROR] {str(e)}\n",
            )

    def on_flush():
        msg = engine.stop_server()
        return msg, f"**显存状态**：{engine.get_status_text()}"

    def on_rescan_models(custom_path):
        global MODELS_DIR, APP_CONFIG
        p_str = custom_path.strip() if custom_path else ""
        if p_str:
            p = Path(p_str)
            if not p.is_absolute():
                p = (BASE_DIR / p).resolve()
        else:
            p = (BASE_DIR / "models").resolve()

        if not p.exists() or not p.is_dir():
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                f"❌ 路径不存在或不是有效文件夹: `{p}`",
            )
        MODELS_DIR = p
        APP_CONFIG["models_dir"] = to_rel_or_abs(p)
        save_config(APP_CONFIG)

        d_list, t_list, v_list = scan_models(MODELS_DIR)
        d_val = d_list[0] if d_list else None
        t_val = t_list[0] if t_list else None
        v_val = v_list[0] if v_list else None
        s_val = 6 if d_val and "6step" in d_val.lower() else 8
        display_path = to_rel_or_abs(p)
        msg = f"✅ 模型目录已同步并持久化保存: `{display_path}`\n发现主模型: {len(d_list)} 个 | 文本编码器: {len(t_list)} 个 | VAE: {len(v_list)} 个"
        return (
            gr.update(choices=d_list, value=d_val),
            gr.update(choices=t_list, value=t_val),
            gr.update(choices=v_list, value=v_val),
            s_val,
            msg,
        )

    rescan_btn.click(
        on_rescan_models,
        inputs=[models_dir_input],
        outputs=[diff_select, te_select, vae_select, steps_input, gen_info],
    )

    def on_diff_model_change(m_name):
        if m_name and "6step" in m_name.lower():
            return 6
        return 8

    diff_select.change(on_diff_model_change, inputs=[diff_select], outputs=[steps_input])

    def on_save_api_model(diff_m, te_m, vae_m, steps):
        global APP_CONFIG
        s_int = int(steps) if steps and int(steps) > 0 else (6 if "6step" in (diff_m or "").lower() else 8)
        APP_CONFIG["api_diff_model"] = diff_m
        APP_CONFIG["api_te_model"] = te_m
        APP_CONFIG["api_vae_model"] = vae_m
        APP_CONFIG["api_steps"] = s_int
        save_config(APP_CONFIG)
        return f"✅ **已成功持久化至 config.json**：外部 Agent 接口将默认使用 `{diff_m}`（{s_int} 步）"

    save_api_btn.click(
        on_save_api_model,
        inputs=[diff_select, te_select, vae_select, steps_input],
        outputs=[api_model_info],
    )

    def on_policy_change(new_policy):
        engine.mode = new_policy
        return f"**显存状态**：{engine.get_status_text()}"

    def on_generate_start():
        return gr.update(interactive=False, value="⏳ 图像生成中...")

    def on_generate_finish():
        return (
            gr.update(interactive=True, value="开始生成图像 (Generate)"),
            get_system_metrics_html(),
            f"**显存状态**：{engine.get_status_text()}",
        )

    policy_radio.change(on_policy_change, inputs=[policy_radio], outputs=[vram_badge])
    flush_btn.click(on_flush, outputs=[gen_info, vram_badge]).then(get_system_metrics_html, outputs=[metrics_display])
    generate_btn.click(
        on_generate_start,
        outputs=[generate_btn],
    ).then(
        on_generate,
        inputs=[prompt_input, preset_res, steps_input, seed_input, policy_radio, diff_select, te_select, vae_select],
        outputs=[output_image, gen_info, live_logs_box],
        show_progress="full",
        show_progress_on=[output_image],
    ).then(
        on_generate_finish,
        outputs=[generate_btn, metrics_display, vram_badge],
    )

# 开启 Gradio 队列，确保流式事件和进度条实时推送到浏览器
demo.queue(default_concurrency_limit=1)

# 挂载 Gradio 到 FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# ==============================================================================
# 6. 入口主函数
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("Q-Spark Studio 服务启动中...")
    print("Web 交互界面: http://127.0.0.1:40188")
    print("Agent 接口地址: http://127.0.0.1:40188/v1/images/generations")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=40188)
