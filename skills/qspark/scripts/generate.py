import argparse
import base64
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# 确保 Windows 终端 UTF-8 编码安全，防止 GBK 终端在输出 Emoji 时抛出 UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ASPECT_RATIO_PRESETS = {
    "1:1": (1024, 1024),
    "16:9": (1360, 768),
    "9:16": (768, 1360),
    "4:3": (1024, 768),
    "3:4": (768, 1024),
    "3:2": (1248, 832),
    "2:3": (832, 1248),
    "21:9": (1536, 640),
}


def parse_dimensions(size_str: str = "", prompt_str: str = "") -> tuple[int, int]:
    """智能解析尺寸与比例预设，兼容 832x1248、16:9 以及 --ar 语法"""
    combined = f"{size_str} {prompt_str}"
    m_ar = re.search(r'--?ar\s+(\d+[:/：]\d+)', combined, re.IGNORECASE)
    if m_ar:
        key = m_ar.group(1).replace("/", ":").replace("：", ":")
        if key in ASPECT_RATIO_PRESETS:
            return ASPECT_RATIO_PRESETS[key]

    m_dim = re.search(r'(?<!\d)(\d{3,4})\s*[\*xX×]\s*(\d{3,4})(?!\d)', combined)
    if m_dim:
        try:
            w = max(256, min(4096, round(int(m_dim.group(1)) / 16) * 16))
            h = max(256, min(4096, round(int(m_dim.group(2)) / 16) * 16))
            return w, h
        except Exception:
            pass

    for m_ratio in re.finditer(r'(?<!\d)(\d{1,2})\s*[:/：]\s*(\d{1,2})(?!\d)', combined):
        key = f"{m_ratio.group(1)}:{m_ratio.group(2)}"
        if key in ASPECT_RATIO_PRESETS:
            return ASPECT_RATIO_PRESETS[key]

    return 1024, 1024


def resolve_default_output_dir() -> Path:
    """自动定位当前 Agent 工作区的 outputs 目录"""
    out_dir = Path.cwd() / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def check_info(host: str):
    """查询并打印当前 config.json 中生效的模型与服务状态"""
    url = f"{host.rstrip('/')}/api/config"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Q-Spark-Skill"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cfg = data.get("config", {})
        print(f"CONFIG_DIFF_MODEL: {cfg.get('api_diff_model', '跟随首选')}")
        print(f"CONFIG_STEPS: {cfg.get('api_steps', 8)}")
        print(f"CONFIG_MODELS_DIR: {data.get('models_dir', '')}")
        status_raw = data.get("api_status_text", "")
        status_clean = re.sub(r'[\U00010000-\U0010ffff]', '', status_raw).replace("**", "").replace("`", "").strip()
        if status_clean:
            print(f"API_STATUS: {status_clean}")
    except Exception as e:
        sys.stderr.write(f"[Error] 获取服务配置状态失败: {e}\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate image using local Q-Spark service (follows config.json)")
    parser.add_argument("--prompt", "-p", required=False, help="Image prompt (Chinese or English)")
    parser.add_argument("--size", "-s", default="1024x1024", help="Image size (e.g. 1024x1024, 1360x768, 768x1360, 832x1248)")
    parser.add_argument("--steps", type=int, default=None, help="Sampling steps (defaults to config.json)")
    parser.add_argument("--out", "-o", default=None, help="Output image file path (optional)")
    parser.add_argument("--host", default="http://127.0.0.1:40188", help="Q-Spark API host (default: http://127.0.0.1:40188)")
    parser.add_argument("--info", action="store_true", help="Check currently active model configured in config.json")
    args = parser.parse_args()

    if args.info:
        check_info(args.host)
        return

    if not args.prompt:
        parser.error("生图必须提供 --prompt 参数 (或使用 --info 查看当前生效模型)")

    w, h = parse_dimensions(args.size, args.prompt)
    step_hint = f" | 步数: {args.steps}" if args.steps else ""

    # 1. 实时流式开场：对齐对话流提示信息
    print(f"> 🚀 硬件平台: 本地 NVIDIA GPU | 生图规格: {w}x{h}{step_hint}", flush=True)
    print("> ⏳ 初始化任务配置...", flush=True)

    # 2. 调用标准 v1/images/generations 接口（扩展 stream=True 支持）
    url = f"{args.host.rstrip('/')}/v1/images/generations"
    payload_dict = {
        "prompt": args.prompt,
        "size": f"{w}x{h}",
        "stream": True,
        "response_format": "b64_json",
    }
    if args.steps:
        payload_dict["steps"] = args.steps

    payload = json.dumps(payload_dict).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    start_t = time.time()
    final_out_path = None
    b64_str = None
    model_used = ""
    cost_seconds = 0.0
    last_reported_desc = "初始化任务配置..."

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for line_bytes in resp:
                line = line_bytes.decode("utf-8", errors="replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                raw_data = line[5:].strip()
                if raw_data == "[DONE]":
                    break
                try:
                    ev = json.loads(raw_data)
                except Exception:
                    continue

                if "error" in ev:
                    raise RuntimeError(ev["error"])

                desc = ev.get("desc", "").strip()
                if desc and desc != last_reported_desc:
                    print(f"> ⏳ {desc}", flush=True)
                    last_reported_desc = desc

                if "out_path" in ev:
                    final_out_path = ev["out_path"]
                if "diff_model" in ev:
                    model_used = ev["diff_model"]
                if "cost" in ev:
                    cost_seconds = ev["cost"]
                if "b64_json" in ev:
                    b64_str = ev["b64_json"]

    except urllib.error.URLError as e:
        sys.stderr.write(
            f"[Error] 无法连接到 Q-Spark 服务: {e}\n"
            f"请先在项目根目录启动 Q-Spark 服务 (运行 start.bat 或 Q-Spark.exe，默认端口: {args.host})。\n"
        )
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"[Error] 推理执行异常: {e}\n")
        sys.exit(1)

    total_cost = cost_seconds if cost_seconds > 0 else round(time.time() - start_t, 1)
    print(f"> ✨ 推理生成完成，耗时 {total_cost:.1f}s。", flush=True)

    # 3. 工作区落地保障：确保无论服务端在何处运行，图片均实体落盘到当前 Agent 工作区 outputs/
    target_dir = resolve_default_output_dir()
    target_filename = Path(final_out_path).name if final_out_path else f"qspark_{int(time.time())}.png"
    target_path = Path(args.out).resolve() if args.out else (target_dir / target_filename)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if b64_str:
        target_path.write_bytes(base64.b64decode(b64_str))
    elif final_out_path and Path(final_out_path).is_file():
        if target_path.resolve() != Path(final_out_path).resolve():
            shutil.copyfile(final_out_path, target_path)
    else:
        dl_url = f"{args.host.rstrip('/')}/outputs/{target_filename}"
        urllib.request.urlretrieve(dl_url, str(target_path))

    actual_path = target_path

    try:
        rel_path = os.path.relpath(actual_path, start=os.getcwd()).replace("\\", "/")
    except Exception:
        rel_path = f"outputs/{actual_path.name}"

    abs_link = str(actual_path).replace("\\", "/")
    http_link = f"{args.host.rstrip('/')}/outputs/{target_filename}"

    print(f"SUCCESS: Image saved to {actual_path}")
    if model_used:
        print(f"MODEL_USED: {model_used}")
    print(f"FILE: {actual_path}")
    if http_link:
        print(f"URL: {http_link}")
    print(f"MARKDOWN: ![Generated Image]({rel_path})")
    if http_link:
        print(f"MARKDOWN_HTTP: ![Generated Image]({http_link})")
    print(f"MARKDOWN_FILE: ![Generated Image](file:///{abs_link})")


if __name__ == "__main__":
    main()
