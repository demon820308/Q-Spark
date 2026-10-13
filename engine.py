import asyncio
import base64
import math
import os
import random
import re
import subprocess
import shutil
import sys
import time
from pathlib import Path
from typing import AsyncGenerator, Optional
import json
import httpx
import psutil

# 确保 Windows 控制台字符编码安全
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
        "models_dir": "K:\\ComfyUi\\ComfyUI\\ComfyUI\\models",
        "models_dir_history": [
            "K:\\ComfyUi\\ComfyUI\\ComfyUI\\models",
            "models"
        ],
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
    cur = default_cfg.get("models_dir", "models")
    hist = default_cfg.get("models_dir_history", [])
    if not isinstance(hist, list):
        hist = [cur]
    if cur and cur not in hist:
        hist.insert(0, cur)
    default_cfg["models_dir_history"] = hist
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
OUTPUTS_JSON_DIR = OUTPUTS_DIR / "json"
OUTPUTS_JSON_DIR.mkdir(parents=True, exist_ok=True)
INPUTS_DIR = BASE_DIR / "inputs"
INPUTS_DIR.mkdir(parents=True, exist_ok=True)


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


def compute_aspect_ratio_str(width: int, height: int) -> str:
    """计算标准画幅比例简写 (如 1:1, 16:9, 3:4)"""
    presets = {
        (1024, 1024): "1:1",
        (512, 512): "1:1",
        (768, 1024): "3:4",
        (864, 1152): "3:4",
        (768, 1360): "9:16",
        (832, 1248): "2:3",
        (1024, 768): "4:3",
        (1360, 768): "16:9",
        (1248, 832): "3:2",
        (1536, 640): "21:9",
    }
    if (width, height) in presets:
        return presets[(width, height)]
    ratio = width / max(height, 1)
    if abs(ratio - 1.0) < 0.05:
        return "1:1"
    if abs(ratio - 16 / 9) < 0.05:
        return "16:9"
    if abs(ratio - 9 / 16) < 0.05:
        return "9:16"
    if abs(ratio - 4 / 3) < 0.05:
        return "4:3"
    if abs(ratio - 3 / 4) < 0.05:
        return "3:4"
    if abs(ratio - 3 / 2) < 0.05:
        return "3:2"
    if abs(ratio - 2 / 3) < 0.05:
        return "2:3"
    if abs(ratio - 21 / 9) < 0.08 or abs(ratio - 2.4) < 0.05:
        return "21:9"
    g = math.gcd(width, height)
    w_r, h_r = width // g, height // g
    if w_r <= 32 and h_r <= 32:
        return f"{w_r}:{h_r}"
    return f"{width}:{height}"


DEFAULT_STEPS = 8
DEFAULT_CFG = 1.0
DEFAULT_SAMPLER = "euler"


def get_model_default_steps(diff_model: str) -> int:
    """根据模型命名特征自动判断推荐步数：6step/viggle为6步，turbo为8步，标准基模为25步"""
    name = (diff_model or "").lower()
    if "6step" in name or "viggle" in name:
        return 6
    if "turbo" in name:
        return 8
    return 25


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
    """在模型根目录下查找指定子目录中的具体模型文件，优先 MODELS_DIR，兜底本地 BASE_DIR / models"""
    global MODELS_DIR
    roots = [MODELS_DIR]
    local_dir = BASE_DIR / "models"
    if local_dir.resolve() != MODELS_DIR.resolve():
        roots.append(local_dir)

    for r in roots:
        for folder in subfolder_names:
            candidate = r / folder / filename
            if candidate.exists():
                return candidate
    return MODELS_DIR / subfolder_names[0] / filename


def resolve_vision_projector(root: Optional[Path] = None) -> Optional[Path]:
    """在文本编码器目录下定位 Qwen/Flux 视觉多模态投影器 (mmproj-*.gguf)"""
    global MODELS_DIR
    base = root or MODELS_DIR
    te_dir = get_sub_dir(base, ["text_encoders", "text_encoder"])
    if te_dir.exists():
        for f in te_dir.glob("mmproj*"):
            if f.is_file() and f.suffix.lower() in {".gguf", ".safetensors"}:
                return f
    return None


def scan_models(base_path: Optional[Path | str] = None):
    global MODELS_DIR
    root = Path(base_path) if base_path else MODELS_DIR
    diff_dir = get_sub_dir(root, ["diffusion_models", "diffusion"])
    te_dir = get_sub_dir(root, ["text_encoders", "text_encoder"])
    vae_dir = root / "vae"
    lora_dir = get_sub_dir(root, ["loras", "lora"])

    upscale_dir = get_sub_dir(root, ["upscale_models", "esrgan", "upscale"])

    valid_exts = {".gguf", ".safetensors"}
    valid_upscale_exts = {".pth", ".pt", ".safetensors", ".bin", ".onnx", ".gguf"}

    diff_models = [
        f.name for f in diff_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts
    ] if diff_dir.exists() else []

    te_models = [
        f.name for f in te_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts and not f.name.startswith("mmproj")
    ] if te_dir.exists() else []

    vae_models = [
        f.name for f in vae_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts
    ] if vae_dir.exists() else []

    lora_models = [
        f.name for f in lora_dir.glob("*") if f.is_file() and f.suffix.lower() in valid_exts
    ] if lora_dir.exists() else []

    upscale_candidates = set()
    if upscale_dir.exists():
        for f in upscale_dir.glob("*"):
            if f.is_file() and f.suffix.lower() in valid_upscale_exts:
                upscale_candidates.add(f.name)

    # 扫描项目本地 models/upscale_models 内置超分模型库 (支持放入任意其它超分模型)
    local_upscale_dir = get_sub_dir(BASE_DIR / "models", ["upscale_models", "esrgan", "upscale"])
    if local_upscale_dir.exists() and local_upscale_dir.resolve() != upscale_dir.resolve():
        for f in local_upscale_dir.glob("*"):
            if f.is_file() and f.suffix.lower() in valid_upscale_exts:
                upscale_candidates.add(f.name)

    upscale_models = sorted(list(upscale_candidates), key=lambda x: (0 if "ultrasharp" in x.lower() else 1, x.lower()))

    return (
        diff_models,
        te_models,
        vae_models,
        lora_models,
        upscale_models,
    )


def update_models_dir(new_path: Path):
    global MODELS_DIR
    MODELS_DIR = new_path


def get_system_metrics() -> dict:
    """采集 GPU 显存、物理内存与 CPU 占用率，返回结构化 dict"""
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

    return {
        "vram": {"used": round(vram_u, 2), "total": round(vram_t, 1), "pct": round(vram_pct, 1)},
        "vram_used": round(vram_u, 2),
        "vram_total": round(vram_t, 1),
        "ram": {"used": round(ram_u, 1), "total": round(ram_t, 1), "pct": round(ram_pct, 1)},
        "cpu": {"pct": round(cpu_pct, 1)},
        "active_task": getattr(engine, "current_task", None) if "engine" in globals() else None,
    }


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
        self.current_cli_proc: Optional[asyncio.subprocess.Process] = None
        self.is_task_stopped = False
        self.server_port = 40189
        self.current_model_config = {}
        self.current_task: Optional[dict] = None

    def get_status_text(self):
        is_running = self.server_process is not None and self.server_process.poll() is None
        if self.mode == "on_demand":
            return "即用即走"
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

    def stop_task(self):
        """立即终止当前正在执行的生图任务"""
        self.is_task_stopped = True
        stopped = False
        if self.current_cli_proc and self.current_cli_proc.returncode is None:
            try:
                pid = self.current_cli_proc.pid
                if pid:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception:
                pass
            try:
                self.current_cli_proc.kill()
            except Exception:
                pass
            stopped = True

        if self.server_process and self.server_process.poll() is None:
            self.stop_server()
            stopped = True

        return "已成功终止当前生成任务。" if stopped else "当前无正在运行的生成任务。"

    async def _stream_sd_cli(self, cmd, cwd) -> AsyncGenerator[dict, None]:
        """异步生成器：实时流式输出控制台日志 + 产出结构化进度事件"""
        self.is_task_stopped = False
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        self.current_cli_proc = proc

        error_lines = []
        current_pct = 0.05
        current_desc = "正在初始化推理环境..."
        stage = 1  # 1: 文本编码, 2: DiT加载, 3: 去噪采样, 4: VAE解码

        yield {"pct": current_pct, "desc": current_desc, "log": ">>> 正在启动 GPU 推理任务...\n"}

        try:
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode("utf-8", errors="replace")

                # 1. 实时写到底层控制台黑框 (保留全部底层日志便于排错)
                sys.stdout.write(line)
                sys.stdout.flush()

                error_lines.append(line)
                if len(error_lines) > 40:
                    error_lines.pop(0)

                # 2. 状态机解析与纯净步骤日志提炼
                web_log = ""
                m = re.search(r'\|\s*(\d+)/(\d+)', line)
                if m:
                    cur, tot = int(m.group(1)), int(m.group(2))
                    if stage == 1:
                        current_pct = 0.05 + 0.25 * (cur / tot)
                        current_desc = f"加载文本编码器模型 ({int(cur / tot * 100)}%)..."
                        web_log = f"[1/4] 🚀 载入文本编码器与特征 ({int(cur / tot * 100)}%)...\n"
                    elif stage == 2:
                        current_pct = 0.30 + 0.10 * (cur / tot)
                        current_desc = f"加载 DiT 降噪主模型 ({int(cur / tot * 100)}%)..."
                        web_log = f"[2/4] 🧩 载入 DiT 降噪主模型 ({int(cur / tot * 100)}%)...\n"
                    elif stage == 3:
                        current_pct = 0.40 + 0.50 * (cur / tot)
                        current_desc = f"采样去噪进行中 ({cur}/{tot} 步)..."
                        web_log = f"[3/4] ⚡ GPU 扩散去噪采样中 ({cur}/{tot} 步)...\n"
                    elif stage == 4:
                        current_pct = 0.90 + 0.09 * (cur / tot)
                        current_desc = f"VAE 高清解码渲染中 ({int(cur / tot * 100)}%)..."
                        web_log = f"[4/4] 🎨 VAE 高清解码渲染中 ({int(cur / tot * 100)}%)...\n"

                if "get_learned_condition completed" in line:
                    stage = 2
                    current_pct = 0.35
                    current_desc = "提示词特征提取完成"
                    web_log = "[1/4] 🚀 提示词特征提取完成 ✔\n"
                elif "generating image:" in line:
                    stage = 3
                    current_pct = 0.40
                    current_desc = "载入 DiT 降噪主模型完成"
                    web_log = "[2/4] 🧩 载入 DiT 降噪主模型 ✔\n"
                elif "sampling completed" in line:
                    stage = 4
                    current_pct = 0.90
                    current_desc = "扩散去噪采样完成"
                    web_log = "[3/4] ⚡ 扩散去噪采样完成 ✔\n"
                elif "decode_first_stage completed" in line:
                    current_pct = 0.98
                    current_desc = "VAE 高清图像解码完成"
                    web_log = "[4/4] 🎨 VAE 高清图像解码完成 ✔\n"
                elif "generate_image completed" in line:
                    current_pct = 1.0
                    current_desc = "图像生成完成！"
                    web_log = ">>> ✨ 图像生成流程顺利完成！\n"

                if web_log:
                    yield {"pct": current_pct, "desc": current_desc, "log": web_log}

            ret = await proc.wait()
            if self.is_task_stopped:
                yield {"pct": 0.0, "desc": "任务已手动终止", "log": ">>> ⏹️ 任务已由用户手动终止。\n"}
                return
            if ret != 0:
                err_msg = "".join(error_lines[-15:])
                raise RuntimeError(f"sd-cli 执行失败 (代码 {ret}):\n{err_msg}")
        finally:
            self.current_cli_proc = None

    async def ensure_server(
        self,
        diff_model: str,
        te_model: str,
        vae_model: str,
        steps: Optional[int] = None,
        width: int = 1024,
        height: int = 1024,
    ):
        target_steps = int(steps) if (steps is not None and int(steps) > 0) else (APP_CONFIG.get("api_steps") or get_model_default_steps(diff_model))

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
        is_turbo = "turbo" in diff_path.name.lower() or "6step" in diff_path.name.lower() or "viggle" in diff_path.name.lower()
        if is_turbo and target_steps == 6:
            cmd.extend(["--sigmas", get_viggle_6step_sigmas(width, height)])
        elif is_turbo and target_steps == 8 and "z_image" not in diff_path.name.lower():
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

    def prepare_init_image(self, init_image_input: Optional[str]) -> Optional[Path]:
        """将传入的 Base64 图片或文件路径规整为磁盘上的有效输入图片路径"""
        if not init_image_input or not isinstance(init_image_input, str):
            return None

        INPUTS_DIR.mkdir(parents=True, exist_ok=True)

        # 1. 带 Data URL 前缀的 Base64 数据
        if "base64," in init_image_input:
            try:
                _, b64_data = init_image_input.split("base64,", 1)
                raw_bytes = base64.b64decode(b64_data)
                saved_path = INPUTS_DIR / f"init_{int(time.time())}_{random.randint(1000, 9999)}.png"
                saved_path.write_bytes(raw_bytes)
                return saved_path
            except Exception as ex:
                print(f"[Warning] 解析 Base64 底图失败: {ex}")
                return None

        # 2. 纯 Base64 数据
        if len(init_image_input) > 200 and not init_image_input.endswith((".png", ".jpg", ".jpeg", ".webp")):
            try:
                raw_bytes = base64.b64decode(init_image_input)
                saved_path = INPUTS_DIR / f"init_{int(time.time())}_{random.randint(1000, 9999)}.png"
                saved_path.write_bytes(raw_bytes)
                return saved_path
            except Exception:
                pass

        # 3. 磁盘现有文件或文件名
        cand = Path(init_image_input)
        if cand.is_file():
            return cand

        cand_out = OUTPUTS_DIR / init_image_input
        if cand_out.is_file():
            return cand_out

        cand_in = INPUTS_DIR / init_image_input
        if cand_in.is_file():
            return cand_in

        if init_image_input.startswith("/outputs/"):
            clean_name = init_image_input.replace("/outputs/", "")
            cand_url = OUTPUTS_DIR / clean_name
            if cand_url.is_file():
                return cand_url

        return None

    def prepare_ref_images(self, ref_images_input: Optional[list]) -> list[Path]:
        """将传入的多张参考图 (Base64 或文件名列表) 规整为磁盘上的有效图片路径"""
        if not ref_images_input or not isinstance(ref_images_input, list):
            return []
        valid_paths = []
        for img in ref_images_input:
            if isinstance(img, dict):
                img = img.get("dataUrl") or img.get("url") or img.get("data")
            p = self.prepare_init_image(img)
            if p and p.exists() and p not in valid_paths:
                valid_paths.append(p)
        return valid_paths

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
        negative_prompt: str = "",
        cfg_scale: Optional[float] = None,
        loras: Optional[list] = None,
        source: str = "web",
        init_image: Optional[str] = None,
        ref_images: Optional[list] = None,
        mode: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        async with self.lock:
            start_time = time.time()
            self.last_active = time.time()
            if seed == -1:
                seed = random.randint(1, 2**31 - 1)

            diff_list, te_list, vae_list, lora_list, _ = scan_models()
            diff_model = diff_model or APP_CONFIG.get("api_diff_model") or (diff_list[0] if diff_list else "")
            te_model = te_model or APP_CONFIG.get("api_te_model") or (te_list[0] if te_list else "")
            vae_model = vae_model or APP_CONFIG.get("api_vae_model") or (vae_list[0] if vae_list else "")

            # 智能架构自适应成套匹配 (防止用户修改主模型时因 TE/VAE 不匹配报错)
            if "z_image" in (diff_model or "").lower():
                if not te_model or "qwen3vl" in te_model.lower() or "qwen-image" in te_model.lower():
                    cand_te = next((t for t in te_list if "qwen_3_4b" in t.lower() and "fixed" in t.lower()), None)
                    if not cand_te:
                        cand_te = next((t for t in te_list if "qwen_3_4b" in t.lower()), None)
                    if cand_te:
                        te_model = cand_te
                if not vae_model or "qwen" in vae_model.lower():
                    cand_vae = next((v for v in vae_list if v.lower() == "ae.safetensors" or "flux" in v.lower()), None)
                    if cand_vae:
                        vae_model = cand_vae
            elif "qwen" in (diff_model or "").lower():
                if not te_model or "qwen_3_4b" in te_model.lower():
                    cand_te = next((t for t in te_list if "qwen3vl" in t.lower() or "qwen-image" in t.lower()), None)
                    if cand_te:
                        te_model = cand_te
                if not vae_model or "ae." in vae_model.lower() or "flux" in vae_model.lower():
                    cand_vae = next((v for v in vae_list if "qwen" in v.lower()), None)
                    if cand_vae:
                        vae_model = cand_vae

            if steps is None or int(steps) <= 0:
                steps = APP_CONFIG.get("api_steps") or get_model_default_steps(diff_model)
            steps = int(steps)
            effective_cfg = float(cfg_scale) if (cfg_scale is not None and float(cfg_scale) > 0) else DEFAULT_CFG

            out_filename = f"img_{int(time.time())}_{seed}.png"
            out_filepath = OUTPUTS_DIR / out_filename

            self.current_task = {
                "source": source,
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "seed": seed,
                "diff_model": diff_model,
                "start_time": time.time(),
                "pct": 0.05,
                "desc": "初始化任务配置...",
            }

            diff_path = resolve_model_file(["diffusion_models", "diffusion"], diff_model)
            te_path = resolve_model_file(["text_encoders", "text_encoder"], te_model)
            vae_path = resolve_model_file(["vae"], vae_model)
            lora_dir = get_sub_dir(MODELS_DIR, ["loras", "lora"])

            # 模式隔离：文生图 (txt2img) vs 图像指令编辑 (edit)
            is_txt2img_mode = (mode == "txt2img")
            init_img_path = self.prepare_init_image(init_image) if not is_txt2img_mode else None

            ref_img_paths = self.prepare_ref_images(ref_images) if not is_txt2img_mode else []
            # 仅当没有多模态参考图列表时，才将单独底图作为参考图兜底，绝不重复插入
            if not ref_img_paths and init_img_path:
                ref_img_paths = [init_img_path]

            # 组装 Prompt 与 LoRA 宏
            final_prompt = prompt
            if loras:
                for lora in loras:
                    l_name = lora.get("name", "") if isinstance(lora, dict) else str(lora)
                    l_weight = lora.get("weight", 0.8) if isinstance(lora, dict) else 0.8
                    stem = Path(l_name).stem
                    if l_name and f"<lora:{l_name}" not in final_prompt and f"<lora:{stem}" not in final_prompt:
                        final_prompt = f"{final_prompt} <lora:{stem}:{l_weight}>"

            # 智能映射：多图编辑时将用户输入的“图1”、“图2”、“图片1”等自动映射为 Qwen 原生视觉 Token <image1>, <image2>
            if not is_txt2img_mode and ref_img_paths and len(ref_img_paths) > 1:
                final_prompt = re.sub(r'(?:第)?(?:图|图片)(\d+)(?:张)?(?:图)?', lambda m: f"<image{m.group(1)}>", final_prompt)

            cmd = [
                str(SD_CLI_EXE),
                "--diffusion-model", to_rel_or_abs(diff_path),
                "--llm", to_rel_or_abs(te_path),
                "--vae", to_rel_or_abs(vae_path),
                "-p", final_prompt,
                "--steps", str(steps),
                "--cfg-scale", str(effective_cfg),
                "--sampling-method", DEFAULT_SAMPLER,
                "-W", str(width),
                "-H", str(height),
                "-s", str(seed),
                "--diffusion-fa",
                "--params-backend", "CUDA0",
                "--backend", "CUDA0",
                "-o", to_rel_or_abs(out_filepath),
            ]
            if negative_prompt and negative_prompt.strip():
                cmd.extend(["-n", negative_prompt.strip()])
            if lora_dir.exists():
                cmd.extend(["--lora-model-dir", to_rel_or_abs(lora_dir), "--lora-apply-mode", "auto"])

            vision_projector = resolve_vision_projector(MODELS_DIR)

            if ref_img_paths and not is_txt2img_mode:
                task_mode = "edit"
                if vision_projector and vision_projector.exists():
                    cmd.extend(["--llm_vision", to_rel_or_abs(vision_projector)])
                cmd.append("--increase-ref-index")
                for rp in ref_img_paths:
                    cmd.extend(["-r", to_rel_or_abs(rp)])
                mode_log = f">>> 任务模式: 🖼️ 图像指令编辑 (Image Edit) | 视觉参考图: {len(ref_img_paths)} 张 (纯空噪声起步，完整采样去噪)\n"
            else:
                task_mode = "txt2img"
                mode_log = ">>> 任务模式: 🎨 文生图 (txt2img)\n"

            is_turbo = "turbo" in diff_path.name.lower() or "6step" in diff_path.name.lower() or "viggle" in diff_path.name.lower()
            if is_turbo and steps == 6:
                cmd.extend(["--sigmas", get_viggle_6step_sigmas(width, height)])
            elif is_turbo and steps == 8 and "z_image" not in diff_path.name.lower():
                cmd.extend(["--sigmas", TURBO_SIGMAS])

            policy_map = {
                "on_demand": "即用即走（按需模式）",
                "always_on": "常驻运行（显存常驻）",
                "auto_unload": "智能休眠（自动释放）",
            }
            policy_text = policy_map.get(self.mode, "按需模式")

            lora_log = ""
            if loras:
                items = [
                    f"{l.get('name', str(l))} (权重: {l.get('weight', 0.8)})"
                    if isinstance(l, dict) else str(l)
                    for l in loras if l
                ]
                if items:
                    lora_log = f">>> 挂载 LoRA: {', '.join(items)}\n"

            ref_log = ""
            if ref_img_paths and not is_txt2img_mode:
                ref_log = f">>> 挂载视觉参考图 ({len(ref_img_paths)} 张): {', '.join(f'<image{i+1}>: {p.name}' for i, p in enumerate(ref_img_paths))}\n"

            info_log = (
                f"{mode_log}"
                f">>> 任务规格: {width}x{height} | 采样步数: {steps} | CFG: {effective_cfg} | 随机种子: {seed}\n"
                f">>> 显存策略: {policy_text}\n"
                f">>> 扩散模型: {diff_model}\n"
                f">>> 文本编码: {te_model}\n"
                f">>> VAE 解码: {vae_model}\n"
                f"{lora_log}"
                f"{ref_log}"
            )
            def _save_meta(out_fp: Path, current_diff: str):
                dur = round(time.time() - start_time, 2)
                meta = {
                    "id": out_fp.stem,
                    "filename": out_fp.name,
                    "mode": task_mode,
                    "source": source,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt or "",
                    "cfg_scale": effective_cfg,
                    "steps": steps,
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "aspect_ratio": compute_aspect_ratio_str(width, height),
                    "diff_model": current_diff,
                    "te_model": te_model,
                    "vae_model": vae_model,
                    "loras": loras or [],
                    "vram_mode": self.mode,
                    "duration_seconds": dur,
                    "created_at": int(time.time()),
                    "created_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "init_image": init_img_path.name if init_img_path else None,
                    "ref_images": [p.name for p in ref_img_paths] if ref_img_paths else [],
                }
                try:
                    OUTPUTS_JSON_DIR.mkdir(parents=True, exist_ok=True)
                    with open(OUTPUTS_JSON_DIR / f"{out_fp.stem}.json", "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
                except Exception as ex:
                    print(f"[Warning] 保存历史元数据失败: {ex}")
                return meta

            def _update_task(ev):
                if self.current_task and isinstance(ev, dict):
                    if "pct" in ev:
                        self.current_task["pct"] = ev["pct"]
                    if "desc" in ev and ev.get("desc"):
                        self.current_task["desc"] = ev["desc"]

            try:
                ev_init = {"pct": 0.05, "desc": "初始化任务配置...", "log": info_log}
                _update_task(ev_init)
                yield ev_init

                # 策略 A：按需冷启动模式 (流式输出 + 实时进度) 或者是图生图/参考图任务
                if self.mode == "on_demand" or init_img_path or ref_img_paths:
                    async for event in self._stream_sd_cli(cmd, cwd=BASE_DIR):
                        _update_task(event)
                        yield event
                    if self.is_task_stopped:
                        return
                    meta = _save_meta(out_filepath, diff_model)
                    ev_done = {"pct": 1.0, "desc": "完成！", "log": "", "out_path": str(out_filepath), "diff_model": diff_model, "metadata": meta}
                    _update_task(ev_done)
                    yield ev_done
                    return

                # 策略 B & C：常驻或自动休眠模式
                try:
                    ev_s1 = {"pct": 0.15, "desc": "准备常驻推理服务...", "log": ">>> 正在连接常驻模型服务...\n"}
                    _update_task(ev_s1)
                    yield ev_s1
                    await self.ensure_server(diff_model, te_model, vae_model, steps=steps, width=width, height=height)
                    ev_s2 = {"pct": 0.45, "desc": "服务已就绪，正在进行 GPU 高速去噪...", "log": ">>> 开始发送生图任务...\n"}
                    _update_task(ev_s2)
                    yield ev_s2
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        resp = await client.post(
                            f"http://127.0.0.1:{self.server_port}/v1/images/generations",
                            json={
                                "prompt": final_prompt,
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
                        meta = _save_meta(out_filepath, diff_model)
                        ev_done = {"pct": 1.0, "desc": "生成完成！", "log": ">>> 图像已成功保存。\n", "out_path": str(out_filepath), "diff_model": diff_model, "metadata": meta}
                        _update_task(ev_done)
                        yield ev_done
                        return
                except Exception as e:
                    print(f"\n[Warning] 常驻模式异常，正在降级回退至 sd-cli 流式执行: {e}\n")
                    self.stop_server()
                    async for event in self._stream_sd_cli(cmd, cwd=BASE_DIR):
                        _update_task(event)
                        yield event
                    if self.is_task_stopped:
                        return
                    meta = _save_meta(out_filepath, diff_model)
                    ev_done = {"pct": 1.0, "desc": "完成！", "log": "", "out_path": str(out_filepath), "diff_model": diff_model, "metadata": meta}
                    _update_task(ev_done)
                    yield ev_done
            finally:
                self.current_task = None

    async def run_upscale_task(
        self,
        image_input: str,
        upscale_model: str,
        scale: int = 2,
        tile_size: int = 128,
    ) -> dict:
        async with self.lock:
            from PIL import Image
            src_path = self.prepare_init_image(image_input)
            if not src_path or not src_path.exists():
                raise FileNotFoundError(f"找不到需要放大的输入图片: {image_input}")

            model_path = resolve_model_file(["upscale_models", "esrgan", "upscale"], upscale_model)
            if not model_path or not model_path.exists():
                raise FileNotFoundError(f"未找到超分辨率模型文件: {upscale_model}")

            with Image.open(src_path) as orig_img:
                orig_w, orig_h = orig_img.size

            if max(orig_w, orig_h) > 4096 and scale > 2:
                raise ValueError(f"原图分辨率过高 ({orig_w}x{orig_h})，长边超过 4096px 时为防显存溢出仅支持 2x 放大")

            seed_tag = int(time.time())
            tmp_4x_name = f"tmp_upscale_4x_{seed_tag}_{os.getpid()}.png"
            tmp_4x_path = OUTPUTS_DIR / tmp_4x_name
            final_filename = f"upscale_{scale}x_{seed_tag}.png"
            final_path = OUTPUTS_DIR / final_filename

            cmd = [
                str(SD_CLI_EXE),
                "-M", "upscale",
                "--upscale-model", str(model_path),
                "-i", str(src_path),
                "-o", str(tmp_4x_path),
                "--upscale-tile-size", str(tile_size),
                "--upscale-repeats", "1",
            ]

            start_t = time.time()
            self.current_task = {
                "source": "web_upscale",
                "prompt": f"[🔍 {scale}x 超分辨率放大] 原图: {src_path.name}",
                "width": orig_w * scale,
                "height": orig_h * scale,
                "steps": 1,
                "diff_model": upscale_model,
                "start_time": start_t,
                "pct": 0.3,
                "desc": f"正在进行 {scale}x C++ 硬件加速超分辨率放大...",
            }

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=str(BASE_DIR),
                )
                self.current_cli_proc = proc

                error_lines = []
                tile_re = re.compile(r'(\d+)/(\d+)')
                while True:
                    line_b = await proc.stdout.readline()
                    if not line_b:
                        break
                    line = line_b.decode(errors="replace").strip()
                    error_lines.append(line)

                    if "loading tensors completed" in line:
                        self.current_task["pct"] = 0.15
                        self.current_task["desc"] = "超分模型权重载入完成"
                    elif "it/s" in line or "s/it" in line:
                        m = tile_re.search(line)
                        if m:
                            cur, total = int(m.group(1)), int(m.group(2))
                            if total > 0:
                                pct = 0.15 + 0.75 * (cur / total)
                                self.current_task["pct"] = round(pct, 2)
                                self.current_task["desc"] = f"硬件加速分块超分中 ({cur}/{total})"
                    elif "input_image_tensor upscaled" in line:
                        self.current_task["pct"] = 0.92
                        self.current_task["desc"] = "分块超分完成，正在优化画质..."

                ret = await proc.wait()
                if ret != 0 or not tmp_4x_path.exists():
                    err_msg = "\n".join(error_lines[-15:]) if error_lines else "引擎未生成目标文件"
                    raise RuntimeError(f"sd-cli 超分辨率放大失败 (代码 {ret}):\n{err_msg}")

                with Image.open(tmp_4x_path) as img_4x:
                    w_4x, h_4x = img_4x.size
                    if scale == 2:
                        self.current_task["pct"] = 0.95
                        self.current_task["desc"] = "高质量平滑下采样中..."
                        target_w = max(1, w_4x // 2)
                        target_h = max(1, h_4x // 2)
                        img_2x = img_4x.resize((target_w, target_h), Image.Resampling.LANCZOS)
                        img_2x.save(final_path, quality=95)
                        final_w, final_h = target_w, target_h
                    else:
                        final_w, final_h = w_4x, h_4x

                if scale != 2:
                    shutil.move(tmp_4x_path, final_path)

                duration = round(time.time() - start_t, 2)
                self.current_task["pct"] = 1.0
                self.current_task["desc"] = "超分放大完成！"

                # 检查输入源图是否已有伴生元数据，若有则完整继承原始生成信息
                orig_json_path = OUTPUTS_JSON_DIR / f"{src_path.stem}.json"
                orig_meta = {}
                if orig_json_path.exists():
                    try:
                        with open(orig_json_path, "r", encoding="utf-8") as f:
                            orig_meta = json.load(f)
                    except Exception:
                        pass

                meta = {
                    "id": final_path.stem,
                    "filename": final_filename,
                    "mode": orig_meta.get("mode", f"upscale_{scale}x"),
                    "source": orig_meta.get("source", "web_upscale"),
                    "prompt": orig_meta.get("prompt", f"[🔍 {scale}x 超分辨率放大] 原图: {src_path.name}"),
                    "negative_prompt": orig_meta.get("negative_prompt", ""),
                    "cfg_scale": orig_meta.get("cfg_scale", 1.0),
                    "steps": orig_meta.get("steps", 1),
                    "seed": orig_meta.get("seed", seed_tag),
                    "diff_model": orig_meta.get("diff_model", ""),
                    "te_model": orig_meta.get("te_model", ""),
                    "vae_model": orig_meta.get("vae_model", ""),
                    "loras": orig_meta.get("loras", []),
                    "vram_mode": orig_meta.get("vram_mode", self.mode),
                    "width": final_w,
                    "height": final_h,
                    "aspect_ratio": compute_aspect_ratio_str(final_w, final_h),
                    "duration_seconds": duration,
                    "created_at": int(time.time()),
                    "created_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "init_image": orig_meta.get("init_image", src_path.name),
                    "ref_images": orig_meta.get("ref_images", []),
                    # 专属超分信息
                    "upscale_model": upscale_model,
                    "upscale_scale": scale,
                    "upscaled_from": src_path.name,
                    "orig_width": orig_w,
                    "orig_height": orig_h,
                }
                try:
                    OUTPUTS_JSON_DIR.mkdir(parents=True, exist_ok=True)
                    with open(OUTPUTS_JSON_DIR / f"{final_path.stem}.json", "w", encoding="utf-8") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
                except Exception as ex:
                    print(f"[Warning] 保存超分元数据失败: {ex}")

                return {
                    "success": True,
                    "filename": final_filename,
                    "image_url": f"/outputs/{final_filename}",
                    "width": final_w,
                    "height": final_h,
                    "orig_width": orig_w,
                    "orig_height": orig_h,
                    "scale": scale,
                    "duration": duration,
                    "metadata": meta,
                }
            finally:
                self.current_cli_proc = None
                self.current_task = None
                if tmp_4x_path.exists():
                    try:
                        tmp_4x_path.unlink()
                    except Exception:
                        pass

    async def idle_checker_loop(self):
        while True:
            await asyncio.sleep(10)
            if self.mode == "auto_unload" and self.server_process:
                if time.time() - self.last_active > self.idle_timeout:
                    self.stop_server()


engine = InferenceEngine()
