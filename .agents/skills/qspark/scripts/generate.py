import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def resolve_default_output_dir() -> Path:
    """自动推导默认输出路径：优先当前项目根目录 outputs/，否则当前工作目录 outputs/"""
    repo_root = Path(__file__).resolve().parent.parent.parent
    if (repo_root / "start.bat").exists() or (repo_root / "app.py").exists():
        out_dir = repo_root / "outputs"
    else:
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
        print(f"API_STATUS: {data.get('api_status_text', '')}")
    except Exception as e:
        sys.stderr.write(f"[Error] 获取服务配置状态失败: {e}\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate image using local Q-Spark service (follows config.json)")
    parser.add_argument("--prompt", "-p", required=False, help="Image prompt (Chinese or English)")
    parser.add_argument("--size", "-s", default="1024x1024", help="Image size (e.g. 1024x1024, 1360x768, 768x1360)")
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

    url = f"{args.host.rstrip('/')}/v1/images/generations"
    payload_dict = {
        "prompt": args.prompt,
        "size": args.size,
        "response_format": "b64_json"
    }
    if args.steps:
        payload_dict["steps"] = args.steps

    payload = json.dumps(payload_dict).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        sys.stderr.write(
            f"[Error] 无法连接到 Q-Spark 服务: {e}\n"
            f"请先在项目根目录启动 Q-Spark 服务 (运行 start.bat 或 Q-Spark.exe，默认端口: {args.host})。\n"
        )
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"[Error] 请求异常: {e}\n")
        sys.exit(1)

    items = data.get("data", [])
    if not items:
        sys.stderr.write("[Error] Q-Spark 服务未返回图片数据。\n")
        sys.exit(1)

    img_info = items[0]
    b64_str = img_info.get("b64_json")
    remote_url = img_info.get("url", "")
    model_used = img_info.get("revised_prompt", "").replace("Model: ", "").strip()

    if args.out:
        out_path = Path(args.out).resolve()
    else:
        out_dir = resolve_default_output_dir()
        filename = Path(remote_url).name if remote_url else f"qspark_{int(time.time())}.png"
        out_path = out_dir / filename

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if b64_str:
        out_path.write_bytes(base64.b64decode(b64_str))

    link_path = str(out_path).replace("\\", "/")
    print(f"SUCCESS: Image saved to {out_path}")
    if model_used:
        print(f"MODEL_USED: {model_used}")
    print(f"FILE: {out_path}")
    print(f"MARKDOWN: ![Generated Image](file:///{link_path})")


if __name__ == "__main__":
    main()
